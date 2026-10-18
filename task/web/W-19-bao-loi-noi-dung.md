# W-19 — Báo lỗi nội dung

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 7 ("Báo lỗi nội dung"), 9; [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), bảng
`content_report`; spec thiết kế, nút và hộp báo lỗi.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-08, W-09, W-10 · **Trạng thái:** ready-for-agent

## Vì sao

Bài giảng, câu trả lời, câu quiz đều do LLM sinh. Người học là người thấy lỗi đầu tiên. Báo lỗi có `lecture_key` hay mã đối tượng thì nhóm phát triển tìm
lại đúng bản để sửa, và có thêm dữ liệu cho các vé đánh giá 20–23.

## Cần làm

**`LearningGateway.report_content`** với `target_kind` ∈ {`lecture`, `answer`, `quiz_item`, `document`}, `reason` ∈ {`sai_noi_dung`, `sai_trich_dan`,
`kho_hieu`, `khac`}, `note` ≤ 500 ký tự.
- Lưu `doc_id` và `graph_version` cùng mã đối tượng (`lecture_key`, mã lượt, mã câu, mã tài liệu).
- Câu quiz gọi thêm `report_question` có sẵn của Pha B.
- Mỗi người chỉ báo một lần cho mỗi đối tượng; báo lại thì cập nhật lý do.

**Danh sách:**
- chủ khoá xem báo lỗi của khoá mình;
- admin xem tất cả, đánh dấu `seen`.

**HTTP:** `POST /courses/{cid}/reports`; chủ khoá đọc qua `GET /courses/{cid}/reports`; admin qua `GET /admin/reports`, `PATCH /admin/reports/{id}`.

**Di trú:** `content_report`.

**Giao diện:** nút "Báo lỗi" nhỏ ở cuối bài giảng, mỗi câu trả lời, mỗi câu quiz sau khi nộp, mỗi tài liệu; hộp chọn lý do và ghi chú; danh sách báo lỗi ở
trang quản lý khoá và khu quản trị.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Báo lỗi một bài giảng lưu đúng `lecture_key` của bài người đó đang xem.
- [ ] Báo lỗi câu quiz tạo cả hàng `content_report` lẫn bản ghi `quiz_question_report` của Pha B.
- [ ] Báo hai lần cùng đối tượng thì vẫn một hàng.
- [ ] Thành viên thường không xem được danh sách báo lỗi của khoá.
- [ ] Ảnh chụp nút, hộp báo lỗi, và danh sách của chủ khoá.

## Ngoài vé

Tự động sinh lại nội dung bị báo lỗi.
