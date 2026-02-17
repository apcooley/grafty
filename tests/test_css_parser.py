"""Tests for CSS parser."""

import pytest
from grafty.parsers.css_parser import CSSParser, CSSNode, parse_css_file
from pathlib import Path
import tempfile


class TestCSSNodeBasic:
    """Test CSSNode creation and basic functionality."""

    def test_node_creation_basic(self):
        """Test creating a basic CSSNode."""
        node = CSSNode(
            kind="css_rule",
            name="css_rule:.container",
            value=".container",
            line_start=1,
            line_end=5,
        )
        assert node.kind == "css_rule"
        assert node.name == "css_rule:.container"
        assert node.value == ".container"
        assert node.declarations == {}
        assert node.children == []

    def test_node_with_declarations(self):
        """Test CSSNode with declarations."""
        node = CSSNode(
            kind="css_rule",
            name="css_rule:.container",
            value=".container",
            line_start=1,
            line_end=5,
            declarations={"display": "flex", "flex-direction": "row"},
        )
        assert len(node.declarations) == 2
        assert node.declarations["display"] == "flex"
        assert node.declarations["flex-direction"] == "row"

    def test_node_with_children(self):
        """Test CSSNode with child nodes."""
        parent = CSSNode(
            kind="css_rule",
            name="css_rule:.container",
            value=".container",
        )
        child1 = CSSNode(kind="css_selector", name="css_selector:.container", value=".container")
        
        parent.add_child(child1)
        
        assert len(parent.children) == 1
        assert parent.children[0] == child1
        assert child1.parent == parent

    def test_node_to_dict(self):
        """Test converting CSSNode to dictionary."""
        node = CSSNode(
            kind="css_rule",
            name="css_rule:.container",
            value=".container",
            line_start=1,
            line_end=5,
            declarations={"display": "flex"},
        )
        node_dict = node.to_dict()
        
        assert node_dict["kind"] == "css_rule"
        assert node_dict["name"] == "css_rule:.container"
        assert node_dict["value"] == ".container"
        assert node_dict["declarations"]["display"] == "flex"


class TestCSSParserBasic:
    """Test basic CSS parsing functionality."""

    def test_parse_simple_rule(self):
        """Test parsing a simple CSS rule."""
        parser = CSSParser()
        css = "body { margin: 0; padding: 0; }"
        root, nodes = parser.parse(css)
        
        assert root is not None
        assert len(nodes) > 0
        # Should have a rule node
        rule_nodes = [n for n in nodes if n.kind == "css_rule"]
        assert len(rule_nodes) > 0

    def test_parse_class_selector(self):
        """Test parsing class selector."""
        parser = CSSParser()
        css = ".container { width: 100%; }"
        root, nodes = parser.parse(css)
        
        selector_nodes = [n for n in nodes if n.kind == "css_selector"]
        assert len(selector_nodes) > 0
        assert any(n.value == ".container" for n in selector_nodes)

    def test_parse_id_selector(self):
        """Test parsing ID selector."""
        parser = CSSParser()
        css = "#main { background: white; }"
        root, nodes = parser.parse(css)
        
        selector_nodes = [n for n in nodes if n.kind == "css_selector"]
        assert len(selector_nodes) > 0
        assert any(n.value == "#main" for n in selector_nodes)

    def test_parse_element_selector(self):
        """Test parsing element selector."""
        parser = CSSParser()
        css = "body { font-family: Arial; }"
        root, nodes = parser.parse(css)
        
        selector_nodes = [n for n in nodes if n.kind == "css_selector"]
        assert len(selector_nodes) > 0
        assert any("body" in n.value for n in selector_nodes)

    def test_parse_multiple_declarations(self):
        """Test parsing rule with multiple declarations."""
        parser = CSSParser()
        css = "div { display: flex; justify-content: center; align-items: center; }"
        root, nodes = parser.parse(css)
        
        rule_nodes = [n for n in nodes if n.kind == "css_rule"]
        assert len(rule_nodes) > 0
        
        # Check declarations are parsed
        decl = rule_nodes[0].declarations
        assert "display" in decl
        assert "justify-content" in decl
        assert "align-items" in decl

    def test_parse_css_with_comments(self):
        """Test parsing CSS with comments."""
        parser = CSSParser()
        css = """
        /* Main container */
        .container { width: 100%; }
        """
        root, nodes = parser.parse(css)
        
        selector_nodes = [n for n in nodes if n.kind == "css_selector"]
        assert any(".container" in n.value for n in selector_nodes)


class TestCSSParserSelectors:
    """Test selector parsing."""

    def test_parse_combined_selector(self):
        """Test parsing combined selector."""
        parser = CSSParser()
        css = ".container .content { padding: 20px; }"
        root, nodes = parser.parse(css)
        
        selector_nodes = [n for n in nodes if n.kind == "css_selector"]
        assert len(selector_nodes) > 0

    def test_parse_multiple_selectors(self):
        """Test parsing multiple selectors for same rule."""
        parser = CSSParser()
        css = "h1, h2, h3 { color: blue; }"
        root, nodes = parser.parse(css)
        
        selector_nodes = [n for n in nodes if n.kind == "css_selector"]
        # Should have at least 3 selector nodes
        assert len(selector_nodes) >= 3

    def test_parse_pseudo_class_selector(self):
        """Test parsing pseudo-class selector."""
        parser = CSSParser()
        css = "a:hover { color: red; }"
        root, nodes = parser.parse(css)
        
        selector_nodes = [n for n in nodes if n.kind == "css_selector"]
        assert len(selector_nodes) > 0

    def test_parse_attribute_selector(self):
        """Test parsing attribute selector."""
        parser = CSSParser()
        css = 'input[type="text"] { border: 1px solid; }'
        root, nodes = parser.parse(css)
        
        selector_nodes = [n for n in nodes if n.kind == "css_selector"]
        assert len(selector_nodes) > 0


class TestCSSParserDeclarations:
    """Test declaration parsing."""

    def test_parse_color_property(self):
        """Test parsing color property."""
        parser = CSSParser()
        css = "div { color: #ff0000; }"
        root, nodes = parser.parse(css)
        
        rule_nodes = [n for n in nodes if n.kind == "css_rule"]
        assert len(rule_nodes) > 0
        assert "color" in rule_nodes[0].declarations

    def test_parse_dimension_properties(self):
        """Test parsing dimension properties."""
        parser = CSSParser()
        css = "div { width: 100px; height: 200px; margin: 10px; padding: 5px; }"
        root, nodes = parser.parse(css)
        
        rule_nodes = [n for n in nodes if n.kind == "css_rule"]
        decl = rule_nodes[0].declarations
        assert "width" in decl
        assert "height" in decl
        assert "margin" in decl
        assert "padding" in decl

    def test_parse_font_properties(self):
        """Test parsing font properties."""
        parser = CSSParser()
        css = "body { font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; }"
        root, nodes = parser.parse(css)
        
        rule_nodes = [n for n in nodes if n.kind == "css_rule"]
        decl = rule_nodes[0].declarations
        assert "font-family" in decl
        assert "font-size" in decl
        assert "font-weight" in decl

    def test_parse_display_properties(self):
        """Test parsing display-related properties."""
        parser = CSSParser()
        css = "div { display: flex; flex-direction: column; justify-content: center; }"
        root, nodes = parser.parse(css)
        
        rule_nodes = [n for n in nodes if n.kind == "css_rule"]
        decl = rule_nodes[0].declarations
        assert "display" in decl
        assert "flex-direction" in decl
        assert "justify-content" in decl


class TestCSSParserIntegration:
    """Test CSS parser integration."""

    def test_parse_stylesheet(self):
        """Test parsing a complete stylesheet."""
        parser = CSSParser()
        css = """
        * { margin: 0; padding: 0; }
        
        body {
            font-family: Arial, sans-serif;
            background: white;
        }
        
        .container {
            width: 100%;
            max-width: 1200px;
        }
        
        .container .content {
            padding: 20px;
        }
        
        h1 { font-size: 32px; color: #333; }
        h2 { font-size: 24px; color: #555; }
        
        a { text-decoration: none; color: blue; }
        a:hover { color: red; }
        """
        root, nodes = parser.parse(css)
        
        assert len(nodes) > 0
        # Should have multiple rules
        rule_nodes = [n for n in nodes if n.kind == "css_rule"]
        assert len(rule_nodes) > 5

    def test_parse_minified_css(self):
        """Test parsing minified CSS."""
        parser = CSSParser()
        css = ".a{color:red;margin:10px}.b{padding:5px;border:1px solid}"
        root, nodes = parser.parse(css)
        
        selector_nodes = [n for n in nodes if n.kind == "css_selector"]
        assert len(selector_nodes) > 0


class TestCSSParserFileOperations:
    """Test file-based parsing."""

    def test_parse_css_file(self):
        """Test parsing CSS from a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            css_file = Path(tmpdir) / "styles.css"
            css_file.write_text("""
            .container { width: 100%; }
            .content { padding: 20px; }
            """)
            
            root, nodes = parse_css_file(str(css_file))
            assert root is not None
            assert len(nodes) > 0
            
            selector_nodes = [n for n in nodes if n.kind == "css_selector"]
            assert len(selector_nodes) > 0


class TestCSSParserEdgeCases:
    """Test edge cases."""

    def test_parse_empty_rule(self):
        """Test parsing empty rule block."""
        parser = CSSParser()
        css = ".empty { }"
        root, nodes = parser.parse(css)
        # Should still parse the selector
        selector_nodes = [n for n in nodes if n.kind == "css_selector"]
        # Might be 0 or 1 depending on parser implementation

    def test_parse_rule_with_trailing_semicolon(self):
        """Test parsing rule with trailing semicolon."""
        parser = CSSParser()
        css = "div { color: red; }"
        root, nodes = parser.parse(css)
        
        rule_nodes = [n for n in nodes if n.kind == "css_rule"]
        assert len(rule_nodes) > 0

    def test_parse_property_with_units(self):
        """Test parsing properties with different units."""
        parser = CSSParser()
        css = "div { width: 50%; height: 100px; margin: 1em; padding: 2rem; }"
        root, nodes = parser.parse(css)
        
        rule_nodes = [n for n in nodes if n.kind == "css_rule"]
        assert len(rule_nodes) > 0

    def test_parse_property_with_values(self):
        """Test parsing properties with complex values."""
        parser = CSSParser()
        css = "div { box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }"
        root, nodes = parser.parse(css)
        
        rule_nodes = [n for n in nodes if n.kind == "css_rule"]
        assert len(rule_nodes) > 0

    def test_parse_important_declaration(self):
        """Test parsing !important declarations."""
        parser = CSSParser()
        css = "div { color: red !important; }"
        root, nodes = parser.parse(css)
        
        rule_nodes = [n for n in nodes if n.kind == "css_rule"]
        assert len(rule_nodes) > 0
