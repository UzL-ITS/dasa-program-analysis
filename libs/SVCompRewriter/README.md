# SVComp Verifier Rewriter

A Python tool that transforms Java projects by instrumenting `Verifier.nonDet*` calls with witness logging. This tool automatically adds line numbers, class names (in bytecode format), and method descriptors (in bytecode format) to all non-deterministic value calls.

## Features

- Parses Java code using tree-sitter for accurate AST-based transformations
- Automatically detects all `Verifier.nonDet*` method calls
- Wraps calls with `Witness.recordAndReturnValue*` methods that log and return values
- Generates method descriptors in Java bytecode format (e.g., `main([Ljava/lang/String;)V`)
- Generates class names in bytecode format (e.g., `com/example/MyClass`)
- Supports all nonDet types: boolean, byte, char, short, int, long, float, double, String
- Handles both `nondetBool()` and `nondetBoolean()` variants
- Automatically generates the `Witness.java` helper class
- Processes single files or entire directory trees

## Installation

```bash
# Create virtual environment (if not already created)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Process a single file

Overwrite the original file:
```bash
python rewriter.py Test.java
```

Save to output directory:
```bash
python rewriter.py Test.java -o output/
```

### Process a directory

Process all Java files recursively:
```bash
python rewriter.py src/ -o output/
```

### Specify package for Witness class

```bash
python rewriter.py src/ -o output/ --package org.example
```

## Example Transformation

### Before:
```java
public class Main {
    public static void main(String[] args) {
        int x = Verifier.nondetInt();
        if (x > 0) {
            System.out.println("Positive");
        }
    }
}
```

### After:
```java
public class Main {
    public static void main(String[] args) {
        int x = Witness.recordAndReturnValueInt(Verifier.nondetInt(), 3, "Main", "main([Ljava/lang/String;)V");
        if (x > 0) {
            System.out.println("Positive");
        }
    }
}
```

The tool also generates `Witness.java`:
```java
import java.util.Base64;

public class Witness {
    public static int recordAndReturnValueInt(int value, int lineNumber, String cname, String desc) {
        String witness = value + "@@@" + lineNumber + "@@@" + cname + "@@@" + desc;
        String enc = Base64.getEncoder().encodeToString(witness.getBytes());
        System.out.println("[WITNESS] " + enc);
        return value;
    }
    // ... other methods for each type
}
```

## Witness Output Format

The witness information is encoded as:
```
[WITNESS] <base64-encoded-string>
```

Where the decoded string contains:
```
<value>@@@<lineNumber>@@@<className>@@@<methodDescriptor>
```

Example:
```
42@@@32@@@Main@@@main([Ljava/lang/String;)V
```

This means:
- Value: `42`
- Line number: `32`
- Class: `Main`
- Method: `main([Ljava/lang/String;)V` (main method taking String array, returning void)

## Bytecode Descriptor Format

### Method Descriptors

Format: `methodName(parameterTypes)returnType`

Examples:
- `main([Ljava/lang/String;)V` - main method taking String[], returning void
- `equals(Ljava/lang/Object;)Z` - equals method taking Object, returning boolean
- `add(II)I` - method taking two ints, returning int

### Type Descriptors

| Java Type | Bytecode Descriptor |
|-----------|-------------------|
| boolean   | Z                 |
| byte      | B                 |
| char      | C                 |
| short     | S                 |
| int       | I                 |
| long      | J                 |
| float     | F                 |
| double    | D                 |
| void      | V                 |
| Object    | Ljava/lang/Object; |
| String    | Ljava/lang/String; |
| int[]     | [I                |
| String[]  | [Ljava/lang/String; |

### Class Names

Package separators are replaced with `/`:
- `com.example.MyClass` → `com/example/MyClass`
- `Main` → `Main` (no package)

## Architecture

The tool consists of four main components:

1. **`bytecode_utils.py`** - Converts Java types and method signatures to bytecode descriptor format
2. **`witness_generator.py`** - Generates the `Witness.java` helper class
3. **`java_rewriter.py`** - Core AST transformation logic using tree-sitter
4. **`rewriter.py`** - CLI interface for processing files and directories

## Supported Verifier Methods

All standard SV-COMP Verifier methods are supported:
- `nondetBoolean()` / `nondetBool()`
- `nondetByte()`
- `nondetChar()`
- `nondetShort()`
- `nondetInt()`
- `nondetLong()`
- `nondetFloat()`
- `nondetDouble()`
- `nondetString()`

## Limitations

- Requires valid Java syntax (the tool will fail on malformed code)
- Type resolution for complex generic types may not be perfect
- Inner classes use `$` separator (standard bytecode format)

## Requirements

- Python 3.8+
- tree-sitter 0.21.3+
- tree-sitter-java 0.21.0+

## License

This tool is provided as-is for research and educational purposes.

## References

- [SV-COMP Verifier class](https://gitlab.com/sosy-lab/benchmarking/sv-benchmarks/-/blob/main/java/common/org/sosy_lab/sv_benchmarks/Verifier.java)
- [SWAT Witness class](https://github.com/SWAT-project/SWAT/blob/945335b347be87936578cdf409ec5f1dfda605d9/symbolic-executor/src/main/java/de/uzl/its/swat/witness/Witness.java)
- [Tree-sitter](https://tree-sitter.github.io/)
