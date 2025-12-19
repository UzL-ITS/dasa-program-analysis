import nodes.BaseNode
import torch

class SinNode(nodes.BaseNode):


    def exec(self):

        #print(self.node['id'], self.inputs)
        if 'callTarget' in self.inputs:
            key = self.inputs['callTarget']['arguments']
        else:
            key = self.inputs["value"]

        self.output = torch.sin(key)

