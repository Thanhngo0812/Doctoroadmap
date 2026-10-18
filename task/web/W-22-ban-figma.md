# W-22 — Bản Figma theo spec thiết kế

**Nguồn chân lý:** [spec thiết kế giao diện](../../doc/web-thiet-ke-giao-dien-spec.md) (toàn bộ); [spec chức năng](../../doc/web-chuc-nang-spec.md) (danh sách chức năng, mã lỗi); tệp
thương hiệu ở `design/`.
**Ai:** người thiết kế của nhóm · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** ready-for-agent

## Vì sao

Nhóm cần một bản thiết kế thống nhất cho báo cáo đồ án và để nhóm React đối chiếu. Claude không vẽ trên Figma; spec thiết kế là nguồn, Figma là bản vẽ của
spec đó.

## Cần làm

**Thư viện thành phần:**
- **biến (variables)** khớp đúng token của spec thiết kế: màu sáng và tối, chữ Be Vietnam Pro, khoảng cách, bo góc, bóng. Tên biến giữ đúng tên token, để
  nhóm React đối chiếu;
- **thành phần có biến thể** theo danh sách của spec: nút, ô nhập, thẻ, thẻ khoá học, thẻ module, nhãn trạng thái, dải thông báo, hộp thoại, khung chat, khối
  bài giảng, vòng chờ, trạng thái rỗng.

**Màn hình:** mọi trang trong sơ đồ trang của spec thiết kế, mỗi trang ở **390 px** và **1280 px**. Mỗi trang có các trạng thái spec liệt kê: rỗng, đang
tải, lỗi, hết trần, không có quyền.

**Luồng nguyên mẫu** (prototype) cho bốn luồng chính:
1. đăng ký → khoá mẫu → bài giảng;
2. chia sẻ link → tham gia;
3. tải sách → dựng;
4. làm quiz.

**Thương hiệu:** dùng đúng tệp logo và favicon theo bảng tệp của spec. Không vẽ lại logo; không đổi màu logo ngoài hai bản đen và trắng-trên-xanh.

## Tiêu chí nghiệm thu

- [ ] Biến màu và chữ trong Figma trùng tên và giá trị với bảng token của spec. Người soát đối chiếu từng dòng.
- [ ] Đủ mọi trang và trạng thái trong danh sách kiểm của spec thiết kế, ở hai cỡ màn hình.
- [ ] Tương phản chữ đạt WCAG AA (4,5:1 cho chữ thường, 3:1 cho chữ lớn và biểu tượng), kiểm bằng plugin; ghi các cặp màu đã kiểm.
- [ ] Bốn luồng nguyên mẫu bấm được.
- [ ] Link Figma (quyền xem) và ảnh xuất của từng trang để vào báo cáo vé.

## Ngoài vé

Hoạt hình ngoài vòng chờ GIF. Bộ minh hoạ mới.
