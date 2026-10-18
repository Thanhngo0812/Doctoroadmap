# SA-47 — Tiến độ: giữ lựa chọn của người học khi quiz hoàn tất đồng thời

**Nguồn chân lý:** [SA-34](34-tien-do-hoc.md), [spec B2](../../doc/pha-b2-spec.md), mục 5/bất biến 6, [ADR 0019](../../doc/adr/0019-tien-do-hoc-khong-chan-nhan-gan-luc-doc.md).

**Ai:** nhân viên · nhân viên cấp cao kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** đã vá và kiểm thử 2026-10-19; chờ kiểm ghép 46–51

**Bàn giao:** [SA-47](../../report/pha-b-sa47-2026-10-19.md). Hai đường learner/quiz dùng `store.atomic()`, hai bản cài kho giữ hợp đồng. Race đã đỏ trên memory/JSON trước sửa, xanh sau sửa; kiểm mở lại JSON và hai instance use case dùng cùng kho. Không gọi mô hình.

## Vì sao

`ProgressUseCase.mark_quiz_correct` đọc bản ghi rồi ghi lại trong `single_flight`, nhưng `set_progress` không đi cùng cơ chế bảo vệ. Một thứ tự hợp lệ trên máy chủ có nhiều luồng:

1. Quiz đọc chưa có bản ghi learner.
2. Người học bỏ dấu, bản ghi trở thành `not_learned/source=learner`.
3. Quiz ghi đè thành `learned/source=quiz` từ kết quả đọc cũ.

Test `test_learner_not_learned_choice_wins_if_quiz_completion_races` trong `tests/unit/application/test_sa45_sessions_audit_regressions.py` tái hiện đỏ trên mã ngày 2026-10-18, không gọi mô hình. Đây là vi phạm lựa chọn learner luôn thắng, không phải yêu cầu mô hình trình độ mới.

## Cần làm

- Bảo vệ việc đọc/ghi tiến độ theo `(owner, doc_id, node_id)` cho cả thao tác learner và quiz. Việc kiểm nguồn learner và ghi của quiz phải nguyên tử đối với thao tác learner.
- Dùng port/cơ chế kho hiện hành phù hợp, giữ hợp đồng B2 và hai bản cài memory/JSON. Không đặt khoá chỉ ở một instance use case vì mỗi request có thể dựng instance mới.
- Giữ cách ly người học/tài liệu, không làm tiến độ thành điều kiện chặn học.

## Tiêu chí nghiệm thu

- [ ] Test race nêu trên đỏ trước sửa, xanh sau sửa, không treo khi bản sửa dùng khoá chung; bỏ nhãn xfail SA-47.
- [ ] Kiểm cả hai thứ tự learner trước/sau quiz; kết quả cuối cùng là lựa chọn learner, không chỉ kiểm cờ trong luồng quiz.
- [ ] Kiểm qua memory và JSON, hai instance use case dùng cùng kho; không mất bản ghi của node/owner khác.
- [ ] Test quiz nộp đúng, remap module, nhãn bài giảng, nhắc nền và kiến trúc vẫn xanh. Chạy bằng đồ thị tổng hợp, 0 USD.

## Ngoài vé

Không sửa lấy mẫu quiz, phiên hay luật nhắc nền; không chuyển kho sang cơ sở dữ liệu, không sửa ADR.
