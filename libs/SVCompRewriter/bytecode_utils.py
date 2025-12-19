"""
Utilities for converting Java types and method signatures to bytecode descriptor format.
"""

from typing import Dict, List, Optional
from tree_sitter import Node


class BytecodeDescriptorGenerator:
    """Generates bytecode descriptors for Java types and methods."""

    # Primitive type mappings
    PRIMITIVE_DESCRIPTORS: Dict[str, str] = {
        'boolean': 'Z',
        'byte': 'B',
        'char': 'C',
        'short': 'S',
        'int': 'I',
        'long': 'J',
        'float': 'F',
        'double': 'D',
        'void': 'V'
    }

    # Common type mappings for quick resolution
    COMMON_TYPES: Dict[str, str] = {
        'String': 'java/lang/String',
        'Object': 'java/lang/Object',
        'Integer': 'java/lang/Integer',
        'Long': 'java/lang/Long',
        'Double': 'java/lang/Double',
        'Float': 'java/lang/Float',
        'Boolean': 'java/lang/Boolean',
        'Byte': 'java/lang/Byte',
        'Short': 'java/lang/Short',
        'Character': 'java/lang/Character',
        'StringBuilder': 'java/lang/StringBuilder',
        'StringBuffer': 'java/lang/StringBuffer',
        'List': 'java/util/List',
        'Map': 'java/util/Map',
        'Set': 'java/util/Set',
    }

    def __init__(self, source_code: bytes):
        self.source_code = source_code

    def get_text(self, node: Node) -> str:
        """Extract text from a tree-sitter node."""
        return self.source_code[node.start_byte:node.end_byte].decode('utf-8')

    def get_type_descriptor(self, type_node: Node) -> str:
        """
        Convert a Java type to bytecode descriptor format.

        Examples:
        - int -> I
        - String -> Ljava/lang/String;
        - int[] -> [I
        - String[][] -> [[Ljava/lang/String;
        """
        if type_node is None:
            return 'V'

        type_text = self.get_text(type_node).strip()

        # Handle array types
        array_dims = type_text.count('[')
        base_type = type_text.replace('[', '').replace(']', '').strip()

        # Get base type descriptor
        if base_type in self.PRIMITIVE_DESCRIPTORS:
            descriptor = self.PRIMITIVE_DESCRIPTORS[base_type]
        else:
            # Object type
            class_name = self._resolve_class_name(base_type)
            descriptor = f'L{class_name};'

        # Add array brackets
        return '[' * array_dims + descriptor

    def _resolve_class_name(self, class_name: str) -> str:
        """
        Resolve a class name to its internal format (with / instead of .).

        For simple names, tries to resolve to common types.
        For fully qualified names, converts dots to slashes.
        """
        # Remove generic type parameters if present
        if '<' in class_name:
            class_name = class_name.split('<')[0].strip()

        # Check if it's a common type
        if class_name in self.COMMON_TYPES:
            return self.COMMON_TYPES[class_name]

        # If it contains a dot, assume it's fully qualified
        if '.' in class_name:
            return class_name.replace('.', '/')

        # Otherwise, return as-is (might be a local class)
        return class_name

    def get_method_descriptor(self, method_node: Node) -> str:
        """
        Generate a bytecode method descriptor.

        Format: methodName(param1Type;param2Type;...)returnType
        Example: main([Ljava/lang/String;)V
        """
        # Get method name
        method_name = None
        for child in method_node.children:
            if child.type == 'identifier':
                method_name = self.get_text(child)
                break

        if not method_name:
            method_name = "unknown"

        # Build parameter descriptor
        param_descriptor = self._get_parameters_descriptor(method_node)

        # Get return type
        return_descriptor = self._get_return_type_descriptor(method_node)

        return f"{method_name}({param_descriptor}){return_descriptor}"

    def _get_parameters_descriptor(self, method_node: Node) -> str:
        """Extract parameter descriptors from a method."""
        params = []

        # Find formal_parameters node
        for child in method_node.children:
            if child.type == 'formal_parameters':
                # Iterate through parameters
                for param_child in child.children:
                    if param_child.type == 'formal_parameter':
                        # Get the type node
                        type_node = None
                        for param_part in param_child.children:
                            if param_part.type in ['integral_type', 'floating_point_type',
                                                    'boolean_type', 'type_identifier',
                                                    'generic_type', 'array_type']:
                                type_node = param_part
                                break

                        if type_node:
                            params.append(self.get_type_descriptor(type_node))

        return ''.join(params)

    def _get_return_type_descriptor(self, method_node: Node) -> str:
        """Extract return type descriptor from a method."""
        # Find the return type (usually first child that's a type)
        for child in method_node.children:
            if child.type in ['void_type', 'integral_type', 'floating_point_type',
                             'boolean_type', 'type_identifier', 'generic_type', 'array_type']:
                return self.get_type_descriptor(child)

        return 'V'  # Default to void

    def get_class_internal_name(self, package: Optional[str], class_name: str) -> str:
        """
        Get the internal class name in bytecode format.

        Example: package=com.example, class_name=MyClass -> com/example/MyClass
        """
        if package:
            return f"{package.replace('.', '/')}/{class_name}"
        return class_name
