# Changelog

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
