import torch

import nodes.BaseNode
from nodes.custom.MathFunctions import MathFunctions
from nodes.custom.sigmoid import Sigmoid

class IntegerEqualsNode(nodes.BaseNode):

    def exec(self):
        x = self.inputs['x']
        y = self.inputs['y']
        if not x:
            x = torch.tensor(0.0, requires_grad=True)
        if not y:
            y = torch.tensor(0.0, requires_grad=True)
        v = MathFunctions.equals(x, y)
        self.output = v
