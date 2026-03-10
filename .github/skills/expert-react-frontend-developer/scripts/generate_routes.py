#!/usr/bin/env python3
"""
React Router Generator
======================
Generate React Router route definitions and lazy-loaded imports for features.

Usage:
    python generate_routes.py --features dashboard,settings,profile
    python generate_routes.py --features notifications --base-path /admin
"""

import argparse
from pathlib import Path


def to_pascal_case(name: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))


def to_kebab_case(name: str) -> str:
    """Convert snake_case to kebab-case."""
    return name.lower().replace('_', '-')


def generate_lazy_imports(features: list[str]) -> str:
    """Generate lazy import statements."""
    lines = ["import { lazy } from 'react';", ""]
    
    for feature in features:
        pascal = to_pascal_case(feature)
        lower = feature.lower().replace('-', '_')
        lines.append(f"const {pascal}Layout = lazy(() => import('./{lower}/app/{pascal}Layout'));")
    
    return '\n'.join(lines)


def generate_route_config(features: list[str], base_path: str = "") -> str:
    """Generate route configuration."""
    lines = [
        "import { RouteObject } from 'react-router-dom';",
        "",
        "// Lazy-loaded feature layouts",
    ]
    
    # Add lazy imports
    for feature in features:
        pascal = to_pascal_case(feature)
        lower = feature.lower().replace('-', '_')
        lines.append(f"const {pascal}Layout = lazy(() => import('./{lower}/app/{pascal}Layout'));")
    
    lines.append("")
    lines.append("export const featureRoutes: RouteObject[] = [")
    
    for feature in features:
        pascal = to_pascal_case(feature)
        kebab = to_kebab_case(feature)
        path = f"{base_path}/{kebab}" if base_path else f"/{kebab}"
        
        lines.append(f"  {{")
        lines.append(f"    path: '{path}',")
        lines.append(f"    element: <{pascal}Layout />,")
        lines.append(f"    children: [")
        lines.append(f"      {{ index: true, element: <{pascal}ListPage /> }},")
        lines.append(f"      {{ path: ':id', element: <{pascal}DetailPage /> }},")
        lines.append(f"      {{ path: 'new', element: <{pascal}CreatePage /> }},")
        lines.append(f"      {{ path: ':id/edit', element: <{pascal}EditPage /> }},")
        lines.append(f"    ],")
        lines.append(f"  }},")
    
    lines.append("];")
    
    return '\n'.join(lines)


def generate_nav_items(features: list[str], base_path: str = "") -> str:
    """Generate navigation items for sidebar/menu."""
    lines = [
        "import {",
        "  Dashboard as DashboardIcon,",
        "  Settings as SettingsIcon,",
        "  Notifications as NotificationsIcon,",
        "  Person as PersonIcon,",
        "} from '@mui/icons-material';",
        "",
        "export interface NavItem {",
        "  label: string;",
        "  path: string;",
        "  icon: React.ReactNode;",
        "}",
        "",
        "export const navItems: NavItem[] = [",
    ]
    
    # Map common feature names to icons
    icon_map = {
        'dashboard': 'DashboardIcon',
        'settings': 'SettingsIcon',
        'notifications': 'NotificationsIcon',
        'profile': 'PersonIcon',
        'users': 'PersonIcon',
    }
    
    for feature in features:
        pascal = to_pascal_case(feature)
        kebab = to_kebab_case(feature)
        path = f"{base_path}/{kebab}" if base_path else f"/{kebab}"
        icon = icon_map.get(feature.lower(), 'DashboardIcon')
        
        lines.append(f"  {{")
        lines.append(f"    label: '{pascal}',")
        lines.append(f"    path: '{path}',")
        lines.append(f"    icon: <{icon} />,")
        lines.append(f"  }},")
    
    lines.append("];")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate React Router configuration for features"
    )
    parser.add_argument(
        "--features",
        required=True,
        help="Comma-separated list of feature names"
    )
    parser.add_argument(
        "--base-path",
        default="",
        help="Base path prefix for routes (e.g., /admin)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path"
    )
    parser.add_argument(
        "--type",
        choices=["routes", "nav", "imports", "all"],
        default="all",
        help="Type of output to generate"
    )

    args = parser.parse_args()
    features = [f.strip() for f in args.features.split(',')]

    output_parts = []

    if args.type in ["all", "imports"]:
        output_parts.append("// === Lazy Imports ===")
        output_parts.append(generate_lazy_imports(features))
        output_parts.append("")

    if args.type in ["all", "routes"]:
        output_parts.append("// === Route Configuration ===")
        output_parts.append(generate_route_config(features, args.base_path))
        output_parts.append("")

    if args.type in ["all", "nav"]:
        output_parts.append("// === Navigation Items ===")
        output_parts.append(generate_nav_items(features, args.base_path))

    output = '\n'.join(output_parts)

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"Generated routes saved to: {args.output}")
    else:
        print("=" * 60)
        print("GENERATED ROUTES")
        print("=" * 60)
        print(output)


if __name__ == "__main__":
    main()
