"""
swift_ts.py — Swift indexing via Tree-sitter.
Supports: .swift files
"""
from typing import List, Optional
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_swift
except ImportError as e:
    raise ImportError(
        "tree-sitter and tree-sitter-swift required."
    ) from e

from ..models import Node


class SwiftParser:
    """Index Swift files using Tree-sitter."""

    def __init__(self) -> None:
        self.language = Language(tree_sitter_swift.language())
        self.parser = Parser(self.language)

    def parse_file(self, file_path: str) -> List[Node]:
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")
        try:
            tree = self.parser.parse(content.encode("utf-8"))
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return []

        nodes: List[Node] = []
        self._walk(tree.root_node, file_path, nodes, None, None)
        return nodes

    def _walk(
        self, node, file_path: str, nodes: List[Node],
        parent_id: Optional[str], parent_name: Optional[str],
    ) -> None:
        if node.type == "source_file":
            for child in node.children:
                self._walk(child, file_path, nodes, None, None)

        elif node.type == "class_declaration":
            # Swift uses class_declaration for class, struct, enum
            kind = self._detect_kind(node)
            cls = self._extract_named(node, file_path, kind, parent_id, parent_name)
            if cls:
                nodes.append(cls)
                doc = self._extract_doc(node, file_path, cls)
                if doc:
                    nodes.append(doc)
                self._walk_body(node, file_path, nodes, cls)

        elif node.type == "protocol_declaration":
            proto = self._extract_named(node, file_path, "swift_protocol", parent_id, parent_name)
            if proto:
                nodes.append(proto)
                doc = self._extract_doc(node, file_path, proto)
                if doc:
                    nodes.append(doc)
                self._walk_body(node, file_path, nodes, proto)

        elif node.type == "function_declaration":
            is_method = parent_id is not None
            kind = "swift_method" if is_method else "swift_function"
            func = self._extract_func(node, file_path, kind, parent_id, parent_name)
            if func:
                func.is_method = is_method
                nodes.append(func)
                doc = self._extract_doc(node, file_path, func)
                if doc:
                    nodes.append(doc)

    def _detect_kind(self, node) -> str:
        """Detect class vs struct vs enum."""
        for child in node.children:
            if child.type == "struct":
                return "swift_struct"
            if child.type == "enum":
                return "swift_enum"
        return "swift_class"

    def _walk_body(self, node, file_path, nodes, parent):
        for child in node.children:
            if child.type in ("class_body", "protocol_body", "enum_class_body"):
                for stmt in child.children:
                    self._walk(stmt, file_path, nodes, parent.id, parent.name)
                return

    def _extract_named(self, node, file_path, kind, parent_id, parent_name):
        name = None
        for child in node.children:
            if child.type in ("type_identifier", "identifier", "simple_identifier"):
                name = child.text.decode("utf-8")
                break
        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        qualname = f"{parent_name}.{name}" if parent_name else name
        node_id = Node.compute_id(file_path, kind, name, start_line, qualname)
        return Node(
            id=node_id, kind=kind, name=name, path=file_path,
            start_line=start_line, end_line=end_line,
            start_byte=node.start_byte, end_byte=node.end_byte,
            parent_id=parent_id, qualname=qualname,
        )

    def _extract_func(self, node, file_path, kind, parent_id, parent_name):
        """Extract function — name is simple_identifier after 'func'."""
        name = None
        found_func = False
        for child in node.children:
            if child.type == "func":
                found_func = True
            elif found_func and child.type == "simple_identifier":
                name = child.text.decode("utf-8")
                break
        if not name:
            # Fallback
            return self._extract_named(node, file_path, kind, parent_id, parent_name)

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        qualname = f"{parent_name}.{name}" if parent_name else name
        node_id = Node.compute_id(file_path, kind, name, start_line, qualname)
        return Node(
            id=node_id, kind=kind, name=name, path=file_path,
            start_line=start_line, end_line=end_line,
            start_byte=node.start_byte, end_byte=node.end_byte,
            parent_id=parent_id, qualname=qualname,
        )

    def _extract_doc(self, ts_node, file_path, parent_node):
        """Extract /// doc comment block preceding a declaration."""
        comments = []
        prev = ts_node.prev_named_sibling
        while prev and prev.type == "comment":
            text = prev.text.decode("utf-8")
            if text.startswith("///"):
                comments.insert(0, prev)
                prev = prev.prev_named_sibling
            else:
                break
        if not comments:
            return None

        start_line = comments[0].start_point[0] + 1
        end_line = comments[-1].end_point[0] + 1
        node_id = Node.compute_id(
            file_path, "swift_doc", parent_node.name,
            start_line, parent_node.qualname,
        )
        return Node(
            id=node_id, kind="swift_doc", name=parent_node.name,
            path=file_path, start_line=start_line, end_line=end_line,
            start_byte=comments[0].start_byte,
            end_byte=comments[-1].end_byte,
            parent_id=parent_node.id, qualname=parent_node.qualname,
        )
