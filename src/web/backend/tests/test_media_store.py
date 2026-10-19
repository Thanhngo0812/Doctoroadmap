from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import struct
from urllib.error import HTTPError
from zipfile import ZIP_DEFLATED, ZipFile
import zlib

import pytest

import wayfinder.infrastructure.media as media_module
from wayfinder.fakes.media import MemoryMediaStore
from wayfinder.infrastructure.media import _tiny_pdf, media_smoke


def _exercise_contract(store, tmp_path):
    source = tmp_path / "source.pdf"
    source.write_bytes(_tiny_pdf())
    public_id = store.upload(source, "wayfinder/test/uploads", "image")
    try:
        downloaded = store.download(public_id)
        try:
            assert downloaded.read_bytes() == source.read_bytes()
        finally:
            downloaded.unlink(missing_ok=True)
        page_image = store.fetch_page_image(public_id, 1, 1400)
        assert page_image[:4] == b"RIFF" and page_image[8:12] == b"WEBP"
        image_bytes = store.fetch_image(public_id)
        assert image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP"
        assert store.temporary_download_url(
            public_id, datetime(2030, 1, 1, tzinfo=timezone.utc)
        )
    finally:
        store.delete(public_id)
    _assert_deleted(store, public_id)

    png = tmp_path / "sample.png"
    png.write_bytes(_tiny_png())
    image_id = store.upload(png, "wayfinder/test/media", "image")
    try:
        image_bytes = store.fetch_image(image_id)
        assert image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP"
        image_download = store.download(image_id)
        try:
            assert image_download.suffix == ".png"
            assert image_download.read_bytes() == png.read_bytes()
        finally:
            image_download.unlink(missing_ok=True)
        image_url = store.temporary_download_url(
            image_id, datetime(2030, 1, 1, tzinfo=timezone.utc)
        )
        assert "format=png" in image_url
    finally:
        store.delete(image_id)
    _assert_deleted(store, image_id)

    docx = tmp_path / "source.docx"
    docx_bytes = BytesIO()
    with ZipFile(docx_bytes, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>',
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>',
        )
        archive.writestr(
            "word/document.xml",
            '<?xml version="1.0"?><document xmlns="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>',
        )
    docx.write_bytes(docx_bytes.getvalue())
    raw_id = store.upload(docx, "wayfinder/test/uploads", "raw")
    try:
        assert raw_id.endswith(".docx")
        raw_download = store.download(raw_id)
        try:
            assert raw_download.read_bytes() == docx.read_bytes()
        finally:
            raw_download.unlink(missing_ok=True)
        assert store.temporary_download_url(
            raw_id, datetime(2030, 1, 1, tzinfo=timezone.utc)
        )
    finally:
        store.delete(raw_id)
    _assert_deleted(store, raw_id)


def _assert_deleted(store, public_id):
    try:
        store.download(public_id)
    except Exception as exc:
        if isinstance(store, MemoryMediaStore):
            assert isinstance(exc, KeyError)
        else:
            from cloudinary.exceptions import NotFound

            assert isinstance(exc, NotFound) or isinstance(exc, HTTPError) and exc.code == 404
    else:
        pytest.fail("deleted media remained downloadable")


def test_fake_satisfies_shared_media_contract(tmp_path):
    store = MemoryMediaStore()
    _exercise_contract(store, tmp_path)
    assert store.fetch_count == 9


def test_fake_rejects_expired_temporary_url(tmp_path):
    store = MemoryMediaStore()
    source = tmp_path / "source.png"
    source.write_bytes(b"png")
    public_id = store.upload(source, "wayfinder/test/media", "image")

    with pytest.raises(ValueError, match="future timezone-aware"):
        store.temporary_download_url(
            public_id, datetime(2020, 1, 1, tzinfo=timezone.utc)
        )


def test_cloudinary_satisfies_shared_media_contract_when_explicitly_enabled(tmp_path):
    import os

    if not os.environ.get("CLOUDINARY_URL") or os.environ.get(
        "WAYFINDER_RUN_CLOUDINARY_TESTS"
    ) != "1":
        pytest.skip(
            "set CLOUDINARY_URL and WAYFINDER_RUN_CLOUDINARY_TESTS=1 for live Cloudinary tests"
        )
    from wayfinder.infrastructure.media import CloudinaryMediaStore

    _exercise_contract(CloudinaryMediaStore(), tmp_path)


def test_smoke_cleans_local_and_remote_files_when_page_fetch_fails(
    tmp_path, monkeypatch, capsys
):
    import tempfile

    class BrokenStore(MemoryMediaStore):
        def fetch_page_image(self, public_id, page, width):
            raise RuntimeError("fetch failed")

    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    store = BrokenStore()
    with pytest.raises(RuntimeError, match=r"page image failed \(RuntimeError\)"):
        media_smoke(store)

    assert store.files == {}
    assert list(tmp_path.iterdir()) == []
    assert "page image: failed (RuntimeError)" in capsys.readouterr().out


def test_smoke_downloads_signed_url_without_printing_it_and_cleans_on_mismatch(
    tmp_path, monkeypatch, capsys
):
    import tempfile

    class PrivateUrlStore(MemoryMediaStore):
        def temporary_download_url(self, public_id, expires_at):
            return "https://private.example/download?api_key=secret"

    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(media_module, "_read_url", lambda url: b"incorrect bytes")
    store = PrivateUrlStore()

    with pytest.raises(RuntimeError, match=r"download failed \(RuntimeError\)"):
        media_module.media_smoke(store)

    assert store.files == {}
    assert list(tmp_path.iterdir()) == []
    assert "secret" not in capsys.readouterr().out


def _tiny_png():
    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    pixel = zlib.compress(b"\x00\x00\x00\x00")
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", pixel) + chunk(b"IEND", b"")
