import nodes.BaseNode

class VirtualInstanceNode(nodes.BaseNode):

    def exec(self):
        print(self.inputs)
        pass # Do nothing
