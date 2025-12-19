# DASA - Differentiable Abstract Symbolic Analyzer

DASA is an optimization-driven engine for symbolic program analysis. Instead of using traditional constraint solvers, DASA converts Java programs into differentiable computational graphs and uses gradient-based optimization to discover inputs that lead to specific execution paths or target conditions.

## Key Features

- **Gradient-Based Analysis**: Uses PyTorch and Adam optimizer to find test inputs
- **Automatic Input Discovery**: Finds inputs that trigger assertion violations, exceptions, and specific code paths
- **Differentiable Execution**: Models control flow and computations as differentiable operations
- **Type-Aware Optimization**: Specialized handling for integers, floats, booleans, chars, and strings

## How It Works

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Java Source │───▶│   GraalVM   │───▶│   Graph     │───▶│  Gradient   │
│   Program   │    │  Compiler   │    │  Builder    │    │ Optimization│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                  │                  │
                          ▼                  ▼                  ▼
                   Compiler IR         Python Graph      Found Inputs
                   (BGV format)        (PyTorch)         (Violations)
```

1. **Compile**: GraalVM compiles Java code and exports compiler intermediate representation
2. **Build Graph**: DASA converts the IR into a differentiable PyTorch computation graph
3. **Optimize**: Gradient descent finds input values that maximize reachability to target nodes
4. **Validate**: Generated inputs are executed against the original Java program

## Quick Example

```java
// Main.java - Find input that triggers assertion
import org.sosy_lab.sv_benchmarks.Verifier;

class Main {
    public static void main(String[] args) {
        int x = Verifier.nondetInt();
        if (x >= 100) {
            assert false : "Found large value!";
        }
    }
}
```

DASA will automatically discover that `x = 100` (or any value >= 100) triggers the assertion.

## Getting Started

- [Installation](installation.md) - Set up DASA on your system
- [Quick Start](quickstart.md) - Run your first analysis in 5 minutes
- [Usage Examples](usage.md) - Detailed examples and use cases

## License

MIT License - University of Lübeck, Institute for IT Security
