# W-15 — Nối bộ dựng thật; đo USD/cuốn và phút/cuốn

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 4, 8, câu hỏi mở 2; vé [W-13](W-13-dung-mot-cuon-o-loi.md), [W-14](W-14-tai-sach-len-ban-dung.md).
**Ai:** nhân viên lõi chạy · người soát và Claude đọc số · **Chi phí mô hình:** một cuốn mới, ước dưới 3 USD theo D-01; dry-run trước, **chủ dự án duyệt**
· **Chặn bởi:** W-13, W-14 · **Trạng thái:** ready-for-agent

## Vì sao

Bản demo không giới hạn khâu dựng (chủ dự án chốt 2026-10-18), nhưng chuỗi gộp hiện hành chưa có số USD/cuốn đo trên một cuốn mới hoàn toàn. Cần số thật
để chủ dự án biết một cuốn tốn bao nhiêu, và để biết bật trần ở mức nào nếu có lạm dụng. Cũng cần chạy trọn đường web với bộ dựng thật một lần.

## Cần làm

- **Nối dây:** worker dùng `BuildRunner` thật khi bật cấu hình `build_runner = real`; mặc định vẫn là bản giả ở dev.
- **Đường gọi thật:** worker tạm dùng Vertex AI (`DOC2ROADMAP_LLM_TRANSPORT=vertex`), cả sinh và embedding (chủ dự án cập nhật 2026-10-19). Kiểm cấu hình
  trước dry-run/lượt thật, ghi transport trong báo cáo cùng số đo; không chép bí mật. Chỉ chuyển Developer API khi chủ dự án yêu cầu chuẩn bị demo.
- **Lượt 1, 0 USD:** tải doc-6 qua web. Phải dùng lại bản dựng hay cache sẵn có, nên chi thật xấp xỉ 0. Kiểm trọn đường đi: trạng thái, thư, khoá học.
- **Lượt 2, có tiền:** chọn **một** cuốn tiếng Việt cỡ vừa trong `document-data/train/`, chưa có artifact chuỗi gộp.
  - **Không** dùng `document-data/test/` hay cuốn của tập giữ lại.
  - Ghi tên tệp và số trang vào báo cáo **trước** khi chạy.
  - Chạy dry-run nội bộ kiểm phụ thuộc; người làm chuẩn bị riêng dự toán/trần đề nghị cho chủ dự án duyệt, rồi mới chạy qua web. `BuildRunner`/app không
    tính dự toán theo cập nhật W-13; không tự bỏ bước duyệt tiền vì app đã bỏ dự toán.
- **Đo** cho mỗi lượt:
  - USD theo bước (từ sổ chi `purpose = build` và manifest đồ thị);
  - phút theo bước, tách phần chờ embedding;
  - số lời gọi mô hình;
  - usage_complete và các giới hạn số đo; ghi riêng trần được duyệt so với chi thực, không yêu cầu app có dự toán.
- **Đọc tận nơi:** mở khoá học của lượt 2 trên web; đọc tên module và vài bài giảng (phát lại hay mô hình giả, 0 USD). Ghi nhận xét chất lượng; không chặn vé.

## Tiêu chí nghiệm thu

- [ ] Lượt 1 qua web xong với chi ≈ 0, khoá học `ready`, thư "bản dựng xong" trong `Mailer` console.
- [ ] Lượt 2 có dry-run, có xác nhận duyệt của chủ dự án (trích tin nhắn hay ghi chú), rồi mới chạy.
- [ ] Bảng số: USD/cuốn, phút/cuốn theo bước, số lời gọi/token thực và cờ thiếu usage; trần đã duyệt so với chi thực. Không lấy chi lịch sử trong manifest
  làm chi của lần cache mới; không yêu cầu chức năng dự toán trên app.
- [ ] Báo cáo ghi đúng transport thực tế: hiện tạm dùng `vertex` cho sinh/embedding; nếu chủ dự án đã chỉ thị chuyển để demo thì trích chỉ thị và ghi
  cấu hình mới. Không tự chuyển transport.
- [ ] Đề xuất mức `system_daily_build_max_usd`, `build_monthly_max` **để sẵn khi cần bật**, theo số đo. Claude đọc rồi báo chủ dự
  án.
- [ ] Không mở tập giữ lại.

## Ngoài vé

Tối ưu chi phí khâu dựng (việc của phiên pha A).
