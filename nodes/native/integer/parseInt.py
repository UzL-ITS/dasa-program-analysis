import torch
from nodes.types.String import String
from nodes.custom.MathFunctions import MathFunctions


class parseInt:

    @staticmethod
    def parseInt(arguments):
        input_value = [p for p in arguments.values() if isinstance(p, String)][0]
        input_bytes = input_value.data
        input_bytes_len = len(input_value.data) # TODO: possibly use length of input_bytes instead?
        int_value = torch.tensor(0.0, requires_grad=True)
        penalty = torch.tensor(0.0, requires_grad=True)

        # TODO: interpret the first byte as a sign byte (- or +) and skip it

        for i, b in enumerate(input_bytes):
            #print(b-48, input_bytes_len - i, 10 ** (input_bytes_len - i - 1))
            exponent = 10 ** (input_bytes_len - i - 1)
            int_value = int_value + (b - 48) * exponent

            # greater than returns 1 if a > b, 0 otherwise. Hence, the penalty is increased if b > 58
            penalty = penalty + torch.relu(MathFunctions.greater_than(b, 58) - 1)
            penalty = penalty + torch.relu(MathFunctions.less_than(b, 48) - 1)

        # if there is a penalty, set the int_value close to 0
        int_value = int_value * (torch.relu(MathFunctions.greater_than(penalty, 0) - 1) + 1)
        print("Parse int: ", int_value, penalty)

        return int_value, penalty
