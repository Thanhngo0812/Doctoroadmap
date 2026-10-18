# Khoá học là đơn vị chia sẻ; dữ liệu học theo người × cuốn; bản dựng dùng lại theo băm tệp

**Status:** proposed — 2026-10-18 (chờ chủ dự án duyệt cùng [spec web](../web-chuc-nang-spec.md))

**Khoá học** là thứ người dùng tạo, chia sẻ và tham gia. Mỗi khoá trỏ tới đúng một `doc_id` (một tài liệu đã dựng) và ghim một
`published_graph_version`. Người khác vào khoá bằng link mời, lời mời email, hay khoá mẫu.

**Dữ liệu học khoá theo người × cuốn**, không theo khoá học. Gateway gọi Pha B với `owner = user_id`, `doc_id = course.doc_id`. Phiên, lượt, tiến độ, tài
liệu và lần làm quiz vì vậy không đổi khoá so với Pha B hiện tại.
- Một người ở hai khoá của cùng một cuốn thấy chung tiến độ, phiên và thư viện.
- Rời khoá hay bị xoá khỏi khoá không xoá dữ liệu học; vào lại thì thấy lại.
- Chỉ xoá tài khoản mới xoá dữ liệu học.

**Bản dựng dùng lại theo băm tệp.** Tệp tải lên có cùng SHA-256 và cùng `pipeline_version` với một bản dựng đã thành công thì khoá học mới trỏ thẳng vào
`doc_id` đó: 0 USD, không trừ lượt dựng. `doc_id` của tệp tải lên là `u-` cộng 20 ký tự hex đầu của băm.

**Căn cứ:**
- Bài giảng và ngân hàng quiz đã cache theo nội dung (ADR 0011). Chia sẻ một bản dựng cho nhiều người làm chi phí bài giảng chia đều; thêm người học không
  thêm tiền bài giảng.
- Khâu dựng là khâu đắt nhất (D-01: khoảng 1,75 USD/cuốn ở chuỗi cũ, chưa gồm pass chính A8; bài giảng khoảng 0,002 USD/bài). Ưu tiên số một của dự án là
  USD/cuốn và phút/cuốn.
- Tiến độ và phạm vi đã neo vào `node_id` (ADR 0017, 0019), nên ghim phiên bản theo khoá học và đổi phiên bản sau này không làm hỏng dữ liệu học.

**Considered Options**

- *Dữ liệu học theo người × khoá học.* Tách sạch hơn khi một người ở hai khoá của cùng cuốn. Bị bác: phải đổi khoá `owner` của mọi use case Pha B, hoặc
  ghép `owner` thành chuỗi `user:course`, làm trần ngày theo người (Pha B2 mục 8) tính sai theo từng khoá. Ca hai khoá cùng cuốn hiếm, và dùng chung là hợp
  lý vì nội dung giống hệt.
- *Mỗi người tải lên tự dựng riêng, không dùng lại.* Đơn giản hơn, nhưng trả tiền nhiều lần cho cùng một tệp.
- *Dùng lại theo tên tệp hay tiêu đề.* Bị bác: hai tệp khác nhau có thể trùng tên; băm nội dung mới chắc.
- *Khoá học gồm nhiều tài liệu.* Để sau: Pha A dựng theo từng tài liệu.

**Consequences**

- Có thực thể web: khoá học, thành viên, link mời, lời mời, tệp tải lên, bản dựng.
- Có một `LearningGateway` là chỗ duy nhất gọi Pha B, kiểm thành viên rồi mới truyền `owner`, `doc_id`, `graph_version`.
- Xoá khoá học không xoá dữ liệu học hay artifact khi còn khoá khác dùng cùng `doc_id`; dọn artifact mồ côi là lệnh của admin.
- Phát hành phiên bản đồ thị mới là thao tác của chủ khoá, không tự động.
