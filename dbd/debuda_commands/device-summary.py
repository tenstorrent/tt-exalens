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
    "expected_argument_count" : [0, 1],
    "arguments" : "device_id",
    "description" : "Shows a device summary. When no argument is supplied, it iterates through all devices."
}

import tt_util as util

def run(args, context, ui_state = None):
    runtime_data = context.server_ifc.get_runtime_data()

    if len(args) == 2:
        device_id = int(args[1])
        if device_id not in context.devices:
            util.ERROR (f"Invalid device ID '{device_id}'. Valid devices IDs: %s" % [ d for d in context.devices ])
            return []
        devices_list = [ device_id ]
    else:
        devices_list = list(context.devices.keys())

    for device_id in devices_list:
        device = context.devices[device_id]
        is_mmio_device = runtime_data and "chips_with_mmio" in runtime_data.root and device.id() in runtime_data.root['chips_with_mmio']
        util.INFO (f"==== Device {device.id()} {'(MMIO)' if is_mmio_device else ''}")

        configured_streams = util.set()
        for loc in device.get_block_locations (block_type = "functional_workers"):
            for stream_id in range (64):
                phase_reg = device.get_stream_phase (loc, stream_id)
                epoch = phase_reg >> 15
                phase = phase_reg & 0x7fff

                if phase_reg > 0:
                    configured_streams.add (loc)
        # print (configured_streams)
        emphasize_explanation = "Functional worker with configured stream(s)"
        print(device.render (options="rc", emphasize_noc0_loc_list = configured_streams, emphasize_explanation = emphasize_explanation))
        # print()
        # print(device.render (options="physical", emphasize_noc0_loc_list = configured_streams, emphasize_explanation = emphasize_explanation))
        # print()
        # print(device.render (options="noc0", emphasize_noc0_loc_list = configured_streams, emphasize_explanation = emphasize_explanation))

    navigation_suggestions = []
    return navigation_suggestions