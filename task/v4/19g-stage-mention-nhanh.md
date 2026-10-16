# 19g — Stage mention nhanh hơn

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 2 mục 3.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (có thể bớt embedding) · **Chặn bởi:** không · **Trạng thái:** sẵn sàng giao

## Vì sao

Stage mention mất 400 giây trên doc-4 (nghiên cứu mục 4), vì ba chỗ:
- độ gần ngữ nghĩa tính bằng Python thuần;
- khớp tên chính xác chạy lặp;
- khoảng 630 tên bị embed lại, dù stage cụm đã embed.

## Cần làm

- Tính độ gần ngữ nghĩa bằng thư viện số học vector.
- Khớp tên chính xác một lần cho cả tài liệu.
- Dùng lại vector tên đã có ở stage cụm, không embed lại.
- **Mention map phải giống hệt trước**, kể cả thứ tự và các trường số. Nếu có sai lệch số học nhỏ ở độ gần, ghi rõ và giữ thứ hạng không đổi.

## Nghiệm thu

- [ ] Test trên fixture thật: mention map trước và sau cùng băm, hoặc chỉ lệch số học trong dung sai đã ghi mà thứ hạng y nguyên.
- [ ] Số lời gọi embedding của stage mention giảm, với số đếm từ embedding giả.
- [ ] Ghi số giây trước và sau cho doc-4 ở kho thử, 0 USD nhờ cache embedding nếu có.
- [ ] Toàn bộ test qua.
