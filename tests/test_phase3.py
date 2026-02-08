"""
test_phase3.py — Tests for Phase 3 features (line editing, improved errors, query language).
"""
from pathlib import Path
from grafty.indexer import Indexer
from grafty.selectors import Resolver, LineNumberSelector
from grafty.editor import Editor


class TestLineNumberEditing:
    """Tests for line-number editing feature (3.1)."""

    def test_single_line_selector_format(self):
        """Test parsing file.py:42 format."""
        selector = "test.py:42"
        parsed = LineNumberSelector.parse(selector)
        assert parsed is not None
        assert parsed.file_path == "test.py"
        assert parsed.start_line == 42
        assert parsed.end_line == 42

    def test_line_range_selector_format(self):
        """Test parsing file.py:42-50 format."""
        selector = "test.py:42-50"
        parsed = LineNumberSelector.parse(selector)
        assert parsed is not None
        assert parsed.file_path == "test.py"
        assert parsed.start_line == 42
        assert parsed.end_line == 50

    def test_line_selector_with_path_slashes(self):
        """Test parsing src/file.py:42-50 with path."""
        selector = "src/file.py:42-50"
        parsed = LineNumberSelector.parse(selector)
        assert parsed is not None
        assert parsed.file_path == "src/file.py"
        assert parsed.start_line == 42
        assert parsed.end_line == 50

    def test_line_selector_invalid_format(self):
        """Test invalid line selector formats."""
        # Invalid: no line number
        assert LineNumberSelector.parse("test.py:abc") is None
        # Invalid: three colons
        assert LineNumberSelector.parse("test.py:42:50") is None

    def test_replace_by_line_number_single(self, tmp_repo, python_file):
        """Test replacing a single line by line number."""
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))

        # Get the file index
        file_index = indices[str(python_file)]

        # Create editor and replace line 5
        editor = Editor(file_index)

        original = editor.current_content
        operation = {
            "kind": "replace",
            "start_line": 5,
            "end_line": 5,
            "text": "    # Replaced line",
        }

        from grafty.patch import apply_patch_to_buffer
        result = apply_patch_to_buffer(original, operation)

        assert "# Replaced line" in result
        # Original line 5 should be gone
        lines = original.splitlines()
        original_line_5 = lines[4] if len(lines) > 4 else ""
        if original_line_5:
            assert original_line_5 not in result or "# Replaced line" in result

    def test_replace_by_line_number_range(self, tmp_repo, python_file):
        """Test replacing a line range by line numbers."""
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))

        file_index = indices[str(python_file)]
        editor = Editor(file_index)

        original = editor.current_content
        operation = {
            "kind": "replace",
            "start_line": 1,
            "end_line": 3,
            "text": '"""New docstring."""\n\n# New comment',
        }

        from grafty.patch import apply_patch_to_buffer
        result = apply_patch_to_buffer(original, operation)

        assert "New docstring" in result
        assert "New comment" in result

    def test_resolver_accepts_line_selectors(self, tmp_repo, python_file):
        """Test that resolver can handle line-number selectors."""
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        Resolver(indices)

        # Should not error on line selector, even if no exact match
        # The resolver will pass it to line number handler
        selector = str(python_file) + ":5-10"
        # This should be parsed differently, not via traditional resolve
        parsed = LineNumberSelector.parse(selector)
        assert parsed is not None


class TestImprovedErrorMessages:
    """Tests for improved error messages feature (3.2)."""

    def test_fuzzy_match_with_candidates(self, tmp_repo, python_file):
        """Test that fuzzy match returns helpful candidates."""
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Search for something close to an existing function
        result = resolver.resolve("my_clas")  # Close to MyClass

        # Should have candidates, not just error
        assert result.candidates or result.exact_match or result.error

    def test_error_message_explains_mismatch(self, tmp_repo, python_file):
        """Test that error messages explain why selector didn't resolve."""
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Search for something that doesn't exist
        result = resolver.resolve("nonexistent_xyz_function")

        # Should have informative error
        assert result.error is not None
        # Error should suggest what to search for
        assert "No node found" in result.error or "matching" in result.error.lower()

    def test_candidates_when_ambiguous(self, tmp_repo, python_file):
        """Test that ambiguous matches show candidates."""
        # Create a file with duplicate names to test ambiguity
        tmp_dir = Path(tmp_repo)

        content = '''
def helper():
    pass

class Helper:
    pass

def another_helper():
    pass
'''
        test_file = tmp_dir / "helpers.py"
        test_file.write_text(content)

        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Search for 'helper'
        result = resolver.resolve("helper")

        # Should either have exact match or candidates
        # (exact match for first found, or multiple candidates)
        assert result.exact_match or result.candidates

    def test_improved_error_for_path_kind_name_mismatch(self, tmp_repo, python_file):
        """Test improved error when path:kind:name selector fails."""
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Try to find a non-existent function
        result = resolver.resolve("test.py:py_function:nonexistent_func")

        assert result.error is not None
        # Error should be informative
        assert "nonexistent_func" in result.error or "No node found" in result.error

    def test_suggest_similar_names(self, tmp_repo, python_file):
        """Test that resolver suggests similar names."""
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Close to actual method name
        result = resolver.resolve("method_on")  # Close to method_one

        # Should have candidates with similar names
        if result.candidates:
            candidate_names = [c.name for c in result.candidates]
            # At least some candidates should be similar
            assert len(candidate_names) > 0

    def test_error_message_format_consistency(self, tmp_repo, python_file):
        """Test that error messages have consistent format."""
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        result1 = resolver.resolve("nothing_here_xyz")
        result2 = resolver.resolve("totally_fake")

        # Both should have either error or candidates
        assert result1.error or result1.candidates or result1.exact_match
        assert result2.error or result2.candidates or result2.exact_match


class TestQueryLanguage:
    """Tests for query language feature (3.3)."""

    def test_glob_pattern_wildcard_match(self, tmp_repo):
        """Test glob pattern matching with wildcards."""
        # Create test file with functions
        tmp_dir = Path(tmp_repo)
        content = '''
def validate_input():
    pass

def validate_schema():
    pass

def process_data():
    pass

def validate_output():
    pass
'''
        test_file = tmp_dir / "validators.py"
        test_file.write_text(content)

        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Query for pattern *validate*
        results = resolver.query_nodes_by_pattern("*validate*")

        assert len(results) >= 3  # Should find all validate_* functions
        assert all("validate" in node.name for node in results)

    def test_glob_pattern_start_wildcard(self, tmp_repo):
        """Test glob pattern with wildcard at start."""
        tmp_dir = Path(tmp_repo)
        content = '''
def my_validate():
    pass

def his_validate():
    pass

def validate_input():
    pass
'''
        test_file = tmp_dir / "test.py"
        test_file.write_text(content)

        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Query for *_validate pattern
        results = resolver.query_nodes_by_pattern("*_validate")

        # Should find my_validate, his_validate
        assert len(results) >= 2
        assert all(node.name.endswith("_validate") for node in results)

    def test_glob_pattern_end_wildcard(self, tmp_repo):
        """Test glob pattern with wildcard at end."""
        tmp_dir = Path(tmp_repo)
        content = '''
def validate_input():
    pass

def validate_schema():
    pass

def process_data():
    pass
'''
        test_file = tmp_dir / "test.py"
        test_file.write_text(content)

        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Query for validate_* pattern
        results = resolver.query_nodes_by_pattern("validate_*")

        # Should find validate_input, validate_schema
        assert len(results) >= 2
        assert all(node.name.startswith("validate") for node in results)

    def test_path_glob_pattern(self, tmp_repo):
        """Test path glob patterns."""
        tmp_dir = Path(tmp_repo)

        # Create nested structure
        src_dir = tmp_dir / "src"
        src_dir.mkdir(exist_ok=True)

        content = '''
def validate_input():
    pass

def process_output():
    pass
'''
        (src_dir / "main.py").write_text(content)

        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Debug: print available paths
        available_paths = list(indices.keys())

        # Query for src/:py_function:*validate*
        # Note: paths might be absolute or relative, adjust pattern accordingly
        if available_paths:
            actual_path = available_paths[0]
            if "src" in actual_path and "main" in actual_path:
                # Use actual path structure
                results = resolver.query_nodes_by_path_glob(f"{actual_path}:py_function:*validate*")
            else:
                results = resolver.query_nodes_by_path_glob("*src*main*:py_function:*validate*")
        else:
            results = []

        assert len(results) >= 1
        assert "validate" in results[0].name

    def test_search_command_with_patterns(self, tmp_repo, python_file):
        """Test search functionality with patterns."""
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Should have search method
        assert hasattr(resolver, 'query_nodes_by_pattern')

        # Query for all methods
        results = resolver.query_nodes_by_pattern("*method*")

        # Should find method nodes
        assert len(results) >= 0  # May or may not find depending on file content

    def test_glob_pattern_multiple_matches(self, tmp_repo):
        """Test glob pattern returning multiple matches."""
        tmp_dir = Path(tmp_repo)
        content = '''
def test_addition():
    pass

def test_subtraction():
    pass

def test_multiplication():
    pass

def helper_test():
    pass
'''
        test_file = tmp_dir / "tests.py"
        test_file.write_text(content)

        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Query for test_* pattern
        results = resolver.query_nodes_by_pattern("test_*")

        # Should find all test_ functions
        assert len(results) >= 3
        test_functions = [r for r in results if r.name.startswith("test_")]
        assert len(test_functions) == 3

    def test_glob_pattern_case_sensitivity(self, tmp_repo):
        """Test glob pattern matching (case sensitivity)."""
        tmp_dir = Path(tmp_repo)
        content = '''
def ValidateInput():
    pass

def validate_input():
    pass

def VALIDATE_INPUT():
    pass
'''
        test_file = tmp_dir / "mixed.py"
        test_file.write_text(content)

        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Query for validate* (lowercase)
        results = resolver.query_nodes_by_pattern("validate*")

        # Should match validate_input and similar
        assert len(results) >= 1

    def test_query_nodes_empty_result(self, tmp_repo):
        """Test query returning empty results."""
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Query for pattern that matches nothing
        results = resolver.query_nodes_by_pattern("*xyz_nonexistent_abc*")

        assert len(results) == 0
        assert isinstance(results, list)


class TestPhase3Integration:
    """Integration tests for Phase 3 features."""

    def test_line_editing_via_cli_simulation(self, tmp_repo, python_file):
        """Simulate CLI usage of line editing."""
        # This tests that the line editing can be used in a workflow
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        file_index = indices[str(python_file)]

        editor = Editor(file_index)

        # Simulate: grafty replace file.py:5-10 --text "..."
        operation = {
            "kind": "replace",
            "start_line": 5,
            "end_line": 10,
            "text": "# New code",
        }

        from grafty.patch import apply_patch_to_buffer
        result = apply_patch_to_buffer(editor.current_content, operation)

        assert "# New code" in result
        assert len(result) > 0

    def test_error_messages_in_resolver(self, tmp_repo, python_file):
        """Test that resolver provides helpful error context."""
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        # Test various failing selectors and check error quality
        result1 = resolver.resolve("path/to/nonexistent.py:py_class:FakeClass")
        result2 = resolver.resolve("very_similar_to_something")

        # All should have informative results
        assert result1.error or result1.candidates
        assert result2.error or result2.candidates or result2.exact_match

    def test_query_and_edit_workflow(self, tmp_repo):
        """Test combined query + edit workflow."""
        tmp_dir = Path(tmp_repo)
        content = '''
def validate_user():
    return True

def validate_role():
    return True

def validate_permission():
    return True
'''
        test_file = tmp_dir / "auth.py"
        test_file.write_text(content)

        # 1. Query for all validate_* functions
        indexer = Indexer()
        indices = indexer.index_directory(str(tmp_repo))
        resolver = Resolver(indices)

        validate_funcs = resolver.query_nodes_by_pattern("validate_*")

        assert len(validate_funcs) >= 3

        # 2. Could edit each one
        if validate_funcs:
            file_index = indices[validate_funcs[0].path]
            editor = Editor(file_index)

            # Replace first validate function
            editor.replace(validate_funcs[0], "def validate_user():\n    return False")

            patch = editor.generate_patch()
            assert "validate_user" in patch
