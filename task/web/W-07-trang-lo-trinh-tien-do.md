# W-07 — Trang lộ trình và tiến độ

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), "Giải pháp" (trang lộ trình), mục 5 (`progress-1`); [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 7;
spec thiết kế, trang lộ trình.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-06, SA-34 · **Trạng thái:** ready-for-agent

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

- [ ] Hai thành viên cùng khoá: A đánh dấu một khái niệm thì tiến độ của B không đổi (test tầng dịch vụ, thấy đỏ trên bản sai dùng chung `owner`).
- [ ] Bỏ dấu một khái niệm rồi làm đúng quiz của nó thì nó vẫn `not_learned` (bất biến 6 của Pha B2, kiểm lại qua gateway).
- [ ] `PUT` với `node_id` không thuộc đồ thị đã phát hành thì `not_found`.
- [ ] Ví dụ JSON thật của `get_roadmap` và `get_progress` cho doc-1; ảnh chụp trang ở 390 px và 1280 px, có một module mở.

## Ngoài vé

Bài giảng (W-08). Phiên chat (W-09). Quiz, tài liệu, thư viện (W-10).
