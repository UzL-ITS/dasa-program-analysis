import torch
import nodes.BaseNode
from nodes.custom.MathFunctions import MathFunctions
from nodes.types.String import String

class ArrayEqualsNode(nodes.BaseNode):


    def exec(self):
        if not type(self.inputs.get('array1')) == type(self.inputs.get('array2')):
            self.output = torch.tensor(0.0, requires_grad=True)
        else:
            x = self.inputs['array1']
            y = self.inputs['array2']
            v_len = MathFunctions.equals(x.length, y.length) * MathFunctions.equals(x.is_null, y.is_null)
            v_data = 0
            for i in range(int(round(x.length.item()))):
                v_data += MathFunctions.equals(x.data[i], y.data[i])
            v_data /= x.length
            self.output = v_len * v_data
