import json
import re
import sys
import nodes
from .InputNodeTypes import input_node_tuple, TYPE_CONV_INT, TYPE_CONV_FLOAT, TYPE_CONV_DEFAULT, TYPE_CONV_STRING, \
    string_input_node_tuple, TYPE_CONV_CHAR, TYPE_CONV_BOOL, TYPE_CONV_BYTE, TYPE_CONV_SHORT, TYPE_CONV_LONG
import GraalWrapper

current_working_dir = ""


def get_recursion_boundary_node(node_id, thousands_offset=0):
    return (node_id // 1000 + thousands_offset) * 1000


class GraphBuilder:
    def __init__(self, graph_json_file, work_dir=None, rec_list=None):
        global current_working_dir
        if work_dir is not None:
            current_working_dir = work_dir
        self.graph_json_file = current_working_dir + graph_json_file
        self.json_graph = None
        self.graph = None
        self.rec_list = rec_list if rec_list is not None else []
        self.verbose = False

    def load_graph(self):

        if self.json_graph is not None:
            return self.json_graph

        with open(self.graph_json_file, 'r') as file:
            data = file.read()

        # Split using regex
        json_strings = re.split(r'}\n{', data)
        orig_json_graph = json.loads(json_strings[0] + "}")
        rec_offset = len(self.rec_list)
        if rec_offset > 0:
            adapted_json_graph = {}
            for key in orig_json_graph:
                if key == "nodes":
                    adapted_json_graph[key] = []
                    for node in orig_json_graph[key]:
                        node['id'] += 1000 * rec_offset
                        node['props']['id'] = node['id']
                        adapted_json_graph[key].append(node)
                elif key == "edges":
                    adapted_json_graph[key] = []
                    for node in orig_json_graph[key]:
                        node['from'] += 1000 * rec_offset
                        node['to'] += 1000 * rec_offset
                        adapted_json_graph[key].append(node)
                else:
                    adapted_json_graph[key] = orig_json_graph[key]
            self.json_graph = adapted_json_graph
        else:
            self.json_graph = orig_json_graph
        return self.json_graph


    def do_backward_slicing(self, graph, end_node):
        # do a BFS to infer all nodes that are connected to the end node
        curr_node = end_node
        visited = set()
        queue = [curr_node]
        while queue:
            curr_node = queue.pop(0)
            visited.add(curr_node)
            for edge in graph['edges']:
                if edge['to'] == curr_node:
                    if edge['from'] not in visited:
                        queue.append(edge['from'])

        return visited

    def build(self, start_node, end_node):

        graph = self.load_graph()
        allowed_nodes = None
        if 0 <= end_node <= 1000: #only do backwards slicing if the end_node is not inside a called function
            allowed_nodes = self.do_backward_slicing(graph, end_node)
        new_graph = {}
        unknown_nodes = []
        for node in graph['nodes']:
            if allowed_nodes is not None and end_node >= 0 and node['id'] not in allowed_nodes:
                continue
            if node['id'] >= get_recursion_boundary_node(start_node, 1):
                continue
            node_class = node['props']['node_class']['node_class']

            if node_class == 'jdk.graal.compiler.nodes.calc.AddNode':
                new_graph[node['id']] = nodes.calc.AddNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.ConstantNode':
                new_graph[node['id']] = nodes.ConstantNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.IntegerLessThanNode':
                new_graph[node['id']] = nodes.calc.IntegerLessThanNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.FloatLessThanNode':
                new_graph[node['id']] = nodes.calc.FloatLessThanNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.ConditionalNode':
                new_graph[node['id']] = nodes.calc.ConditionalNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.ValuePhiNode':
                new_graph[node['id']] = nodes.ValuePhiNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.IntegerEqualsNode':
                new_graph[node['id']] = nodes.calc.IntegerEqualsNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.FloatEqualsNode':
                new_graph[node['id']] = nodes.calc.FloatEqualsNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.IfNode':
                new_graph[node['id']] = nodes.IfNode(node)
            elif node_class in ['jdk.graal.compiler.nodes.InvokeNode',
                                'jdk.graal.compiler.nodes.InvokeWithExceptionNode']:
                if re.match(r"FdLibm\$[A-Za-z0-9]+\.compute", node['props']['targetMethod']):
                    # Don't actually call a function, instead use the corresponding math function
                    new_graph[node['id']] = self.get_invoked_math_node(node)
                elif node['props']['targetMethod'] == "String.charAt":
                    new_graph[node['id']] = nodes.java.CharAtNode(node)
                elif node['props']['targetMethod'] == "String.indexOf":
                    new_graph[node['id']] = nodes.java.IndexOfNode(node)
                else:
                    new_graph.update(self.inline_new_graph(node))
            elif node_class == 'jdk.graal.compiler.nodes.MergeNode':
                new_graph[node['id']] = nodes.MergeNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.BeginNode':
                new_graph[node['id']] = nodes.BeginNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.EndNode':
                new_graph[node['id']] = nodes.EndNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.LeftShiftNode':
                new_graph[node['id']] = nodes.calc.LeftShiftNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.IntegerBelowNode':
                new_graph[node['id']] = nodes.calc.IntegerBelowNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.FloatBelowNode':
                new_graph[node['id']] = nodes.calc.FloatBelowNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.SubNode':
                new_graph[node['id']] = nodes.calc.SubNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.MulNode':
                new_graph[node['id']] = nodes.calc.MulNode(node)
            elif node_class in ['jdk.graal.compiler.nodes.calc.SignedFloatingIntegerDivNode',
                                'jdk.graal.compiler.nodes.calc.FloatDivNode']:
                new_graph[node['id']] = nodes.calc.DivNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.SqrtNode':
                new_graph[node['id']] = nodes.calc.SqrtNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.SignedFloatingIntegerRemNode':
                new_graph[node['id']] = nodes.calc.ModNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.NegateNode':
                new_graph[node['id']] = nodes.calc.NegateNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.StartNode':
                new_graph[node['id']] = nodes.StartNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.ParameterNode':
                new_graph[node['id']] = nodes.ParameterNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.ReturnNode':
                new_graph[node['id']] = nodes.ReturnNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.virtual.VirtualInstanceNode':
                new_graph[node['id']] = nodes.virtual.VirtualInstanceNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.virtual.CommitAllocationNode':
                new_graph[node['id']] = nodes.virtual.CommitAllocationNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.virtual.AllocatedObjectNode':
                new_graph[node['id']] = nodes.virtual.AllocatedObjectNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.java.LoadFieldNode':
                new_graph[node['id']] = nodes.java.LoadFieldNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.FrameState':
                new_graph[node['id']] = nodes.FrameState(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.ObjectEqualsNode':
                new_graph[node['id']] = nodes.calc.ObjectEqualsNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.calc.IsNullNode':
                new_graph[node['id']] = nodes.calc.IsNullNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.java.ArrayLengthNode':
                new_graph[node['id']] = nodes.java.ArrayLengthNode(node)
            elif node_class == 'jdk.graal.compiler.replacements.nodes.ArrayEqualsNode':
                new_graph[node['id']] = nodes.java.ArrayEqualsNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.PiNode':
                new_graph[node['id']] = nodes.PiNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.java.LoadIndexedNode':
                new_graph[node['id']] = nodes.java.LoadIndexedNode(node)
            elif node_class == 'com.oracle.svm.core.nodes.SubstrateMethodCallTargetNode':
                new_graph[node['id']] = nodes.types.com.oracle.svm.core.nodes.SubstrateMethodCallTargetNode(node)
            elif node_class == 'jdk.graal.compiler.nodes.FullInfopointNode':
                new_graph[node['id']] = nodes.FullInfoPointNode(node)
            elif node_class == 'jdk.graal.compiler.replacements.nodes.UnaryMathIntrinsicNode':
                match node['props']['operation']:
                    case 'SIN':
                        new_graph[node['id']] = nodes.calc.SinNode(node)
                    case 'COS':
                        new_graph[node['id']] = nodes.calc.CosNode(node)
                    case 'TAN':
                        new_graph[node['id']] = nodes.calc.TanNode(node)
                    case 'LOG':
                        new_graph[node['id']] = nodes.calc.LogNode(node)
                    case 'LOG10':
                        new_graph[node['id']] = nodes.calc.Log10Node(node)
                    case 'EXP':
                        new_graph[node['id']] = nodes.calc.ExpNode(node)
                    case _:
                        print_orange = "\033[33m"
                        print_normal = "\033[00m"
                        if self.verbose and node_class not in unknown_nodes:
                            unknown_nodes.append(node_class)
                            print(f"{print_orange}Unknown Unary Math function {node['props']['operation']}\n"
                                  f"using FallbackNode instead...{print_normal}")
                        new_graph[node['id']] = nodes.FallbackNode(node)
            elif node_class == 'jdk.graal.compiler.replacements.nodes.BinaryMathIntrinsicNode':
                match node['props']['operation']:
                    case 'POW':
                        new_graph[node['id']] = nodes.calc.PowNode(node)
                    case _:
                        print_orange = "\033[33m"
                        print_normal = "\033[00m"
                        if self.verbose and node_class not in unknown_nodes:
                            unknown_nodes.append(node_class)
                            print(f"{print_orange}Unknown Binary Math function {node['props']['operation']}\n"
                                  f"using FallbackNode instead...{print_normal}")
                        new_graph[node['id']] = nodes.FallbackNode(node)
            elif node_class in ['com.oracle.svm.core.graal.nodes.ThrowBytecodeExceptionNode',
                                'jdk.graal.compiler.nodes.extended.BytecodeExceptionNode']:
                new_graph[node['id']] = nodes.types.com.oracle.svm.core.graal.graal_nodes.ThrowBytecodeExceptionNode(node)
            else:
                # default
                if node['id'] == -1:
                    print(node)
                    sys.exit(0)

                print_orange = "\033[33m"
                print_normal = "\033[00m"
                if self.verbose and node_class not in unknown_nodes:
                    unknown_nodes.append(node_class)
                    print(f"{print_orange}Unknown node class {node_class}\nusing FallbackNode instead...{print_normal}")
                new_graph[node['id']] = nodes.FallbackNode(node)

        self.graph = new_graph

        self.connect_nodes(start_node=start_node)

        return new_graph

    def connect_nodes(self, start_node):

        # do a BFS to find all nodes that are connected to the start node
        # and all nodes that are connected to the end node
        if start_node != -1:
            curr_node = start_node
            visited = set()
            queue = [curr_node]
            # manually add all parameter nodes of the current layer (they don't have a parent yet)
            queue.extend(node[0] for node in self.graph.items()
                         if get_recursion_boundary_node(start_node, 0) <= node[0]
                         < get_recursion_boundary_node(start_node, 1)
                         and isinstance(node[1], nodes.ParameterNode))
            while queue:
                curr_node = queue.pop(0)
                visited.add(curr_node)
                for edge in self.json_graph['edges']:
                    if edge['from'] == curr_node and edge['to'] not in visited:
                        if edge['to'] // 1000 > curr_node // 1000:
                            # we already walked this graph in another iteration and can skip it now
                            visited.update([node['id'] for node in
                                            self.json_graph['nodes'] if node['id'] >= edge['to']])
                        else:
                            queue.append(edge['to'])

            # delete all nodes that are not connected to the start node
            for node in list(self.graph.keys()):
                # delete if not ConstantNode
                if node not in visited and not isinstance(self.graph[node], nodes.ConstantNode):
                    del self.graph[node]

        for edge in self.json_graph['edges']:

            # make sure that both nodes exist
            if (edge['from'] not in self.graph or edge['to'] not in self.graph or
                    (edge['from'] >= get_recursion_boundary_node(start_node, 1) and
                     edge['to'] >= get_recursion_boundary_node(start_node, 1))):
                continue

            src = self.graph[edge['from']]
            dest = self.graph[edge['to']]

            #print(f'{edge["from"]} -> {edge["to"]}')

            src.add_child(dest, edge)
            dest.add_parent(parent=src, edge=edge)

    def get_invoked_math_node(self, node):
        function_str = node['props']['targetMethod']
        function_str = function_str.split('$')[1].split('.')[0]
        match function_str:
            case 'Asin':
                return nodes.calc.AsinNode(node)
            case 'Acos':
                return nodes.calc.AcosNode(node)
            case 'Atan':
                return nodes.calc.AtanNode(node)
            case 'Atan2':
                return nodes.calc.Atan2Node(node)
            case 'Sin':
                return nodes.calc.SinNode(node)
            case 'Cos':
                return nodes.calc.CosNode(node)
            case 'Tan':
                return nodes.calc.TanNode(node)
            case 'Log':
                return nodes.calc.LogNode(node)
            case 'Log10':
                return nodes.calc.Log10Node(node)
            case 'Exp':
                return nodes.calc.ExpNode(node)
            case 'Pow':
                return nodes.calc.PowNode(node)
            case _:
                if self.verbose:
                    print_orange = "\033[33m"
                    print_normal = "\033[00m"
                    print(f"{print_orange}Unknown Invoked Math function {node['props']['targetMethod']}\n"
                          f"Using InvokeNode instead...{print_normal}")
                return nodes.InvokeNode(node)


    def inline_new_graph(self, node):
        inline_graph = {node['id']: nodes.InvokeNode(node)}
        loaded_method = GraalWrapper.MethodRegister.get_method(node['props']['targetMethod'])
        if not loaded_method:
            return inline_graph
        rec_list = self.rec_list.copy()
        rec_list.append(node['id'])
        loaded_graph = GraphBuilder(loaded_method, rec_list=rec_list)
        try:
            inline_graph.update(loaded_graph.get_graph(get_recursion_boundary_node(node['id'], 1), -1))
        except FileNotFoundError:
            print(f"Unknown method {node['props']['targetMethod']}")
            return inline_graph
        return_targets = []
        for edge in self.json_graph['edges']:
            if edge['from'] == node['id']:
                return_targets.append(edge)
        for edge in return_targets:
            self.json_graph['edges'].remove(edge)
        min_node_id = get_recursion_boundary_node(node['id'], 1) # Node 0 of highest layer of inlined graph
        max_node_id = get_recursion_boundary_node(node['id'], 2) - 1 # Node 999 of highest layer of inlined graph
        self.json_graph['edges'].extend(loaded_graph.json_graph['edges'])
        self.json_graph['nodes'].extend(loaded_graph.json_graph['nodes'])
        for idx, child_node in inline_graph.items():
            if not min_node_id <= idx <= max_node_id:
                continue # only nodes in the highest layer need to be linked to the invoke node
            if isinstance(child_node, nodes.StartNode):
                edge = {
                    "from": node['id'],
                    "to": idx,
                    "props": {
                        "direct": True,
                        "name": "next",
                        "type": None,
                        "index": 0
                    }
                }
                self.json_graph['edges'].append(edge)
            elif isinstance(child_node, nodes.ParameterNode):
                edge = {
                    "from": node['id'],
                    "to": idx,
                    "props": {
                        "direct": True,
                        "name": "parameter",
                        "type": "Value",
                        "index": child_node.node['props']['index']
                    }
                }
                self.json_graph['edges'].append(edge)
            elif isinstance(child_node, nodes.ReturnNode):
                for edge in return_targets:
                    edge = edge.copy()
                    edge['from'] = idx
                    self.json_graph['edges'].append(edge)

        self.rec_list = loaded_graph.rec_list
        return inline_graph

    def get_graph(self, start_node, end_node, reset=False, verbose=False):
        if self.graph is None or reset:
            self.verbose = verbose
            self.build(start_node, end_node)
        return self.graph

    def infer_string_length(self, string_invoke_node_id):
        if self.json_graph is None:
            self.load_graph()

        length_hints = []
        index_hints = []

        for node in self.json_graph['nodes']:
            node_props = node['props']
            if node_props.get('targetMethod') == "String.charAt":
                for edge in self.json_graph.get('edges', []):
                    if edge['to'] == node['id'] and edge.get('from') == string_invoke_node_id:
                        length_hints.append(10)
                        break

            if node_props.get('node_class', {}).get('node_class') == "jdk.graal.compiler.nodes.calc.ObjectEqualsNode":
                from_ids = set()
                for edge in self.json_graph.get('edges', []):
                    if edge['to'] == node['id']:
                        from_ids.add(edge['from'])
                for other_node in self.json_graph['nodes']:
                    if (other_node['props'].get('node_class', {}).get('node_class')
                            == 'jdk.graal.compiler.nodes.ConstantNode' and other_node['id'] in from_ids):
                        return len(other_node['props'].get('rawvalue', ''))
            # Check for contains/indexOf with constant string arguments
            if 'String.indexOf' in str(node_props.get('targetMethod', '')):
                # Look for ConstantNode with string in the graph
                for other_node in self.json_graph['nodes']:
                    if other_node['props'].get('node_class', {}).get('node_class') == 'jdk.graal.compiler.nodes.ConstantNode':
                        if 'java.lang.String' in other_node['props'].get('stamp', ''):
                            raw_value = other_node['props'].get('rawvalue', '')
                            # Need at least as long as the constant + buffer for matching
                            index_hints.append(raw_value)

        for i in range(len(index_hints)):
            i_str = index_hints[i]
            length_hint = len(i_str) + 5
            for j in range(i + 1, len(index_hints)):
                j_str = index_hints[j]
                if i_str not in j_str and j_str not in i_str:
                    length_hint += len(j_str)
            length_hints.append(length_hint)

        if length_hints:
            return max(length_hints)
        return 10  # Default fallback

    def get_start_end_constant_nodes(self):
        start_nodes = []
        end_nodes = []
        constant_nodes = {"num": set(), "string": set(), "float": set()}
        if self.json_graph is None:
            self.load_graph()
        for node in self.json_graph['nodes']:
            node_class = node['props']['node_class']['node_class']
            if (node_class in ['jdk.graal.compiler.nodes.InvokeNode',
                              "jdk.graal.compiler.nodes.InvokeWithExceptionNode"]
                    and node['props']['targetMethod'].startswith('Verifier.')):
                method = TYPE_CONV_DEFAULT
                if node['props']['targetMethod'] == "Verifier.nondetInt":
                    method = TYPE_CONV_INT
                elif node['props']['targetMethod'] in ["Verifier.nondetFloat", "Verifier.nondetDouble"]:
                    method = TYPE_CONV_FLOAT
                elif node['props']['targetMethod'] == "Verifier.nondetChar":
                    method = TYPE_CONV_CHAR
                elif node['props']['targetMethod'] == "Verifier.nondetBoolean":
                    method = TYPE_CONV_BOOL
                elif node['props']['targetMethod'] == "Verifier.nondetByte":
                    method = TYPE_CONV_BYTE
                elif node['props']['targetMethod'] == "Verifier.nondetShort":
                    method = TYPE_CONV_SHORT
                elif node['props']['targetMethod'] == "Verifier.nondetLong":
                    method = TYPE_CONV_LONG
                elif node['props']['targetMethod'] == "Verifier.nondetString":
                    inferred_length = self.infer_string_length(node['id'])
                    start_nodes.append(string_input_node_tuple(node['id'], TYPE_CONV_STRING,
                                                               string_length=inferred_length))
                    continue  # Skip the regular append below
                start_nodes.append(input_node_tuple(node['id'], method))
            elif node_class in ['com.oracle.svm.core.graal.nodes.ThrowBytecodeExceptionNode',
                                'jdk.graal.compiler.nodes.extended.BytecodeExceptionNode']:
                end_nodes.append(node['id'])
            elif node_class == 'jdk.graal.compiler.nodes.ConstantNode':
                if re.match("[if][0-9]+", node['props']['stampKind']):
                    constant_nodes["float"].add(float(node['props']['stamp'].split('[')[1].strip(']')))
                if re.match("i[0-9]+", node['props']['stampKind']):
                    constant_nodes["num"].add(float(node['props']['stamp'].split('[')[1].strip(']')))
                elif "java.lang.String" in node['props']['stamp']:
                    constant_nodes["string"].add(node['props']['rawvalue'])

        return start_nodes, end_nodes, constant_nodes

    def reconstruct_path_through_graph(self, start_node, end_node):
        start_node = self.graph[start_node]
        end_node = self.graph[end_node]
        curr_node = start_node
        visited = set()
        queue = [curr_node]
        while queue:
            curr_node = queue.pop(0)
            if curr_node not in visited:
                visited.add(curr_node)
            if curr_node == end_node:
                return [key for key, node in self.graph.items() if node in visited]
            if type(curr_node) is nodes.IfNode:
                if len(curr_node.children) == 1:
                    queue.append(list(curr_node.children.values())[0])
                elif curr_node.c >= 0.5:
                    queue.append(curr_node.children['trueSuccessor'])
                else:
                    queue.append(curr_node.children['falseSuccessor'])
            elif type(curr_node) is nodes.FrameState:
                continue
            else:
                for child in curr_node.children.values():
                    if child not in visited:
                        queue.append(child)
        return [key for key, node in self.graph.items() if node in visited]