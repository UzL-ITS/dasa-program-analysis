import nodes.BaseNode

class ModNode(nodes.BaseNode):


    def exec(self):

        #print(self.node['id'], self.inputs)
        x_key = [key for key in self.inputs.keys() if 'x' in key][0]
        y_key = [key for key in self.inputs.keys() if 'y' in key][0]

        x = self.inputs[x_key]
        y = self.inputs[y_key]

        self.output = x % y

