import nodes.BaseNode
import nodes

class SubstrateMethodCallTargetNode(nodes.BaseNode):


    def exec(self):
        self.output = self.inputs
        #print(self.node['id'], self.node['props']['targetMethod'], self.controlFlowMultiplicative, self)

    def add_parent(self, parent, edge):
        super().add_parent(parent, edge)

        # check if invoke
        if not isinstance(parent, nodes.InvokeNode):
            return

        if parent.node['props']['targetMethod'] == 'Integer.parseInt':
            return # TODO hack

        self.add_child(parent, edge) # add reverse edge