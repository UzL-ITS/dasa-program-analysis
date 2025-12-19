import nodes.BaseNode

class CommitAllocationNode(nodes.BaseNode):

    def exec(self):
        if 'values' in self.inputs:
            self.output = self.inputs['values'] # pass the input values to the output
        else:
            self.output = list(self.inputs.values())[0]