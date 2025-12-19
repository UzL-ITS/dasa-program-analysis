# Quick Start

This guide will walk you through analyzing your first Java program with DASA.

## Create a Test Program

Create a directory for your program:

```bash
mkdir -p SUTs/MyFirstTest
```

Create `SUTs/MyFirstTest/Main.java`:

```java
import org.sosy_lab.sv_benchmarks.Verifier;

class Main {
    public static void main(String[] args) {
        int x = Verifier.nondetInt();
        int y = Verifier.nondetInt();

        if (x > 0 && y > 0 && x + y == 42) {
            assert false : "Found the answer!";
        }

        System.out.println("No solution found");
    }
}
```

This program has a hidden assertion that triggers when `x + y == 42` with both positive.

## Stage 1: Extract the Computation Graph

Use Docker to compile with GraalVM and extract the compiler graph:

```bash
docker run --rm \
  -v "$(pwd)/SUTs/MyFirstTest:/SUT" \
  -v "$(pwd)/svHelpers/evaluation:/svHelpers" \
  -e TARGET=Main \
  dasa-graph-extractor
```

You should see GraalVM native-image output, ending with:

```
Graph generation complete!
-rw-r--r-- 1 root root XXXXX /SUT/Main.main.json
```

## Stage 2: Run the Optimization

First, compile the Java file locally (for test execution):

```bash
javac -cp svHelpers/evaluation SUTs/MyFirstTest/Main.java -d SUTs/MyFirstTest/
```

Now run the DASA optimization:

```bash
source venv/bin/activate
python3 -c "
import test

result = test.main(
    target_file='Main.main.json',
    start_nodes=None,
    end_nodes=None,
    auto_detect_start_end=True,
    test_dir='SUTs/MyFirstTest/',
    test_class='Main',
    num_iterations=10,
    verbose=False
)

if result == test.STATE_CORRECT:
    print('SUCCESS: Found inputs that trigger the assertion!')
else:
    print('No violation found')
"
```

## Understanding the Output

DASA will output something like:

```
Start nodes: [33, 45]
End nodes: [72]
Target 72 Try 0: Inputs=[33, 45] Values=[21, 21] Loss=-0.999...
----------- Input of the test execution ------------
b'INPUT_000 21\nINPUT_001 21'
----------- Output of the test execution -----------
Exception in thread "main" java.lang.AssertionError: Found the answer!
```

This shows:

- **Start nodes**: The `Verifier.nondetInt()` calls (input sources)
- **End nodes**: The assertion/exception target
- **Values**: The discovered inputs (`x=21, y=21`, and `21+21=42`)
- **AssertionError**: Confirms the violation was triggered

## Using the Verifier API

DASA uses the SV-COMP Verifier class for nondeterministic inputs:

| Method | Type | Description |
|--------|------|-------------|
| `Verifier.nondetInt()` | `int` | Nondeterministic 32-bit integer |
| `Verifier.nondetLong()` | `long` | Nondeterministic 64-bit integer |
| `Verifier.nondetFloat()` | `float` | Nondeterministic float |
| `Verifier.nondetDouble()` | `double` | Nondeterministic double |
| `Verifier.nondetBoolean()` | `boolean` | Nondeterministic boolean |
| `Verifier.nondetChar()` | `char` | Nondeterministic character |
| `Verifier.nondetString()` | `String` | Nondeterministic string |
| `Verifier.nondetByte()` | `byte` | Nondeterministic byte |
| `Verifier.nondetShort()` | `short` | Nondeterministic short |

## What DASA Finds

DASA automatically detects and targets:

- `assert false` statements
- `throw new AssertionError()`
- `BytecodeExceptionNode` (array bounds, null pointer, etc.)

## Next Steps

- [Usage Examples](usage.md) - More complex examples
- [Architecture](architecture.md) - How DASA works internally
- [Configuration](configuration.md) - Tuning optimization parameters
