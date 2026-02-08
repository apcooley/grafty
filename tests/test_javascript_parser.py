"""
Tests for JavaScript/TypeScript parser.
"""
from grafty.parsers import JavaScriptParser


class TestJavaScriptParser:
    """Test JavaScript parser with TypeScript/JSX support."""

    parser = JavaScriptParser()

    def test_parse_functions_and_classes(self, tmp_path) -> None:
        """Test parsing JavaScript functions and classes."""
        code = """
class DataProcessor {
  constructor(name) {
    this.name = name;
  }

  parse(data) {
    return JSON.parse(data);
  }

  validate() {
    return true;
  }
}

function fetchData(url) {
  return fetch(url);
}

async function processAsync(data) {
  return data;
}
"""
        test_file = tmp_path / "test.js"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        # Should have: DataProcessor class, 3 methods, 2 functions (6 total)
        assert len(nodes) == 6

        # Find DataProcessor class
        processor = next(n for n in nodes if n.name == "DataProcessor")
        assert processor.kind == "js_class"
        assert len(processor.children_ids) == 3

        # Check methods are children
        method_names = [n.name for n in nodes if n.parent_id == processor.id]
        assert set(method_names) == {"constructor", "parse", "validate"}

        # Check functions
        functions = [n for n in nodes if n.kind == "js_function"]
        assert len(functions) == 2
        assert {f.name for f in functions} == {"fetchData", "processAsync"}

    def test_class_with_methods(self, tmp_path) -> None:
        """Test parsing class with methods."""
        code = """
class Foo {
  method1() { }
  method2() { }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        foo_class = next(n for n in nodes if n.kind == "js_class")
        assert foo_class.name == "Foo"
        assert len(foo_class.children_ids) == 2

        methods = [n for n in nodes if n.kind == "js_method"]
        assert len(methods) == 2

    def test_function_declaration(self, tmp_path) -> None:
        """Test parsing function declarations."""
        code = """
function foo() {
  return 42;
}

function bar(x, y) {
  return x + y;
}
"""
        test_file = tmp_path / "test.js"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        functions = [n for n in nodes if n.kind == "js_function"]
        assert len(functions) == 2
        assert {f.name for f in functions} == {"foo", "bar"}

    def test_line_ranges(self, tmp_path) -> None:
        """Test that line ranges are correct."""
        code = """
function foo() {
  console.log("foo");
}

class Bar {
  method() {
    return 42;
  }
}
"""
        test_file = tmp_path / "test.js"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        foo = next(n for n in nodes if n.name == "foo")
        assert foo.start_line == 2
        assert foo.end_line == 4

        bar_class = next(n for n in nodes if n.name == "Bar")
        assert bar_class.start_line == 6
        assert bar_class.end_line == 10

    def test_empty_file(self, tmp_path) -> None:
        """Test parsing empty file."""
        code = ""
        test_file = tmp_path / "test.js"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))
        assert len(nodes) == 0

    def test_file_with_only_comments(self, tmp_path) -> None:
        """Test parsing file with only comments."""
        code = """
// This is a comment
/* Multi-line
   comment */
"""
        test_file = tmp_path / "test.js"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))
        assert len(nodes) == 0
