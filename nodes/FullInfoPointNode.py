import nodes.BaseNode

class FullInfoPointNode(nodes.BaseNode):

    def exec(self):
        key = [x for x in self.inputs.keys()][0]
        self.output = self.inputs[key]