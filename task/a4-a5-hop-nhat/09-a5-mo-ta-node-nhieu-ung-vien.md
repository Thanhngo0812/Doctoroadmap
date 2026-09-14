# 09 — A5: mô tả chuẩn cho node nhiều ứng viên

**What to build:** `a4` viết mô tả chuẩn cho mọi node có từ hai ứng viên trở lên: 1–4 câu, **mỗi câu kèm `chunk_id`
trích dẫn**, viết theo ngôn ngữ chủ đạo của tài liệu, gắn cờ khi các nguồn mâu thuẫn nhau. `first_order_index` của node
giờ lấy từ chunk **định nghĩa hoặc giảng** node mà A5 chỉ ra, thay cho giá trị tạm của ticket 02.

## Vì sao đọc chunk nguồn, không đọc draft

Draft của A3 là câu *vai trò tại chỗ được nhắc*, và có draft sai hẳn ngay trong nhóm đúng tên — một draft của
`Kém khớp` tả quá khớp. Tổng hợp từ draft là chép lại lỗi, kể cả lỗi trái nghĩa. Chi phí không phải lý do để tiết kiệm:
đọc toàn bộ chunk nguồn của mọi node trên corpus chỉ khoảng 87 nghìn token.

Còn một lý do nữa: 2b sẽ suy tiên quyết. Mô tả do mô hình viết tự do là đường để kiến thức nền của mô hình lọt vào đồ
thị. Trích dẫn từng câu là thứ code giữ được; cờ mâu thuẫn là van phát hiện gộp nhầm (spec D8).

**Blocked by:** 02 — Viên đạn vạch đường: lớp tên → bảng node canonical, lệnh `a4`

**Status:** done

**Cập nhật triển khai 2026-09-11:** Đã triển khai synthesis/citation/defining chunks/fallback và test offline; chất lượng mô tả thật chờ task 14.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] **Ngôn ngữ chủ đạo**: bỏ chunk thuần bảng/code/công thức/hình rồi lấy đa số theo token; nếu không còn văn xuôi
      thì dùng toàn bộ chunk. Một chunk là tiếng Việt khi ≥ 20% số từ mang dấu; cả bốn tài liệu ra `vi`.
- [x] **Đầu vào** mỗi node: tên chuẩn, alias, ký hiệu, kiểu, và toàn văn chunk bằng chứng theo thứ tự tài liệu, trần
      khoảng 4k token — vượt trần thì giữ câu bằng chứng cộng chunk sớm nhất. Draft không làm nguồn.
- [x] **Đầu ra**: 1–4 câu **theo lượng bằng chứng**, mỗi câu kết thúc bằng một hoặc nhiều `chunk_id`; được phép ghi
      *"tài liệu không nói thêm"*. Kèm `defining_chunk_ids` ⊆ trích dẫn. Nguồn mâu thuẫn ⇒ **không hoà giải**, gắn cờ
      `nghi_gop_nham` kèm lý do.
- [x] **Code kiểm**: mọi `chunk_id` trích dẫn thuộc node; `defining_chunk_ids` ⊆ trích dẫn; số câu 1–4. Sai ⇒ thử lại
      một lần; vẫn sai ⇒ giữ draft của ứng viên neo, gắn cờ, ghi nhật ký.
- [x] `first_order_index` = `order_index` nhỏ nhất trên `defining_chunk_ids`; rỗng ⇒ nhỏ nhất trên mọi ứng viên.
      `first_mention_index` = nhỏ nhất trên mọi ứng viên.
- [x] Media không qua A5. Node một ứng viên chưa qua A5 ở ticket này (ticket 10).
- [x] Model A5 cấu hình **riêng**, mặc định cùng model A3. Model, tham số, khung prompt (tiếng Anh), schema và luật ngôn
      ngữ vào `prompt_hash` và config hash. Mỗi node một phiên một lượt qua cổng hội thoại LLM hiện có.
- [x] Nhật ký ghi mỗi lời gọi A5: node, model, `prompt_hash`, băm dữ liệu gửi đi, số lần thử lại, kết quả kiểm.
- [x] **Manifest**: số node đã tổng hợp, số lần giữ draft vì lỗi, số cờ `nghi_gop_nham`, ngôn ngữ chủ đạo.
- [x] **Seam ①**, người viết giả viết tay, không chạm mạng:
    - trả câu có trích dẫn hợp lệ ⇒ mô tả được lưu;
    - trả `chunk_id` ngoài node hai lần ⇒ giữ draft và gắn cờ (thấy hỏng khi bỏ guard);
    - `first_order_index` đi theo `defining_chunk_ids`, không theo ứng viên sớm nhất;
    - nguồn mâu thuẫn ⇒ có cờ `nghi_gop_nham`, mô tả không bị ép hoà giải.
- [x] **Seam ②**: luật ngôn ngữ (chunk lai, ngưỡng 20%, hoà theo token); kiểm trích dẫn.
- [x] Toàn bộ test hiện có vẫn xanh.
