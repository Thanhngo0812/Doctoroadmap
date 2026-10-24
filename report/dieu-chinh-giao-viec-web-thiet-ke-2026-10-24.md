# Điều chỉnh giao việc web và thiết kế — 2026-10-24

## Quyết định của chủ dự án

Chủ dự án yêu cầu sửa bản giao việc theo điểm chờ mới của Claude, đồng thời chốt: “nhóm thiết kế làm tốt việc giao diện web cũng đc r ko cần cloud figma đâu”.
Chủ dự án nhắc lại việc nhóm thiết kế đã tạo mẫu HTML cho nhóm web tham khảo; giữ cách phối hợp này.

Áp dụng từ lượt này:

- **Thiết kế bàn giao HTML/CSS/token → web tham khảo và triển khai React → hai nhóm soát giao diện chạy thật.**
  Các mẫu trong `design/preview/` tiếp tục là tài liệu hỗ trợ; spec và token đã chốt là căn cứ khi mẫu có lỗi hoặc chưa theo hợp đồng mới.
- Bỏ yêu cầu Cloud Figma, Variables export từ Cloud, native components/bindings/reactions và bốn video Present Figma khỏi điều kiện nghiệm thu.
  Bằng chứng web vẫn gồm ảnh, kiểm responsive/sáng tối/reduced-motion, tương phản, focus và tương tác thực tế; video trình duyệt dùng khi cần chứng minh hiệu ứng.
- **W-22/W-24 đạt có ghi chú cho mốc thiết kế web đã kiểm và bàn giao**, dựa trên kết quả đã lưu ở lần 3: token, bố cục, responsive,
  sửa Variables/chat và kiểm thị giác. Đây là thay đổi phạm vi nghiệm thu theo chủ dự án; không có lượt test hoặc bản vá mới trong quyết định này.
  Các lỗi còn ghi trên preview HTML phải đánh dấu bản cũ hoặc sửa khi tiếp tục dùng mẫu; lỗi chức năng React vẫn do vé web tương ứng xử lý.
  Những màn W-09/W-10 chưa triển khai được nghiệm thu khi có giao diện thật. Nhánh W-24 `f292f18` chưa được ghép bởi quyết định tài liệu này.
- W-23 chuyển sang đối chiếu **React với spec/token và mẫu HTML đã được chọn**, bỏ phụ thuộc Cloud; vẫn chờ các màn W-08/W-09/W-10 để nhận toàn bộ.

## Điểm chờ mới từ Claude

Lần đọc đầu trên main `fcff761`, bàn giao `ce2ad73` yêu cầu W-09 chờ SA-69. Trong khi chỉnh tài liệu,
Claude đã ghép SA-69 và cập nhật tại **`2a39c32`**; trạng thái có hiệu lực khi bàn giao như sau:

- SA-66 **đã ghép `ba4350f`**, không còn là điểm chờ của W-09.
- **SA-69 đã ghép `973fa99`, W-09 được gỡ chặn và nhận answer-3 từ main sau W-08.** Claude xác nhận đã sửa và chạy thật lại công cụ quiz/tài liệu.
  Web nhận main rồi kiểm tích hợp bằng fake đúng hợp đồng; phân giải scope ở lõi, không tự vá ở web.
  Thẻ quiz/tài liệu lấy từ sự kiện `artifact`; link mô hình tự bịa dạng `quiz:…` trong chữ giữ dạng văn bản, không biến thành link bấm được.
- **SA-70** sẽ ngừng phát delta từ tiêu đề tự kiểm tra bằng cùng biểu thức với bộ tách core. Khi chưa ghép, web vẫn sửa/giữ hồi quy R-W08-2;
  khi nhận SA-70 kiểm lại HTTP/React và tránh hai quy tắc cắt khác nhau. R-W08-1 về nhãn tiến độ vẫn giữ.
- Spec [document-3](../doc/tai-lieu-3-spec.md), [quiz-3](../doc/quiz-3-spec.md) và vé SA-67/68 đã có; W-10 nhận mốc triển khai được Claude nghiệm thu trước tích hợp cuối.
  Spec mới chưa tự chứng minh mã đã vào main. SA-70 mục 11.7 còn thay chính sách lỗi chụp ảnh trang lúc dựng; W-15 theo dõi sau khi mốc đó ghép.

## Cách bàn giao và kiểm

Tiếp dùng [bản giao việc lần 3 đã chỉnh](lenh-giao-viec-ba-nhom-lan3-2026-10-23.md).
Các mẫu mới W-08/W-09/W-10/W-11 đang ở `tmp/w24-figma-evidence/design/preview/`, nhánh `work/w24-figma-evidence`;
nhóm web có thể đọc mẫu tại đó, ghi rõ nguồn. Nhận vào nhánh bằng commit đã soát đúng phạm vi, không chép đè cây React hoặc nhập cả nhánh chưa duyệt.

Giữ [biên bản kiểm lần 3](dieu-phoi-nghiem-thu-ba-nhom-lan3-2026-10-23.md) và bằng chứng như lịch sử đúng ngày;
không đổi kết quả đỏ/xanh cũ thành kết quả mới. Không chạy lại cổng vì lượt này chỉ sửa tài liệu.
Kiểm đường dẫn/diff/phạm vi commit và SHA sáu tệp dở của phiên khác; chi dịch vụ ngoài mới 0 USD. Giữ Vertex.
