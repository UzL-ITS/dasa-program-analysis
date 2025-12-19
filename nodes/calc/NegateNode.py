import nodes.BaseNode

class NegateNode(nodes.BaseNode):


    def exec(self):

        #print(self.node['id'], self.inputs)
        val_key = [key for key in self.inputs.keys() if 'value' in key][0]

        val = self.inputs[val_key]

        self.output = -val

