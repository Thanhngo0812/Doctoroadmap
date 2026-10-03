# Vé 23 — tên module chỉ có mã, 2026-10-03

Đã chạy lại **chỉ bước đặt tên module** trên sáu tài liệu phát triển từ A10 v7, tái dùng tên v8, tạo tệp cuối v9. Không chạy lại A8/A9/A10 hay tập giữ lại. Cấu hình tên module `a10-module-titles-v9`; prompt chọn 1–3 tên khái niệm nguyên vẹn khi nền chỉ là mã mục, không có danh sách từ theo ngôn ngữ.

Doc-2, năm tên đổi (các module khác giữ nguyên):

| Module | v8 | v9 |
|---|---|---|
| 011 | Chapter 3 | Chapter 3 — Fundamental theorem of linear maps · identity operator |
| 034 | 6B | 6B — Orthonormal list · Orthonormal basis · Gram-Schmidt procedure |
| 038 | 7C | 7C — positive operator · positive square root |
| 040 | Chapter 7 | Chapter 7 — positive invertible operator · singular values |
| 045 | Chapter 8 | Chapter 8 — Jordan form · Jordan basis |

`kiem_doc_duoc.py`: `ten-nen-chi-co-ma` doc-2 **5 → 0**; năm tài liệu khác **0 → 0**. Mọi loại khác không tăng trên cả sáu; doc-1 còn 6 `ten-la-cau-dai`, 1 `ten-khai-niem-vo-nghia`, 1 `muc-bi-xe` từ trước; nhap-mon-ml còn 3 `ten-la-cau-dai` từ trước. `sequence`, `requires_edges`, `nodes` không đổi. Tên của module khác không đổi. `kiem_tuong_duong_chuoi.py` với đích v9: doc-1 và doc-6 đều 11/11 stage tái dùng, kể cả transport 128 output token của tên module.

Dry-run dự toán 5 lời gọi, 0,00144 USD. Bản chạy hoàn tất ghi 7 lời gọi (2 phản hồi không hợp lệ cần thử lại), **usage hoàn tất 0,000727 USD** theo token trả về. Lượt đầu bị sandbox chặn trước OAuth và để lại bản ghi đặt chỗ bảo thủ trong ledger; những bản ghi đó không phải phản hồi hay chi phí mô hình đã xác nhận.
