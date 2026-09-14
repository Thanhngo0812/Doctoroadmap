# ADR 0007: 2a đề xuất quan hệ kiểu mở, `subtype_of` là một kiểu trong đó

**Trạng thái:** accepted  
**Ngày:** 2026-09-14

## Bối cảnh

Trước đây, đầu ra phân hoạch của 2a chỉ có một loại cạnh là `subtype_of`. Đo trên bốn tài liệu:
- 10 trong 19 cạnh `subtype_of` sai có lý do tả một quan hệ khác loại, như *"is used to estimate"*, *"a statistic of"*,
  *"an application of"*. Mô hình bị ép chọn vì khuôn chỉ có một chỗ để ghi.
- 48/246 lý do của node đứng riêng tả quan hệ, nhưng thông tin đó chỉ nằm dưới dạng chữ trong nhật ký.
- 10/11 cặp *liên quan* bị gắn sai không có cạnh A3 nào. A3 đọc từng section, còn cụm 2a gom tên giống nhau ở khắp tài
  liệu.
- Cấm bằng prompt ("bộ phận, công cụ… không phải cha–con") chỉ làm mô hình im lặng: mất 8 cặp cha–con đúng.

## Quyết định

1. **Quan hệ kiểu mở.** Đầu ra phân hoạch có `relations[{source, target, edge_type, chunk_ids, reason}]` giữa các
   nhóm ở hai node khác nhau. `subtype_of` chỉ là một kiểu, nghĩa là "là một loại / dạng / biến thể / trường hợp riêng".
   Kiểu không được là `requires` hay đồng nghĩa, cũng không được là kiểu dành cho media.
2. **Luật nhất quán, không cần nhãn.** Có hai trường hợp coi là mâu thuẫn:
   - quan hệ nối hai nhóm mà chính mô hình đặt chung node (R1);
   - quan hệ đồng nhất nối hai node tách riêng (R2).

   Gặp mâu thuẫn thì mô hình phán lại một lần; vẫn mâu thuẫn thì hoãn cả cụm.
3. **Nguồn gốc cạnh.** Mọi cạnh ghi `origins` là `a3`, `2a` hoặc cả hai. 2b coi mọi quan hệ 2a là đề xuất.

Prompt phân hoạch là v3. Mô hình vẫn là `gemini-3.1-flash-lite`.

## Số đo và quyết định của chủ dự án

| | Mặc định (v1) | v3 + luật nhất quán |
|---|---:|---:|
| Precision / recall / F1 gộp | 1,000 / 0,660 / 0,795 | 0,946 / 0,745 / 0,833 |
| Precision `subtype_of` | 0,635 | 0,658 |
| Quan hệ khác `subtype_of` | — | 35, mẫu 30 cho 70% đúng |

Theo luật chấm viết trước (precision gộp ≥ 0,95), bản này trượt đúng một ca gộp sai. **Chủ dự án chấp nhận**, đổi một
chút precision lấy recall, F1 và quan hệ kiểu mở.

Sau đó, mẫu xác nhận và lượt chạy kho chính đều qua ngưỡng xác nhận precision gộp ≥ 0,93, với cùng số 35 / 2 / 12.
Bản này thành mặc định từ 2026-09-14 (commit gộp `c418499`). Với `temperature` 0, ba lượt chạy cho quyết định giống
hệt nhau, nên chúng chứng minh tái lập được chứ không đo biến động.

## Hệ quả

- Precision gộp không còn tuyệt đối. Còn hai kiểu gộp sai hệ thống không mang tín hiệu mâu thuẫn: tên chung với tên
  riêng (`Đường hồi quy mẫu Y theo X` / `Đường hồi quy mẫu`), và các bài toán anh em (`Bài toán phân loại` / `Bài toán
  phân cụm`).
- Lượt thử lại hay tách cả node, làm mất cặp đúng (F83). Sửa lời báo là đổi nội dung gửi cho mô hình, nên cần nhãn mới.
- Đồ thị có thêm quan hệ giữa các tên na ná ở những section khác nhau, những cặp mà A3 không thấy.
- Mọi lần đổi prompt phân hoạch đều đổi cách gộp của flash-lite. Thêm việc cho lời gọi phân hoạch là đánh cược với
  precision gộp.

## Phương án đã loại

- **Cấm bằng prompt:** mô hình im lặng thay vì chọn đúng kiểu, và mất cặp đúng.
- **Cho agent tự đọc chunk bằng tool:** phá thiết kế một lời gọi mỗi cụm, trong khi đầu vào không phải chỗ tắc.
- **Hai lời gọi:** giữ nguyên prompt phân hoạch v1 (precision gộp 1,000 theo cấu trúc) và hỏi quan hệ bằng một lời gọi
  riêng. Đây là phương án reviewer đề nghị. Chủ dự án chọn bản đã chạy thật và đã có số. Nếu precision gộp thành vấn đề ở
  2b, đây là đường lui đầu tiên.
