"""
clojure_ts.py — Clojure/ClojureScript indexing via Tree-sitter.
Falls back to balanced-paren scanner if Tree-sitter fails.
"""
from typing import List, Optional
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_clojure
    HAS_TS_CLOJURE = True
except ImportError:
    HAS_TS_CLOJURE = False

from ..models import Node
from .clojure_fallback import ClojureFallbackParser


class ClojureParser:
    """Index Clojure/ClojureScript files using Tree-sitter or fallback."""

    def __init__(self, use_fallback: bool = False):
        self.use_fallback = use_fallback or not HAS_TS_CLOJURE
        self.language = None
        self.parser = None

        if not self.use_fallback:
            try:
                self.language = Language(tree_sitter_clojure.language())
                self.parser = Parser(self.language)
            except Exception as e:
                print(f"Warning: Clojure Tree-sitter unavailable: {e}")
                self.use_fallback = True

        self.fallback = ClojureFallbackParser()

    def parse_file(self, file_path: str) -> List[Node]:
        """Index a Clojure file and return list of definition nodes."""
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        if self.use_fallback:
            return self.fallback.parse_file(file_path)

        try:
            tree = self.parser.parse(content.encode("utf-8"))
            nodes = self._extract_defs(tree.root_node, file_path, content)
            if not nodes:
                # Fallback if no defs found
                return self.fallback.parse_file(file_path)
            return nodes
        except Exception as e:
            print(f"Warning: Tree-sitter parse failed for {file_path}; using fallback: {e}")
            return self.fallback.parse_file(file_path)

    def _extract_defs(
        self,
        node,
        file_path: str,
        content: str,
    ) -> List[Node]:
        """Recursively extract all definitions (defn, defmacro, etc.)."""
        nodes: List[Node] = []

        # Look for lists that start with def/defn/etc.
        if node.type == "list_lit":
            def_node = self._parse_def_form(node, file_path, content)
            if def_node:
                nodes.append(def_node)

        # Also look for namespaces
        if node.type == "list_lit":
            ns_node = self._parse_ns_form(node, file_path, content)
            if ns_node:
                nodes.append(ns_node)

        # Recurse
        for child in node.children:
            nodes.extend(self._extract_defs(child, file_path, content))

        return nodes

    def _parse_def_form(
        self,
        node,
        file_path: str,
        content: str,
    ) -> Optional[Node]:
        """Parse a def/defn/defmacro form."""
        # First child should be a symbol
        if not node.children:
            return None

        first_child = node.children[0]
        if first_child.type != "sym_lit":
            return None

        keyword = first_child.text.decode("utf-8")
        if not keyword.startswith("def"):
            return None

        # Second child is the name
        if len(node.children) < 2:
            return None

        name_child = node.children[1]
        if name_child.type != "sym_lit":
            return None

        name = name_child.text.decode("utf-8")
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        kind = {
            "defn": "clj_defn",
            "defmacro": "clj_defmacro",
            "defmulti": "clj_defmulti",
            "defmethod": "clj_defmethod",
        }.get(keyword, "clj_def")

        node_id = Node.compute_id(file_path, kind, name, start_line, keyword)

        return Node(
            id=node_id,
            kind=kind,
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            signature=keyword,
        )

    def _parse_ns_form(
        self,
        node,
        file_path: str,
        content: str,
    ) -> Optional[Node]:
        """Parse a namespace form."""
        if not node.children:
            return None

        first_child = node.children[0]
        if first_child.type != "sym_lit":
            return None

        keyword = first_child.text.decode("utf-8")
        if keyword != "ns":
            return None

        # Second child is the namespace name
        if len(node.children) < 2:
            return None

        ns_child = node.children[1]
        if ns_child.type != "sym_lit":
            return None

        ns_name = ns_child.text.decode("utf-8")
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        node_id = Node.compute_id(file_path, "clj_ns", ns_name, start_line)

        return Node(
            id=node_id,
            kind="clj_ns",
            name=ns_name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            namespace=ns_name,
        )
