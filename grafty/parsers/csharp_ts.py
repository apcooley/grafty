"""
csharp_ts.py — C# indexing via Tree-sitter.
Supports: .cs files
"""
from typing import List, Optional
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_c_sharp
except ImportError as e:
    raise ImportError(
        "tree-sitter and tree-sitter-c-sharp required."
    ) from e

from ..models import Node


class CSharpParser:
    """Index C# files using Tree-sitter."""

    def __init__(self) -> None:
        self.language = Language(tree_sitter_c_sharp.language())
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
        if node.type == "compilation_unit":
            for child in node.children:
                self._walk(child, file_path, nodes, None, None)

        elif node.type == "namespace_declaration":
            # Recurse into namespace body
            for child in node.children:
                if child.type == "declaration_list":
                    for stmt in child.children:
                        self._walk(stmt, file_path, nodes, parent_id, parent_name)

        elif node.type == "class_declaration":
            cls = self._extract_named(node, file_path, "cs_class", parent_id, parent_name)
            if cls:
                nodes.append(cls)
                doc = self._extract_doc(node, file_path, cls)
                if doc:
                    nodes.append(doc)
                self._walk_body(node, file_path, nodes, cls)

        elif node.type == "interface_declaration":
            iface = self._extract_named(node, file_path, "cs_interface", parent_id, parent_name)
            if iface:
                nodes.append(iface)
                doc = self._extract_doc(node, file_path, iface)
                if doc:
                    nodes.append(doc)
                self._walk_body(node, file_path, nodes, iface)

        elif node.type == "struct_declaration":
            st = self._extract_named(node, file_path, "cs_struct", parent_id, parent_name)
            if st:
                nodes.append(st)
                doc = self._extract_doc(node, file_path, st)
                if doc:
                    nodes.append(doc)
                self._walk_body(node, file_path, nodes, st)

        elif node.type == "enum_declaration":
            enum = self._extract_named(node, file_path, "cs_enum", parent_id, parent_name)
            if enum:
                nodes.append(enum)
                doc = self._extract_doc(node, file_path, enum)
                if doc:
                    nodes.append(doc)

        elif node.type == "method_declaration":
            method = self._extract_method(node, file_path, parent_id, parent_name)
            if method:
                nodes.append(method)
                doc = self._extract_doc(node, file_path, method)
                if doc:
                    nodes.append(doc)

        elif node.type == "constructor_declaration":
            ctor = self._extract_named(node, file_path, "cs_constructor", parent_id, parent_name)
            if ctor:
                ctor.is_method = True
                nodes.append(ctor)

        elif node.type == "property_declaration":
            prop = self._extract_method(node, file_path, parent_id, parent_name, kind="cs_property")
            if prop:
                nodes.append(prop)

    def _walk_body(self, node, file_path, nodes, parent):
        for child in node.children:
            if child.type == "declaration_list":
                for stmt in child.children:
                    self._walk(stmt, file_path, nodes, parent.id, parent.name)
                break

    def _extract_named(self, node, file_path, kind, parent_id, parent_name):
        name = None
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
            id=node_id, kind=kind, name=name, path=file_path,
            start_line=start_line, end_line=end_line,
            start_byte=node.start_byte, end_byte=node.end_byte,
            parent_id=parent_id, qualname=qualname,
        )

    def _extract_method(self, node, file_path, parent_id, parent_name, kind="cs_method"):
        """Extract method — skip return type, get identifier."""
        name = None
        found_type = False
        for child in node.children:
            if child.type in ("predefined_type", "type_identifier",
                              "generic_name", "nullable_type", "array_type",
                              "void_keyword"):
                found_type = True
            elif found_type and child.type == "identifier":
                name = child.text.decode("utf-8")
                break
            elif not found_type and child.type == "identifier":
                # Could be the name if no explicit return type visible
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
            parent_id=parent_id, qualname=qualname, is_method=True,
        )

    def _extract_doc(self, ts_node, file_path, parent_node):
        """Extract XML doc comment (///) preceding a declaration."""
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
            file_path, "cs_doc", parent_node.name,
            start_line, parent_node.qualname,
        )
        return Node(
            id=node_id, kind="cs_doc", name=parent_node.name,
            path=file_path, start_line=start_line, end_line=end_line,
            start_byte=comments[0].start_byte,
            end_byte=comments[-1].end_byte,
            parent_id=parent_node.id, qualname=parent_node.qualname,
        )
