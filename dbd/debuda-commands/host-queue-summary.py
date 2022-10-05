import tt_util as util
import tt_device
from tt_netlist import Queue
from tabulate import tabulate

command_metadata = {
          "long" : "host-queue",
          "short" : "hq",
          "expected_argument_count" : 0,
          "arguments_description" : ": prints Host queue summary"
        }

def run (cmd, context, ui_state):
    table = []

    for graph_name in context.netlist.graph_names():
        print (f"{util.CLR_INFO}HOST queues for graph {graph_name}{util.CLR_END}")
        graph = context.netlist.graph(graph_name)

        for buffer in graph.buffers:
            buffer_data = buffer.root
            if buffer_data["dram_io_flag_is_remote"] != 0:
                dram_addr = buffer_data['dram_addr']
                # bits 31,30 peer_id==0 means HOST
                if dram_addr >> 30 == 0:
                    chip_id = buffer_data['chip_id'][0]
                    rdptr = tt_device.SERVER_IFC.host_dma_read (chip_id, dram_addr)
                    wrptr = tt_device.SERVER_IFC.host_dma_read (chip_id, dram_addr + 4)
                    slot_size_bytes = buffer_data["size_tiles"] * buffer_data["tile_size"]
                    queue_size_bytes = slot_size_bytes * buffer_data["q_slots"]
                    occupancy = Queue.occupancy (buffer_data["q_slots"], wrptr, rdptr)

                    # IMPROVE: Duplicated from print_dram_queue_summary. Merge into one function.
                    input_buffer_op_name_list = []
                    for other_buffer_id in graph.get_connected_buffers([buffer.id()], 'src'):
                        input_buffer_op_name_list.append (graph.buffers.find_id(other_buffer_id).root["md_op_name"])
                    output_buffer_op_name_list = []
                    for other_buffer_id in graph.get_connected_buffers([buffer.id()], 'dest'):
                        output_buffer_op_name_list.append (graph.buffers.find_id(other_buffer_id).root["md_op_name"])

                    input_ops = f"{' '.join (input_buffer_op_name_list)}"
                    output_ops = f"{' '.join (output_buffer_op_name_list)}"

                    table.append ([ buffer.id(), buffer_data["md_op_name"], input_ops, output_ops, buffer_data["dram_buf_flag"], buffer_data["dram_io_flag"], f"0x{dram_addr:x}", f"{rdptr}", f"{wrptr}", occupancy, buffer_data["q_slots"], queue_size_bytes ])

    if len(table) > 0:
        print (tabulate(table, headers=["Buffer name", "Op", "Input Ops", "Output Ops", "dram_buf_flag", "dram_io_flag", "Address", "RD ptr", "WR ptr", "Occupancy", "Q slots", "Q Size [bytes]"] ))
    else:
        print ("No host queues found")
