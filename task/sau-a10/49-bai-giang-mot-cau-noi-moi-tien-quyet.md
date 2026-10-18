# SA-49 — Bài giảng: một câu nối cho mỗi tiên quyết, nhất quán stream và final

**Nguồn chân lý:** [SA-40](40-goi-lai-tien-quyet-cau-noi-tiep-theo.md), [spec B2](../../doc/pha-b2-spec.md), mục 6/K10–K12 và nguyên tắc không rút ý đã gửi.

**Ai:** nhân viên · nhân viên cấp cao kiểm · **Chi phí mô hình:** 0 USD (phản hồi đã ghi/mô hình giả) · **Chặn bởi:** không · **Trạng thái:** ready-for-agent

## Vì sao

Đọc 12 bài SA-43 phát lại ở `tmp/phaseb-sa43-replay-20261018.json`: Bát chính đạo có hai câu nối cùng tiên quyết Tứ đế, Tỉ lệ tổng thể cũng có hai câu nối cùng tiên quyết. Tổng nhánh nhiệt độ 0 có 8 item bridge nhưng chỉ 6 cặp `(bài, tiên quyết)` khác nhau. Đây không phải một câu nối cho mỗi tiên quyết như spec.

`_merge_emitted` loại trùng toàn bộ JSON nên hai diễn đạt khác chữ cho cùng `prereq` cùng được giữ. Test `test_same_prerequisite_has_only_one_bridge_in_lecture_sections` trong `tests/unit/application/test_phase_b_sa45_lecture_audit.py` đã đỏ trên bản hiện hành (2 thay vì 1).

## Cần làm

- Chỉ chấp nhận một câu nối đạt K11/K12 cho mỗi tiên quyết; chọn nhất quán theo thứ tự phát. Không để candidate hỏng chiếm chỗ của câu đạt đến sau.
- Áp dụng trước khi gửi item ra stream, cho cả lần sinh đầu và sửa bài, không chỉ lọc bản final sau khi đã gửi hai câu.
- Giữ một câu đã phát, không thay hay rút nó khi candidate sau khác chữ. `prerequisites[].bridge`, sections và final phải nhất quán với các item đã phát.
- Đổi phiên bản luật/cache để bài cũ có câu nối trùng không được trả nguyên từ cache.

## Tiêu chí nghiệm thu

- [ ] Regression nêu trên đỏ trước sửa, xanh sau sửa; bỏ nhãn xfail SA-49.
- [ ] Thêm test `LectureUseCase` thật với mô hình stream giả trả hai câu khác chữ cùng `prereq`: một item câu nối được gửi và một câu trong final; câu nối của tiên quyết khác vẫn còn.
- [ ] Kiểm candidate hỏng trước/câu đạt sau, candidate trùng qua lần sửa, cache đọc lại; không gửi item trước cổng, không thay ý đã phát.
- [ ] Phát lại 0 USD cả 12 phản hồi đã lưu: báo số item bridge và số cặp `(bài, tiên quyết)` riêng, đọc lại hai bài đã lỗi. Ghi rõ nếu prompt mới làm fixture cũ không khớp; không sửa prompt hash của fixture để che lệch.
- [ ] Test lecture, hợp đồng và kiến trúc xanh, không phát sinh HTTP.

## Ngoài vé

Không đổi S3 sang S2, nhiệt độ retry, luật cạnh Q hay sửa neo Pha A. Lặp ý theo nghĩa trong explanation/example để vé đánh giá 21, không thay K6 thành bộ chấm ngữ nghĩa.
