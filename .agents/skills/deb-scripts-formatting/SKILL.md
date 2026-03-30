---
name: deb-scripts-formatting
description: Use when formatting Python code in deb_scripts before or after edits. Covers the required Python style baseline, import sorting, and code formatting with uvx ruff using a maximum line length of 99.
---

# Code formatting

Use this skill whenever Python files were added or changed.

## Formatting baseline

- Minimum Python version is `3.12`.
- Sort imports with Ruff.
- Format code with Ruff.
- Maximum line length is `99`.

## Commands

Format the whole repository:

```bash
uvx ruff check --select I --fix . --line-length 99
uvx ruff format . --line-length 99
```

Format specific files:

```bash
uvx ruff check --select I --fix path/to/file.py --line-length 99
uvx ruff format path/to/file.py --line-length 99
```

## Usage rules

- Run import sorting before formatting.
- Prefer formatting only touched files when the change is small.
- If Ruff reports unrelated pre-existing issues outside the touched scope, do not broaden the task unless asked.
- Keep formatting changes separate from behavioral refactors in your reasoning and validation.
