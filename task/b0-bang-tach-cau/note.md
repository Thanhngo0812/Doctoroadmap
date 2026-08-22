# Báo cáo triển khai — bảng và tách câu toàn cầu

**Ngày hoàn thành:** 2026-08-21  
**Phạm vi:** 6 ticket trong `task/b0-bang-tach-cau`  
**Phiên bản sau đợt:** adapter `6`, chunk algorithm `section-id-v5`

## 1. Kết quả

Đợt này hoàn thành hai nhánh độc lập:

1. Bảng có `table_id` băm từ ma trận ô đã chuẩn hoá và chunk có `table_refs` kèm offset ký tự.
2. Bộ tách câu đổi thành `UnicodeSentenceSplitter`, nhận các dấu kết câu chính ngoài Latin và bảo vệ các viết
   tắt common Latin/tiếng Việt bằng dữ liệu.

Đồng thời `oversize: bool` được thay bằng `oversize_reason`; splitter không tìm thấy boundary trên block vượt
trần sẽ ghi warning có trang hoặc section vào chunk manifest và CLI.

## 2. Thay đổi theo ticket

| Ticket | Kết quả chính | Bài kiểm |
|---|---|---|
| 01 — schema v5 | Thêm `table_refs`, `oversize_reason`; migrate artifact cũ `oversize=false`, báo rõ với `oversize=true`; bump v5 | JSON có field rỗng/null, legacy load |
| 02 — định danh bảng | Adapter giữ `table_rows`, tính SHA-256 từ cell đã normalize; bump adapter 6 | cùng cell khác markdown cùng ID, đổi cell đổi ID, DOCX thật có ID |
| 03 — tham chiếu bảng | `TableRef(table_id, char_start)` dùng offset full text; fragment row-split giữ một ID; ref ngoài chunk hash | I18, I19, round-trip store, DOCX ingest thật |
| 04 — tách câu | Đổi tên splitter; Unicode punctuation; abbreviation thành data; không thêm dependency | 10 ca bắt buộc + Arabic full stop, Khmer, ellipsis, no-punctuation |
| 05 — cảnh báo | Hai reason tách biệt cho row bảng và splitter; warning kèm vị trí vào manifest/CLI | I17, row không warning, block cắt được không warning |
| 06 — tài liệu/đối chiếu | Mở rộng ADR 0002, CONTEXT, invariant I15/I17, hướng dẫn test và report | ingest sạch PDF + DOCX fixture, full suite |

## 3. Hình dạng dữ liệu

Node bảng trong parse tree:

```json
{
  "node_type": "table",
  "table_rows": [["Name", "Value"], ["A", "1"]],
  "table_id": "<sha256>"
}
```

Chunk chứa bảng:

```json
{
  "table_refs": [{"table_id": "<sha256>", "char_start": 1234}],
  "oversize_reason": null
}
```

`table_refs` và `image_refs` đều đứng ngoài `_chunk_id()`. Nội dung hàng cột không bị sao chép sang chunk:
markdown đã nằm trong `text`, còn ma trận vẫn ở parse tree.

Hai lý do vượt trần ban đầu:

```text
table_row_exceeds_max_tokens
sentence_splitter_no_boundary
```

Artifact schema cũ có `oversize=false` được nạp thành `oversize_reason=null`. Với `oversize=true`, loader báo
phải ingest lại vì artifact cũ không chứa dữ liệu đủ để suy ra nguyên nhân; không tự gán một lý do giả.

## 4. Tách câu

`UnicodeSentenceSplitter` vẫn là regex tất định và giữ masking cùng độ dài, nên `TextSpan` luôn trỏ vào chuỗi
gốc. Không thêm thư viện.

- Dấu cần whitespace hoặc cuối chuỗi: `.`, `!`, `?`, `…`.
- Dấu không cần whitespace: `。`, `！`, `？`, danda `।/॥`, `؟/۔`, `។/៕`.
- Common Latin data gồm danh xưng, `e.g.`, `i.e.`, `et al.`, `cf.`, `vs.` và ký hiệu học thuật
  `Fig./Eq./Sec./Vol./No./p./pp.`.
- Bộ tiếng Việt giữ nguyên `PGS./ThS./TS./GS./TP.`.
- Dấu thập phân giữa hai chữ số vẫn được che tạm.

## 5. Đối chiếu fixture DOCX có bảng

`tests/fixtures/smoke.docx` đi qua parser và ingest thật:

- đúng một node bảng;
- `table_rows = [["Name", "Value"], ["A", "1"]]`;
- `table_id` dài 64 ký tự hex;
- đúng một `table_ref` sau round-trip lưu/nạp;
- `normalized_full_text[char_start:]` bắt đầu bằng `| Name | Value |`.

## 6. Đối chiếu PDF `nhap-mon-ml`

Đã xoá đúng hai artifact cũ của `nhap-mon-ml` rồi ingest lại từ đầu từ:

```text
C:\Users\ngoco\Downloads\nhap_mon_hoc_may_va_khai_pha_du_lieu_5944.pdf
```

| Chỉ số | Sau đợt |
|---|---:|
| Adapter / chunk algorithm | `6` / `section-id-v5` |
| Node giữ / item tổng | 155 / 170 |
| Section / chunk / window | 27 / 41 / 22 |
| Cấp section, không tính root | 4 |
| Nối câu qua trang / trang reorder | 5 / 1 |
| Ảnh / image ref resolve | 9 / 9 |
| Table node / table ref | 0 / 0 |
| Warning splitter bó tay | 0 |
| Chunk có oversize reason | 0 |
| Token min / median / max | 18 / 259 / 400 |
| Vi phạm char span | 0 / 41 |
| Tái ingest từ parse cache | 0,949 giây |

Hash tập 41 chunk ID trước và sau đều là:

```text
726dce8b6c9c1bc2452f9ff409cc9d83f9446421ac1e666fdc4557c6b3d3d7a5
```

Vì vậy tập định danh chunk giữ nguyên tuyệt đối như dự đoán của spec.

## 7. Kiểm thử

```text
71 passed, 5 dependency deprecation warnings
```

Năm warning đến từ Docling/RapidOCR/SWIG; không có test failure và không có warning
`sentence_splitter_no_boundary` trong artifact PDF thật.

## 8. Quyết định tối giản theo Ponytail

- Dùng `hashlib`, `json`, `re` của standard library; không thêm dependency.
- Không tạo repository/file artifact riêng cho bảng vì markdown và parse tree đã chứa đủ dữ liệu.
- Tái dùng `structure_warnings` làm kênh warning document → manifest → CLI; không dựng hệ event mới.
- Không giữ song song `oversize` và `oversize_reason`, tránh hai nguồn sự thật có thể lệch nhau.
- Không thêm language detector; các luật punctuation/abbreviation tất định hiện đủ tiêu chí nghiệm thu.
