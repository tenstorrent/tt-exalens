#!/usr/bin/env python3
"""
tapout.py parses netlist and generates new queues.
"""
import argparse, yaml, subprocess, os
import sys
from collections import defaultdict

GRAYSKULL = "grayskull"
WORMHOLE = "wormhole"
INVALID_ADDRESS = -1
INVALID_CHANNEL = -1

TILE_SIZE = {
    "Float32"   : 32 * 32 * 4 + 32,
    "Tf32"      : 32 * 32 * 4 + 32,
    "Float16"   : 32 * 32 * 2 + 32,
    "Bfp8"      : 32 * 32 + 64 + 32,
    "Bfp4"      : 512 + 64 + 32,
    "Bfp2"      : 256 + 64 + 32,
    "Float16_b" : 32 * 32 * 2 + 32,
    "Bfp8_b"    : 32 * 32 + 64 + 32,
    "Bfp4_b"    : 512 + 64 + 32,
    "Bfp2_b"    : 256 + 64 + 32,
    "Lf8"       : 32 * 32 + 32,
    "UInt16"    : 32 * 32 * 2 + 32,
    "Int8"      : 32 * 32 + 32
}

class NetlistDataShapeReader:
    def __init__(self) -> None:
        pass

    def __init__(self, definition) -> None:
        self._definition = definition

    def get_df(self):
        return self._definition['df']

    def get_grid_size(self):
        return self._definition['grid_size']

    def get_core_count(self):
        return self.get_grid_size()[0] * self.get_grid_size()[1]

    def get_mblock(self):
        return self._definition['mblock']

    def get_ublock(self):
        return self._definition['ublock']

    def get_t(self):
        return self._definition['t']

    def get_size_in_bytes(self):
        return self.get_mblock()[0] * self.get_mblock()[1] * self.get_ublock()[0] * self.get_ublock()[1]*self.get_t()*TILE_SIZE[self.get_df()]

    def __str__(self):
        return f"df: {self.get_df()}, grid_size: {self.get_grid_size()}, mblock: {self.get_mblock()}, ublock: {self.get_ublock()}, t: {self.get_t()}"

class DramAllocation:
    def __init__(self, address, size) -> None:
        self._address = address
        self._size = size

    def get_address(self):
        return self._address

    def get_size(self):
        return self._size

class DramChannel:
    def __init__(self, size) -> None:
        self._size = size
        self._allocations = []

    def set_allocation(self, address, size):
        if (address >= self._size or address + size > self._size or size < 0 or address<0):
            return INVALID_ADDRESS

        for i in range(len(self._allocations)):
            allocation = self._allocations[i]
            if (allocation.get_address() > address):
                if (allocation.get_address() >= address + size):
                    self._allocations.insert(i, DramAllocation(address, size))
                    return address
                else:
                    return INVALID_ADDRESS
            if (allocation.get_address() + allocation.get_size() > address):
                return INVALID_ADDRESS

        self._allocations.append(DramAllocation(address, size))
        return address

    def allocate(self, size):
        if (size < 0 or size > self._size):
            return INVALID_ADDRESS

        previous_empty = 0
        for i in range(len(self._allocations)):
            allocation = self._allocations[i]
            if (allocation.get_address() - previous_empty >= size):
                self._allocations.insert(i, DramAllocation(previous_empty, size))
                return previous_empty
            previous_empty = allocation.get_address() + allocation.get_size()

        if (previous_empty + size <= self._size):
            self._allocations.append(DramAllocation(previous_empty, size))
            return previous_empty

        return INVALID_ADDRESS

    def get_allocations(self):
        return self._allocations

class Dram:
    def __init__(self, channel_cnt, size) -> None:
        self._dram_channels = [DramChannel(size) for i in range(channel_cnt)]
        self._channel_cnt = channel_cnt

    def set_allocation(self, channel, address, size):
        return self._dram_channels[channel].set_allocation(address, size)

    def allocate(self, size):
        for i in range(self._channel_cnt):
            address = self._dram_channels[i].allocate(size)
            if (address != INVALID_ADDRESS):
                return i, address
        return INVALID_CHANNEL, INVALID_ADDRESS

    def get_dram_channels(self):
        return self._dram_channels

    def get_channel_cnt(self):
        return self._channel_cnt


class DramFactory:
    def create_grayskull_dram():
        dram = Dram(8, 1024*1024*1024)
        for i in range(8):
            dram.set_allocation(i, 0, 256 * 1024 * 1024)
        return dram
    def get_dram(netlist):
        if (netlist.get_devices().is_grayskull_supported()):
            dram = DramFactory.create_grayskull_dram()
            for queue in netlist.get_queues():
                if (queue.is_dram()):
                    for channel, address in queue.get_memory():
                        dram.set_allocation(channel, address, queue.get_buffer_size())
            return dram
        return None

class NetlistDevicesReader:
    def __init__(self, devices) -> None:
        self._devices = devices

    def get_count(self):
        return self._devices["count"]

    def is_arch_type_supported(self, name):
        if (type(self.get_arch())==list):
            return name in self.get_arch()
        else:
            return name == self.get_arch()

    def is_grayskull_supported(self):
        return self.is_arch_type_supported(GRAYSKULL)

    def is_wormhole_supported(self):
        return self.is_arch_type_supported(WORMHOLE)

    def get_arch(self):
        return self._devices["arch"]

def get_buffer_size(data_shape, entries):
    return data_shape.get_size_in_bytes() * entries * 2 + 32

class NetlistQueueReader:
    def __init__(self, name, queue) -> None:
        self._name = name
        self._queue = queue

    def get_input(self):
        return self._queue["input"]

    def get_type(self):
        return self._queue["type"]

    def get_entries(self):
        return self._queue["entries"]

    def get_location(self):
        return self._queue["loc"]

    def is_dram(self):
        return self.get_location() == 'dram'

    def get_memory(self):
        return self._queue[self.get_location()]

    def get_buffer_size(self):
        return get_buffer_size(self.get_data_shape(), self.get_entries())

    def get_data_shape(self):
        return NetlistDataShapeReader(self._queue)

class NetlistOperationReader:
    def __init__(self, name, definition) -> None:
        self._name = name
        self._definition = definition
        self._definition['df'] = self._definition['out_df']

    def get_inputs(self):
        return self._definition['inputs']

    def get_name(self):
        return self._name

    def get_data_shape(self):
        return NetlistDataShapeReader(self._definition)

class TopologicalSort:
    def __init__(self):
        self.graph = defaultdict(list)

    def add_edge(self,u,v):
        self.graph[u].append(v)
        self.graph[v]

    def __sort(self,v,visited,sorted_vertices):
        visited[v] = True

        for i in self.graph[v]:
            if visited[i] == False:
                self.__sort(i,visited,sorted_vertices)

        sorted_vertices.insert(0,v)

    def sort(self):
        visited = {}
        for k in self.graph:
            visited[k]=False

        sorted_vertices =[]
        for i in self.graph:
            if visited[i] == False:
                self.__sort(i,visited,sorted_vertices)

        return sorted_vertices

class NetlistGraphReader:
    def __init__(self, name, graph) -> None:
        self._graph = graph
        self._name = name
        self.__init_operations()

    def __init_operations(self):
        self._operations = {}
        for key in self._graph:
            if type(self._graph[key]) is dict:
                self._operations[key] = NetlistOperationReader(key, self._graph[key])

    def get_name(self):
        return self._name

    def get_target_device(self):
        return self._graph['target_device']

    def get_input_count(self):
        return self._graph['input_count']

    def get_inputs(self):
        inputs = set()
        for op in self.get_operations():
            for input in op.get_inputs():
                if not (input in self._operations):
                    inputs.add(input)
        return inputs

    def get_operations(self):
        result = []

        for key in self._operations:
            result.append(self._operations[key])
        return result

    def get_op(self, op_name):
        return self._operations[op_name]

    def get_op_sorted(self):
        topo_sort = TopologicalSort()
        for op in self.get_operations():
            for input in op.get_inputs():
                if input in self._operations:
                    topo_sort.add_edge(input, op.get_name())
        return topo_sort.sort()

class NetlistReader:
    def __init__(self, filename) -> None:
        self._netlist = yaml.safe_load(open(filename))
        self.__devices = self._netlist["devices"]
        self.__queues = self._netlist['queues']
        self.__graphs = self._netlist['graphs']

    def get_devices(self):
        return NetlistDevicesReader(self.__devices)

    def get_graph_names(self):
        return self.__graphs.keys()

    def get_graphs(self):
        graphs = []
        for graph_name in self.get_graph_names():
            graphs.append(self.get_graph(graph_name))
        return graphs

    def get_graph(self, graph_name):
        return NetlistGraphReader(graph_name, self.__graphs[graph_name])

    def get_max_entries(self, graph_name):
        max_entries = 0
        g = self.get_graph(graph_name)
        for input in g.get_inputs():
            max_entries = max(self.get_queue(input).get_entries(), max_entries)
        return max_entries

    def get_queue_names(self):
        return self.__queues.keys()

    def get_queues(self):
        queues = []
        for queue_name in self.get_queue_names():
            queues.append(self.get_queue(queue_name))
        return queues

    def get_queue(self, queue_name):
        return NetlistQueueReader(queue_name, self.__queues[queue_name])

    def get_queue_inputs(self):
        inputs = set()
        for queue in self.get_queues():
            inputs.add(queue.get_input())
        return inputs

class NetlistTapOut:
    def __init__(self, filename) -> None:
        self._netlist = NetlistReader(filename)
        self._filename = filename
        self._dram = DramFactory.get_dram(self._netlist)

    def generate_tapout_queue_as_string(self, graph_name, op_name):
        graph = self._netlist.get_graph(graph_name)
        op = graph.get_op(op_name)
        entries = self._netlist.get_max_entries(graph_name)
        output = f"  DBG_{op.get_name()}: "
        output += "{"
        output += f"input: {op.get_name()}, type: queue, entries: {entries}, {op.get_data_shape()}, target_device: {graph.get_target_device()}, loc: dram, dram: ["
        for i in range(op.get_data_shape().get_core_count()):
            channel, address = self._dram.allocate(get_buffer_size(op.get_data_shape(), entries))
            if (i > 0):
                output+=", "
            output += f"[{channel}, 0x{address:02x}]"
        output += "]}"
        return output

    def get_ops_to_tapout(self):
        result = []
        inputs = self._netlist.get_queue_inputs()
        for graph in self._netlist.get_graphs():
            for op_name in graph.get_op_sorted():
                if not op_name in inputs:
                    result.append([graph.get_name(), op_name])
        return result

class TapoutCommandExecutor:
    def __init__(self, command, out_dir) -> None:
        self._command = command
        self._out_dir = out_dir

    def get_netlist(self):
        cmd = self._command.split()
        return cmd[cmd.index("--netlist") + 1]

    def get_modified_command(self, new_netlist_filename):
        cmd = self._command.split()
        cmd[cmd.index("--netlist") + 1 ] = new_netlist_filename
        return cmd

    def create_netlist(self, output_file, queue):
        file_original = open(self.get_netlist(), "r")
        file_modified = open(output_file, "w")
        for line in file_original:
            file_modified.write(line)
            if (line.startswith("queues:")):
                file_modified.write(queue+"\n")
        file_original.close()
        file_modified.close()

    def run_cmd(op_name, cmd, log_filename, op_error_log):
        TapoutCommandExecutor.reset()
        print(f"Tapout operation:\t{op_name}\nCommand:\t\t{' '.join(cmd)}\nLog:\t\t\t{log_filename}")

        f = open(log_filename, "w")

        f_diff = open(op_error_log, "a")
        f_diff.writelines(f"{op_name}\n")
        f_diff.close()

        operation_processed = False
        tapout_output_error = False
        test_finished = True
        with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
            try:
                lines = []
                cnt = 0
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        break

                    ln = line.decode("utf-8")

                    if "DBG_"+op_name in ln:
                        if not operation_processed:
                            operation_processed = True

                    # Check if we detected error 
                    if "Error" in ln and "Queue:" in ln:
                        if op_name in ln and "DBG" in ln:
                            tapout_output_error = True
                            f_diff = open(op_error_log, "a")
                            lines.append("\n")
                            f_diff.writelines(lines)
                            f_diff.close()
                            print(''.join(lines))
                        lines = []
                        cnt = 0

                    # HACK This is hack to detect that test will start
                    # dumping tiles 
                    if "First Mismatched Tile for Tensor" in ln:
                        cnt = 1

                    if cnt > 0:
                        lines.append(ln)
                        cnt = cnt + 1

                    if cnt > 100:
                        cnt = 0
                        lines = []

                    f.writelines(ln)
            except Exception as e:
                proc.terminate()
                if not "what():  Test Failed" in repr(e):
                    test_finished = False
                f.writelines(repr(e))
                print(e)

        f.close()

        return tapout_output_error, operation_processed, test_finished

    def get_modified_netlist_filename(self, graph_name, op_name):
        return f"{self._out_dir}/{graph_name}_{op_name}.yaml"

    def get_tapout_log(self, graph_name, op_name):
        return f"{self._out_dir}/{graph_name}_{op_name}.log"

    def get_run_result_log(self):
        return f"{self._out_dir}/tapout_result.log"

    def get_op_errors_log(self):
        return f"{self._out_dir}/op_errors.log"

    def reset():
        with subprocess.Popen(["device/bin/silicon/reset.sh"], stdout=subprocess.PIPE) as proc:
            try:
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    ln = line.decode("utf-8")
                    print (ln, end="")
            except Exception as e:
                print(e)
                proc.terminate()

    def run(self):

        if not os.path.exists(self._out_dir):
            os.makedirs(self._out_dir)
        f_diff = open(self.get_op_errors_log(), "w")
        f_diff.close()

        result_file = open(self.get_run_result_log(), "w")

        netlist_tapout = NetlistTapOut(self.get_netlist())
        for graph_name, op_name in netlist_tapout.get_ops_to_tapout():
            netlist_filename = self.get_modified_netlist_filename(graph_name, op_name)
            cmd = self.get_modified_command(netlist_filename)

            self.create_netlist(netlist_filename, netlist_tapout.generate_tapout_queue_as_string(graph_name, op_name))
            log_filename = self.get_tapout_log(graph_name, op_name)
            result, operation_processed, test_finished = TapoutCommandExecutor.run_cmd(op_name, cmd, log_filename, self.get_op_errors_log())
            result_file.writelines(f'op_name: {op_name}\n\tCommand: {" ".join(cmd)}\n\tLog:{log_filename}\n\t')
            if operation_processed:
                result_file.writelines(f'Result: {"PASSED" if result == 0 else "FAILED"}\n')
            else:
                if test_finished:
                    result_file.writelines(f'Result: TAPOUT OUTPUT NOT PROCESSED\n')
                else:
                    result_file.writelines(f'Result: COMMAND FAILURE (For more information look at log file\n')
            result_file.flush()
        result_file.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test_command', type=str, required=True, help='Command that will be executed with modified netlist')
    parser.add_argument('--out_dir', type=str, required=True, help='Output directory')
    args = parser.parse_args()


    command = args.test_command
    TapoutCommandExecutor(command, args.out_dir).run()

if __name__ == "__main__":
    main()