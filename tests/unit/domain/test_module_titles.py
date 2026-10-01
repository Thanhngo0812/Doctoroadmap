from types import SimpleNamespace as Obj

from doc2roadmap.domain.module_titles import (clean_titles, common_content_title, grounded_suffix,
                                              prepare_module_titles, transfer_chunk_sections)


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


def test_root_and_empty_container_titles_follow_real_content():
    rows = [Obj(section_id="root", title="<document>", parent_section_id=None, level=0, role="noi_dung"),
            Obj(section_id="chapter", title="Kapitel 3", parent_section_id="root", level=1,
                role="de_cuong", has_direct_content=False),
            Obj(section_id="a", title="Vektoren", parent_section_id="chapter", level=2, role="noi_dung"),
            Obj(section_id="b", title="Matrizen", parent_section_id="chapter", level=2, role="noi_dung")]
    sections = {row.section_id: row for row in rows}
    assert common_content_title(["a", "b"], sections, clean_titles(rows)) == "Kapitel 3"
    sections["chapter"].has_direct_content = True
    assert common_content_title(["a", "b"], sections, clean_titles(rows)) == ""
    assert common_content_title(["a", "b"], sections, {"root": "document"}) == ""


def test_number_only_titles_use_same_document_contents_or_first_line():
    sections = [Obj(section_id="toc", title="Inhalt", parent_section_id=None, level=0,
                    role="mo_dau", order_index=0),
                Obj(section_id="k1", title="Kapitel 1", parent_section_id=None, level=1,
                    role="noi_dung", order_index=10),
                Obj(section_id="k3", title="Kapitel 3", parent_section_id=None, level=1,
                    role="noi_dung", order_index=30),
                Obj(section_id="j1", title="第1章", parent_section_id=None, level=1,
                    role="noi_dung", order_index=40),
                Obj(section_id="j3", title="第3章", parent_section_id=None, level=1,
                    role="noi_dung", order_index=60)]
    chunks = [Obj(parent_section_id="toc", role="mo_dau", order_index=1,
                  text="Kapitel 3 Lineare Abbildungen 51"),
              Obj(parent_section_id="j3", role="noi_dung", order_index=61,
                  text="線形写像\n本文")]
    titles, flags = prepare_module_titles(sections, chunks)
    assert titles["k3"] == "Kapitel 3 Lineare Abbildungen"
    assert titles["j3"] == "第3章 線形写像"
    assert "k1" in flags and "j1" in flags


def test_numbering_only_title_does_not_take_first_content_line_starting_with_digit():
    sections = [Obj(section_id="c1", title="Chapter 1", parent_section_id=None, level=1,
                    role="noi_dung", order_index=0),
                Obj(section_id="c2", title="Chapter 2", parent_section_id=None, level=1,
                    role="noi_dung", order_index=10)]
    chunks = [Obj(parent_section_id="c1", role="noi_dung", order_index=1,
                  text="3 matrix operations\nSubsequent teaching text"),
              Obj(parent_section_id="c2", role="noi_dung", order_index=11,
                  text="Vector spaces\nSubsequent teaching text")]
    titles, flags = prepare_module_titles(sections, chunks)
    assert titles["c1"] == "Chapter 1" and "c1" in flags
    assert titles["c2"] == "Chapter 2 Vector spaces" and "c2" not in flags


def test_document_case_majority_filters_lowercase_labels_but_not_uncased_script():
    sections = [Obj(section_id=f"s{i}", title=title, parent_section_id=None, level=2,
                    role="noi_dung", order_index=i)
                for i, title in enumerate(["Vector Spaces", "Linear Maps", "Matrix Algebra", "Eigenvalues",
                                           "Inner Products", "Orthogonal Projections", "Spectral Theory",
                                           "Normal Operators", "Jordan Form", "Basis Changes", "positivity"])]
    sections.append(Obj(section_id="ja", title="線形写像", parent_section_id=None,
                        level=3, role="noi_dung", order_index=20))
    titles, _ = prepare_module_titles(sections, [])
    assert "s10" not in titles
    assert titles["ja"] == "線形写像"


def test_suffix_must_contain_letter_even_when_source_only_has_digits():
    assert not grounded_suffix("123", ["123"], concept_names=[])
