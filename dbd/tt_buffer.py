from tt_object import TTObject
import tt_util as util

# Constructed from epoch's pipegen.yaml. Contains information about a buffer.
class Buffer(TTObject):
    def __init__(self, data):
        data["core_coordinates"] = tuple(data["core_coordinates"])
        self.root = data
        self.input_of_pipe_ids = set ()
        self.output_of_pipe_ids = set ()
        self.replicated = False
        self._id = self.root['uniqid']

    # Accessors
    def is_op_input (self):
        return len(self.output_of_pipe_ids) > 0
    def is_op_output (self):
        return len(self.input_of_pipe_ids) > 0
    # Renderer
    def __str__(self):
        r = self.root
        return f"{super().__str__()}, RC coord: [{r['core_coordinates'][0]}, {r['core_coordinates'][1]}]"
