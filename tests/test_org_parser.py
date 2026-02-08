"""
test_org_parser.py — Tests for Org-mode parser.
"""

from grafty.parsers.org import OrgParser


class TestOrgParser:
    """Test Org-mode parsing."""

    def test_parse_headings(self, org_file):
        """Test parsing org headings."""
        parser = OrgParser()
        nodes = parser.parse_file(str(org_file))

        # Should find: Top Level 1, Subtopic 1.1, Subtopic 1.2, Top Level 2, Subtopic 2.1
        assert len(nodes) >= 5

        # Check heading levels
        level1 = [n for n in nodes if n.heading_level == 1]
        assert len(level1) >= 2

        level2 = [n for n in nodes if n.heading_level == 2]
        assert len(level2) >= 3

    def test_heading_names(self, org_file):
        """Test heading name extraction."""
        parser = OrgParser()
        nodes = parser.parse_file(str(org_file))

        names = {n.name for n in nodes}
        assert "Top Level 1" in names
        assert "Subtopic 1.1" in names
        assert "Top Level 2" in names

    def test_heading_extent(self, org_file):
        """Test extent computation."""
        parser = OrgParser()
        nodes = parser.parse_file(str(org_file))

        # Find "Top Level 1" and "Top Level 2"
        top_nodes = [n for n in nodes if n.name.startswith("Top Level")]
        assert len(top_nodes) >= 2

        first = [n for n in top_nodes if n.name == "Top Level 1"][0]
        second = [n for n in top_nodes if n.name == "Top Level 2"][0]

        # First should end before second starts
        assert first.end_line < second.start_line

    def test_subtopic_hierarchy(self, org_file):
        """Test that subtopics are properly nested."""
        parser = OrgParser()
        nodes = parser.parse_file(str(org_file))

        # "Subtopic 1.1" should be nested under "Top Level 1"
        top_level_1 = [n for n in nodes if n.name == "Top Level 1"][0]
        subtopic_11 = [n for n in nodes if n.name == "Subtopic 1.1"][0]

        # Subtopic should be between Top Level 1 and Top Level 2
        assert top_level_1.start_line < subtopic_11.start_line
