"""
editor.py — File mutation operations (replace, insert, delete).
"""
from typing import Optional

from .models import Node, FileIndex
from .patch import (
    apply_patch_to_buffer,
    generate_unified_diff,
    normalize_newlines,
    read_file_with_hash,
    write_atomic,
    validate_drift,
)


class Editor:
    """Handle file mutations (replace, insert, delete)."""

    def __init__(self, file_index: FileIndex):
        """Initialize with file index."""
        self.file_index = file_index
        self.file_path = file_index.path
        self.original_content, self.content_hash, self.mtime = read_file_with_hash(
            self.file_path
        )
        self.normalized_content, self.newline_mode = normalize_newlines(
            self.original_content
        )
        self.current_content = self.normalized_content

    def replace(
        self,
        node: Node,
        text: str,
    ) -> str:
        """
        Replace node with text.
        Returns modified content (doesn't write to disk).
        """
        # Validate node belongs to this file
        if node.path != self.file_path:
            raise ValueError(
                f"Node {node.id} belongs to {node.path}, not {self.file_path}"
            )

        # Apply operation
        operation = {
            "kind": "replace",
            "start_line": node.start_line,
            "end_line": node.end_line,
            "text": text,
        }

        self.current_content = apply_patch_to_buffer(self.current_content, operation)
        return self.current_content

    def insert(
        self,
        text: str,
        line: Optional[int] = None,
        node: Optional[Node] = None,
        position: str = "after",  # before, after, inside-start, inside-end
    ) -> str:
        """
        Insert text at line or relative to node.
        Returns modified content.
        """
        if line is not None:
            # Insert at absolute line
            operation = {
                "kind": "insert",
                "start_line": line,
                "end_line": line,
                "text": text,
            }
        elif node is not None:
            if node.path != self.file_path:
                raise ValueError(
                    f"Node {node.id} belongs to {node.path}, not {self.file_path}"
                )

            # Insert relative to node
            if position == "before":
                insert_line = node.start_line
            elif position == "after":
                insert_line = node.end_line + 1
            elif position == "inside-start":
                insert_line = node.start_line + 1
            elif position == "inside-end":
                insert_line = node.end_line
            else:
                raise ValueError(f"Unknown position: {position}")

            operation = {
                "kind": "insert",
                "start_line": insert_line,
                "end_line": insert_line,
                "text": text,
            }
        else:
            raise ValueError("Must provide either line or node")

        self.current_content = apply_patch_to_buffer(self.current_content, operation)
        return self.current_content

    def delete(self, node: Node) -> str:
        """
        Delete node.
        Returns modified content.
        """
        if node.path != self.file_path:
            raise ValueError(
                f"Node {node.id} belongs to {node.path}, not {self.file_path}"
            )

        operation = {
            "kind": "delete",
            "start_line": node.start_line,
            "end_line": node.end_line,
            "text": "",
        }

        self.current_content = apply_patch_to_buffer(self.current_content, operation)
        return self.current_content

    def generate_patch(self) -> str:
        """Generate unified diff patch."""
        return generate_unified_diff(
            self.original_content,
            self.current_content,
            self.file_path,
        )

    def reset(self) -> None:
        """Reset to original content."""
        self.current_content = self.normalized_content

    def write(self, force: bool = False, backup: bool = False) -> None:
        """
        Write modified content to disk.
        Validates file drift unless force=True.
        """
        validate_drift(self.file_path, self.content_hash, force=force)

        write_atomic(
            self.file_path,
            self.current_content,
            backup=backup,
            newline_mode=self.newline_mode,
        )
