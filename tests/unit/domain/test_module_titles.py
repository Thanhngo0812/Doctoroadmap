from types import SimpleNamespace as Obj

from doc2roadmap.domain.module_titles import clean_titles, common_content_title, grounded_suffix, transfer_chunk_sections


def section(identifier, title, parent=None, role="noi_dung"):
    return Obj(section_id=identifier, title=title, parent_section_id=parent, role=role)


def test_clean_titles_uses_unicode_and_document_evidence_not_language_dictionary():
    rows = [section("ja1", "◆ 学習方法"), section("ja2", "学習 方法"),
            section("fr1", "\ue000 u Algèbre linéaire"), section("fr2", "u Calcul numérique"),
            section("fr3", "u Géométrie analytique"),
            section("sentence", "Ceci est une phrase qui contient beaucoup trop de mots pour servir de titre académique")]
    result = clean_titles(rows)
    assert result["ja1"] == "学習 方法"
    assert result["fr1"] == "Algèbre linéaire"
    assert "sentence" not in result


def test_common_title_must_be_shared_content_section():
    rows = [section("preface", "Préface", role="mo_dau"),
            section("chapter", "Chapitre 1", "preface"),
            section("a", "Vecteurs", "chapter"), section("b", "Matrices", "chapter")]
    sections = {row.section_id: row for row in rows}
    assert common_content_title(["a", "b"], sections, clean_titles(rows)) == "Chapitre 1"
    sections["chapter"].role = "mo_dau"
    assert common_content_title(["a", "b"], sections, clean_titles(rows)) == ""


def test_suffix_rejects_unseen_content_words_across_scripts():
    assert grounded_suffix("Algèbre linéaire", ["Algèbre des matrices", "Transformation linéaire"])
    assert not grounded_suffix("topologie linéaire", ["Algèbre des matrices", "Transformation linéaire"])
    assert not grounded_suffix("学習", ["機械学習", "方法"])
    assert not grounded_suffix("分析", ["機械学習", "方法"])


def test_suffix_rejects_base_repetition_fragments_and_nonletters_across_languages():
    assert not grounded_suffix("Algèbre", ["Algèbre linéaire"], "2.1 Algèbre")
    assert not grounded_suffix("linéaire Algèbre", ["Algèbre linéaire"], "Algèbre")
    assert not grounded_suffix("Matrices", ["Matrices inversibles"], "Matrices inversibles avancées")
    assert not grounded_suffix("linéaire", ["Algèbre linéaire"], "Matrices")
    assert not grounded_suffix("実", ["実数空間"], "空間")
    assert not grounded_suffix("(1/1)", ["Vecteurs"], "Chapitre 1")
    assert grounded_suffix("Algèbre linéaire", ["Algèbre linéaire"], "Matrices")
    assert grounded_suffix("実数空間", ["実数空間"], "行列")


def test_transfer_section_path_by_text_not_broken_old_tree():
    old = [Obj(chunk_id="old", text="uno dos tres cuatro cinco seis siete ocho", parent_section_id="broken")]
    new = [Obj(chunk_id="new-a", text="uno dos tres cuatro cinco seis", parent_section_id="correct"),
           Obj(chunk_id="new-b", text="tres cuatro cinco seis siete ocho", parent_section_id="correct")]
    assert transfer_chunk_sections(old, new) == {"old": "correct"}
    assert old[0].parent_section_id == "broken"
