You are an autonomous coding agent. Your job is to PLAN and BUILD a CLI tool for token-optimized refactoring and editing of large text/code files. The tool must support Markdown (.md), Org-mode (.org), Python (.py), Clojure (.clj), and ClojureScript (.cljs). Its purpose is to let LLM agents operate on long files by referencing stable "selectors" (headers/defs) instead of emitting whole files.

Guiding principle
- Prefer **structural parsing with Tree-sitter** wherever grammars are reliable.
- Validate grammar quality empirically (tests + fixtures).
- Fall back to simpler, well-documented parsers where Tree-sitter is weak or ambiguous.
- All edits are **range-based**, **patch-first**, and **token-bounded**.

────────────────────────────────────────────────────────
1) Core operations (must implement)

A. INDEX
- Discover all structural units ("nodes"):
  - Markdown: headings and sub-headings
  - Org-mode: headings and subtrees
  - Python: modules, classes, functions, methods
  - Clojure / ClojureScript: ns forms, defs, defns, defmacros, defmulti, defmethod
- Output: JSON with node metadata and line numbers.

B. REPLACE
- Replace the full text span of a selected node with:
  - a literal string, OR
  - the contents of another file.

C. INSERT
- Insert a literal string or file contents at:
  - an absolute line number, OR
  - relative to a selected node:
    --before
    --after
    --inside-start
    --inside-end

D. DELETE
- Delete a selected node (equivalent to replace with empty string).

────────────────────────────────────────────────────────
2) Token-optimization requirements (hard)

- Never emit full file contents unless explicitly requested.
- Provide bounded output modes:
  - metadata only
  - preview snippet with max lines / max chars
- All listing and resolution commands must support compact JSON output.
- Output must be deterministic:
  - stable ordering
  - stable IDs
  - normalized newlines

────────────────────────────────────────────────────────
3) Patch-first workflow (hard)

- Every mutating operation must be able to emit a unified diff patch.
- Modes:
  - emit patch only
  - apply patch to working tree
  - check applicability only (no mutation)
- Optional Git integration:
  - if in a git repo, support invoking:
    git apply --check
    git apply
  - Git must not be required to run the tool.

────────────────────────────────────────────────────────
4) Safety & correctness (hard)

- Atomic writes (temp file + rename).
- Optional backups (.bak).
- Handle LF/CRLF robustly.
- Detect file drift between index and edit:
  - hash or mtime guard
  - fail with clear error unless --force.
- Every mutating command supports --dry-run.

────────────────────────────────────────────────────────
5) Parsing strategy (must implement + justify)

You MUST use Tree-sitter where grammars are reliable and test them empirically.

A. Python
- Use Tree-sitter Python grammar as primary parser.
- Extract byte ranges and line ranges for:
  - classes
  - functions
  - methods
- Validate against stdlib ast for correctness where useful.

B. Markdown
- Use Tree-sitter Markdown grammar.
- Extract heading nodes and levels.
- Compute section extent as:
  heading → next heading of same or higher level.
- Explicitly test ATX and Setext headings.

C. Org-mode
- Evaluate Tree-sitter org grammar if available.
- If grammar is insufficient or unstable:
  - implement a correct-enough star-based outline parser.
- Clearly document limitations.

D. Clojure / ClojureScript
- Attempt Tree-sitter clojure grammar first.
- Write tests to validate:
  - def / defn / ns detection
  - correct extent for multi-form bodies
- If grammar fails:
  - fall back to a reader-like or balanced-paren scanner.
- Document decision with test evidence.

For all parsers:
- Capture both line numbers and byte offsets where possible.
- Prefer byte offsets internally for patching.

────────────────────────────────────────────────────────
6) Selector model (hard)

Every discovered unit is a "node" with:
- id (stable if file content unchanged; e.g. hash(path, kind, name, start_line, signature))
- kind (md_heading, org_heading, py_function, clj_defn, etc.)
- name
- path
- start_line, end_line
- start_byte, end_byte (if available)
- parent_id
- children_ids
- extra metadata:
  - heading level
  - Python qualname
  - Clojure namespace (if detectable)

Selectors must support:
- direct id
- (path, kind, name)
- fuzzy name search with explicit disambiguation output
- never guess silently

────────────────────────────────────────────────────────
7) CLI design (must implement)

Commands:
- grafty index [paths...] [--json]
- grafty show <selector> [--max-lines N] [--max-chars N] [--json]
- grafty replace <selector> (--text STR | --file FILE)
    [--patch-out FILE] [--apply] [--dry-run]
- grafty insert
    (--line N | <selector> --before|--after|--inside-start|--inside-end)
    (--text STR | --file FILE)
    [--patch-out FILE] [--apply] [--dry-run]
- grafty delete <selector>
    [--patch-out FILE] [--apply] [--dry-run]
- grafty check <patch.diff>

Global flags:
- --repo-root PATH
- --force
- --backup

────────────────────────────────────────────────────────
8) Implementation constraints

- Language: Python 3.11+
- Tree-sitter bindings via Python.
- Strong typing (type hints throughout).
- Minimal dependencies; justify any non-stdlib additions.
- Project layout:
  grafty/
    cli.py
    selectors.py
    patch.py
    parsers/
      python_ts.py
      markdown_ts.py
      clojure_ts.py
      clojure_fallback.py
      org.py
    tests/
    README.md

────────────────────────────────────────────────────────
9) Tests (hard)

Using pytest, cover:
- indexing correctness per filetype
- selector resolution and ambiguity handling
- replace/insert/delete correctness
- patch generation and check mode
- ID stability when file unchanged
- Tree-sitter vs fallback behavior for clj/cljs

────────────────────────────────────────────────────────
10) Documentation (hard)

README must include:
- philosophy: "token-optimized structural editing"
- architecture overview
- Tree-sitter usage rationale
- fallback strategy for clj/org
- CLI examples:
  1) index → show bounded snippet → replace → patch → apply
  2) insert markdown/org subsection
  3) delete and replace a Python function
- known limitations per language

────────────────────────────────────────────────────────
Process requirements

1) Start with a design plan:
   - text-based architecture diagram
   - node/selector data model
   - Tree-sitter grammar evaluation plan
   - patch strategy and newline handling
   - error handling and UX decisions

2) Implement iteratively:
   - indexing
   - selector resolution + show
   - patch generation + dry-run
   - replace/insert/delete
   - tests
   - documentation

3) Prefer deterministic, token-efficient output at every step.
4) If requirements conflict, explain tradeoffs and choose correctness.

Success criteria
- Indexing returns accurate nodes for md/org/py/clj/cljs.
- Tree-sitter is used where viable and rejected where not, with evidence.
- All edits produce valid unified diffs.
- show output is always bounded.
- Tests pass; README examples work verbatim.
