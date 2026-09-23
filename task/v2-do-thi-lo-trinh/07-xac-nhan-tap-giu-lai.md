# 07 — Xác nhận trên tập giữ lại

**Nguồn chân lý:** spec v2, W18–W19

**What to build:** một lần chạy duy nhất, với cấu hình đã khoá (commit, `prompt_hash`, tham số), trên `xstk-ch3-1` và N2;
chấm Q1–Q9; báo nguyên kết quả kể cả trượt.

**Blocked by:** 02–06; vé 10 — T8 (vàng N2), T10 (duyệt cấu hình khoá)

**Status:** chờ

## Luật

- Trước lần chạy: ghi commit, `prompt_hash` từng khâu, tham số, SHA-256 của mọi tệp nhãn vào chính vé này.
- Chuyển `xstk-ch3-1-chuong-10-13-hoi-y-output.xlsx` thành JSON bằng `a8-gold-check` **ngay trước** lần chạy, không sớm hơn.
- Không chỉnh gì sau khi thấy số. Mọi thay đổi sau đó là hậu kiểm, báo tách riêng.
- Mỗi con số kèm khoảng tin cậy Wilson 95%; khoảng chứa vùng trượt thì kết luận là chưa đủ bằng chứng.
