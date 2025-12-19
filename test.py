from collections import defaultdict

import copy
import traceback

import torch
torch.set_default_dtype(torch.float64)

import subprocess
import nodes
import torch
import torch.optim as optim
import GraalWrapper
from GraalWrapper.InputNodeTypes import input_node_tuple, TYPE_CONV_INT, TYPE_CONV_DEFAULT, string_input_node_tuple, \
    TYPE_CONV_BOOL, TYPE_CONV_BYTE, TYPE_CONV_CHAR, TYPE_CONV_SHORT, TYPE_CONV_LONG, TYPE_CONV_STRING, TYPE_CONV_FLOAT
import random
from datetime import datetime, timedelta
import math

# create graph for TEst 1:
# docker run --rm -v $(pwd)/SUTs/Test1:/SUT graph-extractor

STATE_DEFAULT = 0
STATE_NO_START_NODES_FOUND = 1
STATE_NO_END_NODES_FOUND = 2
STATE_CORRECT = 3
STATE_INCORRECT = 4
STATE_ERROR = 5


def print_has_output(original_seafom_graph, graph):

    for node in graph.values():
        # node id and penalty
        label = f"{node.node['id']}: {node.controlFlowMultiplicative}"
        if node.executed:
            print(f'{node.node["id"]}[style=filled, label="{label}"]')
        else:
            print(f'{node.node["id"]}[label="{label}"]')

    for edge in original_seafom_graph['edges']:

        # make sure that both nodes exist
        if edge['from'] not in graph or edge['to'] not in graph:
            continue

        print(f'{edge["from"]} -> {edge["to"]}')

def run_optimization(graph, input_ids, output_id, graph_builder, verbose=False, I_all=None):
    # Set input
    input_ids = sorted(input_ids)
    #I_all = [torch.tensor(42.0, requires_grad=True) for _ in range(len(input_ids))]
    if I_all is None:
        I_all = get_start_values(len(input_ids))
    #I_1 = torch.tensor(21.0, requires_grad=True)
    #input_obj = nodes.types.Array(initialization_fct=lambda : nodes.types.String())


    # Number of iterations
    iteration_factor = 1 # use iteration_factor to increase number of iterations while maintaining sigmoid annealing
    num_iterations = 2000 * iteration_factor
    sigmoid_annealing_start = 0.001
    sigmoid_annealing_end = 1
    min_loss_delta = 1e-12

    # SGD optimizer
    initial_lr = 0.1
    # Extract optimizable parameters from String objects and scalars
    optimize_params = []
    for inp in I_all:
        if hasattr(inp, 'get_optimize_parameter'):
            # String or other complex type
            optimize_params.extend(inp.get_optimize_parameter())
        else:
            # Scalar tensor
            optimize_params.append(inp)
    optimizer = optim.Adam(optimize_params, lr=initial_lr)


    # calculate the delta
    sigmoid_annealing_delta = sigmoid_annealing_end - sigmoid_annealing_start

    # Temperature annealing for Gumbel-Softmax
    temp_start = 2.0  # High temperature: smooth, exploratory
    temp_end = 0.1    # Low temperature: sharp, exploitative

    previous_loss = 100.0

    for i in range(num_iterations):
        optimizer.zero_grad()  # Zero the gradients

        # set sigmoid annealing smooth
        factor = sigmoid_annealing_start + sigmoid_annealing_delta * ((i//iteration_factor) / num_iterations)
        nodes.custom.Sigmoid.set_annealing_constant(factor)
        #nodes.custom.Sigmoid.set_annealing_constant(1)

        # Temperature annealing for Gumbel-Softmax strings
        temperature = temp_start - (temp_start - temp_end) * ((i // iteration_factor) / num_iterations)
        nodes.types.String.set_temperature(temperature)

        #input_obj.reset()
        for node in graph.values():
            node.reset_inputs()

        # Don't let the start node auto-trigger
        for start_node in input_ids:
            graph[start_node].desired_inputs = -1

        # trigger all constant values to pass on values
        for node in graph.values():
            if node.node['id'] in input_ids:
                continue

            node.pass_constant_value()


        # set the input of the start node, thus, triggering the overall execution
        for idx in range(len(input_ids)):
            graph[input_ids[idx]].controlFlowMultiplicative = torch.tensor(1.0, requires_grad=True)
            graph[input_ids[idx]].set_output(I_all[idx]) # set input

        # print_has_output(original_seafom_graph, graph)
        # return

        #print_has_output(original_seafom_graph=original_seafom_graph, graph=graph)
        #return
        #print(graph[56].controlFlowMultiplicative)
        #return

        # Compute the loss
        loss = -graph[output_id].controlFlowMultiplicative
        penalities = 0.0
        for node in graph.values():
            if node.node_penalty is not None:
                penalities += node.node_penalty

        #print('Output loss:', -graph[output_id].controlFlowMultiplicative)
        #print('Penalities:', penalities)
        loss += penalities
        # Print the progress
        if i >= 1000 and (abs(previous_loss-loss.item()) < min_loss_delta or math.isnan(loss.item())):
            values_str = []
            for x in I_all:
                if hasattr(x, 'item'):
                    values_str.append(x.item())
                elif hasattr(x, 'to_string'):
                    values_str.append(x.to_string())
                else:
                    values_str.append(str(x))
            print(f'Stopped early at iteration {i}: Values={values_str} Loss={loss.item()}')
            break
        if verbose:
            values_str = []
            for x in I_all:
                if hasattr(x, 'item'):
                    values_str.append(f"{x.item():.2f}")
                elif hasattr(x, 'to_string'):
                    values_str.append(x.to_string())
                else:
                    values_str.append(str(x))
            print(f"Iteration {i}: Values={values_str} Loss={loss.item()}")
        previous_loss = loss.item()
        loss.backward()  # Compute gradients
        optimizer.step()  # Update parameters


    walked_graph = graph_builder.reconstruct_path_through_graph(0, output_id)
    #
    # for node in graph.values():
    #     # node id and penalty
    #     label = f"{node.node['id']}: {node.controlFlowMultiplicative}"
    #     if node.executed:
    #         print(f'{node.node["id"]}[style=filled, label="{label}"]')
    #     else:
    #         print(f'{node.node["id"]}[label="{label}"]')
    # Final value of I_0
    values = []
    for idx, x in zip(input_ids, I_all):
        if idx not in walked_graph:
            values.append(None)
        elif hasattr(x, 'item'):
            values.append(x.item())
        else:
            # Complex object (String, etc.)
            values.append(x)
    return {"iteration": i, "loss": loss.item(), "values": values,
            "all_values": [x.item() if hasattr(x, 'item') else x for x in I_all]}

def get_start_values(start_nodes, constant_nodes):
    if not constant_nodes:
        constant_nodes = {"num": set(), "string": set(), "float": set()}
    start_values = [0] * len(start_nodes)
    start_node_types = defaultdict(list)
    for idx, start_node in enumerate(start_nodes):
        if start_node.func == TYPE_CONV_BOOL:
            start_node_types["bool"].append(idx)
        elif start_node.func == TYPE_CONV_CHAR:
            start_node_types["char"].append(idx)
        elif start_node.func == TYPE_CONV_BYTE:
            start_node_types["byte"].append(idx)
        elif start_node.func == TYPE_CONV_SHORT:
            start_node_types["short"].append(idx)
        elif start_node.func == TYPE_CONV_LONG:
            start_node_types["long"].append(idx)
        elif start_node.func == TYPE_CONV_FLOAT:
            start_node_types["float"].append(idx)
        elif start_node.func == TYPE_CONV_STRING:
            start_values[idx] = nodes.types.String(length=start_node.string_length, initialization_bias='uniform',
                                                   initialization_words=constant_nodes['string'])
        else:
            start_node_types["int"].append(idx)
    for start_type, ids in start_node_types.items():
        match start_type:
            case "bool": values = get_start_values_bool(len(ids))
            case "char": values = get_start_values_char(len(ids))
            case "byte": values = get_start_values_byte(len(ids), constant_nodes['num'])
            case "short": values = get_start_values_short(len(ids), constant_nodes['num'])
            case "long": values = get_start_values_long(len(ids), constant_nodes['num'])
            case "float": values = get_start_values_float(len(ids), constant_nodes['float'])
            case _: values = get_start_values_int(len(ids), constant_nodes['num'])
        for idx_local, idx_global in enumerate(ids):
            start_values[idx_global] = values[idx_local]
    return start_values

def get_start_values_int(amount, constant_values):
    start_values = []
    min_val = -2147483648.0
    max_val = 2147483647.0
    special_values = [0.0, -1.0, 1.0, min_val, max_val]
    for val in constant_values:
        if val not in special_values and min_val < val < max_val:
            special_values.append(val)
    for _ in range(amount):
        if random.random() < 0.05: # have a small chance to use special values
            start_values.append(torch.tensor(random.choice(special_values), requires_grad=True))
        else:
            if random.random() < 0.7: # have a tendency towards more common numbers
                bits_cnt = random.randint(2, 14)
            else:
                bits_cnt = random.randint(15, 31)
            rand_num = random.randint(2, (1 << bits_cnt) - 1)
            if random.random() < 0.2:
                rand_num *= -1
            start_values.append(torch.tensor(float(rand_num), requires_grad=True))
    if random.random() < 0.01: # have a small chance to initialize all inputs with the same value
        start_values = [torch.tensor(start_values[0].item(), requires_grad=True) for _ in start_values]
    return start_values

def get_start_values_bool(amount):
    return [torch.tensor(float(random.random() < 0.5), requires_grad=True) for _ in range(amount)]

def get_start_values_byte(amount, constant_values):
    start_values = []
    min_val = float(-2**7)
    max_val = float(2**7 - 1)
    special_values = [0.0, -1.0, 1.0, min_val, max_val]
    for val in constant_values:
        if val not in special_values and min_val < val < max_val:
            special_values.append(val)
    for _ in range(amount):
        if random.random() < 0.05: # have a small chance to use special values
            start_values.append(torch.tensor(random.choice(special_values), requires_grad=True))
        else:
            bits_cnt = random.randint(2, 7)
            rand_num = random.randint(2, (1 << bits_cnt) - 1)
            if random.random() < 0.2:
                rand_num *= -1
            start_values.append(torch.tensor(float(rand_num), requires_grad=True))
    if random.random() < 0.01: # have a small chance to initialize all inputs with the same value
        start_values = [torch.tensor(start_values[0].item(), requires_grad=True) for _ in start_values]
    return start_values

def get_start_values_short(amount, constant_values):
    start_values = []
    min_val = float(-2**15)
    max_val = float(2**15 - 1)
    special_values = [0.0, -1.0, 1.0, min_val, max_val]
    for val in constant_values:
        if val not in special_values and min_val < val < max_val:
            special_values.append(val)
    for _ in range(amount):
        if random.random() < 0.05: # have a small chance to use special values
            start_values.append(torch.tensor(random.choice(special_values), requires_grad=True))
        else:
            bits_cnt = random.randint(2, 15)
            rand_num = random.randint(2, (1 << bits_cnt) - 1)
            if random.random() < 0.2:
                rand_num *= -1
            start_values.append(torch.tensor(float(rand_num), requires_grad=True))
    if random.random() < 0.01: # have a small chance to initialize all inputs with the same value
        start_values = [torch.tensor(start_values[0].item(), requires_grad=True) for _ in start_values]
    return start_values

def get_start_values_long(amount, constant_values):
    start_values = []
    special_values = [0.0, -1.0, 1.0, float(2**63 - 1), float(-2**63)]
    for val in constant_values:
        if val not in special_values:
            special_values.append(val)
    for _ in range(amount):
        if random.random() < 0.05: # have a small chance to use special values
            start_values.append(torch.tensor(random.choice(special_values), requires_grad=True))
        else:
            if random.random() < 0.5: # have a tendency towards more common numbers
                bits_cnt = random.randint(2, 14)
            else:
                bits_cnt = random.randint(15, 63)
            rand_num = random.randint(2, (1 << bits_cnt) - 1)
            if random.random() < 0.2:
                rand_num *= -1
            start_values.append(torch.tensor(float(rand_num), requires_grad=True))
    if random.random() < 0.01: # have a small chance to initialize all inputs with the same value
        start_values = [torch.tensor(start_values[0].item(), requires_grad=True) for _ in start_values]
    return start_values

def get_start_values_float(amount, constant_values):
    start_values = []
    special_values = [0.0, -1.0, 1.0, 2147483647.0, -2147483648.0]
    for val in constant_values:
        if val not in special_values:
            special_values.append(val)
    for _ in range(amount):
        if random.random() < 0.05: # have a small chance to use special values
            start_values.append(torch.tensor(random.choice(special_values), requires_grad=True))
        else:
            if random.random() < 0.7: # have a tendency towards more common numbers
                bits_cnt = random.randint(2, 14)
            else:
                bits_cnt = random.randint(15, 31)
            rand_num = random.randint(2, (1 << bits_cnt) - 1)
            if random.random() < 0.2:
                rand_num *= -1
            start_values.append(torch.tensor(float(rand_num), requires_grad=True))
    if random.random() < 0.01: # have a small chance to initialize all inputs with the same value
        start_values = [torch.tensor(start_values[0].item(), requires_grad=True) for _ in start_values]
    return start_values

def get_start_values_char(amount):
    start_values = []
    for _ in range(amount):
        if random.random() < 0.9: # have a tendency towards more common characters
            rand_num = random.randint(32, 125) # letters, numbers, special characters
        else:
            bits_cnt = random.randint(1, 16)
            rand_num = random.randint(0, (1 << bits_cnt) - 1)
        start_values.append(torch.tensor(float(rand_num), requires_grad=True))
    if random.random() < 0.01: # have a small chance to initialize all inputs with the same value
        start_values = [torch.tensor(start_values[0].item(), requires_grad=True) for _ in start_values]
    return start_values

def get_graph_builder(target_file, work_dir):
    GraalWrapper.MethodRegister.clear()
    graph_builder = GraalWrapper.GraphBuilder(target_file, work_dir=work_dir)
    return graph_builder

def main(target_file, start_nodes, end_nodes, auto_detect_start_end=False, test_dir=None, test_class=None,
         use_sv_helpers=True, return_successfull_output=False, num_iterations=1, verbose=False):
    start_time = datetime.now()
    graph_builder = get_graph_builder(target_file, work_dir=test_dir.replace('dasa_eval/', '') if test_dir else "")
    constant_nodes = {}
    if auto_detect_start_end:
        graph_builder.get_graph(0, -1, reset=True)
        start_nodes, end_nodes, constant_nodes = graph_builder.get_start_end_constant_nodes()
    else:
        new_start_nodes = []
        for start_node in start_nodes:
            if not isinstance(start_node, input_node_tuple):
                start_node = input_node_tuple(start_node, TYPE_CONV_DEFAULT)
            new_start_nodes.append(start_node)
    start_node_ids = [sn.node_id for sn in start_nodes]
    print(f"Start nodes: {start_node_ids}")
    print(f"End nodes: {end_nodes}")
    # run optimization
    results = []
    if not start_nodes:
        return STATE_NO_START_NODES_FOUND
    if not end_nodes:
        return STATE_NO_END_NODES_FOUND
    random.seed(42)
    errors = False
    for end_node in end_nodes:
        graph_builder_unchanged = get_graph_builder(target_file, work_dir=test_dir.replace('dasa_eval', '') if test_dir else "")
        new_graph_unchanged = graph_builder_unchanged.get_graph(0, end_node, reset=True, verbose=verbose)
        for iteration in range(num_iterations):
            if datetime.now() - start_time >= timedelta(minutes=10):
                break
            try:
                graph_builder = copy.deepcopy(graph_builder_unchanged)
                new_graph = copy.deepcopy(new_graph_unchanged)
                # we might not need all input variables to find an Exception
                needed_start_nodes = [n for n in start_nodes if n.node_id in new_graph.keys()]

                I_all = get_start_values(needed_start_nodes, constant_nodes)

                # Run optimization with inputs
                needed_start_node_ids = [n.node_id for n in needed_start_nodes]
                run_res = run_optimization(new_graph, needed_start_node_ids, end_node, graph_builder, verbose=verbose, I_all=I_all)
                run_res['start_nodes'] = needed_start_nodes
                run_res['end_node'] = end_node
                results.append(run_res)

                # Extract values for conversion
                applied_values = []
                for start_node, value in zip(needed_start_nodes, run_res['values']):
                    if value is None:
                        continue
                    else:
                        applied_values.append(start_node.func(value))

                print(f"Target {run_res['end_node']} Try {iteration}: "
                      f"Inputs={[n.node_id for n, v in zip(run_res['start_nodes'], run_res['values']) if v is not None]} "
                      f"Values={applied_values} "
                      f"Loss={run_res['loss']} Iteration={run_res['iteration']} "
                      f"Real Values={[v for v in run_res['values'] if v is not None]}")
                if test_dir:
                    func_input = ("\n".join([f"INPUT_{idx:03d} {v}".replace("\n", "\\n")
                                             for idx, v in enumerate(applied_values)])).encode("utf-8")
                    res = subprocess.run(["java",
                                          "-cp", f"{test_dir}:svHelpers/evaluation/" if use_sv_helpers else test_dir,
                                          "-ea", test_class if test_class else "Main"],
                                         capture_output=True, input=func_input)
                    if verbose or res.returncode != 0:
                        print("----------- Input of the test execution ------------")
                        print(func_input)
                        print("----------- Output of the test execution -----------")
                        print(res.stdout.decode("utf-8").replace("[WITNESS]", "[POSSIBLE WITNESS]"))
                        print(res.stderr.decode("utf-8"))
                        print("----------------------------------------------------")
                        if "java.lang.AssertionError" in res.stderr.decode("utf-8"):
                            for line in res.stdout.decode("utf-8").split("\n"):
                                if "[WITNESS]" in line:
                                    print(line)
                            return STATE_CORRECT if not return_successfull_output else (STATE_CORRECT, res.stdout.decode("utf-8"))
                    if ("[CANNOT PARSE NULL STRING]" in res.stdout.decode("utf-8")
                            and run_res['values'] != run_res['all_values']):
                        print("Failed to hand over all needed variables, retrying with all variables")
                        applied_values = []
                        for start_node, value in zip(needed_start_nodes, run_res['all_values']):
                            if value is None:
                                continue
                            else:
                                applied_values.append(start_node.func(value))

                        print(f"Target {run_res['end_node']} Try {iteration}_all: "
                              f"Inputs={[n.node_id for n in run_res['start_nodes']]} "
                              f"Values={applied_values} "
                              f"Loss={run_res['loss']} Iteration={run_res['iteration']} "
                              f"Real Values={run_res['all_values']}")

                        func_input = ("\n".join([f"INPUT_{idx:03d} {v}".replace("\n", "\\n")
                                                 for idx, v in enumerate(applied_values)])).encode("utf-8")
                        res = subprocess.run(["java",
                                              "-cp", f"{test_dir}:svHelpers/evaluation/" if use_sv_helpers else test_dir,
                                              "-ea", test_class if test_class else "Main"],
                                             capture_output=True, input=func_input)
                        if res.returncode != 0 and "java.lang.AssertionError" in res.stderr.decode("utf-8"):
                            for line in res.stdout.decode("utf-8").split("\n"):
                                if "[WITNESS]" in line:
                                    print(line)
                            return STATE_CORRECT if not return_successfull_output else (STATE_CORRECT, res.stdout.decode("utf-8"))
            except Exception as e:
                errors = True
                if verbose:
                    traceback.print_exc()

    if not results:
        print(f"No result found after {iteration + 1} tries")
        return STATE_ERROR if errors else STATE_DEFAULT
    print(f"Final results:")
    for result in results:
        applied_values = [n.func(v) for n, v in zip(result['start_nodes'], result['values']) if v is not None]
        print(f"Target {result['end_node']}: Inputs={[n.node_id for n in result['start_nodes']]} "
              f"Values={applied_values} "
              f"Loss={result['loss']} Iteration={result['iteration']} "
              f"Real Values={result['values']}")
    return STATE_ERROR if errors else STATE_INCORRECT


if __name__ == '__main__':
    start_nodes = [input_node_tuple(51, TYPE_CONV_INT), input_node_tuple(52, TYPE_CONV_INT)]
    end_nodes = [48]
    target_file = 'Test.main.json'
    main(target_file, start_nodes, end_nodes, auto_detect_start_end=True, test_dir="SUTs/Test44/", test_class="Test",
         num_iterations=1, verbose=True)
