"""
utils.py — Shared utilities for parsing and file handling.
"""
from pathlib import Path
from typing import List, Tuple, Optional


def compute_line_byte_map(content: str) -> Tuple[List[int], List[int]]:
    """
    Compute line → byte offset and byte → line offset mappings.
    Returns (line_starts, byte_to_line).
    """
    line_starts: List[int] = [0]
    byte_to_line: List[int] = [0]

    for i, char in enumerate(content):
        byte_to_line.append(len(line_starts) - 1)
        if char == "\n":
            line_starts.append(i + 1)

    return line_starts, byte_to_line


def byte_to_line_col(content: str, byte_offset: int) -> Tuple[int, int]:
    """Convert byte offset to (line, column). Lines/columns are 1-indexed."""
    if byte_offset < 0 or byte_offset > len(content):
        raise ValueError(f"Byte offset {byte_offset} out of range")

    line = 1
    col = 1
    for i in range(byte_offset):
        if content[i] == "\n":
            line += 1
            col = 1
        else:
            col += 1

    return line, col


def byte_range_to_lines(
    content: str,
    start_byte: int,
    end_byte: int,
) -> Tuple[int, int]:
    """
    Convert byte range to line range (1-indexed, inclusive end).
    """
    start_line, _ = byte_to_line_col(content, start_byte)
    end_line, _ = byte_to_line_col(content, min(end_byte, len(content) - 1))
    return start_line, end_line


def get_text_range(content: str, start_byte: int, end_byte: int) -> str:
    """Extract text between byte offsets."""
    return content[start_byte:end_byte]


def get_line_range(content: str, start_line: int, end_line: int) -> str:
    """Extract text between line numbers (1-indexed, inclusive)."""
    lines = content.splitlines(keepends=True)
    start_idx = start_line - 1
    end_idx = end_line
    return "".join(lines[start_idx:end_idx])


def detect_file_type(path: str) -> Optional[str]:
    """Detect file type from extension."""
    p = Path(path)
    ext_to_kind = {
        ".py": "python",
        ".md": "markdown",
        ".org": "orgmode",
        ".clj": "clojure",
        ".cljs": "clojurescript",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".json": "json",
        ".sh": "bash",
        ".bash": "bash",
        ".java": "java",
        ".cs": "csharp",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".swift": "swift",
    }
    return ext_to_kind.get(p.suffix)


def find_files(root: str, extensions: Optional[List[str]] = None) -> List[str]:
    """
    Recursively find files matching extensions.
    If extensions is None, default to [.py, .md, .org, .clj, .cljs, .js, .ts, .go, .rs, .html, .htm, .css].
    """
    if extensions is None:
        extensions = [
            ".py", ".md", ".org", ".clj", ".cljs", ".js", ".jsx",
            ".ts", ".tsx", ".go", ".rs", ".html", ".htm", ".css",
            ".json", ".sh", ".bash", ".java",
            ".cs", ".kt", ".kts", ".swift",
        ]

    root_path = Path(root)
    files = []

    for ext in extensions:
        files.extend([str(p) for p in root_path.rglob(f"*{ext}") if p.is_file()])

    return sorted(files)


def truncate_text(text: str, max_chars: int = 500, max_lines: int = 20) -> str:
    """Truncate text for preview, respecting line and char limits."""
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append(f"... ({len(text.splitlines()) - max_lines} more lines)")

    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n... ({len(text) - max_chars} more chars)"

    return text
