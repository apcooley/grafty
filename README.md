# grafty — Structural Code Editor for LLMs & Humans

**Edit large files without losing your mind.** grafty indexes code into structural units (functions, classes, headings) so you can reference specific pieces instead of showing entire files. Perfect for LLM agents, batch refactoring, and token-efficient workflows.

```bash
# Instead of asking an LLM to show you the whole 500-line file...
# Just show what matters:
grafty show "src/main.py:py_function:parse_config"
# Returns only that function (10 lines). Token-efficient. ✅
```

---

## Why Structural Editing?

**Problem:** When you edit large files, you have two bad choices:
- Show the entire file (expensive tokens, noise, context bloat)
- Use line numbers (fragile, breaks when file changes)

**Solution:** grafty understands **structure**. Reference code by what it is, not where it is:
- `src/main.py:py_function:parse_config` ← Still the same function even if moved
- `README.md:md_heading:Installation` ← Still the same section even if reordered
- `tasks.org:org_heading_preamble:Phase 1` ← Edit intro, keep subsections intact

**Result:** Safe, bounded, token-efficient editing. For you, for LLM agents, for batch refactoring.

---

## What Can You Do With grafty?

✅ **Show bounded snippets** — Instead of sending entire files to LLMs, show just the function/class/section they need  
✅ **Refactor safely** — Replace, insert, delete with atomic writes and dry-run preview  
✅ **Batch edit** — Find all functions matching a pattern, apply changes across files  
✅ **Understand structure** — Index any codebase and see what's inside (no LSP needed)  
✅ **Integration-friendly** — Works with Git, generates clean unified diffs  
✅ **LLM-native** — Designed for agents: selectors are stable, output is bounded  

---

## Quick Example: See It In Action

Let's say you have a file with a function that needs fixing:

```python
# src/validators.py
def validate_email(email):
    # Naive implementation that doesn't work
    if "@" in email:
        return True
    return False
```

Instead of:
```bash
# ❌ Show me lines 5-10 (brittle, what if the file changes?)
# ❌ Show me the whole file (50 lines, tokens wasted on context)
```

You do:
```bash
# ✅ Show me the validate_email function
grafty show "src/validators.py:py_function:validate_email"

# Output:
# ──── src/validators.py:py_function:validate_email (lines 2-5)
# def validate_email(email):
#     if "@" in email:
#         return True
#     return False
```

Then replace it:
```bash
# Preview the change first (dry-run)
grafty replace "src/validators.py:py_function:validate_email" \
  --text "def validate_email(email):
    \"\"\"Validate email using basic RFC rules.\"\"\"
    return bool(re.match(r'^[a-zA-Z0-9+._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))" \
  --dry-run

# See the unified diff before applying
# Apply it when ready
grafty replace "src/validators.py:py_function:validate_email" \
  --text "..." --apply --backup
```

**That's it.** Safe, clean, token-efficient. Works with any language grafty supports.

---

## Installation

### Option 1: System Install (Recommended for Users)

grafty is available as a system tool. Just use it:

```bash
grafty --help        # Should work
grafty index .       # Index your project
```

If it's not installed yet:

```bash
# Clone the repo
git clone https://github.com/apcooley/grafty.git
cd grafty

# Install as a system tool
python3 -m pip install -e .
# or: uv pip install -e .

# Verify it works
grafty --help
```

### Option 2: Development Install (For Contributors/Advanced Users)

```bash
# Clone and set up
git clone https://github.com/apcooley/grafty.git
cd grafty

# Install dependencies (auto-managed by uv)
uv sync

# Run with development environment
uv run grafty index .
uv run grafty show "file.py:py_function:my_func"
uv run pytest tests/  # Run tests
```

### Requirements

- **Python 3.10+** (any OS: Linux, macOS, Windows WSL)
- **Tree-sitter** (auto-installed via dependencies, no manual setup needed)
- **Git** (optional, for validation and patch checking)

That's it! No complicated setup.

---

## Quick Start: 5 Minutes to Your First Edit

### Step 1: Index a File

```bash
grafty index src/main.py

# Output shows everything grafty found:
# src/main.py (12 nodes)
# [py_class   ] DataProcessor          (lines 1-50)
#   [py_method] __init__               (lines 2-10)
#   [py_method] parse                  (lines 12-30)
#   [py_method] validate               (lines 32-50)
# [py_function] main                   (lines 52-65)
```

### Step 2: Show a Piece

```bash
# Show just the parse method
grafty show "src/main.py:py_class:DataProcessor.parse"
# or
grafty show "src/main.py:py_method:parse"

# Output: just the method, bounded (no token waste)
```

### Step 3: Replace It

```bash
# Create a file with your new implementation
cat > new_parse.py << 'EOF'
def parse(self, data):
    """Parse data using new algorithm."""
    results = []
    for line in data.split('\n'):
        if line.strip():
            results.append(self._parse_line(line))
    return results
EOF

# Apply the change
grafty replace "src/main.py:py_method:parse" \
  --file new_parse.py \
  --apply --backup
```

### Step 4: Verify

```bash
# See what changed
git diff src/main.py

# Or re-show the node to confirm
grafty show "src/main.py:py_method:parse"
```

**Done!** You just edited a structured piece of code safely and efficiently.

---

## Features & Capabilities

### 📁 Supported Languages

| Language | What You Can Edit | Example |
|----------|-------------------|---------|
| **Python** (.py) | Classes, methods, functions, standalone code | `file.py:py_function:parse_config` |
| **JavaScript/TypeScript** (.js, .ts, .jsx, .tsx) | Functions, classes, methods, arrow functions | `app.ts:js_function:handler` |
| **Go** (.go) | Functions, methods, types, structs | `main.go:go_function:main` |
| **Rust** (.rs) | Functions, structs, impls, traits, macros | `lib.rs:rs_struct:DataProcessor` |
| **Markdown** (.md) | Headings, sections, intro paragraphs | `README.md:md_heading:Installation` |
| **Org-mode** (.org) | Headings, subtrees, intro paragraphs | `tasks.org:org_heading:Phase 1` |
| **Clojure** (.clj/.cljs) | Namespaces, defs, macros | `core.clj:clj_defn:my_func` |

### 🎯 Core Features

**Structural Selectors** — Reference code by structure, not line numbers  
```bash
grafty show "src/main.py:py_function:validate"  # Stable, even if file changes
```

**Line Numbers (When You Need Them)** — Quick fixes with simple ranges  
```bash
grafty show "src/main.py:42"        # Single line
grafty show "src/main.py:42-50"     # Range of lines
```

**Heading Preambles** — Edit section intros without destroying subsections (Markdown & Org-mode)  
```bash
# Edit just the intro text of a heading, preserve all subheadings
grafty replace "README.md:md_heading_preamble:Installation" \
  --text "# Installation\n\nNew intro here." \
  --apply
```

**Pattern Search** — Find nodes by name pattern  
```bash
grafty search "*validate*"              # All validation functions
grafty search "test_*" --path "tests/"  # All tests in tests/ directory
grafty search "*handler*" --kind "js_function"  # JS handlers only
```

**Dry-Run Mode** — Always preview before applying  
```bash
grafty replace ... --dry-run  # Shows unified diff
grafty replace ... --apply    # Apply if it looks good
```

**Atomic Writes** — No partial changes, no corruption  
- Changes are written to temp file, then renamed (atomic)
- Optional automatic backups (`.bak` files)
- Safe to use even with long-running processes

**Safety Guarantees** — Peace of mind when editing  
```bash
grafty replace ... --apply --backup          # Auto-backup
grafty replace ... --dry-run                  # Preview first
grafty check my.patch                         # Validate patches
```

---

## Use Cases: Where grafty Shines

### 🤖 LLM Agents & AI Workflows

**Problem:** Your agent is writing code for a 500-line file. Show it just the function it needs to edit:

```bash
# Instead of context bloat, agent gets bounded output
grafty show "src/processing.py:py_function:process_data"

# Agent writes new implementation
# You apply it
grafty replace "src/processing.py:py_function:process_data" \
  --text "$(agent_output)" --apply --backup
```

**Benefits:**
- Smaller context window (save 100+ tokens per operation)
- Agents stay focused on one piece at a time
- Patch diff makes changes auditable before applying

### 📋 Batch Refactoring

**Problem:** You need to rename a function across 10 files and update all callers.

```bash
# Find all calls to old_name
grafty search "old_name*"

# Replace them systematically
grafty replace "src/main.py:py_function:old_name" --file new_impl.py --apply
grafty replace "src/utils.py:py_function:old_name" --file new_impl.py --apply
# ... (repeatable, safe)
```

**Benefits:**
- No need for IDE refactoring (works anywhere: CLI, remote, scripts)
- Every change generates a visible diff
- Easy to automate or batch

### ✏️ Code Review & Documentation

**Problem:** You need to update docstrings or comments in Markdown without affecting code examples.

```bash
# Edit just the intro of a section (keep examples, code blocks intact)
grafty show "DESIGN.md:md_heading_preamble:Architecture"
grafty replace "DESIGN.md:md_heading_preamble:Architecture" \
  --file new_intro.txt --apply
```

**Benefits:**
- Edit documentation structure without touching nested examples
- Precise, bounded changes
- Great for collaborative docs (less merge conflicts)

### 🔧 Integration with CI/CD & Version Control

**Problem:** You're building an auto-fixer that applies changes to multiple repos.

```bash
# grafty generates clean unified diffs
grafty replace "src/api.py:py_function:old_handler" \
  --file new_handler.py --patch-out my_changes.patch

# Apply the patch in CI/CD
git apply my_changes.patch

# Or review first
git apply --check my_changes.patch
```

**Benefits:**
- Standard unified diff format (works with `git apply`, `patch` command, etc.)
- Dry-run lets you validate before pushing
- Integrates with existing git workflows

---

## Full Documentation

Once you're familiar with the basics, check these for deeper knowledge:

- **[USAGE.md](./USAGE.md)** — Detailed command reference with all flags and options
- **[ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md)** — Why grafty was built this way (for the curious)
- **[CHANGELOG.md](./CHANGELOG.md)** — Version history and feature releases
- **[DESIGN.md](./DESIGN.md)** — Original architecture sketches and design rationale

For development:

```bash
cd ~/source/grafty
uv sync                    # Install dev dependencies
uv run pytest tests/ -v    # Run tests (all 37 passing)
uv run ruff check grafty/  # Lint code
```

---

## FAQ

### ❓ Is grafty safe to use?

**Absolutely.** Safety is a core design principle:

✅ **Atomic writes** — Changes written to temp file, then renamed (no partial writes)  
✅ **Dry-run mode** — Always preview with `--dry-run` before applying  
✅ **Automatic backups** — Optional `--backup` creates `.bak` files  
✅ **Patch validation** — `grafty check my.patch` uses `git apply --check`  
✅ **Clear diffs** — Every change shows unified diff so you can audit it  

**Golden rule:** Use `--dry-run` first, review the diff, then apply if it looks good.

### ❓ What if I make a mistake?

**Easy recovery:**

1. **Backup exists** — If you used `--backup`, restore from `.bak`:
   ```bash
   cp src/main.py.bak src/main.py
   ```

2. **Git history** — If it's in a git repo:
   ```bash
   git checkout src/main.py  # Revert the whole file
   git diff                  # See what changed (before your edit)
   ```

3. **Try again** — Use `--dry-run` next time to preview first.

### ❓ Can I use grafty with my LLM?

**Yes!** grafty is designed for LLM workflows:

```python
# Pseudocode: LLM workflow with grafty
current_state = subprocess.run([
    "grafty", "show", 
    "src/main.py:py_function:validate"
]).stdout

prompt = f"""
Here's the current implementation:
{current_state}

Make it better.
"""

new_code = llm.generate(prompt)

# Apply the change
subprocess.run([
    "grafty", "replace",
    "src/main.py:py_function:validate",
    "--text", new_code,
    "--apply", "--backup"
])
```

**Benefits for LLM use:**
- Bounded output (agent sees exactly what it needs to edit)
- Stable selectors (function name doesn't change when file does)
- Clean diffs for review
- Token-efficient (show 20 lines, not 500)

### ❓ What about unsupported file types?

grafty skips them, but you can still use **line-based editing** as a fallback:

```bash
# Works on any text file
grafty show "unknown.txt:42-50"
grafty replace "unknown.txt:42-50" --text "new content" --apply
```

For maximum impact, focus grafty on code files (Python, JS, Go, Rust, Markdown, Org).

### ❓ Why not just use `sed` or my IDE's refactoring?

**sed** works on patterns; **grafty understands structure**:
- `sed -i 's/old_name/new_name/g'` might rename variables, function names, comments—too broad
- `grafty show "file.py:py_function:old_name"` is precise—it's definitely that function
- `grafty replace` handles nested scopes correctly (methods inside classes)

**IDE refactoring** is great locally; **grafty works everywhere**:
- No IDE installation needed
- Works on remote machines, in CI/CD, in containers
- Scriptable for batch operations
- Works across the web via simple CLI calls

**Use both!** IDE for interactive work, grafty for automation and edge cases.

### ❓ Does grafty support merge conflicts?

Yes. grafty outputs standard **unified diffs**:

```bash
grafty replace "src/main.py:py_function:handler" \
  --file new_impl.py \
  --patch-out my_changes.patch

# my_changes.patch is a standard unified diff
# Use standard merge tools:
git apply my_changes.patch
patch < my_changes.patch
```

If conflicts arise, use git's 3-way merge or your favorite merge tool.

### ❓ How does grafty compare to Language Servers (LSP)?

| Feature | grafty | LSP |
|---------|--------|-----|
| **Setup** | Single install, works everywhere | Per-language, requires LSP server |
| **Portability** | CLI, works remote, in containers | IDE-centric |
| **Symbol knowledge** | Tree-sitter (syntax-based) | Compiler-aware (semantic) |
| **For LLMs** | Perfect (bounded output) | Overkill (better for IDE) |
| **Batch editing** | ✅ Great | ❌ Not designed for this |
| **Type awareness** | Limited (syntax only) | Full (compiler-aware) |

**Bottom line:** grafty is for editing; LSP is for IDE integration. Use grafty for agents and batch work.

### ❓ How do I get help or report a bug?

- **Questions?** Check `USAGE.md` or run `grafty --help`
- **Bug report?** Open an issue on [GitHub](https://github.com/apcooley/grafty)
- **Feature request?** See the [Roadmap](#roadmap) for what's planned

---

## Roadmap

grafty is actively developed. Here's what's coming:

### Phase 3: Core Gaps ✅ **Complete in v0.4.0**

✨ **Line-number editing** — `grafty replace file.py:42-50 --text "..."`  
✨ **Improved error messages** — Shows candidates when selectors don't match  
✨ **Query language** — `grafty search "*validate*"` to find code by pattern  

### Phase 4: Safety & Collaboration (Coming)

🔐 **Multi-file patches** — Atomic changes across multiple files  
🔐 **VCS integration** — Auto-commit with rollback on failure  
📝 **Comment extraction** — Edit docstrings separately from code  

### Phase 5: Discovery & Visualization (Coming)

🌐 **Web UI** — Side-by-side before/after visualization  
🌳 **Node tree explorer** — ASCII tree + interactive web explorer  

### Phase 6: Performance & Scale (Coming)

⚡ **Index caching** — 10-50x speedup for large files  
⚡ **LSP integration** — Optional semantic awareness (Rust, Go, etc.)  

### Phase 7: Extended Languages (Coming)

- C/C++ (high demand for large codebases)
- Java, Scala (JVM ecosystem)
- SQL, PostgreSQL (database work)
- Shell script (.sh, .bash)

---

## Getting Started

**Right now, you can:**

1. ✅ Install grafty (`pip install -e .` or use system install)
2. ✅ Index your codebase (`grafty index .`)
3. ✅ Show bounded snippets (`grafty show "file.py:py_function:func"`)
4. ✅ Make safe edits (`grafty replace ... --dry-run --apply`)
5. ✅ Search for code (`grafty search "*pattern*"`)

**Pick a file, try it:**

```bash
# Pick any Python, JS, Go, Rust, Markdown, or Org file
grafty index myfile.py

# Pick a function or class name
grafty show "myfile.py:py_function:my_func"

# Try editing it
grafty replace "myfile.py:py_function:my_func" \
  --text "def my_func():\n    return 42" \
  --dry-run
```

**Questions?** Check `USAGE.md` or run `grafty --help`.

---

## Contributing

Contributions welcome! See `FEATURE_PLAN_PHASE2.md` for detailed phases and complexity levels.

**Good starter issues:**
- Bug reports with reproducers
- Documentation improvements
- Performance profiling
- Real-world use case feedback

**Want to add a language?** See `LANGUAGE_ROADMAP.md` for parser guidance.

---

## License

MIT — Use freely, modify, distribute. See LICENSE for details.

---

**Happy editing!** 🎯  
Made for humans and LLMs alike.
