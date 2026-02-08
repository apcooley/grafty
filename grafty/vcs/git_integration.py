"""
Core Git integration module for grafty (Phase 4.2).

Provides GitRepo and GitConfig for managing VCS operations during patch application.
Features:
  - Pre-flight checks (repository validation, working directory state)
  - Automatic commit after patch application
  - Optional push to remote
  - Dry-run support for testing
  - Automatic rollback to backup files on failure
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class GitConfig:
    """Configuration for Git integration."""

    auto_commit: bool = False
    auto_push: bool = False
    allow_dirty: bool = False
    commit_message: str = "Apply grafty patch"
    dry_run: bool = False


class GitRepo:
    """Manages Git repository operations for patch application."""

    def __init__(self, repo_root: str, config: GitConfig):
        """
        Initialize GitRepo for the given repository.

        Args:
            repo_root: Root path of the repository
            config: GitConfig instance with settings
        """
        self.repo_root = Path(repo_root)
        self.config = config

    def is_clean(self) -> bool:
        """
        Check if working directory is clean (no uncommitted changes).

        Returns:
            True if working directory is clean, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and not result.stdout.strip()
        except Exception:
            return False

    def is_git_repo(self) -> bool:
        """
        Check if the directory is a valid Git repository.

        Returns:
            True if .git exists and is accessible, False otherwise
        """
        return self.repo_root.joinpath(".git").exists()

    def prepare_for_patch(self) -> None:
        """
        Perform pre-flight checks before applying patch.

        Checks:
          - Directory is a Git repository
          - Working directory is clean (unless --allow-dirty is set)

        Raises:
            NotAGitRepo: If not a valid Git repository
            DirtyRepo: If working directory is not clean and allow_dirty=False
        """
        if not self.is_git_repo():
            raise NotAGitRepo(
                f"Not a Git repository: {self.repo_root}. "
                "Use apply-patch without --auto-commit if not in a repo."
            )

        if not self.is_clean() and not self.config.allow_dirty:
            raise DirtyRepo(
                "Working directory not clean. "
                "Commit or stash changes first, or use --allow-dirty to proceed."
            )

    def stage_and_commit(self, files: List[str], message: str) -> str:
        """
        Stage files and create a commit.

        Args:
            files: List of file paths to stage
            message: Commit message

        Returns:
            Commit hash (or "[DRY RUN] commit-hash" if dry_run=True)

        Raises:
            CommitFailed: If git add or commit fails
        """
        if self.config.dry_run:
            print(f"[DRY RUN] git add {' '.join(files)}")
            print(f"[DRY RUN] git commit -m '{message}'")
            return "[DRY RUN] commit-hash"

        try:
            # Stage files
            subprocess.run(
                ["git", "add"] + files,
                cwd=self.repo_root,
                check=True,
                timeout=30,
                capture_output=True,
            )

            # Create commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )

            # Extract commit hash from output (format: [branch commit-hash] message)
            if result.stdout:
                parts = result.stdout.split()
                if len(parts) >= 2:
                    return parts[1].strip("]")
            return "unknown"

        except subprocess.CalledProcessError as e:
            raise CommitFailed(
                f"Commit failed: {e.stderr or e.stdout or 'unknown error'}"
            )

    def push_to_remote(self, remote: str = "origin", branch: Optional[str] = None) -> None:
        """
        Push to remote repository.

        Args:
            remote: Remote name (default: "origin")
            branch: Branch to push (default: None, pushes current branch)

        Raises:
            PushFailed: If git push fails
        """
        if self.config.dry_run:
            print(f"[DRY RUN] git push {remote}" + (f" {branch}" if branch else ""))
            return

        try:
            cmd = ["git", "push", remote]
            if branch:
                cmd.append(branch)

            subprocess.run(
                cmd,
                cwd=self.repo_root,
                check=True,
                timeout=60,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise PushFailed(f"Push failed: {e.stderr or e.stdout or 'unknown error'}")

    def rollback_to_backup(self, file_paths: List[str]) -> None:
        """
        Restore files from .bak backups.

        Used for recovery when patch application fails. Each file is restored
        from its corresponding .bak backup file.

        Args:
            file_paths: List of file paths to restore from backups
        """
        for file_path in file_paths:
            file_p = Path(file_path)
            # Append .bak to filename (not replace suffix)
            backup_path = file_p.parent / (file_p.name + ".bak")

            if backup_path.exists():
                try:
                    backup_path.replace(file_p)
                    print(f"Restored {file_path} from backup")
                except Exception as e:
                    print(f"Warning: Could not restore {file_path}: {e}")

    def get_current_branch(self) -> Optional[str]:
        """
        Get the current branch name.

        Returns:
            Branch name, or None if not on a branch (detached HEAD)
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                return None if branch == "HEAD" else branch
        except Exception:
            pass
        return None


class NotAGitRepo(Exception):
    """Raised when directory is not a Git repository."""

    pass


class DirtyRepo(Exception):
    """Raised when working directory has uncommitted changes."""

    pass


class CommitFailed(Exception):
    """Raised when git commit operation fails."""

    pass


class PushFailed(Exception):
    """Raised when git push operation fails."""

    pass
