# W-10 — Quiz, tài liệu, thư viện

**Nghiệm thu lần 8, 2026-10-26: đạt `aaf68eb`, ghép local `1be7e1c`.** Đóng R-W10-1/R-W10-2; admission button/tool chung và phản hồi submit gắn đúng route/history. Cổng tích hợp `ee5a75f`: 2.824 Python/0 fail/1 skip/1 xfail cũ, 219 React/build; browser 12 cấu hình/96 ảnh/65 Axe/27 SSE đủ body. 0 USD, chỉ local/chưa push. Web tiếp React W-16 rồi W-04; không làm lại phần đã nhận. [biên bản lần 8](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan8-2026-10-26.md) và [lời giao lần 8](../../report/lenh-giao-viec-ba-nhom-lan8-2026-10-26.md).

**Nghiệm thu lần 7, 2026-10-26: chưa nhận/chưa ghép `fa346c9`.** Focused 87/React 212/build/browser 89 ảnh/58 Axe đạt các đường đã kiểm; còn hai Required độc lập: R-W10-1 trực tiếp hết 10 tài liệu nhưng trợ lý vẫn tạo tài liệu thứ 11 (HTTP/PG/model fake có assertion đỏ); R-W10-2 phản hồi nộp quiz cũ ghi kết quả vào màn quiz mới sau Back (React thật, control guard đạt). Sửa admission web chung hai nguồn và ranh giới request/route; giữ use case sinh/cache/retry/ngân sách core, không làm lại những phần đã đúng. Backend W-16/mẫu W-10 đã ghép local c5b4f5f; web nhận main sửa hai lỗi, sau W-10 đạt mới React W-16. [biên bản lần 7](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan7-2026-10-26.md) và [helper/lời giao](../../report/lenh-giao-viec-ba-nhom-lan7-2026-10-26.md).

**Mở sau nghiệm thu lần 6, 2026-10-25:** W-09 đã đạt/ghép local 7f54b14; SA-67/68 đã ở main. Nhóm web bắt đầu W-10 trong worktree riêng, ba lát quiz→submit/chấm, tài liệu trực tiếp→xem/tải và thư viện. Tái dùng phần library/preview W-09; group here/elsewhere theo core/home_scope, không đồng nhất origin button/assistant. Thiết kế sửa D-R6-01 trước khi nhận gói mẫu 0b5993e; phần quiz/tài liệu không bị chặn bởi lỗi mẫu thư viện. Dùng fake/PG 0 USD, không Cloud; [biên bản lần 6](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan6-2026-10-25.md) và [lời giao](../../report/lenh-giao-viec-ba-nhom-lan6-2026-10-25.md).

**Điều phối lần 5, 2026-10-25:** SA-67 document-3 và SA-68 quiz-3 đã ở main, không còn chờ hai lõi này. Web sửa hai Required W-09 trước khi triển khai W-10. Tái dùng library chỉ đọc/preview artifact của W-09 sau được nhận; vẫn còn sinh trực tiếp/submit/chấm/ẩn đáp án/xáo phương án/quyền/thư viện đầy đủ theo spec mới. Design chuẩn bị HTML/CSS/token đúng hợp đồng, không Cloud; [biên bản lần 5](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan5-2026-10-25.md).

**Cập nhật nghiệm thu lần4, 2026-10-24:** SA-67 document-3 đã ghép `6cfc535`, SA-68 quiz-3 đã ghép `21cfab3`. W-10 đã có cả hai mốc lõi mới, xếp sau W-09; đọc spec document-3/quiz-3 và kiểm HTTP/React/ẩn đáp án/xáo phương án/nộp bài/quyền/thư viện bằng PG/fake0USD. Không dùng hợp đồng cũ thay bản mới; [biên bản lần4](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan4-2026-10-24.md). Các điểm chờ SA-67/68 phía dưới là lịch sử.

**Cập nhật 2026-10-24:** đã có spec [document-3](../../doc/tai-lieu-3-spec.md), [quiz-3](../../doc/quiz-3-spec.md) và vé SA-67/68.
Sau W-08/W-09, đọc hợp đồng mới; tích hợp cuối nhận mốc được Claude nghiệm thu/ghép. Các hướng dẫn quiz-2/document-2 bên dưới là lịch sử,
không tự dùng làm chuẩn cho bản nâng mới. UI tham khảo HTML/CSS/token do thiết kế bàn giao, không chờ Cloud Figma.

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
Kế hoạch Pha B mới `f346e71` còn dự kiến nâng tài liệu SA-67 và quiz SA-68 sau bài giảng/trợ lý.
Trước khi mở W-10, nhận đặc tả/vé và mốc lõi thực tế của hai phần đó; đủ nền SA-52 không đồng nghĩa đã đạt chuẩn production mới chưa được cài.

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
- [x] Tầng HTTP: thân phản hồi của `POST /quizzes` không có trường đáp án đúng nào (quét đệ quy mọi khoá có tên kiểu `correct`, `answer`).
- [x] Nộp quiz của người khác thì `not_found`.
- [x] Tài liệu tạo trong phiên module A về khái niệm của module B hiện ở thư viện A (`here`) và thư viện B (`elsewhere`).
- [x] Chọn 6 module thì `scope_too_large`, 0 lời gọi mô hình.
- [x] Yêu cầu tài liệu thứ 11 trong một giờ thì `rate_limited`.
- [x] Ảnh chụp: làm quiz, kết quả quiz, tạo tài liệu, xem tài liệu, thư viện hai nhóm; cỡ 390 px và 1280 px.

## Ngoài vé

Báo lỗi câu quiz và tài liệu (W-19). Tài liệu dạng cây cả sách.
