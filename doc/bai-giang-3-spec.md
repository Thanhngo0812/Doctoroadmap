# Spec bài giảng `lecture-3`: văn xuôi tự nhiên

**Ngày:** 2026-10-23 · **Quyết định:** [ADR 0025](adr/0025-bai-giang-3-van-xuoi-tu-nhien.md), giữ [ADR 0024](adr/0024-bai-giang-luon-hien-luat-kiem-chi-ghi-log.md)
và phần không hiện bản trích câu của [ADR 0018](adr/0018-bai-giang-khong-hien-ban-lui-stream-sau-cong.md) · **Thay:** [spec Pha B2](pha-b2-spec.md) mục 6,
phần cấu trúc bài và luật K · **Vé:** SA-64 (bài giảng), SA-65 (ảnh trang)

## Vấn đề

Người học bấm khái niệm thì nhận vài câu nhắc lại câu định nghĩa, hoặc không có bài. Chủ dự án: "rất tệ, tôi muốn tự nhiên và sáng tạo chút chứ ko sao mà
ra production được".

## Giải pháp

Bài giảng là một bài văn xuôi Markdown, viết như giảng viên giỏi giảng trên lớp. Mô hình có tư liệu rộng từ cả cuốn sách và thấy ảnh trang khi có công thức.
Bài luôn hiện.

## User stories

1. Là người học, tôi muốn bài giảng đọc liền mạch như thầy giảng, để hiểu khái niệm chứ không chỉ thuộc định nghĩa.
2. Là người học, tôi muốn bài mở đầu bằng việc khái niệm này giải quyết vấn đề gì, để biết vì sao phải học.
3. Là người học, tôi muốn có trực giác trước rồi mới tới định nghĩa chính xác theo sách.
4. Là người học, tôi muốn ít nhất một ví dụ giải từng bước, ưu tiên ví dụ trong sách, để làm theo được.
5. Là người học, tôi muốn có ví dụ hay hình ảnh đời thường khi nó giúp hiểu.
6. Là người học, tôi muốn biết chỗ người học hay nhầm.
7. Là người học, tôi muốn công thức hiện đúng như sách, đúng ký hiệu của sách.
8. Là người học, tôi muốn biết khái niệm này dùng vào đâu tiếp.
9. Là người học, tôi muốn một câu tự kiểm tra, đáp án gập sẵn.
10. Là người học, tôi muốn bấm nhãn nguồn hay khối "Trong sách" để mở đúng trang sách.
11. Là người học, tôi muốn chữ hiện dần ngay khi mô hình viết, không chờ cả bài.
12. Là người học, tôi muốn khái niệm sách nói ít vẫn có bài đủ ý.
13. Là người học, tôi muốn khi không có bài thì thấy lý do và nút "Thử lại".
14. Là admin, tôi muốn log mỗi bài: độ dài, nhãn nào trùng nguồn bao nhiêu, còn `[formula]` không, có câu tự kiểm tra không, có thiếu ảnh trang không.
15. Là chủ dự án, tôi muốn bài sinh một lần rồi dùng chung, để chi thấp và mọi người học thấy cùng một bài.

## Quyết định cài đặt

### 1. Use case mới, mã cũ giữ nguyên

- Use case bài giảng mới thay use case `lecture-2` ở composition: nút bấm, công cụ `get_lecture` của trợ lý, trang xem thử, CLI.
- Mã `lecture-2` giữ nguyên tới vé dọn dẹp, vì script đánh giá cũ còn dùng.
- Phần mã dựng giữ như `lecture-2`: vị trí, câu định nghĩa nguyên văn kèm trang và ảnh công thức, khối gợi lại tiên quyết (`recall`), `next_up`, nhãn theo
  người học (ADR 0019).
- Bỏ câu nối do LLM viết: bài văn xuôi tự nối sang tiên quyết.

### 2. Gom tư liệu (`lecture-context-3`)

Theo thứ tự ưu tiên, chỉ lấy đoạn vai trò `noi_dung` hay `bai_tap`:
1. đoạn chứa câu định nghĩa (không có thì đoạn đầu tiên nhắc tên khái niệm), và đoạn liền sau cùng chương;
2. các đoạn có tên hay bí danh khái niệm trong tiêu đề mục, mỗi đoạn kèm đoạn liền sau;
3. các đoạn nhắc tên hay bí danh nhiều nhất trong cả cuốn;
4. đoạn liền trước, và đoạn thứ hai, thứ ba sau đoạn định nghĩa.

So khớp tên theo NFC, không phân biệt hoa thường, tên dài ít nhất 3 ký tự. Dừng khi tổng chữ vượt `lecture_context_chars` (9.000). Xếp lại theo thứ tự đọc,
đánh nhãn `S1…Sn`. Kèm theo:
- tiên quyết: tên, số module, câu định nghĩa cắt 400 ký tự;
- tên các khái niệm `next_up`.

### 3. Ảnh trang

- Khi có đoạn tư liệu chứa `[formula]`, gửi kèm ảnh các trang của những đoạn đó, tối đa `lecture_max_page_images` (4) trang, theo thứ tự đọc.
- Ảnh đọc qua một cổng `PageImages` (`doc_id`, `parse_version`, trang → JPEG hoặc không có). Adapter đọc kho artifact theo định dạng của SA-65.
- Không có ảnh thì chạy chỉ với chữ, và log `thieu_anh_trang`.
- Mỗi ảnh đi kèm một dòng chữ "Ảnh trang p của sách:".

### 4. Lời nhắc (`lecture-prompt-4`)

Lời nhắc hệ thống, nguyên văn. Bản đã thử ngày 2026-10-23 (V4), cộng ba chỗ sửa của V5 ngày 2026-10-24 (mục 11). `{formula_rule}` là luật 1
khi có ảnh, luật 2 khi không có ảnh.

```text
Bạn là một giảng viên đại học giỏi và tận tâm. Bạn viết bài giảng bằng tiếng Việt cho sinh viên đang tự học từ một cuốn sách. Mục tiêu: đọc xong, sinh viên hiểu thật sự khái niệm, không chỉ thuộc định nghĩa.

Cách viết:
- Văn xuôi tự nhiên, mạch lạc, như đang giảng trên lớp: gần gũi nhưng chính xác. Không liệt kê khô khan, không lặp lại cùng một ý bằng lời khác.
- Mở đầu bằng một hai câu cho thấy khái niệm này giải quyết vấn đề gì, hay vì sao cần nó. Nếu có khái niệm tiên quyết, nối sang nó tự nhiên; không viết "như bạn đã học".
- Giải thích trực giác trước, rồi nêu chính xác định nghĩa hay phát biểu theo sách.
- Có ít nhất một ví dụ cụ thể, giải từng bước. Ưu tiên ví dụ trong sách. Được thêm một ví dụ hay hình ảnh so sánh đời thường do bạn nghĩ ra nếu nó giúp hiểu, miễn là đúng: soát lại từng con số, từng bước suy luận của ví dụ tự nghĩ trước khi viết.
- Nêu một hai chỗ người học hay nhầm, hoặc phân biệt với khái niệm gần.
- Kết bằng một câu nối sang khái niệm tiếp theo trong danh sách "Khái niệm tiếp theo" nếu có: nói khái niệm này cần cho nó ở chỗ nào. Đừng tự định nghĩa hay mô tả khái niệm tiếp theo khi tư liệu không nói về nó.
- Cuối bài: một câu hỏi tự kiểm tra ngắn, kèm đáp án.

Trung thực với sách:
- Sách là chuẩn. Không viết điều mâu thuẫn với sách. Dùng đúng ký hiệu và thuật ngữ của sách.
- Giữ đúng chiều và phạm vi của phát biểu trong sách: sách nói "nếu A thì B" thì đừng viết thành "nếu B thì A"; điều sách gán cho đối tượng hay vai trò nào thì giữ đúng đối tượng, vai trò đó.
- Viết công thức bằng LaTeX trong $...$ hoặc $$...$$.
- {formula_rule}
- Đoạn nào dựa vào sách thì gắn nhãn nguồn như [S2] ở cuối đoạn. Phần trực giác hay ví dụ tự nghĩ thì không cần nhãn.
- Nếu tư liệu nói ít về khái niệm, vẫn giảng đầy đủ bằng hiểu biết chung, nhưng không mâu thuẫn với sách.

Định dạng: Markdown, có thể dùng vài tiêu đề nhỏ (###) nếu giúp dễ đọc. Dài khoảng 300–550 từ, tuỳ khái niệm khó hay dễ. Không chào hỏi, không nói về bản thân, không nhắc tới "tư liệu" hay "đoạn trích".
```

- Luật 1, khi có ảnh: `Chữ "[formula: …]" là chỗ công thức bị mất khi trích PDF; phần sau dấu hai chấm là chữ trích thô của công thức, có thể lộn thứ tự và mất ký hiệu. Ảnh các trang sách được đính kèm: đọc công thức đúng từ ảnh. Công thức ở trang không có ảnh thì dựng lại từ chữ trích thô, chỉ khi chắc chắn; không chắc thì diễn đạt bằng lời.`
- Luật 2, khi không có ảnh: `Chữ "[formula: …]" là chỗ công thức bị mất khi trích PDF; phần sau dấu hai chấm là chữ trích thô của công thức, có thể lộn thứ tự và mất ký hiệu. Dựng lại công thức từ chữ trích thô, chỉ khi chắc chắn; không chắc thì diễn đạt bằng lời.`
- Công thức không có chữ trích thô thì vẫn là `[formula]` như cũ.
- **Thêm một dòng định dạng câu tự kiểm tra,** để máy tách được: cuối bài có mục `### Tự kiểm tra`, gồm một dòng `**Câu hỏi:** …` và một dòng
  `**Đáp án:** …`.
- **Tin nhắn người dùng theo khuôn của bản thử:** dòng "Khái niệm: … (còn gọi: …)", module, "Khái niệm tiên quyết:", "Khái niệm tiếp theo dùng tới khái niệm
  này:", "Tư liệu từ sách:", mỗi đoạn mở đầu bằng `[Sk] (trang p, mục …)`.

### 5. Gọi mô hình

- Mô hình `gemini-3.1-flash-lite`, qua transport hiện hành.
- Cấu hình: `lecture_temperature` 1,0; `lecture_max_output_tokens` 4.096; đầu ra là chữ, không lược đồ JSON; stream.
- **Mỗi mẩu chữ là một sự kiện `delta`.** Bài không còn hỏng được từ mẩu đầu tiên. Lỗi sau đó thì giữ phần đã có, trả `ready` kèm `cat_ngan`.
- **Sinh lại một lần,** chỉ khi đầu ra rỗng, hay không có chữ nào dùng được.
- Trần một lần bấm, thử lại tầng mạng và trần chi giữ như ADR 0024.

### 6. Hợp đồng `lecture-3`

```json
{"contract_version": "lecture-3", "status": "ready | generating | no_source | failed", "lecture_key": "sha256:…",
 "position": {}, "definition": {"quote": "…", "citation": {}, "formula_refs": []},
 "prerequisites": [{"recall": {}, "learner_status": "learned | not_learned | unknown"}],
 "body_md": "… Markdown, công thức LaTeX, nhãn [S1] …",
 "self_check": {"question_md": "…", "answer_md": "…"},
 "sources": [{"label": "S1", "chunk_id": "…", "page": 37, "section_path": ["…"]}],
 "next_up": [], "failure": null, "warnings": [], "usage": {}}
```

- **`body_md`** là bài, đã tách mục "Tự kiểm tra". Không tách được thì `self_check = null`, bài giữ nguyên, và log `khong_tach_tu_kiem`.
- **`sources`** là mọi đoạn tư liệu đã gửi, theo nhãn. Đây là khối "Trong sách"; nhãn `[Sx]` trong bài trỏ vào đây. Nhãn không có trong `sources` vẫn để
  nguyên chữ và ghi log.
- **`failure`** theo ADR 0024: `reason_code`, `message`, `retryable = true`, `read_page`, `ask_assistant`.
- **Không có `validation`** trong đối tượng này.
- **Stream:** `skeleton`; các `delta {text}`; rồi `final {lecture}` hoặc `failure`.
- **`no_source`** chỉ khi không tìm được đoạn nào theo mục 2.

### 7. Log cho admin (`validation`, không gửi người học)

Lưu cùng bài trong cache và trong dòng usage `lecture_validation`:
- số từ;
- có câu tự kiểm tra không;
- nhãn dùng, kèm điểm trùng của từng nhãn: tỉ lệ cặp âm tiết của đoạn văn có trong đoạn được dẫn;
- nhãn lạ;
- còn `[formula]` trong bài không;
- n-gram 8 âm tiết lặp từ 3 lần trở lên;
- `finish_reason`; có thiếu ảnh trang không;
- số ảnh đã gửi.

**Không mục nào chặn hay sửa bài.**

### 8. Cache

- Khoá gồm: `doc_id`, `node_id`, băm của tư liệu (chữ và mã ảnh), phiên bản lời nhắc `lecture-prompt-3`, phiên bản gom tư liệu, mô hình, nhiệt độ, trần token.
- Bài `ready` vào cache chung và được phục vụ lại, 0 lời gọi. Bản ghi lỗi theo ADR 0024.

### 9. Trang xem thử và người dùng khác

- **Trang xem thử:** hiện `delta` ngay; hiện Markdown có công thức (KaTeX), nhãn `[Sx]` thành link tới trang trong `sources`, khối "Trong sách", và câu tự kiểm
  tra có đáp án gập sẵn.
- **Công cụ `get_lecture`** của trợ lý trả `body_md` và `sources`, không có `validation`.
- **Web** do người điều phối làm theo hợp đồng mục 6.

### 10. `BSettings` mới

| khoá | mặc định |
|---|---|
| `lecture_contract_version` | `lecture-3` |
| `lecture_prompt_version` | `lecture-prompt-4` (từ `-3`, SA-70) |
| `lecture_context_version` | `lecture-context-4` (từ `-3`, SA-70) |
| `lecture_context_chars` | 9.000 |
| `lecture_max_page_images` | 8 (từ 4, SA-70) |
| `lecture_thinking_level` | không (tắt), SA-70 |
| `lecture_temperature` | 1,0 (từ 0) |
| `lecture_max_output_tokens` | 4.096 (từ 2.048) |

### 11. Bản 2 (SA-70, 2026-10-24)

Lượt thật `lecture-3` 30 bài (2026-10-23, 0,065 USD) đạt 30/30. Sonnet rà lượt đầu, Claude đối chiếu sách. Phần bám sách đúng, công thức khớp ảnh trang. Lỗi nằm ở
phần mô hình tự viết thêm: ví dụ tự nghĩ không nhất quán; câu kết mô tả sai khái niệm tiếp theo; gán sai vai trò; đảo chiều mệnh đề ("r = 0 thì độc lập").
Sáu thay đổi:

1. **Lời nhắc V5** (mục 4, ba chỗ sửa): soát ví dụ tự nghĩ; câu kết không tự định nghĩa khái niệm tiếp theo; giữ chiều và vai trò của phát biểu.
   - Chạy lại đúng 30 khái niệm: năm lỗi đã xác nhận đều hết.
   - So sánh mù V4/V5/V5 có suy nghĩ (Sonnet chấm, 30 khái niệm): không cặp nào khác biệt có ý nghĩa (V5 hơn V4 14/30, p = 0,86; có suy nghĩ hơn V4 19/30,
     p = 0,20; 14/30 "gần ngang").
   - Giữ V5 vì nó nhắm đúng loại lỗi đã thấy và không có dấu hiệu gây hại. Kết quả ở scratchpad `lecture3-so-sanh/`.
2. **Chữ trích thô của công thức** (`lecture-context-4`). Mỗi `[formula]` trong đoạn tư liệu gửi cho mô hình được thay bằng `[formula: <raw_text>]`.
   - `raw_text` là chữ lớp văn bản PDF của nút công thức, lấy qua `formula_refs` của đoạn theo đúng thứ tự, khoảng trắng gộp lại. Pha A đã gửi chữ này cho
     mô hình trích khái niệm từ trước.
   - Ba cuốn có công thức: số `[formula]` khớp số `formula_refs` ở mọi đoạn (doc-1 234, xstk 84, naive-bayes 17 đoạn).
   - Chỉ đổi chữ gửi mô hình. `sources`, `chunk_id`, cách chọn trang ảnh giữ nguyên, theo chữ gốc của đoạn.
3. **Trần ảnh trang 4 → 8.** Với trần 4: 6/19 bài của ba cuốn có công thức nằm trên hơn 4 trang; 63/302 chỗ `[formula]` (21%) không có ảnh mà cũng không có
   chữ. Thử 9 bài khó nhất:
   - thêm chữ thô và trần 8 thì ví dụ "kích thước mẫu" ra đúng N = 42 của sách; trần 8 không chữ thô ra 105 (sai);
   - không bản nào chép chữ thô lộn xộn vào bài;
   - chữ đầu không chậm hơn; chi thêm khoảng 0,0005 USD mỗi bài.
4. **Sửa log ảnh.** `pages_with_formula` đếm mọi trang có công thức của tư liệu **trước khi cắt** theo trần. `thieu_anh_trang` = số ảnh đã gửi < số trang đó.
   Trước đây số trang bị cắt còn 4 trước khi đếm, nên cờ không bao giờ bật khi vượt trần. `formula_left` bắt cả `[formula` (có hay không có chữ thô).
5. **Stream không lộ câu tự kiểm tra.**
   - Khi một dòng khớp tiêu đề tự kiểm tra (cùng biểu thức mà `split_self_check` dùng: `##`–`####`, thụt đầu, dấu hai chấm, không phân biệt hoa thường),
     ngừng phát `delta` từ dòng đó. Phần còn lại chỉ có trong `final`.
   - Dòng đang viết dở mà bắt đầu bằng `#` (sau khoảng trắng) thì giữ lại tới khi đủ dòng, rồi mới quyết phát hay ngừng. Các dòng khác phát ngay như cũ.
   - Lý do: biên bản nghiệm thu web lần 3 (R-W08-2), bốn dạng tiêu đề hợp lệ làm đáp án hiện trước `final`. Chặn ở lõi để mọi người dùng cùng một luật.
6. **Tham số `lecture_thinking_level`**, mặc định tắt. Đặt mức (`low`, …) thì gửi `thinkingConfig` cho lời gọi bài giảng và mức này vào khoá cache. Lý do:
   bản có suy nghĩ xếp nhất 13/30 trong so sánh mù nhưng chưa có ý nghĩa thống kê, chậm hơn 0,8 giây ở trung vị, đắt hơn 40%. Để đợt đánh giá tổng đo lại.

## Quyết định kiểm thử

- **Đường nối chính** ở mức use case. Mô hình giả stream theo kịch bản, cổng `PageImages` giả, kho trong bộ nhớ, đồng hồ giả. Không gọi mạng.
- **Mẫu test:** các test bài giảng hiện có, như `tests/unit/application/test_phase_b_*lecture*.py`.
- **Bất biến phải có test,** mỗi cái thấy đỏ trước trên bản sai:
  1. Gom tư liệu lấy được đoạn có tên khái niệm ở tiêu đề mục, nằm xa đoạn định nghĩa. Dừng ở 9.000 ký tự. Giữ thứ tự đọc. Không lấy đoạn `de_cuong`,
     `hanh_chinh`.
  2. Có `[formula]` trong tư liệu thì gửi ảnh của đúng các trang đó, tối đa 4. Không có `[formula]` thì không gửi ảnh. Cổng ảnh trả rỗng thì vẫn ra bài, và
     log `thieu_anh_trang`.
  3. Lời nhắc hệ thống đúng nguyên văn mục 4, với luật công thức đổi theo việc có ảnh hay không.
  4. Mẩu chữ đầu tiên đến người gọi trước khi mô hình trả xong. Lỗi giữa chừng thì `ready` kèm `cat_ngan`, giữ chữ đã gửi.
  5. Bài có nhãn lạ, còn `[formula]`, hay lặp n-gram vẫn `ready`, đủ chữ. Những điều này chỉ có trong `validation`.
  6. Tách đúng câu tự kiểm tra. Khuôn sai thì `self_check = null` và bài giữ nguyên.
  7. `validation` không có ở kết quả nút bấm, sự kiện `final` hay `get_lecture`.
  8. Đầu ra rỗng thì sinh lại đúng một lần, rồi `failed` kèm `khong_dung_duoc`, `message`, `retryable = true`.
  9. Bấm lần hai thì 0 lời gọi. Đổi phiên bản lời nhắc thì sinh lại.
  10. Không đường nào trả câu TextRank cho người học.
  11. *(SA-70)* Tin nhắn gửi mô hình có `[formula: <raw_text>]` đúng thứ tự cho từng `[formula]` có chữ thô; đoạn không có `formula_refs` giữ `[formula]`;
      `sources` không đổi.
  12. *(SA-70)* Tư liệu có công thức trên 10 trang: gửi đúng 8 ảnh đầu theo thứ tự đọc; `validation.pages_with_formula` = 10 và `thieu_anh_trang` bật.
  13. *(SA-70)* Mô hình giả stream bài có câu tự kiểm tra dưới từng dạng tiêu đề (`### Tự kiểm tra`, `## Tự kiểm tra`, `#### Tự kiểm tra`,
      `### Tự kiểm tra:`, `  ### Tự kiểm tra`), kể cả khi tiêu đề bị cắt qua hai mẩu chữ: nối các `delta` lại không có "Câu hỏi:" hay "Đáp án:", và bằng
      `body_md` của `final` (bỏ khoảng trắng cuối). Tiêu đề khác (`### Ví dụ`) vẫn được phát.
  14. *(SA-70)* Lời nhắc đúng nguyên văn mục 4 (V5); luật công thức theo mục 4.
  15. *(SA-70)* `lecture_thinking_level` tắt thì thân yêu cầu không có `thinkingConfig`; đặt `low` thì có và khoá cache đổi.

## Ngoài phạm vi

- Đổi ảnh công thức sang LaTeX lúc dựng.
- Thử mô hình mạnh hơn.
- Dọn mã `lecture-2`.
- Đánh giá bằng người chấm. Trước khi cho người dùng, Claude đọc một mẫu bài thật (mục "Nghiệm thu" của SA-64).
- Trợ lý: rà riêng sau bài giảng.
