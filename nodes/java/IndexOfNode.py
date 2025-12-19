import nodes.BaseNode
import torch
from nodes.custom.MathFunctions import MathFunctions
from nodes.custom.sigmoid import Sigmoid


class IndexOfNode(nodes.BaseNode):
    """
    Implements differentiable String.indexOf() operation.
    Returns the index of the first occurrence of a substring, or -1 if not found.
    """

    def exec(self):
        if 'callTarget' not in self.inputs:
            print(f"WARNING: IndexOfNode missing callTarget. Inputs: {list(self.inputs.keys())}")
            self.output = torch.tensor(-1.0, requires_grad=True)
            return

        callTarget = self.inputs['callTarget']

        haystack = callTarget.get('arguments', None)
        needle = callTarget.get('arguments_1', None)

        if haystack is None:
            print(f"WARNING: IndexOfNode missing haystack argument")
            self.output = torch.tensor(-1.0, requires_grad=True)
            return

        if needle is None:
            print(f"WARNING: IndexOfNode missing needle argument")
            self.output = torch.tensor(-1.0, requires_grad=True)
            return

        if not hasattr(haystack, 'charAt') or not hasattr(needle, 'charAt'):
            print(f"WARNING: IndexOfNode arguments are not String objects: haystack={type(haystack)}, needle={type(needle)}")
            self.output = torch.tensor(-1.0, requires_grad=True)
            return

        if needle.length > haystack.length:
            self.output = torch.tensor(-1.0, requires_grad=True)
            return

        match_scores = []
        position_values = []

        for start_pos in range(haystack.length - needle.length + 1):
            char_matches = []
            for i in range(needle.length):
                hay_char = haystack.charAt(start_pos + i, use_gumbel=False)
                needle_char = needle.charAt(i, use_gumbel=False)

                match = MathFunctions.equals(hay_char, needle_char)
                char_matches.append(match)

            if len(char_matches) > 0:
                char_matches_stack = torch.stack(char_matches)

                epsilon = 1e-10
                char_matches_clipped = torch.clamp(char_matches_stack, min=epsilon)

                log_mean = torch.mean(torch.log(char_matches_clipped))
                position_match = torch.exp(log_mean)
            else:
                # Empty needle - should match at position 0
                position_match = torch.tensor(1.0, requires_grad=True)

            match_scores.append(position_match)
            position_values.append(torch.tensor(float(start_pos), requires_grad=True))

        best_match_score = torch.max(torch.stack(match_scores))

        weighted_positions = []
        for score, pos in zip(match_scores, position_values):
            weighted_positions.append(score * pos)

        if len(weighted_positions) > 0:
            weighted_sum = torch.sum(torch.stack(weighted_positions))
            total_weight = torch.sum(torch.stack(match_scores))

            epsilon = torch.tensor(1e-10, requires_grad=True)
            found_index = weighted_sum / (total_weight + epsilon)
        else:
            found_index = torch.tensor(0.0, requires_grad=True)

        self.output = -1.0 + (found_index + 1.0) * best_match_score
