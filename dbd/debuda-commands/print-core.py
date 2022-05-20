command_metadata = {
    "short" : "c",
    "expected_argument_count" : 2,
    "arguments_description" : "x y : show core 'x-y'"
}

import tt_device, tt_util as util

# Prints all information on a stream
def run(args, context, ui_state = None):
    x, y = int(args[1]), int(args[2])
    current_device_id = ui_state["current_device_id"]
    current_device = context.devices[current_device_id]

    output_table = dict()

    # 1. Get epochs for core
    stream_regs = current_device.read_core_stream_registers ((x,y))
    core_epochs = set()
    for _, sr in stream_regs.items():
        stream_epoch = current_device.stream_epoch (sr)
        core_epochs.add (stream_epoch)

    output_table[f"epoch{'s' if len(core_epochs) > 1 else ''}"] = " ".join (list({ str(e) for e in core_epochs}))

    # 2. Get the debug registers
    DEBUG_MAILBOX_BUF_BASE  = 112
    DEBUG_MAILBOX_BUF_SIZE  = 64
    THREADS = ["T0", "T1", "T2", "FW"]

    debug_tables = [ dict() ] * len (THREADS)
    mailbox_core_vals = { }
    for thread_idx, thread in enumerate(THREADS):
        mailbox_threads_vals = []
        for idx in range(DEBUG_MAILBOX_BUF_SIZE // 4):
            reg_addr = DEBUG_MAILBOX_BUF_BASE + thread_idx * DEBUG_MAILBOX_BUF_SIZE + idx * 4
            val = tt_device.pci_read_xy(current_device_id, x, y, 0, reg_addr)
            lo_val = val & 0xffff
            hi_val = (val >> 16) & 0xffff
            mailbox_core_vals[thread] = mailbox_threads_vals
            debug_tables[thread_idx][f"DBG[{2 * idx}]"] = "0x%04x" % lo_val
            debug_tables[thread_idx][f"DBG[{2 * idx + 1}]"] = "0x%04x" % hi_val


    # Finally, print the table:

    util.print_columnar_dicts ([ output_table ] + debug_tables, [f"Core {x}-{y}", *THREADS])

    navigation_suggestions = []
    return navigation_suggestions