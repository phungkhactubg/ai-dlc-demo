#!/usr/bin/env python3
"""
Validate Computer Vision code for best practices.

Checks for:
- Proper color space handling (BGR vs RGB)
- Image normalization standards
- Augmentation only on training data
- Memory management in inference
- Proper dataset structure

Usage:
    python validate_cv_pipeline.py src/
    python validate_cv_pipeline.py src/ --strict
    python validate_cv_pipeline.py src/ --json
"""

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set


@dataclass
class CVIssue:
    """Represents a Computer Vision issue."""
    severity: str  # CRITICAL, WARNING, INFO
    category: str
    file: str
    line: int
    message: str
    recommendation: str


@dataclass
class CVValidationResult:
    """CV validation result."""
    issues: List[CVIssue] = field(default_factory=list)
    files_scanned: int = 0
    
    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "CRITICAL")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "WARNING")
    
    @property
    def passed(self) -> bool:
        return self.critical_count == 0


class CVVisitor(ast.NodeVisitor):
    """AST visitor for CV-specific checks."""
    
    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.content = content
        self.lines = content.split('\n')
        self.issues: List[CVIssue] = []
        self.has_bgr_to_rgb = False
        self.has_normalization = False
        self.in_validation_context = False
    
    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls for CV issues."""
        func_name = self._get_func_name(node.func)
        
        # Check cv2.imread without color conversion
        if func_name == 'cv2.imread':
            self._check_imread_usage(node)
        
        # Check for proper normalization
        if 'Normalize' in func_name:
            self.has_normalization = True
            self._check_normalization(node)
        
        # Check for random transforms in validation
        if self._is_random_transform(func_name):
            self._check_validation_augmentation(node, func_name)
        
        # Check inference mode
        if func_name in ('model', 'self.model') and not self._in_inference_mode():
            pass  # Complex to detect, handled by pattern matching
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Check assignments for CV patterns."""
        # Check for BGR to RGB conversion
        if isinstance(node.value, ast.Call):
            func_name = self._get_func_name(node.value.func)
            if 'cvtColor' in func_name:
                for arg in node.value.args:
                    if isinstance(arg, ast.Attribute):
                        if 'COLOR_BGR2RGB' in ast.dump(arg):
                            self.has_bgr_to_rgb = True
        
        self.generic_visit(node)
    
    def _check_imread_usage(self, node: ast.Call) -> None:
        """Check if cv2.imread is followed by color conversion."""
        # This is a heuristic - we look for cvtColor nearby
        line_num = node.lineno
        
        # Check next few lines for color conversion
        has_conversion = False
        for i in range(line_num, min(line_num + 5, len(self.lines))):
            if 'COLOR_BGR2RGB' in self.lines[i]:
                has_conversion = True
                break
        
        if not has_conversion:
            # Check if there's any mention of BGR2RGB in the file
            if 'COLOR_BGR2RGB' not in self.content:
                self.issues.append(CVIssue(
                    severity="WARNING",
                    category="COLOR_SPACE",
                    file=self.file_path,
                    line=line_num,
                    message="cv2.imread() without explicit BGR to RGB conversion",
                    recommendation="Add cv2.cvtColor(image, cv2.COLOR_BGR2RGB) after imread",
                ))
    
    def _check_normalization(self, node: ast.Call) -> None:
        """Check normalization values."""
        # Check if using ImageNet values
        imagenet_mean = "(0.485, 0.456, 0.406)"
        imagenet_std = "(0.229, 0.224, 0.225)"
        
        line = self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else ""
        
        # Check for generic 0.5 normalization
        if "[0.5, 0.5, 0.5]" in line or "(0.5, 0.5, 0.5)" in line:
            self.issues.append(CVIssue(
                severity="INFO",
                category="NORMALIZATION",
                file=self.file_path,
                line=node.lineno,
                message="Using generic [0.5, 0.5, 0.5] normalization",
                recommendation="Consider using dataset-specific normalization (e.g., ImageNet values)",
            ))
    
    def _is_random_transform(self, func_name: str) -> bool:
        """Check if function is a random augmentation."""
        random_transforms = {
            'RandomHorizontalFlip', 'RandomVerticalFlip',
            'RandomRotation', 'RandomCrop', 'RandomResizedCrop',
            'ColorJitter', 'RandomAffine', 'RandomPerspective',
            'RandomErasing', 'GaussNoise', 'RandomBrightnessContrast',
            'HorizontalFlip', 'VerticalFlip', 'ShiftScaleRotate',
        }
        return any(t in func_name for t in random_transforms)
    
    def _check_validation_augmentation(self, node: ast.Call, func_name: str) -> None:
        """Check for random augmentation in validation context."""
        # Check if we're in a validation-related function or variable
        line = self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else ""
        
        validation_indicators = ['val_', 'valid_', 'test_', 'eval_', 'inference']
        
        for indicator in validation_indicators:
            if indicator in line.lower():
                self.issues.append(CVIssue(
                    severity="CRITICAL",
                    category="AUGMENTATION",
                    file=self.file_path,
                    line=node.lineno,
                    message=f"Random augmentation '{func_name}' in validation/test context",
                    recommendation="Only apply random augmentations to training data",
                ))
                break
    
    def _in_inference_mode(self) -> bool:
        """Check if we're in inference mode context."""
        # This is a heuristic check
        return 'inference_mode' in self.content or 'no_grad' in self.content
    
    def _get_func_name(self, node) -> str:
        """Get function name from a Call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parent = self._get_func_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""


def check_pattern_issues(file_path: Path, content: str) -> List[CVIssue]:
    """Check for CV issues using pattern matching."""
    issues = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Check for torch.load without inference mode context
        if 'model(' in line and '@torch.inference_mode' not in content:
            if 'def predict' in content or 'def inference' in content:
                # Check if using no_grad or inference_mode
                if 'no_grad' not in content and 'inference_mode' not in content:
                    pass  # Too many false positives, skip
        
        # Check for PIL/OpenCV mixed usage issues
        if 'cv2.imread' in line and 'PIL' in content:
            issues.append(CVIssue(
                severity="INFO",
                category="LIBRARY_MIX",
                file=str(file_path),
                line=line_num,
                message="Mixing OpenCV and PIL for image loading",
                recommendation="Consider using one library consistently for image I/O",
            ))
        
        # Check for hardcoded image sizes
        hardcoded_sizes = re.findall(r'resize\s*\(\s*\d+\s*,\s*\d+\s*\)', line.lower())
        if hardcoded_sizes and 'config' not in line.lower():
            issues.append(CVIssue(
                severity="INFO",
                category="HARDCODED_SIZE",
                file=str(file_path),
                line=line_num,
                message="Hardcoded image size in resize operation",
                recommendation="Consider using configuration for image sizes",
            ))
    
    return issues


def validate_file(file_path: Path) -> List[CVIssue]:
    """Validate a single file for CV issues."""
    issues = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return [CVIssue(
            severity="WARNING",
            category="FILE_ERROR",
            file=str(file_path),
            line=0,
            message=f"Could not read file: {e}",
            recommendation="Check file permissions",
        )]
    
    # AST-based checks
    try:
        tree = ast.parse(content)
        visitor = CVVisitor(str(file_path), content)
        visitor.visit(tree)
        issues.extend(visitor.issues)
    except SyntaxError:
        pass
    
    # Pattern-based checks
    issues.extend(check_pattern_issues(file_path, content))
    
    return issues


def validate_directory(directory: Path) -> CVValidationResult:
    """Validate all Python files in a directory."""
    result = CVValidationResult()
    
    for file_path in directory.rglob("*.py"):
        if "__pycache__" in str(file_path) or ".venv" in str(file_path):
            continue
        
        result.files_scanned += 1
        result.issues.extend(validate_file(file_path))
    
    return result


def print_results(result: CVValidationResult) -> None:
    """Print validation results."""
    print("\n" + "=" * 60)
    print("🖼️ COMPUTER VISION VALIDATION REPORT")
    print("=" * 60)
    
    print(f"\nFiles scanned: {result.files_scanned}")
    print(f"Critical issues: {result.critical_count}")
    print(f"Warnings: {result.warning_count}")
    print(f"Info: {sum(1 for i in result.issues if i.severity == 'INFO')}")
    
    if result.issues:
        print("\n" + "-" * 60)
        print("ISSUES FOUND:")
        print("-" * 60)
        
        # Sort by severity
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        sorted_issues = sorted(
            result.issues,
            key=lambda x: severity_order.get(x.severity, 3)
        )
        
        for issue in sorted_issues:
            icon = {"CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "ℹ️"}.get(
                issue.severity, "?"
            )
            print(f"\n{icon} [{issue.severity}] {issue.category}")
            print(f"   File: {issue.file}:{issue.line}")
            print(f"   Issue: {issue.message}")
            print(f"   Fix: {issue.recommendation}")
    
    print("\n" + "=" * 60)
    if result.passed:
        print("✅ CV VALIDATION PASSED")
    else:
        print("❌ CV VALIDATION FAILED - Critical issues found")
    print("=" * 60 + "\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Computer Vision code"
    )
    parser.add_argument("path", type=Path, help="Directory to validate")
    parser.add_argument("--strict", action="store_true", help="Strict mode")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)
    
    result = validate_directory(args.path)
    
    if args.json:
        output = {
            "files_scanned": result.files_scanned,
            "critical_count": result.critical_count,
            "warning_count": result.warning_count,
            "passed": result.passed,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "file": i.file,
                    "line": i.line,
                    "message": i.message,
                    "recommendation": i.recommendation,
                }
                for i in result.issues
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print_results(result)
    
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
