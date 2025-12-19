import torch
import re

class BaseNode:

    # constructor
    def __init__(self, node):
        self.node = node
        self.controlFlowMultiplicative = torch.tensor(1.0)
        self.node_penalty = 0
        self.children = {}
        self.inputs = {}
        self.desired_inputs = 0
        self.output = None
        self.executed = False

    def exec(self):
        raise NotImplementedError("Method not implemented for ", self)

    def add_child(self, child, edge):
        edge_name = edge['props']['name']
        if edge['props']['index'] > 0:
            edge_name = f"{edge_name}_{edge['props']['index']}"
        if edge_name not in self.children:
            self.children[edge_name] = child
            return

        self.children[f"{edge_name}__{len(self.children)}"] = child

    def add_parent(self, parent, edge):
        self.desired_inputs += 1

    def reset_inputs(self):

        self.inputs = {}
        self.controlFlowMultiplicative = torch.tensor(1.0)
        self.output = None
        self.executed = False

    def pass_constant_value(self):
        if self.desired_inputs == 0:
            self.executed = 1
            # print(f'Auto Executing node ', self.node['id'])
            self.exec()
            self.set_output()

    def add_input(self, input, edge, controlFlowMultiplicative):
        #if input is None:
        #    raise Exception(f"Invalid input for node {self.node['id']} {self} with edge {edge}")

        if edge not in self.inputs:
            self.inputs[edge] = input
        else:
            self.inputs[f"{edge}_{len(self.inputs)}"] = input

        #if self.node['id'] == 26:
        #    print('Adding controlFlowMultiplicative', controlFlowMultiplicative, 'to node', self.node['id'], 'with edge', edge)
        self.controlFlowMultiplicative = torch.min(controlFlowMultiplicative, self.controlFlowMultiplicative)

        if len(self.inputs) == self.desired_inputs:
            try:
                manually_set_output = self.exec()
                self.executed = True
            except Exception as e:
                print(f"Error for node {self.node['id']} {self}")
                print('Inputs', self.inputs)
                raise e
            if manually_set_output is None:
                self.set_output()

    def set_output(self, forced_output = None):
        self.executed = True
        if forced_output is not None:
            self.output = forced_output

        for edge, c in self.children.items():
            if edge.count("_") > 1:
                edge = edge.rsplit('__', 1)[0] # Rename the output to its original name if the node outputs to multiple nodes
            c.add_input(self.output, edge, self.controlFlowMultiplicative)

