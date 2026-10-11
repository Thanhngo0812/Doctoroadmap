import hashlib
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.ingest_document import _text_quality, tree_text_quality, parse_config, _hash, IngestDocument
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.presentation.cli import main as cli
from tests.conftest import WordCounter, splitter
from tests.unit.application.test_v4_text_quality import SwitchingParser, CLEAN, BROKEN


CORRUPT = 'a) Ký kӃt và thӵc hiӋn hӧp đӗng vӟi chӫ vұt thӇ… '


def test_cyrillic_corruption_in_real_sentence_is_rejected():
    quality = tree_text_quality(DocumentTree([DocumentNode('text', CORRUPT * 10, 0, page=28)]))
    assert quality['warnings']
    assert quality['non_latin_greek_letter_ratio'] > .1
    assert quality['pages'][0]['warnings']


def test_nfkc_micro_and_mathematical_greek_or_latin_are_not_foreign_letters():
    assert _text_quality(['µ μ α 𝛼 𝐀 ℒ 𝓥 Tiếng Việt'])['non_latin_greek_letter_ratio'] == 0


def test_title_is_checked_and_fictitious_heading_type_is_not():
    assert tree_text_quality(DocumentTree([DocumentNode('title', 'BOÄ MOÂN TOAÙN', 0, page=3)]))['warnings']
    assert not tree_text_quality(DocumentTree([DocumentNode('heading', CORRUPT * 10, 0, page=3)]))['warnings']


@pytest.mark.parametrize('reason', [None, 'Tái lập văn bản đã khóa'])
def test_cli_pinned_backend_never_switches_or_reparses_cached_vni(tmp_path, monkeypatch, capsys, reason):
    store = JsonArtifactStore(tmp_path/'store'); source=tmp_path/'book.pdf';source.write_bytes(b'pdf')
    parser = SwitchingParser(); config=parse_config(parser)
    store.save_parse('book', hashlib.sha256(b'pdf').hexdigest(), _hash(config), 'config', {'parser':config},
                     DocumentTree([DocumentNode('section_header','BOÄ MOÂN TOAÙN',0,page=3),DocumentNode('text',CLEAN,1,page=3)]), {})
    # Keep the real composition root: only replace its dependency constructors.
    import doc2roadmap.composition as composition
    monkeypatch.setattr(composition, 'Settings', lambda: SimpleNamespace(artifact_dir=store.root,tokenizer_model='unused',tokenizer_id='words',
        max_tokens=512,max_table_tokens=2048,hard_cap_tokens=6000,target_tokens=256,sentence_overlap=1))
    monkeypatch.setattr(composition, 'DoclingParser', lambda *a,**kw: parser)
    monkeypatch.setattr(composition, 'SentencePieceTokenCounter', lambda *a: WordCounter())
    monkeypatch.setattr(composition, 'require_native_pdf', lambda source: None)  # scope is tested with real PDFs in v416
    monkeypatch.setattr(SwitchingParser,'with_pdf_backend',lambda *a: pytest.fail('pinned backend switched'))
    monkeypatch.setattr(SwitchingParser,'parse',lambda *a: pytest.fail('cached parse repeated'))
    args=['ingest',str(source),'--doc-id','book','--a1','docling','--pdf-backend','docling-parse']
    if reason:args+=['--allow-text-quality-reason',reason]
    status=cli.main(args)
    assert status==(0 if reason else 2)
    if reason:
        assert store.load_latest_chunks('book').manifest['parse_version']==1
        assert store.load_latest_chunks('book').manifest['text_quality_override_reason']==reason
    else:
        assert 'chất lượng chữ' in capsys.readouterr().err
        with pytest.raises(FileNotFoundError):store.load_latest_chunks('book')


def test_unknown_quality_is_not_selected_as_clean_in_dry_run(tmp_path):
    store=JsonArtifactStore(tmp_path);parser=SwitchingParser();config=parse_config(parser)
    store.save_parse('book',hashlib.sha256(b'pdf').hexdigest(),_hash(config),'config',{'parser':config},
                     DocumentTree([DocumentNode('text',BROKEN,0,page=1)]),{})
    use_case=IngestDocument(parser,store,WordCounter(),splitter())
    try:use_case.select_parse(b'pdf','book.pdf','book',dry_run=True)
    except ValueError:pass
    selection=use_case.last_parse_selection
    assert selection['attempts'][0]['quality']['warnings']
    assert selection['selected_backend']=='docling-parse'
    assert selection['reason']!='unmeasured'
    assert selection['attempts'][-1]['quality_status']=='chưa đo'


def test_local_script_corruption_not_diluted_and_pages_under_100_are_exempt():
    tree=DocumentTree([DocumentNode('text','a'*98+'сс',0,page=1),DocumentNode('text',CLEAN*10,1,page=2)])
    quality=tree_text_quality(tree)
    assert quality['non_latin_greek_letter_ratio']<.01
    assert quality['pages'][0]['warnings'] and not quality['pages'][1]['warnings']
    assert any('1' in w for w in quality['warnings'])
    short=tree_text_quality(DocumentTree([DocumentNode('text','a'*97+'сс',0,page=1)]))
    assert not short['warnings']


def test_new_unmeasured_dry_run_reports_unknown_without_parsing(tmp_path, monkeypatch):
    parser=SwitchingParser('pypdfium2')
    monkeypatch.setattr(parser,'parse',lambda *a:pytest.fail('dry-run parsed'))
    case=IngestDocument(parser,JsonArtifactStore(tmp_path),WordCounter(),splitter())
    case.select_parse(b'pdf','book.pdf','book',dry_run=True)
    assert case.last_parse_selection['selected_backend'] is None
    assert case.last_parse_selection['planned_backend']=='pypdfium2'
    assert case.last_parse_selection['attempts'][0]['quality_status']=='chưa đo'


def test_mode_does_not_change_parse_key_and_auto_starts_with_pdfium(monkeypatch,tmp_path):
    import doc2roadmap.composition as composition
    monkeypatch.setattr(composition,'Settings',lambda:SimpleNamespace(artifact_dir=tmp_path,tokenizer_model='none',tokenizer_id='words'))
    monkeypatch.setattr(composition,'SentencePieceTokenCounter',lambda *a:WordCounter())
    auto,_=composition.build_ingest();pinned,_=composition.build_ingest('pypdfium2')
    assert auto.parser.pdf_backend=='pypdfium2'
    assert auto.allow_backend_fallback and not pinned.allow_backend_fallback
    assert parse_config(auto.parser)==parse_config(pinned.parser)
