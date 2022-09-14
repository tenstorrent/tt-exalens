command_metadata = {
    "short" : "d",
    "expected_argument_count" : [0, 1],
    "arguments_description" : "device_id: shows summary of a device. When no argument is supplied, shows summary of all devices"
}

import tt_util as util

def run(args, context, ui_state = None):
    runtime_data = context.server_ifc.get_runtime_data().root

    if len(args) == 2:
        device_id = int(args[1])
        if device_id not in context.devices:
            util.ERROR (f"Invalid device id '{device_id}'")
            return []
        devices_list = [ device_id ]
    else:
        devices_list = list(context.devices.keys())

    for device_id in devices_list:
        device = context.devices[device_id]
        util.INFO (f"==== Device {device.id()} {'(MMIO)' if device.id() in runtime_data['chips_with_mmio'] else ''}")

        configured_streams = util.set()
        for loc in device.get_block_locations (block_type = "functional_workers"):
            for stream_id in range (64):
                phase_reg = device.get_stream_phase (loc, stream_id)
                epoch = phase_reg >> 10
                phase = phase_reg & 0x3ff

                if phase_reg > 0:
                    configured_streams.add (loc)
        # print (configured_streams)
        emphasize_explanation = "Functional worker with configured stream(s)"
        print(device.render (options="rc", emphasize_noc0_loc_list = configured_streams, emphasize_explanation = emphasize_explanation))
        # print(device.render (options="physical", emphasize_noc0_loc_list = configured_streams, emphasize_explanation = emphasize_explanation))
        # print(device.render (options="noc0", emphasize_noc0_loc_list = configured_streams, emphasize_explanation = emphasize_explanation))

    navigation_suggestions = []
    return navigation_suggestions