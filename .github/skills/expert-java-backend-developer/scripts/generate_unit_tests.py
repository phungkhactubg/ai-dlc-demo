#!/usr/bin/env python3
"""
generate_unit_tests.py

Generate JUnit 5 test stubs for Java classes.
Automatically creates test files with Mockito setup.

Usage:
    python generate_unit_tests.py <path> [--output output_dir] [--force]
    python generate_unit_tests.py src/main/java/com/example/notifications/service
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional


class TestGenerator:
    """Generates JUnit 5 test stubs for Java classes."""

    def __init__(self, force: bool = False):
        self.force = force

    def generate_for_directory(self, input_dir: str, output_dir: str) -> int:
        """Generate tests for all classes in a directory."""
        input_path = Path(input_dir)

        if not input_path.exists():
            print(f"Error: Input directory '{input_dir}' does not exist.")
            return 0

        # Find Java files
        java_files = list(input_path.rglob("*.java"))
        java_files = [f for f in java_files if "test" not in str(f).lower()]

        generated = 0

        for java_file in java_files:
            if self._generate_for_file(java_file, output_dir):
                generated += 1

        print(f"\n✅ Generated {generated} test files")

        return generated

    def _generate_for_file(self, java_file: Path, output_base: str) -> bool:
        """Generate test for a single Java file."""
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {java_file}: {e}")
            return False

        # Extract class info
        class_info = self._parse_class_info(content, java_file)
        if not class_info:
            return False

        package, class_name, methods, dependencies = class_info

        # Determine output path
        relative_path = java_file.relative_to(java_file.anchor)

        # Replace src/main/java with src/test/java
        test_parts = list(relative_path.parts)
        if "main" in test_parts:
            idx = test_parts.index("main")
            test_parts[idx] = "test"
        else:
            # Insert src/test/java at the beginning
            test_parts = ["src", "test", "java"] + list(relative_path.parts)

        # Create test file name
        test_filename = f"{class_name}Test.java"
        test_path = Path(output_base) / Path(*test_parts[:-1]) / test_filename

        # Check if test already exists
        if test_path.exists() and not self.force:
            print(f"⏭️  Skipping (exists): {test_path}")
            return False

        # Generate test content
        test_content = self._generate_test_content(
            package, class_name, methods, dependencies, str(java_file)
        )

        # Write test file
        test_path.parent.mkdir(parents=True, exist_ok=True)

        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_content)

        print(f"✅ Generated: {test_path}")

        return True

    def _parse_class_info(self, content: str, file_path: Path) -> Optional[Tuple[str, str, List[dict], List[dict]]]:
        """Parse class information from Java file."""
        # Extract package
        package_match = re.search(r'package\s+([\w.]+);', content)
        package = package_match.group(1) if package_match else ""

        # Extract class name and type
        class_match = re.search(
            r'(?:public\s+)?(?:abstract\s+)?(?:final\s+)?(class|interface|enum|record)\s+(\w+)',
            content
        )
        if not class_match:
            return None

        class_type = class_match.group(1)
        class_name = class_match.group(2)

        # Skip interfaces, enums, records
        if class_type in ['interface', 'enum', 'record']:
            return None

        # Extract public methods
        methods = self._extract_methods(content)

        # Extract dependencies (constructor injection)
        dependencies = self._extract_dependencies(content)

        return package, class_name, methods, dependencies

    def _extract_methods(self, content: str) -> List[dict]:
        """Extract public methods from class."""
        methods = []

        # Pattern for public methods
        method_pattern = re.compile(
            r'public\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:<[^>]+>\s+)?'
            r'([\w<>\[\], ]+)\s+'  # Return type
            r'(\w+)\s*'  # Method name
            r'\(([^)]*)\)'  # Parameters
            r'\s*(?:throws\s+[\w\s,]+)?\s*\{',
            re.MULTILINE
        )

        for match in method_pattern.finditer(content):
            return_type = match.group(1).strip()
            method_name = match.group(2)
            params = match.group(3).strip()

            # Skip getters, setters, toString, equals, hashCode
            if method_name in ['toString', 'equals', 'hashCode', 'main']:
                continue
            if method_name.startswith(('get', 'set', 'is')):
                continue

            methods.append({
                'name': method_name,
                'return_type': return_type,
                'params': params,
                'has_return': return_type not in ['void', 'Void']
            })

        return methods

    def _extract_dependencies(self, content: str) -> List[dict]:
        """Extract constructor-injected dependencies."""
        dependencies = []

        # Find constructor
        constructor_pattern = re.compile(
            r'(?:public|private|protected)\s+'  # Access
            r'(?:static\s+)?'  # Static
            r'(\w+)\s*'  # Class name (constructor name)
            r'\(([^)]*)\)'  # Parameters
            r'\s*(?:throws\s+[\w\s,]+)?\s*\{',
            re.MULTILINE
        )

        class_match = re.search(r'class\s+(\w+)', content)
        if not class_match:
            return dependencies

        class_name = class_match.group(1)

        for match in constructor_pattern.finditer(content):
            constructor_name = match.group(1)

            # Skip if not the class constructor
            if constructor_name != class_name:
                continue

            params_str = match.group(2)
            if not params_str.strip():
                continue

            # Parse parameters
            param_pairs = [p.strip() for p in params_str.split(',') if p.strip()]

            for param in param_pairs:
                parts = param.split()
                if len(parts) >= 2:
                    param_type = ' '.join(parts[:-1])
                    param_name = parts[-1]

                    dependencies.append({
                        'type': param_type,
                        'name': param_name
                    })

        return dependencies

    def _generate_test_content(self, package: str, class_name: str,
                                methods: List[dict], dependencies: List[dict],
                                source_file: str) -> str:
        """Generate test class content."""

        # Generate imports
        imports = set([
            "org.junit.jupiter.api.Test",
            "org.junit.jupiter.api.extension.ExtendWith",
            "org.mockito.InjectMocks",
            "org.mockito.Mock",
            "org.mockito.junit.jupiter.MockitoExtension",
        ])

        # Add class package import
        if package:
            imports.add(f"{package}.{class_name}")

        # Add dependency imports
        for dep in dependencies:
            # Extract simple type name
            simple_type = dep['type'].split('<')[0].split('[')[0].strip()
            # Don't add standard Java types
            if simple_type not in ['String', 'Integer', 'Long', 'Boolean', 'Double', 'Float', 'List', 'Map', 'Set', 'Optional']:
                imports.add(f"{package}.*" if package else simple_type)

        # Generate dependency mocks
        mock_fields = []
        for dep in dependencies:
            simple_type = dep['type'].split('<')[0].split('[')[0].strip()
            mock_fields.append(f"    private {dep['type']} {dep['name']};")

        # Generate test methods
        test_methods = []
        for method in methods[:10]:  # Limit to first 10 methods
            test_method = self._generate_test_method(method, dependencies)
            test_methods.append(test_method)

        # Format imports
        import_list = sorted(imports)
        if "java.util.List" in import_list or "java.util.Map" in import_list or "java.util.Set" in import_list:
            import_list = [i for i in import_list if not i.startswith("java.util.")]
            import_list.extend(["java.util.List", "java.util.Map", "java.util.Optional"])

        # Build test class
        test_content = f"""package {package.replace('.main.', '.test.')};

{chr(10).join(f'import {imp};' for imp in sorted(set(import_list)))}

/**
 * Unit tests for {class_name}.
 * Generated by generate_unit_tests.py - Review and implement test logic.
 */
@ExtendWith(MockitoExtension.class)
class {class_name}Test {{

{chr(10).join(mock_fields)}

    @InjectMocks
    private {class_name} {self._camel_to_snake(class_name)};

{chr(10).join(test_methods)}
}}
"""

        return test_content

    def _generate_test_method(self, method: dict, dependencies: List[dict]) -> str:
        """Generate a test method."""
        method_name = method['name']

        # Determine test name
        test_name = f"test{method_name[0].upper()}{method_name[1:]}"

        # Generate test body
        body = f"""    @Test
    void {test_name}() {{
        // Given
        // TODO: Set up test data

        // When
        // {method_name}();

        // Then
        // TODO: Verify results
"""

        if method['has_return']:
            body += f"""
        // Assert the result
        // assertNotNull(result);
"""

        body += """    }
"""

        return body

    def _camel_to_snake(self, name: str) -> str:
        """Convert CamelCase to snake_case for variable naming."""
        result = [name[0].lower()]
        for char in name[1:]:
            if char.isupper():
                result.append('_')
                result.append(char.lower())
            else:
                result.append(char)
        return ''.join(result)


def main():
    parser = argparse.ArgumentParser(
        description="Generate JUnit 5 test stubs for Java classes"
    )
    parser.add_argument("path", help="Path to Java source file or directory")
    parser.add_argument("--output", default=".", help="Output directory (default: current directory)")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing test files")

    args = parser.parse_args()

    generator = TestGenerator(force=args.force)

    if Path(args.path).is_file():
        # Single file
        test_path = Path(args.output)
        if generator._generate_for_file(Path(args.path), str(test_path)):
            print("\n✅ Generated 1 test file")
    else:
        # Directory
        generator.generate_for_directory(args.path, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
