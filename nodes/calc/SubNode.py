import nodes.BaseNode
import torch

class SubNode(nodes.BaseNode):


    def exec(self):

        # print(self.node['id'], self.inputs)
        x_key = [key for key in self.inputs.keys() if 'x' in key][0]
        y_key = [key for key in self.inputs.keys() if 'y' in key][0]

        x = self.inputs[x_key]
        y = self.inputs[y_key]
        if not x:
            x = torch.tensor(0.0, requires_grad=True)
        if not y:
            y = torch.tensor(0.0, requires_grad=True)
        self.output = x - y

