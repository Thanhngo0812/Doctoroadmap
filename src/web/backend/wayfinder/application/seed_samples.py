from pathlib import Path

from wayfinder.api.errors import WebError


SAMPLE_DOCS = {
    "doc-1": {"pdf": "doc-1.pdf", "title": "Đại số tuyến tính"},
    "nhap-mon-ml": {"pdf": "nhap-mon-ml.pdf", "title": "Nhập môn học máy"},
    "naive-bayes": {"pdf": "5_Naive Bayes Classifier.pdf", "title": "Naive Bayes"},
    "doc-6": {"pdf": "doc-6.pdf", "title": "Khoá mẫu doc-6"},
    "xstk-ch3-1": {"pdf": "xstk-ch3-1.pdf", "title": "Xác suất thống kê — chương 3"},
    "doc-4": {"pdf": "doc-4.pdf", "title": "Khoá mẫu doc-4"},
}


class SampleSeeder:
    def __init__(self, courses, gateway, media, *, source_root: Path, folder: str):
        self.courses, self.gateway, self.media = courses, gateway, media
        self.source_root, self.folder = Path(source_root), folder

    def execute(self, actor, doc_ids=None):
        self.courses.authorize(actor, "seed_samples")
        requested = list(dict.fromkeys(SAMPLE_DOCS if doc_ids is None else doc_ids))
        if self.courses.settings.env != "dev" or not requested or any(doc not in SAMPLE_DOCS for doc in requested):
            raise WebError("not_found", "Chỉ tạo khoá mẫu phát triển trong môi trường dev")
        results = []
        # Validate every source before the first upload/write.
        plans = []
        for doc_id in requested:
            existing = self.courses.store.find_sample(doc_id)
            if existing is not None:
                plans.append((doc_id, existing, None, None))
                continue
            path = self.source_root / SAMPLE_DOCS[doc_id]["pdf"]
            if not path.is_file():
                raise WebError("file_invalid", "Thiếu PDF phát triển của khoá mẫu")
            plans.append((doc_id, None, path, self.gateway.sample_blueprint(actor, doc_id)))
        for doc_id, existing, path, blueprint in plans:
            if existing is not None:
                results.append(existing)
                continue
            public_id = self.media.upload(path, self.folder, "image")
            try:
                result = self.courses.create_course(actor, doc_id=doc_id, title=SAMPLE_DOCS[doc_id]["title"],
                    description="Khoá mẫu phát triển", is_sample=True, source_public_id=public_id, **blueprint)
            except Exception:
                self.media.delete(public_id)
                raise
            results.append(result)
        return results
