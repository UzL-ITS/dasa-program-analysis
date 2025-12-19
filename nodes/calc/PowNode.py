import nodes.BaseNode
import torch

class PowNode(nodes.BaseNode):


    def exec(self):

        #print(self.node['id'], self.inputs)
        if 'callTarget' in self.inputs:
            x = list(self.inputs['callTarget'].values())[0]
            y = list(self.inputs['callTarget'].values())[1]
        else:
            x_key = [key for key in self.inputs.keys() if 'x' in key][0]
            y_key = [key for key in self.inputs.keys() if 'y' in key][0]
            x = self.inputs[x_key]
            y = self.inputs[y_key]

        if x < 0:
            self.output = torch.pow(x, torch.round(y))
        else:
            self.output = torch.pow(x, y)

