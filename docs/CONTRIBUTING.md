# Contributing to grafty

**Welcome!** grafty is actively developed and we love contributions—whether it's code, docs, bug reports, or real-world feedback.

This guide will help you get started.

---

## Getting Started

### 1. Read the Design

Before diving into code, understand why grafty exists and how it works:

- **[ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)** — Core design philosophy and trade-offs
- **[ROADMAP.md](./ROADMAP.md)** — Phases 4-7 and the vision for what's next
- **[USAGE.md](../USAGE.md)** — What grafty can do right now

### 2. Set Up Your Environment

```bash
cd ~/source/grafty

# Install dependencies (auto-managed by uv)
uv sync

# Verify everything works
uv run grafty --help
uv run pytest tests/ -v    # Should pass all 37 tests
```

### 3. Pick Your Task

See **[ROADMAP.md](./ROADMAP.md)** for phases 4–7.

**New to the project?** Start with one of these:

#### Low-Complexity Starter Tasks (Phase 3 wrap-up)

- 📝 **Improve error messages** — When a selector doesn't match, suggest similar function names
  - File: `grafty/core/selector.py`
  - Effort: 2-4 hours
  - Skills: Python, string matching

- 📚 **Add documentation examples** — Write detailed examples for `USAGE.md` showing LLM workflows
  - File: `USAGE.md` (new section)
  - Effort: 3-4 hours
  - Skills: Writing, understanding use cases

- 🐛 **Fix edge cases in Markdown parsing** — Handle nested code blocks and HTML comments
  - File: `grafty/languages/markdown.py`
  - Effort: 4-6 hours
  - Skills: Python, regex, Markdown syntax

#### Medium-Complexity Tasks (Phase 4 prep)

- 🔐 **Multi-file dry-run support** — Show unified diff for multiple files before applying
  - Files: `grafty/core/replace.py`, `grafty/cli/commands.py`
  - Effort: 6-8 hours
  - Skills: Python, file I/O, diff generation

- 📝 **Docstring extraction** — Show/edit Python docstrings separately from function bodies
  - File: `grafty/languages/python.py`
  - Effort: 8-10 hours
  - Skills: Python, AST parsing, Tree-sitter queries

#### High-Complexity Tasks (Phase 5+)

- 🌳 **Tree explorer CLI** — Interactive ASCII tree of codebase structure
  - New file: `grafty/cli/explorer.py`
  - Effort: 2-3 days
  - Skills: Python, terminal UI (curses or rich)

- ⚡ **Index caching system** — Serialize/deserialize parsed ASTs to avoid re-parsing
  - New file: `grafty/cache/index_cache.py`
  - Effort: 3-5 days
  - Skills: Python, serialization, cache invalidation

- 🌐 **Web UI prototype** — Browser-based editor for grafty
  - New directory: `grafty/web/`
  - Effort: 1-2 weeks
  - Skills: Python (FastAPI), React, TypeScript

---

## Complexity Levels

### Low
- Minor bug fixes
- Documentation improvements
- Error message tweaks
- Simple test cases
- **Time:** 2-4 hours

### Medium
- Add a new feature to an existing component
- Expand language support (new queries)
- Improve CLI interface
- Performance optimizations
- **Time:** 1-3 days

### High
- Entire new subsystem (caching, LSP, web UI)
- Add a completely new language
- Multi-file atomic operations
- **Time:** 1-2+ weeks

---

## How to Work on a Task

### 1. Create a Branch

```bash
git checkout -b feature/my-feature-name
```

### 2. Write Tests First (TDD)

```bash
# See existing tests for patterns
ls tests/

# Add your test
cat > tests/test_my_feature.py << 'EOF'
import pytest
from grafty.core.my_module import my_function

def test_my_feature():
    result = my_function("input")
    assert result == "expected_output"
EOF

# Run tests (will fail initially)
uv run pytest tests/test_my_feature.py -v
```

### 3. Implement the Feature

Edit the relevant file(s) in `grafty/` until your test passes:

```bash
# Run tests again
uv run pytest tests/test_my_feature.py -v

# Run all tests to ensure no regressions
uv run pytest tests/ -v
```

### 4. Lint Your Code

```bash
uv run ruff check grafty/
uv run ruff format grafty/
```

### 5. Commit with a Clear Message

```bash
git add .
git commit -m "feat: Add my feature

- What it does
- Why it matters
- References to issue #123 (if applicable)"
```

### 6. Push and Open a Pull Request

```bash
git push origin feature/my-feature-name
```

Then open a PR on GitHub with:
- **Title:** Clear, one-liner
- **Description:** What, why, testing notes
- **Linked issue:** `Closes #123` (if fixing an issue)

---

## Testing Workflow

### Run Specific Tests

```bash
# One test file
uv run pytest tests/test_selectors.py -v

# One test function
uv run pytest tests/test_selectors.py::test_py_function_selector -v

# Pattern matching
uv run pytest tests/ -k "markdown" -v
```

### Check Test Coverage

```bash
uv run pytest tests/ --cov=grafty --cov-report=term-missing
```

### All Tests Should Pass

Before submitting a PR:

```bash
uv run pytest tests/ -v    # All 37 tests pass
uv run ruff check grafty/  # No lint issues
```

---

## Code Style

grafty follows **PEP 8** with a few conventions:

- **Line length:** 100 characters
- **Imports:** Sorted with `ruff`
- **Type hints:** Optional but appreciated (help with IDE support)
- **Docstrings:** Google-style (`"""Summary.\n\nDetails."""`)

Run `ruff check` before committing—it catches style issues automatically.

---

## Understanding the Codebase

### Structure

```
grafty/
├── core/
│   ├── selector.py       # Parse and match selectors like "file.py:py_function:name"
│   ├── index.py          # Index a file into structured nodes
│   ├── show.py           # Show a bounded snippet
│   └── replace.py        # Replace/edit operations
├── languages/
│   ├── python.py         # Python-specific parser (Tree-sitter)
│   ├── javascript.py     # JS/TS parser
│   ├── markdown.py       # Markdown parser
│   └── ...
├── cli/
│   ├── commands.py       # CLI command handlers
│   └── formatter.py      # Output formatting
└── util/
    └── diff.py           # Unified diff generation

tests/
├── test_selectors.py
├── test_index.py
├── test_python.py
├── test_markdown.py
└── ...
```

### Key Modules

**`core/selector.py`** — The heart of grafty  
Parse selectors like `"file.py:py_function:my_func"` and match them against nodes.

**`core/index.py`** — Build the file index  
Use Tree-sitter to parse files and extract structured nodes (functions, classes, headings).

**`languages/*.py`** — Language-specific parsers  
Each language defines queries for Tree-sitter to extract nodes (e.g., `py_function`, `js_method`).

**`core/replace.py`** — Safe replacements  
Show dry-run diffs and apply changes atomically.

---

## Design Philosophy

Before making big changes, read **[ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)** to understand:

- **Why Tree-sitter?** (syntax-based, portable, fast)
- **Why structural editing?** (tokens, stability, LLM-friendly)
- **Why not LSP?** (overkill for CLI, but could integrate in Phase 6)
- **Safety-first approach** — Atomic writes, dry-runs, backups

---

## Getting Help

- **Questions?** Open a [GitHub discussion](https://github.com/apcooley/grafty)
- **Bug report?** Open an [issue](https://github.com/apcooley/grafty/issues)
- **Design question?** Ask in a discussion or check the docs

---

## Thank You! 🎯

Contributing to grafty—whether small fixes or big features—helps make code editing better for everyone (humans and LLMs alike).

**Pick a task, write some tests, and have fun.** 🚀
