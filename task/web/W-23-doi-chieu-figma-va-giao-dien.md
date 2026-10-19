# W-23 — Đối chiếu Figma với giao diện React, chỉnh lệch

**Nguồn chân lý:** [spec thiết kế giao diện](../../doc/web-thiet-ke-giao-dien-spec.md); bản Figma của [W-22](W-22-ban-figma.md).
**Ai:** nhóm web · người thiết kế duyệt · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-22, W-08, W-09, W-10 · **Trạng thái:** ready-for-agent

**Đầu vào W-22 ngày 2026-10-19 chưa đủ nghiệm thu:** cần hoàn tất [W-24](W-24-bo-sung-va-sua-ban-giao-w22.md) rồi người soát xác nhận W-22.
Báo cáo 20 test/17 cặp tương phản không thay cho bằng chứng đủ trang, Variables và bốn prototype. Xem
[tiếp nhận W-22](../../report/dieu-phoi-tiep-nhan-w22-2026-10-19.md); W-23 vẫn giữ các phụ thuộc gốc.

## Vì sao

Các vé trang dựng giao diện theo spec, song song với lúc Figma được vẽ. Cuối cùng phải đối chiếu để hai bên khớp, trước khi chụp ảnh cho báo cáo đồ án.

## Cần làm

- Mỗi trang: đặt ảnh chụp React cạnh khung Figma cùng cỡ màn hình; liệt kê chỗ lệch (màu, chữ, khoảng cách, thành phần, trạng thái).
- **Soát độ hoàn thiện:** kiểm phân cấp thị giác, căn chỉnh, độ dễ đọc, bố cục thích ứng và độ nhất quán theo spec mục 3a, kể cả khi Figma và React khớp
  nhau. Được phép dùng các skill trong bộ `taste-skill` do chủ dự án nạp để hỗ trợ soát/chỉnh, theo luật chung.
- **Đối chiếu hiệu ứng trên tương tác thật:** so React với ghi chú/prototype W-22 về phản hồi nút, menu, hộp thoại, bảng trượt, khối gập và chuyển trạng
  thái. Ghi lỗi thời lượng, nhảy bố cục, mất focus hoặc cản thao tác; kèm video ngắn trước/sau cho lỗi đã sửa.
- **Lệch vì React sai** thì sửa React. **Lệch vì Figma vẽ khác spec** thì báo người thiết kế. **Lệch mà cả hai đều hợp lý** thì ghi lại để chủ dự án chọn; không tự
  đổi spec.
- Kiểm truy cập: điều hướng bằng bàn phím, viền focus thấy được, nhãn cho trình đọc màn hình ở nút chỉ có biểu tượng, `prefers-reduced-motion` thay vòng chờ
  GIF bằng ảnh tĩnh và tắt chuyển động không thiết yếu; phản hồi trạng thái vẫn đầy đủ.

## Tiêu chí nghiệm thu

- [ ] Bảng lệch theo trang, mỗi dòng có ảnh hai bên và cách xử lý.
- [ ] Không còn lệch loại "React sai".
- [ ] Người thiết kế và người soát xác nhận chất lượng thị giác theo spec mục 3a; kiểm thêm bố cục 768 px, sáng/tối và hiệu ứng trên tương tác thật.
- [ ] Kiểm bàn phím và trình đọc màn hình trên bốn luồng chính; bật giảm chuyển động thì không còn GIF chạy.
- [ ] Báo cáo có video ngắn minh chứng hiệu ứng; test giảm chuyển động kiểm cả vòng chờ lẫn chuyển động không thiết yếu theo spec.
- [ ] Bộ ảnh chụp cuối cùng ở 390 px và 1280 px cho báo cáo đồ án.

## Ngoài vé

Thiết kế lại trang nào ngoài spec.
