"""
selectors.py — Selector resolution and tree navigation.
"""
from typing import List, Dict, Optional
from difflib import SequenceMatcher

from .models import Node, SelectorResult, FileIndex


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
          3. "my_func" — fuzzy name search
        Returns SelectorResult with exact_match or candidates.
        """
        # Try by ID
        if selector in self.nodes_by_id:
            return SelectorResult(exact_match=self.nodes_by_id[selector])

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

    def _resolve_by_path_kind_name(
        self,
        path: str,
        kind: str,
        name: str,
    ) -> SelectorResult:
        """Resolve by exact path, kind, name."""
        candidates = []

        # Normalize path (handle both relative and absolute)
        for node in self.nodes_by_path.get(path, []):
            if node.kind == kind and node.name == name:
                candidates.append(node)

        if len(candidates) == 1:
            return SelectorResult(exact_match=candidates[0])
        elif candidates:
            return SelectorResult(candidates=candidates)
        else:
            return SelectorResult(
                error=f"No node found: path={path}, kind={kind}, name={name}"
            )

    def _resolve_fuzzy(self, name: str) -> SelectorResult:
        """Fuzzy name search."""
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
            return SelectorResult(error=f"No node found matching: {name}")

    def resolve_interactive(self, selector: str) -> Optional[Node]:
        """
        Resolve selector and return the node, or None if ambiguous/not found.
        In interactive mode, the CLI would ask user to disambiguate.
        """
        result = self.resolve(selector)
        if result.exact_match:
            return result.exact_match
        return None

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
