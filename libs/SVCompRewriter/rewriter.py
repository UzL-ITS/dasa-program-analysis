#!/usr/bin/env python3
"""
SVComp Verifier Rewriter CLI Tool

Transforms Java projects by instrumenting Verifier.nonDet* calls with witness logging.
"""

import argparse
import glob
import os
import sys
from pathlib import Path
from typing import List

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
LIB_DIR = os.path.join(SCRIPT_DIR, '..')
for wheel in glob.glob(os.path.join(LIB_DIR, "*.whl")):
    sys.path.insert(0, wheel)

# import these after all wheels have been added to the path
from java_rewriter import JavaRewriter
from witness_generator import WitnessGenerator


class SVCompRewriter:
    """Main rewriter class that processes Java files and directories."""

    def __init__(self, output_dir: str = None, package: str = None):
        self.output_dir = output_dir
        self.package = package
        self.files_processed = 0
        self.files_modified = 0

    def process_path(self, input_path: str) -> bool:
        """
        Process a file or directory.

        Args:
            input_path: Path to a Java file or directory

        Returns:
            True if processing was successful
        """
        path = Path(input_path)

        if not path.exists():
            print(f"Error: Path does not exist: {input_path}", file=sys.stderr)
            return False

        if path.is_file():
            if path.suffix == '.java':
                return self._process_file(path)
            else:
                print(f"Warning: Skipping non-Java file: {input_path}", file=sys.stderr)
                return True
        elif path.is_dir():
            return self._process_directory(path)
        else:
            print(f"Error: Invalid path: {input_path}", file=sys.stderr)
            return False

    def _process_directory(self, directory: Path) -> bool:
        """Recursively process all Java files in a directory."""
        print(f"Processing directory: {directory}")

        java_files = list(directory.rglob('*.java'))

        if not java_files:
            print(f"Warning: No Java files found in {directory}", file=sys.stderr)
            return True

        print(f"Found {len(java_files)} Java file(s)")

        success = True
        for java_file in java_files:
            if not self._process_file(java_file):
                success = False

        return success

    def _process_file(self, file_path: Path) -> bool:
        """Process a single Java file."""
        try:
            print(f"Processing: {file_path}")

            # Read source code
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            # Rewrite the code
            rewriter = JavaRewriter(source_code)
            transformed_code = rewriter.rewrite()

            self.files_processed += 1

            # Check if anything changed
            if transformed_code == source_code:
                print(f"  No changes needed")
            else:
                self.files_modified += 1

            # Determine output path
            if self.output_dir:
                output_path = Path(self.output_dir) / file_path.name
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                # Overwrite original file
                output_path = file_path

            # Write transformed code
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transformed_code)

            print(f"  ✓ Transformed and saved to: {output_path}")

            # Generate Witness.java if needed and not already exists
            if rewriter.witness_needed:
                self._generate_witness(output_path.parent, rewriter.package)

            return True

        except Exception as e:
            print(f"  ✗ Error processing {file_path}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False

    def _generate_witness(self, output_dir: Path, package: str = None):
        """Generate Witness.java in the output directory."""
        witness_path = output_dir / "Witness.java"

        # Don't overwrite if it already exists
        if witness_path.exists():
            return

        print(f"  Generating Witness.java in {output_dir}")

        # Use package from file if not specified globally
        if package is None:
            package = self.package

        WitnessGenerator.write_witness_file(str(witness_path), package)
        print(f"  ✓ Generated: {witness_path}")

    def print_summary(self):
        """Print processing summary."""
        print("\n" + "=" * 60)
        print("Processing Summary:")
        print(f"  Files processed: {self.files_processed}")
        print(f"  Files modified:  {self.files_modified}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Transform Java code to instrument Verifier.nonDet* calls with witness logging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Process a single file (overwrites original)
  python rewriter.py Test.java

  # Process a single file and save to output directory
  python rewriter.py Test.java -o output/

  # Process all Java files in a directory
  python rewriter.py src/ -o output/

  # Specify package for Witness class
  python rewriter.py src/ -o output/ --package org.example
        '''
    )

    parser.add_argument(
        'input',
        help='Path to a Java file or directory containing Java files'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output directory (if not specified, files will be overwritten)',
        default=None
    )

    parser.add_argument(
        '--package',
        help='Package name for generated Witness class',
        default=None
    )

    args = parser.parse_args()

    # Create rewriter
    rewriter = SVCompRewriter(output_dir=args.output, package=args.package)

    # Process input
    success = rewriter.process_path(args.input)

    # Print summary
    rewriter.print_summary()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
