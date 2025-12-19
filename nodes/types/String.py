import random
import torch
import torch.nn.functional as F
from nodes.types import BaseType


class String(BaseType):
    """
    String represented as a matrix of logits with Gumbel-Softmax sampling.
    """

    # Class-level temperature (annealed during optimization)
    temperature = 1.0

    vocab = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        " !\"'(),-./:;?[]_"
    )
    vocab_codes = None  # Will be initialized on first use

    def __init__(self, length=10, initialization_bias='uniform', initialization_words=[]):
        super().__init__()

        self.length = length
        self.vocab_size = len(String.vocab)

        # Initialize vocab_codes tensor if not already done
        if String.vocab_codes is None:
            String.vocab_codes = torch.tensor(
                [ord(c) for c in String.vocab],
                dtype=torch.float64
            )

        # Initialize logits matrix with small random values
        # IMPORTANT: Must create as leaf tensor for optimizer
        self.logits = torch.randn(length, self.vocab_size, requires_grad=True)
        self.logits.data *= 0.1  # Scale in-place to keep it as leaf

        # Apply initialization bias
        if initialization_bias == 'lowercase':
            # Bias toward a-z (indices 0-25)
            self.logits.data[:, 0:26] += 1.0
        elif initialization_bias == 'uppercase':
            # Bias toward A-Z (indices 26-51)
            self.logits.data[:, 26:52] += 1.0
        elif initialization_bias == 'digits':
            # Bias toward 0-9 (indices 52-61)
            self.logits.data[:, 52:62] += 1.0
        # else: uniform (no bias)
        if initialization_words and random.random() < 0.2:
            target_word = random.choice(list(initialization_words))
            offset = random.randint(0, self.length - len(target_word)) if self.length > len(target_word) else 0
            for idx, letter in enumerate(target_word[:self.length]):
                if letter not in String.vocab:
                    continue
                self.logits.data[offset + idx, String.vocab.index(letter)] += 10.0


    def gumbel_softmax(self, hard=False):
        # Add small epsilon to prevent log(0)
        gumbel_noise = -torch.log(-torch.log(torch.rand_like(self.logits) + 1e-20) + 1e-20)
        gumbel_logits = (self.logits + gumbel_noise) / String.temperature
        soft_samples = F.softmax(gumbel_logits, dim=1)

        if hard:
            # Straight-through: discrete in forward pass, soft in backward pass
            # Get one-hot encoding of argmax
            hard_samples = F.one_hot(
                soft_samples.argmax(dim=1),
                self.vocab_size
            ).float()

            # Straight-through trick: use hard in forward, but backprop through soft
            # This is done by: hard - soft.detach() + soft
            soft_samples = hard_samples - soft_samples.detach() + soft_samples

        return soft_samples

    def get_char_probs(self):
        return F.softmax(self.logits / String.temperature, dim=1)

    def get_char_codes(self, use_gumbel=True):
        if use_gumbel:
            char_probs = self.gumbel_softmax()
        else:
            char_probs = self.get_char_probs()
        char_codes = torch.matmul(char_probs, String.vocab_codes)
        return char_codes

    def charAt(self, index, use_gumbel=True):
        # For string charAt operations, we want SHARP indexing, not soft blending
        # Use temperature-controlled selection that becomes sharp during optimization
        temperature_scale = 0.1  # Controls sharpness (lower = sharper)

        # Compute distances from each position to target index
        positions = torch.arange(self.length, dtype=torch.float64)
        distances = -torch.abs(positions - index) / temperature_scale
        position_weights = torch.softmax(distances, dim=0)

        if use_gumbel:
            char_probs = self.gumbel_softmax()
        else:
            char_probs = self.get_char_probs()

        blended_probs = torch.sum(
            char_probs * position_weights.unsqueeze(1),
            dim=0
        )

        expected_code = torch.sum(blended_probs * String.vocab_codes)
        return expected_code

    def to_string(self, use_gumbel=False):
        if use_gumbel:
            char_probs = self.gumbel_softmax()
        else:
            char_probs = self.get_char_probs()

        # Argmax to get most likely character at each position
        char_indices = torch.argmax(char_probs, dim=1)

        chars = [String.vocab[idx] for idx in char_indices]
        return ''.join(chars)

    def get_optimize_parameter(self):
        return super().get_optimize_parameter() + [self.logits]

    def reset(self):
        pass

    def __repr__(self):
        current_string = self.to_string(use_gumbel=False)
        return f"String(length={self.length}, temp={String.temperature:.3f}, value='{current_string}')"

    @staticmethod
    def set_temperature(temp):
        String.temperature = temp


def get_start_values_string(length=10, initialization_bias='uniform'):
    return String(length=length, initialization_bias=initialization_bias)
