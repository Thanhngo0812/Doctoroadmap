from types import SimpleNamespace as Obj

from doc2roadmap.domain.module_titles import clean_titles, common_content_title, grounded_suffix


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
    assert grounded_suffix("学習", ["機械学習", "方法"])
    assert not grounded_suffix("分析", ["機械学習", "方法"])
