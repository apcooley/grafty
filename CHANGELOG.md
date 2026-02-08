# Changelog

## [0.4.0] - 2026-02-08

### 🎯 Phase 3: Core Gaps Complete

#### 1. Line-Number Editing (3.1)
- **Support absolute line references** instead of just structural selectors
- **Format**: `grafty replace file.py:42 --text "..."` (single line)
- **Format**: `grafty replace file.py:42-50 --text "..."` (range)
- **Leverage**: Existing patch infrastructure for reliable mutations
- **Example**: Edit config section without knowing exact function name

#### 2. Improved Error Messages (3.2)
- **Show candidates** when fuzzy match fails (top 10 matches)
- **Explain failures** with context about available nodes
- **Suggest similar names** in candidates list
- **Better UX** for discovery and disambiguation
- **Example**: `No node found in src/main.py lines 42-50. Available: MyClass (1-20), helper (22-35)`

#### 3. Query Language (3.3)
- **Glob pattern matching** for node names
- **Format**: `grafty search "*validate*"` finds all containing "validate"
- **Supported wildcards**: `*pattern`, `pattern*`, `*pattern*`, `start*end`
- **Path globs**: `grafty search "*validate*" --path src/`
- **New command**: `grafty search` with pattern, kind, and path filters
- **Example**: Find all test functions with `grafty search "test_*"`

### 📊 Test Coverage
- **24 new tests** for Phase 3 features
- **78 total tests** passing (54 original + 24 new)
- **100% backward compatible** with v0.3.0

### 🔧 Quality Gates Met
✅ All tests passing
✅ Linting clean (ruff)
✅ No breaking changes
✅ Backward compatible workflows

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
