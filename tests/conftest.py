"""
conftest.py — pytest fixtures for grafty tests.
"""
import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def tmp_repo():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def python_file(tmp_repo):
    """Create a sample Python file."""
    content = '''
"""Module docstring."""

class MyClass:
    """A simple class."""

    def __init__(self):
        pass

    def method_one(self):
        """First method."""
        return 1

    def method_two(self):
        """Second method."""
        return 2

def top_level_function():
    """A top-level function."""
    pass
'''
    p = tmp_repo / "test.py"
    p.write_text(content)
    return p


@pytest.fixture
def markdown_file(tmp_repo):
    """Create a sample Markdown file."""
    content = '''# Main Heading

Some intro text.

## Sub Heading 1

Content for section 1.

## Sub Heading 2

Content for section 2.

### Nested Heading

Nested content.

# Another Main

More content.
'''
    p = tmp_repo / "test.md"
    p.write_text(content)
    return p


@pytest.fixture
def org_file(tmp_repo):
    """Create a sample Org-mode file."""
    content = '''* Top Level 1
  Some content here.
** Subtopic 1.1
   Details.
** Subtopic 1.2
   More details.
* Top Level 2
  Another section.
** Subtopic 2.1
   Content.
'''
    p = tmp_repo / "test.org"
    p.write_text(content)
    return p


@pytest.fixture
def clojure_file(tmp_repo):
    """Create a sample Clojure file."""
    content = '''(ns my.namespace)

(defn my-func [x]
  (+ x 1))

(defmacro my-macro [form]
  `(do ~form))

(defn another-func
  "Another function."
  [a b]
  (+ a b))
'''
    p = tmp_repo / "test.clj"
    p.write_text(content)
    return p
