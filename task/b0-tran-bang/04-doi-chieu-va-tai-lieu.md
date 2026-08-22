# 04 — Đối chiếu và tài liệu

**What to build:** Toàn bộ đợt được kiểm trên dữ liệu thật, và người đọc số liệu sau này không nhìn nhầm phân
bố hai đỉnh thành hệ thống hỏng.

Phép kiểm bằng mắt trên dữ liệu thật là thứ đã phát hiện ra **cả năm** đợt vá trước — mỗi lần bộ test đều xanh
và không cái nào thấy gì.

**Blocked by:** 02, 03 — mọi thay đổi phải nằm đủ trước khi đối chiếu mới có nghĩa.

**Status:** completed — 2026-08-21

## Đối chiếu trên tài liệu thật

- [x] Xoá artifact cũ rồi ingest lại từ đầu
- [x] **Tập định danh chunk giống hệt trước đợt này** — đây là tiêu chí mạnh nhất. Tài liệu không có bảng, khối
      lớn nhất 400 token dưới cả ba trần. Nếu tập định danh đổi thì **dừng và tìm ra vì sao** trước khi đóng đợt
- [x] Không chunk nào mang lý do vượt trần, vì không khối nào chạm tới luật mới
- [x] Manifest ghi đủ **ba** trần
- [x] Không thoái lui: cây section vẫn bốn cấp, năm chỗ nối câu qua trang còn nguyên, tham chiếu hình vẫn
      resolve đủ, vị trí ký tự vẫn đúng với mọi chunk

## Đối chiếu trên fixture có bảng

- [x] Ingest fixture DOCX; bảng trong đó **vẫn nguyên một chunk** và vẫn có đúng một tham chiếu bảng

## Tài liệu

- [x] Ghi vào chỗ báo cáo số liệu rằng **phân bố kích thước chunk giờ có hai đỉnh** — quanh 256 cho văn xuôi và
      tới 2048 cho chunk có bảng. Đây là hệ quả có chủ ý, không phải lỗi
- [x] Ghi rõ con số **2048 chưa được kiểm chứng bằng chất lượng truy hồi trên dữ liệu thật** — PDF bảng hiện
      mới xác nhận không còn cắt sớm ở 512. Phải hiệu chỉnh khi có corpus và phép đo retrieval
- [x] Ghi lại **yêu cầu cho bước nhúng**: phải đếm lại token bằng bộ đếm của chính mô hình trước khi gọi API,
      vì bộ đếm ở bước ingest chỉ là xấp xỉ. Bước đó chưa tồn tại nên chỉ ghi, không làm
- [x] Rà `CONTEXT.md`: có thuật ngữ nào cần thêm hoặc sửa vì ba trần không
- [x] Ghi giới hạn đã biết: bảng **vượt** trần bảng thì câu dẫn vẫn bị bỏ lại, vì cắt bảng xảy ra sau khi gom
      nhóm

## Đóng đợt

- [x] Toàn bộ bộ test xanh
- [x] Ghi lại số đo sau đợt để lần sau còn đối chiếu

> **Một việc nên làm luôn:** bốn đợt liên tiếp gặp cùng một hình dạng lỗi — *một thứ trông như đang bảo vệ
> nhưng không bảo vệ gì*: tên test hứa quá, guard chưa từng chạy nhánh chặn, bất biến khẳng định lại thứ code
> tự gán, và giờ là một bất biến **chưa từng tồn tại dưới dạng test có nhãn**. Đáng ghi thành một mục ngắn
> trong tài liệu hướng dẫn, kèm cách phát hiện: **một bài kiểm chưa bao giờ đỏ là một bài kiểm đáng ngờ.**
