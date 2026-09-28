# 07 — Dãy học chỉ gồm khái niệm được dạy

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R5 · **Ai:** nhân viên · **Phụ thuộc:** 05, 10b · **Chi phí mô hình:** 0

**Trạng thái:** chờ giao. **Chờ vé 10b:** đại diện nhóm danh tính hiện có thể là nút chỉ-nhắc (doc-6: "CSDL" ở đề cương thay cho
"Cơ sở dữ liệu" được dạy); lọc `mentioned_only` trước khi 10b sửa luật đại diện sẽ làm mất khái niệm được dạy.

## Việc cần làm
- A10 chỉ xếp `taught` và `uncertain` vào dãy học và module. `mentioned_only`, `unchecked` rời dãy học; cạnh qua chúng co lại như
  nút bị loại (`bypass_excluded`).
- Hiển thị: mỗi module có mục "Nhắc tới" cho khái niệm chỉ-được-nhắc lần đầu (trong `noi_dung`) thuộc module đó; khái niệm chỉ có trong
  đề cương vào khối "Tổng quan môn học" đầu lộ trình, không phải một module.
- Payload giữ danh sách `mentioned_nodes` riêng; bộ chấm Q6 coi khái niệm vàng nằm ở danh sách này là thiếu đầu (không lặng lẽ bỏ).

## Tệp liên quan
`application/use_cases/build_roadmap.py`, `domain/sequence.py`, `application/use_cases/a8_score.py` (tên thiếu đầu).

## Nghiệm thu
- Test: khái niệm chỉ-được-nhắc không có trong `sequence`; cạnh A(taught) → M(mentioned) → B(taught) thành A → B; M không kéo B ra
  sau vị trí của M.
- **Tôi kiểm:** doc-1 mục 3.5 không còn bị tách (Độ dài, Góc, Gram-Schmidt về lại gần Tích vô hướng); "Định lý về số chiều" về mục
  4.2; doc-6 và doc-3 dãy học chỉ còn khái niệm được dạy.

## Kiểm thử (Claude, 2026-09-28) — đạt về mã; chất lượng doc-2 đo lại sau vé 05b

- Đột biến bị bắt (nút chỉ-nhắc giữ trong dãy học). Bảng kiểm: khái niệm chỉ-nhắc trong dãy học 0 trên cả sáu tài liệu; doc-1 mục bị xé
  11 → 1; dãy học doc-1 theo đúng thứ tự sách. Đọc doc-3, doc-6: phần hành chính và ví dụ chỉ nêu tên (Python, VGG-19, Random Forests…)
  nằm ở "Tổng quan" hoặc "Nhắc tới", không còn là bài học.
- doc-1 Q6 3/40 → 1/40; "Số phức", "Đa thức" (sách không dạy) được báo là ngoài phạm vi, không lặng lẽ bỏ.
- doc-2 có 19 cạnh vàng ngoài phạm vi, do ba nguyên nhân: (a) phép đo là composite, chạy **trước** danh tính 10b ("Matrix of T" chưa gộp
  vào "Matrix of a linear map"); (b) neo sai vì bước chọn câu ứng viên bỏ sót câu định nghĩa thật → vé [05b](05b-cau-ung-vien-neo.md);
  (c) một phần đúng thiết kế: tính chất kết hợp và phân phối của phép nhân ma trận được sách để cho bài tập. Nghiệm thu chất lượng doc-2
  sau 05b, đo end-to-end (neo → danh tính → A9 → A10) trong một kho thử.
