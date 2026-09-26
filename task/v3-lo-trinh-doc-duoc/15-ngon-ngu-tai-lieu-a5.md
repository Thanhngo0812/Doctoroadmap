# 15 — Ngôn ngữ tài liệu bất kỳ ở A5

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R14 · **Ai:** nhân viên · **Phụ thuộc:** — ·
**Chi phí mô hình:** một lời gọi mỗi tài liệu để xác định ngôn ngữ khi không khai (≈ 0,0001 USD)

**Trạng thái:** chờ giao

## Vì sao
- `canonicalize --language` chỉ nhận `vi` hoặc `en`.
- `document_language` trả `vi` nếu ít nhất 10% chữ cái mang dấu tiếng Việt, còn lại là `en`; mô tả bị kiểm bằng `vietnamese()`. Sách
  tiếng Pháp, Trung, Nga vì thế nhận mô tả tiếng Anh.
- Thử 2026-09-26: câu tiếng Pháp "Cette définition sera utilisée à chaque étape du chapitre." bị `vietnamese()` nhận là tiếng Việt,
  nên mô tả đúng có thể bị bác.
- Tách câu của mô tả dùng `[.!?]` ASCII: một đoạn tiếng Trung ba câu bị coi là một câu.

## Việc cần làm
- `--language` nhận mã ISO 639-1 bất kỳ (chỉ kiểm định dạng, không kiểm theo danh sách).
- Không khai thì xác định một lần mỗi tài liệu bằng một lời gọi mô hình trên vài đoạn văn xuôi mẫu, trả mã ISO 639-1; cache theo
  nguồn; ghi mã và cách xác định vào config/manifest.
- Prompt mô tả nhận mã ngôn ngữ; mô tả viết bằng ngôn ngữ đó.
- Kiểm "mô tả khác ngôn ngữ tài liệu" bằng chữ viết: chữ viết chiếm đa số của mô tả phải trùng chữ viết chiếm đa số của tài liệu
  (thuộc tính Unicode). Bỏ `vietnamese()` và mọi nhánh vi/en trong `canonicalize.py`, `canonical_decisions.py`,
  `canonical_reasoning.py`.
- Tách câu của mô tả dùng luật ranh giới câu Unicode của `UnicodeSentenceSplitter` (B0).
- A5 chạy bằng lệnh `canonicalize` riêng, ngoài chuỗi `roadmap`: vé này **không chạy lại** `canonicalize` trên tài liệu hiện có.

## Tệp liên quan
`application/use_cases/canonicalize.py`, `domain/canonical_decisions.py` (`document_language`, `vietnamese`, `split_sentences`,
`validate_description`), `application/use_cases/canonical_reasoning.py`, CLI `canonicalize --language`.

## Nghiệm thu
- Test với mô hình giả: mã ngôn ngữ lấy từ lời gọi xác định, được cache; `--language fr` được nhận, `--language xyz1` bị từ chối.
- Test kiểm mô tả: mô tả tiếng Pháp cho tài liệu `fr` được nhận; mô tả tiếng Anh cho tài liệu `zh` bị bác (khác chữ viết); câu tiếng
  Pháp nhiều dấu không còn bị coi là tiếng Việt.
- Test tách câu: đoạn tiếng Trung ba câu thành ba câu; mô tả tiếng Việt, tiếng Anh tách như cũ.
- **Tôi kiểm:** lời gọi xác định ngôn ngữ trên sáu tài liệu phát triển ra đúng mã mà hàm cũ `document_language` cho trên cùng chunk
  (tôi đã tính 2026-09-26: `vi` cho doc-1, doc-6, nhap-mon-ml, naive-bayes; `en` cho doc-2, doc-3). Khi có T19: chạy A5 trên tài liệu
  ngôn ngữ thứ ba và đọc mô tả.
