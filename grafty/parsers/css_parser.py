"""CSS parser for grafty.

This module provides a CSS parser that builds a tree of Node objects
representing CSS rules, selectors, and declarations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import re

from ..models import Node


@dataclass
class CSSNode:
    """Represents a CSS rule, selector, or declaration in the parse tree.
    
    Attributes:
        kind: Type of node (css_rule, css_selector, css_declaration)
        name: Selector or rule identifier
        value: For declarations, the property value
        line_start: Starting line number (1-indexed)
        line_end: Ending line number (1-indexed)
        col_start: Starting column (1-indexed)
        col_end: Ending column (1-indexed)
        declarations: Dictionary of CSS properties and values
        children: Child nodes
        parent: Parent node reference
    """
    kind: str
    name: str
    value: Optional[str] = None
    line_start: int = 1
    line_end: int = 1
    col_start: int = 1
    col_end: int = 1
    declarations: Optional[Dict[str, str]] = None
    children: Optional[List['CSSNode']] = None
    parent: Optional['CSSNode'] = None

    def __post_init__(self):
        if self.declarations is None:
            self.declarations = {}
        if self.children is None:
            self.children = []

    def add_child(self, child: 'CSSNode') -> None:
        """Add a child node."""
        self.children.append(child)
        child.parent = self

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "kind": self.kind,
            "name": self.name,
            "value": self.value,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "col_start": self.col_start,
            "col_end": self.col_end,
            "declarations": self.declarations,
            "children": [child.to_dict() for child in self.children],
        }


class CSSParser:
    """Parse CSS and build a tree of CSSNode objects.
    
    This parser uses cssutils when available for robustness, with a
    fallback regex-based parser for edge cases.
    """

    def __init__(self, use_cssutils: bool = True):
        """Initialize the CSS parser.
        
        Args:
            use_cssutils: Whether to attempt using cssutils library
        """
        self.use_cssutils = use_cssutils
        self.cssutils_available = False

        if use_cssutils:
            try:
                import cssutils
                self.cssutils = cssutils
                self.cssutils_available = True
            except ImportError:
                self.use_cssutils = False

        self.root = None
        self.nodes = []
        self.line_num = 1

    def parse(self, css_content: str) -> Tuple[CSSNode, List[CSSNode]]:
        """Parse CSS content and return the tree and flat node list.
        
        Args:
            css_content: CSS content as string
            
        Returns:
            Tuple of (root_node, flat_node_list)
        """
        # Reset state
        self.root = CSSNode(
            kind="stylesheet",
            name="stylesheet",
            line_start=1,
        )
        self.nodes = []

        # Try cssutils first if available
        if self.cssutils_available:
            return self._parse_with_cssutils(css_content)
        else:
            return self._parse_with_regex(css_content)

    def _parse_with_cssutils(self, css_content: str) -> Tuple[CSSNode, List[CSSNode]]:
        """Parse CSS using cssutils library.
        
        Args:
            css_content: CSS content as string
            
        Returns:
            Tuple of (root_node, flat_node_list)
        """
        import cssutils

        # Suppress cssutils warnings
        import logging as log_module
        log_module.getLogger("cssutils").setLevel(log_module.CRITICAL)

        try:
            sheet = cssutils.parseString(css_content)
        except Exception:
            # Fallback to regex parser on error
            return self._parse_with_regex(css_content)

        line_num = 1

        # Process rules
        for rule in sheet:
            if hasattr(rule, "selectorList"):
                # Regular CSS rule
                selector_text = rule.selectorText if hasattr(rule, "selectorText") else ""

                # Create rule node
                rule_node = CSSNode(
                    kind="css_rule",
                    name=f"css_rule:{selector_text}",
                    value=selector_text,
                    line_start=line_num,
                )

                # Parse declarations
                declarations = {}
                if hasattr(rule, "style"):
                    for prop in rule.style:
                        declarations[prop.name] = prop.value

                rule_node.declarations = declarations

                # Create individual selector nodes
                if hasattr(rule, "selectorList"):
                    for selector in rule.selectorList:
                        sel_text = selector.selectorText if hasattr(selector, "selectorText") else str(selector)
                        sel_node = CSSNode(
                            kind="css_selector",
                            name=f"css_selector:{sel_text}",
                            value=sel_text,
                            line_start=line_num,
                        )
                        rule_node.add_child(sel_node)
                        self.nodes.append(sel_node)

                self.root.add_child(rule_node)
                self.nodes.append(rule_node)
                line_num += 1

        return self.root, self.nodes

    def _parse_with_regex(self, css_content: str) -> Tuple[CSSNode, List[CSSNode]]:
        """Parse CSS using regex fallback.
        
        This is more robust for minified and edge-case CSS.
        
        Args:
            css_content: CSS content as string
            
        Returns:
            Tuple of (root_node, flat_node_list)
        """
        # Remove comments
        css_no_comments = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)

        # Pattern to match CSS rules: selector { declarations }
        rule_pattern = r'([^{]+)\{([^}]*)\}'

        line_num = 1

        for match in re.finditer(rule_pattern, css_no_comments):
            selector_str = match.group(1).strip()
            declarations_str = match.group(2).strip()

            # Skip empty rules
            if not selector_str or not declarations_str:
                continue

            # Parse selectors (can be comma-separated)
            selectors = [s.strip() for s in selector_str.split(',')]

            # Parse declarations
            declarations = {}
            for decl in declarations_str.split(';'):
                decl = decl.strip()
                if ':' in decl:
                    prop, value = decl.split(':', 1)
                    declarations[prop.strip()] = value.strip()

            # Create rule node for the full selector string
            rule_node = CSSNode(
                kind="css_rule",
                name=f"css_rule:{selector_str}",
                value=selector_str,
                line_start=line_num,
            )
            rule_node.declarations = declarations

            # Create individual selector nodes
            for selector in selectors:
                sel_node = CSSNode(
                    kind="css_selector",
                    name=f"css_selector:{selector}",
                    value=selector,
                    line_start=line_num,
                )
                rule_node.add_child(sel_node)
                self.nodes.append(sel_node)

            self.root.add_child(rule_node)
            self.nodes.append(rule_node)

            # Update line count (approximation)
            line_num += match.group(0).count('\n') + 1

        return self.root, self.nodes

    def parse_file(self, file_path: str) -> List[Node]:
        """Parse a CSS file and return list of grafty Node objects with parent_id.
        
        Args:
            file_path: Path to CSS file
            
        Returns:
            List of Node objects with parent relationships
        """
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        # Parse CSS
        root, css_nodes = self.parse(content)

        # Filter to only css_rule nodes (skip declarations)
        rule_nodes = [n for n in css_nodes if n.kind == "css_rule"]

        # Convert CSSNode objects to grafty Node objects with parent_id
        nodes: List[Node] = []
        css_to_grafty: Dict[int, str] = {}  # id(css_node) -> grafty_node_id

        for css_node in rule_nodes:
            # Compute end_line
            end_line = css_node.line_end if css_node.line_end > css_node.line_start else css_node.line_start

            # Create grafty Node
            node_id = Node.compute_id(file_path, "css_rule", css_node.name, css_node.line_start)
            node = Node(
                id=node_id,
                kind="css_rule",
                name=css_node.name,
                path=file_path,
                start_line=css_node.line_start,
                end_line=end_line,
            )
            nodes.append(node)
            css_to_grafty[id(css_node)] = node_id

        # Build parent_id relationships
        for css_node in rule_nodes:
            grafty_id = css_to_grafty[id(css_node)]

            # Find the grafty Node for this css_node
            grafty_node = next((n for n in nodes if n.id == grafty_id), None)
            if not grafty_node:
                continue

            # Find parent (for nested CSS like @media)
            if css_node.parent and css_node.parent.kind == "css_rule":
                parent_css_id = id(css_node.parent)
                if parent_css_id in css_to_grafty:
                    parent_grafty_id = css_to_grafty[parent_css_id]
                    grafty_node.parent_id = parent_grafty_id

                    # Add to parent's children_ids
                    parent_node = next((n for n in nodes if n.id == parent_grafty_id), None)
                    if parent_node:
                        parent_node.children_ids.append(grafty_id)

        return nodes


def parse_css_file(file_path: str) -> Tuple[CSSNode, List[CSSNode]]:
    """Parse a CSS file and return the tree and flat node list.
    
    Args:
        file_path: Path to CSS file
        
    Returns:
        Tuple of (root_node, flat_node_list)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = CSSParser()
    return parser.parse(content)


def extract_css_nodes_by_kind(nodes: List[CSSNode], kind: str) -> List[CSSNode]:
    """Filter nodes by kind.
    
    Args:
        nodes: List of CSSNode objects
        kind: Node kind to filter by
        
    Returns:
        List of nodes matching the kind
    """
    return [n for n in nodes if n.kind == kind]


def find_css_node_by_selector(nodes: List[CSSNode], selector: str) -> Optional[CSSNode]:
    """Find CSS rule by selector.
    
    Args:
        nodes: List of CSSNode objects
        selector: Selector to search for
        
    Returns:
        First matching CSS rule or None
    """
    for node in nodes:
        if node.kind == "css_rule" and selector in node.value:
            return node
    return None


def extract_css_selectors(nodes: List[CSSNode]) -> List[str]:
    """Extract all selectors from CSS nodes.
    
    Args:
        nodes: List of CSSNode objects
        
    Returns:
        List of unique selectors
    """
    selectors = set()
    for node in nodes:
        if node.kind == "css_selector" and node.value:
            selectors.add(node.value)
    return sorted(list(selectors))


def extract_css_properties(nodes: List[CSSNode]) -> Dict[str, int]:
    """Extract all CSS property names and their frequencies.
    
    Args:
        nodes: List of CSSNode objects
        
    Returns:
        Dictionary mapping property names to usage count
    """
    properties = {}
    for node in nodes:
        if node.kind == "css_rule":
            for prop in node.declarations.keys():
                properties[prop] = properties.get(prop, 0) + 1
    return properties
