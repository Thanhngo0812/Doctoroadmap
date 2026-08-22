from pathlib import Path

from doc2roadmap.infrastructure.parsing import DoclingParser

from create_smoke_pdf import build_pdf


if __name__ == "__main__":
    tree = DoclingParser().parse(build_pdf("Docling smoke test"), "smoke.pdf")
    assert len(tree.nodes) > 0
    print(f"Docling OK: {len(tree.nodes)} block(s)")

