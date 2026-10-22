"""Run the core fake only against manifest-verified independent development copies."""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import shutil
from tempfile import TemporaryDirectory

from doc2roadmap.application.ports.build import BuildResult
from doc2roadmap.infrastructure.artifacts.fake_build_runner import FakeBuildRunner
from wayfinder.domain.file_paths import safe_path


class ManifestFakeBuildRunner:
    def __init__(self,fixture_root,artifact_root,source_doc,*,manifest,manifest_sha256,recorder=None,pipeline_version='web-fake-v1'):
        if source_doc not in FakeBuildRunner.SOURCES: raise ValueError('Unapproved development source')
        if sha256(Path(manifest).read_bytes()).hexdigest()!=manifest_sha256: raise ValueError('Manifest hash mismatch')
        self.fixture_root,self.artifact_root=Path(fixture_root),Path(artifact_root)
        self.source_doc,self.recorder,self.pipeline_version=source_doc,recorder,pipeline_version
        entries=json.loads(Path(manifest).read_text(encoding='utf-8'))['files']
        roots=[f'artifacts/{kind}/{source_doc}/' for kind in FakeBuildRunner.ARTIFACTS]
        roots.append(f'artifacts/phase_b/formula_images/{source_doc}/')
        self.entries=[e for e in entries if any(e['path'].startswith(root) for root in roots)]
        if not self.entries: raise ValueError('Source is absent from manifest')

    def execute(self,file_path,doc_id,**kwargs):
        with TemporaryDirectory(prefix='wayfinder-fake-artifacts-') as directory:
            scratch=Path(directory)
            expected={e['path'] for e in self.entries}
            actual=set()
            roots=[f'artifacts/{kind}/{self.source_doc}' for kind in FakeBuildRunner.ARTIFACTS]
            roots.append(f'artifacts/phase_b/formula_images/{self.source_doc}')
            for relative in roots:
                base=safe_path(self.fixture_root,relative)
                if base.exists():
                    for path in base.rglob('*'):
                        safe_path(self.fixture_root,path.relative_to(self.fixture_root).as_posix())
                        if path.is_file(): actual.add(path.relative_to(self.fixture_root).as_posix())
            if actual!=expected: raise ValueError('Fixture files differ from manifest allowlist')
            for entry in self.entries:
                source=safe_path(self.fixture_root,entry['path'])
                if sha256(source.read_bytes()).hexdigest()!=entry['sha256']: raise ValueError('Fixture hash mismatch')
                target=safe_path(scratch,entry['path'])
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,target)
            runner=FakeBuildRunner(scratch/'artifacts',self.source_doc,pipeline_version=self.pipeline_version)
            result=runner.execute(file_path,doc_id,**kwargs)
            if result.status=='succeeded':
                for kind in (*FakeBuildRunner.ARTIFACTS,'phase_b/formula_images'):
                    source=scratch/'artifacts'/kind/doc_id
                    if source.exists():
                        for path in source.rglob('*'):
                            if not path.is_file(): continue
                            relative=(Path(kind)/doc_id/path.relative_to(source)).as_posix()
                            target=safe_path(self.artifact_root,relative)
                            target.parent.mkdir(parents=True,exist_ok=True)
                            if target.exists() and target.read_bytes()!=path.read_bytes():
                                raise ValueError('Published fake artifact conflicts with destination')
                            if not target.exists(): shutil.copyfile(path,target)
            if self.recorder: self.recorder(result)
            return result
