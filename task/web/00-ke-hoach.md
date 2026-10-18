# Web WayFinder — kế hoạch vé

**Nguồn chân lý:**
- [spec chức năng web](../../doc/web-chuc-nang-spec.md), cùng ADR [0020](../../doc/adr/0020-khoa-hoc-la-don-vi-chia-se-du-lieu-hoc-theo-nguoi-va-cuon.md) và
  [0021](../../doc/adr/0021-phien-dang-nhap-phia-may-chu-trong-cookie.md);
- [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), cùng ADR [0022](../../doc/adr/0022-postgresql-cho-du-lieu-web-artifact-o-kho-tep-hang-doi-bang-bang.md);
- [spec thiết kế giao diện](../../doc/web-thiet-ke-giao-dien-spec.md) (font Be Vietnam Pro, logo và favicon WayFinder, màu, bố cục từng trang);
- [spec Pha B2](../../doc/pha-b2-spec.md) cho mọi hợp đồng nội dung học;
- [ADR 0023](../../doc/adr/0023-cloudinary-cho-tep-goc-va-anh.md): tệp gốc và ảnh ở Cloudinary (gói miễn phí, riêng tư), artifact Pha A ở đĩa.

**Stack:** React (Vite, TypeScript) + FastAPI + PostgreSQL 16 + Cloudinary (tệp gốc và ảnh). React phục vụ cùng nguồn với API.

**Quy trình:** Claude soạn vé; chủ dự án giao nhóm web và nhân viên; người soát (Claude, hay nhân viên cấp cao theo SA-45 khi Claude vắng) kiểm theo tiêu
chí của vé. Vé sửa sau soát đánh số tiếp từ W-24.

**Số vé:** tiền tố `W-` để không trùng dãy `SA-` (SA-45 giữ số 46 trở đi cho vé sửa Pha B).

## Luật chung của mọi vé

- **Test thấy đỏ trước** trên bản sai rồi mới xanh (AGENTS.md mục 5). Đường nối chính là **tầng dịch vụ** với kho bộ nhớ, đồng hồ giả, `Mailer` giả,
  `BuildRunner` giả, và Pha B chạy trên mô hình giả theo kịch bản (spec chức năng, "Quyết định kiểm thử"). Tầng HTTP chỉ kiểm thứ sống ở HTTP.
- **Mỗi vé một lát dọc:** di trú cơ sở dữ liệu, dịch vụ, API, giao diện React, test. Vé chỉ xong khi chạy được từ trình duyệt.
- **Mỗi vé thêm bảng thì thêm đúng một bản di trú Alembic,** tên theo vé. Không sửa di trú đã vào nhánh chính.
- **Test PostgreSQL:** lệnh kiểm của vé chạy cả bản PostgreSQL (dịch vụ `db-test` trong docker compose). Thiếu PostgreSQL thì coi là **hỏng**, không phải
  "bỏ qua".
- **Giao diện:**
  - theo spec thiết kế: token màu, chữ, khoảng cách, trạng thái rỗng, đang tải, lỗi;
  - chữ hiện cho người dùng là tiếng Việt;
  - mỗi vé có giao diện thì kèm ảnh chụp màn hình ở cỡ điện thoại (390 px) và máy tính (1280 px) trong báo cáo vé.
- **Ví dụ JSON thật** của mọi điểm cuối mới trong báo cáo vé, cho nhóm React.
- **Không dùng tập giữ lại:** máy chủ web không nạp `d01-t01`, `d01-t02`, `document-data/test/`, `Desktop\d02-tap-khoa`. Dữ liệu dev là sáu cuốn phát triển.
  Không nhập `artifacts/phase_b/live.json` (có cache của tập giữ lại); không in phần `cache` của nó.
- **Tiền:** chỉ `gemini-3.1-flash-lite`. Mọi lượt có tiền dry-run trước, chủ dự án duyệt. Ngoài W-15, mọi vé là 0 USD.
- **Commit chỉ đường dẫn của vé** (`git commit -m … -- <tệp>`). Không sửa tệp của phiên pha A; cần đổi mã Pha A thì ghi yêu cầu vào báo cáo vé.
- **Lưu dần:** làm tới đâu commit tới đó; báo cáo vé có dòng trạng thái ở đầu.
- **Cloudinary:**
  - test dùng `MediaStore` giả, không gọi Cloudinary;
  - `CLOUDINARY_URL` chỉ ở `.env`, không commit, không dán vào báo cáo hay chat; thiếu thì hỏi chủ dự án;
  - dev và triển khai tách bằng thư mục `wayfinder/dev`, `wayfinder/prod`;
  - trình duyệt không bao giờ nhận link Cloudinary dùng lâu được (ADR 0023).
- **Môi trường:** `.venv/Scripts/python.exe`; `pytest` cần `--basetemp` trỏ vào thư mục ghi được, kèm `-p no:cacheprovider`.

## Phụ thuộc vào vé Pha B2

Phần học (W-07…W-10) gọi use case Pha B2. Vé Pha B2 chưa xong thì gateway gọi hợp đồng đang có, ghi rõ trong báo cáo vé, và đổi khi vé B2 xong. Hợp đồng
còn đổi; nhóm web đã được báo.

## Bảng vé

| vé | việc | chặn bởi | trạng thái |
|---|---|---|---|
| [W-01](W-01-nen-web-fastapi-react-postgres.md) | nền: FastAPI, React, PostgreSQL, Alembic, đường nối test, token giao diện | — | ready-for-agent |
| [W-02](W-02-dang-ky-dang-nhap-phien.md) | đăng ký, đăng nhập, đăng xuất, phiên cookie, CSRF, giới hạn thử | W-01 | ready-for-agent |
| [W-03](W-03-xac-minh-email-quen-mat-khau.md) | xác minh email, quên mật khẩu, cổng gửi thư | W-02 | ready-for-agent |
| [W-04](W-04-ho-so-doi-mat-khau-dang-xuat-moi-noi.md) | hồ sơ, đổi mật khẩu, đăng xuất mọi nơi | W-02 | ready-for-agent |
| [W-05](W-05-kho-pha-b-postgresql.md) | kho Pha B trên PostgreSQL, `single_flight` liên tiến trình, nới port sổ chi | W-01 | ready-for-agent |
| [W-06](W-06-khoa-mau-khoa-hoc-cua-toi-gateway.md) | khoá mẫu, "Khoá học của tôi", `LearningGateway`, test người ngoài khoá | W-02, W-05 | ready-for-agent |
| [W-07](W-07-trang-lo-trinh-tien-do.md) | trang lộ trình và tiến độ | W-06, SA-34 | ready-for-agent |
| [W-08](W-08-trang-hoc-bai-giang-doc-trang.md) | trang học: bài giảng stream, "Đọc trang p" | W-07, SA-39, SA-40, SA-41 | ready-for-agent |
| [W-09](W-09-tro-ly-va-phien.md) | trợ lý và phiên chat | W-07, SA-32, SA-33, SA-42 | ready-for-agent |
| [W-10](W-10-quiz-tai-lieu-thu-vien.md) | quiz, tài liệu, thư viện | W-07, SA-35, SA-37 | ready-for-agent |
| [W-11](W-11-chia-se-link-thanh-vien.md) | chia sẻ bằng link, thành viên, rời khoá | W-06 | ready-for-agent |
| [W-12](W-12-moi-qua-email.md) | mời qua email, lời mời trong ứng dụng | W-03, W-11 | ready-for-agent |
| [W-13](W-13-dung-mot-cuon-o-loi.md) | use case `build_document` ở lõi | — | ready-for-agent |
| [W-14](W-14-tai-sach-len-ban-dung.md) | tải sách lên, kiểm sớm, dự toán, hàng đợi, worker, bộ dựng giả | W-03, W-06 | ready-for-agent |
| [W-15](W-15-noi-bo-dung-that-do-usd-cuon.md) | nối bộ dựng thật, đo USD/cuốn và phút/cuốn | W-13, W-14 | ready-for-agent |
| [W-16](W-16-muc-dung.md) | trang mức dùng và dải hết trần | W-09, W-14 | ready-for-agent |
| [W-17](W-17-quan-tri.md) | quản trị: người dùng, bản dựng, chi, khoá mẫu, nhật ký | W-14, W-16 | ready-for-agent |
| [W-18](W-18-tien-do-thanh-vien-cho-chu-khoa.md) | tiến độ tổng hợp của thành viên cho chủ khoá | W-07, W-11 | ready-for-agent (chờ câu hỏi mở 3) |
| [W-19](W-19-bao-loi-noi-dung.md) | báo lỗi nội dung | W-08, W-09, W-10 | ready-for-agent |
| [W-20](W-20-xoa-tai-khoan-xoa-khoa-hoc.md) | xoá tài khoản, xoá khoá học | W-11, W-14 | ready-for-agent |
| [W-21](W-21-trien-khai-sao-luu-thu-dau-cuoi.md) | triển khai, sao lưu, thử đầu-cuối, soát an ninh | W-12, W-15, W-17, W-20 | ready-for-agent |
| [W-22](W-22-ban-figma.md) | bản Figma theo spec thiết kế | — | ready-for-agent |
| [W-23](W-23-doi-chieu-figma-va-giao-dien.md) | đối chiếu Figma với giao diện React, chỉnh lệch | W-22, W-08, W-09, W-10 | ready-for-agent |

## Thứ tự đề xuất

- **Song song ngay:** W-01 (nhóm web), W-13 (nhân viên lõi), W-22 (người thiết kế).
- **Sau W-01:** W-02 rồi W-03, W-04; W-05 song song.
- **Sau W-06:** phần học W-07 → W-08, W-09, W-10 (bám vé Pha B2); W-11 → W-12; W-14 → W-15.
- **Cuối:** W-16, W-17, W-18, W-19, W-20, rồi W-21 và W-23.

## Câu hỏi mở của chủ dự án

Bảy câu ở cuối spec chức năng, đều có mặc định. Nhân viên làm theo mặc định. W-18 chờ câu 3 trước khi bật cho người dùng thật; cài thì cứ cài, tắt được bằng
cấu hình.
