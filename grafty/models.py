"""
models.py — Core data structures for grafty
"""
from dataclasses import dataclass, field
from typing import Optional, List
from hashlib import sha256


@dataclass
class Node:
    """Structural unit (heading, function, etc.) in a file."""

    id: str  # stable hash(path, kind, name, start_line)
    kind: str  # "md_heading", "py_function", "clj_defn", etc.
    name: str  # heading text, function name, etc.
    path: str  # file path (relative or absolute)
    start_line: int  # 1-indexed
    end_line: int  # 1-indexed, inclusive
    start_byte: Optional[int] = None  # byte offset for precise patching
    end_byte: Optional[int] = None
    parent_id: Optional[str] = None  # for tree structure
    children_ids: List[str] = field(default_factory=list)

    # Extra metadata
    heading_level: Optional[int] = None  # Markdown/Org
    qualname: Optional[str] = None  # Python "Class.method"
    namespace: Optional[str] = None  # Clojure ns
    signature: Optional[str] = None  # Python/Clojure for disambiguation
    is_method: Optional[bool] = None  # Python
    docstring: Optional[str] = None  # first 200 chars if available

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_byte": self.start_byte,
            "end_byte": self.end_byte,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "heading_level": self.heading_level,
            "qualname": self.qualname,
            "namespace": self.namespace,
            "signature": self.signature,
            "is_method": self.is_method,
            "docstring": self.docstring,
        }

    @staticmethod
    def compute_id(
        path: str,
        kind: str,
        name: str,
        start_line: int,
        signature: Optional[str] = None,
    ) -> str:
        """Compute stable node ID via SHA256 hash."""
        content = f"{path}:{kind}:{name}:{start_line}"
        if signature:
            content += f":{signature}"
        return sha256(content.encode()).hexdigest()[:16]


@dataclass
class SelectorResult:
    """Result of a selector resolution (exact or ambiguous)."""

    exact_match: Optional[Node] = None
    candidates: List[Node] = field(default_factory=list)
    error: Optional[str] = None

    def is_resolved(self) -> bool:
        """True if exactly one match."""
        return self.exact_match is not None

    def to_dict(self) -> dict:
        """Convert to JSON."""
        return {
            "exact_match": self.exact_match.to_dict() if self.exact_match else None,
            "candidates": [c.to_dict() for c in self.candidates],
            "error": self.error,
        }


@dataclass
class FileIndex:
    """Index of all nodes in a file."""

    path: str
    content_hash: str  # SHA256 of file content for drift detection
    mtime: float  # file modification time
    nodes: List[Node] = field(default_factory=list)
    nodes_by_id: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to JSON."""
        return {
            "path": self.path,
            "content_hash": self.content_hash,
            "mtime": self.mtime,
            "nodes": [n.to_dict() for n in self.nodes],
        }


@dataclass
class PatchOperation:
    """Represents a file mutation (replace/insert/delete)."""

    kind: str  # "replace", "insert", "delete"
    file_path: str
    start_line: int  # 1-indexed
    end_line: int  # 1-indexed, inclusive
    start_byte: Optional[int] = None
    end_byte: Optional[int] = None
    text: str = ""  # text to insert or replace with

    def to_dict(self) -> dict:
        """Convert to dict."""
        return {
            "kind": self.kind,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_byte": self.start_byte,
            "end_byte": self.end_byte,
            "text": self.text,
        }
