# Nghiên cứu quiz tự kiểm tra do LLM sinh cho từng module — 2026-10-11

Báo cáo trả lời tám câu hỏi về quiz tự kiểm tra cho từng module của lộ trình (Pha B). **Quiz là phần thêm ngoài đề cương**: đề cương đồ
án chỉ ghi trợ lý hỏi đáp và bài giảng ([đề cương](../doanchuyennganh/decuong/de-cuong-do-an-chuyen-nganh.md), mục tiêu 4 và phạm vi),
còn quiz chỉ có trong đặc tả cũ ([`spec-addendum.md`](../doc/spec-addendum.md), A11 dòng 701–711, B3 dòng 1078–1082). Báo cáo theo quyết
định của chủ dự án ngày 2026-10-11: quiz để tự kiểm tra, không khoá module, không mô hình hoá trình độ; `gemini-3.1-flash-lite` sinh câu;
mỗi câu gắn một khái niệm; điền khuyết không LLM (V11 trong [`pipeline-seminar-chuan-V1-V13-v2.md`](../doc/pipeline-seminar-chuan-V1-V13-v2.md))
làm mốc. Vì vậy báo cáo **bỏ** phần "mastery", ngưỡng 70%/40% và mở khoá module của B3.

Phạm vi và cách làm:
- Nguồn đọc ngày 2026-10-11. PDF tải về thư mục tạm, đọc bằng `pdftotext`; mọi số trích từ văn liệu đã đối chiếu với chữ PDF. Sáu nguồn đọc
  toàn văn hoặc đọc kỹ các phần liên quan; còn lại chỉ đọc tóm tắt hay kiểm siêu dữ liệu (Crossref, PubMed, ACL Anthology), ghi ở mục 7.
  Haladyna, Downing, Rodriguez 2002 không có bản mở: tôi chỉ kiểm siêu dữ liệu và đọc danh sách hướng dẫn qua bản dùng lại (bảng 19 lỗi
  viết câu của Moore và cộng sự, và bản 1989 của Haladyna & Downing).
- Số đo dự án do tôi tự đo bằng script chỉ đọc artifact của sáu cuốn; không gọi mô hình, không gửi nội dung giáo trình đi đâu. Truy vấn tìm
  kiếm chỉ dùng tên bài và từ khoá chung.
- Không viết mã sản phẩm, spec hay vé. Không chạy lượt tốn tiền; mọi USD và giây chờ là **ước**, công thức ghi rõ.
- Để ăn khớp, báo cáo dùng lại quy ước của [báo cáo bài giảng](nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md): nhãn nguồn ngắn (S1,
  N1…), `quote` kiểm nguyên văn, khoá cache theo `context_hash`, cách xử lý công thức (ảnh gốc + nhãn `[CTk]`). Mô tả module lấy từ
  [báo cáo tên và mô tả module](nghien-cuu-ten-va-mo-ta-module-2026-10-11.md) khi có. Văn liệu chung về trung thực và LLM giám khảo chỉ
  nhắc phần áp cho quiz.
- Đoạn mở đầu bằng *Suy luận:* là ý kiến của người viết, chưa có thí nghiệm.

---

## Tóm tắt

Chín ý chính:
1. **Nạp đủ mọi nguồn vẫn rẻ.** Tên, mô tả, câu neo, chunk dạy, tiên quyết, ứng viên câu nhiễu, bài tập và chú thích hình của một module chỉ
   chiếm trung vị 1.600–3.100 token, lớn nhất 4.458 (số đo, mục 1.2). Cộng lời dặn thì dưới khoảng 6.000 token, tức khoảng 0,0015 USD đầu
   vào. Tiền nằm ở token ra (khoảng 78%). Không cần cắt ngữ cảnh; cần cắt độ dài lời giải thích.
2. **Câu nhiễu: đồ thị cho đủ số lượng nhưng thiếu độ gần.** Mọi khái niệm có ≥ 3 ứng viên trong module hoặc cụm đã học, nhưng chỉ 26–56% có
   ứng viên từ cạnh mở (`contrasts_with`, cùng cha `subtype_of`, cùng tổng thể `component_of`), và cạnh mở chưa được kiểm. Khuyến nghị: mã
   đưa danh sách ứng viên, LLM chọn hoặc viết câu nhiễu, rồi một lời gọi kiểm độc lập xác nhận câu nhiễu sai theo tài liệu. Văn liệu ủng hộ
   LLM viết câu nhiễu: giáo viên chấm 57,6% câu nhiễu ChatGPT zero-shot là dùng được ngay, so với 28,9% của mô hình xếp hạng dùng lại câu nhiễu
   có sẵn ([Bitew 2023](https://arxiv.org/abs/2307.16338)).
3. **Dạng câu:** trắc nghiệm một đáp án đúng, **3 phương án** (1 đúng, 2 nhiễu; [Rodriguez 2005](https://doi.org/10.1111/j.1745-3992.2005.00006.x)),
   mỗi lần làm 1 câu cho mỗi khái niệm (5–8 câu, như A11), ngân hàng 2 câu mỗi khái niệm ở hai mức Bloom (nhớ/hiểu và hiểu/vận dụng).
   Không làm tự luận chấm bằng LLM ở bản đầu: chi phí theo lượt làm, thiên lệch giám khảo; thay bằng câu tự giải thích có đáp án mẫu để người
   học tự so.
4. **LLM sinh câu đạt gần mức người, nhưng có hai lỗi nặng lặp lại.** GPT-4 sinh câu lập trình: 81,7% qua mọi tiêu chí, nhưng 4,9% có nhiều
   đáp án đúng (người viết 1,1%) và 4,0% có câu nhiễu lộ đáp án ([Doughty 2024](https://arxiv.org/abs/2312.03173)). Với sách giáo khoa, LLM
   không khác người ở 6/7 thước đo nhưng Bing Chat bỏ sót đáp án khỏi các phương án ở 9% câu ([Olney 2023](https://ceur-ws.org/Vol-3487/paper7.pdf)).
5. **Kiểm tự động bằng luật trước, LLM sau.** Luật mã bắt 91% lỗi viết câu mà người tìm thấy, GPT-4 chỉ 79% và gắn quá tay (trung bình 4,2
   lỗi/câu so với 1,6 của người); cả hai gần như không bắt được "nhiều hơn một đáp án đúng" ([Moore 2023](https://arxiv.org/abs/2307.08161)).
   Thiết kế: chín luật mã 0 USD (mục 3.4) cộng một lời gọi "giải mù" độc lập mỗi module, khoảng 0,002–0,003 USD. Lỗi "nhiều đáp án đúng" vẫn
   phải đo bằng người.
6. **Công thức là chỗ yếu của sách toán.** 81% khái niệm doc-1 và 50% khái niệm xstk có `[formula]` trong chunk dạy; câu neo chứa công thức
   ở 40% và 25%. `raw_text` gốc có cho mọi công thức nhưng chỉ khoảng 6–20% đọc được rõ. Khuyến nghị: không ra câu mà đáp án nằm trong công
   thức; web hiện ảnh gốc công thức theo `page` + `bbox`; đo tỉ lệ khái niệm có câu sống sót ở doc-1 làm cổng mở nhánh đưa ảnh cho mô hình.
7. **Vận hành:** sinh khi người học mở module lần đầu (tải trước, không đợi bấm quiz), cache chung theo khoá có `context_hash`, xáo câu và
   phương án ở mỗi lần làm. Ước 0,015 USD mỗi module; sinh hết cả cuốn 0,03–1,22 USD (doc-4 cao nhất), bằng 0,05–1,90 USD với
   `gemini-3.5-flash-lite`. Giây chờ ước 20–70 giây cho một module nếu sinh lúc bấm, nên phải tải trước; số tốc độ của Flash-Lite phải đo.
8. **Phản hồi bắt buộc.** Trắc nghiệm có thể gieo kiến thức sai từ câu nhiễu; phản hồi (ngay hay chậm) làm tăng câu đúng và giảm lặp câu
   nhiễu ở bài kiểm tra sau ([Butler & Roediger 2008](https://doi.org/10.3758/MC.36.3.604)). Phản hồi nên ở mức nhiệm vụ và quá trình, không
   khen người ([Hattie & Timperley 2007](https://doi.org/10.3102/003465430298487)): đáp án đúng, câu trích, vì sao phương án đã chọn sai, link
   bài giảng của khái niệm làm sai.
9. **Đánh giá:** chấm người bằng rubric 19 lỗi viết câu cộng bốn tiêu chí đúng theo nguồn; hai người chấm độc lập, làm câu trước khi chấm;
   báo κ của Cohen [27] kèm phần trăm đồng ý và Gwet AC1, vì κ có thể chỉ 0,07–0,35 khi AC1 là 0,62–0,96 (Doughty 2024). Lượt có tiền dự toán
   dưới 2 USD. Luật quyết định viết trước ở mục 5.6.

---

## 1. Hiện trạng dữ liệu cho quiz (số đo 0 USD)

Mọi số trong mục này do tôi đo ngày 2026-10-11 bằng script chỉ đọc artifact của sáu cuốn (graph, chunk, cây phân tích theo bảng ở bối cảnh
chung của phiên); script không gọi mô hình. Script nằm trong thư mục tạm của phiên, không đưa vào repo.

### 1.1 Cỡ module

Bảng dưới cho số khái niệm mỗi module và số chunk dạy (gộp trùng) mỗi module:

| tài liệu | khái niệm | module | khái niệm/module, trung vị (min–max) | chunk dạy/module, trung vị |
|---|---:|---:|---|---:|
| doc-1 | 199 | 32 | 6 (4–8) | 3 |
| nhap-mon-ml | 54 | 9 | 6 (4–7) | 3 |
| naive-bayes | 20 | 3 | 7 (6–7) | 4 |
| doc-6 | 12 | 2 | 6 (6–6) | 4 |
| xstk-ch3-1 | 72 | 9 | 8 (8–8) | 4 |
| doc-4 | 489 | 87 | 6 (3–8) | 3 |

### 1.2 Cỡ ngữ cảnh nạp cho một module

Gemini không có tokenizer chạy offline, nên tôi quy ký tự ra token theo hai cách:
- **Tokenizer Gemma** mà bộ cắt chunk đã dùng (`google-gemma-sentencepiece-v1`, trường `token_count` của chunk). Tỉ lệ ký tự/token trên chunk
  `noi_dung`: doc-1 2,63; nhap-mon-ml 3,64; naive-bayes 2,64; doc-6 3,33; xstk 2,89; doc-4 3,73. Sách toán tốn token hơn vì ký hiệu.
- **Đối chiếu bằng usage thật của Gemini:** hồi quy `promptTokenCount` theo độ dài input JSON trên 1.033 lời gọi `anchor_decision_log` của sáu
  cuốn cho 0,311 token/ký tự (3,22 ký tự/token), cộng khoảng 770 token cố định của lời dặn. Đầu ra (`raw_text` so với `candidatesTokenCount`)
  có trung vị 3,09 ký tự/token.

Các bảng dưới dùng tỉ lệ Gemma của từng cuốn. Bốn mức nạp được định nghĩa như sau:
- **A:** tên, mô tả A5 (bỏ mã trích dẫn) và câu neo của mọi khái niệm trong module.
- **B:** A cộng chữ các chunk dạy của module.
- **C:** B cộng tên và mô tả của tiên quyết hiển thị nằm ngoài module (tối đa 3 mỗi khái niệm), và tên, mô tả của tối đa 4 ứng viên câu nhiễu mỗi
  khái niệm, nằm ngoài module (ưu tiên cạnh mở, rồi cùng cụm ở module đã học).
- **D:** C cộng tối đa 2 chunk bài tập cùng chương và chú thích của hình, bảng `confirmed`.

Chưa tính lời dặn cùng schema JSON (ước 1.500 token) và mô tả module (theo báo cáo tên và mô tả module; ước dưới 150 token).

| tài liệu | A | B | C | D trung vị | D p90 | D lớn nhất | D cộng cả cuốn |
|---|---:|---:|---:|---:|---:|---:|---:|
| doc-1 | 703 | 1.476 | 2.100 | 2.493 | 3.085 | 3.623 | 76.550 |
| nhap-mon-ml | 467 | 1.369 | 1.747 | 1.800 | 2.345 | 2.345 | 16.601 |
| naive-bayes | 1.392 | 2.052 | 2.538 | 2.859 | 3.190 | 3.190 | 8.235 |
| doc-6 | 905 | 1.313 | 1.447 | 1.595 | 2.135 | 2.135 | 3.190 |
| xstk-ch3-1 | 1.060 | 2.050 | 2.812 | 3.132 | 4.458 | 4.458 | 29.007 |
| doc-4 | 535 | 1.518 | 2.363 | 2.363 | 3.697 | 4.315 | 214.501 |

*Suy luận:* nạp đủ mọi nguồn (mức D) vẫn dưới 4.500 token mỗi module, tức khoảng 6.000 token khi cộng lời dặn. Đầu vào vì vậy chỉ tốn khoảng
0,0015 USD mỗi module. Không cần cắt ngữ cảnh để tiết kiệm; tiền nằm ở token ra (mục 3.8).

### 1.3 Ứng viên câu nhiễu

Bảng dưới đếm khái niệm có ứng viên câu nhiễu theo từng nguồn. "Cạnh mở" gồm `contrasts_with`, các khái niệm cùng cha qua `subtype_of` và cùng
tổng thể qua `component_of`. "Đã học" nghĩa là ứng viên nằm ở module cùng hoặc trước module của khái niệm.

| tài liệu | ≥ 1 ứng viên từ cạnh mở | riêng `contrasts_with` | ≥ 3 từ cạnh mở | ≥ 3 trong cùng module | ≥ 3 khi gộp cạnh mở, cùng module, cùng cụm (đã học) | ≥ 3 cùng `node_type` (đã học) |
|---|---|---|---|---|---|---|
| doc-1 | 53/199 (27%) | 14 (7%) | 16 (8%) | 199 (100%) | 199 (100%) | 134 (67%) |
| nhap-mon-ml | 14/54 (26%) | 5 (9%) | 0 | 54 (100%) | 54 (100%) | 42 (78%) |
| naive-bayes | 7/20 (35%) | 4 (20%) | 0 | 20 (100%) | 20 (100%) | 10 (50%) |
| doc-6 | 0/12 | 0 | 0 | 12 (100%) | 12 (100%) | 11 (92%) |
| xstk-ch3-1 | 22/72 (31%) | 6 (8%) | 4 (6%) | 72 (100%) | 72 (100%) | 57 (79%) |
| doc-4 | 276/489 (56%) | 101 (21%) | 121 (25%) | 450 (92%) | 476 (97%) | 437 (89%) |

Ba điều rút ra từ bảng:
- **Số lượng đủ, độ gần thì không.** Cùng module luôn cho đủ 3 ứng viên, nhưng chỉ 26–56% khái niệm có ứng viên "gần nghĩa" từ cạnh mở, và chỉ
  7–21% có cạnh `contrasts_with`.
- **Cạnh mở là đề xuất chưa kiểm** (bối cảnh chung của phiên, mục 4). Một cạnh `subtype_of` sai sẽ sinh câu nhiễu thực ra cũng
  đúng. Vì vậy mọi câu nhiễu phải qua phép kiểm "sai theo tài liệu" ở mục 3.4, kể cả ở bản không LLM.
- **Cùng kiểu nút** (đều là `algorithm`, đều là `theorem`…) giúp các phương án đồng nhất, nhưng naive-bayes chỉ có 50% khái niệm đủ ba ứng viên
  cùng kiểu.

### 1.4 Câu neo và mốc điền khuyết

Mốc không LLM đục lỗ tên khái niệm trong câu neo. Bảng dưới đếm số khái niệm làm được việc đó. Một khái niệm "đủ điều kiện" khi câu neo chứa
nguyên văn tên (hoặc `display_name`, bí danh), không chứa `[formula]`, dài ít nhất 40 ký tự và không phải dòng tiêu đề.

| tài liệu | tên có trong câu neo | câu neo chứa `[formula]` | đủ điều kiện đục lỗ | câu neo trung vị (ký tự) | mô tả A5 chứa tên khái niệm |
|---|---|---|---|---:|---|
| doc-1 | 163/199 (82%) | 80 (40%) | 91 (46%) | 145 | 81 (41%) |
| nhap-mon-ml | 50/54 (93%) | 0 | 49 (91%) | 126 | 17 (31%) |
| naive-bayes | 16/20 (80%) | 8 (40%) | 12 (60%) | 197 | 15 (75%) |
| doc-6 | 12/12 (100%) | 0 | 12 (100%) | 348 | 4 (33%) |
| xstk-ch3-1 | 63/72 (88%) | 18 (25%) | 44 (61%) | 160 | 26 (36%) |
| doc-4 | 430/489 (88%) | 0 | 426 (87%) | 150 | 162 (33%) |

Tôi cũng mô phỏng cách chọn câu nhiễu của mốc: lấy 3 tên khái niệm theo thứ tự ưu tiên cạnh mở, cùng module, cùng cụm, 20 lần mỗi khái niệm.
Đáp án đúng là phương án dài nhất duy nhất trong 18–25% số lần, không cao hơn mức may rủi 25%. Dùng tên khái niệm làm phương án vì vậy không
lộ đáp án qua độ dài. Riêng cột cuối cho thấy 31–75% mô tả A5 chứa chính tên khái niệm: câu hỏi kiểu "mô tả sau ứng với khái niệm nào" phải
che tên trước.

### 1.5 Công thức bị thay bằng `[formula]`

Cây phân tích (`artifacts/parse_tree/<doc>/v<N>/tree.json`) vẫn giữ mỗi công thức đứng riêng thành một nút `formula` có `raw_text`, `page` và
`bbox`. Mọi chỗ `[formula]` trong chunk đều trỏ được về nút đó qua `formula_refs`. Bảng dưới đo ảnh hưởng và chất lượng `raw_text`:

| tài liệu | chỗ `[formula]` | khái niệm có chunk dạy chứa `[formula]` | câu neo chứa `[formula]` | module bị ảnh hưởng | `raw_text` khôi phục được | phân loại thô `raw_text` |
|---|---:|---|---|---|---|---|
| doc-1 | 562 | 161/199 (81%) | 80 (40%) | 30/32 | 562/562, trung vị 62 ký tự | dàn phẳng 376 (67%), ngoặc ma trận vỡ 142 (25%), có toán tử và không lỗi rõ 34 (6%), không toán tử 10 |
| xstk-ch3-1 | 263 | 36/72 (50%) | 18 (25%) | 7/9 | 263/263, trung vị 31 ký tự | dàn phẳng 151 (57%), có toán tử và không lỗi rõ 52 (20%), không toán tử 49 (19%), ngoặc vỡ 11 (4%) |
| naive-bayes | 32 | 17/20 (85%) | 8 (40%) | 3/3 | 32/32, trung vị 28 ký tự | có toán tử 20, rác ký tự CJK 10, ngoặc vỡ 1, không toán tử 1 |

Các nhãn phân loại là luật thô do tôi đặt, chưa có người đọc kiểm:
- "Ngoặc ma trận vỡ" là `raw_text` chứa ký tự vùng dùng riêng U+E000–U+F8FF.
- "Dàn phẳng" là ít nhất 60% từ có một ký tự: chỉ số trên, dưới bị trải ra.
- "Không toán tử" gồm cả chữ "Giải" và chuỗi phím máy tính bị nhận nhầm là công thức.

Đọc mẫu 14 công thức mỗi cuốn, tôi thấy hai trường hợp. Có công thức đọc được, như `c 1 α 1 + · · · + c n α n = θ.` hay
`H : p = 0,02 ; H : p ≠ 0,02`, dù chỉ số H₀, H₁ đã mất. Có công thức vô nghĩa, như `1 2 2 2 1 2 1 2 x x t s s n n − = +` (thống kê t hai mẫu
bị xáo). Ở doc-1, chunk dạy có công thức còn trung vị 673 ký tự chữ sau khi bỏ chỗ trống, và 92/199 khái niệm có từ 3 chỗ `[formula]` trở lên.

### 1.6 Bài tập có sẵn và hình

Bảng dưới đếm chunk bài tập và số module có bài tập cùng chương (khớp theo "Chương N" trong `section_path`; xstk chỉ có một chương nên mọi module
dùng chung):

| tài liệu | chunk `bai_tap` | module có bài tập cùng chương | bài tập chứa `[formula]` | độ dài trung vị (ký tự) | module có hình/bảng `confirmed` |
|---|---:|---|---|---:|---|
| doc-1 | 37 | 26/32 | 32/37 | 490 | 12/32 |
| nhap-mon-ml | 0 | 0/9 | — | — | 2/9 |
| naive-bayes | 2 | 3/3 | 0/2 | 288 | 3/3 |
| doc-6 | 0 | 0/2 | — | — | 2/2 |
| xstk-ch3-1 | 21, cộng 48 chunk "Cách giải" bị gán nhầm `de_cuong` | 9/9 | 3/21 | 779 | 3/9 |
| doc-4 | 2 (câu hỏi ôn cuối chương) | 14/87 | 0/2 | 448 | 0/87 |

Kiểu nút cũng gợi dạng câu: doc-1 có 127 `concept`, 23 `algorithm`, 18 `theorem`, 14 `metric`; xstk có 37 `concept`, 21 `method`, 14 `metric`;
doc-4 có 452 `concept`, 22 `method`.

### 1.7 Hệ quả cho thiết kế

*Suy luận:* năm hệ quả từ số đo:
- **Ngữ cảnh không phải ràng buộc.** Nạp cả module trong một lời gọi được; một lời gọi cho cả module rẻ hơn tách theo khái niệm và cho mô hình
  thấy mọi khái niệm anh em để chọn câu nhiễu.
- **Câu nhiễu cần một bước kiểm.** Ứng viên có đủ, nhưng nguồn "gần nghĩa" (cạnh mở) chưa kiểm và chỉ phủ 26–56% khái niệm.
- **Mốc điền khuyết phủ không đều.** 87–100% khái niệm ở doc-4, doc-6, nhap-mon-ml đục lỗ được, nhưng chỉ 46% ở doc-1 và 61% ở xstk.
- **Sách toán sẽ có ít câu sống sót hơn**, vì luật cấm dựa vào công thức. Đây là số phải đo đầu tiên ở lượt thử.
- **Bài tập chỉ hợp làm mẫu văn phong ở xstk và naive-bayes.** 32/37 bài tập của doc-1 chứa `[formula]`; doc-4 chỉ có câu hỏi ôn chương;
  hai cuốn không có bài tập. Không thể dựa vào bài tập để điều khiển độ khó.

---

## 2. Văn liệu

### 2.1 Hướng dẫn viết câu và lỗi viết câu

Ba nguồn chính:
- **Haladyna, Downing, Rodriguez 2002** kiểm chứng một bảng 31 hướng dẫn viết câu trắc nghiệm dựa trên 27 giáo trình đo lường và 27 nghiên
  cứu từ 1990, chủ yếu cho kiểm tra trên lớp ([AME 15(3)](https://doi.org/10.1207/s15324818ame1503_5); chỉ kiểm siêu dữ liệu và tóm tắt).
  Bản 1989 của Haladyna & Downing ([AME 2(1)](https://doi.org/10.1207/s15324818ame0201_3)), đọc qua bản in lại của
  [Penn State](https://www.schreyerinstitute.psu.edu/pdf/Multiple_Choice_Item_Writing_Rules.pdf), có các luật liên quan trực tiếp: "chỉ một
  đáp án đúng", "phương án đồng nhất về nội dung", "độ dài phương án tương đương", "tránh 'tất cả/không có đáp án nào ở trên'", "tránh câu
  dẫn phủ định", "dùng lỗi thường gặp của người học làm câu nhiễu", và **"tránh chép nguyên văn sách khi viết câu"**. Luật cuối là điểm yếu
  cố hữu của mốc điền khuyết.
- **Bảng 19 lỗi viết câu (IWF)** do Moore và cộng sự dùng, rút từ bảng 31 hướng dẫn trên, có định nghĩa từng lỗi và κ giữa hai người chấm
  0,66–1,00 ([Moore 2023](https://arxiv.org/abs/2307.08161), đọc toàn văn). Mười chín lỗi: mơ hồ, câu nhiễu khó tin, "không có đáp án nào",
  phương án dài nhất là đáp án, thông tin thừa, phương án là chuỗi đúng/sai, gợi ý hội tụ, gợi ý logic, "tất cả các đáp án", chỗ trống giữa
  câu, từ tuyệt đối, lặp từ giữa câu dẫn và đáp án, câu dẫn không tập trung, dạng K (tổ hợp), gợi ý ngữ pháp, sai thứ tự, từ mơ hồ ("thường",
  "đôi khi"), nhiều hơn một đáp án đúng, câu dẫn phủ định. Theo Tarrant và cộng sự 2006
  ([Nurse Educ. Today 26(8)](https://doi.org/10.1016/j.nedt.2006.07.006); chỉ kiểm siêu dữ liệu), câu có 0–1 lỗi là chấp nhận được, từ 2
  lỗi là không; Moore dẫn rằng gần nửa trong hơn hai nghìn câu thi điều dưỡng không đạt.
- **Số phương án.** Phân tích gộp 80 năm nghiên cứu của Rodriguez kết luận 3 phương án là tối ưu: làm được nhiều câu hơn trong cùng thời gian
  mà không hại chất lượng đo ([EM:IP 24(2)](https://doi.org/10.1111/j.1745-3992.2005.00006.x); chỉ đọc tóm tắt). Downing 2005 về hậu quả
  của câu viết lỗi lên điểm thi ([AHSE 10(2)](https://doi.org/10.1007/s10459-004-4019-5)) chỉ được kiểm siêu dữ liệu.

### 2.2 Sinh câu hỏi tự động: tổng quan và Bloom

Tổng quan của Kurdi và cộng sự ([IJAIED 30(1)](https://doi.org/10.1007/s40593-019-00186-y), đọc toàn văn các phần dùng ở đây) gom 93 bài từ
2015 đến đầu 2019. Năm điểm áp cho dự án:
- Câu điền khuyết và câu hỏi sự kiện là hai dạng được sinh nhiều nhất từ văn bản (15 và 17 bài).
- Cách chọn câu nhiễu chủ đạo là **độ giống với đáp án**; một số bài lấy **khái niệm anh em trong cơ sở tri thức**. Cách này gần với việc dùng
  cạnh `subtype_of` và cùng cụm của dự án.
- **Phản hồi bị bỏ quên:** chỉ một bài sinh phản hồi kèm câu hỏi; tổng quan trước đó ghi chỉ ba bài, và phản hồi chỉ động viên hay đưa tài
  liệu đọc thêm, không giải thích vì sao sai.
- **Đánh giá:** chuyên gia chấm là cách phổ biến nhất (21 bài), so với câu người viết đứng thứ hai (15 bài); 43 bài không báo độ đồng thuận
  giữa người chấm. Tác giả khuyên chuyên gia **tự làm câu trước khi chấm**, định nghĩa tiêu chí chính xác, chấm thử trước, và lấy mẫu phân
  tầng theo dạng câu, mức khó.
- Không so sánh được hiệu năng giữa các bài vì thang chấm khác nhau; chuyên gia chấm chỉ là bằng chứng ban đầu, độ khó và độ phân biệt phải
  có người học làm thử.

Bloom bản sửa đổi (Anderson & Krathwohl 2001) có sáu mức quá trình nhận thức: nhớ, hiểu, vận dụng, phân tích, đánh giá, sáng tạo, cộng một
chiều kiến thức ([Krathwohl 2002, Theory Into Practice 41(4)](https://doi.org/10.1207/s15430421tip4104_2); chỉ kiểm siêu dữ liệu; sách
gốc **chưa xác minh** trực tiếp). *Suy luận:* với câu trắc nghiệm từ một đoạn sách, ba mức đầu là thực tế; ba mức sau cần tình huống mới mà
tài liệu không chứa nên khó kiểm căn cứ.

### 2.3 Thực nghiệm LLM sinh câu trắc nghiệm có chuyên gia chấm

Bảng dưới gom ba bài đọc toàn văn; số đã đối chiếu với PDF:

| bài | thiết lập | người chấm | kết quả chính | lỗi đặc trưng của LLM |
|---|---|---|---|---|
| Olney 2023 ([CEUR 3487](https://ceur-ws.org/Vol-3487/paper7.pdf)) | 120 câu từ giáo trình giải phẫu–sinh lý OpenStax; LLM nhận câu nguồn và đáp án, sinh câu dẫn và phương án; so Macaw tinh chỉnh, Bing Chat zero-shot, câu của sách | 16 người làm nghề y (điều dưỡng, bác sĩ), 7 thang chấm; κ > 0,60 ở 39/42 thang | không khác câu của sách ở 6/7 thước đo; "chất lượng chung" 85,5 (Bing) và 86,9 (Macaw) so với 93,6 (sách), khác có ý nghĩa | Bing Chat không đưa đáp án đã cho vào phương án ở 9% câu; Macaw lặp phương án ở 7,5% |
| Doughty 2024 ([ACE 2024](https://doi.org/10.1145/3636243.3636256), [arXiv](https://arxiv.org/abs/2312.03173)) | GPT-4 sinh 651 câu 3 phương án cho 246 mục tiêu học tập của 6 môn Python; so 449 câu người viết | 7 sinh viên, 6 giảng viên, mỗi câu ≥ 1 sinh viên + 1 giảng viên, làm câu trước khi chấm | 81,7% câu sinh qua cả 6 tiêu chí; khớp mục tiêu học tập tốt hơn câu người viết | 4,9% nhiều đáp án đúng (người 1,1%); 4,0% câu nhiễu lộ đáp án (người 0,9%), phần lớn lộ ngay ở câu dẫn; câu sinh dễ hơn (sinh viên làm đúng 71,5% so với 62,6%) |
| Moore 2023 ([EC-TEL 2023](https://doi.org/10.1007/978-3-031-42682-7_16), [arXiv](https://arxiv.org/abs/2307.08161)) | kiểm 200 câu do sinh viên viết theo 19 lỗi viết câu; luật mã so với GPT-4 | 2 chuyên gia, κ 0,66–1,00 | luật mã khớp 90,9% nhãn người, GPT-4 78,9%; GPT-4 gắn trung bình 4,2 lỗi/câu, người 1,6 | cả hai gần như không bắt được "nhiều hơn một đáp án đúng" (F1 0,00 ở ba trên bốn môn); luật độ dài và từ khoá thì tốt |

Ba bài cho cùng một hình ảnh. LLM đạt gần mức người về văn và độ khớp mục tiêu. Lỗi nặng còn lại hiếm nhưng chí mạng: đáp án sai, nhiều đáp
án đúng, câu nhiễu lộ đáp án. Bộ kiểm bằng LLM lại có xu hướng gắn lỗi quá tay. Đầu vào "câu nguồn + đáp án" của Olney gần với thiết kế của
dự án (câu neo + khái niệm).

### 2.4 Câu nhiễu

Hai nguồn chính:
- **Bitew và cộng sự 2023** ([arXiv 2307.16338](https://arxiv.org/abs/2307.16338), đọc toàn văn) cho 10 giáo viên chấm 12.860 câu nhiễu
  của 300 câu hỏi theo bốn nhãn: trùng đáp án, tốt, kém, vô nghĩa. Với câu hỏi kiến thức sự kiện, tỉ lệ câu nhiễu tốt và vô nghĩa là: mô hình
  xếp hạng dùng lại câu nhiễu có sẵn (DQ-SIM) 28,9% và 50,1%; ChatGPT zero-shot 57,6% và 17,5%; ChatGPT có ví dụ truy hồi động 58,8% và
  16,4%. Đồng thuận giữa giáo viên chỉ ở mức vừa: κ 0,29 (tiếng Anh) và 0,52 (địa lý).
- **Gierl và cộng sự 2017** tổng quan việc viết, phân tích và dùng câu nhiễu, ghi rằng việc tạo câu nhiễu ít được nghiên cứu hơn nhiều so với
  phần còn lại của câu trắc nghiệm ([RER 87(6)](https://doi.org/10.3102/0034654317726529); chỉ đọc tóm tắt).

Mitkov và cộng sự dựng câu trắc nghiệm từ văn bản bằng trích thuật ngữ, biến đổi câu và khoảng cách ngữ nghĩa để chọn câu nhiễu, cho người
soạn sửa sau ([NLE 12(2)](https://doi.org/10.1017/S1351324906004177); chỉ đọc tóm tắt). Đó là tổ tiên trực tiếp của mốc V11.

*Suy luận:* bài toán của dự án là kiến thức sự kiện, khái niệm trong một tài liệu, đúng loại mà LLM làm tốt nhất trong Bitew. Ứng viên từ đồ
thị nên đưa vào như gợi ý, không như danh sách bắt buộc; điều khiển chất lượng nằm ở bước kiểm "sai theo tài liệu".

### 2.5 Điền khuyết

Ba nguồn, đều chỉ kiểm tóm tắt hoặc trang bài:
- Mitkov & Ha 2003 ([HLT-NAACL 2003 Workshop on Building Educational Applications](https://aclanthology.org/W03-0203/)): sinh câu trắc
  nghiệm có hỗ trợ máy tính từ giáo trình, chọn khái niệm quan trọng bằng trích thuật ngữ.
- Agarwal & Mannem 2011 ([BEA 2011](https://aclanthology.org/W11-1407/)): sinh câu điền khuyết từ sách giáo khoa; chỉ kiểm trang bài.
- Kurdi 2020 (mục 2.2): điền khuyết là một trong hai dạng phổ biến nhất vì cấu tạo rẻ, không lo sai ngữ pháp ở câu dẫn.

Bảng 19 lỗi coi **chỗ trống giữa câu** là lỗi. Bản 1989 của Haladyna & Downing cũng bảo tránh chép nguyên văn sách. *Suy luận:* mốc V11 nên
đổi chỗ trống thành dạng hỏi ("Câu trích sau định nghĩa khái niệm nào?") để không vướng lỗi chỗ trống. Nó vẫn chỉ đo mức nhớ, nên cột so sánh
quan trọng nhất giữa hai bản là phân bố mức Bloom.

### 2.6 Phản hồi và hiệu ứng kiểm tra

Năm nguồn:
- **Hattie & Timperley 2007** ([RER 77(1)](https://doi.org/10.3102/003465430298487), đọc toàn văn các phần dùng ở đây). 12 phân tích gộp
  (196 nghiên cứu, 6.972 hệ số ảnh hưởng) cho ảnh hưởng trung bình 0,79. Phân tích của Kluger & DeNisi (470 hệ số) cho 0,38, và 32% số hệ
  số là âm. Phản hồi tốt trả lời ba câu: đi đâu, đang tới đâu, tiếp theo là gì. Bốn mức phản hồi: nhiệm vụ, quá trình, tự điều chỉnh, bản
  thân; mức bản thân (khen) kém nhất. Phản hồi mức nhiệm vụ mạnh nhất khi chỉ ra **cách hiểu sai**; nếu người học thiếu kiến thức thì **dạy
  lại** có tác dụng hơn phản hồi. Về thời điểm: ở tình huống kiểm tra, phản hồi chậm một chút có lợi (0,36, theo Kulik & Kulik); Clariana và
  cộng sự thấy lợi của phản hồi chậm tăng theo độ khó của câu (−0,06 câu dễ, 0,35 câu vừa, 1,17 câu khó).
- **Roediger & Karpicke 2006**: sau 2 ngày và 1 tuần, nhóm làm bài kiểm tra nhớ tốt hơn hẳn nhóm đọc lại, dù nhóm đọc lại tự tin hơn
  ([Psych. Science 17(3)](https://doi.org/10.1111/j.1467-9280.2006.01693.x); chỉ đọc tóm tắt).
- **Dunlosky và cộng sự 2013** xếp luyện tập bằng kiểm tra và học giãn cách vào nhóm hữu dụng cao trong mười kỹ thuật
  ([PSPI 14(1)](https://doi.org/10.1177/1529100612453266); chỉ đọc tóm tắt).
- **Roediger & Marsh 2005** ([JEP:LMC 31(5)](https://doi.org/10.1037/0278-7393.31.5.1155); chỉ kiểm siêu dữ liệu, nội dung qua tóm tắt
  của Butler & Roediger): trắc nghiệm có thể làm người học **học luôn câu nhiễu** thành kiến thức sai.
- **Butler & Roediger 2008** ([Mem. Cogn. 36(3)](https://doi.org/10.3758/MC.36.3.604); chỉ đọc tóm tắt): phản hồi ngay hay chậm đều tăng tỉ
  lệ trả lời đúng và giảm việc lặp lại câu nhiễu ở bài kiểm tra sau. Lời khuyên của tác giả: luôn có phản hồi khi dùng trắc nghiệm.

### 2.7 LLM làm giám khảo

Zheng và cộng sự ghi nhận thiên lệch vị trí và thiên lệch dài dòng của LLM giám khảo; dữ liệu của họ chưa đủ để kết luận về thiên lệch tự
khen (ưu ái câu do chính mô hình sinh) ([NeurIPS 2023 D&B](https://arxiv.org/abs/2306.05685), đọc các mục về thiên lệch qua bản tải của
phiên tên module). Với quiz, hai hệ quả: bộ kiểm dùng cùng `gemini-3.1-flash-lite` với bộ sinh có thể dễ dãi với lỗi của chính nó; và theo
Moore 2023, LLM chấm theo bảng lỗi lại gắn lỗi quá tay. Vì vậy LLM chỉ là bộ lọc trước, kết luận cuối đo bằng người (mục 5).

---

## 3. Thiết kế khuyến nghị

Luồng tổng: mã lắp ngữ cảnh của module → **một lời gọi sinh** ngân hàng câu (JSON) → luật mã → **một lời gọi kiểm "giải mù"** → luật
mã lần hai → lưu cache → mỗi lần làm, mã chọn và xáo câu.

`[CHÈN HÌNH 1 – Sơ đồ luồng quiz: khối "Lắp ngữ cảnh module (mã)" → "Sinh ngân hàng (LLM, 1 lời gọi)" → "Luật mã Q1–Q8" → "Giải mù (LLM, 1
lời gọi)" → "Luật mã lần 2" → "Cache chung"; nhánh hỏng quay về "Sinh lại cho khái niệm thiếu (tối đa 1 lần)" rồi "Mốc điền khuyết". Bên
phải: "Lần làm của người học: chọn 1 câu/khái niệm, xáo phương án → nộp → phản hồi + link bài giảng". Bố cục ngang, hai làn: máy chủ và web.]`

### 3.1 Thông tin nạp vào

Bảng dưới ghi từng nguồn, có nạp hay không và nhãn. Nhãn theo quy ước của báo cáo bài giảng; mã giữ bảng nhãn → `chunk_id`, vị trí ký tự,
trang:

| khối | nội dung | nhãn | nạp? | lý do | token (đo hoặc ước) |
|---|---|---|---|---|---|
| 0. Chỉ dẫn | vai trò; 12 luật viết câu rút từ mục 2.1; danh sách lỗi cấm; luật trích dẫn; luật công thức; lược đồ | — | có | đặt chuẩn Haladyna vào prompt | 1.200–1.500 (ước) |
| 1. Thẻ module | tên và mô tả module (nếu có), danh sách khái niệm theo thứ tự học | — | có | để câu bám mục tiêu module | 50–200 (ước) |
| 2. Thẻ khái niệm | `concept_id` (nhãn K1…), `display_name`, alias, `node_type`, **mức Bloom mục tiêu do mã gán** | K1–K8 | có | mỗi câu phải gắn đúng một khái niệm | khoảng 30/khái niệm |
| 3. Câu neo | `anchor.sentence`, ghi rõ nằm trong chunk nào | trỏ S | có | nguồn đáp án mạnh nhất, kiểm nguyên văn được | 40–110/khái niệm (đo) |
| 4. Chunk dạy | chữ chunk, gộp trùng; `[formula]` thay theo mục 3.6 | S1–S8 | có | căn cứ duy nhất cho đáp án và câu trích | mức B trừ A: 400–1.000/module (đo) |
| 5. Mô tả A5 | mô tả đã kiểm trích dẫn | — | có, ghi "chỉ để hiểu, không trích" | gợi ý diễn đạt lại để tránh chép nguyên văn sách | trong mức A (đo) |
| 6. Tiên quyết | tối đa 3 mỗi khái niệm, ngoài module: tên + câu neo | N1… | có | cấm ra câu cho tiên quyết; cho phép dùng làm câu nhiễu "nhầm với khái niệm nền" | trong mức C (đo) |
| 7. Ứng viên câu nhiễu | do mã chọn, tối đa 4 mỗi khái niệm: cạnh mở → cùng module → cùng cụm ở module đã học, ưu tiên cùng `node_type`; mỗi ứng viên có tên + câu neo; cạnh mở kèm câu bằng chứng | D1… | có | Bitew: LLM viết nhiễu tốt hơn xếp hạng; ứng viên giữ nhiễu bám tài liệu | trong mức C (đo) |
| 8. Bài tập | tối đa 2 chunk `bai_tap` cùng chương, bỏ chunk có ≥ 3 `[formula]` | B1, B2 | có, khi có | làm mẫu văn phong và độ khó cho câu vận dụng; cấm chép | 0–700 (đo) |
| 9. Hình, bảng `confirmed` | chú thích | H1… | **không** ở bản đầu | mô hình chỉ thấy chú thích, không thấy hình; doc-4 không có hình nào | — |
| 10. Câu mẫu | một câu tốt bằng tiếng Việt viết tay, không thuộc tài liệu nào | — | có | few-shot cho văn phong và lược đồ | khoảng 300 (ước) |
| 11. Nhắc nhiệm vụ | 2–3 câu nhắc luật quan trọng nhất | — | có | đặt nhiệm vụ ở cuối | khoảng 80 (ước) |

Mức Bloom mục tiêu do mã gán theo kiểu nút và nguồn có sẵn, không để LLM tự chọn:

| kiểu nút | câu 1 | câu 2 |
|---|---|---|
| `concept`, `definition`, `property` | nhớ: nhận ra khái niệm từ định nghĩa đã diễn đạt lại | hiểu: phân biệt với khái niệm gần, hoặc nhận ví dụ đúng |
| `theorem` | nhớ: điều kiện hoặc kết luận | hiểu: khi nào áp dụng được |
| `algorithm`, `method`, `metric` | hiểu: dùng để làm gì, đầu vào và đầu ra | vận dụng: chỉ khi chunk dạy hoặc bài tập có ví dụ có lời giải, và đáp án nằm trong đó; nếu không thì hiểu |

Tổng token vào của lời gọi sinh: mức D (đo, trung vị 1.600–3.100) cộng khoảng 1.700 chỉ dẫn và câu mẫu, tức khoảng 3.300–4.800. *Suy luận:*
gần ngưỡng 4.096 token của cache ngầm nhưng phần chung giữa các module chỉ là chỉ dẫn, nên đừng trông vào cache.

### 3.2 Dạng và số câu

Bảng sau so các dạng câu:

| dạng | quyết định | lý do |
|---|---|---|
| Trắc nghiệm một đáp án đúng, 3 phương án | **dạng chính** | Rodriguez 2005: 3 phương án tối ưu; Doughty 2024 cũng dùng 3; ít phải đẻ nhiễu khi ứng viên gần nghĩa hiếm |
| Đúng/sai | không dùng | đoán trúng 50%; một phát biểu sai phải viết thêm, khó kiểm "sai theo tài liệu" |
| Điền khuyết | chỉ ở mốc không LLM, đổi thành dạng hỏi | chỗ trống giữa câu là lỗi viết câu; chỉ đo mức nhớ |
| Tự luận ngắn chấm bằng LLM | **không** ở bản đầu | xem dưới |
| Câu tự giải thích, người học tự so với đáp án mẫu | tuỳ chọn, 1 câu/module | 0 USD lúc làm; giữ lợi ích của câu hỏi mở mà không cần chấm |

Rủi ro của tự luận chấm bằng LLM:
- **Tiền theo lượt làm.** Câu trắc nghiệm sinh một lần rồi cache chung; tự luận phải gọi LLM mỗi lần một người nộp, chi phí tăng theo số người
  học.
- **Giây chờ thêm** mỗi lần nộp.
- **Thiên lệch giám khảo** (mục 2.7): dễ dãi hay gắt không đều, khó giải thích với người học.
- **Không đo được** nếu thiếu đáp án vàng do người chấm.

Số câu:
- **Mỗi lần làm: 1 câu cho mỗi khái niệm** của module, tức 3–8 câu (trung vị 6–8, đo). Module 3–4 khái niệm thêm câu thứ hai cho các khái niệm
  đầu để đủ 5 câu, khớp khoảng 5–8 câu của A11.
- **Ngân hàng: 2 câu mỗi khái niệm**, ở hai mức Bloom theo bảng trên. Lần làm thứ hai dùng biến thể còn lại; từ lần thứ ba xáo lại cả hai và
  đổi thứ tự phương án. Thứ tự phương án do mã xáo, nên luật "đáp án nằm đều các vị trí" luôn đạt.
- Khái niệm không còn câu nào sau khi kiểm: sinh lại một lần cho riêng nó; vẫn hỏng thì dùng câu điền khuyết nếu khái niệm đủ điều kiện (mục
  1.4), nếu không thì bỏ khái niệm khỏi quiz và ghi nhật ký.

### 3.3 Lược đồ JSON một câu hỏi

LLM trả lời bằng nhãn; mã đổi nhãn ra `chunk_id`. Lược đồ đầu ra của LLM cho cả ngân hàng một module:

```json
{
  "items": [
    {
      "concept": "K3",
      "bloom": "nho | hieu | van_dung",
      "stem": "…",
      "correct": {"text": "…", "sources": ["S2"], "quote": "…"},
      "distractors": [
        {"text": "…", "from": "D4 | N1 | moi", "why_wrong": "…", "sources": ["S5"], "quote": "…"},
        {"text": "…", "from": "…", "why_wrong": "…", "sources": ["…"], "quote": "…"}
      ],
      "explanation": "…",
      "formula_refs": ["CT2"]
    }
  ],
  "gaps": ["…"]
}
```

Ghi chú lược đồ:
- `quote` là đoạn nguyên văn ngắn trong nguồn đầu tiên của `sources`, như bài giảng. Với đáp án, nó là căn cứ cho phương án đúng; với câu
  nhiễu, nó là đoạn cho thấy phương án đó **sai** hoặc thuộc khái niệm khác.
- `from = moi` là câu nhiễu mô hình tự viết; khi đó `quote` bắt buộc.
- `explanation` ≤ 300 ký tự và `why_wrong` ≤ 150 ký tự (mã kiểm, vì structured output không ép độ dài). Hai giới hạn này là đòn bẩy chi phí
  chính.
- `formula_refs` chỉ được nhắc ở `stem` hay `explanation`, không ở phương án (mục 3.6).
- `gaps` ghi khái niệm mà mô hình thấy tài liệu không đủ để ra câu; web không hiện.

Bản lưu và gửi web của một câu (sau khi mã đổi nhãn, gán mã và kết quả kiểm):

```json
{
  "item_id": "qi_<sha256 của concept_id + stem + phương án>",
  "concept_id": "node_…",
  "module_id": "module_007",
  "generator": "llm | cloze",
  "bloom": "hieu",
  "stem": "…",
  "options": [
    {"option_id": "o1", "text": "…", "is_correct": true},
    {"option_id": "o2", "text": "…", "is_correct": false, "distractor_concept_id": "node_… | null", "why_wrong": "…",
     "evidence": [{"chunk_id": "c_…", "char_start": 0, "char_end": 0, "page": 12, "quote": "…"}]}
  ],
  "explanation": "…",
  "evidence": [{"chunk_id": "c_…", "char_start": 0, "char_end": 0, "page": 12, "quote": "…"}],
  "formula_refs": [{"label": "CT2", "formula_id": "…", "page": 11, "bbox": [0, 0, 0, 0]}],
  "checks": {"rules_passed": ["Q1", "Q2"], "verifier": "pass | flag", "flags": []}
}
```

`is_correct` và `why_wrong` chỉ gửi web sau khi nộp bài (mục 4). Báo cáo bài giảng đề nghị dùng chung lược đồ câu hỏi; câu `self_check` của
bài giảng có thể là một câu của ngân hàng này với `generator` riêng.

### 3.4 Luật kiểm tự động

Chín luật mã (0 USD, dưới 50 ms mỗi module, *suy luận*) chạy ngay sau lời gọi sinh; lời gọi kiểm chạy sau đó; luật mã chạy lại trên kết
quả kiểm. Bảng dưới ghi đủ các phép kiểm được yêu cầu:

| # | phép kiểm | cách | chi phí | khi hỏng |
|---|---|---|---|---|
| Q1 | đúng lược đồ, đủ trường, độ dài trong giới hạn, `concept` thuộc module, mỗi khái niệm có câu | mã | 0 | sinh lại phần thiếu 1 lần |
| Q2 | **đáp án có căn cứ trong chunk** | mã: `quote` của đáp án tìm được nguyên văn (NFC, chuẩn hoá khoảng trắng) trong chunk dạy hoặc chunk định nghĩa của **chính** khái niệm, hoặc chunk cùng module; rồi lời gọi kiểm (V) phán căn cứ có đỡ đáp án không | mã 0; V chung một lời gọi/module | bỏ câu |
| Q3 | **chỉ một đáp án đúng** | mã: phương án không trùng hay chứa nhau sau chuẩn hoá; phương án là tên khái niệm thì không được là tên, alias hay danh tính đã gộp của khái niệm đáp án. V: giải mù, phán từng phương án | như trên | bỏ câu nếu V chọn khác đáp án hoặc thấy > 1 phương án đúng |
| Q4 | **câu nhiễu sai theo tài liệu** | mã: câu nhiễu `moi` phải có `quote` nguyên văn; câu nhiễu là khái niệm khác thì câu neo của nó phải khác câu neo của đáp án. V: phán từng câu nhiễu "sai theo nguồn / đúng theo nguồn / nguồn không nói" | như trên | "đúng theo nguồn" → bỏ câu; "nguồn không nói" → gắn cờ, thay câu nhiễu nếu còn ứng viên |
| Q5 | **không lộ đáp án qua độ dài, ngữ pháp, từ lặp** | mã: (a) đáp án không được dài nhất duy nhất và dài hơn 1,3 lần trung bình hai nhiễu; (b) âm tiết nội dung của câu dẫn không được xuất hiện ở đáp án mà không xuất hiện ở nhiễu; (c) cấm "tất cả/không có đáp án nào ở trên", "KHÔNG/ngoại trừ" ở câu dẫn, từ tuyệt đối ("luôn luôn", "không bao giờ") ở phương án — đồ án nay chỉ tiếng Việt nên danh sách từ tiếng Việt chấp nhận được; (d) tên đáp án không có nguyên văn trong câu dẫn | 0 | (a), (b) sinh lại câu đó trong lượt sửa; (c), (d) bỏ |
| Q6 | **không dựa vào hình không hiển thị được** | mã: câu dẫn hoặc phương án nhắc "Hình", "Bảng", "đồ thị", "hình vẽ", hay chứa chuỗi `[formula]`, hay nhắc nhãn `CTk` không có ảnh → bỏ; phương án không được chứa nhãn `CTk` | 0 | bỏ câu |
| Q7 | **tiếng Việt tự nhiên** | mã: tỉ lệ âm tiết có dấu tiếng Việt không thấp bất thường so với chính chunk nguồn; không có câu tiếng Anh dài không có trong nguồn; không còn dấu Markdown, "Câu hỏi:", nhãn S/D/K lọt ra chữ. V cho điểm 1–3 "tự nhiên" như thông tin; kết luận bằng người | 0 (V chung) | gắn cờ; điểm 1 → bỏ |
| Q8 | **không trùng câu** | mã: Jaccard trên 3-gram âm tiết của câu dẫn + đáp án ≥ 0,6 giữa hai câu cùng module → bỏ câu sau; hai câu cùng khái niệm phải khác mức Bloom hoặc khác đáp án | 0 | bỏ câu trùng |
| — | **không bịa ký hiệu toán** (luật K5 của bài giảng) | mã: không có ký hiệu toán, chữ số hay biến mới ngoài nguồn được trích, kể cả `raw_text` | 0 | bỏ câu |

Lời gọi kiểm V ("giải mù"), một lời gọi cho cả module:
- **Đầu vào:** các chunk dạy (nhãn S), các câu đã qua luật mã với phương án **đã xáo và không đánh dấu đáp án**.
- **Đầu ra cho mỗi câu:** phương án chọn kèm `quote`; phán quyết từng phương án (đúng / sai / nguồn không nói); cờ "câu có thể trả lời mà
  không cần nguồn" (gợi ý câu quá dễ); điểm tiếng Việt 1–3.
- **Chi phí ước:** vào khoảng 800 + chunk dạy (400–1.000) + 12 câu × khoảng 250 = khoảng 4.500 token; ra 12 × 80 = 960 token, tức khoảng
  0,0026 USD mỗi module.
- **Vì sao một lời gọi thay vì NLI:** câu hỏi và phương án không phải cặp tiền đề–giả thuyết sẵn; ghép câu dẫn với phương án thành mệnh đề
  cần thêm bước, và chưa có số đo NLI tiếng Việt cho văn giáo trình. *Suy luận:* NLI đa ngôn ngữ chạy CPU (0 USD) đáng thử ở lượt 0 USD như
  một phép kiểm thứ hai cho Q2 trên câu điền khuyết và câu đã chấm người, không đặt trên đường chính trước khi có số đo.
- **Giới hạn đã biết:** Moore 2023 cho thấy "nhiều hơn một đáp án đúng" gần như không bắt được tự động, và cùng mô hình kiểm chính nó có thể
  dễ dãi (mục 2.7). Vì vậy tỉ lệ lỗi này phải đo bằng người, và độ chính xác của V được đo so với người (mục 5.4).

### 3.5 Vận hành và cache

**Sinh lúc nào.** Khuyến nghị cùng nguyên tắc với bài giảng (sinh khi cần lần đầu, cache chung), nhưng **kích hoạt sớm hơn**: khi người học
đầu tiên mở trang module hay bài giảng đầu tiên của module, máy chủ xếp hàng sinh ngân hàng quiz của module đó. Lý do: sinh và kiểm cả
module mất ước 20–70 giây (mục 3.8), dài hơn nhiều một bài giảng, mà người học thường đọc vài phút trước khi làm quiz. Nếu người học bấm quiz
khi ngân hàng chưa xong: hiện tiến độ; tuỳ chủ dự án, cho làm ngay bản điền khuyết (0 USD, sinh sẵn) có ghi rõ "bản tự động đơn giản".

**Một lời gọi cho cả module** (cộng một lời gọi kiểm), không tách theo khái niệm. Lý do: ít lời gọi (ưu tiên số một của dự án), mô hình thấy
mọi khái niệm để tránh trùng và chọn nhiễu nhất quán. Nếu đo thấy p50 thời gian sẵn sàng > 20 giây, chuyển sang hai lời gọi song song, mỗi
lời gọi một nửa khái niệm.

**Khoá cache** theo mẫu của bài giảng:

```
quiz_bank_key = sha256(doc_id, module_id, context_hash, prompt_hash, schema_hash, verifier_prompt_hash,
                       model_id, generation_config, contract_version)
context_hash  = sha256(JSON chuẩn hoá của khối 1–11 sau khi lắp, gồm chữ chunk, danh sách khái niệm và ứng viên nhiễu)
```

Khi `module_id` giữ nguyên mà danh sách khái niệm hay chữ chunk đổi thì `context_hash` đổi và ngân hàng sinh lại. `graph_version` lưu làm siêu
dữ liệu. Chống sinh trùng (single-flight) theo khoá; không cache bản lỗi; "cache âm" 60 giây khi API lỗi, như bài giảng.

**Mỗi lần làm.** Chọn 1 câu/khái niệm theo vòng biến thể, xáo phương án, ghi `attempt` (người học, ngân hàng, câu, lựa chọn, thời điểm) chỉ
để hiện lịch sử tự kiểm tra cho chính người đó; không tính "mastery", không khoá module.

**Nhiệt độ.** Bài giảng chốt 0. Với ngân hàng câu, *suy luận:* nên thử nhiệt độ mặc định vì cần hai biến thể khác nhau cho mỗi khái niệm và
tài liệu Gemini 3 cảnh báo lặp khi nhiệt độ thấp (theo báo cáo bài giảng, mục 3.6); tính tái lập đã có nhờ cache. Lời gọi kiểm giữ 0. Đặt
làm một nhánh trong lượt thử, không chốt trước.

**Lỗi và thử lại.** 429/503 thử lại tối đa 2 lần, lùi theo hàm mũ có nhiễu; sinh lại phần thiếu tối đa 1 lần; tổng tối đa 4 lời gọi mỗi
module.

### 3.6 Công thức `[formula]`

Theo khuyến nghị của báo cáo bài giảng (mục 4.6 ở đó), với ràng buộc riêng của quiz:
- **Web hiện ảnh gốc công thức** cắt theo `page` + `bbox` khi câu dẫn hay lời giải thích nhắc `[CTk]`.
- **LLM nhận `raw_text`** ở dạng `⟦CTk: raw_text⟧` kèm ghi chú "chữ thô, có thể sai cấu trúc".
- **Cấm ra câu mà đáp án hay câu nhiễu là một công thức** (Q6): mô hình không viết được biến thể sai mà vẫn bám tài liệu, và `raw_text` đọc
  rõ chỉ khoảng 6–20% (mục 1.5).
- **Ưu tiên câu về điều kiện, ý nghĩa, tên gọi, mục đích** của công thức, những thứ có trong chữ thường quanh `[formula]`. Ở doc-1, chunk dạy
  có công thức còn trung vị 673 ký tự chữ (đo).

Hệ quả ước: sách toán có ít câu vận dụng hơn và một số khái niệm không có câu. Chỉ số theo dõi là **tỉ lệ khái niệm có ≥ 1 câu sống sót** trên
doc-1, xstk, naive-bayes. Nhánh F2 (gửi ảnh công thức cho mô hình) chỉ thử khi tỉ lệ này < 70% ở doc-1 (mục 5.6). Chi phí ước của F2: trung
vị 6 công thức mỗi module ở doc-1 và naive-bayes (7), 5 ở xstk (đo); với 280–1.120 token mỗi ảnh (số của báo cáo bài giảng, chưa đo cho
Flash-Lite) là thêm 1.700–6.700 token, khoảng 0,0004–0,0017 USD mỗi module, 0,01–0,05 USD cho doc-1.

### 3.7 Phản hồi sau khi làm

Phản hồi hiện **khi nộp cả bài** (chậm vừa phải, hợp tình huống kiểm tra theo Hattie & Timperley), không sau từng câu; có thể bật "xem ngay"
cho người muốn. Mỗi câu hiện:
1. Đúng hay sai, đáp án đúng.
2. Lời giải thích ngắn kèm **câu trích tô sáng** và link về trang, đoạn nguồn.
3. Nếu chọn sai: `why_wrong` của chính phương án đã chọn, kèm đoạn trích cho thấy vì sao sai. Đây là phản hồi mức nhiệm vụ về **cách hiểu
   sai**, loại mạnh nhất theo Hattie & Timperley.

Cuối bài:
- Danh sách khái niệm làm sai, mỗi khái niệm có **link bài giảng** (đã cache, hoặc sinh khi bấm như quyết định chung). Hattie & Timperley: thiếu
  kiến thức thì dạy lại hiệu quả hơn phản hồi.
- Gợi ý "làm lại sau" với biến thể khác (học giãn cách, Dunlosky 2013), không ép.
- Không khen hay chê con người ("bạn giỏi quá"); không điểm phần trăm làm cổng. Chỉ hiện "đúng 5/7 câu" như thông tin.

Phản hồi luôn có, vì trắc nghiệm không phản hồi có thể làm người học nhớ câu nhiễu (Roediger & Marsh 2005; Butler & Roediger 2008). Mọi chữ
phản hồi đã có sẵn trong ngân hàng, nên phản hồi tốn 0 USD và 0 giây chờ.

### 3.8 USD và giây chờ

Giả định, ghi rõ đo hay ước:
- Token vào: ngữ cảnh mức D theo từng module (**đo**, quy đổi bằng tokenizer Gemma), cộng 1.500 token chỉ dẫn (**ước**).
- Token ra: 450 token mỗi câu đủ trường (**ước**: câu dẫn khoảng 150 ký tự, 3 phương án, giải thích ≤ 300, 2 `why_wrong` ≤ 150, câu trích,
  khoá JSON; tỉ lệ đầu ra đo được 3,09 ký tự/token).
- Lời gọi kiểm: 800 token chỉ dẫn, cộng chunk dạy và câu cần kiểm; ra 80 token mỗi câu (**ước**).
- Ngân hàng 2 câu mỗi khái niệm; cộng 20% cho sinh lại (**ước**).

Bảng dưới là kết quả theo công thức trên:

| tài liệu | câu trong ngân hàng | token vào cả cuốn | token ra cả cuốn | USD/module, trung vị (3.1 Flash-Lite) | USD/cuốn, 3.1 Flash-Lite | USD/cuốn, 3.5 Flash-Lite |
|---|---:|---:|---:|---:|---:|---:|
| doc-1 | 398 | 425.045 | 253.128 | 0,0150 | 0,49 | 0,76 |
| nhap-mon-ml | 108 | 112.185 | 68.688 | 0,0145 | 0,13 | 0,21 |
| naive-bayes | 40 | 42.383 | 25.440 | 0,0167 | 0,05 | 0,08 |
| doc-6 | 24 | 23.288 | 15.264 | 0,0144 | 0,03 | 0,05 |
| xstk-ch3-1 | 144 | 148.913 | 91.584 | 0,0193 | 0,18 | 0,27 |
| doc-4 | 978 | 1.131.887 | 622.008 | 0,0145 | 1,22 | 1,90 |

Ghi chú:
- **Token ra chiếm khoảng 78% tiền** (doc-1: 0,38 trên 0,49 USD). Giảm `explanation` từ 300 xuống 200 ký tự bớt khoảng 5% tiền (*ước*).
- Đây là **cận trên** "mọi module đều được mở"; sinh khi cần thì chỉ tốn cho module có người mở.
- Sáu cuốn cộng lại khoảng 2,1 USD (3.1) hay 3,3 USD (3.5). Bài giảng của sáu cuốn khoảng 1,6 USD (báo cáo bài giảng). Pass phụ doc-4 theo
  giá v3 khoảng 46 USD, nên quiz cả cuốn doc-4 dưới 3% chi phí dựng đồ thị.
- Batch hoặc Flex rẻ 50% nếu chủ dự án chọn sinh trước khi tải tài liệu lên.

**Giây chờ.** Không có số chính thức về tốc độ của 3.1 Flash-Lite (báo cáo bài giảng, mục 3.6), nên phải đo. Công thức ước:
`T ≈ TTFT_sinh + N_ra_sinh / v + TTFT_kiểm + N_ra_kiểm / v + T_luật`, với N_ra_sinh khoảng 5.400 token (12 câu) và N_ra_kiểm khoảng 960.
Bảng dưới chỉ minh hoạ độ nhạy với **giá trị giả định**:

| TTFT giả định | tốc độ giả định | sinh | kiểm | tổng một module |
|---:|---:|---:|---:|---:|
| 0,5 giây | 300 token/giây | khoảng 19 giây | khoảng 4 giây | khoảng 23 giây |
| 1 giây | 200 token/giây | khoảng 28 giây | khoảng 6 giây | khoảng 34 giây |
| 2 giây | 100 token/giây | khoảng 56 giây | khoảng 12 giây | khoảng 68 giây |

*Suy luận:* con số này quá dài cho một lượt bấm, nên tải trước khi mở module là bắt buộc. Khi ngân hàng đã cache, giây chờ chỉ là đọc cache
(vài chục mili giây). Nếu tải trước vẫn không đủ, có hai cách: sinh 1 câu/khái niệm trước (khoảng nửa thời gian), biến thể thứ hai sinh nền
sau lần làm đầu (thêm 1 lời gọi mỗi module); hoặc chia hai lời gọi song song (mục 3.5).

### 3.9 Mốc không LLM

Mốc V11 làm như sau, toàn bộ bằng mã, 0 USD:
1. Lấy khái niệm đủ điều kiện ở mục 1.4: 46–100% tuỳ cuốn (đo).
2. Câu dẫn: "Câu sau trích từ tài liệu nói về khái niệm nào?", kèm câu neo đã thay mọi lần xuất hiện của tên, `display_name` và alias bằng
   "___".
3. Phương án: tên đáp án và 2 tên nhiễu, theo thứ tự ưu tiên cạnh mở → cùng module → cùng cụm ở module đã học, ưu tiên cùng `node_type`.
   Mô phỏng cho thấy cách này không lộ đáp án qua độ dài: đáp án dài nhất duy nhất ở 18–25% số lần, không hơn may rủi (đo).
4. Lời giải thích: "Câu trên là định nghĩa của X trong tài liệu" kèm link nguồn. Câu nhiễu là tên khái niệm khác, nên "sai theo tài liệu" theo
   cấu trúc, nhưng vẫn phải qua Q3 về alias, danh tính đã gộp và câu neo trùng.
5. Chạy cùng các luật Q1, Q5–Q8.

Cách so với bản LLM (chi tiết ở mục 5):
- Trên **cùng tập khái niệm** đủ điều kiện, chấm mù trộn lẫn hai bản.
- So tỉ lệ câu chấp nhận được, lỗi nặng, phân bố Bloom, độ phủ khái niệm, USD và giây chờ.
- Kỳ vọng (*suy luận*): mốc ít lỗi nặng hơn nhưng chỉ đo mức nhớ, và phủ kém ở sách toán. Bản LLM phải hơn rõ ở mức hiểu, vận dụng mà không
  thêm lỗi nặng thì mới đáng tiền.

---

## 4. Hợp đồng dữ liệu JSON cho web

Phần này chỉ định nghĩa dữ liệu; đường dẫn API, xác thực và lưu trữ do nhóm web tự thiết kế. Có bốn đối tượng.

**4.1 Trạng thái ngân hàng của một module** (máy chủ → web), dùng để hiện "đang chuẩn bị quiz":

```json
{
  "module_id": "module_007",
  "status": "ready | generating | failed",
  "bank_key": "sha256…",
  "graph_version": "…",
  "model_id": "gemini-3.1-flash-lite",
  "generated_at": "2026-10-11T08:00:00Z",
  "concepts_total": 6,
  "concepts_covered": 6,
  "fallback_available": "cloze | null"
}
```

**4.2 Đề của một lần làm** (máy chủ → web). Không chứa `is_correct`, `why_wrong` hay giải thích, để không lộ đáp án trên trình duyệt:

```json
{
  "attempt_id": "att_…",
  "module_id": "module_007",
  "generator": "llm | cloze",
  "items": [
    {
      "item_id": "qi_…",
      "concept_id": "node_…",
      "concept_display_name": "…",
      "bloom": "nho | hieu | van_dung",
      "stem": "…",
      "options": [{"option_id": "o2", "text": "…"}, {"option_id": "o1", "text": "…"}, {"option_id": "o3", "text": "…"}],
      "formula_refs": [{"label": "CT2", "image_ref": "…"}]
    }
  ]
}
```

**4.3 Bài nộp** (web → máy chủ):

```json
{"attempt_id": "att_…", "answers": [{"item_id": "qi_…", "option_id": "o2"}]}
```

**4.4 Kết quả và phản hồi** (máy chủ → web):

```json
{
  "attempt_id": "att_…",
  "correct_count": 5,
  "total": 7,
  "items": [
    {
      "item_id": "qi_…",
      "concept_id": "node_…",
      "chosen_option_id": "o2",
      "correct_option_id": "o1",
      "is_correct": false,
      "explanation": "…",
      "evidence": [{"chunk_id": "c_…", "page": 12, "char_start": 0, "char_end": 0, "quote": "…"}],
      "why_chosen_wrong": "…",
      "chosen_wrong_evidence": [{"chunk_id": "c_…", "page": 14, "quote": "…"}]
    }
  ],
  "review": [
    {"concept_id": "node_…", "display_name": "…", "module_id": "module_007", "lecture_ref": {"node_id": "node_…"}}
  ],
  "retake_available": true
}
```

Thêm một đối tượng phụ để người học báo câu hỏi lỗi: `{"item_id": "qi_…", "reason": "sai_dap_an | nhieu_dap_an | kho_hieu | khac",
"note": "…"}`. Nhật ký này là nguồn rẻ nhất để tìm lỗi nặng sau khi chạy thật; câu bị báo nhiều lần thì ẩn khỏi ngân hàng chờ người soát.

Ba quy ước chung với bài giảng:
- `chunk_id`, `page`, `char_start`/`char_end`, `quote` cùng nghĩa với hợp đồng bài giảng, để web dùng chung thành phần tô sáng đoạn nguồn.
- `formula_refs` trỏ ảnh cắt theo `page` + `bbox` từ cây phân tích; web thay nhãn `[CTk]` trong chữ bằng ảnh.
- Không có trường điểm theo khái niệm hay "mastery": việc đó ngoài phạm vi.

---

## 5. Giao thức thí nghiệm

### 5.1 Bước 0 USD (làm trước)

Năm việc không gọi mô hình:
1. **Dựng mốc điền khuyết** cho sáu cuốn; đếm khái niệm đủ điều kiện (để so với mục 1.4) và chạy luật Q1, Q3, Q5–Q8 trên nó.
2. **Dựng bộ lắp ngữ cảnh** và in token Gemma theo từng khối cho mọi module; xác nhận trần ở mục 3.1.
3. **Kiểm thử luật bằng câu lỗi cài sẵn.** Viết tay khoảng 40 câu, mỗi câu mang đúng một lỗi (đáp án dài nhất, "tất cả các đáp án trên", câu
   dẫn phủ định, `quote` không có trong nguồn, phương án là alias của đáp án, câu nhắc "Hình 2", chuỗi `[formula]`, câu trùng…), cùng khoảng
   20 câu sạch. Mỗi luật phải bắt đúng câu của nó và không bắt câu sạch. Theo AGENTS.md mục 5, luật chưa từng thấy hỏng là luật đáng ngờ.
4. **Cắt thử ảnh công thức** theo `page` + `bbox` cho 30 công thức doc-1 và xstk; đếm ảnh đọc được bằng mắt.
5. **Thử NLI đa ngôn ngữ trên CPU** (cài trong môi trường riêng, không vào `.venv` của dự án) cho câu điền khuyết, để biết NLI có đáng làm
   phép kiểm thứ hai cho Q2 không.

### 5.2 Mẫu và các nhánh của lượt có tiền

Chọn **120 khái niệm** đủ điều kiện đục lỗ, phân tầng theo cuốn: doc-1 30, doc-4 30, xstk 20, nhap-mon-ml 20, naive-bayes 10, doc-6 10.
Chọn trọn các module chứa chúng, khoảng 20 module, vì ngân hàng sinh theo module. Riêng doc-1 và xstk, ghi thêm kết quả trên mọi khái niệm của
các module đã chọn, kể cả khái niệm không đục lỗ được, để đo độ phủ ở sách toán.

Bảng dưới ghi các nhánh:

| nhánh | mô tả | câu đưa chấm người | trả lời câu hỏi |
|---|---|---|---|
| A | LLM, nạp đủ (mức D), có lời gọi kiểm V | 120 (câu 1 của mỗi khái niệm) | thiết kế chính |
| B | LLM, chỉ nạp mức A (tên, mô tả, câu neo) | 60 | "nạp tăng cường" có đáng không |
| C | như A nhưng bỏ ứng viên câu nhiễu (khối 7) | 60 | ứng viên từ đồ thị có giúp câu nhiễu không |
| D | mốc điền khuyết | 120 (cùng khái niệm với A) | LLM có đáng tiền không |
| A′ | như A, nhiệt độ mặc định thay 0 | chỉ số đo tự động | nhiệt độ |

Tổng 360 câu chấm người. Câu của các nhánh trộn lẫn, bỏ dấu hiệu nhánh, thứ tự ngẫu nhiên.

### 5.3 Chấm người

Rubric cho mỗi câu, hai người chấm độc lập trên toàn bộ 360 câu:
1. **Làm câu trước**, ghi đáp án mình chọn (Kurdi 2020, Doughty 2024). Người chấm làm sai là tín hiệu câu mơ hồ hoặc sai đáp án.
2. Bốn tiêu chí đúng theo nguồn, có/không: đáp án đúng theo đoạn trích; chỉ một đáp án đúng; mọi câu nhiễu sai theo tài liệu; câu đúng khái
   niệm và đúng mức Bloom ghi trên câu.
3. 19 lỗi viết câu theo bảng của Moore 2023 (mục 2.1), có/không từng lỗi.
4. Tiếng Việt tự nhiên: 1–3.
5. Kết luận: dùng ngay / sửa nhẹ / bỏ.

Định nghĩa dùng cho luật quyết định:
- **Lỗi nặng**: đáp án sai, nhiều hơn một đáp án đúng, hay một câu nhiễu đúng theo tài liệu.
- **Câu chấp nhận được**: không có lỗi nặng và có 0–1 lỗi viết câu (theo Tarrant 2006 và Moore 2023).

Cỡ mẫu: 120 câu cho phép ước tỉ lệ chấp nhận khoảng 0,8 với nửa khoảng tin cậy 95% khoảng ±0,07. Nhánh B, C chỉ để thấy chênh lệch lớn. Ước
1,5 phút mỗi câu, tức khoảng 9 giờ mỗi người chấm (*ước*). Chấm thử 20 câu ngoài mẫu trước, sửa hướng dẫn, rồi mới chấm thật.

Đồng thuận: κ của Cohen [27] cho từng tiêu chí, **kèm phần trăm đồng ý, tỉ lệ nhãn dương và Gwet AC1**
([Gwet 2008](https://doi.org/10.1348/000711006X126600)). Lý do: lỗi viết câu hiếm nên κ bị kéo thấp (Doughty: κ 0,07–0,35 trong khi AC1
0,62–0,96). Bất đồng giải quyết bằng thảo luận; người làm câu đúng được ưu tiên, như Doughty.

So sánh A với D trên cùng khái niệm: kiểm định McNemar cho tỉ lệ chấp nhận được và tỉ lệ lỗi nặng; báo kèm khoảng tin cậy của chênh lệch.

### 5.4 Số đo tự động

Mỗi nhánh ghi các số sau:
- Tỉ lệ qua từng luật Q1–Q8; tỉ lệ câu bị V loại, theo lý do.
- **Độ phủ**: tỉ lệ khái niệm có ≥ 1 câu sống sót, theo cuốn (chỉ số chính cho sách toán).
- Phân bố Bloom ghi trên câu, so với nhãn Bloom của người chấm.
- **Độ chính xác của V so với người**: precision và recall của V khi bắt lỗi nặng. Đây là cách duy nhất biết bộ kiểm cùng mô hình có dễ dãi
  không.
- Tỉ lệ trùng (Q8), tỉ lệ câu có công thức bị loại (Q6 và luật ký hiệu toán).
- Token vào, token ra (từ `usage`), USD mỗi module; p50 và p95 thời gian sinh và thời gian kiểm.

LLM làm giám khảo theo bảng 19 lỗi (một lời gọi mỗi câu) là tuỳ chọn, chỉ để so với người; không dùng thay người, vì Moore thấy GPT-4 gắn quá
tay và không bắt được lỗi nhiều đáp án đúng.

### 5.5 Giới hạn

Ba giới hạn phải ghi trong báo cáo đồ án:
- **Độ khó và độ phân biệt** (tỉ lệ làm đúng, hệ số phân biệt) cần người học thật làm thử; chuyên gia chấm chỉ là bằng chứng ban đầu (Kurdi
  2020). Lượt này không đo được.
- **Hiệu quả học** nằm ngoài phạm vi đề cương.
- Người chấm là thành viên nhóm, không phải giảng viên môn; kết quả là "chấm của nhóm", ghi rõ như vậy.

### 5.6 Luật quyết định (viết trước khi đo)

Bảng dưới ghi luật cho từng câu hỏi thiết kế:

| câu hỏi | luật |
|---|---|
| Bản LLM có làm mặc định không? | Có, nếu nhánh A đạt **≥ 80% câu chấp nhận được** (mốc tham chiếu: 81,7% của Doughty), **≤ 3% lỗi nặng**, và không kém D quá 2 điểm phần trăm về lỗi nặng. Nếu lỗi nặng > 3%: không mở cho người học; sửa prompt hay V rồi đo lại. |
| LLM có hơn mốc rõ không? | Bản LLM chỉ đáng tiền nếu ≥ 30% câu được người chấm xếp mức hiểu hoặc vận dụng (mốc gần như 0%) mà vẫn qua dòng trên. Nếu không, dùng mốc điền khuyết và chỉ gọi LLM cho khái niệm không đục lỗ được. |
| Có nạp đủ (A) hay nạp gọn (B)? | Giữ A nếu tỉ lệ chấp nhận hơn B ≥ 5 điểm phần trăm hoặc lỗi nặng thấp hơn; nếu không khác, chọn B vì rẻ hơn. |
| Có giữ ứng viên câu nhiễu (A hay C)? | Giữ nếu tỉ lệ "câu nhiễu khó tin" theo người chấm giảm ≥ 5 điểm phần trăm; nếu không, bỏ khối 7. |
| Có giữ lời gọi kiểm V? | Giữ nếu V bắt ≥ 50% lỗi nặng mà người tìm thấy với precision ≥ 0,5. Nếu không: bỏ V, chỉ giữ luật mã, và báo rõ lỗi nặng còn lại. |
| Có mở nhánh ảnh công thức (F2)? | Mở thử nếu độ phủ khái niệm ở doc-1 < 70%. |
| Có tách lời gọi để giảm giây chờ? | Tách nếu p50 thời gian sẵn sàng của một module > 20 giây. |
| Nhiệt độ? | Chọn nhiệt độ mặc định nếu A′ cho tỉ lệ trùng (Q8) thấp hơn và tỉ lệ qua luật không kém A quá 3 điểm phần trăm; nếu không, giữ 0 như bài giảng. |

### 5.7 Dự toán lượt có tiền (chưa chạy)

Lượt này phải dry-run trước và được chủ dự án duyệt. Dự toán theo mục 3.8:

| hạng mục | cách tính | USD (ước) |
|---|---|---:|
| Nhánh A (sinh + kiểm) | 20 module × 0,015 | 0,30 |
| Nhánh B | 20 module × khoảng 0,0125 (vào ít hơn) | 0,25 |
| Nhánh C | 20 module × khoảng 0,014 | 0,28 |
| Nhánh A′ | 20 module × 0,015 | 0,30 |
| Tuỳ chọn: LLM chấm 19 lỗi | 360 câu × (khoảng 1.500 token vào + 300 ra) | 0,30 |
| Dự phòng sinh lại, lỗi | 20% | 0,29 |
| **Tổng** | | **khoảng 1,7** |

Khoảng 80 lời gọi; cũng là số mẫu để đo p50/p95 giây chờ. Mức chi nhỏ so với các trần ngân sách đã ghi của dự án.

---

## 6. Rủi ro và câu hỏi cho chủ dự án

Bảng rủi ro:

| rủi ro | ảnh hưởng | giảm thiểu |
|---|---|---|
| Cạnh mở sai làm câu nhiễu thực ra đúng | lỗi nặng | Q4 và V; người học báo lỗi; đo bằng người |
| "Nhiều hơn một đáp án đúng" khó bắt tự động | lỗi nặng lọt qua | đo bằng người; nút báo lỗi; ẩn câu bị báo |
| Bộ kiểm cùng mô hình dễ dãi với chính nó | V báo đạt sai | đo precision/recall của V; nếu kém thì bỏ V và nói rõ |
| Sách toán ít câu vì công thức | quiz mỏng ở doc-1 | đo độ phủ; mốc điền khuyết; nhánh ảnh công thức |
| Câu nhiễu gieo kiến thức sai | hại học | phản hồi bắt buộc, có `why_wrong` và câu trích |
| Đồ thị chia module sai, khái niệm cốt lõi lạc chỗ | câu hỏi khái niệm chưa học | câu chỉ hỏi khái niệm của module; nhiễu chỉ lấy từ module đã học |
| Giây chờ dài khi người học vào thẳng quiz | trải nghiệm kém | tải trước; mốc điền khuyết làm bản tạm |
| `gemini-3.1-flash-lite` tắt sớm nhất 2027-05-07 | phải sinh lại | `model_id` trong khoá cache; ngân sách 3.5 Flash-Lite +56% (mục 3.8) |

Câu hỏi cho chủ dự án:
1. Đồng ý **3 phương án** (1 đúng, 2 nhiễu) thay vì 4 như thói quen đề thi?
2. **Tải trước khi mở module** (tốn tiền cả cho module mở mà không làm quiz, khoảng 0,015 USD mỗi module) hay chỉ sinh khi bấm quiz (chờ 20–70
   giây)?
3. Bản điền khuyết có được **hiện cho người học** khi bản LLM chưa xong hay hỏng, hay chỉ dùng trong thí nghiệm?
4. Có cần **câu tự giải thích** có đáp án mẫu (người học tự so, 0 USD lúc làm)?
5. Có lưu **lịch sử làm bài** theo người học (chỉ để chính họ xem lại, không mô hình hoá trình độ)?
6. Ai là **hai người chấm** cho 360 câu (khoảng 9 giờ mỗi người), và có cần giảng viên môn chấm một phần nhỏ để đối chiếu?
7. Quiz là phần thêm ngoài đề cương: đưa vào báo cáo đồ án như **mục mở rộng của trợ lý học tập** hay để ở phụ lục?

---

## 7. Nguồn

Đọc ngày 2026-10-11. Mức đọc ghi sau mỗi nguồn. Nguồn trùng danh mục đề cương ghi số của đề cương.

Viết câu, lỗi viết câu, số phương án:
- [1] T. M. Haladyna, S. M. Downing, and M. C. Rodriguez, "A review of multiple-choice item-writing guidelines for classroom assessment,"
  *Applied Measurement in Education*, vol. 15, no. 3, pp. 309–333, 2002, doi: 10.1207/S15324818AME1503_5. — chỉ kiểm siêu dữ liệu (Crossref)
  và tóm tắt; nội dung hướng dẫn đọc qua [2] và [3]; **chưa đọc toàn văn** (không có bản mở).
- [2] T. M. Haladyna and S. M. Downing, "A taxonomy of multiple-choice item-writing rules," *Applied Measurement in Education*, vol. 2, no. 1,
  pp. 37–50, 1989, doi: 10.1207/s15324818ame0201_3. — đọc danh sách luật qua bản in lại của Penn State Schreyer Institute
  (https://www.schreyerinstitute.psu.edu/pdf/Multiple_Choice_Item_Writing_Rules.pdf).
- [3] S. Moore, H. A. Nguyen, T. Chen, and J. Stamper, "Assessing the quality of multiple-choice questions using GPT-4 and rule-based methods,"
  in *Proc. EC-TEL 2023*, LNCS, Springer, 2023, doi: 10.1007/978-3-031-42682-7_16; arXiv:2307.08161. — đọc toàn văn.
- [4] M. Tarrant, A. Knierim, S. K. Hayes, and J. Ware, "The frequency of item writing flaws in multiple-choice questions used in high stakes
  nursing assessments," *Nurse Education Today*, vol. 26, no. 8, pp. 662–671, 2006, doi: 10.1016/j.nedt.2006.07.006. — chỉ kiểm siêu dữ liệu;
  nội dung qua [3]. Crossref có thêm một bản cùng tên ở *Nurse Education in Practice* 6(6), doi: 10.1016/j.nepr.2006.07.002.
- [5] M. C. Rodriguez, "Three options are optimal for multiple-choice items: A meta-analysis of 80 years of research," *Educational
  Measurement: Issues and Practice*, vol. 24, no. 2, pp. 3–13, 2005, doi: 10.1111/j.1745-3992.2005.00006.x. — chỉ đọc tóm tắt.
- [6] S. M. Downing, "The effects of violating standard item writing principles on tests and students," *Advances in Health Sciences
  Education*, vol. 10, no. 2, pp. 133–143, 2005, doi: 10.1007/s10459-004-4019-5. — chỉ kiểm siêu dữ liệu.

Sinh câu hỏi, câu nhiễu, điền khuyết, Bloom:
- [7] G. Kurdi, J. Leo, B. Parsia, U. Sattler, and S. Al-Emari, "A systematic review of automatic question generation for educational
  purposes," *International Journal of Artificial Intelligence in Education*, vol. 30, no. 1, pp. 121–204, 2020,
  doi: 10.1007/s40593-019-00186-y. — đọc toàn văn các phần về dạng câu, câu nhiễu, phản hồi, đánh giá và chất lượng báo cáo.
- [8] A. M. Olney, "Generating multiple choice questions from a textbook: LLMs match human performance on most metrics," in *Proc. Workshop on
  Empowering Education with LLMs (AIED 2023)*, CEUR-WS vol. 3487, 2023. https://ceur-ws.org/Vol-3487/paper7.pdf — đọc toàn văn.
- [9] J. Doughty *et al.*, "A comparative study of AI-generated (GPT-4) and human-crafted MCQs in programming education," in *Proc. 26th
  Australasian Computing Education Conf. (ACE 2024)*, 2024, doi: 10.1145/3636243.3636256; arXiv:2312.03173. — đọc toàn văn.
- [10] S. K. Bitew, J. Deleu, C. Develder, and T. Demeester, "Distractor generation for multiple-choice questions with predictive prompting and
  large language models," arXiv:2307.16338, 2023 (bản hội nghị doi: 10.1007/978-3-031-74627-7_4 chỉ thấy qua kết quả tìm kiếm,
  **chưa xác minh**). — đọc toàn văn bản arXiv.
- [11] M. J. Gierl, O. Bulut, Q. Guo, and X. Zhang, "Developing, analyzing, and using distractors for multiple-choice tests in education: A
  comprehensive review," *Review of Educational Research*, vol. 87, no. 6, pp. 1082–1116, 2017, doi: 10.3102/0034654317726529. — chỉ đọc tóm
  tắt.
- [12] R. Mitkov and L. A. Ha, "Computer-aided generation of multiple-choice tests," in *Proc. HLT-NAACL 03 Workshop on Building Educational
  Applications Using NLP*, 2003. https://aclanthology.org/W03-0203/ — chỉ kiểm trang bài.
- [13] R. Mitkov, L. A. Ha, and N. Karamanis, "A computer-aided environment for generating multiple-choice test items," *Natural Language
  Engineering*, vol. 12, no. 2, pp. 177–194, 2006, doi: 10.1017/S1351324906004177. — chỉ đọc tóm tắt.
- [14] M. Agarwal and P. Mannem, "Automatic gap-fill question generation from text books," in *Proc. 6th Workshop on Innovative Use of NLP for
  Building Educational Applications*, 2011. https://aclanthology.org/W11-1407/ — chỉ kiểm trang bài.
- [15] D. R. Krathwohl, "A revision of Bloom's taxonomy: An overview," *Theory Into Practice*, vol. 41, no. 4, pp. 212–218, 2002,
  doi: 10.1207/s15430421tip4104_2. — chỉ kiểm siêu dữ liệu.
- [16] L. W. Anderson and D. R. Krathwohl, Eds., *A Taxonomy for Learning, Teaching, and Assessing: A Revision of Bloom's Taxonomy of
  Educational Objectives*. New York, NY, USA: Longman, 2001. — **chưa xác minh** trực tiếp; dẫn qua [15].

Phản hồi và hiệu ứng kiểm tra:
- [17] J. Hattie and H. Timperley, "The power of feedback," *Review of Educational Research*, vol. 77, no. 1, pp. 81–112, 2007,
  doi: 10.3102/003465430298487. — đọc toàn văn các phần về số liệu tổng hợp, mô hình ba câu hỏi, bốn mức và thời điểm phản hồi.
- [18] H. L. Roediger and J. D. Karpicke, "Test-enhanced learning: Taking memory tests improves long-term retention," *Psychological Science*,
  vol. 17, no. 3, pp. 249–255, 2006, doi: 10.1111/j.1467-9280.2006.01693.x. — chỉ đọc tóm tắt.
- [19] J. Dunlosky, K. A. Rawson, E. J. Marsh, M. J. Nathan, and D. T. Willingham, "Improving students' learning with effective learning
  techniques," *Psychological Science in the Public Interest*, vol. 14, no. 1, pp. 4–58, 2013, doi: 10.1177/1529100612453266. — chỉ đọc tóm
  tắt.
- [20] H. L. Roediger and E. J. Marsh, "The positive and negative consequences of multiple-choice testing," *Journal of Experimental
  Psychology: Learning, Memory, and Cognition*, vol. 31, no. 5, pp. 1155–1159, 2005, doi: 10.1037/0278-7393.31.5.1155. — chỉ kiểm siêu dữ
  liệu; nội dung qua tóm tắt của [21].
- [21] A. C. Butler and H. L. Roediger, "Feedback enhances the positive effects and reduces the negative effects of multiple-choice
  testing," *Memory & Cognition*, vol. 36, no. 3, pp. 604–616, 2008, doi: 10.3758/MC.36.3.604. — chỉ đọc tóm tắt (PubMed).

Đồng thuận và LLM giám khảo:
- [27 của đề cương] J. Cohen, "A coefficient of agreement for nominal scales," *Educational and Psychological Measurement*, vol. 20, no. 1,
  pp. 37–46, 1960, doi: 10.1177/001316446002000104. — chỉ kiểm siêu dữ liệu.
- [22] K. L. Gwet, "Computing inter-rater reliability and its variance in the presence of high agreement," *British Journal of Mathematical
  and Statistical Psychology*, vol. 61, no. 1, pp. 29–48, 2008, doi: 10.1348/000711006X126600. — chỉ kiểm siêu dữ liệu.
- [23] L. Zheng *et al.*, "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena," in *Advances in Neural Information Processing Systems 36
  (Datasets and Benchmarks)*, 2023; arXiv:2306.05685. — đọc các mục về thiên lệch, trên bản tải của phiên tên module.

Tài liệu nội bộ của dự án:
- [Báo cáo bài giảng](nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md) — nhãn nguồn, luật `quote`, khoá cache, xử lý công thức, số token ảnh,
  số liệu tài liệu Gemini.
- [Báo cáo tên và mô tả module](nghien-cuu-ten-va-mo-ta-module-2026-10-11.md) — mô tả module dùng làm khối 1.
- [Nghiên cứu Gemini v4](nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md) — giá, cache ngầm, Batch và Flex, vòng đời mô hình.
- [`spec-addendum.md`](../doc/spec-addendum.md) — A11 (dòng 701–711), B3 (dòng 1078–1082).
- [`pipeline-seminar-chuan-V1-V13-v2.md`](../doc/pipeline-seminar-chuan-V1-V13-v2.md) — V11 điền khuyết.
- [Đề cương đồ án](../doanchuyennganh/decuong/de-cuong-do-an-chuyen-nganh.md) — mục tiêu 4, phạm vi, phương pháp đánh giá, [27].
- Artifact đo: graph, chunk và cây phân tích của sáu cuốn theo bảng trong bối cảnh chung của phiên; nhật ký `anchor_decision_log` (1.033 lời
  gọi) để hiệu chỉnh ký tự/token.
