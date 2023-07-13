import tt_util as util
from tt_stream import Stream
from tt_object import TTObject, TTObjectSet
from tt_pipe import Pipe
from tt_buffer import Buffer
from tt_object import TTObject

import itertools

# Queues
class Queue(TTObject):
    def __init__(self, name, data):
        self.root = data
        self._id = name
        self.output_ops = TTObjectSet()
        assert(self.is_dram() or self.is_host())
        assert(self.get_mem_addr())

    # Class functions
    def occupancy (entries, wrptr, rdptr):
        return (wrptr - rdptr) if wrptr >= rdptr else wrptr - (rdptr - 2 * entries)
    def to_str (channel, addr):
        return f"Ch%d-0x%x" % (channel, addr)

    # Accessors
    def outputs_as_str(self):
        ret_str = ""
        num_ops_fed_by_queue = len(self.output_ops)
        output_op_names = [ op.id() for op in self.output_ops ]
        if num_ops_fed_by_queue > 1:
            ret_str = f"[{num_ops_fed_by_queue}]: "
        if num_ops_fed_by_queue > 0:
            ret_str += ', '.join (output_op_names) if num_ops_fed_by_queue > 0 else ""
        return ret_str

    def get_loc(self):
        return self.root['loc']

    def get_mem_addr(self):
        loc = self.get_loc()
        if loc in self.root:
            addresses = self.root[loc]
            # Host Queues now have channels like DRAM. Here is workaround for back-compat period
            # to support host queues without mem channel, default to channel 0
            for idx, a in enumerate(addresses):
                if (self.is_host() and type(a) is int):
                    addresses[idx] = [0, a]

            for a in addresses:
                assert(type(a) is list)
            return addresses
        return []

    def is_dram(self):
        return self.get_loc() == 'dram'

    def is_host(self):
        return self.get_loc() == 'host'

    def entries(self):
        return self.root["entries"]

# Operations
class Op(TTObject):
    def __init__(self, graph, name, data):
        self.root = data
        self._id = name
        self.graph = graph

class Graph(TTObject):
    """Represents a single graph within a netlist.
    Contains all the information from graph's blob.yaml and pipegen.yaml.
    Provides functions for graph traversal.
    """

    # Some keys do not refer to operations, and we keep them here to be used when parsing
    non_op_keys = set (['target_device', 'input_count'])

    def __init__(self, netlist, name, root, pipegen_yaml, blob_yaml):
        self._id = name
        self.root = root # The entry in netlist file
        self.pipegen_yaml = pipegen_yaml
        self.blob_yaml = blob_yaml
        self.ops = TTObjectSet()
        self.netlist = netlist
        self.queues = netlist.queues # A shortcut to queues

        for op_name in self.op_names():
            op = Op (self, op_name, self.root[op_name])
            self.ops.add(op)

    def load_pipegen_and_blob (self):
        # 1. Load pipegen_yaml
        self.buffers = TTObjectSet()
        self.pipes = TTObjectSet()

        input_buffers_ids = util.set()
        output_buffers_ids = util.set()

        for key, val in self.pipegen_yaml.items():
            if key == "graph_names": # This key is pluralized in util.YamlFile
                if self.id() not in val:
                    util.WARN(f"Expected graph {self.id()} to be in {val}")
            elif "buffer" in key:
                b = Buffer(self, val)
                self.buffers.add(b)
                uniqid = val["uniqid"]
                for r in range (1, val["replicate"]): # Handle replicated buffers (see issue #326)
                    val["uniqid"] = uniqid + r * val["scatter_gather_num_tiles"]
                    b = Buffer(self, val)
                    self.buffers.add(b)
                    b.replicated = True # Mark the buffers we created by replication
            elif "pipe" in key:
                p = Pipe(self, val)
                self.pipes.add(p)
                input_buffers_ids.update (val['input_list'])
                output_buffers = val['output_list']
                if isinstance(output_buffers[0], list):
                    output_buffers = tuple(itertools.chain.from_iterable(output_buffers))
                output_buffers_ids.update (output_buffers)
            else:
                raise RuntimeError(f"{self.pipegen_yaml.id()}: Cannot interpret {key}: {val}")

        for b in self.get_buffers (input_buffers_ids):
            b.is_input = True
        for b in self.get_buffers (output_buffers_ids):
            b.is_output = True

        # 2. Load blob_yaml
        self.streams = TTObjectSet()
        for key, val in self.blob_yaml.items():
            if key == "dram_blob":
                util.VERBOSE ("- Skipping dram_blob")
            elif key == "dram_perf_dump_blob":
                util.VERBOSE ("- Skipping dram_perf_dump_blob")
            elif key == "overlay_blob_extra_size":
                util.VERBOSE ("- Skipping overlay_blob_extra_size")
            elif key.startswith ("phase_"):
                phase_id = int (key[6:]) # Skip phase_
                for stream_designator, stream_data in val.items():
                    stream_data['phase_id'] = phase_id
                    s = Stream (self, stream_designator, stream_data)
                    self.streams.add (s)
            else:
                raise RuntimeError(f"{self.blob_yaml.id()}: Cannot interpret {key}: {val}")


    RECURSION_DEPTH = 0 # Temporary/debug limit to prevent infinite recursion

    # Overriding this to support lazy loading of yaml files (this can take a lot of time)
    def __getattr__(self, name):
        if name in { "buffers", "pipes", "streams" }:
            self.load_pipegen_and_blob() # Lazy-loaded structures
        return object.__getattribute__(self, name)

    # Given a buffer list, find all buffers that are connected (pipegen.yaml)
    # connection can be src, dest, or srcdest (for either)
    def get_connected_buffers (self, buffer_id_list, connection="dest"):
        if type(buffer_id_list) != list: buffer_id_list = [ buffer_id_list ] # If not a list, assume a single buffer id, and create a list from it

        connected_buffers = []
        look_for_dest = "dest" in connection
        look_for_src = "src" in connection
        assert (look_for_src or look_for_dest), "Either src or dest must be present"
        for p in self.pipes:
            for b in buffer_id_list:
                if look_for_dest and b in p.root["input_list"]:
                    connected_buffers += p.root["output_list"]
                if look_for_src and b in p.root["output_list"]:
                    connected_buffers += p.root["input_list"]

        return list(set(connected_buffers))

    # Given a buffer list, find all RC coordinates of the cores where the buffers reside
    def get_buff_core_coordinates_rc (self, buffer_id_list):
        if type(buffer_id_list) != list: buffer_id_list = [ buffer_id_list ] # If not a list, assume a single buffer id, and create a list from it
        buff_cores = { b.root["core_coordinates"] for b in self.buffers if b.id() in buffer_id_list }
        return list (buff_cores)

    # Given a list of core coordinates, returns all buffers residing at those coordinates
    def get_core_buffers (self, core_coordinates_list_rc):
        if type(core_coordinates_list_rc) != list: core_coordinates_list_rc = [ core_coordinates_list_rc ] # If not a list, assume a single buffer id, and create a list from it

        buffer_set = util.set()
        for b in self.buffers:
            if b.root["core_coordinates"] in core_coordinates_list_rc:
                buffer_set.add (b.root["uniqid"])
        return list(buffer_set)

    # Checks if a given buffer is a source buffer (i.e. it shows up in the input_list of a pipe)
    def is_src_buffer(self, buffer_id):
        if type(buffer_id) == Buffer: buffer_id = buffer_id.id()
        for p in self.pipes:
            if buffer_id in p.root["input_list"]:
                return True
        return False

    # Checks if a given buffer is a destination buffer (i.e. it shows up in the output_list of a pipe)
    def is_dest_buffer(self, buffer_id):
        if type(buffer_id) == Buffer: buffer_id = buffer_id.id()
        for p in self.pipes:
            if buffer_id in p.root["output_list"]:
                return True
        return False

    # Return list of DRAM buffers
    def get_dram_buffers(self):
        input_buffers = []
        for bid, buffer in self.buffers.items():
            if buffer.root["dram_buf_flag"] != 0 or buffer.root["dram_io_flag"] != 0:
                input_buffers.append (bid)
        return input_buffers

    # Computes all buffers that are feeding into the buffers from buffer_id_list
    def fan_in_buffer_set(self, buffer_id_list, already_visited = util.set()):
        if Graph.RECURSION_DEPTH > 400:
            util.ERROR (f"Recursion limit reached")
            return util.set()
        Graph.RECURSION_DEPTH=Graph.RECURSION_DEPTH+1

        if type(buffer_id_list) != list: buffer_id_list = [ buffer_id_list ]
        if len (buffer_id_list) == 0:
            return util.set()

        # Get direct fan-ins
        buff_core_coords = self.get_buff_core_coordinates_rc (buffer_id_list)
        # print (buff_core_coords)
        if (255,255) in buff_core_coords: buff_core_coords.remove ((255,255)) # Exclude DRAM
        buffer_id_list = self.get_core_buffers (buff_core_coords)
        # print (f"Looking for direct fan ins of {buffer_id_list}")
        # print_buffer_info(buffer_id_list)
        direct_fan_ins = set(self.get_connected_buffers (buffer_id_list, "src"))
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

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: {self.id()}: Op count: {len (self.root.keys()) - len(Graph.non_op_keys)}, Input count: {self.input_count()}"

    # Returns an array of [r,c] pairs for the operation
    def get_op_rc_coords (self, op_name):
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
    def core_coord_to_full_op_name (self, rc_loc):
        op_name = self.core_coord_to_op_name(rc_loc)
        if op_name is not None:
            op = self.root[op_name]
            return f"{self.id()}/{op_name}:{op['type']}"
        else:
            return f"No op at [{rc_loc[0]},{rc_loc[1]}]"

    # Returns the op name mapped to a given RC location
    def core_coord_to_op_name (self, rc_loc):
        for op_name, op in self.root.items():
            if op_name not in ['target_device', 'input_count']:
                op_locations = self.get_op_rc_coords(op_name)
                if rc_loc in op_locations:
                    return op_name
        return None

    # API NOVEAU!
    def input_queues_to_op_map (self, netlist_queues):
        graph_input_queues_to_op_map = TTObjectSet()
        for op in self.ops:
            for input in op.root["inputs"]:
                if input in netlist_queues:
                    if input not in graph_input_queues_to_op_map:
                        graph_input_queues_to_op_map[input] = TTObjectSet()
                    graph_input_queues_to_op_map[input].add(op)
        return graph_input_queues_to_op_map

    # Get buffers on two connected ops op_A and op_B (A feeds B).
    # Returns a set of tuples (buff_A, buff_B, pipe_id)
    def get_buffers_and_pipes_and_streams (self, op_A, op_B):
        assert op_A in self.get_fanin(op_B) and op_B in self.get_fanout(op_A), f"{op_A} does not feed {op_B}"

        dest_buffers = TTObjectSet(b for b in self.get_buffers (op_B) if self.is_dest_buffer (b))
        buffer_and_pipes = set ()

        util.VERBOSE (f"Running get_buffer_pars for {op_A}->{op_B}")
        for dest_buffer in dest_buffers:
            dest_buffer_id = dest_buffer.id()
            for src_buffer in self.get_fanin (dest_buffer):
                if src_buffer.root["md_op_name"] == op_A.id(): # src buffer is in op A
                    pipes_with_src = self.get_pipes (src_buffer)
                    pipes_with_dest = self.get_pipes (dest_buffer)
                    # util.VERBOSE (f"pipes_with_src: {pipes_with_src}")
                    # util.VERBOSE (f"pipes_with_dest: {pipes_with_dest}")
                    pipes = pipes_with_dest.intersection(pipes_with_src)
                    util.VERBOSE (f"intersection: {pipes}")
                    for pipe in pipes:
                        print (f"--------- pipe {pipe.id()} for {src_buffer.id()}->{dest_buffer_id}")
                        assert src_buffer.id() in pipe.inputs(), f"{src_buffer.id()} not in input_list of {pipe.id()}"
                        assert dest_buffer.id() in pipe.outputs(), f"{dest_buffer.id()} not in output_list of {pipe.id()}"
                        src_stream_id = dest_stream_id = None
                        for s in self.streams:
                            if s.get_buffer_id() == src_buffer.id():
                                print (f"Match stream_id {s.id()} by src_buffer_id {src_buffer.id()}")
                            if s.get_buffer_id() == dest_buffer_id:
                                print (f"Match stream_id {s.id()} by dest_buffer_id {dest_buffer.id()}")
                            if s.get_pipe_id() == pipe.id():
                                print (f"Match stream_id {s.id()} by pipe.id() {pipe.id()}")
                        # buffer_and_pipes.add ( (src_buffer_id, dest_buffer_id, pipe_id, src_stream_id, dest_stream_id ) )
        return buffer_and_pipes

    def get_buffers(self, where):
        ret_val = TTObjectSet()
        if type(where) == str or type(where) == int:
            expected_id = int(where)
            ret_val.update( b for b in self.buffers if b.id() == expected_id )
        elif type(where) == Pipe:
            ret_val.update( b for b in self.buffers if b.id() in where.inputs() or b.id() in where.outputs() )
        elif type(where) == Op or type(where) == Queue:
            ret_val.update( b for b in self.buffers if b.root["md_op_name"] == where.id() )
        elif util.is_iterable(where):
            for o in where: ret_val.update (self.get_buffers (o))
        else:
            raise TypeError (f"Usupported object type: {type(where)}")
        return ret_val

    def get_streams (self, where):
        ret_val = TTObjectSet()
        if type(where) == tuple:
            # Looking by stream location tuple
            ret_val.update( s for s in self.streams if s.id() == where )
        elif type(where) == Buffer:
            ret_val.update( s for s in self.streams if s.get_buffer_id() == where.id() )
        elif type(where) == Pipe:
            ret_val.update( s for s in self.streams if s.get_pipe_id() == where.id() )
        elif util.is_iterable(where):
            for o in where: ret_val.update (self.get_streams (o))
        else:
            raise TypeError (f"Usupported object type: {type(where)}")
        return ret_val

    def get_ops_pipes(self):
        ret_val = dict()
        for op in self.ops:
            ret_val[op.id()] = []

        # connect pipes with op_names
        for pipe in self.pipes:
            for buffer in self.get_buffers(pipe):
                id = buffer.root["md_op_name"]
                if id in ret_val:
                    ret_val[id].append(pipe)

        res = dict()
        for key in ret_val.keys():
            s = TTObjectSet()
            s.update(ret_val[key])
            res[key] = s
        return res

    def get_pipes (self, where):
        ret_val = TTObjectSet()
        if type(where) == int:
            ret_val.update( p for p in self.pipes if p.id() == where )
        elif type(where) == Buffer:
            ret_val.update( p for p in self.pipes if where.id() in p.inputs() or where.id() in p.outputs() )
        elif type(where) == Op or type(where) == Queue:
            def is_ops (b):
                return b.root["md_op_name"]==where.id()
            for p in self.pipes:
                ret_val.update ( p for b in self.get_buffers(p) if is_ops(b) )
        elif util.is_iterable(where):
            for o in where: ret_val.update (self.get_pipes (o))
        else:
            raise TypeError (f"Usupported object type: {type(where)}")
        return ret_val

    def get_fanin_op_and_queue_level (self, where):
        if type(where) == Op:
            op_input_names = { i for i in where.root["inputs"] }
            # Fed by input queue
            ret_val = TTObjectSet( q for q in self.netlist.queues if q.id() in op_input_names )
            # Fed by another op
            ret_val.update ( op for op in self.ops if op.id() in op_input_names )
        elif type(where) == Queue:
            # Fed by input queue
            ret_val = TTObjectSet( q for q in self.netlist.queues if q.id() == where.root["input"] )
            # Fed by another op
            ret_val.update ( op for op in self.ops if op.id() == where.root["input"] )
        else:
            raise TypeError (f"Usupported object type: {type(where)}")
        return ret_val

    def get_fanout_op_and_queue_level (self, where):
        if type(where) == Op or type(where) == Queue:
            # Feeding output queue
            ret_val = TTObjectSet( q for q in self.netlist.queues if where.id() == q.root["input"] )
            # Feeding another op
            ret_val.update (TTObjectSet( op for op in self.ops if where.id() in op.root["inputs"] ))
        else:
            raise TypeError (f"Usupported object type: {type(where)}")
        return ret_val

    def get_fanin_buffer_level (self, where):
        if type(where) == Buffer:
            assert self.is_dest_buffer(where), "fanin is valid only for dest buffers"
            pipes = { p for p in self.pipes if where.id() in p.root["output_list"] }
            src_buffers = self.get_buffers (pipes)
            src_buffers.keep (self.is_src_buffer)
            return src_buffers
        else:
            raise TypeError (f"Usupported object type: {type(where)}")

    def get_fanout_buffer_level (self, where):
        if type(where) == Buffer:
            assert self.is_src_buffer(where), "fanout is valid only for src buffers"
            pipes = { p for p in self.pipes if where.id() in p.root["input_list"] }
            dest_buffers = self.get_buffers (pipes)
            dest_buffers.keep (self.is_dest_buffer)
            return dest_buffers
        else:
            raise TypeError (f"Usupported object type: {type(where)}")

    def get_fanin (self, where):
        ret_val = TTObjectSet()
        if util.is_iterable(where):
            for o in where: ret_val.update (self.get_fanin (o))
        elif type(where) == Op or type(where) == Queue:
            ret_val.update (self.get_fanin_op_and_queue_level(where))
        else:
            ret_val.update (self.get_fanin_buffer_level(where))
        return ret_val

    def get_fanout (self, where):
        ret_val = TTObjectSet()
        if util.is_iterable(where):
            for o in where: ret_val.update (self.get_fanout (o))
        elif type(where) == Op or type(where) == Queue:
            return self.get_fanout_op_and_queue_level(where)
        else:
            return self.get_fanout_buffer_level(where)
        return ret_val

    # Test
    def _test_print(self):
        for _, b in self.buffers.items():
            print (f"{b}")
        for _, p in self.pipes.items():
            print (f"{p}")
        for stream, s in self.streams.items():
            print (f"{s}")
