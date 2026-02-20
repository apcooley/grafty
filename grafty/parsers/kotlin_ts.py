"""
kotlin_ts.py — Kotlin indexing via Tree-sitter.
Supports: .kt, .kts files
"""
from typing import List, Optional
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_kotlin
except ImportError as e:
    raise ImportError(
        "tree-sitter and tree-sitter-kotlin required."
    ) from e

from ..models import Node


class KotlinParser:
    """Index Kotlin files using Tree-sitter."""

    def __init__(self) -> None:
        self.language = Language(tree_sitter_kotlin.language())
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
            # Kotlin uses class_declaration for class, interface, enum, data class
            kind = self._detect_class_kind(node)
            cls = self._extract_named(node, file_path, kind, parent_id, parent_name)
            if cls:
                nodes.append(cls)
                doc = self._extract_doc(node, file_path, cls)
                if doc:
                    nodes.append(doc)
                # Recurse into class body
                for child in node.children:
                    if child.type == "class_body":
                        for stmt in child.children:
                            self._walk(stmt, file_path, nodes, cls.id, cls.name)

        elif node.type == "object_declaration":
            obj = self._extract_named(node, file_path, "kt_object", parent_id, parent_name)
            if obj:
                nodes.append(obj)
                doc = self._extract_doc(node, file_path, obj)
                if doc:
                    nodes.append(doc)
                for child in node.children:
                    if child.type == "class_body":
                        for stmt in child.children:
                            self._walk(stmt, file_path, nodes, obj.id, obj.name)

        elif node.type == "function_declaration":
            is_method = parent_id is not None
            kind = "kt_method" if is_method else "kt_function"
            func = self._extract_named(node, file_path, kind, parent_id, parent_name)
            if func:
                func.is_method = is_method
                nodes.append(func)
                doc = self._extract_doc(node, file_path, func)
                if doc:
                    nodes.append(doc)

    def _detect_class_kind(self, node) -> str:
        """Determine if class, interface, enum, or data class."""
        for child in node.children:
            if child.type == "interface":
                return "kt_interface"
            if child.type == "modifiers":
                text = child.text.decode("utf-8")
                if "data" in text:
                    return "kt_data_class"
                if "enum" in text:
                    return "kt_enum"
        return "kt_class"

    def _extract_named(self, node, file_path, kind, parent_id, parent_name):
        name = None
        for child in node.children:
            if child.type in ("identifier", "type_identifier", "simple_identifier"):
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

    def _extract_doc(self, ts_node, file_path, parent_node):
        """Extract KDoc (/** ... */) preceding a declaration."""
        prev = ts_node.prev_named_sibling
        if prev and prev.type in ("block_comment", "multiline_comment"):
            text = prev.text.decode("utf-8")
            if text.startswith("/**"):
                start_line = prev.start_point[0] + 1
                end_line = prev.end_point[0] + 1
                node_id = Node.compute_id(
                    file_path, "kt_doc", parent_node.name,
                    start_line, parent_node.qualname,
                )
                return Node(
                    id=node_id, kind="kt_doc", name=parent_node.name,
                    path=file_path, start_line=start_line, end_line=end_line,
                    start_byte=prev.start_byte, end_byte=prev.end_byte,
                    parent_id=parent_node.id, qualname=parent_node.qualname,
                )
        return None
