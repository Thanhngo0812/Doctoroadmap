"""Private source delivery and lazy media publication for a pinned learning graph."""
from datetime import timedelta
from pathlib import PurePosixPath

from sqlalchemy import text

from doc2roadmap.application.phase_b.clock import SystemClock
from wayfinder.api.errors import WebError
from wayfinder.domain.file_paths import safe_path


class LearningMedia:
    def __init__(self, engine, settings, *, store=None, clock=None):
        self.engine, self.settings, self.store = engine, settings, store
        self.clock = clock or SystemClock()

    def _store(self):
        if self.store is None:
            from wayfinder.infrastructure.media import CloudinaryMediaStore
            self.store = CloudinaryMediaStore(
                self.settings.cloudinary_url.get_secret_value() if self.settings.cloudinary_url else None)
        return self.store

    def _source(self, course, graph):
        with self.engine.connect() as c:
            row = c.execute(text('SELECT public_id,kind,page_count FROM upload WHERE course_id=:cid'),
                            {'cid': course.id}).mappings().first()
        if row:
            return dict(row)
        if course.source_public_id:
            kind = 'docx' if course.source_public_id.lower().endswith('.docx') else 'pdf'
            stats = getattr(getattr(graph, 'tree', None), 'parse_stats', {})
            return {'public_id': course.source_public_id, 'kind': kind, 'page_count': stats.get('page_count')}
        return None

    def describe_source(self, course, graph):
        source = self._source(course, graph)
        return {key: source[key] for key in ('kind', 'page_count')} if source else None

    def open_source_page(self, course, graph, page):
        source = self._source(course, graph)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 0
        if (not source or source['kind'] != 'pdf' or not source['page_count']
                or not 1 <= page <= source['page_count']):
            raise WebError('not_found', 'Tài liệu không có trang này')
        return self._store().fetch_page_image(source['public_id'], page, self.settings.page_image_width), source['page_count']

    def open_source_file(self, course, graph):
        source = self._source(course, graph)
        if not source:
            raise WebError('not_found', 'Không có tệp tài liệu')
        return self._store().temporary_download_url(source['public_id'],
            self.clock.now() + timedelta(seconds=self.settings.signed_url_ttl_seconds))

    def asset_key(self, graph, ref):
        known = getattr(graph, 'formula_images', {})
        source = known.get(ref.get('occurrence_id'))
        version = getattr(graph, 'parse_version', None)
        if not source or not version or not source.get('image_ref'):
            return None
        relative = str(source['image_ref'])
        key = f'parse-v{int(version)}/{relative}'
        try:
            safe_path(self.settings.artifact_root, f'phase_b/formula_images/{graph.doc_id}/{key}')
        except ValueError:
            return None
        return key

    def media_keys(self, graph, row):
        keys = []
        for ref in row.get('image_refs', []):
            key = ref.get('asset_key') or ref.get('image_ref') if isinstance(ref, dict) else ref
            if not isinstance(key, str):
                continue
            try:
                safe_path(self.settings.artifact_root, key)
            except ValueError:
                continue
            keys.append(key)
        return keys

    def _assets(self, graph):
        assets = {}
        for occurrence in getattr(graph, 'formula_images', {}):
            key = self.asset_key(graph, {'occurrence_id': occurrence})
            if key:
                assets[key] = (f'phase_b/formula_images/{graph.doc_id}/{key}', 'formula')
        for nid in graph.learnable_nodes:
            for row in graph.get_media(nid):
                for key in self.media_keys(graph, row):
                    assets[key] = (key, 'media')
        return assets

    def get_media(self, course, graph, asset_key):
        # The published graph is the allowlist, even if a different version has a DB mapping.
        asset = self._assets(graph).get(asset_key)
        if not asset or PurePosixPath(asset_key).is_absolute():
            raise WebError('not_found', 'Không tìm thấy nội dung yêu cầu')
        relative, kind = asset
        with self.engine.begin() as c:
            params = {'doc': course.doc_id, 'key': asset_key}
            c.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:identity,0))'),
                      {'identity': course.doc_id + '/' + asset_key})
            public = c.scalar(text('SELECT public_id FROM media_asset WHERE doc_id=:doc AND asset_key=:key'), params)
            if public is None:
                path = safe_path(self.settings.artifact_root, relative)
                if not path.is_file():
                    raise WebError('not_found', 'Không tìm thấy ảnh trong tài liệu')
                public = self._store().upload(path, self.settings.cloudinary_folder + '/media/' + course.doc_id, 'image')
                try:
                    c.execute(text('INSERT INTO media_asset(doc_id,asset_key,public_id,kind,bytes,created_at) '
                        'VALUES(:doc,:key,:public,:kind,:bytes,:now)'),
                        {**params, 'public': public, 'kind': kind, 'bytes': path.stat().st_size, 'now': self.clock.now()})
                except Exception:
                    self._store().delete(public)
                    raise
        return self._store().fetch_image(public)
