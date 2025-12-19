import nodes.BaseNode
import torch

class Atan2Node(nodes.BaseNode):


    def exec(self):

        #print(self.node['id'], self.inputs)
        x = list(self.inputs['callTarget'].values())[0]
        y = list(self.inputs['callTarget'].values())[1]

        self.output = torch.atan2(y, x)

