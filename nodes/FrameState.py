import nodes.BaseNode

class FrameState(nodes.BaseNode):

    def __init__(self, node):
        super().__init__(node)
        self.desired_inputs = -1

    def exec(self):
        pass # Do nothing

    def pass_constant_value(self):
        # make it always triggering
        self.desired_inputs = 0
        super().pass_constant_value()