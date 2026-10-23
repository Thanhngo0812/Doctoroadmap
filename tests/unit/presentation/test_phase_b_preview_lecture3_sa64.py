"""SA-64: the preview page streams lecture-3 pieces, and renders Markdown, formulas and source links safely."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "application"))

from test_phase_b_preview import events, request, runtime, server  # noqa: F401  (fixtures)
from sa64_support import FakeModel, wait_for

HTML = Path(__file__).resolve().parents[3] / "src" / "doc2roadmap" / "presentation" / "preview" / "phase_b.html"
NODE = shutil.which("node")


def test_page_pins_katex_and_marked_versions_on_cdnjs_and_the_server_allows_exactly_that(server):
    page = HTML.read_text(encoding="utf-8")
    scripts = re.findall(r'<(?:script src|link rel="stylesheet" href)="(https://[^"]+)"', page)
    assert sorted(scripts) == [
        "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css",
        "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"]
    _, base = server
    with urlopen(Request(base + "/"), timeout=10) as response:
        policy = response.headers["Content-Security-Policy"]
    for directive in ("script-src", "style-src", "font-src"):
        assert "https://cdnjs.cloudflare.com" in re.search(directive + r"[^;]*", policy).group(0)
    assert "default-src 'self'" in policy and "frame-ancestors 'none'" in policy


def test_lecture_button_streams_deltas_then_a_final_lecture_with_no_validation_then_serves_the_cache(server, runtime):
    runtime.mode, runtime.allow_spend = "gemini", True
    model = FakeModel()
    runtime.model = lambda purpose: model
    service, base = server
    args = {"doc_id": "doc-1", "graph_version": 1, "node_id": "n0"}
    first = events(request(base + "/api/lecture", args))
    kinds = [event["event"] for event in first]
    assert kinds[0] == "skeleton" and kinds[-1] == "final" and "delta" in kinds
    assert kinds.index("delta") < kinds.index("final")
    final = first[-1]["lecture"]
    assert final["contract_version"] == "lecture-3" and final["status"] == "ready" and final["self_check"]
    assert "validation" not in json.dumps(first)
    second = events(request(base + "/api/lecture", args))
    assert [event["event"] for event in second] == ["skeleton", "final"]
    # the page also preloads the next concept; the clicked one was written only once
    assert sum(call.prompt.startswith("Khái niệm: Ma trận" + chr(10)) for call in model.calls) == 1
    wait_for(lambda: len([r for r in runtime.store.usage_rows("doc-1") if r["purpose"] == "lecture"]) >= 2)


JS = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const pick = name => html.split('\n').find(line => line.startsWith('function ' + name + '('));
eval(pick('sourceHtml') + '\n' + pick('renderMarkdown') + '\nglobalThis.renderMarkdown = renderMarkdown;');
globalThis.window = globalThis;
globalThis.marked = {parse: text => '<p>' + text + '</p>'};
globalThis.katex = {renderToString: (tex, o) => '<k d=' + o.displayMode + '>' + tex + '</k>'};
const cases = JSON.parse(process.argv[2]);
console.log(JSON.stringify(cases.map(([md, sources]) => renderMarkdown(md, sources))));
"""


def render(*cases):
    done = subprocess.run([NODE, "-e", JS, "--", str(HTML), json.dumps(cases)], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(done.stdout)


SOURCES = [{"label": "S1", "page": 37}, {"label": "S2", "page": 38}]


@pytest.mark.skipif(NODE is None, reason="node not installed")
def test_markdown_rendering_keeps_formulas_makes_label_links_and_escapes_html():
    inline, display, links, group, unknown, hostile = render(
        ["Ta có $x_1^2 < y$ nên", SOURCES], ["$$a<b$$", SOURCES], ["Theo sách [S1].", SOURCES],
        ["Hai nguồn [S1, S2].", SOURCES], ["Nhãn lạ [S9].", SOURCES], ["<img src=x onerror=alert(1)> [S1]", SOURCES])
    assert "<k d=false>x_1^2 < y</k>" in inline
    assert "<k d=true>a<b</k>" in display
    assert '<a href="#" class="src" data-page="37">[S1]</a>' in links
    assert links.count("<a ") == 1 and group.count("<a ") == 2 and 'data-page="38"' in group
    assert "<a " not in unknown and "[S9]" in unknown
    assert "<img" not in hostile and "&lt;img" in hostile


@pytest.mark.skipif(NODE is None, reason="node not installed")
def test_page_script_has_no_syntax_error():
    script = re.search(r"<script>\n(.*?)</script>", HTML.read_text(encoding="utf-8"), re.S).group(1)
    path = Path(__file__).with_name("_sa64_script_check.js")
    path.write_text("new Function(" + json.dumps(script) + ");", encoding="utf-8")
    try:
        subprocess.run([NODE, str(path)], capture_output=True, text=True, check=True)
    finally:
        path.unlink()
