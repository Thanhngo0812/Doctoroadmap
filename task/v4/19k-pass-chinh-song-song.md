# 19k — Pass chính song song (chỉ làm nếu 19j nhận)

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 1b, "Pass chính song song".
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (test bằng mô hình giả) · **Chặn bởi:** 19j · **Trạng thái:** chờ 19j quyết

## Vì sao

Nếu thí nghiệm 19j cho thấy bỏ cạnh của các phiên trước khỏi đầu vào phiên không làm E4 tụt quá nhiễu, thì các phiên của một chương có thể chạy song
song. Pass chính doc-4 khi đó có thể còn vài phút thay vì 13,7 phút.

## Cần làm

- Thêm tuỳ chọn cho pass chính: không đưa "cạnh đã có của các phiên trước trong chương" vào đầu vào phiên. Tuỳ chọn nằm trong khoá cache.
- Khi bật, các phiên của một chương chạy song song, qua bộ giới hạn tốc độ hiện có.
- Đặt làm mặc định theo quyết định ghi ở spec mục 1b.
- Checkpoint và thứ tự nhật ký vẫn tất định.

## Nghiệm thu

- [ ] Test với mô hình giả: khi bật, đầu vào phiên không có cạnh của phiên trước, và các phiên chạy đồng thời; khi tắt, hành vi như cũ.
- [ ] Đổi tuỳ chọn thì khoá cache đổi. Toàn bộ test qua.
