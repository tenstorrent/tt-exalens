import sys, os
from dbd.tt_object import TTObjectSet
import tt_util as util, tt_device
from tt_graph import Graph, Queue

# Wrapper for Buda run netlist.yaml and, currently, runtime_data.yaml files
class Netlist:
    def load_netlist_data (self):
        # 1. Cache epoch id, device id and graph names
        self.epoch_id_to_graph_names_map = dict()
        self._epoch_ids = util.set()
        self.__map_graph_names = dict()

        for graph_name in self.graph_names():
            epoch_id = self.graph_name_to_epoch_id(graph_name)
            device_id = self.graph_name_to_device_id(graph_name)
            if device_id not in self.__map_graph_names:
                self.__map_graph_names[device_id] = dict()
            self.__map_graph_names[device_id][epoch_id] = graph_name

            # assert (epoch_id not in self._epoch_ids)  # We do not support multiple graphs in the same epoch
            self._epoch_ids.add (epoch_id)

            if epoch_id not in self.epoch_id_to_graph_names_map:
                self.epoch_id_to_graph_names_map[epoch_id] = util.set()
            self.epoch_id_to_graph_names_map[epoch_id].add (graph_name)

        self._epoch_ids = list (self._epoch_ids)
        self._epoch_ids.sort()

        # 2. Load queues
        self.queues = TTObjectSet()
        for queue_name in self.queue_names():
            queue = Queue (queue_name, self.yaml_file.root["queues"][queue_name])
            self.queues.add (queue)

    # Initializes, but does not yet load pipegen and blob files
    def load_graphs (self, rundir):
        self.epoch_to_pipegen_yaml_file = dict()
        self.epoch_to_blob_yaml_file = dict()
        self.__map_graphs = dict()
        self.graphs = TTObjectSet()
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
            self.graphs.add(g)
            self.__map_graphs[graph_name] = g

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

        # 4. Store the Ops for input queues
        all_queue_ids = TTObjectSet( q.id() for q in self.queues )
        for graph in self.graphs:
            for op in graph.ops:
                for input in op.root["inputs"]:
                    if input in all_queue_ids:
                        self.queues.find_id(input).output_ops.add (op)

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
    def epoch_id_to_graph_names (self, epoch_id):
        return self.epoch_id_to_graph_names_map[epoch_id] if epoch_id in self.epoch_id_to_graph_names_map else None
    def graph (self, graph_name):
        if graph_name in self.__map_graphs:
            return self.__map_graphs[graph_name]
        return None

    def get_graph_name(self, epoch_id, device_id):
        if device_id in self.__map_graph_names:
            if epoch_id in self.__map_graph_names[device_id]:
                return self.__map_graph_names[device_id][epoch_id]
        return None

    def graph_by_epoch_and_device (self, epoch_id, device_id):
        graph_name = self.get_graph_name(epoch_id, device_id)
        if graph_name:
            return self.graph(graph_name)
        return None

    def device_graph_names(self):
        return self.__map_graph_names

    def devices(self):
        return self.yaml_file.root["devices"]
    def queue(self, queue_name):
        return self.queues[queue_name]

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
