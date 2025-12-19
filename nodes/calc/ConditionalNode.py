import nodes.BaseNode

class ConditionalNode(nodes.BaseNode):

    def exec(self):
        # get input
        condition_key = [x for x in self.inputs.keys() if x.startswith('condition')][0]
        value = self.inputs[condition_key]
        self.output = value * self.inputs['trueValue'] + (1 - value) * self.inputs['falseValue']
