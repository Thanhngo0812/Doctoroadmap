"""Copy only manifest-listed development inputs; never link or import a learner store."""
import hashlib
import json
import shutil
import stat
import sys
from pathlib import Path, PurePosixPath


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(base, relative):
    part = PurePosixPath(relative)
    if part.is_absolute() or ".." in part.parts or ":" in relative or "\\" in relative:
        raise ValueError("manifest path escapes root")
    path = base.joinpath(*part.parts)
    for ancestor in (path, *path.parents):
        try:
            metadata = ancestor.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f"linked path: {ancestor}")
        if stat.S_ISREG(metadata.st_mode) and metadata.st_nlink != 1:
            raise ValueError(f"hardlinked file: {ancestor}")
    return path


def main():
    root = Path(__file__).absolute().parents[4]
    sys.path.insert(0, str(root / "src/web/backend"))
    shared = root.parents[1]
    bundles = json.loads((root / "report/w06-fixtures-evidence-2026-10-20/bundles.json").read_text(encoding="utf-8"))
    planned = []
    from wayfinder.application.seed_samples import SAMPLE_DOCS
    for bundle in bundles["bundles"]:
        manifest_path = safe_path(root, bundle["manifest"])
        if digest(manifest_path) != bundle["manifest_sha256"]:
            raise ValueError("bundle manifest hash mismatch")
        source = safe_path(shared, bundle["snapshot"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            relative = entry["path"]
            parts = PurePosixPath(relative).parts
            # Never import a learner store, even the separate CLI rebuild store.
            if relative.startswith("artifacts/phase_b/") and not relative.startswith("artifacts/phase_b/formula_images/"):
                continue
            if not (relative in {spec["pdf"] for spec in SAMPLE_DOCS.values()}
                    or parts[0] == "artifacts" and set(SAMPLE_DOCS).intersection(parts)):
                raise ValueError(f"input is outside development allowlist: {relative}")
            original, target = safe_path(source, relative), safe_path(root, relative)
            if not original.is_file() or digest(original) != entry["sha256"]:
                raise ValueError(f"source hash mismatch: {relative}")
            if target.exists() and digest(target) != entry["sha256"]:
                raise ValueError(f"destination conflict: {relative}")
            planned.append((entry, original, target))
    for entry, original, target in planned:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            safe_path(root, entry["path"])
            shutil.copyfile(original, target)
        safe_path(root, entry["path"])
        if digest(target) != entry["sha256"]:
            raise ValueError(f"destination hash mismatch: {entry['path']}")
    evidence = root / "report/w06-evidence"
    evidence.mkdir(exist_ok=True)
    result = {"bundles": bundles["bundles"], "verified_files": len(planned), "links_used": False,
        "learner_stores_copied": False, "files": [{"path": row["path"], "sha256": row["sha256"]} for row, _, _ in planned]}
    (evidence / "fixture-copy.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "files"}, indent=2))


if __name__ == "__main__":
    main()
