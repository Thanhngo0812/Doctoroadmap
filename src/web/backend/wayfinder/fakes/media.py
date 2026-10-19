from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4


class MemoryMediaStore:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.resource_types: dict[str, str] = {}
        self.formats: dict[str, str] = {}
        self.fetch_count = 0

    def upload(self, path: Path, folder: str, resource_type: str) -> str:
        if resource_type not in {"image", "raw"}:
            raise ValueError("resource_type must be 'image' or 'raw'")
        if resource_type == "raw" and path.suffix.lower() != ".docx":
            raise ValueError("raw uploads must be DOCX files")
        public_id = f"{folder.rstrip('/')}/{uuid4().hex}"
        if resource_type == "raw":
            public_id += path.suffix
        self.files[public_id] = Path(path).read_bytes()
        self.resource_types[public_id] = resource_type
        self.formats[public_id] = path.suffix.lstrip(".").lower() or "bin"
        return public_id

    def download(self, public_id: str) -> Path:
        content = self._get(public_id)
        with NamedTemporaryFile(suffix="." + self.formats[public_id], delete=False) as temporary:
            temporary.write(content)
        return Path(temporary.name)

    def fetch_page_image(self, public_id: str, page: int, width: int) -> bytes:
        self._get(public_id)
        if self.resource_types[public_id] != "image":
            raise ValueError("page images require an image resource")
        if page < 1 or width < 1:
            raise ValueError("page and width must be positive")
        return _fake_webp(f"page:{page};width:{width}".encode())

    def fetch_image(self, public_id: str) -> bytes:
        self._get(public_id)
        if self.resource_types[public_id] != "image":
            raise ValueError("image fetch requires an image resource")
        return _fake_webp(b"image")

    def temporary_download_url(self, public_id: str, expires_at: datetime) -> str:
        if public_id not in self.files:
            raise KeyError(public_id)
        if expires_at.tzinfo is None or expires_at <= datetime.now().astimezone():
            raise ValueError("expires_at must be a future timezone-aware datetime")
        return (
            f"memory://{public_id}?resource_type={self.resource_types[public_id]}"
            f"&format={self.formats[public_id]}&expires_at={expires_at.isoformat()}"
        )

    def delete(self, public_id: str) -> None:
        self.files.pop(public_id, None)
        self.resource_types.pop(public_id, None)
        self.formats.pop(public_id, None)

    def _get(self, public_id: str) -> bytes:
        self.fetch_count += 1
        return self.files[public_id]


def _fake_webp(data: bytes) -> bytes:
    return b"RIFF" + len(data).to_bytes(4, "little") + b"WEBP" + data
