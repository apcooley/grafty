"""Tests for Java parser."""

import pytest
from grafty.parsers.java_ts import JavaParser


@pytest.fixture
def java_file(tmp_path):
    f = tmp_path / "Example.java"
    f.write_text(
        "package com.example;\n"
        "\n"
        "/**\n"
        " * A greeter class.\n"
        " */\n"
        "public class Greeter {\n"
        "    /** Says hello. */\n"
        "    public String hello(String name) {\n"
        '        return "Hello " + name;\n'
        "    }\n"
        "\n"
        "    public int add(int a, int b) {\n"
        "        return a + b;\n"
        "    }\n"
        "}\n"
        "\n"
        "interface Doable {\n"
        "    void doIt();\n"
        "}\n"
        "\n"
        "enum Status {\n"
        "    ACTIVE, INACTIVE\n"
        "}\n"
    )
    return f


def test_extract_class(java_file):
    nodes = JavaParser().parse_file(str(java_file))
    classes = [n for n in nodes if n.kind == "java_class"]
    assert len(classes) == 1
    assert classes[0].name == "Greeter"


def test_extract_methods(java_file):
    nodes = JavaParser().parse_file(str(java_file))
    methods = [n for n in nodes if n.kind == "java_method"]
    assert len(methods) == 3  # hello, add, doIt (interface method)
    names = [n.name for n in methods]
    assert "hello" in names
    assert "add" in names
    assert "doIt" in names


def test_method_qualname(java_file):
    nodes = JavaParser().parse_file(str(java_file))
    hello = [n for n in nodes if n.name == "hello" and n.kind == "java_method"][0]
    assert hello.qualname == "Greeter.hello"
    assert hello.is_method is True


def test_extract_interface(java_file):
    nodes = JavaParser().parse_file(str(java_file))
    ifaces = [n for n in nodes if n.kind == "java_interface"]
    assert len(ifaces) == 1
    assert ifaces[0].name == "Doable"


def test_extract_enum(java_file):
    nodes = JavaParser().parse_file(str(java_file))
    enums = [n for n in nodes if n.kind == "java_enum"]
    assert len(enums) == 1
    assert enums[0].name == "Status"


def test_javadoc_class(java_file):
    nodes = JavaParser().parse_file(str(java_file))
    docs = [n for n in nodes if n.kind == "java_doc" and n.name == "Greeter"]
    assert len(docs) == 1
    assert docs[0].start_line == 3


def test_javadoc_method(java_file):
    nodes = JavaParser().parse_file(str(java_file))
    docs = [n for n in nodes if n.kind == "java_doc" and n.name == "hello"]
    assert len(docs) == 1
    assert docs[0].parent_id is not None


def test_no_javadoc_no_node(java_file):
    nodes = JavaParser().parse_file(str(java_file))
    docs = [n for n in nodes if n.kind == "java_doc" and n.name == "add"]
    assert len(docs) == 0


def test_node_ids_stable(java_file):
    p = JavaParser()
    ids1 = [n.id for n in p.parse_file(str(java_file))]
    ids2 = [n.id for n in p.parse_file(str(java_file))]
    assert ids1 == ids2
