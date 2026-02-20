"""
javascript_ts.py — JavaScript/TypeScript indexing via Tree-sitter.
Supports: .js, .ts, .jsx, .tsx files
"""
from typing import List, Optional, Dict
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript
except ImportError as e:
    raise ImportError(
        "tree-sitter and tree-sitter-javascript required. "
        "Install: pip install tree-sitter tree-sitter-javascript"
    ) from e

from ..models import Node


class JavaScriptParser:
    """Index JavaScript/TypeScript files using Tree-sitter."""

    def __init__(self) -> None:
        self.language = Language(tree_sitter_javascript.language())
        self.parser = Parser(self.language)

    def parse_file(self, file_path: str) -> List[Node]:
        """Index a JavaScript/TypeScript file and return list of nodes."""
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

        if node.type == "program":
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

        elif node.type == "class_declaration":
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

                # Check for JSDoc comment
                jsdoc = self._extract_jsdoc(node, file_path, class_node)
                if jsdoc:
                    nodes.append(jsdoc)

                # Recurse into class body for methods
                for child in node.children:
                    if child.type == "class_body":
                        for stmt in child.children:
                            if stmt.type == "method_definition":
                                method_node = self._extract_method(
                                    stmt,
                                    file_path,
                                    content,
                                    parent_id=class_node.id,
                                    parent_qualname=class_node.name,
                                )
                                if method_node:
                                    nodes.append(method_node)
                                    class_node.children_ids.append(method_node.id)

                                    jsdoc = self._extract_jsdoc(
                                        stmt, file_path, method_node
                                    )
                                    if jsdoc:
                                        nodes.append(jsdoc)

        elif node.type == "function_declaration":
            # Function definition
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

                # Check for JSDoc comment
                jsdoc = self._extract_jsdoc(node, file_path, func_node)
                if jsdoc:
                    nodes.append(jsdoc)

        elif node.type == "export_statement":
            # export function foo() { ... } or export class Bar { ... }
            for child in node.children:
                if child.type in ("function_declaration", "class_declaration"):
                    self._walk_tree(
                        child,
                        file_path,
                        content,
                        nodes,
                        nodes_dict,
                        parent_id=parent_id,
                        parent_qualname=parent_qualname,
                    )

    def _extract_function(
        self,
        node,
        file_path: str,
        content: str,
        parent_id: Optional[str],
        parent_qualname: Optional[str],
    ) -> Optional[Node]:
        """Extract function_declaration node."""
        # Function name is identifier after 'function' keyword
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
        node_id = Node.compute_id(file_path, "js_function", name, start_line, qualname)

        return Node(
            id=node_id,
            kind="js_function",
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

    def _extract_class(
        self,
        node,
        file_path: str,
        content: str,
        parent_id: Optional[str],
        parent_qualname: Optional[str],
    ) -> Optional[Node]:
        """Extract class_declaration node."""
        # Class name is identifier after 'class' keyword
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
        node_id = Node.compute_id(file_path, "js_class", name, start_line, qualname)

        return Node(
            id=node_id,
            kind="js_class",
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

    def _extract_method(
        self,
        node,
        file_path: str,
        content: str,
        parent_id: Optional[str],
        parent_qualname: Optional[str],
    ) -> Optional[Node]:
        """Extract method_definition node (method in class)."""
        # Method name is property_identifier or computed_property_name
        name = None
        for child in node.children:
            if child.type in ("property_identifier", "identifier"):
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        qualname = f"{parent_qualname}.{name}" if parent_qualname else name
        node_id = Node.compute_id(file_path, "js_method", name, start_line, qualname)

        return Node(
            id=node_id,
            kind="js_method",
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
        self,
        ts_node,
        file_path: str,
        parent_node: Node,
    ) -> Optional[Node]:
        """Extract JSDoc comment (/** ... */) preceding a declaration."""
        prev = ts_node.prev_named_sibling
        if prev and prev.type == "comment":
            text = prev.text.decode("utf-8")
            if text.startswith("/**"):
                start_line = prev.start_point[0] + 1
                end_line = prev.end_point[0] + 1
                name = parent_node.name
                node_id = Node.compute_id(
                    file_path, "js_jsdoc", name, start_line,
                    parent_node.qualname,
                )
                return Node(
                    id=node_id,
                    kind="js_jsdoc",
                    name=name,
                    path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    start_byte=prev.start_byte,
                    end_byte=prev.end_byte,
                    parent_id=parent_node.id,
                    qualname=parent_node.qualname,
                )
        return None
