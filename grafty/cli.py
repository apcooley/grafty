"""
cli.py - Command-line interface for grafty.
"""
import sys
import json
from pathlib import Path
from typing import Optional, List

import click

from .indexer import Indexer
from .selectors import Resolver
from .editor import Editor
from .models import Node
from .patch import git_apply_check, format_patch_summary
from .utils import truncate_text
from .multi_file_patch import PatchSet


def _print_human_readable(indices: dict) -> None:
    """Print index in human-readable format with smart column widths."""
    for file_path, idx in sorted(indices.items()):
        # Build nodes_by_id lookup for this file
        nodes_by_id = {node.id: node for node in idx.nodes}
        
        # First pass: calculate max column widths
        max_kind = len("KIND")
        max_name = len("NODE NAME")
        max_lines = len("LINES")
        
        for node in idx.nodes:
            nested_path = _compute_nested_path(node, nodes_by_id)
            max_kind = max(max_kind, len(node.kind))
            max_name = max(max_name, len(nested_path))
            # Line range format: "4-180" (no padding)
            lines_str = f"{node.start_line}-{node.end_line}"
            max_lines = max(max_lines, len(lines_str))
        
        # Add 1-2 chars padding
        max_kind += 1
        max_name += 2
        max_lines += 1
        
        # Header
        click.echo(f"\n{'═' * (max_kind + max_name + max_lines + 6)}")
        click.echo(f"FILE: {file_path} ({len(idx.nodes)} nodes)")
        click.echo(f"{'═' * (max_kind + max_name + max_lines + 6)}")
        
        # Column headers
        click.echo(
            f"{'KIND':<{max_kind}} │ {'NODE NAME':<{max_name}} │ {'LINES':>{max_lines}}"
        )
        click.echo(
            f"{'-' * (max_kind - 1)}─┼─{'-' * (max_name - 1)}─┼─{'-' * (max_lines - 1)}"
        )
        
        # Data rows (no indentation, paths already show hierarchy with /)
        for node in idx.nodes:
            nested_path = _compute_nested_path(node, nodes_by_id)
            lines_str = f"{node.start_line}-{node.end_line}"
            
            click.echo(
                f"{node.kind:<{max_kind}} │ {nested_path:<{max_name}} │ {lines_str:>{max_lines}}"
            )


def _format_toon(indices: dict) -> str:
    """Format as Token Optimized Object Notation (compact, structured)."""
    lines = []
    
    for file_path, idx in sorted(indices.items()):
        lines.append(f"# {file_path} ({len(idx.nodes)} nodes)")
        
        # Build nodes_by_id lookup
        nodes_by_id = {node.id: node for node in idx.nodes}
        
        for node in idx.nodes:
            nested_path = _compute_nested_path(node, nodes_by_id)
            # No indentation - path already shows hierarchy with /
            # TOON format: kind | path | lines (compact, no quotes)
            lines.append(
                f"{node.kind} | {nested_path} | {node.start_line}-{node.end_line}"
            )
    
    return "\n".join(lines)


def _compute_nested_path(node: Node, nodes_by_id: dict) -> str:
    """Compute nested path for a node (e.g., 'Parent/Child/GrandChild')."""
    parts = [node.name]
    current = node
    
    while current.parent_id:
        parent = nodes_by_id.get(current.parent_id)
        if parent:
            parts.insert(0, parent.name)
            current = parent
        else:
            break
    
    return "/".join(parts)


def _show_node(
    node: Node,
    output_json: bool = False,
    max_lines: int = 50,
    max_chars: int = 2000,
) -> None:
    """Display a node's content (helper function)."""
    # Read node content
    p = Path(node.path)
    content = p.read_text(encoding="utf-8")
    lines = content.splitlines()

    start_idx = node.start_line - 1
    end_idx = node.end_line
    node_text = "\n".join(lines[start_idx:end_idx])

    if output_json:
        output = {
            "node": node.to_dict(),
            "text": node_text,
        }
        click.echo(json.dumps(output, indent=2))
    else:
        # Truncate for display
        truncated = truncate_text(node_text, max_chars=max_chars, max_lines=max_lines)
        click.echo(f"Node: {node.qualname or node.name} ({node.kind})")
        click.echo(f"File: {node.path} (lines {node.start_line}-{node.end_line})")
        click.echo("\n" + truncated)


@click.group()
def cli():
    """Token-optimized structural editor for code/text files."""
    pass


@cli.command()
@click.argument("paths", nargs=-1, type=str)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--toon", is_flag=True, help="Output as Token Optimized Object Notation (compact)")
def index(paths: List[str], output_json: bool, toon: bool) -> None:
    """Index files and list all structural units."""
    if not paths:
        paths = ["."]

    indexer = Indexer()
    indices = {}

    for path in paths:
        # Expand tilde and resolve to absolute path
        p = Path(path).expanduser().resolve()
        
        if not p.exists():
            click.echo(f"Error: Path does not exist: {path}", err=True)
            sys.exit(1)
        
        if p.is_file():
            indices[str(p)] = indexer.index_file(str(p))
        else:
            indices.update(indexer.index_directory(str(p)))

    if output_json:
        # Output JSON
        output = {path: idx.to_dict() for path, idx in indices.items()}
        click.echo(json.dumps(output, indent=2))
    elif toon:
        # Token Optimized Object Notation (compact JSON-like format)
        output = _format_toon(indices)
        click.echo(output)
    else:
        # Human-readable with headers and aligned columns
        _print_human_readable(indices)


@cli.command()
@click.argument("pattern")
@click.option("--path", type=str, help="Limit search to path pattern (e.g., src/)")
@click.option("--kind", type=str, help="Limit to node kind (e.g., py_function)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--repo-root", type=click.Path(), default=".", help="Repository root")
def search(
    pattern: str, path: Optional[str], kind: Optional[str],
    output_json: bool, repo_root: str
) -> None:
    """
    Search nodes by glob pattern (Phase 3.3).

    Examples:
    - grafty search "*validate*"        # Find all nodes with 'validate'
    - grafty search "test_*"             # Find all nodes starting with 'test_'
    - grafty search "*_test" --path src/ # Find nodes ending with '_test' in src/
    """
    indexer = Indexer()
    indices = indexer.index_directory(repo_root)
    resolver = Resolver(indices)

    # Build selector for query_nodes_by_path_glob
    if path and kind:
        selector = f"{path}:{kind}:{pattern}"
        results = resolver.query_nodes_by_path_glob(selector)
    elif path:
        selector = f"{path}:*:{pattern}"
        results = resolver.query_nodes_by_path_glob(selector)
    elif kind:
        # Query all paths with specific kind
        results = [n for n in resolver.query_nodes_by_pattern(pattern) if n.kind == kind]
    else:
        # Just pattern search
        results = resolver.query_nodes_by_pattern(pattern)

    if output_json:
        output = {
            "pattern": pattern,
            "count": len(results),
            "nodes": [n.to_dict() for n in results],
        }
        click.echo(json.dumps(output, indent=2))
    else:
        if not results:
            click.echo(f"No nodes matching pattern: {pattern}")
        else:
            click.echo(f"Found {len(results)} nodes matching '{pattern}':\n")
            for node in results[:20]:  # Limit to 20 results
                path_spec = f"{node.path}:{node.start_line}-{node.end_line}"
                click.echo(f"[{node.kind:15}] {node.name:40} {path_spec}")
            if len(results) > 20:
                click.echo(f"\n... and {len(results) - 20} more")


@cli.command()
@click.argument("selector")
@click.option("--max-lines", type=int, default=50, help="Max lines to show")
@click.option("--max-chars", type=int, default=2000, help="Max chars to show")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--repo-root", type=click.Path(), default=".", help="Repository root")
def show(selector: str, max_lines: int, max_chars: int, output_json: bool, repo_root: str) -> None:
    """
    Show a node by selector.

    Selector formats (Phase 3):
    - ID-based: abc123def456
    - Structural: file.py:py_function:my_func (parses file on-demand)
    - Line-based: file.py:42 or file.py:42-50
    - Fuzzy: my_func (searches all nodes)

    Examples:
    - grafty show "src/main.py:py_function:parse_config"
    - grafty show "file.py:42"          # Line number selector
    - grafty show "file.py:42-50"       # Line range
    - grafty show "process"             # Fuzzy search
    """
    from pathlib import Path

    # If selector has path:kind:name format, parse that file on-demand (zero persistence)
    if ":" in selector and not selector[0].isalnum():
        parts = selector.split(":", 2)
        if len(parts) >= 2:
            maybe_file = parts[0]
            file_path = Path(maybe_file).expanduser().resolve()
            
            # Try parsing the specific file
            if file_path.is_file():
                try:
                    indexer = Indexer()
                    file_index = indexer.index_file(str(file_path))
                    indices = {str(file_path): file_index}
                    
                    resolver = Resolver(indices)
                    result = resolver.resolve(selector)
                    
                    if result.is_resolved():
                        node = result.exact_match
                        assert node is not None
                        
                        # Show node content
                        _show_node(node, output_json, max_lines, max_chars)
                        return
                except Exception:
                    pass  # Fall through to fuzzy search below

    # Fallback: index repo_root and do fuzzy/ambiguous search
    indexer = Indexer()
    indices = indexer.index_directory(repo_root)

    # Resolve selector
    resolver = Resolver(indices)
    result = resolver.resolve(selector)

    if not result.is_resolved():
        if result.candidates:
            click.echo("Ambiguous selector. Did you mean:", err=True)
            for node in result.candidates[:5]:
                click.echo(
                    f"  {node.path}:{node.kind}:{node.name}",
                    err=True,
                )
            click.echo("\nUse full path:kind:name format to disambiguate.", err=True)
            sys.exit(1)
        else:
            # Improved error message (Phase 3)
            error_msg = result.error or f"Selector '{selector}' did not resolve"
            click.echo(f"Error: {error_msg}", err=True)
            click.echo("\nTip: Use 'grafty index <path>' to see available nodes.", err=True)
            sys.exit(1)

    node = result.exact_match
    assert node is not None
    
    _show_node(node, output_json, max_lines, max_chars)


@cli.command()
@click.argument("selector")
@click.option("--text", type=str, help="Replacement text")
@click.option("--file", type=click.Path(exists=True), help="Read replacement from file")
@click.option("--patch-out", type=click.Path(), help="Write patch to file")
@click.option("--apply", is_flag=True, help="Apply changes to file")
@click.option("--dry-run", is_flag=True, help="Show patch but don't write")
@click.option("--force", is_flag=True, help="Skip file drift checks")
@click.option("--backup", is_flag=True, help="Create .bak backup")
@click.option("--repo-root", type=click.Path(), default=".", help="Repository root")
def replace(
    selector: str,
    text: Optional[str],
    file: Optional[str],
    patch_out: Optional[str],
    apply: bool,
    dry_run: bool,
    force: bool,
    backup: bool,
    repo_root: str,
) -> None:
    """
    Replace a node or line range.

    Selector formats (Phase 3):
    - Structural: file.py:py_function:main
    - Line-based: file.py:42 (single) or file.py:42-50 (range)
    - Fuzzy: my_func

    Examples:
    - grafty replace "src/main.py:py_function:old_impl" --text "def old_impl(): return 42" --apply
    - grafty replace "file.py:42-50" --file new_impl.py --apply
    - grafty replace "main.py:10" --text "new_line" --apply

    Options:
    - --text: Inline replacement text
    - --file: Read replacement from file
    - --apply: Apply changes to file (default: dry-run shows patch)
    - --backup: Create .bak backup before applying
    - --force: Skip drift detection
    - --patch-out: Save patch to file
    """
    if not text and not file:
        click.echo("Error: Must provide --text or --file", err=True)
        sys.exit(1)

    if text and file:
        click.echo("Error: Can't specify both --text and --file", err=True)
        sys.exit(1)

    replacement_text = text or Path(file).read_text(encoding="utf-8")

    # Index and resolve
    indexer = Indexer()
    indices = indexer.index_directory(repo_root)
    resolver = Resolver(indices)

    # Try to resolve selector - might be line number format
    result = resolver.resolve(selector)

    if not result.is_resolved():
        # Improved error message (Phase 3)
        if result.candidates:
            click.echo("Ambiguous selector. Did you mean:", err=True)
            for node in result.candidates[:5]:
                click.echo(
                    f"  {node.path}:{node.kind}:{node.name}",
                    err=True,
                )
            click.echo("\nUse full path:kind:name format to disambiguate.", err=True)
        else:
            error_msg = result.error or f"Selector '{selector}' did not resolve"
            click.echo(f"Error: {error_msg}", err=True)
            formats = "path:kind:name | path:line | path:line-line | fuzzy_name"
            click.echo(f"\nFormats: {formats}", err=True)
        sys.exit(1)

    node = result.exact_match
    assert node is not None

    file_index = indices[node.path]
    editor = Editor(file_index)
    editor.replace(node, replacement_text)

    patch = editor.generate_patch()

    # Show patch
    click.echo(patch)

    # Write patch file if requested
    if patch_out:
        Path(patch_out).write_text(patch)
        click.echo(f"Patch written to {patch_out}")

    # Apply if not dry-run
    if not dry_run and apply:
        editor.write(force=force, backup=backup)
        click.echo(f"Applied changes to {node.path}")


@cli.command()
@click.option("--line", type=int, help="Insert at line number")
@click.argument("selector", required=False)
@click.option("--before", is_flag=True, help="Insert before selector")
@click.option("--after", is_flag=True, help="Insert after selector")
@click.option("--inside-start", is_flag=True, help="Insert at start of block")
@click.option("--inside-end", is_flag=True, help="Insert at end of block")
@click.option("--text", type=str, help="Text to insert")
@click.option("--file", type=click.Path(exists=True), help="Read text from file")
@click.option("--patch-out", type=click.Path(), help="Write patch to file")
@click.option("--apply", is_flag=True, help="Apply changes")
@click.option("--dry-run", is_flag=True, help="Show patch but don't write")
@click.option("--force", is_flag=True, help="Skip drift checks")
@click.option("--backup", is_flag=True, help="Create .bak backup")
@click.option("--repo-root", type=click.Path(), default=".", help="Repository root")
def insert(
    line: Optional[int],
    selector: Optional[str],
    before: bool,
    after: bool,
    inside_start: bool,
    inside_end: bool,
    text: Optional[str],
    file: Optional[str],
    patch_out: Optional[str],
    apply: bool,
    dry_run: bool,
    force: bool,
    backup: bool,
    repo_root: str,
) -> None:
    """
    Insert text at a line number or relative to a selector.

    Insertion modes:
    - --line N: Insert at line N (absolute)
    - --before: Insert before selector
    - --after: Insert after selector
    - --inside-start: Insert at start of selector block
    - --inside-end: Insert at end of selector block

    Examples:
    - grafty insert --line 42 --text "new line" --apply
    - grafty insert "file.py:py_class:MyClass" --inside-end --text "def new_method(): pass" --apply
    - grafty insert "file.py:py_function:main" --before --file header.txt --apply

    Options:
    - --text: Inline text to insert
    - --file: Read text from file
    - --apply: Apply changes (default: dry-run shows patch)
    """
    if not text and not file:
        click.echo("Error: Must provide --text or --file", err=True)
        sys.exit(1)

    # Insert command is Phase 5+ (future work)
    # See ROADMAP.md for details
    click.echo("insert command: Phase 5+ (future implementation)", err=True)
    click.echo("See ROADMAP.md for Phase 5 features")


@cli.command()
@click.argument("selector")
@click.option("--patch-out", type=click.Path(), help="Write patch to file")
@click.option("--apply", is_flag=True, help="Apply changes")
@click.option("--dry-run", is_flag=True, help="Show patch but don't write")
@click.option("--force", is_flag=True, help="Skip drift checks")
@click.option("--backup", is_flag=True, help="Create .bak backup")
@click.option("--repo-root", type=click.Path(), default=".", help="Repository root")
def delete(
    selector: str,
    patch_out: Optional[str],
    apply: bool,
    dry_run: bool,
    force: bool,
    backup: bool,
    repo_root: str,
) -> None:
    """
    Delete a node or line range.

    Selector formats (Phase 3):
    - Structural: file.py:py_function:unused_fn
    - Line-based: file.py:42-50
    - Fuzzy: unused_fn

    Examples:
    - grafty delete "src/utils.py:py_function:unused_fn" --apply
    - grafty delete "file.py:42-50" --apply --backup
    - grafty delete "old_code" --dry-run  # See patch first

    Options:
    - --apply: Apply deletion (default: dry-run shows patch)
    - --backup: Create .bak backup before applying
    - --patch-out: Save patch to file
    """
    # Index and resolve
    indexer = Indexer()
    indices = indexer.index_directory(repo_root)
    resolver = Resolver(indices)
    result = resolver.resolve(selector)

    if not result.is_resolved():
        click.echo(f"Error: {result.error or 'Ambiguous selector'}", err=True)
        sys.exit(1)

    node = result.exact_match
    assert node is not None

    file_index = indices[node.path]
    editor = Editor(file_index)
    editor.delete(node)

    patch = editor.generate_patch()

    # Show patch
    click.echo(patch)

    # Write patch file if requested
    if patch_out:
        Path(patch_out).write_text(patch)
        click.echo(f"Patch written to {patch_out}")

    # Apply if not dry-run
    if not dry_run and apply:
        editor.write(force=force, backup=backup)
        click.echo(f"Deleted from {node.path}")


@cli.command()
@click.argument("patch_file", type=click.Path(exists=True))
@click.option("--repo-root", type=click.Path(), default=".", help="Repository root")
def check(patch_file: str, repo_root: str) -> None:
    """Validate patch applicability."""
    patch_content = Path(patch_file).read_text(encoding="utf-8")

    success, output = git_apply_check(patch_content, repo_root)

    if success:
        click.echo("✓ Patch is valid")
        click.echo(format_patch_summary(patch_content))
    else:
        click.echo("✗ Patch validation failed:", err=True)
        click.echo(output, err=True)
        sys.exit(1)


@cli.command()
@click.argument("patch_file", type=click.Path(exists=True))
@click.option("--format", type=click.Choice(["json", "simple"]), default="simple",
              help="Patch file format (simple: file:op:start:end:text, json: list of mutations)")
@click.option("--apply", is_flag=True, help="Apply changes to files (default: dry-run)")
@click.option("--backup", is_flag=True, help="Create .bak backups before applying")
@click.option("--repo-root", type=click.Path(), default=".", help="Repository root")
@click.option("--force", is_flag=True, help="Skip drift validation")
@click.option(
    "--auto-commit",
    is_flag=True,
    help="Automatically commit changes after applying patch",
)
@click.option(
    "--auto-push", is_flag=True, help="Automatically push to remote after commit"
)
@click.option(
    "--commit-message",
    type=str,
    default="Apply grafty patch",
    help="Custom commit message",
)
@click.option(
    "--allow-dirty",
    is_flag=True,
    help="Allow committing with dirty working directory",
)
def apply_patch(
    patch_file: str,
    format: str,
    apply: bool,
    backup: bool,
    repo_root: str,
    force: bool,
    auto_commit: bool,
    auto_push: bool,
    commit_message: str,
    allow_dirty: bool,
) -> None:
    """
    Apply atomic multi-file patches (Phase 4.1, Phase 4.2 with VCS).

    Supports two patch file formats:

    1. Simple format (default, one per line):
       file_path:operation_kind:start_line:end_line[:text]

       Example:
         src/main.py:replace:10:12:def new_func(): pass
         src/config.py:insert:5:5:    enabled = True
         src/old.py:delete:1:10:

    2. JSON format (--format json):
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

    VCS Integration (Phase 4.2):
    - --auto-commit: Create a commit after applying patch
    - --auto-push: Push to remote after commit
    - --commit-message: Custom commit message (default: "Apply grafty patch")
    - --allow-dirty: Allow commits even with uncommitted changes in working dir

    Examples:
    - grafty apply-patch patch.txt                    # Dry-run, simple format
    - grafty apply-patch patch.json --format json --apply  # Apply JSON patch
    - grafty apply-patch patch.txt --apply --backup   # Apply with backups
    - grafty apply-patch patch.txt --apply --auto-commit --auto-push  # Apply + commit + push
    - grafty apply-patch patch.txt --apply --auto-commit -m "Update API"  # Custom message
    """
    from .vcs import GitRepo, GitConfig, NotAGitRepo, DirtyRepo

    patch_set = PatchSet()

    # Load patch file
    patch_content = Path(patch_file).read_text(encoding="utf-8")

    try:
        if format == "json":
            patch_set.load_from_json(patch_content)
        else:  # simple format
            patch_set.load_from_simple_format(patch_content)
    except ValueError as e:
        click.echo(f"Error parsing patch file: {e}", err=True)
        sys.exit(1)

    if not patch_set.mutations:
        click.echo("Error: No mutations found in patch file", err=True)
        sys.exit(1)

    # Always validate first
    validation = patch_set.validate_all(repo_root)
    if not validation.success:
        click.echo(str(validation), err=True)
        sys.exit(1)

    # Generate and show diffs (dry-run)
    diffs = patch_set.generate_diffs(repo_root)
    if not diffs.success:
        click.echo(str(diffs), err=True)
        sys.exit(1)

    # Show diffs
    click.echo("=" * 70)
    click.echo(f"Multi-file patch preview ({len(diffs.diffs)} file(s))")
    click.echo("=" * 70)
    for file_path, diff in sorted(diffs.diffs.items()):
        click.echo(diff)

    click.echo("=" * 70)
    click.echo(str(diffs))
    click.echo("=" * 70)

    # Apply if flag is set
    if apply:
        # Prepare git config if auto-commit is requested
        git_config = None
        if auto_commit or auto_push:
            git_config = GitConfig(
                auto_commit=auto_commit,
                auto_push=auto_push,
                allow_dirty=allow_dirty,
                commit_message=commit_message,
                dry_run=False,
            )

            # Pre-flight checks if git is enabled
            try:
                git_repo = GitRepo(repo_root, git_config)
                git_repo.prepare_for_patch()
            except (NotAGitRepo, DirtyRepo) as e:
                click.echo(f"\n✗ Git check failed: {e}", err=True)
                sys.exit(1)

        result = patch_set.apply_atomic(
            repo_root=repo_root,
            backup=backup,
            force=force,
            git_config=git_config,
        )

        if result.success:
            click.echo("\n✓ Patch applied successfully")
            click.echo(str(result))
        else:
            click.echo("\n✗ Patch application failed", err=True)
            click.echo(str(result), err=True)
            sys.exit(1)
    else:
        click.echo("\n(Use --apply to apply changes)")


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
