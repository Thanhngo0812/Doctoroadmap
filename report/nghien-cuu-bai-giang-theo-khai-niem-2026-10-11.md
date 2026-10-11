# Nghiên cứu Pha B: bài giảng sinh khi người học bấm vào một khái niệm — 2026-10-11

Báo cáo này trả lời bảy câu hỏi về bài giảng sinh theo khái niệm của Pha B: nạp ngữ cảnh gì, khung sư phạm, trích dẫn và kiểm trung
thực, công thức bị mất ở sách toán, vận hành (cache, stream, giây chờ, USD), mốc so sánh và giao thức đánh giá, văn liệu thực nghiệm về
LLM sinh nội dung giảng dạy. Quyết định của chủ dự án ngày 2026-10-11 được coi là đã chốt: bài giảng sinh ở lần bấm đầu, temperature 0,
cache chung cho mọi người học, gọi `gemini-3.1-flash-lite`. Báo cáo không viết lại phần của hai báo cáo song song về
[quiz](nghien-cuu-quiz-tu-kiem-tra-2026-10-11.md) và [trợ lý hỏi đáp](nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md); văn liệu trung
thực và trích dẫn dùng chung chỉ được trình bày ở phần áp cho bài giảng.

**Cách làm.** Mọi nguồn được đọc ngày 2026-10-11. PDF tải vào thư mục tạm và đọc bằng `pdftotext`; số liệu lấy từ chính bài, không qua
công cụ tóm tắt web. Siêu dữ liệu kiểm qua Crossref, ACL Anthology, OpenAlex và Europe PMC. Số đo dự án do ba script chỉ đọc artifact của
sáu cuốn được phép; không gọi Gemini hay API trả tiền nào, không gửi nội dung giáo trình lên dịch vụ ngoài, không mở tập giữ lại. Báo cáo
không viết spec, vé hay mã sản phẩm, và không thiết kế API web. Lượt làm bị ngắt hai lần vì hết lượt dùng, nên một số nguồn chỉ dừng ở tóm
tắt; mức đọc ghi ở mục 8. Đoạn mở đầu bằng *Suy luận:* là ý kiến của người viết, chưa có thí nghiệm.

---

## Tóm tắt

Chín ý chính:
1. **Ngữ cảnh bài giảng ngắn, nên vấn đề là nhiễu chứ không phải độ dài.** Lắp đủ mọi nguồn từ đồ thị chỉ có trung vị 470–850 token và p90
   550–1.550 token (đo bằng bộ tách Gemma). Đồ thị làm ngữ cảnh tăng 2,5–3 lần so với chỉ chunk dạy. Câu nhiễu cùng chủ đề là loại gây hại
   nhất ([Shi, ICML 2023](https://arxiv.org/abs/2302.00093)), mà khái niệm kề, cạnh mở, khái niệm học sau đều là loại đó. Khuyến nghị lắp tất
   định từ cấu trúc, có trần từng khối và nhãn vai trò (mục 4.1); truy hồi chỉ là nhánh dự phòng.
2. **Mã làm phần có sẵn, LLM chỉ viết phần diễn giải.** Vị trí trong module, câu định nghĩa nguyên văn, danh sách tiên quyết kèm câu trích,
   tên khái niệm học sau đều do mã dựng, 0 USD, hiện ngay. LLM viết bốn phần: nhắc nền, giải thích, ví dụ trong sách, phân biệt, cộng một
   câu tự kiểm tra (mục 4.2). Khung dựa trên Merrill (kích hoạt, minh hoạ), Ausubel (khung mở bài), Atkinson (ví dụ có lời giải), Mayer
   (chia đoạn, tín hiệu, bỏ phần thừa), so sánh ca (d = 0,50, [Alfieri 2013](https://doi.org/10.1080/00461520.2013.775712)) và testing
   effect ([Roediger & Karpicke 2006](https://doi.org/10.1111/j.1467-9280.2006.01693.x)).
3. **Trích dẫn theo từng ý bằng nhãn ngắn, kiểm câu trích nguyên văn bằng mã.** Mỗi ý có nhãn nguồn (`S1`, `N2`…) và một câu trích ngắn;
   mã kiểm câu trích như hợp đồng `quote` của A8. Nhãn ngắn tốn 4 token, `chunk_id` tốn 25 (mục 2.3). Trích trong lúc sinh tốt hơn gắn
   trích dẫn sau: citation recall của cách gắn sau thấp hơn 47% trên ASQA ([ALCE, EMNLP 2023](https://aclanthology.org/2023.emnlp-main.398/)).
   Kiểm bằng mã không bắt được diễn giải sai; phần đó đo offline bằng citation recall/precision và RAGAS (mục 4.4, 6.3).
4. **Tiên quyết phải trình bày khiêm tốn.** Mọi tiên quyết hiển thị là cạnh cứng có câu trích, và câu trích nằm trong định nghĩa của chính
   khái niệm đích ở 98–100% cạnh. Câu đó chứng minh định nghĩa *dùng* tiên quyết, không chứng minh phải học trước. Có 2–7% cạnh ngược thứ tự
   sách. Câu dẫn đề xuất: "Định nghĩa này dùng tới…", kèm nút xem câu trích và nút báo sai.
5. **Công thức bị mất là lỗ hổng lớn nhất ở sách toán, nhưng chữ gốc và vị trí vẫn còn.** 81% khái niệm doc-1 có chunk dạy chứa
   `[formula]`, 40% có câu định nghĩa chứa nó (xstk: 50% và 25%). Cây parse giữ `raw_text`, `page`, `bbox` cho 562/562 công thức doc-1, nhưng
   25% có ký tự PUA và cấu trúc hai chiều bị dàn phẳng. Khuyến nghị: web hiện ảnh gốc cắt theo `bbox`; LLM nhận `raw_text` và chỉ nhắc
   công thức bằng nhãn, không tự viết; ảnh cho mô hình đa phương thức (280–1.120 token/ảnh theo trang Gemini) là nhánh thí nghiệm, thêm
   0,02–0,09 USD cho doc-1 (mục 4.6).
6. **Stream được JSON, nên kiểm từng ý trước khi hiện.** Trang Gemini chính thức nói các mẩu stream là JSON dở ghép được thành đối tượng
   đầy đủ, theo thứ tự khoá của schema. Máy chủ kiểm từng ý khi ý đó đóng; ý hỏng không bao giờ hiện. Khoá cache nên dùng băm của ngữ cảnh đã
   lắp, để đổi đồ thị không liên quan thì không phải sinh lại (mục 4.5).
7. **Rẻ: khoảng 0,0019 USD mỗi bài, 0,37 USD cho doc-1 và 0,92 USD cho doc-4 nếu mọi khái niệm được bấm** (khoảng 0,0013–0,0027 USD/bài).
   Token ra chiếm khoảng 70% tiền. Giây chờ không có số chính thức; phải đo. Với giả định 1 giây TTFT và 200 token/giây, ý đầu tiên hiện sau
   khoảng 1,6 giây và bài xong sau khoảng 5,5 giây; phần do mã dựng hiện ngay (mục 4.7).
8. **Nhiệt độ 0 có rủi ro.** Tài liệu Gemini 3 khuyên giữ nhiệt độ mặc định và cảnh báo lặp hoặc giảm chất lượng khi dưới 1.0, nhất là bài
   toán. Giữ quyết định nhiệt độ 0, nhưng có luật kiểm lặp và một nhánh so sánh.
9. **Đánh giá bằng 80 khái niệm, chấm mù theo cặp, hai người chấm.** Các nhánh gồm mốc trích câu V11, LLM không đồ thị, LLM có đồ thị, ảnh
   công thức, nhiệt độ mặc định, và LLM không ngữ cảnh. Luật quyết định viết trước khi đo. Giám khảo LLM chỉ làm nhãn bạc, chấm hai thứ tự
   ([Zheng 2023](https://arxiv.org/abs/2306.05685)). Bước đầu tốn 0 USD; lượt có tiền dự toán 1,8–2,7 USD, xin trần 5 USD (mục 6).

---

## 1. Bối cảnh và ràng buộc

Bài giảng phải thoả ba yêu cầu của đề cương ([mục tiêu 4](../doanchuyennganh/decuong/de-cuong-do-an-chuyen-nganh.md), phạm vi mục 4.2,
phương pháp mục 5.2):
- nội dung chỉ trong phạm vi tài liệu đã tải lên;
- mọi nội dung trích dẫn đoạn nguồn;
- chủ động nhắc khái niệm nền theo đồ thị, và bài giảng đi theo thứ tự lộ trình.

Các ràng buộc khác lấy từ bối cảnh chung của Pha B:
- Pha B chưa có dòng mã nào: không có A11, A12, B1–B4, prompt bài giảng hay web. Đặc tả A11 trong
  [spec-addendum](../doc/spec-addendum.md) (dòng 701–711) ghi "sinh offline"; quyết định 2026-10-11 đổi thành sinh ở lần bấm đầu.
- Tiền và thời gian là nguyên tắc số một: mỗi khuyến nghị phải có USD và giây chờ. Giá `gemini-3.1-flash-lite`: 0,25 USD cho 1 triệu
  token vào, 1,50 USD cho 1 triệu token ra; cache ngầm của dòng Gemini 3 cần tiền tố ít nhất 4.096 token
  ([nghiên cứu Gemini v4](nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md)).
- Đồ thị có cạnh sai: độ chính xác cạnh bao đóng 0,87 trên tài liệu phát triển, 0,58–0,64 trên tập giữ lại v3; chấm mù thấy khoảng
  1/3 cạnh dư "không cần thứ tự" ([kết quả tập giữ lại v3](ket-qua-tap-giu-lai-v3-2026-10-04.md)). Bài giảng không được khẳng định quá
  mức về tiên quyết.
- Đề cương đặt mô hình hoá trình độ từng người học ngoài phạm vi, nên bài giảng là một bản chung cho mọi người học.

---

## 2. Hiện trạng dữ liệu cho bài giảng (số đo 2026-10-11)

### 2.1 Cách đo

Ba script chỉ đọc artifact của sáu cuốn được phép, không gọi mô hình hay embedding: `d_context.py` (cỡ ngữ cảnh), `e_formula_tokens.py`
(công thức, hệ số token), `f_edges.py` (cạnh tiên quyết hiển thị). Script và kết quả thô (`context-summary.json`, `rows-<doc>.json`) nằm
trong thư mục tạm của phiên, không đưa vào repo.

Token được ước theo hai cách:
- **Ký tự / 3**, quy ước dry-run của dự án.
- **Bộ tách SentencePiece của Gemma** (`vendor/gemma/tokenizer.model`, cũng là bộ tách dự án dùng để cắt chunk), chạy cục bộ. Bộ tách
  của Gemini 3 không có bản offline, nên số Gemma chỉ là đại diện; số chính xác phải đo bằng `countTokens` ở bước 0 USD (mục 6).
  Trên chữ thật của sáu cuốn, một token Gemma ứng với 2,6–3,7 ký tự: sách toán nhiều ký hiệu (doc-1) khoảng 2,6–2,9, văn xuôi triết
  học (doc-4) khoảng 3,6–3,7; trung bình 1,2–1,3 token cho mỗi âm tiết tiếng Việt. Quy ước 3 ký tự/token vì vậy hơi cao với doc-1 và
  hơi thấp với doc-4.

Sáu cách lắp ngữ cảnh được đo, mỗi cách cộng thêm vào cách trước:

| mã | gồm | nguồn trong `graph.json` và chunk |
|---|---|---|
| B0 | tên khái niệm và chunk dạy, **không dùng đồ thị** (mốc ablation) | `teaching_chunk_ids` |
| B1 | + câu neo, mô tả A5, chunk định nghĩa khác chunk dạy | `anchor.sentence`, `description`, `defining_chunk_ids` |
| B2 | + tiên quyết hiển thị: tên, câu đầu mô tả, câu trích `quote` của cạnh `requires` | `display_prerequisites`, `requires_edges` |
| B3 | + tên module, khái niệm đứng trước và sau trong module (tên, câu đầu mô tả) | `modules[].title`, `modules[].node_ids` |
| B4 | + cạnh mở `example_of`, `contrasts_with`, `subtype_of`, `component_of`, `uses` kèm câu bằng chứng; hình/bảng `confirmed` (chú thích) | `open_edges` |
| B5 | + một chunk bài tập có nhắc đúng tên (gần chunk dạy nhất), tối đa 3 khái niệm học sau theo `requires` | chunk vai trò `bai_tap`, `mention_map`, `requires_edges` |

Số đo chỉ tính phần ngữ cảnh; chỉ dẫn hệ thống và lược đồ đầu ra được cộng riêng ở mục 4.7.

### 2.2 Mỗi khái niệm có những nguồn gì

Bảng sau đếm số khái niệm có từng loại nguồn (tỉ lệ trên số khái niệm của cuốn):

| tài liệu | khái niệm | chunk dạy khác nhau (khái niệm/chunk) | có chunk định nghĩa thêm | có ≥ 1 tiên quyết hiển thị | có cạnh mở 5 kiểu | có hình/bảng xác nhận | có chunk bài tập nhắc tên | có khái niệm học sau |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| doc-1 | 199 | 94 (2,1) | 29 (15%) | 190 (95%) | 144 (72%) | 15 (8%) | 44 (22%) | 146 (73%) |
| nhap-mon-ml | 54 | 26 (2,1) | 11 (20%) | 36 (67%) | 40 (74%) | 3 (6%) | 0 (không có chunk `bai_tap`) | 29 (54%) |
| naive-bayes | 20 | 12 (1,7) | 11 (55%) | 6 (30%) | 18 (90%) | 4 (20%) | 1 (5%) | 6 (30%) |
| doc-6 | 12 | 8 (1,5) | 3 (25%) | 3 (25%) | 1 (8%) | 5 (42%) | 0 | 1 (8%) |
| xstk-ch3-1 | 72 | 34 (2,1) | 18 (25%) | 67 (93%) | 59 (82%) | 5 (7%) | 11 (15%) | 53 (74%) |
| doc-4 | 489 | 286 (1,7) | 130 (27%) | 403 (82%) | 403 (82%) | 0 | 19 (4%) | 310 (63%) |

Sáu điều rút ra từ số đo, có ảnh hưởng trực tiếp tới thiết kế:
1. **Một chunk dạy phục vụ trung bình 1,5–2,1 khái niệm**, có chunk dạy tới 7 khái niệm (doc-1), 6 (nhap-mon-ml, xstk), 5 (doc-4). Các
   khái niệm cùng chunk sẽ nhận ngữ cảnh gần giống nhau. Nếu không có gì định hướng, các bài giảng này dễ lặp nhau. Câu neo
   (`anchor.sentence`) là thứ phân biệt chúng: câu neo luôn nằm trong chunk dạy (199/199 ở doc-1, 71/72 ở xstk, 489/489 ở doc-4).
2. **Mọi tiên quyết hiển thị đều là cạnh cứng có câu trích.** Ở cả sáu cuốn, mọi cặp trong `display_prerequisites` đều có cạnh trực tiếp
   trong `requires_edges`, `soft_reason` rỗng, `prerequisite_kind = can_de_hieu`, có `quote` (doc-1 302/302, doc-4 643/643). Câu trích
   nằm trong chunk dạy hoặc chunk định nghĩa của chính khái niệm đích ở 298/302 cạnh (doc-1) và 642/643 (doc-4). Kiểu căn cứ chủ yếu là
   `trong_dinh_nghia` (doc-1 283/302, doc-4 522/643). Câu trích trung vị 99 ký tự ở doc-1, 148 ở doc-4. Như vậy câu "vì sao học cái này
   trước" gần như luôn là một câu trong định nghĩa của khái niệm đích có nhắc tới tiên quyết. Đây là bằng chứng tốt để trích, nhưng chỉ
   cho thấy định nghĩa *dùng* tiên quyết, không chứng minh người học *phải* học nó trước.
3. **Có cạnh ngược thứ tự sách trong tiên quyết hiển thị**: `order_relation = ngược` ở 5/302 cạnh của doc-1, 3/99 của xstk, 3/59 của
   nhap-mon-ml, 43/643 của doc-4. Với các cạnh này, sách dạy tiên quyết *sau* khái niệm đích, nên bài giảng không được viết "bạn đã học
   X ở phần trước".
4. **Hình/bảng xác nhận hiếm** (0–15 khái niệm mỗi cuốn), bài tập nhắc tên cũng hiếm (0–22%). Hai phần này là tuỳ chọn, không thể là
   trụ của khung bài giảng. Riêng xstk có 48 chunk "Cách giải" bị gán nhầm `de_cuong`, nên số bài tập của xstk bị đếm thiếu.
5. **Có ca thiếu nguồn.** xstk có 1 khái niệm không có câu neo và chunk dạy (`teaching_status = uncertain`). Mô tả A5 rơi về bản nháp
   chưa kiểm (`draft_fallback_invalid`) ở 1 khái niệm của doc-1 và 4 của doc-4. Lắp ngữ cảnh phải có nhánh cho các ca này.
6. **Cạnh `requires` trong `open_edges` là đề xuất chưa kiểm** (doc-1 có 7, doc-4 có 25). Các cạnh này không được đưa vào khối tiên quyết.

### 2.3 Cỡ ngữ cảnh theo cách lắp

Bảng sau ghi token Gemma của phần ngữ cảnh, dạng trung vị / p90 / lớn nhất:

| tài liệu | B0 chỉ chunk dạy | B1 lõi | B2 + tiên quyết | B3 + module | B4 + cạnh mở, hình | B5 đầy đủ | ký tự/token (B5) |
|---|---|---|---|---|---|---|---:|
| doc-1 | 275 / 314 / 593 | 368 / 628 / 1.103 | 527 / 806 / 1.331 | 604 / 921 / 1.391 | 650 / 1.017 / 1.686 | 728 / 1.265 / 1.978 | 2,86 |
| nhap-mon-ml | 305 / 355 / 414 | 379 / 896 / 1.130 | 555 / 1.099 / 1.304 | 651 / 1.181 / 1.406 | 732 / 1.319 / 1.554 | 737 / 1.421 / 1.687 | 3,45 |
| naive-bayes | 138 / 268 / 281 | 473 / 786 / 1.041 | 549 / 786 / 1.041 | 638 / 846 / 1.087 | 738 / 1.032 / 1.476 | 738 / 1.032 / 1.627 | 3,28 |
| doc-6 | 122 / 168 / 169 | 308 / 372 / 445 | 363 / 445 / 473 | 422 / 538 / 547 | 470 / 554 / 703 | 470 / 554 / 703 | 3,32 |
| xstk-ch3-1 | 282 / 347 / 416 | 419 / 887 / 2.135 | 601 / 1.064 / 2.321 | 689 / 1.136 / 2.429 | 745 / 1.218 / 2.953 | 848 / 1.346 / 3.051 | 3,15 |
| doc-4 | 315 / 447 / 530 | 446 / 940 / 1.848 | 617 / 1.076 / 2.214 | 702 / 1.187 / 2.312 | 778 / 1.420 / 2.797 | 831 / 1.549 / 2.975 | 3,57 |

Bảng sau ghi cỡ từng phần, dạng số khái niệm có phần đó / token Gemma trung vị khi có:

| phần | doc-1 | xstk-ch3-1 | doc-4 | nhap-mon-ml |
|---|---|---|---|---|
| câu neo | 199 / 49 | 71 / 45 | 489 / 39 | 54 / 33 |
| mô tả A5 | 199 / 26 | 72 / 30 | 489 / 31 | 54 / 26 |
| chunk dạy | 199 / 260 | 71 / 270 | 489 / 299 | 54 / 292 |
| chunk định nghĩa thêm | 29 / 300 | 18 / 280 | 130 / 344 | 11 / 460 |
| khối tiên quyết | 190 / 120 | 67 / 140 | 403 / 142 | 36 / 198 |
| khối module | 199 / 85 | 72 / 105 | 489 / 89 | 54 / 89 |
| cạnh mở 5 kiểu | 144 / 50 | 59 / 67 | 403 / 66 | 40 / 71 |
| hình/bảng xác nhận | 15 / 49 | 5 / 48 | 0 | 3 / 55 |
| chunk bài tập | 44 / 276 | 11 / 257 | 19 / 148 | 0 |
| khái niệm học sau | 146 / 80 | 53 / 97 | 310 / 95 | 29 / 90 |

Bốn điều rút ra:
- **Ngữ cảnh rất ngắn.** Ngay cả cách lắp đầy đủ B5 cũng chỉ có trung vị 470–850 token và p90 550–1.550 token; ca lớn nhất khoảng
  3.000 token (xstk, doc-4). Các thí nghiệm "lost in the middle" dùng ngữ cảnh dài gấp nhiều lần (mục 3.1). Với bài giảng, vấn đề chính
  là **nhiễu và chọn lọc**, không phải độ dài.
- **Cả lời gọi vẫn dưới ngưỡng cache ngầm 4.096 token.** Cộng chỉ dẫn và lược đồ (ước 1.000–1.500 token, mục 4.7), lời gọi trung vị chỉ
  khoảng 2.000 token. Cache ngầm của Gemini vì vậy gần như không giúp bài giảng, giống kết luận cho pass phụ.
- **Đồ thị làm ngữ cảnh tăng khoảng 2,5–3 lần** so với chỉ chunk dạy (doc-1: 275 → 728 token trung vị; doc-4: 315 → 831). Phần tăng
  lớn nhất là chunk định nghĩa thêm và khối tiên quyết.
- **Mã định danh chunk rất đắt khi mô hình phải chép lại.** Một `chunk_id` dạng `c_` + 24 ký tự hex tốn 25 token Gemma; nhãn ngắn `[S3]`
  chỉ tốn 4. Mười câu trích bằng `chunk_id` thêm khoảng 250 token ra, tức khoảng 0,0004 USD mỗi bài, và dễ chép sai. Mục 4.3 đề xuất
  nhãn nguồn ngắn, mã ánh xạ về `chunk_id`.

### 2.4 Công thức bị mất ở sách toán

Bảng sau đo các chỗ `[formula]` (công thức đứng riêng bị thay bằng chuỗi cố định) trên ba cuốn có công thức:

| | doc-1 | xstk-ch3-1 | naive-bayes |
|---|---:|---:|---:|
| chunk có `[formula]` | 159/199 | 84/126 | 17/40 |
| số chỗ `[formula]` | 562 | 263 | 32 |
| khái niệm có `[formula]` trong câu neo | 80/199 (40%) | 18/72 (25%) | 8/20 |
| khái niệm có `[formula]` trong chunk dạy | 161/199 (81%) | 36/72 (50%) | 17/20 |
| khái niệm có `[formula]` trong chunk định nghĩa thêm | 22 | 16 | 7 |
| số `[formula]` trong chunk dạy, mỗi khái niệm (trung vị / p90) | 2 / 6 | 0,5 / 6 | 1 / 4 |
| khái niệm có ≥ 3 công thức trong chunk dạy | 92/199 | 14/72 | 6/20 |
| chunk dạy (khác nhau) có `[formula]` | 78/94 | 19/34 | 9/12 |
| công thức có chữ gốc `raw_text` và `bbox`, `page` trong cây parse | 562/562 | 263/263 | 32/32 |
| `raw_text` chứa ký tự vùng riêng (PUA, U+E000–U+F8FF) | 142 (25%) | 11 (4%) | 1 (3%) |
| token Gemma của `raw_text` (trung vị mỗi công thức) | 41 | 21 | 22 |
| số trang có công thức | 91 | 50 | 17 |

Chữ gốc vẫn còn. Mỗi chỗ `[formula]` trong chunk có một mục `formula_refs` (vị trí ký tự, `formula_id`). `formula_id` trỏ tới nút
`formula` trong `artifacts/parse_tree/<doc>/v<N>/tree.json`, và nút này giữ `raw_text` (chữ `orig` của PDF), `page` và `bbox`. Khớp
được 562/562 (doc-1), 263/263 (xstk), 32/32 (naive-bayes). Chất lượng chữ gốc không đều, như các ví dụ sau:
- Đọc được, ở công thức một dòng của doc-1: `A ∪ B = { x | x ∈ A hoặc x ∈ B } .`
- Mất cấu trúc hai chiều, ở ma trận của doc-1: dấu ngoặc ma trận thành ký tự PUA, chỉ số dưới bị dàn phẳng thành `a 11 a 12 · · · a`.
- Mất phân số, ở naive-bayes: `P(AB) P(A|B)= P(B)` lẽ ra là P(A|B) = P(AB)/P(B).
- Toán tử tách khỏi toán hạng, ở xstk: `2 2 2 2 1 2 ( ) ( ) ... ( ) n x s − + − + + − =` lẽ ra là công thức phương sai mẫu; ví dụ này
  cũng được nêu trong [spec công thức B0](../doc/B0-symbol-va-cong-thuc-spec.md).

Hệ quả cho bài giảng: ở doc-1, 81% khái niệm có chunk dạy bị khuyết công thức, và 40% khái niệm có câu neo, tức câu định nghĩa, chứa
chỗ khuyết. Mô hình đọc `[formula]` sẽ phải đoán công thức, nghĩa là sinh nội dung ngoài tài liệu. Phương án xử lý ở mục 4.6.

---

## 3. Văn liệu theo nhóm

Mức đọc của từng nguồn ghi ở mục 8. Số liệu dưới đây đều lấy từ chính bài (toàn văn hoặc tóm tắt), không qua công cụ tóm tắt web.

### 3.1 Độ dài, vị trí và nhiễu của ngữ cảnh

Ba kết quả dưới đây quyết định cách lắp ngữ cảnh:
- **Vị trí.** Liu và cộng sự đặt đoạn chứa đáp án ở các vị trí khác nhau trong 10, 20, 30 đoạn (khoảng 2K, 4K, 6K token) và thấy đường
  hình chữ U: mô hình dùng tốt thông tin ở đầu và cuối, kém ở giữa. GPT-3.5-Turbo có thể giảm hơn 20 điểm; ca xấu nhất còn thấp hơn khi
  không có tài liệu nào (closed-book 56,1%). Ở QA miền mở, thêm quá 20 đoạn chỉ tăng 1,5% (GPT-3.5) và 1% (Claude-1.3) trong khi tốn thêm
  độ trễ và tiền. Đặt câu hỏi cả trước và sau dữ liệu giúp gần tuyệt đối ở bài khoá–giá trị, nhưng gần như không đổi xu hướng ở QA nhiều
  tài liệu ([TACL 2024](https://aclanthology.org/2024.tacl-1.9/)).
- **Nhiễu.** Shi và cộng sự thêm một câu không liên quan vào bài toán (GSM-IC): dưới 30% bài gốc còn được giải nhất quán; câu nhiễu cùng
  chủ đề, trùng tên vai và số trong khoảng hợp lý là loại gây hại nhất. Thêm chỉ dẫn "có thể bỏ qua thông tin không liên quan", hoặc ví dụ mẫu
  có câu nhiễu, giúp giảm hại ([ICML 2023](https://arxiv.org/abs/2302.00093)). ALCE quan sát cùng hiện tượng: mô hình đọc tài liệu "dễ bị
  phân tán bởi đoạn không liên quan" ([EMNLP 2023](https://aclanthology.org/2023.emnlp-main.398/)).
- **Kết nối bịa giữa các mẩu thông tin.** Biên tập viên Wikipedia chấm bài của STORM thấy lỗi kiểm chứng chủ yếu là "red herring" và suy
  diễn quá đà: bài nối những mẩu thông tin không có liên hệ đã kiểm chứng ([NAACL 2024](https://aclanthology.org/2024.naacl-long.347/)).

*Suy luận:* ngữ cảnh bài giảng chỉ 500–1.500 token (mục 2.3), ngắn hơn nhiều so với các thí nghiệm vị trí, nên vị trí là mối lo thứ yếu.
Mối lo chính là nhiễu *cùng chủ đề*: khái niệm kề trong module, khái niệm cùng chunk, cạnh mở, khái niệm học sau đều đúng là loại câu nhiễu
"in-topic, trùng tên" gây hại nhất theo Shi. Vì vậy mỗi khối ngữ cảnh phải được dán nhãn vai trò ("chỉ để liên hệ, không giảng") và có hạn
mức. Lỗi kiểu STORM là rủi ro thật với cạnh đồ thị sai: mô hình dễ viết "X dùng để làm Y" từ một cạnh `uses` chưa kiểm.

**Lắp tất định so với truy hồi.** Đề cương chọn truy hồi lai và hướng kết hợp đồ thị với LLM của TutorQA [18] và GraphRAG [23]. Với bài
giảng thì khác: Pha A đã tính sẵn và đã kiểm "đoạn nào dạy khái niệm này" (câu neo, chunk dạy, chunk định nghĩa, câu trích của cạnh). Truy
hồi chỉ tìm lại cái đã biết, cộng thêm nguy cơ kéo về đoạn cùng chủ đề nhưng không đúng (nhiễu kiểu Shi). *Suy luận:* bài giảng nên lắp
tất định từ cấu trúc; truy hồi chỉ là nhánh dự phòng cho khái niệm thiếu chunk dạy (xstk có 1 ca), và là việc của trợ lý hỏi đáp. Không
tìm thấy nghiên cứu so trực tiếp hai cách cho bài giảng; ablation ở mục 6 sẽ đo.

### 3.2 Khoa học học tập

Bảng sau tóm các nguồn sư phạm và điều rút ra cho bài giảng:

| nguồn | bằng chứng | áp cho bài giảng |
|---|---|---|
| Merrill 2002, *First principles of instruction* ([ETR&D 50(3)](https://doi.org/10.1007/BF02505024)) | Tổng hợp các lý thuyết thiết kế dạy học, không phải thí nghiệm. Năm nguyên tắc: vấn đề thực, kích hoạt, minh hoạ, áp dụng, tích hợp. Kích hoạt gồm gợi lại kinh nghiệm cũ và **cung cấp cấu trúc** để tổ chức kiến thức mới. Minh hoạ khái niệm bằng **ví dụ và phản ví dụ**, so sánh nhiều minh hoạ. Câu hỏi "nhớ lại điều đã được kể" ít tác dụng. Chủ đề gây hứng thú nhưng không liên quan có thể gây hại, tăng tải nhận thức. | Phần "nhắc khái niệm nền" (kích hoạt) đặt đầu bài; phần ví dụ ưu tiên ví dụ và phản ví dụ của sách; câu tự kiểm tra không chỉ là nhớ lại định nghĩa. |
| Ausubel 1960 ([J. Educ. Psych. 51(5)](https://doi.org/10.1037/h0046669)); [1] trong đề cương | Đưa trước các khái niệm bao trùm (advance organizer) giúp học và nhớ tài liệu lạ, vì cấu trúc nhận thức tổ chức theo tầng. | Tên module và vị trí của khái niệm trong module là "khung" ngắn mở bài. |
| Atkinson, Derry, Renkl, Wortham 2000 ([RER 70(2)](https://doi.org/10.3102/00346543070002181)) | Ví dụ có lời giải hiệu quả ở giai đoạn đầu học kỹ năng; ví dụ tốt có thành phần tích hợp, **đánh dấu hoặc chia bước**; nhiều ví dụ cho mỗi loại bài; đặt ví dụ sát bài luyện tương ứng; khuyến khích tự giải thích. | Nếu sách có ví dụ hoặc bài tập liên quan (22% khái niệm ở doc-1), đưa ví dụ có lời giải chia bước, trích từ sách. |
| Dunlosky và cộng sự 2013 ([PSPI 14(1)](https://doi.org/10.1177/1529100612453266)) | Practice testing và distributed practice: hữu dụng cao. Tóm tắt, tô sáng, đọc lại: hữu dụng thấp. | Bài giảng chỉ là tóm tắt có cấu trúc, tự nó ít giá trị; nên kèm câu tự kiểm tra (nối với quiz, không thay quiz). |
| Roediger & Karpicke 2006 ([Psych. Science 17(3)](https://doi.org/10.1111/j.1467-9280.2006.01693.x)) | Sau 5 phút, học lại tốt hơn kiểm tra; sau 2 ngày và 1 tuần, kiểm tra nhớ tốt hơn hẳn, dù học lại làm người học tự tin hơn. | Câu tự kiểm tra cuối bài là phần rẻ nhất có bằng chứng. Người học phải trả lời trước khi thấy đáp án. |
| Mayer & Moreno 2003 ([Educ. Psychologist 38(1)](https://doi.org/10.1207/s15326985ep3801_6)) | Bằng chứng từ hoạt hình có lời thuyết minh. Segmenting: chia bài thành đoạn nhỏ người học tự chuyển. Pretraining: cho biết trước tên và đặc điểm các thành phần. Weeding (coherence): bỏ phần thú vị nhưng thừa. Signaling: gắn tín hiệu chỉ cách xử lý tài liệu. | Chia bài thành phần ngắn có tiêu đề; nhắc tên khái niệm nền trước (giống pretraining); không chèn chuyện bên lề; in đậm thuật ngữ. Chuyển từ hoạt hình sang văn bản là suy luận. |
| Alfieri, Nokes-Malach, Schunn 2013 ([Educ. Psychologist 48(2)](https://doi.org/10.1080/00461520.2013.775712)); Schwartz & Bransford 1998 ([Cogn. Instr. 16(4)](https://doi.org/10.1207/s1532690xci1604_4)) | Phân tích gộp 57 thí nghiệm, 336 phép thử: so sánh ca cho kết quả học tốt hơn học từng ca hay học truyền thống, d = 0,50 (KTC 95% 0,44–0,56). Tốt hơn khi yêu cầu tìm điểm giống, nêu nguyên lý sau khi so, kiểm tra ngay. | Cạnh `contrasts_with` và `subtype_of` có bằng chứng thì làm phần "phân biệt với" ngắn. |
| Kalyuga, Ayres, Chandler, Sweller 2003 ([Educ. Psychologist 38(1)](https://doi.org/10.1207/s15326985ep3801_4)) | Kỹ thuật hiệu quả với người mới có thể mất tác dụng, thậm chí gây hại, với người đã giỏi (expertise reversal). | Một bài chung cho mọi người học (mô hình hoá trình độ ngoài phạm vi) nên cho phép **gập** phần nhắc nền và ví dụ. |

*Suy luận:* các nguyên tắc này đến từ dạy học có người thiết kế; không nguồn nào đo bài giảng do LLM viết. Chúng là căn cứ chọn khung, còn
giá trị thật phải đo bằng người (mục 6).

### 3.3 Trích dẫn và kiểm trung thực

Bảng sau gom các cách trích dẫn và kiểm, chỉ phần áp cho bài giảng (tổng quan dùng chung ở báo cáo trợ lý hỏi đáp):

| nguồn | cách làm | số liệu chính | áp cho bài giảng |
|---|---|---|---|
| ALCE ([EMNLP 2023](https://aclanthology.org/2023.emnlp-main.398/)) | Mô hình trích `[1][2]` theo từng câu, tối đa 3 trích dẫn mỗi câu. **Citation recall** của câu = 1 khi ghép các đoạn được trích thì kéo theo (NLI) câu đó. Một trích dẫn **không liên quan** khi riêng nó không đỡ câu và bỏ nó đi thì các trích dẫn còn lại vẫn đỡ; **citation precision** là tỉ lệ trích dẫn không bị như vậy. | Trên ELI5, mô hình tốt nhất vẫn thiếu đỡ trọn ở khoảng 50% câu. Sinh trước rồi gắn trích dẫn sau (POSTCITE) có citation recall thấp hơn trích trong lúc sinh 47% trên ASQA. Kappa người–ALCE: 0,698 (recall), 0,525 (precision). Chép nguyên đoạn top-1 được điểm trích dẫn gần tuyệt đối nhưng kém trôi chảy và thiếu ý. | Trích ngay trong lúc sinh, theo từng ý, bằng nhãn ngắn. Độ đo trích dẫn phải đi kèm độ đo giá trị sư phạm, vì mốc trích câu (V11) đạt trích dẫn hoàn hảo một cách hiển nhiên. |
| Liu, Zhang, Liang ([Findings EMNLP 2023](https://aclanthology.org/2023.findings-emnlp.467/)) | Chấm người bốn máy tìm kiếm sinh. | Trung bình 51,5% câu được trích dẫn đỡ trọn; 74,5% trích dẫn đỡ câu của nó. | Không tin trích dẫn của mô hình nếu không kiểm. |
| RARR ([ACL 2023](https://aclanthology.org/2023.acl-long.910/)) | Sau khi sinh: tìm bằng chứng, rồi sửa tối thiểu phần không được đỡ. | Tăng attribution mà giữ văn bản gốc nhiều hơn các mô hình sửa trước. | Ứng viên cho bước sửa lỗi khi kiểm hỏng, nhưng tốn thêm lời gọi; ưu tiên loại hoặc đánh dấu câu hỏng. |
| FActScore ([EMNLP 2023](https://aclanthology.org/2023.emnlp-main.741/)) | Tách văn bản thành sự kiện nguyên tử, tính tỉ lệ được nguồn đỡ. | ChatGPT 58% khi viết tiểu sử; bộ ước tự động sai dưới 2% so với điểm người. | Chấm người theo ý nguyên tử chính xác hơn chấm cả câu. |
| RAGAS [28] ([EACL 2024 demo](https://aclanthology.org/2024.eacl-demo.16/)) | Faithfulness: tách câu trả lời thành mệnh đề rồi hỏi LLM mệnh đề nào suy ra được từ ngữ cảnh. | (chưa đối chiếu trang tài liệu hiện hành) | Độ đo của đề cương; dùng được cho bài giảng với ngữ cảnh = các chunk đã nạp. Phải cấu hình sang Gemini. |
| Chain-of-Verification ([Findings ACL 2024](https://aclanthology.org/2024.findings-acl.212/)) | Nháp → lập câu hỏi kiểm → trả lời độc lập → viết lại. | Giảm ảo giác trên nhiều tác vụ. | Gấp 2–4 lần lời gọi; không hợp đường bấm-chờ. Chỉ dùng như bộ chấm offline. |
| AIS, Rashkin và cộng sự ([Computational Linguistics 49(4)](https://doi.org/10.1162/coli_a_00486)) | Khung "quy được cho nguồn đã nêu": câu đúng *chỉ dựa trên* nguồn. | — | Định nghĩa nhãn cho người chấm. |

Dự án đã có hai hợp đồng gần với nhu cầu:
- **Hợp đồng câu trích của A8** (`_source_quote` trong `src/doc2roadmap/domain/prerequisites.py`): câu `quote` phải tìm được nguyên văn
  (chuẩn hoá khoảng trắng) trong chunk được khai báo, không thì cạnh bị loại.
- **Hợp đồng mô tả A5** (`validate_description` trong `src/doc2roadmap/domain/canonical_decisions.py`): mỗi phần tử đúng một câu, có
  `chunk_ids` khác rỗng và nằm trong tập được phép, đúng ngôn ngữ tài liệu. Hợp đồng này kiểm *tính hợp lệ* của trích dẫn, chưa kiểm câu
  có được đoạn trích đỡ hay không.

### 3.4 LLM làm giám khảo

Zheng và cộng sự ([NeurIPS 2023 Datasets and Benchmarks](https://arxiv.org/abs/2306.05685)) đo ba thiên lệch:
- **Vị trí:** khi đảo thứ tự hai câu trả lời gần giống nhau, GPT-4 chỉ nhất quán 65,0%, GPT-3.5 46,2%, Claude-v1 23,8%. Cách giảm bảo
  thủ: chấm hai lần đổi chỗ, chỉ tính thắng khi thắng cả hai, lệch thì tính hoà. Ví dụ mẫu (few-shot) nâng độ nhất quán của GPT-4 lên
  77,5% nhưng làm lời gọi đắt gấp 4.
- **Độ dài:** với đòn "danh sách lặp" (viết lại danh sách rồi chèn thêm, không thêm thông tin), Claude-v1 và GPT-3.5 bị lừa 91,3%, GPT-4
  8,7%.
- **Chấm toán kém:** GPT-4 nhận sai đáp án sai là đúng ở 14/20 ca; có lời giải tham chiếu thì còn 3/20.
- GPT-4 đồng ý với người 85% (không tính hoà), cao hơn mức đồng ý giữa người với người (81%).

Wang và cộng sự cho thấy chỉ đổi thứ tự là đủ để Vicuna-13B "thắng" ChatGPT 66/80 câu khi ChatGPT làm giám khảo
([ACL 2024](https://aclanthology.org/2024.acl-long.511/)).

*Suy luận cho dự án:* giám khảo là `gemini-3.1-flash-lite`, yếu hơn GPT-4 nhiều, nên thiên lệch có thể lớn hơn các số trên. Giám khảo LLM
chỉ dùng để sàng và làm nhãn bạc; kết luận cuối do người chấm. Sách toán thì giám khảo phải có tham chiếu (chunk nguồn kèm công thức).

### 3.5 LLM sinh nội dung giảng dạy và giải thích

Bảng sau gom các bài thực nghiệm đã kiểm:

| nguồn | thiết lập | kết quả | áp cho dự án |
|---|---|---|---|
| MacNeil và cộng sự ([SIGCSE 2023](https://doi.org/10.1145/3545945.3569785)) | Giải thích mã do GPT-3 và Codex sinh, gắn vào e-book; người học bấm nút để xem; ba kiểu: từng dòng, danh sách khái niệm, tóm tắt. | 58/116 sinh viên có xem; 42,1% xem ở đoạn mã đầu rồi tụt còn khoảng 10%; chương khó lên 32–39%. Kiểu từng dòng được xem nhiều nhất (58,5%, có thể do nút nằm bên trái) nhưng bị chấm ít hữu ích nhất; tóm tắt được ưa hơn. Codex hay lạc đề; few-shot làm câu trả lời bắt chước khuôn quá mức. | Đúng mô hình "bấm mới sinh": phần lớn khái niệm có thể không ai bấm, nên sinh lười là hợp lý. Ưu tiên bài ngắn có cấu trúc. |
| Leinonen và cộng sự ([ITiCSE 2023](https://doi.org/10.1145/3587102.3588785)) | So giải thích mã của sinh viên và của LLM trong lớp khoảng 1.000 người. | Giải thích của LLM được chấm dễ hiểu hơn và tóm tắt chính xác hơn có ý nghĩa thống kê. | LLM viết giải thích đủ tốt cho người mới; chỉ đọc tóm tắt. |
| Shao và cộng sự, STORM ([NAACL 2024](https://aclanthology.org/2024.naacl-long.347/)) | Viết bài kiểu Wikipedia: nghiên cứu theo nhiều góc nhìn, lập dàn ý, rồi viết từng mục có trích dẫn từ tài liệu tìm được. | So với RAG theo dàn ý: tốt hơn 25 điểm % về tổ chức, 10 điểm % về độ phủ. Citation recall 84,83%, precision 85,18% (Mistral 7B chấm). Câu không được đỡ chủ yếu do suy diễn sai và diễn đạt lại thiếu chính xác, không phải bịa nội dung. 20 cặp bài, mỗi cặp 2 biên tập viên. | Dàn ý cố định trước (ở đây là khung bài giảng) giúp tổ chức. Lỗi chính cần bắt là suy diễn và nối sai, không phải bịa từ đầu. |
| Kasneci và cộng sự [14] ([Learn. Indiv. Differ. 103](https://doi.org/10.1016/j.lindif.2023.102274)) | Bài quan điểm về cơ hội và thách thức của LLM trong giáo dục. | Không có thí nghiệm. | Dẫn như bối cảnh, không dẫn như bằng chứng hiệu quả. |
| Bastani và cộng sự ([PNAS 122(26), 2025](https://doi.org/10.1073/pnas.2422633122)) | Thực nghiệm thực địa gần 1.000 học sinh trung học học toán, hai trợ lý GPT-4: giao diện ChatGPT thường (GPT Base) và có rào chắn sư phạm (GPT Tutor). | Có trợ lý khi luyện: điểm tăng 48% (Base) và 127% (Tutor). Khi bỏ trợ lý: nhóm Base kém hơn nhóm chưa từng dùng 17%; Tutor gần như triệt tiêu tác hại. Có bản đính chính ([PNAS 122(34)](https://doi.org/10.1073/pnas.2518204122)), chưa đọc nội dung đính chính. | Thiết kế quyết định tác động học. Bài giảng nên đòi người học tự trả lời câu tự kiểm tra trước khi xem đáp án. |

Không tìm thấy nghiên cứu nào đo bài giảng LLM sinh theo khái niệm từ đồ thị tiên quyết trên người học; mục 6 vì vậy đo chất lượng văn bản,
không đo hiệu quả học (đề cương đặt hiệu quả học ngoài phạm vi).

### 3.6 Tài liệu chính thức của Gemini (đọc 2026-10-11)

Bảng sau ghi các điều tài liệu chính thức nói, kèm hệ quả:

| chủ đề | tài liệu nói | hệ quả |
|---|---|---|
| Stream structured output | Trang [Structured outputs (generateContent)](https://ai.google.dev/gemini-api/docs/generate-content/structured-output), cập nhật 2026-10-09: "The streamed chunks will be valid partial JSON strings, which can be concatenated to form the final, complete JSON object." Đầu ra theo đúng thứ tự khoá trong schema (Gemini 3). Chỉ bảo đảm đúng cú pháp, không bảo đảm đúng nghĩa. Không liệt kê `minLength`, `maxLength`, `pattern`; mô hình bỏ qua thuộc tính không hỗ trợ. 3.1 Flash-Lite có hỗ trợ. | Stream được JSON, nhưng mỗi mẩu là JSON dở; máy chủ phải parse dần. Xếp khoá theo thứ tự hiển thị để mục nào đóng xong thì hiện mục đó. Giới hạn độ dài phải kiểm bằng mã. |
| Stream văn bản | Trang [Text generation](https://ai.google.dev/gemini-api/docs/generate-content/text-generation), cập nhật 2026-10-09: stream "lets you display partial results immediately". Không có số độ trễ hay TTFT. | Giây chờ phải đo. |
| Nhiệt độ | Cùng trang: Google "strongly recommend" giữ tham số mặc định với Gemini 3.x; đặt temperature dưới 1.0 có thể gây "looping or degraded performance", nhất là bài toán và suy luận. | Quyết định temperature 0 có rủi ro lặp, đặc biệt ở sách toán. Phải đo tỉ lệ lặp và cắt cụt; xem mục 7. |
| Mô hình | Trang [3.1 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite): "low-latency, cost-effective"; vào tối đa 1.048.576 token, ra 65.536; hỗ trợ structured output, cache, thinking, Batch. Không có số TTFT hay token/giây. | Không có số chính thức về tốc độ. |
| Token ảnh | Trang [Media resolution](https://ai.google.dev/gemini-api/docs/media-resolution), cập nhật 2026-09-23, cho Gemini 3: ảnh mặc định 1.120 token; `low` 280, `medium` 560, `high` 1.120, `ultra_high` 2.240. PDF mặc định 560 token/trang; các mức đặt rõ cộng thêm chữ gốc của PDF. Trang không ghi riêng Flash-Lite. Trang [Tokens](https://ai.google.dev/gemini-api/docs/generate-content/tokens) vẫn ghi quy tắc cũ 258 token/ảnh ≤ 384 px. | Ảnh vùng công thức tốn 280–1.120 token mỗi ảnh; phải đo bằng `countTokens`. |

---

## 4. Thiết kế khuyến nghị

Nguyên tắc chung: phần nào làm được bằng mã thì không giao cho LLM. Câu định nghĩa nguyên văn, danh sách tiên quyết kèm câu trích, vị trí
trong module, tên khái niệm học sau đều có sẵn trong `graph.json`; mã dựng chúng ngay lúc bấm, 0 USD, không chờ. LLM chỉ viết phần diễn
giải, ví dụ, phân biệt và câu tự kiểm tra, và mọi ý của LLM phải trỏ về nguồn đã nạp.

### 4.1 Lắp ngữ cảnh

Khuyến nghị dùng cách lắp B4 cộng một chunk bài tập (gần B5), có hạn mức từng khối. Mỗi khối có nhãn nguồn ngắn; mã giữ bảng ánh xạ nhãn →
`chunk_id`, vị trí ký tự, trang. Bảng sau ghi các khối theo thứ tự trong prompt:

| thứ tự | khối | nội dung | nhãn | hạn mức (token Gemma) | ghi chú |
|---|---|---|---|---|---|
| 0 | chỉ dẫn hệ thống | vai trò, khung bài, luật trích dẫn, luật công thức, "có thể bỏ qua thông tin không liên quan" (Shi 2023) | — | khoảng 1.000–1.500 kể cả lược đồ (ước) | cố định, chung mọi lời gọi |
| 1 | thẻ khái niệm | `display_name`, alias, tên và số thứ tự module, vị trí k/n trong module | — | khoảng 50 | |
| 2 | câu định nghĩa | `anchor.sentence`, ghi rõ "nằm trong S1" | trỏ S1 | 40–110 (trung vị) | lặp lại một câu đã có trong S1 để làm tín hiệu |
| 3 | chunk dạy | chữ chunk, `[formula]` thay theo mục 4.6 | S1 | 300 (trung vị) | bắt buộc |
| 4 | chunk định nghĩa thêm | tối đa 2 chunk | S2, S3 | tối đa 600 mỗi chunk | có ở 15–55% khái niệm |
| 5 | tiên quyết hiển thị | tối đa 3: tên, câu neo của tiên quyết (nguyên văn, có thể trích), câu `quote` của cạnh, ghi chú thứ tự sách (`order_relation`) | N1–N3 (câu neo), Q1–Q3 (câu trích cạnh) | khoảng 120–200 | ghi rõ "quan hệ do hệ thống suy ra, có thể sai" |
| 6 | phân biệt, liên hệ | tối đa 3 cạnh mở `contrasts_with`, `subtype_of`, `example_of`, `component_of`, `uses`, kèm câu bằng chứng nguyên văn | R1–R3 | khoảng 70 | ghi "đề xuất chưa kiểm, chỉ dùng khi bằng chứng nói rõ"; không nạp cạnh `requires` của `open_edges` |
| 7 | hình, bảng đã xác nhận | chú thích, `media_id` | H1… | khoảng 50 | web hiện ảnh; mô hình chỉ được nhắc "xem Hình…" |
| 8 | bài tập | tối đa 1 chunk `bai_tap` có nhắc đúng tên, gần chunk dạy nhất | B1 | tối đa 500 | có ở 0–22% khái niệm |
| 9 | học để làm gì | tối đa 3 khái niệm học sau theo `requires`: tên, số module | — | khoảng 30 | chỉ tên; không nạp mô tả để giảm nhiễu cùng chủ đề |
| 10 | nhắc nhiệm vụ | 2–3 câu nhắc khung và luật trích | — | khoảng 80 | đặt nhiệm vụ ở cuối như Google khuyên cho ngữ cảnh dài |

Lý do của thứ tự và hạn mức:
- **Khối cốt lõi đứng đầu** (định nghĩa, chunk dạy), khối liên hệ đứng sau, nhiệm vụ nhắc lại ở cuối: hợp với kết quả vị trí của Liu, dù ngữ
  cảnh ngắn nên tác động nhỏ.
- **Khối liên hệ có trần cứng và nhãn vai trò**, vì đây là loại nhiễu cùng chủ đề gây hại nhất (Shi) và là nơi đồ thị có cạnh sai.
- **Tiên quyết dùng câu neo, không dùng mô tả A5.** Câu neo là nguyên văn trong chunk dạy của tiên quyết nên kiểm được bằng mã; mô tả A5
  là diễn đạt lại, không kiểm nguyên văn được.
- **Nhãn ngắn** (S1, N2, Q1…) thay cho `chunk_id`: 4 token thay vì 25, và mô hình không phải chép chuỗi hex.

Ngân sách: trần mềm 2.500 token Gemma cho phần ngữ cảnh. Theo số đo, p90 của B5 là 554–1.549 token và lớn nhất 3.051 token (xstk), nên trần
chỉ chạm vài khái niệm. Khi vượt, bỏ dần theo thứ tự: bài tập → học để làm gì → cạnh mở → chunk định nghĩa thứ hai → cắt đuôi chunk định
nghĩa thứ nhất. Không bao giờ cắt chunk dạy và câu định nghĩa.

Ba nhánh cho ca thiếu nguồn:
- Thiếu chunk dạy (xstk 1 ca): dùng chunk định nghĩa nếu có. Không có thì không gọi LLM; trang hiện "tài liệu chưa có đoạn giảng khái
  niệm này" kèm các đoạn có nhắc tên (từ `mention_map`), cho người học hỏi trợ lý.
- Mô tả A5 là bản nháp chưa kiểm (`draft_fallback_invalid`, 5 khái niệm): không nạp mô tả.
- Nhiều khái niệm cùng một chunk dạy (trung bình 1,5–2,1): thẻ khái niệm và câu định nghĩa nói rõ đây là khái niệm nào; chỉ dẫn yêu cầu
  "chỉ giảng khái niệm này; khái niệm khác trong đoạn chỉ nhắc tên".

### 4.2 Khung bài giảng

Bài giảng có bảy phần. Ba phần do mã dựng, bốn phần do LLM viết. Độ dài tính bằng âm tiết tiếng Việt (1 âm tiết ≈ 1,2–1,3 token Gemma):

| phần | ai làm | nội dung | độ dài | trích nguồn | căn cứ |
|---|---|---|---|---|---|
| 1. Bạn đang ở đâu | mã | module n: tên module (từ khâu tên module), khái niệm thứ k/m, khái niệm trước và sau | 1–2 dòng | không cần (dữ liệu cấu trúc) | advance organizer (Ausubel), signaling (Mayer) |
| 2. Kiến thức nền | mã dựng danh sách, LLM viết mỗi mục một câu nhắc | mỗi tiên quyết hiển thị: một câu nhắc nghĩa (trích N), một câu "vì sao cần" dựa trên câu trích cạnh (trích Q). Mã gắn ghi chú thứ tự: "đã học ở module m", "cùng module, ngay trước", hoặc "sách trình bày ở phần sau" khi cạnh ngược thứ tự | tối đa 3 mục, mỗi mục ≤ 40 âm tiết | bắt buộc | kích hoạt (Merrill), pretraining (Mayer) |
| 3. Định nghĩa | mã | câu neo nguyên văn, kèm trang | 1 câu | nguyên văn, tự có | — |
| 4. Giải thích | LLM | diễn giải định nghĩa theo từng ý, nêu điều kiện, thành phần, tính chất có trong S1–S3 | 3–6 ý, tổng ≤ 150 âm tiết | bắt buộc, từng ý | demonstration (Merrill), segmenting (Mayer) |
| 5. Ví dụ | LLM | ví dụ hoặc bài tập có lời giải *trong tài liệu*, trình bày theo bước; nếu tài liệu không có ví dụ thì bỏ phần này | 0–1 ví dụ, ≤ 120 âm tiết | bắt buộc | worked examples (Atkinson) |
| 6. Phân biệt và liên hệ | LLM | 0–2 mục từ cạnh mở có bằng chứng (ví dụ, phản ví dụ, loại con, đối lập); một dòng "học để làm gì" do mã dựng từ tên khái niệm học sau | ≤ 60 âm tiết | bắt buộc cho mục LLM | contrasting cases (Alfieri), ví dụ và phản ví dụ (Merrill) |
| 7. Tự kiểm tra | LLM | 1 câu hỏi, đáp án ẩn, người học trả lời trước rồi mới mở. Ưu tiên câu phân loại ví dụ/phản ví dụ, điền khuyết vào câu định nghĩa, đúng/sai có giải thích; tránh câu chỉ nhắc lại định nghĩa | 1 câu | đáp án bắt buộc trích | testing effect (Roediger & Karpicke, Dunlosky); Bastani 2025 |

Tổng phần LLM viết khoảng 250–400 âm tiết, tức khoảng 300–500 token chữ; cộng khoá JSON, nhãn và câu trích, đầu ra khoảng 700–1.100 token.
Bài ngắn theo hai lý do: người học ưa tóm tắt hơn giải thích dài (MacNeil 2023), và tài liệu nguồn chỉ có 1–3 chunk.

Phần 2 và 5 có thể gập lại (mặc định mở với khái niệm đầu module, gập với khái niệm sau) để giảm hiệu ứng đảo chiều chuyên môn (Kalyuga 2003)
khi không mô hình hoá trình độ. Câu tự kiểm tra là phần thêm của bài giảng; quiz của module là việc của
[báo cáo quiz](nghien-cuu-quiz-tu-kiem-tra-2026-10-11.md), hai bên nên dùng chung lược đồ câu hỏi nếu báo cáo đó chốt lược đồ.

**Ví dụ ngoài sách.** *Suy luận:* bản đầu nên **tắt**. Lý do: đề cương ghi "chỉ trong phạm vi tài liệu"; lỗi chính của STORM là nối sai
giữa các mẩu thông tin; và Merrill cảnh báo chủ đề không liên quan gây hại. Nếu chủ dự án muốn bật (ví dụ cho sách triết học không có ví
dụ), dùng bốn điều kiện:
- trường `outside_document: true`, web hiện trong khung riêng có nhãn "Ví dụ minh hoạ, không có trong tài liệu";
- tối đa 1 ví dụ mỗi bài, không chứa số liệu, định nghĩa hay khẳng định mới về khái niệm;
- vẫn phải trỏ về câu định nghĩa mà nó minh hoạ (trích S1);
- đo riêng tỉ lệ ví dụ sai hoặc gây hiểu lầm trong lượt chấm người; vượt 5% thì tắt.

### 4.3 Lược đồ JSON đầu ra

Lược đồ dưới đây là đầu ra của LLM, khoá xếp theo thứ tự hiển thị để stream được (mục 3.6). Mỗi `item` là một ý; `sources` là nhãn
ngắn; `quote` là đoạn nguyên văn ngắn trong nguồn đầu tiên, dùng để mã kiểm và để web tô sáng:

```json
{
  "prereq_notes": [
    {"prereq": "N1", "text": "…", "sources": ["N1", "Q1"], "quote": "…"}
  ],
  "explanation": [
    {"text": "…", "sources": ["S1"], "quote": "…"}
  ],
  "example": [
    {"text": "…", "sources": ["B1"], "quote": "…", "outside_document": false}
  ],
  "contrasts": [
    {"relation": "R2", "text": "…", "sources": ["R2", "S1"], "quote": "…"}
  ],
  "self_check": {
    "kind": "phan_loai | dien_khuyet | dung_sai",
    "question": "…",
    "answer": "…",
    "sources": ["S1"],
    "quote": "…"
  },
  "gaps": ["…"]
}
```

Ghi chú lược đồ:
- `gaps` là chỗ mô hình ghi điều tài liệu không nói (ví dụ "đoạn nguồn không có ví dụ"), thay vì tự bịa. Web không hiện `gaps`; nhóm dùng
  để soát chất lượng.
- `minItems`/`maxItems` có trong danh sách hỗ trợ; độ dài chuỗi và mẫu chuỗi thì không (mục 3.6), nên mã kiểm.
- Không có trường văn bản tự do ngoài các mục trên; phần 1, 3 và dòng "học để làm gì" do mã dựng.

### 4.4 Luật kiểm bằng mã

Bảng sau ghi các luật, chạy sau khi stream xong, tổng thời gian dưới 50 ms (*suy luận*, xử lý chuỗi trên vài nghìn ký tự):

| # | luật | khi hỏng | lấy từ |
|---|---|---|---|
| K1 | JSON đúng lược đồ; số mục trong giới hạn | sinh lại 1 lần, rồi về mốc trích câu | — |
| K2 | mọi nhãn trong `sources` thuộc tập nhãn đã nạp; `prereq` là N có thật; `relation` là R có thật | bỏ ý | hợp đồng A5 |
| K3 | `quote` khác rỗng, ≤ 200 ký tự, tìm được nguyên văn (NFC, chuẩn hoá khoảng trắng) trong chữ của nguồn đầu tiên trong `sources` | bỏ ý | hợp đồng câu trích A8, `quote_is_verbatim` |
| K4 | độ phủ từ: tỉ lệ âm tiết nội dung của `text` có mặt trong các nguồn được trích ≥ ngưỡng (đặt từ dữ liệu ở lượt thử; âm tiết chức năng nhận bằng tần suất trong chính cuốn sách, không bằng danh sách từ viết tay) | gắn cờ "cần soát", vẫn hiện | ý của luật 1 ở báo cáo tên module |
| K5 | không có ký hiệu toán, chữ số hay biến mới không có trong nguồn được trích (kể cả `raw_text` công thức) | bỏ ý | chống bịa công thức (mục 4.6) |
| K6 | không lặp: không có n-gram 8 âm tiết lặp ≥ 3 lần; `finishReason` không phải cắt vì hết token | sinh lại 1 lần với giới hạn chặt hơn | rủi ro nhiệt độ 0 (mục 3.6) |
| K7 | `outside_document` phải `false` khi tính năng tắt; khi bật thì ≤ 1 và vẫn trích S1 | bỏ ý | mục 4.2 |
| K8 | phần giải thích còn ≥ 2 ý sau khi bỏ | nếu không, sinh lại 1 lần kèm danh sách lỗi; vẫn hỏng thì dùng mốc trích câu (V11) và đánh dấu | — |
| K9 | đáp án câu tự kiểm tra qua K2, K3 | bỏ câu tự kiểm tra | — |

K3 kiểm *có trích đúng chỗ*, chưa kiểm câu diễn giải có được đoạn đỡ hay không. Phần đó chỉ kiểm được bằng NLI hoặc LLM. *Suy luận:* không
đặt lời gọi kiểm NLI trên đường bấm-chờ (gấp đôi chi phí và giây chờ); dùng nó offline trong đánh giá (citation recall/precision kiểu ALCE)
và cho một mẫu bài đã cache, để biết K3–K5 bắt được bao nhiêu lỗi.

**Trình bày tiên quyết khi đồ thị có cạnh sai.** Bốn quy tắc:
- Mã, không phải LLM, quyết định danh sách tiên quyết và câu dẫn. Câu dẫn mặc định: "Định nghĩa này dùng tới các khái niệm sau", không phải
  "Bạn phải học trước".
- Mỗi tiên quyết hiện kèm câu trích `quote` (nút "vì sao?"), đúng câu đã kiểm nguyên văn ở A8.
- Cạnh ngược thứ tự sách hiện "sách trình bày ở phần sau", không viết "đã học".
- Chỉ dẫn LLM cấm suy ra quan hệ mới giữa các khái niệm ngoài câu bằng chứng (lỗi "red herring" của STORM); K2 chặn nhắc tiên quyết không có
  trong danh sách. Nút "báo sai quan hệ này" ghi phản hồi để A13 xem (đặc tả có A13, chưa làm).

### 4.5 Vận hành và cache

**Khoá cache.** Quyết định đã chốt khoá theo (khái niệm, phiên bản đồ thị, prompt). Khuyến nghị cụ thể hoá như sau:

```
lecture_key = sha256(doc_id, node_id, context_hash, prompt_hash, schema_hash, model_id, generation_config, contract_version)
context_hash = sha256(JSON chuẩn hoá của toàn bộ khối 1–10 sau khi lắp, gồm chữ chunk và câu trích)
```

Lý do dùng `context_hash` thay cho số phiên bản đồ thị:
- Đổi phiên bản đồ thị mà ngữ cảnh của khái niệm không đổi (ví dụ chỉ sửa module khác) thì không phải sinh lại.
- Ngữ cảnh đổi (chunk sửa chữ, tiên quyết đổi, tên module đổi) thì khoá tự đổi; không cần danh sách vô hiệu hoá viết tay.
- `graph_version` vẫn lưu cạnh bài giảng làm siêu dữ liệu, để biết bài sinh từ bản nào và để xoá hàng loạt khi cần.
- `node_id` là băm định danh; nếu A4/A10 đổi danh tính khái niệm thì `node_id` đổi và cache trượt, đúng như mong muốn.
- Khoá cũng có `model_id`: khi chuyển sang `gemini-3.5-flash-lite` (bản 3.1 tắt sớm nhất 2027-05-07) thì bài sinh lại dần theo lượt bấm.

**Chống sinh trùng.** Hai người bấm cùng lúc một khái niệm chưa có bài: khoá theo `lecture_key` (single-flight); người đến sau nghe cùng
luồng stream hoặc chờ bản đã kiểm. Không lưu bản lỗi vào cache; ghi "cache âm" 60 giây để không gọi dồn khi API đang lỗi.

**Stream và kiểm.** Tài liệu cho phép stream structured output dưới dạng JSON dở ghép dần (mục 3.6). Luồng khuyến nghị:
1. Khi bấm: mã trả ngay phần 1, 2 (danh sách tiên quyết và câu trích), 3 (câu định nghĩa) và hình đã xác nhận. Phần này không chờ LLM.
2. Gọi LLM có stream; máy chủ parse JSON dở, mỗi khi một `item` đóng xong thì chạy K2, K3, K5 cho riêng nó (các luật cục bộ) rồi mới đẩy
   cho web. Ý hỏng không bao giờ hiện ra.
3. Hết stream: chạy K1, K4, K6–K9 cho toàn bài; nếu phải bỏ ý hoặc sinh lại thì gửi bản cuối thay bản tạm. Chỉ bản cuối vào cache.

*Suy luận:* kiểm từng ý trước khi hiện tránh được cảnh người học đọc một câu rồi câu đó biến mất. Cái giá là ý hiện theo cụm thay vì theo
từng chữ. Phương án sinh văn bản thường có thẻ `[S1]` rồi kiểm sau cũng được, nhưng phải tự tách câu và thẻ; JSON stream đơn giản hơn với
mã kiểm.

**Khi kiểm phát hiện lỗi:** bỏ ý (K2, K3, K5, K7); gắn cờ "cần soát" mà vẫn hiện (K4); sinh lại một lần (K1, K6, K8). Nếu vẫn hỏng thì hiện
bản trích câu (mốc V11) với dòng "Bài giảng tóm tắt từ đoạn nguồn" và ghi vào nhật ký. Không hiện thông báo kỹ thuật cho người học.

**Tải trước.** Khi người học mở khái niệm k, xếp hàng sinh khái niệm k+1 trong dãy học (một lời gọi, khoảng 0,002 USD) nếu chưa có trong
cache. Chỉ tải trước một bước để chi phí lãng phí bị chặn. Tuỳ chọn mạnh hơn, cần chủ dự án quyết: khi tải tài liệu lên, sinh trước toàn bộ
bằng Batch hoặc Flex (rẻ 50%, nhưng Flex có độ trễ mục tiêu 1–15 phút và Batch tới 24 giờ theo
[nghiên cứu Gemini v4](nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md)).

**Lỗi và thử lại.** 429 và 503: thử lại tối đa 2 lần, lùi theo hàm mũ có nhiễu; timeout mỗi lời gọi 30 giây (*suy luận*, phải chỉnh theo số
đo p99). Developer API không tính tiền lời gọi lỗi 400/500 nhưng vẫn tính vào hạn mức; phản hồi 200 sai nghĩa vẫn bị tính đủ
([nghiên cứu Gemini v4](nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md)).

**Nhiệt độ.** Quyết định là 0. Tài liệu Gemini 3 khuyên giữ mặc định và cảnh báo lặp khi thấp hơn 1.0 (mục 3.6); báo cáo tên module cũng ghi
cùng rủi ro. Vì bài đã cache nên tính tái lập không cần nhiệt độ 0. Khuyến nghị: giữ 0 như đã chốt, nhưng K6 đo tỉ lệ lặp và cắt cụt, và lượt
thử có một nhánh nhiệt độ mặc định để so (mục 6).

### 4.6 Xử lý công thức

Bảng sau so bốn phương án phía Pha B (A1 đang tạm dừng nên chỉ nêu phương án chờ A1). Chi phí tính trên doc-1: trung vị 2, p90 6 công thức
trong chunk dạy mỗi khái niệm; 161/199 khái niệm có công thức:

| phương án | cách làm | USD thêm mỗi bài | USD thêm cho doc-1 nếu bấm hết | ưu | nhược |
|---|---|---|---|---|---|
| F0. Không làm gì | giữ `[formula]`, cấm mô hình viết công thức | 0 | 0 | rẻ, không bịa | 81% bài thiếu công thức; "giải thích" mất nội dung chính |
| F1. Chữ gốc `raw_text` | thay `[formula]` bằng `⟦CTk: raw_text⟧`, ghi "chữ thô có thể sai cấu trúc, không chép lại thành công thức" | trung vị +82 token vào (2 × 41), khoảng +0,00002 | khoảng 0,003 | có sẵn 562/562, 0 hạ tầng | 25% có ký tự PUA; phân số, ma trận, chỉ số bị dàn phẳng; mô hình có thể "dựng lại" sai |
| F2. Ảnh vùng công thức cho mô hình | cắt ảnh theo `page` + `bbox` từ PDF gốc, gửi kèm (đa phương thức) | 2 ảnh × 280 (`low`) đến 1.120 token (mặc định) = +560 đến +2.240 token, tức +0,00014 đến +0,00056; p90 6 ảnh đến +0,0017 | khoảng 0,02–0,09 | mô hình đọc được công thức thật | cần giữ PDF gốc và dịch vụ cắt ảnh; số token ảnh của Flash-Lite phải đo; LaTeX mô hình viết ra không kiểm nguyên văn được |
| F3. Chờ A1 | CodeFormulaV2 sinh LaTeX ở khâu đọc PDF | 0 ở Pha B | 0 | sạch nhất | A1 đang dừng; theo [nghiên cứu A1](nghien-cuu-v4-a1-docling-2026-10-04.md) mục 2 cũng phải đổi adapter và chạy lại các khâu sau |

Khuyến nghị (*suy luận*, phải đo ở mục 6): kết hợp hiển thị ảnh gốc với F1, bật F2 chỉ khi lượt thử cho thấy F1 không đủ:
- **Web hiện ảnh gốc của công thức** cắt theo `page` + `bbox`, đúng chỗ `[formula]` trong câu định nghĩa và đoạn trích. Phần này không cần
  LLM và trung thực tuyệt đối vì là pixel của sách.
- **LLM nhận `raw_text` (F1) và chỉ được nhắc công thức bằng nhãn** `[CTk]`. Web thay nhãn bằng ảnh gốc. LLM không tự viết công thức;
  K5 bỏ ý có ký hiệu toán không có trong nguồn.
- **F2 là nhánh thí nghiệm** cho khái niệm có công thức trong câu định nghĩa (80/199 ở doc-1, 18/72 ở xstk). Chỉ bật khi chấm người cho
  thấy giải thích tốt hơn rõ mà không có công thức bịa.

### 4.7 USD và giây chờ

Giả định token, ghi rõ đâu là đo, đâu là ước:
- Ngữ cảnh (đo, token Gemma): trung vị 470–850, p90 550–1.550 (B4–B5).
- Chỉ dẫn và lược đồ (ước): 1.000–1.500.
- Đầu ra (ước): 700–1.100 token, trần `maxOutputTokens` 2.048.
- Token Gemini có thể lệch token Gemma; phải đo bằng `countTokens` (mục 6).

Bảng sau tính USD với giá `gemini-3.1-flash-lite` Standard (0,25 / 1,50 USD cho 1 triệu token vào / ra):

| kịch bản | token vào | token ra | USD/bài | doc-1 (199 khái niệm) | doc-4 (489) | sáu cuốn (846) |
|---|---:|---:|---:|---:|---:|---:|
| thấp | 1.600 | 600 | 0,0013 | 0,26 | 0,64 | 1,10 |
| giữa | 2.100 | 900 | 0,0019 | 0,37 | 0,92 | 1,59 |
| cao (p90) | 3.000 | 1.300 | 0,0027 | 0,54 | 1,32 | 2,28 |
| ca xấu nhất | 4.500 | 2.048 | 0,0042 | — | — | — |

Ghi chú cho bảng:
- **Token ra chiếm khoảng 70% tiền** ở kịch bản giữa. Đòn bẩy chi phí là độ dài bài và nhãn ngắn, không phải cắt ngữ cảnh.
- Cộng khoảng 10% cho sinh lại (K1, K6, K8) và tải trước bị bỏ phí (*ước*).
- Với `gemini-3.5-flash-lite` (0,30 / 2,50), kịch bản giữa thành khoảng 0,0029 USD/bài (+53%).
- Batch hoặc Flex: bằng nửa, nếu chủ dự án chọn sinh trước.
- Cache ngầm gần như không giúp vì lời gọi dưới 4.096 token (mục 2.3).
- So với Pha A: pass phụ doc-4 theo giá v3 khoảng 46 USD; sinh hết bài giảng của doc-4 khoảng 1 USD, dưới 3% chi phí dựng đồ thị.
- Công thức theo F2 thêm 0,02–0,09 USD cho doc-1.

**Giây chờ.** Không có số chính thức về TTFT hay token/giây của 3.1 Flash-Lite (mục 3.6), nên **phải đo**. Công thức ước:
`T_hết_bài ≈ T_hàng_đợi + TTFT + N_ra / v`, còn ý đầu tiên hiện sau khoảng `TTFT + N_ý_đầu / v` (ý đầu khoảng 100–150 token kể cả khoá JSON
và câu trích). Bảng dưới chỉ minh hoạ độ nhạy với **giá trị giả định**, không phải số đo:

| TTFT giả định | tốc độ giả định | ý đầu tiên | hết bài (900 token) |
|---:|---:|---:|---:|
| 0,5 giây | 300 token/giây | khoảng 1 giây | khoảng 3,5 giây |
| 1 giây | 200 token/giây | khoảng 1,6 giây | khoảng 5,5 giây |
| 2 giây | 100 token/giây | khoảng 3,3 giây | khoảng 11 giây |

Phần do mã dựng (vị trí, tiên quyết, định nghĩa, ảnh) hiện trong vài chục mili giây vì chỉ đọc dữ liệu (*suy luận*). Bài đã có trong cache
thì giây chờ chỉ là đọc cache. Tải trước khái niệm kế làm phần lớn lượt bấm theo thứ tự lộ trình trúng cache.

---

## 5. Hợp đồng dữ liệu JSON cho web

Mục này chỉ định nghĩa dữ liệu bài giảng mà web nhận; đường dẫn API, cách gọi và giao diện do nhóm web tự thiết kế. Mọi `chunk_id`,
`page`, `section_path` lấy từ artifact; web không cần đọc `graph.json`.

```json
{
  "contract_version": "lecture-1",
  "doc_id": "doc-1",
  "graph_version": "v9",
  "node_id": "node_…",
  "lecture_key": "sha256:…",
  "status": "ready",
  "generated_at": "2026-10-11T08:00:00Z",
  "model_id": "gemini-3.1-flash-lite",
  "position": {"module_id": "module_004", "module_index": 3, "module_title": "…", "index_in_module": 2, "count_in_module": 6,
               "previous_node_id": "node_…", "next_node_id": "node_…"},
  "concept": {"name": "…", "aliases": ["…"]},
  "definition": {"quote": "…", "chunk_id": "c_…", "char_start": 8876, "page": 10,
                 "formula_refs": [{"formula_id": "…", "page": 10, "bbox": [239.1, 330.9, 384.5, 312.7]}]},
  "prerequisites": [
    {"node_id": "node_…", "name": "…", "module_index": 2,
     "order_note": "module_truoc | cung_module_truoc | sach_trinh_bay_sau",
     "why": {"quote": "…", "chunk_id": "c_…", "page": 10},
     "note": {"text": "…", "citations": [{"chunk_id": "c_…", "quote": "…", "page": 9}], "check": "pass"}}
  ],
  "sections": [
    {"kind": "giai_thich | vi_du | phan_biet",
     "items": [{"text": "…", "citations": [{"chunk_id": "c_…", "quote": "…", "page": 10, "section_path": ["Chương 1", "1.1 Tập hợp"]}],
                "formula_labels": ["CT1"], "outside_document": false, "check": "pass | can_soat"}]}
  ],
  "formulas": {"CT1": {"formula_id": "…", "page": 10, "bbox": [239.1, 330.9, 384.5, 312.7]}},
  "media": [{"media_id": "…", "kind": "figure | table", "caption": "…"}],
  "used_later": [{"node_id": "node_…", "name": "…", "module_index": 7}],
  "self_check": {"kind": "phan_loai | dien_khuyet | dung_sai", "question": "…", "answer": "…",
                 "citations": [{"chunk_id": "c_…", "quote": "…", "page": 10}]},
  "warnings": ["thieu_cong_thuc", "ban_trich_cau", "khong_co_doan_day"],
  "usage": {"input_tokens": 2100, "output_tokens": 900, "usd": 0.0019, "ttft_ms": 0, "total_ms": 0, "regenerated": false}
}
```

Luật của hợp đồng:
- `status`: `ready` (đã kiểm, đã cache), `generating`, `fallback` (bản trích câu V11), `no_source` (không có đoạn dạy), `failed`.
- `bbox` theo hệ toạ độ của cây parse (điểm PDF, gốc dưới trái, như `artifacts/parse_tree/.../tree.json`); máy chủ cắt ảnh từ PDF gốc rồi
  web hiện ảnh tại vị trí nhãn `CTk` trong `text`.
- `check = can_soat` thì web vẫn hiện, có thể đánh dấu nhẹ; ý hỏng K2, K3, K5 không bao giờ có trong hợp đồng.
- `usage` để nhóm ghi USD và giây chờ cho báo cáo; web không hiện cho người học.
- Khi stream, máy chủ gửi ba loại sự kiện có cùng hình dạng con: `skeleton` (mọi trường do mã dựng, trước khi gọi LLM), `item` (một ý đã
  qua luật cục bộ, kèm `section_kind`), `final` (cả đối tượng trên). Web thay toàn bộ bằng `final` khi nhận được.

---

## 6. Giao thức thí nghiệm và đánh giá

### 6.1 Bước 0 USD (làm trước)

Bước này không gọi mô hình:
1. **Mã lắp ngữ cảnh** theo mục 4.1 cho cả 846 khái niệm của sáu cuốn; in phân bố token Gemma (đối chiếu với mục 2.3) và số ca chạm trần.
2. **Mốc không LLM theo V11** ([pipeline seminar](../doc/pipeline-seminar-chuan-V1-V13-v2.md), mục V11) cho mọi khái niệm: câu định nghĩa
   (câu neo), danh sách tiên quyết kèm câu trích, và 3–5 câu chọn bằng TextRank trong chunk dạy và chunk định nghĩa. Bản này trích dẫn đúng
   tuyệt đối theo cấu tạo, nên là mốc cho giá trị sư phạm, không phải cho trung thực (ALCE gọi đây là đường tắt).
3. **Kiểm thử luật K1–K9 trên đầu ra giả có lỗi cố ý** (nhãn lạ, câu trích không nguyên văn, công thức bịa, lặp, cắt cụt), để mỗi luật được
   thấy hỏng ít nhất một lần, theo mục 5 của AGENTS.md.
4. **Chọn mẫu 80 khái niệm**, phân tầng: doc-1 25, xstk-ch3-1 15, doc-4 25, nhap-mon-ml 10, naive-bayes và doc-6 5. Trong mỗi cuốn chia theo
   có/không công thức trong câu neo, có/không tiên quyết hiển thị, chung/riêng chunk dạy. Không dùng tài liệu tập giữ lại.
5. **Viết rubric, luật quyết định và dry-run chi phí** trước khi gọi mô hình.

### 6.2 Các nhánh so sánh

Bảng sau ghi các nhánh; mọi nhánh LLM dùng cùng khung và cùng luật kiểm:

| nhánh | ngữ cảnh | mục đích |
|---|---|---|
| A0 | không LLM: bản trích câu V11 | mốc không LLM |
| A1 | LLM, chỉ chunk dạy (B0) | ablation không đồ thị |
| A2 | LLM, lắp đầy đủ theo mục 4.1, công thức F1 | thiết kế khuyến nghị |
| A3 | A2 cộng ảnh công thức F2 (chỉ khái niệm có công thức trong câu neo, khoảng 30 bài) | phương án công thức |
| A4 | A2 với nhiệt độ mặc định (khoảng 40 bài) | rủi ro lặp ở nhiệt độ 0 |
| A5 | LLM không ngữ cảnh, chỉ tên khái niệm và tên module | mốc "hỏi LLM trực tiếp" của đề cương; đo mức bịa ngoài tài liệu |

### 6.3 Độ đo

Độ đo tự động (nhãn bạc):
- tỉ lệ ý bị luật K2, K3, K5 loại; tỉ lệ bài phải sinh lại, rơi về mốc, lặp, cắt cụt;
- citation recall và precision kiểu ALCE, dùng giám khảo `gemini-3.1-flash-lite` làm bộ NLI trên từng ý;
- RAGAS faithfulness [28] với ngữ cảnh là các nguồn đã nạp, cấu hình sang Gemini;
- USD, token vào/ra, TTFT, thời gian hết bài (p50, p95), ở song song 1 và 8.

Chấm người (kết luận cuối), theo bảng rubric:

| tiêu chí | thang | định nghĩa ngắn |
|---|---|---|
| Đúng | có/không lỗi sai sự thật, đếm số ý sai | so với tài liệu, không so với kiến thức ngoài |
| Trung thực | mỗi ý: được nguồn trích đỡ trọn / một phần / không (khung AIS) | cho citation recall và precision người |
| Giá trị sư phạm | 1–5 | có kích hoạt nền đúng chỗ, giải thích làm rõ hơn câu định nghĩa, ví dụ hoặc phân biệt có ích |
| Đọc được | 1–5 | mạch lạc, đúng tiếng Việt, không lặp |
| Độ dài | ngắn quá / vừa / dài quá | |

Cách chấm:
- **Chấm mù theo cặp:** A2 so A1 và A2 so A0 trên cùng khái niệm, thứ tự trái phải ngẫu nhiên, ẩn nhãn nhánh; người chấm chọn bài tốt hơn về
  giá trị sư phạm hoặc hoà. Trung thực chấm riêng từng bài theo ý.
- **Hai người chấm độc lập** trên cả 80 khái niệm; đo κ của Cohen [27] cho nhãn có/không lỗi và cho lựa chọn cặp; κ có trọng số cho thang
  1–5. Bất đồng giải quyết bằng thảo luận sau khi đã tính κ.
- **Cỡ mẫu:** kiểm định dấu hai phía, α = 0,05. Với 80 cặp không hoà, phát hiện được tỉ lệ ưa 70% với lực khoảng 0,94 (cần ≥ 50/80); với 60
  cặp lực khoảng 0,84 (cần ≥ 39/60); tỉ lệ ưa 65% thì 80 cặp chỉ có lực khoảng 0,72 (tự tính bằng phân phối nhị thức). Cặp hoà làm giảm cỡ
  mẫu hiệu dụng.
- **Công:** 80 × 2 so sánh × 2 người = 320 lượt; ước 3 phút mỗi lượt, khoảng 8 giờ mỗi người (*ước*).
- **Giám khảo LLM** chạy song song trên cùng cặp, mỗi cặp hai thứ tự, chỉ tính thắng khi thắng cả hai (Zheng 2023), có chunk nguồn làm tham
  chiếu; đo κ với người. Đạt κ ≥ 0,6 thì mới dùng giám khảo LLM cho các lần chỉnh prompt sau.

### 6.4 Luật quyết định (viết trước khi đo)

Sáu luật sau phải được chốt trước khi chạy:
1. **Chấp nhận A2** khi đồng thời: ý không được nguồn đỡ (người chấm) ≤ 5% sau luật kiểm; không có lỗi sai sự thật ở ≥ 95% bài; A2 thắng A1
   ở ≥ 60% cặp không hoà về giá trị sư phạm.
2. **Đồ thị không đáng giá** nếu A2 không thắng A1 có ý nghĩa thống kê: bỏ các khối 6, 8, 9; giữ khối tiên quyết (đề cương bắt buộc).
3. **LLM không đáng giá** nếu A2 không thắng A0 ở ≥ 60% cặp không hoà: dùng bản trích câu, LLM chỉ viết câu tự kiểm tra.
4. **Công thức:** bật F2 khi A3 hơn A2 ở giá trị sư phạm trên khái niệm có công thức và không có công thức bịa; nếu không thì giữ ảnh gốc + F1.
5. **Nhiệt độ:** nếu ở nhiệt độ 0 tỉ lệ lặp hoặc cắt cụt > 2% và A4 không kém A2 về trung thực, chuyển sang nhiệt độ mặc định.
6. **Giây chờ:** nếu p95 thời gian tới ý LLM đầu tiên > 8 giây, bật sinh trước theo module khi người học mở module.

### 6.5 Lượt có tiền nhỏ (chỉ dự toán, chưa chạy)

Bảng sau dự toán theo kịch bản giữa và cao của mục 4.7:

| việc | số lời gọi | USD |
|---|---:|---:|
| sinh A1, A2 trên 80 khái niệm | 160 | 0,30–0,43 |
| sinh A3 (30), A4 (40), A5 (80) | 150 | 0,25–0,40 |
| sinh lại do luật kiểm (khoảng 10%) | khoảng 30 | 0,06–0,08 |
| giám khảo cặp, hai thứ tự (khoảng 3.500 token vào, 300 ra mỗi lời gọi) | 320 | khoảng 0,42 |
| citation recall/precision và RAGAS trên khoảng 390 bài | khoảng 800–1.200 (*ước*, tuỳ số ý) | 0,6–1,0 |
| đo giây chờ: 30 khái niệm × 3 lần, song song 1 và 8 | 90–180 | 0,17–0,35 |
| `countTokens` cho 846 khái niệm | 846 | trang Tokens không nói giá, phải kiểm trước |
| **tổng** (chưa tính `countTokens`) | khoảng 1.550–2.050 | **khoảng 1,8–2,7** |

Đề xuất xin trần 5 USD cho lượt này, dry-run trước và chờ chủ dự án duyệt. Thời gian chạy ước dưới 15 phút ở song song 8 (*suy luận*, phụ
thuộc số đo giây chờ).

---

## 7. Rủi ro và câu hỏi cho chủ dự án

Bảng sau ghi các rủi ro chính:

| rủi ro | mức | cách giảm |
|---|---|---|
| Cạnh tiên quyết sai được trình bày như sự thật | cao (độ chính xác cạnh 0,58–0,64 trên tập giữ lại) | mã dựng danh sách, câu dẫn "định nghĩa dùng tới", hiện câu trích, nút báo sai |
| Diễn giải sai nhưng có trích dẫn đúng chỗ (K3 không bắt) | trung bình | đo bằng người và NLI offline; luật K4 gắn cờ |
| Công thức bịa ở sách toán | cao ở doc-1 (81% khái niệm thiếu công thức) | ảnh gốc + nhãn `[CTk]`, luật K5 |
| Lặp hoặc giảm chất lượng do nhiệt độ 0 với Gemini 3 | chưa biết | luật K6, nhánh A4 |
| Bài của các khái niệm cùng chunk dạy lặp nhau | trung bình (1,5–2,1 khái niệm/chunk) | thẻ khái niệm và câu định nghĩa riêng; người chấm ghi lặp |
| Số token và giây chờ thật khác ước | trung bình | `countTokens` và lượt đo ở mục 6 |
| Bản `gemini-3.1-flash-lite` tắt từ 2027-05-07 | chắc chắn xảy ra | `model_id` trong khoá cache; bản 3.5 đắt hơn khoảng 53% mỗi bài |
| Bài giảng thành "chỗ dựa" làm người học không tự học (Bastani 2025) | chưa đo được trong phạm vi đồ án | câu tự kiểm tra phải trả lời trước khi xem đáp án |

Câu hỏi cho chủ dự án:
1. Ví dụ ngoài sách: tắt ở bản đầu như khuyến nghị, hay bật có nhãn theo bốn điều kiện ở mục 4.2?
2. Có giữ PDF gốc trên máy chủ để cắt ảnh công thức không? Không giữ thì chỉ còn F0/F1.
3. Khoá cache theo `context_hash` thay vì số phiên bản đồ thị có được không?
4. Có sinh trước toàn bộ bằng Batch/Flex khi tải tài liệu (khoảng 0,5 USD cho doc-4) hay chỉ tải trước một bước như khuyến nghị?
5. Nhiệt độ: chấp nhận luật quyết định 5 (đổi sang mặc định nếu lặp > 2%) không?
6. Ai là hai người chấm, và có chấp nhận khoảng 8 giờ chấm mỗi người không?
7. Trần 5 USD cho lượt thử ở mục 6.5 có được duyệt không?

---

## 8. Nguồn

Nguồn ghi theo IEEE, kèm mức đọc ngày 2026-10-11. Số trong ngoặc vuông dạng [n] ở thân bài là số của danh mục đề cương.

Ngữ cảnh, nhiễu, trích dẫn và trung thực:
- [B1] N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, and P. Liang, "Lost in the middle: How language models use long contexts," *Trans. Assoc. Comput. Linguistics*, vol. 12, pp. 157–173, 2024. https://aclanthology.org/2024.tacl-1.9/ — *đọc toàn văn* (arXiv 2307.03172v3), các mục 2, 4, 5.
- [B2] F. Shi, X. Chen, K. Misra, N. Scales, D. Dohan, E. Chi, N. Schärli, and D. Zhou, "Large language models can be easily distracted by irrelevant context," in *Proc. 40th ICML*, PMLR 202, 2023. https://arxiv.org/abs/2302.00093 — *đọc toàn văn* phần mở đầu, kết quả và phân tích yếu tố.
- [B3] T. Gao, H. Yen, J. Yu, and D. Chen, "Enabling large language models to generate text with citations," in *Proc. EMNLP*, 2023, pp. 6465–6488. https://aclanthology.org/2023.emnlp-main.398/ — *đọc toàn văn* phần độ đo, kết quả, chấm người (bản văn bản do agent tên module tải).
- [B4] N. Liu, T. Zhang, and P. Liang, "Evaluating verifiability in generative search engines," in *Findings of EMNLP*, 2023, pp. 7001–7025. https://aclanthology.org/2023.findings-emnlp.467/ — *chỉ đọc tóm tắt*.
- [B5] L. Gao *et al.*, "RARR: Researching and revising what language models say, using language models," in *Proc. 61st ACL*, 2023, pp. 16477–16508. https://aclanthology.org/2023.acl-long.910/ — *chỉ đọc tóm tắt*.
- [B6] S. Min *et al.*, "FActScore: Fine-grained atomic evaluation of factual precision in long form text generation," in *Proc. EMNLP*, 2023, pp. 12076–12100. https://aclanthology.org/2023.emnlp-main.741/ — *chỉ đọc tóm tắt và phần mở đầu*.
- [B7] S. Dhuliawala *et al.*, "Chain-of-verification reduces hallucination in large language models," in *Findings of ACL*, 2024, pp. 3563–3578. https://aclanthology.org/2024.findings-acl.212/ — *chỉ đọc tóm tắt*.
- [28] S. Es, J. James, L. Espinosa-Anke, and S. Schockaert, "RAGAs: Automated evaluation of retrieval augmented generation," in *Proc. 18th EACL: System Demonstrations*, 2024, pp. 150–158. https://aclanthology.org/2024.eacl-demo.16/ — *chỉ kiểm siêu dữ liệu*; định nghĩa faithfulness ở mục 3.3 chưa đối chiếu trang tài liệu docs.ragas.io hiện hành (lượt đọc bị ngắt).
- [B8] H. Rashkin *et al.*, "Measuring attribution in natural language generation models," *Computational Linguistics*, vol. 49, no. 4, pp. 777–840, 2023. https://doi.org/10.1162/coli_a_00486 — *chỉ kiểm siêu dữ liệu*.
- [B9] Y. Shao, Y. Jiang, T. A. Kanell, P. Xu, O. Khattab, and M. S. Lam, "Assisting in writing Wikipedia-like articles from scratch with large language models," in *Proc. NAACL-HLT*, 2024, pp. 6252–6278. https://aclanthology.org/2024.naacl-long.347/ — *đọc toàn văn* phần phương pháp, kết quả, chấm người (arXiv 2402.14207v2).
- [23] D. Edge *et al.*, "From local to global: A graph RAG approach to query-focused summarization," arXiv:2404.16130, 2024; [18] R. Yang *et al.*, arXiv:2402.14293, 2024 — chỉ dẫn theo đề cương, không đọc lại trong lượt này.

LLM làm giám khảo:
- [B10] L. Zheng *et al.*, "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena," arXiv:2306.05685, 2023. https://arxiv.org/abs/2306.05685 — *đọc toàn văn* mục 3 và các bảng 2–4 (bản văn bản do agent tên module tải); nơi đăng NeurIPS 2023 (Datasets and Benchmarks) **chưa xác minh** trong lượt này.
- [B11] P. Wang *et al.*, "Large language models are not fair evaluators," in *Proc. 62nd ACL*, 2024, pp. 9440–9450. https://aclanthology.org/2024.acl-long.511/ — *chỉ đọc tóm tắt*.
- [27] J. Cohen, "A coefficient of agreement for nominal scales," *Educ. Psychol. Meas.*, vol. 20, no. 1, pp. 37–46, 1960 — theo đề cương.

Khoa học học tập:
- [B12] M. D. Merrill, "First principles of instruction," *Educ. Technol. Res. Dev.*, vol. 50, no. 3, pp. 43–59, 2002. https://doi.org/10.1007/BF02505024 — *đọc toàn văn* các phần nguyên tắc 1–5 (bản tác giả lưu trên Wayback Machine, đối chiếu siêu dữ liệu Crossref).
- [1] D. P. Ausubel, *Educational Psychology: A Cognitive View*, 1968 (đề cương); [B13] D. P. Ausubel, "The use of advance organizers in the learning and retention of meaningful verbal material," *J. Educ. Psychol.*, vol. 51, no. 5, pp. 267–272, 1960. https://doi.org/10.1037/h0046669 — *chỉ đọc tóm tắt* (OpenAlex, phần mục đích và giả thuyết).
- [B14] R. K. Atkinson, S. J. Derry, A. Renkl, and D. Wortham, "Learning from examples: Instructional principles from the worked examples research," *Rev. Educ. Res.*, vol. 70, no. 2, pp. 181–214, 2000. https://doi.org/10.3102/00346543070002181 — *chỉ đọc tóm tắt*.
- [B15] J. Dunlosky, K. A. Rawson, E. J. Marsh, M. J. Nathan, and D. T. Willingham, "Improving students' learning with effective learning techniques," *Psychol. Sci. Public Interest*, vol. 14, no. 1, pp. 4–58, 2013. https://doi.org/10.1177/1529100612453266 — *chỉ đọc tóm tắt* (tóm tắt dài, có đủ xếp hạng mười kỹ thuật).
- [B16] H. L. Roediger and J. D. Karpicke, "Test-enhanced learning: Taking memory tests improves long-term retention," *Psychol. Sci.*, vol. 17, no. 3, pp. 249–255, 2006. https://doi.org/10.1111/j.1467-9280.2006.01693.x — *chỉ đọc tóm tắt*.
- [B17] R. E. Mayer and R. Moreno, "Nine ways to reduce cognitive load in multimedia learning," *Educ. Psychol.*, vol. 38, no. 1, pp. 43–52, 2003. https://doi.org/10.1207/S15326985EP3801_6 — *đọc toàn văn Bảng 1 và mục loại quá tải 2–3* (bản lưu trên trang môn học của University of Kentucky); không dẫn cỡ hiệu ứng vì bảng tách chữ bị lệch cột.
- [B18] L. Alfieri, T. J. Nokes-Malach, and C. D. Schunn, "Learning through case comparisons: A meta-analytic review," *Educ. Psychol.*, vol. 48, no. 2, pp. 87–113, 2013. https://doi.org/10.1080/00461520.2013.775712 — *chỉ đọc tóm tắt*.
- [B19] D. L. Schwartz and J. D. Bransford, "A time for telling," *Cogn. Instr.*, vol. 16, no. 4, pp. 475–522, 1998. https://doi.org/10.1207/s1532690xci1604_4 — *chỉ kiểm siêu dữ liệu*.
- [B20] S. Kalyuga, P. Ayres, P. Chandler, and J. Sweller, "The expertise reversal effect," *Educ. Psychol.*, vol. 38, no. 1, pp. 23–31, 2003. https://doi.org/10.1207/S15326985EP3801_4 — *chỉ đọc tóm tắt*.

LLM sinh nội dung giảng dạy:
- [B21] S. MacNeil *et al.*, "Experiences from using code explanations generated by large language models in a web software development e-book," in *Proc. 54th ACM SIGCSE TS V.1*, 2023, pp. 931–937. https://doi.org/10.1145/3545945.3569785 — *đọc toàn văn* phần kết quả và thảo luận (arXiv 2211.02265v1).
- [B22] J. Leinonen *et al.*, "Comparing code explanations created by students and large language models," in *Proc. ITiCSE V.1*, 2023. https://doi.org/10.1145/3587102.3588785 — *chỉ đọc tóm tắt* (arXiv 2304.03938).
- [14] E. Kasneci *et al.*, "ChatGPT for good? On opportunities and challenges of large language models for education," *Learn. Individ. Differ.*, vol. 103, Art. no. 102274, 2023. https://doi.org/10.1016/j.lindif.2023.102274 — *chỉ kiểm siêu dữ liệu*.
- [B23] H. Bastani, O. Bastani, A. Sungu, H. Ge, Ö. Kabakcı, and R. Mariman, "Generative AI without guardrails can harm learning: Evidence from high school mathematics," *Proc. Natl. Acad. Sci. USA*, vol. 122, no. 26, Art. no. e2422633122, 2025. https://doi.org/10.1073/pnas.2422633122 — *chỉ đọc tóm tắt* (Europe PMC); có đính chính tại https://doi.org/10.1073/pnas.2518204122, chưa đọc nội dung đính chính.

Tài liệu chính thức Gemini (đọc 2026-10-11):
- [G1] Google, "Structured outputs" (generateContent), cập nhật 2026-10-09. https://ai.google.dev/gemini-api/docs/generate-content/structured-output
- [G2] Google, "Structured outputs" (Interactions API), cập nhật 2026-09-23. https://ai.google.dev/gemini-api/docs/structured-output
- [G3] Google, "Text generation", cập nhật 2026-10-09. https://ai.google.dev/gemini-api/docs/generate-content/text-generation
- [G4] Google, "Gemini 3.1 Flash-Lite", cập nhật 2026-07-21. https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite
- [G5] Google, "Media resolution", cập nhật 2026-09-23. https://ai.google.dev/gemini-api/docs/media-resolution
- [G6] Google, "Understand and count tokens", cập nhật 2026-09-04. https://ai.google.dev/gemini-api/docs/generate-content/tokens
- Giá, cache ngầm, Batch, Flex, ngày tắt mô hình: lấy từ [nghiên cứu Gemini v4](nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md), không đọc lại.

Tài liệu và mã nội bộ được dẫn:
- [Đề cương đồ án](../doanchuyennganh/decuong/de-cuong-do-an-chuyen-nganh.md); [spec-addendum](../doc/spec-addendum.md) (A11, A12, B1–B4);
  [pipeline seminar V1–V13](../doc/pipeline-seminar-chuan-V1-V13-v2.md) (V11); [spec công thức B0](../doc/B0-symbol-va-cong-thuc-spec.md).
- [Nghiên cứu A1 docling](nghien-cuu-v4-a1-docling-2026-10-04.md) mục 2; [kết quả tập giữ lại v3](ket-qua-tap-giu-lai-v3-2026-10-04.md);
  [nghiên cứu tên và mô tả module](nghien-cuu-ten-va-mo-ta-module-2026-10-11.md) mục 6.
- Mã: `src/doc2roadmap/domain/prerequisites.py` (`_source_quote`), `src/doc2roadmap/domain/provenance.py` (`quote_is_verbatim`),
  `src/doc2roadmap/domain/canonical_decisions.py` (`validate_description`), `src/doc2roadmap/infrastructure/text/tokenizer.py`.
- Artifact đã đọc: `graph.json`, `chunks.json` của sáu cuốn ở bảng bối cảnh; `artifacts/parse_tree/doc-1/v5`, `xstk-ch3-1/v2`,
  `naive-bayes/v1` (`tree.json`).
