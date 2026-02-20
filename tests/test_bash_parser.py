"""Tests for Bash parser."""

import pytest
from grafty.parsers.bash_ts import BashParser


@pytest.fixture
def bash_file(tmp_path):
    f = tmp_path / "example.sh"
    f.write_text(
        "#!/bin/bash\n"
        "\n"
        "# Setup the environment\n"
        "# for the application\n"
        "setup() {\n"
        "    export APP_HOME=/opt/app\n"
        "    mkdir -p $APP_HOME\n"
        "}\n"
        "\n"
        "deploy() {\n"
        "    echo 'deploying...'\n"
        "    return 0\n"
        "}\n"
        "\n"
        "cleanup() {\n"
        "    rm -rf /tmp/build\n"
        "}\n"
    )
    return f


def test_extract_functions(bash_file):
    nodes = BashParser().parse_file(str(bash_file))
    funcs = [n for n in nodes if n.kind == "bash_function"]
    assert len(funcs) == 3
    names = [n.name for n in funcs]
    assert "setup" in names
    assert "deploy" in names
    assert "cleanup" in names


def test_function_lines(bash_file):
    nodes = BashParser().parse_file(str(bash_file))
    setup = [n for n in nodes if n.name == "setup" and n.kind == "bash_function"][0]
    assert setup.start_line == 5
    assert setup.end_line == 8


def test_doc_comment(bash_file):
    nodes = BashParser().parse_file(str(bash_file))
    docs = [n for n in nodes if n.kind == "bash_doc"]
    assert len(docs) == 1
    assert docs[0].name == "setup"
    assert docs[0].start_line == 3
    assert docs[0].parent_id is not None


def test_no_doc_no_node(bash_file):
    nodes = BashParser().parse_file(str(bash_file))
    docs = [n for n in nodes if n.kind == "bash_doc" and n.name == "deploy"]
    assert len(docs) == 0


def test_node_ids_stable(bash_file):
    p = BashParser()
    nodes1 = p.parse_file(str(bash_file))
    nodes2 = p.parse_file(str(bash_file))
    ids1 = [n.id for n in nodes1]
    ids2 = [n.id for n in nodes2]
    assert ids1 == ids2
