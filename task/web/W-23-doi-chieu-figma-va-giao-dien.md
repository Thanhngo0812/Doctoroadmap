# W-23 — Đối chiếu Figma với giao diện React, chỉnh lệch

**Nguồn chân lý:** [spec thiết kế giao diện](../../doc/web-thiet-ke-giao-dien-spec.md); bản Figma của [W-22](W-22-ban-figma.md).
**Ai:** nhóm web · người thiết kế duyệt · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-22, W-08, W-09, W-10 · **Trạng thái:** ready-for-agent

## Vì sao

Các vé trang dựng giao diện theo spec, song song với lúc Figma được vẽ. Cuối cùng phải đối chiếu để hai bên khớp, trước khi chụp ảnh cho báo cáo đồ án.

## Cần làm

- Mỗi trang: đặt ảnh chụp React cạnh khung Figma cùng cỡ màn hình; liệt kê chỗ lệch (màu, chữ, khoảng cách, thành phần, trạng thái).
- **Lệch vì React sai** thì sửa React. **Lệch vì Figma vẽ khác spec** thì báo người thiết kế. **Lệch mà cả hai đều hợp lý** thì ghi lại để chủ dự án chọn; không tự
  đổi spec.
- Kiểm truy cập: điều hướng bằng bàn phím, viền focus thấy được, nhãn cho trình đọc màn hình ở nút chỉ có biểu tượng, `prefers-reduced-motion` thay vòng chờ
  GIF bằng ảnh tĩnh.

## Tiêu chí nghiệm thu

- [ ] Bảng lệch theo trang, mỗi dòng có ảnh hai bên và cách xử lý.
- [ ] Không còn lệch loại "React sai".
- [ ] Kiểm bàn phím và trình đọc màn hình trên bốn luồng chính; bật giảm chuyển động thì không còn GIF chạy.
- [ ] Bộ ảnh chụp cuối cùng ở 390 px và 1280 px cho báo cáo đồ án.

## Ngoài vé

Thiết kế lại trang nào ngoài spec.
