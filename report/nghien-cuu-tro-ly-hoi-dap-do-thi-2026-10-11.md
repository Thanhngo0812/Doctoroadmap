# Nghiên cứu: trợ lý hỏi đáp dùng đồ thị tiên quyết (Pha B) — 2026-10-11

Báo cáo trả lời ba câu hỏi về trợ lý hỏi đáp của Pha B: nạp thông tin gì, vận hành agent ra sao, và đánh giá thế nào. Phạm vi là trợ lý của
B2 (`doc/spec-addendum.md` dòng 1052–1076) cộng các quyết định của chủ dự án ngày 2026-10-11: chỉ tìm trong tài liệu đã tải lên, không chặn
theo tiến độ, module đang mở là ngữ cảnh ưu tiên, mỗi lần một tài liệu, mô hình `gemini-3.1-flash-lite`, embedding `gemini-embedding-001`
768 chiều. Bài giảng theo khái niệm và quiz thuộc hai báo cáo khác cùng ngày, báo cáo này không làm lại.

**Cách làm.** Mọi nguồn được mở ngày 2026-10-11. Bài đọc toàn văn được tải PDF về thư mục tạm và đọc bằng `pdftotext`; trang tài liệu chính thức
(ai.google.dev, docs.ragas.io) và mã nguồn thư viện được đọc trực tiếp. Truy vấn tìm kiếm chỉ dùng từ khoá chung; không có tên khái niệm, nội
dung giáo trình hay dữ liệu dự án nào được gửi ra ngoài. Phần hiện trạng đo bằng script cục bộ chỉ đọc artifact của sáu cuốn được giao; thí
nghiệm tách từ chạy offline bằng underthesea và pyvi có sẵn trong `tmp/venv-ml`. Script nằm ở thư mục tạm của phiên, không đưa vào kho.

**Những gì không làm.** Không gọi Gemini, embedding hay API trả tiền nào; mọi con số USD và giây chờ là ước, ghi rõ cách tính. Không mở tập
giữ lại, tập khoá hay `khoa.jsonl`. Không viết spec, vé hay mã sản phẩm; không sửa tệp nào ngoài báo cáo này; không commit.

Báo cáo dùng các quy ước sau:
- Nhận định từ văn liệu có link ngay tại chỗ; tên đầy đủ, nơi đăng và mức đọc nằm ở mục [Nguồn](#7-nguồn). Mức đọc gồm *đọc toàn văn*,
  *đọc phần liên quan*, *chỉ đọc tóm tắt*, *chỉ kiểm siêu dữ liệu*, hoặc **chưa xác minh**.
- "Số đo dự án" dẫn về artifact trong repo. Đoạn mở đầu bằng *Suy luận:* là ý kiến của người viết, chưa có thí nghiệm.
- Token của chunk lấy từ trường `token_count` trong `chunks.json`, do tokenizer Gemma mà dự án dùng để cắt chunk đếm (`tokenizer_id`
  `google-gemma-sentencepiece-v1`). Gemini không có tokenizer offline, nên đây là số xấp xỉ.

---

## Tóm tắt

Chín ý chính của báo cáo:
1. **Kiến trúc nên là quy trình cố định có định tuyến bằng mã; agent chỉ là nhánh phụ, tối đa 2 vòng công cụ.** Mã liên kết câu hỏi với khái niệm,
   truy hồi lai, gọi sẵn công cụ đồ thị (không tốn tiền), rồi một lời gọi sinh có stream. Ước 0,0014 USD và 1,4 giây tới chữ đầu mỗi câu, so với
   0,0034 USD và 4,3 giây của agent ba lời gọi (mục 3.1, 3.9). Văn liệu ủng hộ: Adaptive-RAG giữ F1 của nhiều bước với 1,46 thay vì 3,33 lần thời
   gian ([NAACL 2024](https://aclanthology.org/2024.naacl-long.389/)); HippoRAG truy hồi một bước trên đồ thị đạt F1 48,1 so với 44,7 của IRCoT,
   rẻ hơn 10–30 lần ([NeurIPS 2024](https://arxiv.org/abs/2405.14831)).
2. **Trả lời câu "agent thường hỏi đáp trong một module đúng không":** văn liệu không có chuẩn bó trong một module. Đề xuất truy hồi trên cả tài
   liệu, xếp hạng ưu tiên module đang mở rồi tới module trước, gắn nhãn vị trí cho mọi đoạn; khái niệm ở module sau vẫn trả lời, kèm "học kỹ ở
   module N" do mã gắn (mục 3.1, 3.6).
3. **Hiện trạng đủ cho công cụ đồ thị, nhưng A12 phải làm thêm một việc.** Mọi liên kết Hasse là cạnh cứng có `quote` nguyên văn (100% ở sáu
   cuốn), nên công cụ "vì sao khái niệm đứng ở đây" có dữ liệu. Nhưng `chunk_module_map` chỉ phủ 28–63% chỉ mục; gán chunk còn lại theo chunk dạy
   đứng trước phủ 74–99% (mục 1.2, 1.5).
4. **Bảy công cụ, kết quả gọn** (mục 3.3): giữ năm công cụ B2 và thêm `why_here`, `path_to`. `path_to` phải gộp vì lộ trình p90 của doc-4 có
   47 module và 256 khái niệm. Cạnh mở kiểu `requires` (25 ở doc-4) không bao giờ trả cho người học. Media chỉ lấy cạnh `confirmed`, và còn chờ
   chủ dự án quyết vì spec A12 chặn media chưa gắn module.
5. **Liên kết khái niệm bằng khớp tên dài nhất trước, có luật độ hiếm.** Khớp tên tìm được chunk dạy ở 80–100% khái niệm; nhưng tên một âm tiết
   khớp sai nhiều ("chất" khớp 297/671 chunk doc-4, theo ranh giới từ chỉ 51). Tách từ không cải thiện BM25 trong proxy của báo cáo; cặp âm tiết
   liền kề tăng MRR@10 0,02–0,05 (mục 1.3, 1.4).
6. **Nhắc khái niệm nền do mã sinh từ đồ thị, theo vị trí module, tối đa một khối mỗi câu và không nhắc lại trong phiên** (mục 3.5). Không có mô
   hình người học nên luật này là đề xuất, phải để người học chấm "có ích hay phiền".
7. **Từ chối phải dựa vào mã, không chỉ lời dặn.** Văn liệu cho thấy mô hình lớn thường trả lời sai thay vì từ chối khi ngữ cảnh không đủ
   ([ICLR 2025](https://arxiv.org/abs/2411.06037)). Câu ngoài tài liệu bị chặn ở bước định tuyến (0 USD); câu trả lời không có nhãn trích dẫn hợp
   lệ bị đổi thành từ chối (mục 3.6, 3.7).
8. **Gemini: không dùng function calling ở nhánh chính.** Gemini 3 bắt buộc gửi lại thought signature khi gọi hàm; structured output kết hợp công
   cụ mới ở Preview cho 3.1 Pro và 3.8 Flash; flash-lite mặc định thinking `minimal`. Câu trả lời vì vậy là văn bản stream có nhãn `[S#]`, mã
   hậu kiểm (mục 2.9, 3.7).
9. **Đánh giá:** 330 lượt hỏi thuộc 8 loại, tạo bằng agentic rồi người duyệt 60 mục; mốc LLM không bằng chứng, RAG thuần, agent thuần và 9 ablation;
   RAGAS cấu hình Gemini (ragas 0.4.3) kèm độ khớp với người. RAGAS cho câu từ chối 0 điểm relevancy nên phải tách riêng. Có tám luật quyết định
   viết trước. Lượt 1 khoảng 8 USD, lượt 2 khoảng 20 USD, phải dry-run và được duyệt (mục 5).

---

## 1. Hiện trạng (số đo ngày 2026-10-11)

### 1.1 Cách đo

Có năm script đọc cục bộ, làm năm việc sau:
- `c_hien_trang.py` đọc `graph.json`, `chunks.json` và `retrieval.json` của sáu cuốn, rồi đếm phạm vi module của chunk, khớp tên và alias,
  tiên quyết Hasse có câu trích, cạnh mở, media và cỡ ngữ cảnh. Script cũng gọi hàm thuần `target_roadmap` cho từng khái niệm để đo cỡ kết
  quả "lộ trình tới mục tiêu"; hàm này không gọi mô hình.
- `d_bo_sung.py` đo tỉ lệ ký tự trên token Gemini thật từ 1.033 lời gọi `anchor` đã ghi trong `anchor_decision_log` (cộng chữ prompt và JSON
  đầu vào, chia cho `promptTokenCount`). Script cũng đo độ phủ module nếu gán chunk theo chunk dạy đứng trước, và tổ tiên theo cạnh cứng.
- `f_bm25.py` chạy thí nghiệm proxy về tách từ cho BM25 (mục 1.4).
- `g_lien_ket.py` so khớp tên theo ranh giới âm tiết với khớp theo ranh giới từ của underthesea.
- `h_toc_do.py` đo thời gian `HybridRetriever` của dự án trên chỉ mục thật, với vector truy vấn lấy từ một chunk có sẵn (không gọi embedding).

### 1.2 Truy hồi: chỉ mục có sẵn, nhưng chưa lọc được theo module

Mã truy hồi ở `src/doc2roadmap/domain/retrieval.py` là `HybridRetriever`, gồm các phần sau:
- BM25 với k1 = 1,5 và b = 0,75. Token tách theo khoảng trắng sau chuẩn hoá NFC và casefold, tức theo âm tiết với tiếng Việt.
- Dense: cosine giữa vector truy vấn và vector chunk.
- Hợp hai nhánh bằng RRF với k = 60; mỗi nhánh xếp hạng toàn bộ chỉ mục rồi mới hợp.
- Quét O(N) trong bộ nhớ. Tham số `allowed_stage_ids` đã có, nhưng chưa dùng được vì `stage_id` rỗng.

Vector chunk được embed từ chuỗi "đường dẫn mục + chữ chunk" với task type `RETRIEVAL_DOCUMENT` (`index_document.py`). Câu hỏi của người học
vì vậy phải embed bằng task type phía truy vấn; mục 2.9 ghi task type mà tài liệu Gemini khuyên.

Bảng 1 cho thấy chỉ mục của sáu cuốn và phạm vi module của chunk:

| tài liệu | chunk trong chỉ mục | `stage_id` rỗng | chunk có trong `chunk_module_map` | phủ nếu gán theo chunk dạy đứng trước | token/chunk trung vị, p90 | tổng token chỉ mục | chunk có `[formula]` |
|---|---:|---:|---:|---:|---|---:|---:|
| doc-1 | 199 | 199 | 94 (47%) | 190 (95%) | 260, 302 | 43.781 | 159 |
| nhap-mon-ml | 41 | 41 | 26 (63%) | 36 (88%) | 261, 338 | 8.932 | 1 |
| naive-bayes | 40 | 40 | 12 (30%) | 38 (95%) | 102, 340 | 5.783 | 17 |
| doc-6 | 27 | 27 | 8 (30%) | 20 (74%) | 43, 154 | 1.507 | 0 |
| xstk-ch3-1 | 126 | 126 | 35 (28%) | 125 (99%) | 264, 316 | 30.393 | 84 |
| doc-4 | 671 | 671 | 286 (43%) | 667 (99%) | 262, 401 | 151.585 | 0 |

Bảng 1 cho bốn điểm chính:
- **A12 chưa làm.** Mọi mục của chỉ mục có `stage_id` rỗng. Trang và `section_id` thì đủ ở mọi chunk, nên trích dẫn trang và mục làm được
  ngay.
- **`chunk_module_map` chỉ phủ chunk dạy, tức 28–63% chỉ mục.** Phần còn lại gồm chunk nội dung không dạy khái niệm nào (doc-4 có 354 chunk
  như vậy), chunk bài tập (doc-1 37, xstk 21) và chunk đề cương (xstk 47, trong đó có các mục "Cách giải" bị gán nhầm vai). Nếu A12 chỉ chép
  `chunk_module_map` sang chỉ mục thì phép lọc theo module sẽ bỏ hơn một nửa sách. Gán chunk còn lại theo chunk dạy gần nhất đứng trước phủ
  được 74–99%; phần sót là chunk đứng trước chunk dạy đầu tiên, như trang hành chính hay lời mở đầu.
- **Cả cuốn đã nhỏ.** Tổng chỉ mục từ 1.507 tới 151.585 token, nên với bốn cuốn nhỏ, cả tài liệu vừa trong một lời gọi. Mục 3.9 tính lựa chọn
  "nhồi cả tài liệu" như một mốc so sánh.
- **Sách toán thiếu công thức.** doc-1 có 159/199 chunk chứa `[formula]`, xstk 84/126. Câu trả lời về công thức sẽ thiếu dữ kiện, và trợ lý
  phải nói rõ điều đó thay vì tự điền công thức (mục 3.6).

Tỉ lệ ký tự trên token Gemini thật, đo trên 1.033 lời gọi `anchor` của sáu cuốn, có trung vị 3,26 (p10 2,98, p90 3,39). Quy ước "3 ký tự/token"
của dự án vì vậy hơi dư, tức an toàn khi dự toán. Tokenizer Gemma đếm chunk ở mức 2,5–3,7 ký tự/token; sách toán đếm dày hơn.

### 1.3 Tên và alias: khớp chuỗi dùng được, nhưng cần khớp dài nhất và chặn tên một âm tiết

Bảng 2 cho thấy tên và alias của khái niệm học được, khớp theo ranh giới âm tiết trên chữ chunk đã chuẩn hoá:

| tài liệu | khái niệm | có alias | tên bề mặt | tên trùng giữa ≥ 2 khái niệm | tên nằm trọn trong tên dài hơn | tên có trong chunk dạy | số chunk một khái niệm khớp: trung vị / p90 / max | số khái niệm được gọi tên trong một chunk: trung vị / p90 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| doc-1 | 199 | 47 | 255 | 1 | 54 | 177 (89%) | 2 / 15 / 89 | 6 / 11 |
| nhap-mon-ml | 54 | 38 | 108 | 0 | 16 | 53 (98%) | 2 / 10 / 28 | 6 / 10 |
| naive-bayes | 20 | 10 | 34 | 1 | 8 | 16 (80%) | 3 / 9 / 10 | 1 / 5 |
| doc-6 | 12 | 9 | 26 | 0 | 5 | 12 (100%) | 2 / 15 / 18 | 2 / 4 |
| xstk-ch3-1 | 72 | 9 | 81 | 0 | 20 | 67 (93%) | 3,5 / 19 / 95 | 4 / 8 |
| doc-4 | 489 | 98 | 617 | 4 | 116 | 454 (93%) | 3 / 41 / 311 | 12 / 21 |

Bảng 2 cho bốn điểm chính:
- **Khớp tên tìm được chunk dạy ở 80–100% khái niệm.** Liên kết câu hỏi với khái niệm bằng khớp chuỗi vì vậy là bước đầu rẻ và tốt; embedding
  mô tả chỉ cần cho câu hỏi không gọi tên.
- **Tên lồng nhau nhiều.** doc-4 có 116/617 tên nằm trọn trong một tên dài hơn, doc-1 có 54/255. Phải khớp tên dài nhất trước, rồi mới xét tên
  ngắn nằm trong nó.
- **Tên trùng có thật nhưng ít.** doc-1 có hai khái niệm cùng hiện "Định lý 6"; doc-4 có bốn tên trùng ("Brahman", "khoa học", "phép biện
  chứng", "tâm lý xã hội"). `target_roadmap` hiện báo lỗi khi một tên khớp nhiều khái niệm; trợ lý thì phải hỏi lại hoặc trả cả hai.
- **Một chunk gọi tên nhiều khái niệm.** Trung vị 6 ở doc-1 và 12 ở doc-4. Mở rộng đồ thị từ mọi khái niệm có trong chunk truy hồi được sẽ
  phình rất nhanh; phải mở rộng từ khái niệm mà câu hỏi nhắm tới.

Bảng 3 cho thấy tên chỉ có một âm tiết hay một từ là nguồn khớp sai lớn nhất:

| tài liệu | số tên một âm tiết | chunk khớp theo âm tiết | chunk khớp theo từ (underthesea) | ví dụ: theo âm tiết → theo từ |
|---|---:|---:|---:|---|
| doc-1 | 17 | 251 | 119 | "hợp" 46 → 1; "hiệu" 33 → 2 |
| nhap-mon-ml | 27 | 95 | 80 | "học" 28 → 22 |
| xstk-ch3-1 | 1 | 95 | 93 | "mẫu" 95 → 93 |
| doc-4 | 28 | 1.238 | 189 | "chất" 297 → 51; "độ" 161 → 4; "vô" 102 → 3 |

*Suy luận:* "chất" khớp 297/671 chunk của doc-4 vì nó nằm trong "vật chất", "bản chất", "tính chất". Tách từ loại được phần lớn các khớp này,
nhưng là thành phần riêng của tiếng Việt. Cách rẻ hơn, không phụ thuộc ngôn ngữ, là đánh giá tên theo độ hiếm: tên khớp quá nhiều chunk chỉ được
nhận khi câu hỏi gần như chỉ gồm tên đó ("Chất là gì?"), còn lại nhường cho embedding.

### 1.4 Tách từ cho BM25: proxy không ủng hộ, cặp âm tiết thì có ích

Thí nghiệm proxy này chạy offline, không gọi mô hình, với thiết kế sau:
- Truy vấn sinh từ đồ thị, ba loại cho mỗi khái niệm: tên; "tên + là gì?"; câu đầu của mô tả A5 đã xoá mọi tên và alias của khái niệm.
- Đích là chunk dạy của khái niệm. Độ đo là MRR@10 và Recall@5, tính trên 845 khái niệm của sáu cuốn rồi lấy trung bình vĩ mô theo cuốn.
- Bốn cách tách token cho cùng BM25 (k1 1,5; b 0,75): âm tiết như mã dự án; âm tiết cộng cặp âm tiết liền kề; tách từ bằng underthesea 9.5.0;
  tách từ bằng pyvi 0.1.1.

Bảng 4 cho kết quả, trung bình vĩ mô sáu cuốn:

| cách tách | tên: MRR@10 / R@5 | "tên là gì?": MRR@10 / R@5 | mô tả bỏ tên: MRR@10 / R@5 |
|---|---|---|---|
| âm tiết (hiện tại) | 0,694 / 0,861 | 0,671 / 0,849 | 0,787 / 0,869 |
| âm tiết + cặp âm tiết | **0,729 / 0,889** | **0,724 / 0,862** | **0,808** / 0,868 |
| underthesea | 0,652 / 0,810 | 0,629 / 0,789 | 0,771 / 0,863 |
| pyvi | 0,636 / 0,799 | 0,668 / 0,836 | 0,776 / **0,870** |

Ba điều cần đọc kèm bảng 4:
- **Tách từ không thắng âm tiết trong proxy này.** Theo MRR@10, underthesea thấp hơn âm tiết ở cả ba loại truy vấn; pyvi thấp hơn ở hai loại và
  ngang ở loại "tên là gì?". Thêm cặp âm tiết liền kề cho MRR@10 cao nhất ở cả ba loại (+0,02 tới +0,05).
- **Proxy thiên về khớp chữ.** Tên khái niệm thường nằm nguyên văn trong chunk dạy, còn mô tả A5 được viết từ chính chunk đó. Câu hỏi thật sẽ ít
  trùng chữ hơn, và nhánh dense chưa được tính vì không gọi embedding.
- **Mẫu nhỏ ở hai cuốn.** naive-bayes chỉ có 20 khái niệm và doc-6 có 12, nên chênh lệch giữa các cách ở hai cuốn này dao động mạnh.

### 1.5 Đồ thị: tiên quyết Hasse luôn có câu trích, còn bao đóng và lộ trình tới mục tiêu thì lớn

Bảng 5 cho thấy phần đồ thị mà công cụ của trợ lý sẽ đọc:

| tài liệu | khái niệm có 0 / 1 / 2 / 3 tiên quyết Hasse | liên kết Hasse là cạnh cứng có `quote` nguyên văn | tổ tiên theo cạnh cứng: trung vị / p90 / max | `requires_edges` (trong đó `cong_cu`; ngược thứ tự sách) | cạnh mở kiểu `requires` | cạnh media `confirmed` → khái niệm | `path_to`: số module trung vị / p90 / max | `path_to`: số khái niệm trung vị / p90 / max |
|---|---|---:|---|---|---:|---|---|---|
| doc-1 | 9 / 108 / 52 / 30 | 302/302 | 8 / 23 / 36 | 674 (222; 8) | 7 | 16 → 15 | 7 / 18 / 20 | 47 / 115 / 124 |
| nhap-mon-ml | 18 / 16 / 17 / 3 | 59/59 | 2 / 7 / 10 | 126 (49; 10) | 1 | 3 → 3 | 3 / 5 / 6 | 21 / 32 / 36 |
| naive-bayes | 14 / 6 / 0 / 0 | 6/6 | 0 / 2 / 3 | 6 (0; 0) | 2 | 7 → 4 | 2 / 3 / 3 | 14 / 20 / 20 |
| doc-6 | 9 / 3 / 0 / 0 | 3/3 | 0 / 1 / 1 | 3 (0; 0) | 0 | 8 → 5 | 1,5 / 2 / 2 | 9 / 12 / 12 |
| xstk-ch3-1 | 5 / 44 / 14 / 9 | 99/99 | 6 / 14 / 21 | 240 (103; 2) | 7 | 9 → 5 | 5 / 9 / 9 | 40 / 72 / 72 |
| doc-4 | 86 / 225 / 116 / 62 | 643/643 | 11 / 41 / 69 | 1.954 (883; 201) | 25 | 0 | 14 / 47 / 53 | 86 / 256 / 291 |

Bảng 5 cho năm điểm chính:
- **Công cụ "vì sao đứng ở đây" có đủ dữ liệu.** Mọi liên kết Hasse là một cạnh `requires` cứng có `quote`, và mọi `quote` của
  `requires_edges` đều có nguyên văn trong chunk mà cạnh trích (sau chuẩn hoá NFC, casefold và khoảng trắng). Câu trích có thể khó đọc khi lớp
  chữ PDF hỏng. Ví dụ, một cạnh của naive-bayes trích "Voi P(A)>Ova{B，B,,Bn}la mot he day du cac bienc6".
- **Không được đổ cả bao đóng vào ngữ cảnh.** Ở doc-4, một khái niệm ở p90 có 41 tổ tiên theo cạnh cứng; nếu tính cả cạnh mềm thì trung vị đã là
  235. Hasse giới hạn tối đa 3 là tay cầm đúng; 13 khái niệm của doc-4 có thêm tiên quyết bị ẩn (`display_prerequisites_more_count` > 0).
- **Kết quả `target_roadmap` quá dài để đưa nguyên cho mô hình.** Ở doc-4, lộ trình tới một khái niệm p90 gồm 47 module và 256 khái niệm. Công cụ
  `path_to` phải trả bản gọn theo module (mục 3.3).
- **Cạnh mở kiểu `requires` là đề xuất chưa kiểm.** Có 7 ở doc-1, 7 ở xstk và 25 ở doc-4. Chúng nằm trong `open_edges`, không phải
  `requires_edges`, nên công cụ không được trộn hai loại.
- **Media dùng được rất ít, và chưa có module.** Số khái niệm có cạnh media đã xác nhận là 15, 3, 4, 5, 5 và 0. Cả 93 node media đều chưa có
  `module_id`. Mô tả ảnh phần lớn do mô hình sinh: 80/93 có `caption_source` khác `original`.

Ngân sách ngữ cảnh đồ thị nhỏ. Tính chunk dạy, mô tả của khái niệm và mô tả của tối đa 3 tiên quyết Hasse thì trung vị là 193–504 token, p90 là
242–749 token, tuỳ cuốn.

### 1.6 Chất lượng đồ thị và những gì Pha B chưa có

Trợ lý phải chịu được cạnh sai. Theo [kết quả tập giữ lại v3](ket-qua-tap-giu-lai-v3-2026-10-04.md), độ chính xác cạnh bao đóng đạt 0,874 trên
tài liệu phát triển nhưng chỉ 0,584–0,636 trên tập giữ lại. Chấm mù cho thấy khoảng 1/3 cạnh dư bị cho là "không cần thứ tự". doc-4 còn có khái
niệm khung bị làm tiên quyết, còn xstk có khái niệm cốt lõi bị đẩy ra ngoài bài. Vì vậy, khi trợ lý nói "học X trước Y", nó phải kèm câu trích
và giọng điệu đề xuất, không khẳng định như luật.

Pha B hiện thiếu các phần sau:
- **A12** chưa làm: chỉ mục chưa có `module_id`, và chunk không dạy khái niệm nào chưa có luật gán module.
- **A11** (enrichment) chưa có, nên `get_module_info` của B2 chưa có mục tiêu hay tóm tắt module để trả. Tên và mô tả module đang được nghiên cứu
  ở [báo cáo riêng](nghien-cuu-ten-va-mo-ta-module-2026-10-11.md).
- **Media** chưa gắn module. Spec A12 ghi Pha B phải chặn media chưa gắn module cho tới khi có luật riêng.
- **Mô hình người học** nằm ngoài phạm vi đề cương, nên bảng tiến độ `concept_mastery` của B1 và vòng thích nghi B4 không dùng được làm căn cứ.
  Tín hiệu vị trí duy nhất là module người học đang mở.
- **Không có mã** cho B1–B4, prompt trợ lý, hay web.

---

## 2. Văn liệu

Mục này gom văn liệu theo tám nhóm. Mỗi nhóm kết thúc bằng điều dùng được cho dự án. Mức đọc từng nguồn ghi ở mục 7.

### 2.1 Quy trình cố định, RAG nhiều bước và agent gọi công cụ

Ba dòng văn liệu so một bước với nhiều bước:
- **ReAct** cho mô hình xen kẽ suy luận và hành động (gọi công cụ), rồi đọc kết quả để quyết bước kế
  ([Yao và cộng sự, ICLR 2023](https://arxiv.org/abs/2210.03629)). Đây là khuôn của "agent vòng lặp gọi công cụ"; mỗi vòng là một lời gọi
  mô hình.
- **IRCoT** xen truy hồi với từng câu chuỗi suy luận, vì với câu hỏi nhiều bước "cần tìm gì phụ thuộc vào cái đã suy ra"
  ([Trivedi và cộng sự, ACL 2023](https://aclanthology.org/2023.acl-long.557/)). Tóm tắt bài báo tăng tới 21 điểm truy hồi và 15 điểm QA trên
  bốn bộ nhiều bước. **Self-RAG** huấn luyện một mô hình tự quyết khi nào truy hồi và tự phê bình bằng token phản tư
  ([Asai và cộng sự, ICLR 2024](https://arxiv.org/abs/2310.11511)); cách này cần huấn luyện mô hình, nên không dùng được với Gemini API.
- **Adaptive-RAG** (đọc toàn văn) dùng một bộ phân loại nhỏ chọn một trong ba chiến lược theo độ phức tạp của câu hỏi: không truy hồi, truy hồi
  một bước, hay nhiều bước kiểu IRCoT ([Jeong và cộng sự, NAACL 2024](https://aclanthology.org/2024.naacl-long.389/)). Bảng 1 của bài (đã đối chiếu
  bằng ảnh trang) cho số với GPT-3.5:

| chiến lược (GPT-3.5) | F1 | số bước | thời gian so với một bước |
|---|---:|---:|---:|
| không truy hồi | 48,56 | 0 | 0,71 |
| một bước | 46,99 | 1 | 1,00 |
| nhiều bước (IRCoT) | 50,87 | 2,81 | 3,33 |
| Adaptive-RAG | 50,91 | 1,03 | 1,46 |
| Adaptive-RAG với bộ phân loại hoàn hảo | 62,80 | 0,50 | 1,03 |

Bảng cho ba điểm:
- Nhiều bước chỉ hơn một bước 3,9 điểm F1 nhưng tốn 3,33 lần thời gian. Định tuyến giữ được F1 của nhiều bước với 1,46 lần thời gian.
- Khoảng cách tới bộ phân loại hoàn hảo (62,80) rất lớn, tức định tuyến sai là nguồn lỗi chính. Ma trận nhầm của bài cho thấy 47% câu "không cần
  truy hồi" bị xếp vào "một bước".
- Bối cảnh khác dự án: kho Wikipedia, truy hồi BM25, câu hỏi nhiều bước kiểu nối thực thể. Ở dự án, phần "nhiều bước" chủ yếu là đi trên đồ thị
  tiên quyết, và việc đó mã làm được mà không cần mô hình.

**HippoRAG** (đọc toàn văn) cho bằng chứng trực tiếp rằng đồ thị thay được truy hồi lặp
([Gutiérrez và cộng sự, NeurIPS 2024](https://arxiv.org/abs/2405.14831)). Truy hồi một bước bằng Personalized PageRank trên đồ thị, gieo từ các
nút mà câu hỏi nhắc tới, đạt F1 QA trung bình 48,1, cao hơn IRCoT (44,7) trên ba bộ nhiều bước (Bảng 4, đã đối chiếu ảnh). Phụ lục G ghi chi phí
cho 1.000 câu hỏi: IRCoT 1–3 USD và 20–40 phút, HippoRAG 0,1 USD và 3 phút, tức rẻ hơn 10–30 lần và nhanh hơn 6–13 lần. Tóm tắt của bài ghi
"10–20 lần", lệch với thân bài. Bảng 5 có một kết quả đáng chú ý: thêm láng giềng trực tiếp của nút truy vấn mà không có PPR làm R@2 trung bình
tụt từ 50,7 xuống 42,2, dù R@5 tăng nhẹ từ 56,2 lên 59,2. Mở rộng đồ thị không có trọng số chọn lọc có thể đưa nhiễu vào.

*Suy luận:* văn liệu ủng hộ "một lời gọi sinh, phần nhiều bước để mã và đồ thị làm", và chỉ dùng vòng lặp agent cho phần nhỏ câu hỏi thật sự
cần. Không có nghiên cứu nào trong số đã đọc đo trên trợ lý giáo trình tiếng Việt, nên tỉ lệ câu hỏi cần nhiều bước phải đo trên bộ câu hỏi thử.

### 2.2 GraphRAG và các biến thể: cái nào hợp một tài liệu 30–700 chunk có sẵn đồ thị

**GraphRAG [23]** (đọc toàn văn bản v2, 2025-02-19) nhắm câu hỏi "toàn cục" kiểu tóm tắt theo truy vấn, ví dụ "chủ đề chính của kho là gì?",
trên kho khoảng 1 triệu token ([Edge và cộng sự](https://arxiv.org/abs/2404.16130)). Quy trình như sau:
- LLM trích thực thể, quan hệ và claim từ từng chunk; gom cộng đồng bằng Leiden phân cấp; LLM viết tóm tắt cho từng cộng đồng.
- Khi hỏi, mỗi tóm tắt cộng đồng sinh một câu trả lời cục bộ kèm điểm hữu ích 0–100 (map), rồi gộp thành câu trả lời cuối (reduce).
- Đánh giá bằng LLM làm giám khảo so cặp trên 125 câu hỏi mỗi kho, mỗi phép so lặp 5 lần. GraphRAG thắng RAG vector 72–83% về độ đầy đủ và
  62–82% về độ đa dạng; RAG vector vẫn "trực tiếp" nhất. Dựng chỉ mục kho podcast mất 281 phút với gpt-4-turbo.
- Bài tự nói tiêu chí faithfulness và answer relevance của RAGAS "không hợp" câu hỏi toàn cục, và chưa so tỉ lệ bịa.

Bảng sau so các biến thể với hoàn cảnh dự án: một tài liệu, 1.507–151.585 token, đồ thị tiên quyết có kiểu và có câu trích đã dựng sẵn ở Pha A:

| phương pháp | ý chính | chi phí dựng | chi phí mỗi câu hỏi | hợp dự án? |
|---|---|---|---|---|
| GraphRAG global [23] | tóm tắt cộng đồng, map-reduce khi hỏi | LLM qua mọi chunk và mọi cộng đồng | nhiều lời gọi (một lời mỗi lô tóm tắt) | **Không** cho hỏi đáp thường. Lấy ý: tóm tắt module (báo cáo tên module, A11) đóng vai tóm tắt cộng đồng cho câu hỏi tổng quan |
| LightRAG ([Guo và cộng sự 2024](https://arxiv.org/abs/2410.05779)) | chỉ mục thực thể và quan hệ, truy hồi hai mức: thấp (thực thể) và cao (chủ đề) | LLM trích lại đồ thị | 1 lời gọi tách từ khoá + 1 lời sinh | **Một phần.** Không dựng lại đồ thị (trùng A3–A8); lấy ý hai mức: khái niệm qua `lookup_concept`, module qua `get_module_info` |
| HippoRAG (NeurIPS 2024) | PPR từ nút của câu hỏi, một bước | LLM OpenIE qua mọi chunk | 1 lời gọi trích thực thể + 1 lời sinh | **Ý hợp, công cụ không cần.** Liên kết câu hỏi với khái niệm làm bằng mã; PPR trên đồ thị tiên quyết là nhánh ablation, không phải mặc định |
| Think-on-Graph ([Sun và cộng sự, ICLR 2024](https://arxiv.org/abs/2307.07697)) | LLM làm agent dò beam search trên KG qua nhiều vòng | 0 (dùng KG có sẵn) | nhiều lời gọi mỗi câu | **Không.** Giây chờ và USD tăng theo số vòng; đồ thị của dự án nhỏ, mã duyệt được |
| G-Retriever ([He và cộng sự 2024](https://arxiv.org/abs/2402.07630)) | chọn đồ thị con, mã hoá bằng GNN, đưa vào LLM bằng soft prompt có tinh chỉnh | huấn luyện GNN và projector | 1 lời gọi mô hình mở | **Không.** Cần tinh chỉnh mô hình mở; đề cương không huấn luyện hay tinh chỉnh mô hình |
| CGLLM của TutorQA [18] | LLM viết lệnh Cypher truy đồ thị, LLM thứ hai trả lời từ đường đi | LLM khôi phục đồ thị | 2 lời gọi | **Một phần.** Thay bước "LLM viết Cypher" bằng công cụ cố định có tham số |

Hai khảo sát GraphRAG chia lĩnh vực thành ba khâu: lập chỉ mục dựa trên đồ thị, truy hồi dẫn bởi đồ thị, sinh có tăng cường đồ thị
([Peng và cộng sự 2024](https://arxiv.org/abs/2408.08921); [Han và cộng sự 2025](https://arxiv.org/abs/2501.00309)). Theo cách chia này, dự án
đã xong khâu một ở Pha A. Việc của Pha B chỉ là khâu hai và ba.

*Suy luận:* không biến thể nào được thiết kế cho trường hợp đồ thị đã có kiểu, có câu trích và có thứ tự học. Lợi thế của dự án là bỏ được bước
LLM dựng đồ thị lúc hỏi, và trả được câu "vì sao" bằng câu trích có sẵn. Đây là chỗ báo cáo đồ án nên nói rõ đóng góp.

### 2.3 TutorQA [18]: các loại tác vụ và phần dùng lại được

TutorQA (đọc toàn văn; arXiv chỉ có bản v1 ngày 2024-02-22) gồm 500 cặp hỏi đáp về NLP do chuyên gia duyệt, chia năm tác vụ, mỗi tác vụ 100 câu
([Yang và cộng sự](https://arxiv.org/abs/2402.14293)). Câu hỏi được sinh bằng cách lấy mẫu trên đồ thị LectureBankCD (322 khái niệm NLP có nhãn
tiên quyết), rồi chuyên gia lọc bỏ câu trùng hoặc đường quá ngắn.

| tác vụ | câu hỏi mẫu (dịch) | đáp án | độ đo | điểm GPT-4 → GPT-4 + đồ thị |
|---|---|---|---|---|
| T1 dự đoán tiên quyết | "Tôi đã học A, nó có giúp tôi học B không?" (50 cặp dương, 50 âm) | có/không | accuracy, F1 | 0,52/0,68 → 0,94/0,94 |
| T2 tìm đường | "Muốn học X thì nên học gì trước?" | danh sách khái niệm | F1 theo độ tương đồng | 0,80 → 0,89 |
| T3 đường ngắn nhất | "Tôi biết A, muốn học B, đi theo đường nào?" | danh sách khái niệm | F1 theo độ tương đồng | 0,89 → 0,85 |
| T4 tư vấn khái niệm | mô tả một dự án → cần học khái niệm nào | danh sách khái niệm | F1 theo độ tương đồng | 0,69 → 0,72 |
| T5 ý tưởng dự án | đã biết các khái niệm → đề xuất dự án | văn bản mở | hai chuyên gia chấm 1–5, κ = 0,7626 | đánh giá người |

Cách họ dùng đồ thị: CGLLM chạy qua LangChain; một LLM sinh lệnh Cypher để lấy đường đi khái niệm, LLM thứ hai trả lời với chỉ dẫn "chỉ dùng
đường đi được trả làm thông tin". "F1 theo độ tương đồng" coi hai khái niệm là khớp khi cosine embedding BERT > 0,6. Bài tự nhận độ đo này bỏ
qua thứ tự khái niệm trong đường đi.

Ba điều cần đọc kèm:
- **Đồ thị không phải lúc nào cũng giúp.** Ở T3, GPT-4 cộng đồ thị giảm từ 0,89 xuống 0,85, dù thân bài viết "cải thiện nhất quán".
- **Mức không đồ thị gần ngẫu nhiên ở T1** (GPT-4 accuracy 0,52). Câu hỏi "có cần học A trước B" vì vậy là loại câu mà đồ thị đóng góp rõ nhất.
- **TutorQA không có trích dẫn, không có câu ngoài tài liệu, không có hội thoại nhiều lượt**, và đồ thị lấy từ nhãn chuyên gia chứ không phải
  đồ thị máy dựng có lỗi.

Phần dùng lại được cho bộ câu hỏi thử của dự án:
- T1, T2, T3 dịch thẳng sang ba loại câu "vì sao tiên quyết", "học gì trước X" và "lộ trình tới mục tiêu".
- Chấm T2/T3 bằng khớp đúng `node_id` vì tập khái niệm của dự án là đóng, cộng một độ đo thứ tự (Kendall τ); cách này sửa đúng hạn chế bài tự nhận.
- T1 cần đáp án độc lập với đồ thị đang thử, nếu không phép đo là vòng tròn. Lấy nhãn vàng tiên quyết đã có ở tài liệu phát triển
  (`artifacts/a8-gold`), không lấy từ chính `requires_edges`.
- T4 và T5 nằm ngoài phạm vi "chỉ trong tài liệu", nên bỏ.

### 2.4 Tách từ tiếng Việt cho BM25

Tách từ có công cụ tốt: VnCoreNLP đạt F1 tách từ 97,90 ([Vu và cộng sự, NAACL 2018 Demo](https://aclanthology.org/N18-5012/)), và underthesea,
pyvi đều chạy offline. Nhưng chưa tìm được nghiên cứu so BM25 âm tiết với BM25 đã tách từ trên giáo trình tiếng Việt; lượt tìm này không đủ để
kết luận là chưa có. Proxy ở mục 1.4 không ủng hộ tách từ: underthesea và pyvi thấp hơn hoặc ngang âm tiết, còn cặp âm tiết liền kề thì hơn
0,02–0,05 MRR@10. Lỗi tách từ trên văn bản toán cũng thấy được: underthesea cắt "khai triển Laplace" thành "khai triển_Laplace", và ở doc-1
chỉ 62% lần khớp tên nhiều âm tiết trùng ranh giới từ của underthesea. Riêng với liên kết tên một âm tiết, tách từ loại được tới 85% khớp sai
(mục 1.3).

*Suy luận:* cặp âm tiết rẻ, không phụ thuộc ngôn ngữ, và hợp với chỉ mục RRF đang có. Nên thử nó trước tách từ.

### 2.5 Nhắc khái niệm nền và scaffolding

Khái niệm "scaffolding" xuất phát từ Wood, Bruner và Ross: người dạy đỡ những phần người học chưa làm được, để người học tập trung vào phần trong
tầm ([J. Child Psychology and Psychiatry, 1976](https://doi.org/10.1111/j.1469-7610.1976.tb00381.x)). Tổng quan của VanLehn [13] so gia sư người,
hệ gia sư thông minh và các dạng khác ([Educational Psychologist, 2011](https://doi.org/10.1080/00461520.2011.611369)). Cả hai chỉ được kiểm siêu
dữ liệu trong lượt này. Lý thuyết không gian tri thức [10] mô tả phần người học "sẵn sàng học" dựa trên quan hệ tiên quyết, nhưng cần trạng thái
tri thức của từng người, tức mô hình người học, mà đề cương để ngoài phạm vi.

*Suy luận:* văn liệu đã đọc không đưa ra luật "khi nào nhắc tiên quyết" mà không cần mô hình người học. Mục 3.5 vì vậy đề xuất luật dựa trên vị
trí module, và luật này phải được người học thử chấm (có ích hay phiền).

### 2.6 Câu hỏi không trả lời được và từ chối

Hai kết quả chính:
- **Sufficient Context** (đọc phần liên quan) định nghĩa "ngữ cảnh đủ" là ngữ cảnh chứa đủ thông tin để trả lời, không cần đáp án vàng
  ([Joren và cộng sự, ICLR 2025](https://arxiv.org/abs/2411.06037)). Bộ chấm "đủ/không đủ" bằng LLM đạt 93% accuracy. Mô hình lớn
  (Gemini 1.5 Pro, GPT-4o, Claude 3.5) khi ngữ cảnh không đủ thường trả lời sai thay vì từ chối, và việc thêm ngữ cảnh RAG còn làm mô hình
  ít từ chối hơn so với hỏi suông. Mô hình vẫn trả lời đúng 35–62% số ca ngữ cảnh không đủ, nên từ chối cứng mọi ca "không đủ" sẽ mất câu đúng.
  Kết hợp tín hiệu "đủ" với độ tự tin của mô hình để từ chối có chọn lọc làm tỉ lệ đúng trong số câu được trả lời tăng 2–10%.
- **RGB** đo bốn năng lực RAG, trong đó có "negative rejection", tức từ chối khi không đoạn nào chứa đáp án
  ([Chen và cộng sự, AAAI 2024](https://arxiv.org/abs/2309.01431); chỉ đọc tóm tắt). Tóm tắt bài kết luận các mô hình còn kém ở năng lực này.

*Suy luận:* không thể chỉ dựa vào câu dặn "nếu không có thì nói không có". Cần một tín hiệu từ truy hồi do mã tính, một cờ do mô hình trả, và
một luật hậu kiểm (mục 3.6).

### 2.7 Trích dẫn, trung thực và giám khảo LLM

Ba nguồn dùng cho đánh giá:
- **ALCE** định nghĩa citation recall (câu được các đoạn nó trích hỗ trợ đầy đủ) và citation precision (mỗi trích dẫn có cần không), chấm bằng
  mô hình NLI TRUE (T5-11B) ([Gao và cộng sự, EMNLP 2023](https://arxiv.org/abs/2305.14627); đọc lại bản tải của báo cáo tên module).
- **Giám khảo LLM** có ba thiên lệch: vị trí, độ dài và tự đề cao; GPT-4 làm giám khảo khớp người trên 80%, ngang mức hai người khớp nhau
  ([Zheng và cộng sự, NeurIPS 2023 D&B](https://arxiv.org/abs/2306.05685)). Mô hình nhận ra và chấm cao văn bản của chính nó
  ([Panickssery và cộng sự 2024](https://arxiv.org/abs/2404.13076); chỉ đọc tóm tắt). Dự án dùng flash-lite vừa sinh vừa chấm nên rủi ro tự
  đề cao có thật.
- **Lost in the Middle**: mô hình dùng thông tin ở đầu và cuối ngữ cảnh tốt hơn ở giữa
  ([Liu và cộng sự, TACL](https://arxiv.org/abs/2307.03172); chỉ đọc tóm tắt). Đoạn quan trọng nhất nên đứng đầu khối ngữ cảnh.

### 2.8 RAGAS [28] và Gemini

RAGAS bản hiện hành là 0.4.3 (PyPI, 2026-01-13); kho mã đã chuyển sang `github.com/vibrantlabsai/ragas`. Định nghĩa bốn độ đo theo
[docs.ragas.io](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) như sau:

| độ đo | cách tính | cần gì | ghi chú cho dự án |
|---|---|---|---|
| faithfulness | LLM tách câu trả lời thành các claim, rồi xét từng claim có suy ra được từ `retrieved_contexts` không; điểm = claim được đỡ / tổng claim | câu hỏi, câu trả lời, ngữ cảnh | chỉ LLM, không embedding |
| response (answer) relevancy | LLM sinh ngược 3 câu hỏi từ câu trả lời (`strictness`), lấy cosine trung bình với câu hỏi gốc | câu hỏi, câu trả lời; LLM và embedding | **câu trả lời "lảng" bị nhân 0**: mã nguồn 0.4.3 (`collections/answer_relevancy/metric.py`, dòng 154) đặt điểm = 0 khi mọi lần sinh đánh dấu `noncommittal`. Câu từ chối đúng sẽ bị 0 điểm |
| context precision | trung bình precision@k có trọng số theo vị trí của các đoạn liên quan; mỗi đoạn được LLM xét liên quan hay không so với câu trả lời tham chiếu | câu hỏi, ngữ cảnh, `reference` | một lời gọi LLM cho mỗi đoạn |
| context recall | tách câu trả lời tham chiếu thành claim, xét từng claim có quy được về ngữ cảnh không | ngữ cảnh, `reference` | cần đáp án tham chiếu |

Cấu hình Gemini: trang [Gemini integration](https://docs.ragas.io/en/stable/howtos/integrations/gemini/) dùng
`llm_factory("<model>", provider="google", client=genai.Client(...))` với SDK `google-genai`, và `GoogleEmbeddings(client=client,
model="gemini-embedding-001")`. Trang nói khi LLM là Gemini thì embedding tự khớp sang Google, "không cần khoá OpenAI". Mã nguồn 0.4.3 có
`GoogleEmbeddings` mặc định `gemini-embedding-001`. Gói vẫn kéo `openai` và `langchain_openai` làm phụ thuộc cài đặt, nên phải kiểm bằng nhật ký
mạng rằng không lời gọi nào đi tới OpenAI. Prompt của RAGAS viết bằng tiếng Anh; có trang hướng dẫn chuyển ngôn ngữ prompt
(`metrics_language_adaptation`). API metric kiểu cũ (`SingleTurnSample`) bị đánh dấu sẽ bỏ ở 1.0; nên dùng `ragas.metrics.collections`.

### 2.9 Vận hành Gemini (tài liệu chính thức, đọc 2026-10-11)

Bảng sau gom các quy định liên quan tới trợ lý, lấy từ bản `generateContent` của tài liệu:

| chủ đề | quy định | nguồn | hệ quả |
|---|---|---|---|
| chế độ gọi hàm | `AUTO` (mặc định khi chỉ có hàm): mô hình tự chọn gọi hàm hay trả lời; `ANY`: buộc gọi hàm, có thể giới hạn `allowed_function_names`; `NONE`: cấm gọi hàm; `VALIDATED`: mặc định khi kết hợp công cụ có sẵn hoặc structured output, giảm lời gọi hàm hỏng | [Function calling](https://ai.google.dev/gemini-api/docs/generate-content/function-calling), cập nhật 2026-10-09 | vòng cuối dùng `NONE` để chắc chắn ra câu trả lời |
| gọi song song, gọi nối | 3.1 Flash-Lite hỗ trợ cả hai; kết quả song song trả theo `id`, không cần đúng thứ tự | như trên | gọi nhiều công cụ trong một vòng |
| số công cụ | "lý tưởng giữ tập công cụ đang bật tối đa 10–20"; mô tả hàm tính vào token vào | như trên | 7 công cụ là vừa |
| thought signature | Gemini 3 trả chữ ký ở phần `functionCall` đầu tiên; **phải** gửi lại đúng chỗ trong lượt hiện tại, thiếu thì lỗi 400, kể cả ở mức thinking `minimal`. Chỉ lượt hiện tại bị kiểm. Không nên chèn `functionCall` tự tạo; nếu buộc phải, dùng chữ ký giả `skip_thought_signature_validator`. SDK tự xử lý nếu nối nguyên đối tượng phản hồi vào lịch sử | [Thought signatures](https://ai.google.dev/gemini-api/docs/generate-content/thought-signatures), 2026-09-04 | kết quả công cụ do mã chạy sẵn thì đưa vào dạng văn bản, không giả làm lời gọi hàm |
| thinking | 3.1 Flash-Lite mặc định `minimal`, hỗ trợ `minimal`, `low`, `medium`, `high`; `minimal` "không bảo đảm tắt suy nghĩ"; token suy nghĩ tính như token ra | [Thinking](https://ai.google.dev/gemini-api/docs/generate-content/thinking), 2026-10-09 | để `minimal` cho câu trả lời; đo `thoughtsTokenCount` |
| structured output | JSON đúng cú pháp nhưng không bảo đảm đúng nghĩa; stream được thành JSON dở ghép dần. **Kết hợp structured output với công cụ** đang ở Preview và trang chỉ ghi `gemini-3.1-pro-preview`, `gemini-3.8-flash` | [Structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output), 2026-10-09 | với flash-lite, không dựa vào JSON schema trong vòng có công cụ |
| stream | `streamGenerateContent?alt=sse`; khi không có lời gọi hàm, chữ ký có thể nằm trong một phần chữ rỗng, nên đọc tới `finish_reason` | trang Text generation và Thought signatures | lưu đủ các phần khi ghi lịch sử |
| embedding | `gemini-embedding-001`: câu hỏi dùng `RETRIEVAL_QUERY` hoặc `QUESTION_ANSWERING` đi với `RETRIEVAL_DOCUMENT`; tối đa 2.048 token vào; chiều khác 3072 phải tự chuẩn hoá | [Embeddings](https://ai.google.dev/gemini-api/docs/embeddings), 2026-10-09 | chỉ mục đang dùng `RETRIEVAL_DOCUMENT`, 768 chiều; mã cosine đã tự chuẩn hoá |
| giá | 3.1 Flash-Lite 0,25 / 1,50 USD cho 1 triệu token vào / ra; cache 0,025; bậc trả phí ghi "không dùng để cải thiện sản phẩm", bậc miễn phí thì có. Trang giá không còn dòng `gemini-embedding-001`; mức 0,15 USD/1 triệu token chỉ thấy ở dòng File search | [Pricing](https://ai.google.dev/gemini-api/docs/pricing), 2026-10-09 | chỉ gửi giáo trình qua bậc trả phí; embedding một câu hỏi cỡ 30 token tốn cỡ 10⁻⁵ USD |

Tài liệu Developer API nay viết mặc định cho Interactions API. Trong API đó, chế độ có trạng thái (`store: true`) để máy chủ giữ chữ ký; chế độ
không trạng thái phải gửi lại nguyên các bước `thought`. Báo cáo giữ `generateContent` cho đồng bộ với mã Pha A.

---

## 3. Thiết kế khuyến nghị

### 3.1 Kiến trúc: quy trình cố định có định tuyến bằng mã, agent chỉ là nhánh phụ

Bảng sau so ba lựa chọn. USD và giây chờ tính ở mục 3.9; số là ước, không phải đo.

| tiêu chí | A. quy trình cố định (mã truy hồi, mở rộng đồ thị, 1 lời gọi sinh) | B. agent vòng lặp gọi công cụ (ReAct, function calling) | C. lai: mã định tuyến theo loại câu, agent chỉ cho phần khó |
|---|---|---|---|
| chất lượng | tốt với câu một khái niệm, định nghĩa, ví dụ, vì sao tiên quyết, lộ trình (mã gọi công cụ đồ thị sẵn); yếu với câu so sánh nhiều khái niệm không gọi tên | linh hoạt nhất; nhưng flash-lite có thể chọn sai công cụ hoặc dừng sớm, và mỗi vòng thêm chỗ lỗi | gần B ở câu khó, bằng A ở phần còn lại |
| số lời gọi mô hình | 1 (+ 1 lời viết lại câu hỏi ở khoảng 20% lượt nối tiếp) | 2–5 | 1, đôi khi 2–3 |
| USD mỗi câu (trung vị) | khoảng 0,0014 | khoảng 0,0034 (3 lời gọi) | khoảng 0,0017 |
| giây chờ tới chữ đầu | khoảng 1,4 giây | khoảng 4,3 giây (2 vòng) | khoảng 1,4 giây, câu khó khoảng 2,8 giây |
| độ tái lập | cao: ngữ cảnh do mã lắp, ghi được `context_hash` | thấp: đường đi công cụ khác nhau giữa các lần | cao ở nhánh A; nhánh agent ghi vết công cụ |
| độ khó kiểm thử | thấp: kiểm từng bước bằng mã, ngữ cảnh cố định | cao: phải kiểm cả chuỗi lựa chọn công cụ | trung bình: kiểm bộ định tuyến và nhánh agent riêng |
| rủi ro Gemini 3 | không dùng function calling, không lo thought signature | phải giữ chữ ký trong lượt; structured output với công cụ chưa có cho flash-lite | như B nhưng ít lượt |

**Khuyến nghị: C, với định tuyến làm bằng mã chứ không bằng LLM.** Lý do:
- Bảy loại câu trong bộ câu hỏi thử phần lớn chỉ cần một lời gọi sinh nếu mã đã lấy sẵn bằng chứng. Mã liên kết được câu hỏi với khái niệm ở
  80–100% trường hợp có gọi tên (mục 1.3), và công cụ đồ thị không tốn tiền nên mã gọi luôn, không cần mô hình chọn.
- Văn liệu cho thấy phần "nhiều bước" làm bằng đồ thị một bước rẻ hơn 10–30 lần mà không kém IRCoT (HippoRAG), và định tuyến theo độ phức tạp
  giữ được chất lượng với 1,46 thay vì 3,33 lần thời gian (Adaptive-RAG).
- Nhánh agent chỉ bật khi mã không liên kết được khái niệm nào mà câu hỏi lại dài, hoặc khi câu hỏi nhắc từ hai khái niệm trở lên với ý so
  sánh. **Tối đa 2 vòng công cụ**, tức tối đa 3 lời gọi mô hình; vòng cuối đặt `function_calling_config.mode = NONE`. Hai vòng đủ cho
  "tìm khái niệm → lấy quan hệ hoặc đoạn"; Adaptive-RAG đo nhiều bước trung bình 2,81 bước, và mỗi vòng thêm khoảng 1,4 giây.

Trả lời câu hỏi của chủ dự án, **"agent thường hỏi đáp trong một module đúng không"**: văn liệu đã đọc không có chuẩn nào bó hỏi đáp trong một
module. Spec B2 cũ lọc cứng `module_index <= current`, nhưng quyết định ngày 2026-10-11 bỏ việc chặn theo tiến độ. Thiết kế khuyến nghị vì vậy
là: **truy hồi trên cả tài liệu, xếp hạng ưu tiên module đang mở**, rồi tới các module trước, cuối cùng là module sau, và mọi đoạn mang nhãn vị
trí so với module đang mở. Module đang mở là ngữ cảnh mặc định, không phải ranh giới. Đây là đề xuất (*suy luận*); mục 5 có ablation "lọc cứng
theo module" để đo cái giá của từng cách.

### 3.2 Luồng xử lý một câu hỏi

`[CHÈN HÌNH 1 – sơ đồ luồng một câu hỏi: cột trái "mã" (chuẩn hoá → liên kết khái niệm → định tuyến → truy hồi lai có ưu tiên module → công cụ
đồ thị → lắp ngữ cảnh), cột phải "Gemini" (1 lời gọi sinh có stream; nhánh agent tối đa 2 vòng công cụ), dưới cùng "mã hậu kiểm" (kiểm nhãn trích
dẫn, luật từ chối, nhắc khái niệm nền) rồi tới web. Mũi tên nét đứt cho nhánh agent; hộp xám cho phần không tốn tiền.]`

Các bước sau chạy trên máy chủ cho mỗi câu hỏi:
1. **Chuẩn hoá và ghép lượt.** NFC, casefold. Nếu câu hỏi không liên kết được khái niệm nào và có dấu hiệu nối tiếp (đại từ, câu dưới 6 âm
   tiết), mượn khái niệm của lượt trước. Chỉ khi vẫn không liên kết được mới gọi một lời viết lại câu hỏi (mục 3.8).
2. **Liên kết khái niệm** (0 USD). Khớp tên, `display_name` và alias theo ranh giới âm tiết, tên dài nhất trước. Tên khớp quá nhiều chunk (ví dụ
   "chất" 297/671) chỉ được nhận khi câu hỏi gần như chỉ gồm tên đó. Tên trùng giữa hai khái niệm thì giữ cả hai làm ứng viên.
3. **Embedding câu hỏi** một lần, task type `QUESTION_ANSWERING`, 768 chiều. Vector này dùng cho cả truy hồi chunk và liên kết khái niệm theo mô
   tả khi bước 2 không ra gì. Muốn liên kết theo mô tả thì cần embed sẵn mô tả A5 của mọi khái niệm, một lần cho mỗi tài liệu.
4. **Định tuyến** bằng luật mã:
   - "ngoài tài liệu" nếu không liên kết được khái niệm, điểm dense cao nhất dưới ngưỡng τ_d và điểm BM25 cao nhất dưới ngưỡng τ_b; ngưỡng
     đặt trên bộ câu hỏi thử;
   - "lộ trình" nếu câu có mẫu "muốn học X", "để hiểu X cần gì" và có khái niệm đích;
   - "vì sao tiên quyết" nếu nhắc hai khái niệm có cạnh Hasse giữa chúng, hoặc hỏi "vì sao học A trước B";
   - "agent" nếu không liên kết được mà câu dài, hoặc nhắc từ hai khái niệm trở lên mà không có cạnh giữa chúng;
   - còn lại là "một khái niệm".
5. **Truy hồi lai** trên cả tài liệu (`HybridRetriever`, đo 0,059 giây mỗi truy vấn trên 671 chunk của doc-4), lấy 20 đoạn đầu rồi chia suất theo
   mục 3.4.
6. **Công cụ đồ thị do mã gọi sẵn**: `why_here` cho khái niệm chính, `path_to` nếu là câu lộ trình, `traverse` cho cạnh mở có câu trích. Kết quả
   vào ngữ cảnh dưới dạng văn bản có nhãn, không giả làm `functionCall`.
7. **Lời gọi sinh** có stream, `thinkingLevel = minimal`. Nhánh agent thì gọi với 7 công cụ ở chế độ `AUTO`, tối đa 2 vòng, vòng cuối `NONE`.
8. **Hậu kiểm bằng mã** (dưới 50 ms): kiểm nhãn trích dẫn (mục 3.7), luật từ chối (mục 3.6), gắn ghi chú "học kỹ ở module N", và gắn khối nhắc
   khái niệm nền (mục 3.5).
9. **Ghi nhật ký**: câu hỏi, khái niệm liên kết, đường định tuyến, `chunk_id` đã nạp, lời gọi công cụ, token, USD, giây chờ.

### 3.3 Bảng công cụ

Bảng sau giữ năm công cụ của B2 và thêm hai công cụ. Mọi công cụ là hàm thuần trên `graph.json` và chỉ mục, không gọi mô hình. Giới hạn độ dài
tính theo token Gemini ước (3 ký tự/token).

| công cụ | tham số | kết quả | giới hạn | luật bắt buộc |
|---|---|---|---|---|
| `search_document` (thay `search_module_content`) | `query`; `scope` ∈ {`uu_tien_module`, `ca_tai_lieu`, `module:<index>`}; `k` ≤ 6 | danh sách đoạn: nhãn `S#`, `chunk_id`, `page`, `section_path`, `module_index` (có thể rỗng), quan hệ với module đang mở (`truoc`/`dang_mo`/`sau`/`khong_ro`), chữ đoạn | ≤ 6 đoạn, mỗi đoạn ≤ 1.200 ký tự; tổng ≤ 2.400 token | đoạn có `[formula]` giữ nhãn `[CTk]` như báo cáo bài giảng, không tự điền công thức |
| `lookup_concept` | `name` | tối đa 3 ứng viên: `node_id`, tên hiển thị, `module_index`, `sequence_index`, mô tả A5 ≤ 300 ký tự, cách khớp (`ten`/`alias`/`mo_ta`), điểm | ≤ 400 token | nhiều ứng viên ngang điểm thì trả cả, không đoán |
| `get_module_info` | `module_index` hoặc `module_id` | `index`, tên, mô tả 1–2 câu (theo báo cáo tên module), tên các khái niệm theo thứ tự, vị trí so với module đang mở | ≤ 8 khái niệm, ≤ 300 token | chưa có A11 thì không có mục tiêu hay tóm tắt; không bịa |
| `why_here` (mới: "vì sao khái niệm đứng ở đây") | `concept_id` | module và vị trí trong dãy; tối đa 3 tiên quyết Hasse, mỗi cái: tên, `module_index`, `quote` ≤ 200 ký tự, `chunk_id`, trang, `soft_reason`, `order_relation`; `more_count` | ≤ 500 token | chỉ đọc `display_prerequisites` và `requires_edges`; đo được 100% liên kết Hasse là cạnh cứng có `quote` nguyên văn (mục 1.5); cạnh `cong_cu` ghi "công cụ, không bắt buộc"; cạnh ngược thứ tự sách ghi "sách trình bày ở phần sau" |
| `path_to` (mới, bọc `target_roadmap`) | `target` (tên, alias hoặc `node_id`) | `target_module_index`; danh sách module cần học, mỗi module: `index`, tên, số khái niệm, trạng thái so với module đang mở; số module trước module đang mở chỉ ghi tổng | ≤ 12 module liệt kê, phần còn lại gộp "và N module nữa"; ≤ 600 token | dùng đúng `target_roadmap` (bỏ cạnh `soft`); tên mơ hồ thì trả ứng viên thay vì lỗi; ở doc-4, lộ trình p90 có 47 module (mục 1.5) nên bắt buộc gộp |
| `traverse` | `node_id`, `edge_type` (chuỗi tự do, đối chiếu `type_registry`), `direction` ∈ {`ra`, `vao`}, `limit` ≤ 5 | các cạnh: kiểu, khái niệm đầu kia, câu trích bằng chứng ≤ 200 ký tự, `confirmed`, nguồn (`open_edges` hay `requires_edges`) | ≤ 5 cạnh, ≤ 400 token | `edge_type = requires` chỉ đọc `requires_edges`. Cạnh mở kiểu `requires` (7 ở doc-1, 25 ở doc-4) là đề xuất chưa kiểm: **không trả cho người học**, chỉ hiện ở màn quản trị A13. Cạnh mở không có câu trích thì không trả |
| `get_media_for_concept` | `concept_id` | tối đa 2 hình/bảng: `media_id`, loại, mô tả, `caption_source`, trang, đường dẫn ảnh | ≤ 2, ≤ 200 token | **chỉ cạnh `illustrates`/`tabulates` có `confirmed = true`**; media chưa có `module_id` nên không lọc được theo module. Spec A12 chặn media chưa gắn module; giữ chặn cho tới khi chủ dự án trả lời câu hỏi H2 (mục 6). `caption_source` khác `original` thì web ghi "mô tả do máy sinh" |

Ba luật chung cho mọi công cụ:
- Tổng kết quả công cụ trong một vòng không quá khoảng 2.500 token; thừa thì cắt theo thứ hạng, không cắt giữa câu.
- Kết quả dùng nhãn ngắn (`S#` cho đoạn, `N#` cho câu neo tiên quyết, `Q#` cho câu trích cạnh, `R#` cho cạnh mở, `CT#` cho công thức), cùng quy
  ước với [báo cáo bài giảng](nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md). Mã giữ bảng tra nhãn → `chunk_id`, trang, mục.
- Lỗi công cụ trả thông báo ngắn có cấu trúc (`{"loi": "khong_tim_thay", "goi_y": [...]}`), không ném ngoại lệ ra mô hình.

### 3.4 Nạp ngữ cảnh

Khối ngữ cảnh lắp theo thứ tự sau; đoạn quan trọng nhất đứng đầu vì mô hình dùng phần đầu và cuối ngữ cảnh tốt hơn phần giữa (mục 2.7):

| # | khối | nội dung | token ước | luật |
|---|---|---|---:|---|
| 1 | thẻ khái niệm | tên, module, vị trí, mô tả A5 | 60–100 | chỉ cho khái niệm đã liên kết, tối đa 2 |
| 2 | S1 | chunk dạy của khái niệm chính | 260 (trung vị), 400 (p90 doc-4) | luôn có khi đã liên kết |
| 3 | tiên quyết Hasse | tối đa 3: tên, module, `Q#` câu trích cạnh | 100–250 | ghi "quan hệ do hệ thống suy ra, có thể sai" |
| 4 | đoạn truy hồi | S2–S6 chia suất: tối đa 3 đoạn thuộc module đang mở hoặc module trước; tối đa 2 đoạn bất kỳ nếu chúng đứng trong top 5 toàn tài liệu | 1.000–1.600 | bỏ trùng với S1; mỗi đoạn mang nhãn vị trí so với module đang mở |
| 5 | kết quả công cụ khác | `path_to`, `traverse` khi định tuyến cần | 0–600 | — |
| 6 | lịch sử | tối đa 3 lượt gần nhất, chỉ câu hỏi và câu trả lời, bỏ ngữ cảnh cũ | 0–1.000 | — |

Tổng ngữ cảnh trung vị khoảng 2.400 token, p90 khoảng 4.000 (*ước*, từ token Gemma của chunk). Mã đã đo ở mục 1.5: chỉ riêng chunk dạy, mô tả
và mô tả tiên quyết đã là 193–504 token trung vị.

Hai việc A12 phải làm trước khi có ưu tiên module:
- Ghi `module_id` vào chỉ mục từ `chunk_module_map`, và cho chunk không dạy khái niệm nào một `module_hint` lấy từ chunk dạy gần nhất đứng trước.
  Cách này phủ 74–99% chỉ mục (mục 1.2); phần còn lại để rỗng và xếp như "không rõ".
- Không xoá chunk không có module khỏi truy hồi: chunk bài tập (doc-1 37, xstk 21) là nguồn tốt cho câu hỏi "ví dụ".

Nhánh thí nghiệm, không phải mặc định:
- BM25 âm tiết cộng cặp âm tiết liền kề (proxy +0,02 tới +0,05 MRR@10, mục 1.4).
- Thay chia suất bằng PPR trên đồ thị tiên quyết kiểu HippoRAG.
- "Nhồi cả tài liệu" cho bốn cuốn nhỏ (1.507–8.932 token), làm mốc so sánh (mục 5). Theo tóm tắt của
  [Li và cộng sự (EMNLP 2024, industry)](https://arxiv.org/abs/2407.16833), ngữ cảnh dài thắng RAG về trung bình khi đủ tài nguyên, còn RAG rẻ
  hơn nhiều; bài đề xuất Self-Route để mô hình tự chọn giữa hai đường.

### 3.5 Nhắc khái niệm nền khi không có mô hình người học

Mục tiêu 4 của đề cương yêu cầu trợ lý "chủ động nhắc lại các khái niệm nền dựa trên đồ thị". Khi không có trạng thái tri thức của người học,
tín hiệu duy nhất là vị trí: module đang mở và `sequence_index`. Luật khuyến nghị (*suy luận*, phải thử với người học) như sau:

| trường hợp | nhắc gì | ví dụ câu do mã sinh |
|---|---|---|
| khái niệm được hỏi ở module sau module đang mở | ghi chú "học kỹ ở module N" và tối đa 3 tiên quyết Hasse nằm giữa module đang mở và module N | "Phần này học kỹ ở module 7. Trước đó bạn sẽ gặp: A (module 5), B (module 6)." |
| khái niệm được hỏi thuộc module đang mở, tiên quyết thuộc module trước | nhắc ngắn 1 dòng, có link tới khái niệm nền và nút "vì sao?" hiện `Q#` | "Định nghĩa này dùng tới A (module 3)." |
| tiên quyết ở module sau khái niệm được hỏi (cạnh ngược thứ tự sách) | không gọi là "đã học" | "A được sách trình bày ở phần sau." |
| câu hỏi đang hỏi chính về khái niệm nền đó | không nhắc | — |

Bốn luật chống làm phiền:
- Tối đa một khối nhắc mỗi câu trả lời, tối đa 3 khái niệm, đặt ở cuối câu trả lời.
- Không nhắc lại cùng một khái niệm nền trong cùng phiên; mã giữ tập "đã nhắc" trong trạng thái hội thoại.
- Không nhắc ở câu nối tiếp ngắn và câu từ chối.
- Có nút tắt nhắc; số lần bấm tắt là một độ đo của mục 5.

Khối nhắc do **mã** sinh từ đồ thị, không phải LLM viết. Cách này tốn 0 USD, không bịa quan hệ, và không phụ thuộc mô hình có làm theo chỉ dẫn hay
không. Mô hình chỉ được dặn không mâu thuẫn với khối này.

### 3.6 Ngoài tài liệu, không trả lời được, và khái niệm ở module sau

Bốn trường hợp và cách xử lý:
- **Ngoài tài liệu** (định tuyến ở bước 4): không gọi mô hình. Mã trả câu cố định: "Tài liệu này không có nội dung về câu hỏi của bạn." Kèm tối
  đa 3 khái niệm gần nhất theo embedding mô tả, nếu điểm vượt ngưỡng thấp. Tiết kiệm trọn một lời gọi.
- **Có liên quan nhưng không đủ để trả lời**: mô hình được dặn trả `KHONG_DU` ở dòng đầu nếu ngữ cảnh không đủ. Sau đó mã hiện câu cố định cùng các
  đoạn gần nhất. Văn liệu cho thấy chỉ dặn là chưa đủ, vì mô hình hay trả lời thay vì từ chối (mục 2.6). Vì vậy có thêm luật hậu kiểm: câu trả
  lời không có nhãn trích dẫn hợp lệ nào thì đổi thành câu từ chối và ghi nhật ký.
- **Đủ một phần**: trả phần có nguồn, nói rõ phần tài liệu không đề cập.
- **Khái niệm ở module sau**: trả lời bình thường từ nguồn, kèm ghi chú "học kỹ ở module N" do mã gắn (mục 3.5). Không rút gọn câu trả lời; quyết
  định không chặn theo tiến độ đã bỏ lý do để rút.

Công thức thiếu (`[formula]`) xử lý như báo cáo bài giảng: mô hình chỉ được nhắc `[CTk]`, web thay bằng ảnh gốc theo trang và bbox; không tự
viết công thức. Bộ chấm "ngữ cảnh đủ" bằng LLM (93% accuracy trong văn liệu) không đặt trên đường chờ vì gấp đôi lời gọi. Nó dùng offline trong
đánh giá (mục 5) để biết luật hậu kiểm bắt được bao nhiêu ca.

### 3.7 Trích dẫn

Ba luật trích dẫn:
- Câu trả lời là văn bản Markdown có stream, mỗi câu có nội dung gắn nhãn `[S2]`, `[Q1]`… ở cuối câu. Chọn văn bản thay cho JSON vì vòng có
  công cụ của flash-lite chưa kết hợp được structured output (mục 2.9), và văn bản stream được từng chữ. Báo cáo bài giảng chọn JSON stream vì bài
  giảng có cấu trúc cố định; hai lựa chọn dùng chung tập nhãn.
- Mã hậu kiểm từng câu khi stream: nhãn phải thuộc tập đã nạp, nhãn lạ thì xoá. Câu có chữ số, ký hiệu toán hay tên khái niệm mà không có nhãn
  thì gắn cờ "chưa có nguồn". Câu trả lời không có nhãn hợp lệ nào thì xử lý như mục 3.6.
- Web hiện mỗi nhãn thành trích dẫn: `chunk_id`, trang, đường dẫn mục, và câu được tô sáng. Mã chọn câu tô sáng là câu trong đoạn trùng nhiều
  âm tiết nhất với câu trả lời, nên không cần mô hình chép `quote` (rẻ hơn, không có rủi ro chép sai). Riêng `Q#` là câu trích cạnh đã kiểm
  nguyên văn ở A8.

Mã chỉ kiểm được "trích đúng chỗ có thật". Việc câu trả lời có được đoạn đỡ hay không thì đo offline bằng faithfulness của RAGAS và citation
recall/precision kiểu ALCE (mục 5).

### 3.8 Hội thoại nhiều lượt

Năm luật cho hội thoại nhiều lượt:
- **Mỗi lượt truy hồi lại.** Không mang đoạn của lượt cũ sang lượt mới; lịch sử chỉ gồm câu hỏi và câu trả lời.
- **Mượn khái niệm trước khi viết lại.** Câu không liên kết được khái niệm thì mượn khái niệm của lượt trước (0 USD). Chỉ khi vẫn trống mới gọi
  một lời viết lại câu hỏi (khoảng 600 token vào, 40 token ra, khoảng 0,0002 USD), theo khuôn rewrite-retrieve-read
  ([Ma và cộng sự, EMNLP 2023](https://arxiv.org/abs/2305.14283); chỉ đọc tóm tắt).
- **Cắt lịch sử**: giữ 3 lượt gần nhất, trần 1.000 token; lượt cũ hơn bỏ, không tóm tắt (phiên học ngắn, tóm tắt tốn thêm lời gọi).
- **Thought signature**: nhánh A không dùng function calling nên không phát sinh. Nhánh agent dùng SDK chat, hoặc lưu nguyên các phần của phản hồi
  (kể cả `thoughtSignature`) trong lượt hiện tại. Các lượt trước chỉ cần lưu văn bản vì API chỉ kiểm chữ ký của lượt hiện tại (mục 2.9).
- **Trạng thái phiên** do máy chủ giữ: `doc_id`, module đang mở, tập khái niệm đã nhắc, 3 lượt gần nhất. Không lưu trình độ người học.

### 3.9 USD và giây chờ

Giả định chung (*ước*): chỉ dẫn hệ thống 900 token; khai báo 7 công cụ 700 token (chỉ nhánh agent); ngữ cảnh như mục 3.4; câu trả lời 350
token (p90 600); giá 3.1 Flash-Lite 0,25 / 1,50 USD cho 1 triệu token vào / ra. Embedding câu hỏi cỡ 10⁻⁵ USD, bỏ qua.

| kịch bản | lời gọi | token vào | token ra | USD/câu |
|---|---:|---:|---:|---:|
| A, trung vị | 1 | 3.300 | 350 | 0,0014 |
| A, p90 (doc-4, lịch sử đầy) | 1 | 5.000 | 600 | 0,0021 |
| A + viết lại câu hỏi | 2 | 3.900 | 390 | 0,0016 |
| B, một vòng công cụ | 2 | 6.100 | 430 | 0,0022 |
| B, hai vòng công cụ | 3 | 10.600 | 510 | 0,0034 |
| B, bốn vòng (không chặn) | 5 | khoảng 20.000 | khoảng 650 | khoảng 0,0060 |
| C, giả định 85% đi A, 15% đi B hai vòng | 1,3 trung bình | — | — | khoảng 0,0017 |
| mốc "nhồi cả tài liệu": naive-bayes / nhap-mon-ml / doc-1 / doc-4 | 1 | 5.800 / 8.900 / 43.800 / 151.600 + 1.300 | 350 | 0,0023 / 0,0031 / 0,012 / 0,039 |

Ghi chú cho bảng:
- Ở nhánh agent, mỗi vòng gửi lại toàn bộ hội thoại, nên token vào tăng gần theo bình phương số vòng. Đó là lý do chặn ở 2 vòng.
- Cache ngầm cần tiền tố ≥ 4.096 token và "không bảo đảm"; nhánh A dưới ngưỡng. Với mốc nhồi cả tài liệu, phần tài liệu là tiền tố chung giữa
  các câu hỏi nên có thể trúng cache (giá 10%), nhưng không được tính vào dự toán.
- Với `gemini-3.5-flash-lite` (0,30 / 2,50), A trung vị thành khoảng 0,0019 USD (+39%).
- 1.000 câu hỏi theo C tốn khoảng 1,7 USD.

Giây chờ dùng cùng giả định với báo cáo bài giảng: TTFT 1 giây, 200 token/giây, embedding 0,3 giây. Đây là **giá trị giả định**, phải đo.
Truy hồi cục bộ thì đã đo: 0,059 giây trên doc-4, 0,017 giây trên doc-1; dựng chỉ mục doc-4 trong bộ nhớ mất 0,82 giây, làm một lần khi nạp tài liệu.

| kịch bản | chữ đầu tiên | xong câu trả lời |
|---|---:|---:|
| ngoài tài liệu (không gọi mô hình) | khoảng 0,4 giây | khoảng 0,4 giây |
| A | khoảng 1,4 giây | khoảng 3,1 giây |
| A + viết lại câu hỏi | khoảng 2,6 giây | khoảng 4,3 giây |
| B, một vòng | khoảng 2,8 giây | khoảng 4,6 giây |
| B, hai vòng | khoảng 4,3 giây | khoảng 6,1 giây |

Phần do mã sinh (ghi chú module, khối nhắc khái niệm nền, lộ trình, nhãn trích dẫn) hiện ngay khi có, không chờ mô hình.

---

## 4. Hợp đồng dữ liệu cho web

Web và API do nhóm tự thiết kế; mục này chỉ định nghĩa dữ liệu. Có ba đối tượng: yêu cầu, sự kiện stream, và câu trả lời hoàn chỉnh.

**Yêu cầu** người học gửi:

```json
{
  "doc_id": "doc-1",
  "graph_version": 9,
  "session_id": "s_…",
  "current_module_id": "module_007",
  "question": "Vì sao phải học định thức trước ma trận nghịch đảo?",
  "client_turn_id": "t_…"
}
```

**Sự kiện stream** (SSE), theo thứ tự xuất hiện:

| `type` | khi nào | trường |
|---|---|---|
| `route` | sau định tuyến, khoảng 0,4 giây | `route` ∈ {`mot_khai_niem`, `vi_sao`, `lo_trinh`, `agent`, `ngoai_tai_lieu`}, `linked_concepts` |
| `graph_card` | ngay sau đó, do mã sinh | `module_note`, `prerequisites` (Hasse kèm `quote`), `path` (nếu có) |
| `tool_call` | chỉ nhánh agent | `name`, `args`, `result_summary`, `ms` |
| `delta` | khi mô hình stream | `text` (Markdown có nhãn `[S2]`) |
| `final` | hết stream và hậu kiểm xong | đối tượng câu trả lời hoàn chỉnh bên dưới |

**Câu trả lời hoàn chỉnh** lưu lại và gửi trong sự kiện `final`:

```json
{
  "answer_id": "a_…",
  "doc_id": "doc-1",
  "graph_version": 9,
  "current_module": {"module_id": "module_007", "index": 6},
  "route": "vi_sao",
  "status": "answered",
  "answer_markdown": "Định thức cho biết ma trận có khả nghịch hay không [S1]. …",
  "linked_concepts": [
    {"node_id": "node_…", "name": "Ma trận nghịch đảo", "module_index": 6, "relation_to_current": "dang_mo", "match": "ten"}
  ],
  "citations": [
    {"label": "S1", "chunk_id": "c_…", "page": 41, "section_path": ["Chương 2", "2.3 Ma trận nghịch đảo"],
     "module_index": 6, "highlight": {"char_start": 120, "char_end": 245}, "valid": true},
    {"label": "Q1", "kind": "requires_quote", "source": "node_…", "target": "node_…",
     "quote": "…", "chunk_id": "c_…", "page": 40, "valid": true}
  ],
  "module_note": {"later_module_index": null, "text": null},
  "prerequisite_reminder": {
    "shown": true,
    "items": [{"node_id": "node_…", "name": "Định thức", "module_index": 3, "quote_label": "Q1", "soft_reason": null}],
    "disclaimer": "Quan hệ do hệ thống suy ra từ tài liệu, có thể sai."
  },
  "media": [],
  "formula_refs": [{"label": "CT2", "page": 41, "bbox": [72.1, 300.4, 410.0, 330.2]}],
  "flags": {"uncited_sentences": 0, "dropped_labels": 0, "refusal_rule": null},
  "tool_calls": [
    {"name": "why_here", "by": "code", "args": {"concept_id": "node_…"}, "result_tokens": 310, "ms": 4},
    {"name": "search_document", "by": "code", "args": {"query": "…", "scope": "uu_tien_module", "k": 6}, "result_tokens": 1450, "ms": 61}
  ],
  "usage": {"model_id": "gemini-3.1-flash-lite", "model_calls": 1, "input_tokens": 3312, "output_tokens": 341,
            "thought_tokens": 0, "usd": 0.00134, "ttft_ms": 1380, "total_ms": 3120},
  "context_hash": "sha256:…",
  "prompt_hash": "sha256:…",
  "created_at": "2026-10-11T08:00:00Z"
}
```

Bảy ghi chú cho hợp đồng:
- `status` ∈ {`answered`, `partial`, `not_in_document`, `insufficient_context`, `error`}. Câu từ chối vẫn có `citations` rỗng và `route`.
- `relation_to_current` ∈ {`truoc`, `dang_mo`, `sau`, `khong_ro`}; `module_note.later_module_index` khác rỗng khi khái niệm thuộc module sau.
- `tool_calls[].by` ∈ {`code`, `model`}: phân biệt công cụ mã gọi sẵn với công cụ mô hình chọn, để đo riêng nhánh agent.
- `media` chỉ chứa media từ cạnh `confirmed`, mỗi mục có `caption_source`; rỗng chừng nào câu hỏi H2 (mục 6) chưa được trả lời.
- `formula_refs` cho web thay `[CTk]` bằng ảnh gốc, như báo cáo bài giảng.
- `usage` để nhóm ghi USD và giây chờ cho báo cáo; web không hiện cho người học.
- `context_hash` băm khối ngữ cảnh sau khi lắp, để tái lập và để so ablation; câu trả lời không cache chung giữa người học vì phụ thuộc lịch sử
  và module đang mở.

---

## 5. Giao thức đánh giá

### 5.1 Bộ câu hỏi thử

Bảng sau đề xuất 240 câu một lượt và 30 hội thoại ba lượt, tổng 330 lượt hỏi trên sáu cuốn:

| loại câu | số câu | nguồn đáp án | chấm |
|---|---:|---|---|
| định nghĩa ("X là gì?", hỏi bằng lời khác tên) | 50 | chunk dạy, mô tả A5 | RAGAS, trích dẫn |
| vì sao tiên quyết / "có cần học A trước B không" (kiểu T1 của TutorQA; 20 cặp dương, 20 cặp âm) | 40 | nhãn vàng tiên quyết đã có (`artifacts/a8-gold`) ở tài liệu phát triển; không lấy từ chính `requires_edges` | accuracy có/không + RAGAS |
| so sánh hai khái niệm | 30 | hai chunk dạy, cạnh `contrasts_with` nếu có | RAGAS, trích dẫn |
| ví dụ, bài tập | 30 | chunk `bai_tap`, cạnh `example_of` | RAGAS, trích dẫn |
| lộ trình tới mục tiêu (kiểu T2/T3) | 30 | `target_roadmap` tính từ đồ thị vàng nếu có, nếu không thì người duyệt | F1 trên tập module, Kendall τ thứ tự |
| ngoài tài liệu (20 khác hẳn, 10 "gần": cùng lĩnh vực nhưng sách không dạy) | 30 | kiểm bằng tìm chuỗi rằng chunk không chứa | tỉ lệ từ chối đúng |
| khái niệm ở module sau module đang mở | 30 | `module_id` của khái niệm | ghi chú đúng module N (mã kiểm) + RAGAS |
| hội thoại ba lượt (lượt 2–3 có đại từ, câu ngắn) | 30 × 3 | như các loại trên | RAGAS từng lượt, liên kết khái niệm đúng |

Chia theo cuốn tỉ lệ với số khái niệm nhưng có sàn: naive-bayes 20, doc-6 20, nhap-mon-ml 30, xstk 40, doc-1 60, doc-4 70. Với n = 50 một loại, khoảng
tin cậy 95% của một tỉ lệ quanh 0,8 rộng khoảng ±0,11; với 240 câu là khoảng ±0,05.

Cách tạo nhãn:
- Viết đặc tả nhãn chi tiết trước (theo quy trình của dự án), rồi agentic sinh câu hỏi và nhãn bạc. Mỗi mục gồm: loại, câu hỏi, module đang mở giả
  định, `node_id` đích, `chunk_id` tham chiếu, câu trả lời tham chiếu, cờ trả lời được, module N kỳ vọng.
- Câu hỏi không được chép nguyên văn chunk: cấm trùng chuỗi từ 5 âm tiết trở lên với chunk tham chiếu, trừ tên khái niệm. GraphRAG tránh sinh
  câu hỏi trực tiếp từ kho vì lý do này (mục 2.2); proxy ở mục 1.4 cũng cho thấy truy vấn trùng chữ làm BM25 trông tốt hơn thật.
- Một lượt duyệt agentic cho toàn bộ, ghi là "agentic + duyệt agentic". Người duyệt độc lập 60 mục (25%) và đo độ khớp. Kết luận cuối dựa trên
  phần người duyệt.
- Sáu cuốn là tài liệu phát triển. Đề cương yêu cầu đánh giá cuối trên tập kiểm tra dùng một lần; phần đó chạy sau khi đóng băng thiết kế,
  không mở trong lượt này.

### 5.2 Mốc, nhánh so sánh và ablation

Bảng sau liệt kê các nhánh:

| mã | nhánh | mục đích |
|---|---|---|
| M0 | LLM không bằng chứng: hỏi thẳng flash-lite, không ngữ cảnh | mốc bắt buộc của đề cương |
| M1 | RAG thuần: truy hồi lai top 6 trên cả tài liệu, 1 lời gọi, không đồ thị | đóng góp của đồ thị |
| M2 | thiết kế khuyến nghị (C) | hệ thống chính |
| M3 | agent thuần: mọi câu qua vòng gọi công cụ, tối đa 4 vòng | trả lời "quy trình hay agent" |
| M2−H | bỏ khối tiên quyết Hasse và `why_here` | đóng góp của câu trích tiên quyết |
| M2−P | bỏ `path_to` | đóng góp của lộ trình |
| M2−T | bỏ `traverse` | đóng góp của cạnh mở |
| M2−U | bỏ ưu tiên module (xếp hạng toàn cục) | giá trị của "module đang mở" |
| M2+L | lọc cứng `module_index ≤ hiện tại` như spec B2 cũ | cái giá của lọc cứng |
| M2−B, M2−D | chỉ dense; chỉ BM25 | đóng góp từng nhánh truy hồi |
| M2+G | BM25 âm tiết + cặp âm tiết | kiểm proxy mục 1.4 |
| LC | nhồi cả tài liệu, chỉ bốn cuốn nhỏ | mốc ngữ cảnh dài |

Khối nhắc khái niệm nền không ảnh hưởng RAGAS vì đứng ngoài câu trả lời do mô hình viết. Nó được chấm bằng người (mục 5.3).

### 5.3 Độ đo

Bảy nhóm độ đo:
- **RAGAS faithfulness** với ngữ cảnh đã nạp. Thêm "faithfulness với ngữ cảnh tham chiếu" cho mọi nhánh, vì M0 không có ngữ cảnh; nhờ vậy so được
  M0 với các nhánh khác trên cùng thước.
- **Response relevancy** chỉ tính trên câu có `status = answered`. Câu từ chối bị RAGAS cho 0 điểm (mục 2.8), nên phải chấm riêng bằng độ đo từ chối.
- **Context precision và context recall** cho các nhánh có truy hồi, so với câu trả lời tham chiếu.
- **Trích dẫn** kiểu ALCE: citation recall và precision, giám khảo NLI là flash-lite với prompt dịch từ ALCE. Thêm số câu "chưa có nguồn" từ
  hậu kiểm.
- **Từ chối**: recall từ chối trên câu ngoài tài liệu; tỉ lệ từ chối nhầm trên câu trả lời được.
- **Đồ thị**: accuracy câu có/không (T1); F1 tập module và Kendall τ của lộ trình; tỉ lệ ghi chú "module N" đúng; liên kết khái niệm đúng (so
  `node_id` đích).
- **Chi phí và thời gian**: token vào/ra, USD, TTFT, thời gian xong; p50 và p95; chạy ở song song 1 và 8.

Người chấm hai việc trên 60 câu trả lời của M2: nhãn được đỡ/không cho từng claim (để đo độ khớp giữa RAGAS và người), và khối nhắc khái niệm nền
"có ích / trung tính / phiền".

**Cấu hình RAGAS:** ragas 0.4.3 dùng API `ragas.metrics.collections`; `llm_factory("gemini-3.1-flash-lite", provider="google",
client=genai.Client(...))`; `GoogleEmbeddings(model="gemini-embedding-001")`. Cài trong venv riêng của thí nghiệm, không trong `.venv` của dự án.
Chặn mạng tới `api.openai.com` và kiểm nhật ký để chắc không dữ liệu nào rời Gemini. Thử prompt gốc tiếng Anh và bản chuyển ngôn ngữ trên 30 câu;
chọn bản khớp người hơn.

**Thiên lệch của giám khảo:** flash-lite vừa sinh vừa chấm nên có rủi ro tự đề cao (mục 2.7). Dùng độ đo theo từng câu thay vì so cặp; nếu
phải so cặp thì chấm hai thứ tự. Báo cáo số RAGAS là bạc, kèm độ khớp với người. Muốn giám khảo khác họ mô hình thì cần chủ dự án duyệt.

### 5.4 Luật quyết định (viết trước khi đo)

Mọi so sánh dùng bootstrap ghép cặp 95% trên câu hỏi:
- **Đ1. Đồ thị có ích:** giữ công cụ đồ thị nếu so với M1, faithfulness không giảm quá 0,02, và accuracy của nhóm "vì sao" cộng "lộ trình" tăng
  ≥ 0,10 với khoảng tin cậy không chứa 0.
- **Đ2. Agent thay quy trình:** M3 chỉ thay M2 nếu faithfulness và relevancy cùng hơn ≥ 0,03 (khoảng tin cậy không chứa 0), p95 giây chờ
  ≤ 8 giây, và USD ≤ 2 lần M2.
- **Đ3. Nhánh agent trong C:** giữ nếu, trên tập câu bị định tuyến sang agent, nó hơn nhánh A ≥ 0,05 faithfulness hoặc relevancy. Không thì bỏ
  nhánh agent, C còn A.
- **Đ4. Từ chối:** chọn ngưỡng τ sao cho từ chối nhầm ≤ 5%. Đạt nếu recall từ chối ngoài tài liệu ≥ 0,9. Không đạt thì thêm bộ chấm "ngữ cảnh đủ"
  vào đường chờ, chấp nhận thêm một lời gọi.
- **Đ5. Ưu tiên module:** giữ nếu M2 không kém M2−U trên câu thuộc module đang mở, và ghi chú "module N" đúng 100%. M2+L chỉ để báo cáo cái giá
  của lọc cứng.
- **Đ6. Cặp âm tiết:** dùng M2+G nếu context recall tăng ≥ 0,02 và không độ đo nào giảm quá 0,01.
- **Đ7. Tin RAGAS:** chỉ báo số RAGAS như kết quả nếu độ khớp với người trên faithfulness có κ ≥ 0,6; nếu không thì báo số người.
- **Đ8. Nhắc khái niệm nền:** giữ nếu ≥ 70% đánh giá là "có ích" hoặc "trung tính", và ≤ 15% là "phiền".

### 5.5 Làm trước với 0 USD, rồi dự toán

Bốn việc làm trước, không tốn tiền:
1. Dựng bộ câu hỏi thử và nhãn.
2. Đo offline trên bộ đó: liên kết khái niệm đúng; định tuyến đúng; recall@6 của BM25 các biến thể theo `chunk_id` tham chiếu.
3. Kiểm `why_here` và `path_to` đúng với đồ thị; đếm cỡ ngữ cảnh mỗi nhánh.
4. Viết bộ chạy có dry-run in số lời gọi, token và USD dự toán.

Dự toán, tính theo giá 3.1 Flash-Lite Standard (*ước*):

| lượt | nội dung | sinh câu trả lời | giám khảo | tổng |
|---|---|---:|---:|---:|
| 1 | M0, M1, M2 trên 330 lượt hỏi, đủ độ đo | khoảng 1,3 USD | khoảng 6,4 USD | khoảng 8 USD |
| 2 | M3, các ablation, LC; ablation chỉ chấm faithfulness và trích dẫn; context metrics chỉ cho 5 nhánh truy hồi | khoảng 6 USD | khoảng 14 USD | khoảng 20 USD |

Cách tính giám khảo: faithfulness khoảng 2 lời gọi, relevancy 1, trích dẫn 1, context precision 6 (một lời mỗi đoạn), context recall 1; trung bình
khoảng 0,0065 USD một câu trả lời khi đủ độ đo, 0,0036 USD khi bỏ context metrics. Embedding câu hỏi (330 × khoảng 30 token) không đáng kể. Lượt 2
chỉ chạy nếu lượt 1 đạt Đ1 và Đ7. Cả hai lượt phải dry-run và được chủ dự án duyệt; agent nghiên cứu không chạy.

---

## 6. Rủi ro và câu hỏi cho chủ dự án

Bảng sau ghi các rủi ro chính:

| rủi ro | biểu hiện | giảm thiểu |
|---|---|---|
| cạnh tiên quyết sai (độ chính xác bao đóng 0,58–0,64 trên tập giữ lại) | trợ lý nói "phải học A trước B" khi không cần | câu dẫn mềm do mã viết, luôn kèm `Q#`, nút báo sai cho A13; chỉ dùng Hasse, không dùng bao đóng |
| liên kết sai tên một âm tiết | "chất" khớp 297/671 chunk doc-4 | luật độ hiếm (mục 3.2 bước 2); đo liên kết đúng ở mục 5.5 |
| mô hình trả lời thay vì từ chối | bịa từ hiểu biết chung | định tuyến ngoài tài liệu bằng mã, luật hậu kiểm "không có nhãn thì từ chối", Đ4 |
| sách toán thiếu công thức | câu trả lời mơ hồ hoặc tự viết công thức | nhãn `[CTk]` + ảnh gốc như báo cáo bài giảng; cấm mô hình viết công thức |
| RAGAS không hợp tiếng Việt hoặc tự đề cao | số đẹp mà sai | người chấm 60 câu, luật Đ7 |
| RAGAS phạt câu từ chối | relevancy bằng 0 | tách câu từ chối ra độ đo riêng |
| thay đổi API Gemini | tài liệu nay viết mặc định cho Interactions API; structured output cùng công cụ chưa có cho flash-lite; 3.1 Flash-Lite tắt sớm nhất 2027-05-07 | giữ `generateContent`, văn bản có nhãn thay vì JSON, `model_id` trong nhật ký; giá 3.5 Flash-Lite đã tính (+39%) |
| chunk không có module | ưu tiên module bỏ sót | `module_hint` theo chunk dạy đứng trước (phủ 74–99%) |
| dữ liệu giáo trình rời Gemini | RAGAS kéo `openai` làm phụ thuộc | chặn mạng tới OpenAI khi chấm; chỉ dùng bậc trả phí (bậc miễn phí "dùng để cải thiện sản phẩm") |

Các câu hỏi cho chủ dự án, kèm đề xuất:
- **H1. Kiến trúc C với định tuyến bằng mã và nhánh agent tối đa 2 vòng có được chốt không?** Đề xuất: có. M3 vẫn chạy trong đánh giá để trả lời
  câu hỏi "agent hay quy trình" bằng số.
- **H2. Media chưa gắn module có được hiện không?** Spec A12 chặn media chưa gắn module, nhưng lý do chặn (lọc theo tiến độ) đã bị bỏ ngày
  2026-10-11. Đề xuất: cho hiện media từ cạnh `confirmed` (15, 3, 4, 5, 5 và 0 khái niệm), ghi "mô tả do máy sinh" khi cần. Chưa trả lời thì
  công cụ trả rỗng.
- **H3. Nhiệt độ của trợ lý.** Bài giảng đã chốt 0. Câu trả lời trợ lý không cache nên không cần 0 để tái lập; tài liệu Gemini 3 khuyên giữ mặc
  định (theo báo cáo bài giảng). Đề xuất: 0 trong lượt đánh giá để giảm phương sai, và một nhánh nhỏ ở nhiệt độ mặc định để so.
- **H4. Cỡ bộ câu hỏi thử và người duyệt:** 330 lượt, người duyệt độc lập 60 mục. Có đủ người không, hay giảm còn 240 câu một lượt?
- **H5. Ngân sách đánh giá:** lượt 1 khoảng 8 USD, lượt 2 khoảng 20 USD (mục 5.5). Có duyệt dry-run lượt 1 không?
- **H6. Có cho thêm `module_hint` vào A12** (gán chunk không dạy khái niệm theo chunk dạy đứng trước) không? Đây là thay đổi Pha A nhỏ, không gọi
  mô hình và không phải embed lại.
- **H7. Embed mô tả A5** của mọi khái niệm để liên kết câu hỏi không gọi tên: 846 mô tả × khoảng 50 token, chi phí không đáng kể. Có cho làm
  cùng lượt 1 không?

---

## 7. Nguồn

Mọi nguồn được mở ngày 2026-10-11. Số trong ngoặc vuông cuối dòng là số của danh mục đề cương nếu trùng.

**Bài báo**
1. R. Yang *et al.*, "Leveraging large language models for concept graph recovery and question answering in NLP education," arXiv:2402.14293
   (v1), 2024. — *đọc toàn văn*. [18]
2. D. Edge *et al.*, "From local to global: A GraphRAG approach to query-focused summarization," arXiv:2404.16130 (v2, 2025-02-19). — *đọc
   toàn văn* (thân bài, không đọc phụ lục). [23]
3. S. Jeong, J. Baek, S. Cho, S. J. Hwang, and J. C. Park, "Adaptive-RAG: Learning to adapt retrieval-augmented large language models through
   question complexity," in *Proc. NAACL-HLT 2024 (Long Papers)*, pp. 7036–7050. — *đọc toàn văn*; Bảng 1 đối chiếu bằng ảnh trang.
4. B. Jiménez Gutiérrez, Y. Shu, Y. Gu, M. Yasunaga, and Y. Su, "HippoRAG: Neurobiologically inspired long-term memory for large language
   models," in *Proc. NeurIPS 2024*; arXiv:2405.14831 (v3). — *đọc toàn văn* phần chính và phụ lục G; Bảng 4, 5 đối chiếu bằng ảnh trang.
5. S. Yao *et al.*, "ReAct: Synergizing reasoning and acting in language models," in *Proc. ICLR 2023*; arXiv:2210.03629. — *chỉ đọc tóm tắt*.
6. H. Trivedi, N. Balasubramanian, T. Khot, and A. Sabharwal, "Interleaving retrieval with chain-of-thought reasoning for knowledge-intensive
   multi-step questions," in *Proc. ACL 2023*, 2023.acl-long.557. — *chỉ đọc tóm tắt*; kiểm trang ACL Anthology.
7. A. Asai, Z. Wu, Y. Wang, A. Sil, and H. Hajishirzi, "Self-RAG: Learning to retrieve, generate, and critique through self-reflection," in
   *Proc. ICLR 2024*; arXiv:2310.11511. — *chỉ đọc tóm tắt*; nơi đăng lấy từ danh mục tham khảo của bài [3].
8. Z. Guo *et al.*, "LightRAG: Simple and fast retrieval-augmented generation," arXiv:2410.05779, 2024. — *chỉ đọc tóm tắt*.
9. J. Sun *et al.*, "Think-on-Graph: Deep and responsible reasoning of large language model on knowledge graph," in *Proc. ICLR 2024*;
   arXiv:2307.07697. — *chỉ đọc tóm tắt*.
10. X. He *et al.*, "G-Retriever: Retrieval-augmented generation for textual graph understanding and question answering," arXiv:2402.07630,
    2024. — *chỉ đọc tóm tắt*; nơi đăng hội nghị **chưa xác minh**.
11. B. Peng *et al.*, "Graph retrieval-augmented generation: A survey," arXiv:2408.08921, 2024. — *chỉ đọc tóm tắt*.
12. H. Han *et al.*, "Retrieval-augmented generation with graphs (GraphRAG)," arXiv:2501.00309, 2025. — *chỉ đọc tóm tắt*.
13. H. Joren, J. Zhang, C.-S. Ferng, D.-C. Juan, A. Taly, and C. Rashtchian, "Sufficient context: A new lens on retrieval augmented generation
    systems," in *Proc. ICLR 2025*; arXiv:2411.06037. — *đọc phần liên quan* (tóm tắt, mở đầu, mục 4–5.1).
14. J. Chen, H. Lin, X. Han, and L. Sun, "Benchmarking large language models in retrieval-augmented generation," in *Proc. AAAI 2024*;
    arXiv:2309.01431. — *chỉ đọc tóm tắt*.
15. T. Gao, H. Yen, J. Yu, and D. Chen, "Enabling large language models to generate text with citations," in *Proc. EMNLP 2023*;
    arXiv:2305.14627. — *đọc phần liên quan* (định nghĩa citation recall/precision), từ bản tải của báo cáo tên module.
16. L. Zheng *et al.*, "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena," in *NeurIPS 2023 Datasets and Benchmarks*; arXiv:2306.05685.
    — *đọc phần liên quan*, từ bản tải của báo cáo tên module.
17. A. Panickssery, S. R. Bowman, and S. Feng, "LLM evaluators recognize and favor their own generations," arXiv:2404.13076, 2024. — *chỉ đọc
    tóm tắt*.
18. N. F. Liu *et al.*, "Lost in the middle: How language models use long contexts," *Trans. ACL*; arXiv:2307.03172. — *chỉ đọc tóm tắt*.
19. X. Ma, Y. Gong, P. He, H. Zhao, and N. Duan, "Query rewriting for retrieval-augmented large language models," in *Proc. EMNLP 2023*;
    arXiv:2305.14283. — *chỉ đọc tóm tắt*.
20. Z. Li *et al.*, "Retrieval augmented generation or long-context LLMs? A comprehensive study and hybrid approach," in *Proc. EMNLP 2024
    Industry Track*; arXiv:2407.16833. — *chỉ đọc tóm tắt*.
21. S. Es, J. James, L. Espinosa-Anke, and S. Schockaert, "RAGAs: Automated evaluation of retrieval augmented generation," in *Proc. EACL 2024
    System Demonstrations*, pp. 150–158; arXiv:2309.15217. — *chỉ đọc tóm tắt*; định nghĩa độ đo lấy từ tài liệu chính thức. [28]
22. T. Vu, D. Q. Nguyen, D. Q. Nguyen, M. Dras, and M. Johnson, "VnCoreNLP: A Vietnamese natural language processing toolkit," in *Proc. NAACL
    2018 Demonstrations*. — *đọc phần liên quan* (số F1 tách từ 97,90), từ bản tải của báo cáo tên module.
23. D. Wood, J. S. Bruner, and G. Ross, "The role of tutoring in problem solving," *J. Child Psychology and Psychiatry*, vol. 17, no. 2,
    pp. 89–100, 1976, doi: 10.1111/j.1469-7610.1976.tb00381.x. — *chỉ kiểm siêu dữ liệu* (Crossref).
24. K. VanLehn, "The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems," *Educational
    Psychologist*, vol. 46, no. 4, pp. 197–221, 2011, doi: 10.1080/00461520.2011.611369. — *chỉ kiểm siêu dữ liệu* (Crossref). [13]
25. J.-P. Doignon and J.-C. Falmagne, "Knowledge spaces and learning spaces," arXiv:1511.06757, 2015. — không đọc lại trong lượt này; dẫn theo
    đề cương. [10]

**Tài liệu chính thức và mã nguồn**
- Google, Gemini API (bản `generateContent`): [Function calling](https://ai.google.dev/gemini-api/docs/generate-content/function-calling)
  (cập nhật 2026-10-09); [Thought signatures](https://ai.google.dev/gemini-api/docs/generate-content/thought-signatures) (2026-09-04);
  [Thinking](https://ai.google.dev/gemini-api/docs/generate-content/thinking) (2026-10-09);
  [Structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output) (2026-10-09);
  [Text generation](https://ai.google.dev/gemini-api/docs/generate-content/text-generation) (2026-10-09);
  [Embeddings](https://ai.google.dev/gemini-api/docs/embeddings) (2026-10-09); [Pricing](https://ai.google.dev/gemini-api/docs/pricing)
  (2026-10-09). Trang [Thinking](https://ai.google.dev/gemini-api/docs/thinking) bản Interactions API (2026-10-09) đọc để so. — *đọc phần
  liên quan*.
- RAGAS: [Faithfulness](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/),
  [Response Relevancy](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/answer_relevance/),
  [Context Precision](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/),
  [Context Recall](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/),
  [Gemini integration](https://docs.ragas.io/en/stable/howtos/integrations/gemini/). — *đọc toàn trang*.
- Mã nguồn ragas 0.4.3 (sdist từ [PyPI](https://pypi.org/project/ragas/), phát hành 2026-01-13): `metrics/collections/answer_relevancy/metric.py`,
  `embeddings/google_provider.py`. — *đọc phần liên quan*.

**Nguồn trong dự án**
- `doc/spec-addendum.md` (A11, A12, B1–B4); `doanchuyennganh/decuong/de-cuong-do-an-chuyen-nganh.md`.
- `src/doc2roadmap/domain/retrieval.py`, `src/doc2roadmap/application/use_cases/index_document.py`,
  `src/doc2roadmap/application/use_cases/build_roadmap.py` (`target_roadmap`), `src/doc2roadmap/presentation/cli/main.py` (`roadmap-target`).
- Artifact sáu cuốn ở bảng mục 4 của tệp bối cảnh chung (`graph.json`, `chunks.json`, `retrieval.json`).
- [Kết quả tập giữ lại v3](ket-qua-tap-giu-lai-v3-2026-10-04.md), [nghiên cứu Gemini v4](nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md),
  [báo cáo bài giảng](nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md), [báo cáo tên module](nghien-cuu-ten-va-mo-ta-module-2026-10-11.md).
- Script đo (thư mục tạm của phiên, không vào kho): `c_hien_trang.py`, `d_bo_sung.py`, `f_bm25.py`, `g_lien_ket.py`, `h_toc_do.py`.
