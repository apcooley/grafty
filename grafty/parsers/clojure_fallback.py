"""
clojure_fallback.py — Fallback balanced-paren scanner for Clojure.
"""
from typing import List, Optional, Tuple
from pathlib import Path

from ..models import Node


class ClojureFallbackParser:
    """Fallback Clojure parser using balanced-paren scanning."""

    def __init__(self):
        pass

    def parse_file(self, file_path: str) -> List[Node]:
        """Index a Clojure file using balanced-paren scanning."""
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        nodes: List[Node] = []
        i = 0

        while i < len(content):
            # Look for opening paren
            if content[i] == "(":
                # Try to parse form
                form_text, form_start, form_end = self._scan_form(content, i)
                if form_text:
                    form_lines = self._get_form_lines(content, form_start, form_end)
                    start_line, end_line = form_lines

                    # Try to extract def/ns
                    def_node = self._parse_form(
                        form_text,
                        file_path,
                        start_line,
                        end_line,
                        form_start,
                        form_end,
                    )
                    if def_node:
                        nodes.append(def_node)

                    i = form_end
                else:
                    i += 1
            else:
                i += 1

        return nodes

    def _scan_form(self, content: str, start: int) -> Tuple[str, int, int]:
        """
        Scan a balanced-paren form starting at position `start`.
        Returns (form_text, start_pos, end_pos).
        """
        if start >= len(content) or content[start] != "(":
            return "", start, start

        depth = 0
        in_string = False
        escape = False
        i = start

        while i < len(content):
            char = content[i]

            # Handle strings
            if char == '"' and not escape:
                in_string = not in_string

            # Handle escapes
            if char == "\\" and in_string:
                escape = not escape
            else:
                escape = False

            # Count parens only outside strings
            if not in_string:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        # Found closing paren
                        form_text = content[start:i + 1]
                        return form_text, start, i + 1

            i += 1

        # Unclosed form
        return "", start, start

    def _get_form_lines(self, content: str, start: int, end: int) -> Tuple[int, int]:
        """Get line numbers (1-indexed) for byte range [start:end)."""
        start_line = content[:start].count("\n") + 1
        end_line = content[:end].count("\n") + 1
        return start_line, end_line

    def _parse_form(
        self,
        form_text: str,
        file_path: str,
        start_line: int,
        end_line: int,
        start_byte: int,
        end_byte: int,
    ) -> Optional[Node]:
        """Parse a form and extract name/kind if it's a def/ns."""
        # Remove outer parens and whitespace
        inner = form_text[1:-1].strip()
        if not inner:
            return None

        # Split by whitespace (first token is keyword)
        tokens = inner.split(None, 1)
        if len(tokens) < 2:
            return None

        keyword, rest = tokens[0], tokens[1]

        # Check if it's a def-like form
        if not keyword.startswith("def") and keyword != "ns":
            return None

        # Extract name (first token in rest)
        name_tokens = rest.split(None, 1)
        if not name_tokens:
            return None

        name = name_tokens[0]

        kind = {
            "defn": "clj_defn",
            "defmacro": "clj_defmacro",
            "defmulti": "clj_defmulti",
            "defmethod": "clj_defmethod",
            "ns": "clj_ns",
        }.get(keyword, "clj_def")

        node_id = Node.compute_id(file_path, kind, name, start_line, keyword)

        node = Node(
            id=node_id,
            kind=kind,
            name=name,
            path=file_path,
            start_line=start_line,
            end_line=end_line,
            start_byte=start_byte,
            end_byte=end_byte,
            signature=keyword,
        )

        if kind == "clj_ns":
            node.namespace = name

        return node
