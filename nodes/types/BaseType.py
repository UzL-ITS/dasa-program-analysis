import torch

class BaseType:

    def __init__(self):
        self.is_null = torch.tensor(0.0, requires_grad=True)

    def get_optimize_parameter(self):
        return [self.is_null]

    def to_string(self):
        raise NotImplementedError("Method not implemented for ", self)