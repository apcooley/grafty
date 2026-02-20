"""
python_ts.py — Python indexing via Tree-sitter.
"""
from typing import List, Optional, Dict
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python
except ImportError as e:
    raise ImportError(
        "tree-sitter and tree-sitter-python required. "
        "Install: pip install tree-sitter tree-sitter-python"
    ) from e

from ..models import Node


class PythonParser:
    """Index Python files using Tree-sitter."""

    def __init__(self):
        self.language = Language(tree_sitter_python.language())
        self.parser = Parser(self.language)

    def parse_file(self, file_path: str) -> List[Node]:
        """Index a Python file and return list of nodes."""
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        try:
            tree = self.parser.parse(content.encode("utf-8"))
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return []

        nodes: List[Node] = []
        nodes_dict: Dict[int, Node] = {}

        self._walk_tree(
            tree.root_node,
            file_path,
            content,
            nodes,
            nodes_dict,
            parent_id=None,
            parent_qualname=None,
        )

        return nodes

    def _walk_tree(
        self,
        node,
        file_path: str,
        content: str,
        nodes: List[Node],
        nodes_dict: Dict[int, Node],
        parent_id: Optional[str],
        parent_qualname: Optional[str],
    ) -> None:
        """Recursively walk Tree-sitter AST, extracting definitions."""

        if node.type == "module":
            # Check for module-level docstring
            stmts = [c for c in node.children if c.type not in ("\n", "comment")]
            if stmts and stmts[0].type == "expression_statement":
                for sub in stmts[0].children:
                    if sub.type == "string":
                        start_line = stmts[0].start_point[0] + 1
                        end_line = stmts[0].end_point[0] + 1
                        node_id = Node.compute_id(
                            file_path, "py_docstring", "__module__", start_line
                        )
                        nodes.append(Node(
                            id=node_id,
                            kind="py_docstring",
                            name="__module__",
                            path=file_path,
                            start_line=start_line,
                            end_line=end_line,
                            start_byte=stmts[0].start_byte,
                            end_byte=stmts[0].end_byte,
                        ))
                        break

            # Top-level; process children
            for child in node.children:
                self._walk_tree(
                    child,
                    file_path,
                    content,
                    nodes,
                    nodes_dict,
                    parent_id=None,
                    parent_qualname=None,
                )

        elif node.type == "class_definition":
            # Class definition
            class_node = self._extract_class(
                node,
                file_path,
                content,
                parent_id=parent_id,
                parent_qualname=parent_qualname,
            )
            if class_node:
                nodes.append(class_node)
                nodes_dict[id(node)] = class_node

                # Extract docstring if present
                doc_node = self._extract_docstring(
                    node, file_path, class_node
                )
                if doc_node:
                    nodes.append(doc_node)

                # Recurse into class body
                for child in node.children:
                    if child.type == "block":
                        for stmt in child.children:
                            self._walk_tree(
                                stmt,
                                file_path,
                                content,
                                nodes,
                                nodes_dict,
                                parent_id=class_node.id,
                                parent_qualname=class_node.qualname or class_node.name,
                            )
                        break

        elif node.type == "function_definition":
            # Function or method
            func_node = self._extract_function(
                node,
                file_path,
                content,
                parent_id=parent_id,
                parent_qualname=parent_qualname,
            )
            if func_node:
                nodes.append(func_node)
                nodes_dict[id(node)] = func_node

                # Extract docstring if present
                doc_node = self._extract_docstring(
                    node, file_path, func_node
                )
                if doc_node:
                    nodes.append(doc_node)

        elif node.type == "decorated_definition":
            # @decorator + def/class
            for child in node.children:
                if child.type in ("function_definition", "class_definition"):
                    self._walk_tree(
                        child,
                        file_path,
                        content,
                        nodes,
                        nodes_dict,
                        parent_id=parent_id,
                        parent_qualname=parent_qualname,
                    )
                    break

    def _extract_class(
        self,
        node,
        file_path: str,
        content: str,
        parent_id: Optional[str],
        parent_qualname: Optional[str],
    ) -> Optional[Node]:
        """Extract class_definition node."""
        # Class name is first identifier child
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        qualname = f"{parent_qualname}.{name}" if parent_qualname else name
        node_id = Node.compute_id(file_path, "py_class", name, start_line, qualname)

        return Node(
            id=node_id,
            kind="py_class",
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            parent_id=parent_id,
            qualname=qualname,
            is_method=False,
        )

    def _extract_function(
        self,
        node,
        file_path: str,
        content: str,
        parent_id: Optional[str],
        parent_qualname: Optional[str],
    ) -> Optional[Node]:
        """Extract function_definition node."""
        # Function name is first identifier after 'def' keyword
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        is_method = parent_qualname is not None
        qualname = f"{parent_qualname}.{name}" if parent_qualname else name

        node_id = Node.compute_id(
            file_path,
            "py_method" if is_method else "py_function",
            name,
            start_line,
            qualname,
        )

        return Node(
            id=node_id,
            kind="py_method" if is_method else "py_function",
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            parent_id=parent_id,
            qualname=qualname,
            is_method=is_method,
        )

    def _extract_docstring(
        self,
        ts_node,
        file_path: str,
        parent_node: Node,
    ) -> Optional[Node]:
        """Extract docstring from a function/class definition's body block."""
        for child in ts_node.children:
            if child.type == "block":
                stmts = [c for c in child.children if c.type not in ("\n", "comment")]
                if stmts and stmts[0].type == "expression_statement":
                    for sub in stmts[0].children:
                        if sub.type == "string":
                            start_line = stmts[0].start_point[0] + 1
                            end_line = stmts[0].end_point[0] + 1
                            name = parent_node.name
                            qualname = parent_node.qualname
                            node_id = Node.compute_id(
                                file_path, "py_docstring", name,
                                start_line, qualname,
                            )
                            return Node(
                                id=node_id,
                                kind="py_docstring",
                                name=name,
                                path=file_path,
                                start_line=start_line,
                                end_line=end_line,
                                start_byte=stmts[0].start_byte,
                                end_byte=stmts[0].end_byte,
                                parent_id=parent_node.id,
                                qualname=qualname,
                            )
                break
        return None
