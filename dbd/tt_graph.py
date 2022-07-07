import tt_util as util
import tt_stream
from tt_object import TTObject
from tt_pipe import Pipe
from tt_buffer import Buffer
from tt_object import TTObject

# Queues
class Queue(TTObject):
    def __init__(self, name, data):
        self.root = data
        self._id = name
        self.output_ops = set() # set of names of queue's output_ops

    # Class functions
    def occupancy (entries, wrptr, rdptr):
        return (wrptr - rdptr) if wrptr >= rdptr else wrptr - (rdptr - 2 * entries)
    def to_str (channel, addr):
        return f"Ch%d-0x%x" % (channel, addr)

    # Accessors
    def outputs_as_str(self):
        ret_str = ""
        num_ops_fed_by_queue = len(self.output_ops)
        if num_ops_fed_by_queue > 1:
            ret_str = f"[{num_ops_fed_by_queue}]: "
        if num_ops_fed_by_queue > 0:
            ret_str += ', '.join (list(self.output_ops)) if num_ops_fed_by_queue > 0 else ""
        return ret_str

# Operations
class Op(TTObject):
    def __init__(self, name, graph_id, data):
        self.root = data
        self._graph_id = graph_id
        self._id = f"{self._graph_id}/{name}"

# Class that represents a single graph within a netlist
# Contains all the information from graph's blob.yaml and pipegen.yaml
# Provides functions for graph traversal
class Graph(TTObject):
    # Some keys do not refer to operations, and we keep them here to be used when parsing
    non_op_keys = set (['target_device', 'input_count'])

    def __init__(self, name, root, pipegen_yaml, blob_yaml):
        self._id = name
        self.root = root # The entry in netlist file
        self.pipegen_yaml = pipegen_yaml
        self.blob_yaml = blob_yaml
        self.ops = dict()

        for op_name in self.op_names():
            op = Op (op_name, self.id(), self.root[op_name])
            self.ops[op_name] = op

    def load_pipegen_and_blob (self):
        # 1. Load pipegen_yaml
        self.buffers = dict()
        self.op_name_to_buffer_list = dict() # Cache for lookup by op name
        self.pipes = dict()
        for key, val in self.pipegen_yaml.items():
            if key == "graph_name":
                if self.id() != val:
                    util.WARN(f"Expected 'graph_name: {self.id()}' in {self.pipegen_yaml.id()}, but got 'graph_name: {val}'")
            elif "buffer" in key:
                b = Buffer(val)
                self.buffers[b.id()] = b
                op_name = val["md_op_name"]
                if op_name not in self.op_name_to_buffer_list:
                    self.op_name_to_buffer_list[op_name] = []
                self.op_name_to_buffer_list[op_name].append (b)
                uniqid = val["uniqid"]
                for r in range (1, val["replicate"]): # Handle replicated buffers (see issue #326)
                    val["uniqid"] = uniqid + r * val["scatter_gather_num_tiles"]
                    b = Buffer(val)
                    self.buffers[b.id()] = b
                    b.replicated = True # Mark the buffers we created by replication
            elif "pipe" in key:
                p = Pipe(val)
                self.pipes[p.id()] = p
            else:
                raise RuntimeError(f"{self.pipegen_yaml.id()}: Cannot interpret {key}: {val}")

        # 1a. Link buffers to pipe
        max_lines_printed_for_num_missing_buffers = 10
        def print_missing_buffer (self, buf_id, pipe_id, is_input):
            nonlocal max_lines_printed_for_num_missing_buffers
            if max_lines_printed_for_num_missing_buffers > 0:
                max_lines_printed_for_num_missing_buffers -= 1
                if max_lines_printed_for_num_missing_buffers == 0:
                    util.ERROR ("... skipping the rest ...")
                else:
                    util.ERROR (f"Buffer {buf_id} shows up as an {'input' if is_input else 'output'} of pipe {pipe_id} but has no definition in graph {self.id()}. See {self.pipegen_yaml.filepath}")

        for _, p in self.pipes.items():
            for buf_id in p.inputs():
                if buf_id not in self.buffers:
                    print_missing_buffer (self, buf_id, p.id(), True)
                else:
                    self.buffers[buf_id].input_of_pipe_ids.add (p.id())

            for buf_id in p.outputs():
                if buf_id not in self.buffers:
                    print_missing_buffer (self, buf_id, p.id(), False)
                else:
                    self.buffers[buf_id].output_of_pipe_ids.add (p.id())

        # 2. Load blob_yaml
        self.streams = dict()
        for key, val in self.blob_yaml.items():
            if key == "dram_blob":
                util.VERBOSE ("- Skipping dram_blob")
            elif key == "dram_perf_dump_blob":
                util.VERBOSE ("- Skipping dram_perf_dump_blob")
            elif "phase" in key:
                phase_id = int (key[6:])
                for stream_designator, stream_data in val.items():
                    stream_data['phase_id'] = phase_id
                    s = tt_stream.Stream (stream_designator, stream_data)
                    self.streams[s.id()] = s
            else:
                raise RuntimeError(f"{self.blob_yaml.id()}: Cannot interpret {key}: {val}")


    RECURSION_DEPTH = 0 # Temporary/debug limit to prevent infinite recursion

    # Find a buffer given a buffer_id
    def get_buffer (self, buffer_id):
        return self.buffers.get (buffer_id, None)
    def get_buffer_by_op_name (self, op_name):
        return self.op_name_to_buffer_list.get (op_name, None)
    def get_pipe (self, pipe_id):
        return self.pipes.get (pipe_id, None)
    def get_stream (self, stream_loc):
        return self.streams.get (stream_loc, None)

    def __getattr__(self, name):
        if name in { "buffers", "pipes", "streams" }:
            self.load_pipegen_and_blob() # Lazy-loaded structures
        return object.__getattribute__(self, name)

    # Given a buffer list, find all buffers that are connected (pipegen.yaml)
    # connection can be input/output/inputoutput
    def get_connected_buffers (self, buffer_id_list, connection="outputs"):
        if type(buffer_id_list) != list: buffer_id_list = [ buffer_id_list ] # If not a list, assume a single buffer id, and create a list from it

        connected_buffers = []

        for p in self.pipes:
            for b in buffer_id_list:
                if "output" in connection and b in self.get_pipe(p).root["input_list"]:
                    connected_buffers += self.get_pipe(p).root["output_list"]
                if "input" in connection and b in self.get_pipe(p).root["output_list"]:
                    connected_buffers += self.get_pipe(p).root["input_list"]

        return list(set(connected_buffers))

    # Given a buffer list, find all RC coordinates of the cores where the buffers reside
    def get_buff_core_coordinates_rc (self, buffer_id_list):
        if type(buffer_id_list) != list: buffer_id_list = [ buffer_id_list ] # If not a list, assume a single buffer id, and create a list from it
        buff_cores = { self.get_buffer(b).root["core_coordinates"] for b in self.buffers if b in buffer_id_list }
        return list (buff_cores)

    # Prints condensed information on a buffer (list)
    def print_buffer_info (self, buffer_id_list):
        if type(buffer_id_list) != list: buffer_id_list = [ buffer_id_list ] # If not a list, assume a single buffer id, and create a list from it
        for buffer_id in buffer_id_list:
            print (self.get_buffer (buffer_id))

    # Given a list of core coordinates, returns all buffers residing at those coordinates
    def get_core_buffers (self, core_coordinates_list_rc):
        if type(core_coordinates_list_rc) != list: core_coordinates_list_rc = [ core_coordinates_list_rc ] # If not a list, assume a single buffer id, and create a list from it

        buffer_set = set()
        for b in self.buffers:
            b_root = self.get_buffer (b).root
            if b_root["core_coordinates"] in core_coordinates_list_rc:
                buffer_set.add (b_root["uniqid"])
        return list(buffer_set)

    # Checks if a given buffer is an input buffer (i.e. it shows up in the input_list of a pipe)
    def is_input_buffer(self, buffer_id):
        for p in self.pipes:
            p_root = self.get_pipe (p).root
            if buffer_id in p_root["input_list"]: return True
        return False

    # Checks if a given buffer is an output buffer (i.e. it shows up in the output_list of a pipe)
    def is_output_buffer(self, buffer_id):
        for p in self.pipes:
            p_root = self.get_pipe (p).root
            if buffer_id in p_root["output_list"]: return True
        return False

    # Filters a list of buffers, to return only input or output buffers
    def filter_buffers (self, buffer_list, filter):
        if filter == "input":
            return [ bid for bid in buffer_list if self.is_input_buffer(bid) ]
        elif filter == "output":
            return [ bid for bid in buffer_list if self.is_output_buffer(bid) ]
        else:
            raise (f"Exception: {util.CLR_ERR} Invalid filter '{filter}' {util.CLR_END}")

    # Return list of DRAM buffers
    def get_dram_buffers(self):
        input_buffers = []
        for bid, buffer in self.buffers.items():
            if buffer.root["dram_buf_flag"] != 0 or buffer.root["dram_io_flag"] != 0:
                input_buffers.append (bid)
        return input_buffers

    # Computes all buffers that are feeding into the buffers from buffer_id_list
    def fan_in_buffer_set(self, buffer_id_list, already_visited = set()):
        if Graph.RECURSION_DEPTH > 400:
            util.ERROR (f"Recursion limit reached")
            return set()
        Graph.RECURSION_DEPTH=Graph.RECURSION_DEPTH+1

        if type(buffer_id_list) != list: buffer_id_list = [ buffer_id_list ]
        if len (buffer_id_list) == 0:
            return set()

        # Get direct fan-ins
        buff_core_coords = self.get_buff_core_coordinates_rc (buffer_id_list)
        # print (buff_core_coords)
        if (255,255) in buff_core_coords: buff_core_coords.remove ((255,255)) # Exclude DRAM
        buffer_id_list = self.get_core_buffers (buff_core_coords)
        # print (f"Looking for direct fan ins of {buffer_id_list}")
        # print_buffer_info(buffer_id_list)
        direct_fan_ins = set(self.get_connected_buffers (buffer_id_list, "input"))
        # print (f"direct_fan_ins = {direct_fan_ins}")

        # Filter out the buffers we already visited
        # Figure out the set of fan-ins that we have not already visited
        propagate_fan_in_set = direct_fan_ins - already_visited
        # print (f"propagate_fan_in_set = {propagate_fan_in_set}")
        # print (f"fan_in_set = {fan_in_set}")
        already_visited = already_visited | direct_fan_ins

        # print (f"already_visited: {already_visited}")

        return already_visited.union (self.fan_in_buffer_set(list (propagate_fan_in_set), already_visited))

    # Given a list of cores (as a list of RC locations), returns a list of RC coordinates of all the cores
    # that eventually feed the given cores. I.e. returns cores that the given cores depend on.
    def get_fanin_cores_rc (self, core_coordinates_list_rc):
        if type(core_coordinates_list_rc) != list: core_coordinates_list_rc = [ core_coordinates_list_rc ] # If not a list, assume a single buffer id, and create a list from it

        all_core_buffers = self.get_core_buffers (core_coordinates_list_rc)
        # print (f"all_core_buffers: {all_core_buffers}")
        Graph.RECURSION_DEPTH = 0
        core_buffers = list (self.fan_in_buffer_set(all_core_buffers))
        # print (f"get_fanin_cores_rc/core_buffers: {core_buffers}")
        fanin_cores_rc = self.get_buff_core_coordinates_rc (core_buffers)
        # print (f"get_fanin_cores_rc/fanin_cores_rc: {fanin_cores_rc}")
        if (255,255) in fanin_cores_rc: fanin_cores_rc.remove ((255,255)) # Exclude DRAM
        return fanin_cores_rc

    # Accessors
    def op_names (self):
        on = list(set (self.root.keys()) - Graph.non_op_keys)
        on.sort()  # Sort to remove the non-determinism of the above operations
        return on
    def device_id (self):
        return self.root['target_device']
    def input_count (self):
        return self.root['input_count']
    def epoch_id (self):
        return self._epoch_id
    def op (self, op_name):
        return self.ops[op_name]

    def get_pipes_for_buffer (self, buffer_id):
        pipes = []
        for pipe_id in self.pipes:
            pipe = self.get_pipe(pipe_id)
            if buffer_id in pipe.inputs() or buffer_id in pipe.outputs():
                pipes.append(pipe_id)
        return pipes

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: {self.id()}: Op count: {len (self.root.keys()) - len(Graph.non_op_keys)}, Input count: {self.input_count()}"

    # Returns an array of [r,c] pairs for the operation
    def get_op_coords (self, op_name):
        locations = []
        op = self.root[op_name]
        opr = op['grid_loc'][0]
        opc = op['grid_loc'][1]
        for r in range(op['grid_size'][0]):
            for c in range(op['grid_size'][1]):
                locations.append ( ( opr + r, opc + c ) )
        return locations

    # Returns the full op name mapped to a given RC location
    # The name format is graph/op_name:op_type
    def core_coord_to_full_op_name (self, r, c):
        op_name = self.core_coord_to_op_name(r, c)
        if op_name is not None:
            op = self.root[op_name]
            return f"{self.id()}/{op_name}:{op['type']}"
        else:
            return f"No op at {r},{c}"

    # Returns the op name mapped to a given RC location
    def core_coord_to_op_name (self, r, c):
        for op_name, op in self.root.items():
            if op_name not in ['target_device', 'input_count']:
                op_locations = self.get_op_coords(op_name)
                if (r, c) in op_locations:
                    return op_name
        return None

    # API
    def get_op_buffers (self, op_name):
        op_buffers = set( b for _, b in self.buffers.items() if b.root["md_op_name"] == op_name )
        return op_buffers

    # Test
    def _test_print(self):
        for _, b in self.buffers.items():
            print (f"{b}")
        for _, p in self.pipes.items():
            print (f"{p}")
        for stream, s in self.streams.items():
            print (f"{s}")
