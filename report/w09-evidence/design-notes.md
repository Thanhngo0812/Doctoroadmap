# W-09 — quyết định giao diện và phạm vi nguồn thiết kế

- Câu hỏi chính của màn: người học đang vướng gì ở bài đang mở và cần đọc/hỏi gì tiếp theo?
- Dữ liệu: khoá/tài liệu, module, bài đang mở, phiên riêng theo người/cuốn, câu hỏi và answer-3, nguồn theo trang, thẻ nội dung đã lưu, tỷ lệ hạn mức hôm nay.
- Tác vụ: hỏi tiếp và đọc nguồn; sau đó mở lại/đổi tên/xoá phiên, chuyển module, xem quiz/tài liệu do trợ lý tạo. Không dựng thư viện/chấm quiz W-10 trong W-09.
- Quy mô minh hoạ lấy từ snapshot doc-1 v8, PG UUID riêng. Tỷ lệ 0%/100% là dữ liệu sổ chi giả của harness, không phải chi thật hoặc lượt/ngày.
- Áp dụng `design-taste-frontend`, nhánh app screen, kế thừa hướng editorial-greeting của W-08 (seed 1026014839), giữ palette/type và logo đã nhận; không tạo landing page hoặc đổi thương hiệu.
- Dấu hiệu riêng của WayFinder: bài đang mở/phạm vi phiên và nguồn [Sx] mở đúng trang nằm trong cùng hành trình đọc, cùng logo Artboard 24/28, font Be Vietnam Pro và token main.
- Nguồn tham khảo: `tmp/w24-figma-evidence/design/preview/w09_chat_screens.html`, commit `eb29f291709245a9ccf3d121415f6202fdeaae7f`, SHA-256 `eb49103245bba6a54f3174afca7c73d0bfd21d816396b1352160b7b859fe83fb`.
- Ba lỗi công thức preview đang vá: D-R4-01 HTML giả KaTeX thiếu bố cục chỉ số; D-R4-02 phần toán aria-hidden thiếu MathML/nhãn tương đương; D-R4-03 span không đóng ở preview W-08. React dùng react-markdown/KaTeX thật đã nhận trên main, không chép HTML công thức hoặc cả nhánh thiết kế.
- Bố cục desktop: phần đọc, mục bài học và chat 380 px. Tablet dùng dialog, mobile toàn màn. Không dùng CSS chat của demo marketing: tên lớp riêng `learning-chat-*` để tránh lan kiểu dáng.
- Chữ trả lời là khối chính, nguồn bấm 44 px, nhãn công cụ nhỏ; không avatar trang trí, gradient hay số liệu bịa. Chỉ thẻ từ sự kiện có kiểm quyền mới mở nội dung; URL tự bịa trong chữ giữ dạng chữ.
- Motion dùng token 200 ms cho khung và 120 ms cho điều khiển có sẵn; reduced-motion thật bỏ animation. Composer hoặc nút đóng nhận focus khi mở, Escape trả focus về nút mở trên dialog.
- Ảnh browser là HTTP/PG/use case thật, provider/media/mailer giả. Snapshot DOM dành riêng taste inspector không thay bằng chứng tương tác React; báo cáo cuối ghi rõ phạm vi từng lượt Axe và đo tương phản toán thủ công bổ sung.
