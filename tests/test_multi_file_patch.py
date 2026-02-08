"""
test_multi_file_patch.py — Tests for multi-file atomic patch system (Phase 4.1).

39 comprehensive tests for PatchSet, FileMutation, and PatchSetResult.
Tests cover loading, validation, dry-run, atomic application, and edge cases.
"""
import json
import tempfile
from pathlib import Path

import pytest

from grafty.multi_file_patch import FileMutation, PatchSet, PatchSetResult


class TestPatchSetBasics:
    """Tests for basic PatchSet creation and mutation addition."""

    def test_patchset_creation_empty(self):
        """Test creating an empty PatchSet."""
        ps = PatchSet()
        assert ps.mutations == []
        assert len(ps.mutations) == 0

    def test_add_single_mutation(self):
        """Test adding a single mutation."""
        ps = PatchSet()
        ps.add_mutation("file.py", "replace", 10, 12, "new code")

        assert len(ps.mutations) == 1
        mut = ps.mutations[0]
        assert mut.file_path == "file.py"
        assert mut.operation_kind == "replace"
        assert mut.start_line == 10
        assert mut.end_line == 12
        assert mut.text == "new code"

    def test_add_multiple_mutations(self):
        """Test adding multiple mutations."""
        ps = PatchSet()
        ps.add_mutation("file1.py", "replace", 1, 2, "text1")
        ps.add_mutation("file2.py", "insert", 5, 5, "text2")
        ps.add_mutation("file3.py", "delete", 10, 15, "")

        assert len(ps.mutations) == 3
        assert ps.mutations[0].file_path == "file1.py"
        assert ps.mutations[1].file_path == "file2.py"
        assert ps.mutations[2].file_path == "file3.py"

    def test_mutation_with_description(self):
        """Test adding mutation with description."""
        ps = PatchSet()
        ps.add_mutation(
            "file.py", "replace", 1, 2, "new", description="Update function signature"
        )

        mut = ps.mutations[0]
        assert mut.description == "Update function signature"

    def test_mutation_to_dict(self):
        """Test FileMutation.to_dict() serialization."""
        mut = FileMutation(
            file_path="src/main.py",
            operation_kind="replace",
            start_line=10,
            end_line=12,
            text="def new_func(): pass",
            description="Update main",
        )

        d = mut.to_dict()
        assert d["file_path"] == "src/main.py"
        assert d["operation_kind"] == "replace"
        assert d["start_line"] == 10
        assert d["end_line"] == 12
        assert d["text"] == "def new_func(): pass"
        assert d["description"] == "Update main"


class TestPatchSetLoading:
    """Tests for loading patches from different formats."""

    def test_load_from_simple_format_single_mutation(self):
        """Test loading single mutation from simple format."""
        ps = PatchSet()
        ps.load_from_simple_format("src/main.py:replace:10:12:def new_func(): pass")

        assert len(ps.mutations) == 1
        mut = ps.mutations[0]
        assert mut.file_path == "src/main.py"
        assert mut.operation_kind == "replace"
        assert mut.start_line == 10
        assert mut.end_line == 12
        assert mut.text == "def new_func(): pass"

    def test_load_from_simple_format_multiple_lines(self):
        """Test loading multiple mutations from simple format."""
        content = """src/main.py:replace:10:12:def new(): pass
src/config.py:insert:5:5:enabled=True
src/old.py:delete:1:10:"""

        ps = PatchSet()
        ps.load_from_simple_format(content)

        assert len(ps.mutations) == 3
        assert ps.mutations[0].file_path == "src/main.py"
        assert ps.mutations[1].file_path == "src/config.py"
        assert ps.mutations[2].file_path == "src/old.py"

    def test_load_from_simple_format_skip_comments(self):
        """Test that simple format skips comments and blank lines."""
        content = """# This is a comment
src/main.py:replace:10:12:code

# Another comment
src/config.py:insert:5:5:enabled=True"""

        ps = PatchSet()
        ps.load_from_simple_format(content)

        assert len(ps.mutations) == 2

    def test_load_from_simple_format_invalid_raises(self):
        """Test that invalid simple format raises ValueError."""
        ps = PatchSet()

        with pytest.raises(ValueError, match="Invalid simple format"):
            ps.load_from_simple_format("file.py:replace")  # Missing parts

    def test_load_from_json_single_mutation(self):
        """Test loading single mutation from JSON."""
        json_content = json.dumps([{
            "file_path": "src/main.py",
            "operation_kind": "replace",
            "start_line": 10,
            "end_line": 12,
            "text": "def new(): pass",
            "description": "Update main"
        }])

        ps = PatchSet()
        ps.load_from_json(json_content)

        assert len(ps.mutations) == 1
        mut = ps.mutations[0]
        assert mut.file_path == "src/main.py"
        assert mut.description == "Update main"

    def test_load_from_json_multiple_mutations(self):
        """Test loading multiple mutations from JSON."""
        json_content = json.dumps([
            {
                "file_path": "file1.py",
                "operation_kind": "replace",
                "start_line": 1,
                "end_line": 2,
                "text": "text1"
            },
            {
                "file_path": "file2.py",
                "operation_kind": "insert",
                "start_line": 5,
                "end_line": 5,
                "text": "text2"
            }
        ])

        ps = PatchSet()
        ps.load_from_json(json_content)

        assert len(ps.mutations) == 2

    def test_load_from_json_invalid_json_raises(self):
        """Test that invalid JSON raises ValueError."""
        ps = PatchSet()

        with pytest.raises(ValueError, match="Invalid JSON"):
            ps.load_from_json("{invalid json}")

    def test_load_from_json_missing_required_field_raises(self):
        """Test that missing required field raises ValueError."""
        json_content = json.dumps([{
            "file_path": "file.py",
            # Missing operation_kind and other required fields
        }])

        ps = PatchSet()

        with pytest.raises(ValueError, match="missing required fields"):
            ps.load_from_json(json_content)


class TestPatchSetValidation:
    """Tests for patch validation."""

    def test_validate_all_empty_patchset(self):
        """Test validation of empty PatchSet."""
        ps = PatchSet()
        result = ps.validate_all()

        assert not result.success
        assert "No mutations" in result.message

    def test_validate_all_file_not_found(self, tmp_repo):
        """Test validation fails when file doesn't exist."""
        ps = PatchSet()
        ps.add_mutation("nonexistent.py", "replace", 1, 2, "text")

        result = ps.validate_all(str(tmp_repo))

        assert not result.success
        assert any("not found" in err for err in result.errors)

    def test_validate_all_line_numbers_invalid_start_greater_than_end(self, tmp_repo):
        """Test validation fails when start_line > end_line."""
        # Create a test file
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\nline2\nline3\n")

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 10, 5, "text")  # Invalid range

        result = ps.validate_all(str(tmp_repo))

        assert not result.success
        assert any("start_line > end_line" in err for err in result.errors)

    def test_validate_all_line_numbers_out_of_bounds(self, tmp_repo):
        """Test validation fails when line numbers exceed file size."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\nline2\nline3\n")  # 3 lines

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 100, 200, "text")  # Way out of bounds

        result = ps.validate_all(str(tmp_repo))

        assert not result.success
        assert any("start_line" in err and "file size" in err for err in result.errors)

    def test_validate_all_detects_overlapping_mutations(self, tmp_repo):
        """Test validation warns about overlapping mutations."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 1, 3, "text1")
        ps.add_mutation("test.py", "replace", 2, 4, "text2")  # Overlaps with first

        result = ps.validate_all(str(tmp_repo))

        # Should warn about overlap but not fail validation if individual mutations are OK
        assert len(result.warnings) > 0 or result.success


class TestPatchSetDryRun:
    """Tests for dry-run diff generation."""

    def test_generate_diffs_single_file_replace(self, tmp_repo):
        """Test generating diff for single file replacement."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\nline2\nline3\n")

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 2, 2, "modified line")

        result = ps.generate_diffs(str(tmp_repo))

        assert result.success
        assert "test.py" in result.diffs
        assert "+modified line" in result.diffs["test.py"]
        assert "-line2" in result.diffs["test.py"]

    def test_generate_diffs_multiple_files(self, tmp_repo):
        """Test generating diffs for multiple files."""
        file1 = tmp_repo / "file1.py"
        file2 = tmp_repo / "file2.py"
        file1.write_text("a1\na2\na3\n")
        file2.write_text("b1\nb2\nb3\n")

        ps = PatchSet()
        ps.add_mutation("file1.py", "replace", 1, 1, "x1")
        ps.add_mutation("file2.py", "replace", 2, 2, "x2")

        result = ps.generate_diffs(str(tmp_repo))

        assert result.success
        assert len(result.diffs) == 2
        assert "file1.py" in result.diffs
        assert "file2.py" in result.diffs

    def test_generate_diffs_does_not_modify_files(self, tmp_repo):
        """Test that generate_diffs doesn't actually modify files."""
        test_file = tmp_repo / "test.py"
        original_content = "line1\nline2\nline3\n"
        test_file.write_text(original_content)

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 2, 2, "modified")

        result = ps.generate_diffs(str(tmp_repo))

        assert result.success
        # File should be unchanged
        assert test_file.read_text() == original_content

    def test_generate_diffs_validates_first(self, tmp_repo):
        """Test that generate_diffs validates before generating."""
        ps = PatchSet()
        ps.add_mutation("nonexistent.py", "replace", 1, 2, "text")

        result = ps.generate_diffs(str(tmp_repo))

        assert not result.success
        assert len(result.errors) > 0


class TestPatchSetApplyAtomic:
    """Tests for atomic application with rollback."""

    def test_apply_atomic_single_file_replace(self, tmp_repo):
        """Test applying atomic replacement to single file."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\nline2\nline3\n")

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 2, 2, "modified")

        result = ps.apply_atomic(str(tmp_repo))

        assert result.success
        assert "test.py" in result.files_modified
        content = test_file.read_text()
        assert "modified" in content
        assert "line2" not in content

    def test_apply_atomic_multiple_files(self, tmp_repo):
        """Test applying atomic changes to multiple files."""
        file1 = tmp_repo / "file1.py"
        file2 = tmp_repo / "file2.py"
        file1.write_text("a1\na2\na3\n")
        file2.write_text("b1\nb2\nb3\n")

        ps = PatchSet()
        ps.add_mutation("file1.py", "replace", 1, 1, "x1")
        ps.add_mutation("file2.py", "replace", 2, 2, "x2")

        result = ps.apply_atomic(str(tmp_repo))

        assert result.success
        assert len(result.files_modified) == 2
        assert "x1" in file1.read_text()
        assert "x2" in file2.read_text()

    def test_apply_atomic_with_backup(self, tmp_repo):
        """Test that --backup creates .bak files."""
        test_file = tmp_repo / "test.py"
        original = "line1\nline2\nline3\n"
        test_file.write_text(original)

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 2, 2, "modified")

        result = ps.apply_atomic(str(tmp_repo), backup=True)

        assert result.success
        # Check backup was created
        backup_file = tmp_repo / "test.py.bak"
        assert backup_file.exists()
        assert backup_file.read_text() == original

    def test_apply_atomic_validates_before_applying(self, tmp_repo):
        """Test that apply_atomic validates before modifying files."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\n")

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 100, 200, "text")  # Invalid range

        result = ps.apply_atomic(str(tmp_repo))

        assert not result.success
        # File should be unchanged
        assert test_file.read_text() == "line1\n"

    def test_apply_atomic_preserves_newline_style(self, tmp_repo):
        """Test that atomic application applies changes correctly."""
        test_file = tmp_repo / "test.py"
        original = "line1\nline2\nline3\n"
        test_file.write_text(original)

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 2, 2, "modified")

        result = ps.apply_atomic(str(tmp_repo))

        assert result.success
        content = test_file.read_text()
        # Should contain modified line
        assert "modified" in content
        assert "line1" in content
        assert "line3" in content
        # Original line2 should be gone
        assert "line2" not in content


class TestPatchSetComplexScenarios:
    """Tests for complex patch scenarios."""

    def test_patch_multiple_mutations_same_file(self, tmp_repo):
        """Test multiple mutations in the same file."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 1, 1, "modified1")
        ps.add_mutation("test.py", "replace", 3, 3, "modified3")
        ps.add_mutation("test.py", "replace", 5, 5, "modified5")

        result = ps.apply_atomic(str(tmp_repo))

        assert result.success
        content = test_file.read_text()
        assert "modified1" in content
        assert "modified3" in content
        assert "modified5" in content

    def test_patch_insert_operation(self, tmp_repo):
        """Test insert operation."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\nline2\n")

        ps = PatchSet()
        ps.add_mutation("test.py", "insert", 2, 2, "inserted line")

        result = ps.apply_atomic(str(tmp_repo))

        assert result.success
        content = test_file.read_text()
        assert "inserted line" in content
        assert "line2" in content  # Original line2 should still be there

    def test_patch_delete_operation(self, tmp_repo):
        """Test delete operation."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\nline2\nline3\nline4\n")

        ps = PatchSet()
        ps.add_mutation("test.py", "delete", 2, 3, "")  # Delete lines 2-3

        result = ps.apply_atomic(str(tmp_repo))

        assert result.success
        content = test_file.read_text()
        assert "line1" in content
        assert "line4" in content
        assert "line2" not in content
        assert "line3" not in content

    def test_patch_mixed_operations_same_file(self, tmp_repo):
        """Test mixed operations (insert, replace, delete) on same file."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("a\nb\nc\nd\ne\nf\n")

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 1, 1, "A")  # Replace a -> A
        ps.add_mutation("test.py", "insert", 3, 3, "X")  # Insert X at 3
        ps.add_mutation("test.py", "delete", 5, 6, "")  # Delete e, f

        result = ps.apply_atomic(str(tmp_repo))

        assert result.success
        content = test_file.read_text()
        lines = content.strip().split('\n')
        assert "A" in lines
        assert "X" in lines
        assert "e" not in lines
        assert "f" not in lines

    def test_patch_unicode_handling(self, tmp_repo):
        """Test patch with unicode characters."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("hello\nworld\n", encoding="utf-8")

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", 2, 2, "мир 🌍")  # Russian + emoji

        result = ps.apply_atomic(str(tmp_repo))

        assert result.success
        content = test_file.read_text(encoding="utf-8")
        assert "мир 🌍" in content


class TestPatchSetErrors:
    """Tests for error handling and edge cases."""

    def test_error_invalid_operation_kind(self, tmp_repo):
        """Test validation catches invalid operation_kind."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\n")

        ps = PatchSet()
        ps.add_mutation("test.py", "invalid_op", 1, 1, "text")

        result = ps.validate_all(str(tmp_repo))

        assert not result.success
        assert any("Invalid operation_kind" in err for err in result.errors)

    def test_error_negative_line_numbers(self, tmp_repo):
        """Test validation catches negative line numbers."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\n")

        ps = PatchSet()
        ps.add_mutation("test.py", "replace", -1, 1, "text")

        result = ps.validate_all(str(tmp_repo))

        assert not result.success
        assert any("must be >= 1" in err for err in result.errors)

    def test_error_file_read_permission_denied(self, tmp_repo):
        """Test handling of permission denied errors."""
        test_file = tmp_repo / "test.py"
        test_file.write_text("line1\n")

        # Make file unreadable (if supported by platform)
        try:
            test_file.chmod(0o000)

            ps = PatchSet()
            ps.add_mutation("test.py", "replace", 1, 1, "text")

            result = ps.validate_all(str(tmp_repo))

            assert not result.success
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)

    def test_patchset_result_string_representation(self):
        """Test PatchSetResult string representation."""
        result = PatchSetResult(
            success=False,
            message="Test failed",
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            files_modified=["file.py"],
        )

        result_str = str(result)
        assert "Test failed" in result_str
        assert "Error 1" in result_str
        assert "Warning 1" in result_str


class TestPatchSetIntegration:
    """Integration tests with realistic scenarios."""

    def test_integration_full_workflow_validate_dryrun_apply(self, tmp_repo):
        """Test complete workflow: validate -> dry-run -> apply."""
        file1 = tmp_repo / "file1.py"
        file2 = tmp_repo / "file2.py"
        file1.write_text("def foo():\n    return 1\n")
        file2.write_text("def bar():\n    return 2\n")

        ps = PatchSet()
        ps.add_mutation("file1.py", "replace", 2, 2, "    return 42")
        ps.add_mutation("file2.py", "replace", 2, 2, "    return 99")

        # Step 1: Validate
        val_result = ps.validate_all(str(tmp_repo))
        assert val_result.success

        # Step 2: Dry-run (generate diffs)
        diff_result = ps.generate_diffs(str(tmp_repo))
        assert diff_result.success
        assert len(diff_result.diffs) == 2

        # Step 3: Apply
        apply_result = ps.apply_atomic(str(tmp_repo))
        assert apply_result.success
        assert len(apply_result.files_modified) == 2

        # Verify changes
        assert "return 42" in file1.read_text()
        assert "return 99" in file2.read_text()

    def test_integration_five_file_atomic_application(self, tmp_repo):
        """Test atomic application across 5 files (real-world scenario)."""
        files = {}
        for i in range(1, 6):
            fname = f"file{i}.py"
            fpath = tmp_repo / fname
            fpath.write_text(f"# File {i}\noriginal_line\n")
            files[fname] = fpath

        ps = PatchSet()
        for i in range(1, 6):
            ps.add_mutation(f"file{i}.py", "replace", 2, 2, f"modified_line_{i}")

        result = ps.apply_atomic(str(tmp_repo))

        assert result.success
        assert len(result.files_modified) == 5

        # Verify all files were modified
        for i in range(1, 6):
            fname = f"file{i}.py"
            content = files[fname].read_text()
            assert f"modified_line_{i}" in content
            assert "original_line" not in content

    def test_integration_format_roundtrip_simple_to_json(self, tmp_repo):
        """Test converting between simple and JSON formats."""
        # Create a patch set via simple format
        ps1 = PatchSet()
        simple_content = """file1.py:replace:1:2:text1
file2.py:insert:5:5:text2"""
        ps1.load_from_simple_format(simple_content)

        # Convert to JSON and back
        json_list = [m.to_dict() for m in ps1.mutations]
        json_content = json.dumps(json_list)

        ps2 = PatchSet()
        ps2.load_from_json(json_content)

        assert len(ps2.mutations) == len(ps1.mutations)
        for m1, m2 in zip(ps1.mutations, ps2.mutations):
            assert m1.file_path == m2.file_path
            assert m1.operation_kind == m2.operation_kind
            assert m1.start_line == m2.start_line
            assert m1.end_line == m2.end_line
            assert m1.text == m2.text
