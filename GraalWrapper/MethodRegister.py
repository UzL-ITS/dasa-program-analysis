import GraalWrapper
from collections import defaultdict

methods = defaultdict(int)
class MethodRegister:

    @staticmethod
    def clear():
        global methods
        methods = defaultdict(int)

    @staticmethod
    def get_method(key):
        #if key not in MethodRegister.methods:
        #    MethodRegister.methods[key] = MethodRegister.create_method(key)
        #else:
        #    # del

        # Always start fresh in case there are some leftover bits from the last execution of the method
        if key == 'PrintStream.writeln':
            #print('Println', self.controlFlowMultiplicative)
            return None # TODO Hacky
        if key == 'Integer.parseInt':
            #self.output, self.node_penalty = parseInt.parseInt(self.inputs['callTarget'])
            return None #  value is set by start node

        if key.startswith('Verifier.'):
            return None # value is usually what we optimize for

        return MethodRegister.create_method(key)

    @staticmethod
    def create_method(key):
        if methods[key] >= 10:
            return None
        methods[key] += 1
        if key == 'org_example_Test.convertValue':
            return GraalWrapper.GraphBuilder('SUTs/Test7/graph_convert_value.json')
        return f"{key}.json"
