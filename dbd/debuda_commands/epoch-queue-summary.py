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
    arch_name = runtime_data.root.get('arch_name').upper()
    graph_name = ui_state["current_graph_name"]
    device_id = context.netlist.graph_name_to_device_id(graph_name)
    epoch_device = context.devices[device_id]
    distribtued_eq = bool(runtime_data.root.get("distribute_epoch_tables", 1))
    EPOCH_Q_NUM_SLOTS = runtime_data.root.get('epoch_queue_num_slots', 64)
    DRAM_EPOCH_METADATA_LIMIT = runtime_data.root.get('dram_epoch_metadata_limit', 8 * 1024 * 1024)
    grid_size_row = runtime_data.root.get("grid_size_row", 12)
    grid_size_col = runtime_data.root.get("grid_size_col", 10)

    print (f"{util.CLR_INFO}Epoch queues for graph {graph_name}, device id {device_id} with EPOCH_Q_NUM_SLOTS: {EPOCH_Q_NUM_SLOTS} {util.CLR_END}")

    # From tt_epoch_dram_manager::tt_epoch_dram_manager and following the constants
    EPOCH_Q_SLOT_SIZE = 32
    EPOCH_Q_SLOTS_OFFSET = 32
    EPOCH_QUEUE_SIZE_BYTES = grid_size_row*grid_size_col*(EPOCH_Q_NUM_SLOTS*EPOCH_Q_SLOT_SIZE+EPOCH_Q_SLOTS_OFFSET)
    EPOCH_QUEUE_START_ADDR = DRAM_EPOCH_METADATA_LIMIT - EPOCH_QUEUE_SIZE_BYTES

    dram_chan = 0 # CHECK: This queue is always in channel 0
    dram_loc = epoch_device.get_block_locations (block_type = "dram")[dram_chan]

    table=[]
    loc_str = "DRAM"

    for blocktype in ["functional_workers", "eth"]:
        coretype = "Worker" if blocktype == "functional_workers" else "Ethernet"
        for x, y in epoch_device.get_block_locations (block_type = blocktype):
            if distribtued_eq:
                dram_loc = epoch_device.get_t6_queue_location(arch_name, {'x': x, 'y': y})

            offset = (grid_size_col * y + x) * (EPOCH_Q_NUM_SLOTS*EPOCH_Q_SLOT_SIZE+EPOCH_Q_SLOTS_OFFSET)
            addr = EPOCH_QUEUE_START_ADDR + offset
            dx, dy = dram_loc['x'], dram_loc['y'] # mapped dram location for this core

            rdptr = tt_device.SERVER_IFC.pci_read_xy (device_id, dx, dy, 0, addr) & 0xffff
            wrptr = tt_device.SERVER_IFC.pci_read_xy (device_id, dx, dy, 0, addr + 4) & 0xffff
            occupancy = Queue.occupancy (EPOCH_Q_NUM_SLOTS, wrptr, rdptr)
            if occupancy > 0:
                table.append ([f"{util.noc_loc_str((x, y))}", coretype, loc_str, f"{util.noc_loc_str((dx, dy))}", f"0x{addr:x}", f"{rdptr}", f"{wrptr}", occupancy])

    if len(table) > 0:
        print (tabulate(table, headers=["T6", "CoreType", "Location", "DRAM", "Address", "RD ptr", "WR ptr", "Occupancy"] ))
    else:
        print ("No epoch queues have occupancy > 0")
