# DG-13 — Chấm A1/A2

**Nguồn:** spec mục 8 (A1, A2); bộ chấm D-02 `scripts/a1-d02/cham_d02.py` · **Ai:** agent A · **Chi phí:** 0 · **Chặn bởi:** DG-04, DG-12 · **Hạn:** 02/11 ·
**Trạng thái:** ready-for-agent

## Làm được gì

Lõi chấm có thêm hai nhóm thước, đầu ra theo bảng số đếm theo chương; phần A2 có thêm bản tính cả cuốn:
- **A1:** M1 F1 tiêu đề (khớp khi phủ từ nửa số dòng trở lên, cùng trang); F1 "complete entry" (tiêu đề + cấp + trang); M2 trên tiêu đề khớp, ghi mẫu số; M3
  gán mục theo ký tự. Dùng lại định nghĩa của bộ chấm D-02. M4 không áp.
- **A2:** recall `noi_dung` theo mục và theo ký tự; macro-F1 sáu vai trò; ma trận nhầm lẫn; **lỗi có hại** (khái niệm G3 có câu định nghĩa nằm trong mục bị
  hệ gán khác `noi_dung`).

## Tiêu chí

- [ ] Trên nhãn D-02 phát triển, M1, M2, M3 bằng đúng số của bộ chấm D-02 cho cùng đầu ra. Bảng so ghi trong báo cáo.
- [ ] Ca dựng tay cho recall `noi_dung` và lỗi có hại.
- [ ] Bảng phá, gồm ít nhất: M3 tính cả đầu và chân trang; khớp tiêu đề khác trang; lỗi có hại đếm cả khái niệm không có câu định nghĩa.
