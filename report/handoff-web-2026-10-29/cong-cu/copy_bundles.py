"""Copy the two frozen development bundles into a worktree, file by file, per doc/du-lieu-phat-trien-va-fixture.md:
verify SHA-256 at the source, refuse links and path escapes, shutil.copyfile, verify SHA-256 at the target, stop on a
target file that already exists with a different hash. Usage: python copy_bundles.py <worktree>"""
import hashlib, json, os, shutil, sys
from pathlib import Path

REPO = Path(r"C:/Users/ngoco/Desktop/Doctoroadmap")
MANIFESTS = [REPO / "report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json",
             REPO / "report/w06-fixtures-evidence-2026-10-20/development-fixtures.json"]
target_root = Path(sys.argv[1]).resolve()
assert target_root.parent == (REPO / "tmp").resolve(), "target must be a worktree one level under tmp/"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_link(path, stop):
    for part in [path, *path.parents]:
        if part == stop.parent:
            break
        if part.is_symlink() or (part.exists() and os.path.isjunction(part)):
            return True
    return False


copied = same = 0
for manifest_path in MANIFESTS:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_root = Path(manifest["snapshot"]).resolve()
    for row in manifest["files"]:
        source = (source_root / row["path"]).resolve(); target = (target_root / row["path"]).resolve()
        if source_root not in source.parents or target_root not in target.parents:
            raise SystemExit(f"path escapes root: {row['path']}")
        if has_link(source, source_root) or has_link(target, target_root):
            raise SystemExit(f"link on path: {row['path']}")
        if sha(source) != row["sha256"]:
            raise SystemExit(f"source hash differs: {row['path']}")
        if target.exists():
            if sha(target) != row["sha256"]:
                raise SystemExit(f"target exists with a different hash, stop: {row['path']}")
            same += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha(target) != row["sha256"]:
            raise SystemExit(f"target hash differs after copy: {row['path']}")
        copied += 1
print(f"bundles ok: copied {copied}, already identical {same}")
