import nodes.BaseNode
from nodes.custom.sigmoid import Sigmoid
from nodes.custom.sigmoid import Sigmoid

class IsNullNode(nodes.BaseNode):

    def exec(self):
        if not (isinstance(self.inputs['value'], nodes.types.Array) or isinstance(self.inputs['value'], nodes.types.String)):
            raise Exception('Currently only arrays are supported for null check')

        self.output = Sigmoid.sigmoid(self.inputs['value'].is_null)

