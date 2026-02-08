"""
Tests for VCS integration module (Phase 4.2).

Tests Git repository operations, commit/push flows, and error handling.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

import pytest

from grafty.vcs import GitRepo, GitConfig, NotAGitRepo, DirtyRepo, CommitFailed, PushFailed


class TestGitConfig:
    """Test GitConfig dataclass."""

    def test_default_config(self):
        """Test default GitConfig values."""
        config = GitConfig()
        assert config.auto_commit is False
        assert config.auto_push is False
        assert config.allow_dirty is False
        assert config.commit_message == "Apply grafty patch"
        assert config.dry_run is False

    def test_custom_config(self):
        """Test custom GitConfig values."""
        config = GitConfig(
            auto_commit=True,
            auto_push=True,
            allow_dirty=True,
            commit_message="Custom message",
            dry_run=True,
        )
        assert config.auto_commit is True
        assert config.auto_push is True
        assert config.allow_dirty is True
        assert config.commit_message == "Custom message"
        assert config.dry_run is True


class TestGitRepo:
    """Test GitRepo class with actual git operations."""

    @pytest.fixture
    def git_repo(self) -> Tuple[Path, GitRepo]:
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Initialize git repo
            subprocess.run(
                ["git", "init"],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

            # Configure git user (required for commits)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

            config = GitConfig()
            repo = GitRepo(str(repo_path), config)

            yield repo_path, repo

    @pytest.fixture
    def non_git_dir(self) -> Path:
        """Create a temporary non-git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_is_git_repo_valid(self, git_repo: Tuple[Path, GitRepo]):
        """Test is_git_repo returns True for valid git repo."""
        _, repo = git_repo
        assert repo.is_git_repo() is True

    def test_is_git_repo_invalid(self, non_git_dir: Path):
        """Test is_git_repo returns False for non-git directory."""
        config = GitConfig()
        repo = GitRepo(str(non_git_dir), config)
        assert repo.is_git_repo() is False

    def test_is_clean_empty_repo(self, git_repo: Tuple[Path, GitRepo]):
        """Test is_clean returns True for empty/clean repo."""
        _, repo = git_repo
        assert repo.is_clean() is True

    def test_is_clean_with_untracked_files(self, git_repo: Tuple[Path, GitRepo]):
        """Test is_clean with untracked files.

        Note: git status --porcelain DOES show untracked files (with ?? prefix),
        so is_clean will return False. We test that behavior here.
        """
        repo_path, repo = git_repo

        # Create untracked file
        (repo_path / "untracked.txt").write_text("content")

        # git status --porcelain shows untracked files with ?? prefix
        # So is_clean correctly returns False
        assert repo.is_clean() is False

    def test_is_clean_with_modifications(self, git_repo: Tuple[Path, GitRepo]):
        """Test is_clean returns False for modified tracked files."""
        repo_path, repo = git_repo

        # Create and commit a file
        test_file = repo_path / "test.txt"
        test_file.write_text("original")

        subprocess.run(
            ["git", "add", "test.txt"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Modify the file
        test_file.write_text("modified")

        assert repo.is_clean() is False

    def test_prepare_for_patch_not_a_git_repo(self, non_git_dir: Path):
        """Test prepare_for_patch raises NotAGitRepo for non-git directory."""
        config = GitConfig()
        repo = GitRepo(str(non_git_dir), config)

        with pytest.raises(NotAGitRepo):
            repo.prepare_for_patch()

    def test_prepare_for_patch_dirty_repo_not_allowed(self, git_repo: Tuple[Path, GitRepo]):
        """Test prepare_for_patch raises DirtyRepo when working directory is dirty."""
        repo_path, repo = git_repo

        # Create and commit a file
        test_file = repo_path / "test.txt"
        test_file.write_text("original")

        subprocess.run(
            ["git", "add", "test.txt"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Modify the file
        test_file.write_text("modified")

        # Prepare with allow_dirty=False should raise
        with pytest.raises(DirtyRepo):
            repo.prepare_for_patch()

    def test_prepare_for_patch_dirty_repo_allowed(self, git_repo: Tuple[Path, GitRepo]):
        """Test prepare_for_patch succeeds when allow_dirty=True."""
        repo_path, repo = git_repo

        # Create and commit a file
        test_file = repo_path / "test.txt"
        test_file.write_text("original")

        subprocess.run(
            ["git", "add", "test.txt"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Modify the file
        test_file.write_text("modified")

        # Create new config with allow_dirty=True
        config = GitConfig(allow_dirty=True)
        repo = GitRepo(str(repo_path), config)

        # Should not raise
        repo.prepare_for_patch()

    def test_stage_and_commit(self, git_repo: Tuple[Path, GitRepo]):
        """Test stage_and_commit creates a commit."""
        repo_path, repo = git_repo

        # Create a test file
        test_file = repo_path / "test.txt"
        test_file.write_text("content")

        # Stage and commit
        commit_hash = repo.stage_and_commit(["test.txt"], "Test commit")

        # Verify commit was created
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        assert "Test commit" in result.stdout
        assert commit_hash != "unknown"

    def test_stage_and_commit_multiple_files(self, git_repo: Tuple[Path, GitRepo]):
        """Test stage_and_commit with multiple files."""
        repo_path, repo = git_repo

        # Create test files
        (repo_path / "file1.txt").write_text("content1")
        (repo_path / "file2.txt").write_text("content2")

        # Stage and commit both
        repo.stage_and_commit(
            ["file1.txt", "file2.txt"], "Multi-file commit"
        )

        # Verify both files are in the commit
        result = subprocess.run(
            ["git", "show", "--name-only"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        assert "file1.txt" in result.stdout
        assert "file2.txt" in result.stdout

    def test_stage_and_commit_dry_run(self, git_repo: Tuple[Path, GitRepo]):
        """Test stage_and_commit dry-run mode."""
        repo_path, repo = git_repo

        # Create a test file
        test_file = repo_path / "test.txt"
        test_file.write_text("content")

        # Configure dry-run
        config = GitConfig(dry_run=True)
        repo = GitRepo(str(repo_path), config)

        # Stage and commit (should not actually commit)
        commit_hash = repo.stage_and_commit(["test.txt"], "Test commit")

        assert commit_hash == "[DRY RUN] commit-hash"

        # Verify no actual commit was created
        result = subprocess.run(
            ["git", "log"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        assert "fatal" in result.stderr  # No commits in repo

    def test_push_to_remote_dry_run(self, git_repo: Tuple[Path, GitRepo]):
        """Test push_to_remote dry-run mode."""
        _, repo = git_repo

        # Configure dry-run
        config = GitConfig(dry_run=True)
        repo = GitRepo(str(repo.repo_root), config)

        # Push should not raise in dry-run mode
        repo.push_to_remote()

    def test_push_to_remote_no_remote(self, git_repo: Tuple[Path, GitRepo]):
        """Test push_to_remote fails when no remote is configured."""
        repo_path, repo = git_repo

        # Create and commit a file
        test_file = repo_path / "test.txt"
        test_file.write_text("content")

        subprocess.run(
            ["git", "add", "test.txt"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Test commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Push should fail (no remote configured)
        with pytest.raises(PushFailed):
            repo.push_to_remote()

    def test_rollback_to_backup(self, git_repo: Tuple[Path, GitRepo]):
        """Test rollback_to_backup restores from .bak files."""
        repo_path, repo = git_repo

        # Create a file and its backup
        test_file = repo_path / "test.txt"
        backup_file = repo_path / "test.txt.bak"

        test_file.write_text("modified")
        backup_file.write_text("original")

        # Verify setup
        assert test_file.read_text() == "modified"
        assert backup_file.read_text() == "original"

        # Rollback
        repo.rollback_to_backup([str(test_file)])

        # Verify file was restored
        assert test_file.read_text() == "original"
        assert not backup_file.exists()

    def test_rollback_to_backup_no_backup(self, git_repo: Tuple[Path, GitRepo]):
        """Test rollback_to_backup handles missing backup gracefully."""
        repo_path, repo = git_repo

        # Create a file without backup
        test_file = repo_path / "test.txt"
        test_file.write_text("content")

        # Rollback (should not raise)
        repo.rollback_to_backup(["test.txt"])

        # File should be unchanged
        assert test_file.read_text() == "content"

    def test_get_current_branch_main(self, git_repo: Tuple[Path, GitRepo]):
        """Test get_current_branch returns correct branch name."""
        repo_path, repo = git_repo

        # Create and commit a file to establish main branch
        test_file = repo_path / "test.txt"
        test_file.write_text("content")

        subprocess.run(
            ["git", "add", "test.txt"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Get current branch
        branch = repo.get_current_branch()

        # Should be "main" or "master" depending on git config
        assert branch in ("main", "master")

    def test_get_current_branch_custom(self, git_repo: Tuple[Path, GitRepo]):
        """Test get_current_branch with custom branch."""
        repo_path, repo = git_repo

        # Create and commit a file
        test_file = repo_path / "test.txt"
        test_file.write_text("content")

        subprocess.run(
            ["git", "add", "test.txt"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Create and checkout new branch
        subprocess.run(
            ["git", "checkout", "-b", "feature"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Get current branch
        branch = repo.get_current_branch()

        assert branch == "feature"


class TestGitExceptions:
    """Test custom Git exception classes."""

    def test_not_a_git_repo_exception(self):
        """Test NotAGitRepo exception."""
        exc = NotAGitRepo("test message")
        assert str(exc) == "test message"

    def test_dirty_repo_exception(self):
        """Test DirtyRepo exception."""
        exc = DirtyRepo("test message")
        assert str(exc) == "test message"

    def test_commit_failed_exception(self):
        """Test CommitFailed exception."""
        exc = CommitFailed("test message")
        assert str(exc) == "test message"

    def test_push_failed_exception(self):
        """Test PushFailed exception."""
        exc = PushFailed("test message")
        assert str(exc) == "test message"
