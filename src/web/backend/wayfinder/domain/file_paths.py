"""Require ordinary independent files within an explicitly owned root."""
from pathlib import PurePosixPath
import stat


def safe_path(root,relative):
    part=PurePosixPath(relative)
    if part.is_absolute() or '..' in part.parts or ':' in relative or '\\' in relative:
        raise ValueError('Path escapes its root')
    path=root.joinpath(*part.parts)
    for ancestor in (path,*path.parents):
        try: metadata=ancestor.lstat()
        except FileNotFoundError: continue
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError('Linked path')
        if stat.S_ISREG(metadata.st_mode) and metadata.st_nlink!=1:
            raise ValueError('Hardlinked file')
    return path
