"""
test_markdown_parser.py — Tests for Markdown parser.
"""

from grafty.parsers.markdown_ts import MarkdownParser


class TestMarkdownParser:
    """Test Markdown parsing."""

    def test_parse_headings(self, markdown_file):
        """Test parsing headings."""
        parser = MarkdownParser()
        nodes = parser.parse_file(str(markdown_file))

        # Should find: Main Heading, Sub Heading 1, Sub Heading 2, Nested Heading, Another Main
        assert len(nodes) >= 4

        # Check heading levels
        h1_nodes = [n for n in nodes if n.heading_level == 1]
        assert len(h1_nodes) >= 2

        h2_nodes = [n for n in nodes if n.heading_level == 2]
        assert len(h2_nodes) >= 2

        h3_nodes = [n for n in nodes if n.heading_level == 3]
        assert len(h3_nodes) >= 1

    def test_heading_names(self, markdown_file):
        """Test that heading names are extracted."""
        parser = MarkdownParser()
        nodes = parser.parse_file(str(markdown_file))

        names = {n.name for n in nodes}
        assert "Main Heading" in names
        assert "Sub Heading 1" in names
        assert "Nested Heading" in names

    def test_heading_extent(self, markdown_file):
        """Test that heading extents are computed correctly."""
        parser = MarkdownParser()
        nodes = parser.parse_file(str(markdown_file))

        # Main heading should span to the next main heading
        main_headings = [n for n in nodes if n.heading_level == 1]
        assert len(main_headings) >= 2

        # First main heading
        first = main_headings[0]
        second = main_headings[1]

        # First should end before second starts
        assert first.end_line < second.start_line

    def test_line_ranges(self, markdown_file):
        """Test that line ranges are valid."""
        parser = MarkdownParser()
        nodes = parser.parse_file(str(markdown_file))

        for node in nodes:
            assert node.start_line >= 1
            assert node.end_line >= node.start_line
            # Nodes can be md_heading or md_heading_preamble
            assert node.kind in ("md_heading", "md_heading_preamble")
