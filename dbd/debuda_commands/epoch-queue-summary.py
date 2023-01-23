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
    runtime_data = context.server_ifc.get_runtime_data()
    graph_name = ui_state["current_graph_name"]
    device_id = context.netlist.graph_name_to_device_id(graph_name)
    epoch_device = context.devices[device_id]
    distribtued_eq = bool(runtime_data.root.get("distribute_epoch_tables", 1))
    epoch_queue_in_dram = bool(runtime_data.root.get("epoch_queue_in_dram", 1))

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

    for blocktype in ["functional_workers"]: # , "eth"]:
        for loc in epoch_device.get_block_locations (block_type = blocktype):
            x, y = loc[0], loc[1]
            loc_is_dram = epoch_queue_in_dram or blocktype == "eth"
            coretype = "Worker" if blocktype == "functional_workers" else "Ethernet"
            if loc_is_dram:
                loc_str = "DRAM"
                if distribtued_eq:
                    dram_loc = epoch_device.get_t6_queue_location (loc) # FIXME - Hardcoded for GS, wrong for WH "eth" cores.
                EPOCH_QUEUE_START_ADDR = reserved_size_bytes
                offset = (GridSizeCol * y + x) * (EPOCH_Q_NUM_SLOTS*EPOCH_Q_SLOT_SIZE+EPOCH_Q_SLOTS_OFFSET)
                addr = EPOCH_QUEUE_START_ADDR + offset
                x, y = dram_loc[0], dram_loc[1] # Override core xy for reading.
            else:
                loc_str = "L1"
                addr = runtime_data.root['ncrisc_l1_epoch_q_base'] # runtime_data.root['eth_l1_epoch_q_base'] when erisc moves to L1.

            rdptr = tt_device.SERVER_IFC.pci_read_xy (device_id, x, y, 0, addr)
            wrptr = tt_device.SERVER_IFC.pci_read_xy (device_id, x, y, 0, addr + 4)
            occupancy = Queue.occupancy (EPOCH_Q_NUM_SLOTS, wrptr, rdptr)
            # if occupancy > 0:
            table.append ([f"{util.noc_loc_str((x, y))}", coretype, loc_str, f"0x{addr:x}", f"{rdptr}", f"{wrptr}", occupancy ])

    if len(table) > 0:
        print (tabulate(table, headers=["CoreLoc", "CoreType", "Location", "Address", "RD ptr", "WR ptr", "Occupancy" ] ))
    else:
        print ("No epoch queues have occupancy > 0")

    util.WARN ("WIP: This results of this function need to be verified")
