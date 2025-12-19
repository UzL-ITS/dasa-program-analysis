import nodes.BaseNode
from nodes.custom.sigmoid import Sigmoid
import torch

class ArrayLengthNode(nodes.BaseNode):

    def exec(self):
        if not isinstance(self.inputs['array'], nodes.types.Array):
            raise Exception('Arraylength can only be applied to arrays')

        self.node_penalty = torch.relu(self.inputs['array'].is_null)
        #if self.inputs['array'].length < 0:
        #    self.node_penalty = self.node_penalty + -self.inputs['array'].length*1*999 # add penality for array size < 0
        self.output = self.inputs['array'].length

        #print(f'ArrayLengthNode {self.node["id"]} {self.inputs["array"].length}')
