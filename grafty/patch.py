"""
patch.py — Unified diff generation, validation, and atomic file writes.
"""
import difflib
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Tuple


def compute_hash(content: str) -> str:
    """Compute SHA256 hash of file content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def read_file_with_hash(path: str) -> Tuple[str, str, float]:
    """Read file and return (content, hash, mtime)."""
    p = Path(path)
    content = p.read_text(encoding="utf-8")
    mtime = p.stat().st_mtime
    hash_val = compute_hash(content)
    return content, hash_val, mtime


def normalize_newlines(content: str) -> Tuple[str, str]:
    """
    Normalize CRLF → LF internally.
    Returns (normalized_content, original_mode) where mode is "lf" or "crlf".
    """
    if "\r\n" in content:
        return content.replace("\r\n", "\n"), "crlf"
    return content, "lf"


def restore_newlines(content: str, mode: str) -> str:
    """Restore original newline style (LF or CRLF)."""
    if mode == "crlf":
        return content.replace("\n", "\r\n")
    return content


def generate_unified_diff(
    original: str,
    modified: str,
    file_path: str,
    context_lines: int = 3,
) -> str:
    """
    Generate unified diff between original and modified content.
    Returns diff string (with file headers).
    """
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)

    diff = difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm="",
        n=context_lines,
    )
    return "\n".join(diff) + "\n"


def apply_patch_to_buffer(content: str, operation: dict) -> str:
    """
    Apply a single patch operation to a content buffer.
    Operation: {"kind": "replace"|"insert"|"delete", "start_line": int,
                "end_line": int, "text": str}
    Returns modified content.
    """
    lines = content.splitlines(keepends=True)

    kind = operation["kind"]
    start_line = operation["start_line"]  # 1-indexed
    end_line = operation["end_line"]  # 1-indexed, inclusive
    text = operation.get("text", "")

    # Convert to 0-indexed
    start_idx = start_line - 1
    end_idx = end_line  # exclusive for slicing

    if kind == "replace":
        # Remove lines [start_idx:end_idx], insert text
        new_lines = lines[:start_idx]
        if text:
            # Preserve existing newline if text doesn't have one
            if not text.endswith("\n"):
                text += "\n"
            new_lines.extend(text.splitlines(keepends=True))
        new_lines.extend(lines[end_idx:])
        return "".join(new_lines)

    elif kind == "insert":
        # Insert at start_line (before it)
        new_lines = lines[:start_idx]
        if text:
            if not text.endswith("\n"):
                text += "\n"
            new_lines.extend(text.splitlines(keepends=True))
        new_lines.extend(lines[start_idx:])
        return "".join(new_lines)

    elif kind == "delete":
        # Delete lines [start_idx:end_idx]
        new_lines = lines[:start_idx]
        new_lines.extend(lines[end_idx:])
        return "".join(new_lines)

    else:
        raise ValueError(f"Unknown operation kind: {kind}")


def write_atomic(
    file_path: str,
    content: str,
    backup: bool = False,
    newline_mode: str = "lf",
) -> None:
    """
    Atomically write content to file (temp + rename).
    Optionally create .bak backup.
    Restores newline style before writing.
    """
    p = Path(file_path)

    # Create backup if requested
    if backup and p.exists():
        bak_path = Path(f"{file_path}.bak")
        shutil.copy2(file_path, bak_path)

    # Restore newline mode and write atomically
    content = restore_newlines(content, newline_mode)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=p.parent,
        delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    # Atomic rename
    os.replace(tmp_path, file_path)


def validate_drift(
    file_path: str,
    expected_hash: str,
    force: bool = False,
) -> None:
    """
    Check if file content has drifted (hash mismatch).
    Raises ValueError if drift detected and force=False.
    """
    _, actual_hash, _ = read_file_with_hash(file_path)
    if actual_hash != expected_hash and not force:
        raise ValueError(
            f"File {file_path} has drifted (hash mismatch). "
            f"Use --force to override."
        )


def git_apply_check(patch_content: str, repo_root: str = ".") -> Tuple[bool, str]:
    """
    Validate patch applicability via 'git apply --check'.
    Returns (success, output_or_error).
    """
    import subprocess

    git_dir = Path(repo_root) / ".git"
    if not git_dir.exists():
        # Not a git repo; skip check
        return True, "Not a git repo (skipping git validation)"

    try:
        result = subprocess.run(
            ["git", "apply", "--check"],
            input=patch_content,
            text=True,
            cwd=repo_root,
            capture_output=True,
        )
        return result.returncode == 0, result.stderr or result.stdout
    except FileNotFoundError:
        # git not found
        return True, "git not found (skipping validation)"


def format_patch_summary(patch_content: str) -> str:
    """Extract summary info from unified diff (file count, line counts, etc.)."""
    lines = patch_content.strip().split("\n")
    files = set()
    added = 0
    removed = 0

    for line in lines:
        if line.startswith("+++"):
            files.add(line.split("\t")[0][6:])  # strip "b/"
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        if line.startswith("-") and not line.startswith("---"):
            removed += 1

    return f"{len(files)} file(s), +{added} -{removed} lines"
