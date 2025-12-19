import nodes.BaseNode
import torch

class StartNode(nodes.BaseNode):

    def __init__(self, node):
        super().__init__(node)
        self.desired_inputs = 0
        self.controlFlowMultiplicative = torch.tensor(1.0, requires_grad=True)

    def exec(self):
        pass

    def pass_constant_value(self):
        pass # Don't auto execute!!!
