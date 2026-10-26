# W-23 — Đối chiếu giao diện React với spec/token và mẫu HTML

**Điều phối lần 7, 2026-10-26: W-23 vẫn chưa đạt.** Báo cáo thiết kế 26e4a9a gọi nhầm ảnh HTML là React và ghép cặp khác trạng thái; đã ghi đính chính ở đầu báo cáo, rút tuyên bố “khớp hoàn hảo”/nghiệm thu từng phần. Mẫu W-10/source D-R6-01 được nhận bằng browser độc lập 12 cấu hình, không thay điều kiện W-23. Tiếp bảng cặp ảnh React/HTML đúng nguồn/SHA/viewport/theme/state, video thao tác/bàn phím/reduced-motion; W-10 còn hai Required chức năng nên toàn W-23 tiếp tục mở. Không Cloud; [biên bản lần 7](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan7-2026-10-26.md).

**Điều phối lần 6, 2026-10-25:** W-08/W-09 đã đạt, thiết kế có thể soát cả hai ngay. Báo cáo 0b5993e hiện soát source React và chụp preview HTML, chưa đủ bảng ảnh React/HTML cùng viewport/video thao tác thật để nhận W-23. Đính chính phạm vi, bổ sung đối chiếu thực bằng fake/PG 0 USD, được tái dùng bằng chứng điều phối khi SHA nguồn khớp. Toàn vé vẫn chờ W-10; không yêu cầu Cloud, không tự sửa chéo React. [biên bản lần 6](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan6-2026-10-25.md).

**Điều phối lần 5, 2026-10-25:** thiết kế web và ba sửa công thức đã được nhận/ghép local, không cần Cloud Figma. Có thể soát React W-08 ngay theo spec/token/mẫu HTML đã ghép; W-09 còn hai lỗi chức năng do web sửa, toàn W-23 chờ đủ W-09/W-10. Chỉ ghi lỗi thị giác/tương tác mới, không tự sửa tệp React web đang làm. [biên bản lần 5](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan5-2026-10-25.md).

**Nguồn chân lý:** [spec thiết kế giao diện](../../doc/web-thiet-ke-giao-dien-spec.md), token và mẫu HTML/CSS được nhận từ [W-22](W-22-ban-figma.md).
**Ai:** nhóm web · người thiết kế duyệt · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-22, W-08, W-09, W-10 · **Trạng thái:** ready-for-agent

**Cập nhật chủ dự án 2026-10-24:** bỏ phụ thuộc Cloud Figma; W-22/W-24 đạt có ghi chú mốc thiết kế web đã kiểm.
Có thể soát từng trang đã chạy, nghiệm thu trọn bộ vẫn chờ W-08/W-09/W-10. Dùng mẫu HTML/CSS/token và React thực tế,
không yêu cầu Variables export, node Cloud hoặc Present Figma. [Phạm vi mới](../../report/dieu-chinh-giao-viec-web-thiet-ke-2026-10-24.md).

## Vì sao

Các vé trang dựng React từ spec/token và mẫu HTML thiết kế. Đối chiếu trên trình duyệt trước khi chụp ảnh báo cáo đồ án.

## Cần làm

- Mỗi trang: so ảnh React với spec/token và mẫu HTML được chọn cùng cỡ màn hình; liệt kê chỗ lệch (màu, chữ, khoảng cách, thành phần, trạng thái).
- **Soát độ hoàn thiện:** kiểm phân cấp thị giác, căn chỉnh, độ dễ đọc, bố cục thích ứng và độ nhất quán theo spec mục 3a, kể cả khi mẫu HTML và React khớp
  nhau. Được phép dùng các skill trong bộ `taste-skill` do chủ dự án nạp để hỗ trợ soát/chỉnh, theo luật chung.
- **Đối chiếu hiệu ứng trên tương tác thật:** so React với ghi chú/prototype W-22 về phản hồi nút, menu, hộp thoại, bảng trượt, khối gập và chuyển trạng
  thái. Ghi lỗi thời lượng, nhảy bố cục, mất focus hoặc cản thao tác; kèm video ngắn trước/sau cho lỗi đã sửa.
- **Lệch vì React sai** thì sửa React. **Lệch vì mẫu HTML khác spec** thì báo người thiết kế. **Lệch mà cả hai đều hợp lý** thì ghi lại để chủ dự án chọn; không tự
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
