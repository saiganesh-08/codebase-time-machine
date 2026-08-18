"""
Parses Python source files with the `ast` module to build a function-level
dependency graph: which functions call which. This is real static analysis,
not LLM guessing -- the LLM layer only explains what this graph finds.
"""
import ast
import os
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FunctionInfo:
    qualified_name: str
    name: str
    file_path: str
    start_line: int
    end_line: int
    docstring: str = ""
    calls: List[str] = field(default_factory=list)  # unqualified callee names


def _module_name(file_path: str, repo_root: str) -> str:
    rel = os.path.relpath(file_path, repo_root)
    rel = rel[:-3] if rel.endswith(".py") else rel
    return rel.replace(os.sep, ".")


class _CallCollector(ast.NodeVisitor):
    """Collects the names of functions called within a function body."""

    def __init__(self):
        self.called_names: List[str] = []

    def visit_Call(self, node: ast.Call):
        target = node.func
        if isinstance(target, ast.Name):
            self.called_names.append(target.id)
        elif isinstance(target, ast.Attribute):
            self.called_names.append(target.attr)
        self.generic_visit(node)


def analyze_file(file_path: str, repo_root: str) -> List[FunctionInfo]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        return []

    module = _module_name(file_path, repo_root)
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            collector = _CallCollector()
            collector.visit(node)
            functions.append(FunctionInfo(
                qualified_name=f"{module}.{node.name}",
                name=node.name,
                file_path=os.path.relpath(file_path, repo_root),
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                docstring=ast.get_docstring(node) or "",
                calls=list(set(collector.called_names)),
            ))

    return functions


def build_dependency_graph(repo_root: str) -> Dict[str, FunctionInfo]:
    """
    Walk the repo, parse every .py file, and resolve unqualified call
    names to qualified names where possible. Returns qualified_name -> FunctionInfo.
    """
    all_functions: Dict[str, FunctionInfo] = {}
    name_to_qualified: Dict[str, List[str]] = {}

    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in (
            ".git", "node_modules", "venv", ".venv", "__pycache__"
        )]
        for filename in filenames:
            if filename.endswith(".py"):
                file_path = os.path.join(dirpath, filename)
                for fn in analyze_file(file_path, repo_root):
                    all_functions[fn.qualified_name] = fn
                    name_to_qualified.setdefault(fn.name, []).append(fn.qualified_name)

    # Resolve calls: unqualified name -> best-guess qualified name(s)
    resolved_edges: Dict[str, List[str]] = {}
    for qname, fn in all_functions.items():
        resolved = []
        for called in fn.calls:
            candidates = name_to_qualified.get(called, [])
            resolved.extend(c for c in candidates if c != qname)
        resolved_edges[qname] = list(set(resolved))

    for qname, fn in all_functions.items():
        fn.calls = resolved_edges.get(qname, [])

    return all_functions


def build_called_by(functions: Dict[str, FunctionInfo]) -> Dict[str, List[str]]:
    called_by: Dict[str, List[str]] = {q: [] for q in functions}
    for qname, fn in functions.items():
        for callee in fn.calls:
            if callee in called_by:
                called_by[callee].append(qname)
    return called_by
