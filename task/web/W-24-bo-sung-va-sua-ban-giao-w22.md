# W-24 — Bổ sung bằng chứng và sửa bản bàn giao W-22

**Nguồn chân lý:** [W-22](W-22-ban-figma.md); [spec thiết kế](../../doc/web-thiet-ke-giao-dien-spec.md), mục 3, 3a, 7–11 và quyết định kiểm thử.
**Căn cứ soát:** [tiếp nhận W-22](../../report/dieu-phoi-tiep-nhan-w22-2026-10-19.md).
**Ai:** người làm W-22 / người thiết kế; nhóm React phối hợp hợp đồng token · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** đã bàn giao, kiểm lại chưa đạt toàn bộ; tiếp tục cùng vé.

**Kiểm lại bản `7baa7d2`, 2026-10-19:** 14 test token đạt; GIF tĩnh tự động ở cả bốn preview, vùng bấm cũ ở 390 đạt,
cả ba phép đổi primary/spacing/RGBA đã bị bắt; chat mẫu không còn tạo node từ payload HTML. Đã có bản auth cho W-02.
Xem [kết quả kiểm mới](../../report/dieu-phoi-kiem-lai-w13-w24-2026-10-19.md); không giao lại những lỗi này.

**Chỉ còn các nhóm việc sau để hoàn tất tiêu chí gốc:**

- plugin còn sáu màu tối khác token; giao Variables export thực từ Figma có nguồn gốc và đúng tên/giá trị, không chỉ mã tạo Variables;
- đủ node/ảnh từng trang/trạng thái, bốn link prototype bấm được và video; khung chữ mô tả luồng không thay liên kết tương tác;
- khung xem auth mới tràn ngang 20 px ở viewport 390; sửa khung hoặc giao ảnh/frame 390 đúng kích thước.

Giữ cùng vé; báo cáo phân biệt phần đã kiểm đạt và phần chưa có bằng chứng, không ghi hoàn tất 100% khi các mục trên còn mở.

## Mục tiêu

Hoàn thiện các tiêu chí gốc của W-22 và sửa những lỗi đã tái hiện. Không thiết kế lại thương hiệu, đổi spec hoặc xây ứng dụng React trong vé này.
Nếu phần còn thiếu đã có trên Figma, bổ sung bằng chứng thay vì làm lại.

## Cần làm

1. **Nút chế độ tối:** sửa chữ trắng trên nền `#29A9FF` trong preview/thành phần; dùng cặp màu đúng spec.
   Kiểm các biến thể thường/hover/focus/nguy hiểm ở cả hai chế độ, bao gồm các nút nổi trên điện thoại.
2. **Vùng bấm điện thoại:** sửa các nút Học tiếp (32 px), Đọc trang (28 px), Hỏi trợ lý (39 px) để vùng thao tác đạt ít nhất 44×44 px.
   Đối chiếu chữ bài giảng, cỡ GIF 96/160 và các giá trị token theo spec; không giữ giá trị thu nhỏ chỉ để vừa khung mockup.
3. **Giảm chuyển động:** bàn giao ảnh tĩnh của vòng chờ và cách chọn ảnh khi `prefers-reduced-motion: reduce`.
   Kiểm trên trình duyệt thật rằng vùng ảnh không tiếp tục thay khung, hiệu ứng không thiết yếu tắt và phản hồi thao tác vẫn rõ.
4. **Token và guard:** cung cấp JSON xuất thực từ Figma Variables, tên công cụ/phiên bản và bảng đối chiếu với CSS đang dùng.
   Script/test tương phản đọc giá trị thực, kiểm cặp chữ/nền của thành phần; không chỉ kiểm các mã màu viết sẵn trong `PAIRS`.
   Kiểm định dạng nhập/xuất trước khi tiếp tục tuyên bố chuẩn W3C hoặc đồng bộ Figma 100%.
5. **Đủ bản vẽ và bằng chứng:** lập bảng theo từng dòng spec mục 11, gồm trang, trạng thái, cỡ 390/1280, node Figma và ảnh xuất.
   Ghi rõ đã có/chưa có; hoàn thiện phần còn thiếu, gồm các màn tối theo spec. Kiểm bố cục thêm ở 768 px.
   Không dùng canvas desktop bị cắt làm bằng chứng thích ứng điện thoại; nếu giữ HTML để minh chứng thì ghi rõ phạm vi của nó.
6. **Bốn prototype trong Figma:** nộp link chạy được, node bắt đầu và video ngắn của từng luồng W-22.
   Thể hiện menu/hộp thoại/chat/khối gập, phản hồi nút và trạng thái thuộc các luồng; ghi 120/200 ms, easing và phương án giảm chuyển động.
7. Cập nhật báo cáo W-22 theo kết quả thực, gỡ các khẳng định hoàn tất/đồng bộ/kiểm hoàn hảo chưa có bằng chứng.
   Ghi skill đã dùng và quyết định áp dụng. Commit đúng phạm vi vé; báo cáo có hash commit và lệnh kiểm.

## Tiêu chí nghiệm thu

- [ ] Các cặp chữ/nền thực trong sáng/tối đạt ngưỡng spec; có ảnh và số đo, gồm nút primary tối.
- [ ] Vùng bấm điện thoại đạt ≥ 44×44 px; chữ bài giảng và vòng chờ đúng token/spec.
- [ ] Bật giảm chuyển động thì vòng chờ dùng ảnh tĩnh; kiểm nhiều thời điểm không còn khung GIF đổi.
- [ ] JSON xuất từ Figma có nguồn gốc; đối chiếu đầy đủ tên/giá trị với CSS và token trong spec.
- [ ] Phép sửa sai thấy đỏ: đổi riêng primary CSS sang `#29A9FF` phải bị bắt do tương phản/khác JSON;
  đổi một giá trị JSON cho lệch CSS cũng phải bị bắt. Không bỏ/giảm ngưỡng test để xanh.
- [ ] Phép sửa sai giảm chuyển động thấy đỏ khi bỏ chuyển sang ảnh tĩnh; bản đúng xanh.
- [ ] Bảng trang/trạng thái không còn thiếu so với checklist W-22; có ảnh 390/1280, màn tối và ghi nhận bố cục 768.
- [ ] Người soát mở được file Figma, đối chiếu Variables/thành phần và bấm đủ bốn prototype; có video hiệu ứng.
- [ ] Báo cáo bổ sung có bằng chứng trước/sau, kết quả kiểm và commit riêng; người soát xác nhận lại tiêu chí W-22.

## Bàn giao

`report/w24-bo-sung-w22-2026-10-19.md` (đổi ngày nếu giao ngày khác), JSON Variables, bảng ánh xạ checklist,
link node/prototype và đường dẫn ảnh/video. Không đưa tài khoản, khoá hoặc tệp dữ liệu giữ lại vào gói.

W-01 tiếp tục phần nền theo spec; chưa chờ W-24 để bắt đầu. W-23 chỉ mở sau khi W-22 được nghiệm thu và đủ các phụ thuộc gốc.
