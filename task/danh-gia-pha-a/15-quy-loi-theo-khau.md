# DG-15 — Quy lỗi theo khâu

**Nguồn:** spec mục 10 · **Ai:** agent B · **Chi phí:** 0 · **Chặn bởi:** DG-10, DG-13 · **Hạn:** 03/11 · **Trạng thái:** ready-for-agent

## Làm được gì

Lõi chấm quy mỗi cạnh vàng trong phạm vi mà lộ trình làm sai (thiếu, ngược, đầu ngoài dãy học) vào **lý do đầu tiên** trong 7 lý do của spec mục 10. Nó cũng
xếp loại mỗi cạnh máy ngoài vàng: đúng theo G5(b), ngược chiều, bắc cầu của cạnh vàng, hay sai hẳn.

Đầu ra:
- bảng đếm theo cuốn và tổng, làm dữ liệu cho Hình 4 (thác nước);
- danh sách cạnh theo lý do, chỉ cho tập phát triển. Với tập thử thì chỉ in số, theo allowlist.

## Tiêu chí

- [ ] Mỗi lý do 1–7 có một ca dựng tay rơi đúng vào lý do đó, không rơi vào lý do sau.
- [ ] Tổng các lý do cộng cạnh đúng bằng tổng cạnh vàng trong phạm vi.
- [ ] Lý do 1 bỏ qua được khi chưa có G2 (cờ "không áp").
- [ ] Bảng phá, gồm ít nhất: xét lý do theo thứ tự khác; đếm một cạnh vào hai lý do.
