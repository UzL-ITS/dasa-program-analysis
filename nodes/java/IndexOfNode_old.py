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

        # Exponential decay penalty: prefer early positions
        # Higher lambda = stronger preference for early positions
        # lambda=0.35: pos0→1.0, pos1→0.70, pos2→0.50, pos5→0.17
        lambda_decay = 0.4

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

            # Apply exponential position penalty to prefer early matches
            # pos 0 → 1.0, pos 1 → 0.61, pos 2 → 0.37, pos 5 → 0.08
            position_penalty = torch.exp(torch.tensor(-lambda_decay * start_pos, requires_grad=True))
            penalized_match = position_match * position_penalty

            match_scores.append(penalized_match)
            position_values.append(torch.tensor(float(start_pos), requires_grad=True))

        # Strategy 1: Cumulative "First Match" Probability
        # Model indexOf semantics: return the FIRST occurrence
        # If we find a match at position 0 with high probability, later positions contribute much less

        not_found_yet_prob = torch.tensor(1.0, requires_grad=True)
        expected_index = torch.tensor(0.0, requires_grad=True)
        found_prob_total = torch.tensor(0.0, requires_grad=True)

        weighted_positions = []  # Keep for debug output

        for score, pos in zip(match_scores, position_values):
            # Probability we find it HERE = we haven't found it yet AND it matches here
            find_here_prob = not_found_yet_prob * score

            expected_index = expected_index + find_here_prob * pos
            found_prob_total = found_prob_total + find_here_prob

            # Update: reduce "not found yet" by how much we matched here
            not_found_yet_prob = not_found_yet_prob * (1.0 - score)

            weighted_positions.append(find_here_prob * pos)  # For debug

        epsilon = torch.tensor(1e-10, requires_grad=True)
        found_index = expected_index / (found_prob_total + epsilon)
        best_match_score = found_prob_total  # Total probability we found it somewhere

        # Simple linear interpolation: -1 when not found, found_index when found
        # This prevents "cheating" by having partial match at high index appear as low index
        self.output = -1.0 + (found_index + 1.0) * best_match_score
        print(f"weighted_pos (cumulative): {[x.item() for x in weighted_positions]}")
        print(f"match_scores: {[x.item() for x in match_scores]}")
        print(f"pos_values: {[x.item() for x in position_values]}")
        print(f"idx: {found_index.item()} score: {best_match_score.item()} output: {self.output.item()}")
