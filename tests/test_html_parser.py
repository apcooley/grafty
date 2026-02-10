"""Tests for HTML parser."""

import pytest
from grafty.parsers.html_parser import HTMLParser, HTMLNode, parse_html_file
from pathlib import Path
import tempfile


class TestHTMLNodeBasic:
    """Test HTMLNode creation and basic functionality."""

    def test_node_creation_basic(self):
        """Test creating a basic HTMLNode."""
        node = HTMLNode(
            kind="html_element",
            name="div",
            line_start=1,
            line_end=1,
        )
        assert node.kind == "html_element"
        assert node.name == "div"
        assert node.value is None
        assert node.children == []

    def test_node_with_id(self):
        """Test HTMLNode with ID attribute."""
        node = HTMLNode(
            kind="html_element",
            name="div",
            line_start=1,
            line_end=1,
            attributes={"id": "main"},
        )
        assert node.attributes["id"] == "main"

    def test_node_with_class(self):
        """Test HTMLNode with class attribute."""
        node = HTMLNode(
            kind="html_element",
            name="div",
            line_start=1,
            line_end=1,
            attributes={"class": "container active"},
        )
        assert node.attributes["class"] == "container active"

    def test_node_with_multiple_attributes(self):
        """Test HTMLNode with multiple attributes."""
        node = HTMLNode(
            kind="html_element",
            name="div",
            line_start=1,
            line_end=1,
            attributes={
                "id": "main",
                "class": "container",
                "data-value": "123",
            },
        )
        assert len(node.attributes) == 3
        assert node.attributes["id"] == "main"
        assert node.attributes["class"] == "container"
        assert node.attributes["data-value"] == "123"

    def test_node_with_children(self):
        """Test HTMLNode with child nodes."""
        parent = HTMLNode(kind="html_element", name="div")
        child1 = HTMLNode(kind="html_element", name="span")
        child2 = HTMLNode(kind="html_element", name="p")
        
        parent.add_child(child1)
        parent.add_child(child2)
        
        assert len(parent.children) == 2
        assert parent.children[0] == child1
        assert parent.children[1] == child2
        assert child1.parent == parent
        assert child2.parent == parent

    def test_node_to_dict(self):
        """Test converting HTMLNode to dictionary."""
        node = HTMLNode(
            kind="html_element",
            name="div",
            line_start=1,
            line_end=5,
            attributes={"id": "main"},
        )
        node_dict = node.to_dict()
        
        assert node_dict["kind"] == "html_element"
        assert node_dict["name"] == "div"
        assert node_dict["line_start"] == 1
        assert node_dict["line_end"] == 5
        assert node_dict["attributes"]["id"] == "main"


class TestHTMLParserBasic:
    """Test basic HTML parsing functionality."""

    def test_parse_simple_div(self):
        """Test parsing a simple div element."""
        parser = HTMLParser()
        html = "<div>Hello</div>"
        root, nodes = parser.parse(html)
        
        assert root is not None
        assert len(nodes) > 0
        # First real node should be the div
        element_nodes = [n for n in nodes if n.kind == "html_element"]
        assert len(element_nodes) > 0
        assert element_nodes[0].name == "div"

    def test_parse_div_with_id(self):
        """Test parsing div with ID attribute."""
        parser = HTMLParser()
        html = '<div id="main">Content</div>'
        root, nodes = parser.parse(html)
        
        # Should have html_id nodes
        id_nodes = [n for n in nodes if n.kind == "html_id"]
        assert len(id_nodes) > 0
        assert any(n.value == "main" for n in id_nodes)

    def test_parse_div_with_class(self):
        """Test parsing div with class attribute."""
        parser = HTMLParser()
        html = '<div class="container">Content</div>'
        root, nodes = parser.parse(html)
        
        # Should have html_class nodes
        class_nodes = [n for n in nodes if n.kind == "html_class"]
        assert len(class_nodes) > 0
        assert any(n.value == "container" for n in class_nodes)

    def test_parse_multiple_classes(self):
        """Test parsing element with multiple classes."""
        parser = HTMLParser()
        html = '<div class="container active primary">Content</div>'
        root, nodes = parser.parse(html)
        
        class_nodes = [n for n in nodes if n.kind == "html_class"]
        class_values = [n.value for n in class_nodes]
        
        assert "container" in class_values
        assert "active" in class_values
        assert "primary" in class_values

    def test_parse_button(self):
        """Test parsing button element."""
        parser = HTMLParser()
        html = "<button>Click Me</button>"
        root, nodes = parser.parse(html)
        
        element_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "button"]
        assert len(element_nodes) > 0

    def test_parse_heading(self):
        """Test parsing heading elements."""
        parser = HTMLParser()
        html = "<h1>Title</h1><h2>Subtitle</h2>"
        root, nodes = parser.parse(html)
        
        h1_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "h1"]
        h2_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "h2"]
        
        assert len(h1_nodes) > 0
        assert len(h2_nodes) > 0

    def test_parse_paragraph(self):
        """Test parsing paragraph element."""
        parser = HTMLParser()
        html = "<p>This is a paragraph.</p>"
        root, nodes = parser.parse(html)
        
        p_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "p"]
        assert len(p_nodes) > 0

    def test_parse_link(self):
        """Test parsing anchor element."""
        parser = HTMLParser()
        html = '<a href="http://example.com">Link</a>'
        root, nodes = parser.parse(html)
        
        a_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "a"]
        assert len(a_nodes) > 0
        assert a_nodes[0].attributes.get("href") == "http://example.com"

    def test_parse_image(self):
        """Test parsing image element."""
        parser = HTMLParser()
        html = '<img src="image.png" alt="Image">'
        root, nodes = parser.parse(html)
        
        img_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "img"]
        assert len(img_nodes) > 0
        assert img_nodes[0].attributes.get("src") == "image.png"
        assert img_nodes[0].attributes.get("alt") == "Image"


class TestHTMLParserAttributes:
    """Test attribute parsing."""

    def test_parse_data_attributes(self):
        """Test parsing data-* attributes."""
        parser = HTMLParser()
        html = '<div data-value="123" data-id="main">Content</div>'
        root, nodes = parser.parse(html)
        
        attr_nodes = [n for n in nodes if n.kind == "html_attr"]
        attr_values = {n.name: n.value for n in attr_nodes}
        
        assert "html_attr:data-value" in attr_values
        assert "html_attr:data-id" in attr_values

    def test_parse_aria_attributes(self):
        """Test parsing aria-* attributes."""
        parser = HTMLParser()
        html = '<button aria-label="Menu" aria-expanded="false">Menu</button>'
        root, nodes = parser.parse(html)
        
        attr_nodes = [n for n in nodes if n.kind == "html_attr"]
        attr_values = [n.name for n in attr_nodes]
        
        assert any("aria-label" in v for v in attr_values)
        assert any("aria-expanded" in v for v in attr_values)

    def test_parse_boolean_attributes(self):
        """Test parsing boolean attributes."""
        parser = HTMLParser()
        html = '<input type="checkbox" checked disabled>'
        root, nodes = parser.parse(html)
        
        input_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "input"]
        assert len(input_nodes) > 0


class TestHTMLParserNesting:
    """Test nested element parsing."""

    def test_parse_nested_divs(self):
        """Test parsing nested div elements."""
        parser = HTMLParser()
        html = """
        <div id="outer" class="container">
            <div id="inner" class="content">
                Nested content
            </div>
        </div>
        """
        root, nodes = parser.parse(html)
        
        # Should have multiple divs with different IDs
        id_nodes = [n for n in nodes if n.kind == "html_id"]
        id_values = [n.value for n in id_nodes]
        
        assert "outer" in id_values
        assert "inner" in id_values

    def test_parse_list_structure(self):
        """Test parsing list structure."""
        parser = HTMLParser()
        html = """
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        """
        root, nodes = parser.parse(html)
        
        ul_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "ul"]
        li_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "li"]
        
        assert len(ul_nodes) > 0
        assert len(li_nodes) == 2

    def test_parse_form_structure(self):
        """Test parsing form with inputs."""
        parser = HTMLParser()
        html = """
        <form id="login">
            <input type="text" name="username">
            <input type="password" name="password">
            <button type="submit">Login</button>
        </form>
        """
        root, nodes = parser.parse(html)
        
        form_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "form"]
        input_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "input"]
        button_nodes = [n for n in nodes if n.kind == "html_element" and n.name == "button"]
        
        assert len(form_nodes) > 0
        assert len(input_nodes) == 2
        assert len(button_nodes) > 0


class TestHTMLParserLineRanges:
    """Test line number tracking."""

    def test_single_line_element(self):
        """Test line tracking for single-line element."""
        parser = HTMLParser()
        html = "<div>Content</div>"
        root, nodes = parser.parse(html)
        
        element_nodes = [n for n in nodes if n.kind == "html_element"]
        assert len(element_nodes) > 0
        assert element_nodes[0].line_start > 0

    def test_multiline_element(self):
        """Test line tracking for multiline element."""
        parser = HTMLParser()
        html = """
        <div id="main">
            Content
        </div>
        """
        root, nodes = parser.parse(html)
        
        id_nodes = [n for n in nodes if n.kind == "html_id" and n.value == "main"]
        assert len(id_nodes) > 0


class TestHTMLParserIntegration:
    """Test HTML parser integration."""

    def test_parse_complex_page(self):
        """Test parsing a complex HTML page."""
        parser = HTMLParser()
        html = """
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <header id="page-header">
                <nav class="navbar">
                    <a href="/">Home</a>
                    <a href="/about">About</a>
                </nav>
            </header>
            <main id="content" class="container">
                <h1>Welcome</h1>
                <p>This is a test page</p>
            </main>
            <footer id="page-footer">
                <p>© 2024</p>
            </footer>
        </body>
        </html>
        """
        root, nodes = parser.parse(html)
        
        assert len(nodes) > 0
        # Should have IDs
        id_nodes = [n for n in nodes if n.kind == "html_id"]
        id_values = [n.value for n in id_nodes]
        assert "page-header" in id_values
        assert "content" in id_values
        assert "page-footer" in id_values
        
        # Should have classes
        class_nodes = [n for n in nodes if n.kind == "html_class"]
        class_values = [n.value for n in class_nodes]
        assert "navbar" in class_values
        assert "container" in class_values


class TestHTMLParserFileOperations:
    """Test file-based parsing."""

    def test_parse_html_file(self):
        """Test parsing HTML from a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "test.html"
            html_file.write_text("""
            <html>
            <body>
                <div id="main">Content</div>
            </body>
            </html>
            """)
            
            root, nodes = parse_html_file(str(html_file))
            assert root is not None
            assert len(nodes) > 0
            
            id_nodes = [n for n in nodes if n.kind == "html_id"]
            assert len(id_nodes) > 0


class TestHTMLParserEdgeCases:
    """Test edge cases."""

    def test_empty_attributes(self):
        """Test parsing with empty attribute values."""
        parser = HTMLParser()
        html = '<div data-value="">Content</div>'
        root, nodes = parser.parse(html)
        assert len(nodes) > 0

    def test_special_characters_in_attributes(self):
        """Test parsing with special characters in attributes."""
        parser = HTMLParser()
        html = '<div data-config=\'{"key": "value"}\'>Content</div>'
        root, nodes = parser.parse(html)
        assert len(nodes) > 0

    def test_html_entities(self):
        """Test parsing HTML entities."""
        parser = HTMLParser()
        html = '<div title="&copy; 2024">Copyright</div>'
        root, nodes = parser.parse(html)
        assert len(nodes) > 0
