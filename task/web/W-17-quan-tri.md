# W-17 — Quản trị: người dùng, bản dựng, chi, khoá mẫu, nhật ký

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 3 (admin không đọc chat), 8 (`spend_summary`), 9, 10 (nhật ký); spec thiết kế, khu quản
trị.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-14, W-16 · **Trạng thái:** ready-for-agent

## Vì sao

Cần một chỗ để khoá tài khoản lạm dụng, cấp thêm lượt dựng, gỡ lỗi bản dựng, đối soát chi với hoá đơn, và chọn khoá mẫu cho demo. Admin không được đọc nội
dung học của người khác.

## Cần làm

**`AdminService`:** `list_users`, `update_user` (trạng thái, vai trò, `build_monthly_max`), `list_builds`, `set_sample_course`, và xem nhật ký.
- Không tự hạ quyền nếu là admin cuối cùng.
- **`UsageService.spend_summary`:** chi theo ngày × `purpose`, theo khoá học, 20 tài khoản chi nhiều nhất, số lời gọi, p50 và p90 giây, trong khoảng ngày
  chọn. Ghi rõ "ước theo token, không thay hoá đơn".
- `system_caps_today`: trần nội dung dùng chung và trần khâu dựng hôm nay, đã dùng bao nhiêu.
- Mọi thao tác admin ghi `audit_event`.

**HTTP:** các điểm cuối nhóm "quản trị" ở spec mục 11, trừ báo lỗi nội dung (W-19).

**Giao diện:** khu `/admin` chỉ hiện với admin, gồm các thẻ: Người dùng, Bản dựng, Chi, Khoá mẫu, Nhật ký. Bảng có tìm và lọc; biểu đồ cột chi theo ngày
và mục đích.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Người dùng thường gọi mọi route `/admin/*` đều bị `forbidden` (test liệt kê route).
- [ ] **Admin không đọc được nội dung học:** test duyệt mọi hàm của `AdminService` và `UsageService` trên dữ liệu có chat, và kiểm phản hồi không chứa câu hỏi
  hay câu trả lời nào đã ghi (tìm chuỗi đánh dấu đặt trong câu hỏi thử).
- [ ] Khoá tài khoản thì mọi phiên của người đó hết hiệu lực ngay.
- [ ] Admin cuối cùng không tự hạ quyền được.
- [ ] Tổng `spend_summary` khớp tổng sổ chi trong khoảng ngày, tính theo giờ Việt Nam.
- [ ] Ảnh chụp năm thẻ ở 1280 px. Khu quản trị không bắt buộc đẹp ở 390 px, nhưng không vỡ bố cục.

## Ngoài vé

Danh sách báo lỗi nội dung (W-19). Dọn artifact mồ côi bằng lệnh (W-20).
