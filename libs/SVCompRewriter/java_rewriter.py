"""
Main Java code rewriter that transforms Verifier.nonDet* calls.
"""

import re
from typing import List, Tuple, Optional
from tree_sitter import Node, Parser, Language
from tree_sitter_java import language as java_language
from bytecode_utils import BytecodeDescriptorGenerator
from witness_generator import WitnessGenerator


class VerifierCallInfo:
    """Information about a Verifier.nonDet* call."""

    def __init__(self, node: Node, line: int, method_name: str,
                 enclosing_class: str, enclosing_method_desc: str):
        self.node = node
        self.line = line
        self.method_name = method_name  # e.g., "nondetInt"
        self.enclosing_class = enclosing_class  # e.g., "Main"
        self.enclosing_method_desc = enclosing_method_desc  # e.g., "main([Ljava/lang/String;)V"

    def __repr__(self):
        return f"VerifierCall({self.method_name} at line {self.line} in {self.enclosing_class}.{self.enclosing_method_desc})"


class JavaRewriter:
    """Rewrites Java source code to instrument Verifier.nonDet* calls."""

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.source_bytes = source_code.encode('utf-8')
        self.parser = Parser(Language(java_language()))
        self.tree = self.parser.parse(self.source_bytes)
        self.bytecode_gen = BytecodeDescriptorGenerator(self.source_bytes)
        self.package = None
        self.witness_needed = False

    def rewrite(self) -> str:
        """
        Main method to rewrite the Java source code.

        Returns:
            Transformed Java source code
        """
        # Extract package name
        self.package = self._extract_package()

        # Find all Verifier.nonDet* calls
        verifier_calls = self._find_verifier_calls(self.tree.root_node)

        if not verifier_calls:
            return self.source_code

        # Mark that we need to import Witness
        self.witness_needed = True

        # Transform code by replacing calls
        transformed_code = self._transform_code(verifier_calls)

        # Add Witness import if needed
        transformed_code = self._add_witness_import(transformed_code)

        return transformed_code

    def _extract_package(self) -> Optional[str]:
        """Extract the package name from the source code."""
        for child in self.tree.root_node.children:
            if child.type == 'package_declaration':
                for subchild in child.children:
                    if subchild.type == 'scoped_identifier' or subchild.type == 'identifier':
                        return self.bytecode_gen.get_text(subchild)
        return None

    def _find_verifier_calls(self, node: Node,
                            enclosing_class: Optional[str] = None,
                            enclosing_method: Optional[Node] = None) -> List[VerifierCallInfo]:
        """
        Recursively find all Verifier.nonDet* method calls in the AST.
        """
        calls = []

        # Track enclosing class
        if node.type in ['class_declaration', 'interface_declaration']:
            enclosing_class = self._get_class_name(node)

        # Track enclosing method
        if node.type == 'method_declaration':
            enclosing_method = node

        # Check if this node is a method invocation
        if node.type == 'method_invocation':
            call_info = self._check_verifier_call(node, enclosing_class, enclosing_method)
            if call_info:
                calls.append(call_info)

        # Recursively check children
        for child in node.children:
            calls.extend(self._find_verifier_calls(child, enclosing_class, enclosing_method))

        return calls

    def _check_verifier_call(self, node: Node,
                            enclosing_class: Optional[str],
                            enclosing_method: Optional[Node]) -> Optional[VerifierCallInfo]:
        """Check if a method invocation is a Verifier.nonDet* call."""
        # Method invocation structure:
        # (method_invocation
        #   object: (identifier) @object
        #   name: (identifier) @method_name
        #   arguments: (argument_list))

        method_name = None
        object_name = None

        for child in node.children:
            if child.type == 'identifier':
                if object_name is None:
                    object_name = self.bytecode_gen.get_text(child)
                else:
                    method_name = self.bytecode_gen.get_text(child)
            elif child.type == 'field_access':
                # Handle Verifier.nondetInt() case
                object_name, method_name = self._parse_field_access(child)

        # Check if it's a Verifier.nonDet* call
        if object_name == 'Verifier' and method_name and method_name.startswith('nondet'):
            line = node.start_point[0] + 1  # tree-sitter uses 0-indexed lines

            # Get enclosing method descriptor
            method_desc = "unknown()V"
            if enclosing_method:
                method_desc = self.bytecode_gen.get_method_descriptor(enclosing_method)

            # Get enclosing class name
            class_name = enclosing_class or "Unknown"

            return VerifierCallInfo(
                node=node,
                line=line,
                method_name=method_name,
                enclosing_class=class_name,
                enclosing_method_desc=method_desc
            )

        return None

    def _parse_field_access(self, node: Node) -> Tuple[Optional[str], Optional[str]]:
        """Parse a field_access node to get object and field names."""
        object_name = None
        field_name = None

        for child in node.children:
            if child.type == 'identifier':
                if object_name is None:
                    object_name = self.bytecode_gen.get_text(child)
                else:
                    field_name = self.bytecode_gen.get_text(child)

        return object_name, field_name

    def _get_class_name(self, node: Node) -> str:
        """Extract class name from a class_declaration node."""
        for child in node.children:
            if child.type == 'identifier':
                return self.bytecode_gen.get_text(child)
        return "Unknown"

    def _transform_code(self, verifier_calls: List[VerifierCallInfo]) -> str:
        """
        Transform the source code by replacing Verifier calls with instrumented versions.

        Strategy: Work backwards through the calls to preserve byte offsets.
        """
        # Sort calls by position (backwards to preserve offsets during replacement)
        sorted_calls = sorted(verifier_calls, key=lambda c: c.node.start_byte, reverse=True)

        # Convert source to list of characters for easier manipulation
        lines = self.source_code.split('\n')

        for call_info in sorted_calls:
            lines = self._replace_call(lines, call_info)

        return '\n'.join(lines)

    def _replace_call(self, lines: List[str], call_info: VerifierCallInfo) -> List[str]:
        """
        Replace a single Verifier.nonDet* call with an instrumented version.

        Transform:
            Verifier.nondetInt()
        Into:
            Verifier.nondetInt(); Witness.recordValueInt(temp_var, line, class, method)

        But we need to capture the value, so we use an immediately invoked lambda or helper.

        Actually, better approach:
            ({int $temp = Verifier.nondetInt(); Witness.recordValueInt($temp, ...); $temp;})

        But Java doesn't have statement expressions. So we need to be context-aware:

        If it's used in an expression, we need to extract it to a variable.
        If it's a standalone statement, we can add the witness call after.

        For simplicity, let's use a wrapper approach that always works:
        Create a static helper method that takes the value and returns it after logging.

        But that requires modifying the Witness class dynamically...

        Better: Always extract to a temp variable before the statement.
        """
        node = call_info.node
        start_line = node.start_point[0]
        end_line = node.end_point[0]
        start_col = node.start_point[1]
        end_col = node.end_point[1]

        # Get the original call text
        if start_line == end_line:
            original_call = lines[start_line][start_col:end_col]
        else:
            # Multi-line call (rare, but possible)
            original_call = lines[start_line][start_col:]
            for i in range(start_line + 1, end_line):
                original_call += '\n' + lines[i]
            original_call += '\n' + lines[end_line][:end_col]

        # Generate the witness call
        java_type = WitnessGenerator.get_java_type(call_info.method_name)
        record_method = WitnessGenerator.get_record_method_name(call_info.method_name)

        # Get class internal name
        class_internal = self.bytecode_gen.get_class_internal_name(self.package, call_info.enclosing_class)

        # Create the transformation
        # We'll use: ((TYPE)(__witness_helper(Verifier.nondetX(), line, class, method)))
        # But Java doesn't have statement expressions...

        # Simplest approach: Use a helper that returns the value
        # Let's modify Witness to have: recordValueInt(int val, ...) that returns val

        # Actually, looking at the SWAT code, they just print. So we need a different strategy.
        # Let's wrap: Witness.recordValueInt((temp_var = Verifier.nondetInt()), ...)
        # But recordValue doesn't return anything...

        # Best approach: Use inline assignment with comma trick via helper
        # Or: Generate wrapper methods in Witness that return the value

        # For now, let's use a simple approach: replace with a method call that does both
        # We'll need to update WitnessGenerator to create methods that return the value

        replacement = f"Witness.recordAndReturnValue{record_method[len('recordValue'):]}({original_call}, {call_info.line}, \"{class_internal}\", \"{call_info.enclosing_method_desc}\")"

        # Replace in the line
        if start_line == end_line:
            lines[start_line] = lines[start_line][:start_col] + replacement + lines[start_line][end_col:]
        else:
            # Multi-line replacement (rare)
            lines[start_line] = lines[start_line][:start_col] + replacement
            for i in range(start_line + 1, end_line + 1):
                lines[i] = ''

        return lines

    def _add_witness_import(self, code: str) -> str:
        """Add import statement for Witness class if not already present."""
        if 'import' in code and 'Witness' not in code:
            # Add after existing imports
            lines = code.split('\n')
            last_import_idx = -1

            for i, line in enumerate(lines):
                if line.strip().startswith('import '):
                    last_import_idx = i

            if last_import_idx >= 0:
                # Add after last import
                if self.package:
                    witness_import = f"import {self.package}.Witness;"
                else:
                    witness_import = "// Witness class should be in the same package"
                lines.insert(last_import_idx + 1, witness_import)
                return '\n'.join(lines)

        # If no imports, add after package declaration
        if self.package:
            package_line = f"package {self.package};"
            if package_line in code:
                witness_import = f"\nimport {self.package}.Witness;\n"
                return code.replace(package_line, package_line + witness_import)

        return code
