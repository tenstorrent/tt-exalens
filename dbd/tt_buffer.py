from tt_object import TTObject, TTObjectSet
import tt_util as util

# Constructed from epoch's pipegen.yaml. Contains information about a buffer.
class Buffer(TTObject):
    def __init__(self, data):
        data["core_coordinates"] = tuple(data["core_coordinates"])
        self.root = data
        self._id = self.root['uniqid']
        self.replicated = False

    # Renderer
    def __str__(self):
        r = self.root
        R = r['core_coordinates'][0]
        C = r['core_coordinates'][1]
        return f"{super().__str__()} {r['md_op_name']}:[{R},{C}]"
