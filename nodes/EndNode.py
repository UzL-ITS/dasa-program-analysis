import nodes.BaseNode

class EndNode(nodes.BaseNode):

    def exec(self):
        self.output = self.inputs['next']
