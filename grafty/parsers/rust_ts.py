"""
rust_ts.py — Rust indexing via Tree-sitter.
Supports: .rs files
"""
from typing import List, Optional, Dict
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_rust
except ImportError as e:
    raise ImportError(
        "tree-sitter and tree-sitter-rust required. "
        "Install: pip install tree-sitter tree-sitter-rust"
    ) from e

from ..models import Node


class RustParser:
    """Index Rust files using Tree-sitter."""

    def __init__(self) -> None:
        self.language = Language(tree_sitter_rust.language())
        self.parser = Parser(self.language)

    def parse_file(self, file_path: str) -> List[Node]:
        """Index a Rust file and return list of nodes."""
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

        if node.type == "source_file":
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

        elif node.type == "struct_item":
            struct_node = self._extract_struct(node, file_path, content)
            if struct_node:
                nodes.append(struct_node)
                nodes_dict[id(node)] = struct_node
                doc = self._extract_doc_comment(node, file_path, struct_node)
                if doc:
                    nodes.append(doc)

        elif node.type == "trait_item":
            trait_node = self._extract_trait(node, file_path, content)
            if trait_node:
                nodes.append(trait_node)
                nodes_dict[id(node)] = trait_node
                doc = self._extract_doc_comment(node, file_path, trait_node)
                if doc:
                    nodes.append(doc)

        elif node.type == "impl_item":
            # Impl block: impl Foo { ... }
            impl_node = self._extract_impl(node, file_path, content)
            if impl_node:
                nodes.append(impl_node)
                nodes_dict[id(node)] = impl_node

                # Recurse into impl block for methods
                for child in node.children:
                    if child.type == "declaration_list":
                        for stmt in child.children:
                            if stmt.type == "function_item":
                                method_node = self._extract_method(
                                    stmt,
                                    file_path,
                                    content,
                                    parent_id=impl_node.id,
                                    parent_qualname=impl_node.name,
                                )
                                if method_node:
                                    nodes.append(method_node)
                                    impl_node.children_ids.append(method_node.id)
                                    doc = self._extract_doc_comment(
                                        stmt, file_path, method_node
                                    )
                                    if doc:
                                        nodes.append(doc)

        elif node.type == "function_item":
            # Function definition: fn foo() { ... }
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
                doc = self._extract_doc_comment(node, file_path, func_node)
                if doc:
                    nodes.append(doc)

        elif node.type == "macro_definition":
            # Macro definition: macro_rules! my_macro { ... }
            macro_node = self._extract_macro(node, file_path, content)
            if macro_node:
                nodes.append(macro_node)

    def _extract_function(
        self,
        node,
        file_path: str,
        content: str,
        parent_id: Optional[str],
        parent_qualname: Optional[str],
    ) -> Optional[Node]:
        """Extract function_item node."""
        # Function name is identifier after 'fn' keyword
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
        node_id = Node.compute_id(file_path, "rs_function", name, start_line, qualname)

        return Node(
            id=node_id,
            kind="rs_function",
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

    def _extract_struct(
        self,
        node,
        file_path: str,
        content: str,
    ) -> Optional[Node]:
        """Extract struct_item node."""
        # Struct name is type_identifier after 'struct' keyword
        name = None
        for child in node.children:
            if child.type == "type_identifier":
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        node_id = Node.compute_id(file_path, "rs_struct", name, start_line)

        return Node(
            id=node_id,
            kind="rs_struct",
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            parent_id=None,
            is_method=False,
        )

    def _extract_trait(
        self,
        node,
        file_path: str,
        content: str,
    ) -> Optional[Node]:
        """Extract trait_item node."""
        # Trait name is type_identifier after 'trait' keyword
        name = None
        for child in node.children:
            if child.type == "type_identifier":
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        node_id = Node.compute_id(file_path, "rs_trait", name, start_line)

        return Node(
            id=node_id,
            kind="rs_trait",
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            parent_id=None,
            is_method=False,
        )

    def _extract_impl(
        self,
        node,
        file_path: str,
        content: str,
    ) -> Optional[Node]:
        """Extract impl_item node."""
        # Impl name: impl Foo or impl Trait for Foo
        # Extract the type name (first identifier or after 'for')
        name = None
        for child in node.children:
            if child.type == "type_identifier":
                name = child.text.decode("utf-8")
                break
            elif child.type == "identifier":
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        node_id = Node.compute_id(file_path, "rs_impl", name, start_line)

        return Node(
            id=node_id,
            kind="rs_impl",
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
        parent_id: Optional[str],
        parent_qualname: Optional[str],
    ) -> Optional[Node]:
        """Extract method from function_item inside impl block."""
        # Method name is identifier after 'fn' keyword
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
        node_id = Node.compute_id(file_path, "rs_method", name, start_line, qualname)

        return Node(
            id=node_id,
            kind="rs_method",
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

    def _extract_macro(
        self,
        node,
        file_path: str,
        content: str,
    ) -> Optional[Node]:
        """Extract macro_definition node."""
        # Macro name: macro_rules! foo { ... }
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        node_id = Node.compute_id(file_path, "rs_macro", name, start_line)

        return Node(
            id=node_id,
            kind="rs_macro",
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            parent_id=None,
            is_method=False,
        )

    def _extract_doc_comment(
        self,
        ts_node,
        file_path: str,
        parent_node: Node,
    ) -> Optional[Node]:
        """Extract Rust doc comments (/// or //!) preceding a declaration."""
        comments = []
        prev = ts_node.prev_named_sibling
        while prev and prev.type == "line_comment":
            text = prev.text.decode("utf-8")
            if text.startswith("///") or text.startswith("//!"):
                comments.insert(0, prev)
                prev = prev.prev_named_sibling
            else:
                break

        if not comments:
            return None

        start_line = comments[0].start_point[0] + 1
        end_line = comments[-1].end_point[0] + 1
        name = parent_node.name
        node_id = Node.compute_id(
            file_path, "rs_doc", name, start_line,
            parent_node.qualname,
        )
        return Node(
            id=node_id,
            kind="rs_doc",
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=comments[0].start_byte,
            end_byte=comments[-1].end_byte,
            parent_id=parent_node.id,
            qualname=parent_node.qualname,
        )
