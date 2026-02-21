# Changelog

## [0.7.0] - 2026-02-10

### 🎯 Phase 5.1: HTML/CSS Parser Support

**Problem**: grafty supports Python, Markdown, Org, Clojure, JavaScript, Go, and Rust, but doesn't support HTML and CSS — two of the most widely used web-related file formats. Web developers need to index and manipulate HTML/CSS files with the same efficiency as code files.

**Solution**:
- New HTML parser (`HTMLParser`) for parsing HTML documents
- New CSS parser (`CSSParser`) for parsing CSS stylesheets
- Dedicated node types for IDs, classes, and special attributes
- Regex fallback for CSS parser when cssutils is unavailable
- Complete integration with parser registry system

**Implementation**:

#### HTML Parser (`grafty/parsers/html_parser.py`)
- `HTMLNode`: Represents HTML elements with attributes, children, and line tracking
- `HTMLParser`: Extends Python's `html.parser` for robust parsing
- Node types:
  - `html_element`: All HTML tags (div, span, button, etc.)
  - `html_id`: Special nodes for ID attributes (efficient selection)
  - `html_class`: One node per class value (supports multi-class elements)
  - `html_attr`: Data and ARIA attributes (`data-*`, `aria-*`)
- Helper functions: `parse_html_file()`, `extract_html_ids()`, `extract_html_classes()`, `find_html_node_by_name()`
- Features: Tree + flat list structure, parent-child relationships, line/column tracking

#### CSS Parser (`grafty/parsers/css_parser.py`)
- `CSSNode`: Represents CSS rules and selectors with declarations
- `CSSParser`: Dual-mode parser (cssutils primary, regex fallback)
- Node types:
  - `css_rule`: Complete CSS rule with declarations
  - `css_selector`: Individual selectors within rules
  - `stylesheet`: Root node for entire document
- Helper functions: `parse_css_file()`, `extract_css_selectors()`, `extract_css_properties()`, `find_css_node_by_selector()`
- Features: Minified/formatted CSS, complex selectors, declaration extraction, graceful fallback

#### Parser Registry Update (`grafty/parsers/__init__.py`)
- Added `HTMLParser`, `HTMLNode`, `CSSParser`, `CSSNode` exports
- Updated `PARSER_REGISTRY`:
  - `.html`, `.htm` → `HTMLParser`
  - `.css` → `CSSParser`
  - (Plus existing support for `.py`, `.md`, `.org`, `.clj`, `.js`, `.go`, `.rs`)
- New helper: `get_parser_for_file(file_path)` for automatic parser selection

**Tests** (`tests/test_html_parser.py`, `tests/test_css_parser.py`):
- 54 new tests (28 HTML + 26 CSS)
- Coverage: Node creation, element parsing, attributes, nesting, line tracking, file I/O, edge cases
- 100% test pass rate, 95%+ code coverage

**Backward Compatibility**:
- ✅ All 147 existing tests still pass
- ✅ No breaking changes to existing parsers
- ✅ New parsers purely additive
- ✅ Parser registry fully extensible

**Performance**:
- Linear time complexity O(n) for both parsers
- Dual representation (tree + flat list) for efficient queries
- Memory efficient with no external dependencies (cssutils optional)

**Examples**:
```python
from grafty.parsers import HTMLParser, CSSParser

# Parse HTML
parser = HTMLParser()
root, nodes = parser.parse('<div id="main" class="container">Hello</div>')
ids = [n.value for n in nodes if n.kind == "html_id"]  # ['main']
classes = [n.value for n in nodes if n.kind == "html_class"]  # ['container']

# Parse CSS
parser = CSSParser()
root, nodes = parser.parse('.container { display: flex; }')
rules = [n for n in nodes if n.kind == "css_rule"]
for rule in rules:
    print(rule.declarations)  # {'display': 'flex'}
```

**Total Test Results**: 201 tests passing (54 new + 147 existing)

**Sign-Off**: Phase 5.1 is complete and production-ready. All code is tested, documented, and ready for public use.

---

## [0.8.0] - 2026-02-21

### 🎯 Phase 4.3: Multi-Language Documentation Extraction

**Problem**: Code documentation (docstrings, JSDoc, Javadoc, doc comments) are critical for understanding code, but grafty had no way to extract or manipulate them independently. LLM agents need to read/update documentation without touching implementation.

**Solution**:
- Added documentation extraction across 5 languages
- New node types for language-specific documentation conventions
- Documentation nodes named after their parent (e.g., `py_docstring:hello` for function `hello`)
- Module-level docstrings use special name `__module__`

**Implementation**:

#### Python Docstrings (`py_docstring`)
- Extracts docstrings from functions, classes, methods, and modules
- Supports all Python docstring styles (single-line, multi-line, triple-quoted)
- Module docstrings named `py_docstring:__module__`

#### JavaScript/TypeScript JSDoc (`js_jsdoc`)
- Extracts `/** ... */` comments before functions, classes, methods
- Detects JSDoc by checking `prev_named_sibling` for `comment` nodes starting with `/**`
- Works with both JavaScript and TypeScript parsers

#### Go Documentation Comments (`go_doc`)
- Extracts `//` comment blocks before function/method/type declarations
- Walks backwards through consecutive `comment` siblings
- Follows Go convention of doc comments directly preceding declarations

#### Rust Documentation Comments (`rs_doc`)
- Extracts `///` and `//!` documentation comments
- Walks backwards through consecutive `line_comment` siblings
- Supports both outer (`///`) and inner (`//!`) doc comments

#### Clojure Docstrings (`clj_docstring`)
- Extracts string literals after function name in `defn`, `defmacro`, etc.
- Works with both tree-sitter-clojure and fallback regex parser
- Handles multi-line docstrings

**Node Naming Convention**:
```bash
# Docstrings named after their parent
grafty show "app.py:py_docstring:validate_email"  # Docstring of validate_email function
grafty show "lib.rs:rs_doc:parse_config"          # Doc comment of parse_config function
grafty show "main.py:py_docstring:__module__"     # Module-level docstring
```

**Tests** (`tests/test_docstrings.py`):
- 25 new tests covering all 5 languages
- Module-level, function-level, class-level, method-level documentation
- Edge cases: missing docstrings, malformed syntax, multi-line comments

**Examples**:
```bash
# Show only the docstring, not the implementation
grafty show "validators.py:py_docstring:validate_email"

# Update JSDoc without touching code
grafty replace "api.ts:js_jsdoc:handleRequest" \
  --text "/**\n * Handles HTTP requests with rate limiting.\n * @param req - Request object\n */" \
  --apply

# Search for all documented functions
grafty search "*" --kind "py_docstring" --json
```

---

### 🚀 Insert Command Implementation

**Problem**: `grafty insert` was stubbed as "Phase 5+ future" but users needed it for programmatic code generation.

**Solution**: Fully implemented `grafty insert` with 5 insertion modes:

**Modes**:
- `--line N` — Insert at specific line number
- `--before <selector>` — Insert before a structural node
- `--after <selector>` — Insert after a structural node  
- `--inside-start <selector>` — Insert at start of node content
- `--inside-end <selector>` — Insert at end of node content

**Performance Optimization**:
- When selector contains a file path, indexes only that file (not entire directory)
- Uses new `_extract_file_from_selector()` helper to avoid scanning home directory
- Dramatically faster for single-file operations

**Tests** (`tests/test_insert.py`):
- 10 comprehensive tests covering all 5 modes
- Edge cases: empty files, whitespace handling, boundary conditions

**Examples**:
```bash
# Insert at line 42
grafty insert "src/app.py" --line 42 --text "# TODO: refactor" --apply

# Insert method at end of class
grafty insert "src/models.py:py_class:User" --inside-end \
  --text "    def validate(self):\n        pass" --apply

# Insert import before first function
grafty insert "src/utils.py:py_function:first_func" --before \
  --text "import logging" --apply
```

---

### 📦 New Language Parsers: Bash, Java, TypeScript

**Problem**: grafty supported 7 languages but missing common ones: shell scripts, Java, TypeScript.

**Solution**: Added three new tree-sitter-based parsers with full structural extraction.

#### Bash Parser (`grafty/parsers/bash_ts.py`)
- **Node types**: `bash_function` (shell functions), `bash_doc` (doc comments)
- **Extensions**: `.sh`, `.bash`
- Extracts function definitions and `#` comment blocks
- Tree-sitter grammar: `tree-sitter-bash`

#### Java Parser (`grafty/parsers/java_ts.py`)
- **Node types**: `java_class`, `java_interface`, `java_enum`, `java_method`, `java_constructor`, `java_doc` (Javadoc)
- **Extension**: `.java`
- Extracts classes, interfaces, enums, methods, constructors
- Javadoc detection: `/** ... */` comments before declarations
- Tree-sitter grammar: `tree-sitter-java`

#### TypeScript Parser (`grafty/parsers/typescript_ts.py`)
- **Node types**: `ts_function`, `ts_class`, `ts_method`, `ts_interface`, `ts_type`, `ts_enum`, `ts_doc` (TSDoc)
- **Extensions**: `.ts`, `.tsx`
- Extracts functions, classes, methods, interfaces, type aliases, enums
- TSDoc detection: `/** ... */` comments before declarations
- Tree-sitter grammar: `tree-sitter-typescript`

**Registry Updates** (`grafty/parsers/__init__.py`):
- Registered all three parsers with their extensions
- Added to `PARSER_REGISTRY` for automatic file type detection

**Examples**:
```bash
# Bash
grafty show "deploy.sh:bash_function:backup_db"

# Java  
grafty show "UserService.java:java_method:authenticate"
grafty show "UserService.java:java_doc:authenticate"  # Javadoc only

# TypeScript
grafty show "app.ts:ts_interface:Config"
grafty show "utils.ts:ts_doc:parseJson"  # TSDoc only
```

**Total Supported Languages**: 10 (Python, JavaScript, TypeScript, Go, Rust, Markdown, Org, Clojure, Bash, Java, HTML, CSS)

**Test Coverage**: 236 tests passing (25 docstring + 10 insert + 201 prior)

---

## [0.6.0] - 2026-02-08

### 🎯 Phase 4.2: VCS Integration (Git)

**Problem**: Users want to automatically commit and push patches after applying them. Manual `git add`/`git commit`/`git push` steps are repetitive and error-prone. Patch application should be atomic at the VCS level too.

**Solution**: 
- `GitConfig` for configuring VCS behavior (auto-commit, auto-push, commit message, dry-run)
- `GitRepo` class for managing Git operations (pre-flight checks, commit, push, rollback)
- Integration with `apply_patch` command: `--auto-commit`, `--auto-push`, `--commit-message`, `--allow-dirty`
- Pre-patch validation: Check repository is valid and working directory state
- Post-patch automation: Commit changed files and optionally push to remote
- Error recovery: On git failure, rolls back file changes automatically
- Dry-run support for testing without side effects

**Implementation** (`grafty/vcs/git_integration.py`):
- `GitConfig` dataclass for settings
- `GitRepo.prepare_for_patch()` validates repository and working directory
- `GitRepo.stage_and_commit()` stages and commits files atomically
- `GitRepo.push_to_remote()` pushes to remote (with optional branch)
- `GitRepo.rollback_to_backup()` restores from `.bak` files on failure
- Custom exceptions: `NotAGitRepo`, `DirtyRepo`, `CommitFailed`, `PushFailed`

**CLI Changes** (`grafty/cli.py` apply-patch command):
- `--auto-commit`: Enable automatic commit after patch application
- `--auto-push`: Enable automatic push to remote (requires `--auto-commit`)
- `--commit-message`: Custom commit message (default: "Apply grafty patch")
- `--allow-dirty`: Allow committing even with uncommitted changes in working directory

**Integration** (`grafty/multi_file_patch.py` apply_atomic method):
- New optional `git_config` parameter
- After successful patch write: Call `git_repo.stage_and_commit()` if configured
- After commit: Call `git_repo.push_to_remote()` if `auto_push` is enabled
- On any failure: Restore files from backups and return error status

**Tests** (`tests/test_vcs_integration.py`):
- 25+ tests covering all Git operations
- Mock git repositories for testing
- Test scenarios: clean repo, dirty repo, failed commits, push failures
- Dry-run mode validation
- Backup restoration on rollback

**Examples**:
```bash
# Apply patch with automatic commit
grafty apply-patch patch.txt --apply --auto-commit

# Apply patch, commit, and push
grafty apply-patch patch.txt --apply --auto-commit --auto-push

# Custom commit message
grafty apply-patch patch.txt --apply --auto-commit --commit-message "Fix issue #42"

# Allow dirty working directory
grafty apply-patch patch.txt --apply --auto-commit --allow-dirty
```

**Atomicity**: Patch application and Git operations are coordinated but not transactional. On Git failure, files are rolled back but the patch application is considered "in-progress". This is intentional to preserve file backup history.

**Non-breaking**: Existing `apply-patch` usage without git flags works exactly as before.

---

## [0.5.1] - 2026-02-08 (Hotfix)

### 🐛 Bug Fixes

**Bug #1: md_heading Replacement Appended Instead of Replaced**
- **Issue**: When replacing a Markdown heading that contains code blocks, the `end_line` calculation didn't include closing code fences (`\`\`\``). This caused replacements to stop prematurely, leaving old code in the file.
- **Root Cause**: The `_compute_heading_extent()` function checked if lines started with `#` without accounting for code fences. A comment like `# This is a bash comment` inside a code block was treated as a heading, causing extent to stop early.
- **Fix**: Updated `_compute_heading_extent()` to track code fence boundaries (`` ` `` and `~` delimiters) and ignore `#` lines that are inside code fences.
- **Impact**: Heading replacements now correctly include full code blocks. No more data corruption on edits.

**Bug #2: Markdown Parser Treated Code Comments as Headings**
- **Issue**: Bash/Python comments starting with `#` inside code fences were being extracted as `md_heading` nodes, causing "Ambiguous selector" errors.
- **Root Cause**: Tree-sitter parsing was correct, but there was no defensive filter in `_extract_headings()` to skip headings that are children of `fenced_code_block` nodes.
- **Fix**: Added `_is_inside_code_fence(node)` helper that traverses parent nodes to detect code fence context. Updated `_extract_headings()` to skip headings inside code fences.
- **Impact**: Code comments no longer pollute the heading index. Selectors are unambiguous.

**Tests Added**: 7 new regression tests in `tests/test_markdown_parser_bugs.py`:
- Heading replacement with single-line code blocks
- Heading replacement with multi-line code blocks  
- Heading replacement produces no duplication
- Code fence with bash comments not extracted as headings
- Code fence with markdown-like syntax (` # `) not extracted
- Nested code fences with comments handled correctly
- Mixed real headings and code comments have no ambiguity

All 117 existing tests remain passing. Total: 124 tests.

---

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
