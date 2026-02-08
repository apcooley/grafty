# DESIGN.md — grafty Architecture Plan

## 1. Overall Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Layer (cli.py)                   │
│  - Argument parsing, subcommand dispatch                │
│  - User-facing error messages and output formatting    │
└────────────┬──────────────────────────────────────────┘
             │
             ├─→ IndexCommand → Index.run()
             ├─→ ShowCommand → Selector.resolve() → show_bounded()
             ├─→ ReplaceCommand → Patcher.replace()
             ├─→ InsertCommand → Patcher.insert()
             ├─→ DeleteCommand → Patcher.delete()
             └─→ CheckCommand → Patcher.validate_patch()
                   │
┌────────────┴──────────────────────────────────────────┐
│             Indexer & Selector Layer                   │
│  - index.py: File discovery, parse dispatch            │
│  - selectors.py: Resolution, ID generation, tree walk  │
└────────────┬──────────────────────────────────────────┘
             │
             ├─→ Parser Strategy:
             │    ├─ Python: Tree-sitter (ts-python)
             │    ├─ Markdown: Tree-sitter (ts-markdown)
             │    ├─ Clojure/ClojureScript: Tree-sitter first, fallback scanner
             │    └─ Org-mode: Tree-sitter if stable, else star-based parser
             │
┌────────────┴──────────────────────────────────────────┐
│             Parser Layer (parsers/)                    │
│  - python_ts.py: Tree-sitter Python indexing          │
│  - markdown_ts.py: Tree-sitter Markdown sections       │
│  - clojure_ts.py: Tree-sitter Clojure forms           │
│  - clojure_fallback.py: Balanced-paren fallback       │
│  - org.py: Star-based outline parser + fallback       │
└────────────┬──────────────────────────────────────────┘
             │
┌────────────┴──────────────────────────────────────────┐
│             Patch & File Layer (patch.py)              │
│  - Unified diff generation (via difflib)               │
│  - Atomic writes (temp + rename)                       │
│  - Backup + mtime/hash guards                          │
│  - Git integration (optional: git apply --check)       │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Node & Selector Data Model

### Node Structure
```python
@dataclass
class Node:
    id: str                          # stable hash(path, kind, name, start_line, sig)
    kind: str                        # "md_heading", "py_function", "clj_defn", etc.
    name: str                        # heading text, function name, etc.
    path: str                        # file path (relative or absolute)
    start_line: int                  # 1-indexed
    end_line: int                    # 1-indexed, inclusive
    start_byte: Optional[int]        # byte offset for precise patching
    end_byte: Optional[int]
    parent_id: Optional[str]         # for tree structure
    children_ids: List[str]          # direct children
    
    # Extra metadata
    heading_level: Optional[int]     # Markdown/Org
    qualname: Optional[str]          # Python "Class.method"
    namespace: Optional[str]         # Clojure ns
    signature: Optional[str]         # Python/Clojure for disambiguation
    is_method: Optional[bool]        # Python
    docstring: Optional[str]         # first N chars if available
```

### Selector Types
1. **By ID**: `node_id` (stable if file unchanged)
2. **By Path + Kind + Name**: `("path/to/file.py", "py_function", "my_func")`
3. **Fuzzy Name Search**: User supplies partial name; tool returns candidates with full qualnames for disambiguation

---

## 3. Tree-Sitter Grammar Evaluation Plan

### Python
- **Grammar**: tree-sitter-python (mature, widely tested)
- **Extract**: modules, classes, functions, methods, async variants
- **Validation**: Compare byte ranges with stdlib `ast.parse()` on sample files
- **Fallback**: None (Python grammar is reliable)

### Markdown
- **Grammar**: tree-sitter-markdown (covers ATX + Setext headings)
- **Extract**: heading → next-same-or-higher-level heading = section extent
- **Validation**: Test ATX headings (###), Setext underlines, nested lists
- **Fallback**: Regex-based if Tree-sitter fails (heading pattern: `^#+` or underline)

### Org-mode
- **Grammar**: tree-sitter-org (if available in Python bindings)
- **Extract**: headings, subtrees (stars = level)
- **Validation**: Test star counts, property drawer nesting
- **Fallback**: Star-based outline parser (match `^\*+\s+` lines, compute extent by level)

### Clojure / ClojureScript
- **Grammar**: tree-sitter-clojure (covers forms, defs, namespaces)
- **Extract**: ns forms, defn, defmacro, defmulti, etc.; capture full form extent
- **Validation**: Test balanced parens, multi-form bodies
- **Fallback**: Balanced-paren scanner (count parens, handle strings/comments carefully)

---

## 4. Patch Strategy & Newline Handling

### Byte vs. Line Offsets
- **Internal representation**: byte offsets (precise, unambiguous)
- **Human-facing**: line + column ranges (easier to read)
- **Conversions**: Pre-compute line→byte and byte→line mappings on load

### Newline Handling
- **Normalize on load**: Convert CRLF → LF internally
- **Preserve on write**: Detect original file ending; restore (LF vs CRLF)
- **Diff output**: Use LF consistently in unified diffs

### Patch Generation
- Apply change (replace/insert/delete) to working buffer
- Generate unified diff via `difflib.unified_diff()`
- Modes:
  1. **Emit patch only** (--patch-out FILE)
  2. **Dry-run** (show patch, don't write)
  3. **Apply** (write to file after mtime/hash check)

### Git Integration
- If `.git/` exists: `git apply --check <patch>` before commit
- If not a repo: skip (not required)
- On error: report cleanly, suggest `--force`

---

## 5. Error Handling & UX

### Validation Before Mutation
1. **File drift detection**:
   - Capture mtime + content hash on index
   - Before write, recompute hash; fail if mismatch (unless --force)
2. **Selector resolution**:
   - Exact match: proceed
   - Ambiguous (multiple matches): list candidates with qualnames
   - No match: suggest similar names (fuzzy)
3. **Patch applicability**:
   - Run `git apply --check` (if git available)
   - Fail gracefully with clear error

### UX Principles
- **Always show patches in dry-run mode** (so user sees exactly what will happen)
- **Never guess silently** (ambiguous selectors → list options + exit)
- **Backups are opt-in** (--backup flag creates .bak)
- **Clear error messages** (path, line number, what went wrong)

---

## 6. CLI Design

### Commands
```
grafty index [paths...] [--json]
  # Index one or more files; output JSON node list

grafty show <selector> [--max-lines N] [--max-chars N] [--json]
  # Resolve selector, show bounded snippet

grafty replace <selector> (--text STR | --file FILE)
    [--patch-out FILE] [--apply] [--dry-run]
  # Replace node content

grafty insert (--line N | <selector> --before|--after|--inside-start|--inside-end)
    (--text STR | --file FILE)
    [--patch-out FILE] [--apply] [--dry-run]
  # Insert at line or relative to node

grafty delete <selector>
    [--patch-out FILE] [--apply] [--dry-run]
  # Delete node (replace with empty string)

grafty check <patch.diff>
  # Validate patch applicability (dry-run git apply)
```

### Global Flags
- `--repo-root PATH`: Root directory for indexing/patching
- `--force`: Skip mtime/hash guards
- `--backup`: Create .bak files before mutation

### Selector Syntax
- **By ID**: `--selector <id>`
- **By Path + Kind + Name**: `--selector "path/file.py:py_function:my_func"`
- **Positional (shorthand)**: `grafty show "path/file.py:py_function:my_func"`

---

## 7. Implementation Roadmap

### Phase 1: Core Infrastructure
- [ ] Project layout & dependencies (tree-sitter, pytest)
- [ ] Base Node & Selector dataclasses
- [ ] Unified diff + atomic file write utilities (patch.py)

### Phase 2: Parsers
- [ ] Python Tree-sitter parser + tests
- [ ] Markdown Tree-sitter parser + tests
- [ ] Org-mode star-based parser + tests
- [ ] Clojure Tree-sitter + fallback scanner + tests

### Phase 3: Indexing & Selection
- [ ] Index.run() — multi-file indexing
- [ ] Selector.resolve() — all resolution strategies
- [ ] Node tree building (parent/child links)

### Phase 4: Mutations
- [ ] Patcher.replace(), insert(), delete()
- [ ] Dry-run + patch-out modes
- [ ] Atomic writes with backup support

### Phase 5: CLI & Git Integration
- [ ] CLI command dispatch (click or argparse)
- [ ] Output formatting (JSON, human-readable)
- [ ] Git integration (git apply --check)

### Phase 6: Tests & Docs
- [ ] Full test suite (pytest)
- [ ] README with examples
- [ ] Known limitations per language

---

## 8. Known Limitations & Tradeoffs

| Language | Limitation | Rationale |
|----------|-----------|-----------|
| **Python** | Async context not fully decoratable | ts-python captures form extent; edge case |
| **Markdown** | Nested code blocks may confuse heading extent | Fall back to next ATX heading |
| **Org-mode** | Drawer/comment nesting not fully parsed | Star-based parser simplicity vs precision |
| **Clojure** | Metadata comments above defs | Fallback scanner handles parens; user disambiguates if needed |

---

## 9. Success Criteria

✅ **Parsing**: Index returns accurate nodes for all 5 filetypes  
✅ **Tree-Sitter**: Used where viable; rejected with test evidence where not  
✅ **Patches**: All edits produce valid unified diffs  
✅ **Token Efficiency**: `show` output bounded by default; no full-file emission  
✅ **Tests**: pytest suite passes; README examples work verbatim  
✅ **Safety**: Atomic writes, backup support, mtime/hash guards  

---

## Next Steps

1. Set up project skeleton
2. Implement parsers (start with Python, most reliable)
3. Build indexing & selector resolution
4. Add patch generation & mutation operations
5. Write tests iteratively
6. Document & ship

