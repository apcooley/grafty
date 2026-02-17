"""
json_parser.py — JSON indexing via Tree-sitter.
"""
from typing import List, Optional, Dict
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_json
except ImportError:
    print("Warning: tree-sitter-json module not found. Parser might fail.")
    pass

from ..models import Node


class JsonParser:
    """Index JSON files using Tree-sitter."""

    def __init__(self):
        try:
            self.language = Language(tree_sitter_json.language())
            self.parser = Parser(self.language)
        except NameError:
            self.parser = None

    def parse_file(self, file_path: str) -> List[Node]:
        """Index a JSON file and return list of nodes."""
        if not self.parser:
            print(f"Warning: Cannot parse {file_path} due to missing TS setup.")
            return []

        p = Path(file_path)
        content = p.read_text(encoding="utf-8")

        try:
            tree = self.parser.parse(content.encode("utf-8"))
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return []

        nodes: List[Node] = []
        nodes_dict: Dict[int, Node] = {}

        self._walk_tree(
            tree.root_node,
            file_path,
            content,
            nodes,
            nodes_dict,
            parent_id=None,
            inside_pair_value=False,
        )

        return nodes

    def _walk_tree(
        self,
        node,
        file_path: str,
        content: str,
        nodes: List[Node],
        nodes_dict: Dict[int, Node],
        parent_id: Optional[str],
        inside_pair_value: bool = False,
    ) -> None:
        """Recursively walk Tree-sitter AST, extracting definitions.
        
        Strategy:
        - Index the root object (document level)
        - Index all 'pair' nodes as json_member (the key-value pairs)
        - Skip object/array nodes that are values of pairs (redundant)
        - Index array elements that are objects (for config arrays)
        """
        
        if node.type == "document":
            # Process children
            for child in node.children:
                self._walk_tree(child, file_path, content, nodes, nodes_dict, 
                               parent_id, inside_pair_value=False)
            return

        if node.type == "object":
            # Only create a node for the root object or objects inside arrays
            # Skip objects that are direct values of pairs (parent_id will be a json_member)
            if parent_id is None:
                # Root object
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                node_id = Node.compute_id(file_path, "json_root", "root", start_line)
                
                grafty_node = Node(
                    id=node_id,
                    kind="json_root",
                    name="root",
                    path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    parent_id=None,
                )
                nodes.append(grafty_node)
                nodes_dict[id(node)] = grafty_node
                
                # Process children with this as parent
                for child in node.children:
                    self._walk_tree(child, file_path, content, nodes, nodes_dict,
                                   grafty_node.id, inside_pair_value=False)
            elif inside_pair_value:
                # Object is value of a pair - skip creating node, just recurse
                for child in node.children:
                    self._walk_tree(child, file_path, content, nodes, nodes_dict,
                                   parent_id, inside_pair_value=False)
            else:
                # Object inside an array - create indexed node
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                name = f"[{start_line}]"
                node_id = Node.compute_id(file_path, "json_object", name, start_line)
                
                grafty_node = Node(
                    id=node_id,
                    kind="json_object",
                    name=name,
                    path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    parent_id=parent_id,
                )
                nodes.append(grafty_node)
                nodes_dict[id(node)] = grafty_node
                
                for child in node.children:
                    self._walk_tree(child, file_path, content, nodes, nodes_dict,
                                   grafty_node.id, inside_pair_value=False)
            return

        if node.type == "array":
            if inside_pair_value:
                # Array is value of a pair - skip creating node, just recurse
                for child in node.children:
                    self._walk_tree(child, file_path, content, nodes, nodes_dict,
                                   parent_id, inside_pair_value=False)
            else:
                # Standalone array - create node
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                name = f"array[{start_line}]"
                node_id = Node.compute_id(file_path, "json_array", name, start_line)
                
                grafty_node = Node(
                    id=node_id,
                    kind="json_array",
                    name=name,
                    path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    parent_id=parent_id,
                )
                nodes.append(grafty_node)
                nodes_dict[id(node)] = grafty_node
                
                for child in node.children:
                    self._walk_tree(child, file_path, content, nodes, nodes_dict,
                                   grafty_node.id, inside_pair_value=False)
            return

        if node.type == "pair":
            # Key-value pair - this is the main structural unit
            key_node = node.children[0] if node.children else None
            name = "unknown"
            if key_node and key_node.type == "string":
                name = key_node.text.decode("utf-8").strip('"')
            
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            node_id = Node.compute_id(file_path, "json_member", name, start_line)
            
            grafty_node = Node(
                id=node_id,
                kind="json_member",
                name=name,
                path=file_path,
                start_line=start_line,
                end_line=end_line,
                start_byte=node.start_byte,
                end_byte=node.end_byte,
                parent_id=parent_id,
            )
            nodes.append(grafty_node)
            nodes_dict[id(node)] = grafty_node
            
            # Process the value (third child: key, colon, value) with inside_pair_value=True
            # This tells object/array children to skip creating redundant nodes
            if len(node.children) > 2:
                value_node = node.children[2]
                self._walk_tree(value_node, file_path, content, nodes, nodes_dict,
                               grafty_node.id, inside_pair_value=True)
            return

        # For other node types (string, number, etc.), just recurse
        for child in node.children:
            self._walk_tree(child, file_path, content, nodes, nodes_dict,
                           parent_id, inside_pair_value)
