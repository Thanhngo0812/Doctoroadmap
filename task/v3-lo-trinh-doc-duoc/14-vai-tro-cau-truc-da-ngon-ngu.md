# 14 — Vai trò vùng và cấu trúc mục không phụ thuộc ngôn ngữ

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), nguyên tắc đa ngôn ngữ, R1, R2 · **Ai:** nhân viên ·
**Phụ thuộc:** 03; làm tiếp ngay trên phần vé 04 đang dở · **Chi phí mô hình:** một lời gọi Gemini mỗi tài liệu cho nhãn nghĩa
(≈ 0,001–0,01 USD)

**Trạng thái:** chờ giao. **Thay** phần từ khoá của vé 03 và vé 04.

## Vì sao
Rà soát 2026-09-26: vai trò vùng (vé 03) và cấu trúc mục (vé 04) dựa vào danh sách từ tiếng Việt/tiếng Anh — `ROLE_PATTERNS`, tìm
chương đầu bằng "chương|chapter", `_MATH_CHAPTER` "Chapter", `_MATH_EXERCISES` "Exercises", `_MATH_RESULT` "định lý/ví dụ…",
`_MATH_PAGE_HEADING` "Exercises". Với sách tiếng Pháp, Trung, Nga…, các luật này lặng lẽ không chạy: bài tập, lời nói đầu, chỉ mục
lại thành nơi dạy; kết quả đánh số lại mở mục mới.

Thêm một lỗi: cờ "sách toán" bật khi chỉ cần **một** tiêu đề khớp `\d+[A-Z]`. Một tiêu đề kiểu "2D convolution" sẽ biến mọi mục
"n.m Tên" của sách thành khối; doc-1 ("1.1 Tập hợp") và nhap-mon-ml ("1.1 Các khái niệm và bài toán học cơ bản") có mục thật khớp
`_MATH_RESULT`, hôm nay chỉ an toàn vì không có tiêu đề nào bật cờ.

## Việc cần làm

### A. Lớp cấu trúc (tất định, trong A2)
- **Chương** = chuỗi tiêu đề cấp cao cùng tiền tố, số tăng dần (`_chapter_sequences`). Bỏ regex "chương|chapter" và `_MATH_CHAPTER`.
  `mo_dau` = phần trước phần tử đầu của chuỗi chương.
- **Mục số + chữ:** số chương đi liền một chữ in hoa Unicode (`Lu`), và phải thành chuỗi A, B, C… trong cùng chương, ít nhất ba tiêu
  đề. Một tiêu đề lẻ không bật chế độ này.
- **Kết quả đánh số là khối:** họ tiêu đề cùng tiền tố (kể cả tiền tố rỗng như "3.36 …") có số chạy dày, không đánh lại ở mỗi mục
  cùng cấp (chỉ đánh lại theo chương), và thân ngắn → khối trong mục đang mở. Ngưỡng (số phần tử mỗi chương, độ dài thân) ghi trong
  config; báo giá trị đo được trên kho phát triển. Bỏ `_MATH_RESULT`.
- **Tiêu đề Docling coi là page_header:** chỉ phục hồi khi nó chứa đúng mã của một mục số + chữ đã biết ("3C …", "… 3B"). Bỏ từ
  "Exercises" trong `_MATH_PAGE_HEADING`.
- **`de_cuong`:** `_toc_runs`; tiêu đề lặp lại ở đầu nhiều mục. **`cuoi_sach`:** phần sau chương cuối mà đa số dòng là mục từ ngắn
  kết thúc bằng số trang, hoặc mang mẫu trích dẫn (năm bốn chữ số, tên viết tắt).
- Mục bài tập đóng lại khi gặp tiêu đề cùng cấp hoặc cao hơn kế tiếp.

### B. Lớp nhãn nghĩa (một lời gọi Gemini mỗi tài liệu, bước riêng sau A2)
- Tiêu đề lớp A chưa quyết thì mô hình gán vào `noi_dung` · `bai_tap` · `de_cuong` · `mo_dau` · `hanh_chinh` · `cuoi_sach`. Đầu vào
  mỗi tiêu đề: tiêu đề, đường dẫn mục, vị trí, vài dòng đầu. Khung prompt tiếng Anh, dữ liệu giữ ngôn ngữ của tài liệu (theo
  `prompts/README.md`).
- Kiểm: mọi tiêu đề nhận đúng một nhãn trong tập; thiếu hoặc lỗi → `noi_dung` kèm cảnh báo. Lớp B không ghi đè kết quả lớp A.
- Ghi version chunks mới như `refresh_chunk_roles` (không đổi ID, text, offset); cache theo (version chunks, prompt hash); qua
  `SpendGuard`; có `plan()` cho `--dry-run`.

### C. Gỡ bỏ
`ROLE_PATTERNS`, `heading_role` theo mẫu, regex tìm chương, `_MATH_CHAPTER`, `_MATH_EXERCISES`, phần từ của `_MATH_RESULT`, từ
"Exercises" trong adapter. Không thêm danh sách từ của ngôn ngữ nào.

## Tệp liên quan
`domain/chunking.py`, `infrastructure/parsing/docling_parser.py`, `application/use_cases/ingest_document.py` (`refresh_chunk_roles`),
use case mới cho nhãn nghĩa, prompt mới trong `prompts/`.

## Nghiệm thu
- Test lớp A trên cây tổng hợp ở ba ngôn ngữ ngoài vi/en, gồm một chữ viết không Latin và một chữ viết không cách từ (ví dụ
  "Chapitre 1 … Exercices … Index", "第1章 … 练习 … 索引", "Глава 1 … Упражнения"): chương, mục số + chữ, kết quả đánh số, mục lục,
  chỉ mục được nhận đúng mà trong mã không có từ nào của các ngôn ngữ đó.
- Test một tiêu đề lẻ "2D convolution" không bật chế độ sách toán; mục kiểu "1.1 Tập hợp" của doc-1 vẫn là mục.
- Test lớp B với mô hình giả: gán nhãn, kiểm tập đóng, thiếu nhãn → `noi_dung`, không ghi đè lớp A.
- **Tôi kiểm:**
  - vai trò trên doc-1, doc-2, doc-6, nhap-mon-ml ít nhất đúng như bản đọc ở vé 03;
  - doc-2 còn khoảng 161 chunk `bai_tap`, và "Photo Credits" thành `cuoi_sach`;
  - ID và text chunk của doc-1, xstk, doc-4 không đổi (so hash, không đọc nội dung tập giữ lại);
  - `--dry-run` trên sáu tài liệu: không stage tốn tiền nào chuyển sang "sẽ chạy" vì vé này;
  - khi có T19: chạy trên tài liệu thật ngôn ngữ thứ ba và đọc vai trò.
