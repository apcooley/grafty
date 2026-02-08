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
| **JavaScript/TypeScript** (.js, .ts, .jsx, .tsx) | Functions, classes, methods | `app.ts:js_function:handler` |
| **Go** (.go) | Functions, methods, types | `main.go:go_function:main` |
| **Rust** (.rs) | Functions, structs, impls, traits, macros | `lib.rs:rs_impl:DataProcessor` |
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

## Line-Number Editing (Phase 3.1)

**New in v0.4.0**: Edit specific lines without needing to know structural context.

### Single Line

```bash
# Replace line 42
grafty replace "file.py:42" --text "new_content" --apply

# Show line 42
grafty show "file.py:42"

# Delete line 42
grafty delete "file.py:42" --apply
```

### Line Ranges

```bash
# Replace lines 42-50
grafty replace "file.py:42-50" --text "new_impl" --apply

# Show lines 42-50
grafty show "file.py:42-50"

# Delete lines 42-50
grafty delete "file.py:42-50" --apply
```

### When to Use Line Numbers
- Quick fixes and emergency edits
- When you're working from a diff or stack trace
- Complementing existing line-based workflows (sed, awk)
- When structural selectors are overkill for simple changes

---

## Query Language / Search (Phase 3.3)

**New in v0.4.0**: Find nodes by pattern matching.

### Search by Name Pattern

```bash
# Find all functions/methods containing "validate"
grafty search "*validate*"
# Output:
# Found 5 nodes matching '*validate*':
# [py_function    ] validate_email      src/validators.py:45-60
# [py_function    ] validate_config     src/config.py:20-35
# [py_method      ] validate            src/User.py:100-120
# ...

# Find all test functions
grafty search "test_*"

# Find all ending with "_error"
grafty search "*_error"
```

### Search with Path Filter

```bash
# Find all validation functions in src/
grafty search "*validate*" --path "src/"

# Find all handlers in handlers/ directory
grafty search "handle_*" --path "src/handlers/"

# Works with glob patterns
grafty search "*process*" --path "src/**/"
```

### Search with Kind Filter

```bash
# Find all methods (not functions) containing "process"
grafty search "*process*" --kind "py_method"

# Find all structs containing "data"
grafty search "*data*" --kind "rs_struct"

# Find all Go functions
grafty search "*" --kind "go_function"
```

### JSON Output

```bash
# Get results as JSON for scripting
grafty search "test_*" --json
# Output:
# {
#   "pattern": "test_*",
#   "count": 12,
#   "nodes": [
#     {
#       "id": "abc123...",
#       "name": "test_parse",
#       "kind": "py_function",
#       "path": "tests/test_parser.py",
#       "start_line": 42,
#       "end_line": 65
#     },
#     ...
#   ]
# }
```

### Patterns Supported
- `*pattern` — ends with "pattern"
- `pattern*` — starts with "pattern"
- `*pattern*` — contains "pattern"
- `start*end` — starts with "start", ends with "end"
- `*` — all nodes (useful with --kind filter)

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
# By structural selector
grafty show "file.py:py_function:my_func"

# By line numbers (Phase 3)
grafty show "file.py:42"
grafty show "file.py:42-50"

# With options
grafty show "file.py:py_function:my_func" --max-lines 50 --max-chars 2000 --json
```

**Flags**: `--max-lines`, `--max-chars`, `--json`, `--repo-root`

### search
Find nodes by pattern matching (Phase 3.3).

```bash
# Search by name pattern
grafty search "*validate*"

# With path filter
grafty search "*process*" --path "src/"

# With kind filter
grafty search "*handler*" --kind "py_function"

# JSON output
grafty search "test_*" --json
```

**Flags**: `--path`, `--kind`, `--json`, `--repo-root`

### replace
Replace a node's content.

```bash
# By structural selector
grafty replace "file.py:py_function:old" --text "def old(): return 42" --apply

# By line numbers (Phase 3)
grafty replace "file.py:42-50" --file new_impl.py --apply

# Dry-run mode (preview before applying)
grafty replace "file.py:py_function:old" --file new.py --dry-run
```

**Flags**: `--text`, `--file`, `--dry-run`, `--apply`, `--backup`, `--force`, `--patch-out`, `--repo-root`

### insert
Insert text at a line or relative to a node.

```bash
# Absolute line insertion
grafty insert --line 42 --text "new_line" --apply

# Relative to selector
grafty insert "file.py:py_class:MyClass" --inside-end --text "def new_method(): pass" --apply
```

**Flags**: `--line`, `--before`, `--after`, `--inside-start`, `--inside-end`, `--text`, `--file`, `--apply`, `--dry-run`, `--backup`, `--patch-out`, `--repo-root`

### delete
Delete a node or line range.

```bash
# By structural selector
grafty delete "file.py:py_function:unused" --apply

# By line numbers (Phase 3)
grafty delete "file.py:42-50" --apply --backup

# Dry-run to preview
grafty delete "file.py:py_function:unused" --dry-run
```

**Flags**: `--apply`, `--backup`, `--dry-run`, `--force`, `--patch-out`, `--repo-root`

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

## 🗺️ Roadmap

Grafty is designed around **boundaries**: every feature is precise, safe, and doesn't bleed into others. This roadmap reflects lessons learned from Phase 1 & 2 development.

### Phase 3: Core Gaps ✅ Complete

**Status**: All three Phase 3 features shipped in v0.4.0!

#### 3.1: Line-Number Editing ✅
- **What**: Support `grafty replace file.py:42-50 --text "..."`
- **Selector formats**: `file.py:42` (single) and `file.py:42-50` (range)
- **Works with**: replace, show, delete, insert --line
- **Impact**: Complements structural editing; handles quick fixes and diff-based workflows
- **Status**: Implemented and tested

#### 3.2: Improved Error Messages ✅
- **What**: Show candidates and helpful context on selector failures
- **Features**: 
  - Top 10 candidates shown when fuzzy match finds multiple
  - Context about available nodes (name, line range) when selector doesn't resolve
  - Clear error messages explaining how to disambiguate
- **Example**: 
  ```
  Error: No node found in src/main.py lines 42-50.
  Available: MyClass (1-20), helper (22-35), process (35-70)
  ```
- **Status**: Implemented with improved UX

#### 3.3: Query Language / Search ✅
- **What**: Pattern matching on node names
- **Command**: `grafty search <pattern> [--path <glob>] [--kind <kind>] [--json]`
- **Patterns**: `*validate*`, `test_*`, `*_error`, etc. (fnmatch glob patterns)
- **Impact**: Discover code without knowing exact names; enable "find all X" workflows
- **Examples**:
  - `grafty search "*validate*"` → all validation functions/methods
  - `grafty search "test_*" --path "tests/"` → all tests
  - `grafty search "*handler*" --kind "js_function"` → JS handlers
- **Status**: Fully implemented

### Phase 4: Safety & Collaboration

Features that make grafty safe and auditable in team environments.

#### 4.1: Multi-File Patches
- **Why**: Real refactors span multiple files (rename class → update all references)
- **What**: Single unified diff covering multiple files
  ```bash
  grafty replace src/a.py:py_class:Processor \
                  src/b.py:py_function:create_processor \
                  --file changes.patch --apply
  ```
- **Impact**: Atomic cross-file edits; coordinated refactoring
- **Complexity**: High (extend patch infrastructure)
- **Status**: Future (v0.4+)

#### 4.2: VCS Integration (Git/Hg/SVN)
- **Why**: Full traceability; automatic rollback on failure
- **What**:
  - Auto-commit after successful edits (with message template)
  - Atomic: if patch fails, rollback to pre-edit state
  - Multi-VCS support
- **Impact**: Zero-risk editing; audit trail for every change
- **Complexity**: Medium (spawn VCS commands, handle errors)
- **Status**: Future (v0.4+)

#### 4.3: Comment/Docstring Extraction
- **Why**: Documentation lives in code; sometimes you only want to edit docs
- **What**: New node kinds for docstrings
  - `py_docstring:MyClass` → docstring only
  - `rs_doc_comment:validate` → rustdoc comment
  - `go_godoc:Package` → package-level godoc
- **Impact**: Update docs without risking code; extract API reference
- **Complexity**: Medium (per-language comment parsing)
- **Status**: Future (v0.4+)

### Phase 5: Discovery & Visualization

Features that make patches understandable and reviewable.

#### 5.1: Web UI for Patch Visualization
- **Why**: Unified diffs are hard to review for non-technical users
- **What**:
  - Side-by-side before/after view with syntax highlighting
  - Click to apply/reject individual hunks
  - Show structural context (class → method changed)
- **Impact**: Makes reviewing agent-generated patches non-scary
- **Complexity**: High (React/Vue UI, diff rendering)
- **Status**: Future (v0.5+)

#### 5.2: Node Hierarchy Visualization
- **Why**: Understanding structure helps with selector discovery
- **What**:
  - `grafty tree file.py` → ASCII tree of all nodes
  - Interactive web explorer (drill down by kind/name)
  - Export as JSON/GraphQL
- **Impact**: Helps agents understand file structure before editing
- **Complexity**: Medium (tree rendering)
- **Status**: Future (v0.5+)

### Phase 6: Performance & Scale

Features that make grafty work on large codebases and generated code.

#### 6.1: Index Caching
- **Why**: Currently, 10MB+ files are slow (re-parse every run)
- **What**:
  - Persist parse tree to `.grafty.cache/`
  - Invalidate on file change (mtime + hash)
  - Share cache across commands
- **Impact**: 10-50x speedup for large files
- **Complexity**: Medium (cache invalidation is hard)
- **Status**: Future (v0.5+)

#### 6.2: Language Server Integration
- **Why**: Tree-sitter is good; LSP is better (semantic info, real symbols)
- **What**:
  - Optional: use LSP instead of Tree-sitter for languages with good servers
  - Fallback: Tree-sitter if LSP unavailable
  - Tradeoff: more dependencies, less portable
- **Impact**: Better type awareness, actual compiler symbols
- **Complexity**: High (LSP protocol, language-specific servers)
- **Status**: Future (v0.6+, optional)

### Phase 7: Extended Languages

Parsers for ecosystems where grafty would unlock value.

- **Go, Rust, Java**: High demand (already v0.3 has Go/Rust)
- **C/C++**: Complex but valuable for large codebases
- **JavaScript/TypeScript**: Already in v0.3; consider Web-specific nodes (DOM, React)
- **SQL**: Query structure extraction (stored procedures, schemas)

---

## 🎯 Design Principles (Guiding All Phases)

1. **Precise Boundaries**: Every node has clear start/end. No ambiguity.
2. **Backward Compatibility**: New features don't break old selectors.
3. **Token Efficiency**: Every feature saves tokens vs. showing whole files.
4. **Safety First**: Atomic writes, drift detection, dry-run always available.
5. **Structural > Textual**: Understand code shape, not patterns.

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

**v0.4.0** (2026-02-08) — Phase 3 Complete ✅
- ✨ **Line-number editing**: `file.py:42` and `file.py:42-50` selectors
- ✨ **Improved error messages**: Candidates + context on selector failures
- ✨ **Query language**: `grafty search` command with glob patterns
- 🧪 24 new tests for Phase 3 (78 total passing)
- 📚 Updated documentation with Phase 3 examples
- 🎯 All Phase 3 goals achieved: safe line editing, better discovery, discoverable selectors

**v0.3.0** (2026-02-08)
- ✨ Multi-language support: JavaScript/TypeScript, Go, Rust
- 🧪 17 new parser tests (54/54 total passing)
- 📋 Comprehensive roadmap for future phases
- 📚 Retrospective + feature analysis

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

Contributions welcome! See the **[Roadmap](#-roadmap)** for detailed phases and complexity levels.

**High-impact, low-complexity starter tasks:**
- Line-number editing (Phase 3.1)
- Improved error messages (Phase 3.2)
- Query language for finding code (Phase 3.3)
- Comment/docstring extraction (Phase 4.3)

**Challenging but valuable:**
- Multi-file patches (Phase 4.1)
- VCS integration (Phase 4.2)
- Web UI (Phase 5.1)
- Language server integration (Phase 6.2)

**Always welcome:**
- Bug reports with minimal reproducers
- Performance profiling + optimization ideas
- Real-world use case feedback
- Documentation improvements

---

**Ready to use.** Questions? Check the docs or run `grafty --help`.
