# Configuration

DASA's behavior can be tuned through various parameters in the optimization process.

## Optimization Parameters

These parameters are set in `test.py:run_optimization()`:

### Iterations

```python
num_iterations = 2000  # Maximum optimization steps
```

More iterations allow finding harder-to-reach targets but increase runtime.

### Learning Rate

```python
initial_lr = 0.1  # Adam optimizer learning rate
```

- Higher values: Faster convergence but may overshoot
- Lower values: More stable but slower

### Sigmoid Annealing

```python
sigmoid_annealing_start = 0.001
sigmoid_annealing_end = 1.0
```

Controls how "soft" control flow decisions are during optimization:

- Early iterations: Soft decisions allow gradient flow through all branches
- Later iterations: Sharp decisions commit to specific paths

### Temperature Annealing (Strings)

```python
temp_start = 2.0   # High: exploratory sampling
temp_end = 0.1     # Low: sharp character selection
```

For Gumbel-Softmax string generation:

- High temperature: Smooth probability distribution
- Low temperature: Near-deterministic character selection

### Early Stopping

```python
min_loss_delta = 1e-12  # Stop if loss changes less than this
```

Optimization stops early when loss plateaus.

## Docker Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET` | `Main` | Main class name to analyze |

### Volume Mounts

```bash
docker run --rm \
  -v "/path/to/java/files:/SUT" \      # Java source files
  -v "/path/to/verifier:/svHelpers" \  # Verifier.java location
  dasa-graph-extractor
```

## Test Execution Parameters

When calling `test.main()`:

| Parameter | Type | Description |
|-----------|------|-------------|
| `target_file` | `str` | Path to JSON graph file |
| `start_nodes` | `list` | Input nodes (or `None` for auto) |
| `end_nodes` | `list` | Target nodes (or `None` for auto) |
| `auto_detect_start_end` | `bool` | Auto-detect input/target nodes |
| `test_dir` | `str` | Directory with .class files |
| `test_class` | `str` | Main class name |
| `use_sv_helpers` | `bool` | Include svHelpers in classpath |
| `return_successfull_output` | `bool` | Return stdout on success |
| `num_iterations` | `int` | Optimization attempts per target |
| `verbose` | `bool` | Print iteration progress |

## Initial Value Strategies

DASA uses smart initialization for different types:

### Integers

```python
# 70% chance: 2-14 bit values (common range)
# 30% chance: 15-31 bit values (edge cases)
# 5% chance: special values (0, -1, 1, MIN, MAX)
```

### Floats

Similar to integers but includes floating-point ranges.

### Booleans

```python
# 50% true, 50% false
```

### Characters

```python
# 90% chance: printable ASCII (32-125)
# 10% chance: full Unicode range
```

### Strings

```python
# Default length: 10 characters
# Initialization: uniform distribution or biased toward constants
```

## Timeout Configuration

In `test.py`:

```python
# 10-minute global timeout per analysis
if datetime.now() - start_time >= timedelta(minutes=10):
    break
```

## GraalVM Options

In `scripts/entrypoint.sh`:

```bash
native-image -ea \
  -H:Dump=:1 \                  # Dump compiler graphs
  -H:MaximumInliningSize=0 \    # Disable inlining
  -H:+UnlockExperimentalVMOptions \
  $TARGET
```

If graph generation fails, it retries with `-O0` (no optimization).

## Customizing Node Behavior

To modify how specific nodes behave, edit files in `nodes/`:

```
nodes/
├── calc/           # Math operations
├── java/           # Java-specific operations
├── types/          # Complex types (String, Array)
├── custom/         # Custom operations (Sigmoid)
└── BaseNode.py     # Base class for all nodes
```

Each node can define:

- `exec()`: Computation logic
- `node_penalty`: Additional loss term
- `controlFlowMultiplicative`: Path reachability score
