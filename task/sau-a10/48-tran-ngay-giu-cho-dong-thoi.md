# SA-48 — Trần ngày: chặn tổng chi khi nhiều lời gọi đồng thời

**Nguồn chân lý:** [SA-42](42-tran-chi-theo-ngay.md), [spec B2](../../doc/pha-b2-spec.md), mục 8/bất biến 17–18.

**Ai:** nhân viên · nhân viên cấp cao kiểm · **Chi phí mô hình:** 0 USD (mô hình giả/phát lại) · **Chặn bởi:** không · **Trạng thái:** đạt sau vá/kiểm ghép 2026-10-19; xem [bàn giao 46–51](../../report/pha-b-sa46-51-2026-10-19.md)

Bằng chứng: [triển khai SA-48](../../report/pha-b-sa48-2026-10-19.md), [soát độc lập](../../report/soat-pha-b-sa48-2026-10-19.md).

## Vì sao

`DailySpendGuard.check` chỉ cộng ledger đã hoàn tất. Hai request cùng lúc đều thấy đủ tiền, qua kiểm, rồi đều gọi provider. Quiz còn chạy tối đa tám khái niệm đồng thời; bài giảng khác node và assistant/tài liệu cũng có thể cùng chạy.

Test `test_concurrent_paid_calls_do_not_exceed_daily_cap` trong `tests/unit/application/test_sa45_sessions_audit_regressions.py` dùng hai `call_json` thật với `NoNetworkFakeModel` và cùng owner. Mỗi phản hồi giả có token tương ứng 0,12 USD, trần 0,20 USD. Đo độc lập thấy **hai model calls và ledger 0,24 USD**; assertion tổng ledger đỏ trên mã hiện hành. Không có lời gọi mạng hoặc tiền thật trong test.

## Cần làm

- Giữ chỗ ngân sách nguyên tử trước khi cho phép gọi mô hình, hoặc cơ chế đồng bộ tương đương giữ đúng trần. Phải tính cả lượt đang chạy, không chỉ ledger đã ghi.
- Áp dụng nhất quán cho ngân sách learner (assistant + document, qua nhiều tài liệu) và hệ thống (lecture + quiz generation/verification), qua các instance use case/guard dùng cùng kho.
- Chốt giữ chỗ theo usage thực, giải phóng phần dư/lượt không tốn tiền; lỗi sau khi provider đã tính tiền vẫn ghi chi phí đúng một lần. Không biến lỗi parse thành lượt miễn phí.
- Cache/phát lại vẫn dùng được khi hết trần, không giữ chỗ có tiền cho phản hồi phát lại. Ngày tính theo đồng hồ/múi giờ cấu hình.

## Tiêu chí nghiệm thu

- [x] Test race đã nêu đỏ trước sửa, xanh sau sửa, bỏ nhãn xfail SA-48; kiểm model calls và ledger, không chỉ cờ cấp phép.
- [x] Hai lượt có tổng ước tính vượt phần tiền còn lại không cùng được gọi; lượt đủ tiền vẫn được gọi sau khi phần giữ chỗ dư giải phóng.
- [x] Kiểm hai nhóm learner/system, hai guard/instance dùng cùng kho, đổi ngày/timezone, cache/phát lại sau khi hết trần.
- [x] Kiểm timeout, lỗi mạng không usage, lỗi parse có usage: không giữ chỗ vĩnh viễn, không ghi chi hai lần. Tất cả bằng mô hình giả, 0 USD.
- [x] Test memory/JSON, assistant, tài liệu, quiz, lecture và kiến trúc xanh; hợp đồng `daily_limit` giữ nguyên.

## Ngoài vé

Không đổi mức trần chủ dự án đã duyệt, giá mô hình, retry temperature hoặc kiến trúc stream. Không chạy có tiền để kiểm trần.
