"""Prints a graphical representation of a given device.

.. code-block::
   :caption: Example

        Current epoch:0(test_op) device:0 core:5-3 rc:2,4 stream:8 > c 1 1
        Core 1-1
        ----------  ------
        epochs      1023 0
        Current epoch:0(test_op) device:0 core:5-3 rc:2,4 stream:8 > d
        ==== Device 0
        00  +   +   +   +   .   .   .   .   .   .   .   .   Coordinate system: RC
        01  .   .   .   .   .   .   .   .   .   .   .   .   . - Functional worker
        02  .   .   +   .   +   .   +   .   .   .   .   .   + - Functional worker with configured stream(s)
        03  .   .   .   .   .   .   .   .   .   .   .   .
        04  .   .   .   .   .   .   .   .   .   .   .   .
        05  .   .   .   .   .   .   .   .   .   .   .   .
        06  .   .   .   .   .   .   .   .   .   .   .   .
        07  .   .   .   .   .   .   .   .   .   .   .   .
        08  .   .   .   .   .   .   .   .   .   .   .   .
        09  .   .   .   .   .   .   .   .   .   .   .   .
            00  01  02  03  04  05  06  07  08  09  10  11

"""
command_metadata = {
    "short" : "d",
    "long" : "device",
    "type" : "high-level",
    "expected_argument_count" : [0, 1, 2, 3],
    "arguments" : "device_id, axis coord, cell coord",
    "description" : "Shows a device summary. When no argument is supplied, it iterates through all devices used by the currently loaded netlist. Coords available: netlist, noc0, noc1, nocTr, nocVirt, die, tensix, none"
}

import tt_util as util

def run(args, context, ui_state = None):
    if len(args) > 1 and int(args[1]) != 0:
        device_id = int(args[1])
        if device_id not in context.devices:
            util.ERROR (f"Invalid device ID '{device_id}'. Valid devices IDs: %s" % [ d for d in context.devices ])
            return []
        devices_list = [ device_id ]
    else:
        devices_list = list(context.devices.keys())

    axis_coordinate = "netlist" # Default coordinate system
    if len(args) > 2:
        axis_coordinate = args[2]

    cell_val_coordinate = "nocTr" # Default cell contents
    if len(args) > 3:
        cell_val_coordinate = args[3]

    for device_id in devices_list:
        device = context.devices[device_id]
        util.INFO (f"==== Device {device.id()}")

        configured_streams = util.set()

        func_workers = device.get_block_locations (block_type = "functional_workers")
        for loc in func_workers:
            core_epoch = device.get_epoch_id(loc)
            for stream_id in range (64):
                phase_reg = device.get_stream_phase (loc, stream_id)
                epoch = core_epoch
                phase = phase_reg & 0x7fff

                if phase_reg > 0:
                    configured_streams.add (loc)
                    # util.INFO (f"Configured stream {stream_id} at {loc.full_str()} with epoch {epoch} and phase {phase}")

        blue_plus = f"{util.CLR_INFO}+{util.CLR_END}"
        def render_configured_stream(loc):
            if loc in configured_streams:
                return blue_plus
            else:
                return " "

        legend = [ "Legend:",
                f"  Axis in {axis_coordinate}" + (f", cell contents in {cell_val_coordinate} coordinates" if cell_val_coordinate!='none' else " coordinates"),
                f"  {blue_plus} Functional worker with configured stream(s)" ]

        print(device.render (legend=legend, axis_coordinate=axis_coordinate, cell_renderer=lambda loc: (loc.to_str (cell_val_coordinate) if cell_val_coordinate!='none' else "") + render_configured_stream(loc)))

    navigation_suggestions = []
    return navigation_suggestions