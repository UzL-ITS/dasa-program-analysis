import torch
import nodes.BaseNode
from nodes.custom.MathFunctions import MathFunctions
from nodes.types.String import String

class ObjectEqualsNode(nodes.BaseNode):


    def exec(self):
        if not type(self.inputs.get('x')) == type(self.inputs.get('y')):
            self.output = torch.tensor(0.0, requires_grad=True)
        elif isinstance(self.inputs.get('x'), String) and isinstance(self.inputs.get('y'), String):
            x = self.inputs['x']
            y = self.inputs['y']
            v_len = MathFunctions.equals(torch.tensor(x.length), torch.tensor(y.length)) * MathFunctions.equals(x.is_null, y.is_null)
            v_data = 0
            for i in range(x.length):
                v_data += MathFunctions.equals(x.charAt(i, use_gumbel=False), y.charAt(i, use_gumbel=False))
            v_data /= x.length
            self.output = v_len * v_data
        else: # We have some unknown type
            print(f"Currently the ObjectEqualsNode only supports String, "
                  f"but got {type(self.inputs.get('x'))} and {type(self.inputs.get('y'))}")
            self.output = torch.tensor(0.0, requires_grad=True)
