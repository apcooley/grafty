"""Tests for insert command — line-based and selector-relative insertion."""

import pytest
from pathlib import Path
from grafty.editor import Editor
from grafty.indexer import Indexer


@pytest.fixture
def py_file(tmp_path):
    """Create a simple Python file for testing."""
    f = tmp_path / "example.py"
    f.write_text(
        "class Greeter:\n"
        "    def hello(self):\n"
        "        return 'hi'\n"
        "\n"
        "    def goodbye(self):\n"
        "        return 'bye'\n"
    )
    return f


@pytest.fixture
def indexed(py_file):
    """Index the test file and return (indices, file_path)."""
    indexer = Indexer()
    indices = indexer.index_directory(str(py_file.parent))
    return indices, str(py_file)


# ── Line-based insertion ──


def test_insert_at_line(indexed):
    indices, path = indexed
    editor = Editor(indices[path])
    editor.insert(text="# comment", line=1)
    lines = editor.current_content.splitlines()
    assert lines[0] == "# comment"
    assert lines[1] == "class Greeter:"


def test_insert_at_end_line(indexed):
    indices, path = indexed
    editor = Editor(indices[path])
    total = len(editor.current_content.splitlines())
    editor.insert(text="# end", line=total + 1)
    lines = editor.current_content.splitlines()
    assert lines[-1] == "# end"


# ── Selector-relative insertion ──


def test_insert_before_node(indexed):
    indices, path = indexed
    resolver_nodes = [n for n in indices[path].nodes if n.name == "goodbye"]
    assert len(resolver_nodes) == 1
    node = resolver_nodes[0]

    editor = Editor(indices[path])
    editor.insert(text="    # before goodbye", node=node, position="before")
    lines = editor.current_content.splitlines()
    assert "    # before goodbye" in lines
    idx = lines.index("    # before goodbye")
    assert "goodbye" in lines[idx + 1]


def test_insert_after_node(indexed):
    indices, path = indexed
    resolver_nodes = [n for n in indices[path].nodes if n.name == "hello"]
    assert len(resolver_nodes) == 1
    node = resolver_nodes[0]

    editor = Editor(indices[path])
    editor.insert(text="    # after hello", node=node, position="after")
    lines = editor.current_content.splitlines()
    assert "    # after hello" in lines
    idx = lines.index("    # after hello")
    assert "hello" in lines[idx - 1] or "return" in lines[idx - 1]


def test_insert_inside_start(indexed):
    indices, path = indexed
    cls_nodes = [n for n in indices[path].nodes if n.name == "Greeter"]
    assert len(cls_nodes) == 1
    node = cls_nodes[0]

    editor = Editor(indices[path])
    editor.insert(text="    # first line inside class", node=node, position="inside-start")
    lines = editor.current_content.splitlines()
    assert lines[0] == "class Greeter:"
    assert lines[1] == "    # first line inside class"


def test_insert_inside_end(indexed):
    indices, path = indexed
    cls_nodes = [n for n in indices[path].nodes if n.name == "Greeter"]
    assert len(cls_nodes) == 1
    node = cls_nodes[0]

    editor = Editor(indices[path])
    editor.insert(text="    # last line inside class", node=node, position="inside-end")
    lines = editor.current_content.splitlines()
    assert "    # last line inside class" in lines


# ── Diff generation ──


def test_insert_generates_diff(indexed):
    indices, path = indexed
    editor = Editor(indices[path])
    editor.insert(text="# new", line=1)
    patch = editor.generate_patch()
    assert "+# new" in patch
    assert "---" in patch


# ── Write with backup ──


def test_insert_apply_with_backup(indexed):
    indices, path = indexed
    editor = Editor(indices[path])
    editor.insert(text="# top", line=1)
    editor.write(backup=True)

    content = Path(path).read_text()
    assert content.startswith("# top\n")
    assert Path(path + ".bak").exists()


# ── Error handling ──


def test_insert_no_line_no_node(indexed):
    indices, path = indexed
    editor = Editor(indices[path])
    with pytest.raises(ValueError, match="Must provide either line or node"):
        editor.insert(text="x")


def test_insert_wrong_file_node(indexed, tmp_path):
    indices, path = indexed
    from grafty.models import Node
    fake_node = Node(
        id="fake",
        kind="py_function",
        name="fake",
        path="/other/file.py",
        start_line=1,
        end_line=2,
    )
    editor = Editor(indices[path])
    with pytest.raises(ValueError, match="belongs to"):
        editor.insert(text="x", node=fake_node, position="after")
