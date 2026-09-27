# 16 — Tên, ký hiệu và tìm nhắc tên không phụ thuộc chữ viết

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R15 · **Ai:** nhân viên · **Phụ thuộc:** — ·
**Chi phí mô hình:** 0 · **Ưu tiên:** cao nhất trong nhóm vé đa ngôn ngữ

**Trạng thái:** đã triển khai và kiểm thử 2026-09-27; chờ reviewer nghiệm thu. [Kết quả](../../report/v3-05-14-16-ket-qua-2026-09-27.md).

## Vì sao
- `canonical.alias_kind` chỉ coi một chuỗi là "tên" khi có chữ cái LATIN. Thử 2026-09-26: "Векторное пространство", "向量空间",
  "ベクトル空間", "Διανυσματικός χώρος", "متجه" đều bị xếp là ký hiệu.
- Hệ quả: A3 loại mọi khái niệm có tên bị coi là ký hiệu mà không có alias Latin (`rejected_symbol_only_name`) — tức gần hết khái niệm
  của sách chữ không Latin; A4 bỏ các tên đó khi đề cử; A6 bỏ chúng khi tìm nhắc tên.
- `exact_mentions` đòi ranh giới `(?<!\w)…(?!\w)`, nên với chữ viết không cách từ không khớp được tên nào; `retrieval._tokens` tách theo
  khoảng trắng, nên BM25 không dùng được cho các chữ viết đó.

## Việc cần làm
- **`alias_kind`:** "tên" khi có ít nhất một từ gồm ≥ 2 chữ cái (Unicode `L*`) không thuộc khối Mathematical Alphanumeric Symbols hay
  Letterlike Symbols và không phải chỉ số trên/dưới; "ký hiệu" cho phần còn lại; "abbreviation" giữ như cũ. Bỏ điều kiện "LATIN".
- **`exact_mentions`:** tên có chữ thuộc chữ viết không cách từ (Hán, Hiragana, Katakana, Thái, Lào, Khmer, Myanmar — nhận theo khối
  hay thuộc tính Unicode) thì khớp chuỗi con, không đòi ranh giới; còn lại giữ ranh giới như cũ.
- **`retrieval._tokens`:** đoạn thuộc các chữ viết đó tách thành bigram ký tự (ký tự đứng riêng giữ unigram); chữ viết có cách từ
  giữ nguyên.
- Không thêm phụ thuộc mới nếu bảng khối Unicode là đủ.
- **Không làm tài liệu hiện có phải chạy lại:** ba sửa này phải cho kết quả y hệt với mọi tên và văn bản có chữ Latin. Chứng minh bằng
  cách phân loại lại mọi tên và alias trong artifact candidates/canonical hiện có, và tính lại `exact_mentions` cùng token BM25 trên
  chunk hiện có — 0 khác biệt. Ghi phiên bản luật vào manifest; chỉ đổi khoá cache của stage nào mà đầu ra thật sự đổi.

## Tệp liên quan
`domain/canonical.py` (`alias_kind`, `structured_symbol`), `application/use_cases/extract_entities.py`, `domain/nomination.py`,
`domain/mentions.py` (`exact_mentions`), `domain/retrieval.py` (`_tokens`).

## Nghiệm thu
- Test `alias_kind` trên tên nhiều chữ viết (Kirin, Hán, Nhật, Hy Lạp, Ả Rập, Devanagari, Thái) → tên; chữ đơn, chữ toán 𝑇, ℳ, chỉ số →
  ký hiệu; mọi tên Latin trong fixture hiện có giữ nguyên phân loại.
- Test `exact_mentions`: "向量空间" khớp trong "…在向量空间中…"; "set" vẫn không khớp bên trong "subset".
- Test BM25: câu tiếng Trung truy hồi được bằng một từ hai ký tự; token tiếng Việt, tiếng Anh như cũ.
- Test A3: khái niệm tên tiếng Nga không có alias Latin không còn bị `rejected_symbol_only_name`.
- **Tôi kiểm:** 0 khác biệt phân loại và khớp trên sáu tài liệu phát triển (doc-4, xstk so bằng hash, không đọc nội dung); `--dry-run`
  sáu tài liệu không có stage tốn tiền nào chuyển sang "sẽ chạy". Khi có T19: chạy A3 trên tài liệu chữ không Latin, xem số
  `rejected_symbol_only_name`.
