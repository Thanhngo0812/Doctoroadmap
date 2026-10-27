"""Kho artifact chỉ đọc cho bộ phát lại: đọc từ thư mục kho, artifact mới (A9, đặt tên, A10) chỉ nằm trong bộ nhớ.

Không ghi tệp, không ghi checkpoint, không dùng cache (`find_graph` luôn trống), nên phát lại không bao giờ trùng một artifact đã lưu
mà không chạy lại mã.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from doc2roadmap.domain.canonical import digest
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore

SO_BAT_DAU = 10_000


class KhoPhatLai(JsonArtifactStore):
    def __init__(self, goc):
        super().__init__(Path(goc))
        self.phien_ban, self.da_luu = SO_BAT_DAU, {}

    def find_graph(self, *args):
        return None

    def load_checkpoint(self, *args):
        return None

    def save_checkpoint(self, *args):
        pass

    def clear_checkpoint(self, *args):
        pass

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        self.phien_ban += 1
        artifact = SimpleNamespace(payload=payload, version=self.phien_ban, path=None, manifest={
            "config": config, "config_hash": config_hash, "source_hash": source_hash,
            "upstream_version": kwargs.get("upstream_version"), **kwargs.get("manifest_fields", {})})
        self.da_luu[self.phien_ban] = artifact
        return artifact

    def load_graph(self, doc_id, version):
        return self.da_luu[version] if version in self.da_luu else super().load_graph(doc_id, version)


class MoHinhDaGhi:
    """Trả đúng phản hồi đã ghi theo băm đầu vào; đầu vào chưa ghi thì dừng (không bao giờ gọi mạng)."""

    transport = "da_ghi"

    def __init__(self, model_id, hang):
        self.model_id = model_id
        self.hang = {digest(h["input"]): h for h in hang}

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        du_lieu = json.loads(prompt.split("\nCorrect this validation error:")[0])
        h = self.hang.get(digest(du_lieu))
        if h is None:
            raise AssertionError("đầu vào tên khái niệm chưa ghi: " + str(du_lieu.get("node_id")))
        return SimpleNamespace(payload=h.get("output", h.get("last_output", {})))
