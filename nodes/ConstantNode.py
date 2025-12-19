import nodes.BaseNode
import nodes.types.String
import torch
import re

class ConstantNode(nodes.BaseNode):

    def __init__(self, node):
        super().__init__(node)

        if not (re.match("[if][0-9]+", self.node['props']['stampKind'])
                or "java.lang.String" in self.node['props']['stamp'] or "byte[]" in self.node['props']['stamp']):
            print(f'Currently the constant node only supports Integer, Float, String and Byte arrays '
                  f'but got {self.node["props"]["stampKind"]}')

    def exec(self):

        if re.match("i[0-9]+", self.node['props']['stampKind']):
            self.output = torch.tensor(float(int(self.node['props']['rawvalue'])))
        elif re.match("f[0-9]+", self.node['props']['stampKind']):
            self.output = torch.tensor(float(self.node['props']['rawvalue']))
        elif "java.lang.String" in self.node['props']['stamp']:
            raw_value = self.node['props']['rawvalue']
            string_length = len(raw_value)
            string_obj = nodes.types.String(length=string_length)

            # Pre-initialize logits to strongly favor target characters
            for pos, char in enumerate(raw_value):
                if char in nodes.types.String.vocab:
                    char_idx = nodes.types.String.vocab.index(char)
                    # Set logits: target char = +20, others = -20 (very strong bias)
                    string_obj.logits.data[pos, :] = -20.0
                    string_obj.logits.data[pos, char_idx] = 20.0
                else:
                    #print(f"WARNING: Character '{char}' (ord={ord(char)}) not in vocab for constant '{raw_value}'")
                    # Default to first character in vocab
                    string_obj.logits.data[pos, :] = -20.0
                    string_obj.logits.data[pos, 0] = 20.0

            # Freeze the logits so constants don't change during optimization
            string_obj.logits.requires_grad = False
            self.output = string_obj

        elif "byte[]" in self.node['props']['stamp']:
            raw_value = self.node['props']['rawvalue']
            array = raw_value.split("{")[1].replace("}","")
            array = [torch.tensor(float(v.strip())) for v in array.split(",")]
            self.output = nodes.types.Array(array, torch.tensor(float(len(array))))

