"""
bash_ts.py — Bash/Shell indexing via Tree-sitter.
Supports: .sh, .bash files
"""
from typing import List, Optional
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_bash
except ImportError as e:
    raise ImportError(
        "tree-sitter and tree-sitter-bash required. "
        "Install: pip install tree-sitter tree-sitter-bash"
    ) from e

from ..models import Node


class BashParser:
    """Index Bash/Shell files using Tree-sitter."""

    def __init__(self) -> None:
        self.language = Language(tree_sitter_bash.language())
        self.parser = Parser(self.language)

    def parse_file(self, file_path: str) -> List[Node]:
        """Index a Bash file and return list of nodes."""
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        try:
            tree = self.parser.parse(content.encode("utf-8"))
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return []

        nodes: List[Node] = []
        for child in tree.root_node.children:
            if child.type == "function_definition":
                func_node = self._extract_function(child, file_path)
                if func_node:
                    nodes.append(func_node)
                    doc = self._extract_doc_comment(child, file_path, func_node)
                    if doc:
                        nodes.append(doc)
        return nodes

    def _extract_function(
        self, node, file_path: str
    ) -> Optional[Node]:
        """Extract function_definition node."""
        name = None
        for child in node.children:
            if child.type == "word":
                name = child.text.decode("utf-8")
                break

        if not name:
            return None

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        node_id = Node.compute_id(file_path, "bash_function", name, start_line)

        return Node(
            id=node_id,
            kind="bash_function",
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
        )

    def _extract_doc_comment(
        self, ts_node, file_path: str, parent_node: Node
    ) -> Optional[Node]:
        """Extract comment block immediately preceding a function."""
        comments = []
        prev = ts_node.prev_named_sibling
        # Walk backwards, collecting only contiguous comment lines
        expected_line = ts_node.start_point[0]  # 0-indexed line before function
        while prev and prev.type == "comment":
            prev_end = prev.end_point[0]
            # Must be contiguous (allow 1 blank line gap max)
            if expected_line - prev_end > 1:
                break
            # Skip shebangs
            text = prev.text.decode("utf-8")
            if text.startswith("#!"):
                break
            comments.insert(0, prev)
            expected_line = prev.start_point[0]
            prev = prev.prev_named_sibling

        if not comments:
            return None

        start_line = comments[0].start_point[0] + 1
        end_line = comments[-1].end_point[0] + 1
        node_id = Node.compute_id(
            file_path, "bash_doc", parent_node.name, start_line
        )
        return Node(
            id=node_id,
            kind="bash_doc",
            name=parent_node.name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=comments[0].start_byte,
            end_byte=comments[-1].end_byte,
            parent_id=parent_node.id,
        )
