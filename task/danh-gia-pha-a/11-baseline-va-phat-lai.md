# DG-11 — Baseline B1–B4, bộ phát lại A9 → A10 và các biến thể

**Nguồn:** spec mục 11 · **Ai:** agent B · **Chi phí:** 0 · **Chặn bởi:** DG-04 · **Hạn:** 01/11 · **Trạng thái:** ready-for-agent

## Làm được gì

Các baseline sau xuất ra hợp đồng `danh-gia-xuat-1` từ hợp đồng và artifact của hệ chính:
- **B1:** node của hệ chính xếp theo vị trí dạy, không cạnh.
- **B2:** cạnh X → Y khi tên X hoặc tên khác của X nằm trong cửa sổ định nghĩa của Y, và X được dạy trước Y. Dùng bộ khớp theo âm tiết. Dãy học qua hàm A10.
- **B3:** mỗi tiêu đề A1 (bỏ số mục) là một khái niệm.
- **B4:** ứng viên A3 gộp chỉ khi trùng tên sau chuẩn hoá.

**Bộ phát lại A9 → A10** dựa trên `scripts/pass-phu-ml/phat_lai_e4.py` và `phat_lai_tat_r17.py`:
- đưa vào gói `danhgia/phat_lai/`, thuộc seam xuất;
- tên khái niệm lấy từ phản hồi đã ghi, không gọi mạng;
- các biến thể: tắt R17, bỏ cạnh pass chính, bỏ cạnh pass phụ, **oracle A10** (cạnh G4 căn được, đặt vào hàm dãy học trên node của hệ chính).

## Tiêu chí

- [ ] **Kiểm tái tạo:** phát lại với cạnh không đổi phải ra đúng `sequence` và `requires_edges` đã lưu, trên graph phát triển xstk v68 và doc-4 v27.
- [ ] Mỗi baseline có fixture nhỏ với đầu ra tính tay. Hợp đồng qua validator.
- [ ] Tắt R17 ra đúng số E8 đã báo trên cùng đầu vào, nếu tìm được đầu vào cũ; không tìm được thì ghi vào báo cáo.
- [ ] Không gọi mạng: test với transport bị chặn.
- [ ] Bảng phá, gồm ít nhất: B2 khớp chuỗi con thay âm tiết; phát lại quên cạnh mềm có sẵn; oracle A10 dùng cạnh vàng chưa căn.
