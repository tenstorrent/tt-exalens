import tt_util as util
from tt_stream import Stream
from tt_object import TTObject, TTObjectSet
from tt_pipe import Pipe
from tt_buffer import Buffer
from tt_object import TTObject

# Queues
class Queue(TTObject):
    def __init__(self, name, data):
        self.root = data
        self._id = name
        self.output_ops = util.set() # set of names of queue's output_ops

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
        self._id = name
        self._graph_id = graph_id

# Class that represents a single graph within a netlist
# Contains all the information from graph's blob.yaml and pipegen.yaml
# Provides functions for graph traversal
class Graph(TTObject):
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
            op = Op (op_name, self.id(), self.root[op_name])
            self.ops.add(op)

    def load_pipegen_and_blob (self):
        # 1. Load pipegen_yaml
        self.buffers = TTObjectSet()
        self.pipes = TTObjectSet()

        input_buffers_ids = util.set()
        output_buffers_ids = util.set()

        for key, val in self.pipegen_yaml.items():
            if key == "graph_name":
                if self.id() != val:
                    util.WARN(f"Expected 'graph_name: {self.id()}' in {self.pipegen_yaml.id()}, but got 'graph_name: {val}'")
            elif "buffer" in key:
                b = Buffer(val)
                self.buffers.add(b)
                uniqid = val["uniqid"]
                for r in range (1, val["replicate"]): # Handle replicated buffers (see issue #326)
                    val["uniqid"] = uniqid + r * val["scatter_gather_num_tiles"]
                    b = Buffer(val)
                    self.buffers.add(b)
                    b.replicated = True # Mark the buffers we created by replication
            elif "pipe" in key:
                p = Pipe(val)
                self.pipes.add(p)
                input_buffers_ids.update (val['input_list'])
                output_buffers_ids.update (val['output_list'])
            else:
                raise RuntimeError(f"{self.pipegen_yaml.id()}: Cannot interpret {key}: {val}")

        for b in self.get_buffers (input_buffers_ids):
            b.is_input = True
        for b in self.get_buffers (output_buffers_ids):
            assert not hasattr (b, 'is_input'), f"Buffer {b.id()} is already set as input, but now it wants to be output"
            b.is_input = False

        # 2. Load blob_yaml
        self.streams = TTObjectSet()
        for key, val in self.blob_yaml.items():
            if key == "dram_blob":
                util.VERBOSE ("- Skipping dram_blob")
            elif key == "dram_perf_dump_blob":
                util.VERBOSE ("- Skipping dram_perf_dump_blob")
            elif key.startswith ("phase_"):
                phase_id = int (key[6:]) # Skip phase_
                for stream_designator, stream_data in val.items():
                    stream_data['phase_id'] = phase_id
                    s = Stream (stream_designator, stream_data)
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

    # Prints condensed information on a buffer (list)
    def print_buffer_info (self, buffer_id_list):
        if type(buffer_id_list) != list: buffer_id_list = [ buffer_id_list ] # If not a list, assume a single buffer id, and create a list from it
        for buffer_id in buffer_id_list:
            print (self.get_buffer (buffer_id))

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

    # Filters a list of buffers, to return only src or dest buffers
    def filter_buffers (self, buffer_list, filter):
        if filter == "src":
            return [ bid for bid in buffer_list if self.is_src_buffer(bid) ]
        elif filter == "dest":
            return [ bid for bid in buffer_list if self.is_dest_buffer(bid) ]
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
    def op (self, op_name):
        return self.ops[op_name]

    # Returns all pipes a buffer is a part of
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
    def get_op_buffers (self, op_name):
        op_buffers = set( b for b in self.buffers.items() if b.root["md_op_name"] == op_name )
        return op_buffers

    def input_queues_to_op_map (self, netlist_queues):
        graph_input_queues_to_op_map = TTObjectSet()
        for op in self.ops:
            for input in op.root["inputs"]:
                if input in netlist_queues:
                    if input not in graph_input_queues_to_op_map:
                        graph_input_queues_to_op_map[input] = TTObjectSet()
                    graph_input_queues_to_op_map[input].add(op)
        return graph_input_queues_to_op_map

    # # Return all immediate fan-out ops of a given op
    # def get_fanout (self, op_name):
    #     ret_set = util.set()
    #     for fanout_op_name, op in self.ops.items():
    #         if op_name in op.root["inputs"]:
    #             ret_set.add (fanout_op_name)
    #     return ret_set

    # # Return all immediate fan-out ops of a given op
    # def get_fanin (self, op_name):
    #     ret_set = util.set()
    #     op = self.ops[op_name]
    #     for fanin_op_name in op.root["inputs"]:
    #         if fanin_op_name in self.ops: # Make sure it is an Op in this graph
    #             ret_set.add (fanin_op_name)
    #     return ret_set

    # Get buffers on two connected ops op_A and op_B (A feeds B).
    # Returns a set of tuples (buff_A, buff_B, pipe_id)
    def get_buffers_and_pipes_and_streams (self, op_A, op_B):
        assert op_A in self.get_fanin(op_B) and op_B in self.get_fanout(op_A), f"{op_A} does not feed {op_B}"

        dest_buffer_ids = self.filter_buffers (set( b.id() for b in self.get_op_buffers (op_B) ), "dest")
        buffer_and_pipes = set ()

        util.VERBOSE (f"Running get_buffer_pars for {op_A}->{op_B}")
        for dest_buffer_id in dest_buffer_ids:
            for src_buffer_id in self.get_connected_buffers (dest_buffer_id, "src"):
                if self.buffers[src_buffer_id].root["md_op_name"] == A: # src buffer is in op A
                    pipes_with_src = set(self.get_pipes_for_buffer (src_buffer_id))
                    pipes_with_dest = set(self.get_pipes_for_buffer (dest_buffer_id))
                    # util.VERBOSE (f"pipes_with_src: {pipes_with_src}")
                    # util.VERBOSE (f"pipes_with_dest: {pipes_with_dest}")
                    pipes = pipes_with_dest.intersection(pipes_with_src)
                    util.VERBOSE (f"intersection: {pipes}")
                    for pipe_id in pipes:
                        print (f"--------- pipe {pipe_id} for {src_buffer_id}->{dest_buffer_id}")
                        assert src_buffer_id in self.pipes[pipe_id].root["input_list"], f"{src_buffer_id} not in input_list of {pipe_id}"
                        assert dest_buffer_id in self.pipes[pipe_id].root["output_list"], f"{dest_buffer_id} not in output_list of {pipe_id}"
                        src_stream_id = dest_stream_id = None
                        for stream_id, s in self.streams.items():
                            if s.get_buffer_id() == src_buffer_id:
                                print (f"Match stream_id {stream_id} by src_buffer_id {src_buffer_id}")
                            if s.get_buffer_id() == dest_buffer_id:
                                print (f"Match stream_id {stream_id} by dest_buffer_id {dest_buffer_id}")
                            if s.get_pipe_id() == pipe_id:
                                print (f"Match stream_id {stream_id} by pipe_id {pipe_id}")
                        # buffer_and_pipes.add ( (src_buffer_id, dest_buffer_id, pipe_id, src_stream_id, dest_stream_id ) )
        return buffer_and_pipes

    def get_buffers(self, where):
        ret_val = TTObjectSet()
        if type(where) == str or type(where) == int:
            expected_id = int(where)
            ret_val = TTObjectSet.fromiterable( { b for b in self.buffers if b.id() == expected_id } )
        elif type(where) == Pipe:
            ret_val = TTObjectSet.fromiterable( { b for b in self.buffers if b.id() in where.root['input_list'] or b.id() in where.root['output_list'] } )
        elif type(where) == Op:
            ret_val = TTObjectSet.fromiterable( { b for b in self.buffers if b.root["md_op_name"] == where.id() } )
        elif util.is_iterable(where):
            for o in where: ret_val.update (self.get_buffers (o))
        else:
            raise TypeError (f"Usupported object type: {type(where)}")
        return ret_val

    def get_streams (self, where):
        ret_val = TTObjectSet()
        if type(where) == tuple:
            # Looking by strema location tuple
            ret_val = TTObjectSet.fromiterable( { s for s in self.streams if s.id() == where } )
        elif util.is_iterable(where):
            for o in where: ret_val.update (self.get_streams (o))
        else:
            raise TypeError (f"Usupported object type: {type(where)}")
        return ret_val

    def get_pipes (self, where):
        ret_val = TTObjectSet()
        if type(where) == int:
            ret_val = TTObjectSet.fromiterable( { p for p in self.pipes if p.id() == where } )
        elif type(where) == Buffer:
            ret_val = TTObjectSet.fromiterable( { p for p in self.pipes if where.id() in p.root['input_list'] or where.id() in p.root['output_list'] } )
        elif util.is_iterable(where):
            for o in where: ret_val.update (self.get_pipes (o))
        else:
            raise TypeError (f"Usupported object type: {type(where)}")
        return ret_val

    def get_fanin_op_and_queue_level (self, where):
        if type(where) == Op:
            op_input_names = { i for i in where.root["inputs"] }
            # Fed by input queue
            ret_val = TTObjectSet.fromiterable ({ q for q in self.netlist.queues if q.id() in op_input_names })
            # Fed by another op
            ret_val.update (TTObjectSet.fromiterable ({ op for op in self.ops if op.id() in op_input_names }))
        elif type(where) == Queue:
            # Fed by input queue
            ret_val = (TTObjectSet.fromiterable ({ q for q in self.netlist.queues if q.id() == where.root["input"] }))
            # Fed by another op
            ret_val.update (TTObjectSet.fromiterable ({ op for op in self.ops if op.id() == where.root["input"] }))
        else:
            raise TypeError (f"Usupported object type: {type(where)}")
        return ret_val

    def get_fanout_op_and_queue_level (self, where):
        if type(where) == Op or type(where) == Queue:
            # Feeding output queue
            ret_val = TTObjectSet.fromiterable ({ q for q in self.netlist.queues if where.id() == q.root["input"] })
            # Feeding another op
            ret_val.update (TTObjectSet.fromiterable ({ op for op in self.ops if where.id() in op.root["inputs"] }))
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
        if type(where) == Op or type(where) == Queue:
            return self.get_fanin_op_and_queue_level(where)
        else:
            return self.get_fanin_buffer_level(where)

    def get_fanout (self, where):
        if type(where) == Op or type(where) == Queue:
            return self.get_fanout_op_and_queue_level(where)
        else:
            return self.get_fanout_buffer_level(where)

    # Test
    def _test_print(self):
        for _, b in self.buffers.items():
            print (f"{b}")
        for _, p in self.pipes.items():
            print (f"{p}")
        for stream, s in self.streams.items():
            print (f"{s}")
