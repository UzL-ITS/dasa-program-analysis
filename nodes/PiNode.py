import nodes.BaseNode

class PiNode(nodes.BaseNode):


    def exec(self):
        self.output = self.inputs['object']