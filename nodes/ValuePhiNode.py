import nodes.BaseNode
import torch

class ValuePhiNode(nodes.BaseNode):

    def exec(self):
        vals = [val for key, val in self.inputs.items() if "values" in key]
        if self.inputs.get('merge', -1) >= 0:
            merge_factor = self.inputs['merge']
            try:
                self.output = (1-merge_factor)*vals[0] + merge_factor*vals[1]
            except TypeError:
                self.output = vals[int(merge_factor.item())]
        else:
            sum = torch.tensor(0.0)
            for val in vals:
                sum += val

            self.output = sum
            # TODO: add punishment for having too many non-zero inputs


    def add_parent(self, parent, edge):
        if edge['props']['type'] == 'Value' or edge['props']['type'] == 'Association':
            super().add_parent(parent, edge)
