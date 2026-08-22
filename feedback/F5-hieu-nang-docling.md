# F10 🟠 — `DocumentConverter` được dựng lại mỗi lần `parse()`

> **Đã xử lý 2026-08-14:** parser khởi tạo converter khi parse lần đầu và tái sử dụng cho các lần parse sau;
> unit test xác nhận chỉ khởi tạo một lần.

Kèm theo: số đo hiệu năng thật của Docling, để tham chiếu về sau.

## Lỗi

```python
# src/doc2roadmap/infrastructure/parsing/docling_parser.py:68
document = DocumentConverter().convert(temporary_name).document
#          ^^^^^^^^^^^^^^^^^^^ dựng MỚI mỗi lần gọi parse()
```

Mỗi lần `parse()` nạp lại toàn bộ 770 trọng số của model layout cộng ba model RapidOCR. Log xác nhận —
`Loading weights: 0/770` xuất hiện trước **mọi** lần parse, kể cả các lần liên tiếp trong cùng một tiến trình.

**Chi phí đo được: ~4.7 giây mỗi lần gọi `parse()`.**

| | 20 trang |
|---|---|
| Converter dùng lại | 34.25s |
| Dựng mới mỗi lần (bản hiện tại) | 38.99s |

**Ảnh hưởng thực tế phụ thuộc cách dùng:**

- Ingest **một** giáo trình 500 trang: 4.7s trên ~15 phút — không đáng kể.
- Ingest **nhiều tài liệu ngắn** trong một phiên: 4.7s **mỗi tài liệu**. Với 100 bài báo 10 trang, đó là gần
  8 phút thuần tuý nạp đi nạp lại cùng một model.
- **Test tích hợp**: 3 fixture × 4.7s ≈ 14s trong tổng 27.6s — **quá nửa thời gian chạy test là nạp model lại.**

**Sửa:** dựng converter một lần trong `__init__` (hoặc lazy rồi cache trên instance), giữ `parse()` không đổi
chữ ký. Adapter vốn đã nằm sau cổng nên không có gì phía ngoài phải sửa.

Lưu ý khi sửa: nếu dựng trong `__init__` thì việc khởi tạo `DoclingParser()` trở nên đắt, mà `composition.py`
có thể tạo nó cả khi lệnh không parse gì. Lazy + cache là an toàn hơn.

---

## Số đo hiệu năng Docling (CPU, máy này)

> ⚠️ **Đính chính 2026-08-15 — số dưới đây thấp hơn thực tế khoảng 4 lần.**
> Bench này chạy trên PDF **tự sinh, không có ảnh nào**, nên OCR không có gì để làm. Trên giáo trình thật
> (`nhap-mon-ml`, 20 trang có hình): **144,6 giây = 7,2 giây/trang**, không phải 1,8. Suy lại: 500 trang là
> **~60 phút**, không phải 15. Xem [F8](./F8-chunk-vun-va-mat-mat-im-lang.md).
> Kết luận về việc đóng băng `parse_tree` **không đổi** — nó chỉ đúng hơn nữa.

Đo trên PDF sinh bằng script, mỗi trang một heading + 28 dòng văn bản.

| Trang | Giây | Giây/trang |
|---:|---:|---:|
| 1 | 4.6 | 4.61 |
| 5 | 13.8 | 2.75 |
| 20 | 43.0 | 2.15 |
| 50 | 91.5 | **1.83** |

Chi phí cố định ~2–3s bị khấu hao dần; **trạng thái ổn định khoảng 1.7–1.8 giây/trang.**

Suy ra cho giáo trình thật:

| Tài liệu | Thời gian parse |
|---|---|
| 100 trang | ~3 phút |
| 300 trang | ~9 phút |
| **500 trang** | **~15 phút** |
| 1000 trang | ~30 phút |

Lần chạy đầu tiên trong một tiến trình mới tốn thêm ~9–13 giây nạp model lần đầu.

## Tắt OCR **không** giúp — đã đo, giả thuyết sai

Tôi ngờ OCR là nút thắt vì `PdfPipelineOptions` mặc định bật nó, và spec §12 vốn đặt OCR là **fallback** có
điều kiện (`min_text_ratio: 0.1`) chứ không phải luôn bật. Nhưng số đo bác bỏ:

| 20 trang | Giây |
|---|---|
| Mặc định (OCR bật) | 34.25 |
| `do_ocr=False` | 37.54 |

Chậm hơn 10%, tức nằm trong nhiễu. Docling **khởi tạo** model OCR nhưng **không chạy** nó trên trang đã có
text layer. Nút thắt là suy luận của **model layout** trên từng trang, và nó chạy dù có OCR hay không.

Kết luận: **đừng đụng vào cấu hình OCR để mong nhanh hơn.** Nếu cần nhanh hơn thật thì hướng là GPU, hoặc
model layout nhỏ hơn, hoặc parse song song nhiều tài liệu bằng nhiều tiến trình.

## Điều này xác nhận quyết định đóng băng `parse_tree` là đúng

| Việc | Thời gian (500 trang) |
|---|---|
| Parse bằng Docling | **~15 phút** |
| Cắt lại chunk từ cây đã đóng băng | **mili-giây** |

Chênh nhau khoảng **sáu bậc độ lớn**. Nếu không đóng băng cây parse, mỗi lần thử một giá trị `max_tokens`
khác sẽ tốn 15 phút — và §13.1 của spec gốc nói rõ tham số đó **phải** hiệu chỉnh bằng cách đo trên corpus
thật, tức là phải thử nhiều lần.

Quyết định D14 hoá ra còn quan trọng hơn lúc chốt nó.
