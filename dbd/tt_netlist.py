import sys, os
from dbd.tt_object import TTObject
import tt_util as util, tt_device, tt_stream
import tt_object
from tt_graph import Graph, Queue, Op

# 'this' is a reference to the module object instance itself.
this = sys.modules[__name__]
this.context = None

# converts data format to string
def get_data_format_from_string(str):
    data_format = {}
    data_format["Float32"]   = 0
    data_format["Float16"]   = 1
    data_format["Bfp8"]      = 2
    data_format["Bfp4"]      = 3
    data_format["Bfp2"]      = 11
    data_format["Float16_b"] = 5
    data_format["Bfp8_b"]    = 6
    data_format["Bfp4_b"]    = 7
    data_format["Bfp2_b"]    = 15
    data_format["Lf8"]       = 10
    data_format["UInt16"]    = 12
    data_format["Int8"]      = 14
    data_format["Tf32"]      = 4
    if str in data_format:
        return data_format[str]
    return None

# Wrapper for Buda run netlist.yaml and, currently, runtime_data.yaml files
class Netlist:
    def load_netlist_data (self):
        # 1. Cache epoch id, device id and graph names
        self.epoch_id_to_graph_name_map = dict()
        self._epoch_ids = set()

        for graph_name in self.graph_names():
            epoch_id = self.graph_name_to_epoch_id(graph_name)
            assert (epoch_id not in self._epoch_ids)  # We do not support multiple graphs in the same epoch
            self._epoch_ids.add (epoch_id)

            self.epoch_id_to_graph_name_map[epoch_id] = graph_name

        self._epoch_ids = list (self._epoch_ids)
        self._epoch_ids.sort()

        # 2. Load queues
        self.queues = dict()
        for queue_name in self.queue_names():
            queue = Queue (queue_name, self.yaml_file.root["queues"][queue_name])
            self.queues[queue_name] = queue

    # Initializes, but does not yet load pipegen and blob files
    def load_graphs (self, rundir):
        self.epoch_to_pipegen_yaml_file = dict()
        self.epoch_to_blob_yaml_file = dict()
        self.graphs = dict()
        for graph_name in self.graph_names():
            epoch_id = self.graph_name_to_epoch_id(graph_name)
            graph_dir=f"{rundir}/temporal_epoch_{epoch_id}"
            if not os.path.isdir(graph_dir):
                util.FATAL (f"Error: cannot find directory {graph_dir}")

            pipegen_file=f"{graph_dir}/overlay/pipegen.yaml"
            blob_file=f"{graph_dir}/overlay/blob.yaml"

            pipegen_yaml = util.YamlFile(pipegen_file)
            self.epoch_to_pipegen_yaml_file[epoch_id] = pipegen_yaml
            blob_yaml = util.YamlFile(blob_file)
            self.epoch_to_blob_yaml_file[epoch_id] = blob_yaml

            # Create the graph
            g = Graph(graph_name, self.yaml_file.root['graphs'][graph_name], pipegen_yaml, blob_yaml)
            self.graphs[graph_name] = g

    def __init__(self, netlist_filepath, rundir):
        # 1. Load the runtime data file
        self.runtime_data_yaml = util.YamlFile(f"{rundir}/runtime_data.yaml")

        if netlist_filepath is None:
            netlist_filepath = self.get_netlist_path()

        # 2. Load the netlist itself
        self.yaml_file = util.YamlFile (netlist_filepath)
        self.load_netlist_data ()

        # 3. Load pipegen/blob yamls
        self.load_graphs (rundir)

        # 4. Extra stuff
        for graph_name, graph in self.graphs.items():
            for op_name, op in graph.ops.items():
                for input in op.root["inputs"]:
                    if input in self.queues:
                        self.queues[input].output_ops.add (op_name)

    # Accessors
    def epoch_ids (self):
        return self._epoch_ids
    def graph_names (self):
        return self.yaml_file.root['graphs'].keys()
    def queue_names (self):
        return self.yaml_file.root['queues'].keys()
    def graph_name_to_epoch_id (self, graph_name):
        return self.runtime_data_yaml.root["graph_to_epoch_map"][graph_name]["epoch_id"]
    def graph_name_to_device_id (self, graph_name):
        return self.runtime_data_yaml.root["graph_to_epoch_map"][graph_name]["target_device"] if graph_name in self.runtime_data_yaml.root["graph_to_epoch_map"] else None
    def epoch_id_to_graph_name (self, epoch_id):
        return self.epoch_id_to_graph_name_map[epoch_id] if epoch_id in self.epoch_id_to_graph_name_map else None
    def graph (self, graph_name):
        return self.graphs[graph_name]
    def devices(self):
        return self.yaml_file.root["devices"]
    def queue(self, queue_name):
        return self.queues[queue_name]

    # Determines the architecture
    def get_arch (self):
        if "arch_name" in self.runtime_data_yaml.root:
            return self.runtime_data_yaml.root["arch_name"]
        return None

    # Determines the netlist file path
    def get_netlist_path (self):
        if "netlist_path" in self.runtime_data_yaml.root:
            return self.runtime_data_yaml.root["netlist_path"]
        return None

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: {self.yaml_file.filepath}. Graphs({len(self.graph_names())}): {' '.join (self.graph_names())}"

# All-encompassing structure representing a Buda run context
class Context:
    netlist = None # Netlist and related 'static' data (i.e. data stored in files such as blob.yaml, pipegen.yaml)
    devices = None # A list of objects of class Device used to extract 'dynamic' data (i.e. data read from the devices)
    pass

# Loads all files necessary to debug a single buda run
# Returns a debug 'context' that contains the loaded information
def load (netlist_filepath, run_dirpath):
    if (this.context is None):  # This refers to the module
        util.VERBOSE (f"Initializing context")
        this.context = Context()

    # Load netlist files
    this.context.netlist = Netlist(netlist_filepath, run_dirpath)

    netlist_devices = this.context.netlist.devices()
    arch = this.context.netlist.get_arch ()
    this.context.devices = [ tt_device.Device.create(arch) for i in range (16) ]

    return this.context