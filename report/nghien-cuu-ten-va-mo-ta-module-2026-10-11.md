# Nghiên cứu: đặt tên và viết mô tả ngắn cho module của lộ trình — 2026-10-11

Báo cáo trả lời câu hỏi: cách nào tốt nhất để đặt tên và viết mô tả 1–2 câu cho một module (3–8 khái niệm liền nhau trong dãy học sinh từ
giáo trình tiếng Việt), cho cả đồ án (được dùng LLM) lẫn seminar (Pha A không dùng LLM sinh văn bản). Mọi nguồn được mở ngày 2026-10-11.
Bài đọc toàn văn được tải PDF về thư mục tạm và đọc bằng `pdftotext`; bảng số quan trọng được đối chiếu bằng ảnh trang. Truy vấn tìm kiếm chỉ
dùng từ khoá chung; không có tên khái niệm, nội dung giáo trình hay dữ liệu dự án nào được gửi ra ngoài. Phần hiện trạng chỉ đọc artifact
của sáu cuốn được giao bằng script cục bộ, và phát lại các hàm kiểm thuần của `module_titles.py` trên nhật ký có sẵn. Không gọi Gemini hay
API trả tiền, không chạy lệnh dự án nào gọi mô hình, không sửa mã.

Báo cáo dùng các quy ước sau:
- Nhận định từ văn liệu có số tham chiếu [n] trỏ về mục [Nguồn](#9-nguồn), ghi theo IEEE kèm mức đọc: *đọc toàn văn*, *đọc phần liên quan*,
  *chỉ đọc tóm tắt*, *chỉ kiểm siêu dữ liệu*, hoặc **chưa xác minh**.
- "Số đo dự án" dẫn về artifact trong repo; script đo nằm ở thư mục tạm của phiên, không đưa vào kho.
- Đoạn mở đầu bằng *Suy luận:* là ý kiến của người viết, chưa có thí nghiệm.
- "Từ" khi đếm độ dài là token tách bằng khoảng trắng, như mã hiện tại đếm; với tiếng Việt, mỗi token là một âm tiết.

---

## Tóm tắt

Tám ý chính:
1. **Lỗi tên hiện nay chủ yếu không do LLM.** Có 68/71 câu trả lời của LLM là tên khái niệm chép nguyên vẹn. Ở xstk, cả 16 câu bị loại vì một
   trần độ dài mà prompt không nêu. Lỗi nặng đến từ ba nguồn:
   - cây mục: dòng tiêu đề gộp, xstk mất §2 và §3;
   - vai trò `de_cuong` gán nhầm cho mục nội dung;
   - hai luật lọc của chính khâu tên: trần 12 token (với tiếng Việt chỉ khoảng 5–7 từ) và lấy tổ tiên chung.

   Ở doc-4, 23/87 tên nhảy lên trên tổ tiên chung vì hai luật lọc đó; chỉ 2/87 vì module thật sự vắt hai chương (mục 2).
2. **Chỉ 51/142 module (36%) trùng đúng một mục sách.** Ở nhóm này nên giữ tiêu đề tác giả. Bằng chứng gần nhất là bài sinh mục lục giáo
   trình: người chấm ưa tiêu đề tác giả hơn tiêu đề máy 115 lần, kém 13, ngang 22 [21].
3. **Đưa module kề vào có ích cho độ phân biệt nếu làm đối chứng hẹp.** Tiêu đề kề ±1 đủ; thêm nhiều ngữ cảnh hơn gần như không lợi thêm [22].
   Mô hình có ràng buộc giữa các tiêu đề giảm lặp từ 40% xuống 5,5% [21]. Clio dùng cụm gần làm đối chứng [16]. Rủi ro mượn nội dung kề có
   thật [19], nên chỉ đưa tên và chặn bằng mã.
4. **Không có bằng chứng sạch rằng nhãn do máy sinh tốt hơn nhãn trích.** Bài sinh nhãn [4] chỉ có độ đo tự động. LLM ngang người gán nhãn
   không chuyên ở [14], nhưng đó không phải tác giả sách. Đề xuất: trích từ vựng của sách; LLM chỉ được sắp và nén trong từ vựng đóng.
5. **Mô tả 1–2 câu nên là preview "học gì, cần gì trước", có trích `node_id` từng câu và kiểm bằng mã.** Mục tiêu theo thang Bloom để cho A11
   như spec. Tóm tắt trừu tượng tự do có tỉ lệ ảo giác cao [24]; trích dẫn kiểm được là cách đo chuẩn [27].
6. **Câu lý do của R7 cần sửa.** "Hai phân tích gộp" là Alpizar 2020 và Schneider 2018 [36], [38]. Cả hai về tín hiệu đa phương tiện nói
   chung, không riêng tiêu đề. Schneider không ủng hộ ý "nhất là người ít kiến thức nền"; ý này chỉ có ở Richter 2016 [35]. Bằng chứng riêng
   cho tiêu đề là [31], [33], [34].
7. **Khuyến nghị: phương án (e), một mã nguồn cho hai môn.**
   - Tầng 1: tiêu đề tác giả.
   - Tầng 2: xếp hạng ứng viên và khuôn mô tả, không LLM; đây là bản seminar.
   - Tầng 3: LLM viết lại khi điểm tin cậy thấp, chỉ trong đồ án; doc-4 tốn khoảng 0,01–0,02 USD, dưới 1 phút.

   Phương án (a) của chủ dự án tốn 0,035–0,059 USD cho doc-4 và 0,013–0,022 USD cho doc-1. Phương án này không hỏng vì tiền: nó bỏ qua tiêu
   đề tác giả, khó kiểm trung thực, và đi ngược đích bỏ LLM.
8. **Việc đầu tiên tốn 0 USD.** Gồm bốn việc:
   - sửa ba lỗi trong khâu tên: trần token, kiểm từng mảnh, `display_name`;
   - phát lại luật kiểm trên nhật ký;
   - chạy các biến thể tất định;
   - chấm mù theo cặp 142 module.

   Thí nghiệm LLM sau đó tốn dưới 1 USD. Luật quyết định viết trước ở mục 7.6, gồm khả năng bỏ LLM khỏi khâu tên ngay ở đồ án.

---

## 1. Bối cảnh và câu hỏi

Lộ trình là dãy học chia module liền mạch, mỗi module tối đa 8 khái niệm ([ADR 0010](../doc/adr/0010-lo-trinh-la-day-hoc-chia-module.md)).
Tên module hiện theo R7 ([spec v3](../doc/v3-lo-trinh-doc-duoc-spec.md), dòng 119–143); mô tả module chưa có, còn A11 dự kiến `objectives`
và `summary` ([spec addendum](../doc/spec-addendum.md), dòng 701–711).

Chủ dự án đề xuất đưa danh sách khái niệm kèm module trước và sau cho LLM đặt tên và mô tả, và yêu cầu tìm cách tốt nhất theo bằng chứng.
Có hai ràng buộc:
- seminar cấm LLM sinh văn bản ở Pha A;
- đồ án được dùng LLM nhưng có đích dài hạn là bỏ LLM ở khâu tên.

Thước đo ưu tiên là chất lượng người học thấy, độ trung thực, tính tái lập, rồi USD và phút mỗi cuốn.

---

## 2. Hiện trạng và chẩn đoán lỗi tên (số đo ngày 2026-10-11)

### 2.1 Cách đo

Có bốn script đọc cục bộ, làm bốn việc sau:
- Đọc `graph.json` và `manifest.json` của sáu cuốn; lấy cây mục ở phiên bản `title_sections_version` ghi trong manifest (`sections.json`).
- Xếp mỗi module vào một trong bốn loại, theo quan hệ với cây mục:
  - **E**: tập khái niệm của module trùng đúng tập khái niệm được dạy trong một mục (kể cả mục con của nó);
  - **L**: module là một phần của một mục lá;
  - **S**: module vắt qua từ hai mục con trở lên mà không trùng mục nào;
  - **R**: module không có mục chung nào ngoài gốc.
- Với mỗi module, tìm tổ tiên chung sâu nhất. Nếu tên nền nằm cao hơn tổ tiên đó, ghi lý do từng mục bị bỏ qua.
- Phát lại `grounded_suffix` và luật độ dài của `name_modules.py` trên từng câu trả lời trong `module_title_decision_log`. Đây là hàm thuần,
  không gọi mô hình.

### 2.2 Module so với cây mục

Bảng sau cho thấy module của sáu cuốn quan hệ với cây mục ra sao:

| tài liệu | module | cỡ trung vị (min–max) | E trùng một mục | L một phần mục lá | S vắt qua mục con | R không mục chung | mục đa số ≥ 50% khái niệm |
|---|---:|---|---:|---:|---:|---:|---:|
| doc-1 | 32 | 6 (4–8) | 10 | 5 | 17 | 0 | 27/32 |
| nhap-mon-ml | 9 | 6 (4–7) | 0 | 1 | 8 | 0 | 8/9 |
| naive-bayes | 3 | 7 (6–7) | 0 | 0 | 0 | 3 | 0/3 |
| doc-6 | 2 | 6 (6–6) | 0 | 0 | 0 | 2 | 2/2 |
| xstk-ch3-1 | 9 | 8 (8–8) | 1 | 0 | 8 | 0 | 7/9 |
| doc-4 | 87 | 6 (3–8) | 40 | 7 | 40 | 0 | 76/87 |
| **tổng** | **142** | | **51 (36%)** | **13** | **73 (51%)** | **5** | **120/142** |

Bảng cho bốn điểm chính:
- **Chỉ 51/142 module trùng đúng một mục sách.** Chỉ ở nhóm này, tiêu đề của tác giả mô tả đúng và đủ module. Nhóm này cũng là tập dùng
  được cho phép thử "dựng lại tiêu đề đã giấu" (mục 7).
- **Một nửa module vắt qua mục con.** Với luật "tổ tiên chung sâu nhất", 73 module này nhận tiêu đề của mục cha. Mục cha rộng hơn module,
  nên nhiều module kề nhau nhận chung một tên nền. Có 37 cặp module kề nhau cùng tên nền sau khi bỏ số đánh mục.
- **Mục đa số vẫn rõ.** Ở 120/142 module, một mục lá chứa ít nhất một nửa số khái niệm.
- **Hai cuốn không có cây dùng được.** naive-bayes và doc-6 có module không chung mục nào ngoài gốc. Tiêu đề mục của naive-bayes là nhiễu,
  ví dụ "Trong đó:" và "quyét dinh (play=yes/no)".

### 2.3 Vì sao tên nền nhảy lên cấp phần hay chương

Ở doc-1, nhap-mon-ml và xstk, tên nền luôn đúng là tổ tiên chung sâu nhất. Ở doc-4, 23/87 module có tên nền nằm cao hơn tổ tiên đó, và lý do
nằm ở hai luật lọc của chính khâu đặt tên, không phải ở việc module vắt mục:

| lý do một mục bị bỏ qua (doc-4) | số lần | ví dụ |
|---|---:|---|
| tiêu đề dài hơn 12 token (`clean_titles`, `max_words=12`) | 21 | "III- Quy luật thống nhất và đấu tranh của các mặt đối lập" (13 token); hai dòng tiêu đề bị bộ đọc gộp làm một: "III- Triết học Tây Âu thời phục hưng và cận đại 1. Triết học Tây Âu thời kỳ phục hưng thế kỷ XV - XVI" (25 token) |
| mục nội dung bị A2 gán vai trò `de_cuong` mà có nội dung trực tiếp | 16 | "B. Lịch sử triết học Tây Âu trước Mác", "Chương X", "Ý thức xã hội", "II- Các hình thái ý thức xã hội" |

Hai luật này sinh ra phần lớn các tên tệ nhất mà phiên chính đã liệt kê:
- "Chương II — Thuyết nhật tâm · Phương pháp con nhện": mục "III-…" bị gộp dòng nên dài 25 token, còn mục "B. …" bị gán `de_cuong`.
- "Chương XIII — Ý thức chính trị · Pháp luật": mục "Ý thức xã hội" và "II- Các hình thái ý thức xã hội" đều bị gán `de_cuong`.
- "Chương XI": mục chung là một dòng gộp dài 20 token.

Chỉ 2/87 module của doc-4 vắt qua hai chương nên tổ tiên chung thật sự là "Phần":
- "Phần I Khái lược về triết học và lịch sử triết học": 5 khái niệm về tư tưởng yêu nước Việt Nam, 1 khái niệm của chương sau;
- "Phần II — Tôn trọng khách quan": 3 khái niệm cuối chương V, 1 khái niệm của chương VI.

Đây là lỗi chia module của A10 (`segment_modules` chỉ phạt mềm việc vắt chương), không phải lỗi khâu tên.

Với tiếng Việt, mỗi token khoảng trắng là một âm tiết, nên trần 12 token chỉ chứa khoảng 5–7 từ. Tiêu đề mục 13 âm tiết là chuyện thường gặp.

### 2.4 Lời gọi LLM hiện tại: bị luật kiểm loại, không phải trả lời sai

Phát lại luật kiểm trên nhật ký cho kết quả sau:

| tài liệu | dòng nhật ký (hợp lệ) | câu trả lời | trả lời toàn bằng tên khái niệm nguyên vẹn | vượt 12 token khi ghép với tên nền | vượt 72 ký tự | hợp từ nằm gọn trong một tên |
|---|---|---:|---:|---:|---:|---:|
| xstk-ch3-1 | 8 (0) | 16 | 16 | 16 | 2 | 2 |
| doc-4 | 33 (11) | 55 | 52 | 51 | 16 | 2 |

Bảng cho bốn điểm:
- **Mô hình gần như luôn làm đúng việc được giao.** Ở xstk, cả 16 câu trả lời đều là 2–3 tên khái niệm chép nguyên vẹn, ví dụ "Ước lượng
  không chệch · Khoảng tin cậy". Cả 16 vẫn bị loại, vì tên nền "THỐNG KÊ TOÁN §1. LÝ THUYẾT MẪU" đã chiếm 7 token.
- **Prompt không nói các trần mà mã áp.** Hai trần là tổng ≤ 12 token và phần phụ ≤ 72 ký tự. Trần 12 token còn không nhất quán: khi riêng
  tên nền cộng một khái niệm đã vượt 12 token thì mã bỏ trần. Vì vậy doc-4 vẫn có tên 24–27 token.
- **Luật "không là mẩu của một tên" bắt nhầm.** Nó loại "Độ lệch mẫu · Độ lệch mẫu hiệu chỉnh" và "Vận động · Vận động cơ học", tức hai tên
  nguyên vẹn, vì hợp các từ nằm gọn trong tên dài hơn.
- **Lời gọi rất rẻ.** Theo `module_title_metrics`, xstk tốn 16 lời gọi với 5.960 token vào và 325 token ra. doc-4 tốn 56 lời gọi với 19.049
  token vào và 1.105 token ra, tức khoảng 0,0064 USD theo giá 0,25/1,50 USD cho 1 triệu token.

Hai lỗi nữa nằm trong mã, không trong mô hình:
- **Nhánh "trùng tên nền" không buộc chọn tên nguyên vẹn.** Prompt cho phép phần phụ tự ghép, miễn mọi từ có trong tên khái niệm hoặc tiêu đề.
  Luật "mẩu tên" xét cả chuỗi phần phụ, không xét từng mảnh giữa các dấu " · ". Vì vậy "Tích hợp · Giảm" (mẩu của "Tích hợp dữ liệu" và "Giảm
  dữ liệu") và "thực · không · vuông cấp n" vẫn qua. Hai tên này đến từ bản cũ được dùng lại: doc-1 và nhap-mon-ml không có dòng nhật ký nào.
  Nhánh `reuse_artifact` giữ tên cũ khi tên cũ bắt đầu bằng tên nền.
- **Tên module dùng `name`, không dùng `display_name`.** "2.2 Định thức — Ma trận con · Tính chất 3" lấy tên thô "Tính chất 3". R9 đã đổi tên
  hiển thị của khái niệm này thành "Công thức khai triển định thức theo hàng i". doc-1 có 7 khái niệm được đổi tên hiển thị.

### 2.5 Phân loại lỗi tên trên 142 module

Bảng dưới đếm bằng luật thô; một tên có thể rơi vào nhiều dòng:

| loại lỗi | số tên | ví dụ thật |
|---|---:|---|
| tên nền ở cấp phần/chương hoặc ở mục bị cây gộp sai | 29 (xstk 8, doc-4 21) | "THỐNG KÊ TOÁN §1. LÝ THUYẾT MẪU — Độ tin cậy" cho module về ước lượng khoảng; "Phần II — Tôn trọng khách quan" |
| hai module kề nhau cùng tên nền, chỉ khác phần phụ | 37 cặp | "1.1 Tập hợp — Phần tử · Tập hợp con" rồi "1.1 Tập hợp — Phần bù · Giao hoán · Kết hợp" |
| tên gần trùng do tiêu đề con lặp tiêu đề cha | (gồm trong dòng trên) | "3.5.1 Không gian véc tơ Euclid" rồi "3.5 Không gian véc tơ Euclid" |
| phần phụ có mảnh không phải tên khái niệm nguyên vẹn | 9 | "2.1 Ma trận — thực · không · vuông cấp n"; "1.4 Thu thập và tiền xử lý dữ liệu — Tích hợp · Giảm" |
| nhãn đánh số trong tên | 1 | "2.2 Định thức — Ma trận con · Tính chất 3" |
| tiêu đề chung chung hoặc nhãn đầu đoạn | 3 | "2.2.2 Tính chất", "4.1 Các khái niệm cơ bản", "Tư tưởng triết học:" |
| tiêu đề mở đầu bằng dấu đánh số cục bộ | 62 (doc-4) | "a) Thị tộc", "b) Lực lượng sản xuất", "c) Tính giai cấp của ý thức xã hội." |
| lỗi chữ từ bộ đọc | vài tên ở doc-4 | "I- triết học ấn Độ cổ, trung đại", "C. Lịch sử tư tưởng triết học Việt Nam(*)" |
| dài hơn 12 token | 17 | "Chương XIV Quan điểm triết học Mác - Lênin về con người — Yếu tố sinh học · Yếu tố xã hội · Bản chất con người" (27 token) |

Không có hai tên nào trùng nguyên văn: luật hậu tố và luật "(i/n)" đã chặn được việc này. Trung bình một tên dài 10,3 token.

[CHÈN HÌNH 1 – Sơ đồ cây mục doc-4 chương X: các mục "Chương X", "I-…", "II-… 1. …" (dòng gộp), "a) b) c)", tô màu mục bị bỏ qua vì `de_cuong` và vì quá 12 token; mũi tên từ hai module (58, 63) lên tên "Phần II" mà chúng nhận được.]

### 2.6 Đối chiếu với chẩn đoán của phiên chính

Phiên chính chẩn đoán: lỗi nặng nhất đến từ cây mục và từ việc lấy tổ tiên chung, không đến từ LLM, và LLM hiện chỉ chọn tên khái niệm.
Số đo ở trên đồng ý với phần chính và bổ sung bốn điểm:
- **Đồng ý:** LLM không gây lỗi nặng. 68/71 câu trả lời là tên khái niệm nguyên vẹn.
- **Bổ sung 1 — lỗi nằm ở luật lọc của khâu tên.** Ở doc-4, việc nhảy lên "Chương"/"Phần" chủ yếu do trần 12 token và bộ lọc vai trò `de_cuong`
  (23/87 module). Chỉ 2/87 module nhảy lên vì thật sự vắt hai chương. Trần 12 token là luật của khâu tên, sửa được ngay mà không chờ A1.
- **Bổ sung 2 — nhánh LLM hỏng vì luật kiểm.** "0/8 hợp lệ" ở xstk không phải mô hình trả sai. Luật độ dài không có trong prompt, và luật "mẩu
  tên" bắt nhầm.
- **Bổ sung 3 — "LLM chỉ chọn tên khái niệm" chỉ đúng một phần.** Câu này đúng cho nhánh không có tên nền và nhánh tên nền chỉ là mã. Nhánh
  trùng tên nền cho phép ghép mảnh, và các tên mảnh cũ được giữ qua cơ chế dùng lại.
- **Bổ sung 4 — tên module bỏ qua tên hiển thị R9.** Mã dùng `name` thay vì `display_name`.

---

## 3. Văn liệu

### 3.1 Gán nhãn chủ đề và cụm, kể cả cụm phân cấp

Bảng dưới tóm các công trình đã kiểm, xếp từ thời trước LLM tới thời LLM:

| công trình | cách làm | kết quả liên quan |
|---|---|---|
| Mei và cộng sự, KDD 2007 [1] | trích n-gram và noun chunk, xếp theo độ liên quan với chủ đề | nhãn tốt phải dễ hiểu, liên quan, phủ chủ đề, và **phân biệt với chủ đề khác**. Điểm phân biệt = điểm với chủ đề đích − μ × điểm với các chủ đề còn lại |
| Lau và cộng sự, ACL 2011 [2] | ứng viên là tiêu đề Wikipedia và từ đầu bảng của chủ đề; xếp hạng có giám sát; MTurk chấm 0–3, ít nhất 10 người mỗi nhãn | điểm nhãn top-1 1,79–2,02, trần 2,29–2,45. Nhóm ứng viên "5 từ đầu của chủ đề" kém nhất. Phương pháp của Mei và cộng sự chỉ đạt 1,26–1,53. Khi người tự đặt nhãn, chỉ khoảng 36% nhãn có trong chính kho văn bản, 60% là tiêu đề Wikipedia |
| Bhatia và cộng sự, COLING 2016 [3] | embedding doc2vec/word2vec để chọn tiêu đề Wikipedia | đơn giản hơn và tốt hơn [2]; tiêu đề Wikipedia là ứng viên tốt hơn n-gram trích từ tài liệu |
| Alokaili và cộng sự, SIGIR 2020 [4] | seq2seq **sinh** nhãn, huấn luyện trên cặp bài–tiêu đề Wikipedia | chỉ đánh giá tự động: BERTScore F 0,919–0,929, so với 0,902 của "2 từ đầu". Không có chấm người cho nhãn sinh ra. Có ca hỏng như nhãn "the", "and" khi chủ đề rời rạc hoặc khác miền |
| Treeratpituk và Callan, dg.o 2006 [5]; Glover và cộng sự, CIKM 2002 [6] | gán nhãn cụm phân cấp bằng thông tin của cụm, **cụm cha** và thống kê kho | nhãn gần với nhãn biên tập viên ODP [5]. Nhãn phân cấp phải tách nhãn chung cho cha khỏi nhãn riêng cho con ([7], §17.9) |
| Manning và cộng sự, giáo trình IR [7] | tổng hợp | gán nhãn "vi phân" so phân bố từ của cụm với cụm khác. Ở cây, phải phân biệt nút với **anh em, cha và con**. Tiêu đề dễ đọc hơn danh sách từ; danh sách cụm từ "tốn thời gian hiểu hơn một tiêu đề viết khéo" |
| Chang và cộng sự, NIPS 2009 [9] | phép thử *word intrusion* (5 từ + 1 từ lạ) và *topic intrusion* (tài liệu + 4 chủ đề, 1 lạ) trên MTurk | mô hình có likelihood tốt hơn có thể cho chủ đề khó hiểu hơn. Độ đo nội tại không thay được phép thử với người |
| BERTopic [10] | cụm embedding rồi c-TF-IDF: W(t,c) = tf(t,c) · log(1 + A / tf(t)) | biểu diễn chủ đề phân biệt được mà không cần LLM |
| TopicGPT, NAACL 2024 [11] | LLM sinh nhãn kèm mô tả, có thấy các chủ đề đã sinh; gộp cặp gần trùng (cosine ≥ 0,5); gán chủ đề kèm câu trích | tỉ lệ chủ đề lệch so với nhãn người (Wikipedia): LDA 62,4%, TopicGPT 39,8% (chưa tinh chỉnh) và 30,3% (đã tinh chỉnh). Chủ đề lặp giảm từ 11,9% xuống 0. GPT-3.5 và Mistral-7B không theo nổi định dạng khi sinh chủ đề. LLM không tất định dù giải mã tham lam |
| GoalEx [12]; Stammbach và cộng sự [13] | LLM đề xuất, gán, chọn cụm theo mục tiêu; LLM chấm chủ đề | GoalEx cho giải thích đúng và sát mục tiêu hơn phương pháp trước. Điểm LLM chấm tương quan với người tốt hơn độ đo tự động cũ (chỉ đọc tóm tắt) |
| Piper và Wu, NLP4DH 2025 [14] | nhãn của 4 LLM so với nhãn của 2 người gán, trên 100 đoạn; 200 người đọc xếp hạng mù | hạng trung bình (thấp là tốt), truyện: Gemma2 2,25, GPT-4o 2,57, người 3,23. Tin tức: không khác biệt có ý nghĩa. Người đọc tin tức ưa nhãn **cụ thể** hơn ("prostate cancer" hơn "health awareness") |
| Rijcken và cộng sự, IFSA 2023 [15] | ChatGPT viết tóm tắt chủ đề trên bệnh án | chuyên gia thấy một nửa số mô tả hữu ích (chỉ đọc tóm tắt) |
| Clio, 2024 [16] | đặt tên và mô tả hai câu cho cụm: 50 mẫu trong cụm, 50 mẫu **gần tâm nhưng ngoài cụm** làm đối chứng, prompt ghi rõ "không thuộc nhóm" | kiểm tay: 97% tên cụm phân cấp phản ánh đúng nội dung. Không có thí nghiệm bỏ phần đối chứng |

Từ bảng rút ra ba điểm:
- **Phân biệt với nút kề là tiêu chí cổ điển.** Nó có từ thời trước LLM [1], [5], [7], và được làm bằng phép trừ điểm, không cần sinh văn bản.
- **Không có bằng chứng sạch rằng nhãn sinh tốt hơn nhãn trích.** [4] chỉ dùng độ đo tự động. Ở [14], "người" là sinh viên gán nhãn, không
  phải tác giả sách. Bài gần bài toán của dự án nhất là [21] (mục 3.3), và ở đó tiêu đề tác giả thắng rõ.
- **LLM gán nhãn tốt khi có ràng buộc.** Các hệ dùng LLM thành công đều thêm khâu kiểm: câu trích, gộp trùng, tự sửa [11]; đối chứng [16].

### 3.2 Mô tả tương phản và rủi ro ngữ cảnh thừa

Bốn công trình cho bằng chứng hai chiều:
- **D3, ICML 2022 [17].** Hệ đưa mẫu của hai phân bố cho GPT-3 để đề xuất mô tả khác biệt, rồi một bộ kiểm học được xếp lại theo mức mô tả
  đúng trên tập mẫu lớn hơn. Trên 54 bài phân loại nhị phân, Curie chỉ ra mô tả giống người 7% số lần; thêm tinh chỉnh và xếp lại đạt 61%;
  Davinci đạt 76%. Bài học: *đề xuất rồi kiểm* tốt hơn hẳn chỉ đề xuất.
- **D5, NeurIPS 2023 [18].** Có mục tiêu người dùng thì LLM đề xuất khác biệt liên quan hơn. Kết quả được kiểm trên nửa dữ liệu không dùng để
  đề xuất.
- **Shi và cộng sự, ICML 2023 [19].** Thêm thông tin không liên quan vào đề làm độ chính xác "giảm mạnh". Dặn mô hình bỏ qua thông tin thừa,
  hoặc dùng self-consistency, giúp giảm.
- **Liu và cộng sự, TACL 2024 [20].** Mô hình dùng thông tin ở đầu và cuối ngữ cảnh tốt hơn ở giữa.

*Suy luận:* module kề đúng là thông tin "thừa" đối với nội dung của module đích. Nó có ích cho việc phân biệt, nhưng có thể bị mô hình chép vào
tên. Cần ba biện pháp: chỉ đưa tên, gắn nhãn đối chứng, và kiểm "mượn" bằng mã.

### 3.3 Sinh tiêu đề mục và mục lục

Ba công trình gần bài toán đặt tên module nhất:
- **Branavan và cộng sự, ACL 2007 [21].** Bài sinh mục lục cho giáo trình thuật toán 1.180 trang (540 tiêu đề, trung bình 3,64 từ).
  - Mô hình phân cấp có đặc trưng toàn cục: trùng tiêu đề anh em, trùng tiêu đề cha, hai tiêu đề kề chung từ đầu. Mô hình còn dùng từ của
    đoạn kề và phạt cụm chung chung.
  - Kết quả: trích cụm TF-IDF cho 40% tiêu đề bị lặp; mô hình phân cấp chỉ 5,5%, còn mục lục gốc 9% (lặp "Analysis", "Chapter Outline").
  - Người chấm thấy mô hình phân cấp hơn mô hình phẳng 68 lần, kém 32, ngang 49 (p ≤ 0,0002).
  - **Tiêu đề tác giả hơn mô hình phân cấp 115 lần, kém 13, ngang 22** (bảng 4, đã đối chiếu ảnh trang). Thêm phụ thuộc toàn cục đổi 30% tiêu
    đề.
- **Zhang và cộng sự, SIGIR 2019 [22].** Bài sinh dàn ý trên WIKIOG. Khi biết ranh giới mục, ROUGE-1 của tiêu đề như sau:
  - độc lập: 57,8;
  - phụ thuộc mọi tiêu đề trước: 57,9, vì "quá nhiều ngữ cảnh";
  - phụ thuộc tiêu đề kề: 59,0;
  - thêm cơ chế "review" chống lặp: 59,4 (bộ mixture).

  Bỏ chú ý vào nội dung mục gây hại nhiều hơn bỏ phụ thuộc giữa tiêu đề. Không có ngữ cảnh kề thì mô hình sinh tiêu đề lặp ("career" hai lần).
- **Field và cộng sự, WNGT 2020 [23].** Bộ giải mã có attention đạt điểm cao khi đặt tên mục Wikipedia chủ yếu nhờ sinh văn bản trích xuất.

### 3.4 Trung thực, trích dẫn và LLM làm giám khảo

Năm công trình cho khung đo độ trung thực:
- **Maynez và cộng sự [24].** Ảo giác có ở hơn 70% bản tóm một câu (XSum). Phần lớn là ảo giác ngoại sinh, và hơn 90% trong số đó sai. Độ đo
  suy diễn (entailment) tương quan với độ trung thực tốt hơn ROUGE và BERTScore.
- **SummaC [25].** NLI ở mức câu cộng gộp đạt balanced accuracy 74,4% trên sáu bộ phát hiện mâu thuẫn. Kiểm bằng NLI dùng được nhưng còn sai
  khoảng một phần tư, và đó là số trên tiếng Anh.
- **FActScore [26].** Bài tách văn bản thành mệnh đề nguyên tử rồi đếm tỉ lệ được nguồn chống đỡ; ChatGPT chỉ đạt 58% trên tiểu sử. Bộ ước
  lượng tự động sai dưới 2%.
- **ALCE [27].** Bài đo citation recall/precision bằng NLI. Trên ELI5, mô hình tốt nhất vẫn thiếu chống đỡ đầy đủ ở 50% số trường hợp.
- **Zheng và cộng sự [28] và Wang và cộng sự [29].** GPT-4 đồng thuận với người 85% (không tính ngang), ngang mức người–người 81%. Nhưng có
  thiên lệch vị trí: độ nhất quán khi đảo thứ tự chỉ 65% với GPT-4, 23,8% với Claude-v1 [28]; đảo thứ tự lật được 66/80 kết quả [29].

*Suy luận:* với tên và mô tả 1–2 câu, kiểm bằng mã trên từ vựng đóng và trích `node_id` rẻ và chắc nhất. NLI tiếng Việt là lớp phụ cần tự đo
trước khi tin; LLM giám khảo chỉ để sàng lọc.

### 3.5 Tiêu đề, tín hiệu và mục tiêu học tập trong văn liệu giáo dục

Có bốn nhóm bằng chứng:
- **Tiêu đề là một loại tín hiệu.**
  - Lorch [31] tổng quan các tín hiệu: tiêu đề sách, tiêu đề mục, preview, overview, tóm tắt. Theo bài, *"gần như mọi loại tín hiệu"* giúp
    nhớ tốt hơn thông tin chúng đánh dấu, trong khi thông tin không được đánh dấu thường không bị ảnh hưởng.
  - Hartley và Trueman [33] làm 17 thí nghiệm. Tiêu đề, ở dạng câu khẳng định hay câu hỏi, giúp học sinh 14–15 tuổi nhớ lại, tìm và truy xuất
    thông tin; vị trí tiêu đề (lề hay xen) không ảnh hưởng. Tiêu đề dạng câu hỏi không giúp người đọc yếu hơn tiêu đề dạng câu khẳng định.
  - Lorch, Lemarié và Grant [34] cho thấy tiêu đề thể hiện tổ chức thứ bậc làm dàn ý người đọc đầy đủ hơn, còn tiêu đề thể hiện tổ chức tuần
    tự làm tìm kiếm nhanh hơn.
  - Lorch và Lorch [32] nghiên cứu riêng tiêu đề với nhớ lại và tóm tắt; tôi chỉ kiểm được siêu dữ liệu.
- **Hai phân tích gộp mà R7 viện dẫn.** Nguồn là [báo cáo đánh giá lộ trình](danh-gia-lo-trinh-2026-09-26.md): Alpizar và cộng sự [38] và
  Schneider và cộng sự [36]. Cả hai về tín hiệu trong học đa phương tiện nói chung (tô màu, mũi tên, nhấn mạnh), **không riêng tiêu đề**.
  - Alpizar và cộng sự: 29 nghiên cứu, 2.726 người, d = 0,38. Hiệu ứng lớn hơn ở nghiên cứu chất lượng cao và có kiểm soát khác biệt kiến thức
    nền.
  - Schneider và cộng sự: 103 nghiên cứu, 12.201 người; nhớ lại g = 0,53, chuyển giao g = 0,33. Số này lấy qua bản tóm tắt thứ cấp của TU
    München [37]. Theo bản tóm tắt đó, nghiên cứu này **không** thấy người ít kiến thức nền hưởng lợi nhiều hơn.
  - Kết luận "nhất là người ít kiến thức nền" đến từ một phân tích gộp thứ ba: Richter và cộng sự [35], về tín hiệu liên kết chữ–hình (27
    nghiên cứu, r = 0,17, có điều tiết bởi kiến thức nền).
  - Vì vậy câu lý do của R7 cần sửa (mục 4, câu hỏi 5).
- **Tiêu đề cụ thể hay nhãn chung.** Tôi không tìm được thí nghiệm học tập so trực tiếp hai loại này. Có ba bằng chứng gián tiếp: tín hiệu chỉ
  giúp phần nó đánh dấu [31]; người đọc ưa nhãn cụ thể [14]; hệ sinh mục lục phải phạt cụm chung và tiêu đề trùng [21].
- **Mục tiêu học tập.**
  - Thang Bloom sửa đổi [41], [42] cho khung động từ và hai chiều: quá trình nhận thức và loại kiến thức.
  - Hamilton [43] khung hoá hiệu quả của câu hỏi chèn và mục tiêu học tập trong học từ văn bản (chỉ đọc tóm tắt, không có số).
  - GPT-4 sinh được mục tiêu học tập hợp lý, phần lớn đúng mức Bloom, trên 127 mục tiêu; nhưng cần người duyệt [44].
  - Chương về tín hiệu trong Cambridge Handbook là của van Gog [39], không phải của Mayer và Fiorella. Chương của Mayer và Fiorella [40] gộp
    nhiều nguyên tắc giảm xử lý thừa; tôi chỉ kiểm siêu dữ liệu cả hai chương.

### 3.6 Trích cụm từ khoá và công cụ tiếng Việt

Các công cụ cho bản không LLM:
- **TextRank [45]:** đồ thị đồng xuất hiện; F 36,2 so với 33,0 của Hulth trên tóm tắt bài báo.
- **YAKE [46]:** đặc trưng thống kê cục bộ, không cần kho (chỉ kiểm siêu dữ liệu).
- **EmbedRank [47]:** xếp cụm theo cosine với embedding tài liệu; bản EmbedRank++ dùng MMR [48] để đa dạng. Trong khảo sát hơn 200 phiếu,
  người dùng ưa bộ cụm đa dạng dù F-score không tăng.
- **KeyBERT [49]:** cài đặt cùng ý tưởng.
- **c-TF-IDF [10]:** cho cụm phân biệt giữa các lớp; ở đây lớp là module.
- **Tiếng Việt:**
  - PhoBERT [50] đòi văn bản đã tách từ;
  - VnCoreNLP [51] tách từ;
  - underthesea [52] giấy phép Apache-2.0;
  - multilingual-e5 [53] không cần tách từ.

  Chi tiết giới hạn và giấy phép của các công cụ này đã có ở [báo cáo ML/DL](nghien-cuu-ml-dl-loc-cap-va-tien-quyet-2026-10-04.md) mục 5.

*Suy luận:* trong giáo trình, từ vựng cần cho tên module đã nằm sẵn trong tên khái niệm và tiêu đề mục. Trích cụm từ khoá tự do từ văn xuôi
chủ yếu thêm nhiễu, nên chỉ nên dùng làm đặc trưng xếp hạng, không dùng làm tên.

---

## 4. Trả lời sáu câu hỏi con

**Câu hỏi 1 — Module kề có giúp tên phân biệt và thể hiện tiến trình không; có rủi ro mượn không?**
- Có bằng chứng cho phần "phân biệt":
  - ngữ cảnh tiêu đề kề và cơ chế chống lặp nâng chất lượng tiêu đề và hết lặp [22];
  - mô hình mục lục phân cấp hơn mô hình phẳng 68–32 và giảm tiêu đề lặp từ 40% (trích từ khoá) xuống 5,5% [21];
  - gán nhãn cây cổ điển dùng cụm cha và cụm anh em [1], [5], [7]; Clio dùng cụm gần tâm làm đối chứng [16].
- Ngữ cảnh rộng hơn ±1 không thêm gì: dùng mọi tiêu đề trước chỉ hơn độc lập 0,1–0,6 điểm [22].
- Về "thể hiện tiến trình", tôi không tìm được thí nghiệm nào. *Suy luận:* cấu trúc song song giữa tên kề ("Ma trận: …", "Định thức: …") là
  cách văn liệu mục lục làm [21], nhưng chưa có số đo trên người học.
- Rủi ro mượn là có thật: thông tin không liên quan làm LLM sai nhiều hơn [19]. Biện pháp ở mục 6.2: chỉ đưa tên, ghi nhãn đối chứng, chặn
  token chỉ có ở module kề. Phép thử L1–L2 ở mục 7.5 đo trực tiếp rủi ro này.

**Câu hỏi 2 — Trích xuất hay trừu tượng hoá?**
- Ở bài gần nhất (mục lục giáo trình), người chấm ưa tiêu đề tác giả hơn tiêu đề máy 115/150 lần [21].
- Văn liệu gán nhãn chủ đề không có so sánh sạch giữa nhãn sinh và nhãn trích có chấm người:
  - [4] chỉ có BERTScore;
  - LLM ngang hoặc hơn người gán nhãn không chuyên trên đoạn truyện và tin [14];
  - chuyên gia thấy một nửa mô tả ChatGPT hữu ích [15].
- Ở kho văn bản chung, nhãn tốt thường không có trong tài liệu (36%) [2]. Ở giáo trình thì khác: tác giả đã viết sẵn tiêu đề.
- Kết luận:
  - module trùng một mục → giữ tiêu đề tác giả, trừ khi đó là nhãn chung hoặc trùng (mục 6.4);
  - module vắt mục → trích từ vựng của sách rồi ghép;
  - chỉ cho LLM sắp xếp và nén trong từ vựng đóng.

**Câu hỏi 3 — Giữ trung thực bằng gì?**
- Lớp chính là kiểm bằng mã: từ vựng đóng, chặn mượn, trích `node_id` cho mỗi câu. Lớp này rẻ, tất định, và bắt đúng loại lỗi đã gặp.
- NLI là lớp phụ cho mô tả. Nó tương quan với trung thực tốt hơn ROUGE [24], nhưng vẫn sai khoảng một phần tư trên tiếng Anh [25], và chưa có
  số đo tiếng Việt.
- LLM giám khảo chỉ dùng để sàng lọc, phải đảo thứ tự [28], [29].
- Mô tả 1–2 câu cần trích tới `node_id`, không cần tới chunk: mỗi khái niệm có đúng một chunk dạy, và mô tả A5 đã kiểm trích dẫn.

**Câu hỏi 4 — Mô tả là tóm tắt, mục tiêu Bloom hay danh sách "học gì"?**
- Với 1–2 câu ở A10, nên là preview "học gì và cần gì trước". Preview và overview là tín hiệu giúp nhớ nội dung được đánh dấu [31]. Dạng này
  chỉ cần thông tin đã có trong đồ thị, nên trung thực nhất.
- Mục tiêu đo được theo Bloom [41], [42] đòi suy ra năng lực người học, vượt ra ngoài văn bản. Theo spec, chúng thuộc A11 (3–5 mục tiêu, sinh
  offline từ chunk). LLM sinh được mục tiêu hợp lý nhưng cần người duyệt [44].
- Tôi không tìm thấy bằng chứng rằng một câu mục tiêu Bloom tốt hơn preview ở vị trí này.

**Câu hỏi 5 — Nguyên tắc tín hiệu và loại tiêu đề.**
- Tiêu đề giúp nhớ lại, tìm và truy xuất [33]. Tín hiệu nói chung có hiệu ứng nhỏ–vừa: d = 0,38 [38]; g = 0,53 nhớ lại và 0,33 chuyển giao
  [36], [37].
- Hai phân tích gộp R7 dẫn đều không riêng về tiêu đề. Ý "nhất là người ít kiến thức nền" chỉ được [35] ủng hộ, còn [36] thì không.
- Đề nghị sửa câu lý do của R7 thành: "tiêu đề có nội dung là tín hiệu giúp nhớ và tìm thông tin [31], [33], [34]; tín hiệu nói chung có hiệu
  ứng nhỏ–vừa [36], [38]; bằng chứng về người ít kiến thức nền không nhất quán [35], [36]".
- Về loại tiêu đề: nên mô tả nội dung cụ thể và cho thấy vị trí trong cấu trúc [34]. Nhãn chung như "Tính chất" chỉ chấp nhận khi đi kèm mục cha.

**Câu hỏi 6 — Đánh giá.** Xem mục 7.

---

## 5. So sánh các phương án

Ngoài bốn phương án được giao, báo cáo đề xuất thêm phương án (e). Đó là một chuỗi quyết định nhiều tầng: giữ tiêu đề tác giả khi module trùng
một mục; nếu không thì xếp hạng ứng viên bằng mã; chỉ gọi LLM (bản đồ án) khi điểm tin cậy của mã thấp. Bảng dưới so năm phương án trên năm
trục; chi phí tính theo giá `gemini-3.1-flash-lite` (0,25/1,50 USD cho 1 triệu token).

| trục | (a) LLM tự đặt, có module kề | (b) hiện trạng | (c) không LLM | (d) lai: mã sinh ứng viên, LLM chọn/viết lại, mã kiểm | (e) đề xuất: tác giả trước, mã xếp hạng, LLM chỉ khi cần |
|---|---|---|---|---|---|
| đúng nội dung | khá: tóm từ danh sách khái niệm; dễ bỏ qua tiêu đề tác giả, trong khi tiêu đề tác giả được người chấm ưa hơn máy 115/150 lần [21] | tốt ở 51 module trùng mục; sai khi cây hỏng hay tên nền nhảy lên "Phần/Chương" (29 tên) | tốt khi có tiêu đề hay tên khái niệm đại diện; không nén ý được ("các dạng ma trận đặc biệt") | tốt: dùng từ vựng của sách, LLM nén và sắp lại | như (d) ở ca khó, như tác giả ở ca dễ |
| phân biệt với module kề | tốt nếu đưa module kề làm đối chứng [16], [22]; có rủi ro "mượn" nội dung kề [19] | kém: 37 cặp kề cùng tên nền | khá: điểm phân biệt kiểu Mei [1], c-TF-IDF [10], MMR [47], [48] | tốt: đối chứng ±1 cộng luật mã chặn từ chỉ có ở module kề | tốt |
| ngắn gọn, tự nhiên tiếng Việt | tốt nhất về văn | kém khi ghép "tên nền — mẩu · mẩu"; 17 tên dài hơn 12 token | trung bình: khuôn cố định, chuỗi tên nối "·" | tốt | tốt ở ca dùng LLM, trung bình ở ca mã |
| trung thực của mô tả | rủi ro cao nếu viết tự do: tóm tắt trừu tượng có ảo giác ở hơn 70% bản tóm một câu trên XSum [24] | không có mô tả | cao: khuôn câu chỉ chứa tên khái niệm và quan hệ đã có | cao nếu mỗi câu trích `node_id` và mã kiểm [27] | cao |
| tái lập | trung bình: nhiệt độ 0 vẫn không tất định [11], cần cache | cao | tuyệt đối | trung bình–cao, nhờ cache | cao; phần LLM có cache |
| USD/cuốn (doc-4, 87 module) | 0,035–0,059 | khoảng 0,006 (đo được) | 0 | 0,02–0,045 | 0–0,03 tuỳ tỉ lệ ca khó |
| USD/cuốn (doc-1, 32 module) | 0,013–0,022 | gần 0 (dùng lại) | 0 | 0,008–0,017 | 0–0,01 |
| phút/cuốn | dưới 1 phút ở song song 16 (*Suy luận*, chưa đo độ trễ) | dưới 1 phút | vài giây đến vài chục giây trên CPU (nếu dùng embedding) | dưới 1 phút | dưới 1 phút |
| seminar (cấm LLM sinh văn bản) | không dùng được | phải bỏ nhánh LLM | dùng được | không dùng được | tầng 1–2 dùng được nguyên |
| đồ án (được LLM, đích dài hạn bỏ LLM ở khâu tên) | dùng được nhưng đi ngược đích dài hạn | dùng được | dùng được | dùng được | dùng được; đo được tỉ lệ ca cần LLM để quyết bỏ |

Cách tính chi phí (a): đầu vào khoảng 1.000–1.500 token và đầu ra 100–200 token mỗi module. Đầu vào gồm tên và mô tả khái niệm (trung vị
1.265–2.716 ký tự mỗi module, tuỳ cuốn), tên module ±1 và chỉ dẫn. Tỉ lệ đo trên nhật ký thật là khoảng 3,6 ký tự/token. Như vậy doc-4 tốn
87 × (1.000–1.500 × 0,25 + 100–200 × 1,50) / 10⁶ = 0,035–0,059 USD, và doc-1 tốn 0,013–0,022 USD. (d) rẻ hơn vì không gửi mô tả đầy đủ,
chỉ gửi ứng viên và tên. Ở mọi phương án, tiền đặt tên dưới 0,1% chi phí một cuốn: pass phụ doc-4 tốn 45,92 USD
([nghiên cứu tiền và thời gian](nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md)). Cache ngầm của Gemini 3 cần tối thiểu 4.096 token, nên
không áp dụng cho các lời gọi này ([nghiên cứu Gemini](nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md)).

*Suy luận:* tiền không phân biệt được các phương án. Phân biệt chúng là ba điều: chất lượng người học thấy, độ trung thực, và việc seminar cấm
LLM. Vì vậy (e) là lựa chọn hợp lý: một mã nguồn chung cho hai môn, chỉ thêm một tầng LLM tuỳ chọn cho đồ án. Tầng này đo được mức đóng góp
của mình, nên có căn cứ để bỏ LLM khi đến lúc.

---

## 6. Khuyến nghị thiết kế

### 6.1 Khung chung cho hai môn (phương án e)

Mỗi module đi qua ba tầng; tầng 1 và tầng 2 không dùng LLM:

| tầng | điều kiện vào | việc làm | đầu ra |
|---|---|---|---|
| 1. Tiêu đề tác giả | module loại E (trùng đúng một mục) và tiêu đề qua bộ lọc chất lượng (6.4) | dùng nguyên tiêu đề đã làm sạch; nếu tiêu đề trùng với module kề hoặc là nhãn chung thì ghép ngữ cảnh mục cha: "Định thức — Tính chất" | tên, `title_source = "author_section"` |
| 2. Xếp hạng bằng mã | mọi module còn lại | sinh ứng viên, chấm đặc trưng, ghép theo khuôn (6.3) | tên, mô tả khuôn, điểm tin cậy |
| 3. LLM viết lại (chỉ đồ án) | điểm tin cậy tầng 2 dưới ngưỡng, hoặc tên tầng 2 trùng/gần trùng với module kề | LLM chọn và ghép từ ứng viên, có đối chứng ±1; mã kiểm; hỏng thì giữ tầng 2 | tên, mô tả có trích `node_id` |

Mô tả 1–2 câu luôn có bản khuôn từ tầng 2. Tầng 3 chỉ thay bản khuôn khi qua được kiểm tra trung thực.

### 6.2 Bản đồ án: lời gọi tầng 3

Đầu vào lời gọi gồm bốn nhóm, tất cả là JSON:
- **Module đích:** đường mục đầy đủ đã làm sạch của mục đa số và của tổ tiên chung; danh sách khái niệm theo thứ tự dãy học, mỗi khái niệm có
  `node_id`, `display_name` (không phải `name`), mô tả A5 cắt còn tối đa 200 ký tự, và kiểu cạnh mở trong module đã xác nhận (ví dụ `subtype_of`).
- **Ứng viên của tầng 2:** 3–5 tiêu đề hoặc cụm có điểm cao nhất, kèm điểm.
- **Đối chứng:** chỉ tên (tầng 1 hoặc 2) và tên khái niệm của module ngay trước và ngay sau (±1), ghi rõ "không thuộc module này". Không gửi
  mô tả của module kề. Ngữ cảnh kề ±1 đủ: heading kề nhau cho phần lớn lợi ích, còn gửi mọi heading trước chỉ thêm 0,1–0,6 điểm [22].
- **Ràng buộc:** độ dài tối đa tính bằng ký tự (ví dụ 60 ký tự cho tên), ngôn ngữ của tài liệu, cấm số đánh mục, cấm từ chỉ có ở module kề.
  Mọi giới hạn mã sẽ kiểm phải được ghi trong prompt; xstk đã hỏng vì thiếu điều này (mục 2.4).

Lược đồ JSON đầu ra như sau:

```json
{
  "title": "Phép toán trên ma trận",
  "title_terms_from": ["n_12", "s_2_1_3"],
  "description": [
    {"text": "Cộng, nhân với một số, nhân hai ma trận, lũy thừa và chuyển vị.", "node_ids": ["n_12", "n_13", "n_14", "n_15", "n_16"]},
    {"text": "Dựa trên các dạng ma trận đặc biệt ở module trước.", "node_ids": ["n_12"], "module_ids": ["module_008"]}
  ]
}
```

Có năm luật kiểm bằng mã. Hỏng ở luật nào cũng giữ kết quả tầng 2; không hỏi lại, vì luật được nêu trong prompt:
1. Mọi token nội dung của `title` và `description` phải có trong từ vựng của module đích: tên, alias, mô tả A5 của các khái niệm, và tiêu đề
   các mục chứa chúng. Ngoại lệ là các token chức năng, nhận ra bằng tần suất trong chính tài liệu (ví dụ nằm trong 1% token phổ biến nhất của
   cuốn), không bằng danh sách từ viết tay.
2. Token chỉ có ở từ vựng module kề mà không có ở module đích thì là "mượn". Câu chứa token mượn bị loại.
3. `node_ids` của mỗi câu phải thuộc module đích; `module_ids` chỉ được là module phụ thuộc trong `module_dependencies`. Mỗi câu cần ít nhất
   một `node_id`. Đây là bản rút gọn của citation precision/recall trong ALCE [27]. Mỗi khái niệm đã có đúng một chunk dạy và mô tả A5 đã
   kiểm trích dẫn, nên trích tới `node_id` là đủ; không cần trích thẳng tới chunk.
4. Tên ≤ 60 ký tự, không trùng (sau chuẩn hoá) với tên module ±2, không là nhãn đánh số theo luật họ nhãn R9.
5. Mỗi mảnh giữa hai dấu " · " (nếu có) phải là một tên khái niệm nguyên vẹn hoặc một tiêu đề mục nguyên vẹn. Luật hiện tại kiểm cả chuỗi
   nên để lọt "Tích hợp · Giảm".

Khoá cache là băm của: `model_id`, băm prompt, băm schema, cấu hình sinh, và JSON chuẩn hoá của đầu vào (gồm cả tên module kề). Hệ quả: đổi
tên một module sẽ làm mất cache của hai module kề, và như vậy là đúng. Không dùng lại tên từ artifact cũ khi băm prompt khác; nhánh
`reuse_artifact` hiện tại đã giữ lại các tên mẩu cũ.

Nhiệt độ: giữ 0 như các khâu khác để so sánh được; tính tái lập dựa vào cache, không dựa vào nhiệt độ. Hướng dẫn Gemini 3 khuyên giữ 1.0
([nghiên cứu Gemini](nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md)); nếu đổi thì phải thử đối chứng.

Chi phí ước cho tầng 3, giả định 30–50% module rơi vào tầng này:
- doc-4: 26–44 lời gọi × (khoảng 900 token vào, 150 token ra), khoảng 0,012–0,02 USD;
- doc-1: 10–16 lời gọi, dưới 0,01 USD;
- thời gian: dưới 30 giây ở song song 16 (*Suy luận*, cần đo).

### 6.3 Bản seminar: tầng 1–2 không LLM

Thuật toán gồm bốn bước:
1. **Sinh ứng viên:**
   - tiêu đề của mục trùng (E), mục đa số, tổ tiên chung sâu nhất, và cặp hai mục con lớn nhất ghép bằng " · " (luật gốc của A10);
   - tên hiển thị của các khái niệm;
   - "đầu chung": tiền tố âm tiết dài nhất dùng chung bởi ít nhất hai tên trong module (ví dụ "Ma trận" trong "Ma trận thực/không/hàng/cột");
   - cụm từ khoá c-TF-IDF [10] tính trên mô tả và câu neo, với lớp là module và nền đối chứng là các module cùng chương. Chỉ giữ cụm có trong
     tên khái niệm hoặc tiêu đề (có căn cứ). Tách từ bằng underthesea [52] (Apache-2.0) hoặc VnCoreNLP [51]; khi đưa vào mã sản phẩm, xem
     lại giấy phép theo [báo cáo trước](nghien-cuu-ml-dl-loc-cap-va-tien-quyet-2026-10-04.md).
2. **Chấm điểm** mỗi ứng viên bằng tổ hợp tuyến tính các đặc trưng sau (trọng số chọn trên tập phát triển, xem mục 7):
   - *liên quan:* cosine giữa embedding ứng viên và trọng tâm mô tả của module (multilingual-e5 [53] hoặc PhoBERT [50]);
   - *phủ:* tỉ lệ khái niệm của module có tên chứa ứng viên hoặc gần nó về embedding;
   - *phân biệt:* liên quan tới module đích trừ liên quan lớn nhất tới module ±1, theo cách Mei và cộng sự trừ điểm của chủ đề khác [1];
   - *trung tâm:* bậc vào của khái niệm qua cạnh `subtype_of`/`component_of` trong module, cộng số module sau phụ thuộc vào nó;
   - *tiền nghiệm tác giả:* thưởng nếu ứng viên là tiêu đề mục `noi_dung` và mục đó trùng module;
   - *phạt:* độ dài, tiêu đề chung chung (6.4), mảnh không nguyên vẹn.
3. **Ghép theo khuôn:** "tiêu đề tốt nhất" nếu điểm phủ ≥ ngưỡng. Nếu không thì "tiêu đề — 1–2 tên khái niệm", chọn bằng MMR [47], [48] để
   tên vừa đại diện vừa khác module kề. Tài liệu không có cây thì dùng "2–3 tên khái niệm" chọn bằng MMR. Cuối cùng kiểm trùng với ±2.
4. **Mô tả khuôn** (không sinh văn bản tự do), gồm hai câu:
   - "Gồm {c1}, {c2} và {c3}{, cùng k khái niệm khác}." Thứ tự là thứ tự dãy học, ưu tiên khái niệm trung tâm.
   - "Cần học trước: {tên module phụ thuộc}." Câu này lấy từ `module_dependencies`.
   - Khi có cạnh mở đã xác nhận, thêm mệnh đề quan hệ, ví dụ "{A}, {B} là các dạng của {C}" từ `subtype_of`.

Điểm tin cậy dùng để quyết tầng 3 là điểm của ứng viên thắng cộng biên cách ứng viên thứ hai. Ngưỡng chọn sao cho tầng 3 nhận các module mà
người chấm ở thí nghiệm 0 thấy tên tầng 2 kém.

*Suy luận về câu hỏi "bản không LLM có đủ tốt để dùng chung không":* có ba lý do để tin là có thể. 36% module dùng thẳng tiêu đề tác giả.
Sách thường có sẵn tiêu đề mục con nói đúng ý mà LLM sẽ viết lại, ví dụ "2.1.3 Phép toán trên ma trận" đã có trong cây doc-1. Lỗi nặng nhất
hiện nay sửa được bằng mã (mục 6.5). Chỗ LLM còn hơn là nén nhiều tên thành một cụm tự nhiên, ở tài liệu phẳng hoặc cây hỏng. Việc có dùng
chung hay không phải do thí nghiệm ở mục 7 quyết, theo luật viết trước.

### 6.4 Khi nào giữ nguyên tiêu đề tác giả

Giữ nguyên ở cả hai bản khi đủ năm điều kiện:
1. Module loại E.
2. Mục có vai trò nội dung.
3. Tiêu đề không phải nhãn chung. Nhãn chung nhận bằng bằng chứng trong chính tài liệu, không bằng danh sách từ: cùng chuỗi tiêu đề (bỏ số)
   xuất hiện ở từ hai mục cha khác nhau trở lên ("Tính chất", "Định nghĩa", "Các khái niệm cơ bản").
4. Tiêu đề không trùng với tên module ±2 sau khi bỏ số.
5. Tiêu đề không phải nhãn đầu đoạn (kết thúc bằng ":") hay chỉ có mã ("Chương XI").

Nếu là nhãn chung hoặc trùng thì ghép với tiêu đề mục cha gần nhất có nội dung, ví dụ "Định thức — Tính chất". Cách này theo đặc trưng toàn
cục của Branavan và cộng sự, vốn phạt tiêu đề trùng với anh em hoặc với cha [21].

Về số đánh mục:
- Giữ số đường dẫn toàn cục ("2.1.3"), vì tiêu đề cho thấy tổ chức thứ bậc và tuần tự giúp người đọc dựng dàn ý và tìm nhanh hơn [34].
- Bỏ dấu đánh số cục bộ đứng đầu ("a)", "b)", "I-", "1."), vì đứng một mình trong danh sách module chúng không cho biết vị trí. Nhận bằng mẫu
  Unicode: ký tự chữ hoặc số La Mã ngắn, theo sau là ")", "-" hoặc ".".

### 6.5 Sửa ở chỗ khác, không phải ở khâu tên

Các lỗi sau không nên vá bằng LLM, vì chúng nằm ở dữ liệu vào:

| lỗi | nơi sửa | bằng chứng (mục 2) |
|---|---|---|
| bộ đọc gộp hai dòng tiêu đề thành một ("III- … 1. …") | A1 (bộ đọc); trước mắt khâu tên có thể tách tại mã đánh mục nằm giữa chuỗi | 21 lần bỏ qua vì quá 12 token ở doc-4, nhiều lần do dòng gộp |
| xstk không nhận §2, §3 | A1 | 8/9 module mang "§1. LÝ THUYẾT MẪU" |
| lỗi chữ ("ấn Độ", "(*)", "m ột") | A1 | doc-4 |
| mục nội dung bị gán `de_cuong` | A2 | 16 lần bỏ qua ở doc-4 ("Chương X", "Ý thức xã hội") |
| module vắt qua hai chương | A10 `segment_modules`: coi ranh giới chương là cứng, cho phép module nhỏ hơn 3 ở ranh giới chương | 2/87 module doc-4 |
| trần 12 token cho tiêu đề | khâu tên: đổi sang trần ký tự hoặc phân vị độ dài tiêu đề của chính tài liệu | tiêu đề tiếng Việt 13 âm tiết bị loại |
| tên thô thay tên hiển thị | khâu tên: dùng `display_name` | "Tính chất 3" |

Bộ đọc A1 đang tạm dừng theo quyết định ngày 2026-10-10, nên ba dòng cuối của bảng là việc làm được ngay. Chúng chỉ gỡ một phần 23 tên nhảy
cấp ở doc-4: các ca chỉ vướng tiêu đề thật dài 13–22 âm tiết, như "III- Quy luật thống nhất và đấu tranh của các mặt đối lập". Các ca do vai
trò `de_cuong` hay dòng gộp vẫn cần A2/A1. Trước khi các khâu đó được sửa, khâu tên có thể tạm bỏ qua vai trò `de_cuong` khi mục chứa khái
niệm được dạy. Cách này cần chủ dự án duyệt, vì nó nới một luật của R1.

---

## 7. Giao thức thí nghiệm và đánh giá

### 7.1 Tập dữ liệu

Dùng 142 module của sáu cuốn ở mục 2, chia tầng theo loại E/L/S/R. Đây là tài liệu phát triển: tham số tầng 2 (trọng số, ngưỡng) được chọn trên
bốn cuốn và kiểm trên hai cuốn còn lại, theo kiểu bỏ-một-tài-liệu. Không dùng tập giữ lại d01-t01, d01-t02.

### 7.2 Thí nghiệm 0 USD (làm trước)

Bốn thí nghiệm đều chạy cục bộ:
- **T0.1 — Phát lại luật kiểm.** Áp các luật mới (6.2: ký tự thay token, kiểm từng mảnh, `display_name`) lên 71 câu trả lời có sẵn trong nhật
  ký. Đếm số câu được nhận, và đọc tay các câu được nhận thêm.
- **T0.2 — Các biến thể tất định.** So V0 (hiện trạng), V1 (mục đa số), V2 (tổ tiên chung với trần ký tự), V3 (ghép hai mục con) và V4 (xếp
  hạng đầy đủ 6.3). Embedding chạy cục bộ trên CPU, không tốn tiền.
- **T0.3 — Dựng lại tiêu đề đã giấu.** Áp trên 51 module loại E. Giấu tiêu đề của chính mục đó (vẫn cho tiêu đề cha), cho V4 sinh tên, rồi so
  với tiêu đề tác giả. Tiêu đề tác giả chỉ là tham chiếu bạc: Branavan và cộng sự cho thấy nhiều tiêu đề máy gần nghĩa mà ROUGE không bắt được
  [21].
- **T0.4 — Chấm mù theo cặp V0 với biến thể tất định tốt nhất** (7.4).

### 7.3 Độ đo tự động

Bảng dưới liệt kê độ đo; mọi độ đo tính cho từng cuốn rồi lấy trung vị:

| độ đo | định nghĩa | dùng cho |
|---|---|---|
| khớp tên–module (kiểu intrusion [9]) | cho một tên và danh sách khái niệm của module đó cùng hai module kề, chọn đúng module; ngẫu nhiên = 1/3. Làm cả chiều ngược: cho danh sách khái niệm và ba tên. Người chấm thật, hoặc LLM làm proxy (bạc) | phân biệt |
| giống nhau với module kề | cosine lớn nhất (multilingual-e5) giữa tên module i và tên i±1, i±2; số cặp kề trùng sau chuẩn hoá | phân biệt |
| dựng lại tiêu đề đã giấu | chrF (n-gram ký tự, hợp âm tiết tiếng Việt), khớp đúng sau chuẩn hoá, cosine embedding; trên 51 module E | đúng nội dung |
| tỉ lệ từ có căn cứ | tỉ lệ token nội dung có trong từ vựng module đích | trung thực |
| tỉ lệ mượn | tỉ lệ tên/câu chứa token chỉ có ở module kề | trung thực, câu hỏi 1 |
| độ dài | ký tự và âm tiết; tỉ lệ vượt trần | ngắn gọn |
| trích dẫn của mô tả | citation precision/recall theo `node_id` [27] | trung thực |
| ổn định | chạy lại 30 module ba lần ở nhiệt độ 0; tỉ lệ đầu ra giống hệt | tái lập |

### 7.4 Chấm bằng người (kết luận cuối)

Cách chấm theo cặp:
- Mỗi phiếu có danh sách khái niệm (tên hiển thị và mô tả ngắn), tên hai module kề, và hai tên (hoặc hai mô tả) A/B của hai hệ.
- Thứ tự A/B ngẫu nhiên theo phiếu; người chấm không biết hệ nào.
- Người chấm chọn "A tốt hơn / ngang / B tốt hơn" cho từng tiêu chí của rubric, rồi chọn một kết luận chung.
- Có thể dùng best–worst scaling khi so từ ba hệ trở lên, vì nó tin cậy hơn thang điểm khi cùng số lượt chấm [56].

Rubric cho tên có bốn tiêu chí:
1. **Đúng nội dung:** tên nói đúng điều module dạy, không rộng hơn (kiểu "Phần II") hay hẹp hơn (chỉ một khái niệm).
2. **Phân biệt:** đọc tên biết module này khác hai module kề ở đâu.
3. **Ngắn gọn:** không thừa mã, dấu đánh số, mẩu tên.
4. **Tự nhiên:** là một cụm tiếng Việt người dạy có thể viết; thuật ngữ tiếng Anh được phép nếu sách dùng.

Rubric cho mô tả có hai tiêu chí. **Trung thực** chấm theo mức câu, kiểu FActScore [26]: mỗi mệnh đề được tài liệu chống đỡ hay không.
**Hữu ích** hỏi: đọc xong có biết học gì và cần gì trước không.

Người chấm và độ đồng thuận:
- Ít nhất hai người, ví dụ chủ dự án và một thành viên nhóm đồ án, chấm độc lập toàn bộ 142 phiếu tên.
- Mô tả chấm trên mẫu 60 module, chia tầng theo loại.
- Báo Cohen κ [54] hoặc Krippendorff α [55] cho kết luận chung; dưới 0,6 thì sửa rubric và chấm lại một mẫu.
- Thực hành theo khuyến nghị đánh giá người cho NLG [57]: công bố rubric, số người chấm, phân bố "ngang".

Cỡ mẫu (tính bằng kiểm định dấu, một phía, α = 0,05, chỉ đếm phiếu không ngang):
- với 100 phiếu không ngang, cần ít nhất 59 phiếu thắng;
- lực kiểm định là 0,62 nếu tỉ lệ thắng thật là 60%, 0,91 nếu là 65%;
- với 60 phiếu không ngang, lực chỉ là 0,45 và 0,75.

Vì vậy nên chấm đủ 142 module, không lấy mẫu nhỏ hơn.

### 7.5 Thí nghiệm có tiền nhỏ (chỉ dự toán, chưa chạy)

Ba biến thể LLM chạy trên 142 module bằng `gemini-3.1-flash-lite`:
- **L1:** phương án (a), có đối chứng ±1;
- **L2:** phương án (a), không có module kề;
- **L3:** tầng 3 của (e), từ vựng đóng, có đối chứng ±1.

L1 so với L2 trả lời trực tiếp câu hỏi 1: module kề có tăng độ phân biệt và có gây mượn không.

| khoản | số lời gọi | token vào/ra mỗi lời gọi | USD |
|---|---:|---|---:|
| sinh tên + mô tả, 3 biến thể × 142 | 426 | 1.200 / 160 | 0,23 |
| chạy lại 30 module × 3 lần × 3 biến thể (ổn định) | 270 | 1.200 / 160 | 0,15 |
| LLM làm giám khảo theo cặp, hai thứ tự, 3 cặp × 142 | 852 | 1.500 / 60 | 0,40 |
| dự phòng hỏi lại và lỗi 20% | | | 0,16 |
| **tổng** | | | **khoảng 0,94** |

LLM làm giám khảo chỉ để sàng lọc, vì có thiên lệch vị trí:
- Ở MT-Bench, GPT-4 chỉ cho kết quả nhất quán khi đảo thứ tự ở 65% ca; Claude-v1 23,8%, GPT-3.5 46,2% [28].
- Đổi thứ tự trình bày làm Vicuna-13B "thắng" ChatGPT ở 66/80 câu hỏi khi ChatGPT làm giám khảo [29].

Cách giảm theo [28], [29]:
- gọi hai lần với hai thứ tự, chỉ tính thắng khi cả hai lần cùng chọn;
- lần nào lệch thì tính "ngang";
- báo tỉ lệ lệch.

Kết luận cuối vẫn lấy từ người chấm (7.4).

### 7.6 Luật quyết định (viết trước khi đo)

Bốn luật sau phải ghi vào vé trước khi chạy:
1. **Thay V0 bằng biến thể tất định tốt nhất** khi đủ ba điều kiện:
   - thắng ở ít nhất 59/100 phiếu không ngang (kiểm định dấu p < 0,05);
   - không tăng số cặp kề trùng;
   - tỉ lệ từ có căn cứ của tên là 100%.
2. **Giữ tầng 3 LLM trong đồ án** chỉ khi đủ ba điều kiện:
   - L3 thắng biến thể tất định tốt nhất với tỉ lệ thắng ≥ 60% phiếu không ngang (kiểm định dấu p < 0,05), trên các module tầng 3 nhận;
   - tỉ lệ mượn ≤ 1%;
   - mọi tên qua luật kiểm.
   Nếu không đủ, đồ án dùng chung bản tất định với seminar, tức là bỏ LLM khỏi khâu tên sớm hơn đích dài hạn.
3. **Đưa module kề vào lời gọi** chỉ khi L1 hơn L2 ở độ đo khớp tên–module ít nhất 5 điểm phần trăm và tỉ lệ mượn của L1 ≤ 1%.
4. **Dùng mô tả do LLM viết thay mô tả khuôn** chỉ khi hai điều kiện đều đạt trên mẫu 60 module chấm bằng người:
   - ≥ 95% câu được chống đỡ hoàn toàn;
   - không câu nào sai nghiêm trọng (nêu khái niệm không có trong module).

Số đo tự động và giám khảo LLM là thông tin để đọc kỹ, không phải cổng tự động. Quyết định cuối do người đọc các ca thắng thua.

---

## 8. Rủi ro và câu hỏi mở

Năm rủi ro chính:
- **Cây mục vẫn hỏng.** A1 đang tạm dừng, nên xstk và các cuốn có tiêu đề gộp dòng vẫn cho ứng viên tiêu đề sai. Tầng 2 phải đủ mạnh khi chỉ có
  tên khái niệm.
- **Người chấm ít.** Hai người chấm, cùng nhóm dự án, có thể thiên vị cách viết quen. Phải chấm mù và báo độ đồng thuận.
- **Tiêu đề tác giả làm tham chiếu bạc.** Có ở 51 module, nhưng tác giả cũng viết nhãn chung [21]. Điểm dựng lại cao không có nghĩa là tên tốt.
- **NLI và embedding tiếng Việt chưa được đo** trên tên ngắn có xen thuật ngữ tiếng Anh.
- **Mô hình hết hạn.** `gemini-3.1-flash-lite` có ngày tắt sớm nhất 2027-05-07; cache phải gắn `model_id`.

Câu hỏi mở cho chủ dự án:
1. Có đồng ý phương án (e) và luật quyết định ở mục 7.6, gồm khả năng bỏ hẳn LLM khỏi khâu tên của đồ án nếu bản tất định không thua?
2. Ai là người chấm thứ hai, và có chấm đủ 142 module không (khoảng 2–3 giờ mỗi người, *Suy luận*)?
3. Có cho khâu tên tạm bỏ qua vai trò `de_cuong` khi mục chứa khái niệm được dạy, trước khi A2 được sửa?
4. Có sửa câu lý do của R7 như mục 4, câu hỏi 5?
5. Mô tả 1–2 câu ở A10 có hiện cho người học ngay, hay chờ A11 (`summary`, `objectives`)?
6. Có giữ số đường dẫn mục ("2.1.3") trong tên hiển thị không?

---

## 9. Nguồn

Mọi trang được mở ngày 2026-10-11. Mức đọc ghi cuối mỗi dòng.

[1] Q. Mei, X. Shen, and C. Zhai, "Automatic labeling of multinomial topic models," in *Proc. 13th ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining*, San Jose, CA, USA, 2007, pp. 490–499, doi: 10.1145/1281192.1281246. — đọc phần phương pháp (bản của tác giả: https://public.websites.umich.edu/~qmei/pub/kdd07-label.pdf).

[2] J. H. Lau, K. Grieser, D. Newman, and T. Baldwin, "Automatic labelling of topic models," in *Proc. 49th Annu. Meeting Assoc. Comput. Linguistics (ACL-HLT)*, Portland, OR, USA, 2011, pp. 1536–1545. https://aclanthology.org/P11-1154/ — đọc toàn văn.

[3] S. Bhatia, J. H. Lau, and T. Baldwin, "Automatic labelling of topics with neural embeddings," in *Proc. COLING 2016*, Osaka, Japan, 2016, pp. 953–963. https://aclanthology.org/C16-1091/ — đọc tóm tắt và phần kết quả.

[4] A. Alokaili, N. Aletras, and M. Stevenson, "Automatic generation of topic labels," in *Proc. 43rd Int. ACM SIGIR Conf.*, 2020, pp. 1965–1968, doi: 10.1145/3397271.3401185. — đọc toàn văn (arXiv:2006.00127).

[5] P. Treeratpituk and J. Callan, "Automatically labeling hierarchical clusters," in *Proc. 2006 Int. Conf. Digital Government Research*, 2006, pp. 167–176, doi: 10.1145/1146598.1146650. — chỉ đọc tóm tắt.

[6] E. J. Glover, D. M. Pennock, S. Lawrence, and R. Krovetz, "Inferring hierarchical descriptions," in *Proc. 11th ACM CIKM*, 2002, pp. 507–514, doi: 10.1145/584792.584876. — chỉ kiểm siêu dữ liệu; nội dung qua [7].

[7] C. D. Manning, P. Raghavan, and H. Schütze, *Introduction to Information Retrieval*. Cambridge, U.K.: Cambridge Univ. Press, 2008, §17.7, §17.9. https://nlp.stanford.edu/IR-book/ — đọc phần liên quan.

[8] D. Carmel, H. Roitman, and N. Zwerdling, "Enhancing cluster labeling using Wikipedia," in *Proc. 32nd Int. ACM SIGIR Conf.*, 2009, pp. 139–146, doi: 10.1145/1571941.1571967. — chỉ kiểm siêu dữ liệu; không dùng cho nhận định nào.

[9] J. Chang, S. Gerrish, C. Wang, J. Boyd-Graber, and D. M. Blei, "Reading tea leaves: How humans interpret topic models," in *Advances in Neural Information Processing Systems 22*, 2009. https://papers.nips.cc/paper_files/paper/2009/hash/f92586a25bb3145facd64ab20fd554ff-Abstract.html — đọc phần nhiệm vụ và kết quả.

[10] M. Grootendorst, "BERTopic: Neural topic modeling with a class-based TF-IDF procedure," arXiv:2203.05794, 2022. — đọc phần phương pháp.

[11] C. M. Pham, A. Hoyle, S. Sun, P. Resnik, and M. Iyyer, "TopicGPT: A prompt-based topic modeling framework," in *Proc. NAACL-HLT 2024 (Vol. 1)*, Mexico City, Mexico, 2024, pp. 2956–2984, doi: 10.18653/v1/2024.naacl-long.164. — đọc phần phương pháp và đánh giá người.

[12] Z. Wang, J. Shang, and R. Zhong, "Goal-driven explainable clustering via language descriptions," in *Proc. EMNLP 2023*, Singapore, 2023, pp. 10626–10649. https://aclanthology.org/2023.emnlp-main.657/ — chỉ đọc tóm tắt.

[13] D. Stammbach, V. Zouhar, A. Hoyle, M. Sachan, and E. Ash, "Revisiting automated topic model evaluation with large language models," in *Proc. EMNLP 2023*, Singapore, 2023, pp. 9348–9357. https://aclanthology.org/2023.emnlp-main.581/ — chỉ đọc tóm tắt.

[14] A. Piper and S. Wu, "Evaluating large language models for narrative topic labeling," in *Proc. 5th Int. Conf. Natural Language Processing for Digital Humanities (NLP4DH)*, 2025, pp. 281–291. https://aclanthology.org/2025.nlp4dh-1.25/ — đọc phần phương pháp và kết quả.

[15] E. Rijcken, F. Scheepers, K. Zervanou, M. Spruit, P. Mosteiro, and U. Kaymak, "Towards interpreting topic models with ChatGPT," presented at the *20th World Congress of the Int. Fuzzy Systems Association (IFSA)*, Daegu, Korea, 2023. https://research.tue.nl/en/publications/towards-interpreting-topic-models-with-chatgpt/ — chỉ đọc tóm tắt.

[16] A. Tamkin *et al.*, "Clio: Privacy-preserving insights into real-world AI use," arXiv:2412.13678, 2024. — đọc phần đặt tên cụm (phụ lục G) và kiểm tay (phụ lục C).

[17] R. Zhong, C. Snell, D. Klein, and J. Steinhardt, "Describing differences between text distributions with natural language," in *Proc. 39th ICML*, PMLR 162, 2022, pp. 27099–27116. — đọc tóm tắt và phần phương pháp.

[18] R. Zhong, P. Zhang, S. Li, J. Ahn, D. Klein, and J. Steinhardt, "Goal driven discovery of distributional differences via language descriptions," in *Advances in Neural Information Processing Systems 36*, 2023. arXiv:2302.14233 — chỉ đọc tóm tắt.

[19] F. Shi *et al.*, "Large language models can be easily distracted by irrelevant context," in *Proc. 40th ICML*, PMLR 202, 2023, pp. 31210–31227. — chỉ đọc tóm tắt.

[20] N. F. Liu *et al.*, "Lost in the middle: How language models use long contexts," *Trans. Assoc. Comput. Linguistics*, vol. 12, pp. 157–173, 2024. — chỉ đọc tóm tắt.

[21] S. R. K. Branavan, P. Deshpande, and R. Barzilay, "Generating a table-of-contents," in *Proc. 45th Annu. Meeting ACL*, Prague, Czech Republic, 2007, pp. 544–551. https://aclanthology.org/P07-1069/ — đọc toàn văn; bảng 4 đối chiếu bằng ảnh trang.

[22] R. Zhang, J. Guo, Y. Fan, Y. Lan, and X. Cheng, "Outline generation: Understanding the inherent content structure of documents," in *Proc. 42nd Int. ACM SIGIR Conf.*, Paris, France, 2019, pp. 745–754, doi: 10.1145/3331184.3331208. — đọc phần phương pháp và kết quả (arXiv:1905.10039).

[23] A. Field, S. Rothe, S. Baumgartner, C. Yu, and A. Ittycheriah, "A generative approach to titling and clustering Wikipedia sections," in *Proc. 4th Workshop on Neural Generation and Translation*, 2020. arXiv:2005.11216 — chỉ đọc tóm tắt.

[24] J. Maynez, S. Narayan, B. Bohnet, and R. McDonald, "On faithfulness and factuality in abstractive summarization," in *Proc. 58th Annu. Meeting ACL*, 2020, pp. 1906–1919. — đọc tóm tắt và phần kết luận chính.

[25] P. Laban, T. Schnabel, P. N. Bennett, and M. A. Hearst, "SummaC: Re-visiting NLI-based models for inconsistency detection in summarization," *Trans. Assoc. Comput. Linguistics*, vol. 10, pp. 163–177, 2022. — chỉ đọc tóm tắt.

[26] S. Min *et al.*, "FActScore: Fine-grained atomic evaluation of factual precision in long form text generation," in *Proc. EMNLP 2023*, Singapore, 2023, pp. 12076–12100. — chỉ đọc tóm tắt.

[27] T. Gao, H. Yen, J. Yu, and D. Chen, "Enabling large language models to generate text with citations," in *Proc. EMNLP 2023*, Singapore, 2023, pp. 6465–6488. — đọc tóm tắt và phần định nghĩa độ đo.

[28] L. Zheng *et al.*, "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena," in *Advances in Neural Information Processing Systems 36 (Datasets and Benchmarks)*, 2023, pp. 46595–46623. — đọc phần thiên lệch vị trí và đồng thuận.

[29] P. Wang *et al.*, "Large language models are not fair evaluators," in *Proc. 62nd Annu. Meeting ACL (Vol. 1)*, Bangkok, Thailand, 2024, pp. 9440–9450, doi: 10.18653/v1/2024.acl-long.511. — chỉ đọc tóm tắt.

[30] Z. Ji *et al.*, "Survey of hallucination in natural language generation," *ACM Computing Surveys*, vol. 55, no. 12, Art. no. 248, 2023 (trùng đề cương [7]). — chỉ kiểm siêu dữ liệu; dẫn làm nền.

[31] R. F. Lorch, Jr., "Text-signaling devices and their effects on reading and memory processes," *Educational Psychology Review*, vol. 1, no. 3, pp. 209–234, 1989, doi: 10.1007/BF01320135. — chỉ đọc tóm tắt.

[32] R. F. Lorch, Jr. and E. P. Lorch, "Effects of headings on text recall and summarization," *Contemporary Educational Psychology*, vol. 21, no. 3, pp. 261–278, 1996, doi: 10.1006/ceps.1996.0022. — chỉ kiểm siêu dữ liệu (nhà xuất bản chặn truy cập tự động).

[33] J. Hartley and M. Trueman, "A research strategy for text designers: The role of headings," *Instructional Science*, vol. 14, no. 2, pp. 99–155, 1985, doi: 10.1007/BF00052394. — chỉ đọc tóm tắt.

[34] R. F. Lorch, Jr., J. Lemarié, and R. A. Grant, "Signaling hierarchical and sequential organization in expository text," *Scientific Studies of Reading*, vol. 15, no. 3, pp. 267–284, 2011, doi: 10.1080/10888431003747535. — chỉ đọc tóm tắt (ERIC EJ922663).

[35] J. Richter, K. Scheiter, and A. Eitel, "Signaling text-picture relations in multimedia learning: A comprehensive meta-analysis," *Educational Research Review*, vol. 17, pp. 19–36, 2016, doi: 10.1016/j.edurev.2015.12.003. — chỉ đọc tóm tắt (qua bản ghi dữ liệu PsychArchives, doi: 10.23668/psycharchives.2387).

[36] S. Schneider, M. Beege, S. Nebel, and G. D. Rey, "A meta-analysis of how signaling affects learning with media," *Educational Research Review*, vol. 23, pp. 1–24, 2018, doi: 10.1016/j.edurev.2017.11.001. — chỉ kiểm siêu dữ liệu; số liệu qua [37], **chưa đối chiếu với nguồn gốc**.

[37] Clearinghouse Unterricht, TU München, "Kurzreview 22: Gestaltung von Lernmaterial: Wie Hervorhebungen den Lernerfolg beeinflussen," 2018. https://www.clearinghouse.edu.tum.de/wp-content/uploads/2018/12/CHU_KR-22_-Schneider_2017_Lernmaterial_Hervorhebungen.pdf — đọc toàn văn (nguồn thứ cấp).

[38] D. Alpizar, O. O. Adesope, and R. M. Wong, "A meta-analysis of signaling principle in multimedia learning environments," *Educational Technology Research and Development*, vol. 68, no. 5, pp. 2095–2119, 2020, doi: 10.1007/s11423-020-09748-7. — chỉ đọc tóm tắt.

[39] T. van Gog, "The signaling (or cueing) principle in multimedia learning," in *The Cambridge Handbook of Multimedia Learning*, 2nd ed., R. E. Mayer, Ed. Cambridge, U.K.: Cambridge Univ. Press, 2014, pp. 263–278, doi: 10.1017/CBO9781139547369.014. — chỉ kiểm siêu dữ liệu.

[40] R. E. Mayer and L. Fiorella, "Principles for reducing extraneous processing in multimedia learning: Coherence, signaling, redundancy, spatial contiguity, and temporal contiguity principles," in *The Cambridge Handbook of Multimedia Learning*, 2nd ed., 2014, pp. 279–315, doi: 10.1017/CBO9781139547369.015. — chỉ kiểm siêu dữ liệu.

[41] L. W. Anderson and D. R. Krathwohl, Eds., *A Taxonomy for Learning, Teaching, and Assessing: A Revision of Bloom's Taxonomy of Educational Objectives*. New York, NY, USA: Longman, 2001. — chỉ kiểm siêu dữ liệu.

[42] D. R. Krathwohl, "A revision of Bloom's taxonomy: An overview," *Theory Into Practice*, vol. 41, no. 4, pp. 212–218, 2002, doi: 10.1207/s15430421tip4104_2. — chỉ kiểm siêu dữ liệu.

[43] R. J. Hamilton, "A framework for the evaluation of the effectiveness of adjunct questions and objectives," *Review of Educational Research*, vol. 55, no. 1, pp. 47–85, 1985, doi: 10.3102/00346543055001047. — chỉ đọc tóm tắt (ERIC EJ317651).

[44] P. Sridhar *et al.*, "Harnessing LLMs in curricular design: Using GPT-4 to support authoring of learning objectives," arXiv:2306.17459, 2023. — chỉ đọc tóm tắt.

[45] R. Mihalcea and P. Tarau, "TextRank: Bringing order into texts," in *Proc. EMNLP 2004*, Barcelona, Spain, 2004, pp. 404–411. — đọc phần trích từ khoá.

[46] R. Campos *et al.*, "YAKE! Keyword extraction from single documents using multiple local features," *Information Sciences*, vol. 509, pp. 257–289, 2020, doi: 10.1016/j.ins.2019.09.013. — chỉ kiểm siêu dữ liệu.

[47] K. Bennani-Smires, C. Musat, A. Hossmann, M. Baeriswyl, and M. Jaggi, "Simple unsupervised keyphrase extraction using sentence embeddings," in *Proc. 22nd CoNLL*, Brussels, Belgium, 2018, pp. 221–229. — đọc tóm tắt và phần MMR.

[48] J. Carbonell and J. Goldstein, "The use of MMR, diversity-based reranking for reordering documents and producing summaries," in *Proc. 21st ACM SIGIR*, 1998, pp. 335–336, doi: 10.1145/290941.291025. — chỉ kiểm siêu dữ liệu.

[49] M. Grootendorst, *KeyBERT* (phần mềm), Zenodo, 2021, doi: 10.5281/zenodo.4461265. — chỉ kiểm siêu dữ liệu.

[50] D. Q. Nguyen and A. T. Nguyen, "PhoBERT: Pre-trained language models for Vietnamese," in *Findings of EMNLP 2020*, pp. 1037–1042. — chỉ đọc tóm tắt; giới hạn dẫn theo báo cáo ML/DL của dự án.

[51] T. Vu, D. Q. Nguyen, D. Q. Nguyen, M. Dras, and M. Johnson, "VnCoreNLP: A Vietnamese natural language processing toolkit," in *Proc. NAACL-HLT 2018: Demonstrations*, New Orleans, LA, USA, 2018, pp. 56–60. — chỉ đọc tóm tắt.

[52] undertheseanlp, *underthesea* (phần mềm, Apache-2.0). https://github.com/undertheseanlp/underthesea — chỉ kiểm trang dự án.

[53] L. Wang, N. Yang, X. Huang, L. Yang, R. Majumder, and F. Wei, "Multilingual E5 text embeddings: A technical report," arXiv:2402.05672, 2024. — chỉ đọc tóm tắt.

[54] J. Cohen, "A coefficient of agreement for nominal scales," *Educational and Psychological Measurement*, vol. 20, no. 1, pp. 37–46, 1960 (trùng đề cương [27]). — chỉ kiểm siêu dữ liệu.

[55] K. Krippendorff, *Content Analysis: An Introduction to Its Methodology*, 4th ed. Thousand Oaks, CA, USA: SAGE, 2018. — **chưa xác minh** (dẫn làm phương pháp chuẩn).

[56] S. Kiritchenko and S. M. Mohammad, "Best-worst scaling more reliable than rating scales: A case study on sentiment intensity annotation," in *Proc. 55th Annu. Meeting ACL (Vol. 2)*, Vancouver, Canada, 2017, pp. 465–470. — chỉ đọc tóm tắt.

[57] C. van der Lee, A. Gatt, E. van Miltenburg, S. Wubben, and E. Krahmer, "Best practices for the human evaluation of automatically generated text," in *Proc. 12th Int. Conf. Natural Language Generation (INLG)*, Tokyo, Japan, 2019, pp. 355–368. — chỉ đọc tóm tắt.

Hai nguồn trong gợi ý ban đầu không dùng: Mao và cộng sự (gán nhãn chủ đề phân cấp, CIKM 2012) **chưa xác minh**; Carmel và cộng sự [8] chỉ
kiểm được siêu dữ liệu.
