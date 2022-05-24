command_metadata = {
    "short" : "d",
    "expected_argument_count" : [0, 1],
    "arguments_description" : "device_id: shows summary of a device. When no argument is supplied, shows summary of all devices"
}

import tt_util as util

def run(args, context, ui_state = None):
    if len(args) == 2:
        devices_list = [ (int(args[1])) ]
    else:
        devices_list = [ did for did in range (len(context.devices)) ]

    for device_id in devices_list:
        device = context.devices[device_id]
        util.INFO (f"==== Device {device.id()}")

        configured_streams = set()
        for loc in device.get_block_locations (block_type = "functional_workers"):
            for stream_id in range (64):
                phase_reg = device.get_stream_phase (loc[0], loc[1], stream_id)
                epoch = phase_reg >> 10
                phase = phase_reg & 0x3ff

                if phase_reg > 0:
                    configured_streams.add (loc)
        # print (configured_streams)
        emphasize_explanation = "Functional worker with configured stream(s)"
        print(device.render (options="rc", emphasize_noc0_loc_list = configured_streams, emphasize_explanation = emphasize_explanation))

    navigation_suggestions = []
    return navigation_suggestions