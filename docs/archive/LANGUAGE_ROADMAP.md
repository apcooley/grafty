# Language Roadmap: Add Popular Languages to grafty

**Objective**: Expand grafty support to cover 90% of codebases (by lines of code).

---

## Current Support

| Language | Type | Status | Example Selector |
|----------|------|--------|------------------|
| Python | Compiled via Tree-sitter | ✅ v0.1.0 | `file.py:py_function:my_func` |
| Markdown | Compiled via Tree-sitter | ✅ v0.1.0 | `file.md:md_heading:Title` |
| Org-mode | Custom regex parser | ✅ v0.1.0 | `file.org:org_heading:Title` |
| Clojure | Compiled + fallback | ✅ v0.1.0 | `file.clj:clj_defn:my_func` |

---

## Language Selection Criteria

### Tier 1: High Priority (Most Common)
- Large ecosystem (millions of developers)
- Frequently found in codebases
- Good Tree-sitter grammar available
- Clear structural units (functions, classes)

### Tier 2: Medium Priority (Emerging/Niche)
- Growing popularity
- Tree-sitter grammar exists but less mature
- Worth supporting for completeness

### Tier 3: Low Priority (Specialist)
- Niche communities
- Grammar maturity uncertain
- Lower ROI on implementation effort

---

## Tier 1: High Priority Languages

### 1. JavaScript / TypeScript
**Why**: #2/#3 most popular languages, 50+ million developers, widely used in web/backend

**Nodes to Index**:
```
- Functions: function foo() { }
- Arrow functions: const foo = () => { }
- Classes: class MyClass { }
- Methods: methodName() { }
- Constants: const VAR = ...
- Imports: import { x } from 'y'
- Exports: export const foo = ...
```

**Selectors**:
```
file.js:js_function:myFunc
file.ts:ts_class:MyClass
file.js:js_const:MY_VAR
```

**Tree-sitter**:
- `tree-sitter-javascript` — Very mature, reliable ✅
- `tree-sitter-typescript` — Mature, covers both JS and TS ✅

**Effort**: 2-3 hours
- Parser similar to Python (classes, functions, methods)
- Handle arrow functions
- Handle const/let/var declarations
- Support imports/exports (optional)

**Preambles**: ✅ Support (function body vs intro)

---

### 2. Go
**Why**: Very popular for backends, cloud infrastructure, DevOps; 1M+ developers

**Nodes to Index**:
```
- Functions: func foo() { }
- Methods: func (r *Receiver) Method() { }
- Structs: type MyStruct struct { }
- Interfaces: type MyInterface interface { }
- Packages: package main
```

**Selectors**:
```
file.go:go_function:myFunc
file.go:go_struct:MyStruct
file.go:go_method:MyReceiver.MyMethod
```

**Tree-sitter**:
- `tree-sitter-go` — Mature, widely used ✅

**Effort**: 2-3 hours
- Similar structure to Python
- Method receiver syntax (func (r *Receiver) Method)
- Package organization

**Preambles**: ✅ Support

---

### 3. Rust
**Why**: Growing rapidly, systems programming, 500K+ developers

**Nodes to Index**:
```
- Functions: fn foo() { }
- Methods: impl MyStruct { fn method() { } }
- Structs: struct MyStruct { }
- Enums: enum MyEnum { }
- Traits: trait MyTrait { }
- Impl blocks: impl MyTrait for MyStruct { }
- Modules: mod mymod { }
```

**Selectors**:
```
file.rs:rs_function:my_func
file.rs:rs_struct:MyStruct
file.rs:rs_impl:MyStruct.my_method
file.rs:rs_trait:MyTrait
```

**Tree-sitter**:
- `tree-sitter-rust` — Mature, reliable ✅

**Effort**: 3-4 hours
- More complex than Go (traits, impl, associated items)
- Need to handle impl blocks specially
- Macros (optional: can skip for v1)

**Preambles**: ✅ Support

---

### 4. Java
**Why**: #1 enterprise language, 9M+ developers, huge codebase footprint

**Nodes to Index**:
```
- Classes: public class MyClass { }
- Methods: public void method() { }
- Interfaces: public interface MyInterface { }
- Enums: public enum MyEnum { }
- Constructors: MyClass() { }
- Inner classes: class Outer { class Inner { } }
```

**Selectors**:
```
file.java:java_class:MyClass
file.java:java_method:MyClass.myMethod
file.java:java_interface:MyInterface
```

**Tree-sitter**:
- `tree-sitter-java` — Mature, reliable ✅

**Effort**: 2-3 hours
- Very similar to Python class/method structure
- Package organization
- Access modifiers (optional)

**Preambles**: ✅ Support

---

## Tier 2: Medium Priority Languages

### 5. C/C++
**Why**: Systems programming, embedded, widely used

**Nodes to Index**:
```
- Functions: void foo() { }
- Structs: struct MyStruct { }
- Classes (C++): class MyClass { }
- Methods (C++): void MyClass::method() { }
- Macros (optional): #define MACRO ...
- Typedefs (optional): typedef struct { } MyType;
```

**Tree-sitter**:
- `tree-sitter-c` — Mature ✅
- `tree-sitter-cpp` — Mature ✅

**Effort**: 3-4 hours
- Header/implementation separation complexity
- Macro parsing (tricky, maybe skip v1)
- Scope resolution operators (::)

**Preambles**: ✅ Support

---

### 6. Ruby
**Why**: 250K+ developers, web development (Rails)

**Nodes to Index**:
```
- Methods: def method_name; end
- Classes: class MyClass; end
- Modules: module MyModule; end
- Blocks: do |x| ... end
- Class methods: def self.class_method; end
```

**Tree-sitter**:
- `tree-sitter-ruby` — Mature ✅

**Effort**: 2-3 hours
- Similar indentation-based structure to Python
- Block syntax
- Class methods

**Preambles**: ✅ Support

---

### 7. PHP
**Why**: 77% of all websites, millions of developers

**Nodes to Index**:
```
- Functions: function foo() { }
- Classes: class MyClass { }
- Methods: public function method() { }
- Namespaces: namespace MyNamespace;
- Traits: trait MyTrait { }
```

**Tree-sitter**:
- `tree-sitter-php` — Mature ✅

**Effort**: 2-3 hours
- Similar to Java class structure
- Namespace handling
- Mixed HTML/PHP (skip for v1)

**Preambles**: ✅ Support

---

## Tier 3: Lower Priority (Specialist)

### 8. Swift
**Tree-sitter**: ✅ Available  
**Effort**: 3 hours  
**Rationale**: Apple ecosystem, smaller (but growing) developer base

### 9. Kotlin
**Tree-sitter**: ✅ Available  
**Effort**: 2-3 hours  
**Rationale**: JVM alternative to Java, growing but smaller community

### 10. C#
**Tree-sitter**: ✅ Available  
**Effort**: 3 hours  
**Rationale**: .NET ecosystem, enterprise popular

### 11. R
**Tree-sitter**: ✅ Available  
**Effort**: 2 hours  
**Rationale**: Data science, niche but important

---

## Implementation Plan

### Phase 1: Foundation (8-10 hours)
Add 3 languages (maximum impact):

**Recommended**: JavaScript, Go, Rust

**Steps**:
1. Create `grafty/parsers/javascript_ts.py` (2-3h)
2. Create `grafty/parsers/go_ts.py` (2-3h)
3. Create `grafty/parsers/rust_ts.py` (3-4h)
4. Write tests for each (1-2h per language)
5. Update CLI to auto-detect and dispatch
6. Update README with examples

**Timeline**: ~2 weeks (part-time, ~4h/day)

### Phase 2: Expansion (6-8 hours)
Add 2-3 more languages:

**Recommended**: Java, C/C++, Ruby

**Same as Phase 1 per language**

**Timeline**: ~2 weeks additional

### Phase 3: Polish (4-6 hours)
- Language parity testing (all have same features)
- Unified selector syntax docs
- Cross-language examples
- Performance optimization if needed

---

## Unified Selector Syntax

### Pattern
All languages follow same selector format:

```
file.ext:language_kind:name[.parent]
```

**Examples**:
```
app.js:js_function:parseData
app.ts:ts_class:ApiClient
app.go:go_function:main
app.rs:rs_struct:MyStruct.new_method
MyClass.java:java_method:parseConfig
config.py:py_function:load_config
README.md:md_heading:Installation
tasks.org:org_heading_preamble:Phase 1
```

### Consistency
All languages support:
- ✅ Full section nodes
- ✅ Preamble nodes (intro text only)
- ✅ Nested/parent scoping
- ✅ Fuzzy name resolution

---

## Testing Strategy

### Per-Language Tests
Same pattern as current tests:

```python
class TestJavaScriptParser:
    def test_parse_functions(self, tmp_repo):
        """Test function extraction."""
    
    def test_parse_classes(self, tmp_repo):
        """Test class extraction."""
    
    def test_parse_methods(self, tmp_repo):
        """Test method extraction."""
    
    def test_preambles(self, tmp_repo):
        """Test intro-only nodes."""
    
    def test_nested_scope(self, tmp_repo):
        """Test nested qualnames."""
```

**Target**: 16+ tests per language (same as preambles tests)

---

## Documentation Updates

### README.md
Add supported languages table with selector examples:

```markdown
| Language | Kind | Example |
|----------|------|---------|
| JavaScript | `js_function`, `js_class` | `app.js:js_function:parse` |
| Go | `go_function`, `go_struct` | `main.go:go_struct:Config` |
| Rust | `rs_function`, `rs_struct` | `lib.rs:rs_struct:MyStruct` |
...
```

### Language Guides
Create `docs/languages/` directory:
- `docs/languages/javascript.md` — Selector examples, syntax notes
- `docs/languages/go.md`
- `docs/languages/rust.md`
- etc.

---

## Success Criteria

### Per Language
- ✅ Parser implemented
- ✅ 16+ tests passing
- ✅ Selectors documented
- ✅ Examples in README
- ✅ Preambles supported

### Overall
- ✅ 10+ languages supported
- ✅ 100% backward compatible
- ✅ Unified selector syntax
- ✅ <10s index time for typical project
- ✅ All tests passing (200+ tests)

---

## Effort Estimation

**Per Language** (Tree-sitter available):
- Parser implementation: 2-4 hours
- Tests: 1-2 hours
- Docs: 0.5-1 hour
- **Total**: 3-7 hours per language

**Total for 10 Languages**:
- Core: 30-70 hours
- Foundation (3 langs): ~10 hours
- Phase 2 (3 langs): ~10 hours
- Phase 3 (4 langs): ~10 hours
- Testing & docs: ~10 hours
- **Grand Total**: ~40-50 hours (1-2 months part-time)

---

## Priority Recommendation

### MVP: Phase 1 (2 weeks)
**Languages**: JavaScript, Go, Rust
**Why**: 
- Cover web, backend, systems programming
- All have mature Tree-sitter grammars
- High developer populations
- Clear structural units

### Add Soon: Phase 2 (2 weeks)
**Languages**: Java, C/C++, Ruby
**Why**:
- Complete enterprise coverage
- Large existing codebases
- High implementation ROI

### Nice to Have: Phase 3 (2 weeks)
**Languages**: PHP, Swift, Kotlin, C#, R
**Why**: Completeness, smaller but important communities

---

## Implementation Checklist

### For Each Language
- [ ] Research Tree-sitter grammar maturity
- [ ] Create `parsers/<lang>_ts.py` file
- [ ] Implement hierarchy building (parent/child)
- [ ] Implement preamble creation
- [ ] Write fixture files (test data)
- [ ] Write 16+ test cases
- [ ] Update `indexer.py` with dispatch
- [ ] Add selector examples to README
- [ ] Create language guide doc
- [ ] Test end-to-end (index → show → replace)

---

## Known Blockers

### None Expected
All high-priority languages have mature Tree-sitter grammars.

**Potential Issues**:
- C++ complexity (templates, complex scoping) → manageable with phased rollout
- PHP mixed HTML/code → skip HTML mixing for v1
- Macros in C → optional feature, skip v1

---

## Next Steps

1. **Decide**: Approve Phase 1 languages (JavaScript, Go, Rust)?
2. **Schedule**: When to start (weeks of dev time available)?
3. **Allocate**: Part-time or dedicated sprint?
4. **Track**: Add to CHANGELOG as languages ship

**Ready to build?** Start with Phase 1. Each language is <3h once pattern is established.
