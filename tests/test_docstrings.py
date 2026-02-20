"""Tests for Phase 4.3: Docstring & Doc Comment extraction."""

import pytest
from pathlib import Path


# ── Python Docstrings ──


class TestPythonDocstrings:
    @pytest.fixture
    def py_file(self, tmp_path):
        f = tmp_path / "example.py"
        f.write_text(
            '"""Module docstring."""\n'
            "\n"
            "def hello():\n"
            '    """Hello docstring."""\n'
            "    return 1\n"
            "\n"
            "def no_doc():\n"
            "    return 2\n"
            "\n"
            "class Foo:\n"
            '    """Foo class doc."""\n'
            "\n"
            "    def bar(self):\n"
            '        """Bar method doc."""\n'
            "        pass\n"
            "\n"
            "    def baz(self):\n"
            "        pass\n"
        )
        return f

    def _parse(self, py_file):
        from grafty.parsers.python_ts import PythonParser
        return PythonParser().parse_file(str(py_file))

    def _docs(self, nodes):
        return [n for n in nodes if n.kind == "py_docstring"]

    def test_module_docstring(self, py_file):
        docs = self._docs(self._parse(py_file))
        mod_docs = [d for d in docs if d.name == "__module__"]
        assert len(mod_docs) == 1
        assert mod_docs[0].start_line == 1

    def test_function_docstring(self, py_file):
        docs = self._docs(self._parse(py_file))
        hello_docs = [d for d in docs if d.name == "hello"]
        assert len(hello_docs) == 1
        assert hello_docs[0].start_line == 4

    def test_no_docstring_no_node(self, py_file):
        docs = self._docs(self._parse(py_file))
        no_doc = [d for d in docs if d.name == "no_doc"]
        assert len(no_doc) == 0

    def test_class_docstring(self, py_file):
        docs = self._docs(self._parse(py_file))
        foo_docs = [d for d in docs if d.name == "Foo"]
        assert len(foo_docs) == 1

    def test_method_docstring(self, py_file):
        docs = self._docs(self._parse(py_file))
        bar_docs = [d for d in docs if d.name == "bar"]
        assert len(bar_docs) == 1
        assert bar_docs[0].parent_id is not None

    def test_method_without_doc(self, py_file):
        docs = self._docs(self._parse(py_file))
        baz_docs = [d for d in docs if d.name == "baz"]
        assert len(baz_docs) == 0

    def test_multiline_docstring(self, tmp_path):
        f = tmp_path / "multi.py"
        f.write_text(
            'def func():\n'
            '    """Line 1.\n'
            '\n'
            '    Line 3.\n'
            '    """\n'
            '    pass\n'
        )
        docs = self._docs(self._parse(f))
        assert len(docs) == 1
        assert docs[0].start_line == 2
        assert docs[0].end_line == 5

    def test_total_docstring_count(self, py_file):
        docs = self._docs(self._parse(py_file))
        # __module__, hello, Foo, bar = 4
        assert len(docs) == 4


# ── JavaScript JSDoc ──


class TestJSDocstrings:
    @pytest.fixture
    def js_file(self, tmp_path):
        f = tmp_path / "example.js"
        f.write_text(
            "/**\n"
            " * Does something.\n"
            " * @param {string} name\n"
            " */\n"
            "function hello(name) {\n"
            "    return name;\n"
            "}\n"
            "\n"
            "// regular comment\n"
            "function noDoc() {\n"
            "    return 1;\n"
            "}\n"
            "\n"
            "/**\n"
            " * A class.\n"
            " */\n"
            "class Foo {\n"
            "    /** Method doc. */\n"
            "    bar() {\n"
            "        return 2;\n"
            "    }\n"
            "}\n"
        )
        return f

    def _parse(self, js_file):
        from grafty.parsers.javascript_ts import JavaScriptParser
        return JavaScriptParser().parse_file(str(js_file))

    def _docs(self, nodes):
        return [n for n in nodes if n.kind == "js_jsdoc"]

    def test_function_jsdoc(self, js_file):
        docs = self._docs(self._parse(js_file))
        hello_docs = [d for d in docs if d.name == "hello"]
        assert len(hello_docs) == 1
        assert hello_docs[0].start_line == 1

    def test_regular_comment_not_jsdoc(self, js_file):
        docs = self._docs(self._parse(js_file))
        no_docs = [d for d in docs if d.name == "noDoc"]
        assert len(no_docs) == 0

    def test_class_jsdoc(self, js_file):
        docs = self._docs(self._parse(js_file))
        foo_docs = [d for d in docs if d.name == "Foo"]
        assert len(foo_docs) == 1

    def test_method_jsdoc(self, js_file):
        docs = self._docs(self._parse(js_file))
        bar_docs = [d for d in docs if d.name == "bar"]
        assert len(bar_docs) == 1
        assert bar_docs[0].parent_id is not None

    def test_jsdoc_count(self, js_file):
        docs = self._docs(self._parse(js_file))
        # hello, Foo, bar = 3
        assert len(docs) == 3


# ── Go Doc Comments ──


class TestGoDocstrings:
    @pytest.fixture
    def go_file(self, tmp_path):
        f = tmp_path / "example.go"
        f.write_text(
            "package main\n"
            "\n"
            "// Hello says hello.\n"
            "// It is very friendly.\n"
            "func Hello() string {\n"
            '    return "hello"\n'
            "}\n"
            "\n"
            "func NoDoc() int {\n"
            "    return 1\n"
            "}\n"
            "\n"
            "// MyType is a type.\n"
            "type MyType struct {\n"
            "    Name string\n"
            "}\n"
        )
        return f

    def _parse(self, go_file):
        from grafty.parsers.go_ts import GoParser
        return GoParser().parse_file(str(go_file))

    def _docs(self, nodes):
        return [n for n in nodes if n.kind == "go_doc"]

    def test_function_doc(self, go_file):
        docs = self._docs(self._parse(go_file))
        hello_docs = [d for d in docs if d.name == "Hello"]
        assert len(hello_docs) == 1
        assert hello_docs[0].start_line == 3
        assert hello_docs[0].end_line == 4

    def test_no_doc_no_node(self, go_file):
        docs = self._docs(self._parse(go_file))
        no_docs = [d for d in docs if d.name == "NoDoc"]
        assert len(no_docs) == 0

    def test_type_doc(self, go_file):
        docs = self._docs(self._parse(go_file))
        type_docs = [d for d in docs if d.name == "MyType"]
        assert len(type_docs) == 1

    def test_doc_count(self, go_file):
        docs = self._docs(self._parse(go_file))
        assert len(docs) == 2


# ── Rust Doc Comments ──


class TestRustDocstrings:
    @pytest.fixture
    def rs_file(self, tmp_path):
        f = tmp_path / "example.rs"
        f.write_text(
            "/// Does something cool.\n"
            "/// Multi-line doc.\n"
            "fn hello() -> i32 {\n"
            "    42\n"
            "}\n"
            "\n"
            "// regular comment\n"
            "fn no_doc() -> i32 {\n"
            "    1\n"
            "}\n"
            "\n"
            "/// A struct.\n"
            "struct Foo {\n"
            "    x: i32,\n"
            "}\n"
        )
        return f

    def _parse(self, rs_file):
        from grafty.parsers.rust_ts import RustParser
        return RustParser().parse_file(str(rs_file))

    def _docs(self, nodes):
        return [n for n in nodes if n.kind == "rs_doc"]

    def test_function_doc(self, rs_file):
        docs = self._docs(self._parse(rs_file))
        hello_docs = [d for d in docs if d.name == "hello"]
        assert len(hello_docs) == 1
        assert hello_docs[0].start_line == 1
        # Two /// lines, end_line may include trailing content
        assert hello_docs[0].end_line >= 2

    def test_regular_comment_not_doc(self, rs_file):
        docs = self._docs(self._parse(rs_file))
        no_docs = [d for d in docs if d.name == "no_doc"]
        assert len(no_docs) == 0

    def test_struct_doc(self, rs_file):
        docs = self._docs(self._parse(rs_file))
        foo_docs = [d for d in docs if d.name == "Foo"]
        assert len(foo_docs) == 1

    def test_doc_count(self, rs_file):
        docs = self._docs(self._parse(rs_file))
        assert len(docs) == 2


# ── Clojure Docstrings ──


class TestClojureDocstrings:
    @pytest.fixture
    def clj_file(self, tmp_path):
        f = tmp_path / "example.clj"
        f.write_text(
            '(ns myapp.core)\n'
            '\n'
            '(defn hello\n'
            '  "Says hello."\n'
            '  [name]\n'
            '  (str "Hello " name))\n'
            '\n'
            '(defn no-doc [x]\n'
            '  (+ x 1))\n'
            '\n'
            '(def my-val\n'
            '  "A value doc."\n'
            '  42)\n'
        )
        return f

    def _parse(self, clj_file):
        from grafty.parsers.clojure_ts import ClojureParser
        return ClojureParser().parse_file(str(clj_file))

    def _docs(self, nodes):
        return [n for n in nodes if n.kind == "clj_docstring"]

    def test_defn_docstring(self, clj_file):
        docs = self._docs(self._parse(clj_file))
        hello_docs = [d for d in docs if d.name == "hello"]
        assert len(hello_docs) == 1
        assert hello_docs[0].start_line == 4

    def test_no_docstring_no_node(self, clj_file):
        docs = self._docs(self._parse(clj_file))
        no_docs = [d for d in docs if d.name == "no-doc"]
        assert len(no_docs) == 0

    def test_def_docstring(self, clj_file):
        docs = self._docs(self._parse(clj_file))
        val_docs = [d for d in docs if d.name == "my-val"]
        assert len(val_docs) == 1

    def test_doc_count(self, clj_file):
        docs = self._docs(self._parse(clj_file))
        assert len(docs) == 2
