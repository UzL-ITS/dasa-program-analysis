import nodes.BaseNode
import torch

class Log10Node(nodes.BaseNode):


    def exec(self):

        #print(self.node['id'], self.inputs)
        if 'callTarget' in self.inputs:
            key = self.inputs['callTarget']['arguments']
        else:
            key = self.inputs["value"]

        if key <= 0:
            self.node_penalty = 10 - key
            self.output = torch.tensor(-1e20, requires_grad=True)
        else:
            self.node_penalty = None
            self.output = torch.log10(key)

