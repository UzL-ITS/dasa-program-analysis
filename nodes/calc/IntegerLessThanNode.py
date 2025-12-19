import nodes.BaseNode
import torch
from nodes.custom.MathFunctions import MathFunctions

class IntegerLessThanNode(nodes.BaseNode):


    def exec(self):
        x_key = [key for key in self.inputs.keys() if 'x' in key][0]
        y_key = [key for key in self.inputs.keys() if 'y' in key][0]
        x = self.inputs[x_key]
        y = self.inputs[y_key]
        if not x:
            x = torch.tensor(0.0, requires_grad=True)
        if not y:
            y = torch.tensor(0.0, requires_grad=True)

        #if self.node['id'] == 32:
        #print('Less than: ', y, ' is less than ', x, MathFunctions.less_than(y, x))

        self.output = MathFunctions.less_than(x, y)

