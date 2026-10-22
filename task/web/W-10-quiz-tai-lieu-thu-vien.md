# W-10 — Quiz, tài liệu, thư viện

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 4 (`library-1`), 7 (`quiz-2`, `document-2`), 10; [spec chức năng](../../doc/web-chuc-nang-spec.md),
mục 7, 11 (đề quiz không có đáp án); spec thiết kế, trang quiz, tài liệu, thư viện.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** W-07, SA-35, SA-37; sửa SA-52 · **Trạng thái:** phần quiz chờ SA-52 đạt/ghép.

**Đối chiếu Pha B 2026-10-22:** phần quiz chưa đủ phụ thuộc: Claude soát SA-50 chưa đạt, mở SA-52 sửa Q3/Q6/câu dẫn/nhiễu/cache, SA-35/37 còn chờ. Chờ Claude nghiệm thu/ghép SA-52 trước khi chốt quiz W-10; không lấy kết quả local hoặc cổng backend W-25 thay phán xét này. Xem [kế hoạch mới](../../report/dieu-phoi-kiem-lai-w25-w14-react-w24-va-ke-hoach-2026-10-22.md).

## Vì sao

Người học tự kiểm tra bằng quiz, xin tài liệu theo yêu cầu, và tìm lại mọi thứ đã tạo ở thư viện của lộ trình hay của module.

## Cần làm

**Gateway:** `make_quiz`, `submit_quiz`, `make_document`, `get_document`, `list_library`.
- Nút ở trang lộ trình gửi phạm vi `roadmap`; nút ở trang học gửi phạm vi của module.
- Tài liệu từ trang lộ trình gửi danh sách module đã chọn, tối đa 5.
- **Giới hạn tần suất** `documents_per_hour` (10) mỗi người.

**HTTP:**
- `POST /courses/{cid}/quizzes` trả đề **không có đáp án**;
- `POST /courses/{cid}/quizzes/{aid}/submit` trả điểm, đáp án, giải thích;
- `POST /courses/{cid}/documents`;
- `GET /courses/{cid}/documents/{did}`;
- `GET /courses/{cid}/library?scope=roadmap|module:<id>|all`.

**Giao diện:**
- **trang làm quiz:**
  - mỗi câu một khối; câu nào xong trước hiện trước (quiz sinh song song);
  - nút nộp; kết quả từng câu kèm giải thích và trích dẫn;
  - **ẩn khung chat** khi đang làm (Q7 của Pha B2);
- **tạo tài liệu:**
  - hộp nhập yêu cầu;
  - ở trang lộ trình có chọn tối đa 5 module;
  - lỗi `scope_too_large` hiện câu khuyên thu hẹp;
  - đang tạo thì hiện vòng chờ;
- **xem tài liệu:** Markdown có chú thích nguồn bấm được; nội dung ngoài sách có nhãn;
- **thư viện:**
  - ở trang lộ trình là nội dung `roadmap`, cộng bộ lọc "tất cả";
  - ở trang học có hai nhóm "Tạo ở đây" và "Tạo ở nơi khác";
  - mục quiz có điểm nếu đã nộp.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Tầng HTTP: thân phản hồi của `POST /quizzes` không có trường đáp án đúng nào (quét đệ quy mọi khoá có tên kiểu `correct`, `answer`).
- [ ] Nộp quiz của người khác thì `not_found`.
- [ ] Tài liệu tạo trong phiên module A về khái niệm của module B hiện ở thư viện A (`here`) và thư viện B (`elsewhere`).
- [ ] Chọn 6 module thì `scope_too_large`, 0 lời gọi mô hình.
- [ ] Yêu cầu tài liệu thứ 11 trong một giờ thì `rate_limited`.
- [ ] Ảnh chụp: làm quiz, kết quả quiz, tạo tài liệu, xem tài liệu, thư viện hai nhóm; cỡ 390 px và 1280 px.

## Ngoài vé

Báo lỗi câu quiz và tài liệu (W-19). Tài liệu dạng cây cả sách.
