# Phase 2: Multi-Language Support (JavaScript, Go, Rust)

## Goal
Extend grafty to support JavaScript, Go, and Rust parsing, using grafty itself for surgical edits where possible.

## Constraints & Approach
- **Tree-sitter first**: Use tree-sitter grammars for all three languages
- **Consistent node kinds**: Match existing patterns (e.g., `py_function`, `js_function`, `go_function`)
- **Backward compatible**: All Phase 1 features work unchanged
- **Self-editing**: Use grafty to edit grafty's own code during development (preambles, registry updates)
- **Test-driven**: Add tests before/alongside implementation

## Language Roadmap

### JavaScript (TypeScript-compatible)
**Nodes to extract:**
- `js_function` — Function declarations (arrow, regular, async)
- `js_class` — Class declarations
- `js_method` — Class methods
- `js_export` — Export statements (named, default)
- `js_import` — Import statements

**Grammar:** tree-sitter-javascript (covers JS + JSX + TypeScript)

**Example:**
```javascript
// js_function:asyncFetch
async function asyncFetch(url) {
  const response = await fetch(url);
  return response.json();
}

// js_class:DataProcessor
class DataProcessor {
  // js_method:parse
  parse(data) {
    return JSON.parse(data);
  }
}

// js_export:processData (default)
export default function processData(input) {
  return input.trim();
}
```

### Go
**Nodes to extract:**
- `go_function` — Function declarations
- `go_type` — Type declarations (struct, interface, type alias)
- `go_method` — Method declarations
- `go_import` — Import statements
- `go_package` — Package declaration

**Grammar:** tree-sitter-go

**Example:**
```go
// go_package:main (placeholder, line 1)
package main

// go_function:main
func main() {
  fmt.Println("Hello")
}

// go_type:DataProcessor (struct)
type DataProcessor struct {
  Name string
  ID   int
}

// go_method:Process
func (dp *DataProcessor) Process(data string) string {
  return strings.TrimSpace(data)
}
```

### Rust
**Nodes to extract:**
- `rs_function` — Function declarations
- `rs_struct` — Struct declarations
- `rs_impl` — Implementation blocks
- `rs_method` — Methods (within impl blocks)
- `rs_trait` — Trait declarations
- `rs_macro` — Macro definitions

**Grammar:** tree-sitter-rust

**Example:**
```rust
// rs_struct:DataProcessor
struct DataProcessor {
    name: String,
    id: u32,
}

// rs_impl:DataProcessor
impl DataProcessor {
    // rs_method:new
    fn new(name: String, id: u32) -> Self {
        DataProcessor { name, id }
    }

    // rs_method:process
    fn process(&self, data: &str) -> String {
        data.trim().to_string()
    }
}

// rs_trait:Processable
pub trait Processable {
    fn process(&self, data: &str) -> String;
}
```

## Implementation Plan

### Phase 2a: Setup & JavaScript
1. ✅ Add tree-sitter grammar packages to `pyproject.toml`
2. ✅ Create `grafty/parsers/javascript_ts.py` (TypeScript-compatible)
3. ✅ Add unit tests: `tests/test_javascript_parser.py`
4. ✅ Update parser registry in `indexer.py`
5. ✅ Use grafty to surgically edit:
   - `indexer.py` — Add `.js`/`.ts`/`.jsx`/`.tsx` file support
   - `README.md` — Preamble: Update supported file types
   - `USAGE.md` — Preamble: Add JS examples
6. ✅ Test with real React/TypeScript files

### Phase 2b: Go
1. ✅ Create `grafty/parsers/go_ts.py`
2. ✅ Add unit tests: `tests/test_go_parser.py`
3. ✅ Update `indexer.py` via grafty (`.go` file support)
4. ✅ Document Go support in README (preamble edit)
5. ✅ Test with real Go codebases

### Phase 2c: Rust
1. ✅ Create `grafty/parsers/rust_ts.py`
2. ✅ Add unit tests: `tests/test_rust_parser.py`
3. ✅ Update `indexer.py` via grafty
4. ✅ Document Rust support
5. ✅ Test with real Rust projects

### Phase 2d: Integration & Polish
1. ✅ Update `ARCHITECTURE_DECISIONS.md` with new language reasoning
2. ✅ Create comprehensive integration tests
3. ✅ Bump version: 0.2.0 → 0.3.0
4. ✅ Ship: Send summary to Discord

## Meta: Using Grafty to Build Grafty

This is the clever twist: as we add these parsers, we'll use grafty itself to make surgical edits where it's elegant.

**Example edits:**
```bash
# Update the SUPPORTED_FORMATS list in README
grafty replace "README.md:md_heading_preamble:Supported File Types" \
  --text "| **JavaScript** (.js, .ts, .jsx, .tsx) | ..." --apply

# Add Go to the indexer registry
grafty insert "grafty/indexer.py:py_class:FileIndexer" \
  --inside-end --text "'.go': GoPythonParser()," --apply

# Update the changelog preamble
grafty replace "CHANGELOG.md:md_heading_preamble:0.3.0" \
  --text "## [0.3.0] - 2026-02-08\n\nJavaScript, Go, Rust support..." --apply
```

## Success Criteria

- ✅ All three parsers implemented and tested
- ✅ 20+ new unit tests (all passing)
- ✅ Real-world test files for each language
- ✅ Backward compatible (0% regressions)
- ✅ Used grafty's own features to edit grafty code
- ✅ v0.3.0 shipped
- ✅ Zero breaking changes

## Estimated Timeline

- **Phase 2a (JS)**: 1-2 hours (parser + tests)
- **Phase 2b (Go)**: 45 min (similar pattern)
- **Phase 2c (Rust)**: 1 hour (slightly more complex)
- **Phase 2d (Polish)**: 30 min

**Total: ~4 hours** (plus documentation + shipping)

## Open Questions

1. Should we support JSX/TSX as separate node kinds, or roll into `js_function`/`js_class`?
   - **Decision**: Roll into `js_function`/`js_class` (simpler for now, can split later)

2. For Go, how do we handle package main vs. libraries?
   - **Decision**: Treat all as regular nodes, `go_package` is just a marker node

3. For Rust, how deep into impl blocks do we go?
   - **Decision**: `rs_impl` is the block, `rs_method` is children within it (like Python methods in classes)

## Testing Strategy

For each language:
1. **Unit tests**: Parsing a sample file with 3-5 nodes
2. **Integration tests**: Real-world code from popular projects
3. **Edge cases**: Async functions (JS), generics (Rust), error handling (Go)
4. **Selector fuzzy matching**: Ensure names resolve correctly

## References

- Tree-sitter JavaScript: https://github.com/tree-sitter/tree-sitter-javascript
- Tree-sitter Go: https://github.com/tree-sitter/tree-sitter-go
- Tree-sitter Rust: https://github.com/tree-sitter/tree-sitter-rust

---

**Let's ship language support! 🚀**
