import torch
from nodes.custom.sigmoid import Sigmoid

class MathFunctions:

    @staticmethod
    def equals(a, b):
        #return Sigmoid.sigmoid(-torch.abs(a - b)) * 2 # problem: if equal non-equality can not be reached
        equality = Sigmoid.sigmoid(a - b) * Sigmoid.sigmoid(b - a) * 4
        return equality

    @staticmethod
    def greater_than(a, b):
        """
        Becomes big when a is greater than b
        :param a: tensor a
        :param b: tensor b
        :return: big when a is greater than b
        """
        return Sigmoid.sigmoid(a - b)

    @staticmethod
    def less_than(a, b):
        """
        Becomes big when a is less than b

        :param a:
        :param b:
        :return:
        """
        return MathFunctions.greater_than(b, a)
