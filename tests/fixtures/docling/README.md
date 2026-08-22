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
đổi `PDF` và tên file đích trong script; không parse PDF thật trong test nhanh.
