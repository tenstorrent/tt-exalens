command_metadata = {
    "short" : "q",
    "expected_argument_count" : [0, 1],
    "arguments_description" : ": Prints summary of queues"
}

import tt_util as util
import tt_device
from tabulate import tabulate

def run(args, context, ui_state = None):
    table = []

    column_format = [
        { 'key_name' : 'entries',       'title': 'Entries',    'formatter': None },
        { 'key_name' : 'wrptr',         'title': 'Wr',         'formatter': None },
        { 'key_name' : 'rdptr',         'title': 'Rd',         'formatter': None },
        { 'key_name' : 'occupancy',     'title': 'Occ',        'formatter': lambda x: f"{util.CLR_BLUE}{x}{util.CLR_END}" },
        { 'key_name' : 'type',          'title': 'Type',       'formatter': None },
        { 'key_name' : 'target_device', 'title': 'Device',     'formatter': None },
        { 'key_name' : 'loc',           'title': 'Loc',        'formatter': None },
        { 'key_name' : None,            'title': 'Name',       'formatter': None },
        { 'key_name' : 'input',         'title': 'Input',      'formatter': None },
        { 'key_name' : 'outputs',       'title': 'Outputs',    'formatter': None},
        { 'key_name' : 'dram',          'title': 'Dram addr',  'formatter': None},
    ]

    table=util.TabulateTable(column_format)

    # Whether to print all DRAM positions or aggregate them
    expand_queue_positions = True

    for q_name, queue in context.netlist.queues.items():
        q_data = queue.root
        q_data["outputs"] = queue.outputs_as_str()
        if "dram" not in q_data:
            q_data["dram"] = '-'

        queue_positions = []
        if "host" in q_data:
            q_data["target_device"] = 'host'
            addr = q_data["host"][0]
            rdptr = tt_device.PCI_IFC.host_dma_read (addr)
            wrptr = tt_device.PCI_IFC.host_dma_read (addr + 4)
            # rdptr = wrptr = 0
            occupancy = (wrptr - rdptr) if wrptr >= rdptr else wrptr - (rdptr - 2 * entries)
            queue_positions.append ((rdptr, wrptr, occupancy))
        else:
            device_id = q_data["target_device"]
            device = context.devices[device_id]
            entries = q_data["entries"]
            for queue_position in range(len(q_data["dram"])):
                dram_place = q_data["dram"][queue_position]
                dram_chan = dram_place[0]
                dram_addr = dram_place[1]
                dram_loc = device.CHANNEL_TO_DRAM_LOC[dram_chan]
                rdptr = device.pci_read_xy (dram_loc[0], dram_loc[1], 0, dram_addr)
                wrptr = device.pci_read_xy (dram_loc[0], dram_loc[1], 0, dram_addr + 4)
                occupancy = (wrptr - rdptr) if wrptr >= rdptr else wrptr - (rdptr - 2 * entries)
                queue_positions.append ((rdptr, wrptr, occupancy))

        def queue_positions_to_str (queue_positions, i):
            mini = min(tup[i] for tup in queue_positions)
            maxi = max(tup[i] for tup in queue_positions)
            if mini != maxi: return mini
            else: return f"{mini}..{maxi}"

        num_queue_positions = len (queue_positions)
        add_suffix = num_queue_positions > 1
        if not expand_queue_positions:
            q_data["rdptr"]     = queue_positions_to_str(queue_positions, 0)
            q_data["wrptr"]     = queue_positions_to_str(queue_positions, 1)
            q_data["occupancy"] = queue_positions_to_str(queue_positions, 2)
            table.add_row (q_name if not add_suffix else f"{q_name}[0-{num_queue_positions}]", q_data)
        else:

            for i, qt in enumerate(queue_positions):
                q_data["rdptr"]     = qt[0]
                q_data["wrptr"]     = qt[1]
                q_data["occupancy"] = qt[2]
                table.add_row (q_name if not add_suffix else f"{q_name}[{i}]", q_data)

    print (table)