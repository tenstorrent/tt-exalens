command_metadata = {
    "short" : "q",
    "expected_argument_count" : [0, 3],
    "arguments_description" : " [ queue_name, start_addr, num_bytes ]: Prints summary of queues. If arguments supplied, it will print contents"
}

import tt_util as util, tt_object
import tt_device
from tt_graph import Queue

def get_queue_data (context, queue):
    q_data = queue.root
    device_id = q_data["target_device"]
    device = context.devices[device_id]

    q_data["outputs"] = queue.outputs_as_str()
    if "dram" not in q_data:
        q_data["dram"] = '-'

    queue_locations = []
    if "host" in q_data: # This queues is on the host
        q_data["target_device"] = 'host'
        addr = q_data["host"][0]
        rdptr = tt_device.PCI_IFC.host_dma_read (addr)
        wrptr = tt_device.PCI_IFC.host_dma_read (addr + 4)
        entries = q_data["entries"]
        occupancy = Queue.occupancy(entries, wrptr, rdptr)
        queue_locations.append ((rdptr, wrptr, occupancy))
    else:
        device_id = q_data["target_device"]
        entries = q_data["entries"]
        for queue_position in range(len(q_data["dram"])):
            dram_place = q_data["dram"][queue_position]
            dram_chan = dram_place[0]
            dram_addr = dram_place[1]
            dram_loc = device.DRAM_CHANNEL_TO_NOC0_LOC[dram_chan]
            rdptr = device.pci_read_xy (dram_loc[0], dram_loc[1], 0, dram_addr)
            wrptr = device.pci_read_xy (dram_loc[0], dram_loc[1], 0, dram_addr + 4)
            occupancy = Queue.occupancy(entries, wrptr, rdptr)
            queue_locations.append ((rdptr, wrptr, occupancy))
    return q_data, queue_locations

def  print_word_array (word_array):
    for i in range(len(word_array)):
        print ("0x%08x " % word_array[i], end="")
        if i%8 == 7:
            print()

# Returns word array
def print_queue_contents (context, queue, start_addr, num_bytes):
    util.INFO (f"Contents of queue {queue.id()}:")
    q_data = queue.root
    device_id = q_data["target_device"]
    device = context.devices[device_id]
    word_array=[]

    if "host" in q_data: # This queues is on the host
        addr = q_data["host"][0]
        for i in range (num_bytes // 4):
            data = tt_device.PCI_IFC.host_dma_read (addr + start_addr + i * 4)
            word_array.append(data)
        print_word_array (word_array)
    else:
        device_id = q_data["target_device"]
        for queue_position in range(len(q_data["dram"])):
            dram_place = q_data["dram"][queue_position]
            dram_chan = dram_place[0]
            dram_addr = dram_place[1]
            print("At ch{dram_chan}-0x%x" % dram_addr)
            dram_loc = device.DRAM_CHANNEL_TO_NOC0_LOC[dram_chan]
            for i in range (num_bytes // 4):
                data = device.pci_read_xy (dram_loc[0], dram_loc[1], 0, dram_addr + start_addr + i * 4)
                word_array.append(data)
            print_word_array (word_array)

def print_single_queue_summary(args, context, ui_state = None):
    qid = args[1]
    queue = context.netlist.queues.find_id (qid)
    if not queue:
        util.WARN (f"Cannot find queue '{qid}'")
    else:
        q_data, queue_locations = get_queue_data(context, queue)
        util.INFO (f"Summary for queue '{qid}'")

def run(args, context, ui_state = None):
    queue_id = args[1] if len(args) > 1 else None

    column_format = [
        { 'key_name' : 'entries',       'title': 'Entries',      'formatter': None },
        { 'key_name' : 'wrptr',         'title': 'Wr',           'formatter': None },
        { 'key_name' : 'rdptr',         'title': 'Rd',           'formatter': None },
        { 'key_name' : 'occupancy',     'title': 'Occ',          'formatter': lambda x: f"{util.CLR_BLUE}{x}{util.CLR_END}" },
        { 'key_name' : 'type',          'title': 'Type',         'formatter': None },
        { 'key_name' : 'target_device', 'title': 'Device',       'formatter': None },
        { 'key_name' : 'loc',           'title': 'Loc',          'formatter': None },
        { 'key_name' : None,            'title': 'Name',         'formatter': None },
        { 'key_name' : 'input',         'title': 'Input',        'formatter': None },
        { 'key_name' : 'outputs',       'title': 'Outputs',      'formatter': None},
        { 'key_name' : 'dram',          'title': 'DRAM ch-addr', 'formatter': lambda x: ', '.join(Queue.to_str (e[0], e[1]) for e in x) if x!='-' else '-' },
    ]

    table=util.TabulateTable(column_format)

    # Whether to print all DRAM positions or aggregate them
    show_each_queue_dram_location = True

    for queue in context.netlist.queues:
        q_name = queue.id()
        if queue_id and queue_id != q_name: continue
        q_data, queue_locations = get_queue_data(context, queue)

        def aggregate_queue_locations_to_str (queue_locations, i):
            mini = min(tup[i] for tup in queue_locations)
            maxi = max(tup[i] for tup in queue_locations)
            return f"{mini}" if mini == maxi else f"{mini}..{maxi}"

        num_queue_locations = len (queue_locations)
        show_index = num_queue_locations > 1
        if show_each_queue_dram_location:
            for i, qt in enumerate(queue_locations):
                q_data["rdptr"]     = qt[0]
                q_data["wrptr"]     = qt[1]
                q_data["occupancy"] = qt[2]
                table.add_row (q_name if not show_index else f"{q_name}[{i}]", q_data)
        else: # Show only aggregate
            q_data["rdptr"]     = aggregate_queue_locations_to_str(queue_locations, 0)
            q_data["wrptr"]     = aggregate_queue_locations_to_str(queue_locations, 1)
            q_data["occupancy"] = aggregate_queue_locations_to_str(queue_locations, 2)
            table.add_row (q_name if not show_index else f"{q_name}[0..{num_queue_locations}]", q_data)

    print (table)

    if queue_id:
        print_queue_contents(context, queue, int(args[2], 0), int(args[3], 0))