# SA-37 — Quiz cả lộ trình và tài liệu nhiều module

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 7; đợt tra hỏi 2026-10-18, Q4 và Q30.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (mô hình giả; ngân hàng có sẵn); lượt nhỏ nếu cần thử thật · **Chặn bởi:** 34, 35 ·
**Trạng thái:** ready-for-agent

## Vì sao

Trang lộ trình có nút "Làm quiz" và "Tạo tài liệu" cho cả lộ trình.
- **Quiz cả sách** rẻ, vì lấy mẫu từ ngân hàng câu.
- **Tài liệu cả sách** không nhét vừa một lời gọi: đầu ra 3.000 token không đủ cho 91 module của doc-4. Vì vậy bản đầu giới hạn 5 module mỗi yêu cầu.

## Cần làm

**Quiz phạm vi lộ trình:**
- tối đa `quiz_roadmap_max_items` (10) câu;
- chọn khái niệm đã đánh dấu học trước, trải đều theo module (lần lượt từng module);
- thiếu thì bù bằng khái niệm chưa học, cũng trải theo module;
- hạt giống cố định theo lần làm;
- khái niệm chưa có ngân hàng thì sinh như cũ.

**Tài liệu:**
- phạm vi tối đa `document_max_modules` (5) module, tính theo đồ thị hiện hành;
- vượt thì `status = failed`, `reason = scope_too_large`, 0 lời gọi mô hình;
- khi đó trợ lý nói với người học là cần thu hẹp phạm vi; chữ do mã viết.

## Tiêu chí nghiệm thu

- [ ] Test, mỗi cái thấy đỏ trước:
  - người học đã học 4 khái niệm ở 2 module thì quiz cả lộ trình gồm cả 4, rồi bù khái niệm khác trải theo module, tổng ≤ 10;
  - chưa học khái niệm nào thì các câu trải đều theo module;
  - cùng hạt giống thì cùng tập khái niệm;
  - tài liệu 6 module trả `scope_too_large`, và 0 lời gọi mô hình;
  - tài liệu 5 module được tạo bình thường.
- [ ] Chạy 0 USD trên doc-4 với ngân hàng sẵn có, hoặc câu điền khuyết. Báo số câu và số module được phủ.
