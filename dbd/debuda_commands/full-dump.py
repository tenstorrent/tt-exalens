command_metadata = {
          "long" : "full-dump",
          "short" : "fd",
          "expected_argument_count" : 0,
          "arguments_description" : ": performs a full dump at current x-y"
        }

def run (cmd, context, ui_state=None):
    ui_state['current_device'].full_dump_xy( (ui_state['current_x'], ui_state['current_y']) )