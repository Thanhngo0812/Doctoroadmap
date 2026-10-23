# Bài giảng LLM luôn hiện; luật kiểm chỉ ghi log cho admin; ý hiện ngay, không còn cổng

**Status:** accepted — 2026-10-23. Thay phần "bài hỏng hẳn vì luật kiểm" và "stream sau cổng" của ADR 0018, và cột "khi hỏng" của luật K2–K9 ở spec Pha B
mục 8. Giữ nguyên phần còn lại của ADR 0018: không bao giờ hiện bản trích câu, gợi lại tiên quyết bằng câu nối có trích dẫn.

**Bài LLM viết luôn hiện cho người học.**
- K2, K3, K5, K6, K7, K8, K9 không còn bỏ ý, không làm bài hỏng, không gây sinh lại. Ý trượt hiện như ý đạt, không nhãn.
- Kết quả kiểm chỉ đi vào log cho admin và vào số đo đánh giá. Bài trong cache mang khối `validation`; phản hồi cho người học không có khối này.
- Vẫn bỏ hai loại ý, có ghi log: ý sai lược đồ hay chữ rỗng, vì không có gì để hiện; ý gần trùng một ý trước, vì hiện ra là thừa.
- Câu nối giữ luật cũ: trượt K11 hay K12 thì bỏ câu nối. Câu nối hỏng không làm bài hỏng, và K12 chặn câu "như bạn đã học" trong bài dùng chung.

**Ý hiện ngay, không còn cổng.** Cổng 2 ý giải thích đạt chỉ có để tránh cảnh hiện vài ý rồi báo hỏng vì luật kiểm. Luật kiểm không còn làm bài hỏng, nên
mỗi ý gửi ngay khi đóng xong. Sau ý đầu tiên, bài không còn hỏng được: lỗi ở đuôi chỉ làm bài ngắn lại (`cat_ngan`).

**Không có bài** chỉ còn khi chưa gửi được ý nào: lỗi mạng, quá giờ, hết trần, hay đầu ra không đọc được (`khong_dung_duoc`).
- Người học thấy khung bài do mã dựng, lời nhắn nêu lý do, lời nhắc thử lại sau, và nút "Thử lại" với mọi lý do.
- `kiem_noi_dung` và thời hạn ghi nhớ 24 giờ bị bỏ. Lỗi được ghi nhớ 60 giây; hết trần hệ thống thì tới hết ngày.

**Căn cứ:**
- Chủ dự án, 2026-10-23: "tôi muốn bài giảng vẫn hiện dù có hỏng, chỉ log lại thôi, đánh giá thì vẫn đánh giá nhưng production phải hoạt động". Ý trượt
  luật: "log lỗi để admin biết thôi". Khi không có bài: "cứ báo lỗi lí do cho user r kêu thử lại sau kèm nút thử lại".
- **SA-21, đo qua Vertex** ([báo cáo](../../report/danh-gia-sa21-2026-10-23.md)): ở thiết kế chính (nhiệt độ 0), 16/50 bài hỏng hẳn ngay lần bấm đầu, doc-4
  tới 8/15. Hầu hết vì K2 và K3 loại hết ý giải thích, rồi K8 đánh trượt cả bài. Lần sinh lại ở nhiệt độ 0 thường trượt y như cũ.

**Considered Options**

- *Hiện ý trượt kèm nhãn "chưa đối chiếu được với sách".* Bị bác theo chủ dự án: chỉ admin cần biết.
- *Chỉ hiện ý đạt, bỏ ngưỡng 2 ý.* Bị bác: nhiều bài gần như trống phần giải thích.
- *Hiện bản trích câu khi không có bài.* Bị bác: giữ quyết định 2026-10-18 của ADR 0018.

**Consequences**

- Người học có thể thấy ý sai so với sách mà không được báo. Rủi ro này được chấp nhận để sản phẩm luôn chạy. Admin thấy log và đánh giá đo tỉ lệ trượt.
- Đánh giá SA-21 đo theo thiết kế cũ: phiếu chấm chỉ có bài qua kiểm. Sau khi cài cần một lượt nhỏ chấm nội dung các bài trượt kiểm, vì người học nay thấy
  chúng.
- Hợp đồng `lecture-2` đổi phía web: `item` đến sớm hơn, `failure.message` mới, `retryable` luôn true, bỏ `kiem_noi_dung`. Trang admin cần đọc log kiểm.
- Bài trượt kiểm vào cache chung. Đổi prompt hay luật kiểm thì khoá bài đổi, bài cũ tự được sinh lại.
