# Change: Refactor Import Execution

## Why
Currently, the import process is triggered by a standalone script `run_import.py` in the root directory. This breaks the standard package structure and makes it harder to manage dependencies and imports cleanly. Moving this to a module within `src` standardizes the execution flow and aligns with Python best practices.
Note: The user requested `src.import`, but since `import` is a reserved keyword in Python, we will use `src.importer` to avoid syntax errors while maintaining the spirit of the request.

## What Changes
- Move `run_import.py` logic to `src/importer/__main__.py`.
- Create `src/importer` package.
- Allow execution via `python -m src.importer ...`.
- **Preserve all original command-line arguments** (e.g., `--channel`, `--limit`).
- Remove `run_import.py`.

## Impact
- **Affected specs**: `telegram-client` (adding CLI requirement).
- **Affected code**: `run_import.py`, `src/` structure.
