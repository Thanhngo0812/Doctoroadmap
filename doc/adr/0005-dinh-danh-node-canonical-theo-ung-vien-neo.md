# ADR 0005: Định danh node canonical theo ứng viên neo

**Trạng thái:** accepted  
**Ngày:** 2026-09-11

## Bối cảnh

Node canonical là thứ tiến độ người học bám vào: B1 lưu `concept_mastery` theo id node, quiz A11 gắn
`concept_id`. Ví dụ trong spec đặt id theo tên (`cpt_overfitting`), nhưng tên chuẩn đổi theo luật chọn tên —
riêng đợt A4 đã sửa luật D5, và `Naïve Bayes Classification` thành `Naïve Bayes`. Id băm theo tập thành viên
thì đổi mỗi khi thêm hoặc bớt một ứng viên.

## Quyết định

Id node canonical là băm của **ứng viên neo** — ứng viên có `first_order_index` của chính nó nhỏ nhất trong
node, hoà thì lấy `candidate_id` nhỏ nhất. `candidate_id` đã băm doc + section + tên chuẩn hoá (ADR 0001),
nên neo đứng yên qua các lần chạy lại chừng nào ứng viên đó còn trong node.

Khi neo đổi — gộp hai node, tách một node, hoặc ứng viên neo biến mất ở lần trích sau — id cũ được ghi vào
**bảng chuyển hướng** trỏ sang id mới. Một id đã dùng không bao giờ được cấp lại cho khái niệm khác.

## Hệ quả

- Đổi tên chuẩn, alias, ký hiệu hay mô tả không đổi id.
- Đổi tên heading của section chứa ứng viên neo, hoặc A3 đặt lại tên khái niệm, sẽ đổi id; bảng chuyển
  hướng nối id cũ sang id mới theo thành viên chung giữa hai phiên bản.
- Media giữ id theo `media_id`, không qua luật này.
