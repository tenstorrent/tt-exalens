import os
from tt_object import TTObjectIDDict
import tt_util as util
from tt_graph import Graph, Queue

# Wrapper for Buda run netlist.yaml and, currently, runtime_data.yaml files
class Netlist:
    def load_netlist_data (self):
        # 1. Cache epoch id, device id and graph names
        self._epoch_id_to_graph_names_map = dict()
        self._epoch_ids = util.set()
        self._map_graph_names = dict()

        for graph_name in self.graph_names():
            epoch_id = self.graph_name_to_epoch_id(graph_name)
            device_id = self.graph_name_to_device_id(graph_name)
            if device_id not in self._map_graph_names:
                self._map_graph_names[device_id] = dict()
            self._map_graph_names[device_id][epoch_id] = graph_name

            # assert (epoch_id not in self._epoch_ids)  # We do not support multiple graphs in the same epoch
            self._epoch_ids.add (epoch_id)

            if epoch_id not in self._epoch_id_to_graph_names_map:
                self._epoch_id_to_graph_names_map[epoch_id] = util.set()
            self._epoch_id_to_graph_names_map[epoch_id].add (graph_name)

        self._epoch_ids = list (self._epoch_ids)
        self._epoch_ids.sort()

        # 2. Load queues
        self._queues = TTObjectIDDict()
        for queue_name in self.queue_names():
            queue = Queue (queue_name, self.yaml_file.root["queues"][queue_name])
            self._queues[queue.id()]=queue

    # Initializes, but does not yet load pipegen and blob files
    def load_graphs (self, rundir):
        self.epoch_to_pipegen_yaml_file = dict()
        self.epoch_to_blob_yaml_file = dict()
        self.graphs = TTObjectIDDict()
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
            g = Graph(self, graph_name, self.yaml_file.root['graphs'][graph_name], pipegen_yaml, blob_yaml)
            self.graphs[g.id()] = g

    def __init__(self, netlist_filepath, rundir, runtime_data_yaml):
        # 1. Set the file. It will be lazy loaded on first access
        assert runtime_data_yaml is not None
        self.runtime_data_yaml = runtime_data_yaml

        if netlist_filepath is None:
            netlist_filepath = self.get_netlist_path()

        # 2. Load the netlist itself
        self.yaml_file = util.YamlFile (netlist_filepath)
        self.load_netlist_data ()

        # 3. Load pipegen/blob yamls
        self.load_graphs (rundir)

        # 4. Cache the output_ops for each queue
        all_queue_ids = self._queues.keys()
        for graph_id, graph in self.graphs.items():
            for op_id, op in graph.ops.items():
                for input in op.root["inputs"]:
                    if input in all_queue_ids:
                        self._queues[input].output_ops.add (op)

    # Accessors
    def epoch_ids (self):
        return self._epoch_ids

    # Returns names of graphs directly from the netlist yaml file
    def graph_names (self):
        return self.yaml_file.root['graphs'].keys()
    # Returns names of queues directly from the netlist yaml file
    def queue_names (self):
        return self.yaml_file.root['queues'].keys()

    # Given a graph name, returns the epoch id directly from the runtime_data yaml file
    def graph_name_to_epoch_id (self, graph_name):
        return self.runtime_data_yaml.root["graph_to_epoch_map"][graph_name]["epoch_id"]
    # Given a graph name, returns the device id directly from the runtime_data yaml file
    def graph_name_to_device_id (self, graph_name):
        return self.runtime_data_yaml.root["graph_to_epoch_map"][graph_name]["target_device"] if graph_name in self.runtime_data_yaml.root["graph_to_epoch_map"] else None

    def epoch_id_to_graph_names (self, epoch_id):
        return self._epoch_id_to_graph_names_map[epoch_id] if epoch_id in self._epoch_id_to_graph_names_map else None
    def graph (self, graph_name):
        return self.graphs[graph_name]

    def get_graph_name(self, epoch_id, device_id):
        if device_id in self._map_graph_names:
            if epoch_id in self._map_graph_names[device_id]:
                return self._map_graph_names[device_id][epoch_id]
        return None

    def graph_by_epoch_and_device (self, epoch_id, device_id):
        graph_name = self.get_graph_name(epoch_id, device_id)
        if graph_name:
            return self.graph(graph_name)
        return None

    def device_graph_names(self):
        return self._map_graph_names

    def devices(self):
        return self.yaml_file.root["devices"]
    def queue(self, queue_name):
        return self._queues[queue_name]
    def queues(self):
        return self._queues

    # Determines the architecture
    def get_arch (self):
        if "arch_name" in self.runtime_data_yaml.root:
            return self.runtime_data_yaml.root["arch_name"]
        return None

    # Returns all device ids used by the graphs and the queues in the netlist
    def get_device_ids(self):
        device_ids = util.set (q["target_device"] for _, q in self.yaml_file.root["queues"].items())
        device_ids.update (util.set (g["target_device"] for _, g in self.yaml_file.root["graphs"].items()))
        return device_ids

    # Determines the netlist file path
    def get_netlist_path (self):
        if "netlist_path" in self.runtime_data_yaml.root:
            return self.runtime_data_yaml.root["netlist_path"]
        return None

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: {self.yaml_file.filepath}. Graphs({len(self.graph_names())}): {' '.join (self.graph_names())}"

    def __repr__(self):
        return self.__str__()
