# Báo cáo triển khai — ba trần token

**Ngày hoàn thành:** 2026-08-21  
**Phạm vi:** F27, F28 và 4 ticket trong `task/b0-tran-bang`  
**Phiên bản sau đợt:** adapter `6`, chunk algorithm `section-id-v6`

## 1. Kết quả

Pipeline giờ phân biệt ba câu hỏi thay vì dùng một con số cho mọi việc:

| Tham số | Mặc định | Vai trò |
|---|---:|---|
| `max_tokens` | 512 | Trần mềm của văn xuôi |
| `max_table_tokens` | 2048 | Trần mềm của bảng và nhóm có bảng |
| `hard_cap_tokens` | 6000 | Trần tuyệt đối của mọi chunk |

Hai feedback ngày 21-08 cũng đã được xử lý:

- F27: `/artifacts/` chỉ ignore output root, không còn che package source cùng tên.
- F28: splitter không cắt nếu ký tự chữ-số có nghĩa tiếp theo là chữ thường; ba ca review có regression test.

Ca chữ cái viết hoa đơn (`J. Smith`, `T. P. E.`) chưa được gom vào F28. Không có luật tất định an toàn để
phân biệt nó với câu kết thúc thật như `Xem chương T.`; thêm heuristic khi chưa có tiêu chí sẽ mở rộng phạm vi
và có nguy cơ tạo lỗi mới.

## 2. Luồng code sau sửa

```text
Settings / biến môi trường
    max_tokens=512
    max_table_tokens=2048
    hard_cap_tokens=6000
             │
             ▼
CLI → IngestDocument.execute()
             │  validate + đưa đủ ba số vào config_hash/manifest
             ▼
chunk_document()
    ├─ văn xuôi quá 512 → ưu tiên tách câu
    ├─ bảng quá 2048   → cắt theo hàng, lặp header, giữ table_id
    ├─ gom block       → candidate có bảng dùng 2048; còn lại dùng 512
    │                    target đóng nhóm vẫn là 256
    └─ mọi mảnh        → kiểm cuối ở 6000
                         ├─ tìm khoảng trắng trong 10% cuối trước trần
                         └─ không có: cắt đúng trước trần tại cụm ký tự
```

Các file chịu trách nhiệm:

| File | Trách nhiệm sau sửa |
|---|---|
| `src/doc2roadmap/config.py` | Khai báo mặc định của ba trần |
| `application/use_cases/ingest_document.py` | Validate, hash config, manifest và truyền xuống domain |
| `presentation/cli/main.py` | Nối Settings vào use case |
| `domain/chunking.py` | Chọn trần theo loại, trần gom và cắt cứng cuối luồng |
| `infrastructure/text/sentence_splitter.py` | Guard chữ thường của F28 |

Adapter Docling không đổi vì cây parse, reading order và schema node không đổi. `section-id-v5` tăng đúng một
bậc thành `section-id-v6` vì semantics chunk/config thay đổi.

## 3. Trần bảng và câu dẫn

`_table_parts()` chỉ dùng `max_table_tokens`. Trong hàng đợi gộp, nếu pending hoặc block mới là bảng thì
candidate được so với 2048; nhóm không có bảng vẫn so với 512. Sau khi thêm block, nhóm vẫn đóng ngay khi đạt
`target_tokens=256`, vì vậy bảng nhỏ không hút văn xuôi không liên quan cho tới 2048.

Bảng vượt 2048 vẫn cắt theo hàng như trước. Mỗi mảnh lặp hai dòng header và giữ cùng `table_id`; thứ bị cắt là
đơn vị truy hồi, không phải ma trận hàng/cột trong parse tree.

## 4. Trần cứng

Trần cứng chạy sau splitter và row splitter, nên cả câu không có boundary lẫn một hàng bảng dị thường đều có
đường thoát. Mỗi mảnh cưỡng bức:

- có `token_count <= hard_cap_tokens`;
- mang `oversize_reason="hard_cap_forced_split"`;
- tăng `split_index` tuần tự;
- có span liền mạch, ráp lại đúng chuỗi gốc;
- không bắt đầu bằng Unicode combining mark;
- giữ `table_id` ở mọi mảnh nếu nguồn là bảng.

Luật chỉ nhìn lùi trong 10% cuối trước điểm trần, không tìm whitespace phía sau. Nếu một cụm ký tự đơn lẻ đã
lớn hơn cả trần thì code báo lỗi tường minh, vì không có cách chia mà vẫn đồng thời giữ cụm ký tự và I20.

## 5. Test hồi quy

Các test mới khóa trực tiếp:

- đổi từng trần tạo chunk artifact version/config hash mới, parse tree vẫn tái dùng;
- bảng 11 hàng × 6 cột còn một chunk;
- câu dẫn + bảng 30 hàng ở cùng chunk;
- bảng nhỏ không hút văn xuôi đến 2048;
- văn xuôi khoảng 700 token vẫn dùng trần 512;
- bảng trên trần vẫn row-split, lặp header và giữ một ID;
- văn xuôi không boundary và hàng bảng quá dài đều bị chặn bởi hard cap;
- tiếng Việt NFD không vỡ dấu, CJK không-space vẫn cắt được;
- whitespace chỉ được chọn trong cửa sổ 10% trước trần;
- block dưới trần không bị gắn lý do;
- ba ví dụ F28 đều trả đúng hai câu.

Test F28 và các test trần được chạy trước phần triển khai; lượt đầu đỏ ngay ở collection vì production chưa có
hằng/lối cắt mới. Sau sửa, toàn bộ suite có **85 passed**, chỉ còn 5 deprecation warning từ dependency.

## 6. Nghiệm thu PDF bảng thật `xstk-ch3-1.pdf`

PDF 59 trang, SHA-256:

```text
c265d409800af5515ba6e71408a9998020b38670369dfec4a5c01246e07fd20c
```

Kết quả ingest sạch:

| Chỉ số | Giá trị |
|---|---:|
| Section / chunk / window | 68 / 132 / 60 |
| Docling item / node giữ | 992 / 724 |
| Table node / table ID phân biệt | 51 / 48 |
| Table ref / ID ref phân biệt | 51 / 48 |
| Ref thiếu / dangling | 0 / 0 |
| Văn xuôi: chunk / median / max | 93 / 236 / 398 |
| Có bảng: chunk / median / max | 39 / 286 / 535 |
| Chunk bảng trên 512 | 2 (525 và 535) |
| Chunk bảng có thêm ngữ cảnh | 39/39 |
| Chunk vượt trần áp dụng / hard cap | 0 / 0 |
| Lỗi char span | 0/132 |
| Ảnh / image ref | 5 / 5 |

Đối chứng cùng parse tree nhưng ép trần bảng cũ 512:

| | Trần cũ 512 | Trần mới 2048 |
|---|---:|---:|
| Tổng chunk | 134 | 132 |
| Chunk chứa bảng | 40 | 39 |
| Chunk bảng có ngữ cảnh loại khác | 38 | 39 |
| Chunk chỉ có bảng | 2 | 0 |

Hai chunk chỉ-bảng cũ ở trang 9 và 16. Kết quả mới cho thấy một bảng không còn bị cắt và câu dẫn được giữ
cùng bảng. Kiểm tra bằng mắt các trang 4, 5, 44 và 50 trên bản render xác nhận Docling đang xử lý bảng thật,
gồm bảng nhiều hàng và bảng có header phức tạp, không phải text fixture giả.

Corpus này có bảng tối đa 12 hàng và chunk bảng lớn nhất 535 token. Nó đủ xác nhận 512 cắt/gom quá sớm, nhưng
**chưa** chứng minh 2048 tối ưu cho chất lượng retrieval. Con số 2048 phải được hiệu chỉnh khi có corpus bảng
lớn hơn và phép đo retrieval.

## 7. Đối chiếu không thoái lui

Đã xóa đúng hai artifact cũ của `nhap-mon-ml`, ingest lại hoàn toàn từ PDF nguồn rồi kiểm:

| Chỉ số | Kết quả |
|---|---:|
| Section / chunk / window | 27 / 41 / 22 |
| Nối qua trang / trang reorder | 5 / 1 |
| Ảnh / ref resolve | 9 / 9 |
| Token median / max | 259 / 400 |
| Oversize reason | 0 |
| Lỗi char span | 0/41 |
| Adapter / algorithm | 6 / `section-id-v6` |

Hash tập 41 chunk ID vẫn đúng baseline:

```text
726dce8b6c9c1bc2452f9ff409cc9d83f9446421ac1e666fdc4557c6b3d3d7a5
```

Fixture `tests/fixtures/smoke.docx` cũng đi qua integration ingest thật: đúng một `table_ref`, trỏ vào markdown
`| Name | Value |`.

## 8. Giới hạn và yêu cầu downstream

- Bảng vượt 2048 có thể vẫn để câu dẫn lại phía trước vì row-split chạy sau bước gom. Đây là giới hạn được spec
  chấp nhận; đảo thứ tự hai pha là thay đổi lớn hơn phạm vi ticket.
- Bước embedding sau này phải đếm lại token bằng tokenizer của chính model ngay trước khi gọi API. Tokenizer
  Gemma ở ingest là bộ đếm ổn định cho artifact, không phải cam kết tuyệt đối với model khác.
- Phân bố thiết kế có hai miền: văn xuôi quanh 256 và bảng được phép tới 2048. Trên `xstk-ch3-1`, hai miền còn
  chồng nhau (median 236/286) vì bảng thật chưa đủ lớn; không được diễn giải nó thành bằng chứng 2048 tối ưu.

## 9. Quyết định tối giản theo Ponytail

- Dùng `unicodedata` và binary search trong standard library; không thêm dependency grapheme/config mới.
- Chỉ chạy cắt cứng trên đường ngoại lệ; chưa cache boundary khi chưa có profiling cho thấy đây là hot path.
- Không đổi adapter/schema parse vì yêu cầu chỉ thuộc tầng chunk.
- Không sửa lead của bảng trên 2048 và không đoán luật chữ cái viết hoa đơn; cả hai đều có tradeoff thật và đã
  được ghi rõ thay vì che bằng abstraction dự phòng.
