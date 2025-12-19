# API Reference

This page documents the main Python API for using DASA programmatically.

## test.main()

The primary entry point for running DASA analysis.

```python
def main(
    target_file: str,
    start_nodes: list | None,
    end_nodes: list | None,
    auto_detect_start_end: bool = False,
    test_dir: str | None = None,
    test_class: str | None = None,
    use_sv_helpers: bool = True,
    return_successfull_output: bool = False,
    num_iterations: int = 1,
    verbose: bool = False
) -> int | tuple[int, str]
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_file` | `str` | required | Path to the JSON graph file (e.g., `Main.main.json`) |
| `start_nodes` | `list[input_node_tuple]` | `None` | List of input source nodes. Set to `None` with `auto_detect_start_end=True` |
| `end_nodes` | `list[int]` | `None` | List of target node IDs. Set to `None` with `auto_detect_start_end=True` |
| `auto_detect_start_end` | `bool` | `False` | Automatically detect input and target nodes from `Verifier.*` calls |
| `test_dir` | `str` | `None` | Directory containing compiled `.class` files for validation |
| `test_class` | `str` | `None` | Name of the main class to execute |
| `use_sv_helpers` | `bool` | `True` | Include `svHelpers/evaluation/` in the Java classpath |
| `return_successfull_output` | `bool` | `False` | Return stdout along with result code on success |
| `num_iterations` | `int` | `1` | Number of optimization attempts per target node |
| `verbose` | `bool` | `False` | Print detailed iteration progress |

### Return Values

| Code | Constant | Description |
|------|----------|-------------|
| 0 | `STATE_DEFAULT` | Default/unset state |
| 1 | `STATE_NO_START_NODES_FOUND` | No `Verifier.nondet*()` calls found |
| 2 | `STATE_NO_END_NODES_FOUND` | No assertion/exception targets found |
| 3 | `STATE_CORRECT` | Successfully found violation |
| 4 | `STATE_INCORRECT` | Ran but no violation triggered |
| 5 | `STATE_ERROR` | Error during analysis |

If `return_successfull_output=True` and a violation is found, returns `(STATE_CORRECT, stdout_string)`.

### Example

```python
import test

result = test.main(
    target_file='Main.main.json',
    start_nodes=None,
    end_nodes=None,
    auto_detect_start_end=True,
    test_dir='SUTs/MyProgram/',
    test_class='Main',
    num_iterations=10,
    verbose=True
)

if result == test.STATE_CORRECT:
    print("Found violation!")
```

---

## test.run_optimization()

Low-level optimization function. Called internally by `main()`.

```python
def run_optimization(
    graph: dict,
    input_ids: list[int],
    output_id: int,
    graph_builder: GraphBuilder,
    verbose: bool = False,
    I_all: list | None = None
) -> dict
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `graph` | `dict[int, BaseNode]` | Constructed computation graph |
| `input_ids` | `list[int]` | Node IDs for input sources |
| `output_id` | `int` | Target node ID |
| `graph_builder` | `GraphBuilder` | Graph builder instance |
| `verbose` | `bool` | Print iteration progress |
| `I_all` | `list` | Initial input values (auto-generated if `None`) |

### Returns

```python
{
    "iteration": int,      # Final iteration count
    "loss": float,         # Final loss value
    "values": list,        # Discovered input values (None for unused)
    "all_values": list     # All input values including unused
}
```

---

## GraalWrapper.GraphBuilder

Loads and constructs computation graphs from GraalVM JSON output.

```python
class GraphBuilder:
    def __init__(
        self,
        graph_json_file: str,
        work_dir: str | None = None,
        rec_list: list | None = None
    )
```

### Methods

#### get_graph()

```python
def get_graph(
    self,
    start_node: int,
    end_node: int,
    reset: bool = False,
    verbose: bool = False
) -> dict[int, BaseNode]
```

Returns the constructed graph as a dictionary mapping node IDs to node objects.

#### get_start_end_constant_nodes()

```python
def get_start_end_constant_nodes(self) -> tuple[list, list, dict]
```

Auto-detects:

- `start_nodes`: Nodes from `Verifier.nondet*()` calls
- `end_nodes`: Nodes for assertions/exceptions
- `constant_nodes`: Constant values in the program

---

## InputNodeTypes

Type conversion utilities for input nodes.

### input_node_tuple

```python
from GraalWrapper.InputNodeTypes import input_node_tuple

node = input_node_tuple(node_id=33, func=TYPE_CONV_INT)
```

### string_input_node_tuple

```python
from GraalWrapper.InputNodeTypes import string_input_node_tuple

node = string_input_node_tuple(
    node_id=45,
    func=TYPE_CONV_STRING,
    string_length=20
)
```

### Type Converters

| Constant | Java Type | Description |
|----------|-----------|-------------|
| `TYPE_CONV_INT` | `int` | 32-bit signed integer |
| `TYPE_CONV_LONG` | `long` | 64-bit signed integer |
| `TYPE_CONV_FLOAT` | `float` | 32-bit float |
| `TYPE_CONV_BOOL` | `boolean` | Boolean |
| `TYPE_CONV_CHAR` | `char` | 16-bit Unicode character |
| `TYPE_CONV_BYTE` | `byte` | 8-bit signed integer |
| `TYPE_CONV_SHORT` | `short` | 16-bit signed integer |
| `TYPE_CONV_STRING` | `String` | String (use `string_input_node_tuple`) |
| `TYPE_CONV_DEFAULT` | varies | Default conversion |

---

## nodes.BaseNode

Base class for all computation nodes.

```python
class BaseNode:
    def __init__(self, node: dict):
        self.node = node                    # Original JSON node data
        self.controlFlowMultiplicative = torch.tensor(1.0)
        self.node_penalty = 0               # Additional loss term
        self.children = {}                  # Child nodes
        self.inputs = {}                    # Input values
        self.output = None                  # Computed output
        self.executed = False               # Has been executed
```

### Key Methods

| Method | Description |
|--------|-------------|
| `exec()` | Perform node computation |
| `add_child(child, edge)` | Register a child node |
| `add_parent(parent, edge)` | Register a parent node |
| `add_input(value, edge, flow)` | Receive input value |
| `set_output(value)` | Propagate output to children |
| `reset_inputs()` | Reset for new iteration |

---

## nodes.types.String

Differentiable string type using Gumbel-Softmax.

```python
from nodes.types import String

s = String(
    length=10,
    initialization_bias='uniform',
    initialization_words=set()
)

# Get optimizable parameters for Adam
params = s.get_optimize_parameter()

# Convert to actual string
text = s.to_string()
```

### Class Methods

```python
String.set_temperature(0.5)  # Set Gumbel-Softmax temperature
```

---

## nodes.custom.Sigmoid

Annealing sigmoid for differentiable control flow.

```python
from nodes.custom import Sigmoid

# Set annealing constant (0.001 to 1.0)
Sigmoid.set_annealing_constant(0.5)
```

Lower values = softer decisions (more gradient flow)
Higher values = sharper decisions (more discrete)
