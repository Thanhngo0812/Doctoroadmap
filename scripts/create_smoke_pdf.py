from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def _pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_pdf(stream: bytes) -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(output)


def build_pdf(
    title: str,
    paragraphs: str | list[str] = "This paragraph proves leaf extraction works.",
) -> bytes:
    if isinstance(paragraphs, str):
        paragraphs = [paragraphs]
    lines = [f"BT /F1 18 Tf 72 720 Td ({_pdf_text(title)}) Tj ET"]
    lines.extend(
        f"BT /F1 11 Tf 72 {680 - index * 60} Td ({_pdf_text(paragraph)}) Tj ET"
        for index, paragraph in enumerate(paragraphs)
    )
    return _wrap_pdf("\n".join(lines).encode("ascii"))


def build_two_column_pdf() -> bytes:
    lines = [
        "BT /F1 11 Tf 72 720 Td 18 TL (Left column first.) Tj T* (Left column second.) Tj T* (Left column third.) Tj ET",
        "BT /F1 11 Tf 340 720 Td 18 TL (Right column first.) Tj T* (Right column second.) Tj T* (Right column third.) Tj ET",
    ]
    return _wrap_pdf("\n".join(lines).encode("ascii"))


def build_docx(path: Path) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""
    relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    document_relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""
    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
    <w:pPr><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/></w:rPr>
  </w:style>
</w:styles>"""
    document = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
  <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>DOCX smoke heading</w:t></w:r></w:p>
  <w:p><w:r><w:t>This paragraph proves DOCX leaf extraction works.</w:t></w:r></w:p>
  <w:tbl>
    <w:tblPr/><w:tblGrid><w:gridCol/><w:gridCol/></w:tblGrid>
    <w:tr><w:tc><w:p><w:r><w:t>Name</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Value</w:t></w:r></w:p></w:tc></w:tr>
    <w:tr><w:tc><w:p><w:r><w:t>A</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>1</w:t></w:r></w:p></w:tc></w:tr>
  </w:tbl>
  <w:sectPr/></w:body></w:document>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/_rels/document.xml.rels", document_relationships)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", styles)


if __name__ == "__main__":
    destination = Path("tests/fixtures/smoke.pdf")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(build_pdf("Docling smoke test"))
    updated = destination.with_name("smoke-updated.pdf")
    updated.write_bytes(
        build_pdf(
            "Docling smoke test",
            ["A newly inserted paragraph.", "This paragraph proves leaf extraction works."],
        )
    )
    two_column = destination.with_name("two-column.pdf")
    two_column.write_bytes(build_two_column_pdf())
    docx = destination.with_suffix(".docx")
    build_docx(docx)
    print(destination)
    print(updated)
    print(two_column)
    print(docx)
