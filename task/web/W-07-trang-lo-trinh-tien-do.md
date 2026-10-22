# W-07 — Trang lộ trình và tiến độ

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), "Giải pháp" (trang lộ trình), mục 5 (`progress-1`); [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 7;
spec thiết kế, trang lộ trình.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-06, SA-34 · **Trạng thái:** đạt · đã ghép `f20d198` tại mốc `2a14723`, đã đẩy GitHub.

**Nghiệm thu 2026-10-21:** nhận `cd1ecb8` và main `2f4998c`, mốc soát `2a14723`. Cổng độc lập **2.114 Python đạt/0 fail/1 Cloudinary live không bật; React 85/build; 8 backend +2 UI mutation bị bắt; browser PostgreSQL: 11 kiểm tra/6 cấu hình**, 0 USD. Hai engine/runtime PostgreSQL kiểm cách ly và cả hai thứ tự quiz/learner; browser/SQL xác nhận rollback không ghi dữ liệu. Không thêm migration, head `w06_0005`. Xem [báo cáo nghiệm thu](../../report/dieu-phoi-nghiem-thu-w07-w14-w24-va-ke-hoach-2026-10-21.md). Phạm vi không thay nghiệm thu toàn SA-34/Pha B2.

**Đợt sau W-06, 2026-10-21:** ưu tiên tiếp theo của web sau khi W-06 được ghi ghép trong
[nghiệm thu và kế hoạch](../../report/dieu-phoi-nghiem-thu-w06-va-ke-hoach-2026-10-21.md). Đã soát độc lập phần sửa SA-47 memory/JSON,
đủ dùng hợp đồng tiến độ hiện có; đây chưa phải nghiệm thu W-07/toàn SA-34. Bắt buộc kiểm race/cách ly bằng PostgreSQL qua các connection/runtime độc lập,
membership và actor từ phiên; không dùng kết quả memory/JSON để bỏ phần này.
Giữ nhãn người dùng “tài liệu”/“bài học”; API/node/graph vẫn theo hợp đồng. Dùng graph doc-1 v8, không ghim lại v45/v57, không nhập cache CLI/live vào web.
Không tạo migration rỗng nếu không thêm bảng. Bàn giao JSON thật, ảnh 390/1280 sáng/tối, kiểm 768/video và test đánh dấu thất bại rollback UI.

## Vì sao

Trang lộ trình là trang đầu tiên người học thấy trong một khoá: các module theo thứ tự, mỗi module có tên, mô tả, khái niệm và "xong x/y".

## Cần làm

**Gateway:** `get_progress`, `set_progress`, và `get_roadmap` thêm tóm tắt tiến độ mỗi module của người hỏi.

**HTTP:** `GET /courses/{cid}/progress`, `PUT /courses/{cid}/progress/{node_id}` với thân `{learned: true|false}`.

**Giao diện trang lộ trình:**
- đầu trang: tên khoá, mô tả, tiến độ cả khoá;
- danh sách module theo thứ tự: số thứ tự, tên, mô tả, "xong x/y", nút mở trang học của module;
- mở một module ra thì thấy khái niệm theo thứ tự, mỗi khái niệm có dấu "đã học" bấm được;
- vùng để sẵn cho W-09 (phiên chat) và W-10 (thư viện, nút quiz, nút tài liệu), theo bố cục của spec thiết kế;
- bấm "đã học" thì cập nhật ngay trên màn hình, và quay lại trạng thái cũ kèm thông báo nếu máy chủ trả lỗi.

## Tiêu chí nghiệm thu

- [x] Hai thành viên cùng khoá: A đánh dấu một khái niệm thì tiến độ của B không đổi (test tầng dịch vụ, thấy đỏ trên bản sai dùng chung `owner`).
- [x] Bỏ dấu một khái niệm rồi làm đúng quiz của nó thì nó vẫn `not_learned` (bất biến 6 của Pha B2, kiểm lại qua gateway).
- [x] `PUT` với `node_id` không thuộc đồ thị đã phát hành thì `not_found`.
- [x] Ví dụ JSON thật của `get_roadmap` và `get_progress` cho doc-1; ảnh chụp trang ở 390 px và 1280 px, có một module mở.

## Ngoài vé

Bài giảng (W-08). Phiên chat (W-09). Quiz, tài liệu, thư viện (W-10).
