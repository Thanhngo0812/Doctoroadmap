# Spec quiz `quiz-3`: câu hỏi kiểm hiểu và vận dụng, giải mù có suy nghĩ

**Ngày:** 2026-10-24 · **ADR:** [0028](adr/0028-quiz-3-cau-hoi-hieu-va-giai-mu.md) · **Liên quan:** [spec bài giảng 3](bai-giang-3-spec.md) mục 11 (tư liệu, chữ thô công
thức, ảnh trang); spec Pha B2 mục 7–8 (phạm vi, trần chi) · **Vé:** SA-68

## Vấn đề

Người học bấm "Làm quiz" để tự kiểm tra. Bản hiện tại (`quiz-2`) có ba vấn đề:
- nhiều khái niệm không có câu nào;
- câu chủ yếu ở mức nhớ, chỉ 3 phương án;
- câu điền khuyết có khi vô nghĩa.

Nguyên nhân là hơn 15 luật loại câu: trích nguyên văn, cấm công thức, độ dài, chữ lặp. Thêm một bước kiểm bị cắt ở 400 token.

## Giải pháp

Mỗi khái niệm có 3 câu 4 phương án ở ba mức nhớ, hiểu, vận dụng, có công thức khi cần và lời giải thích. Câu chỉ được giữ khi một lần giải mù có suy nghĩ ra
cùng đáp án và không thấy đáp án thứ hai. Ngân hàng dùng chung cho mọi người học.

## User stories

1. Là người học, tôi muốn quiz của một module có câu cho mọi khái niệm tôi chọn, không thiếu khái niệm nào.
2. Là người học, tôi muốn câu hỏi kiểm hiểu và vận dụng, không chỉ thuộc định nghĩa.
3. Là người học, tôi muốn 4 phương án, các phương án sai là chỗ người học hay nhầm, không vô lý.
4. Là người học, tôi muốn công thức trong câu và phương án hiện đúng (LaTeX).
5. Là người học, tôi muốn đáp án luôn đúng, vì đáp án sai làm tôi học sai.
6. Là người học, sau khi nộp, tôi muốn thấy vì sao đáp án đúng, và phương án tôi chọn sai ở đâu.
7. Là người học, tôi muốn biết đáp án lấy ở trang nào của sách.
8. Là người học, tôi muốn quiz của khái niệm đã có người làm thì mở ngay, không chờ sinh lại.
9. Là người học, tôi muốn báo một câu sai để admin xem lại.
10. Là admin, tôi muốn log câu bị loại và lý do người giải đưa ra, để theo dõi chất lượng.
11. Là chủ dự án, tôi muốn mỗi khái niệm chỉ tốn khoảng 0,006 USD một lần, dùng chung cho mọi người học.

## Quyết định cài đặt

### 1. Use case

- Thay phần sinh ngân hàng (`_generate_bank`, lời nhắc, `quiz_verify`, `_rules_pass`) bằng luồng `quiz-3`.
- Giữ:
  - `make_quiz` với phạm vi, số câu, lộ trình;
  - lần làm quiz, `submit`, `history`, `report_question`;
  - tiến độ;
  - ngân hàng trong cache chung;
  - trần hệ thống.
- **Câu điền khuyết** chỉ dùng khi không có câu mô hình: hết trần hệ thống, hay mô hình lỗi. Câu điền khuyết bị bỏ khi câu chứa ký hiệu toán (`=`, `[`,
  chữ số đi liền chữ cái…) hay `[formula]`.

### 2. Tư liệu (`quiz-context-3`)

- Gom đoạn như bài giảng: `gather_chunks`, trần `lecture_context_chars`.
- Thay `[formula]` bằng chữ thô (hàm chung của SA-70). Ảnh các trang có công thức, tối đa 8.
- Tin nhắn:
  - `Khái niệm: <tên>`;
  - `Các khái niệm khác cùng module: …`, tối đa 12, làm nguồn cho phương án nhiễu;
  - `Tư liệu từ sách:` với `[Sk] (trang p, mục …)`.

### 3. Sinh câu (`quiz-gen-5`)

Lời nhắc hệ thống, nguyên văn bản thử 2026-10-24. `{formula_rule}` như luật 1, 2 của spec bài giảng mục 4.

```text
Bạn là một giảng viên đại học giỏi, ra câu hỏi trắc nghiệm tiếng Việt để sinh viên tự kiểm tra mức hiểu một khái niệm trong cuốn sách họ đang học.

Ra đúng 3 câu cho khái niệm được nêu:
- Câu 1 kiểm tra nắm định nghĩa hay tính chất cốt lõi. Câu 2 kiểm tra hiểu: giải thích, phân biệt với khái niệm gần, nhận ra ví dụ đúng. Câu 3 kiểm tra vận dụng: một tình huống hay một bài tính ngắn.
- Mỗi câu có 4 phương án, đúng một phương án đúng. Ba phương án sai phải hợp lý với người học chưa nắm chắc: hiểu nhầm thường gặp, khái niệm gần, đảo điều kiện hay đảo chiều phát biểu. Không có phương án vô lý.
- Không để lộ đáp án qua độ dài, cách viết, hay chữ lặp lại từ câu hỏi. Không dùng "tất cả đều đúng", "không có đáp án nào".
- Câu hỏi đọc độc lập được: không viết "theo đoạn trên", "trong tài liệu", không nhắc nhãn nguồn.
- Được dùng công thức LaTeX trong $...$ ở câu hỏi và phương án. Bài tính thì chọn số đơn giản và tính lại cẩn thận.
- Lời giải thích ngắn: vì sao phương án đúng là đúng, mỗi phương án sai sai ở đâu.
- Bám sách: đáp án phải đúng theo sách; dùng đúng ký hiệu và thuật ngữ của sách; giữ đúng chiều và điều kiện của phát biểu trong sách.
- {formula_rule}
```

- **Lược đồ JSON:** `items[]` gồm:
  - `bloom` ∈ {`nho`, `hieu`, `van_dung`};
  - `stem`;
  - `options[4]`, mỗi phương án `{text, why_wrong}`, với `why_wrong` rỗng ở đáp án đúng;
  - `correct_index` từ 0 tới 3;
  - `explanation`;
  - `source_labels`.
- Nhiệt độ 1,0, `quiz_generation_max_output_tokens` 4.096, không bật suy nghĩ.

### 4. Giải mù (`quiz-verify-5`)

Lời nhắc hệ thống, nguyên văn:

```text
Bạn là người giải đề cẩn thận. Đọc tư liệu sách và từng câu trắc nghiệm, rồi tự giải: câu tính toán thì tự tính lại từng bước, không đoán. Chọn phương án đúng theo sách và kiến thức chuẩn. Kiểm cả các phương án còn lại: nếu có phương án khác cũng đúng (kể cả đúng trong điều kiện câu hỏi cho phép), hoặc không phương án nào đúng, đánh dấu ambiguous và nói lý do ngắn.
```

- **Đầu vào:** cùng tư liệu và ảnh; các câu chỉ có `stem` và phương án đã xáo, không có đáp án, giải thích hay `why_wrong`.
- **Lược đồ:** `answers[]` gồm `q`, `chosen` (0–3), `ambiguous`, `reason`.
- **Cấu hình:** nhiệt độ 0, `quiz_verifier_max_output_tokens` 8.192 (từ 400), `thinkingConfig.thinkingLevel` = `quiz_verifier_thinking_level` (`medium`).
- **Giữ câu khi:** người giải chọn đúng đáp án sau khi đổi lại thứ tự gốc, và `ambiguous` sai.
- **Luật cục bộ còn lại,** chạy trước khi giải mù:
  - đúng 4 phương án, khác nhau sau chuẩn hoá;
  - `correct_index` hợp lệ;
  - `stem` không rỗng.
- **Ít hơn 2 câu được giữ thì sinh thêm một lượt** (sinh + giải mù), chỉ một lần. Kết quả lưu vào ngân hàng dù có bao nhiêu câu.

### 5. Ngân hàng và chi

- Khoá ngân hàng có `quiz-gen-5`, `quiz-verify-5`, mức suy nghĩ, băm tư liệu và mô hình.
- Đổi phiên bản thì khái niệm sinh lại khi có người làm.
- Chi tính vào trần hệ thống với `purpose` `quiz_gen` và `quiz_verify`, như cũ.
- Ước tính chi trước khi gọi: chữ chia 3, cộng 1.300 token mỗi ảnh, cộng trần đầu ra.
- Các khái niệm của một lần làm quiz được sinh **song song**, tối đa `quiz_parallel_concepts` (4) cùng lúc.

### 6. Hợp đồng `quiz-3`

- **Câu công khai:** `{item_id, concept_id, module_id, generator: "llm" | "cloze", bloom, stem, options: [{option_id, text}]}`.
  - Câu mô hình có 4 phương án; câu điền khuyết giữ số phương án cũ.
  - `stem`, `text` có thể có LaTeX `$…$`.
- **Kết quả nộp bài:** giữ dạng `quiz-2`, `contract_version` = `quiz-3`.
  - `evidence` là danh sách `{label, chunk_id, page}` theo `source_labels`.
  - `why_wrong` lấy từ phương án người học chọn.
- Không trả lý do của người giải mù cho người học.

### 7. Log cho admin

- Bản ghi `quiz_rejection` cho mỗi câu bị loại: khái niệm, lượt, lý do cục bộ hay `reason` của người giải.
- Dòng usage `quiz_verify` có số câu giữ, số câu loại.

### 8. `BSettings`

| khoá | mặc định |
|---|---|
| `quiz_contract_version` | `quiz-3` |
| `quiz_generation_prompt_version` | `quiz-gen-5` |
| `quiz_verifier_prompt_version` | `quiz-verify-5` |
| `quiz_generation_max_output_tokens` | 4.096 (từ 1.200) |
| `quiz_verifier_max_output_tokens` | 8.192 (từ 400) |
| `quiz_verifier_thinking_level` | `medium` |
| `quiz_items_per_concept` | 3 |
| `quiz_parallel_concepts` | 4 |

## Quyết định kiểm thử

- **Đường nối chính** ở mức use case: hai mô hình giả (sinh, giải) theo kịch bản, cổng ảnh giả, kho trong bộ nhớ.
- **Mẫu test:** `tests/unit/application/test_phase_b_quiz.py`, `test_phase_b_quiz_sa27.py`, và test bài giảng 3 cho tư liệu, ảnh.
- **Bất biến phải có test,** mỗi cái thấy đỏ trước:
  1. Người giải nhận phương án đã xáo, không có đáp án, `explanation` hay `why_wrong`.
  2. Chỉ giữ câu mà người giải chọn đúng đáp án gốc (sau khi đổi thứ tự lại) và `ambiguous` sai. Chọn sai thì loại; `ambiguous` thì loại; mỗi câu bị loại có
     bản ghi `quiz_rejection`.
  3. Lời gọi giải có `thinkingConfig` mức `medium`, nhiệt độ 0. Lời gọi sinh không có `thinkingConfig`.
  4. Câu có LaTeX trong `stem` và phương án được giữ; không còn luật cấm công thức, trích nguyên văn, độ dài.
  5. Ít hơn 2 câu được giữ thì sinh thêm đúng một lượt.
  6. Ngân hàng lần hai: 0 lời gọi. Đổi phiên bản lời nhắc thì sinh lại.
  7. Hết trần hệ thống thì dùng ngân hàng sẵn có, rồi câu điền khuyết. Câu điền khuyết có ký hiệu toán hay `[formula]` bị bỏ.
  8. `submit` trả `why_wrong` của phương án đã chọn và `evidence` theo `source_labels`. Không trả lý do của người giải.
  9. Lời nhắc sinh và giải đúng nguyên văn mục 3, 4.
  10. Tư liệu có `[formula: <raw_text>]` và ảnh trang khi có công thức.
- **Graph thật, chỉ đọc,** cho "Hệ số tương quan mẫu" (xstk v68): tin nhắn sinh câu có đoạn định nghĩa, chữ thô `0,8165`, và 2 ảnh trang.

## Ngoài phạm vi

- Web: hiện 4 phương án, KaTeX trong câu hỏi, lời giải thích. Người điều phối làm theo mục 6.
- Sinh sẵn ngân hàng khi dựng sách.
- Mô hình mạnh hơn hay `high` ở bước giải: chờ đợt đánh giá tổng.
- Dọn mã `quiz-2` cũ.
