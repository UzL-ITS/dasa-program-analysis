import nodes.BaseNode
import torch

class AcosNode(nodes.BaseNode):


    def exec(self):

        #print(self.node['id'], self.inputs)
        key = self.inputs['callTarget']['arguments'] \
            if 'callTarget' in self.inputs else torch.tensor(0.0, requires_grad=True)

        if key < -1:
            self.node_penalty = 10 - key
            self.output = torch.tensor(4.0, requires_grad=True)
        elif key > 1:
            self.node_penalty = 10 + key
            self.output = torch.tensor(-1.0, requires_grad=True)
        else:
            self.node_penalty = None
            self.output = torch.acos(key)
