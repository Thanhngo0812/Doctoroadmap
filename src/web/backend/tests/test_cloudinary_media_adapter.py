from datetime import datetime, timedelta, timezone
import os
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import cloudinary
import cloudinary.api

from wayfinder.infrastructure.media import CloudinaryMediaStore


class RecordingUploader:
    def __init__(self):
        self.calls = []

    def upload(self, path, **options):
        self.calls.append(("upload", path, options))
        return {"public_id": f"{options['folder']}/{options['public_id']}"}

    def explicit(self, public_id, **options):
        self.calls.append(("explicit", public_id, options))
        return {"eager": []}

    def destroy(self, public_id, **options):
        self.calls.append(("destroy", public_id, options))
        return {"result": "ok"}


def test_upload_explicit_and_delete_use_authenticated_asset_options(tmp_path):
    uploader = RecordingUploader()
    store = CloudinaryMediaStore.__new__(CloudinaryMediaStore)
    store._cloudinary = SimpleNamespace(uploader=uploader)
    source = tmp_path / "original.docx"
    source.write_bytes(b"test")
    image_source = tmp_path / "photo.png"
    image_source.write_bytes(b"image fixture")

    public_id = store.upload(source, "wayfinder/test/uploads", "raw")
    image_id = store.upload(image_source, "wayfinder/test/media", "image")
    store._generate_derived("wayfinder/test/uploads/source.pdf", "pg_1,w_1400,c_scale,f_webp")
    store.delete(public_id)
    store.delete(image_id)

    uploaded = uploader.calls[0][2]
    assert uploaded["resource_type"] == "raw"
    assert uploaded["type"] == "authenticated"
    assert uploaded["public_id"].endswith(".docx")
    image_upload = uploader.calls[1][2]
    assert image_upload["resource_type"] == "image"
    assert image_upload["type"] == "authenticated"
    eager = uploader.calls[2][2]
    assert eager["type"] == "authenticated"
    assert eager["eager"] == ["pg_1,w_1400,c_scale,f_webp"]
    deleted = uploader.calls[3][2]
    assert deleted["resource_type"] == "raw"
    assert deleted["type"] == "authenticated"
    deleted_image = uploader.calls[4][2]
    assert deleted_image["resource_type"] == "image"
    assert deleted_image["type"] == "authenticated"


def test_temporary_download_uses_cloudinary_format_and_absolute_expiry():
    api_calls = []
    url_calls = []

    def resource(public_id, **options):
        api_calls.append((public_id, options))
        # Raw resource responses may omit format; raw public IDs retain .docx.
        return {} if options["resource_type"] == "raw" else {"format": "png"}

    def private_download_url(public_id, asset_format, **options):
        url_calls.append((public_id, asset_format, options))
        return "private-download-url"

    sdk = SimpleNamespace(
        api=SimpleNamespace(resource=resource),
        utils=SimpleNamespace(private_download_url=private_download_url),
    )
    stores = [CloudinaryMediaStore.__new__(CloudinaryMediaStore) for _ in range(2)]
    for store in stores:
        store._cloudinary = sdk
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    assert stores[0].temporary_download_url("uploads/photo.png", expires_at) == "private-download-url"
    assert stores[1].temporary_download_url("uploads/source.docx", expires_at) == "private-download-url"
    assert [call[1]["resource_type"] for call in api_calls] == ["image"]
    assert [call[1]["type"] for call in api_calls] == ["authenticated"]
    assert [call[1] for call in url_calls] == ["png", "docx"]
    for _, _, options in url_calls:
        assert options["type"] == "authenticated"
        assert options["attachment"] is True
        assert options["expires_at"] == int(expires_at.timestamp())


def test_signed_authenticated_image_url_uses_raw_transformation_path():
    original_config = cloudinary.config().__dict__.copy()
    try:
        cloudinary.config(
            cloud_name="dummy-cloud",
            api_key="dummy-key",
            api_secret="dummy-secret",
            secure=True,
        )
        store = CloudinaryMediaStore.__new__(CloudinaryMediaStore)
        store._cloudinary = cloudinary
        url = store._signed_image_url(
            "wayfinder/test/uploads/source", "pg_1,w_1400,c_scale,f_webp"
        )
    finally:
        _restore_config(original_config)

    assert "/image/authenticated/s--" in url
    assert "/pg_1,w_1400,c_scale,f_webp/" in url
    assert "/t_pg_1" not in url


def test_sdk_private_download_urls_use_metadata_format_and_absolute_expiry(monkeypatch):
    original_config = cloudinary.config().__dict__.copy()
    old_resource = cloudinary.api.resource
    api_calls = []

    def resource(public_id, **options):
        api_calls.append((public_id, options))
        return {} if options["resource_type"] == "raw" else {"format": "png"}

    try:
        cloudinary.config(
            cloud_name="dummy-cloud",
            api_key="dummy-key",
            api_secret="dummy-secret",
            secure=True,
        )
        monkeypatch.setattr(cloudinary.api, "resource", resource)
        store = CloudinaryMediaStore.__new__(CloudinaryMediaStore)
        store._cloudinary = cloudinary
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        image_url = store.temporary_download_url("uploads/photo.png", expires_at)
        raw_url = store.temporary_download_url("uploads/source.docx", expires_at)
    finally:
        monkeypatch.setattr(cloudinary.api, "resource", old_resource)
        _restore_config(original_config)

    image = urlparse(image_url)
    raw = urlparse(raw_url)
    assert image.path.endswith("/image/download")
    assert parse_qs(image.query)["format"] == ["png"]
    assert parse_qs(image.query)["type"] == ["authenticated"]
    assert parse_qs(image.query)["expires_at"] == [str(int(expires_at.timestamp()))]
    assert raw.path.endswith("/raw/download")
    assert parse_qs(raw.query)["format"] == ["docx"]
    assert parse_qs(raw.query)["type"] == ["authenticated"]
    assert [call[1]["resource_type"] for call in api_calls] == ["image"]


def test_constructor_reloads_current_cloudinary_url_and_restores_global_config(monkeypatch):
    original_config = cloudinary.config().__dict__.copy()
    for name in tuple(os.environ):
        if name.startswith("CLOUDINARY_") and name != "CLOUDINARY_URL":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(
        "CLOUDINARY_URL", "cloudinary://fresh-key:fresh-secret@fresh-cloud"
    )
    try:
        CloudinaryMediaStore()
        config = cloudinary.config()
        assert config.cloud_name == "fresh-cloud"
        assert config.api_key == "fresh-key"
        assert config.api_secret == "fresh-secret"
        assert config.timeout == 30
    finally:
        _restore_config(original_config)


def _restore_config(snapshot):
    cloudinary.reset_config()
    cloudinary.config().update(**snapshot)
