import nodes.BaseNode

class ReturnNode(nodes.BaseNode):

    def exec(self):
        self.output = self.inputs['result'] if 'result' in self.inputs else None # Simply pass the value
