# grafty Roadmap — Future Phases

**These are future phases beyond v0.4.0.**

grafty v0.4.0 ✅ marks completion of **Phase 3: Core Gaps**. This document outlines the vision for phases 4–7.

Current stable release includes:
- ✅ Structural selectors for Python, JavaScript, TypeScript, Go, Rust, Markdown, Org-mode, Clojure
- ✅ Line-number editing as a fallback
- ✅ Query language for pattern-based search
- ✅ Dry-run safety mode with unified diff output

---

## Phase 4: Safety & Collaboration

**Goal:** Make grafty production-grade with multi-file workflows and version control integration.

🔐 **Multi-file patches** — Atomic changes across multiple files  
&nbsp;&nbsp;&nbsp;&nbsp;Write changes to multiple files, validate together, commit atomically. No partial states.

🔐 **VCS integration** — Auto-commit with rollback on failure  
&nbsp;&nbsp;&nbsp;&nbsp;Auto-stage, commit, and push changes. Rollback cleanly if validation fails.

📝 **Comment extraction** — Edit docstrings separately from code  
&nbsp;&nbsp;&nbsp;&nbsp;Show/edit Python docstrings, JSDoc comments independently from function bodies.

**Effort:** Medium  
**Impact:** High (enterprise workflows, batch automation)

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

Want to tackle Phase 4? Phase 7? Start there! 🚀

---

## Questions?

- Read **[ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)** to understand the design philosophy
- Check **[USAGE.md](../USAGE.md)** for current capabilities
- Open an issue on [GitHub](https://github.com/apcooley/grafty) with questions or ideas
