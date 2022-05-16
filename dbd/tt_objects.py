import sys, yaml, os, re, pickle
from tabulate import tabulate
import tt_util as util, tt_device, tt_stream

# this is a pointer to the module object instance itself.
this = sys.modules[__name__]
this.context = None

# Each class should have a to_str function ('single-line', 'extensive')

# Store all data loaded from a yaml file here
# Other classes constructed from the data in the yaml (netlist, blob, etc) can point to this
class YamlFile:
    def __init__ (self, filepath):
        util.DEBUG (f"Loading '{filepath}'")
        self.filepath = filepath
        self.root = dict()
        # Since some files (Pipegen.yaml) contain multiple documents (separated by ---): We merge them all into one map.
        for i in yaml.safe_load_all(open(filepath)):
            self.root = { **self.root, **i }

    def __str__(self):
        return f"{type(self).__name__}: {self.filepath}"
    def items(self):
        return self.root.items()
    def id(self):
        return self.filepath

class CachedDictFile:
    def __init__ (self, filepath):
        self.filepath = filepath
        self.enabled = True

    def load_cached (self, generator, generator_name):
        # Use cache
        if self.enabled and os.path.exists (self.filepath):
            print (f"{util.CLR_WARN}Loading {generator_name} cache from file {self.filepath}{util.CLR_END}")
            with open(self.filepath, 'rb') as f:
                streams = pickle.load(f)
                return streams
        else:
            streams = generator()

        if self.enabled:
            print (f"{util.CLR_WARN}Saving {generator_name} cache to file {self.filepath}{util.CLR_END}")
            with open(self.filepath, 'wb') as f:
                pickle.dump(streams, f)

        return streams

class Location:
    # Types: 'core-in-device', 'device-in-cluster', 'stream-in-device'...
    pass

# Constructed from epoch's pipegen.yaml
class Buffer:
    def __init__(self, data):
        data["core_coordinates"] = tuple(data["core_coordinates"])
        self.root = data

    # Accessors
    def id (self):
        return self.root['uniqid']

    # Renderer
    def __str__(self):
        r = self.root
        return f"{type(self).__name__}: id: {self.id()}, coord: {r['core_coordinates']}"

# Constructed from epoch's pipegen.yaml
class Pipe:
    def __init__(self, data):
        self.root = data

    # Accessors
    def id (self):
        return self.root['id']
    def inputs(self):
        return self.root['input_list']
    def outputs(self):
        return self.root['output_list']

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: id: {self.id()}, inputs: {self.inputs()}, outputs: {self.outputs()}"

class Graph:
    # Some keys do not refer to operations, and we keep them here to be used when parsing
    non_op_keys = set (['target_device', 'input_count'])

    def __init__(self, name, root, pipegen_yaml, blob_yaml):
        self.name = name
        self.root = root # The entry in netlist file

        # 1. Load pipegen_yaml
        self.buffers = dict()
        self.pipes = dict()
        for key, val in pipegen_yaml.items():
            if key == "graph_name":
                if self.name != val:
                    util.WARN(f"Expected 'graph_name: {self.name}' in {pipegen_yaml.id()}, but got 'graph_name: {val}'")
            elif "buffer" in key:
                b = Buffer(val)
                self.buffers[b.id()] = b
            elif "pipe" in key:
                p = Pipe(val)
                self.pipes[p.id()] = p
            else:
                raise RuntimeError(f"{pipegen_yaml.id()}: Cannot interpret {key}: {val}")

        # 2. Load blob_yaml
        self.streams = dict()
        for key, val in blob_yaml.items():
            if key == "dram_blob":
                util.INFO ("Skipping dram_blob")
            elif key == "dram_perf_dump_blob":
                util.INFO ("Skipping dram_perf_dump_blob")
            elif "phase" in key:
                phase_id = int (key[6:])
                for stream_designator, stream_data in val.items():
                    stream_data['phase_id'] = phase_id
                    s = tt_stream.Stream (stream_designator, stream_data)
                    self.streams[s.id()] = s
            else:
                raise RuntimeError(f"{blob_yaml.id()}: Cannot interpret {key}: {val}")

    RECURSION_DEPTH = 0 # Temporary/debug limit to prevent infinite recursion

    # Find a buffer given a buffer_id
    def get_buffer (self, buffer_id):
        return self.buffers.get (buffer_id, None)
    def get_pipe (self, pipe_id):
        return self.pipes.get (pipe_id, None)

    # Not used
    # # Find stream information for a given buffer (from blob.yaml)
    # def get_stream_for_buffer_id (self, buffer_id):
    #     for s in self.streams:
    #         stream_data = s.root
    #         if "buf_id" in stream_data and stream_data["buf_id"] == buffer_id:
    #             return s.id()
    #     return None

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

    # Checks if a given buffer is and output buffer (shows up in the input_list of a pipe)
    def is_input_buffer(self, buffer_id):
        for p in self.pipes:
            p_root = self.get_pipe (p).root
            if buffer_id in p_root["input_list"]: return True
        return False

    # Checks if a given buffer is an output buffer (shows up in the output_list of a pipe)
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
            print (f"{util.CLR_ERR}Recursion limit reached{util.CLR_END}")
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


    # # Test only code
    # def test_traverse_from_inputs (graph, chip_array, current_x, current_y):
    #     graph_buffs = get_dram_buffers (graph)
    #     # print (f"graph_buffs = {graph_buffs}")
    #     in_buffs = filter_buffers(graph_buffs, "input")
    #     # print (f"in_buffs = {in_buffs}")
    #     out_buffs = filter_buffers(graph_buffs, "output")
    #     # print (f"out_buffs = {out_buffs}")

    #     dest_buffers = get_connected_buffers (in_buffs, "outputs")
    #     core_coordinates = get_buff_core_coordinates_rc(dest_buffers)
    #     # print (f"get_buff_core_coordinates_rc: {core_coordinates}")
    #     core_buffers = get_core_buffers (core_coordinates)
    #     # print (f"core_buffers: {core_buffers}")
    #     core_output_buffers = filter_buffers (core_buffers, "output")
    #     # print (f"core_output_buffers: {core_output_buffers}")
    #     print_buffer_info (core_output_buffers)

    #     fan_in_set = fan_in_buffer_set(core_output_buffers)
    #     # print (f"fan_in_buffer_set of {core_output_buffers} are: {fan_in_set}")


    # Accessors
    def id (self):
        return self.name
    def op_names (self):
        return set (self.root.keys()) - Graph.non_op_keys
    def device_id (self):
        return self.root['target_device']
    def input_count (self):
        return self.root['input_count']
    def epoch_id (self):
        return self._epoch_id

    def get_pipes_for_buffer (self, buffer_id):
        pipes = []
        for pipe_id in self.pipes:
            pipe = self.get_pipe(pipe_id)
            if buffer_id in pipe.inputs() or buffer_id in pipe.outputs():
                pipes.append(pipe_id)
        return pipes

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: {self.name}: Op count: {len (self.root.keys()) - len(Graph.non_op_keys)}, Input count: {self.input_count()}"


    # Returns an array of [r,c] pairs for the operation
    def get_op_coords (self, op_name):
        locations = []
        op = self.root[op_name]
        opr = op['grid_loc'][0]
        opc = op['grid_loc'][1]
        for r in range(op['grid_size'][1]):
            for c in range(op['grid_size'][0]):
                locations.append ( [ opr + r, opc + c ] )
        return locations

    # Returns the op name mapped to a given RC location
    def core_coord_to_op_name (self, r, c):
        for op_name, op in self.root.items():
            if op_name not in ['target_device', 'input_count']:
                op_locations = self.get_op_coords(op_name)
                if [ r, c ] in op_locations:
                    return f"{self.name}/{op_name}:{op['type']}"

    # Test
    def _test_print(self):
        for bname, b in self.buffers.items():
            print (f"{b}")
        for pname, p in self.pipes.items():
            print (f"{p}")
        for stream, s in self.streams.items():
            print (f"{s}")

class Netlist:
    def __init__(self, filepath, rundir):
        # 1. Load the netlist itself
        self.yaml_file = YamlFile (filepath)

        # 2. Load the graph to epoch map. Example:
        self.graph_to_epoch_map_yaml_file = yaml.safe_load(open(f"{rundir}/graph_to_epoch_map.yaml"))

        # Cache epoch id, device id and graph names
        self.epoch_id_to_graph_name_map = dict()
        self._epoch_ids = set()

        for graph_name in self.graph_names():
            epoch_id = self.graph_name_to_epoch_id(graph_name)
            assert (epoch_id not in self._epoch_ids)  # We do not support multiple graphs in the same epoch
            self._epoch_ids.add (epoch_id)
            target_device = self.graph_name_to_device_id(graph_name)

            self.epoch_id_to_graph_name_map[epoch_id] = graph_name

        self._epoch_ids = list (self._epoch_ids)
        self._epoch_ids.sort()

        # 3. Load pipegen and blob files
        self.epoch_to_pipegen_yaml_file = dict()
        self.epoch_to_blob_yaml_file = dict()
        self.graphs = dict()
        for graph_name in self.graph_names():
            epoch_id = self.graph_name_to_epoch_id(graph_name)
            util.DEBUG (f"Loading epoch {epoch_id} ({graph_name})")
            graph_dir=f"{rundir}/temporal_epoch_{epoch_id}"
            if not os.path.isdir(graph_dir):
                util.FATAL (f"Error: cannot find directory {graph_dir}")

            pipegen_file=f"{graph_dir}/overlay/pipegen.yaml"
            blob_file=f"{graph_dir}/overlay/blob.yaml"

            pipegen_yaml = YamlFile(pipegen_file)
            self.epoch_to_pipegen_yaml_file[epoch_id] = pipegen_yaml
            blob_yaml = YamlFile(blob_file)
            self.epoch_to_blob_yaml_file[epoch_id] = blob_yaml

            # Create the graph
            g = Graph(graph_name, self.yaml_file.root['graphs'][graph_name], pipegen_yaml, blob_yaml)
            self.graphs[graph_name] = g

    # Accessors
    def epoch_ids (self):
        return self._epoch_ids
    def graph_names (self):
        return self.yaml_file.root['graphs'].keys()
    def graph_name_to_epoch_id (self, graph_name):
        return self.graph_to_epoch_map_yaml_file[graph_name]["epoch_id"]
    def graph_name_to_device_id (self, graph_name):
        return self.graph_to_epoch_map_yaml_file[graph_name]["target_device"] if graph_name in self.graph_to_epoch_map_yaml_file else None
    def epoch_id_to_graph_name (self, epoch_id):
        return self.epoch_id_to_graph_name_map[epoch_id] if epoch_id in self.epoch_id_to_graph_name_map else None
    def graph (self, graph_name):
        return self.graphs[graph_name]
    def devices(self):
        return self.yaml_file.root["devices"]

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: {self.yaml_file.filepath}. Graphs({len(self.graph_names())}): {' '.join (self.graph_names())}"


# All-encompassing structure to pass around
class Context:
    netlist = None
    devices = None
    pass

def load (netlist_filepath, run_dirpath):
    if (this.context is None):  # This refers to the module
        print (f"Initializing context")
        this.context = Context()

    # Load netlist files
    print (f"Loading netlist '{netlist_filepath}'")
    this.context.netlist = Netlist(netlist_filepath, run_dirpath)

    netlist_devices = this.context.netlist.devices()
    this.context.devices = [ tt_device.Device.create(netlist_devices['arch']) ] * netlist_devices["count"]

    return this.context