"""
java_ts.py — Java indexing via Tree-sitter.
Supports: .java files
"""
from typing import List, Optional
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_java
except ImportError as e:
    raise ImportError(
        "tree-sitter and tree-sitter-java required. "
        "Install: pip install tree-sitter tree-sitter-java"
    ) from e

from ..models import Node


class JavaParser:
    """Index Java files using Tree-sitter."""

    def __init__(self) -> None:
        self.language = Language(tree_sitter_java.language())
        self.parser = Parser(self.language)

    def parse_file(self, file_path: str) -> List[Node]:
        """Index a Java file and return list of nodes."""
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        try:
            tree = self.parser.parse(content.encode("utf-8"))
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return []

        nodes: List[Node] = []
        self._walk(tree.root_node, file_path, nodes, parent_id=None, parent_name=None)
        return nodes

    def _walk(
        self, node, file_path: str, nodes: List[Node],
        parent_id: Optional[str], parent_name: Optional[str],
    ) -> None:
        """Walk AST extracting classes, interfaces, enums, methods."""
        if node.type == "program":
            for child in node.children:
                self._walk(child, file_path, nodes, None, None)

        elif node.type == "class_declaration":
            cls = self._extract_named(node, file_path, "java_class", parent_id, parent_name)
            if cls:
                nodes.append(cls)
                doc = self._extract_javadoc(node, file_path, cls)
                if doc:
                    nodes.append(doc)
                self._walk_body(node, "class_body", file_path, nodes, cls)

        elif node.type == "interface_declaration":
            iface = self._extract_named(node, file_path, "java_interface", parent_id, parent_name)
            if iface:
                nodes.append(iface)
                doc = self._extract_javadoc(node, file_path, iface)
                if doc:
                    nodes.append(doc)
                self._walk_body(node, "interface_body", file_path, nodes, iface)

        elif node.type == "enum_declaration":
            enum = self._extract_named(node, file_path, "java_enum", parent_id, parent_name)
            if enum:
                nodes.append(enum)
                doc = self._extract_javadoc(node, file_path, enum)
                if doc:
                    nodes.append(doc)

        elif node.type == "method_declaration":
            method = self._extract_named(node, file_path, "java_method", parent_id, parent_name)
            if method:
                method.is_method = True
                nodes.append(method)
                doc = self._extract_javadoc(node, file_path, method)
                if doc:
                    nodes.append(doc)

        elif node.type == "constructor_declaration":
            ctor = self._extract_named(node, file_path, "java_constructor", parent_id, parent_name)
            if ctor:
                ctor.is_method = True
                nodes.append(ctor)
                doc = self._extract_javadoc(node, file_path, ctor)
                if doc:
                    nodes.append(doc)

    def _walk_body(
        self, node, body_type: str, file_path: str,
        nodes: List[Node], parent: Node,
    ) -> None:
        """Recurse into class/interface body."""
        for child in node.children:
            if child.type == body_type:
                for stmt in child.children:
                    self._walk(
                        stmt, file_path, nodes,
                        parent.id, parent.name,
                    )
                break

    def _extract_named(
        self, node, file_path: str, kind: str,
        parent_id: Optional[str], parent_name: Optional[str],
    ) -> Optional[Node]:
        """Extract a named declaration."""
        name = None
        # For methods/constructors, use identifier only (skip type_identifier = return type)
        if kind in ("java_method", "java_constructor"):
            for child in node.children:
                if child.type == "identifier":
                    name = child.text.decode("utf-8")
                    break
        else:
            for child in node.children:
                if child.type in ("identifier", "type_identifier"):
                    name = child.text.decode("utf-8")
                    break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        qualname = f"{parent_name}.{name}" if parent_name else name
        node_id = Node.compute_id(file_path, kind, name, start_line, qualname)

        return Node(
            id=node_id,
            kind=kind,
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            parent_id=parent_id,
            qualname=qualname,
        )

    def _extract_javadoc(
        self, ts_node, file_path: str, parent_node: Node,
    ) -> Optional[Node]:
        """Extract Javadoc comment (/** ... */) preceding a declaration."""
        prev = ts_node.prev_named_sibling
        if prev and prev.type == "block_comment":
            text = prev.text.decode("utf-8")
            if text.startswith("/**"):
                start_line = prev.start_point[0] + 1
                end_line = prev.end_point[0] + 1
                node_id = Node.compute_id(
                    file_path, "java_doc", parent_node.name,
                    start_line, parent_node.qualname,
                )
                return Node(
                    id=node_id,
                    kind="java_doc",
                    name=parent_node.name,
                    path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    start_byte=prev.start_byte,
                    end_byte=prev.end_byte,
                    parent_id=parent_node.id,
                    qualname=parent_node.qualname,
                )
        return None
