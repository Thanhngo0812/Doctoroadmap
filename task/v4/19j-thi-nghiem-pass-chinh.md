# 19j — Thí nghiệm pass chính: đo nhiễu và chạy song song

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 3.
**Ai:** Claude · **Chi phí mô hình:** khoảng 1,5 USD (thêm khoảng 2,2 USD nếu chạy doc-4); nằm trong trần 10 USD của đợt, dry-run trước mỗi lượt
· **Chặn bởi:** không · **Trạng thái:** sẵn sàng

## Vì sao

- Pass chính nhạy với cạnh trục: Q7 của doc-1 dao động 0,42–0,73 giữa hai lượt (17i mục 7). Cổng cần một dải nhiễu E4 đo được.
- Mỗi phiên pass chính nhận cạnh của phiên trước trong chương, nên các phiên phải chạy nối tiếp: doc-4 mất 13,7 phút.

## Cần làm

1. **(15) Đo nhiễu.** Phát lại một số phiên pass chính với đầu vào cố định, lấy từ nhật ký 17i, vài lần mỗi phiên. Đo độ ổn định của cạnh, rồi suy ra dải
   nhiễu E4. Khoảng 0,93 USD.
2. **(14) Pass chính song song.** Bằng script nghiên cứu, không sửa mã sản phẩm: bỏ "cạnh đã có của các phiên trước trong chương" khỏi đầu vào phiên.
   Chạy trên doc-1 và xstk (khoảng 0,55 USD); thêm doc-4 nếu kết quả hứa hẹn.
3. **Quyết vé 19k:** nhận nếu E4 không tụt quá dải nhiễu của (15) và thời gian giảm rõ. Ghi quyết định vào spec mục 1b.

## Nghiệm thu

- [ ] Báo cáo có dải nhiễu E4, kết quả (14) gồm E4 và thời gian, và quyết định về 19k.
- [ ] Chi phí thật nằm trong trần.
