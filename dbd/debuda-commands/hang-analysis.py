from tabulate import tabulate
from dbd.tt_object import TTObjectSet
import tt_util as util
from tt_graph import Queue, Op
import tt_device

command_metadata = {
        "short" : "ha",
        "expected_argument_count" : 0,
        "arguments_description" : ": Prints operation summary"
    }

def run(args, context, ui_state = None):
    navigation_suggestions = []

    for device in context.devices:
        util.INFO (f"Analyzing device {device.id()}")
        all_stream_regs = device.read_all_stream_registers ()
        device_epochs = set()
        for loc, stream_regs in all_stream_regs.items():
            epoch_id = device.stream_epoch (stream_regs)
            device_epochs.add (epoch_id)

        device_graph_names = { context.netlist.epoch_id_to_graph_name (epoch_id) for epoch_id in device_epochs }
        util.INFO (f"  Device {device.id()} is running graph{'s:' if len(device_graph_names) > 1 else ':' } {' '.join (device_graph_names)}")

        # Returns if the Op wants more data on a given input
        def wants_more_data_from_input (all_stream_regs, graph, graph_device, op, input_queue):
            op_buffers = graph.get_buffers(op)
            # As not all streams have buf_id, and not all have pipe_id, we try to find either
            relevant_buffers = set()
            relevant_pipes = set()
            util.VERBOSE (f"Running wants_more_data_from_input for {op} on input {input_queue}")
            util.VERBOSE (f"  Found these buffers for {op}: {op_buffers}")
            for dest_buffer in op_buffers:
                if graph.is_dest_buffer (dest_buffer):
                    src_buffers = graph.get_fanin (dest_buffer)
                    src_buffers.keep (lambda b: b.root["md_op_name"] == input_queue.id())
                    for b in src_buffers:
                        relevant_buffers.add (dest_buffer)
                        pipes = graph.get_pipes_for_buffer (dest_buffer)
                        for p in pipes:
                            relevant_pipes.add (p)
            util.VERBOSE (f"  Found these source buffers for {input_queue}->{op} conection: {relevant_buffers}")
            relevant_streams = set (s for _, s in graph.streams.items() if s.get_buffer_id() in relevant_buffers or s.get_pipe_id() in relevant_pipes)

            if not relevant_streams:
                util.WARN (f"No relevant streams for buffers {' '.join (list(relevant_buffers))}")
            else:
                util.VERBOSE (f"  Found these relevant_streams for {input_queue}->{op} conection: {' '.join ([ s.__str__() for s in relevant_streams ])}")

            for s in relevant_streams:
                stream_data = all_stream_regs.get (s.on_chip_id(), None)
                if stream_data:
                    if not graph_device.is_stream_done (stream_data):
                        return True
            return False

        all_good = True
        column_format = [
            { 'key_name' : 'op',          'title': 'Op Name',   'formatter': None },
            { 'key_name' : 'input',       'title': 'Input Name',   'formatter': None },
            { 'key_name' : 'has_data',    'title': 'Input has data',   'formatter': lambda x: f"{util.CLR_RED}{x}{util.CLR_END}" },
            { 'key_name' : 'wants_data',  'title': 'Op wants data',   'formatter': lambda x: f"{util.CLR_RED}{x}{util.CLR_END}" },
        ]
        table=util.TabulateTable(column_format)
        table.rows = [ ]

        for graph_name in device_graph_names:
            util.INFO (f"    Analyzing graph {graph_name}")
            graph = context.netlist.graph(graph_name)
            graph_device = context.devices[context.netlist.graph_name_to_device_id(graph_name)]

            # Obtain all queues that feed all the operations within the graph
            input_queues = graph.get_fanin(graph.ops, Queue)
            # Keep only 'queue' type
            input_queues.keep (lambda q: q.root['type'] == 'queue')

            problematic_ops = TTObjectSet()
            for q in input_queues:
                # Get ops that the queue feeds
                ops = graph.get_fanout (input_queues, Op)

                # Check each q->ops connection
                q_data = q.root
                q_loc = q_data['loc']
                loc_array = q_data[q_loc]
                entries = q_data["entries"]
                for loc in loc_array:
                    # Get read and write pointers
                    if q_loc == 'dram':
                        dram_chan, dram_addr = loc[0], loc[1]
                        dram_noc0_loc = graph_device.DRAM_CHANNEL_TO_NOC0_LOC[dram_chan]
                        rdptr = graph_device.pci_read_xy (dram_noc0_loc[0], dram_noc0_loc[1], 0, dram_addr)
                        wrptr = graph_device.pci_read_xy (dram_noc0_loc[0], dram_noc0_loc[1], 0, dram_addr + 4)
                    elif q_loc == 'host':
                        rdptr = tt_device.PCI_IFC.host_dma_read (loc)
                        wrptr = tt_device.PCI_IFC.host_dma_read (loc + 4)
                    else:
                        util.WARN (f"Unknown queue loc: {q_loc}")
                        continue

                    input_has_data = Queue.occupancy(entries, wrptr, rdptr) > 0
                    for op in ops:
                        if not input_has_data:
                            op_wants_data = wants_more_data_from_input (all_stream_regs, graph, graph_device, op, q)
                            if op_wants_data:
                                table.add_row (None, { 'op' : op.id(), 'input' : q.id(), 'has_data': input_has_data, "wants_data": op_wants_data })
                                # util.WARN (f"Op {op}, input {q_name}: input_has_data {input_has_data} != {op_wants_data} op_wants_data")
                                problematic_ops.add (op)
                                all_good = False

            # Test other ops
            # visited_ops = set () # problematic_ops
            # ops_to_visit = set ()
            # for _, ops in graph_input_queues_to_op_map.items():
            #     for op_name in ops:
            #         ops_to_visit.add (op_name)

            # while ops_to_visit:
            #     new_ops_to_visit = set()
            #     for op_name in ops_to_visit:
            #         if op_name not in visited_ops:
            #             fanout_ops = graph.get_fanout (op_name)
            #             new_ops_to_visit = new_ops_to_visit.union (fanout_ops)
            #             for dest_op_name in fanout_ops:
            #                 op_wants_data = wants_more_data_from_input (all_stream_regs, graph, graph_device, dest_op_name, op_name)
            #                 print (f"Wants more data {op_wants_data}: {op_name} -> {dest_op_name} ")
            #                 buffers_and_pipes_and_streams = graph.get_buffers_and_pipes_and_streams (op_name, dest_op_name)
            #                 for b in buffers_and_pipes_and_streams:
            #                     print (b)
            #             visited_ops.add(op_name)
            #     ops_to_visit = new_ops_to_visit

        if table.rows:
            print (table)

        if all_good:
            util.INFO (f"No problems on device {device.id()}")

    return navigation_suggestions