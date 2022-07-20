from tt_object import TTObject

# Constructed from epoch's pipegen.yaml. Contains information about a pipe.
class Pipe(TTObject):
    def __init__(self, graph, data):
        self.root = data
        self._id = self.root['id']
        self.graph = graph

    # Accessors
    def inputs(self):
        return self.root['input_list']
    def outputs(self):
        return self.root['output_list']

    # Renderer
    def __str__(self):
        return f"{super().__str__()}, inputs: {self.inputs()}, outputs: {self.outputs()}"
