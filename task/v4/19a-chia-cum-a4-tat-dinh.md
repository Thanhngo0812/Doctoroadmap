# 19a — Chia cụm A4 tất định

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 1a mục 5.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** sẵn sàng giao

## Vì sao

Cụm A4 của chuỗi gộp phụ thuộc `PYTHONHASHSEED`. Cùng đầu vào, mỗi lần chạy lại ra cụm khác. Hệ quả: lời gọi phán cụm không tái dùng được, và không so
được hai cấu hình trên cùng tài liệu (nghiên cứu mục 2).

## Cần làm

- Trước khi chạy thuật toán chia cụm, đổi id node thành số nguyên theo thứ tự đã sắp, rồi đổi ngược kết quả.
- Giữ nguyên thuật toán (Louvain), seed và tham số.
- Chỉ áp ở chuỗi `gop`; mã luật chia cụm đi vào config của chuỗi `gop`. Băm config của chuỗi v3 giữ nguyên.

## Nghiệm thu

- [ ] Hai tiến trình con với `PYTHONHASHSEED` khác nhau, cùng fixture tài liệu thật, ra cùng cụm và cùng băm payload canonical. Test phải đỏ trên mã
      hiện nay.
- [ ] Băm config v3 không đổi. Toàn bộ test qua.
