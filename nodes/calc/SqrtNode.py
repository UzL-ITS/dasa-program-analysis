import nodes.BaseNode
import torch

class SqrtNode(nodes.BaseNode):


    def exec(self):

        #print(self.node['id'], self.inputs)
        key = self.inputs["value"]

        if key < 0:
            self.node_penalty = 10 - key
            self.output = torch.tensor(0.0, requires_grad=True)
        else:
            self.node_penalty = None
            self.output = torch.sqrt(key)

