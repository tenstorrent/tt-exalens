from tt_object import TTObject, TTObjectIDDict
import tt_util as util
from tt_stream import Stream
from tt_buffer import Buffer
from tt_pipe import Pipe
import itertools

class TemporalEpoch(TTObject):
    def __init__(self, id, netlist, pipegen_filename, blob_filename):
        # Pipegen.yaml is a special case since it contains multiple documents (separated by ---). It also depends on the
        # order of the documents. Each graph starts with "graph_name:" followed by graph's buffers. After all buffers are
        # loaded, we have an array of pipes.
        def post_process_pipegen_yaml (root):
            new_root = {}
            graphs = {}
            pipes = {}
            current_graph_name = None
            for i in root:
                if "graph_name" in i:
                    current_graph_name = i["graph_name"]
                    graphs[current_graph_name] = {}
                elif len(i.keys()) == 1 and "buffer" in list(i.keys())[0]: # Special case for buffers
                    graphs[current_graph_name] = { **graphs[current_graph_name], **i }
                elif len(i.keys()) == 1 and "pipe" in list(i.keys())[0]: # Special case for buffers
                    pipes = { **pipes, **i }
                else:
                    raise RuntimeError(f"Cannot interpret {i} in file {self.pipegen_yaml.filepath}")
            new_root["graphs"] = graphs
            new_root["pipes"] = pipes
            return new_root

        self._id = id
        self.netlist = netlist # Store netlist to have access to graphs.
        self.pipegen_yaml = util.YamlFile (pipegen_filename, post_process_pipegen_yaml)
        self.blob_yaml = util.YamlFile (blob_filename)
        self.graphs = None

    # Lazy loading of pipegen and blob files
    def load_pipegen (self):
        self.pipes = TTObjectIDDict()

        pipes = self.pipegen_yaml.root["pipes"]

        for g_name, pipegen_graph in self.pipegen_yaml.root["graphs"].items():
            netlist_graph = self.netlist.graphs[g_name]
            netlist_graph.buffers = TTObjectIDDict()
            netlist_graph.temporal_epoch = self
            self.graphs.add (netlist_graph)

            for bid, val in pipegen_graph.items():
                b = Buffer(netlist_graph, val)
                netlist_graph.buffers.add (b)
                uniqid = val["uniqid"]
            for pid, val in pipes.items():
                p = Pipe(self, val)
                self.pipes[p.id()] = p
                output_buffers = val['output_list']
                if isinstance(output_buffers[0], list):
                    output_buffers = tuple(itertools.chain.from_iterable(output_buffers))

        def find_buffer_by_uniqid (uniqid):
            for _, g in self.graphs.items():
                if uniqid in g.buffers:
                    return g.buffers[uniqid]
            return None

        # Cache buffer to pipe and vice versa mapping
        for pipe_id, pipe in self.pipes.items():
            for input_buffer_id in pipe.root["input_list"]:
                input_buffer_id = input_buffer_id - (input_buffer_id % 1000000000) # Clear the offset
                b = find_buffer_by_uniqid(input_buffer_id)
                if b is None:
                    assert b, "Cannot find buffer with uniqid {input_buffer_id}"
                b.input_of_pipes.add (pipe)
                pipe.input_buffers.add (b)
            for output_buffer_id_or_list in pipe.root["output_list"]:
                if type(output_buffer_id_or_list) == list:
                    # Flatten the list of lists
                    for buf_id in output_buffer_id_or_list:
                        b = find_buffer_by_uniqid(buf_id)
                        b.output_of_pipes.add (pipe)
                        pipe.output_buffers.add (b)
                else: # This is a single buffer
                    b = find_buffer_by_uniqid(output_buffer_id_or_list)
                    b.output_of_pipes.add (pipe)
                    pipe.output_buffers.add (b)

    def load_blob (self):
        self.streams = TTObjectIDDict()
        for key, val in self.blob_yaml.items():
            if key == "dram_blob":
                util.VERBOSE ("- Skipping dram_blob")
            elif key == "dram_perf_dump_blob":
                util.VERBOSE ("- Skipping dram_perf_dump_blob")
            elif key == "overlay_blob_extra_size":
                util.VERBOSE ("- Skipping overlay_blob_extra_size")
            elif key.startswith ("phase_"):
                phase_id = int (key[6:]) # Skip "phase_" string to get the id
                for stream_designator, stream_data in val.items():
                    phase_id = phase_id & 0xFFFFFFFF # Lower 32 bits are phase, upper 32 bits are epoch
                    stream_data['phase_id'] = phase_id
                    s = Stream (self, stream_designator, stream_data)
                    self.streams.add (s)

                    # # Add the stream to the corresponding buffer
                    # if "buf_id" in s.root:
                    #     if s.root["buf_id"] not in self.buffers:
                    #         util.WARN (f"Stream {s.id()} refers to buffer {s.root['buf_id']} which is not in pipegen.yaml")
                    #     if self.buffers[s.root["buf_id"]].stream_id is not None:
                    #         util.WARN (f"Stream {s.id()} refers to buffer {s.root['buf_id']} which is already in use by stream {self.buffers[s.root['buf_id']].stream_id}")
                    #     self.buffers[s.root["buf_id"]].stream_id = s.id()
            else:
                raise RuntimeError(f"{self.blob_yaml.id()}: Cannot interpret {key}: {val}")

    def __getattr__(self, name):
        if name == "pipes":
            self.load_pipegen()
        elif name == "streams":
            self.load_blob()
        return object.__getattribute__(self, name)

