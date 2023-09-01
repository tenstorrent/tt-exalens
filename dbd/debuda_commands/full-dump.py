"""Dumps all stream configuration at the currently selected core.

.. code-block::
   :caption: Example

        Tensix x=01,y=01 => stream 00 STREAM_ID = 0
        Tensix x=01,y=01 => stream 00 PHASE_AUTO_CFG_PTR (word addr) = 0
        Tensix x=01,y=01 => stream 00 CURR_PHASE = 0
        Tensix x=01,y=01 => stream 00 CURR_PHASE_NUM_MSGS_REMAINING = 0
        ...

"""

command_metadata = {
    "short" : "fd",
    "type" : "low-level",
    "expected_argument_count" : [ 0 ],
    "arguments" : "",
    "description" : "Performs a full stream dump at current x-y location."
}

def run (cmd, context, ui_state=None):
    ui_state['current_device'].full_dump_xy( ui_state['current_loc'] )