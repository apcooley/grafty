"""
typescript_ts.py — TypeScript-specific indexing via Tree-sitter.
Supports: .ts, .tsx files (TS-specific nodes: interfaces, type aliases, enums)
Falls back to JavaScriptParser for .js/.jsx.
"""
from typing import List, Optional
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_typescript
except ImportError as e:
    raise ImportError(
        "tree-sitter and tree-sitter-typescript required. "
        "Install: pip install tree-sitter tree-sitter-typescript"
    ) from e

from ..models import Node


class TypeScriptParser:
    """Index TypeScript files using Tree-sitter."""

    def __init__(self) -> None:
        self.language = Language(tree_sitter_typescript.language_typescript())
        self.parser = Parser(self.language)

    def parse_file(self, file_path: str) -> List[Node]:
        """Index a TypeScript file and return list of nodes."""
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        try:
            tree = self.parser.parse(content.encode("utf-8"))
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return []

        nodes: List[Node] = []
        self._walk(tree.root_node, file_path, content, nodes, None, None)
        return nodes

    def _walk(
        self, node, file_path: str, content: str,
        nodes: List[Node],
        parent_id: Optional[str], parent_qualname: Optional[str],
    ) -> None:
        """Walk AST extracting declarations."""
        if node.type == "program":
            for child in node.children:
                self._walk(child, file_path, content, nodes, None, None)

        elif node.type == "function_declaration":
            func = self._extract_named(
                node, file_path, "ts_function", parent_id, parent_qualname
            )
            if func:
                nodes.append(func)
                doc = self._extract_jsdoc(node, file_path, func)
                if doc:
                    nodes.append(doc)

        elif node.type == "class_declaration":
            cls = self._extract_named(
                node, file_path, "ts_class", parent_id, parent_qualname
            )
            if cls:
                nodes.append(cls)
                doc = self._extract_jsdoc(node, file_path, cls)
                if doc:
                    nodes.append(doc)
                # Methods
                for child in node.children:
                    if child.type == "class_body":
                        for stmt in child.children:
                            if stmt.type in (
                                "method_definition",
                                "public_field_definition",
                            ):
                                method = self._extract_method(
                                    stmt, file_path, cls.id, cls.name
                                )
                                if method:
                                    nodes.append(method)
                                    doc = self._extract_jsdoc(stmt, file_path, method)
                                    if doc:
                                        nodes.append(doc)

        elif node.type == "interface_declaration":
            iface = self._extract_named(
                node, file_path, "ts_interface", parent_id, parent_qualname
            )
            if iface:
                nodes.append(iface)
                doc = self._extract_jsdoc(node, file_path, iface)
                if doc:
                    nodes.append(doc)

        elif node.type == "type_alias_declaration":
            alias = self._extract_named(
                node, file_path, "ts_type", parent_id, parent_qualname
            )
            if alias:
                nodes.append(alias)
                doc = self._extract_jsdoc(node, file_path, alias)
                if doc:
                    nodes.append(doc)

        elif node.type == "enum_declaration":
            enum = self._extract_named(
                node, file_path, "ts_enum", parent_id, parent_qualname
            )
            if enum:
                nodes.append(enum)
                doc = self._extract_jsdoc(node, file_path, enum)
                if doc:
                    nodes.append(doc)

        elif node.type == "export_statement":
            for child in node.children:
                self._walk(child, file_path, content, nodes, parent_id, parent_qualname)

    def _extract_named(
        self, node, file_path: str, kind: str,
        parent_id: Optional[str], parent_qualname: Optional[str],
    ) -> Optional[Node]:
        """Extract a named declaration."""
        name = None
        for child in node.children:
            if child.type in ("identifier", "type_identifier"):
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        qualname = f"{parent_qualname}.{name}" if parent_qualname else name
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

    def _extract_method(
        self, node, file_path: str,
        parent_id: str, parent_name: str,
    ) -> Optional[Node]:
        """Extract method from class body."""
        name = None
        for child in node.children:
            if child.type in ("property_identifier", "identifier"):
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        qualname = f"{parent_name}.{name}"
        node_id = Node.compute_id(file_path, "ts_method", name, start_line, qualname)

        return Node(
            id=node_id,
            kind="ts_method",
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            parent_id=parent_id,
            qualname=qualname,
            is_method=True,
        )

    def _extract_jsdoc(
        self, ts_node, file_path: str, parent_node: Node,
    ) -> Optional[Node]:
        """Extract JSDoc/TSDoc comment (/** ... */) preceding a declaration."""
        prev = ts_node.prev_named_sibling
        if prev and prev.type == "comment":
            text = prev.text.decode("utf-8")
            if text.startswith("/**"):
                start_line = prev.start_point[0] + 1
                end_line = prev.end_point[0] + 1
                node_id = Node.compute_id(
                    file_path, "ts_doc", parent_node.name,
                    start_line, parent_node.qualname,
                )
                return Node(
                    id=node_id,
                    kind="ts_doc",
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
