# Usage Examples

This page provides detailed examples for common DASA use cases.

## Example 1: Finding Integer Bounds

Find values that satisfy complex integer constraints:

```java
import org.sosy_lab.sv_benchmarks.Verifier;

class BoundsCheck {
    public static void main(String[] args) {
        int a = Verifier.nondetInt();
        int b = Verifier.nondetInt();
        int c = Verifier.nondetInt();

        if (a > 10 && a < 20) {
            if (b > a && b < 30) {
                if (c == a + b) {
                    assert false : "Found valid combination!";
                }
            }
        }
    }
}
```

DASA will find values like `a=15, b=20, c=35` that satisfy all conditions.

## Example 2: String Matching

DASA supports differentiable string generation:

```java
import org.sosy_lab.sv_benchmarks.Verifier;

class StringMatch {
    public static void main(String[] args) {
        String input = Verifier.nondetString();

        if (input.indexOf("secret") >= 0) {
            assert false : "Found secret!";
        }
    }
}
```

DASA uses Gumbel-Softmax sampling to generate strings that contain the target substring.

## Example 3: Array Operations

```java
import org.sosy_lab.sv_benchmarks.Verifier;

class ArrayBounds {
    public static void main(String[] args) {
        int[] arr = {1, 2, 3, 4, 5};
        int idx = Verifier.nondetInt();

        // This will find idx < 0 or idx >= 5
        int value = arr[idx];
        System.out.println(value);
    }
}
```

DASA targets `BytecodeExceptionNode` for array bounds violations.

## Example 4: Multiple Input Types

```java
import org.sosy_lab.sv_benchmarks.Verifier;

class MultiType {
    public static void main(String[] args) {
        int i = Verifier.nondetInt();
        double d = Verifier.nondetDouble();
        boolean b = Verifier.nondetBoolean();

        if (b && i > 100 && d > 3.14 && d < 3.15) {
            assert false : "Found precise values!";
        }
    }
}
```

## Running Multiple Iterations

For complex programs, run multiple optimization iterations:

```python
import test

result = test.main(
    target_file='Main.main.json',
    start_nodes=None,
    end_nodes=None,
    auto_detect_start_end=True,
    test_dir='SUTs/MyProgram/',
    test_class='Main',
    num_iterations=100,  # More attempts
    verbose=True         # Show progress
)
```

## Batch Analysis Script

Create a script to analyze multiple programs:

```python
#!/usr/bin/env python3
import os
import test

programs = ['Program1', 'Program2', 'Program3']

for prog in programs:
    test_dir = f'SUTs/{prog}/'
    json_file = 'Main.main.json'

    if not os.path.exists(os.path.join(test_dir, json_file)):
        print(f"Skipping {prog}: no graph file")
        continue

    result = test.main(
        target_file=json_file,
        start_nodes=None,
        end_nodes=None,
        auto_detect_start_end=True,
        test_dir=test_dir,
        test_class='Main',
        num_iterations=10
    )

    status = "VIOLATION" if result == test.STATE_CORRECT else "UNKNOWN"
    print(f"{prog}: {status}")
```

## Using Custom Start/End Nodes

For fine-grained control, specify nodes manually:

```python
from GraalWrapper.InputNodeTypes import input_node_tuple, TYPE_CONV_INT

# Specify exact input nodes and their types
start_nodes = [
    input_node_tuple(33, TYPE_CONV_INT),
    input_node_tuple(45, TYPE_CONV_INT)
]

# Target specific assertion node
end_nodes = [72]

result = test.main(
    target_file='Main.main.json',
    start_nodes=start_nodes,
    end_nodes=end_nodes,
    auto_detect_start_end=False,  # Use manual nodes
    test_dir='SUTs/MyProgram/',
    test_class='Main',
    num_iterations=10
)
```

## Handling Different Input Types

```python
from GraalWrapper.InputNodeTypes import (
    input_node_tuple,
    string_input_node_tuple,
    TYPE_CONV_INT,
    TYPE_CONV_FLOAT,
    TYPE_CONV_BOOL,
    TYPE_CONV_CHAR,
    TYPE_CONV_STRING
)

start_nodes = [
    input_node_tuple(33, TYPE_CONV_INT),
    input_node_tuple(45, TYPE_CONV_FLOAT),
    input_node_tuple(52, TYPE_CONV_BOOL),
    string_input_node_tuple(60, TYPE_CONV_STRING, string_length=20)
]
```

## Interpreting Results

The `test.main()` function returns a state code:

| Code | Constant | Meaning |
|------|----------|---------|
| 0 | `STATE_DEFAULT` | Default state |
| 1 | `STATE_NO_START_NODES_FOUND` | No input sources found |
| 2 | `STATE_NO_END_NODES_FOUND` | No target nodes found |
| 3 | `STATE_CORRECT` | Found violation (success!) |
| 4 | `STATE_INCORRECT` | No violation found |
| 5 | `STATE_ERROR` | Error during analysis |

## Verbose Output

Enable verbose mode to see optimization progress:

```python
result = test.main(
    target_file='Main.main.json',
    start_nodes=None,
    end_nodes=None,
    auto_detect_start_end=True,
    test_dir='SUTs/MyProgram/',
    test_class='Main',
    num_iterations=5,
    verbose=True  # Shows iteration-by-iteration loss
)
```

Output:
```
Iteration 0: Values=['17.00'] Loss=-0.501...
Iteration 1: Values=['17.10'] Loss=-0.502...
...
Iteration 1324: Values=['45.65'] Loss=-0.999...
```

The loss approaching `-1.0` indicates high confidence in reaching the target.
