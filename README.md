# DASA

[![Documentation](https://img.shields.io/badge/docs-online-blue)](https://uzl-its.github.io/dasa-program-analysis/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)

**DASA** (Differentiable Abstract Symbolic Analyzer) is an optimization-driven engine for symbolic program analysis.

Instead of using traditional constraint solvers, DASA converts Java programs into differentiable computational graphs and uses gradient-based optimization (PyTorch) to discover inputs that trigger specific execution paths, assertions, or exceptions.

## How It Works

```
Java Source → GraalVM Compiler → Computation Graph → Gradient Optimization → Found Inputs
```

1. **Compile**: GraalVM compiles Java and exports compiler intermediate representation
2. **Build Graph**: DASA converts the IR into a differentiable PyTorch computation graph
3. **Optimize**: Adam optimizer finds input values that maximize reachability to target nodes
4. **Validate**: Generated inputs are executed against the original program to confirm violations

## Quick Start

### Prerequisites

- Docker (for GraalVM graph extraction)
- Python 3.9+
- Java 17+ (for test execution)

### Installation

```bash
git clone https://github.com/UzL-ITS/dasa-program-analysis.git
cd dasa-program-analysis

# Build Docker image
docker build -t dasa-graph-extractor .

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Compile helper classes
cd svHelpers/evaluation && javac org/sosy_lab/sv_benchmarks/Verifier.java && cd ../..
```

### Example

Create a test program `SUTs/MyTest/Main.java`:

```java
import org.sosy_lab.sv_benchmarks.Verifier;

class Main {
    public static void main(String[] args) {
        int x = Verifier.nondetInt();
        if (x >= 42) {
            assert false : "Found it!";
        }
    }
}
```

Run DASA:

```bash
# Stage 1: Extract graph using Docker
docker run --rm \
  -v "$(pwd)/SUTs/MyTest:/SUT" \
  -v "$(pwd)/svHelpers/evaluation:/svHelpers" \
  dasa-graph-extractor

# Stage 2: Compile locally and run optimization
javac -cp svHelpers/evaluation SUTs/MyTest/Main.java -d SUTs/MyTest/

source venv/bin/activate
python3 -c "
import test
result = test.main('Main.main.json', None, None, True, 'SUTs/MyTest/', 'Main', 5)
print('VIOLATION FOUND!' if result == 3 else 'No violation')
"
```

DASA will discover that `x = 42` (or higher) triggers the assertion.

## Features

- **Gradient-Based Analysis**: Uses PyTorch and Adam optimizer for input discovery
- **Automatic Target Detection**: Finds `Verifier.nondet*()` inputs and assertion/exception targets
- **Type-Aware Optimization**: Specialized handling for int, long, float, boolean, char, and String
- **Differentiable Strings**: Gumbel-Softmax sampling for string input generation
- **SV-COMP Compatible**: Generates witnesses in SV-COMP format

## Documentation

Full documentation is available at **[uzl-its.github.io/dasa-program-analysis](https://uzl-its.github.io/dasa-program-analysis/)**

- [Installation Guide](https://uzl-its.github.io/dasa-program-analysis/installation/)
- [Quick Start Tutorial](https://uzl-its.github.io/dasa-program-analysis/quickstart/)
- [Usage Examples](https://uzl-its.github.io/dasa-program-analysis/usage/)
- [Architecture](https://uzl-its.github.io/dasa-program-analysis/architecture/)
- [API Reference](https://uzl-its.github.io/dasa-program-analysis/api/)

## Project Structure

```
dasa-program-analysis/
├── test.py                 # Main optimization loop
├── run_sv-comp.py          # SV-COMP competition wrapper
├── GraalWrapper/           # Graph loading and construction
├── nodes/                  # Differentiable node implementations
├── scripts/                # Docker entrypoint
├── SUTs/                   # Example test programs
├── svHelpers/              # SV-COMP Verifier class
└── docs/                   # MkDocs documentation source
```

## License

MIT License - University of Lübeck, Institute for IT Security

See [LICENSE.txt](LICENSE.txt) for details.
