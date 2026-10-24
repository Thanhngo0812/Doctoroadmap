# W-08 — Trang học: bài giảng stream, "Đọc trang p"

**Nguồn chân lý:** [spec bài giảng 3](../../doc/bai-giang-3-spec.md), mục 6 (`lecture-3`) và 9; [ADR 0025](../../doc/adr/0025-bai-giang-3-van-xuoi-tu-nhien.md),
[ADR 0024](../../doc/adr/0024-bai-giang-luon-hien-luat-kiem-chi-ghi-log.md); nhãn người học ở [spec Pha B2](../../doc/pha-b2-spec.md), mục 6.5;
[spec chức năng](../../doc/web-chuc-nang-spec.md), mục 1 (SSE), 7 (mở tệp gốc); spec thiết kế, trang học và vòng chờ.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** W-07; SA-64 thay SA-63, ảnh trang SA-65 · **Trạng thái:**
sửa hai Required sau kiểm độc lập `89122f6`, chưa ghép; SA-62/64/65 đều đã ở main, không còn chờ lõi.

**Báo trước của Claude 2026-10-24:** [SA-70](../sau-a10/70-bai-giang-3-ban-2.md) sẽ ngừng phát delta từ tiêu đề tự kiểm tra bằng cùng biểu thức của bộ tách core.
Tới lúc SA-70 ghép vẫn sửa/giữ hồi quy R-W08-2 phía web; sau nhận main đó kiểm lại HTTP/React để tránh hai quy tắc khác nhau.
R-W08-1 về nhãn tiến độ giữ nguyên. UI tham khảo mẫu HTML/CSS/token của nhóm thiết kế và được soát trên React, không cần Cloud Figma.

**Nghiệm thu lần 3, 2026-10-23 tối:** mốc điều phối `1449d51` nhận main `0ccedae`, mã khớp web `e6b336e`.
2.385 Python đạt / 0 fail / 1 Cloudinary live không bật, 158 React và build đạt; browser 12 cấu hình / 101 ảnh / 17 Axe đạt có phạm vi.
Ca phản chứng bổ sung có **6 assertion fail/11 pass/0 error**: (1) đánh dấu B ở sidebar không cập nhật nhãn B trong tiên quyết/Tiếp theo của bài A;
(2) bốn tiêu đề tự kiểm tra hợp lệ với core (`##`, `####`, thụt đầu, dấu `:`) làm lộ đáp án trước final do regex React chỉ nhận một dạng.
Sửa cả save/rollback bằng tiến độ hiện tại, không sinh lại bài; đồng bộ che/gập đáp án khi stream và giữ trường hợp không có self_check.
Nhận ca hồi quy vào suite, ghi RED→GREEN, nhận main mới/chạy cổng/browser trước đề nghị ghép. Không làm lại phần đã đạt.
[Biên bản/ca tái hiện](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan3-2026-10-23.md),
[lời giao tiếp](../../report/lenh-giao-viec-ba-nhom-lan3-2026-10-23.md).

**Cập nhật sau ghép SA-62:** core lecture-3 đã ở main (`1d91b0b`), port PG cũng đã vào main (`9ac2a85`), cổng kết hợp trên `14110c0` có2.355Python/143React/build xanh.
Web nhận main mới rồi cài/kiểm W-08 theo hợp đồng hiện hành. **SA-65 đã ghép `4a4b957`, bàn giao `e5fa492`**;
ảnh trang vẫn ở kho tệp cạnh artifact, dữ liệu mới cần manifest/SHA riêng; không tự sửa lõi hay ghi đè snapshot cũ.

**Quyết định mới nhất 2026-10-23, `9ee69ce`:** ADR 0025 thay cấu trúc lecture-2 bằng lecture-3; SA-63 dừng, thay bằng SA-64.
Nội dung là `body_md` Markdown/LaTeX, `self_check` đáp án gập và `sources[]`; bỏ `sections`/`bridge`.
Stream `skeleton` → `delta {text}` → `final {lecture}` hoặc `failure`. KaTeX hiển thị công thức; nhãn `[Sx]` hợp lệ mở đúng trang nguồn,
khối Trong sách dùng `sources`, nhãn lạ giữ nguyên chữ. Log validation chỉ admin. Đây là hợp đồng triển khai mới, không tiếp tục cài item/lecture-2.
SA-65 chụp ảnh trang công thức vào artifact, do Claude cài/ghép; web không tự sửa lõi hoặc chuyển artifact vào DB.

**Lịch sử cập nhật trước ADR 0025:** chủ dự án chốt ADR 0024, khi đó SA-63 đang cài. Ý LLM hiện ngay khi đóng xong, không chờ đủ hai ý;
trượt luật kiểm không làm bài lỗi hoặc gắn nhãn cho người học. `validation` chỉ nằm trong cache/log admin, không lọt qua JSON/SSE/tool.
`failed` chỉ khi chưa gửi ý nào; hiển thị `failure.message` và luôn có nút Thử lại. Sau ý đầu, lỗi đuôi giữ các ý đã gửi, `ready` + `cat_ngan`.
Không cài theo yêu cầu cũ “stream sau cổng”. Chính sách giữ nội dung/lỗi vẫn có hiệu lực; cấu trúc và sự kiện nay theo lecture-3 ở trên.

**Lịch sử đối chiếu Pha B 2026-10-22, trước ADR 0025:** Claude nghiệm thu SA-53 và ghép `62dad5b`, đóng điểm chờ câu nối final của SA-40/41.
Hợp đồng lecture-2 khi đó nay đã được thay bằng lecture-3 ở đầu vé; kiểm với PostgreSQL/đồ giả. Cập nhật ngày 23: SA-56/58 của W-09 đã vào main;
wrapper lecture/cache_only và HTTP trợ lý thuộc W-09, không tự sửa use case trợ lý trong W-08.
Ưu tiên sửa Required W-11 rồi bắt đầu W-08; xem [lời giao mới](../../report/lenh-giao-viec-sau-w11-2026-10-23.md)
và [soát Pha B của Claude](../../report/soat-pha-b-52-53-sonnet-2026-10-22.md).

## Vì sao

Bấm vào một khái niệm là thao tác chính của người học. Bài giảng phải hiện dần, không bao giờ hiện bản lùi, và khi hỏng hẳn phải có lối ra rõ ràng.

## Cần làm

**Gateway:** `get_lecture`, `stream_lecture`, `open_source_page`, `open_source_file`, `get_media`.
- Bài giảng trong cache chỉ chứa `asset_key`. Gateway đổi thành `/courses/{cid}/media/<asset_key>` lúc trả bài; không bao giờ đưa `public_id` hay link
  Cloudinary ra phản hồi.
- Ảnh công thức và media chưa có trên Cloudinary (khoá mẫu) thì tải lên ở lần đầu được xin, ghi `media_asset`, rồi dùng lại. Bản dựng mới (W-14) tải sẵn ở
  bước `learning_prep`.

**HTTP:**
- `GET /courses/{cid}/concepts/{node_id}/lecture` trả `lecture-3` đầy đủ khi bài đã có trong cache;
- `GET /courses/{cid}/concepts/{node_id}/lecture/stream` là **SSE**: `skeleton`, các `delta {text}` hiện ngay, `final {lecture}` hoặc `failure`;
- `GET /courses/{cid}/source/pages/{p}`: máy chủ lấy ảnh trang p từ Cloudinary (một cỡ, WebP) rồi chuyển cho trình duyệt, `Cache-Control: private,
  max-age=300`;
- `GET /courses/{cid}/source`: chuyển hướng 302 tới link tải riêng tư có hạn 300 giây ("Mở cả tệp");
- `GET /courses/{cid}/media/{asset_key}`: máy chủ chuyển ảnh công thức hay media.
- Người học đóng trang giữa chừng thì lần sinh vẫn chạy xong và vào cache cho người sau. Không huỷ lời gọi đang trả tiền.

**Giao diện trang học** (một module):
- danh sách khái niệm theo thứ tự, có dấu "đã học";
- vùng bài giảng:
  - **`skeleton`:** vị trí, câu định nghĩa nguyên văn kèm trang, ảnh công thức, media;
  - **tiên quyết gập sẵn:** tên, module, nhãn "đã học / chưa học"; mở ra thấy câu định nghĩa;
  - `body_md` văn xuôi Markdown hiện dần theo delta, công thức LaTeX bằng KaTeX; không giữ khối bridge/sections của lecture-2;
  - `self_check.question_md`, đáp án `answer_md` gập sẵn; self_check null thì không bịa câu hỏi;
  - khối Trong sách từ `sources[]`; nhãn `[Sx]` hợp lệ mở đúng trang, nhãn lạ hiện nguyên chữ, không tạo URL tuỳ ý;
  - **khối "Tiếp theo"** ở cuối, bấm được để mở khái niệm đó;
- **đang chờ chữ đầu:** hiện phần mã dựng ngay, vòng chờ GIF WayFinder và câu "Đang soạn bài…"; nhận delta đầu thì hiện ngay, không đợi cả bài;
- **chưa có bài:** khi chưa có chữ dùng được; giữ phần mã dựng, hiện `failure.message` tiếng Việt nêu lý do/thời điểm thử lại, và ba nút:
  - "Đọc trang p trong sách" mở khung xem ảnh trang p (`/source/pages/p`), có nút trang trước, trang sau và "Mở cả tệp"; DOCX hay không có tệp thì nút
    báo không có trang;
  - "Hỏi trợ lý" mở khung chat của module (W-09), điền sẵn câu hỏi về khái niệm;
  - "Thử lại" luôn hiện (`retryable=true` theo hợp đồng mới).
- Cảnh báo `cat_ngan` hiện một dòng nhỏ "Bài được rút gọn".

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Tầng HTTP/React: kịch bản mô hình giả có `skeleton` trước, delta đầu đến/hiện trước khi mô hình trả xong; kết thúc final/failure đúng lecture-3/SA-64.
- [ ] `body_md`, LaTeX inline/block, sources/nhãn hợp lệ và nhãn lạ, self_check/đáp án gập hoặc null đều hiện đúng. Nội dung Markdown không thực thi HTML/script hoặc URL nguy hiểm.
- [ ] Ý trượt luật kiểm vẫn hiện; không nhãn kiểm hay khối `validation` trong JSON/SSE cho người học. Cache/log admin có validation không được trả nguyên ra web.
- [ ] Lỗi sau delta đầu không rút chữ hoặc đổi thành failed: giữ nội dung đã gửi, kết thúc `ready` + `cat_ngan`; không thêm lời gọi sinh lại do log kiểm.
- [ ] Chưa có ý: mọi reason hợp lệ có `failure.message` không rỗng và nút Thử lại; không dùng `kiem_noi_dung`. Lỗi được nhớ 60 giây, hết trần tới hết ngày theo lõi; không hardcode 24 giờ ở React.
- [ ] Hai thành viên mở cùng một khái niệm: tổng cộng 1 lời gọi mô hình; `lecture_key` giống nhau; `learner_status` khác nhau theo tiến độ của mỗi người.
- [ ] Không đường nào trả fallback/TextRank; chưa có bài thì chỉ phần mã dựng/message/lối ra, không bịa body. Lecture-3 không chứa sections/bridge cũ.
- [ ] Ảnh trang, ảnh công thức, "Mở cả tệp" bởi người ngoài khoá thì `not_found`, và `MediaStore` giả ghi 0 lần lấy. Bởi thành viên thì có đủ header.
- [ ] Quét đệ quy mọi phản hồi JSON của bài giảng: không có tên miền Cloudinary hay `public_id`. Cache bài giảng không chứa URL.
- [ ] Trang p ngoài khoảng 1…số trang thì `not_found`.
- [ ] Ngắt kết nối SSE giữa chừng thì lần sinh vẫn xong và vào cache: lần mở sau là 0 lời gọi.
- [ ] Ảnh chụp: chờ chữ đầu, Markdown đang hiện dần/công thức, xong có tiên quyết mở/Trong sách/tự kiểm tra, chưa có bài với message/ba nút; 390/768/1280 px sáng/tối/reduced-motion.

## Ngoài vé

Trợ lý (W-09). Báo lỗi bài giảng (W-19).
