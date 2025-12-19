import nodes.BaseNode
import torch

class AtanNode(nodes.BaseNode):


    def exec(self):

        #print(self.node['id'], self.inputs)
        key = self.inputs['callTarget']['arguments'] \
            if 'callTarget' in self.inputs else torch.tensor(0.0, requires_grad=True)

        self.output = torch.atan(key)
