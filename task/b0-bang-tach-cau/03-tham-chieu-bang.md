# 03 — Tham chiếu bảng có vị trí trên chunk

**What to build:** Từ một chunk, truy ra được **những bảng nằm trong nó và chỗ chúng đứng** — y hệt cách chunk
đã trỏ tới hình từ đợt trước. Đây là mảnh cuối để bước trích khái niệm chạy song song ở pha sau dựng được node
loại bảng và vẽ cạnh từ khái niệm tới một bảng cụ thể.

Hình dạng **đối xứng từng điểm** với tham chiếu hình: định danh cộng vị trí ký tự, dùng chung hệ toạ độ với vị
trí ký tự sẵn có của chunk. Không phát sinh khái niệm toạ độ mới.

Và như hình, tham chiếu bảng chứa **định danh**, không chứa đường dẫn hay bản sao nội dung.

## Chỗ tinh vi nhất: bảng bị cắt thì các mảnh phải cùng định danh

Bảng vượt trần bị cắt theo hàng thành nhiều chunk. Hiện **không gì ghi lại rằng các mảnh ấy vốn là một bảng** —
ba chunk trông y hệt ba đoạn markdown không liên quan.

Sau ticket này, **mọi mảnh mang cùng một định danh bảng**, khác nhau ở vị trí ký tự. Bước trích khái niệm nhờ
đó ghép lại được: ba chunk cùng định danh bảng là ba mảnh của một bảng, không phải ba bảng.

Định danh bảng sinh từ **node**, mà cắt theo hàng là chia một node thành nhiều mảnh — nên các mảnh **tự nhiên**
cùng định danh. Đây không phải việc phải làm thêm, mà là việc phải **kiểm**, vì một bản triển khai vô ý tính
lại định danh cho từng mảnh sẽ phá nó mà không ai thấy.

## Quyết định trung tâm, kế thừa từ đợt hình

**Tham chiếu bảng không tham gia khoá băm định danh chunk.** Đây là mở rộng của quyết định đã ghi trong ADR
0002, không phải quyết định mới — ticket `06` sẽ cập nhật ADR để nói "hình và bảng" thay vì chỉ "hình".

**Blocked by:** 01 — cần trường tham chiếu bảng đã tồn tại trên chunk. 02 — cần định danh bảng trên node.

**Status:** completed — 2026-08-21

- [x] Chunk mang danh sách tham chiếu bảng, mỗi tham chiếu gồm định danh bảng và vị trí ký tự
- [x] Vị trí dùng cùng hệ toạ độ với vị trí ký tự sẵn có của chunk, tức offset trong chuỗi văn bản đầy đủ
- [x] Tham chiếu chứa **định danh**, không chứa đường dẫn và không chứa bản sao hàng cột
- [x] **I18** — bảng bị cắt theo hàng thành nhiều chunk ⇒ mọi mảnh mang **cùng** định danh bảng, khác vị trí
- [x] **I19** — đổi tập tham chiếu bảng mà giữ nguyên phần văn bản ⇒ định danh chunk **không đổi**
- [x] Chunk gộp chứa một bảng và một đoạn văn ⇒ khai đúng cả hai loại khối, và tham chiếu trỏ đúng chỗ bảng
- [x] Có test: cắt chuỗi tại vị trí tham chiếu ra đúng dòng đầu của bảng markdown
- [x] Có test: chunk không chứa bảng nào ⇒ danh sách rỗng
- [x] Có test ở tầng ingest: tham chiếu bảng sống sót qua vòng lưu rồi nạp lại
- [x] Ingest fixture DOCX có bảng và kiểm tham chiếu trỏ đúng vị trí trong văn bản
- [x] Ingest lại tài liệu thử nghiệm: **không có bảng nên danh sách rỗng ở mọi chunk**, và tập định danh chunk 
      vẫn không đổi
