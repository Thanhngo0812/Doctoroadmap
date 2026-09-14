# 07 — Gỡ bullet vùng dùng riêng đầu mục liệt kê (F40)

**What to build:** Văn bản chunk của slide sạch ký tự vùng dùng riêng: **72 ký tự `U+F097`** —
bullet của font template, ngoài bảng Adobe Symbol — biến mất khỏi đầu các mục liệt kê. Cảnh báo
`remaining_private_use` từ đó chỉ còn đo những ký tự **thật sự** không xử lý được.

## Luật

Trong adapter, **sau** khi tra bảng Symbol: mục liệt kê (`list_item`) mở đầu bằng ký tự vùng dùng
riêng **chưa ánh xạ được** ⇒ gỡ ký tự đó và khoảng trắng theo sau, đếm vào thống kê parse
(`stripped_pua_bullets`).

- Chỉ gỡ ở **đầu** mục liệt kê — ký tự vùng dùng riêng ở vị trí khác giữ nguyên và tiếp tục được
  đếm trong `remaining_private_use`.
- Chỉ gỡ ký tự **chưa ánh xạ** — không giẫm lên bảng Symbol: `U+F0B7` vẫn ánh xạ thành `•` như
  vòng 8 đã chốt.
- Không đoán nghĩa font: nội dung liệt kê đã nằm trong cấu trúc `list_item`, dấu đầu dòng vô danh
  không mang thêm thông tin.

**Blocked by:** 04 — cùng vùng adapter, làm nối tiếp; phiên bản adapter đã nhích ở 03, ticket này
**không** nhích nữa.

**Status:** done

- [x] Có test: `list_item` mở đầu bằng ký tự vùng dùng riêng lạ ⇒ ký tự và khoảng trắng sau nó bị gỡ
- [x] Có test: `U+F0B7` đầu mục vẫn thành `•` qua bảng Symbol — hai đường không giẫm nhau
- [x] Có test: ký tự vùng dùng riêng **giữa** câu không bị gỡ, vẫn đếm trong `remaining_private_use`
- [x] Trên fixture slide: số ký tự vùng dùng riêng trong văn bản chunk **72 → 0**;
      `stripped_pua_bullets: 72` trong thống kê parse
- [x] Số vàng: slide đổi đúng cột vùng-dùng-riêng và các định danh chunk chứa bullet (liệt kê trong
      commit); **ba tài liệu kia đứng yên** — chúng không có bullet vùng dùng riêng
