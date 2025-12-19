# Node Types

DASA models GraalVM compiler nodes as differentiable Python classes. This page documents the available node types.

## Control Flow Nodes

### IfNode

Represents conditional branching. Uses sigmoid for differentiable path selection.

```python
class IfNode(BaseNode):
    # Inputs: condition (boolean/numeric)
    # Outputs to: trueSuccessor, falseSuccessor
```

**Behavior**: Distributes `controlFlowMultiplicative` to both branches based on sigmoid of condition.

### MergeNode

Combines multiple control flow paths.

```python
class MergeNode(BaseNode):
    # Takes minimum controlFlowMultiplicative from incoming paths
```

### BeginNode / EndNode

Mark the start and end of basic blocks.

### StartNode

Entry point of a method.

### ReturnNode

Method return point. Propagates values to callers.

---

## Value Nodes

### ConstantNode

Holds literal values (integers, floats, strings).

```python
class ConstantNode(BaseNode):
    def exec(self):
        # Extract value from node['props']['stamp']
        self.output = parsed_value
```

### ValuePhiNode

Selects between values based on incoming control flow (SSA phi function).

```python
class ValuePhiNode(BaseNode):
    # Selects input value from the path with highest flow
```

### ParameterNode

Method parameter. Receives values from caller.

### PiNode

Type narrowing node (e.g., after instanceof check).

---

## Arithmetic Nodes (nodes/calc/)

### Basic Operations

| Node | Operation | Example |
|------|-----------|---------|
| `AddNode` | Addition | `a + b` |
| `SubNode` | Subtraction | `a - b` |
| `MulNode` | Multiplication | `a * b` |
| `DivNode` | Division | `a / b` |
| `ModNode` | Modulo | `a % b` |
| `NegateNode` | Negation | `-a` |

### Bitwise Operations

| Node | Operation |
|------|-----------|
| `LeftShiftNode` | `a << b` |

### Comparison Nodes

| Node | Operation | Returns |
|------|-----------|---------|
| `IntegerLessThanNode` | `a < b` | Soft boolean (0.0-1.0) |
| `IntegerEqualsNode` | `a == b` | Soft boolean |
| `IntegerBelowNode` | Unsigned `a < b` | Soft boolean |
| `FloatLessThanNode` | `a < b` (float) | Soft boolean |
| `FloatEqualsNode` | `a == b` (float) | Soft boolean |
| `FloatBelowNode` | `a < b` (unsigned float) | Soft boolean |
| `ObjectEqualsNode` | Object equality | Soft boolean |
| `IsNullNode` | `a == null` | Soft boolean |

### Mathematical Functions

| Node | Function |
|------|----------|
| `SinNode` | `sin(x)` |
| `CosNode` | `cos(x)` |
| `TanNode` | `tan(x)` |
| `AsinNode` | `asin(x)` |
| `AcosNode` | `acos(x)` |
| `AtanNode` | `atan(x)` |
| `Atan2Node` | `atan2(y, x)` |
| `ExpNode` | `e^x` |
| `LogNode` | `ln(x)` |
| `Log10Node` | `log10(x)` |
| `SqrtNode` | `sqrt(x)` |
| `PowNode` | `x^y` |

### Conditional Node

```python
class ConditionalNode(BaseNode):
    # condition ? trueValue : falseValue
    # Uses soft selection based on condition
```

---

## Java Nodes (nodes/java/)

### LoadFieldNode

Loads a field from an object.

### LoadIndexedNode

Array element access: `array[index]`

### ArrayLengthNode

Returns array length: `array.length`

### ArrayEqualsNode

Compares two arrays for equality.

### CharAtNode

String character access: `str.charAt(index)`

### IndexOfNode

String search: `str.indexOf(substring)`

---

## Type Nodes (nodes/types/)

### String

Differentiable string representation using Gumbel-Softmax.

```python
class String:
    def __init__(self, length=10):
        # Each character is a probability distribution over vocabulary
        self.char_logits = [torch.randn(vocab_size) for _ in range(length)]

    def to_string(self):
        # Sample characters using current temperature
        return sampled_string
```

### Array

Represents Java arrays with differentiable access.

### BaseType

Base class for complex types.

---

## Virtual Nodes (nodes/virtual/)

### VirtualInstanceNode

Represents an object that may be stack-allocated.

### CommitAllocationNode

Materializes virtual objects to heap.

### AllocatedObjectNode

Reference to an allocated object.

---

## Invocation Nodes

### InvokeNode

Method invocation. May inline the called method's graph.

```python
class InvokeNode(BaseNode):
    def __init__(self, node):
        # Check if method should be inlined
        # Special handling for Verifier.nondet* methods
```

**Special Methods**:

- `Verifier.nondet*()`: Treated as input sources
- `FdLibm.*`: Replaced with math functions
- `String.charAt`: Uses CharAtNode
- `String.indexOf`: Uses IndexOfNode

---

## Exception Nodes

### ThrowBytecodeExceptionNode

Target node for exceptions:

- Array index out of bounds
- Null pointer
- Class cast
- Division by zero

These are typically end nodes that DASA tries to reach.

---

## Utility Nodes

### FrameState

Debugging information (not executed).

### FullInfoPointNode

Source location information.

### FallbackNode

Used for unrecognized node types. Passes through values without modification.

---

## Custom Nodes (nodes/custom/)

### Sigmoid

Annealing sigmoid function for differentiable control flow.

```python
class Sigmoid:
    annealing_constant = 0.001  # Starts soft, becomes sharp

    @classmethod
    def set_annealing_constant(cls, value):
        cls.annealing_constant = value
```

### MathFunctions

Additional mathematical operations.

---

## Adding New Node Types

To add support for a new GraalVM node type:

1. Create a new class in the appropriate directory:

```python
# nodes/calc/MyNewNode.py
from nodes.BaseNode import BaseNode

class MyNewNode(BaseNode):
    def exec(self):
        x = self.inputs['x']
        y = self.inputs['y']
        self.output = x + y  # Your computation
```

2. Register it in `GraalWrapper/GraphBuilder.py`:

```python
elif node_class == 'jdk.graal.compiler.nodes.calc.MyNewNode':
    new_graph[node['id']] = nodes.calc.MyNewNode(node)
```

3. Export it in `nodes/calc/__init__.py`:

```python
from .MyNewNode import MyNewNode
```
