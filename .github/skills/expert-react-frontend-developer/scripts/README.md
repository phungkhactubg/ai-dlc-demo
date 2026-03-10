# Helper Scripts for Expert React Frontend Developer

This directory contains utility scripts to assist in developing high-quality, architecturally compliant React applications.

## 🔴 CRITICAL SCRIPTS

### `validate_frontend_architecture.py`
**Usage:** `python validate_frontend_architecture.py <path-to-feature>`
**Purpose:** Enforces strict code quality rules.
- ❌ **Fails if:**
  - `any` type is used.
  - Services are imported directly into Components (Architecture Violation).
- ⚠️ **Warns if:**
  - Component > 250 lines.
  - Hook > 200 lines.
  - Services missing Zod validation (`.parse()`).

Run this script BEFORE committing any code.

### `extract_go_api.py`
**Usage:** `python extract_go_api.py <path-to-go-controller> --format zod`
**Purpose:** Generates TypeScript Zod schemas directly from Go Backend structs. This ensures your Frontend API logic matches the Backend perfectly.

---

## 🛠️ UTILITY SCRIPTS

### `scaffold_feature.py`
**Usage:** `python scaffold_feature.py <feature_name> --path apps/frontend/src`
**Purpose:** Creates the folder structure for a new feature following the Feature-Sliced + Clean Architecture standard.

### `analyze_code.py`
**Usage:** `python analyze_code.py <path-to-feature>`
**Purpose:** Provides a general analysis of code structure, counting lines of code and identifying basic patterns.

### `generate_zod_from_api.py`
**Usage:** `python generate_zod_from_api.py <json_file>`
**Purpose:** Converts a JSON response (saved in a file) into a Zod schema. Useful if you don't have access to the Backend source code but have the API response.

### `check_architecture.py`
**Usage:** `python check_architecture.py <path-to-feature>`
**Purpose:** Verifies that the folder structure exists and follows the naming conventions.

### `generate_routes.py`
**Usage:** `python generate_routes.py <path-to-pages>`
**Purpose:** Automatically generates a route configuration object based on the files found in the pages directory (convention-based routing helper).
