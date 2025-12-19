import torch





annealing_constant = 0.001

class Sigmoid:

    @staticmethod
    def set_annealing_constant(constant):
        global annealing_constant
        annealing_constant = constant

    @staticmethod
    def sigmoid(x):
        return torch.sigmoid(annealing_constant * x)
