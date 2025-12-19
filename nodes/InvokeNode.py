import nodes.BaseNode
import GraalWrapper
import nodes.native.integer.parseInt
from nodes.native.integer import parseInt

class InvokeNode(nodes.BaseNode):


    def exec(self):
        # pass parameters
        inputs = self.inputs['callTarget']['arguments'] if 'callTarget' in self.inputs else None
        self.output = inputs
