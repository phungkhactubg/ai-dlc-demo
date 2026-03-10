#!/usr/bin/env python3
"""
Architecture Checker - Verify Clean Architecture compliance.

Usage:
    python check_architecture.py apps/frontend/src/dashboard
"""

import argparse
import sys
from pathlib import Path

REQUIRED = {'core': ['models', 'interfaces', 'constants'],
            'infrastructure': ['api', 'stores', 'services'],
            'shared': ['components', 'hooks'], 'app': []}

def check(feature_path: Path) -> bool:
    errors = []
    for layer, subdirs in REQUIRED.items():
        lp = feature_path / layer
        if not lp.exists():
            errors.append(f"Missing: {layer}/")
            continue
        for sd in subdirs:
            if not (lp / sd).exists():
                errors.append(f"Missing: {layer}/{sd}/")
    
    # Check dependency violations
    for ts in (feature_path / 'core').rglob('*.ts') if (feature_path / 'core').exists() else []:
        content = ts.read_text(encoding='utf-8')
        if 'infrastructure/' in content:
            errors.append(f"Violation: {ts.name} imports infrastructure")
    
    for e in errors:
        print(f"  ❌ {e}")
    return len(errors) == 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    target = Path(args.path)
    if not target.exists():
        sys.exit(1)
    print(f"Checking: {target}")
    passed = check(target)
    print("✅ PASSED" if passed else "❌ FAILED")
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
