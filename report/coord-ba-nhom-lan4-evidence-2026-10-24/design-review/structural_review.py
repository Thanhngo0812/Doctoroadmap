from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import traceback

ROOT = Path(__file__).resolve().parent
COPY = ROOT / "isolated"


class Node:
    def __init__(self, tag="root", attrs=(), parent=None):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children = []

    def descendants(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.descendants()

    def hasclass(self, name):
        return name in (self.attrs.get("class") or "").split()

    def accessible_text(self):
        if self.attrs.get("aria-hidden") == "true":
            return ""
        if self.attrs.get("aria-label"):
            return self.attrs["aria-label"]
        return "".join(child.accessible_text() if isinstance(child, Node) else child for child in self.children)


class Tree(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.root = Node()
        self.current = self.root
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        child = Node(tag, attrs, self.current)
        self.current.children.append(child)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.current = child

    def handle_endtag(self, tag):
        node = self.current
        while node is not self.root:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def parse(name):
    source = (COPY / "design/preview" / name).read_text(encoding="utf-8")
    return source, Tree(source)


def math_accessibility(name):
    _, tree = parse(name)
    formulas = [n for n in tree.root.descendants() if n.hasclass("katex")]
    result = [{"text_after_hiding_aria_hidden": n.accessible_text().strip(),
               "has_mathml": any(c.tag == "math" for c in n.descendants()),
               "has_aria_label": bool(n.attrs.get("aria-label")),
               "aria_hidden_branches": sum(c.attrs.get("aria-hidden") == "true" for c in n.descendants())}
              for n in formulas]
    return result


def test_w08_formulas_have_accessible_content():
    formulas = math_accessibility("w08_lecture_screens.html")
    assert len(formulas) == 2
    assert all(f["has_mathml"] or f["has_aria_label"] or "=" in f["text_after_hiding_aria_hidden"] for f in formulas), formulas


def test_w09_formulas_have_accessible_content():
    formulas = math_accessibility("w09_chat_screens.html")
    assert len(formulas) == 1
    assert all(f["has_mathml"] or f["has_aria_label"] or "=" in f["text_after_hiding_aria_hidden"] for f in formulas), formulas


def test_w08_formula_nodes_are_not_accidentally_nested():
    _, tree = parse("w08_lecture_screens.html")
    formulas = [n for n in tree.root.descendants() if n.hasclass("katex")]
    assert all(not any(child.hasclass("katex") for child in n.descendants()) for n in formulas), "W08 inline formula has unclosed outer .katex span and contains the following display formula and prose"


def test_w09_formula_has_subscript_layout_styles():
    source, _ = parse("w09_chat_screens.html")
    styles = "".join(re.findall(r"<style>(.*?)</style>", source, re.S))
    for match in re.finditer(r'<link\b[^>]*href="([^"]+)"', source):
        href = match.group(1)
        if ":" not in href:
            styles += (COPY / "design/preview" / href).resolve().read_text(encoding="utf-8")
    assert re.search(r"\.(?:msub|vlist-t|katex)\b[^{}]*\{", styles), "W09 has KaTeX-shaped DOM but zero KaTeX/subscript layout CSS in inline or linked tokens.css"


def test_w08_retry_controls_and_tail_claim():
    source, tree = parse("w08_lecture_screens.html")
    ids = {n.attrs["id"]: n for n in tree.root.descendants() if "id" in n.attrs}
    for section, button in [("section-lecture-early-error", "btn-retry-lecture-early"),
                            ("section-lecture-fatal-error", "btn-retry-lecture-fatal")]:
        assert any(n.attrs.get("id") == button and n.tag == "button" for n in ids[section].descendants())
    tail = ids["section-lecture-tail-error"].accessible_text()
    assert "cat_ngan" in tail
    assert "Tải lại bản đủ" not in tail


def test_w08_artwork_decodes_and_reduced_motion_has_static_source():
    from PIL import Image

    _, tree = parse("w08_lecture_screens.html")
    image = next(n for n in tree.root.descendants() if n.attrs.get("id") == "waiting-character-96px")
    assert image.attrs["width"] == "96" and image.attrs["height"] == "96"
    static = next(n for n in image.parent.children if isinstance(n, Node) and n.tag == "source")
    assert static.attrs["media"] == "(prefers-reduced-motion: reduce)"
    paths = {"animated": image.attrs["src"], "static": static.attrs["srcset"]}
    output = {}
    for kind, relative in paths.items():
        path = (COPY / "design/preview" / relative).resolve()
        assert path.is_relative_to(COPY)
        with Image.open(path) as image_file:
            frames = getattr(image_file, "n_frames", 1)
            for index in range(frames):
                image_file.seek(index)
                image_file.load()
            output[kind] = {"path": str(path.relative_to(COPY)), "decoded_frames": frames,
                            "natural_size": image_file.size, "format": image_file.format}
    assert output["animated"]["decoded_frames"] > 1
    assert output["static"]["decoded_frames"] == 1
    (ROOT / "artwork-decode.json").write_text(json.dumps(output, indent=2), encoding="utf-8")


def test_fixed_report_anchor_ids_exist():
    report = (COPY / "report/w24-kiem-lai-2026-10-22.md").read_text(encoding="utf-8")
    checks = [("w11_course_management_screens.html", "btn-delete-course-permanent"),
              ("w09_chat_screens.html", "text-tool-action")]
    for filename, anchor in checks:
        _, tree = parse(filename)
        assert any(n.attrs.get("id") == anchor for n in tree.root.descendants())
        assert f"`#{anchor}`" in report


def test_vm_independent_mode_writes_reconcile_with_actual_report():
    observations = {}
    for name, expected_writes in [("baseline", 74), ("fault-create-primary", 72), ("removed-accounting", 74)]:
        data = json.loads((ROOT / ("vm-" + name + ".json")).read_text(encoding="utf-8"))
        variables = data["variables"]
        written = sum(len(v["valuesByMode"]) for v in variables)
        assert len({v["name"] for v in variables}) == len(variables)
        assert written == expected_writes
        if name != "removed-accounting":
            assert written == data["report"]["created"]
            assert all(set(v["valuesByMode"]) == {"mode_light", "mode_dark"} for v in variables)
        else:
            assert data["report"]["created"] == 0
            assert data["report"]["created"] != written
        observations[name] = {"actual_variable_records": len(variables), "independent_written_mode_values": written,
                              "reported_created": data["report"]["created"], "reported_failed": data["report"]["failed"]}
    (ROOT / "vm-independent-observations.json").write_text(json.dumps(observations, indent=2), encoding="utf-8")


def main():
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    records = []
    for test in tests:
        try:
            test()
            records.append({"name": test.__name__, "status": "PASS"})
        except Exception as exc:
            records.append({"name": test.__name__, "status": "FAIL", "error": str(exc),
                            "traceback": traceback.format_exc()})
    (ROOT / "structural-observations.json").write_text(json.dumps({"tests": records,
        "math": {name: math_accessibility(name) for name in ("w08_lecture_screens.html", "w09_chat_screens.html")},
        "scope": "Reviewer-added assertions against SHA-matched ordinary copies; not browser evidence or repository PostgreSQL gate."}, indent=2), encoding="utf-8")
    print(json.dumps([{k: v for k, v in r.items() if k != "traceback"} for r in records], indent=2))
    return int(any(r["status"] == "FAIL" for r in records))


if __name__ == "__main__":
    sys.exit(main())
