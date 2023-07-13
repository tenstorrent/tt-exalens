"""
.. code-block::
   :caption: Example

        Current epoch:0(test_op) device:0 core:1-1 rc:0,0 stream:8 > q
        Entries    Wr    Rd    Occ  Type      Device  Loc    Name    Input    Outputs    DRAM ch-addr
        ---------  ----  ----  -----  ------  --------  -----  ------  -------  ---------  --------------
                1     1     0      1  queue          0  dram   input0  HOST     f_op0      Ch0-0x30000000
                1     1     0      1  queue          0  dram   input1  HOST     f_op1      Ch0-0x31000000
                1     0     0      0  queue          0  dram   output  d_op3               Ch0-0x32000000
"""

command_metadata = {
    "short" : "q",
    "type" : "high-level",
    "expected_argument_count" : [0, 1, 3],
    "arguments" : "queue_name start_addr num_bytes",
    "description" : "Prints summary of all queues. If the arguments are supplied, it prints given queue contents."
}

import tt_util as util, tt_object
import tt_device
from tt_graph import Queue

def get_queue_data (context, queue):
    q_data = queue.root
    q_data["outputs"] = queue.outputs_as_str()
    queue_locations = []
    if queue.is_host(): # This queues is on the host
        q_data["ch_addr"] = q_data["host"]
        target_device = int (q_data["target_device"])
        for queue_position in range(len(q_data["host"])):
            dram_place = q_data["host"][queue_position]
            if (type(dram_place) is list):
                host_chan = dram_place[0]
                host_addr = dram_place[1]
            elif (type(dram_place) is int):
                # Host Queues back-compat support for no mem-channel, default to 0x0.
                host_chan = 0
                host_addr = dram_place[0]
            else:
                assert False , f"Unexpected Host queue addr format"

            rdptr = tt_device.SERVER_IFC.host_dma_read (target_device, host_addr, host_chan)
            wrptr = tt_device.SERVER_IFC.host_dma_read (target_device, host_addr + 4, host_chan)
            entries = q_data["entries"]
            occupancy = Queue.occupancy(entries, wrptr, rdptr)
            queue_locations.append ((rdptr, wrptr, occupancy))
    else:
        device_id = q_data["target_device"]
        device = context.devices[device_id]
        entries = q_data["entries"]
        q_data["ch_addr"] = q_data["dram"]
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

# Returns word array
def read_queue_contents (context, queue, start_addr, num_bytes):
    util.INFO (f"Contents of queue {queue.id()}:")
    num_words = (num_bytes-1) // 4 + 1
    ret_val = tt_object.TTObjectSet()
    q_data = queue.root
    device_id = q_data["target_device"]
    device = context.devices[device_id]

    if "host" in q_data: # This queues is on the host
        for queue_position in range(len(q_data["host"])):
            dram_place = q_data["host"][queue_position]

            if (type(dram_place) is list):
                host_chan = dram_place[0]
                host_addr = dram_place[1]
            elif (type(dram_place) is int):
                # Host Queues back-compat support for no mem-channel, default to 0x0.
                host_chan = 0
                host_addr = dram_place[0]
            else:
                assert False , f"Unexpected Host queue addr format"

            da = tt_object.DataArray(f"host-0x{host_addr:08x}-ch{host_chan}-{num_words * 4}")
            for i in range (num_words):
                data = tt_device.SERVER_IFC.host_dma_read (device_id, host_addr + start_addr + i * 4, host_chan)
                da.data.append(data)
            ret_val.add (da)
    else:
        for queue_position in range(len(q_data["dram"])):
            dram_place = q_data["dram"][queue_position]
            dram_chan = dram_place[0]
            addr = dram_place[1]
            dram_loc = device.DRAM_CHANNEL_TO_NOC0_LOC[dram_chan]
            da = tt_object.DataArray(f"dram-ch{dram_chan}-0x{addr:08x}-{num_words * 4}")
            for i in range (num_words):
                data = device.pci_read_xy (dram_loc[0], dram_loc[1], 0, addr + start_addr + i * 4)
                da.data.append(data)
            ret_val.add (da)
    return ret_val

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
        { 'key_name' : 'ch_addr',       'title': 'HOST/DRAM ch-addr', 'formatter': lambda x: ', '.join(Queue.to_str (e[0], e[1]) for e in x) if x!='-' else '-' },
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
        queue = context.netlist.queues.find_id(queue_id)
        queue_start_addr = int(args[2], 0) if len(args) > 2 else 0
        queue_num_bytes = int(args[3], 0) if len(args) > 3 else 128
        alignment_bytes=queue_start_addr % 4
        queue_start_addr-=alignment_bytes
        queue_num_bytes+=alignment_bytes

        data = read_queue_contents(context, queue, queue_start_addr, queue_num_bytes)
        # for d in data:
        #     d.to_bytes_per_entry(1)
        print (data)