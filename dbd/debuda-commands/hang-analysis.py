from tabulate import tabulate
import tt_util as util

command_metadata = {
        "short" : "ha",
        "expected_argument_count" : 0,
        "arguments_description" : ": Prints operation summary"
    }

def run(args, context, ui_state = None):
    navigation_suggestions = []

    # 1. Print all current graphs
    for device in context.devices:
        all_stream_regs = device.read_all_stream_registers ()
        device_epochs = set()
        for loc, stream_regs in all_stream_regs.items():
            epoch_id = device.stream_epoch (stream_regs)
            device_epochs.add (epoch_id)

        device_graph_names = { context.netlist.epoch_id_to_graph_name (epoch_id) for epoch_id in device_epochs }
        util.INFO (f"Device {device.id()} is running graph{'s:' if len(device_graph_names) > 1 else ': ' } {' '.join (device_graph_names)}")

        for graph_name in device_graph_names:
            graph = context.netlist.graph(graph_name)
            graph_device = context.devices[context.netlist.graph_name_to_device_id(graph_name)]
            for op_name in graph.ops:
                op = graph.ops[op_name]
                for input in op.root["inputs"]:
                    if input in context.netlist.queues:
                        q = context.netlist.queues[input]
                        q_data = q.root
                        if "host" not in q_data and q_data['type'] == 'queue':
                            entries = q_data["entries"]
                            for queue_position in range(len(q_data["dram"])):
                                dram_place = q_data["dram"][queue_position]
                                dram_chan = dram_place[0]
                                dram_addr = dram_place[1]
                                dram_loc = graph_device.CHANNEL_TO_DRAM_LOC[dram_chan]
                                rdptr = graph_device.pci_read_xy (dram_loc[0], dram_loc[1], 0, dram_addr)
                                wrptr = graph_device.pci_read_xy (dram_loc[0], dram_loc[1], 0, dram_addr + 4)
                                occupancy = (wrptr - rdptr) if wrptr >= rdptr else wrptr - (rdptr - 2 * entries)
                                if occupancy == 0:
                                    util.WARN (f"Queue {q.id()} in an input to op {op.id()}, but has occupancy 0")

    return navigation_suggestions