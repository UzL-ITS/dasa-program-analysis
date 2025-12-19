# Contributing

Thank you for your interest in contributing to DASA!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/dasa-program-analysis.git
   ```
3. Set up the development environment (see [Installation](installation.md))

## Development Workflow

### Running Tests

```bash
# Run smoke tests
./smoketest.sh

# Or manually:
source venv/bin/activate
python3 -c "
import test
result = test.main('Main.main.json', None, None, True, 'SUTs/Smoketest1/', 'Main', 3)
assert result == 3, 'Smoketest1 failed'
print('All tests passed!')
"
```

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to new functions and classes
- Keep functions focused and small

### Adding New Node Types

1. Identify the GraalVM node class name from the JSON graph
2. Create a new Python class in `nodes/` (see [Node Types](nodes.md))
3. Register the mapping in `GraalWrapper/GraphBuilder.py`
4. Add tests for the new node type

### Testing Your Changes

Create a test case in `SUTs/`:

```bash
mkdir SUTs/MyTest
```

Create `SUTs/MyTest/Main.java` that exercises your changes.

Run the full pipeline:

```bash
# Generate graph
docker run --rm \
  -v "$(pwd)/SUTs/MyTest:/SUT" \
  -v "$(pwd)/svHelpers/evaluation:/svHelpers" \
  dasa-graph-extractor

# Compile and test
javac -cp svHelpers/evaluation SUTs/MyTest/Main.java -d SUTs/MyTest/
python3 -c "
import test
result = test.main('Main.main.json', None, None, True, 'SUTs/MyTest/', 'Main', 5)
print(f'Result: {result}')
"
```

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. Make your changes with clear commit messages

3. Ensure all tests pass

4. Push to your fork:
   ```bash
   git push origin feature/my-new-feature
   ```

5. Open a Pull Request with:
   - Clear description of the change
   - Any relevant issue numbers
   - Test results

## Areas for Contribution

### High Priority

- **New node types**: Many GraalVM node types fall back to `FallbackNode`
- **String operations**: Improve differentiable string handling
- **Performance**: Optimize the optimization loop
- **Documentation**: Improve examples and explanations

### Medium Priority

- **Error handling**: Better error messages and recovery
- **Logging**: Add structured logging
- **Configuration**: More tunable parameters
- **Visualization**: Graph visualization tools

### Good First Issues

- Add missing type converters in `InputNodeTypes.py`
- Improve error messages when graph loading fails
- Add more example programs in `SUTs/`
- Fix typos in documentation

## Code Structure

```
dasa-program-analysis/
├── test.py                 # Main entry point - optimization loop
├── run_sv-comp.py          # SV-COMP competition wrapper
├── GraalWrapper/
│   ├── GraphBuilder.py     # Graph construction (most complex)
│   ├── MethodRegister.py   # Method inlining tracking
│   └── InputNodeTypes.py   # Type conversions
├── nodes/
│   ├── BaseNode.py         # Base class for all nodes
│   ├── calc/               # Arithmetic and comparison
│   ├── java/               # Java-specific operations
│   ├── types/              # Complex types (String, Array)
│   ├── virtual/            # Object allocation
│   └── custom/             # Custom operations
├── scripts/
│   └── entrypoint.sh       # Docker entry point
├── SUTs/                   # Test programs
├── svHelpers/              # SV-COMP Verifier class
└── docs/                   # Documentation (you are here)
```

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Be respectful and constructive in discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
