"""Shows debug registers for given cores.

.. code-block::
   :caption: Example

        Current epoch:0(test_op) device:0 core:1-1 rc:0,0 stream:8 > cdr 1 1
        === Debug registers for core 1-1 ===
        T0               T1               T2               FW
        -------  ------  -------  ------  -------  ------  -------  ------
        DBG[0]   0x0000  DBG[0]   0x0000  DBG[0]   0x0000  DBG[0]   0x0000
        DBG[1]   0x0000  DBG[1]   0x0000  DBG[1]   0x0000  DBG[1]   0x0000
        DBG[2]   0x0000  DBG[2]   0x0000  DBG[2]   0x0000  DBG[2]   0x0000
        DBG[3]   0x0000  DBG[3]   0x0000  DBG[3]   0x0000  DBG[3]   0x0000
        ...
"""
command_metadata = {
    "short" : "cdr",
    "type" : "low-level",
    "expected_argument_count" : [0, 2],
    "arguments" : "x y",
    "description" : "Prints the state of the debug registers for core 'x-y'. If coordinates are not supplied, it iterates through all cores."
}

import tt_util as util

def run(args, context, ui_state = None):
    current_device_id = ui_state["current_device_id"]
    current_device = context.devices[current_device_id]
    if len(args) == 3:
        core_locations = [ (int(args[1]), int(args[2])) ]
    else:
        core_locations = current_device.get_block_locations (block_type = "functional_workers")

    for core_loc in core_locations:
        print (f"=== Debug registers for core {util.noc_loc_str(core_loc)} ===")
        THREADS = ["T0", "T1", "T2", "FW"]

        # Get the register values
        debug_tables = current_device.get_debug_regs (core_loc)

        render_tables = [ dict() ] * len(THREADS)
        for thread_idx in range (len(THREADS)):
            for reg_id, reg_vals in enumerate(debug_tables[thread_idx]):
                render_tables[thread_idx][f"DBG[{2 * reg_id}]"] = "0x%04x" % reg_vals["lo_val"]
                render_tables[thread_idx][f"DBG[{2 * reg_id + 1}]"] = "0x%04x" % reg_vals["hi_val"]

        # Finally, print the table:
        util.print_columnar_dicts (render_tables, [*THREADS])

    navigation_suggestions = []
    return navigation_suggestions