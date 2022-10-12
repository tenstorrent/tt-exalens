command_metadata = {
    "short" : "c",
    "type" : "high-level",
    "expected_argument_count" : 2,
    "arguments" : "x y",
    "description" : "Shows summary for core 'x-y'"
}

import tt_util as util

def run(args, context, ui_state = None):
    noc0_loc = int(args[1]), int(args[2])
    current_device_id = ui_state["current_device_id"]
    current_device = context.devices[current_device_id]

    output_table = dict()

    # 1. Get epochs for core
    stream_regs = current_device.read_core_stream_registers (noc0_loc)
    core_epochs = util.set()
    for _, sr in stream_regs.items():
        stream_epoch = current_device.stream_epoch (sr)
        core_epochs.add (stream_epoch)

    output_table[f"epoch{'s' if len(core_epochs) > 1 else ''}"] = " ".join (list({ str(e) for e in core_epochs}))

    # Finally, print the table:
    util.print_columnar_dicts ([ output_table ], [f"Core {util.noc_loc_str(noc0_loc)}"])

    navigation_suggestions = []
    return navigation_suggestions