import sys, yaml, os
import util
# this is a pointer to the module object instance itself.
this = sys.modules[__name__]
this.context = None

# WH (generic case):
# One graph one device.
# One temporal epoch can use multiple graphs. -> one pipegen.yaml might contain multiple graphs.

# GS:
# One graph, one device, one temporal epoch
# This might change when direct streaming over PCI gets implemented

# Is epoch_id


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

class Location:
    # Types: 'core-in-device', 'device-in-cluster', 'stream-in-device'...
    pass

class Buffer:
    def __init__(self, data):
        self.root = data

    # Accessors
    def id (self):
        return self.root['uniqid']

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: {self.root['id']}"

class Pipe:
    def __init__(self, data):
        self.root = data

    # Accessors
    def id (self):
        return self.root['id']

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: {self.root['id']}"

class Graph:
    # Some keys do not refer to operations
    non_op_keys = set (['target_device', 'input_count'])

    def __init__(self, name, root, pipegen_yaml, blob_yaml):
        self.name = name
        self.root = root # The entry in netlist file

        # 1. Load pipegen_yaml
        self.buffers = dict()
        self.pipes = dict()
        for key, val in pipegen_yaml.items():
            if key == "graph_name":
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
        for key, val in blob_yaml.items():
            if key == "dram_blob":
                pass
            elif key == "dram_perf_dump_blob":
                pass
            elif "phase" in key:
                pass
            else:
                raise RuntimeError(f"{blob_yaml.id()}: Cannot interpret {key}: {val}")

    # Accessors
    def ops (self):
        return set (self.root.keys()) - Graph.non_op_keys
    def device_id (self):
        return self.root['target_device']
    def input_count (self):
        return self.root['input_count']

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: {self.name}: Op count: {len (self.root.keys()) - len(Graph.non_op_keys)}, Input count: {self.input_count()}"

class Netlist:
    def __init__(self, filepath, rundir):
        # 1. Load the netlist itself
        self.yaml_file = YamlFile (filepath)

        # 2. Load the graph to epoch map. Example:
        self.graph_to_epoch_map_yaml_file = yaml.safe_load(open(f"{rundir}/graph_to_epoch_map.yaml"))

        # Cache epoch id, device id and graph names
        for graph_name in self.graph_names():
            epoch_id = self.graph_name_to_epoch_id(graph_name)
            target_device = self.graph_name_to_device_id(graph_name)

            self.epoch_id_to_graph_name = dict()
            self.epoch_id_to_graph_name[epoch_id] = graph_name
            self.device_id_to_graph_name = dict()
            self.device_id_to_graph_name[target_device] = graph_name

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
    def graph_names (self):
        return self.yaml_file.root['graphs'].keys()
    def graph_name_to_epoch_id (self, graph_name):
        return self.graph_to_epoch_map_yaml_file[graph_name]["epoch_id"]
    def graph_name_to_device_id (self, graph_name):
        return self.graph_to_epoch_map_yaml_file[graph_name]["target_device"]
    def epoch_id_to_graph_name (self, epoch_id):
        return self.epoch_id_to_graph_name[epoch_id]
    def device_id_to_graph_name (self, device_id):
        return self.device_id_to_graph_name[device_id]
    def graph (self, graph_name):
        return self.graphs[graph_name]

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: {self.yaml_file.filepath}. Graphs({len(self.graph_names())}): {' '.join (self.graph_names())}"

class Device:
    def __init__(self, type = "grayskull"):
        self.type = type

class Queue:
    pass

class Stream:
    pass

def load (netlist_filepath, run_dirpath):
    if (this.context is None):
        print (f"Initializing context")
        this.context = Stream()

    # Load netlist files
    print (f"Loading netlist '{netlist_filepath}'")
    this.context.netlist = Netlist(netlist_filepath, run_dirpath)

    print (this.context.netlist)

def analyze_blocked_streams (graph, chip_array, current_x, current_y):
    headers = [ "X-Y", "Op", "Stream", "Type", "Epoch", "Phase", "MSgrayskull.REMAINING", "MSgrayskull.RECEIVED", "Depends on", "State", "Flag" ]
    rows = []

    # 1. Read and analyze data
    chip_data = dict()
    active_streams = dict()
    empty_input_streams = dict()

    for i, chip in enumerate (chip_array):
        chip_data[i] = {
            "chip" : chip,
            "cores" : { }
        }
        # 1. Read all stream data
        streams = get_all_streams_ui_data (chip, grayskull.x_coords, grayskull.y_coords)

        # 2a. Analyze the data
        for x in grayskull.x_coords:
            chip_data[i]["cores"][x] = {}
            for y in grayskull.y_coords:
                has_active_stream = False
                has_empty_inputs = False

                for stream_id in range (0, 64):
                    if is_stream_active(streams[x][y][stream_id]):
                        has_active_stream = True
                        active_streams[(i, x, y, stream_id)] = streams
                    current_phase = int(streams[x][y][stream_id]['CURR_PHASE'])
                    if current_phase > 0: # Must be configured
                        stream_type_str = stream_type(stream_id)["short"]
                        NUM_MSGS_RECEIVED = int(streams[x][y][stream_id]['NUM_MSGS_RECEIVED'])
                        if stream_type_str == "input" and NUM_MSGS_RECEIVED == 0:
                            has_empty_inputs = True
                            empty_input_streams[(i, x, y, stream_id)] = streams

                chip_data[i]["cores"][x][y] = {\
                    "fan_in_cores" : [],\
                    "has_active_stream" : has_active_stream,\
                    "has_empty_inputs" : has_empty_inputs\
                }

        # 2b. Find stream dependencies
        active_core_rc_list = [ grayskull.noc0_to_rc( active_stream[1], active_stream[2] ) for active_stream in active_streams ]
        active_core_noc0_list = [ ( active_stream[1], active_stream[2] ) for active_stream in active_streams ]
        for active_core_rc in active_core_rc_list:
            fan_in_cores_rc = get_fanin_cores_rc (active_core_rc)
            active_core_noc0 = grayskull.rc_to_noc0 (active_core_rc[0], active_core_rc[1])
            # print (f"fan_in_cores_rc for {active_core_rc}: {fan_in_cores_rc}")
            fan_in_cores_noc0 = [ grayskull.rc_to_noc0 (rc[0], rc[1]) for rc in fan_in_cores_rc ]
            chip_data[i]["cores"][active_core_noc0[0]][active_core_noc0[1]]["fan_in_cores"] = fan_in_cores_noc0

        # 3. Print the output
        last_core_loc = None
        for x in grayskull.x_coords:
            for y in grayskull.y_coords:
                has_active_stream = chip_data[i]["cores"][x][y]["has_active_stream"]
                has_empty_inputs = chip_data[i]["cores"][x][y]["has_empty_inputs"]
                if has_active_stream:
                    for stream_id in range (0, 64):
                        current_phase = int(streams[x][y][stream_id]['CURR_PHASE'])
                        if current_phase > 0:
                            epoch_id = current_phase>>10
                            stream_type_str = stream_type(stream_id)["short"]
                            stream_active = is_stream_active(streams[x][y][stream_id])
                            NUM_MSGS_RECEIVED = int(streams[x][y][stream_id]['NUM_MSGS_RECEIVED'])
                            CURR_PHASE_NUM_MSGS_REMAINING = int(streams[x][y][stream_id]['CURR_PHASE_NUM_MSGS_REMAINING'])
                            graph_name = EPOCH_ID_TO_GRAPH_NAME[epoch_id]
                            op = core_coord_to_op_name(graph_name, x, y)
                            core_loc = f"{x}-{y}"
                            fan_in_cores = chip_data[i]['cores'][x][y]['fan_in_cores']
                            fan_in_cores_str = ""
                            if last_core_loc != core_loc:
                                for fic_noc0 in fan_in_cores:
                                    if fic_noc0 in active_core_noc0_list:
                                        fan_in_cores_str += f"{fic_noc0[0]}-{fic_noc0[1]} "
                            flag = f"{util.CLR_WARN}All core inputs ready, but no output generated{util.CLR_END}" if not has_empty_inputs and last_core_loc != core_loc else ""
                            row = [ core_loc if last_core_loc != core_loc else "", op if last_core_loc != core_loc else "", stream_id, stream_type_str, epoch_id, current_phase, CURR_PHASE_NUM_MSGS_REMAINING, NUM_MSGS_RECEIVED, fan_in_cores_str, f"Active" if stream_active else "", flag ]
                            last_core_loc = core_loc
                            rows.append (row)
    if len(rows) > 0:
        print (tabulate(rows, headers=headers))
    else:
        print ("No blocked streams detected")
