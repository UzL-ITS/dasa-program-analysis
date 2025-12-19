import nodes.BaseNode

class AllocatedObjectNode(nodes.BaseNode):

    def exec(self):
        self.output = self.inputs['commit']
