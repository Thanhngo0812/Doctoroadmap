# Fixture: kết quả parse thật đã ghi lại

`nhap-mon-ml.json` là `DoclingDocument` của giáo trình *Nhập môn Học máy và Khai phá dữ liệu*, 20 trang,
ghi lại bằng `document.export_to_dict()` với trích ảnh bật ở scale `2.0`. Fixture chứa đủ chín ảnh dưới dạng
PNG nhúng.

Nạp lại:

```python
from docling_core.types.doc import DoclingDocument
doc = DoclingDocument.model_validate(json.loads(path.read_text(encoding="utf-8")))
```

## Vì sao có fixture này

Adapter Docling từng lấy nguyên khối `export_to_markdown()` cho hình. Khi bật trích ảnh, nhánh này trả data URI
base64 dài tới 295.568 ký tự thay vì placeholder cũ. Fixture thật mới bảo vệ được cả mìn base64, hình không chú
thích và vòng trích byte ảnh; một object giả lập không tái hiện được hành vi này của thư viện.

Fixture này cho test đối chiếu với **output thật**, mà vẫn nhanh như test đơn vị.

| | Thời gian |
|---|---|
| Chạy Docling trên PDF gốc có trích ảnh | **148,5 s** |
| Nạp lại fixture này | khoảng **0,11 s** |

## Đã kiểm round-trip

Ghi ra rồi nạp lại, kiểm số item và gọi `get_image(doc=…)` trên từng hình:

```
snapshot gốc : 170 item
snapshot sau : 170 item
khác biệt    : 0
✅ ROUND-TRIP HOÀN HẢO

picture khôi phục được pixel sau nạp lại: 9/9
```

Kích thước fixture là 1.543.889 byte; chín ảnh khôi phục có kích thước từ 189×184 tới 707×452.

## Khi nào phải sinh lại

**Mỗi lần nâng phiên bản `docling` hoặc đổi cấu hình/scale trích ảnh.** Fixture đóng băng cả hình dạng output
và pixel của một cấu hình parse cụ thể.
Các test đặt `HF_HUB_OFFLINE=1` để chỉ dùng model Docling đã có trong cache; lần tải model đầu tiên vẫn cần mạng.

Sinh lại:

```python
import json
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

options = PdfPipelineOptions(images_scale=2.0, generate_picture_images=True)
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
)
doc = converter.convert(PDF).document
payload = json.dumps(doc.export_to_dict(), ensure_ascii=False, separators=(",", ":"))
Path("nhap-mon-ml.json").write_text(payload, encoding="utf-8")
```

## Nguồn

- File: `nhap_mon_hoc_may_va_khai_pha_du_lieu_5944.pdf`
- `source_hash` (sha256): `d5a78c95b7603bffff77d6675c0286beaeb997f5633ac9e598bccb25305d3f71`
- Sinh bằng: `docling 2.114.0`, CPU, ảnh scale `2.0`, ngày 2026-08-20
- Nội dung: 170 item — 27 `section_header` (**tất cả `level=1`**), 85 `text`, 35 `list_item`, 9 `picture`,
  9 `caption`, 3 `footnote`, 1 `document_index`, 1 `formula`

## Fixture `xstk-ch3-1.json`

Fixture thứ hai được sinh từ `xstk-ch3-1.pdf` ở root dự án bằng đúng đoạn lệnh trên, cùng Docling 2.114.0,
`images_scale=2.0` và `generate_picture_images=True` ngày 2026-08-22.

- `source_hash` (sha256): `c265d409800af5515ba6e71408a9998020b38670369dfec4a5c01246e07fd20c`
- Kích thước: 1.582.906 byte; round-trip giữ 992/992 item.
- Nội dung: 427 `text`, 264 `formula`, 172 `list_item`, 67 `section_header`, 51 `table`, 6 `caption`,
  5 `picture`.
- Hiện trạng nguồn: 264/264 `formula.text` rỗng, 263/264 `formula.orig` có chữ; 23 heading bắt đầu bằng
  glyph bullet vùng dùng riêng; surface mà adapter cũ đưa vào chunk chứa 653 ký tự vùng dùng riêng.
- Round-trip giữ nguyên 263 raw formula và 1.769 ký tự vùng dùng riêng trên các field raw/cell có nghĩa.

Sinh lại fixture này mỗi lần nâng Docling hoặc đổi cấu hình/scale trích ảnh, giống `nhap-mon-ml.json`. Chỉ cần
đổi source và tên file đích trong script; không parse tài liệu thật trong test nhanh.

## Fixture `baocao-canhan.json`

Fixture DOCX được sinh ngày 2026-08-29 từ `Baocaocanhan_NgoCongThanh.docx` ở root dự án, bằng Docling 2.114.0
và converter mặc định cho DOCX.

- `source_hash` (sha256): `5c46fa3da73bf40e7ec06fdfd81b9eb9e5f5e95eee87cdb19119376c5e2536b6`.
- Kích thước fixture: **1.677.534 byte**; round-trip giữ 396/396 item.
- Nội dung nguồn có ba PNG trong `word/media/`, tổng 793.660 byte. Snapshot có 3 `picture`; cả 3/3 gọi
  `get_image(doc=...)` được sau round-trip.
- Cây heading khai báo có level `{1, 2}`. Fixture giữ raw level để test chuỗi ưu tiên dựng section và giữ các
  run định dạng không bbox để test nối câu.

Docling cũng báo một DrawingML shape cần LibreOffice. Tín hiệu này nằm trong OOXML source, không nằm trong
`DoclingDocument` snapshot; test parser dùng một DOCX in-memory riêng để bảo vệ cảnh báo `missing_image` đó.

## Fixture `naive-bayes.json`

Fixture slide được sinh ngày 2026-08-29 từ `5_Naive Bayes Classifier.pdf` ở root dự án bằng cùng cấu hình PDF
scale 2.0 và trích ảnh như hai fixture giáo trình.

- `source_hash` (sha256): `ec58dfdee3860805be93bd17d1faa6fe67a6cbe122474e73b882d769a33c6dff`.
- Kích thước fixture: **670.440 byte**; round-trip giữ 224/224 item.
- Nội dung: 36 trang, 2 `picture`, 13 `table`, 32 `formula`; cả 2/2 picture khôi phục được pixel.
- Surface trước sửa có 72 ký tự U+F097 đi vào chunk: 71 ở đầu `list_item` và một item text chỉ chứa bullet.

Hai fixture mới cùng hai fixture giáo trình chạy qua test số-vàng ở
`tests/unit/test_four_document_regression.py`. Đổi bất kỳ số vàng nào phải kèm giải thích trong cùng commit.
