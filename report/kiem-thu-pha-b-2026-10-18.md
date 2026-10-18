# Kiểm thử Pha B sau bàn giao: vé 01–18 và 24 (2026-10-18)

**Người kiểm:** Claude (phiên Pha B). **Đầu vào:**
- [bàn giao của nhân viên](pha-b-ban-giao-2026-10-15.md), cùng các báo cáo nhánh `pha-b-*-2026-10-15.md`;
- [bàn giao từ phía pha A](ban-giao-pha-b-sau-t01-2026-10-18.md).

**Chi phí của lượt kiểm:** 0 USD. Không gọi mô hình hay embedding.

**Tập giữ lại:** không mở `d01-t01`, `d01-t02`. Mọi script chỉ nạp sáu cuốn phát triển. Không đọc `cache` của `artifacts/phase_b/live.json`.

## 1. Kết luận

**Phần hạ tầng đạt.** Gồm kho và sổ chi, giới hạn dùng chung, công cụ tra đồ thị, nhãn nguồn ánh xạ về offset gốc, ảnh công thức, A12, chỉ mục khái
niệm, hợp đồng JSON, trang xem thử, và an ninh của máy chủ cục bộ.

**Phần nội dung chưa đạt.** Lỗi gom thành bốn nhóm, mỗi nhóm một vé sửa:
- **Hậu kiểm trích dẫn (vé 09, 18):** để lọt khẳng định không có nguồn.
  - Ở trợ lý, câu có số mà không có nhãn vẫn qua nếu đứng cạnh một câu có nhãn.
  - Ở tài liệu theo yêu cầu, câu mất nhãn vẫn nằm trong bài, kể cả định nghĩa.
  - Nhãn ghép `[S3, S5]` không được kiểm.
  - Khối "ngoài tài liệu" chứa cả định nghĩa.
  - → [SA-25](../task/sau-a10/25-hau-kiem-trich-dan-theo-cau.md).
- **Bài giảng (vé 11, 12, 13):**
  - Ý lặp lại mà luật K6 không bắt.
  - Bản lùi trộn ý LLM đã stream với câu trích, nên một ý lặp tới 3 lần.
  - Không ghi bài hỏng vì luật nào.
  - `usage` báo 0 USD ở mọi bài phải sửa lại hoặc rơi về bản lùi.
  - Đường trích câu sinh ý rác: mẩu vụn ở công thức, `[formula]`, gạch đầu dòng slide.
  - → [SA-26](../task/sau-a10/26-bai-giang-chong-lap-ban-lui-sach.md).
- **Quiz LLM (vé 16):** gần như chưa chạy được.
  - Lượt thật V2 có 34 lời gọi sinh nhưng 0 câu qua luật. Vì vậy lời gọi kiểm chưa chạy lần nào.
  - Cả nhóm chỉ có 1 câu LLM được chấp nhận (V4).
  - Không ghi câu bị loại vì luật nào.
  - → [SA-27](../task/sau-a10/27-quiz-llm-do-luat-loai-va-nghiem-thu-lai.md).
- **Tên module (vé 05, 06):**
  - Tên đạt.
  - Mô tả LLM thì 132/154 chỉ là danh sách tên khái niệm, vì prompt bảo "chỉ liệt kê".
  - Khuôn mô tả của đường lùi lộ mã `module_015` cho người học (6 module).
  - → [SA-28](../task/sau-a10/28-ten-module-mo-ta-thanh-cau.md).

**Lượt thật còn thiếu:**
- trợ lý: vé 08 (khoảng 10 câu) và vé 10 (khoảng 20 câu), mới chạy 6 câu, chưa có TTFT, số vòng, gọi công cụ sai;
- bài giảng: vé 13, chưa có giây tới `skeleton`, tới ý đầu, tới `final`;
- quiz: vé 16, chưa có lượt 2 module.

Các lượt này chạy sau SA-25 và SA-26, để không trả tiền hai lần.

**Bước sau:** chỉ sang đánh giá 20–23 khi bốn vé sửa xong. Đánh giá trên nội dung còn lỗi đã biết thì phí tiền và công chấm.

**Điều kiện trước, phải làm ngay:** khoảng 4.000 dòng mã Pha B **chưa commit**. Gồm trợ lý, quiz, tài liệu, chỉ mục khái niệm, ảnh công thức, bộ
lắp `composition_phase_b.py`, adapter Gemini Pha B, CLI, trang xem thử, và 13 tệp test. Phía pha A đã commit một phần (`common`, `lectures`,
`naming`, `retrieval`) trong `f4871fd`. Nhân viên commit nốt phần còn lại trước khi nhận vé sửa.

## 2. Cách kiểm

| Việc | Kết quả |
|---|---|
| Chạy test Pha B, đồ thị học, adapter, ảnh công thức, trang xem thử, kiến trúc | 124 qua, 0 hỏng |
| Thử sửa sai 11 chỗ canh giữ (khôi phục nguyên văn sau mỗi lần) | 5 bị test bắt; 1 tương đương; **5 test thiếu** (mục 4) |
| Đọc toàn bộ tên và mô tả module trên đồ thị mới nhất của sáu cuốn | 162 module |
| Đọc bài giảng LLM của lượt thật nhóm 2 | 12 bài |
| Đọc bài giảng trích câu (mẫu của nhân viên) | 10 bài |
| Đọc tài liệu theo yêu cầu của lượt thật | 6 tài liệu |
| Soát bằng mắt ảnh công thức (bảng mẫu của nhân viên) | 20 ảnh doc-1, 20 ảnh xstk |
| Dò hậu kiểm của trợ lý trên đồ thị doc-6 thật | 1 ca lọt (mục 3.4) |
| Soát máy chủ xem thử | localhost, Host/Origin, sáu cuốn, không lộ cache |

## 3. Phát hiện

### 3.1 Tên và mô tả module (vé 05, 06)

Đồ thị đọc: doc-1 v53, nhap-mon-ml v46, naive-bayes v45, doc-6 v17, xstk-ch3-1 v64, doc-4 v23. Đây là bản A10 hoàn tất mới nhất. Ba bản doc-1,
xstk, doc-4 do phía pha A chạy lại bằng chuỗi gộp, khâu tên Pha B chạy kèm.

| Cuốn | Module | Tên LLM | Đường lùi | Mô tả LLM chỉ là danh sách tên | Mô tả lộ `module_…` | Thiếu `section_code` |
|---|---:|---:|---:|---:|---:|---:|
| doc-1 | 33 | 32 | 1 | 29/32 | 1 | 0 |
| nhap-mon-ml | 15 | 14 | 1 | 13/14 | 0 | 8 |
| naive-bayes | 5 | 5 | 0 | 5/5 | 0 | 5 |
| doc-6 | 4 | 4 | 0 | 4/4 | 0 | 4 |
| xstk-ch3-1 | 14 | 13 | 1 | 12/13 | 1 | 5 |
| doc-4 | 91 | 86 | 5 | 69/86 | 4 | 53 |
| **Tổng** | **162** | **154** | **8** | **132/154 (86%)** | **6** | **75** |

**Tên: đạt.** Phần lớn là tên học thuật đúng nội dung, ví dụ "Hạng của ma trận", "Kiểm định giả thiết về tính độc lập", "Quy luật phủ định của phủ
định". Lỗi gặp khi đọc:
- **Tên chung, không nói nội dung:**
  - doc-1 module 30 "Các định nghĩa": dạy trị riêng, véctơ riêng;
  - doc-4 module 12 "Tư tưởng triết học": dạy Đạo, Vô vi.
- **Tên lệch trọng tâm:**
  - doc-1 module 4 "Đồ thị của ánh xạ": module dạy ánh xạ, tập nguồn, tập đích;
  - doc-1 module 11 "Công thức khai triển định thức theo hàng 1": module dạy định thức.
- **Trùng tên trong cùng cuốn:** nhap-mon-ml module 9 và 13 cùng "Vài vấn đề cần biết khi dùng học máy". Cả hai cùng mục 1.3, cách nhau 4 nên luật
  ±2 không bắt.
- **Viết thường chữ đầu:** doc-4 module 85 "tính độc lập tương đối của nghệ thuật".

**Mô tả: chưa đạt mục đích.**
- 132/154 mô tả LLM chỉ chép lại tên khái niệm, ví dụ "Phụ thuộc hàm, Dạng chuẩn." hay "Đồ thị của ánh xạ.". Trang lộ trình vốn đã hiện danh sách khái
  niệm, nên mô tả kiểu này không thêm thông tin gì.
- Nguyên nhân là prompt: "Mô tả 1–2 câu ngắn chỉ liệt kê tên khái niệm nguyên vẹn như format_example".
- Prompt hẹp lại có lẽ để qua luật từ vựng. Nhưng mô tả A5 đã nằm trong từ vựng được phép. Bằng chứng là 22 mô tả còn lại viết được thành câu thật, ví
  dụ xstk module 10: "Độ chính xác trong ước lượng tỉ lệ là đại lượng đo lường sai số ε của ước lượng tỉ lệ p."

**Khuôn mô tả của đường lùi lộ mã kỹ thuật:** "Cần trước: module_015, module_023." ở 6 module (doc-1 m24, xstk m12, doc-4 m8, m29, m34, m64).
Báo cáo nhóm 1 ghi "không mô tả nào chứa ID kỹ thuật"; điều đó đúng trên các bản cũ nhưng sai trên bản hiện hành.

### 3.2 Bài giảng (vé 11, 12, 13)

**Lượt thật nhóm 2:** 12 bài, 7 `ready`, 5 `fallback`. Mỗi bài `fallback` đã tốn hai lời gọi.

| Lỗi | Ca thật |
|---|---|
| **Lặp ý, K6 không bắt** | doc-1 "Tập hợp" (`ready`): 4 ý giải thích, ý 1 trùng ý 3, ý 2 trùng ý 4 |
| **Bản lùi trộn ý LLM với câu trích** | xstk "Tỉ lệ tổng thể": 7 ý, câu "các phần tử chia làm hai loại: có tính chất A…" xuất hiện 3 lần; nhap-mon-ml "Mô hình sinh": 9 ý, định nghĩa lặp 2 lần |
| **`usage` báo 0** | mọi bài phải sửa lại hoặc rơi bản lùi (6/12) báo 0 token, 0 USD, dù sổ chi có 2 dòng |
| **Không ghi lý do hỏng** | 5 bài `fallback` chỉ có cờ `ban_trich_cau`; vé 12 cần tỉ lệ bỏ ý theo từng luật, hiện không đo được |
| **Neo sai làm bài sai** | doc-4 "Hình thái ý thức xã hội": câu định nghĩa thật ra nói về triết học, và bài giảng viết "Hình thái ý thức xã hội là cách thức tồn tại của triết học" |
| **"Ví dụ" không phải ví dụ** | doc-4 "Hình thái ý thức xã hội", mục ví dụ: "Triết học được hiểu là hệ thống tri thức lý luận chung nhất…" |

Lỗi `usage` có nguyên nhân rõ:
- `_aggregate_usage` đọc khoá kiểu Gemini (`promptTokenCount`) trên dòng sổ chi đã chuẩn hoá, nơi khoá là `input_tokens`.
- Hệ quả: trang xem thử và mọi số đo vé 13, 21 lấy từ `usage` đều sai ở các bài này.

**Bài trích câu (vé 11).** Phần chạy máy đạt: 915 khái niệm, 5.687 đoạn trích đúng offset, 3 ca `no_source`. Nhưng đọc 10 bài mẫu thì 6 bài dở:

| Lỗi | Ca |
|---|---|
| Bộ tách câu cắt vụn chỗ có dấu chấm trong công thức | doc-1 "Nhân và ảnh": ý ", e m } của Kerf ." và ", e m , v 1 , ." |
| Ý chỉ là dấu giữ chỗ | naive-bayes "Laplace Smoothing": 3/4 ý là `[formula]` |
| Gạch đầu dòng slide và ký tự font ký hiệu | doc-6: "u Tính chủ quyền dữ liệu.", "u Mức ngoài"; naive-bayes: " Probabilistic Graphical Model" |
| Câu cụt ở ranh giới chunk | nhap-mon-ml "Làm sạch dữ liệu": "…có thể tạo ra sự nhầm lẫn trong quy" |
| Mất gạch ngang trên ký hiệu nên câu thành sai | doc-1: "ρ ( A ) = ρ ( A ) : hệ phương trình vô nghiệm" (bản gốc có Ā) |
| Câu định nghĩa lặp làm ý đầu | nhap-mon-ml, doc-6 |

Bộ tách câu `_sentences` là regex `(?<=[.!?])\s+`. Domain đã có `UnicodeSentenceSplitter`, đang dùng ở trợ lý.

Đường trích câu quan trọng vì nó là bản lùi của 5/12 bài LLM, và là bài duy nhất khi không có mô hình.

**Vé 13:** chưa thấy số giây tới `skeleton`, tới ý đầu và tới `final` ở p50, p90 trên lượt thật.

### 3.3 Tài liệu theo yêu cầu (vé 18)

Lượt thật: 6 tài liệu, 4 `ready`, 2 `failed` (`no_valid_citations`). Đọc cả 6:
- **Câu mất nhãn vẫn ở lại trong bài.**
  - Hậu kiểm chỉ xoá nhãn không hợp lệ, không xoá câu mang nhãn đó.
  - Kết quả: nhiều câu kết thúc bằng " ." và không có nguồn, gồm cả định nghĩa. Ví dụ doc-4: "Ý thức xã hội là mặt tinh thần của đời sống xã hội…
    phản ánh tồn tại xã hội ." Một ví dụ khác là đoạn "Ghi chú thêm" của nhap-mon-ml.
  - Spec mục 9 ghi "hậu kiểm bằng cùng luật" như trợ lý; mã chưa làm.
- **Nhãn ghép không được kiểm:** "[S3, S5]" không khớp regex `\[([A-Z]+\d+)\]`, nên ở nguyên trong bài mà không ai kiểm.
- **Khối ngoài tài liệu không có luật nội dung nào:**
  - naive-bayes: khối ngoài tài liệu là một định nghĩa ("Supervised learning… là một nhánh của học máy…"), điều spec cấm.
  - doc-6: khối là lời dặn ôn thi.
  - Ba tài liệu khác: câu sáo rỗng, không phải ví dụ.
- **Tiêu đề lặp:** 4/6 tài liệu có hai dòng `#`, vì `_render` thêm tiêu đề trong khi mô hình đã viết sẵn.

### 3.4 Trợ lý (vé 08, 09, 10)

**Test vòng lặp đạt.** Đã thử bỏ ép `NONE` ở vòng 5 thì test đỏ.

**Hậu kiểm cắt theo đoạn, không theo câu.**
- Đơn vị kiểm là đoạn tách ở xuống dòng, hoặc sau dấu `]` khi theo sau là khoảng trắng.
- Tiếng Việt thường viết "…[S1]. Câu sau". Lúc đó dấu `]` đi liền dấu chấm, nên không tách, và cả đoạn được tính là "có nguồn".
- Dò trên đồ thị doc-6 thật: "CSDL là tập hợp dữ liệu có cấu trúc [S1]. Một hệ quản trị có đúng 7 thành phần bắt buộc." qua hậu kiểm nguyên vẹn,
  không cờ.
- Tiêu chí vé 09 "câu có số mà không có nhãn bị gắn cờ" chỉ đúng khi câu đó đứng riêng một đoạn.

**Khối ngoài tài liệu chặn định nghĩa bằng từ khoá** ("định nghĩa", "theo sách"). Câu "X là …" lọt qua (cùng lỗi với 3.3).

**Lượt thật:** mới có 6 câu trên 6 cuốn (4 `answered`, 2 `insufficient_context`). Thiếu:
- vé 08: khoảng 10 câu doc-6 và naive-bayes, kèm USD/câu, TTFT và tổng giây p50/p90, số vòng, gọi công cụ sai;
- vé 10: khoảng 20 câu doc-1 và nhap-mon-ml, kèm tỉ lệ gọi công cụ sai theo từng công cụ. Luật báo chủ dự án khi quá 10% chưa áp được vì chưa có số.

### 3.5 Quiz (vé 15, 16, 17)

**Quiz điền khuyết đạt.** Độ phủ:

| Cuốn | Tỉ lệ |
|---|---:|
| doc-4 | 84,5% |
| xstk | 79,2% |
| nhap-mon-ml | 69,3% |
| doc-1 | 67,4% |
| naive-bayes | 33,3% |
| doc-6 | 0% |

doc-6 bằng 0 vì 28/28 khái niệm của đồ thị v17 (chuỗi v3) không có neo. Đây là dữ liệu đầu vào, không phải lỗi quiz.

Test chống lộ đáp án bắt được sửa sai.

**Quiz LLM chưa đạt.** Bốn lượt V1–V4 tốn 0,29 USD:
- V2: 34 lời gọi sinh, 0 câu qua luật cục bộ, 0 lời gọi kiểm;
- V4: 1 khái niệm, 1 câu `generator=llm`.

Vì không ghi câu bị loại vì luật nào, không ai biết luật nào loại nhiều nhất. Đọc mã thì thấy một nghi phạm lớn:
- `_rules_pass` loại mọi câu có tên khái niệm trong đề (`if self._name(concept) in stem: return False`).
- Luật này chỉ đúng khi đáp án chính là tên khái niệm. Nó loại luôn mọi câu hỏi kiểu "Trong tài liệu, X dùng để làm gì?".
- Đây là giả thuyết. SA-27 đo bằng cách phát lại các phản hồi đã ghi, 0 USD, trước khi sửa.

### 3.6 Ảnh công thức (vé 04)

Đạt.
- doc-1: 20/20 ảnh cắt đúng vùng, 3 ảnh dính một dòng chữ kề (trang 30, 62, 86).
- xstk: ảnh đúng toạ độ, nhưng khoảng 6/20 vùng không phải công thức. Gồm bảng tần số, chuỗi phím máy tính "SHIFT → 2 → 1", và chữ "Giải". Đây là lỗi
  gán nhãn công thức ở A1; báo lại phía pha A, không sửa ở Pha B.
- Chữ thô của công thức doc-1 nhiều chỗ là rác ("A = □ □ □ □ a 11 a 12 ···"). Điều này xác nhận quyết định đưa ảnh gốc cho người học.

nhap-mon-ml thiếu PDF gốc nên chưa cắt được 1 công thức.

### 3.7 Trang xem thử (vé 24)

Đạt:
- chỉ nghe `127.0.0.1`;
- kiểm `Host` và `Origin`;
- chỉ liệt kê sáu cuốn;
- tham số mã ảnh và mã tài liệu có kiểm dạng;
- không điểm cuối nào trả cache tên.

Hai ghi chú:
- `/api/usage` không truyền `doc_id` thì cộng cả 177 dòng `module_title` của T-01 vào tổng. Chỉ là số, không lộ nội dung, nhưng làm sai tổng hiện
  trên trang.
- Số USD của bài giảng trên trang sai theo lỗi `usage` ở 3.2.

### 3.8 Giá tiền viết cứng

Bảng giá dùng chung có ở `prerequisite_prompt.PRICING_USD_PER_MILLION`. Nhưng Pha B viết cứng `0.25`/`1.5` ở sáu tệp:
- trợ lý, tài liệu, bài giảng, tên, chỉ mục khái niệm;
- riêng quiz và truy hồi dùng bảng chung.

Hệ quả:
- đổi giá ở một chỗ thì trần chi của trợ lý và tài liệu tính sai;
- chỉ mục khái niệm tính embedding bằng giá đầu vào của flash-lite. Cần kiểm lại giá embedding hiện hành.

## 4. Thử sửa sai

| # | Chỗ sửa sai | Kết quả | Vé |
|---|---|---|---|
| M1 | đề quiz kèm `is_correct` | bị bắt | 15, 17 |
| M2 | `traverse` trả cả cạnh `requires` trong `open_edges` | **sống** — test hiện có chỉ dùng cạnh mở giống hệt một cạnh cứng | 02, 10 |
| M3 | `get_media` trả media chưa `confirmed` | bị bắt | 02, 10 |
| M4 | vòng cuối của trợ lý không ép `NONE` | bị bắt | 08 |
| M5 | trợ lý giữ nhãn bịa khi cùng câu có nhãn thật | **sống** | 09 |
| M5b | trợ lý giữ đơn vị không nhãn | bị bắt | 09 |
| M6 | tài liệu giữ nhãn bịa | **sống** | 18 |
| M7 | bài giảng bỏ kiểm câu trích nguyên văn | sống nhưng **tương đương**: `SourceRegistry.citation` kiểm lại lần hai | 12 |
| M8 | tên bỏ luật từ vựng | bị bắt | 06 |
| M9 | bài giảng bỏ K6 | **sống** | 12 |
| M10 | quiz nhận câu khi lời gọi kiểm chọn sai đáp án | **sống** — test hiện có trả `distractor_verdicts` rỗng nên câu bị loại vì lý do khác | 16 |

Năm test thiếu (M2, M5, M6, M9, M10) được đưa vào tiêu chí của các vé sửa.

## 5. Phán xét theo vé

| Vé | Phán xét | Còn thiếu |
|---|---|---|
| 01 | đạt | giá viết cứng (3.8) → SA-25 |
| 02 | **chưa đạt** | test cạnh mở `requires` (M2); chưa báo số tên bị chặn vì "tên phổ biến" (ngưỡng 0,25) ở mỗi cuốn |
| 03 | đạt | chưa báo giây mỗi truy vấn trên doc-4 |
| 04 | đạt | báo pha A: vùng không phải công thức ở xstk |
| 05 | **chưa đạt** | khuôn mô tả lộ `module_…` → SA-28 |
| 06 | **chưa đạt** | mô tả chỉ là danh sách; tên chung; trùng tên trong cuốn → SA-28 |
| 07 | đạt | — |
| 08 | **chưa nghiệm thu** | lượt thật khoảng 10 câu |
| 09 | **chưa đạt** | hậu kiểm theo câu; M5 → SA-25 |
| 10 | **chưa đạt** | M2; lượt thật khoảng 20 câu |
| 11 | **chưa đạt** | chất lượng trích câu → SA-26 |
| 12 | **chưa đạt** | K6, bản lùi, `usage`, lý do hỏng; M9 → SA-26 |
| 13 | **chưa nghiệm thu** | số giây trên lượt thật |
| 14 | đạt | — |
| 15 | đạt | — |
| 16 | **chưa đạt** | → SA-27 |
| 17 | đạt | — |
| 18 | **chưa đạt** | → SA-25 |
| 24 | đạt | tổng USD gộp T-01 (3.7) |

## 6. Báo lại phía pha A

Ba việc, chỉ báo, Pha B không sửa:
- **doc-4 v23, "Hình thái ý thức xã hội":**
  - Khái niệm nằm ở module 1, với câu neo ở chương mở đầu: "…triết học… tồn tại với tư cách là một hình thái ý thức xã hội".
  - Phần dạy thật của khái niệm ở chương ý thức xã hội (module 84).
  - Đây là dạng "lần nhắc đầu" bị coi là chỗ dạy. Bài giảng và quiz kế thừa lỗi này.
- **xstk:** nhiều nút công thức thật ra là bảng, chuỗi phím máy tính hay chữ "Giải".
- **doc-6 v17 (chuỗi v3):** 28/28 khái niệm không có neo. Quiz điền khuyết vì vậy ra 0 câu, và bài giảng không có câu định nghĩa.
  - Chạy lại doc-6 bằng chuỗi gộp có thể sửa, nhưng tốn tiền.
  - Đây là quyết định của chủ dự án.

## 7. Thứ tự đề xuất

1. Nhân viên commit mã Pha B còn lại.
2. SA-25, SA-26, SA-27, SA-28 chạy song song được, vì chạm các tệp khác nhau. Chỉ có `common.py` và bảng giá là chung, nên SA-25 làm phần giá trước.
3. Sau SA-25 và SA-26: một lượt thật gộp cho vé 08, 10, 13, dry-run trước, chủ dự án duyệt.
4. Sau SA-27: lượt thật vé 16.
5. Rồi mới tới đánh giá 20–23. Đánh giá ghim phiên bản đồ thị hiện hành, và ghi `upstream_chain` của từng cuốn, vì ba cuốn còn chuỗi v3.
