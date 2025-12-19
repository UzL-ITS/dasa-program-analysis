import nodes.BaseNode

class FallbackNode(nodes.BaseNode):

    def exec(self):
        keys = [k for k,v in self.inputs.items()
                if v is not None and (isinstance(v, nodes.types.String) or v.requires_grad or v.grad_fn is not None)]
        if not keys:
            keys = [k for k in self.inputs.keys()]
        key = keys[0]
        self.output = self.inputs[key]