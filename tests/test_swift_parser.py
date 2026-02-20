"""Tests for Swift parser."""
import pytest
from grafty.parsers.swift_ts import SwiftParser


@pytest.fixture
def swift_file(tmp_path):
    f = tmp_path / "Example.swift"
    f.write_text(
        "/// A greeter class.\n"
        "class Greeter {\n"
        "    /// Says hello.\n"
        "    func hello(name: String) -> String {\n"
        '        return "Hello " + name\n'
        "    }\n"
        "\n"
        "    func goodbye() {\n"
        '        print("bye")\n'
        "    }\n"
        "}\n"
        "\n"
        "protocol Doable {\n"
        "    func doIt()\n"
        "}\n"
        "\n"
        "struct Point {\n"
        "    var x: Int\n"
        "    var y: Int\n"
        "}\n"
        "\n"
        "enum Color {\n"
        "    case red, green, blue\n"
        "}\n"
        "\n"
        "func greet(name: String) -> String {\n"
        '    return "Hi " + name\n'
        "}\n"
    )
    return f


def test_class(swift_file):
    nodes = SwiftParser().parse_file(str(swift_file))
    classes = [n for n in nodes if n.kind == "swift_class"]
    assert len(classes) == 1
    assert classes[0].name == "Greeter"


def test_methods(swift_file):
    nodes = SwiftParser().parse_file(str(swift_file))
    methods = [n for n in nodes if n.kind == "swift_method"]
    names = [n.name for n in methods]
    assert "hello" in names
    assert "goodbye" in names


def test_protocol(swift_file):
    nodes = SwiftParser().parse_file(str(swift_file))
    protos = [n for n in nodes if n.kind == "swift_protocol"]
    assert len(protos) == 1
    assert protos[0].name == "Doable"


def test_struct(swift_file):
    nodes = SwiftParser().parse_file(str(swift_file))
    structs = [n for n in nodes if n.kind == "swift_struct"]
    assert len(structs) == 1
    assert structs[0].name == "Point"


def test_enum(swift_file):
    nodes = SwiftParser().parse_file(str(swift_file))
    enums = [n for n in nodes if n.kind == "swift_enum"]
    assert len(enums) == 1
    assert enums[0].name == "Color"


def test_function(swift_file):
    nodes = SwiftParser().parse_file(str(swift_file))
    funcs = [n for n in nodes if n.kind == "swift_function"]
    assert len(funcs) == 1
    assert funcs[0].name == "greet"


def test_doc_comment(swift_file):
    nodes = SwiftParser().parse_file(str(swift_file))
    docs = [n for n in nodes if n.kind == "swift_doc"]
    assert len(docs) >= 1
    greeter_doc = [d for d in docs if d.name == "Greeter"]
    assert len(greeter_doc) == 1


def test_method_qualname(swift_file):
    nodes = SwiftParser().parse_file(str(swift_file))
    hello = [n for n in nodes if n.name == "hello" and n.kind == "swift_method"][0]
    assert hello.qualname == "Greeter.hello"


def test_stable_ids(swift_file):
    p = SwiftParser()
    ids1 = [n.id for n in p.parse_file(str(swift_file))]
    ids2 = [n.id for n in p.parse_file(str(swift_file))]
    assert ids1 == ids2
