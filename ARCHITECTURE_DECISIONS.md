# Architecture Decisions

## Package Management: uv Instead of pip

**Decision**: Use `uv` for all package management instead of pip.

**Rationale**:
1. **Speed** — uv is 10-100x faster than pip (written in Rust)
2. **Reliability** — Better dependency resolution, fewer conflicts
3. **Simplicity** — Zero configuration, automatic venv management
4. **Future-proof** — Emerging as Python's standard package manager
5. **Cleanliness** — No ~/.local/bin pollution for local development

**Implementation**:
- Dependencies defined in `pyproject.toml`
- `uv run` manages venv automatically (created in `.venv/`)
- No `pip install` or manual venv activation needed
- Tested with: `uv run pytest`, `uv run grafty`, `uv run ruff`

**Examples**:
```bash
uv run grafty index .          # Auto-venv, auto-deps
uv run pytest tests/           # Same pattern
uv run ruff check grafty/      # Linting via uv
```

---

## Entry Points: [project.scripts] for System Installation

**Decision**: Use `[project.scripts]` in `pyproject.toml` to create a system entry point at `~/.local/bin/grafty`.

**Why This Approach?**
- grafty is now a system tool (installed via `pip install -e .`)
- Users can run `grafty` from anywhere without boilerplate
- Standard Python convention for CLI tools
- Works seamlessly with PATH management
- Entry point created at `~/.local/bin/grafty` automatically

**Entry Points We Support**:
1. `grafty` — Primary (works from anywhere, PATH-based)
2. `uv run grafty` — Development (uses dev dependencies)
3. `uv run python3 -m grafty` — Python module (via `__main__.py`)
4. `python3 -c "from grafty import Indexer"` — Direct API import
5. `./bin/grafty` — Bash wrapper (development convenience)

**Installation Method**:
```bash
cd ~/source/grafty
python3 -m pip install -e .  # or: uv pip install -e .
# Creates ~/.local/bin/grafty automatically
```

**Why Not Just `uv run`?**
- `uv run` is better for development and testing
- System installation (`grafty` command) is better for users
- We do both: install for usage, use `uv run` for development

---

## Project Structure: Source + bin Separation

**Decision**: Keep source in `grafty/` package, CLI wrapper in `bin/`.

```
~/source/grafty/
├── bin/grafty                 # Shell wrapper
├── grafty/                    # Python package
│   ├── __main__.py
│   ├── cli.py
│   ├── parsers/
│   └── ...
├── tests/
└── pyproject.toml
```

**Advantages**:
- Clear separation of concerns
- `grafty/` is the distributable package
- `bin/` is the local development convenience layer
- `.venv/` stays isolated in project root

---

## Virtual Environment: Auto-Managed by uv

**Decision**: Let uv manage the venv (created in `.venv/`).

**Why Auto-Management?**
- No manual `python3 -m venv` or `source venv/bin/activate`
- `uv run` handles venv lifecycle automatically
- Reproducible: `.venv` created same way every time
- Transparent: Users see clear commands (`uv run grafty`)

**.venv Lifecycle**:
1. First `uv run grafty` → Creates `.venv`, installs dependencies
2. Subsequent runs → Uses cached `.venv`
3. Dependency change → `uv run` re-syncs `.venv`
4. Cleanup → `rm -rf .venv` (will be recreated next run)

---

## Access Pattern: Prefer Explicit Over Magic

**Decision**: All commands explicitly use `uv run` or `./bin/grafty`, no implicit PATH magic.

**Why?**
- Clarity: Users know grafty is running with dependencies from `.venv/`
- Predictability: No hidden system PATH interference
- Security: No ~/.local/bin symlink surprises
- Transparency: Commands are reproducible and auditable

**Exception**:
Users can optionally add `~/source/grafty/bin` to PATH:
```bash
export PATH="$PATH:~/source/grafty/bin"
grafty index .  # Now works without uv run
```

This is optional, not default.

---

## Testing: Via uv in Development

**Decision**: Run tests with `uv run pytest`, not bare `pytest`.

**Consistency**:
- Development uses `uv run` for isolated dependencies
- Ensures tests run against `.venv/` dependencies
- Same environment as `uv run grafty` development workflow
- Separate from system `grafty` installation

```bash
cd ~/source/grafty
uv run pytest tests/           # Full suite
uv run pytest tests/ -v        # Verbose
uv run pytest tests/test_patch.py  # Single file
```

## Dual Workflow: System Tool + Development Environment

grafty supports two usage patterns:

**Pattern 1: System Usage (End Users)**
```bash
grafty index src/
grafty show "file.py:py_function:my_func"
# grafty is in ~/.local/bin, installed system-wide
```

**Pattern 2: Development (Contributors)**
```bash
cd ~/source/grafty
uv sync
uv run grafty index .
uv run pytest tests/
uv run ruff check .
# Isolated development environment, doesn't affect system
```

Both patterns work simultaneously and don't interfere with each other.

---

## CI/CD Strategy (Future)

If/when grafty is used in CI:

```yaml
# GitHub Actions example
- name: Lint
  run: uv run ruff check grafty/

- name: Test
  run: uv run pytest tests/

- name: Demo
  run: uv run grafty index .
```

No special venv setup or pip invocation needed.

---

## Migration Path to PyPI

If grafty becomes a public tool:

1. **Keep** `pyproject.toml` (already structured for distribution)
2. **Add** back `[project.scripts]` for end-users
3. **Keep** `uv` for development
4. **Publish** via `uv build && twine upload` (or `uv publish`)

The transition is frictionless — all existing development workflows continue.

---

## Line Numbers Matter Alongside Structural Selectors (Phase 3.1)

**Decision**: Support line-number selectors (`file.py:42`, `file.py:42-50`) alongside structural selectors.

**Rationale**:
1. **Complementary, not competing** — Line numbers and structural selectors solve different problems
   - Structural: "Edit this function" (stable, semantic)
   - Line-based: "Edit lines 42-50" (precise, diff-centric)

2. **Real workflow need** — ~20% of edits are line-based (from diffs, stack traces, "quick fixes")

3. **Consistent interface** — Same mutation operations (replace, show, delete) work with any selector format

4. **Safe fallback** — When structural selectors are imprecise or unknown, lines provide accurate targeting

5. **Integration** — Works with existing patch/diff infrastructure (no new code paths needed)

**Implementation**:
- `LineNumberSelector.parse()` distinguishes line selectors (single colon) from path:kind:name format
- `_resolve_by_line_numbers()` finds nodes overlapping the line range
- CLI accepts selectors uniformly: resolve as line → try path:kind:name → try fuzzy

**Why not just line numbers?** Structural selectors remain superior for long-term stability (lines shift; function names endure).

**Why not just structural?** Line numbers solve the "urgent edit" problem where structural precision is overkill.

---

## Query Language Design: Glob Patterns Over Regex (Phase 3.3)

**Decision**: Use shell-style glob patterns (`fnmatch`) for the search command instead of regex.

**Rationale**:
1. **Approachability** — Glob patterns are familiar to every shell user
   - `test_*` is intuitive (starts with "test_")
   - `*validate*` is obvious (contains "validate")
   - `*.spec.ts` works for file patterns

2. **Safety** — Regex is powerful but scary for casual users
   - Glob patterns are simple, hard to misuse
   - Can always add `--regex` if advanced filtering is needed later

3. **Consistency** — Grafty already uses glob patterns for path filters
   - `--path "src/"` uses glob-style matching
   - Extending to node names is natural extension

4. **Implementation** — Python's `fnmatch` module is battle-tested
   - No regex compilation overhead
   - Straightforward semantics

5. **Composability** — Glob patterns stack naturally
   - `search "*test*" --path "tests/" --kind "py_function"`
   - Each filter is independent and easy to understand

**Alternative considered**: Regex patterns
- **Pro**: More powerful, allows complex matching
- **Con**: Higher cognitive load, regex syntax errors, overkill for 90% of searches

**Future expansion**: Could add `--regex` flag later if users need regex patterns, without breaking glob patterns.

---

## Improved Error Messages with Context (Phase 3.2)

**Decision**: When selectors fail, show candidates and available nodes with context.

**Rationale**:
1. **Discoverability** — Users can learn available nodes from error messages
2. **Debugging** — Seeing "Available: MyClass (1-20), helper (22-35)" helps disambiguate
3. **UX** — Interactive feel without needing an interactive mode
4. **Low cost** — Requires only string formatting and sorting, no new data structures

**Implementation**:
- `_resolve_fuzzy()` returns top 10 candidates (score-sorted)
- `_resolve_by_line_numbers()` shows available nodes in file when line range doesn't match
- Error messages include context: file, node types, line ranges

**Example**:
```
Error: No node found in src/main.py lines 42-50.
Available: MyClass (1-20), helper (22-35), process (35-70)
```

---

## Atomic Multi-File Patching Strategy (Phase 4.1)

**Decision**: Use temporary files + atomic rename for multi-file atomicity, with backup-based rollback.

**Problem**: Coordinating mutations across multiple files safely. If file #1 succeeds but file #2 fails, how do we rollback file #1?

**Alternatives Considered**:
1. **In-place edits** — Fast but unsafe. File #1 modified; file #2 fails; file #1 corrupted.
2. **Database transactions** — Powerful but overkill for file system. Filesystem lacks ACID guarantees.
3. **Git worktree snapshots** — Requires git repo, heavyweight for small patches.
4. **Temp files + rename** ← **CHOSEN**: Simple, atomic at OS level, works offline.

**Our Approach** (Three Phases):
1. **Preparation Phase** (no I/O to actual files):
   - Create `Editor` for each file
   - Apply all mutations in-memory
   - If any mutation fails, stop (no writes yet)
   
2. **Write Phase** (atomic writes):
   - Create `.bak` backups (if requested)
   - Create temp files with modified content in same directory
   - **Atomically rename** temp → original (atomic OS operation)
   - If rename fails, .bak files still exist for manual recovery
   
3. **Cleanup Phase**:
   - Success: leave `.bak` files (user decides when to delete)
   - Failure: attempt rollback from `.bak` files

**Why Atomic Rename?**
- `os.replace()` is atomic on all platforms (Windows, Linux, macOS)
- Cannot be partially applied — succeeds completely or fails completely
- Much faster than copying (true rename on same filesystem)
- Works offline (doesn't require git, network, or database)

**Why Temp Files in Same Directory?**
- Guarantees same filesystem (rename atomic only on same filesystem)
- Works across mounted disks (on Linux: same `/dev`)
- Handles NFS, CIFS, cloud storage correctly

**Error Handling**:
- If any mutation prep fails → return error, no writes
- If temp file creation fails → cleanup temps, return error
- If rename fails → return error, `.bak` files still exist for recovery
- Overlap detection → warning (may be intentional, user decides)

**Example Scenario**:
```
Before:
  file1.py (10 lines)
  file2.py (10 lines)
  file3.py (10 lines) [INVALID LINE 100]

Step 1: Validate all — finds file3 error, stops ✓
Step 2: No temp files created ✓
Result: All files unchanged ✓

Before:
  file1.py, file2.py, file3.py

Step 1: Validate all — passes ✓
Step 2: Prep mutations in-memory — all succeed ✓
Step 3: Create temps, backups
        temp.abc123, file1.py.bak
        temp.def456, file2.py.bak
        temp.ghi789, file3.py.bak
Step 4: Rename temps → originals
        temp.abc123 → file1.py ✓
        temp.def456 → file2.py ✓
        rename fails on file3 ← System error (disk full, permissions)
        
Result:
  file1.py — MODIFIED ✓
  file2.py — MODIFIED ✓
  file3.py — ORIGINAL (rename failed)
  file*.bak — All exist for manual recovery
```

**Trade-offs**:
- **Benefit**: Simple, atomic, works offline, no external deps
- **Cost**: Requires disk space for temp + backup files
- **Mitigation**: Document cleanup; auto-delete old backups possible future feature

**Testing**:
- ✅ Single file success
- ✅ Multi-file success (5 files atomically)
- ✅ Validation failure (no writes)
- ✅ Partial success (file 1-2 succeed, 3 fails — but all had temps)
- ✅ Backup creation and recovery
- ✅ Unicode and CRLF handling
- ✅ Large files (1000+ lines)

---

## Summary

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| Package Manager | uv | Speed, reliability, auto-venv |
| Entry Points | No [project.scripts] | Cleaner for dev, explicit access |
| Venv | Auto-managed by uv | Zero manual setup |
| Primary Access | `uv run grafty` | Clear, reproducible, transparent |
| Tests | `uv run pytest` | Consistency with main commands |
| Future | PyPI-ready | Can distribute whenever needed |

All decisions optimize for **clarity, speed, and simplicity** in development, with a clear upgrade path to distribution.

---

## Markdown Parser: Code Fence Boundary Detection (v0.5.1+)

**Decision**: Markdown heading extents must properly account for code fences, and headings inside code fences should not be extracted.

**Problem (v0.5.0)**:
When computing the extent of a Markdown heading section, the parser looked for the next line starting with `#` to determine where the section ends. However:
- Comments like `# This is a bash comment` inside code blocks (backtick or tilde-fenced) matched the heading pattern
- This caused section extents to stop prematurely, leaving code blocks behind after replacement
- Code comments were incorrectly extracted as heading nodes, causing selector ambiguity

**Solution**:
1. **Track Code Fence Context**: The `_compute_heading_extent()` method now maintains state for open/closed code fences using backticks (`` ` ``) and tildes (`~`).
2. **Skip Lines Inside Fences**: When inside a fence, lines starting with `#` are ignored—they can't be headings.
3. **Defensive Extraction**: Added `_is_inside_code_fence(node)` helper that checks parent nodes in the Tree-sitter AST for `fenced_code_block` context. The `_extract_headings()` method uses this to skip headings that are structurally inside code blocks.

**Implementation Details**:

```python
def _compute_heading_extent(...) -> int:
    """Compute end line, tracking code fence state."""
    lines = content.splitlines()
    in_code_fence = False
    fence_delimiter = None
    
    for i in range(start_line, len(lines)):
        line = lines[i]
        stripped = line.strip()
        
        # Toggle fence state on fence markers
        if stripped.startswith("```") or stripped.startswith("~~~"):
            if not in_code_fence:
                in_code_fence = True
                fence_delimiter = stripped[0]
            elif stripped.startswith(fence_delimiter * 3):
                in_code_fence = False
        
        # Only check for headings if NOT in a fence
        if not in_code_fence and line.startswith("#"):
            # ... find next heading ...
```

**Defensive Layer**:
```python
def _is_inside_code_fence(node) -> bool:
    """Verify node is not structurally inside a code block."""
    current = node.parent
    while current:
        if current.type in ("fenced_code_block", "code_fence"):
            return True
        current = current.parent
    return False
```

**Trade-offs**:
- **Benefit**: Correct heading extents with code blocks; no spurious headings from comments; safe replacements
- **Cost**: Minimal (simple state tracking, one parent traversal per heading)
- **Edge Cases**: Nested code fences handled correctly; both backtick and tilde delimiters supported

**Test Coverage** (v0.5.1):
- ✅ Single-line code blocks in sections
- ✅ Multi-line code blocks with proper extent calculation
- ✅ No duplication on heading replacement
- ✅ Bash/Python comments not extracted as headings
- ✅ Markdown-like syntax inside code (e.g., `# Usage`) ignored
- ✅ Mixed real headings and code comments disambiguated
- ✅ Dogfooding: grafty can edit its own README without data corruption

**Future Considerations**:
- Indented code blocks (4+ spaces) not yet handled—can add if needed
- HTML `<!-- -->` comments not special-cased—edge case unlikely
- Language-specific grammar (e.g., nested backticks in Rust strings) out of scope
