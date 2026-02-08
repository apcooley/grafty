"""
indexer.py — File discovery and indexing.
"""
from typing import List, Dict, Optional

from .models import FileIndex
from .patch import read_file_with_hash
from .utils import detect_file_type, find_files
from .parsers import (
    PythonParser,
    MarkdownParser,
    OrgParser,
    ClojureParser,
    JavaScriptParser,
    GoParser,
    RustParser,
)


class Indexer:
    """Multi-file indexer using appropriate parsers."""

    def __init__(self):
        self.parsers = {
            "python": PythonParser(),
            "markdown": MarkdownParser(),
            "orgmode": OrgParser(),
            "clojure": ClojureParser(),
            "clojurescript": ClojureParser(),
            "javascript": JavaScriptParser(),
            "go": GoParser(),
            "rust": RustParser(),
        }

    def index_file(self, file_path: str) -> FileIndex:
        """Index a single file."""
        file_type = detect_file_type(file_path)

        if not file_type:
            # Unknown type; return empty index
            content, hash_val, mtime = read_file_with_hash(file_path)
            return FileIndex(
                path=file_path,
                content_hash=hash_val,
                mtime=mtime,
                nodes=[],
            )

        parser = self.parsers.get(file_type)
        if not parser:
            # No parser for this type
            content, hash_val, mtime = read_file_with_hash(file_path)
            return FileIndex(
                path=file_path,
                content_hash=hash_val,
                mtime=mtime,
                nodes=[],
            )

        content, hash_val, mtime = read_file_with_hash(file_path)

        # Parse file
        nodes = parser.parse_file(file_path)

        # Build node lookup
        nodes_by_id = {node.id: node for node in nodes}

        return FileIndex(
            path=file_path,
            content_hash=hash_val,
            mtime=mtime,
            nodes=nodes,
            nodes_by_id=nodes_by_id,
        )

    def index_files(self, paths: List[str]) -> Dict[str, FileIndex]:
        """Index multiple files."""
        indices: Dict[str, FileIndex] = {}

        for path in paths:
            try:
                indices[path] = self.index_file(path)
            except Exception as e:
                print(f"Error indexing {path}: {e}")

        return indices

    def index_directory(
        self,
        root: str,
        extensions: Optional[List[str]] = None,
    ) -> Dict[str, FileIndex]:
        """Index all matching files in a directory."""
        files = find_files(root, extensions)
        return self.index_files(files)
