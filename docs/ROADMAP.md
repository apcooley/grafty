# grafty Roadmap

## Status Summary

| Phase | Title | Status | Key Deliverable |
|---|---|---|---|
| 1 | Core Infrastructure | ✅ Complete | Structural parsers (7 languages) |
| 2 | Multi-Language Support | ✅ Complete | JavaScript/TypeScript, Go, Rust support |
| 3 | Core Gaps Filled | ✅ Complete | Line editing, Search Query Language |
| **4.1** | **Atomic Multi-File Patches** | **✅ COMPLETE (v0.5.0)** | `grafty apply-patch` |
| **4.2** | **VCS Integration** | **🔜 Next Up** | Auto-commit/rollback via Git |
| 4.3 | Comment Extraction | ➡️ Planned | Docstring/Comment node type |
| 5 | Discovery & Visualization | ➡️ Planned | Web UI, Node Tree Explorer |
| 6 | Performance & Scale | ➡️ Planned | Index Caching, LSP Hook |
| 7 | Extended Languages | ➡️ Planned | C/C++, JVM, SQL support |

---

## Phase 4: Safety & Collaboration

**Goal:** Make grafty production-grade with multi-file workflows and version control integration.

### **4.1: Atomic Multi-File Patches** (✅ **COMPLETE - v0.5.0**)
- Implemented via `grafty apply-patch`.
- **Key Feature:** Atomic writes across files using temp files + rename, with rollback on error.

### **4.2: VCS Integration** (🔜 **Next Sprint**)

**Goal:** Enable Git integration for automated, traceable refactoring.

🔐 **Auto-commit/Push** — Auto-stage, commit, and push changes  
&nbsp;&nbsp;&nbsp;&nbsp;Use `--auto-commit "message"` or `--auto-push` flag on `apply-patch`.

🔐 **Rollback on Failure** — Revert failed multi-file operations cleanly  
&nbsp;&nbsp;&nbsp;&nbsp;If `apply-patch` fails mid-way, it rolls back all successful writes using `.bak` files.

**Effort:** Medium  
**Impact:** High (enterprise workflows, CI/CD pipelines)

### **4.3: Comment Extraction** (➡️ **Planned**)

**Goal:** Treat documentation blocks as first-class, editable structures.

📝 **Comment/Docstring Extraction** — Edit docstrings separately from code  
&nbsp;&nbsp;&nbsp;&nbsp;New node kinds: `py_docstring`, `js_jsdoc`, `rs_rustdoc`.

**Effort:** Medium  
**Impact:** Medium (improves documentation hygiene)

---

## Phase 5: Discovery & Visualization

**Goal:** Make code exploration intuitive with interactive tools.

🌐 **Web UI** — Side-by-side before/after visualization  
&nbsp;&nbsp;&nbsp;&nbsp;Browser-based editor: select nodes, preview changes, apply with one click.

🌳 **Node tree explorer** — ASCII tree + interactive web explorer  
&nbsp;&nbsp;&nbsp;&nbsp;Browse full codebase structure in terminal or web UI. Jump to any function/class.

**Effort:** Medium  
**Impact:** Medium (nice to have, improves UX)

---

## Phase 6: Performance & Scale

**Goal:** Support large codebases and frequent operations without slowdown.

⚡ **Index caching** — 10-50x speedup for large files  
&nbsp;&nbsp;&nbsp;&nbsp;Cache parsed ASTs to disk. Invalidate on file change. Huge speedup for batch operations.

⚡ **LSP integration** — Optional semantic awareness (Rust, Go, etc.)  
&nbsp;&nbsp;&nbsp;&nbsp;Hook into Language Server Protocol for type-aware refactoring (rename safe-refactoring, find references).

**Effort:** High  
**Impact:** High (necessary for large projects)

---

## Phase 7: Extended Languages

**Goal:** Support more ecosystems (C/C++, JVM, databases, shell).

- **C/C++** (high demand for large codebases)
- **Java, Scala** (JVM ecosystem)
- **SQL, PostgreSQL** (database work)
- **Shell script** (.sh, .bash)

**Effort:** High (one language = 1-2 weeks each)  
**Impact:** High (unlocks new workflows)

---

## How to Contribute

See **[CONTRIBUTING.md](./CONTRIBUTING.md)** for:
- How these phases break down into starter tasks
- Complexity levels (Low/Medium/High)
- How to pick your first issue
- How to run tests and validate your work

Want to tackle Phase 4.2? Start there! 🚀

---

## Questions?

- Read **[ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)** to understand the design philosophy
- Check **[USAGE.md](../USAGE.md)** for current capabilities
- Open an issue on [GitHub](https://github.com/apcooley/grafty) with questions or ideas
