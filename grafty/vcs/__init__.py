"""
VCS module for grafty — Git integration support (Phase 4.2).
"""

from .git_integration import GitRepo, GitConfig, NotAGitRepo, DirtyRepo, CommitFailed, PushFailed

__all__ = [
    "GitRepo",
    "GitConfig",
    "NotAGitRepo",
    "DirtyRepo",
    "CommitFailed",
    "PushFailed",
]
