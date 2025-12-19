import nodes.BaseNode
import torch


class CharAtNode(nodes.BaseNode):

    def exec(self):
        if 'callTarget' not in self.inputs:
            print(f"WARNING: CharAtNode missing callTarget. Inputs: {list(self.inputs.keys())}")
            self.output = torch.tensor(65.0, requires_grad=True)  # 'A'
            return

        callTarget = self.inputs['callTarget']

        # Extract string object (second argument - the receiver)
        string_obj = callTarget.get('arguments', None)
        if string_obj is None:
            print(f"WARNING: CharAtNode missing string argument")
            self.output = torch.tensor(65.0, requires_grad=True)  # 'A'
            return

            # Extract index (first argument)
        index = callTarget.get('arguments_1', None)
        if index is None:
            print(f"WARNING: CharAtNode missing index argument")
            self.output = torch.tensor(65.0, requires_grad=True)  # 'A'
            return

        if not isinstance(index, torch.Tensor):
            print(f"WARNING: Index is not a tensor: {type(index)}")
            self.output = torch.tensor(65.0, requires_grad=True)  # 'A'
            return


        if hasattr(string_obj, 'charAt') and callable(string_obj.charAt):
            self.output = string_obj.charAt(index, use_gumbel=False)
            return
        else:
            # Unknown string type
            print(f"WARNING: Argument is not a String object: {type(string_obj)}")
            self.output = torch.tensor(65.0, requires_grad=True)  # 'A'
