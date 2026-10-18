# SA-34 — Tiến độ học theo khái niệm

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 5, 7 (nộp quiz cập nhật tiến độ); [ADR 0019](../../doc/adr/0019-tien-do-hoc-khong-chan-nhan-gan-luc-doc.md).
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 31 · **Trạng thái:** ready-for-agent

## Vì sao

Trang học cần nút "đã học" và hiện "xong x/y" cho mỗi module. Trợ lý và bài giảng cần biết tiên quyết nào người học đã học. Tiến độ không chặn chức năng
nào.

## Cần làm

**Bản ghi tiến độ** theo (owner, doc_id, node_id): `{state: learned | not_learned, source: learner | quiz, updated_at}`.

**Use case:**
- `set_progress(owner, doc_id, node_id, learned)`, ghi `source = learner`;
- `get_progress(owner, doc_id)`, trả trạng thái từng khái niệm và tóm tắt từng module `{module_id, learned, total}` theo đồ thị hiện hành.

**Nộp quiz:** mỗi khái niệm có ít nhất một câu đúng thì được đặt `learned`, `source = quiz`, chỉ khi chưa có bản ghi `source = learner`. Áp cho cả lần làm
do trợ lý tạo.

**Mở bài giảng không đánh dấu gì.**

**CLI:** lệnh đánh dấu, bỏ dấu và xem tiến độ.

## Tiêu chí nghiệm thu

- [ ] Test, mỗi cái thấy đỏ trước:
  - đánh dấu rồi bỏ dấu thì trạng thái đúng theo lần bấm sau cùng;
  - người học bỏ dấu, rồi nộp quiz đúng câu của khái niệm đó, thì khái niệm vẫn `not_learned`;
  - chưa có bản ghi của người học, nộp quiz đúng thì `learned` với `source = quiz`;
  - nộp quiz sai hết thì không đánh dấu gì;
  - tóm tắt module đếm theo đồ thị hiện hành; dùng cặp đồ thị v1, v2 của vé 31, tiến độ theo `node_id` vẫn đúng sau khi chia module khác;
  - `owner` khác không đọc hay ghi được tiến độ.
- [ ] Ví dụ JSON thật của `progress-1` đính kèm báo cáo vé.
