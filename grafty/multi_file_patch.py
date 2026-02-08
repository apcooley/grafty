"""
multi_file_patch.py — Atomic multi-file patch application (Phase 4.1, Phase 4.2).

Provides PatchSet for managing coordinated changes across multiple files
with atomic writes, validation, rollback support, and optional Git integration.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from .patch import (
    apply_patch_to_buffer,
    generate_unified_diff,
    normalize_newlines,
    read_file_with_hash,
    restore_newlines,
    validate_drift,
    write_atomic,
)

if TYPE_CHECKING:
    from .vcs import GitConfig


@dataclass
class FileMutation:
    """
    A single mutation (edit) to apply to a file.

    Attributes:
        file_path: Path to the file to mutate (relative or absolute)
        operation_kind: Type of mutation: "replace", "insert", or "delete"
        start_line: 1-indexed starting line number
        end_line: 1-indexed ending line number (inclusive)
        text: Text to insert or replace with (empty for delete)
        description: Human-readable description of this mutation
    """

    file_path: str
    operation_kind: str  # "replace", "insert", "delete"
    start_line: int
    end_line: int
    text: str = ""
    description: str = ""

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "file_path": self.file_path,
            "operation_kind": self.operation_kind,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "text": self.text,
            "description": self.description,
        }

    def to_simple_format(self) -> str:
        """Convert to simple line format: file_path:operation_kind:start:end[:text]"""
        parts = [self.file_path, self.operation_kind, str(self.start_line), str(self.end_line)]
        if self.text:
            parts.append(self.text)
        return ":".join(parts)

    @staticmethod
    def from_simple_format(line: str) -> "FileMutation":
        """Parse from simple format line: file_path:operation_kind:start:end[:text]"""
        parts = line.split(":", 4)
        if len(parts) < 4:
            raise ValueError(f"Invalid simple format (need 4+ parts): {line}")

        file_path = parts[0]
        operation_kind = parts[1]
        try:
            start_line = int(parts[2])
            end_line = int(parts[3])
        except ValueError as e:
            raise ValueError(f"Invalid line numbers in: {line}") from e

        text = parts[4] if len(parts) > 4 else ""

        return FileMutation(
            file_path=file_path,
            operation_kind=operation_kind,
            start_line=start_line,
            end_line=end_line,
            text=text,
            description="",
        )


@dataclass
class PatchSetResult:
    """
    Result of patch validation, generation, or application.

    Attributes:
        success: True if operation succeeded
        message: Human-readable status message
        errors: List of error messages (empty if success=True)
        warnings: List of warning messages
        diffs: For generate_diffs(), dict of {file_path: unified_diff_string}
        files_modified: For apply_atomic(), list of modified file paths
    """

    success: bool = False
    message: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    diffs: Dict[str, str] = field(default_factory=dict)
    files_modified: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Human-readable string representation."""
        lines = [self.message]

        if self.errors:
            lines.append("\nErrors:")
            for err in self.errors:
                lines.append(f"  - {err}")

        if self.warnings:
            lines.append("\nWarnings:")
            for warn in self.warnings:
                lines.append(f"  - {warn}")

        if self.files_modified:
            lines.append(f"\nFiles modified: {', '.join(self.files_modified)}")

        return "\n".join(lines)


@dataclass
class PatchSet:
    """
    Manages a set of mutations to apply atomically across multiple files.

    Features:
      - Load from JSON or simple line-based format
      - Validate all mutations before applying
      - Generate dry-run diffs to preview changes
      - Apply atomically with automatic rollback on error
      - Optional .bak backups
      - Overlap detection and warnings
    """

    mutations: List[FileMutation] = field(default_factory=list)

    def add_mutation(
        self,
        file_path: str,
        operation_kind: str,
        start_line: int,
        end_line: int,
        text: str = "",
        description: str = "",
    ) -> None:
        """
        Add a single mutation to the patch set.

        Args:
            file_path: Path to the file
            operation_kind: "replace", "insert", or "delete"
            start_line: 1-indexed starting line
            end_line: 1-indexed ending line (inclusive)
            text: Text to insert or replace with (empty for delete)
            description: Optional human-readable description
        """
        mutation = FileMutation(
            file_path=file_path,
            operation_kind=operation_kind,
            start_line=start_line,
            end_line=end_line,
            text=text,
            description=description,
        )
        self.mutations.append(mutation)

    def load_from_simple_format(self, content: str) -> None:
        """
        Load mutations from simple line-based format.

        Format (one per line):
            file_path:operation_kind:start_line:end_line[:text]

        Example:
            src/main.py:replace:10:12:def new_func(): pass
            src/config.py:insert:5:5:    enabled = True

        Args:
            content: Multi-line string with mutations

        Raises:
            ValueError: If any line has invalid format
        """
        self.mutations.clear()
        lines = content.strip().split("\n")

        for i, line in enumerate(lines, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue  # Skip empty lines and comments

            try:
                mutation = FileMutation.from_simple_format(line)
                self.mutations.append(mutation)
            except ValueError as e:
                raise ValueError(f"Line {i}: {e}") from e

    def load_from_json(self, content: str) -> None:
        """
        Load mutations from JSON format.

        Format: List of mutation objects with optional metadata.

        Example:
            [
              {
                "file_path": "src/main.py",
                "operation_kind": "replace",
                "start_line": 10,
                "end_line": 12,
                "text": "def new_func(): pass",
                "description": "Update main function"
              }
            ]

        Args:
            content: JSON string

        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        self.mutations.clear()

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        if not isinstance(data, list):
            raise ValueError("JSON must be a list of mutations")

        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"Item {i} is not a dict: {item}")

            required = {"file_path", "operation_kind", "start_line", "end_line"}
            if not required.issubset(item.keys()):
                raise ValueError(f"Item {i} missing required fields: {required}")

            try:
                mutation = FileMutation(
                    file_path=item["file_path"],
                    operation_kind=item["operation_kind"],
                    start_line=int(item["start_line"]),
                    end_line=int(item["end_line"]),
                    text=item.get("text", ""),
                    description=item.get("description", ""),
                )
                self.mutations.append(mutation)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Item {i} has invalid values: {e}") from e

    def validate_all(self, repo_root: str = ".") -> PatchSetResult:
        """
        Validate all mutations before applying.

        Checks:
          - Each file exists and is readable
          - Line numbers are valid (1 <= start <= end <= file_lines)
          - No overlapping mutations in same file
          - Operation kind is recognized

        Args:
            repo_root: Root directory for relative file paths

        Returns:
            PatchSetResult with success flag and error details
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not self.mutations:
            return PatchSetResult(
                success=False,
                message="No mutations to validate",
                errors=["Empty patch set"],
            )

        # Group mutations by file
        mutations_by_file: Dict[str, List[FileMutation]] = {}
        for mut in self.mutations:
            if mut.file_path not in mutations_by_file:
                mutations_by_file[mut.file_path] = []
            mutations_by_file[mut.file_path].append(mut)

        # Validate each file and its mutations
        for file_path, file_mutations in mutations_by_file.items():
            abs_path = Path(repo_root) / file_path

            # Check file exists
            if not abs_path.exists():
                errors.append(f"File not found: {file_path}")
                continue

            # Read file and validate line numbers
            try:
                content = abs_path.read_text(encoding="utf-8")
                lines = content.splitlines()
                file_line_count = len(lines)
            except Exception as e:
                errors.append(f"Cannot read {file_path}: {e}")
                continue

            # Validate each mutation
            for i, mut in enumerate(file_mutations):
                # Check operation kind
                if mut.operation_kind not in ("replace", "insert", "delete"):
                    errors.append(
                        f"{file_path}[{i}]: Invalid operation_kind: {mut.operation_kind}"
                    )
                    continue

                # Check line numbers are positive
                if mut.start_line < 1 or mut.end_line < 1:
                    errors.append(
                        f"{file_path}[{i}]: Line numbers must be >= 1 "
                        f"(got {mut.start_line}-{mut.end_line})"
                    )
                    continue

                # Check start <= end
                if mut.start_line > mut.end_line:
                    errors.append(
                        f"{file_path}[{i}]: start_line > end_line "
                        f"({mut.start_line} > {mut.end_line})"
                    )
                    continue

                # Check lines are within file
                if mut.start_line > file_line_count:
                    errors.append(
                        f"{file_path}[{i}]: start_line {mut.start_line} > file size {file_line_count}"
                    )
                    continue

                if mut.end_line > file_line_count and mut.operation_kind != "insert":
                    errors.append(
                        f"{file_path}[{i}]: end_line {mut.end_line} > file size {file_line_count}"
                    )
                    continue

            # Check for overlaps
            sorted_muts = sorted(file_mutations, key=lambda m: (m.start_line, m.end_line))
            for i in range(len(sorted_muts) - 1):
                curr = sorted_muts[i]
                next_mut = sorted_muts[i + 1]
                if curr.end_line >= next_mut.start_line:
                    warnings.append(
                        f"{file_path}: Mutations {i} and {i+1} overlap "
                        f"({curr.start_line}-{curr.end_line} vs {next_mut.start_line}-{next_mut.end_line})"
                    )

        # Overall result
        if errors:
            return PatchSetResult(
                success=False,
                message=f"Validation failed: {len(errors)} error(s)",
                errors=errors,
                warnings=warnings,
            )

        return PatchSetResult(
            success=True,
            message=f"Validation passed: {len(self.mutations)} mutation(s) in {len(mutations_by_file)} file(s)",
            warnings=warnings,
        )

    def generate_diffs(self, repo_root: str = ".") -> PatchSetResult:
        """
        Generate unified diffs for all mutations (dry-run preview).

        Does NOT modify files; only generates diffs to show what would change.

        Args:
            repo_root: Root directory for relative file paths

        Returns:
            PatchSetResult with diffs dict {file_path: unified_diff_string}
        """
        # First validate
        validation = self.validate_all(repo_root)
        if not validation.success:
            return validation

        diffs: Dict[str, str] = {}
        errors: List[str] = []

        # Group mutations by file and apply in order
        mutations_by_file: Dict[str, List[FileMutation]] = {}
        for mut in self.mutations:
            if mut.file_path not in mutations_by_file:
                mutations_by_file[mut.file_path] = []
            mutations_by_file[mut.file_path].append(mut)

        for file_path, file_mutations in mutations_by_file.items():
            abs_path = Path(repo_root) / file_path

            try:
                original = abs_path.read_text(encoding="utf-8")
                modified = original
                normalized, newline_mode = normalize_newlines(original)

                # Apply mutations in reverse order to preserve line numbers
                for mut in sorted(file_mutations, key=lambda m: m.start_line, reverse=True):
                    operation = {
                        "kind": mut.operation_kind,
                        "start_line": mut.start_line,
                        "end_line": mut.end_line,
                        "text": mut.text,
                    }
                    normalized = apply_patch_to_buffer(normalized, operation)

                # Restore newlines
                modified = restore_newlines(normalized, newline_mode)

                # Generate diff
                diff = generate_unified_diff(original, modified, file_path)
                diffs[file_path] = diff

            except Exception as e:
                errors.append(f"{file_path}: {e}")

        if errors:
            return PatchSetResult(
                success=False,
                message=f"Diff generation failed: {len(errors)} error(s)",
                errors=errors,
                diffs=diffs,
            )

        return PatchSetResult(
            success=True,
            message=f"Generated diffs for {len(diffs)} file(s)",
            diffs=diffs,
        )

    def apply_atomic(
        self,
        repo_root: str = ".",
        backup: bool = False,
        force: bool = False,
        git_config: Optional["GitConfig"] = None,
    ) -> PatchSetResult:
        """
        Apply all mutations atomically (all succeed or all rollback).

        Uses temp files + rename for atomic writes. On any error, rolls back
        all changes and restores backups.

        Supports optional Git integration (Phase 4.2):
        - Pre-patch: Validates repository and working directory state
        - Post-patch: Creates commit and optionally pushes to remote
        - On failure: Restores files from backups automatically

        Args:
            repo_root: Root directory for relative file paths
            backup: Create .bak backups before applying
            force: Skip drift validation
            git_config: Optional GitConfig for VCS integration (Phase 4.2)

        Returns:
            PatchSetResult with success flag and file list
        """
        # First validate
        validation = self.validate_all(repo_root)
        if not validation.success:
            return validation

        # Prepare file states for rollback
        file_states: Dict[str, Tuple[str, str, float]] = {}  # {path: (content, hash, mtime)}
        mutations_by_file: Dict[str, List[FileMutation]] = {}

        try:
            # Read all files first (group mutations by file)
            for mut in self.mutations:
                if mut.file_path not in mutations_by_file:
                    mutations_by_file[mut.file_path] = []
                mutations_by_file[mut.file_path].append(mut)

            for file_path in mutations_by_file.keys():
                abs_path = Path(repo_root) / file_path
                content, file_hash, mtime = read_file_with_hash(str(abs_path))
                file_states[file_path] = (content, file_hash, mtime)

                # Check drift if not forced
                if not force:
                    try:
                        validate_drift(str(abs_path), file_hash, force)
                    except ValueError as e:
                        raise ValueError(str(e)) from e

            # Apply mutations to each file
            modified_files: Dict[str, str] = {}  # {path: modified_content}
            newline_modes: Dict[str, str] = {}  # {path: newline_mode}

            for file_path, file_mutations in mutations_by_file.items():
                original, _, _ = file_states[file_path]
                modified = original
                normalized, newline_mode = normalize_newlines(original)
                newline_modes[file_path] = newline_mode

                # Sort mutations by line number (descending) to preserve line numbers
                for mut in sorted(file_mutations, key=lambda m: m.start_line, reverse=True):
                    operation = {
                        "kind": mut.operation_kind,
                        "start_line": mut.start_line,
                        "end_line": mut.end_line,
                        "text": mut.text,
                    }
                    normalized = apply_patch_to_buffer(normalized, operation)

                # Restore newlines
                modified = restore_newlines(normalized, newline_mode)
                modified_files[file_path] = modified

            # Write all files atomically
            for file_path, modified_content in modified_files.items():
                abs_path = Path(repo_root) / file_path
                newline_mode = newline_modes[file_path]

                write_atomic(
                    str(abs_path),
                    modified_content,
                    backup=backup,
                    newline_mode=newline_mode,
                )

            # Handle Git integration (Phase 4.2) if configured
            result_message = f"Applied patch to {len(modified_files)} file(s)"
            if git_config:
                from .vcs import GitRepo, CommitFailed, PushFailed

                try:
                    git_repo = GitRepo(repo_root, git_config)

                    # Stage and commit changes
                    if git_config.auto_commit:
                        modified_abs_paths = [
                            str(Path(repo_root) / f) for f in modified_files.keys()
                        ]
                        commit_hash = git_repo.stage_and_commit(
                            modified_abs_paths, git_config.commit_message
                        )
                        result_message += f"\nCommitted: {commit_hash}"

                        # Push if requested
                        if git_config.auto_push:
                            current_branch = git_repo.get_current_branch()
                            git_repo.push_to_remote(branch=current_branch)
                            result_message += "\nPushed to remote"

                except (CommitFailed, PushFailed) as git_err:
                    # On git error, rollback file changes
                    rollback_errors = []
                    for file_path, (original_content, _, _) in file_states.items():
                        try:
                            abs_path = Path(repo_root) / file_path
                            _, newline_mode = normalize_newlines(original_content)
                            write_atomic(
                                str(abs_path),
                                original_content,
                                backup=False,
                                newline_mode=newline_mode,
                            )
                        except Exception as rollback_e:
                            rollback_errors.append(f"Rollback {file_path}: {rollback_e}")

                    error_msg = f"Git operation failed: {git_err}"
                    if rollback_errors:
                        error_msg += "\nRollback errors:\n" + "\n".join(rollback_errors)

                    return PatchSetResult(
                        success=False,
                        message="Patch applied but Git operation failed; files rolled back",
                        errors=[error_msg] + rollback_errors,
                        files_modified=list(modified_files.keys()),
                    )

            return PatchSetResult(
                success=True,
                message=result_message,
                files_modified=list(modified_files.keys()),
            )

        except Exception as e:
            # Rollback: restore all original files from state
            rollback_errors = []

            for file_path, (original_content, _, _) in file_states.items():
                try:
                    abs_path = Path(repo_root) / file_path
                    _, newline_mode = normalize_newlines(original_content)
                    write_atomic(
                        str(abs_path),
                        original_content,
                        backup=False,
                        newline_mode=newline_mode,
                    )
                except Exception as rollback_e:
                    rollback_errors.append(f"Rollback {file_path}: {rollback_e}")

            error_msg = f"Patch application failed: {e}"
            if rollback_errors:
                error_msg += "\nRollback errors:\n" + "\n".join(rollback_errors)

            return PatchSetResult(
                success=False,
                message="Patch application failed and rolled back",
                errors=[error_msg] + rollback_errors,
            )
