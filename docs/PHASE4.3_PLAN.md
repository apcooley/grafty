# Phase 4.3: Comment & Docstring Extraction

## Goal
Treat docstrings and documentation comments as first-class editable nodes, so users can view and edit documentation separately from code.

## New Node Kinds

| Kind | Language | What It Captures | Tree-sitter Pattern |
|------|----------|-----------------|-------------------|
| `py_docstring` | Python | `"""..."""` as first statement in function/class/method body | `block > expression_statement:first-child > string` |
| `js_jsdoc` | JS/TS | `/** ... */` comment preceding a function/class | `comment` node (starting with `/**`) immediately before declaration |
| `go_doc` | Go | `//` comment block preceding a function/type | Consecutive `comment` nodes immediately before declaration |
| `rs_doc` | Rust | `///` or `//!` doc comments | `line_comment` nodes starting with `///` or `//!` before declaration |
| `clj_docstring` | Clojure | String after name in `defn`/`def` | String literal as 3rd element in def form (after name, before args) |

## Design Decisions

### Docstring ↔ Parent Relationship
Each docstring node is **linked to its parent** function/class via `parent_id`. The docstring's line range is a subset of the parent's range. This means:
- `grafty show "file.py:py_function:hello"` → shows full function including docstring (existing behavior, unchanged)
- `grafty show "file.py:py_docstring:hello"` → shows only the docstring
- `grafty replace "file.py:py_docstring:hello" --text '"""New doc."""'` → replaces just the docstring

### Naming Convention
Docstring nodes inherit the **name of their parent** function/class. So `py_docstring:hello` means "the docstring of the `hello` function." This is unambiguous because each function/class can have at most one docstring.

### Module-Level Docstrings
Module-level docstrings (first expression in a file) get the name `__module__`:
- `file.py:py_docstring:__module__`

### Comments vs Docstrings
- **Docstrings** are structured documentation tied to a specific definition → extracted as nodes
- **Inline comments** (`# ...` in Python, `// ...` in JS) are NOT extracted — too granular, too numerous
- **JSDoc/GoDoc/RustDoc** comments are extracted because they're structured documentation attached to declarations

## Implementation Plan

### Step 1: Python Docstrings (~2 hours)
**File:** `grafty/parsers/python_ts.py`

Modify `_extract_function()` and `_extract_class()` to also emit a `py_docstring` node when the first statement in the body block is `expression_statement > string`.

```python
# After creating the function/class node, check for docstring:
for child in node.children:
    if child.type == "block":
        stmts = [c for c in child.children if c.type != "\n"]
        if stmts and stmts[0].type == "expression_statement":
            expr = stmts[0]
            for sub in expr.children:
                if sub.type == "string":
                    # This is a docstring — create py_docstring node
                    ...
        break
```

**Tests:** 8-10 tests
- Function docstring extraction
- Class docstring extraction  
- Method docstring extraction
- Module-level docstring
- No docstring → no node emitted
- Multi-line docstrings
- Docstring show/replace via selector

### Step 2: JavaScript JSDoc (~2 hours)
**File:** `grafty/parsers/javascript_ts.py`

After extracting a function/class node, look at the **previous sibling** in the AST. If it's a `comment` node whose text starts with `/**`, emit a `js_jsdoc` node.

```python
# Check previous sibling for JSDoc
prev = node.prev_named_sibling
if prev and prev.type == "comment":
    text = prev.text.decode("utf-8")
    if text.startswith("/**"):
        # This is JSDoc — create js_jsdoc node
        ...
```

**Tests:** 6-8 tests
- JSDoc before function
- JSDoc before class
- Regular `//` comment NOT extracted
- Multi-line JSDoc
- No JSDoc → no node

### Step 3: Go Doc Comments (~1.5 hours)
**File:** `grafty/parsers/go_ts.py`

Go doc comments are consecutive `//` comment lines immediately preceding a declaration. Walk backwards from the declaration to collect them.

**Tests:** 5-6 tests

### Step 4: Rust Doc Comments (~1.5 hours)
**File:** `grafty/parsers/rust_ts.py`

Rust uses `///` (outer doc) and `//!` (inner doc). Check previous siblings for `line_comment` nodes starting with `///`.

**Tests:** 5-6 tests

### Step 5: Clojure Docstrings (~1 hour)
**File:** `grafty/parsers/clojure_ts.py` and `grafty/parsers/clojure_fallback.py`

Clojure docstrings are the string literal between the name and the argument vector in `defn`/`def` forms:
```clojure
(defn hello
  "This is the docstring"
  [name]
  (str "Hello " name))
```

In the Tree-sitter AST, look for a `str_lit` node as the child after the symbol name. In the fallback parser, scan for a `"` after the name token.

**Tests:** 4-5 tests
- defn with docstring
- def with docstring
- defn without docstring → no node
- Multi-line Clojure docstring

### Step 6: Integration & CLI
- Verify `grafty index`, `grafty show`, `grafty replace`, `grafty insert`, `grafty delete` all work with docstring selectors
- No CLI changes needed — existing selector resolution handles new node kinds automatically
- Update `grafty search` to support `--kind py_docstring` etc.

## Test Count Estimate
~30-35 new tests, targeting 240+ total.

## Backward Compatibility
✅ Fully backward compatible:
- Existing selectors unchanged
- Existing nodes unchanged  
- New docstring nodes are purely additive
- `py_function:hello` still returns the full function (including docstring)

## Effort Estimate
~9 hours total across all 5 languages + tests.

## Out of Scope
- Docstring formatting/linting
- Extracting parameter docs from docstrings (e.g., `:param name:`)
- Comment extraction for inline `#` / `//` comments
- Org-mode/Markdown (already have heading preambles)
