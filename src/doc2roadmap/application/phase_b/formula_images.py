from __future__ import annotations

import hashlib
import json
from pathlib import Path

from doc2roadmap.application.use_cases.ingest_document import validate_doc_id


def formula_occurrence_key(node) -> str:
    return f"{node.formula_id}@p{node.page}:r{node.reading_order}"


class CutFormulaImages:
    """Create stable per-occurrence formula references through an injected PDF renderer."""

    def __init__(self, renderer, *, scale: float = 2.0) -> None:
        if scale <= 0:
            raise ValueError("scale phải lớn hơn 0")
        self.renderer = renderer
        self.scale = scale

    def execute(self, pdf_path, tree, *, output_dir=None):
        formulas = [node for node in tree.nodes if node.node_type == "formula"]
        rendered = {}
        batch = getattr(self.renderer, "render_formula_batch", None)
        if batch:
            valid = [(index, node) for index, node in enumerate(formulas)
                     if node.formula_id and node.page is not None and node.bbox is not None
                     and len(node.bbox) == 4]
            images_batch = batch(
                pdf_path,
                [(node.page, node.bbox, node.bbox_origin) for _, node in valid],
                scale=self.scale,
            )
            rendered = {index: image for (index, _), image in zip(valid, images_batch, strict=True)}
        counts = {}
        for index, node in enumerate(formulas):
            if node.formula_id:
                counts[node.formula_id] = counts.get(node.formula_id, 0) + 1
        refs, images = [], {}
        for index, node in enumerate(formulas):
            row = {
                "occurrence_id": formula_occurrence_key(node),
                "formula_id": node.formula_id,
                "page": node.page,
                "bbox": list(node.bbox) if node.bbox is not None else None,
                "raw_text": node.raw_text,
                "raw_text_available": bool(node.raw_text),
            }
            if not node.formula_id:
                row["status"] = "missing_formula_id"
            elif node.page is None or node.bbox is None or len(node.bbox) != 4:
                row["status"] = "missing_bbox"
            else:
                image = rendered.get(index) if batch else self.renderer.render_formula(
                    pdf_path, node.page, node.bbox, scale=self.scale, origin=node.bbox_origin)
                if image is None:
                    row["status"] = "invalid_bbox"
                else:
                    media_id = hashlib.sha256(image).hexdigest()
                    images.setdefault(media_id, image)
                    row.update(status="cut", media_id=media_id)
            if counts.get(node.formula_id, 0) > 1:
                row["duplicate_formula_id"] = True
            refs.append(row)
        result = {
            "schema_version": 1,
            "scale": self.scale,
            "coordinate_order": "left,top,right,bottom; PDF bottom-left origin",
            "formula_refs": refs,
            "images": images,
            "cut_count": sum(row["status"] == "cut" for row in refs),
            "skipped_count": sum(row["status"] != "cut" for row in refs),
        }
        if output_dir is not None:
            output_dir = Path(output_dir)
            image_dir = output_dir / "images"
            image_dir.mkdir(parents=True, exist_ok=True)
            for media_id, image in images.items():
                target = image_dir / f"{media_id}.png"
                if not target.exists():
                    target.write_bytes(image)
            index_path = output_dir / "formula_images.json"
            index_path.write_text(json.dumps(
                {key: value for key, value in result.items() if key != "images"},
                ensure_ascii=False, indent=2,
            ) + "\n", encoding="utf-8")
            result["index_path"] = str(index_path)
            result["image_dir"] = str(image_dir)
        return result


def persist_formula_images(result, root, doc_id: str, parse_version: int) -> dict:
    """Persist isolated formula crops and occurrence references under a parse version."""
    validate_doc_id(doc_id)
    if parse_version < 1:
        raise ValueError("parse_version phải lớn hơn 0")
    root = Path(root)
    output_dir = root / "phase_b" / "formula_images" / doc_id / f"parse-v{parse_version}"
    output_dir.mkdir(parents=True, exist_ok=True)
    image_dir = output_dir / "images"
    image_dir.mkdir(exist_ok=True)
    refs = []
    for row in result.get("formula_refs", []):
        ref = dict(row)
        media_id = ref.get("media_id")
        image = result.get("images", {}).get(media_id) if media_id else None
        if ref.get("status") == "cut" and image is not None:
            target = image_dir / f"{media_id}.png"
            if not target.exists():
                target.write_bytes(image)
            ref["image_ref"] = f"images/{media_id}.png"
        refs.append(ref)
    index = {
        "schema_version": 1,
        "doc_id": doc_id,
        "parse_version": parse_version,
        "scale": result.get("scale"),
        "coordinate_order": result.get("coordinate_order"),
        "formula_refs": refs,
        "cut_count": result.get("cut_count", 0),
        "skipped_count": result.get("skipped_count", 0),
    }
    index_path = output_dir / "index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {**index, "index_path": str(index_path), "image_dir": str(image_dir)}
