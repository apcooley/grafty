"""
test_clojure_parser.py — Tests for Clojure parser.
"""

from grafty.parsers.clojure_ts import ClojureParser


class TestClojureParser:
    """Test Clojure parsing."""

    def test_parse_definitions(self, clojure_file):
        """Test parsing Clojure definitions."""
        parser = ClojureParser(use_fallback=False)  # Try Tree-sitter first
        nodes = parser.parse_file(str(clojure_file))

        # Should find: ns, my-func, my-macro, another-func
        assert len(nodes) >= 3

        # Check for namespace
        ns_nodes = [n for n in nodes if n.kind == "clj_ns"]
        assert len(ns_nodes) >= 1
        assert ns_nodes[0].name == "my.namespace"

        # Check for functions
        func_nodes = [n for n in nodes if n.kind == "clj_defn"]
        assert len(func_nodes) >= 2
        func_names = {n.name for n in func_nodes}
        assert "my-func" in func_names
        assert "another-func" in func_names

        # Check for macros
        macro_nodes = [n for n in nodes if n.kind == "clj_defmacro"]
        assert len(macro_nodes) >= 1

    def test_fallback_parser(self, clojure_file):
        """Test fallback parser."""
        parser = ClojureParser(use_fallback=True)
        nodes = parser.parse_file(str(clojure_file))

        # Should still find definitions
        assert len(nodes) >= 3

        func_nodes = [n for n in nodes if n.kind == "clj_defn"]
        assert len(func_nodes) >= 2

    def test_node_line_ranges(self, clojure_file):
        """Test that line ranges are correct."""
        parser = ClojureParser()
        nodes = parser.parse_file(str(clojure_file))

        for node in nodes:
            assert node.start_line >= 1
            assert node.end_line >= node.start_line
