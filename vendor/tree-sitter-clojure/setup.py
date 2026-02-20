from setuptools import setup, Extension

setup(
    name="tree-sitter-clojure",
    version="0.0.1",
    packages=["tree_sitter_clojure"],
    ext_modules=[
        Extension(
            "tree_sitter_clojure._binding",
            sources=[
                "tree_sitter_clojure/binding.c",
                "tree_sitter_clojure/parser.c",
            ],
            include_dirs=["tree_sitter_clojure"],
        )
    ],
)
