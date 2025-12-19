import torch
import nodes.BaseNode

class LoadFieldNode(nodes.BaseNode):

    def exec(self):
        if self.node['props']['location'] == "String.coder":
            self.output = torch.tensor(0.0, requires_grad=True)
        elif self.node['props']['location'] == "String.value":
            obj_str = self.inputs['object']
            if obj_str is None:
                obj_arr = nodes.types.Array()
                obj_arr.is_null = torch.tensor(1.0, requires_grad=True)
            else:
                obj_arr = nodes.types.Array([obj_str.charAt(i) for i in range(obj_str.length)],
                                        torch.tensor(float(obj_str.length)))
            self.output = obj_arr
