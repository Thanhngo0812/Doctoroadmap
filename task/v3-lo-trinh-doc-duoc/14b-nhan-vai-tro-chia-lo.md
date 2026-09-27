# 14b — Nhãn vai trò bằng mô hình: chia lô theo chương, luật kiểm cấu trúc, chuyển vai trò sang chunk cũ

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R1 (bổ sung 2026-09-27) · **Ai:** nhân viên · **Phụ thuộc:** 14 ·
**Chi phí mô hình:** vài lời gọi mỗi tài liệu (≈ 0,005–0,02 USD); chạy lại neo doc-2 chỉ phần đầu vào đổi (≈ 0,05 USD)

**Trạng thái:** chờ giao. **Nghiệm thu vé 07 trên doc-2 chờ vé này:** lọc khái niệm chỉ-nhắc khỏi dãy học khi doc-2 còn 42 khái niệm mất
trạng thái được dạy do nhãn sai sẽ làm mất bài học thật.

## Vì sao (kiểm thử vé 14, 2026-09-27)
- doc-2 v6 (vai trò cho chunk v1, là bản đồ thị A8 hiện có đang dùng): mô hình gắn `de_cuong` cho 104 mục bài giảng (106 chunk), ví dụ
  "Representing a Linear Map by a Matrix", "Jordan Form", "QR Factorization", "8.14 definition: nilpotent" (dòng đầu là định nghĩa).
  Qua vé 05, 42 khái niệm doc-2 mất trạng thái được dạy; 17 trực tiếp vì chunk neo nằm trong mục bị gắn nhầm.
- Nguyên nhân: một lời gọi gán nhãn khoảng 540 tiêu đề (80 nghìn token đầu vào). Danh sách dài làm mô hình dùng kém phần giữa ngữ cảnh
  (Liu và cộng sự, TACL 2024, *Lost in the Middle*); gộp nhiều mục vào một lời gọi làm giảm độ chính xác từng mục (Cheng, Kasai, Yu,
  EMNLP 2023, *Batch Prompting*; Lin và cộng sự 2023, *BatchPrompt*). Thêm nữa, cây mục v1 của doc-2 bị vỡ (đường dẫn kiểu
  "Exercises 3B > Representing a Linear Map by a Matrix") nên chính đầu vào đã gây nhiễu.

## Việc cần làm

### A. Chia lô
Mỗi lời gọi một chương (theo chuỗi chương của lớp cấu trúc), tối đa khoảng 40 tiêu đề; chương dài chia tiếp; phần trước chương đầu và
sau chương cuối là lô riêng. Giữ tập nhãn đóng và prompt hiện có.

### B. Luật kiểm cấu trúc sau khi mô hình trả nhãn (không danh sách từ)
- `mo_dau` ở mục nằm sau khi chương đầu đã bắt đầu → không hợp lệ.
- `cuoi_sach` ở mục trước chương cuối mà nội dung không có dạng chỉ mục hay tài liệu tham khảo (`back_matter`) → không hợp lệ.
- `de_cuong`, `mo_dau` hoặc `hanh_chinh` ở mục mà chính chunk của nó là văn xuôi dài (ngưỡng trong config, ví dụ từ 1.500 ký tự trở lên
  và đa số dòng dài) → không hợp lệ.
- Nhãn không hợp lệ → hỏi lại một lần, trong lô nhỏ chỉ chứa các mục đó; vẫn không hợp lệ → `noi_dung` kèm cảnh báo. Báo số lần mỗi luật
  chạm trên từng tài liệu.

### C. Chuyển vai trò sang version chunks cũ
Khi đồ thị A3–A8 dựng trên version chunks cũ (doc-2 v1) mà đã có cây đã sửa (doc-2 v5), vai trò của chunk cũ lấy từ các chunk mới phủ
phần lớn văn bản của nó (khớp văn bản sau chuẩn hoá khoảng trắng, theo thứ tự đọc), không hỏi mô hình trên cây vỡ. Chunk không khớp được
thì dùng nhãn theo lô (A, B). Báo tỉ lệ chunk cũ khớp được. Vẫn ghi version chunks mới giữ nguyên ID, text, offset như hiện nay.

### D. Chạy lại
- Vai trò doc-2: v1 bằng cách chuyển (C), v5 bằng lô (A, B). Tài liệu khác chỉ chạy lại nếu luật B đổi nhãn nào của chúng.
- Neo doc-2 (tái dùng phán theo hash đầu vào như vé 05), rồi danh tính và dãy học trong kho thử.

## Tệp liên quan
`application/use_cases/label_chunk_roles.py`, `domain/chunking.py` (`assign_section_roles`), `domain/document_structure.py`
(`back_matter`), `infrastructure/artifacts/json_store.py` (`load_role_chunks`), `scripts/doc-lo-trinh/chay_vung_va_neo_v3.py`.

## Nghiệm thu
- Test: lô không vượt cỡ; mỗi luật B bác đúng (`mo_dau` sau chương đầu, `cuoi_sach` sai chỗ, đề cương trên văn xuôi dài); hỏi lại một
  lần rồi mới về `noi_dung`; chuyển vai trò theo văn bản (chunk cũ bị cắt khác vẫn nhận vai trò của phần phủ nhiều nhất); fixture ở ít
  nhất hai ngôn ngữ ngoài vi/en.
- **Tôi kiểm:** đọc lại vai trò doc-2 (không mục bài giảng nào bị gắn đề cương, mở đầu hay hành chính); đọc lại danh sách 42 khái niệm
  doc-2 từng mất trạng thái được dạy; bảng kiểm R11 và Q6/Q7/Q7b doc-2. Số đo là thông tin để tôi đọc, không phải cổng dừng.
