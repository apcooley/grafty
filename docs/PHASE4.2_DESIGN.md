# Grafty Phase 4.2: Git Integration Module Design

**Version:** 1.0  
**Date:** 2026-02-08  
**Phase:** 4.2 - VCS Integration  
**Module:** `grafty/vcs/git_integration.py`

---

## 1. Executive Summary

This design document specifies the Git integration module for grafty's `apply-patch` command. The module provides safe, reversible Git operations with automatic commit/push capabilities, pre-flight validation, rollback safety nets, and comprehensive error handling.

### Key Goals

- **Safety First:** Pre-flight checks prevent accidental commits to wrong branches or with uncommitted changes
- **Reversibility:** Use existing `.bak` files for safe rollback on failure
- **Backward Compatible:** All VCS features are optional (flags default to `off`)
- **Clear Errors:** Helpful error messages guide users toward resolution
- **Testability:** Dry-run mode and pluggable Git operations enable unit testing

---

## 2. Module Structure

### 2.1 Package Layout

```
grafty/
├── vcs/
│   ├── __init__.py              # Public API exports
│   ├── git_integration.py        # Core module (this design)
│   ├── config.py                # VCS configuration classes
│   └── errors.py                # Custom exceptions
└── cli/
    └── apply_patch.py           # Updated command (integrates with VCS)
```

### 2.2 Core Classes

#### **GitConfig** (Dataclass)

Immutable configuration for Git operations.

```python
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum

class DryRunMode(Enum):
    OFF = "off"              # Execute real Git commands
    SIMULATE = "simulate"    # Log operations without executing
    STRICT = "strict"        # Validate without executing (fail on issues)

@dataclass
class GitConfig:
    """VCS configuration for apply-patch workflow."""
    
    # Automation flags
    auto_commit: bool = False           # Stage and commit after patch
    auto_push: bool = False             # Push to remote after commit
    allow_dirty: bool = False           # Allow uncommitted changes before patch
    
    # Repository state
    branch: Optional[str] = None        # Current branch (auto-detected if None)
    remote: str = "origin"              # Remote name for push
    
    # Safety
    dry_run: DryRunMode = DryRunMode.OFF
    require_clean_status: bool = True   # Enforce clean status unless allow_dirty
    
    # Rollback
    use_backups: bool = True            # Use .bak files for rollback
    backup_dir: Optional[str] = None    # Where .bak files are stored
```

#### **GitRepo** (Main Class)

Manages all Git operations with safety guards and rollback capability.

```python
class GitRepo:
    """
    Encapsulates Git repository operations for patching workflow.
    
    Workflow:
        1. prepare_for_patch() → validates state
        2. apply patch (external, creates .bak files)
        3. stage_and_commit() → stages changes, creates commit
        4. push_to_remote() → pushes to remote
        5. On error: rollback_to_backup() → restores from .bak
    """
    
    def __init__(self, repo_path: str, config: GitConfig):
        """
        Initialize Git repo wrapper.
        
        Args:
            repo_path: Path to Git repository root
            config: GitConfig instance with VCS settings
            
        Raises:
            GitNotInitializedError: repo_path is not a Git repository
            InvalidRepoPathError: repo_path does not exist
        """
        self.repo_path = Path(repo_path)
        self.config = config
        self.git = self._init_git_cli()
        self._validate_repo()
    
    # ================================================================
    # Pre-Patch Validation
    # ================================================================
    
    def prepare_for_patch(self) -> dict:
        """
        Pre-flight checks before applying patch.
        
        Returns:
            dict with keys:
                - is_clean: bool → Git status is clean
                - current_branch: str → Current branch name
                - remote_exists: bool → Remote exists and is reachable
                - protected_branch: bool → Branch is protected (metadata only)
        
        Raises:
            GitNotInitializedError: Not in a Git repository
            DirtyWorkingTreeError: Uncommitted changes detected (unless allow_dirty)
            NoRemoteError: Remote not found when auto_push is enabled
            InvalidBranchError: Current branch is invalid or detached
        """
        # Implementation details
        pass
    
    def _check_working_tree(self) -> bool:
        """Returns True if working tree is clean."""
        pass
    
    def _get_current_branch(self) -> str:
        """Returns current branch name."""
        pass
    
    def _validate_remote(self) -> bool:
        """Validates remote exists and is reachable."""
        pass
    
    # ================================================================
    # Commit & Push Operations
    # ================================================================
    
    def stage_and_commit(self, message: str, files: Optional[List[str]] = None) -> str:
        """
        Stage modified files and create a commit.
        
        Args:
            message: Commit message
            files: Specific files to stage. If None, stages all changes.
        
        Returns:
            Commit hash (short SHA)
        
        Raises:
            DryRunError: If dry_run mode prevents actual commit
            NoChangesError: Nothing to commit
            GitCommandError: Git command failed
        """
        # Implementation details
        pass
    
    def push_to_remote(self) -> dict:
        """
        Push current branch to remote.
        
        Returns:
            dict with keys:
                - success: bool
                - commits_pushed: int
                - branch: str
                - timestamp: str (ISO format)
        
        Raises:
            NoRemoteError: Remote doesn't exist
            NetworkError: Network connectivity issue
            PermissionError: No push permission to remote
            PartialPushError: Some commits pushed, some failed
            GitCommandError: Git command failed
        """
        # Implementation details
        pass
    
    # ================================================================
    # Rollback Operations
    # ================================================================
    
    def rollback_to_backup(self, files: List[str]) -> dict:
        """
        Restore files from .bak backups created by apply-patch.
        
        Args:
            files: List of file paths to restore from .bak
        
        Returns:
            dict with keys:
                - restored_files: List[str] → Files successfully restored
                - failed_files: List[str] → Files that couldn't be restored
                - backup_dir: str → Where backups were found
        
        Raises:
            NoBackupFilesError: No .bak files found
            BackupRestoreError: Failed to restore one or more files
        """
        # Implementation details
        pass
    
    def reset_to_commit(self, commit_hash: str, files: Optional[List[str]] = None) -> bool:
        """
        Hard reset to a specific commit (destructive).
        Only used when rollback_to_backup fails.
        
        Args:
            commit_hash: Target commit SHA
            files: If provided, reset only these files (soft reset)
        
        Returns:
            True if successful
        
        Raises:
            GitCommandError: Reset failed
        """
        # Implementation details
        pass
    
    # ================================================================
    # State Query Methods
    # ================================================================
    
    def get_status(self) -> dict:
        """
        Get full repository status.
        
        Returns:
            dict with keys:
                - is_clean: bool
                - branch: str
                - commits_ahead: int
                - commits_behind: int
                - modified_files: List[str]
                - untracked_files: List[str]
                - staged_files: List[str]
        """
        # Implementation details
        pass
    
    def get_last_commit(self) -> dict:
        """
        Get information about the last commit.
        
        Returns:
            dict with keys:
                - hash: str (short SHA)
                - author: str
                - message: str
                - timestamp: str (ISO format)
        """
        # Implementation details
        pass
    
    def list_modified_files(self) -> List[str]:
        """List all modified (not staged) files."""
        pass
    
    def list_staged_files(self) -> List[str]:
        """List all staged files."""
        pass
```

---

## 3. Public API

### 3.1 Main Entry Points

#### **1. `prepare_for_patch()`**

```python
# Usage
repo = GitRepo(repo_path, config)
try:
    status = repo.prepare_for_patch()
    print(f"Branch: {status['current_branch']}")
    print(f"Clean: {status['is_clean']}")
except DirtyWorkingTreeError as e:
    print(f"Error: {e.message}")
    print(f"Suggestion: {e.suggestion}")  # "Use --allow-dirty flag"
except GitNotInitializedError as e:
    print(f"Error: {e.message}")
    print(f"Hint: {e.hint}")  # "Run: git init"
```

**Validation Checklist:**
- ✓ Git repository initialized
- ✓ HEAD is attached (not detached)
- ✓ Working tree is clean (unless `--allow-dirty`)
- ✓ Current branch exists
- ✓ Remote exists (if `--auto-push`)
- ✓ Network connectivity to remote (if `--auto-push`)

---

#### **2. `stage_and_commit(message, files=None)`**

```python
# Usage: Commit all changes
commit_hash = repo.stage_and_commit(
    message="Apply patch: fix issue #123"
)
print(f"Committed: {commit_hash}")

# Usage: Commit specific files
commit_hash = repo.stage_and_commit(
    message="Apply patch: partial update",
    files=["src/main.py", "tests/test_main.py"]
)
```

**Behavior:**
- Stages specified files (or all if not specified)
- Creates commit with provided message
- Returns short SHA for reference
- Fails gracefully if nothing to commit

---

#### **3. `push_to_remote()`**

```python
# Usage
try:
    result = repo.push_to_remote()
    print(f"Pushed {result['commits_pushed']} commits to {result['branch']}")
except PermissionError:
    print("No push permission. Rollback and request access.")
except NetworkError:
    print("Network issue. Will retry in next run.")
```

**Behavior:**
- Pushes current branch to configured remote
- Fails if network down or permissions denied
- Returns push metadata for logging

---

#### **4. `rollback_to_backup(files)`**

```python
# Usage: Restore from .bak files on failure
try:
    result = repo.rollback_to_backup(
        files=["src/file1.py", "src/file2.py"]
    )
    print(f"Restored: {result['restored_files']}")
    if result['failed_files']:
        print(f"Failed to restore: {result['failed_files']}")
except NoBackupFilesError:
    print("No backups found. Manual recovery needed.")
```

**Behavior:**
- Looks for `.bak` files in backup directory
- Restores original content
- Reports which files were recovered
- Suggests manual recovery if backups unavailable

---

### 3.2 Helper Functions

#### **`get_backup_files(file_path) -> Path`**

```python
def get_backup_files(file_path: str, backup_dir: Optional[str] = None) -> Path:
    """
    Locate .bak file for given path.
    
    Searches in order:
      1. backup_dir/.bak/file.ext.bak (if configured)
      2. file.ext.bak (same directory)
      3. returns None if not found
    """
    pass
```

#### **`create_patch_metadata(repo: GitRepo) -> dict`**

```python
def create_patch_metadata(repo: GitRepo) -> dict:
    """
    Capture pre-patch repository state for rollback reference.
    
    Returns:
        {
            "timestamp": "2026-02-08T14:06:00+00:00",
            "branch": "main",
            "commit_before": "abc1234",
            "author": "patch-bot",
            "files_to_backup": ["src/file1.py", ...]
        }
    """
    pass
```

---

## 4. Integration with `apply-patch` Command

### 4.1 Updated Workflow

```
┌─────────────────────────────────────────────────────┐
│ apply-patch command (updated)                       │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
           ┌──────────────────────────┐
           │ parse_args() + GitConfig │
           └──────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │ 1. repo.prepare_for_patch()       │
         │    (validate branch, clean state) │
         └───────────────────────────────────┘
                         │
                    ┌────┴────┐
                    │          │
            clean ◄─┘          └──► dirty & !--allow-dirty
                                            │
                                            ▼
                                    ERROR: DirtyWorkingTree
                                    Suggest: --allow-dirty
                         │
                         ▼
         ┌───────────────────────────────────┐
         │ 2. apply_patch()                  │
         │    (creates .bak files)           │
         └───────────────────────────────────┘
                         │
                    ┌────┴────┐
                    │          │
              SUCCESS          │ FAILED
                │              │
                ▼              ▼
    (if auto_commit)    ROLLBACK: restore .bak
                │        │ Reset repo
                │        │ Exit with error
                │        │
                ▼        └─────────────► END (failure)
    ┌──────────────────────────┐
    │ 3. repo.stage_and_commit │
    │    (create commit)       │
    └──────────────────────────┘
                │
           ┌────┴────┐
           │          │
         OK          FAIL
         │            │
         │            ▼
         │      ROLLBACK: .bak restore
         │            │ ERROR exit
         │            │
         │            └─────────► END (failure)
         │
         ▼
    (if auto_push)
    │
    ├─NO──► END (success)
    │
    ▼
    ┌──────────────────────┐
    │ 4. repo.push_to_remote
    └──────────────────────┘
         │
    ┌────┴────────────────┐
    │                     │
  SUCCESS            FAILED
    │                  │
    │                  ├──────────────┐
    │                  │              │
    │              Network        Permission
    │                  │              │
    │                  ▼              ▼
    │          Log warning      Rollback commit?
    │          (push retry)      (optional flag)
    │                  │              │
    │                  └──────┬───────┘
    │                         │
    │                         ▼
    │                  Offer recovery steps
    │
    ▼
 END (success)
```

### 4.2 CLI Integration

```python
# In apply-patch command

@click.command()
@click.argument('patch_file', type=click.File('r'))
@click.option(
    '--auto-commit',
    is_flag=True,
    default=False,
    help='Automatically commit changes after patch'
)
@click.option(
    '--auto-push',
    is_flag=True,
    default=False,
    help='Automatically push to remote after commit (implies --auto-commit)'
)
@click.option(
    '--allow-dirty',
    is_flag=True,
    default=False,
    help='Allow uncommitted changes before patching'
)
@click.option(
    '--branch',
    type=str,
    default=None,
    help='Target branch (validated before patching)'
)
@click.option(
    '--dry-run',
    type=click.Choice(['off', 'simulate', 'strict']),
    default='off',
    help='Dry-run mode: simulate (log), strict (validate only)'
)
def apply_patch(patch_file, auto_commit, auto_push, allow_dirty, branch, dry_run):
    """
    Apply a patch file to the repository with optional Git integration.
    
    Examples:
        # Simple patch application
        grafty apply-patch fix.patch
        
        # Patch with auto-commit
        grafty apply-patch fix.patch --auto-commit
        
        # Full CI/CD mode: patch, commit, push
        grafty apply-patch fix.patch --auto-commit --auto-push
        
        # Test in dry-run mode first
        grafty apply-patch fix.patch --auto-commit --dry-run=simulate
    """
    pass
```

---

## 5. Error Handling & Safety Features

### 5.1 Custom Exceptions

```python
# Base exception
class GitIntegrationError(Exception):
    """Base for all Git integration errors."""
    def __init__(self, message: str, suggestion: str = None, hint: str = None):
        self.message = message
        self.suggestion = suggestion
        self.hint = hint
        super().__init__(self.message)

# Repository state errors
class GitNotInitializedError(GitIntegrationError):
    """Git repo not initialized in target directory."""
    hint = "Run: git init"

class InvalidRepoPathError(GitIntegrationError):
    """Repository path doesn't exist or is invalid."""

class DirtyWorkingTreeError(GitIntegrationError):
    """Working tree has uncommitted changes."""
    suggestion = "Run: git status  OR  Use --allow-dirty flag"

class DetachedHeadError(GitIntegrationError):
    """HEAD is detached (not on a branch)."""
    suggestion = "Run: git checkout <branch>"

class InvalidBranchError(GitIntegrationError):
    """Branch doesn't exist or is invalid."""

# Remote/Push errors
class NoRemoteError(GitIntegrationError):
    """Remote not found."""
    hint = "Configure remote: git remote add origin <url>"

class NetworkError(GitIntegrationError):
    """Network connectivity issue."""
    suggestion = "Check internet connection and retry"

class PermissionError(GitIntegrationError):
    """No push permission to remote."""
    suggestion = "Check Git credentials and repository permissions"

# Commit/Operation errors
class NoChangesError(GitIntegrationError):
    """Nothing to commit."""

class GitCommandError(GitIntegrationError):
    """Generic Git command execution error."""

# Rollback errors
class NoBackupFilesError(GitIntegrationError):
    """No .bak files found for rollback."""
    suggestion = "Manual recovery required: restore from version control"

class BackupRestoreError(GitIntegrationError):
    """Failed to restore from backup."""
    suggestion = "Manually restore files and run 'git reset HEAD'"

class PartialPushError(GitIntegrationError):
    """Some commits pushed, some failed."""
    suggestion = "Check error log, fix issue, manually push or retry"
```

### 5.2 Pre-Flight Validation

**Checks performed in `prepare_for_patch()`:**

```
✓ Is Git initialized?
  └─ Error: GitNotInitializedError with hint to run git init

✓ Is repo path valid?
  └─ Error: InvalidRepoPathError

✓ Is HEAD attached (not detached)?
  └─ Error: DetachedHeadError with suggestion to checkout branch

✓ Is working tree clean (or --allow-dirty)?
  └─ Error: DirtyWorkingTreeError, suggest --allow-dirty

✓ Does branch exist?
  └─ Error: InvalidBranchError

✓ (if --auto-push) Does remote exist?
  └─ Error: NoRemoteError with hint to configure

✓ (if --auto-push) Is remote reachable?
  └─ Error: NetworkError, suggest connectivity check
```

### 5.3 Rollback Strategy

**On patch failure:**

```python
try:
    apply_patch()
except Exception as e:
    logger.error(f"Patch failed: {e}")
    
    # Step 1: Attempt .bak file restore
    try:
        result = repo.rollback_to_backup(modified_files)
        logger.info(f"Restored from backup: {result['restored_files']}")
    except NoBackupFilesError:
        # Step 2: Attempt git reset if .bak unavailable
        try:
            repo.reset_to_commit(pre_patch_commit)
            logger.info("Reset to pre-patch state")
        except GitCommandError as reset_error:
            # Step 3: Manual recovery guidance
            logger.critical("Automatic rollback failed. Manual recovery needed.")
            print_recovery_steps(modified_files)
```

**Rollback steps printed to user:**

```
Automatic rollback failed!

Manual recovery:
  1. Check which files were modified:
     $ git status
  
  2. Review patch conflicts:
     $ git diff
  
  3. Option A - Keep local changes:
     $ git add <files>
     $ git commit -m "Partial patch with fixes"
  
  4. Option B - Discard and retry:
     $ git reset --hard <commit-before-patch>
     $ grafty apply-patch <patch-file>
  
  5. Contact support if issue persists.
```

### 5.4 Dry-Run Mode

**DryRunMode.SIMULATE:**

```python
if self.config.dry_run == DryRunMode.SIMULATE:
    logger.info(f"[DRY-RUN] Would commit: {files}")
    logger.info(f"[DRY-RUN] Would push to: {self.config.remote}")
    return {"commits_pushed": len(files), "dry_run": True}
```

**DryRunMode.STRICT:**

```python
if self.config.dry_run == DryRunMode.STRICT:
    # Perform all validation but raise error before execution
    status = self._validate_all_preconditions()
    if status['issues']:
        raise ValidationError(f"Issues found: {status['issues']}")
    # Don't execute - return validation results
    return {"validated": True, "issues": []}
```

---

## 6. Implementation Details

### 6.1 Git CLI vs Library

**Decision: Use `subprocess` with `git` CLI**

**Rationale:**
- GitPython adds dependency
- CLI is always available with Git installation
- Easier to test and debug
- Reduces attack surface
- Better error message transparency

**Wrapper approach:**

```python
class GitRepo:
    def _init_git_cli(self):
        """Initialize git CLI interface."""
        # Verify git is installed
        try:
            subprocess.run(['git', '--version'], 
                          capture_output=True, check=True)
        except FileNotFoundError:
            raise GitNotInitializedError("git command not found. Install Git.")
        
        # Return function that executes git commands
        def run_git(*args, **kwargs):
            try:
                result = subprocess.run(
                    ['git', '-C', str(self.repo_path)] + list(args),
                    capture_output=True,
                    text=True,
                    **kwargs
                )
                if result.returncode != 0:
                    raise GitCommandError(result.stderr)
                return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                raise GitCommandError(e.stderr)
        
        return run_git
```

### 6.2 File Path Handling

**Backup file location strategy:**

```
Option 1 (Default): Colocated
  /path/to/src/main.py
  /path/to/src/main.py.bak

Option 2 (Configured): Centralized
  /path/to/.bak/src/main.py.bak
  /path/to/.bak/src/file.txt.bak

Config:
  backup_dir = None        → Use colocated (.bak suffix)
  backup_dir = ".bak"      → Use centralized
  backup_dir = "/tmp"      → Use external directory
```

**Implementation:**

```python
def _find_backup_file(self, file_path: str) -> Optional[Path]:
    """Locate backup file for given path."""
    file_path = Path(file_path)
    
    # Search in configured backup_dir
    if self.config.backup_dir:
        backup_path = (
            Path(self.config.backup_dir) / 
            f"{file_path.name}.bak"
        )
        if backup_path.exists():
            return backup_path
    
    # Search colocated (.bak suffix)
    colocated_backup = file_path.parent / f"{file_path.name}.bak"
    if colocated_backup.exists():
        return colocated_backup
    
    return None
```

### 6.3 Logging & Audit Trail

```python
import logging

logger = logging.getLogger("grafty.vcs.git_integration")

# Log levels
logger.DEBUG    # Git command execution, parameter values
logger.INFO     # Major operations (commit, push, rollback)
logger.WARNING  # Non-fatal issues (network retry, partial success)
logger.ERROR    # Operation failures requiring user action
logger.CRITICAL # Unrecoverable failures (needs manual recovery)

# Example log entries
logger.info(f"Prepared for patch on branch: {branch}")
logger.debug(f"Running: git status --porcelain")
logger.warning(f"Push to {remote} failed, will retry later")
logger.error(f"No .bak files found. Manual recovery needed.")
logger.critical(f"Cannot rollback - state unknown!")
```

---

## 7. Code Examples

### 7.1 Basic Workflow

```python
from pathlib import Path
from grafty.vcs.git_integration import GitRepo, GitConfig, DryRunMode

# Initialize
config = GitConfig(
    auto_commit=True,
    auto_push=True,
    allow_dirty=False,
    dry_run=DryRunMode.OFF
)
repo = GitRepo("/path/to/repo", config)

# Pre-patch validation
try:
    status = repo.prepare_for_patch()
    print(f"✓ Ready on branch: {status['current_branch']}")
except Exception as e:
    print(f"✗ {e.message}")
    exit(1)

# Apply patch (external operation, creates .bak files)
try:
    apply_patch_file("/path/to/fix.patch")
except Exception as e:
    print(f"✗ Patch failed: {e}")
    exit(1)

# Commit changes
try:
    commit_hash = repo.stage_and_commit("Apply fix for issue #123")
    print(f"✓ Committed: {commit_hash}")
except Exception as e:
    print(f"✗ Commit failed: {e.message}")
    # Rollback
    repo.rollback_to_backup(repo.list_modified_files())
    exit(1)

# Push to remote
try:
    result = repo.push_to_remote()
    print(f"✓ Pushed {result['commits_pushed']} commits")
except Exception as e:
    print(f"⚠ Push failed: {e.message}")
    # On push failure, local commit is kept, suggest manual push
    print(f"  Suggestion: {e.suggestion}")
```

### 7.2 Dry-Run Testing

```python
# Test configuration before applying to production
config = GitConfig(
    auto_commit=True,
    auto_push=True,
    dry_run=DryRunMode.SIMULATE
)
repo = GitRepo("/path/to/repo", config)

# Pre-flight checks still run (real validation)
status = repo.prepare_for_patch()

# Actual operations are logged but not executed
commit_hash = repo.stage_and_commit("Test commit")
# Output: [DRY-RUN] Would stage files: [...]
# Output: [DRY-RUN] Would commit with message: "Test commit"

# When satisfied, run with dry_run=OFF
```

### 7.3 Error Recovery Pattern

```python
def safe_apply_patch(patch_file, repo_path):
    """Apply patch with automatic recovery on failure."""
    config = GitConfig(auto_commit=True, allow_dirty=False)
    repo = GitRepo(repo_path, config)
    
    # Capture pre-patch state for recovery
    pre_patch_commit = repo.get_last_commit()['hash']
    modified_files = []
    
    try:
        # Validate
        repo.prepare_for_patch()
        
        # Record which files will be modified
        modified_files = parse_patch_for_files(patch_file)
        
        # Apply
        apply_patch(patch_file)
        
        # Commit
        commit_hash = repo.stage_and_commit(
            f"Apply patch from {patch_file}"
        )
        
        return {
            "success": True,
            "commit": commit_hash,
            "files_modified": modified_files
        }
        
    except Exception as e:
        logger.error(f"Patch failed: {e}")
        
        # Attempt recovery
        try:
            logger.info("Attempting rollback...")
            result = repo.rollback_to_backup(modified_files)
            logger.info(f"Rollback successful. Restored: {result['restored_files']}")
        except Exception as rollback_error:
            logger.critical(f"Rollback failed: {rollback_error}")
            logger.critical(f"Manual intervention required!")
            return {
                "success": False,
                "error": str(e),
                "recovery_status": "MANUAL_REQUIRED",
                "suggestion": rollback_error.suggestion
            }
        
        return {
            "success": False,
            "error": str(e),
            "recovery_status": "AUTO_ROLLBACK_SUCCESS"
        }
```

### 7.4 CLI Integration Example

```python
import click
from grafty.vcs.git_integration import GitRepo, GitConfig, DryRunMode
from grafty.patching import apply_patch_file

@click.command()
@click.argument('patch_file', type=click.File('r'))
@click.option('--auto-commit', is_flag=True, help='Auto-commit after patch')
@click.option('--auto-push', is_flag=True, help='Auto-push after commit')
@click.option('--allow-dirty', is_flag=True, help='Allow uncommitted changes')
@click.option('--dry-run', 
              type=click.Choice(['off', 'simulate', 'strict']),
              default='off')
@click.option('--branch', default=None, help='Target branch')
def apply_patch(patch_file, auto_commit, auto_push, allow_dirty, dry_run, branch):
    """Apply a patch with optional Git integration."""
    
    # Build config
    config = GitConfig(
        auto_commit=auto_commit or auto_push,
        auto_push=auto_push,
        allow_dirty=allow_dirty,
        branch=branch,
        dry_run=DryRunMode(dry_run)
    )
    
    repo = GitRepo(".", config)
    
    try:
        # 1. Pre-flight checks
        status = repo.prepare_for_patch()
        click.echo(f"✓ Ready on {status['current_branch']}")
        
        # 2. Apply patch
        click.echo("Applying patch...")
        apply_patch_file(patch_file.name)
        click.echo("✓ Patch applied")
        
        # 3. Commit (if enabled)
        if config.auto_commit:
            commit_hash = repo.stage_and_commit(
                f"Apply patch: {patch_file.name}"
            )
            click.echo(f"✓ Committed: {commit_hash}")
        
        # 4. Push (if enabled)
        if config.auto_push:
            result = repo.push_to_remote()
            click.echo(f"✓ Pushed {result['commits_pushed']} commits")
        
        click.echo("✓ Complete!")
        
    except Exception as e:
        click.echo(f"✗ Error: {e.message}", err=True)
        if hasattr(e, 'suggestion'):
            click.echo(f"  Try: {e.suggestion}", err=True)
        exit(1)
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# tests/vcs/test_git_integration.py

import pytest
from unittest.mock import patch, MagicMock
from grafty.vcs.git_integration import GitRepo, GitConfig, DryRunMode
from grafty.vcs.errors import DirtyWorkingTreeError, GitNotInitializedError

class TestGitRepoValidation:
    def test_prepare_for_patch_clean_repo(self):
        """Happy path: clean repo, valid branch."""
        config = GitConfig()
        repo = GitRepo(".", config)
        status = repo.prepare_for_patch()
        assert status['is_clean'] == True
        assert 'current_branch' in status
    
    def test_prepare_for_patch_dirty_tree(self):
        """Error: uncommitted changes without --allow-dirty."""
        config = GitConfig(allow_dirty=False)
        repo = GitRepo(".", config)
        with pytest.raises(DirtyWorkingTreeError):
            repo.prepare_for_patch()
    
    def test_prepare_for_patch_allow_dirty(self):
        """Allow dirty tree when flag set."""
        config = GitConfig(allow_dirty=True)
        repo = GitRepo(".", config)
        status = repo.prepare_for_patch()
        # Should not raise, even if dirty

class TestCommitOperations:
    def test_stage_and_commit_all_files(self):
        """Commit all changes."""
        config = GitConfig()
        repo = GitRepo(".", config)
        commit_hash = repo.stage_and_commit("Test commit")
        assert len(commit_hash) == 7  # Short SHA
    
    def test_stage_and_commit_specific_files(self):
        """Commit only specified files."""
        config = GitConfig()
        repo = GitRepo(".", config)
        commit_hash = repo.stage_and_commit(
            "Test commit",
            files=["file1.py", "file2.py"]
        )
        assert commit_hash
    
    def test_stage_and_commit_no_changes(self):
        """Fail when nothing to commit."""
        config = GitConfig()
        repo = GitRepo(".", config)
        with pytest.raises(NoChangesError):
            repo.stage_and_commit("Empty commit")

class TestDryRunMode:
    def test_dry_run_simulate(self):
        """Simulate mode logs but doesn't execute."""
        config = GitConfig(dry_run=DryRunMode.SIMULATE)
        repo = GitRepo(".", config)
        result = repo.push_to_remote()
        assert result['dry_run'] == True
    
    def test_dry_run_strict(self):
        """Strict mode validates but doesn't execute."""
        config = GitConfig(dry_run=DryRunMode.STRICT)
        repo = GitRepo(".", config)
        result = repo.prepare_for_patch()
        assert result['validated'] == True
```

### 8.2 Integration Tests

```python
# tests/integration/test_apply_patch_workflow.py

def test_full_workflow_with_commit_and_push(tmp_git_repo):
    """End-to-end: patch → commit → push."""
    config = GitConfig(auto_commit=True, auto_push=True)
    repo = GitRepo(tmp_git_repo, config)
    
    # Prepare
    repo.prepare_for_patch()
    
    # Simulate patch (create modified file)
    test_file = Path(tmp_git_repo) / "test.py"
    test_file.write_text("modified content")
    
    # Commit
    commit = repo.stage_and_commit("Test patch")
    assert commit
    
    # Verify commit exists
    last_commit = repo.get_last_commit()
    assert last_commit['message'] == "Test patch"

def test_rollback_with_bak_files(tmp_git_repo, tmp_path):
    """Rollback restores files from .bak backup."""
    config = GitConfig(backup_dir=str(tmp_path / ".bak"))
    repo = GitRepo(tmp_git_repo, config)
    
    # Create backup file
    original_content = "original"
    backup_file = tmp_path / ".bak" / "test.py.bak"
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    backup_file.write_text(original_content)
    
    # Corrupt original
    test_file = Path(tmp_git_repo) / "test.py"
    test_file.write_text("corrupted")
    
    # Rollback
    result = repo.rollback_to_backup(["test.py"])
    
    # Verify restoration
    assert test_file.read_text() == original_content
    assert "test.py" in result['restored_files']
```

---

## 9. Implementation Phases

### Phase 1: Core Module (Week 1-2)

- [ ] Create `grafty/vcs/` package
- [ ] Implement `GitConfig` dataclass
- [ ] Implement `GitRepo` base class with subprocess wrapper
- [ ] Implement `prepare_for_patch()` with validation
- [ ] Implement `get_status()` and query methods
- [ ] Unit tests for validation

### Phase 2: Commit & Push (Week 2-3)

- [ ] Implement `stage_and_commit()`
- [ ] Implement `push_to_remote()`
- [ ] Error handling for push failures
- [ ] Integration tests

### Phase 3: Rollback & Safety (Week 3-4)

- [ ] Implement `rollback_to_backup()`
- [ ] Implement `reset_to_commit()` (fallback)
- [ ] Backup file location strategies
- [ ] Rollback error recovery

### Phase 4: CLI Integration (Week 4)

- [ ] Add flags to `apply-patch` command
- [ ] Update apply-patch workflow
- [ ] Dry-run mode testing
- [ ] End-to-end integration tests

### Phase 5: Documentation & Testing (Week 5)

- [ ] User documentation
- [ ] Error message review
- [ ] Performance testing
- [ ] Security audit

---

## 10. Backward Compatibility

All VCS features are **opt-in**:

```python
# Default config: backward compatible
config = GitConfig()
# auto_commit = False (disabled)
# auto_push = False (disabled)
# allow_dirty = False
# dry_run = DryRunMode.OFF

# Existing calls still work:
repo = GitRepo(".", config)
# No validation performed unless prepare_for_patch() called
# Git operations disabled by default
```

**Migration Path:**

1. **Phase 1:** Deploy with flags disabled (no behavior change)
2. **Phase 2:** Optional adoption via `--auto-commit`
3. **Phase 3:** Recommended for CI/CD pipelines
4. **Phase 4:** Document best practices

---

## 11. Security Considerations

### 11.1 Credential Handling

- **SSH Keys:** Use system SSH agent (`git` handles automatically)
- **HTTPS:** Use system credential manager or cached credentials
- **Tokens:** Store in `.git/config` (user responsibility)
- **No embedded credentials** in log files or error messages

### 11.2 File Path Safety

- **Validate paths** are within repo directory (no `/etc/passwd` tricks)
- **Sanitize** commit messages (user-provided, logged)
- **Escape** shell arguments (use list form in subprocess)

```python
# ✓ Safe
subprocess.run(['git', 'commit', '-m', message], ...)

# ✗ Dangerous (shell injection)
subprocess.run(f'git commit -m "{message}"', shell=True, ...)
```

### 11.3 Error Message Exposure

- **Do not expose** full stack traces to users
- **Sanitize** file paths (show relative paths only)
- **Do not reveal** system paths or usernames in errors
- **Log detailed errors** to files, show user-friendly summaries

---

## 12. Future Enhancements

### 12.1 Planned Features

- **Multi-branch support:** Apply patches across multiple branches
- **Stash integration:** Auto-stash dirty changes instead of erroring
- **Signed commits:** GPG signing support
- **Release automation:** Tag and release after patch
- **Webhook integration:** Notify Slack/Teams on push
- **Partial rollback:** Rollback only specific files while keeping others

### 12.2 Metrics & Observability

- Track patch success/failure rates
- Monitor push latency to remotes
- Alert on repeated failures
- Dashboard: patch application trends

---

## 13. References

### Class Diagram

```
┌─────────────────────────────────┐
│      GitConfig (dataclass)      │
├─────────────────────────────────┤
│ - auto_commit: bool             │
│ - auto_push: bool               │
│ - allow_dirty: bool             │
│ - branch: Optional[str]         │
│ - remote: str                   │
│ - dry_run: DryRunMode           │
│ - use_backups: bool             │
│ - backup_dir: Optional[str]     │
└─────────────────────────────────┘
           △
           │ uses
           │
┌─────────────────────────────────┐
│      GitRepo (main class)       │
├─────────────────────────────────┤
│ - repo_path: Path               │
│ - config: GitConfig             │
│ - git: Callable                 │
├─────────────────────────────────┤
│ + prepare_for_patch()           │
│ + stage_and_commit(msg, files)  │
│ + push_to_remote()              │
│ + rollback_to_backup(files)     │
│ + reset_to_commit(sha, files)   │
│ + get_status()                  │
│ + get_last_commit()             │
│ + list_modified_files()         │
│ + list_staged_files()           │
├─ (private) ─────────────────────┤
│ - _init_git_cli()               │
│ - _validate_repo()              │
│ - _check_working_tree()         │
│ - _get_current_branch()         │
│ - _validate_remote()            │
│ - _find_backup_file(path)       │
└─────────────────────────────────┘

Exceptions:
├─ GitIntegrationError (base)
│  ├─ GitNotInitializedError
│  ├─ DirtyWorkingTreeError
│  ├─ DetachedHeadError
│  ├─ InvalidBranchError
│  ├─ NoRemoteError
│  ├─ NetworkError
│  ├─ PermissionError
│  ├─ NoChangesError
│  ├─ NoBackupFilesError
│  ├─ BackupRestoreError
│  ├─ PartialPushError
│  └─ GitCommandError
```

### Sequence Diagram: Happy Path

```
User                CLI              GitRepo             Git CLI
│                   │                │                   │
├──apply-patch──────→│                │                   │
│                   │─prepare_for_patch──→│               │
│                   │                │────status────────→ │
│                   │                │←─(clean, on main)──│
│                   │                │←──return status────│
│                   │←─(validated)────│                   │
│                   │                │                   │
│                   │─apply_patch()──→│                   │
│                   │←(patch applied)  │                   │
│                   │                │                   │
│                   │─stage_and_commit→│                   │
│                   │                │───add files───────→│
│                   │                │←──(success)────────│
│                   │                │───commit───────────→│
│                   │                │←──(abc1234)────────│
│                   │                │←──return commit────│
│                   │                │                   │
│                   │─push_to_remote──→│                   │
│                   │                │───push to origin──→│
│                   │                │←──(success)────────│
│                   │                │←──return success───│
│                   │←─(success!)─────│                   │
│←────✓ Complete────│                │                   │
│                   │                │                   │
```

---

## 14. Appendix: Configuration Examples

### Example 1: Minimal Setup

```python
from grafty.vcs.git_integration import GitRepo, GitConfig

config = GitConfig()  # All defaults
repo = GitRepo(".", config)
```

### Example 2: Full CI/CD Setup

```python
config = GitConfig(
    auto_commit=True,
    auto_push=True,
    allow_dirty=False,
    branch="develop",
    remote="origin",
    dry_run=DryRunMode.OFF,
    use_backups=True,
    backup_dir=".git-backups"
)
repo = GitRepo("/workspace", config)
```

### Example 3: Conservative Setup (Testing)

```python
config = GitConfig(
    auto_commit=True,
    auto_push=False,  # Manual push review
    allow_dirty=False,
    dry_run=DryRunMode.SIMULATE  # Test mode
)
repo = GitRepo(".", config)
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-08  
**Status:** APPROVED FOR IMPLEMENTATION
