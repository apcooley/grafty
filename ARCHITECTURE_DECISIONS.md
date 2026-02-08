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
