import sys, yaml, os, re, pickle
from tabulate import tabulate
import util, device, stream

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
        r = self.root
        return f"{type(self).__name__}: id: {self.id()}, coord: {r['core_coordinates']}"

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
                    s = stream.Stream (stream_designator, stream_data)
                    self.streams[s.id()] = s
            else:
                raise RuntimeError(f"{blob_yaml.id()}: Cannot interpret {key}: {val}")

    # Accessors
    def op_names (self):
        return set (self.root.keys()) - Graph.non_op_keys
    def device_id (self):
        return self.root['target_device']
    def input_count (self):
        return self.root['input_count']

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: {self.name}: Op count: {len (self.root.keys()) - len(Graph.non_op_keys)}, Input count: {self.input_count()}"

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
    this.context.devices = [ device.Device.create(netlist_devices['arch']) ] * netlist_devices["count"]

    return this.context
