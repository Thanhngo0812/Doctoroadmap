"""Persistent fake media shared by local API and worker processes; no cloud traffic."""
from pathlib import Path
import shutil
from uuid import uuid4

from wayfinder.domain.file_paths import safe_path
from wayfinder.fakes.media import MemoryMediaStore


class LocalFakeMediaStore(MemoryMediaStore):
    def __init__(self,root):
        super().__init__()
        self.root=Path(root)

    def upload(self,path,folder,resource_type):
        extension=Path(path).suffix.lower()
        if resource_type not in {'image','raw'} or resource_type=='raw' and extension!='.docx':
            raise ValueError('Unsupported fake upload type')
        public_id=folder.rstrip('/')+'/'+uuid4().hex+extension
        target=safe_path(self.root,public_id)
        target.parent.mkdir(parents=True,exist_ok=True)
        safe_path(self.root,public_id)
        shutil.copyfile(path,target)
        return public_id

    def _get(self,public_id):
        path=safe_path(self.root,public_id)
        data=path.read_bytes()
        self.fetch_count+=1
        self.formats[public_id]=path.suffix.lstrip('.')
        self.resource_types[public_id]='raw' if path.suffix=='.docx' else 'image'
        self.files[public_id]=data
        return data

    def temporary_download_url(self,public_id,expires_at):
        self._get(public_id)
        return super().temporary_download_url(public_id,expires_at)

    def delete(self,public_id):
        safe_path(self.root,public_id).unlink(missing_ok=True)
        super().delete(public_id)
