# W-03 — Logo email Cloudinary và xác nhận Gmail thật

## Yêu cầu và thay đổi

Chủ dự án xác nhận: “tôi kiểm tra mail thật rồi, hoạt động tốt nhưng ảnh logo ko hiện chắc do local”, đồng thời cấp ảnh Cloudinary và yêu cầu thêm vào env. Đây là bằng chứng kiểm giao/nhận thư thật do chủ dự án báo; nhóm web không tự gửi thêm thư.

Mã bản sửa: **`1a658ca64d675e30276cb44bfb95f40cee56a748`**, nhánh `work/w03-email-recovery`.

- Thêm `WAYFINDER_EMAIL_LOGO_URL`, chỉ nhận URL HTTPS không có credential hoặc khoảng trắng. Cấu hình được truyền từ WebSettings qua composition/AuthPolicy vào cả ba mẫu thư; thuộc tính HTML được escape. Khi để trống, giữ logo từ origin của ứng dụng.
- Đã đặt URL được cấp vào **`src/web/.env` của thư mục chung và worktree W-03**. Chỉ sửa khoá này, không đưa env vào commit hoặc in credential. `.env.example` có khoá trống và README có hướng dẫn.
- Ảnh dùng trực tiếp: `https://res.cloudinary.com/dfcb3zzw9/image/upload/v1792483249/Artboard_13_ousztc.png`. Không đổi URL của nút xác minh/reset; các nút vẫn dùng `WAYFINDER_PUBLIC_BASE_URL`.
- Khởi động lại máy chủ local với mã và env mới; health và PostgreSQL đều `ok`. Chỉ thư gửi mới dùng cấu hình mới; thư đã gửi không bị sửa lại.

## Bằng chứng kiểm

- RED thực: **10 test fail** trên hành vi cũ (3 mẫu thư không nhận logo, 6 URL sai không bị từ chối, 1 kiểm xuyên env → composition → thư không có ảnh cloud). [JUnit](w03-evidence/logo-red.xml). Lần nhập bộ lọc có khoảng trắng trước đó chỉ lỗi tham số, không được tính là RED nghiệp vụ.
- GREEN: **41 test Mailer/composition đạt**, gồm 10 kiểm mới; test xuyên composition chạy PostgreSQL thật và Mailer giả, khẳng định cả ba thư có logo cloud nhưng liên kết hành động vẫn trỏ local. [JUnit](w03-evidence/logo-green.xml).
- Tải ảnh thật: HTTP **200**, PNG **2.216 × 2.215**, 30.164 byte. [Metadata](w03-evidence/cloudinary-logo.json).
- Chromium tải trực tiếp URL Cloudinary trong mẫu thư ở **390 và 1280 px**, `naturalWidth > 0`, không tràn ngang; không thay ảnh bằng mock. [Audit](w03-evidence/cloudinary-email-browser.json), [ảnh mobile](w03-evidence/cloudinary-email-390.png), [ảnh desktop](w03-evidence/cloudinary-email-1280.png). Đây là kiểm render Chromium, không tuyên bố đã kiểm ảnh mới qua Gmail proxy.
- `luna_media` soát diff chỉ đọc và approve, không có finding bắt buộc sửa: cấu hình HTTPS, propagation, escape, fallback và link hành động đúng; không đọc env hoặc chạy SMTP/DB/network.

## Cổng hồi quy cuối

Đã chạy cổng đầy đủ qua runner với PostgreSQL bắt buộc trên mã bản sửa: **2.085 đạt, 0 lỗi, 1 Cloudinary live bỏ qua**, 311,22 giây, process exit code **0**; có 8 cảnh báo deprecation thư viện. [JUnit](w03-evidence/logo-full-python.xml), [log](w03-evidence/logo-full-python.log), [tổng hợp](w03-evidence/logo-acceptance-summary.json). Không tắt kiểm, đổi assertion hoặc dựng lại fixture để lấy xanh.

Lệnh từ gốc worktree:

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w03-cloud-logo --junitxml=report/w03-evidence/logo-full-python.xml
```

Frontend không đổi so với commit nghiệm thu `e940633`; kết quả React **62 đạt** và build đạt trong [báo cáo nghiệm thu](web-w03-nghiem-thu-2026-10-20.md) vẫn áp dụng cho cùng mã frontend. Không chạy lại các test frontend trong lượt sửa chỉ ở backend này.

Không gọi mô hình, chi phí mô hình **0 USD**. Không sửa vé/handoff, không làm W-06, không tự ghép main, không dọn cache hoặc worktree.
