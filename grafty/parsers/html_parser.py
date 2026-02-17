"""HTML parser for grafty.

This module provides an HTML parser that builds a tree of Node objects
representing HTML elements with their attributes (id, class, data-*, aria-*).
"""

from html.parser import HTMLParser as StdHTMLParser
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from ..models import Node


@dataclass
class HTMLNode:
    """Represents an HTML element or attribute in the parse tree.

    Attributes:
        kind: Type of node (html_element, html_id, html_class, html_attr)
        name: Element tag name or attribute identifier
        value: For attributes, the attribute value
        line_start: Starting line number (1-indexed)
        line_end: Ending line number (1-indexed)
        col_start: Starting column (1-indexed)
        col_end: Ending column (1-indexed)
        attributes: Dictionary of element attributes
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
    attributes: Optional[Dict[str, str]] = None
    children: Optional[List['HTMLNode']] = None
    parent: Optional['HTMLNode'] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
        if self.children is None:
            self.children = []

    def add_child(self, child: 'HTMLNode') -> None:
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
            "attributes": self.attributes,
            "children": [child.to_dict() for child in self.children],
        }


class HTMLParser(StdHTMLParser):
    """Parse HTML and build a tree of HTMLNode objects.

    This parser extracts HTML elements and their attributes, creating nodes
    for elements, IDs, classes, and other important attributes.
    """

    def __init__(self):
        """Initialize the HTML parser."""
        super().__init__()
        self.root = None
        self.current_node = None
        self.nodes = []  # Flat list of all nodes
        self.line_num = 1
        self.col_num = 1
        self._init_time = True

    def parse(self, html_content: str) -> Tuple[HTMLNode, List[HTMLNode]]:
        """Parse HTML content and return the tree and flat node list.

        Args:
            html_content: HTML content as string

        Returns:
            Tuple of (root_node, flat_node_list)
        """
        # Reset state
        self.root = None
        self.current_node = None
        self.nodes = []
        self.line_num = 1
        self.col_num = 1

        # Create a virtual root to hold all elements
        self.root = HTMLNode(
            kind="document",
            name="document",
            line_start=1,
            line_end=1,
        )
        self.current_node = self.root

        # Parse HTML
        self.feed(html_content)

        return self.root, self.nodes

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        """Handle HTML start tags."""
        # Create element node
        node = HTMLNode(
            kind="html_element",
            name=tag,
            line_start=self.getpos()[0],
            col_start=self.getpos()[1],
        )

        # Process attributes
        attributes = {}
        if attrs:
            for attr_name, attr_value in attrs:
                if attr_value is None:
                    attr_value = ""
                attributes[attr_name] = attr_value

        node.attributes = attributes

        # Add current node as parent
        if self.current_node:
            self.current_node.add_child(node)

        # Add to flat list
        self.nodes.append(node)

        # Create child nodes for special attributes
        if "id" in attributes:
            id_node = HTMLNode(
                kind="html_id",
                name=f"html_id:{attributes['id']}",
                value=attributes["id"],
                line_start=node.line_start,
                col_start=node.col_start,
            )
            node.add_child(id_node)
            self.nodes.append(id_node)

        if "class" in attributes:
            classes = attributes["class"].split()
            for cls in classes:
                class_node = HTMLNode(
                    kind="html_class",
                    name=f"html_class:{cls}",
                    value=cls,
                    line_start=node.line_start,
                    col_start=node.col_start,
                )
                node.add_child(class_node)
                self.nodes.append(class_node)

        # Create nodes for data-* and aria-* attributes
        for attr_name, attr_value in attributes.items():
            if attr_name.startswith("data-") or attr_name.startswith("aria-"):
                attr_node = HTMLNode(
                    kind="html_attr",
                    name=f"html_attr:{attr_name}",
                    value=attr_value,
                    line_start=node.line_start,
                    col_start=node.col_start,
                )
                node.add_child(attr_node)
                self.nodes.append(attr_node)

        # Update current node for nested elements
        self.current_node = node

    def handle_endtag(self, tag: str) -> None:
        """Handle HTML end tags."""
        # Update end position
        if self.current_node and self.current_node.name == tag:
            self.current_node.line_end = self.getpos()[0]
            self.current_node.col_end = self.getpos()[1]

        # Pop back to parent
        if self.current_node and self.current_node.parent:
            self.current_node = self.current_node.parent

    def handle_data(self, data: str) -> None:
        """Handle text content in HTML."""
        # We could create text nodes if needed
        pass

    def parse_file(self, file_path: str) -> List[Node]:
        """Parse an HTML file and return list of grafty Node objects with parent_id.

        Args:
            file_path: Path to HTML file

        Returns:
            List of Node objects with parent relationships
        """
        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        # Parse HTML
        root, html_nodes = self.parse(content)

        # Filter to only html_element nodes (skip ids, classes, attrs)
        element_nodes = [n for n in html_nodes if n.kind == "html_element"]

        # Convert HTMLNode objects to grafty Node objects with parent_id
        nodes: List[Node] = []
        html_to_grafty: Dict[int, str] = {}  # id(html_node) -> grafty_node_id

        for html_node in element_nodes:
            # Compute end_line: for HTML, we use the parser's line tracking
            end_line = html_node.line_end if html_node.line_end > html_node.line_start else html_node.line_start

            # Create grafty Node
            node_id = Node.compute_id(file_path, "html_element", html_node.name, html_node.line_start)
            node = Node(
                id=node_id,
                kind="html_element",
                name=html_node.name,
                path=file_path,
                start_line=html_node.line_start,
                end_line=end_line,
            )
            nodes.append(node)
            html_to_grafty[id(html_node)] = node_id

        # Build parent_id relationships
        for html_node in element_nodes:
            grafty_id = html_to_grafty[id(html_node)]

            # Find the grafty Node for this html_node
            grafty_node = next((n for n in nodes if n.id == grafty_id), None)
            if not grafty_node:
                continue

            # Find parent
            if html_node.parent and html_node.parent.kind == "html_element":
                parent_html_id = id(html_node.parent)
                if parent_html_id in html_to_grafty:
                    parent_grafty_id = html_to_grafty[parent_html_id]
                    grafty_node.parent_id = parent_grafty_id

                    # Add to parent's children_ids
                    parent_node = next((n for n in nodes if n.id == parent_grafty_id), None)
                    if parent_node:
                        parent_node.children_ids.append(grafty_id)

        return nodes


def parse_html_file(file_path: str) -> Tuple[HTMLNode, List[HTMLNode]]:
    """Parse an HTML file and return the tree and flat node list.

    Args:
        file_path: Path to HTML file

    Returns:
        Tuple of (root_node, flat_node_list)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = HTMLParser()
    return parser.parse(content)


def extract_html_nodes_by_kind(nodes: List[HTMLNode], kind: str) -> List[HTMLNode]:
    """Filter nodes by kind.

    Args:
        nodes: List of HTMLNode objects
        kind: Node kind to filter by

    Returns:
        List of nodes matching the kind
    """
    return [n for n in nodes if n.kind == kind]


def find_html_node_by_name(nodes: List[HTMLNode], name: str) -> Optional[HTMLNode]:
    """Find first node matching a name.

    Args:
        nodes: List of HTMLNode objects
        name: Name to search for

    Returns:
        First matching node or None
    """
    for node in nodes:
        if node.name == name:
            return node
    return None


def extract_html_ids(nodes: List[HTMLNode]) -> List[str]:
    """Extract all ID values from HTML nodes.

    Args:
        nodes: List of HTMLNode objects

    Returns:
        List of unique IDs
    """
    ids = set()
    for node in nodes:
        if node.kind == "html_id" and node.value:
            ids.add(node.value)
    return sorted(list(ids))


def extract_html_classes(nodes: List[HTMLNode]) -> List[str]:
    """Extract all class values from HTML nodes.

    Args:
        nodes: List of HTMLNode objects

    Returns:
        List of unique classes
    """
    classes = set()
    for node in nodes:
        if node.kind == "html_class" and node.value:
            classes.add(node.value)
    return sorted(list(classes))
