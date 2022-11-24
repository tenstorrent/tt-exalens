import tt_util as util
import tt_device
from tt_netlist import Queue
from tabulate import tabulate

command_metadata = {
    "long" : "epoch-queue",
    "type" : "dev",
    "short" : "eq",
    "expected_argument_count" : [ 0 ],
    "arguments" : "",
    "description" : "Prints Epoch queue summary"
}

# Prints epoch queues
def run (cmd, context, ui_state):
    graph_name = ui_state["current_graph_name"]
    device_id = context.netlist.graph_name_to_device_id(graph_name)
    epoch_device = context.devices[device_id]

    print (f"{util.CLR_INFO}Epoch queues for graph {graph_name}, device id {device_id}{util.CLR_END}")

    # From tt_epoch_dram_manager::tt_epoch_dram_manager and following the constants
    GridSizeRow = 16
    GridSizeCol = 16
    EPOCH_Q_NUM_SLOTS = 64
    EPOCH_Q_SLOT_SIZE = 32
    EPOCH_Q_SLOTS_OFFSET = 32
    epoch0_start_table_size_bytes = GridSizeRow*GridSizeCol*(EPOCH_Q_NUM_SLOTS*EPOCH_Q_SLOT_SIZE+EPOCH_Q_SLOTS_OFFSET)
    # DRAM_CHANNEL_CAPACITY_BYTES  = 1024 * 1024 * 1024
    DRAM_PERF_SCRATCH_SIZE_BYTES =   8 * 1024 * 1024
    # DRAM_HOST_MMIO_SIZE_BYTES    =  256 * 1024 * 1024
    reserved_size_bytes = DRAM_PERF_SCRATCH_SIZE_BYTES - epoch0_start_table_size_bytes

    chip_id = 0
    chip_id += 1

    dram_chan = 0 # CHECK: This queue is always in channel 0
    dram_loc = epoch_device.get_block_locations (block_type = "dram")[dram_chan]

    table=[]
    for loc in epoch_device.get_block_locations (block_type = "functional_workers"):
        x, y = loc[0], loc[1]
        EPOCH_QUEUE_START_ADDR = reserved_size_bytes
        offset = (GridSizeCol * y + x) * (EPOCH_Q_NUM_SLOTS*EPOCH_Q_SLOT_SIZE+EPOCH_Q_SLOTS_OFFSET)
        dram_addr = EPOCH_QUEUE_START_ADDR + offset
        rdptr = tt_device.SERVER_IFC.pci_read_xy (device_id, dram_loc[0], dram_loc[1], 0, dram_addr)
        wrptr = tt_device.SERVER_IFC.pci_read_xy (device_id, dram_loc[0], dram_loc[1], 0, dram_addr + 4)
        occupancy = Queue.occupancy (EPOCH_Q_NUM_SLOTS, wrptr, rdptr)
        if occupancy > 0:
            table.append ([ f"{util.noc_loc_str((x, y))}", f"0x{dram_addr:x}", f"{rdptr}", f"{wrptr}", occupancy ])

    if len(table) > 0:
        print (tabulate(table, headers=["Location", "Address", "RD ptr", "WR ptr", "Occupancy" ] ))
    else:
        print ("No epoch queues have occupancy > 0")

    util.WARN ("WIP: This results of this function need to be verified")
