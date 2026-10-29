"""MediaStore on local disk for the demo server: real page images, no cloud traffic."""
from base64 import urlsafe_b64decode, urlsafe_b64encode
from hashlib import sha256
import hmac
from io import BytesIO
from pathlib import Path
import secrets
import shutil
from uuid import uuid4

from wayfinder.domain.file_paths import safe_path

DOWNLOAD_ROUTE = '/api/v1/demo-files/'


def _webp(image):
    output = BytesIO()
    image.convert('RGB').save(output, format='WEBP', quality=80)
    return output.getvalue()


class DiskMediaStore:
    def __init__(self, root, *, secret=None):
        self.root = Path(root)
        # Per-process secret: download links never outlive the server that issued them.
        self._secret = secret or secrets.token_bytes(32)

    def _path(self, public_id):
        return safe_path(self.root, public_id)

    def upload(self, path, folder, resource_type):
        extension = Path(path).suffix.lower()
        if resource_type not in {'image', 'raw'} or resource_type == 'raw' and extension != '.docx':
            raise ValueError('Unsupported upload type')
        public_id = folder.rstrip('/') + '/' + uuid4().hex + extension
        target = self._path(public_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        return public_id

    def download(self, public_id, *, destination=None):
        source = self._path(public_id)
        if destination is None:
            destination = self.root / 'tmp' / (uuid4().hex + source.suffix)
            destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        return destination

    def fetch_page_image(self, public_id, page, width):
        if page < 1 or width < 1:
            raise ValueError('page and width must be positive')
        import pypdfium2 as pdfium
        with pdfium.PdfDocument(self._path(public_id).read_bytes()) as document:
            if page > len(document):
                raise ValueError('page is outside the document')
            sheet = document[page - 1]
            try:
                bitmap = sheet.render(scale=width / sheet.get_width())
                return _webp(bitmap.to_pil())
            finally:
                sheet.close()

    def fetch_image(self, public_id):
        from PIL import Image
        with Image.open(self._path(public_id)) as image:
            return _webp(image)

    def temporary_download_url(self, public_id, expires_at):
        if expires_at.tzinfo is None:
            raise ValueError('expires_at must be timezone-aware')
        if not self._path(public_id).is_file():
            raise KeyError(public_id)
        payload = f'{public_id}\n{int(expires_at.timestamp())}'.encode()
        signature = hmac.new(self._secret, payload, sha256).digest()
        return DOWNLOAD_ROUTE + urlsafe_b64encode(payload + b'\n' + signature).decode().rstrip('=')

    def resolve_download(self, token, now):
        """Return the stored file for an unexpired, untampered token, else None."""
        try:
            raw = urlsafe_b64decode(token + '=' * (-len(token) % 4))
            payload, signature = raw[:-33], raw[-32:]
            public_id, expires = payload.decode().split('\n')
            valid = hmac.compare_digest(hmac.new(self._secret, payload, sha256).digest(), signature)
            path = self._path(public_id)
        except (ValueError, UnicodeDecodeError):
            return None
        if not valid or now.timestamp() >= int(expires) or not path.is_file():
            return None
        return path

    def delete(self, public_id):
        self._path(public_id).unlink(missing_ok=True)
