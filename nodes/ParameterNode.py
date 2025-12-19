import nodes.BaseNode

class ParameterNode(nodes.BaseNode):

    def exec(self):
        if self.inputs is None:
            return # Should not happen?!
        if 'parameter' in self.inputs:
            self.output = self.inputs['parameter']
        else:
            self.output = list(self.inputs.values())[0]

    def pass_constant_value(self):
        pass # don't execute parameter nodes of main
