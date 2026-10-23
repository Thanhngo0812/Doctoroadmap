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
- **Sau W-15/SA-62:** tổng tiền/token/lời gọi không cộng lại trace `counted_in="build"`; cột typed trace bằng 0, raw `extra` giữ đối soát.
  Nếu đọc raw `usage_rows()` để làm bảng chi phải lọc cờ này. Kiểm receipt meter được cộng đúng một lần bằng số fake khác 0 và SQL độc lập.
- **ADR 0024/0025, SA-64 thay SA-63:** trang Nhật ký cho admin xem `lecture_validation` theo spec bài giảng 3
  (độ dài, tự kiểm tra, nhãn nguồn/điểm trùng/nhãn lạ, formula còn sót, lặp, finish_reason, thiếu ảnh/số ảnh), có lọc định danh bài/thời gian.
  Không trả khối `validation` qua API/SSE/tool cho người học; không dùng quyền xem log này mở quyền đọc chat hay dữ liệu học riêng.
- **Tín dụng Cloudinary:** đọc mức dùng của tài khoản qua API quản trị của Cloudinary (dung lượng, băng thông, phép biến đổi), lưu tạm 1 giờ, hiện ở thẻ Chi.
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
- [ ] Có receipt build và trace cùng số chi khác 0: bảng chi/đếm lời gọi tính receipt một lần, không cộng trace; raw trace vẫn đọc lại được để đối soát.
- [ ] Người thường bị chặn log `lecture_validation`; admin xem được số đo kiểm/định danh, không lộ chat hoặc dữ liệu học riêng qua log này.
- [ ] Ảnh chụp năm thẻ ở 1280 px. Khu quản trị không bắt buộc đẹp ở 390 px, nhưng không vỡ bố cục.

## Ngoài vé

Danh sách báo lỗi nội dung (W-19). Dọn artifact mồ côi bằng lệnh (W-20).
