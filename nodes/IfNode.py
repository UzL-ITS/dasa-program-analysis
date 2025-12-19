import nodes.BaseNode
import torch

class IfNode(nodes.BaseNode):
    def __init__(self, node):
        super().__init__(node)
        self.c = 0
    def exec(self):

        self.c = self.inputs['condition']
        if not self.c:
            self.c = torch.tensor(0.0, requires_grad=True)
        #if c < -0.1 or c > 1.1:
        #    raise Exception('Invalid range for IF: ', c)
        #if self.node['id'] == 26:
        #    print('Condition', c)

        #c = torch.min(c, torch.tensor(1.0))
        #c = torch.max(c, torch.tensor(0.0))

        # It can happen that during slicing, one of the branches is not used
        if 'trueSuccessor' in self.children:
            self.children['trueSuccessor'].add_input(-999, 'trueSuccessor', self.controlFlowMultiplicative * self.c)
        if 'falseSuccessor' in self.children:
            self.children['falseSuccessor'].add_input(-999, 'falseSuccessor', self.controlFlowMultiplicative * (1-self.c))

        return False # don't set output automatically