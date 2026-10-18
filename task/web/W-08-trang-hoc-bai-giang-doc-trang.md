# W-08 — Trang học: bài giảng stream, "Đọc trang p"

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 6 (`lecture-2`, stream sau cổng, bài hỏng hẳn, nhãn theo người học), mục 10; [spec chức năng](../../doc/web-chuc-nang-spec.md),
mục 1 (SSE), 7 (mở tệp gốc); [ADR 0018](../../doc/adr/0018-bai-giang-khong-hien-ban-lui-stream-sau-cong.md); spec thiết kế, trang học và vòng chờ.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** W-07, SA-39, SA-40, SA-41 · **Trạng thái:**
ready-for-agent

## Vì sao

Bấm vào một khái niệm là thao tác chính của người học. Bài giảng phải hiện dần, không bao giờ hiện bản lùi, và khi hỏng hẳn phải có lối ra rõ ràng.

## Cần làm

**Gateway:** `get_lecture`, `stream_lecture`, `open_source_file`.

**HTTP:**
- `GET /courses/{cid}/concepts/{node_id}/lecture` trả `lecture-2` đầy đủ, khi bài đã có trong cache;
- `GET /courses/{cid}/concepts/{node_id}/lecture/stream` là **SSE**, với đúng các sự kiện `skeleton`, `item` (chỉ sau cổng), `final`, `failure`;
- `GET /courses/{cid}/source` trả PDF gốc với các header ở spec chức năng mục 7.
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
  - "Đọc trang p trong sách" mở `/source#page=p` ở thẻ mới; DOCX hay không có tệp thì nút báo không có trang;
  - "Hỏi trợ lý" mở khung chat của module (W-09), điền sẵn câu hỏi về khái niệm;
  - "Thử lại" chỉ hiện khi `retryable`.
- Cảnh báo `cat_ngan` hiện một dòng nhỏ "Bài được rút gọn".

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Tầng HTTP: luồng SSE của một kịch bản mô hình giả có `skeleton` đầu tiên, không có `item` trước cổng, và kết thúc bằng `final` hay `failure`.
- [ ] Hai thành viên mở cùng một khái niệm: tổng cộng 1 lời gọi mô hình; `lecture_key` giống nhau; `learner_status` khác nhau theo tiến độ của mỗi người.
- [ ] Không đường nào trả `status = fallback` hay câu do TextRank chọn. Một test chạy kịch bản hỏng hẳn và kiểm phản hồi không có trường `sections` nào
  ngoài phần mã dựng.
- [ ] `GET /source` bởi người ngoài khoá thì `not_found`; bởi thành viên thì có đủ header.
- [ ] Ngắt kết nối SSE giữa chừng thì lần sinh vẫn xong và vào cache: lần mở sau là 0 lời gọi.
- [ ] Ảnh chụp: bài đang chờ (vòng chờ), bài đã xong có tiên quyết mở, bài hỏng hẳn với ba nút; cỡ 390 px và 1280 px.

## Ngoài vé

Trợ lý (W-09). Báo lỗi bài giảng (W-19).
