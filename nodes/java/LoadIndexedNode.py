import nodes.BaseNode
from nodes.custom.MathFunctions import MathFunctions
from nodes.custom.sigmoid import Sigmoid
import torch


class LoadIndexedNode(nodes.BaseNode):


    def exec(self):
        input_array_key = [key for key in self.inputs.keys() if key[0:5] == 'array'][0]
        input_array = self.inputs[input_array_key]
        idx = self.inputs['index']

        if not isinstance(input_array, nodes.types.Array):
            raise Exception('Only arrays can be used as input for LoadIndexNode')

        self.node_penalty = torch.relu(input_array.is_null) # this node shall not be called with a null array

        # array length must be as least the index
        self.node_penalty = self.node_penalty + Sigmoid.sigmoid((idx + 1.0) - input_array.length)
        #input_array.length = torch.max(input_array.length, (idx + 1.0) * self.controlFlowMultiplicative) # zero based

        # Find a weighted distance value for the given index
        distance_values = []
        for i in range(len(input_array.data)):
            distance_values.append(MathFunctions.equals(i, idx))

        weighted_distance_values = torch.softmax(torch.tensor(distance_values), dim=0)

        if isinstance(input_array.data[0], torch.Tensor):
            final_value = 0
            for i in range(len(input_array.data)):
                final_value += input_array.data[i] * weighted_distance_values[i]
            self.output = final_value

