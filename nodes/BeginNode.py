import nodes.BaseNode

class BeginNode(nodes.BaseNode):

    def exec(self):
        if "trueSuccessor" or "falseSuccessor" in self.inputs:
            self.output = self.controlFlowMultiplicative
