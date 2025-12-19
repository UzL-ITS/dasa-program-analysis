import nodes.BaseNode
from nodes.custom.MathFunctions import MathFunctions
import torch

class FloatEqualsNode(nodes.BaseNode):

    def exec(self):
        x = self.inputs['x']
        y = self.inputs['y']
        if not x:
            x = torch.tensor(0.0, requires_grad=True)
        if not y:
            y = torch.tensor(0.0, requires_grad=True)
        v = MathFunctions.equals(x, y)
        self.output = v
