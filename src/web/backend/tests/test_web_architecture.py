import ast
from pathlib import Path


BACKEND = Path(__file__).parents[1] / "wayfinder"
FORBIDDEN_FRAMEWORKS = {"fastapi", "sqlalchemy", "alembic", "cloudinary", "argon2"}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".", 1)[0])
    return modules


def _violations(root: Path, forbidden: set[str]) -> set[Path]:
    return {path for path in root.rglob("*.py") if _imports(path) & forbidden}


def test_domain_and_application_do_not_import_infrastructure_frameworks() -> None:
    for layer in ("domain", "application"):
        assert not _violations(BACKEND / layer, FORBIDDEN_FRAMEWORKS)


def test_core_does_not_import_web_package() -> None:
    root = Path(__file__).parents[4] / "src" / "doc2roadmap"
    assert not _violations(root, {"wayfinder"})


def test_import_boundary_guards_detect_mutations_in_isolated_tree(tmp_path) -> None:
    application = tmp_path / "wayfinder" / "application"
    core = tmp_path / "doc2roadmap"
    application.mkdir(parents=True)
    core.mkdir()
    (application / "mutant.py").write_text("import fastapi as api\nfrom sqlalchemy.orm import Session\n", encoding="utf-8")
    (core / "mutant.py").write_text("import wayfinder.api\n", encoding="utf-8")

    assert _violations(application, FORBIDDEN_FRAMEWORKS) == {application / "mutant.py"}
    assert _violations(core, {"wayfinder"}) == {core / "mutant.py"}


def test_openapi_snapshot_matches_application() -> None:
    import json

    from wayfinder.api.app import create_app
    from wayfinder.composition import WebServices
    from wayfinder.settings import WebSettings

    app = create_app(WebSettings(_env_file=None, frontend_dist="C:/missing-wayfinder-dist"),
                     WebServices(health_check=lambda: "ok"))
    snapshot = Path(__file__).parents[2] / "openapi.json"

    _assert_snapshot(app, snapshot)


def test_openapi_snapshot_guard_rejects_an_added_route() -> None:
    import pytest

    from wayfinder.api.app import create_app
    from wayfinder.composition import WebServices
    from wayfinder.settings import WebSettings

    app = create_app(WebSettings(_env_file=None, frontend_dist="C:/missing-wayfinder-dist"),
                     WebServices(health_check=lambda: "ok"))

    @app.get("/api/v1/mutation-probe")
    def mutation_probe():
        return {"status": "probe"}

    snapshot = Path(__file__).parents[2] / "openapi.json"
    with pytest.raises(AssertionError):
        _assert_snapshot(app, snapshot)


def _assert_snapshot(app, snapshot: Path) -> None:
    import json

    assert json.loads(snapshot.read_text(encoding="utf-8")) == app.openapi()
