# W-26 — Máy chủ demo local chạy thật: dựng sách thật, mail thật, ảnh trên đĩa

**Nguồn:** chủ dự án 2026-10-29: "dựng sver frontend backend bản thật có dựng sách thật, ko cần cloudinary, mail thật lên tôi coi"; "sao ko phải là tài
khoản nào cũng up đc"; trần người học "Nâng 3 USD/người/ngày".
**Ai:** subagent lõi · **Chi phí khi cài và test:** 0 USD (mọi test dùng đồ giả) · **Chặn bởi:** — · **Trạng thái:** ready-for-agent

## Vì sao

Chủ dự án cần mở một bản web chạy thật trên máy để xem: đăng ký nhận thư thật, tải sách và dựng thật, học trên sách vừa dựng và trên sáu cuốn phát triển.
Hiện chưa có đường này: worker web khoá chi (`allow_spend=False`) và chỉ operator W-15 trên DB thử mới tạo được giấy phép chi; `seed-samples` đẩy PDF lên
Cloudinary.

## Phạm vi

Một lệnh vận hành chạy máy chủ demo local (ví dụ `wayfinder.cli demo-local` hoặc `scripts/demo_local.py`, chọn theo cấu trúc hiện có), gồm:

1. **DB riêng mới** trên container PostgreSQL dev (tên có ngày, ví dụ `wayfinder_demo_20261029`): tạo nếu chưa có, `db upgrade`, admin đầu tiên tự xác
   lập qua bootstrap trên DB mới. **Không đụng DB `wayfinder` dùng chung** (chưa áp `w17_0009`).
2. **Ảnh và tệp gốc lưu đĩa** dưới thư mục artifact của bản demo, không Cloudinary. Không tạo link dùng lâu cho trình duyệt; server vẫn chuyển ảnh như
   ADR 0023 mô tả.
3. **Mail thật** qua Gmail SMTP trong `src/web/.env` (đăng ký, xác minh, quên mật khẩu, mời, báo dựng xong).
4. **Mô hình thật qua Vertex**, chỉ `gemini-3.1-flash-lite`, như cấu hình web hiện hành.
5. **Dựng thật cho mọi tài khoản** (spec: bản demo ai cũng tải sách được). Giấy phép chi cấp tự động cho từng bản dựng trong máy chủ demo này, với trần
   **3 USD/cuốn** và **10 USD/ngày cho cả máy chủ** (giờ Việt Nam). Hết trần ngày thì bản dựng xếp hàng chờ ngày sau với lý do rõ, không chạy vượt. Tái dùng
   `BuildSpendGuard`, sổ chi và receipt build hiện có; không thêm sổ chi thứ hai; trace `counted_in=build` không cộng hai lần.
6. **Trần người học 3 USD/người/ngày** cho máy chủ demo này (cấu hình, không đổi mặc định 1 USD của ADR 0026).
7. **Sáu khoá mẫu** từ sáu cuốn phát triển, nạp từ đĩa (không Cloudinary), chỉ ở `env=dev`.
8. Backend phục vụ bản build React cùng cổng; worker dựng chạy cùng lệnh hoặc lệnh thứ hai; hướng dẫn chạy/dừng ngắn ở `src/web/README.md`.

Giấy phép chi tự động chỉ được bật bằng cờ của lệnh demo local; mặc định server và worker chung vẫn `allow_spend=False`. Không thêm endpoint HTTP tạo giấy
phép. Ghi rõ quyết định này trong báo cáo, vì nó nới chốt của W-15 ("không endpoint hay setting nào tạo grant") cho riêng máy chủ demo theo chỉ thị
chủ dự án.

## Tiêu chí nghiệm thu (mỗi test đỏ trước trên bản sai)

- [ ] Máy chủ demo không chạm DB `wayfinder` dùng chung; test kiểm tên DB.
- [ ] Không gọi Cloudinary (MediaStore Cloudinary không được khởi tạo); ảnh trang/công thức đọc được qua server.
- [ ] Hai bản dựng của hai tài khoản khác nhau đều được cấp phép và dựng (runner giả có chi giả khác 0); cờ demo tắt thì không bản nào được chi.
- [ ] Trần 3 USD/cuốn dừng bản dựng vượt; trần 10 USD/ngày chặn bản dựng kế, không chạy vượt; ranh ngày theo giờ Việt Nam.
- [ ] Receipt build cộng đúng một lần vào sổ chi; SQL độc lập.
- [ ] Trần người học của máy chủ demo là 3 USD; server thường vẫn 1 USD.
- [ ] Mailer là SMTP ở máy chủ demo (test dùng SMTP giả bắt thư, không gửi thật).
- [ ] Sáu khoá mẫu nạp từ đĩa, không mạng.

## Ngoài vé

Dọn DB/artifact demo, deploy thật (W-21), chuyển Developer API (chờ chủ dự án).
