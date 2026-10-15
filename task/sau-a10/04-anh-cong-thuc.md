# SA-04 — Ảnh công thức

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 5; [báo cáo bài giảng](../../report/nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md),
mục 2 và 4.6.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không, làm ngay được · **Trạng thái:** ready-for-agent

## Vì sao

Công thức đứng riêng đã bị thay bằng `[formula]` trong chữ chunk. doc-1 có 81% khái niệm bị ảnh hưởng ở chunk dạy, xstk có 50%. Cây parse vẫn giữ
`page`, `bbox` và chữ thô cho cả 562 công thức của doc-1. Chủ dự án chốt cách làm: cắt sẵn ảnh vùng công thức ở bước tải tài liệu, để web hiện
đúng pixel của sách.

## Cần làm

**Bước sau parse:**
- Đọc nút công thức của cây parse: `formula_id`, trang, `bbox` (toạ độ điểm PDF, gốc dưới trái).
- Vẽ trang PDF rồi cắt ảnh theo `bbox`. Lưu ảnh cạnh ảnh hình, khoá theo `formula_id`.
- Ghi một chỉ mục `formula_id` → tham chiếu ảnh, trang, `bbox`, có chữ thô hay không. Hệ số vẽ ghi trong manifest.

**Phạm vi chạy:** chạy được cho các tài liệu đã có (sáu cuốn phát triển), và tự chạy ở bước tải mỗi tài liệu mới.

**Không đổi `chunk_id`** và không làm khâu nào phải chạy lại.

**Công thức thiếu `bbox`** (DOCX, hoặc bộ đọc không ghi) thì bỏ qua và ghi cờ.

**Kiểm bộ đọc nhẹ,** mặc định A1 từ vé 16: trên doc-1 và xstk, bộ đọc nhẹ có sinh nút công thức không, có `bbox` không. Chỉ báo lại, không sửa A1,
vì A1 đang tạm dừng theo quyết định của chủ dự án.

## Tiêu chí nghiệm thu

- [ ] doc-1: số ảnh cắt được so với 562 nút công thức, kèm lý do các ca thiếu. Báo tương tự cho xstk và naive-bayes.
- [ ] Một bảng mẫu 20 công thức chọn ngẫu nhiên, mỗi dòng có ảnh cạnh chữ thô, để Claude soát bằng mắt.
- [ ] Sau bước này, dry-run `roadmap` trên sáu cuốn vẫn tái dùng mọi stage.
- [ ] Ghi giây mỗi cuốn của bước cắt ảnh.
- [ ] Báo cáo bộ đọc nhẹ trên doc-1 và xstk: số nút công thức, có `bbox` không, so với docling.
- [ ] Test trên PDF tổng hợp có công thức ở vị trí biết trước:
  - ảnh cắt đúng vùng, kiểm cả phép đổi toạ độ;
  - chạy hai lần cho cùng kết quả.

## Ngoài vé

Ba việc không thuộc vé này:
- sinh LaTeX công thức ở A1;
- gửi ảnh công thức cho mô hình (nhánh thí nghiệm của vé 21);
- hiển thị ảnh trên web.
