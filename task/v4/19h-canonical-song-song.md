# 19h — Canonical chạy song song nhiều hơn

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 2 mục 4.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 19f (cùng đoạn mã neo) · **Trạng thái:** chờ 19f

## Vì sao

Canonical chỉ chạy 4 lời gọi đồng thời. Đường neo của canonical còn chặn theo lô 8 khái niệm. Phần LLM của canonical doc-4 ước có thể từ khoảng 540 giây
xuống khoảng 140 giây (nghiên cứu mục 4). Mục cấu hình `vertex_concurrency` không được đọc ở đâu.

## Cần làm

- Số lời gọi đồng thời mặc định của canonical là khoảng 16, vẫn đi qua bộ giới hạn tốc độ hiện có.
- Bỏ rào lô 8 khái niệm ở đường neo của canonical. Giữ checkpoint và thứ tự ghi nhật ký tất định.
- Xoá mục cấu hình `vertex_concurrency`; cập nhật `.env.example`.
- Không đổi khoá cache.

## Nghiệm thu

- [ ] Test với mô hình giả có độ trễ: số lời gọi đồng thời tối đa đạt mức cấu hình; payload và nhật ký giống hệt khi chạy tuần tự.
- [ ] Bộ giới hạn tốc độ vẫn được tôn trọng.
- [ ] Khoá cache không đổi. Toàn bộ test qua.
