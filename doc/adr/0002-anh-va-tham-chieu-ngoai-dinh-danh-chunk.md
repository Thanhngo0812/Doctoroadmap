---
status: accepted
---

# Hình, bảng, công thức và tham chiếu ngoài định danh chunk

Ingest phải cho chunk trỏ tới hình, bảng và công thức cụ thể mà không đưa chi tiết lưu trữ hoặc metadata tham
chiếu vào định danh bằng chứng. Hình cần lưu byte riêng; bảng đã có nội dung markdown trong text và cấu trúc
hàng cột trong cây parse; công thức PDF giữ nội dung thô trong cây vì reading order glyph chưa đủ tin cậy để
embed như văn xuôi.

## Decision

Các quyết định sau tạo thành một khối, không áp dụng riêng lẻ:

1. **Hình là sản phẩm của parse.** PNG nằm trong thư mục của chính version parse tree đã sinh ra nó; cây chỉ
   giữ `image_id`, không chứa base64.
2. **Định danh nội dung được tính ở adapter.** Hình dùng SHA-256 của byte PNG; bảng dùng SHA-256 của ma trận ô
   đã chuẩn hoá; công thức dùng SHA-256 của nội dung thô đã chuẩn hoá. Cả ba không dùng trang, reading order hay
   đường dẫn.
3. **`image_refs`, `table_refs` và `formula_refs` đứng ngoài khoá băm chunk.** Chunk lưu định danh cùng
   `char_start`, nhưng [công thức định danh chunk của ADR 0001](./0001-dinh-danh-tat-dinh.md) vẫn chỉ dùng nội dung
   text và section.
4. **Ingest không tạo thực thể đồ thị.** Nó chỉ parse, lưu ảnh và sinh tham chiếu tất định; bước trích khái niệm
   tự quyết định sau này có dựng node/cạnh cho hình hoặc bảng hay không.
5. **Cấu trúc hàng cột ở nguyên trong cây parse.** Chunk chỉ giữ markdown đọc được và tham chiếu về `table_id`;
   không nhân đôi ma trận ô sang artifact chunk.
6. **Dấu vết vào văn bản, nội dung ra chỗ khác.** Nội dung phi văn xuôi để lại marker trung tính ngôn ngữ
   (`[figure]`, `[formula]`) tại đúng vị trí; byte ảnh hoặc raw công thức nằm ngoài text embed.

Tra bảng Adobe Symbol cho PDF là một phỏng đoán có kiểm soát: Docling không cung cấp font ở provenance, nhưng
ký tự `U+F000–U+F0FF` không có nghĩa văn bản hợp lệ để giữ nguyên. Adapter ánh xạ toàn bộ entry có đích
Unicode ngoài PUA, ghi số ký tự đã sửa và cảnh báo số glyph corporate-use/không biết còn lại. DOCX không đi qua
phỏng đoán này.

Độ phân giải trích ảnh được ghim ở `2.0` và tham gia parse config hash. Đổi scale buộc parse lại.

## Considered Options

**Nhét ảnh vào `DocumentTree` dưới dạng base64.** Bị loại vì làm JSON miền phình lớn, buộc mọi consumer cây
phải tải byte không dùng và trộn dữ liệu nhị phân vào tầng miền.

**Kho ảnh toàn cục dùng chung giữa tài liệu.** Bị loại dù có thể khử trùng lặp: ảnh không còn chủ sở hữu rõ
ràng, nên xoá hoặc version một tài liệu phải giải bài toán reference counting chưa cần ở B0.

**Lưu đường dẫn trong chunk.** Bị loại vì cách bố trí thư mục là chi tiết hạ tầng; chuyển kho hoặc đổi root sẽ
buộc sinh lại chunk dù nội dung không đổi.

**Đưa `image_refs` vào khoá băm chunk.** Bị loại vì scale hoặc encoder PNG làm đổi byte và `image_id`, kéo gãy
bằng chứng text dù văn bản hoàn toàn không đổi.

**Dựng tầng lưu trữ riêng cho bảng để đối xứng với hình.** Bị loại vì nội dung bảng đã nằm trong chunk dưới
dạng markdown và ma trận ô đã nằm trong cây parse. Tầng mới chỉ nhân đôi dữ liệu mà không thêm khả năng.

**Đưa raw công thức vào text chunk.** Bị loại vì thứ tự glyph trong PDF bị xáo trộn; trên tài liệu đối chiếu nó
thêm 8.280 token không đọc được vào corpus. Marker giữ vị trí, còn `raw_text` và `formula_id` cho phép consumer
sau xử lý lại mà không làm bẩn embedding.

**Dựng node hình trong ingest.** Bị loại vì kéo khái niệm node/cạnh đồ thị vào một pha đang hoàn toàn tất định
và chưa có quyết định về vai trò hình trong topo, chu trình hoặc stage.

## Consequences

- Parse artifact sở hữu cả `tree.json` và `images/<image_id>.png`; ảnh sống và chết cùng version parse.
- Đổi scale làm đổi mọi `image_id` có byte PNG thay đổi. Điểm yếu này được chấp nhận vì `image_refs` không nằm
  trong khoá băm chunk, nên riêng thay đổi ảnh không làm đổi `chunk_id` khi text và ranh giới chunk giữ nguyên.
- Chunk text chỉ chứa caption hoặc marker `[figure]`; không chứa hash, path hay base64.
- Chunk chứa `table_refs` đối xứng với `image_refs`; mọi mảnh khi cắt cùng một bảng theo hàng giữ cùng
  `table_id`.
- Công thức để marker `[formula]` trong text và giữ raw ở parse tree; `formula_refs` đối xứng với hai loại ref
  còn lại và không tham gia `chunk_id`.
- Consumer cần cấu trúc hàng cột đọc node bảng trong parse tree theo `table_id`; không phân tích lại markdown.
- Consumer muốn tái dựng công thức đọc node parse theo `formula_id`; B0 chưa hứa chuyển raw glyph thành LaTeX.
- Hệ thống chưa khử trùng lặp ảnh giữa tài liệu và chưa đưa ảnh thô cho mô hình đa phương thức. Chỉ bổ sung khi
  có nhu cầu đo được và có quyết định riêng về sở hữu hoặc chi phí mô hình.
