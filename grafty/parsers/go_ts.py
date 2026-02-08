"""
go_ts.py — Go indexing via Tree-sitter.
Supports: .go files
"""
from typing import List, Optional, Dict
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_go
except ImportError as e:
    raise ImportError(
        "tree-sitter and tree-sitter-go required. "
        "Install: pip install tree-sitter tree-sitter-go"
    ) from e

from ..models import Node


class GoParser:
    """Index Go files using Tree-sitter."""

    def __init__(self) -> None:
        self.language = Language(tree_sitter_go.language())
        self.parser = Parser(self.language)

    def parse_file(self, file_path: str) -> List[Node]:
        """Index a Go file and return list of nodes."""
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        try:
            tree = self.parser.parse(content.encode("utf-8"))
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return []

        nodes: List[Node] = []

        self._walk_tree(
            tree.root_node,
            file_path,
            content,
            nodes,
            parent_id=None,
        )

        return nodes

    def _walk_tree(
        self,
        node,
        file_path: str,
        content: str,
        nodes: List[Node],
        parent_id: Optional[str],
    ) -> None:
        """Recursively walk Tree-sitter AST, extracting definitions."""

        if node.type == "source_file":
            # Top-level; process children
            for child in node.children:
                self._walk_tree(
                    child,
                    file_path,
                    content,
                    nodes,
                    parent_id=None,
                )

        elif node.type == "package_clause":
            # Package declaration: package main
            pass  # Could extract as go_package node if needed

        elif node.type == "function_declaration":
            # Function definition: func foo() { ... }
            func_node = self._extract_function(node, file_path, content)
            if func_node:
                nodes.append(func_node)

        elif node.type == "method_declaration":
            # Method definition: func (r *Receiver) Method() { ... }
            method_node = self._extract_method(node, file_path, content)
            if method_node:
                nodes.append(method_node)

        elif node.type == "type_declaration":
            # Type declarations: type Foo struct { ... }
            type_nodes = self._extract_type(node, file_path, content)
            nodes.extend(type_nodes)

        # Recurse into children
        for child in node.children:
            if child.type not in (
                "function_declaration",
                "method_declaration",
                "type_declaration",
            ):
                self._walk_tree(
                    child,
                    file_path,
                    content,
                    nodes,
                    parent_id=parent_id,
                )

    def _extract_function(
        self,
        node,
        file_path: str,
        content: str,
    ) -> Optional[Node]:
        """Extract function_declaration node."""
        # Function name follows 'func' keyword
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        node_id = Node.compute_id(file_path, "go_function", name, start_line)

        return Node(
            id=node_id,
            kind="go_function",
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            parent_id=None,
            is_method=False,
        )

    def _extract_method(
        self,
        node,
        file_path: str,
        content: str,
    ) -> Optional[Node]:
        """Extract method_declaration node."""
        # Method name comes after receiver: func (r *Receiver) MethodName() { ... }
        # It can be either identifier or field_identifier
        name = None
        found_receiver = False
        for child in node.children:
            if child.type == "parameter_list":
                found_receiver = True
            elif found_receiver and child.type in ("identifier", "field_identifier"):
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        node_id = Node.compute_id(file_path, "go_method", name, start_line)

        return Node(
            id=node_id,
            kind="go_method",
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            parent_id=None,
            is_method=True,
        )

    def _extract_type(
        self,
        node,
        file_path: str,
        content: str,
    ) -> List[Node]:
        """Extract type_declaration node(s)."""
        # type Foo struct { ... } or type Bar interface { ... }
        nodes: List[Node] = []
        type_spec = None

        for child in node.children:
            if child.type == "type_spec":
                type_spec = child
                break

        if not type_spec:
            return nodes

        # Type name is first type_identifier in type_spec
        name = None
        for child in type_spec.children:
            if child.type == "type_identifier":
                name = child.text.decode("utf-8")
                break

        if not name:
            return nodes

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        node_id = Node.compute_id(file_path, "go_type", name, start_line)

        type_node = Node(
            id=node_id,
            kind="go_type",
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            parent_id=None,
            is_method=False,
        )
        nodes.append(type_node)

        return nodes
