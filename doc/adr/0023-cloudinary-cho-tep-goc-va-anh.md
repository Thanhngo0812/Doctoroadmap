# Tệp gốc và ảnh ở Cloudinary, riêng tư; máy chủ chuyển ảnh, trình duyệt không cầm link Cloudinary

**Status:** accepted — 2026-10-18 (chủ dự án chốt: "lưu trữ file trên cloudinary"; chọn phạm vi tệp gốc + ảnh, gói miễn phí hạ trần, riêng tư, ảnh của
đúng trang)

**Cloudinary giữ tệp gốc** (PDF, DOCX người dùng tải lên) **và ảnh hiện cho người học** (ảnh công thức, media đã xác nhận, ảnh trang). Artifact Pha A (đồ
thị, chunk, vector) vẫn ở đĩa máy chủ (ADR 0022).

**Mọi tài sản ở chế độ `authenticated`.** Trình duyệt không bao giờ nhận một link Cloudinary dùng lâu được:
- **ảnh** (trang, công thức, media): máy chủ kiểm thành viên, lấy ảnh bằng link ký phía máy chủ, rồi chuyển cho trình duyệt;
- **cả tệp:** máy chủ kiểm thành viên rồi chuyển hướng tới link tải riêng tư có `expires_at` vài phút.

**"Đọc trang p"** mở ảnh của đúng trang, do Cloudinary cắt từ PDF, một cỡ duy nhất.

**Cỡ tệp tải lên tối đa bằng giới hạn của gói miễn phí** (khoảng 10 MB; số đúng lấy ở trang gói). Máy chủ tải lên Cloudinary sau khi kiểm tệp; không cho
trình duyệt tải thẳng.

**Căn cứ:**
- Chủ dự án chọn Cloudinary và gói miễn phí.
- Link có chữ ký của Cloudinary chống sửa tham số nhưng không tự hết hạn; link hết hạn bằng token là tính năng gói cao. Chuyển ảnh qua máy chủ là cách giữ
  được luật "người bị xoá khỏi khoá mất quyền ngay" (spec chức năng mục 6) mà không cần gói cao.
- Ảnh trang nhẹ hơn cả cuốn, mở được trên điện thoại, và Cloudinary cắt trang sẵn, nên không phải tự dựng ảnh trang.
- Số đo 2026-10-18: sáu cuốn phát triển ≤ 3,2 MB; 0/16 sách học của D-01 quá 10 MB; 11/20 sách mới quá 10 MB, phần lớn là bản quét, vốn bị từ chối. Trần
  10 MB chủ yếu chặn bản quét.

**Considered Options**

- *Đĩa máy chủ cho mọi thứ.* Gọn nhất, nhưng chủ dự án chọn Cloudinary.
- *Đẩy cả artifact Pha A lên Cloudinary.* Bị bác: phải viết lại phần đọc ghi artifact của Pha A (việc của phiên khác), và mỗi lần nạp đồ thị phải qua mạng.
- *Tài sản công khai với URL khó đoán.* Bị bác: ai có URL thì mở được mãi, kể cả người đã bị xoá khỏi khoá.
- *Đưa link Cloudinary có chữ ký thẳng cho trình duyệt.* Bị bác vì link không hết hạn.
- *Mở cả PDF ở trang p.* Thành nút phụ "Mở cả tệp"; trên điện thoại nhiều trình duyệt không nhảy đúng trang.

**Consequences**

- Có port `MediaStore` (tải lên, lấy về, cắt trang, link tải có hạn, xoá), bản giả trong bộ nhớ cho test, bản Cloudinary cho dev và triển khai.
- Bài giảng trong cache chỉ chứa khoá tài sản; gateway đổi thành đường của máy chủ lúc trả bài.
- Có bảng ánh xạ khoá tài sản sang `public_id` (spec cơ sở dữ liệu).
- Máy chủ chịu băng thông của ảnh; đặt `Cache-Control: private, max-age=300`.
- Xoá tài khoản, xoá khoá, dọn mồ côi phải xoá cả tài sản trên Cloudinary.
- Sao lưu: `pg_dump` không gồm Cloudinary. Cloudinary là nơi giữ bản chính của tệp gốc; mất tài khoản thì mất tệp gốc, nhưng artifact đã dựng vẫn còn trên
  đĩa.
- Tài khoản miễn phí phải bật "Allow delivery of PDF and ZIP files" cho nút "Mở cả tệp".
