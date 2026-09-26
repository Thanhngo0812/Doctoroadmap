# 17 — Tiền tố chung chung của danh tính từ bằng chứng trong tài liệu

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R16 · **Ai:** nhân viên · **Phụ thuộc:** 10b ·
**Chi phí mô hình:** vài lời gọi phán và xác minh cho cặp mới (≈ 0,01 USD / tài liệu)

**Trạng thái:** chờ giao

## Vì sao
`GENERIC_PREFIXES` gồm "hệ véc tơ", "hệ", "phép", "tính", "khái niệm", "the notion of", "the concept of" — danh sách vi/en. Tài liệu ngôn
ngữ khác bỏ sót ứng viên kiểu "Hệ độc lập tuyến tính cực đại ↔ Độc lập tuyến tính cực đại".

## Việc cần làm
- Bỏ `GENERIC_PREFIXES`. Nguồn đề cử `generic_prefix` mới: tên A = w + tên B, hoặc tên B + w, trong đó w dài ≤ 2 từ (với chữ viết
  không cách từ: ≤ 2 ký tự), và trong cùng tài liệu w gắn theo đúng cách đó với ít nhất ba tên khái niệm khác. Tự hiệu chỉnh theo từng
  tài liệu, như luật tiêu đề lặp của B0. Ngưỡng ghi trong config.
- Chỉ đề cử; lượt phán và lượt xác minh R8b quyết gộp. Chạy cùng lượt danh tính kế tiếp của vé 10b.

## Tệp liên quan
`domain/identity.py` (`identity_candidates`, `_stripped`), `application/use_cases/judge_identity.py` (config).

## Nghiệm thu
- Test trên tên tổng hợp: tiền tố lặp ít nhất ba lần được nhận ở tiếng Việt ("hệ …"), tiếng Pháp ("système …") và dạng hậu tố tiếng Anh
  ("… system"); tiền tố chỉ xuất hiện một lần không được nhận; cặp được đề cử vẫn chỉ gộp khi phán và xác minh cùng đồng ý.
- **Tôi kiểm:** các cặp L6 kiểu tiền tố trên doc-1 vẫn được đề cử; báo số cặp đề cử thêm và chi phí thật; đọc mọi gộp mới.
