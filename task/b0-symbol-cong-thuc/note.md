# Báo cáo triển khai Symbol, công thức và lọc tiêu đề

**Status:** completed — 2026-08-22  
**Phạm vi:** 7/7 ticket trong `task/b0-symbol-cong-thuc`  
**Version:** adapter `7`, chunk algorithm `section-id-v7`

## Kết quả chính

- Thêm fixture Docling thật `xstk-ch3-1.json`: 992 item, 264 formula, 51 table, 5 picture; round-trip giữ
  992/992 item và 263 raw formula.
- PDF Symbol được tra về Unicode ở adapter, kể cả table cell/raw; DOCX không bị đụng. Parse stats ghi
  `symbol_characters_mapped`, phần PUA không có đích Unicode sinh warning có count.
- Luật đọc content là `text` rồi `orig`; chỉ cả hai rỗng mới drop. Formula dùng marker `[formula]`, raw và
  SHA-256 `formula_id` ở parse tree.
- `FormulaRef(formula_id, char_start)` sống qua JSON store và đứng ngoài hash `chunk_id`; formula là loại
  mergeable nên không tạo hàng trăm chunk nhỏ.
- Marker hình không caption đổi từ câu tiếng Việt sang `[figure]`.
- Warning lặp được gom ổn định thành `warning ×N`; warning có raw như orphan caption/heading vẫn giữ từng ca.
- Heading không đánh số bị hạ khi text xuất hiện ít nhất hai lần trong body; heading bắt đầu bằng bullet/dash
  Unicode cũng bị hạ. Heading đánh số được miễn luật lặp.

## Luồng formula

```text
Docling item
  text rỗng + orig có dữ liệu
        ↓
DocumentNode(text="[formula]", raw_text=<orig>, formula_id=SHA-256(normalized raw))
        ↓
normalized_full_text chứa đúng marker tại reading order
        ↓
Chunk.formula_refs += {formula_id, char_start}
```

Raw không vào text embed và ref không vào `_chunk_id()`. Vì formula mới khôi phục từng làm nhánh nhận diện cột
PDF đổi hành vi, adapter coi formula như content island khi đo layout/stitch; formula vẫn được sort theo bbox và
giữ marker đúng reading order. Guard này khôi phục đúng 1 trang reorder và đủ 5 stitch của tài liệu học máy.

## Adobe Symbol và giới hạn có chủ đích

Bảng tĩnh lấy từ Unicode Adobe Symbol mapping, gồm 160 mã có đích Unicode ngoài PUA. Các corporate-use glyph
fragment không có ký tự đọc tương đương được giữ nguyên và cảnh báo, thay vì đoán. Nguồn:
`https://www.unicode.org/Public/MAPPINGS/VENDORS/ADOBE/symbol.txt`.

Trên `xstk-ch3-1`, adapter sửa 2.368 lần trên các surface được lưu. Text chunk còn hai `U+F0E7`; parse tree
có 78 lần nếu tính cả text/raw/table surface và ghi đúng `remaining_private_use: 78`. Đây là trạng thái I22
hợp lệ: không còn lỗi PUA im lặng.

## Đối chiếu PDF 20 trang

| Chỉ số | v1 | v2 |
|---|---:|---:|
| Section / chunk / window | 27 / 41 / 22 | 27 / 41 / 22 |
| Formula node / ref | 0 / 0 | 1 / 1 |
| Image ref | 9 | 9 |
| Stitch / reorder | 5 / 1 | 5 / 1 |
| PUA trong chunk | 0 | 0 |
| Span sai / vượt hard cap | 0 / 0 | 0 / 0 |

39/41 `chunk_id` giữ nguyên. Đúng hai ID đổi: chunk nhận `[formula]` và chunk đổi marker `[figure]`; không có
thay đổi thứ ba. Cây section vẫn sâu bốn level. Hash tập ID v2:
`14d7bcbf3eda0e070342408834b3d9218002cb3086cd151c8aa511768e961ccc`.

## Đối chiếu PDF 59 trang

| Chỉ số | v1 | v2 |
|---|---:|---:|
| Node giữ | 724 | 987 |
| Section / chunk / window | 68 / 132 / 60 | 43 / 126 / 40 |
| Formula node / marker / ref | 0 / 0 / 0 | 263 / 263 / 263 |
| Table node / ref | 51 / 51 | 51 / 51 |
| Image ref | 5 | 5 |
| PUA trong chunk | 653 | 2, có warning |
| Warning | 266 | 29 |
| Span/ref sai / vượt hard cap | — | 0 / 0 / 0 |

Section giảm đúng 25: 23 bullet cùng `Chú ý .` và `Trong đó:`. Mọi formula ref trỏ đúng marker và ID node;
mọi table ref còn nguyên. Hash tập 126 chunk ID v2:
`4ee6218d79b1d67e9d42a79fa958eed8842ee8e9a2c477157253123f03316040`.

## Test và bằng chứng falsifiable

Các guard mới được chạy trên code v6 trước implementation và đỏ ở đúng lỗi: Symbol chưa map, parse stat thiếu,
raw fallback bị drop, 263 formula mất, heading giả còn là section, schema chưa có `FormulaRef`. Sau sửa:

```text
97 passed, 5 dependency deprecation warnings
```

- I22: fixture thật kiểm PUA chunk phải có warning tương ứng.
- I23: node `text=""`, `orig!=""` được giữ; cả hai rỗng vẫn bị drop.
- I24: đổi hai `formula_id` nhưng giữ marker/text cho cùng `chunk_id`.
- 300 warning lặp thành một dòng; rare/raw warnings không mất.
- Storage round-trip giữ `formula_refs`; artifact cũ thiếu field mới vẫn load với danh sách rỗng.

## Tệp thay đổi

- Runtime: `domain/models.py`, `domain/chunking.py`, `infrastructure/parsing/docling_parser.py`.
- Test/fixture: loader dùng chung, fixture xstk, adapter/domain/application tests.
- Tài liệu: ADR 0002, `CONTEXT.md`, báo cáo luồng, fixture README và toàn bộ trạng thái ticket.

Không thêm dependency, service hay abstraction mới. Hai PNG render spot-check trang 5–6 đã được xóa sau khi
xác nhận glyph tổng, formula và bullet khớp nội dung PDF.
