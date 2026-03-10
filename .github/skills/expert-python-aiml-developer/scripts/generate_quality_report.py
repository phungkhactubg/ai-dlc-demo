#!/usr/bin/env python3
"""
Generate comprehensive quality report for Python AI/ML code.

Runs all validation scripts and generates a unified quality score.

Usage:
    python generate_quality_report.py src/
    python generate_quality_report.py src/ --html report.html
    python generate_quality_report.py src/ --json
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class ValidatorResult:
    """Result from a single validator."""
    name: str
    passed: bool
    score: int  # 0-100
    issues_count: int
    critical_count: int
    details: Dict


@dataclass
class QualityReport:
    """Complete quality report."""
    timestamp: str
    path: str
    overall_score: int
    validators: List[ValidatorResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        return self.overall_score >= 60


def run_validator(script_name: str, target_path: Path) -> Optional[Dict]:
    """Run a validator script and parse JSON output."""
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        return None
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), str(target_path), "--json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        return {"error": str(e)}


def calculate_score(result: Dict, validator_name: str) -> int:
    """Calculate score for a validator result."""
    if "error" in result:
        return 0
    
    if validator_name == "validate_type_hints.py":
        return int(result.get("coverage_percent", 0))
    
    if validator_name == "validate_production_ready.py":
        critical = result.get("critical_count", 0)
        errors = result.get("error_count", 0)
        if critical > 0:
            return 0
        elif errors > 5:
            return 30
        elif errors > 0:
            return 60
        else:
            return 100
    
    if validator_name == "validate_security.py":
        critical = result.get("critical_count", 0)
        high = result.get("high_count", 0)
        if critical > 0:
            return 0
        elif high > 0:
            return 50
        else:
            return 100
    
    if validator_name == "validate_model_reproducibility.py":
        if result.get("passed", False):
            return 100
        else:
            return 50
    
    return 100 if result.get("passed", True) else 50


def generate_report(target_path: Path) -> QualityReport:
    """Generate comprehensive quality report."""
    report = QualityReport(
        timestamp=datetime.now().isoformat(),
        path=str(target_path),
        overall_score=0,
    )
    
    validators = [
        ("validate_production_ready.py", "Production Readiness", 0.25),
        ("validate_type_hints.py", "Type Hints", 0.25),
        ("validate_security.py", "Security", 0.20),
        ("validate_model_reproducibility.py", "Reproducibility", 0.15),
    ]
    
    total_weight = 0
    weighted_score = 0
    
    for script_name, display_name, weight in validators:
        result = run_validator(script_name, target_path)
        
        if result is None:
            continue
        
        score = calculate_score(result, script_name)
        passed = result.get("passed", score >= 60)
        issues = len(result.get("issues", []))
        critical = result.get("critical_count", 0)
        
        report.validators.append(ValidatorResult(
            name=display_name,
            passed=passed,
            score=score,
            issues_count=issues,
            critical_count=critical,
            details=result,
        ))
        
        weighted_score += score * weight
        total_weight += weight
    
    if total_weight > 0:
        report.overall_score = int(weighted_score / total_weight * (1 / 0.85))
        report.overall_score = min(100, report.overall_score)
    
    # Generate recommendations
    for v in report.validators:
        if v.score < 60:
            if v.name == "Type Hints":
                report.recommendations.append(
                    "Add type hints to all public functions for better code quality."
                )
            elif v.name == "Production Readiness":
                report.recommendations.append(
                    "Remove TODOs, add error handling, and complete all implementations."
                )
            elif v.name == "Security":
                report.recommendations.append(
                    "Fix security issues: remove hardcoded secrets, use safe deserialization."
                )
            elif v.name == "Reproducibility":
                report.recommendations.append(
                    "Add seed setting and environment logging for reproducible experiments."
                )
    
    return report


def print_report(report: QualityReport) -> None:
    """Print quality report to console."""
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE QUALITY REPORT")
    print("=" * 70)
    
    print(f"\nPath: {report.path}")
    print(f"Timestamp: {report.timestamp}")
    print(f"\n{'=' * 70}")
    
    # Score bar
    score = report.overall_score
    bar_length = 40
    filled = int(bar_length * score / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    if score >= 80:
        grade = "A"
        color = "🟢"
    elif score >= 60:
        grade = "B"
        color = "🟡"
    elif score >= 40:
        grade = "C"
        color = "🟠"
    else:
        grade = "D"
        color = "🔴"
    
    print(f"\n{color} OVERALL SCORE: {score}/100 (Grade: {grade})")
    print(f"   [{bar}]")
    
    # Individual validators
    print(f"\n{'-' * 70}")
    print("VALIDATION RESULTS:")
    print(f"{'-' * 70}")
    
    for v in report.validators:
        icon = "✅" if v.passed else "❌"
        issues = f"({v.issues_count} issues" + (f", {v.critical_count} critical)" if v.critical_count > 0 else ")")
        print(f"\n{icon} {v.name}: {v.score}/100 {issues}")
    
    # Recommendations
    if report.recommendations:
        print(f"\n{'-' * 70}")
        print("📋 RECOMMENDATIONS:")
        print(f"{'-' * 70}")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"\n{i}. {rec}")
    
    print(f"\n{'=' * 70}")
    if report.passed:
        print("✅ QUALITY CHECK PASSED")
    else:
        print("❌ QUALITY CHECK FAILED - Score below 60")
    print("=" * 70 + "\n")


def generate_html_report(report: QualityReport) -> str:
    """Generate HTML report."""
    score = report.overall_score
    color = "#22c55e" if score >= 80 else "#eab308" if score >= 60 else "#ef4444"
    
    validators_html = ""
    for v in report.validators:
        v_color = "#22c55e" if v.passed else "#ef4444"
        validators_html += f"""
        <div style="margin: 10px 0; padding: 15px; border: 1px solid #e5e7eb; border-radius: 8px;">
            <h3 style="color: {v_color}; margin: 0 0 10px 0;">
                {'✅' if v.passed else '❌'} {v.name}: {v.score}/100
            </h3>
            <p style="color: #6b7280; margin: 0;">
                {v.issues_count} issues found
                {f', {v.critical_count} critical' if v.critical_count > 0 else ''}
            </p>
        </div>
        """
    
    recs_html = ""
    for rec in report.recommendations:
        recs_html += f"<li style='margin: 10px 0;'>{rec}</li>"
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Quality Report - {report.path}</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .score {{ font-size: 48px; color: {color}; font-weight: bold; }}
        .grade {{ font-size: 24px; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Quality Report</h1>
        <p style="color: #6b7280;">Generated: {report.timestamp}</p>
        <p style="color: #6b7280;">Path: {report.path}</p>
        <div class="score">{score}/100</div>
        <div class="grade">{'PASSED' if report.passed else 'NEEDS IMPROVEMENT'}</div>
    </div>
    
    <h2>Validation Results</h2>
    {validators_html}
    
    <h2>Recommendations</h2>
    <ul>{recs_html if recs_html else '<li>No recommendations - great job!</li>'}</ul>
</body>
</html>
"""


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate quality report")
    parser.add_argument("path", type=Path, help="Directory to analyze")
    parser.add_argument("--html", type=Path, help="Output HTML report to file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    target = args.path.absolute()
    if not target.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)
    
    # Standardized Output Paths
    report_name = target.name
    if not report_name or report_name == ".":
        report_name = "root"
    
    output_dir = Path("project-documentation/quality-reports") / report_name
    
    json_output = None
    html_output = args.html
    
    # In orchestrated mode or if user didn't specify, use standardized path
    if not args.json:
        json_output = output_dir / "QUALITY_REPORT.json"
    
    if not html_output and not args.json:
        html_output = output_dir / "QUALITY_REPORT.html"

    print("Running quality validators...")
    report = generate_report(args.path)
    
    if args.json:
        output = {
            "timestamp": report.timestamp,
            "path": report.path,
            "overall_score": report.overall_score,
            "passed": report.passed,
            "validators": [
                {
                    "name": v.name,
                    "passed": v.passed,
                    "score": v.score,
                    "issues_count": v.issues_count,
                    "critical_count": v.critical_count,
                }
                for v in report.validators
            ],
            "recommendations": report.recommendations,
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(report)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        output = {
            "timestamp": report.timestamp,
            "path": report.path,
            "overall_score": report.overall_score,
            "passed": report.passed,
            "validators": [
                {
                    "name": v.name,
                    "passed": v.passed,
                    "score": v.score,
                    "issues_count": v.issues_count,
                    "critical_count": v.critical_count,
                }
                for v in report.validators
            ],
            "recommendations": report.recommendations,
        }
        json_output.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"✅ JSON report saved to: {json_output}")

    if html_output:
        html_output.parent.mkdir(parents=True, exist_ok=True)
        html = generate_html_report(report)
        html_output.write_text(html, encoding="utf-8")
        print(f"✅ HTML report saved to: {html_output}")
    
    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
