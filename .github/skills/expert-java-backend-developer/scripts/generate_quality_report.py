#!/usr/bin/env python3
"""
generate_quality_report.py

Run ALL validation scripts and generate a comprehensive quality score.
This is the ONE-STOP quality check for Java backend code.

Usage:
    python generate_quality_report.py <path> [--html report.html] [--json] [--verbose]
    python generate_quality_report.py src/main/java/com/example/notifications
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class ValidationResult:
    name: str
    passed: bool
    score: int
    critical: int = 0
    error: int = 0
    warning: int = 0
    info: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "score": self.score,
            "issues": {
                "critical": self.critical,
                "error": self.error,
                "warning": self.warning,
                "info": self.info
            },
            "details": self.details
        }


@dataclass
class QualityReport:
    target_path: str
    overall_score: int
    status: str
    validation_results: List[ValidationResult] = field(default_factory=list)
    files_checked: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "target_path": self.target_path,
            "overall_score": self.overall_score,
            "status": self.status,
            "files_checked": self.files_checked,
            "validations": [v.to_dict() for v in self.validation_results]
        }


class QualityReportGenerator:
    """Generates comprehensive quality reports for Java code."""

    def __init__(self, target_path: str, verbose: bool = False):
        self.target_path = target_path
        self.verbose = verbose
        self.script_dir = Path(__file__).parent

        # Validation scripts with weights
        self.validations = [
            ("validate_production_ready.py", "Production Ready", 30),
            ("validate_exception_handling.py", "Exception Handling", 20),
            ("validate_transaction_boundary.py", "Transaction Boundaries", 15),
            ("validate_security.py", "Security", 25),
            ("validate_function_size.py", "Function Size", 5),
            ("validate_lombok_usage.py", "Lombok Usage", 5),
        ]

        # Analysis scripts (informational)
        self.analyses = [
            "analyze_code.py",
            "analyze_cyclomatic_complexity.py",
            "analyze_dependencies.py",
            "detect_dead_code.py",
        ]

    def generate(self) -> QualityReport:
        """Generate the quality report."""
        report = QualityReport(
            target_path=self.target_path,
            overall_score=0,
            status="UNKNOWN",
            timestamp=datetime.now().isoformat()
        )

        total_weight = sum(weight for _, _, weight in self.validations)
        weighted_score = 0

        print("\n" + "=" * 80)
        print("JAVA BACKEND QUALITY REPORT")
        print("=" * 80)
        print(f"\nTarget: {self.target_path}")
        print(f"Timestamp: {report.timestamp}")
        print("\n" + "-" * 80)

        # Run validation scripts
        for script_name, display_name, weight in self.validations:
            result = self._run_validation(script_name, display_name)
            report.validation_results.append(result)
            report.files_checked = max(report.files_checked, result.details.get("files_checked", 0))

            if result.passed:
                weighted_score += weight

        # Calculate overall score
        report.overall_score = int((weighted_score / total_weight) * 100)

        # Determine status
        if report.overall_score >= 80:
            report.status = "✅ EXCELLENT"
        elif report.overall_score >= 60:
            report.status = "✅ GOOD"
        elif report.overall_score >= 40:
            report.status = "⚠️  NEEDS IMPROVEMENT"
        else:
            report.status = "❌ POOR"

        # Print summary
        self._print_summary(report)

        # Run analysis scripts
        print("\n" + "-" * 80)
        print("ADDITIONAL ANALYSES:")
        print("-" * 80)

        for script_name in self.analyses:
            self._run_analysis(script_name)

        print("\n" + "=" * 80)

        return report

    def _run_validation(self, script_name: str, display_name: str) -> ValidationResult:
        """Run a validation script and return the result."""
        script_path = self.script_dir / script_name

        if not script_path.exists():
            print(f"\n⚠️  {display_name}: Script not found ({script_name})")
            return ValidationResult(
                name=display_name,
                passed=False,
                score=0,
                details={"error": "Script not found"}
            )

        try:
            # Run with JSON output for parsing
            result = subprocess.run(
                ["python3", str(script_path), self.target_path, "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse JSON output
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                # Fallback: parse from text output
                data = self._parse_text_output(result.stdout, script_name)

            summary = data.get("summary", {})
            issues = data.get("issues", [])

            critical = summary.get("critical", 0) + summary.get("high", 0)
            error = summary.get("error", 0)
            warning = summary.get("warning", 0) + summary.get("medium", 0)
            info = summary.get("low", 0) + summary.get("info", 0)
            files_checked = summary.get("files_checked", 0)

            # Determine if passed
            passed = (critical == 0 and error == 0)
            score = self._calculate_score(critical, error, warning)

            # Print result
            status_emoji = "✅" if passed else "❌"
            print(f"\n{status_emoji} {display_name}: {'PASSED' if passed else 'FAILED'}")
            print(f"   Score: {score}/100")
            print(f"   Issues: 🔴 {critical} | ❌ {error} | ⚠️  {warning} | ℹ️  {info}")

            if self.verbose and issues:
                for issue in issues[:5]:
                    print(f"      - {issue.get('file', 'unknown')}:{issue.get('line', '?')} - {issue.get('message', '')[:60]}")

            return ValidationResult(
                name=display_name,
                passed=passed,
                score=score,
                critical=critical,
                error=error,
                warning=warning,
                info=info,
                details={"files_checked": files_checked, "issues_count": len(issues)}
            )

        except subprocess.TimeoutExpired:
            print(f"\n⏱️  {display_name}: Timeout")
            return ValidationResult(
                name=display_name,
                passed=False,
                score=0,
                details={"error": "Timeout"}
            )
        except Exception as e:
            print(f"\n⚠️  {display_name}: Error - {e}")
            return ValidationResult(
                name=display_name,
                passed=False,
                score=0,
                details={"error": str(e)}
            )

    def _run_analysis(self, script_name: str) -> None:
        """Run an analysis script."""
        script_path = self.script_dir / script_name

        if not script_path.exists():
            return

        try:
            result = subprocess.run(
                ["python3", str(script_path), self.target_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Print brief summary
            display_name = script_name.replace("_", " ").replace(".py", "").title()
            print(f"\n📊 {display_name}:")

            # Extract key metrics from output
            lines = result.stdout.split('\n')
            for line in lines[:10]:
                if any(keyword in line for keyword in ["Files", "analyzed", "checked", "Total", "Average"]):
                    print(f"   {line.strip()}")

        except Exception as e:
            print(f"   Error running analysis: {e}")

    def _parse_text_output(self, output: str, script_name: str) -> Dict:
        """Fallback parser for text output."""
        data = {"summary": {}, "issues": []}

        lines = output.split('\n')
        for line in lines:
            if "CRITICAL:" in line:
                try:
                    data["summary"]["critical"] = int(line.split("CRITICAL:")[1].strip().split()[0])
                except:
                    pass
            elif "ERROR:" in line:
                try:
                    data["summary"]["error"] = int(line.split("ERROR:")[1].strip().split()[0])
                except:
                    pass
            elif "WARNING:" in line:
                try:
                    data["summary"]["warning"] = int(line.split("WARNING:")[1].strip().split()[0])
                except:
                    pass
            elif "files checked:" in line.lower():
                try:
                    data["summary"]["files_checked"] = int(line.split("checked:")[1].strip())
                except:
                    pass

        return data

    def _calculate_score(self, critical: int, error: int, warning: int) -> int:
        """Calculate a score (0-100) based on issues."""
        score = 100

        # Deductions
        score -= critical * 20
        score -= error * 10
        score -= warning * 2

        return max(0, score)

    def _print_summary(self, report: QualityReport) -> None:
        """Print the report summary."""
        print("\n" + "=" * 80)
        print("QUALITY SCORE SUMMARY")
        print("=" * 80)

        print(f"\n📊 Overall Score: {report.overall_score}/100")
        print(f"   Status: {report.status}")
        print(f"   Files Checked: {report.files_checked}")

        print("\n" + "-" * 80)
        print("VALIDATION RESULTS:")
        print("-" * 80)

        for result in report.validation_results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"\n{status} {result.name}")
            print(f"   Score: {result.score}/100")
            print(f"   Issues: 🔴 {result.critical} | ❌ {result.error} | ⚠️  {result.warning} | ℹ️  {result.info}")

        # Recommendations
        print("\n" + "-" * 80)
        print("RECOMMENDATIONS:")
        print("-" * 80)

        critical_issues = sum(r.critical for r in report.validation_results)
        error_issues = sum(r.error for r in report.validation_results)
        warning_issues = sum(r.warning for r in report.validation_results)

        if critical_issues > 0:
            print(f"\n🔴 CRITICAL: {critical_issues} critical issues must be fixed before deployment.")
            print("   Run individual scripts for details:")
            for result in report.validation_results:
                if result.critical > 0:
                    print(f"   - python .claude/skills/expert-java-backend-developer/scripts/{result.name.lower().replace(' ', '_')}.py <path>")

        if error_issues > 0:
            print(f"\n❌ {error_issues} errors should be fixed for production readiness.")

        if warning_issues > 0:
            print(f"\n⚠️  {warning_issues} warnings - consider addressing for better code quality.")

        if report.overall_score >= 60 and critical_issues == 0 and error_issues == 0:
            print(f"\n✅ Code quality meets production standards!")


def generate_html_report(report: QualityReport, output_path: str) -> None:
    """Generate an HTML report."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Java Backend Quality Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .score {{ display: flex; align-items: center; gap: 20px; margin: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
        .score-circle {{ width: 120px; height: 120px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: bold; color: white; }}
        .score-excellent {{ background: #10b981; }}
        .score-good {{ background: #22c55e; }}
        .score-needs {{ background: #f59e0b; }}
        .score-poor {{ background: #ef4444; }}
        .score-info h3 {{ font-size: 24px; margin-bottom: 5px; }}
        .score-info p {{ color: #666; }}
        .validations {{ padding: 0 30px 30px; }}
        .validation {{ display: flex; align-items: center; padding: 20px; margin-bottom: 15px; border-radius: 8px; border-left: 4px solid; }}
        .validation.pass {{ background: #f0fdf4; border-color: #10b981; }}
        .validation.fail {{ background: #fef2f2; border-color: #ef4444; }}
        .validation-icon {{ font-size: 24px; margin-right: 15px; }}
        .validation-details {{ flex: 1; }}
        .validation-name {{ font-weight: 600; font-size: 18px; margin-bottom: 5px; }}
        .validation-issues {{ color: #666; font-size: 14px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: 5px; }}
        .badge-critical {{ background: #fee2e2; color: #991b1b; }}
        .badge-error {{ background: #fef3c7; color: #92400e; }}
        .badge-warning {{ background: #dbeafe; color: #1e40af; }}
        .badge-info {{ background: #e0e7ff; color: #3730a3; }}
        .footer {{ padding: 20px 30px; border-top: 1px solid #e5e7eb; text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Java Backend Quality Report</h1>
            <p>Generated: {report.timestamp}</p>
            <p>Target: {report.target_path}</p>
        </div>

        <div class="score">
            <div class="score-circle score-{report.status.lower().replace('✅ ', '').replace('⚠️  ', '').replace('❌ ', '')}">{report.overall_score}</div>
            <div class="score-info">
                <h3>{report.status}</h3>
                <p>{report.files_checked} files analyzed</p>
            </div>
        </div>

        <div class="validations">
            <h2 style="margin-bottom: 20px;">Validation Results</h2>
"""

    for result in report.validation_results:
        status_class = "pass" if result.passed else "fail"
        status_icon = "✅" if result.passed else "❌"

        html += f"""
            <div class="validation {status_class}">
                <div class="validation-icon">{status_icon}</div>
                <div class="validation-details">
                    <div class="validation-name">{result.name}</div>
                    <div class="validation-issues">
"""

        if result.critical > 0:
            html += f'<span class="badge badge-critical">🔴 {result.critical}</span>'
        if result.error > 0:
            html += f'<span class="badge badge-error">❌ {result.error}</span>'
        if result.warning > 0:
            html += f'<span class="badge badge-warning">⚠️ {result.warning}</span>'
        if result.info > 0:
            html += f'<span class="badge badge-info">ℹ️ {result.info}</span>'

        if result.critical == 0 and result.error == 0 and result.warning == 0:
            html += '<span>No issues found</span>'

        html += """
                    </div>
                </div>
            </div>
"""

    html += f"""
        </div>

        <div class="footer">
            <p>Generated by expert-java-backend-developer skill</p>
        </div>
    </div>
</body>
</html>
"""

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"\n📄 HTML report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive quality report for Java backend code"
    )
    parser.add_argument("path", help="Path to Java source directory")
    parser.add_argument("--html", metavar="output.html", help="Generate HTML report")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    generator = QualityReportGenerator(args.path, verbose=args.verbose)
    report = generator.generate()

    if args.json:
        print("\n" + "=" * 80)
        print("JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(report.to_dict(), indent=2))

    if args.html:
        generate_html_report(report, args.html)

    # Exit codes
    if report.overall_score >= 60:
        sys.exit(0)
    elif report.overall_score >= 40:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
