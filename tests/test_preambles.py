"""
test_preambles.py — Tests for heading preambles (.md and .org files).

Preambles allow editing intro text without affecting subheadings.
"""
from pathlib import Path

from grafty.parsers.markdown_ts import MarkdownParser
from grafty.parsers.org import OrgParser
from grafty.indexer import Indexer
from grafty.selectors import Resolver


class TestMarkdownPreambles:
    """Test preamble extraction for Markdown headings."""

    def test_markdown_heading_with_children_has_preamble(self, tmp_repo):
        """Heading with children should have both full and preamble nodes."""
        content = """# Main

Intro text.

## Child 1

Child content.

## Child 2

More content.
"""
        md_file = tmp_repo / "test.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        nodes = parser.parse_file(str(md_file))

        # Check both versions exist
        full_nodes = [n for n in nodes if n.kind == "md_heading" and n.name == "Main"]
        preamble_nodes = [
            n for n in nodes if n.kind == "md_heading_preamble" and n.name == "Main"
        ]

        assert len(full_nodes) == 1, "Should have one full heading node"
        assert len(preamble_nodes) == 1, "Should have one preamble node"

        main_full = full_nodes[0]
        main_preamble = preamble_nodes[0]

        # Full includes children
        assert main_full.start_line == 1
        # End line depends on file structure; just verify preamble < full
        assert main_full.end_line > main_preamble.end_line

        # Preamble ends before first child
        assert main_preamble.start_line == 1
        # Preamble should end before first child
        assert main_preamble.end_line < main_full.end_line

    def test_markdown_preamble_excludes_first_child(self, tmp_repo):
        """Preamble should stop before first child heading."""
        content = """# Main

This is intro.

## Sub 1

Sub 1 content.

## Sub 2

Sub 2 content.
"""
        md_file = tmp_repo / "test.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        nodes = parser.parse_file(str(md_file))

        preamble = [n for n in nodes if n.kind == "md_heading_preamble"][0]

        # Preamble should end before Sub 1 (Sub 1 at line 5, so preamble ends at line 4)
        assert preamble.start_line == 1
        assert preamble.end_line == 4

    def test_markdown_heading_no_children_preamble_equals_full(self, tmp_repo):
        """Heading with no children: preamble = full section."""
        content = """# Main

Just intro.

# Another

More text.
"""
        md_file = tmp_repo / "test.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        nodes = parser.parse_file(str(md_file))

        main_full = [n for n in nodes if n.kind == "md_heading" and n.name == "Main"][0]
        main_preamble = [
            n for n in nodes if n.kind == "md_heading_preamble" and n.name == "Main"
        ][0]

        # For heading with no children, preamble = full
        assert main_preamble.start_line == main_full.start_line
        assert main_preamble.end_line == main_full.end_line

    def test_markdown_nested_preambles(self, tmp_repo):
        """Deeply nested headings should each have preambles."""
        content = """# H1

H1 intro.

## H2

H2 intro.

### H3

H3 intro.

#### H4

H4 intro.
"""
        md_file = tmp_repo / "test.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        nodes = parser.parse_file(str(md_file))

        # Each heading should have a preamble
        for name in ["H1", "H2", "H3", "H4"]:
            full = [n for n in nodes if n.kind == "md_heading" and n.name == name]
            preamble = [
                n for n in nodes if n.kind == "md_heading_preamble" and n.name == name
            ]
            assert len(full) == 1, f"{name} full node missing"
            assert len(preamble) == 1, f"{name} preamble node missing"


class TestOrgPreambles:
    """Test preamble extraction for Org-mode headings."""

    def test_org_heading_with_children_has_preamble(self, tmp_repo):
        """Org heading with children should have both full and preamble nodes."""
        content = """* Main

Intro text.

** Child 1

Child content.

** Child 2

More content.
"""
        org_file = tmp_repo / "test.org"
        org_file.write_text(content)

        parser = OrgParser()
        nodes = parser.parse_file(str(org_file))

        # Check both versions exist
        full_nodes = [n for n in nodes if n.kind == "org_heading" and n.name == "Main"]
        preamble_nodes = [
            n for n in nodes if n.kind == "org_heading_preamble" and n.name == "Main"
        ]

        assert len(full_nodes) == 1, "Should have one full heading node"
        assert len(preamble_nodes) == 1, "Should have one preamble node"

        main_full = full_nodes[0]
        main_preamble = preamble_nodes[0]

        # Full includes children
        assert main_full.start_line == 1
        # Verify preamble < full
        assert main_full.end_line > main_preamble.end_line

        # Preamble ends before first child
        assert main_preamble.start_line == 1
        # Preamble should end before first child
        assert main_preamble.end_line < main_full.end_line

    def test_org_preamble_excludes_first_child(self, tmp_repo):
        """Org preamble should stop before first child heading."""
        content = """* Phase 1

Planning intro.

** Week 1

Week 1 tasks.

** Week 2

Week 2 tasks.
"""
        org_file = tmp_repo / "test.org"
        org_file.write_text(content)

        parser = OrgParser()
        nodes = parser.parse_file(str(org_file))

        preamble = [n for n in nodes if n.kind == "org_heading_preamble"][0]

        # Preamble should end before Week 1 (Week 1 at line 5, so preamble ends at line 4)
        assert preamble.start_line == 1
        assert preamble.end_line == 4

    def test_org_heading_no_children_preamble_equals_full(self, tmp_repo):
        """Org heading with no children: preamble = full section."""
        content = """* Main

Just intro.

* Another

More text.
"""
        org_file = tmp_repo / "test.org"
        org_file.write_text(content)

        parser = OrgParser()
        nodes = parser.parse_file(str(org_file))

        main_full = [n for n in nodes if n.kind == "org_heading" and n.name == "Main"][0]
        main_preamble = [
            n for n in nodes if n.kind == "org_heading_preamble" and n.name == "Main"
        ][0]

        # For heading with no children, preamble = full
        assert main_preamble.start_line == main_full.start_line
        assert main_preamble.end_line == main_full.end_line

    def test_org_nested_preambles(self, tmp_repo):
        """Deeply nested Org headings should each have preambles."""
        content = """* H1

H1 intro.

** H2

H2 intro.

*** H3

H3 intro.

**** H4

H4 intro.
"""
        org_file = tmp_repo / "test.org"
        org_file.write_text(content)

        parser = OrgParser()
        nodes = parser.parse_file(str(org_file))

        # Each heading should have a preamble
        for name in ["H1", "H2", "H3", "H4"]:
            full = [n for n in nodes if n.kind == "org_heading" and n.name == name]
            preamble = [
                n for n in nodes if n.kind == "org_heading_preamble" and n.name == name
            ]
            assert len(full) == 1, f"{name} full node missing"
            assert len(preamble) == 1, f"{name} preamble node missing"


class TestPreambleSelectors:
    """Test that preamble nodes are selectable."""

    def test_preamble_selector_resolution_org(self, tmp_repo):
        """Resolver should find preamble nodes by kind."""
        content = """* Project

This is the project intro.

** Phase 1

Phase 1 details.
"""
        org_file = tmp_repo / "test.org"
        org_file.write_text(content)

        indexer = Indexer()
        indices = indexer.index_files([str(org_file)])

        resolver = Resolver(indices)

        # Resolve preamble by kind
        result = resolver.resolve(f"{org_file}:org_heading_preamble:Project")
        assert result.is_resolved(), "Should resolve preamble selector"
        assert result.exact_match.kind == "org_heading_preamble"
        assert result.exact_match.name == "Project"
        assert result.exact_match.start_line == 1
        assert result.exact_match.end_line == 4  # Before Phase 1 at line 5

    def test_preamble_selector_resolution_markdown(self, tmp_repo):
        """Resolver should find markdown preamble nodes."""
        content = """# Main

Main intro text.

## Child

Child content.
"""
        md_file = tmp_repo / "test.md"
        md_file.write_text(content)

        indexer = Indexer()
        indices = indexer.index_files([str(md_file)])

        resolver = Resolver(indices)

        # Resolve preamble by kind
        result = resolver.resolve(f"{md_file}:md_heading_preamble:Main")
        assert result.is_resolved(), "Should resolve markdown preamble"
        assert result.exact_match.kind == "md_heading_preamble"
        assert result.exact_match.start_line == 1
        assert result.exact_match.end_line == 4  # Before Child at line 5

    def test_full_heading_selector_still_works(self, tmp_repo):
        """Full heading selectors (without _preamble) should still work."""
        content = """* Project

Intro.

** Phase 1

Details.
"""
        org_file = tmp_repo / "test.org"
        org_file.write_text(content)

        indexer = Indexer()
        indices = indexer.index_files([str(org_file)])

        resolver = Resolver(indices)

        # Resolve full heading (backward compatible)
        result = resolver.resolve(f"{org_file}:org_heading:Project")
        assert result.is_resolved(), "Full heading selector should work"
        assert result.exact_match.kind == "org_heading"
        assert result.exact_match.start_line == 1


class TestPreambleEditing:
    """Test that preambles can be edited without affecting children."""

    def test_replace_preamble_preserves_children(self, tmp_repo):
        """Replacing preamble should not touch children."""
        content = """* Phase 1

Old intro text.

** Week 1

Week 1 content.

** Week 2

Week 2 content.
"""
        org_file = tmp_repo / "test.org"
        org_file.write_text(content)

        indexer = Indexer()
        indices = indexer.index_files([str(org_file)])

        resolver = Resolver(indices)
        result = resolver.resolve(
            f"{org_file}:org_heading_preamble:Phase 1"
        )

        assert result.is_resolved()
        preamble = result.exact_match

        # Original preamble content
        original_content = Path(org_file).read_text()
        original_lines = original_content.splitlines()

        # Verify children are after preamble
        assert "** Week 1" in original_lines[4:], "Week 1 should be after preamble"
        assert "** Week 2" in original_lines[6:], "Week 2 should be after preamble"

        # Edit the preamble via editor
        from grafty.editor import Editor

        file_idx = indices[str(org_file)]
        editor = Editor(file_idx)
        editor.replace(
            preamble,
            "* Phase 1\n\nNew intro text here.",
        )
        modified = editor.current_content

        # Verify children are still present
        assert "** Week 1" in modified, "Week 1 should be preserved"
        assert "** Week 2" in modified, "Week 2 should be preserved"
        assert "New intro text here." in modified, "New text should be there"
        assert "Old intro text." not in modified, "Old text should be gone"

    def test_delete_preamble_preserves_children(self, tmp_repo):
        """Deleting preamble should preserve child headings."""
        content = """* Project

Intro text.

** Task 1

Task 1 content.
"""
        org_file = tmp_repo / "test.org"
        org_file.write_text(content)

        indexer = Indexer()
        indices = indexer.index_files([str(org_file)])

        resolver = Resolver(indices)
        result = resolver.resolve(f"{org_file}:org_heading_preamble:Project")

        assert result.is_resolved()
        preamble = result.exact_match

        from grafty.editor import Editor

        file_idx = indices[str(org_file)]
        editor = Editor(file_idx)
        editor.delete(preamble)
        modified = editor.current_content

        # Children should still be there
        assert "** Task 1" in modified, "Child should be preserved"
        assert "Intro text." not in modified, "Preamble content should be gone"


class TestPreambleEdgeCases:
    """Test edge cases for preambles."""

    def test_empty_preamble(self, tmp_repo):
        """Heading immediately followed by child (no intro)."""
        content = """* Main
** Child

Content.
"""
        org_file = tmp_repo / "test.org"
        org_file.write_text(content)

        parser = OrgParser()
        nodes = parser.parse_file(str(org_file))

        preamble = [n for n in nodes if n.kind == "org_heading_preamble"][0]

        # Preamble should just be the heading line
        assert preamble.start_line == 1
        assert preamble.end_line == 1

    def test_preamble_with_blank_lines_before_child(self, tmp_repo):
        """Preamble includes blank lines before first child."""
        content = """* Main

Intro.


** Child

Content.
"""
        org_file = tmp_repo / "test.org"
        org_file.write_text(content)

        parser = OrgParser()
        nodes = parser.parse_file(str(org_file))

        full = [n for n in nodes if n.kind == "org_heading" and n.name == "Main"][0]
        preamble = [
            n for n in nodes if n.kind == "org_heading_preamble" and n.name == "Main"
        ][0]

        # Child is at line 6
        # Preamble should go up to line 5 (before child)
        assert preamble.end_line == 5
        assert full.start_line == 1
        assert full.end_line > preamble.end_line

    def test_last_heading_in_file(self, tmp_repo):
        """Last heading: preamble = full (no next heading)."""
        content = """* First

First content.

* Last

Last content.
"""
        org_file = tmp_repo / "test.org"
        org_file.write_text(content)

        parser = OrgParser()
        nodes = parser.parse_file(str(org_file))

        last_full = [n for n in nodes if n.kind == "org_heading" and n.name == "Last"][0]
        last_preamble = [
            n for n in nodes if n.kind == "org_heading_preamble" and n.name == "Last"
        ][0]

        # Last heading: preamble = full
        assert last_preamble.start_line == last_full.start_line
        assert last_preamble.end_line == last_full.end_line
