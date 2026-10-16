import ast
from pathlib import Path


_DOMAIN_STDLIB = {
    "__future__",
    "collections",
    "dataclasses",
    "hashlib",
    "heapq",
    "json",
    "itertools",
    "math",
    "re",
    "statistics",
    "typing",
    "unicodedata",
}


def _imports(path: Path) -> list[tuple[str, int]]:
    imports = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imports.extend((name.name, 0) for name in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append((node.module or "", node.level))
    return imports


def test_domain_only_uses_stdlib_and_specified_graph_dependency() -> None:
    for path in Path("src/doc2roadmap/domain").rglob("*.py"):
        for module, level in _imports(path):
            if level == 0:
                allowed = _DOMAIN_STDLIB | ({"networkx"} if path.name in {"nomination.py", "secondary_features.py"} else set())
                assert module.split(".", 1)[0] in allowed, f"{path}: {module}"


def test_application_does_not_import_infrastructure() -> None:
    for path in Path("src/doc2roadmap/application").rglob("*.py"):
        assert not any(
            level == 0 and module.startswith("doc2roadmap.infrastructure")
            for module, level in _imports(path)
        ), path
