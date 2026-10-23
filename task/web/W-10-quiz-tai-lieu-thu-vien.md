# W-10 — Quiz, tài liệu, thư viện

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 4 (`library-1`), 7 (`quiz-2`, `document-2`), 10; [spec chức năng](../../doc/web-chuc-nang-spec.md),
mục 7, 11 (đề quiz không có đáp án); spec thiết kế, trang quiz, tài liệu, thư viện.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** W-07, SA-35, SA-37; SA-52 đã ghép · **Trạng thái:** đủ phụ thuộc lõi; xếp sau W-08 nếu chỉ có một phiên web.

**Đối chiếu Pha B 2026-10-22, cập nhật:** Claude đã nghiệm thu SA-52 và ghép `66cd439`, đóng điểm chờ sửa quiz của SA-35/37.
Nhận main có mốc này để cài/kiểm `quiz-2`, tài liệu và thư viện với đồ giả/phát lại; phần web vẫn cần kiểm HTTP không lộ đáp án, owner và nộp bài
nguyên tử. Xem [soát Pha B của Claude](../../report/soat-pha-b-52-53-sonnet-2026-10-22.md).

## Vì sao

**Cập nhật hợp đồng bài giảng, 2026-10-23:** ADR 0025/spec bài giảng 3 thay cấu trúc lecture-2; SA-64 thay SA-63.
W-10 không tự thay `quiz-2`/`document-2`; nếu dùng bài giảng/tool thì nhận `body_md`, `sources`, `self_check` và delta Markdown/LaTeX,
giữ chữ đã hiện, không lọc lại bằng luật cũ, không lộ `validation`, không kỳ vọng sections/bridge/kiem_noi_dung/24 giờ.
Phần dùng hợp đồng mới kiểm sau khi SA-64 được Claude ghép; ảnh trang SA-65 ở kho artifact, không đổi kiến trúc DB.

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
