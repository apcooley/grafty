# grafty — Quick Usage Guide

## Installation Status

✅ **grafty is installed as a system tool** and available in your PATH.

```bash
grafty --help  # Works from anywhere
```

## Usage

### Standard Usage (from anywhere)

```bash
grafty index src/
grafty show "src/main.py:py_function:parse_config"
grafty replace "src/main.py:py_function:old" --file new.py --apply
grafty delete "src/utils.py:py_function:unused" --apply
grafty check my.patch
```

### Development Usage (modifying grafty itself)

If you're working on grafty's source code:

```bash
cd ~/source/grafty
uv sync                 # Sync dependencies
uv run grafty index .   # Run with dev dependencies
uv run pytest tests/    # Run tests
uv run ruff check .     # Lint
```

### Python API (programmatic access)

```python
from grafty import Indexer, Resolver, Editor

# Index files
indexer = Indexer()
indices = indexer.index_directory(".")

# Find nodes by selector
resolver = Resolver(indices)
result = resolver.resolve("main.py:py_function:my_func")

# Mutate files
if result.is_resolved():
    editor = Editor(indices[result.exact_match.path])
    editor.replace(result.exact_match, "def my_func():\n    pass")
    editor.write(apply=True, backup=True)
```

## Common Commands

All commands work with `uv run grafty` or `./bin/grafty`:

### Index files
```bash
uv run grafty index src/
# Shows all functions, classes, methods, headings, etc.
```

### Show a node
```bash
# By structural selector
uv run grafty show "src/main.py:py_function:parse_config" --max-lines 50

# By line number (Phase 3)
uv run grafty show "src/main.py:42"          # Single line
uv run grafty show "src/main.py:42-50"       # Line range
```

### Search for nodes (Phase 3)
```bash
# Find all validation functions
uv run grafty search "*validate*"

# Find all tests in tests/ directory
uv run grafty search "test_*" --path "tests/"

# Find all Python methods (not functions)
uv run grafty search "*" --kind "py_method" --json
```

### Replace a function
```bash
# By structural selector
uv run grafty replace "src/main.py:py_function:old_impl" \
  --file new_impl.py \
  --dry-run  # Preview first

uv run grafty replace "src/main.py:py_function:old_impl" \
  --file new_impl.py \
  --apply --backup  # Apply & create .bak

# By line numbers (Phase 3)
uv run grafty replace "src/main.py:42-50" \
  --text "new implementation" \
  --apply --backup
```

### Delete a node
```bash
# By structural selector
uv run grafty delete "src/utils.py:py_function:unused_fn" --apply

# By line numbers (Phase 3)
uv run grafty delete "src/config.py:42-50" --apply --backup
```

### Insert text
```bash
# At absolute line
uv run grafty insert --line 42 --text "new line" --apply

# Relative to a node
uv run grafty insert "src/main.py:py_class:MyClass" \
  --inside-end \
  --text "def new_method(): pass" \
  --apply
```

### Validate a patch
```bash
uv run grafty check my.patch
```

### Apply atomic multi-file patches (Phase 4.1)
```bash
# Dry-run (show diffs without applying)
uv run grafty apply-patch my.patch

# Apply patch (with backups)
uv run grafty apply-patch my.patch --apply --backup

# Use JSON format instead of simple format
uv run grafty apply-patch my.patch --format json --apply

# Patch file formats:

# Simple format (one mutation per line):
# file_path:operation_kind:start_line:end_line[:text]
cat > my.patch << 'EOF'
src/main.py:replace:10:12:def new_func(): pass
src/config.py:insert:5:5:    DEBUG = False
src/old.py:delete:1:10:
EOF

# JSON format:
cat > my.patch << 'EOF'
[
  {
    "file_path": "src/main.py",
    "operation_kind": "replace",
    "start_line": 10,
    "end_line": 12,
    "text": "def new_func(): pass",
    "description": "Update main function"
  }
]
EOF

# Apply with specific repository root
uv run grafty apply-patch my.patch --apply --repo-root ~/myproject
```

## Development

### Run tests
```bash
uv run pytest tests/ -v
```

### Lint with ruff
```bash
uv run ruff check grafty/ tests/
```

### Format code
```bash
uv run black grafty/ tests/
```

### Type check with mypy
```bash
uv run mypy grafty/
```

## Supported Languages

- **Python**: Classes, functions, methods (Tree-sitter)
- **Markdown**: Headings & sections (Tree-sitter)
- **Org-mode**: Headings & subtrees (custom parser)
- **Clojure/ClojureScript**: Namespaces, defs, macros (Tree-sitter + fallback)

## Documentation

- Full CLI docs: `README.md`
- Architecture: `DESIGN.md`
- Progress: `PROGRESS.md`

---

## Tips

### Add to PATH for convenience
```bash
export PATH="$PATH:~/source/grafty/bin"
# Now you can just: grafty index .
```

### Use with git aliases
```bash
git config --global alias.gindex '!uv run grafty index'
git gindex src/  # now works as: git gindex src/
```

### Environment: uv automatically manages dependencies
- uv creates `.venv` on first run (automatically)
- Dependencies installed in venv via `pyproject.toml`
- No `pip install` or manual venv setup needed
