"""Tests for C# parser."""
import pytest
from grafty.parsers.csharp_ts import CSharpParser


@pytest.fixture
def cs_file(tmp_path):
    f = tmp_path / "Example.cs"
    f.write_text(
        "/// <summary>A greeter.</summary>\n"
        "public class Greeter {\n"
        "    /// <summary>Says hi.</summary>\n"
        "    public string Hello(string name) {\n"
        '        return "Hello " + name;\n'
        "    }\n"
        "\n"
        "    public int Add(int a, int b) {\n"
        "        return a + b;\n"
        "    }\n"
        "}\n"
        "\n"
        "interface IDoable {\n"
        "    void DoIt();\n"
        "}\n"
        "\n"
        "enum Color { Red, Green, Blue }\n"
        "\n"
        "struct Point { public int X; }\n"
    )
    return f


def test_class(cs_file):
    nodes = CSharpParser().parse_file(str(cs_file))
    classes = [n for n in nodes if n.kind == "cs_class"]
    assert len(classes) == 1
    assert classes[0].name == "Greeter"


def test_methods(cs_file):
    nodes = CSharpParser().parse_file(str(cs_file))
    methods = [n for n in nodes if n.kind == "cs_method"]
    names = [n.name for n in methods]
    assert "Hello" in names
    assert "Add" in names


def test_method_qualname(cs_file):
    nodes = CSharpParser().parse_file(str(cs_file))
    hello = [n for n in nodes if n.name == "Hello" and n.kind == "cs_method"][0]
    assert hello.qualname == "Greeter.Hello"


def test_interface(cs_file):
    nodes = CSharpParser().parse_file(str(cs_file))
    ifaces = [n for n in nodes if n.kind == "cs_interface"]
    assert len(ifaces) == 1
    assert ifaces[0].name == "IDoable"


def test_enum(cs_file):
    nodes = CSharpParser().parse_file(str(cs_file))
    enums = [n for n in nodes if n.kind == "cs_enum"]
    assert len(enums) == 1
    assert enums[0].name == "Color"


def test_struct(cs_file):
    nodes = CSharpParser().parse_file(str(cs_file))
    structs = [n for n in nodes if n.kind == "cs_struct"]
    assert len(structs) == 1
    assert structs[0].name == "Point"


def test_doc_comment(cs_file):
    nodes = CSharpParser().parse_file(str(cs_file))
    docs = [n for n in nodes if n.kind == "cs_doc"]
    assert len(docs) >= 1
    greeter_doc = [d for d in docs if d.name == "Greeter"]
    assert len(greeter_doc) == 1


def test_stable_ids(cs_file):
    p = CSharpParser()
    ids1 = [n.id for n in p.parse_file(str(cs_file))]
    ids2 = [n.id for n in p.parse_file(str(cs_file))]
    assert ids1 == ids2
