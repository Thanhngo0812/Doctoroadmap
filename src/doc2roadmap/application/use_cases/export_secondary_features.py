"""Export pre-secondary features; never read labels or call a model."""
import csv
from pathlib import Path

from doc2roadmap.domain.secondary_features import FEATURE_NAMES, feature_rows


class ExportSecondaryFeatures:
    def __init__(self, store, tokenize):
        self.store, self.tokenize = store, tokenize

    def execute(self, doc_id, *, main_version, output_dir, chunks_store=None):
        main = self.store.load_graph(doc_id, main_version)
        if main.payload.get("stage") != "edges" or not main.payload.get("main_complete"):
            raise ValueError("xuất đặc trưng cần artifact pass chính hoàn chỉnh")
        if main.payload.get("secondary_complete"):
            raise ValueError("cần phiên bản pass chính, không dùng artifact pass phụ")
        config = main.manifest["config"]
        chunks = (chunks_store or self.store).load_chunks(doc_id, config["chunks_version"]).result.chunks
        output = Path(output_dir) / f"{doc_id}.csv"
        output.parent.mkdir(parents=True, exist_ok=True)
        fields = ("pair_id", "thu_tu_cap", "x", "y", "ten_x", "ten_y", "ung_vien", *FEATURE_NAMES)
        count, candidates = 0, 0
        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in feature_rows(main.payload, chunks, self.tokenize,
                                    before=config.get("definition_before", 0),
                                    after=config.get("definition_after", 2)):
                writer.writerow(row)
                count += 1
                candidates += row["ung_vien"]
        return {"doc_id": doc_id, "main_version": main.version, "path": str(output),
                "rows": count, "candidates": candidates, "feature_count": len(FEATURE_NAMES),
                "calls": 0, "usd": 0.0}
