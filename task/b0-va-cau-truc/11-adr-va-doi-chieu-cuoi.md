# 11 — Cập nhật ADR và đối chiếu trên tài liệu thật

**What to build:** Người vận hành ingest lại `nhap-mon-ml` và **nhìn bằng mắt** thấy đợt vá đã thành công.
Quyết định về định danh được cập nhật để phản ánh cái giá mà việc gộp block vừa phải trả.

Phép kiểm bằng mắt trên tài liệu thật **chính là thứ phát hiện ra toàn bộ đợt vá này** — hai mươi lăm test đều
xanh, mười hai bất biến đều được khẳng định, và không cái nào thấy gì. Vì vậy nó là một ticket riêng, không
phải một dòng nghiệm thu bị lướt qua ở cuối ticket khác.

**Blocked by:** 04, 05, 06, 07, 08, 09, 10 — mọi thay đổi phải nằm đủ trước khi đối chiếu mới có nghĩa.

**Status:** completed

## Đối chiếu trên `nhap-mon-ml`

- [x] Xoá artifact cũ rồi ingest lại từ đầu
- [x] Cây section có **ba cấp số**, thêm cấp bốn cho `a)`/`b)`, không còn phẳng
- [x] `CHƯƠNG 1` **có section con** và truy được xuống các mục của nó
- [x] `trong đó:` **không còn** trong danh sách section
- [x] Trung vị text chunk là **248 token**; toàn bộ 50 chunk là 202 do 8 hình + 3 cước chú đứng riêng
- [x] **Không chunk nào** chứa thông báo lỗi của thư viện parse
- [x] **Không chunk nào** còn ký hiệu toán nhân bản glyph
- [x] Manifest ghi đủ: danh sách lý do cảnh báo, thống kê node bị bỏ, phiên bản thuật toán `section-id-v3`
- [x] Cảnh báo cây phẳng **không còn bật** — vì cây đã hết phẳng
- [x] Đường dẫn section của chunk dài hơn một phần tử

## Cập nhật tài liệu

- [x] ADR 0001 ghi nhận hệ quả mới: gộp leaf block làm các block dính vào nhau trong khoá băm, nên sửa một
      block nay đổi định danh của cả nhóm thay vì chỉ của chính nó. Đây là mất mát thật về tính ổn định, đổi
      lấy chất lượng vector — ghi rõ cả hai vế
- [x] ADR 0001 ghi nhận rằng đường dẫn section nay do luật suy cấp quyết định, nên **đổi luật suy cấp là đổi
      mọi định danh** — một nguồn bất ổn mới mà bản ADR gốc chưa lường
- [x] Tài liệu phân tích luồng được cập nhật theo hành vi mới, và **không in ra giá trị băm cụ thể nào**
- [x] Bảng bất biến trong đặc tả gốc được bổ sung I13, I14, I15, I16
- [x] Ghi lại số đo sau đợt vá để lần sau còn đối chiếu: số section, số chunk, trung vị token, thời gian parse

## Đóng đợt

- [x] Toàn bộ bộ test xanh
- [x] Đánh dấu F11–F21 đã xử lý trong bảng feedback vòng hai
