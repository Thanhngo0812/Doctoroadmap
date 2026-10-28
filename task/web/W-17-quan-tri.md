# W-17 — Quản trị: người dùng, bản dựng, chi, khoá mẫu, nhật ký

**Nghiệm thu lần 10, 2026-10-28: giữ backend 9cf405ac ở nhánh, chưa nhận/chưa ghép.** Theo hợp đồng cũ có 23 probe độc lập xanh/6 mutant bị bắt. Sau câu trả lời chủ dự án “admin đầu tiên ko đc khóa hay gì”, Required POL-R10-01 bắt buộc bảo vệ định danh admin đầu tiên khỏi khoá/hạ quyền/xoá, không chỉ đếm admin cuối. Test mới đã assertion đỏ/0 setup error. Sửa W-17.1 trước, không coi đây còn là Optional/chờ chủ dự án chọn; [ADR 0030](../../doc/adr/0030-bao-ve-tai-khoan-admin-dau-tien.md). Toàn W-17 còn mở/React chưa làm. [biên bản lần 10](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan10-2026-10-28.md) và [lời giao lần 10](../../report/lenh-giao-viec-ba-nhom-lan10-2026-10-28.md).

**Phân công lần 9, 2026-10-27: mở mốc backend W-17.1, toàn W-17 vẫn mở.** W-14/W-16 đã đạt. Lõi nhận list_users/update_user + GET/PATCH admin/users và GET admin/audit, tái dùng account/session/audit/policy; web làm React ở lượt sau. Kiểm quyền/không lộ dữ liệu học, disable hủy mọi phiên, admin cuối/cạnh tranh, rollback audit. Không tạo migration rỗng, không bật trần demo/Cloudinary thật. Phần bản dựng/khoá mẫu rồi chi/log validation là các mốc sau, chưa hoàn tất; xem [biên bản lần 9](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan9-2026-10-27.md) và [lời giao lần 9](../../report/lenh-giao-viec-ba-nhom-lan9-2026-10-27.md).

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 3 (admin không đọc chat), 8 (`spend_summary`), 9, 10 (nhật ký); spec thiết kế, khu quản
trị.
**Ai:** lõi làm backend theo mốc; web làm React/tích hợp · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-14, W-16 · **Trạng thái:** ready-for-agent

## Vì sao

Cần một chỗ để khoá tài khoản lạm dụng, cấp thêm lượt dựng, gỡ lỗi bản dựng, đối soát chi với hoá đơn, và chọn khoá mẫu cho demo. Admin không được đọc nội
dung học của người khác.

## Cần làm

**`AdminService`:** `list_users`, `update_user` (trạng thái, vai trò, `build_monthly_max`), `list_builds`, `set_sample_course`, và xem nhật ký.
- Không tự hạ quyền nếu là admin cuối cùng.
- **Bảo vệ admin đầu tiên (chủ dự án 28/10):** không cho khoá quản trị/hạ quyền/xoá tài khoản này qua service/API, kể cả tự thao tác; định danh server bền vững, không suy từ danh sách hoặc role hiện hành. Giữ hồ sơ/mật khẩu và guard xác thực bình thường.
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

- [ ] Bảo vệ định danh admin đầu tiên bền vững: không disable/demote/delete, kể cả có admin thứ hai, tự thao tác, PATCH nhiều trường/cạnh tranh; tài khoản thường cũ được nâng admin không thay người được bảo vệ; từ chối không làm đổi phiên/field/audit thành công.

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
