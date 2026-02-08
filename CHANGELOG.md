# Changelog

## [0.5.0] - 2026-02-08

### 🎯 Phase 4.1: Atomic Multi-File Patches

**Problem**: Users need to apply coordinated changes across multiple files atomically — if any file fails validation or writing, all changes are rolled back. Manual synchronization is error-prone.

**Solution**: 
- `PatchSet` class for managing and applying multiple file mutations
- Two input formats: simple line-based or JSON with metadata
- Atomic writes: all succeed or all rollback via temp files + rename
- Validation before any writes: detect conflicts, missing files, invalid line ranges
- Dry-run by default showing unified diffs before applying
- Optional `.bak` backups for recovery

**Implementation** (`grafty/multi_file_patch.py`):
- `FileMutation` dataclass for individual mutations
- `PatchSet.add_mutation()` / `load_from_json()` / `load_from_simple_format()` for building patches
- `PatchSet.validate_all()` checks all files and line numbers before applying
- `PatchSet.generate_diffs()` creates unified diffs for preview (dry-run)
- `PatchSet.apply_atomic()` writes atomically with rollback on error
- `PatchSetResult` provides structured error/success reporting

**CLI**:
```bash
# Dry-run (preview all changes)
grafty apply-patch my.patch

# Apply atomically
grafty apply-patch my.patch --apply --backup

# JSON format with metadata
grafty apply-patch my.patch --format json --apply
```

**Patch Formats**:

Simple (one mutation per line):
```
file_path:operation_kind:start_line:end_line[:text]
src/main.py:replace:10:12:def new_func(): pass
```

JSON (with descriptions):
```json
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
```

**Features**:
- ✅ Atomic writes (temp file + rename, not in-place)
- ✅ Validation before any writes
- ✅ Dry-run mode shows unified diffs
- ✅ Backup creation (.bak files)
- ✅ Rollback on error (restores from backups)
- ✅ Handles unicode, CRLF normalization, large files
- ✅ Merge conflict detection (overlapping mutations)
- ✅ Clear error reporting with context

**Testing**: 39 comprehensive tests
- Multi-file success scenarios (5 files atomically)
- Validation edge cases (invalid lines, non-existent files)
- Backup creation and recovery
- Unicode and large file handling
- Dry-run verification (no mutations)
- Integration tests (validate → dry-run → apply workflow)

**Backward Compatibility**: Zero breaking changes. Existing v0.4 API and CLI unchanged.

---

## [0.4.0] - 2026-02-08

### 🎯 Phase 3: Core Gaps Complete

Three complementary features that fill real workflow gaps:

#### 1. Line-Number Editing (3.1) ✅

**Problem**: Need precise line-based editing for diffs, stack traces, emergency fixes.

**Solution**: 
- `grafty replace file.py:42 --text "..."` — single line
- `grafty replace file.py:42-50 --text "..."` — line range
- Works with `show`, `replace`, `delete`, `insert --line`

**Implementation**:
- Reuses existing patch infrastructure
- `LineNumberSelector.parse()` disambiguates from `path:kind:name` format (single colon)
- Supports all mutation operations safely

**Examples**:
```bash
# Quick fix from a stack trace
grafty replace "src/main.py:42" --text "return None  # FIX" --apply

# Edit a section without structural knowledge
grafty replace "config.yaml:10-20" --file new_config.yaml --apply

# Show lines from a diff
grafty show "src/utils.py:42-50"

# Delete debug code
grafty delete "src/debug.py:15-25" --apply
```

#### 2. Improved Error Messages (3.2) ✅

**Problem**: Vague errors ("No node found matching...") made selectors hard to debug.

**Solution**:
- Show top 10 candidates when fuzzy match fails
- Include context: available nodes, line ranges, file location
- Explain selector format options in errors

**Implementation**:
- `_resolve_fuzzy()` returns best matches by edit distance
- `_resolve_by_line_numbers()` shows available nodes when line range misses
- All error messages include actionable context

**Examples**:
```
$ grafty show "myclass"
Error: No node found matching: 'myclass'.
Did you mean:
  src/main.py:py_class:MyClass
  src/utils.py:py_class:DataClass
(Searched 156 nodes)

$ grafty show "file.py:100-150"
Error: No node found in file.py lines 100-150.
Available: MyClass (1-50), helper (52-80), process (85-95), validate (100-110)
Tip: Use 'grafty index file.py' to see all nodes.
```

**Impact**: Users can discover selectors and debug mistakes without reading docs.

#### 3. Query Language / Search (3.3) ✅

**Problem**: Had to know exact node names to find code (`py_function:validate`). Couldn't discover or refactor.

**Solution**:
- `grafty search <pattern>` — glob-pattern matching on node names
- `grafty search <pattern> --path <glob>` — filter by file path
- `grafty search <pattern> --kind <kind>` — filter by node kind
- `grafty search <pattern> --json` — JSON output for scripting

**Patterns**:
- `*validate*` — contains "validate"
- `test_*` — starts with "test_"
- `*_error` — ends with "_error"
- `start*end` — starts with "start", ends with "end"
- `*` — all nodes (useful with --kind filter)

**Implementation**:
- Uses Python's `fnmatch` (shell-style glob patterns)
- Not regex (simpler, more approachable)
- Leverages existing `query_nodes_by_pattern()` and `query_nodes_by_path_glob()`

**Examples**:
```bash
# Find all validation functions/methods
grafty search "*validate*"
# [py_function    ] validate_email      src/validators.py:45-60
# [py_method      ] validate            src/User.py:100-120
# ...

# Find all tests in tests/ directory
grafty search "test_*" --path "tests/"

# Find all Go error handling code
grafty search "*error*" --kind "go_function"

# Find struct/class definitions containing "data"
grafty search "*data*" --kind "rs_struct"

# List all methods in a class (for analysis)
grafty search "*" --kind "py_method" --json | jq '.nodes[] | .name'
```

**Impact**:
- Users can refactor "all validation functions" without manual grep
- Enables "find all X" workflows that were previously tedious
- Makes code structure discoverable through pattern queries

### 📊 Test Coverage
- **24 new tests** for Phase 3 features (line selectors, improved errors, search patterns)
- **78 total tests** passing (54 v0.3 + 24 v0.4)
- **100% backward compatible** with v0.3.0

### 🔧 Quality Gates Met
✅ All tests passing
✅ Linting clean (ruff)
✅ No breaking changes
✅ All existing selectors work unchanged
✅ All Phase 3 goals achieved:
  - Safe line editing with fallback to patches
  - Discoverable selectors via error messages
  - Query language for pattern-based code discovery

### 🎓 Architecture Decisions
- **Why line numbers + structural**: Complementary approaches, different use cases
- **Why glob patterns, not regex**: Simplicity, approachability, composability
- **Why error context**: Selectors discoverable from errors, no docs lookup needed

See `ARCHITECTURE_DECISIONS.md` for full rationale.

---

## [0.3.0] - 2026-02-08

### ✨ Multi-Language Support

#### JavaScript/TypeScript Parser
- **Node kinds**: `js_function`, `js_class`, `js_method`
- **Supported files**: `.js`, `.ts`, `.jsx`, `.tsx` (JSX/TypeScript compatible)
- **Example**: `grafty show "app.ts:js_class:DataProcessor"`

#### Go Parser
- **Node kinds**: `go_function`, `go_method`, `go_type`
- **Supported files**: `.go`
- **Example**: `grafty show "main.go:go_method:Process"`

#### Rust Parser
- **Node kinds**: `rs_function`, `rs_struct`, `rs_impl`, `rs_method`, `rs_trait`, `rs_macro`
- **Supported files**: `.rs`
- **Example**: `grafty show "lib.rs:rs_impl:DataProcessor"`

### 🧪 New Tests
- 17 comprehensive tests for JS, Go, Rust parsers
- All 54 tests passing (37 original + 17 new)

### 🔄 Backward Compatibility
✅ **100% compatible** — All existing parsers and features work unchanged

---

## [0.2.0] - 2026-02-08

### ✨ New Features

#### Heading Preambles (Markdown & Org-mode)
- **What**: Two new node kinds for safer section editing
  - `md_heading_preamble` — Intro text of a markdown heading
  - `org_heading_preamble` — Intro text of an org heading
- **Why**: Edit section intros without destroying subheadings
- **Example**:
  ```bash
  # Full section (lines 1-10, includes children)
  grafty replace "file.org:org_heading:Phase 1" --text "..."
  
  # Preamble only (lines 1-4, stops before first child)
  grafty replace "file.org:org_heading_preamble:Phase 1" --text "..."
  ```

### 🐛 Bug Fixes
- Fixed fuzzy selector matching when multiple nodes have same name
  - Now correctly sorts by match score without comparing Node objects

### 📚 Documentation
- Added preamble usage examples to README
- Updated architecture decisions (FEATURE_PLAN_PREAMBLES.md)

### 🧪 Testing
- Added 16 comprehensive tests for preambles
  - Markdown preamble extraction (4 tests)
  - Org preamble extraction (4 tests)
  - Selector resolution (3 tests)
  - Editing operations (2 tests)
  - Edge cases (3 tests)
- All 37 tests passing ✅

### 🔄 Backward Compatibility
✅ **Fully backward compatible**
- Existing `org_heading` and `md_heading` selectors work unchanged
- New preamble selectors are opt-in
- All existing tests still pass

---

## [0.1.0] - 2026-02-08

Initial release with:
- Python, Markdown, Org-mode, Clojure parsers
- Full section editing (replace/insert/delete)
- Unified diff generation
- Atomic writes with drift detection
- Token-optimized output for LLM agents
