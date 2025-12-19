from nodes.types import BaseType
import torch

class Array(BaseType):

    length = torch.tensor(0.0, requires_grad=True)
    data = []

    def __init__(self, data=None, length=torch.tensor(0.0, requires_grad=True)):
        super().__init__()
        self.length = length
        if not data:
            data = [torch.tensor(42.0, requires_grad=True) for _ in range(10)]
        if len(data) < 10:
            data.extend([torch.tensor(42.0, requires_grad=True) for _ in range(10 - len(data))])
        self.data = data

    def reset(self):
        pass
        #if self.length < 0:
        #    self.length = torch.tensor(0.1) # length < 0 is not possible

    def to_string(self):
        result = f"[Array length: {self.length}, is_null: {self.is_null}, data="
        for d in self.data:
            if isinstance(d, torch.Tensor):
                result += ', ' + str(d.item())
            elif isinstance(d, BaseType):
                result += ', ' + str(d.to_string())
        result += ']'

        return result

    def get_optimize_parameter(self):
        data_optimize_parameter = []
        for d in self.data:
            # check if the data is a tensor
            if isinstance(d, torch.Tensor):
                data_optimize_parameter.append(d)
            elif isinstance(d, BaseType):
                data_optimize_parameter += d.get_optimize_parameter()
        return super().get_optimize_parameter() + [self.length] + data_optimize_parameter