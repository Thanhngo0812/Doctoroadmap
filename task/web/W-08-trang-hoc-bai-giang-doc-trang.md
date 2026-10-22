# W-08 — Trang học: bài giảng stream, "Đọc trang p"

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 6 (`lecture-2`, stream sau cổng, bài hỏng hẳn, nhãn theo người học), mục 10; [spec chức năng](../../doc/web-chuc-nang-spec.md),
mục 1 (SSE), 7 (mở tệp gốc); [ADR 0018](../../doc/adr/0018-bai-giang-khong-hien-ban-lui-stream-sau-cong.md); spec thiết kế, trang học và vòng chờ.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** W-07, SA-39, SA-40, SA-41 · **Trạng thái:**
đủ phụ thuộc lõi để triển khai; xếp sau W-11 nếu chỉ có một phiên web.

**Đối chiếu Pha B 2026-10-22, cập nhật:** Claude đã nghiệm thu SA-53 và ghép `62dad5b`, đóng điểm chờ câu nối final của SA-40/41.
Nhận main có mốc này, giữ hợp đồng `lecture-2`/SSE và kiểm với PostgreSQL/đồ giả. W-09 có phụ thuộc riêng SA-56; không tự sửa use case trợ lý
trong W-08. Xem [soát Pha B của Claude](../../report/soat-pha-b-52-53-sonnet-2026-10-22.md).

## Vì sao

Bấm vào một khái niệm là thao tác chính của người học. Bài giảng phải hiện dần, không bao giờ hiện bản lùi, và khi hỏng hẳn phải có lối ra rõ ràng.

## Cần làm

**Gateway:** `get_lecture`, `stream_lecture`, `open_source_page`, `open_source_file`, `get_media`.
- Bài giảng trong cache chỉ chứa `asset_key`. Gateway đổi thành `/courses/{cid}/media/<asset_key>` lúc trả bài; không bao giờ đưa `public_id` hay link
  Cloudinary ra phản hồi.
- Ảnh công thức và media chưa có trên Cloudinary (khoá mẫu) thì tải lên ở lần đầu được xin, ghi `media_asset`, rồi dùng lại. Bản dựng mới (W-14) tải sẵn ở
  bước `learning_prep`.

**HTTP:**
- `GET /courses/{cid}/concepts/{node_id}/lecture` trả `lecture-2` đầy đủ, khi bài đã có trong cache;
- `GET /courses/{cid}/concepts/{node_id}/lecture/stream` là **SSE**, với đúng các sự kiện `skeleton`, `item` (chỉ sau cổng), `final`, `failure`;
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
  - câu nối hiện khi tới;
  - các ý giải thích, ví dụ, phân biệt, tự kiểm tra hiện dần;
  - **khối "Tiếp theo"** ở cuối, bấm được để mở khái niệm đó;
- **trước cổng:** hiện vòng chờ GIF WayFinder theo spec thiết kế, kèm câu "Đang soạn bài…". Không hiện ý nào;
- **bài hỏng hẳn:** giữ phần mã dựng, cộng lời nhắn theo `reason_code`, và ba nút:
  - "Đọc trang p trong sách" mở khung xem ảnh trang p (`/source/pages/p`), có nút trang trước, trang sau và "Mở cả tệp"; DOCX hay không có tệp thì nút
    báo không có trang;
  - "Hỏi trợ lý" mở khung chat của module (W-09), điền sẵn câu hỏi về khái niệm;
  - "Thử lại" chỉ hiện khi `retryable`.
- Cảnh báo `cat_ngan` hiện một dòng nhỏ "Bài được rút gọn".

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Tầng HTTP: luồng SSE của một kịch bản mô hình giả có `skeleton` đầu tiên, không có `item` trước cổng, và kết thúc bằng `final` hay `failure`.
- [ ] Hai thành viên mở cùng một khái niệm: tổng cộng 1 lời gọi mô hình; `lecture_key` giống nhau; `learner_status` khác nhau theo tiến độ của mỗi người.
- [ ] Không đường nào trả `status = fallback` hay câu do TextRank chọn. Một test chạy kịch bản hỏng hẳn và kiểm phản hồi không có trường `sections` nào
  ngoài phần mã dựng.
- [ ] Ảnh trang, ảnh công thức, "Mở cả tệp" bởi người ngoài khoá thì `not_found`, và `MediaStore` giả ghi 0 lần lấy. Bởi thành viên thì có đủ header.
- [ ] Quét đệ quy mọi phản hồi JSON của bài giảng: không có tên miền Cloudinary hay `public_id`. Cache bài giảng không chứa URL.
- [ ] Trang p ngoài khoảng 1…số trang thì `not_found`.
- [ ] Ngắt kết nối SSE giữa chừng thì lần sinh vẫn xong và vào cache: lần mở sau là 0 lời gọi.
- [ ] Ảnh chụp: bài đang chờ (vòng chờ), bài đã xong có tiên quyết mở, bài hỏng hẳn với ba nút; cỡ 390 px và 1280 px.

## Ngoài vé

Trợ lý (W-09). Báo lỗi bài giảng (W-19).
