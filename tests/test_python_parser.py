"""
test_python_parser.py — Tests for Python parser.
"""

from grafty.parsers.python_ts import PythonParser


class TestPythonParser:
    """Test Python parsing."""

    def test_parse_class_and_methods(self, python_file):
        """Test parsing class with methods."""
        parser = PythonParser()
        nodes = parser.parse_file(str(python_file))

        # Should find: MyClass, __init__, method_one, method_two, top_level_function
        assert len(nodes) >= 5

        # Check for class
        class_nodes = [n for n in nodes if n.kind == "py_class"]
        assert len(class_nodes) >= 1
        assert class_nodes[0].name == "MyClass"

        # Check for methods
        method_nodes = [n for n in nodes if n.kind == "py_method"]
        assert len(method_nodes) >= 2
        method_names = {n.name for n in method_nodes}
        assert "method_one" in method_names
        assert "method_two" in method_names

        # Check for function
        func_nodes = [n for n in nodes if n.kind == "py_function"]
        assert len(func_nodes) >= 1
        assert func_nodes[0].name == "top_level_function"

    def test_node_qualnames(self, python_file):
        """Test that qualnames are correct."""
        parser = PythonParser()
        nodes = parser.parse_file(str(python_file))

        # Find method
        method_nodes = [n for n in nodes if n.name == "method_one"]
        assert len(method_nodes) == 1

        method_node = method_nodes[0]
        assert method_node.qualname == "MyClass.method_one"
        assert method_node.is_method is True

    def test_line_ranges(self, python_file):
        """Test that line ranges are correct."""
        parser = PythonParser()
        nodes = parser.parse_file(str(python_file))

        # Class should span multiple lines
        class_nodes = [n for n in nodes if n.kind == "py_class"]
        assert len(class_nodes) >= 1

        class_node = class_nodes[0]
        assert class_node.start_line < class_node.end_line
        assert class_node.end_line > 0

    def test_node_ids_stable(self, python_file):
        """Test that node IDs are stable (same file → same IDs)."""
        parser = PythonParser()

        nodes1 = parser.parse_file(str(python_file))
        nodes2 = parser.parse_file(str(python_file))

        ids1 = {n.id for n in nodes1}
        ids2 = {n.id for n in nodes2}

        assert ids1 == ids2
