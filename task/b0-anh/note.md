# Báo cáo hoàn thành — B0 ảnh và tham chiếu

**Status:** completed — 2026-08-20  
**Phạm vi:** 7 ticket trong `task/b0-anh`, adapter version 5, chunk algorithm `section-id-v4`.

## 1. Kết quả

Pipeline hiện trích mọi hình PDF thành PNG, lưu chúng cùng version parse tree và cho chunk tham chiếu lại bằng
`image_id` cùng vị trí `char_start`. Byte ảnh không đi vào domain tree hoặc chunk JSON; chunk text không chứa
base64, hash hay đường dẫn.

```text
source bytes
    ↓
DoclingDocument
    ↓
ParsedDocument
├── tree: DocumentTree, figure chỉ giữ image_id
└── images: {sha256: png_bytes}
    ↓
parse_tree/<doc_id>/vN/
├── tree.json
├── manifest.json
└── images/<sha256>.png
    ↓
chunk_document()
└── Chunk(block_types, image_refs=[{image_id, char_start}])
```

## 2. Xử lý từng ticket

| Ticket | Trạng thái | Thay đổi chính | Kiểm chứng |
|---|---|---|---|
| 01 — cổng parse mang ảnh | Hoàn thành | Thêm `ParsedDocument(tree, images)`; store nhận dictionary ảnh; dictionary rỗng không tạo thư mục. | Test architecture và ingest store. |
| 02 — trích/lưu ảnh | Hoàn thành | Bật ảnh PDF scale 2.0; SHA-256 byte PNG; figure không caption dùng chuỗi cố định; adapter `4 → 5`; fixture có ảnh được sinh lại. | Fixture 9/9 ảnh; ID ổn định; DOCX không trích ảnh; PNG thật nằm trên đĩa. |
| 03 — caption mồ côi | Hoàn thành | Dùng `cref/self_ref` để phân biệt caption đã lấy lại và caption mồ côi; không đoán bbox; caption mồ côi trở lại `text`. | `Hình 2` đúng reading order; stats 8 recovered/1 orphaned; một warning nguyên văn. |
| 04 — `block_types` | Hoàn thành | `block_type` đổi thành danh sách ổn định; artifact cũ được migrate khi nạp; algorithm `v3 → v4`. | Paragraph + list khai đủ hai loại; fixture thật có 14 chunk chứa `list_item`. |
| 05 — gộp hình/bảng | Hoàn thành | Thêm `figure`, `table` vào tập merge hiện có; footnote vẫn đứng riêng; không thêm ngưỡng. | Figure/table nhỏ gộp; bảng lớn vẫn cắt theo hàng; không figure-only chunk dưới 32 token. |
| 06 — image refs | Hoàn thành | Chunk sinh `{image_id, char_start}` theo tọa độ full text; refs không vào `_chunk_id()`. | Hai hình có hai vị trí; đổi image ID không đổi chunk ID; ref sống qua save/load. |
| 07 — tài liệu/đối chiếu | Hoàn thành | Sửa `CONTEXT.md`, thêm ADR 0002, cập nhật báo cáo luồng và ingest sạch PDF thật. | 51 test xanh và các số đo mục 4. |

## 3. Quyết định tối thiểu theo Ponytail

- Không tạo artifact ảnh tầng thứ tư: ảnh thuộc parse version đã sinh ra nó.
- Không tạo kho ảnh dùng chung hoặc reference counting khi corpus chưa cần.
- Không thêm threshold riêng cho figure/table; luật `target_tokens/max_tokens` hiện có đã đủ.
- Không tạo graph entity trong ingest; pha này vẫn tất định và không biết đồ thị.
- Không tạo mapper schema riêng cho artifact cũ; `Chunk.from_dict()` chuyển `block_type` thành danh sách tại đúng
  điểm nạp.
- Caption mồ côi dùng ref Docling sẵn có, không thêm heuristic hình học thứ hai.

## 4. Đối chiếu `nhap-mon-ml`

Nguồn:

```text
C:\Users\ngoco\Downloads\nhap_mon_hoc_may_va_khai_pha_du_lieu_5944.pdf
SHA-256: d5a78c95b7603bffff77d6675c0286beaeb997f5633ac9e598bccb25305d3f71
```

Artifact cũ của riêng `nhap-mon-ml` đã được xóa và ingest lại từ đầu:

```text
artifacts/parse_tree/nhap-mon-ml/v1
artifacts/chunks/nhap-mon-ml/v1
```

| Chỉ số | Kết quả |
|---|---:|
| Thời gian parse sạch | 142,731 giây |
| Tái ingest từ parse cache | 0,649 giây |
| Docling item | 170 |
| Node output | 155 |
| Caption recovered / orphaned | 8 / 1 |
| Fragment stitch | 5 |
| Trang reorder | 1 |
| PNG | 9 file |
| Tổng dung lượng PNG | 821.359 byte |
| Figure node | 9 |
| Image ref | 9 |
| Section | 27 |
| Chunk | 41 |
| Window | 22 |
| Token median / max | 259 / 400 |
| Oversize | 0 |
| Vi phạm char span | 0/41 |
| Figure-only chunk dưới 32 token | 0 |

Các kiểm tra bổ sung:

- tên của cả 9 file PNG khớp SHA-256 nội dung;
- mọi image ref resolve tới file và nằm trong span của chunk chứa nó;
- trang 9 có hai figure node, trong đó hình không caption dùng `[Hình không có chú thích]`; cả hai có ref trong
  một chunk 45 token;
- caption chung `Hình 2: Tập các bức ảnh và các mô tả về chúng.` có trong `normalized_full_text`;
- text node dài nhất 940 ký tự, nên data URI base64 không lọt lại;
- hash tập chunk ID đổi từ baseline `56714bbc…a29911` sang `726dce8b…d3d7a5`.

## 5. Kiểm thử

```text
51 passed, 5 warnings in 25.63s
```

Năm warning đều là deprecation warning của Docling/RapidOCR/SWIG; không có test failure.

## 6. Giới hạn đã chấp nhận

- Đổi image scale có thể đổi mọi `image_id`; chunk ID không đổi theo nếu text và ranh giới chunk giữ nguyên.
- Hai hình đứng riêng, cùng không caption có thể cho vector text giống nhau; chỉ xử lý khi corpus thật chứng minh
  đây là vấn đề truy hồi.
- Nhánh trích ảnh hiện chỉ chạy với PDF; DOCX giữ dictionary ảnh rỗng theo đúng ticket.
- Ingest chưa tạo node/cạnh hình trong graph và chưa gửi ảnh cho mô hình đa phương thức; cả hai ngoài phạm vi B0.
