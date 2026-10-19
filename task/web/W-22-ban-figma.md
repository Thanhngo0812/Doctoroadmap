# W-22 — Bản Figma theo spec thiết kế

**Nguồn chân lý:** [spec thiết kế giao diện](../../doc/web-thiet-ke-giao-dien-spec.md) (toàn bộ); [spec chức năng](../../doc/web-chuc-nang-spec.md) (danh sách chức năng, mã lỗi); tệp
thương hiệu ở `design/`.
**Ai:** người thiết kế của nhóm · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** đã bàn giao, chưa đủ nghiệm thu; bổ sung/sửa theo W-24.

**Tiếp nhận 2026-10-19:** điều phối chạy lại 20 test và 17 cặp tương phản đạt, nhưng tái hiện lỗi nút tối, vùng bấm mobile, GIF khi giảm chuyển động;
thử đổi sai CSS mà 20 test vẫn xanh. Bằng chứng Figma/đủ trang và bốn prototype chưa xác minh được. Xem
[báo cáo tiếp nhận](../../report/dieu-phoi-tiep-nhan-w22-2026-10-19.md) và [vé sửa W-24](W-24-bo-sung-va-sua-ban-giao-w22.md).

**Kiểm bản W-24 mới `7baa7d2`, 2026-10-19:** các lỗi runtime cũ đã sửa đạt, có bản auth cho W-02. W-22 còn mở phần đủ trang/trạng thái,
Variables export thực và bốn prototype Figma; plugin mới vẫn có sáu màu tối khác token. Khung xem auth 390 còn tràn 20 px.
Chỉ tiếp tục các mục này theo [soát sau bổ sung](../../report/dieu-phoi-kiem-lai-w13-w24-2026-10-19.md), không giao lại lỗi cũ đã đóng.

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

**Thương hiệu** (chủ dự án cập nhật 2026-10-19): logo là 20 tệp `design/Artboard 9.png` đến `design/Artboard 28.png`; favicon vẫn là `OTP1`–`OTP6`.
Dùng bảng bố cục/màu/nền trong spec mục 1; ghi tên Artboard đã chọn trên thành phần Figma để React đối chiếu. Artboard 21–24 là đen nền trong, 25–28 là
trắng nền trong; thanh trên sáng/tối dùng Artboard 24/28. Đã có đủ logo để tiếp tục toàn bộ phần thương hiệu, không chờ `logo1`–`logo8`. Không vẽ lại,
kéo méo hay tự đổi màu của biến thể gốc.

**Chất lượng thị giác và hiệu ứng** (chủ dự án bổ sung 2026-10-18): bản Figma phải đẹp, chỉn chu, có phân cấp rõ, căn chỉnh/khoảng cách nhất quán và đủ
trạng thái theo spec thiết kế mục 3a. Kiểm bố cục thêm ở 768 px. Prototype mô tả hiệu ứng hover/bấm, mở/đóng menu, hộp thoại, bảng trượt, khối gập và chuyển
trạng thái thuộc các luồng của vé; ghi thời lượng theo token và phương án giảm chuyển động cho React. Được phép dùng các skill trong bộ `taste-skill`
do chủ dự án nạp theo luật chung; ghi tên skill và quyết định đã áp dụng nếu có dùng.

## Tiêu chí nghiệm thu

- [ ] Biến màu và chữ trong Figma trùng tên và giá trị với bảng token của spec. Người soát đối chiếu từng dòng.
- [ ] Trang thương hiệu ghi đủ Artboard 9–28 và bộ thành phần chỉ rõ tên tệp dùng theo spec mục 1, gồm bản nền trong cho sáng/tối.
- [ ] Đủ mọi trang và trạng thái trong danh sách kiểm của spec thiết kế, ở hai cỡ màn hình.
- [ ] Tương phản chữ đạt WCAG AA (4,5:1 cho chữ thường, 3:1 cho chữ lớn và biểu tượng), kiểm bằng plugin; ghi các cặp màu đã kiểm.
- [ ] Bốn luồng nguyên mẫu bấm được.
- [ ] Người soát xác nhận checklist thị giác ở spec mục 3a; có ghi nhận kiểm bố cục 768 px, hiệu ứng/thời lượng trong prototype và video ngắn các tương tác.
- [ ] Link Figma (quyền xem) và ảnh xuất của từng trang để vào báo cáo vé.

## Ngoài vé

Hoạt hình trang trí không phục vụ tương tác theo spec mục 3a. Bộ minh hoạ mới.
