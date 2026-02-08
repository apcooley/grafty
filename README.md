# grafty — Token-Optimized Structural Editor

A CLI tool for refactoring and editing large code/text files by referencing stable structural selectors (headers, functions, classes) instead of emitting entire file contents.

**Perfect for**: LLM agents, batch editing, token-efficient workflows.

---

## Problem & Solution

### The Problem
LLM agents working with large files often exceed token budgets. You want to edit a specific function, but showing the whole file is expensive.

### The Solution
grafty indexes files into **structural units** (functions, classes, headings, etc.) and lets you edit by **selector** instead of line numbers.

```bash
# Instead of: "Show me line 42-107"
# You can do: "Show me the parse_config function"
grafty show "src/main.py:py_function:parse_config"
# Returns only the function (bounded output, no token waste!)

# Edit it safely with unified diffs
grafty replace "src/main.py:py_function:parse_config" \
  --file new_impl.py --dry-run
# See the exact change before applying
```

---

## Installation

grafty is already installed as a system tool:

```bash
which grafty         # See installation location
grafty --help        # Show commands
grafty index .       # Index current directory
```

### For Development

```bash
cd ~/source/grafty
uv sync              # Install dev dependencies
uv run grafty index . # Run with dev env
uv run pytest        # Run test suite (37 tests)
```

### Requirements
- Python 3.10+
- Dependencies auto-managed via uv (`pyproject.toml`)

---

## Quick Start

### 1. Index a File

```bash
grafty index src/main.py

# Output:
# src/main.py (8 nodes)
# [py_class   ] DataProcessor          (  1-  50)
#   [py_method] parse                   (  5-  20)
#   [py_method] validate                (  22- 35)
# [py_function] main                    (  52-  65)
```

### 2. Show a Node

```bash
# Show a specific function
grafty show "src/main.py:py_function:main"

# Bound output to prevent token waste
grafty show "src/main.py:py_class:DataProcessor" --max-lines 30 --max-chars 2000

# Get JSON output for scripting
grafty show "src/main.py:py_function:parse" --json
```

### 3. Replace a Node

```bash
# Preview the change (dry-run)
grafty replace "src/main.py:py_function:old_impl" --text "def old_impl():\n    return 42" --dry-run

# Apply it
grafty replace "src/main.py:py_function:old_impl" --text "def old_impl():\n    return 42" --apply --backup

# Or read from file
grafty replace "src/main.py:py_function:old_impl" --file new_impl.py --apply
```

### 4. Delete a Node

```bash
grafty delete "src/main.py:py_function:unused_func" --apply
```

### 5. Validate a Patch

```bash
grafty check my.patch
# Uses git apply --check (if in git repo)
```

---

## Supported File Types

| Type | Features | Example |
|------|----------|---------|
| **Python** (.py) | Classes, methods, functions | `file.py:py_class:MyClass` |
| **Markdown** (.md) | Headings, sections, **preambles** | `file.md:md_heading:Title` |
| **Org-mode** (.org) | Headings, subtrees, **preambles** | `file.org:org_heading:Title` |
| **Clojure** (.clj/.cljs) | Namespaces, defs, macros | `file.clj:clj_defn:my_func` |

---

## ✨ Heading Preambles (Markdown & Org)

**New in v0.2.0**: Edit section intros without destroying subheadings!

### The Problem
```org
** Phase 1: Planning       ← Heading (lines 5-14)
Planning intro text.
                          ← Want to edit just this intro...
*** Week 1                ← But replacing the heading loses this!
Week 1 tasks.
*** Week 2
Week 2 tasks.
```

### The Solution: Preambles

Every heading gets **two selectors**:

```bash
# 1. Full section (old behavior, includes children)
grafty replace "file.org:org_heading:Phase 1" --text "..." --apply
# Replaces lines 5-14 (heading + intro + children)

# 2. Preamble ONLY (new, stops before first child)
grafty replace "file.org:org_heading_preamble:Phase 1" --text "..." --apply
# Replaces lines 5-8 (heading + intro only) ← Children PRESERVED! ✅
```

### Usage Examples

```bash
# Show preamble (intro text only)
grafty show "file.org:org_heading_preamble:Phase 1"

# Replace preamble
grafty replace "file.org:org_heading_preamble:Phase 1" \
  --text "** Phase 1\nNew intro text here." --apply

# Delete preamble (removes intro, keeps structure)
grafty delete "file.org:org_heading_preamble:Phase 1" --apply
```

### Index Output
```bash
$ grafty index file.org

file.org (18 nodes)
[org_heading           ] Phase 1: Planning    (6-14)    ← Full
[org_heading_preamble ] Phase 1: Planning    (6-9)     ← Preamble
  [org_heading        ] Week 1               (10-12)   ← Child
  [org_heading_preamble] Week 1              (10-12)   ← Child preamble
```

---

## Selectors

Selectors identify nodes. Four formats:

### 1. By ID (most precise)
```bash
grafty show "abc123def456"
```

### 2. By Path, Kind, Name (recommended)
```bash
grafty show "src/main.py:py_function:parse_config"
grafty show "docs/readme.md:md_heading:Installation"
grafty show "tasks.org:org_heading_preamble:Phase 1"
```

### 3. Fuzzy Name (ambiguous → shows candidates)
```bash
grafty show "parse_config"
# If ambiguous:
# Error: Did you mean:
#   src/main.py:py_function:parse_config
#   src/utils.py:py_function:parse_config
```

### 4. Relative to Node (for insert)
```bash
grafty insert "file.py:py_class:MyClass" --inside-end --text "..."
# Also: --before, --after, --inside-start
```

---

## CLI Commands

### index
List all structural units in files.

```bash
grafty index src/
grafty index . --json  # JSON output
```

**Flags**: `--json`

### show
Display a node's content (bounded output).

```bash
grafty show "file.py:py_function:my_func"
grafty show "file.py:py_function:my_func" --max-lines 50 --max-chars 2000
grafty show "file.py:py_function:my_func" --json
```

**Flags**: `--max-lines`, `--max-chars`, `--json`, `--repo-root`

### replace
Replace a node's content.

```bash
grafty replace "file.py:py_function:old" --text "def old(): return 42" --dry-run
grafty replace "file.py:py_function:old" --file new.py --apply --backup
```

**Flags**: `--text`, `--file`, `--dry-run`, `--apply`, `--backup`, `--force`, `--patch-out`, `--repo-root`

### insert
Insert text at a line or relative to a node (in development).

```bash
grafty insert "file.py:py_class:MyClass" --inside-end --text "def new_method(self): pass"
```

### delete
Delete a node.

```bash
grafty delete "file.py:py_function:unused" --apply --backup
```

**Flags**: `--apply`, `--backup`, `--dry-run`, `--force`, `--patch-out`

### check
Validate a patch file.

```bash
grafty check my.patch
# Uses: git apply --check (if in git repo)
```

---

## Architecture

### Components

```
CLI (cli.py)
  ↓
Indexer (indexer.py) → Parsers (parsers/)
  ↓                     ├─ python_ts.py
Resolver (selectors.py) ├─ markdown_ts.py
  ↓                     ├─ org.py
Editor (editor.py)      └─ clojure_ts.py
  ↓
Patcher (patch.py) → Atomic writes
```

### Key Design Decisions

1. **Tree-sitter First**: Use Tree-sitter for reliable parsing (Python, Markdown, Clojure). Fall back to simpler parsers (Org-mode uses regex-based star counter).

2. **Structural Selectors**: Index by **structure** (function name, heading text), not by **line numbers** (more stable, token-efficient).

3. **Unified Diffs**: All mutations generate patches for safe, reviewable changes.

4. **Atomic Writes**: Temp file → rename (no partial writes).

5. **Preambles**: Two nodes per heading for safer editing of section intros.

See `ARCHITECTURE_DECISIONS.md` for full rationale.

---

## Development

### Install Dev Dependencies

```bash
cd ~/source/grafty
uv sync  # Installs all dev tools (pytest, ruff, mypy, etc.)
```

### Run Tests

```bash
uv run pytest tests/                     # All tests
uv run pytest tests/test_preambles.py -v # Specific test file
uv run pytest tests/ -k "preamble"       # Matching tests
```

Current: **37/37 tests passing** ✅

### Lint & Format

```bash
uv run ruff check grafty/ tests/
uv run black grafty/ tests/
uv run mypy grafty/
```

### Run grafty with Dev Env

```bash
uv run grafty index .
uv run grafty show "file.py:py_function:my_func"
```

---

## Examples

### Example 1: Edit a Python Function

```bash
# Index to find the function
grafty index src/math.py
# Output: py_function "add" (lines 5-8)

# Show it
grafty show "src/math.py:py_function:add"
# def add(a, b):
#     return a + b

# Replace it
grafty replace "src/math.py:py_function:add" \
  --text "def add(a, b):\n    \"\"\"Sum two numbers.\"\"\"\n    return a + b" \
  --dry-run
# Shows: --- a/src/math.py
#        +++ b/src/math.py
#        @@ ...
#         def add(a, b):
#        +"    \"\"\"Sum two numbers.\"\"\""
#         return a + b

# Apply it
grafty replace "src/math.py:py_function:add" \
  --text "def add(a, b):\n    \"\"\"Sum two numbers.\"\"\"\n    return a + b" \
  --apply
```

### Example 2: Edit Markdown Section Intro

```bash
# Show a section
grafty show "README.md:md_heading:Installation"

# Edit just the intro (keep subsections)
grafty replace "README.md:md_heading_preamble:Installation" \
  --text "# Installation\n\nNew installation instructions here." \
  --apply
# Subsections (## Prerequisites, ## Quick Start, etc.) stay intact!
```

### Example 3: Org-mode Refactoring

```bash
# Show full section
grafty show "tasks.org:org_heading:Phase 1"
# Output:
# * Phase 1: Planning
# 
# Planning details.
# 
# ** Week 1
# Week 1 tasks.

# Update intro without losing subheadings
grafty replace "tasks.org:org_heading_preamble:Phase 1" \
  --text "* Phase 1: Planning\n\n🚀 Updated planning details." \
  --apply
# ** Week 1 and ** Week 2 preserved! ✅
```

---

## FAQ

**Q: Why not just use grep/sed?**
A: sed works on patterns, grafty understands structure. `py_function:add` is more precise than `^def add`, handles nested scopes, and works across languages.

**Q: What about merge conflicts?**
A: Patches are unified diffs. Use standard merge tools. grafty outputs valid patches that `git merge` understands.

**Q: Can I use this with LLMs?**
A: Yes! grafty is designed for LLM workflows:
- Index large files, show bounded snippets
- Agents use selectors instead of line ranges
- Get diffs for review before applying
- Example: "Replace the `validate` method with: [new code]"

**Q: Is it safe?**
A: Yes:
- Atomic writes (temp → rename)
- Optional backups (`.bak` files)
- File drift detection (hash-based)
- Dry-run mode (preview before applying)
- Patch validation (`git apply --check`)

**Q: What about unsupported file types?**
A: grafty skips them, but line-based editing still works via patches.

---

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Current status:
# 37/37 tests passing ✅
# - Python parsing (4 tests)
# - Markdown parsing + preambles (8 tests)
# - Org-mode parsing + preambles (8 tests)
# - Clojure parsing (3 tests)
# - Patch operations (6 tests)
# - Preamble editing (2 tests)
# - Edge cases (3 tests)
```

---

## Changelog

**v0.2.0** (2026-02-08)
- ✨ Heading preambles for Markdown & Org-mode
- 🐛 Fixed fuzzy selector matching
- 📚 Comprehensive documentation

**v0.1.0** (2026-02-08)
- Initial release
- Python, Markdown, Org-mode, Clojure parsers
- Full structural editing (replace/insert/delete)

---

## Documentation

- `USAGE.md` — Quick command reference
- `ARCHITECTURE_DECISIONS.md` — Design rationale
- `CHANGELOG.md` — Version history
- `DESIGN.md` — Initial architecture planning
- `/docs/` — Additional guides (TBD)

---

## License

MIT

---

## Contributing

Contributions welcome! Areas of interest:
- Additional language parsers (Go, Rust, Java)
- List item and table cell nodes
- Web UI for patch visualization
- Integration with language servers

---

**Ready to use.** Questions? Check the docs or run `grafty --help`.
