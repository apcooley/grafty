"""
test_markdown_parser_bugs.py — Tests for Markdown parser bugs (v0.5.1 hotfix).

Bug #1: md_heading Replacement Appends Instead of Replaces
- When replacing an md_heading with code block, old content remains
- end_line doesn't include closing code fences

Bug #2: Markdown Parser Treats Code Comments as Headings
- Bash comments inside code fences (# ...) parsed as md_heading nodes
- Causes "Ambiguous selector" errors
"""

import tempfile
from pathlib import Path
from grafty.parsers.markdown_ts import MarkdownParser
from grafty.models import FileIndex
from grafty.editor import Editor


class TestBug1HeadingWithCodeBlock:
    """Test Bug #1: md_heading replacement with code blocks."""

    def test_heading_with_single_line_code_block(self):
        """Test heading with a single line code block."""
        content = """# Main Heading

Some intro text.

## Step 1

Here's a code example:

```bash
echo "hello"
```

Rest of content.
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text(content)

            parser = MarkdownParser()
            nodes = parser.parse_file(str(md_file))

            # Find the "Step 1" heading
            step1 = next(n for n in nodes if n.kind == "md_heading" and n.name == "Step 1")

            # end_line should NOT include the code block closing fence
            # The code block should be within the heading's extent
            original_end = step1.end_line
            assert original_end > step1.start_line

    def test_heading_with_multiline_code_block(self):
        """Test heading with multi-line code block."""
        content = """# Main Heading

## Step 2

Implementation example:

```python
def example():
    print("test")
    return True
```

## Step 3

Another section.
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text(content)

            parser = MarkdownParser()
            nodes = parser.parse_file(str(md_file))

            step2 = next(n for n in nodes if n.kind == "md_heading" and n.name == "Step 2")
            step3 = next(n for n in nodes if n.kind == "md_heading" and n.name == "Step 3")

            # Step 2 should end before Step 3 starts
            assert step2.end_line < step3.start_line
            # Step 2's extent should include the code block
            assert step2.end_line >= 9  # Code block ends at line 9

    def test_replace_heading_with_code_block_no_duplication(self):
        """Test that replacing a heading with code block doesn't leave old content."""
        content = """# Main

## Step 3

```bash
old code here
```

## Next Section

More content.
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text(content)

            parser = MarkdownParser()
            nodes = parser.parse_file(str(md_file))

            step3 = next(n for n in nodes if n.kind == "md_heading" and n.name == "Step 3")

            # Create editor and replace
            file_index = FileIndex(
                path=str(md_file),
                content_hash="dummy",
                mtime=0,
                nodes=nodes,
            )
            editor = Editor(file_index)

            new_content = """## Step 3

```bash
new code here
different code
```"""

            editor.replace(step3, new_content)
            result = editor.current_content

            # Verify "old code here" is NOT in the result
            assert "old code here" not in result
            # Verify "new code here" IS in the result
            assert "new code here" in result
            # Verify next section is still there
            assert "## Next Section" in result


class TestBug2CodeCommentsAsHeadings:
    """Test Bug #2: Code fence comments wrongly extracted as headings."""

    def test_code_fence_with_bash_comments(self):
        """Test that bash comments in code blocks are NOT extracted as headings."""
        content = """# Real Heading 1

Some intro.

## Real Heading 2

Here's a bash script:

```bash
# This is a comment, not a heading
echo "Hello"
# Another comment
grafty show "file.py"
```

## Real Heading 3

More content.
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text(content)

            parser = MarkdownParser()
            nodes = parser.parse_file(str(md_file))

            # Filter to only real headings (md_heading, not preambles)
            headings = [n for n in nodes if n.kind == "md_heading"]

            # Should only find 3 real headings, NOT the bash comments
            assert len(headings) == 3
            heading_names = {h.name for h in headings}
            assert heading_names == {"Real Heading 1", "Real Heading 2", "Real Heading 3"}

    def test_code_fence_with_markdown_heading_syntax(self):
        """Test that # inside code blocks is not treated as heading."""
        content = """# Intro

```bash
# Build the project
cargo build --release
# Run tests
cargo test
```

# Another Heading

Done.
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text(content)

            parser = MarkdownParser()
            nodes = parser.parse_file(str(md_file))

            headings = [n for n in nodes if n.kind == "md_heading"]

            # Only 2 real headings, not the # comments in the code block
            assert len(headings) == 2
            heading_names = {h.name for h in headings}
            assert heading_names == {"Intro", "Another Heading"}

    def test_nested_code_fences_with_comments(self):
        """Test nested code blocks with # comments."""
        content = """# Top

Introduction.

## Config

Here's the config:

```yaml
# Main configuration
apps:
  # App 1
  - name: app1
    # Settings
    port: 8080
```

## Final

Done.
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text(content)

            parser = MarkdownParser()
            nodes = parser.parse_file(str(md_file))

            headings = [n for n in nodes if n.kind == "md_heading"]

            # Only 3 real headings
            assert len(headings) == 3
            heading_names = {h.name for h in headings}
            assert heading_names == {"Top", "Config", "Final"}

    def test_mixed_real_headings_and_code_comments_no_ambiguity(self):
        """Test that code comments don't cause ambiguous selector errors."""
        content = """# Getting Started

## Installation

```bash
# Install grafty
pip install grafty

# Verify installation
grafty --version
```

## Usage

```bash
# Show a function
grafty show "file.py:py_function:my_func"

# Or use a heading selector
# Important: code comments should not interfere
```

## Advanced

More docs.
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text(content)

            parser = MarkdownParser()
            nodes = parser.parse_file(str(md_file))

            headings = [n for n in nodes if n.kind == "md_heading"]

            # Should find exactly 4 real headings, not confused by code comments
            assert len(headings) == 4
            heading_names = {h.name for h in headings}
            assert heading_names == {"Getting Started", "Installation", "Usage", "Advanced"}

            # Each heading should be unique (no duplicates from code comments)
            assert len(headings) == len(heading_names)
