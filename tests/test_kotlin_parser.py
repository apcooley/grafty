"""Tests for Kotlin parser."""
import pytest
from grafty.parsers.kotlin_ts import KotlinParser


@pytest.fixture
def kt_file(tmp_path):
    f = tmp_path / "Example.kt"
    f.write_text(
        "/** A data class. */\n"
        "data class User(val name: String, val age: Int)\n"
        "\n"
        "fun greet(user: User): String {\n"
        "    return user.name\n"
        "}\n"
        "\n"
        "interface Doable {\n"
        "    fun doIt()\n"
        "}\n"
        "\n"
        "enum class Color { RED, GREEN, BLUE }\n"
        "\n"
        "object Singleton {\n"
        "    fun instance() = this\n"
        "}\n"
    )
    return f


def test_data_class(kt_file):
    nodes = KotlinParser().parse_file(str(kt_file))
    dcs = [n for n in nodes if n.kind == "kt_data_class"]
    assert len(dcs) == 1
    assert dcs[0].name == "User"


def test_function(kt_file):
    nodes = KotlinParser().parse_file(str(kt_file))
    funcs = [n for n in nodes if n.kind == "kt_function"]
    assert len(funcs) == 1
    assert funcs[0].name == "greet"


def test_interface(kt_file):
    nodes = KotlinParser().parse_file(str(kt_file))
    ifaces = [n for n in nodes if n.kind == "kt_interface"]
    assert len(ifaces) == 1
    assert ifaces[0].name == "Doable"


def test_enum(kt_file):
    nodes = KotlinParser().parse_file(str(kt_file))
    enums = [n for n in nodes if n.kind == "kt_enum"]
    assert len(enums) == 1
    assert enums[0].name == "Color"


def test_object(kt_file):
    nodes = KotlinParser().parse_file(str(kt_file))
    objs = [n for n in nodes if n.kind == "kt_object"]
    assert len(objs) == 1
    assert objs[0].name == "Singleton"


def test_method_in_object(kt_file):
    nodes = KotlinParser().parse_file(str(kt_file))
    methods = [n for n in nodes if n.kind == "kt_method"]
    names = [n.name for n in methods]
    assert "instance" in names


def test_kdoc(kt_file):
    nodes = KotlinParser().parse_file(str(kt_file))
    docs = [n for n in nodes if n.kind == "kt_doc"]
    assert len(docs) >= 1
    assert docs[0].name == "User"


def test_stable_ids(kt_file):
    p = KotlinParser()
    ids1 = [n.id for n in p.parse_file(str(kt_file))]
    ids2 = [n.id for n in p.parse_file(str(kt_file))]
    assert ids1 == ids2
