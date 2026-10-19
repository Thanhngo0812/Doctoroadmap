# W-13 — các việc triển khai

## Task 1: Chốt hợp đồng (agent chính)
Mô tả: định nghĩa BuildRunner/BuildResult và giao diện pipeline nội bộ để ba Luna làm việc không sửa chồng tệp.
- [x] Hợp đồng có bốn bước, kết quả/chi phí/lỗi/version, hook progress/cancel/record.
- [x] Không phụ thuộc infrastructure/web, không có dự toán sản phẩm.
Kiểm: import `doc2roadmap.application.ports.build`.
Phụ thuộc: không. Tệp: `src/doc2roadmap/application/ports/build.py`. Quy mô: S.

## Task 2: Điều phối một cuốn và kiểm sớm (Luna 1)
Mô tả: chạy bốn bước, cổng chữ/quét/ngôn ngữ, huỷ và kết quả lưu được.
- [x] Chuỗi đầy đủ đúng thứ tự; label-roles không thể bỏ; dry-run không gọi bước mất tiền.
- [x] Cổng từ chối 0 lời gọi; huỷ chặn bước kế; thử lại dùng cache.
- [x] Kết quả lỗi/huỷ/thành công đều chuyển recorder cùng usage thực tế.
Kiểm: `.venv/Scripts/python.exe -m pytest tests/unit/application/test_build_document.py`.
Phụ thuộc: 1. Tệp: use case và test tương ứng. Quy mô: S.

## Task 3: Pipeline thật và cấu hình Vertex (Luna 2)
Mô tả: composition trong tệp mới gọi use case hiện hành, giữ chốt chi và cache, Pha B ghim version.
- [x] Bộ đọc nhẹ, roles→A3/A3′ song song→canonical→roadmap→A12/concept-index/formulas.
- [x] Settings truyền cho cả sinh/embedding; cache miss không gọi mạng khi chưa được phép.
- [x] Usage chỉ tính lời gọi lượt hiện tại, không cộng chi lịch sử trong artifact.
Kiểm: `.venv/Scripts/python.exe -m pytest tests/unit/application/test_build_pipeline.py`.
Phụ thuộc: 1. Tệp: composition_build.py, build_usage.py, test. Quy mô: M.

## Task 4: CLI và bộ dựng giả (Luna 3)
Mô tả: lệnh build dùng cùng port; fake chép artifact phát triển vào doc_id mới và báo bốn bước.
- [x] CLI nhận file/id/dry-run/allow-spend; JSON kết quả không có estimate; exit code phân biệt lỗi.
- [x] Fake không gọi mô hình, dữ liệu đích nạp được, nguồn nguyên vẹn; dry-run không ghi graph.
- [x] Test hợp đồng cùng port và tiến trình/huỷ.
Kiểm: `.venv/Scripts/python.exe -m pytest tests/unit/presentation/test_build_cli.py tests/unit/infrastructure/test_fake_build_runner.py`.
Phụ thuộc: 1 (tích hợp cần 2,3). Tệp: xem plan.md. Quy mô: M.

## Checkpoint: Ba nhánh hội tụ
- [x] Agent chính đọc diff ba nhánh, test riêng đạt, không sửa vùng Pha A.
- [x] Test liên kết fake/real trên bốn bước và transport đạt.

## Task 5: Lưu DB và hiệu chỉnh (agent chính)
Mô tả: SQLite recorder qua callback; đo sáu cuốn phát triển + hai bản tiếng Anh + PDF ảnh.
- [x] Query DB độc lập thấy số thực tế, trạng thái/version đúng cả lỗi và huỷ.
- [x] Có bảng số đo từng tài liệu, ngưỡng có căn cứ và kiểm biên.
Kiểm: test recorder + kiểm đọc thật 0 USD trên allowlist tài liệu phát triển.
Phụ thuộc: 1,2,3. Tệp: recorder/test, script hiệu chỉnh, báo cáo. Quy mô: M.

## Task 6: Nghiệm thu và bàn giao (agent chính)
Mô tả: tích hợp, kiểm hồi quy liên quan và thử đột biến các guard.
- [x] Thấy test đỏ khi bỏ/đổi roles, tắt cổng, nối sai transport; khôi phục và xanh.
- [x] CLI dry-run doc-6 không mạng, không graph mới; cache-only không phát sinh chi.
- [x] Báo cáo chỉ rõ phần chưa đạt/giới hạn cache và yêu cầu không vàng gửi qua chủ dự án; tài liệu theo quyết định bỏ dự toán.
Kiểm: test tập trung W-13 và lân cận, compile/import, git diff --check.
Phụ thuộc: 2–5. Tệp: báo cáo nghiệm thu, W-13/spec đúng phạm vi. Quy mô: M.

## Checkpoint: Hoàn tất
- [x] Mọi tiêu chí được đối chiếu với assertion/lệnh và kết quả thật.
- [x] Báo người dùng những giới hạn còn lại; không nhận nghiệm thu thay phần chưa thực hiện.

## Theo dõi trước khi đóng nghiệm thu chạy thật
- [ ] Có PDF gốc nhap-mon-ml để thay phép đo parse cache bằng phép đo đủ cuốn trên bộ đọc nhẹ.
- [ ] Hoàn tất toàn chuỗi doc-6 từ bộ đọc nhẹ khi có đủ cache, hoặc sau một lượt chi được chủ dự án duyệt. Lượt hiện tại dừng trước khi chi ở concepts, 0 USD.

Mã và kiểm thử 0 USD đã bàn giao; hai dòng trên là giới hạn nghiệm thu, không được tự đánh dấu đã đạt.
