# W-18 — Tiến độ tổng hợp của thành viên cho chủ khoá

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 6 ("Tiến độ tổng hợp cho chủ khoá", thông báo dữ liệu khi tham gia), câu hỏi mở 3; spec thiết kế,
bảng tiến độ lớp.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-07, W-11 · **Trạng thái:** ready-for-agent. Chủ dự án chốt 2026-10-18: bật, báo trước khi tham gia. Vẫn cài sau cờ
`members_progress_enabled` (mặc định bật) để tắt được

## Vì sao

Giảng viên chia sẻ khoá học cho lớp muốn biết lớp đang ở đâu. Dữ liệu này nhạy cảm, nên chỉ lộ đúng phần đã báo trước cho người tham gia.

## Cần làm

**`SharingService.members_progress`:** chỉ chủ khoá gọi được. Mỗi thành viên trả:
- `display_name`, `joined_at`, `last_active_at`;
- mỗi module `{module_id, module_index, learned, total}` theo đồ thị đã phát hành.

**Không có trường nào khác:** không chat, không tài liệu, không điểm quiz, không danh sách khái niệm cụ thể.

**HTTP:** `GET /courses/{cid}/members/progress`.

**Giao diện:**
- bảng lớp: hàng là thành viên, cột là module, ô là "x/y" có tô màu theo tỉ lệ; sắp xếp theo tên hay theo lần học gần nhất;
- ở điện thoại thì đổi thành danh sách thẻ.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Thành viên thường gọi thì `forbidden`; người ngoài khoá thì `not_found`.
- [ ] **Danh sách trường của phản hồi đúng bằng** tập trường ở trên. Test so tập khoá đệ quy, nên thêm một trường là đỏ.
- [ ] Cờ tắt thì điểm cuối trả `not_found`, và nút trên giao diện ẩn.
- [ ] Ảnh chụp bảng lớp ở 1280 px và danh sách thẻ ở 390 px.

## Ngoài vé

Xuất bảng ra tệp. Tiến độ theo từng khái niệm của từng người.
