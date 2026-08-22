# 06 — ADR 0002, từ điển và đối chiếu cuối

**What to build:** Quyết định kiến trúc nói đúng phạm vi nó đang chi phối, từ điển thuật ngữ có chỗ cho bảng,
và toàn bộ đợt được kiểm trên tài liệu thật.

Phép kiểm bằng mắt trên dữ liệu thật là thứ đã phát hiện ra **cả bốn** đợt vá trước — mỗi lần bộ test đều xanh
và không cái nào thấy gì. Vì vậy nó là một ticket riêng, không phải một dòng nghiệm thu bị lướt qua.

**Blocked by:** 03, 04, 05 — mọi thay đổi phải nằm đủ trước khi đối chiếu mới có nghĩa.

**Status:** completed — 2026-08-21

## ADR 0002

- [x] Mở rộng phạm vi từ "hình" sang "**hình và bảng**": quyết định thứ ba — *tham chiếu đứng ngoài khoá băm
      chunk* — nay chi phối cả hai
- [x] Ghi rõ **điểm khác nhau** giữa hình và bảng và vì sao nó không phá tính đối xứng: hình cần file vì byte
      nhị phân không sống được trong văn bản; nội dung bảng thì đã nằm sẵn trong văn bản dưới dạng markdown
- [x] Ghi quyết định "cấu trúc hàng cột ở nguyên trong cây parse", kèm phương án bị loại là dựng một tầng lưu
      trữ riêng cho bảng chỉ để đối xứng hình thức
- [x] Không viết ADR mới — đây là mở rộng của một quyết định đã có, tách ra sẽ làm hai tài liệu nói về cùng
      một nguyên tắc

## Từ điển thuật ngữ

- [x] Thêm **bảng** và **tham chiếu bảng**, theo đúng khuôn của các mục sẵn có, mỗi mục kèm phần *tránh dùng*
- [x] Rà lại mục **Chunk**: nó vừa được sửa ở đợt trước, kiểm xem có cần nhắc tới tham chiếu bảng không
- [x] Rà lại mục nói về bộ tách câu nếu có — nó không còn gắn với một ngôn ngữ

## Đối chiếu trên tài liệu thật

- [x] Xoá artifact cũ rồi ingest lại từ đầu
- [x] **Tập định danh chunk giống hệt trước đợt này** — đây là tiêu chí mạnh nhất của đợt. Tài liệu không có
      bảng, bộ tách câu chưa từng chạy trên nó, và cả hai trường mới đều ngoài khoá băm. Nếu tập định danh đổi
      thì **dừng và tìm ra vì sao** trước khi đóng đợt
- [x] Danh sách tham chiếu bảng rỗng ở mọi chunk, vì tài liệu không có bảng
- [x] Không cảnh báo "bộ tách bó tay" nào, vì mọi khối đều dưới trần
- [x] Manifest ghi đủ: phiên bản adapter mới, phiên bản thuật toán `section-id-v5`
- [x] Không thoái lui: cây section vẫn bốn cấp, năm chỗ nối câu qua trang còn nguyên, tham chiếu hình vẫn
      resolve đủ, vị trí ký tự vẫn đúng với mọi chunk

## Đối chiếu trên fixture có bảng

- [x] Ingest fixture DOCX và kiểm bảng duy nhất trong đó có định danh
- [x] Chunk chứa bảng có đúng một tham chiếu, trỏ đúng vị trí dòng đầu của bảng markdown

## Đóng đợt

- [x] Toàn bộ bộ test xanh
- [x] Ghi lại số đo sau đợt để lần sau còn đối chiếu 

> **Một việc nên làm luôn ở ticket này:** ba đợt liên tiếp gặp cùng một hình dạng lỗi — *một thứ trông như
> đang bảo vệ nhưng không bảo vệ gì* (F4 tên test hứa quá, F23 guard chưa từng chạy nhánh chặn, I15 bất biến
> khẳng định lại thứ code tự gán). Đáng ghi thành một mục ngắn trong tài liệu hướng dẫn của dự án, kèm cách
> phát hiện: **một bài kiểm chưa bao giờ đỏ là một bài kiểm đáng ngờ.**
