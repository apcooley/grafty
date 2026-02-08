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
from .patch import git_apply_check, format_patch_summary
from .utils import truncate_text


@click.group()
def cli():
    """Token-optimized structural editor for code/text files."""
    pass


@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def index(paths: List[str], output_json: bool) -> None:
    """Index files and list all structural units."""
    if not paths:
        paths = ["."]

    indexer = Indexer()
    indices = {}

    for path in paths:
        p = Path(path)
        if p.is_file():
            indices[path] = indexer.index_file(path)
        else:
            indices.update(indexer.index_directory(path))

    if output_json:
        # Output JSON
        output = {path: idx.to_dict() for path, idx in indices.items()}
        click.echo(json.dumps(output, indent=2))
    else:
        # Human-readable
        for path, idx in sorted(indices.items()):
            click.echo(f"\n{path} ({len(idx.nodes)} nodes)")
            for node in idx.nodes:
                indent = "  " if node.parent_id else ""
                click.echo(
                    f"{indent}[{node.kind:15}] {node.name:40} "
                    f"({node.start_line:4}-{node.end_line:4})"
                )


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
    - Structural: file.py:py_function:my_func
    - Line-based: file.py:42 or file.py:42-50
    - Fuzzy: my_func (searches all nodes)
    
    Examples:
    - grafty show "src/main.py:py_function:parse_config"
    - grafty show "file.py:42"          # Line number selector
    - grafty show "file.py:42-50"       # Line range
    - grafty show "process"             # Fuzzy search
    """
    # Index all files
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

    # TODO: Implement insert command with proper mutation
    # insertion_text = text or Path(file).read_text(encoding="utf-8")
    #
    # if line:
    #     # Absolute line insertion
    #     pass
    # elif selector:
    #     # Relative to selector
    #     indexer = Indexer()
    #     indices = indexer.index_directory(repo_root)
    #     resolver = Resolver(indices)
    #     result = resolver.resolve(selector)
    #
    #     if not result.is_resolved():
    #         click.echo(f"Error: {result.error or 'Ambiguous selector'}", err=True)
    #         sys.exit(1)
    #
    #     node = result.exact_match

    click.echo("insert command: TODO (full implementation coming soon)")


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


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
