# SA-24 — Trang xem thử Pha B trên máy cục bộ

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 13 (hợp đồng dữ liệu) và mục 14; chủ dự án yêu cầu ngày 2026-10-15: "cho 1 vé tạo 1
trang html để coi thử".
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD ở chế độ phát lại hay mô hình giả; khi bật `--allow-spend` thì tính theo từng thao tác,
trong trần chung · **Chặn bởi:** 06, 10, 13, 16 · **Trạng thái:** ready-for-agent

## Vì sao

Chủ dự án muốn thử Pha B trong trình duyệt trước khi web FastAPI + React của nhóm xong. Trang này cũng giúp ba việc:
- nhóm web thấy hợp đồng dữ liệu chạy thật;
- người chấm xem nội dung trong bối cảnh;
- việc trình diễn.

**Đây không phải sản phẩm.** Không có tài khoản, không chạy trên mạng ngoài, không thay web của nhóm.

## Cần làm

**Máy chủ:**
- Một lệnh khởi động máy chủ tối giản trên localhost. Máy chủ phục vụ một trang HTML, cộng các điểm cuối JSON và stream gọi thẳng các use case theo
  hợp đồng mục 13.
- Không thêm phụ thuộc nặng.
- Mặc định chạy ở chế độ phát lại hoặc mô hình giả (0 USD). Chỉ gọi Gemini khi khởi động với `--allow-spend`, và vẫn giữ mọi trần chi.

**Trang:**
- Một tệp HTML với JavaScript thuần, không bước build, không tải tài nguyên từ CDN; giao diện tiếng Việt.
- Chọn tài liệu trong sáu cuốn phát triển; không liệt kê tài liệu của tập giữ lại.

**Bốn khu vực:**

| khu vực | nội dung |
|---|---|
| Lộ trình | danh sách module với tên, `section_code`, mô tả; khái niệm theo thứ tự trong module |
| Bài giảng | bấm khái niệm thì hiện `skeleton` ngay, các ý hiện dần theo stream, rồi bản `final`. Có ảnh công thức gốc, hình đã xác nhận, câu tự kiểm tra có đáp án ẩn |
| Quiz | bấm "làm quiz" của module: câu hiện dần, nộp, phản hồi kèm nguồn và link bài giảng, lịch sử các lần làm |
| Chat với trợ lý | dòng tiến trình, lời gọi công cụ, chữ stream có nhãn, khối nhắc khái niệm nền, ghi chú "học kỹ ở module N". Mỗi sự kiện `artifact` mở được bài giảng, lần làm quiz hay tài liệu theo đúng hợp đồng; tài liệu tải được dạng Markdown |

**Trích dẫn:** bấm vào một nhãn nguồn thì hiện câu trích được tô sáng, kèm trang và đường mục.

**Chi phí trên trang:** mỗi thao tác hiện USD và số giây lấy từ `usage`, kèm tổng của phiên. Đây là để thử và đo; web thật không hiện cho người học.

**Ba công cụ tạo nội dung:** `get_lecture`, `make_quiz`, `make_document` (vé 14, 17, 18) hiện được ngay khi các vé đó xong. Trang dựng theo kiểu
hợp đồng nên không phải sửa.

## Tiêu chí nghiệm thu

- [ ] Test các điểm cuối với mô hình giả:
  - mỗi điểm cuối trả đúng JSON của hợp đồng;
  - sự kiện stream của bài giảng, quiz và trợ lý đến đúng thứ tự;
  - đề quiz không chứa đáp án.
- [ ] Trang chạy được khi không có mạng ở chế độ phát lại, trên doc-1 và doc-6.
- [ ] Danh sách thao tác thử tay, mỗi thao tác kèm ảnh chụp trong báo cáo của vé:
  - mở lộ trình;
  - bấm hai khái niệm, xem stream;
  - làm một quiz và nộp;
  - hỏi trợ lý ba câu, gồm một câu ngoài tài liệu và một câu nối tiếp;
  - nhờ trợ lý tạo một tài liệu nếu vé 18 đã xong.
- [ ] Máy chủ chỉ nghe trên localhost; không lộ `.env` hay khoá qua bất kỳ điểm cuối nào.
- [ ] Một buổi thử với Gemini thật nếu chủ dự án muốn: dry-run ước trước, chủ dự án duyệt. Báo USD của buổi thử.

## Ngoài vé

Sáu việc không thuộc vé này: tài khoản, nhiều người dùng, triển khai lên máy chủ thật, giao diện đẹp hay đáp ứng di động, cơ sở dữ liệu Postgres,
và web FastAPI + React của nhóm.
