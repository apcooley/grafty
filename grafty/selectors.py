"""
selectors.py — Selector resolution and tree navigation.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import fnmatch

from .models import Node, SelectorResult, FileIndex


@dataclass
class LineNumberSelector:
    """Represents a line number selector (file.py:42 or file.py:42-50)."""

    file_path: str
    start_line: int
    end_line: int

    @staticmethod
    def parse(selector: str) -> Optional["LineNumberSelector"]:
        """
        Parse a line number selector.
        Formats:
          - file.py:42 (single line)
          - file.py:42-50 (range)

        Returns None if not a valid line selector.
        Must have exactly ONE colon to distinguish from path:kind:name format.
        """
        if selector.count(":") != 1:
            # Only accept selectors with exactly one colon
            return None

        file_path, line_spec = selector.rsplit(":", 1)

        # line_spec must be digits or digits-digits
        if "-" in line_spec:
            parts = line_spec.split("-", 1)
            if len(parts) != 2:
                return None
            if not (parts[0].isdigit() and parts[1].isdigit()):
                return None
            try:
                start_line = int(parts[0])
                end_line = int(parts[1])
                if start_line <= 0 or end_line <= 0:
                    return None
                return LineNumberSelector(file_path, start_line, end_line)
            except ValueError:
                return None
        else:
            if not line_spec.isdigit():
                return None
            try:
                line_num = int(line_spec)
                if line_num <= 0:
                    return None
                return LineNumberSelector(file_path, line_num, line_num)
            except ValueError:
                return None


class Resolver:
    """Resolve selectors to nodes."""

    def __init__(self, indices: Dict[str, FileIndex]):
        """Initialize with indexed files."""
        self.indices = indices
        self._build_lookup()

    def _build_lookup(self) -> None:
        """Build global node lookup."""
        self.nodes_by_id: Dict[str, Node] = {}
        self.nodes_by_kind: Dict[str, List[Node]] = {}
        self.nodes_by_path: Dict[str, List[Node]] = {}

        for file_index in self.indices.values():
            for node in file_index.nodes:
                self.nodes_by_id[node.id] = node

                if node.kind not in self.nodes_by_kind:
                    self.nodes_by_kind[node.kind] = []
                self.nodes_by_kind[node.kind].append(node)

                if node.path not in self.nodes_by_path:
                    self.nodes_by_path[node.path] = []
                self.nodes_by_path[node.path].append(node)

    def resolve(self, selector: str) -> SelectorResult:
        """
        Resolve a selector string to a node.
        Formats:
          1. "<id>" — by node ID
          2. "path/to/file.py:py_function:my_func" — by path, kind, name
          3. "path/to/file.py:42-50" or "path/to/file.py:42" — by line numbers (Phase 3)
          4. "my_func" — fuzzy name search
        Returns SelectorResult with exact_match or candidates.
        """
        # Try by ID
        if selector in self.nodes_by_id:
            return SelectorResult(exact_match=self.nodes_by_id[selector])

        # Try line number format (Phase 3)
        line_sel = LineNumberSelector.parse(selector)
        if line_sel is not None:
            result = self._resolve_by_line_numbers(
                line_sel.file_path, line_sel.start_line, line_sel.end_line
            )
            if result.is_resolved() or result.candidates:
                return result

        # Try path:kind:name format
        if ":" in selector:
            parts = selector.split(":", 2)
            if len(parts) == 3:
                path, kind, name = parts
                result = self._resolve_by_path_kind_name(path, kind, name)
                if result.is_resolved() or result.candidates:
                    return result

        # Try fuzzy name search
        return self._resolve_fuzzy(selector)

    def _normalize_path(self, path: str) -> str:
        """Normalize a path by expanding tilde and resolving to absolute."""
        return str(Path(path).expanduser().resolve())

    def _resolve_by_path_kind_name(
        self,
        path: str,
        kind: str,
        name: str,
    ) -> SelectorResult:
        """Resolve by exact path, kind, name (supports nested paths like Parent/Child)."""
        candidates = []

        # Handle nested paths (e.g., "Wardrobe/JSON parse")
        name_parts = name.split("/")
        is_nested = len(name_parts) > 1

        # Try exact match first
        if path in self.nodes_by_path:
            for node in self.nodes_by_path[path]:
                if node.kind == kind:
                    if is_nested:
                        # Match nested path
                        if self._matches_nested_path(node, name_parts):
                            candidates.append(node)
                    else:
                        # Simple name match
                        if node.name == name:
                            candidates.append(node)

        # If no match, try with normalized paths (tilde expansion, absolute resolution)
        if not candidates:
            normalized_path = self._normalize_path(path)
            for indexed_path, nodes in self.nodes_by_path.items():
                if self._normalize_path(indexed_path) == normalized_path:
                    for node in nodes:
                        if node.kind == kind:
                            if is_nested:
                                if self._matches_nested_path(node, name_parts):
                                    candidates.append(node)
                            else:
                                if node.name == name:
                                    candidates.append(node)

        if len(candidates) == 1:
            return SelectorResult(exact_match=candidates[0])
        elif candidates:
            return SelectorResult(candidates=candidates)
        else:
            return SelectorResult(
                error=f"No node found: path={path}, kind={kind}, name={name}"
            )

    def _matches_nested_path(self, node: Node, name_parts: list) -> bool:
        """Check if node matches a nested path like ['Wardrobe', 'JSON parse']."""
        # Build path from node upwards to root
        path = [node.name]
        current = node
        
        while current.parent_id:
            parent = self.nodes_by_id.get(current.parent_id)
            if parent:
                path.insert(0, parent.name)
                current = parent
            else:
                break
        
        # Check if path ends with name_parts
        return path[-len(name_parts):] == name_parts

    def _resolve_by_line_numbers(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
    ) -> SelectorResult:
        """Resolve by line numbers (Phase 3)."""
        # Find nodes that overlap with the specified line range
        candidates = []

        # Try exact match first
        for node in self.nodes_by_path.get(file_path, []):
            # Check if node overlaps with or is contained in the line range
            if node.start_line >= start_line and node.end_line <= end_line:
                candidates.append(node)

        # If no match, try with normalized paths (tilde expansion)
        if not candidates:
            normalized_path = self._normalize_path(file_path)
            for indexed_path, nodes in self.nodes_by_path.items():
                if self._normalize_path(indexed_path) == normalized_path:
                    for node in nodes:
                        if node.start_line >= start_line and node.end_line <= end_line:
                            candidates.append(node)

        if len(candidates) == 1:
            return SelectorResult(exact_match=candidates[0])
        elif candidates:
            # Sort by specificity (smallest nodes first)
            candidates.sort(key=lambda n: n.end_line - n.start_line)
            return SelectorResult(candidates=candidates)
        else:
            # If no exact match, return error with helpful context
            available_nodes = self.nodes_by_path.get(file_path, [])
            if not available_nodes:
                # Try normalized path lookup
                normalized_path = self._normalize_path(file_path)
                for indexed_path, nodes in self.nodes_by_path.items():
                    if self._normalize_path(indexed_path) == normalized_path:
                        available_nodes = nodes
                        break

            if available_nodes:
                nodes_str = ", ".join(
                    f"{n.name} ({n.start_line}-{n.end_line})"
                    for n in available_nodes[:3]
                )
                return SelectorResult(
                    error=f"No node found in {file_path} lines {start_line}-"
                          f"{end_line}. Available: {nodes_str}"
                )
            else:
                return SelectorResult(error=f"File not indexed: {file_path}")

    def _resolve_fuzzy(self, name: str) -> SelectorResult:
        """Fuzzy name search with improved error messages (Phase 3)."""
        candidates = []
        scores = []

        for node in self.nodes_by_id.values():
            # Match by name
            if node.name == name:
                candidates.append(node)
                scores.append(1.0)
            else:
                # Fuzzy score
                ratio = SequenceMatcher(None, node.name, name).ratio()
                if ratio > 0.6:
                    candidates.append(node)
                    scores.append(ratio)

        # Sort by score (descending) using index to avoid comparing nodes
        if scores:
            sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            candidates = [candidates[i] for i in sorted_indices]

        if len(candidates) == 1:
            return SelectorResult(exact_match=candidates[0])
        elif candidates:
            return SelectorResult(candidates=candidates[:10])  # Top 10
        else:
            # Improved error message (Phase 3)
            return SelectorResult(
                error=f"No node found matching: '{name}'. "
                      f"Try using fuzzy patterns (*validate*) or path:kind:name format."
            )

    def resolve_interactive(self, selector: str) -> Optional[Node]:
        """
        Resolve selector and return the node, or None if ambiguous/not found.
        In interactive mode, the CLI would ask user to disambiguate.
        """
        result = self.resolve(selector)
        if result.exact_match:
            return result.exact_match
        return None

    def query_nodes_by_pattern(self, pattern: str) -> List[Node]:
        """
        Query nodes by glob pattern (Phase 3.3).
        Supports wildcards: *validate*, test_*, *_test, etc.

        Returns list of matching nodes sorted by name.
        """
        matches = []
        for node in self.nodes_by_id.values():
            if fnmatch.fnmatch(node.name, pattern):
                matches.append(node)

        # Sort by name for consistent results
        matches.sort(key=lambda n: n.name)
        return matches

    def query_nodes_by_path_glob(self, selector: str) -> List[Node]:
        """
        Query nodes by path glob pattern (Phase 3.3).
        Format: "src/:py_function:*validate*"
        Supports file path globs and node name patterns.

        Returns list of matching nodes.
        """
        # Parse selector: path:kind:pattern or path:kind or path
        if ":" not in selector:
            # Just a path glob
            path_pattern = selector
            return [n for path, nodes in self.nodes_by_path.items()
                    for n in nodes if fnmatch.fnmatch(path, path_pattern)]

        parts = selector.split(":", 2)

        if len(parts) == 2:
            # path:kind
            path_pattern, kind = parts
            matches = []
            for path, nodes in self.nodes_by_path.items():
                if fnmatch.fnmatch(path, path_pattern):
                    for node in nodes:
                        if node.kind == kind or fnmatch.fnmatch(node.kind, kind):
                            matches.append(node)
            return matches

        elif len(parts) == 3:
            # path:kind:name_pattern
            path_pattern, kind, name_pattern = parts
            matches = []
            for path, nodes in self.nodes_by_path.items():
                if fnmatch.fnmatch(path, path_pattern):
                    for node in nodes:
                        if (node.kind == kind or fnmatch.fnmatch(node.kind, kind)) and \
                           fnmatch.fnmatch(node.name, name_pattern):
                            matches.append(node)
            return matches

        return []

    def get_tree_path(self, node: Node) -> List[Node]:
        """Get path from root to node (ancestry chain)."""
        path = [node]
        current = node

        while current.parent_id:
            parent = self.nodes_by_id.get(current.parent_id)
            if parent:
                path.insert(0, parent)
                current = parent
            else:
                break

        return path

    def get_children(self, node: Node) -> List[Node]:
        """Get direct children of a node."""
        children = []
        for child_id in node.children_ids:
            child = self.nodes_by_id.get(child_id)
            if child:
                children.append(child)
        return children

    def get_subtree(self, node: Node) -> List[Node]:
        """Get all descendants of a node (DFS)."""
        result = [node]
        for child in self.get_children(node):
            result.extend(self.get_subtree(child))
        return result
