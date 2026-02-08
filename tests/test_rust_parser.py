"""
Tests for Rust parser.
"""
from grafty.parsers import RustParser


class TestRustParser:
    """Test Rust parser."""

    parser = RustParser()

    def test_parse_structs_and_impls(self, tmp_path) -> None:
        """Test parsing Rust structs and impl blocks."""
        code = """
pub struct DataProcessor {
    name: String,
    id: u32,
}

impl DataProcessor {
    pub fn new(name: String, id: u32) -> Self {
        DataProcessor { name, id }
    }

    pub fn process(&self, data: &str) -> String {
        data.trim().to_string()
    }

    pub fn validate(&self) -> bool {
        self.name.len() > 0
    }
}

fn main() {
    println!("Hello!");
}

fn fetch_data(url: &str) -> String {
    String::from(url)
}
"""
        test_file = tmp_path / "test.rs"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        # Should have: 1 struct, 1 impl, 3 methods, 2 functions
        assert len(nodes) >= 7

        # Check struct
        structs = [n for n in nodes if n.kind == "rs_struct"]
        assert len(structs) == 1
        assert structs[0].name == "DataProcessor"

        # Check impl
        impls = [n for n in nodes if n.kind == "rs_impl"]
        assert len(impls) == 1
        assert impls[0].name == "DataProcessor"
        assert len(impls[0].children_ids) == 3

        # Check methods
        methods = [n for n in nodes if n.kind == "rs_method"]
        assert len(methods) == 3
        assert set(m.name for m in methods) == {"new", "process", "validate"}

        # Check functions
        functions = [n for n in nodes if n.kind == "rs_function"]
        assert len(functions) == 2
        assert set(f.name for f in functions) == {"main", "fetch_data"}

    def test_trait_declaration(self, tmp_path) -> None:
        """Test parsing trait declaration."""
        code = """
pub trait Processable {
    fn process(&self, data: &str) -> String;
    fn validate(&self) -> bool;
}
"""
        test_file = tmp_path / "test.rs"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        traits = [n for n in nodes if n.kind == "rs_trait"]
        assert len(traits) == 1
        assert traits[0].name == "Processable"

    def test_struct_declaration(self, tmp_path) -> None:
        """Test parsing struct declaration."""
        code = """
pub struct Point {
    x: i32,
    y: i32,
}
"""
        test_file = tmp_path / "test.rs"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        structs = [n for n in nodes if n.kind == "rs_struct"]
        assert len(structs) == 1
        assert structs[0].name == "Point"

    def test_macro_definition(self, tmp_path) -> None:
        """Test parsing macro definition."""
        code = """
macro_rules! debug_print {
    ($($arg:tt)*) => {
        println!($($arg)*)
    };
}
"""
        test_file = tmp_path / "test.rs"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))

        macros = [n for n in nodes if n.kind == "rs_macro"]
        assert len(macros) == 1
        assert macros[0].name == "debug_print"

    def test_line_ranges(self, tmp_path) -> None:
        """Test that line ranges are correct."""
        code = """
fn foo() {
    println!("foo");
}

fn bar() {
    println!("bar");
}
"""
        test_file = tmp_path / "test.rs"
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
        test_file = tmp_path / "test.rs"
        test_file.write_text(code)
        nodes = self.parser.parse_file(str(test_file))
        assert len(nodes) == 0
