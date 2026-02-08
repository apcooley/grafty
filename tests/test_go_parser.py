"""
Tests for Go parser.
"""
import pytest
from grafty.parsers import GoParser


class TestGoParser:
    """Test Go parser."""

    parser = GoParser()

    def test_parse_functions_and_types(self, tmp_path) -> None:
        """Test parsing Go functions and types."""
        code = """
package main

type DataProcessor struct {
  Name string
  ID   int
}

func main() {
  println("hello")
}

func (dp *DataProcessor) Process(data string) string {
  return data
}

func (dp *DataProcessor) Validate() bool {
  return len(dp.Name) > 0
}

func fetchData(url string) string {
  return "data"
}
"""
        test_file = tmp_path / "test.go"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        # Should have: 1 type, 3 functions (main, fetchData + 2 methods)
        assert len(nodes) == 5

        # Check type
        types = [n for n in nodes if n.kind == "go_type"]
        assert len(types) == 1
        assert types[0].name == "DataProcessor"

        # Check functions
        functions = [n for n in nodes if n.kind == "go_function"]
        assert len(functions) == 2
        assert set(f.name for f in functions) == {"main", "fetchData"}

        # Check methods
        methods = [n for n in nodes if n.kind == "go_method"]
        assert len(methods) == 2
        assert set(m.name for m in methods) == {"Process", "Validate"}

    def test_struct_declaration(self, tmp_path) -> None:
        """Test parsing struct declaration."""
        code = """
type Person struct {
  Name string
  Age  int
}
"""
        test_file = tmp_path / "test.go"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        assert len(nodes) == 1
        assert nodes[0].kind == "go_type"
        assert nodes[0].name == "Person"

    def test_method_declaration(self, tmp_path) -> None:
        """Test parsing method declaration."""
        code = """
type Calculator struct {
  Value int
}

func (c *Calculator) Add(x int) {
  c.Value += x
}

func (c *Calculator) Get() int {
  return c.Value
}
"""
        test_file = tmp_path / "test.go"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        methods = [n for n in nodes if n.kind == "go_method"]
        assert len(methods) == 2
        assert set(m.name for m in methods) == {"Add", "Get"}

    def test_line_ranges(self, tmp_path) -> None:
        """Test that line ranges are correct."""
        code = """
func foo() {
  println("foo")
}

func bar() {
  println("bar")
}
"""
        test_file = tmp_path / "test.go"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        foo = next(n for n in nodes if n.name == "foo")
        assert foo.start_line == 2
        assert foo.end_line == 4

        bar = next(n for n in nodes if n.name == "bar")
        assert bar.start_line == 6
        assert bar.end_line == 8

    def test_empty_file(self, tmp_path) -> None:
        """Test parsing empty file."""
        code = ""
        test_file = tmp_path / "test.go"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))
        assert len(nodes) == 0
