from collections import namedtuple
import base64

input_node_tuple = namedtuple('InputNodeTuple', ('node_id', 'func'))
TYPE_CONV_INT = lambda x: (2**31 - 1) if round(x) > (2**31 - 1) else (-2**31) if round(x) < -(2**31) else round(x)
TYPE_CONV_FLOAT = lambda x: x
TYPE_CONV_DEFAULT = lambda x: x
TYPE_CONV_CHAR = lambda x: base64.b64encode(chr(round(x)).encode()).decode()
TYPE_CONV_BOOL = lambda x: x > 0.5
TYPE_CONV_BYTE = lambda x: (2**7 - 1) if round(x) > (2**7 - 1) else (-2**7) if round(x) < -(2**7) else round(x)
TYPE_CONV_SHORT = lambda x: (2**15 - 1) if round(x) > (2**15 - 1) else (-2**15) if round(x) < -(2**15) else round(x)
TYPE_CONV_LONG = round

def TYPE_CONV_STRING(string):
    if hasattr(string, 'to_string'):
        raw_string = string.to_string(use_gumbel=False)
    else:
        # Unknown type
        raw_string = str(string)
    return base64.b64encode(raw_string.encode("utf-8")).decode("utf-8")

# String input node wrapper (compatible with input_node_tuple interface)
class string_input_node_tuple:
    def __init__(self, node_id, func, string_length=10):
        self.node_id = node_id
        self.func = func
        self.string_length = string_length
        self.is_string = True

    def __repr__(self):
        return f"string_input_node_tuple(node_id={self.node_id}, length={self.string_length})"
