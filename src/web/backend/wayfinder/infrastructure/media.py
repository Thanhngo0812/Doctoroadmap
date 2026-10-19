from __future__ import annotations

import os
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from wayfinder.application.media import MediaStore

_TIMEOUT_SECONDS = 30


class CloudinaryMediaStore:
    def __init__(self) -> None:
        if not os.environ.get("CLOUDINARY_URL"):
            raise RuntimeError("CLOUDINARY_URL is required for Cloudinary media storage")
        import cloudinary
        import cloudinary.api  # noqa: F401
        import cloudinary.uploader  # noqa: F401
        import cloudinary.utils  # noqa: F401

        # Reload the SDK config so a newly set CLOUDINARY_URL is honored.
        cloudinary.reset_config()
        cloudinary.config(secure=True, timeout=_TIMEOUT_SECONDS)
        self._cloudinary = cloudinary

    def upload(self, path: Path, folder: str, resource_type: str) -> str:
        if resource_type not in {"image", "raw"}:
            raise ValueError("resource_type must be 'image' or 'raw'")
        if resource_type == "raw" and Path(path).suffix.lower() != ".docx":
            raise ValueError("raw uploads must be DOCX files")
        result = self._cloudinary.uploader.upload(
            str(path),
            folder=folder,
            public_id=uuid4().hex + (Path(path).suffix if resource_type == "raw" else ""),
            resource_type=resource_type,
            type="authenticated",
        )
        return result["public_id"]

    def download(self, public_id: str) -> Path:
        expires_at = datetime.fromtimestamp(time.time() + 300).astimezone()
        asset_format = self._asset_format(public_id)
        url = self._private_download_url(public_id, expires_at, asset_format)
        suffix = "." + asset_format
        path: Path | None = None
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT_SECONDS) as response:
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as output:
                    path = Path(output.name)
                    while chunk := response.read(64 * 1024):
                        output.write(chunk)
            return path
        except Exception:
            if path is not None:
                path.unlink(missing_ok=True)
            raise

    def fetch_page_image(self, public_id: str, page: int, width: int) -> bytes:
        if page < 1 or width < 1:
            raise ValueError("page and width must be positive")
        transformation = f"pg_{page},w_{width},c_scale,f_webp"
        self._generate_derived(public_id, transformation)
        url = self._signed_image_url(public_id, transformation)
        return _read_url(url)

    def fetch_image(self, public_id: str) -> bytes:
        transformation = "f_webp"
        self._generate_derived(public_id, transformation)
        url = self._signed_image_url(public_id, transformation)
        return _read_url(url)

    def temporary_download_url(self, public_id: str, expires_at: datetime) -> str:
        if expires_at.tzinfo is None or expires_at <= datetime.now().astimezone():
            raise ValueError("expires_at must be a future timezone-aware datetime")
        return self._private_download_url(
            public_id, expires_at, self._asset_format(public_id)
        )

    def _private_download_url(
        self, public_id: str, expires_at: datetime, asset_format: str
    ) -> str:
        resource_type = "raw" if _is_raw(public_id) else "image"
        return self._cloudinary.utils.private_download_url(
            public_id,
            asset_format,
            resource_type=resource_type,
            type="authenticated",
            expires_at=int(expires_at.timestamp()),
            attachment=True,
        )

    def _asset_format(self, public_id: str) -> str:
        if _is_raw(public_id):
            # Raw uploads are restricted to DOCX and Cloudinary's raw Admin
            # response may omit `format`.
            return "docx"
        result = self._cloudinary.api.resource(
            public_id,
            resource_type="image",
            type="authenticated",
        )
        asset_format = result["format"]
        if not asset_format.isalnum():
            raise ValueError("Cloudinary returned an invalid asset format")
        return asset_format

    def delete(self, public_id: str) -> None:
        self._cloudinary.uploader.destroy(
            public_id,
            resource_type="raw" if _is_raw(public_id) else "image",
            type="authenticated",
        )

    def _generate_derived(self, public_id: str, transformation: str) -> None:
        # Authenticated assets need derived versions generated before delivery.
        self._cloudinary.uploader.explicit(
            public_id,
            resource_type="image",
            type="authenticated",
            eager=[transformation],
            eager_async=False,
        )

    def _signed_image_url(self, public_id: str, transformation: str) -> str:
        url, _ = self._cloudinary.utils.cloudinary_url(
            public_id,
            resource_type="image",
            type="authenticated",
            sign_url=True,
            secure=True,
            raw_transformation=transformation,
        )
        return url


def media_smoke(store: MediaStore | None = None) -> None:
    media: MediaStore | None = store
    path: Path | None = None
    public_id: str | None = None
    step = "configuration"
    try:
        media = media or CloudinaryMediaStore()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as sample:
            sample_path = Path(sample.name)
            path = sample_path
        sample_path.write_bytes(_tiny_pdf())
        step = "upload"
        public_id = media.upload(sample_path, "wayfinder/dev/uploads", "image")
        print("upload: ok")
        step = "page image"
        image = media.fetch_page_image(public_id, 1, 1400)
        print(f"page image: ok ({len(image)} bytes)")
        step = "temporary download URL"
        link = media.temporary_download_url(
            public_id, datetime.fromtimestamp(time.time() + 300).astimezone()
        )
        if not link:
            raise RuntimeError("Cloudinary did not return a download URL")
        print("temporary download URL: ok")
        step = "download"
        downloaded = _read_url(link)
        if downloaded != sample_path.read_bytes():
            raise RuntimeError("Cloudinary download did not match the uploaded PDF")
        print(f"download: ok ({len(downloaded)} bytes)")
    except Exception as exc:
        print(f"{step}: failed ({type(exc).__name__})")
        raise RuntimeError(f"media smoke {step} failed ({type(exc).__name__})") from None
    finally:
        try:
            if public_id is not None:
                try:
                    media.delete(public_id)
                    print("delete: ok")
                except Exception as exc:
                    print(f"delete: failed ({type(exc).__name__})")
                    raise RuntimeError(
                        f"media smoke delete failed ({type(exc).__name__})"
                    ) from None
        finally:
            if path is not None:
                path.unlink(missing_ok=True)


def _is_raw(public_id: str) -> bool:
    return public_id.lower().endswith(".docx")


def _read_url(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=_TIMEOUT_SECONDS) as response:
        return response.read()


def _tiny_pdf() -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 20 20] /Contents 4 0 R >>",
        b"<< /Length 0 >>\nstream\n\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(pdf)
