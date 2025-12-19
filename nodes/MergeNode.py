import nodes.BaseNode
import torch

class MergeNode(nodes.BaseNode):
    def __init__(self, node):
        super().__init__(node)
        self.controlFlowMultiplicative = torch.tensor(-1.0)

    def exec(self):
        ends = [item for item in self.inputs.items() if "ends" in item[0] and item[1] is not None]
        ends = [v for k,v in sorted(ends, key=lambda k: k[0])]
        if ends:
            self.output = torch.tensor(float(ends.index(max(ends))))
        else:
            self.output = torch.tensor(0.0)

    def add_input(self, input, edge, controlFlowMultiplicative):
        if "ends" in edge:
            if self.node["id"] == 38:
                pass
            controlFlowMultiplicative = torch.max(controlFlowMultiplicative, self.controlFlowMultiplicative)
        super().add_input(input, edge, controlFlowMultiplicative)

