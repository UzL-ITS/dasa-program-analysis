# Installation

DASA uses a two-stage pipeline: Docker for graph extraction (requires GraalVM) and local Python for optimization.

## Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Docker | 20.0+ | GraalVM graph extraction |
| Python | 3.9+ | Optimization and analysis |
| Java | 17+ | Test execution |

## Step 1: Clone the Repository

```bash
git clone https://github.com/UzL-ITS/dasa-program-analysis.git
cd dasa-program-analysis
```

## Step 2: Build the Docker Image

The Docker image contains GraalVM and seafoam for extracting compiler graphs:

```bash
docker build -t dasa-graph-extractor .
```

This will download the GraalVM base image and install required tools (Ruby, graphviz, seafoam).

!!! info "Build Time"
    The first build may take 5-10 minutes depending on your internet connection.

## Step 3: Set Up Python Environment

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Dependencies

The main dependencies are:

| Package | Purpose |
|---------|---------|
| `torch` | Gradient-based optimization |
| `numpy` | Numerical operations |
| `sympy` | Symbolic mathematics |
| `tree-sitter` | Java source parsing (for rewriting) |

## Step 4: Compile Helper Classes

Compile the SV-COMP Verifier helper class with your local Java:

```bash
cd svHelpers/evaluation
javac org/sosy_lab/sv_benchmarks/Verifier.java
cd ../..
```

## Verify Installation

Run the smoke tests to verify everything works:

=== "Two-Stage Pipeline"

    ```bash
    # Stage 1: Generate graph using Docker
    docker run --rm \
      -v "$(pwd)/SUTs/Smoketest1:/SUT" \
      -v "$(pwd)/svHelpers/evaluation:/svHelpers" \
      -e TARGET=Main \
      dasa-graph-extractor

    # Stage 2: Compile Java locally and run optimization
    javac -cp svHelpers/evaluation SUTs/Smoketest1/Main.java -d SUTs/Smoketest1/

    source venv/bin/activate
    python3 -c "
    import test
    result = test.main(
        'Main.main.json', None, None, True,
        'SUTs/Smoketest1/', 'Main', 3
    )
    print('SUCCESS!' if result == 3 else 'FAILED')
    "
    ```

=== "Full Pipeline (requires local GraalVM)"

    ```bash
    ./smoketest.sh
    ```

If you see `SUCCESS!` or `DASA_VERDICT: VIOLATION`, the installation is complete!

## Troubleshooting

### Docker Build Fails

If the Docker build fails, ensure you have enough disk space (at least 5GB) and a stable internet connection.

### Java Class Version Error

If you see `UnsupportedClassVersionError`, your local Java version is older than the Docker Java version. Recompile the Java files locally:

```bash
javac -cp svHelpers/evaluation SUTs/YourProgram/Main.java -d SUTs/YourProgram/
```

### Python Import Errors

Ensure you've activated the virtual environment and installed all dependencies:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Next Steps

- [Quick Start](quickstart.md) - Run your first analysis
- [Usage Examples](usage.md) - Learn common use cases
