"""
org.py — Org-mode indexing via star-based outline parser.
"""
import re
from typing import List
from pathlib import Path

from ..models import Node


class OrgParser:
    """Index Org-mode files using star-based outline parsing."""

    def __init__(self):
        self.heading_pattern = re.compile(r"^\*+\s+")

    def parse_file(self, file_path: str) -> List[Node]:
        """Index an Org-mode file and return list of heading nodes (with preambles)."""
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        lines = content.splitlines()
        nodes: List[Node] = []

        # Scan for headings
        headings: List[tuple] = []  # (line_idx, level, text)

        for i, line in enumerate(lines):
            match = self.heading_pattern.match(line)
            if match:
                level = len(match.group(0)) - len(match.group(0).lstrip("*"))
                text = line[match.end():].strip()
                headings.append((i, level, text))

        # Convert to nodes (compute extents)
        for idx, (line_idx, level, text) in enumerate(headings):
            start_line = line_idx + 1

            # Find extent: next heading of same or higher level (lower or equal star count)
            end_line = len(lines)  # Default: extend to EOF
            for next_idx in range(idx + 1, len(headings)):
                next_line_idx, next_level, _ = headings[next_idx]
                if next_level <= level:
                    # Found a heading of same or higher level; end before it
                    end_line = next_line_idx
                    break

            node_id = Node.compute_id(file_path, "org_heading", text, start_line)

            nodes.append(
                Node(
                    id=node_id,
                    kind="org_heading",
                    name=text,
                    path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    heading_level=level,
                )
            )

        # Build parent-child relationships
        self._build_hierarchy(nodes)

        # Create preamble nodes
        preamble_nodes = self._create_preamble_nodes(nodes, file_path)
        nodes.extend(preamble_nodes)

        return nodes

    def _build_hierarchy(self, nodes: List[Node]) -> None:
        """Build parent-child relationships based on heading levels."""
        for i, node in enumerate(nodes):
            node.parent_id = None
            node.children_ids = []

            # Find parent: previous heading with lower level (fewer stars)
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
            if node.kind == "org_heading" and node.heading_level:
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
                        "org_heading_preamble",
                        node.name,
                        node.start_line,
                    ),
                    kind="org_heading_preamble",
                    name=node.name,
                    path=file_path,
                    start_line=node.start_line,
                    end_line=preamble_end,
                    heading_level=node.heading_level,
                )
                preamble_nodes.append(preamble_node)

        return preamble_nodes
