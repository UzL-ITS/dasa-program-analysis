# Architecture

This page explains how DASA works internally.

## System Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                         DASA Pipeline                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐   │
│  │   Java      │     │   GraalVM   │     │   seafoam           │   │
│  │   Source    │────▶│   native-   │────▶│   bgv2json          │   │
│  │   (.java)   │     │   image     │     │                     │   │
│  └─────────────┘     └─────────────┘     └─────────────────────┘   │
│                             │                      │               │
│                             ▼                      ▼               │
│                      graal_dumps/           Method.main.json       │
│                      (BGV files)            (Graph JSON)           │
│                                                    │               │
│  ┌─────────────────────────────────────────────────┼───────────┐   │
│  │                  Python Analysis                │           │   │
│  │                                                 ▼           │   │
│  │  ┌─────────────┐     ┌─────────────┐     ┌───────────────┐  │   │
│  │  │ GraphBuilder│────▶│  PyTorch    │────▶│ run_          │  │   │
│  │  │ (load JSON) │     │  Graph      │     │ optimization  │  │   │
│  │  └─────────────┘     └─────────────┘     └───────────────┘  │   │
│  │                                                 │           │   │
│  └─────────────────────────────────────────────────┼───────────┘   │
│                                                    ▼               │
│                                          Found Input Values        │
│                                                    │               │
│  ┌─────────────────────────────────────────────────┼───────────┐   │
│  │                  Validation                     ▼           │   │
│  │            ┌─────────────────────────────────────────┐      │   │
│  │            │  java -ea Main < generated_inputs       │      │   │
│  │            │  → AssertionError (if successful)       │      │   │
│  │            └─────────────────────────────────────────┘      │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

## Stage 1: Graph Extraction

### GraalVM Compilation

GraalVM's `native-image` compiles Java to native code while dumping compiler intermediate representation:

```bash
native-image -H:Dump=:1 -H:MaximumInliningSize=0 Main
```

This creates BGV (Binary Graph Visualization) files in `graal_dumps/`.

### JSON Conversion

The `seafoam` tool converts BGV to readable JSON:

```bash
bgv2json "graal_dumps/.../[Main.main].bgv" > Main.main.json
```

### JSON Structure

```json
{
  "nodes": [
    {
      "id": 33,
      "props": {
        "node_class": {"node_class": "jdk.graal.compiler.nodes.InvokeNode"},
        "targetMethod": "Verifier.nondetInt",
        ...
      }
    },
    ...
  ],
  "edges": [
    {"from": 33, "to": 45, "props": {"name": "next", "type": "Control"}},
    ...
  ]
}
```

## Stage 2: Graph Building

### GraphBuilder Class

`GraalWrapper/GraphBuilder.py` converts JSON to Python objects:

```python
graph_builder = GraphBuilder('Main.main.json')
graph = graph_builder.get_graph(start_node=0, end_node=target)
```

### Node Type Mapping

GraalVM node classes are mapped to Python classes:

| GraalVM Node | Python Class | Purpose |
|--------------|--------------|---------|
| `ConstantNode` | `nodes.ConstantNode` | Literal values |
| `InvokeNode` | `nodes.InvokeNode` | Method calls |
| `IfNode` | `nodes.IfNode` | Conditional branches |
| `AddNode` | `nodes.calc.AddNode` | Integer addition |
| `IntegerLessThanNode` | `nodes.calc.IntegerLessThanNode` | Comparison |
| `ThrowBytecodeExceptionNode` | Target node | Assertion/exception |

### Backward Slicing

Only nodes reachable from the target are included:

```python
def do_backward_slicing(self, graph, end_node):
    # BFS from end_node to find all contributing nodes
    visited = set()
    queue = [end_node]
    while queue:
        node = queue.pop(0)
        visited.add(node)
        for edge in graph['edges']:
            if edge['to'] == node and edge['from'] not in visited:
                queue.append(edge['from'])
    return visited
```

## Stage 3: Optimization

### Control Flow Modeling

Each node has a `controlFlowMultiplicative` score (0.0 to 1.0) indicating path reachability:

```python
class BaseNode:
    def __init__(self, node):
        self.controlFlowMultiplicative = torch.tensor(1.0)
```

At merge points, the minimum is taken:

```python
self.controlFlowMultiplicative = torch.min(
    incoming_flow,
    self.controlFlowMultiplicative
)
```

### Differentiable Conditionals

`IfNode` uses a sigmoid to make branching differentiable:

```python
class IfNode(BaseNode):
    def exec(self):
        condition = self.inputs['condition']
        # Sigmoid makes this differentiable
        prob_true = torch.sigmoid(condition * annealing_factor)
        prob_false = 1 - prob_true

        self.children['trueSuccessor'].controlFlowMultiplicative *= prob_true
        self.children['falseSuccessor'].controlFlowMultiplicative *= prob_false
```

### Loss Function

The loss maximizes reachability to the target:

```python
loss = -graph[target_node].controlFlowMultiplicative

# Add penalties for complex operations
for node in graph.values():
    if node.node_penalty:
        loss += node.node_penalty
```

### Adam Optimizer

```python
optimizer = optim.Adam(input_parameters, lr=0.1)

for i in range(num_iterations):
    optimizer.zero_grad()

    # Forward pass: execute graph
    execute_graph(graph, inputs)

    # Compute loss
    loss = -graph[target].controlFlowMultiplicative

    # Backward pass: compute gradients
    loss.backward()

    # Update inputs
    optimizer.step()
```

## Stage 4: Validation

Generated inputs are fed to the actual Java program:

```python
inputs = "INPUT_000 42\nINPUT_001 17"
result = subprocess.run(
    ["java", "-ea", "Main"],
    input=inputs.encode(),
    capture_output=True
)

if "AssertionError" in result.stderr.decode():
    return STATE_CORRECT
```

## Key Design Decisions

### Why GraalVM?

- Produces detailed compiler IR with semantic information
- BGV format captures control flow, data flow, and type information
- `native-image` enables ahead-of-time analysis

### Why Gradient Descent?

- Scales to complex constraint combinations
- Handles non-linear relationships naturally
- Annealing allows exploration then exploitation

### Why Differentiable Execution?

- Gradients guide search toward targets
- Soft control flow enables gradient flow through branches
- Temperature annealing sharpens decisions over time

## File Structure

```
dasa-program-analysis/
├── test.py                 # Main optimization loop
├── run_sv-comp.py          # SV-COMP competition entry
├── GraalWrapper/
│   ├── GraphBuilder.py     # JSON → Python graph
│   ├── MethodRegister.py   # Inlined method tracking
│   └── InputNodeTypes.py   # Type conversion utilities
├── nodes/
│   ├── BaseNode.py         # Base class
│   ├── IfNode.py           # Conditional branching
│   ├── calc/               # Arithmetic operations
│   ├── java/               # Java operations
│   ├── types/              # Complex types
│   └── custom/             # Custom operations
├── scripts/
│   └── entrypoint.sh       # Docker entry point
└── Dockerfile              # GraalVM container
```
