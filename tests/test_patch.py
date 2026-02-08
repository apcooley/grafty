"""
test_patch.py — Tests for patch generation and application.
"""

from grafty.patch import (
    apply_patch_to_buffer,
    generate_unified_diff,
    normalize_newlines,
)


class TestPatchOperations:
    """Test patch generation and application."""

    def test_replace_operation(self):
        """Test replace operation."""
        content = "line 1\nline 2\nline 3\n"

        operation = {
            "kind": "replace",
            "start_line": 2,
            "end_line": 2,
            "text": "replaced line",
        }

        result = apply_patch_to_buffer(content, operation)

        assert "line 1" in result
        assert "replaced line" in result
        assert "line 2" not in result  # Original line 2 removed
        assert "line 3" in result

    def test_insert_operation(self):
        """Test insert operation."""
        content = "line 1\nline 2\n"

        operation = {
            "kind": "insert",
            "start_line": 2,
            "end_line": 2,
            "text": "inserted line",
        }

        result = apply_patch_to_buffer(content, operation)

        assert "line 1" in result
        assert "inserted line" in result
        assert "line 2" in result

    def test_delete_operation(self):
        """Test delete operation."""
        content = "line 1\nline 2\nline 3\n"

        operation = {
            "kind": "delete",
            "start_line": 2,
            "end_line": 2,
            "text": "",
        }

        result = apply_patch_to_buffer(content, operation)

        assert "line 1" in result
        assert "line 2" not in result
        assert "line 3" in result

    def test_unified_diff_generation(self):
        """Test unified diff generation."""
        original = "line 1\nline 2\nline 3\n"
        modified = "line 1\nmodified line 2\nline 3\n"

        diff = generate_unified_diff(original, modified, "test.txt")

        assert "test.txt" in diff
        assert "+modified line 2" in diff
        assert "-line 2" in diff

    def test_normalize_newlines_crlf(self):
        """Test CRLF normalization."""
        content = "line 1\r\nline 2\r\nline 3\r\n"
        normalized, mode = normalize_newlines(content)

        assert mode == "crlf"
        assert "\r\n" not in normalized
        assert "\n" in normalized

    def test_normalize_newlines_lf(self):
        """Test LF detection."""
        content = "line 1\nline 2\nline 3\n"
        normalized, mode = normalize_newlines(content)

        assert mode == "lf"
        assert normalized == content
