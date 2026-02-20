"""
Parsers for different file types.
"""
from .python_ts import PythonParser
from .markdown_ts import MarkdownParser
from .org import OrgParser
from .clojure_ts import ClojureParser
from .javascript_ts import JavaScriptParser
from .go_ts import GoParser
from .rust_ts import RustParser
from .html_parser import HTMLParser
from .css_parser import CSSParser
from .json_parser import JsonParser
from .bash_ts import BashParser
from .java_ts import JavaParser
from .typescript_ts import TypeScriptParser

__all__ = [
    "PythonParser",
    "MarkdownParser",
    "OrgParser",
    "ClojureParser",
    "JavaScriptParser",
    "GoParser",
    "RustParser",
    "HTMLParser",
    "CSSParser",
    "JsonParser",
    "BashParser",
    "JavaParser",
    "TypeScriptParser",
]

# File extension to parser mapping
PARSER_REGISTRY = {
    ".html": HTMLParser,
    ".htm": HTMLParser,
    ".css": CSSParser,
    ".py": PythonParser,
    ".md": MarkdownParser,
    ".org": OrgParser,
    ".clj": ClojureParser,
    ".cljs": ClojureParser,
    ".js": JavaScriptParser,
    ".jsx": JavaScriptParser,
    ".ts": TypeScriptParser,
    ".tsx": TypeScriptParser,
    ".go": GoParser,
    ".rs": RustParser,
    ".json": JsonParser,
    ".sh": BashParser,
    ".bash": BashParser,
    ".java": JavaParser,
}


def get_parser_for_file(file_path: str):
    """Get the appropriate parser for a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Parser class appropriate for the file type, or None if no parser found
    """
    import pathlib
    ext = pathlib.Path(file_path).suffix.lower()
    return PARSER_REGISTRY.get(ext)
