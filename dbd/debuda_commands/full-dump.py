command_metadata = {
    "short" : "fd",
    "type" : "low-level",
    "expected_argument_count" : [ 0 ],
    "arguments" : "",
    "description" : "Performs a full stream dump at current x-y location."
}

def run (cmd, context, ui_state=None):
    ui_state['current_device'].full_dump_xy( (ui_state['current_x'], ui_state['current_y']) )