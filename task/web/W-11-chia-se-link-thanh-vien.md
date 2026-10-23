# W-11 — Chia sẻ bằng link, thành viên, rời khoá

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 3, 6; [ADR 0020](../../doc/adr/0020-khoa-hoc-la-don-vi-chia-se-du-lieu-hoc-theo-nguoi-va-cuon.md);
[spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), bảng `share_link`, mục 6 (tham gia bằng link); spec thiết kế, hộp chia sẻ, trang tham gia, trang
thành viên.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-06 · **Trạng thái:** cần sửa một Required sau soát `8539709`; chưa ghép.

**Soát 2026-10-23:** backend/transaction/token/schema và hồ sơ được đối chiếu; chưa nhận cả vé vì đổi form đăng nhập ↔ đăng ký làm mất `next` của link mời.
Test độc lập: 8 ca đổi form đỏ đúng assertion, 2 ca xác thực trực tiếp xanh; không lỗi setup. Sửa cả link header/footer và nhánh view transition,
giữ đích nội bộ đã kiểm tra, không mở redirect ngoài. Chứng minh RED→GREEN cho hai chiều rồi nhận main mới và chạy lại cổng Python/PostgreSQL, React/build,
browser PG qua link mời đến xác thực và trở lại đúng `/join/<token>`. Giữ kiểm một lần hiện URL, transaction, lượt/cap và dữ liệu học riêng.
Xem [nghiệm thu và Required](../../report/dieu-phoi-nghiem-thu-w11-w15-w24-va-ke-hoach-2026-10-23.md),
[lời giao ba nhóm](../../report/lenh-giao-viec-sau-w11-2026-10-23.md). Không viết lại backend đã đạt review hoặc tự ghép main.

**Ưu tiên tiếp theo sau W-14, 2026-10-22:** W-14 đầu-cuối đã đạt có ghi chú, ghép/đẩy `7fe63df`; web tiếp ngay W-11 tại worktree/nhánh riêng
từ mốc giữ `a53f0d3`, nhận main mới nhất rồi hoàn tất migration/cổng. W-11 chưa được nghiệm thu trong đợt W-14; tuyến vẫn `w14_0006 → w11_0007`.
Sau W-11 mới W-08 nếu chỉ một phiên web; xem [lời giao](../../report/lenh-giao-viec-sau-w14-2026-10-22.md).

**Cập nhật 2026-10-22:** backend/schema W-14+W-25 đã đạt và ghép main `a572459`; gỡ điểm chờ schema. W-11 giữ `a53f0d3`, chưa nghiệm thu; nhận main mới rồi tạo `w11_0007` nối `w14_0006`, không thêm head thứ hai. Nếu một phiên web, ưu tiên cổng cuối W-14 trước rồi hoàn tất W-11. Xem [kế hoạch mới](../../report/dieu-phoi-kiem-lai-w25-w14-react-w24-va-ke-hoach-2026-10-22.md).

**Sau soát W-07/W-14, 2026-10-21:** giữ phần W-11 đang làm ở nhánh riêng; đợt này chưa nghiệm thu W-11. Mốc backend W-14 chưa đạt, cần [W-25](W-25-dong-bo-xac-nhan-huy-va-ket-thuc-ban-dung.md) sửa race trước khi ghép schema. Không đổi tuyến đã chốt; chốt migration/cổng W-11 sau khi nhận main có mốc W-14 đã sửa/soát đạt. Xem [kế hoạch mới](../../report/dieu-phoi-nghiem-thu-w07-w14-w24-va-ke-hoach-2026-10-21.md).

**Đợt sau W-06, 2026-10-21:** đủ điều kiện sau mốc ghép W-06; nếu chỉ có một phiên web, làm sau W-07, không triển khai cùng lúc hai giao diện chưa tích hợp.
**Tuyến migration đã chốt 2026-10-21:** W-14 ghép trước, W-11 nối sau: `w06_0005 → w14_0006 → w11_0007`. W-11 tiếp tục service/API/UI trong lúc chờ; nhận migration W-14 rồi tạo `w11_0007` với `down_revision='w14_0006'`, không tạo head thứ hai hoặc sửa migration W-06/W-14. Trước cổng cuối phải nhận main đã ghép mốc W-14 được soát đạt.
Giữ test tự liệt kê mọi route `{cid}` trên khoá riêng tư, không miễn rộng; preview/join theo token có luật rõ riêng.
Xem [kế hoạch](../../report/dieu-phoi-nghiem-thu-w06-va-ke-hoach-2026-10-21.md).

## Vì sao

Chia sẻ khoá học cho cả lớp là chức năng chủ dự án yêu cầu. Nó cũng làm cache bài giảng có lợi thật: thêm người học không thêm tiền bài giảng.

## Cần làm

**`SharingService`:** `create_share_link`, `list_share_links`, `revoke_share_link`, `preview_share_link`, `join_by_link`, `list_members`, `remove_member`,
`leave_course`.
- **Link:**
  - token 32 byte, chỉ lưu băm; hiện đủ **một lần** lúc tạo;
  - danh sách link chỉ hiện 6 ký tự cuối;
  - hạn mặc định 7 ngày, hoặc "không hết hạn"; `max_uses` tuỳ chọn.
- **Chưa xác minh email** vẫn tạo link và tham gia được (bản demo, chủ dự án chốt 2026-10-18).
- `preview_share_link` mở cho khách; link hỏng vì bất kỳ lý do gì đều trả `link_invalid`.
- **`join_by_link`** chạy trong một giao dịch như spec cơ sở dữ liệu mục 6. Đã là thành viên thì không tăng `use_count`. Đủ 200 thành viên thì `course_full`.
- **`remove_member`:** người bị xoá mất quyền ngay ở lần gọi kế tiếp; dữ liệu học của họ giữ nguyên.
- **`leave_course`:** chủ khoá không rời được (phải xoá khoá ở W-20).
- Nhật ký: `share_link_created`, `share_link_revoked`, `member_joined`, `member_removed`, `member_left`.

**HTTP:** các điểm cuối của nhóm "chia sẻ" ở spec mục 11, trừ lời mời email (W-12) và tiến độ thành viên (W-18).

**Giao diện:**
- **hộp "Chia sẻ"** của chủ khoá: tạo link (hạn, số lượt), nút sao chép, danh sách link với nút thu hồi;
- **trang `/join/<token>`:**
  - khách thấy tên khoá, chủ khoá, số module, kèm nút đăng nhập hay đăng ký; xong thì quay lại đúng trang;
  - người đã đăng nhập thấy **thông báo dữ liệu** (chủ khoá thấy gì, không thấy gì) và nút "Tham gia";
- **trang thành viên:** chủ khoá thấy danh sách và nút xoá; thành viên thường thấy chủ khoá, số thành viên, nút "Rời khoá".

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Link thu hồi, hết hạn (đồng hồ giả), hay hết lượt đều trả `link_invalid`, cùng thân phản hồi.
- [ ] `max_uses = 1`, hai tham gia đồng thời trên PostgreSQL: đúng một người vào.
- [ ] Tham gia lần hai không tăng `use_count`.
- [ ] Bị xoá thì lần gọi kế tiếp `not_found`; tham gia lại bằng link mới thì thấy lại tiến độ và phiên cũ.
- [ ] Thu hồi link không xoá thành viên đã vào.
- [ ] Bảng `share_link` không có token thô.
- [ ] Ảnh chụp: hộp chia sẻ, trang tham gia của khách và của người đã đăng nhập, link hỏng, trang thành viên của chủ khoá và của thành viên.

## Ngoài vé

Mời theo email (W-12). Tiến độ thành viên (W-18). Đồng chủ khoá.
