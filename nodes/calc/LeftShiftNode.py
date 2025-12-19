import nodes.BaseNode
import torch
import re

class LeftShiftNode(nodes.BaseNode):

    def __init__(self, node):
        super().__init__(node)

        if not re.match("i[0-9]+", self.node['props']['stamp']):
            print(f'Currently the LeftShiftNode node only supports Integer, but got {self.node["props"]["stamp"]}')


    def exec(self):
        """
        A left shift node takes two inputs, x and y, and returns x << y
        As a single left shift is the same as multiplying by 2, this is equivalent to x * (2 ** y)
        However, the left shift implementation in java is limited by the size of the data type. Everything above is
        mapped to the corresponding shift inside the boundaries => for 32 bit: 1 << 33 = 1 << 1

        :return:
        """
        x_key = [key for key in self.inputs.keys() if 'x' in key][0]
        y_key = [key for key in self.inputs.keys() if 'y' in key][0]

        x = self.inputs[x_key]
        y = self.inputs[y_key]
        self.output = x * (2 ** (y % 32))

