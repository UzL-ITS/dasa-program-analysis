import nodes.BaseNode
import torch
from nodes.custom.sigmoid import Sigmoid

class IntegerBelowNode(nodes.BaseNode):


    def exec(self):
        """
        Check if x is below y and greater than 0

        :return:
        """
        x_key = [key for key in self.inputs.keys() if 'x' in key][0]
        y_key = [key for key in self.inputs.keys() if 'y' in key][0]
        x = self.inputs[x_key]
        y = self.inputs[y_key]
        if not x:
            x = torch.tensor(0.0, requires_grad=True)
        if not y:
            y = torch.tensor(0.0, requires_grad=True)
        self.output = Sigmoid.sigmoid(0.1*(y - x)) * Sigmoid.sigmoid(0.1*x)

