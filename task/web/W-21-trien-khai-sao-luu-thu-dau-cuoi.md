# W-21 — Triển khai, sao lưu, thử đầu-cuối, soát an ninh

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 10, "Quyết định kiểm thử" (bộ thử trình duyệt); [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), mục 8
(sao lưu); [ADR 0021](../../doc/adr/0021-phien-dang-nhap-phia-may-chu-trong-cookie.md) (HTTPS, cùng nguồn).
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD (mô hình giả hay phát lại khi thử) · **Chặn bởi:** W-12, W-15, W-17, W-20 · **Trạng thái:**
ready-for-agent

## Vì sao

Đồ án cần một bản chạy được trên một máy chủ để demo và để người dùng thật thử. Bản đó phải khôi phục được khi hỏng, và phải qua một lượt soát an ninh có
danh mục.

## Cần làm

**Đóng gói:**
- docker compose cho triển khai: `api`, `worker`, `db`, và một reverse proxy có HTTPS (ví dụ Caddy, tự lấy chứng chỉ);
- React build phục vụ cùng nguồn;
- bí mật (khoá Gemini, SMTP, mật khẩu cơ sở dữ liệu) chỉ qua biến môi trường hay tệp bí mật, không có trong image hay repo;
- `allowed_origins` là tên miền thật; cookie `Secure`.

**Vận hành:**
- `pg_dump` mỗi đêm cộng bản sao kho tệp, giữ 7 bản;
- **một lần thử khôi phục** lên máy trống, ghi các bước vào sổ tay vận hành;
- `web cleanup` chạy mỗi ngày;
- log có `ref` của lỗi; không ghi câu hỏi, câu trả lời, nội dung tài liệu.

**Bộ thử trình duyệt (Playwright)**, chạy trên bản triển khai thử với mô hình giả hay phát lại:
1. đăng ký → xác minh (đọc thư từ `Mailer` console) → tham gia khoá mẫu → mở trang lộ trình → mở một bài giảng → hỏi trợ lý một câu;
2. chủ khoá tạo link → tài khoản thứ hai tham gia bằng link → thấy cùng bài giảng, tiến độ riêng;
3. tải một tệp (bộ dựng giả) → dự toán → dựng → khoá học `ready`;
4. làm quiz cả lộ trình → nộp → tiến độ đổi.

**Soát an ninh theo danh mục:** chọn các mục cấp 1 của OWASP ASVS về xác thực, phiên, kiểm soát truy cập, kiểm đầu vào, tải tệp, cấu hình. Ghi từng mục đạt
hay không, kèm bằng chứng.

## Tiêu chí nghiệm thu

- [ ] Bản triển khai thử chạy trên HTTPS; cookie có `Secure`; trang chủ, đăng nhập, khoá mẫu dùng được từ điện thoại thật.
- [ ] Bốn luồng Playwright xanh; ảnh chụp hay video lưu ở báo cáo vé.
- [ ] Thử khôi phục từ bản sao lưu lên máy trống: đăng nhập được, khoá học và tiến độ còn đủ.
- [ ] Bảng danh mục an ninh, mỗi mục có bằng chứng; mục không đạt có vé sửa (từ W-24).
- [ ] Quét image và repo không thấy bí mật.

## Ngoài vé

Theo dõi và cảnh báo (Prometheus, Grafana). Nhiều máy chủ.
