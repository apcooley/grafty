"""
markdown_ts.py — Markdown indexing via Tree-sitter.
"""
from typing import List, Optional
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_markdown
except ImportError as e:
    raise ImportError(
        "tree-sitter and tree-sitter-markdown required. "
        "Install: pip install tree-sitter tree-sitter-markdown"
    ) from e

from ..models import Node


class MarkdownParser:
    """Index Markdown files using Tree-sitter."""

    def __init__(self):
        self.language = Language(tree_sitter_markdown.language())
        self.parser = Parser(self.language)

    def parse_file(self, file_path: str) -> List[Node]:
        """Index a Markdown file and return list of heading nodes (with preambles)."""
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        try:
            tree = self.parser.parse(content.encode("utf-8"))
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return []

        nodes: List[Node] = []
        self._extract_headings(tree.root_node, file_path, content, nodes)

        # Build parent-child relationships
        self._build_hierarchy(nodes)

        # Create preamble nodes
        preamble_nodes = self._create_preamble_nodes(nodes, file_path)
        nodes.extend(preamble_nodes)

        return nodes

    def _extract_headings(
        self,
        node,
        file_path: str,
        content: str,
        nodes: List[Node],
    ) -> None:
        """Recursively extract all headings."""

        # Tree-sitter markdown uses 'atx_heading' nodes (and setext_heading)
        if node.type in ("atx_heading", "setext_heading"):
            # Extra safety: verify the heading is NOT inside a code fence
            if not self._is_inside_code_fence(node):
                heading_node = self._parse_heading(node, file_path, content)
                if heading_node:
                    nodes.append(heading_node)

        # Recurse into children
        for child in node.children:
            self._extract_headings(child, file_path, content, nodes)

    def _parse_heading(
        self,
        node,
        file_path: str,
        content: str,
    ) -> Optional[Node]:
        """Parse a heading node and compute its extent."""

        # Extract heading level and text
        level = self._get_heading_level(node)
        text = self._get_heading_text(node)

        if not text:
            return None

        start_line = node.start_point[0] + 1

        # Compute end_line: next heading of same or higher level, or EOF
        end_line = self._compute_heading_extent(
            content,
            start_line,
            level,
        )

        node_id = Node.compute_id(file_path, "md_heading", text, start_line)

        return Node(
            id=node_id,
            kind="md_heading",
            name=text,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            heading_level=level,
        )

    def _is_inside_code_fence(self, node) -> bool:
        """
        Check if a node is inside a code fence.
        Traverses parent nodes to find fenced_code_block or code_fence.
        """
        current = node.parent
        while current is not None:
            if current.type in ("fenced_code_block", "code_fence"):
                return True
            current = current.parent
        return False

    def _get_heading_level(self, node) -> int:
        """Extract heading level from Tree-sitter heading node."""
        # Look for atx_h1_marker, atx_h2_marker, ..., atx_h6_marker
        for child in node.children:
            if child.type.startswith("atx_h"):
                # Extract level: atx_h2_marker → level 2
                level_str = child.type[5]  # "atx_h2_marker"[5] = "2"
                try:
                    return int(level_str)
                except ValueError:
                    pass

        # Fallback: count # in text
        text = node.text.decode("utf-8")
        for i, char in enumerate(text):
            if char != "#":
                return i + 1

        return 1

    def _get_heading_text(self, node) -> str:
        """Extract heading text (without markers)."""
        # Find the inline node
        for child in node.children:
            if child.type == "inline":
                return child.text.decode("utf-8").strip()

        # Fallback: use full text and strip markers
        text = node.text.decode("utf-8").strip()
        text = text.lstrip("#").rstrip("#").strip()

        return text

    def _compute_heading_extent(
        self,
        content: str,
        start_line: int,
        level: int,
    ) -> int:
        """
        Compute end line of a heading section.
        Extent: from start_line to next heading of same/higher level (or EOF).
        Lines are 1-indexed.
        Properly handles code fences: ignores # lines inside code blocks.
        """
        lines = content.splitlines()
        in_code_fence = False
        fence_delimiter = None

        for i in range(start_line, len(lines)):
            line = lines[i]
            stripped = line.strip()

            # Check for code fence markers (``` or ~~~)
            if stripped.startswith("```") or stripped.startswith("~~~"):
                if not in_code_fence:
                    in_code_fence = True
                    fence_delimiter = stripped[0]  # '`' or '~'
                elif stripped.startswith(fence_delimiter * 3):
                    in_code_fence = False
                    fence_delimiter = None
                # Skip further checks for this line
                continue

            # Only check for headings if NOT inside a code fence
            if not in_code_fence and line.startswith("#"):
                # Count leading #'s
                heading_level = 0
                for char in line:
                    if char == "#":
                        heading_level += 1
                    else:
                        break

                # If same or higher level (lower or equal #'s), this is the boundary
                if heading_level <= level:
                    return i  # (end_line is 1-indexed, inclusive, so return i)

        # No next heading found; extent to EOF
        return len(lines)

    def _build_hierarchy(self, nodes: List[Node]) -> None:
        """Build parent-child relationships based on heading levels."""
        # Sort nodes by line number (should already be sorted)
        for i, node in enumerate(nodes):
            node.parent_id = None
            node.children_ids = []

            # Find parent: previous heading with lower level (fewer #'s)
            for j in range(i - 1, -1, -1):
                potential_parent = nodes[j]
                if (
                    potential_parent.heading_level
                    and node.heading_level
                    and potential_parent.heading_level < node.heading_level
                ):
                    node.parent_id = potential_parent.id
                    potential_parent.children_ids.append(node.id)
                    break

    def _create_preamble_nodes(self, nodes: List[Node], file_path: str) -> List[Node]:
        """Create preamble nodes for each heading."""
        preamble_nodes: List[Node] = []

        for node in nodes:
            if node.kind == "md_heading" and node.heading_level:
                # Compute preamble extent: heading through first child's line - 1
                preamble_end = node.end_line

                if node.children_ids:
                    # Has children: stop before first child
                    first_child_id = node.children_ids[0]
                    first_child = next(n for n in nodes if n.id == first_child_id)
                    preamble_end = first_child.start_line - 1

                preamble_node = Node(
                    id=Node.compute_id(
                        file_path,
                        "md_heading_preamble",
                        node.name,
                        node.start_line,
                    ),
                    kind="md_heading_preamble",
                    name=node.name,
                    path=file_path,
                    start_line=node.start_line,
                    end_line=preamble_end,
                    start_byte=node.start_byte,
                    end_byte=None,  # Not computed for preambles
                    heading_level=node.heading_level,
                )
                preamble_nodes.append(preamble_node)

        return preamble_nodes
