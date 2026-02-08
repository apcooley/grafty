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
