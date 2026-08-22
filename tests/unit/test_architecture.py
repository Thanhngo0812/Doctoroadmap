import ast
from pathlib import Path


_DOMAIN_STDLIB = {
    "__future__",
    "collections",
    "dataclasses",
    "hashlib",
    "json",
    "re",
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


def test_domain_does_not_import_project_or_external_packages() -> None:
    for path in Path("src/doc2roadmap/domain").rglob("*.py"):
        for module, level in _imports(path):
            if level == 0:
                assert module.split(".", 1)[0] in _DOMAIN_STDLIB, f"{path}: {module}"


def test_application_does_not_import_infrastructure() -> None:
    for path in Path("src/doc2roadmap/application").rglob("*.py"):
        assert not any(
            level == 0 and module.startswith("doc2roadmap.infrastructure")
            for module, level in _imports(path)
        ), path
