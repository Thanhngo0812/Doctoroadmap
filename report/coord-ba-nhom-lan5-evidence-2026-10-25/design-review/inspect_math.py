from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
COPY = ROOT / "isolated"
sys.path.insert(0, str(COPY))
spec = importlib.util.spec_from_file_location("candidate_token_tests", COPY / "tests/unit/presentation/test_tokens_and_wcag.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def text(node):
    return "".join(text(c) if isinstance(c, module.HtmlAstNode) else c for c in node.children)


def main():
    records = []
    for filename, expected in [
        ("w08_lecture_screens.html", ["P_coronary = P_diastolic - P_LVEDP", "Q = (P_diastolic - P_LVEDP) / R_coronary"]),
        ("w09_chat_screens.html", ["P_coronary = P_diastolic - P_LVEDP"]),
    ]:
        _, tree = module.parse_preview_tree(filename)
        formulas = [n for n in tree.root.descendants() if n.hasclass("katex")]
        assert len(formulas) == len(expected)
        for formula, label in zip(formulas, expected):
            nodes = list(formula.descendants())
            assert formula.attrs.get("role") == "math"
            assert formula.attrs.get("aria-label") == label
            assert not any(n.hasclass("katex") for n in nodes)
            assert "Lưu lượng dòng máu đạt đỉnh" not in text(formula)
            math = [n for n in nodes if n.tag == "math"]
            assert len(math) == 1
            assert math[0].attrs.get("xmlns") == "http://www.w3.org/1998/Math/MathML"
            current = math[0]
            while current is not None:
                assert current.attrs.get("aria-hidden") != "true"
                current = current.parent
            semantics = list(math[0].descendants())
            assert len([n for n in semantics if n.tag == "msub"]) == 3
            assert "=" in [text(n) for n in semantics if n.tag == "mo"]
            assert "−" in [text(n) for n in semantics if n.tag == "mo"]
            assert len([n for n in semantics if n.tag == "mfrac"]) == int(label.startswith("Q"))
            html = [n for n in nodes if n.hasclass("katex-html")]
            assert len(html) == 1 and html[0].attrs.get("aria-hidden") == "true"
            records.append({"file": filename, "role": formula.attrs["role"], "accessible_label": label,
                "namespace": math[0].attrs["xmlns"], "mathml_subscripts": 3, "has_fraction": label.startswith("Q"),
                "nested_katex": 0, "prose_inside_formula": False, "mathml_aria_hidden_ancestor": False})
    (ROOT / "math-structure.json").write_text(json.dumps({"status": "PASS", "formulas": records,
        "scope": "Three static sample formulas; this does not establish a generic LaTeX renderer or browser geometry."}, indent=2), encoding="utf-8")
    print(json.dumps({"sample_formulas_checked": len(records), "status": "PASS"}))


if __name__ == "__main__":
    main()
