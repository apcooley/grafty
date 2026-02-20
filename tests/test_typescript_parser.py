"""Tests for TypeScript parser."""

import pytest
from grafty.parsers.typescript_ts import TypeScriptParser


@pytest.fixture
def ts_file(tmp_path):
    f = tmp_path / "example.ts"
    f.write_text(
        "/** User interface. */\n"
        "interface User {\n"
        "    name: string;\n"
        "    age: number;\n"
        "}\n"
        "\n"
        "type Status = 'active' | 'inactive';\n"
        "\n"
        "enum Color {\n"
        "    Red,\n"
        "    Green,\n"
        "    Blue,\n"
        "}\n"
        "\n"
        "/** Greet a user. */\n"
        "function greet(user: User): string {\n"
        "    return user.name;\n"
        "}\n"
        "\n"
        "class Greeter {\n"
        "    /** Say hello. */\n"
        "    hello(name: string): string {\n"
        "        return `Hello ${name}`;\n"
        "    }\n"
        "\n"
        "    goodbye(): void {\n"
        "        console.log('bye');\n"
        "    }\n"
        "}\n"
    )
    return f


def test_extract_interface(ts_file):
    nodes = TypeScriptParser().parse_file(str(ts_file))
    ifaces = [n for n in nodes if n.kind == "ts_interface"]
    assert len(ifaces) == 1
    assert ifaces[0].name == "User"


def test_extract_type_alias(ts_file):
    nodes = TypeScriptParser().parse_file(str(ts_file))
    types = [n for n in nodes if n.kind == "ts_type"]
    assert len(types) == 1
    assert types[0].name == "Status"


def test_extract_enum(ts_file):
    nodes = TypeScriptParser().parse_file(str(ts_file))
    enums = [n for n in nodes if n.kind == "ts_enum"]
    assert len(enums) == 1
    assert enums[0].name == "Color"


def test_extract_function(ts_file):
    nodes = TypeScriptParser().parse_file(str(ts_file))
    funcs = [n for n in nodes if n.kind == "ts_function"]
    assert len(funcs) == 1
    assert funcs[0].name == "greet"


def test_extract_class_and_methods(ts_file):
    nodes = TypeScriptParser().parse_file(str(ts_file))
    classes = [n for n in nodes if n.kind == "ts_class"]
    assert len(classes) == 1
    assert classes[0].name == "Greeter"

    methods = [n for n in nodes if n.kind == "ts_method"]
    assert len(methods) == 2
    names = [n.name for n in methods]
    assert "hello" in names
    assert "goodbye" in names


def test_method_qualname(ts_file):
    nodes = TypeScriptParser().parse_file(str(ts_file))
    hello = [n for n in nodes if n.name == "hello" and n.kind == "ts_method"][0]
    assert hello.qualname == "Greeter.hello"
    assert hello.is_method is True


def test_ts_doc_interface(ts_file):
    nodes = TypeScriptParser().parse_file(str(ts_file))
    docs = [n for n in nodes if n.kind == "ts_doc" and n.name == "User"]
    assert len(docs) == 1


def test_ts_doc_function(ts_file):
    nodes = TypeScriptParser().parse_file(str(ts_file))
    docs = [n for n in nodes if n.kind == "ts_doc" and n.name == "greet"]
    assert len(docs) == 1


def test_ts_doc_method(ts_file):
    nodes = TypeScriptParser().parse_file(str(ts_file))
    docs = [n for n in nodes if n.kind == "ts_doc" and n.name == "hello"]
    assert len(docs) == 1
    assert docs[0].parent_id is not None


def test_no_doc_no_node(ts_file):
    nodes = TypeScriptParser().parse_file(str(ts_file))
    docs = [n for n in nodes if n.kind == "ts_doc" and n.name == "goodbye"]
    assert len(docs) == 0


def test_node_ids_stable(ts_file):
    p = TypeScriptParser()
    ids1 = [n.id for n in p.parse_file(str(ts_file))]
    ids2 = [n.id for n in p.parse_file(str(ts_file))]
    assert ids1 == ids2
