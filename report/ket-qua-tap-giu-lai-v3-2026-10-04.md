# Kết quả tập giữ lại v3 (T10/07 v2) — 2026-10-04

Đây là kết quả chính của lượt chạy một lần trên hai tài liệu giữ lại, chấm theo [giao thức](../task/v3-lo-trinh-doc-duoc/T10-07v2-giao-thuc-tap-giu-lai.md)
đã chốt trước khi chạy. Báo nguyên kết quả, kể cả phần xấu. Mọi đề xuất sửa ở cuối là hậu kiểm, không thay kết quả này.

## Lượt chạy có sạch không

Lượt chạy **sạch** theo các kiểm sau:
- Mã chạy (`src/`) không đổi so với commit khoá `fce6c48`. Bảng khoá sinh tại `2f03781`.
- Dry-run lệnh `roadmap` đã khoá, với tệp T14, cho ra **11/11 tầng "tái dùng"** ở cả hai tài liệu. Vậy artifact cuối (xstk v46, doc-4 v12)
  đúng là thứ đường chạy đã khoá sinh ra, dù với xstk nhân viên gọi từng bước để dừng giữa pass chính và pass phụ.
- 16 tệp nhãn giữ lại khớp SHA-256 trong bảng khoá trước khi mở.
- doc-4 bị tạm dừng một lần (chủ dự án tắt máy) và chạy tiếp từ điểm lưu, đúng luật "sập giữa chừng thì chạy tiếp, không đổi cấu hình".
- T14: chủ dự án duyệt đủ 13 cặp danh tính trước A8, không mở vàng.

Chi: **51,97 USD** đã ghi nhận (usage LLM cộng cận trên embedding), dưới trần 90 USD. Chưa gồm vài khoản không đo được: lời gọi đang bay lúc
ngắt, một lượt neo doc-4 bị ngắt trước đó, retry embedding. Số HTTP 429 không đo được vì Monitoring/Logging API chưa bật.

## Vàng

- **xstk-ch3-1:** chuyển từ hai bảng người gán và bảng hội ý ngay trước khi chấm (`a8-gold-check` cho A1, A2; `a8-gold-merge` với bảng hội ý).
  - Kết quả: 26 đích, 62 cạnh; concept hash `b2bf64de…` khớp bảng gốc.
  - Hai người gán **chỉ cùng chọn 20 cạnh, khác nhau 67 cạnh**; hội ý giữ 42 trong 67. Bộ vàng này rất nhiễu.
  - SHA-256: vàng `3817f0e5…`, A1 `3b070573…`, A2 `6d016a18…`.
- **doc-4:** vàng đã khoá từ 2026-09-25: 47 đích, 72 cạnh; băm lại khớp `df0c6cb9…`.

## Điểm chính, so với mức tài liệu phát triển

Lệnh chấm: `scripts/doc-lo-trinh/cham_tap_giu_lai.py`, chạy tại commit `5e8e9b5`. Trong ngoặc là Wilson 95%. Cột cuối đọc theo luật đã
chốt: khoảng tin cậy chồng mức phát triển thì "giữ"; cận trên (với tỉ lệ lỗi là cận dưới) xấu hơn mức phát triển thấp nhất thì "không giữ".

| chỉ số | doc-1 (phát triển) | doc-2 (phát triển) | xstk (giữ lại) | doc-4 (giữ lại) | đọc |
|---|---|---|---|---|---|
| Q6 lỗi thứ tự học | 0,103 (0,041–0,236) | 0,228 (0,138–0,352) | **0,550** (0,425–0,669) | 0,157 (0,090–0,260) | xstk không giữ; doc-4 giữ |
| — trong đó ngược / ngoài phạm vi | 1 / 3 | 0 / 13 | 4 / **29** | **11** / 0 | |
| Q7 độ phủ tổ tiên · n gần nhất | 0,667 · 0,921 | 0,395 · 0,703 | 0,414 · 0,654 | **0,322** · 0,945 | xstk giữ; doc-4 dưới mức |
| Q7b độ chính xác tổ tiên · n gần nhất | 0,877 · 0,381 | 0,869 · 0,356 | **0,644** · 0,224 | **0,606** · 0,155 | cả hai dưới mức, vẫn gấp ~3–4 lần đường cơ sở |
| cạnh trực tiếp P | 0,630 (0,442–0,785) | 0,688 (0,444–0,858) | **0,235** (0,096–0,473) | 0,510 (0,375–0,644) | xstk không giữ; doc-4 giữ |
| cạnh trực tiếp R | 0,607 (0,424–0,764) | 0,344 (0,204–0,517) | **0,114** (0,045–0,260) | 0,472 (0,344–0,603) | xstk không giữ; doc-4 giữ |
| cạnh bao đóng P | 0,874 (0,799–0,923) | 0,800 (0,609–0,911) | **0,636** (0,466–0,778) | **0,584** (0,496–0,667) | cả hai không giữ |
| cạnh bao đóng R | 0,740 (0,659–0,808) | 0,294 (0,199–0,411) | 0,214 (0,145–0,305) | 0,459 (0,384–0,537) | cả hai giữ |
| Q2 danh tính còn mở | 0 | 1 nhóm | 0 | 0 | giữ |
| Q3 khái niệm trọng yếu | 81% (phát triển) | | 33/34 | 37/50 | chung 70/84 = 83% (74–90%), giữ; dưới mốc 90% |

Bảng kiểm đọc được (R11):
- xstk có 6 "mục bị xé": 8/9 module mang tên "THỐNG KÊ TOÁN §1. LÝ THUYẾT MẪU — …", kể cả module về ước lượng và kiểm định.
- doc-4 có 8 tên dài; các loại khác 0.

**Tóm lại:**
- Chuỗi v3 **tổng quát hoá một phần**.
- doc-4 là lĩnh vực mới (triết học). Thứ tự học và độ phủ cạnh giữ được mức phát triển; độ chính xác thì không.
- xstk hỏng nặng về phạm vi: một nửa cạnh vàng nằm ngoài dãy học.
- Điểm mạnh chính của vé 12 là độ chính xác khoảng 0,87 trên tài liệu phát triển. Điểm này **không giữ được**: trên tập giữ lại còn 0,58–0,64
  (bao đóng). Một phần do vàng nhiễu (xem dưới), một phần là lỗi thật.

## Vì sao: truy lỗi về khâu

**1. xstk: 29/60 cạnh vàng ngoài dãy học. Nguyên nhân là A2 gán nhầm vai trò vùng, lan sang C8.**
- 48/126 đoạn của xstk bị gán `de_cuong` (đề cương). Đọc lại thì **cả 48 đều là mục "Cách giải"** trong 2.2, 2.3, 2.4, 3.2–3.6, tức nội dung
  dạy cách làm. Đây là kiểu mục mà tài liệu phát triển không có. Bậc 1 đã ghi tỉ lệ 38% này là điểm cần theo dõi.
- 7/8 khái niệm rơi khỏi dãy học có căn cứ A3 nằm trong các mục đó: "Độ chính xác ε", "Khoảng ước lượng của phương sai tổng thể",
  "Ước lượng trung bình", "Xác định kích thước mẫu trong ước lượng trung bình", "Phân phối Student", "Phân phối χ 2"…
- Neo C8 không bao giờ hỏi mô hình về khái niệm chỉ có căn cứ ngoài `noi_dung`, nên chúng nhận thẳng `mentioned_only`. Đây cùng lỗ hổng
  đã thấy ở vé 21 (mục hành chính trong Tổng quan doc-1).
- Hệ quả người học thấy: các khái niệm cốt lõi của ước lượng nằm ở "Nhắc tới" hay "Tổng quan môn học" thay vì trong bài.
- Trong 31 cạnh vàng có hai đầu trong dãy học, máy không có đường đi cho 15 cạnh. Đây là phần thiếu hồi tưởng của A8.

**2. doc-4: 11 cạnh vàng bị xếp ngược. 5 cạnh do luật R17, 6 cạnh do A8 không tìm ra.**
- Máy **đã tìm đúng** 5 cạnh, như "Xã hội → Quy luật xã hội", "Tự nhiên → Quy luật tự nhiên", "Phán đoán → Quy luật của tư duy",
  "Sự thống nhất của các mặt đối lập → Quy luật thống nhất và đấu tranh của các mặt đối lập". Nhưng A10 làm mềm chúng vì **ngược thứ tự sách**
  (R17, vé 18), nên dãy học vẫn theo sách.
- Giáo trình triết học thường nêu một quy luật trước rồi mới giải thích thành phần, hoặc dùng "xã hội", "tự nhiên" ở chương phép biện chứng
  trước khi định nghĩa ở chương sau. Với sách toán, R17 đúng vì sách định nghĩa trước khi dùng; với loại sách này thì không.
- 6 cạnh còn lại máy không có theo đúng chiều:
  - 3 cạnh là thứ tự trong cùng một module: quy luật hay khái niệm đứng đầu mục, thành phần ngay sau ("Mâu thuẫn → Quy luật thống nhất…",
    "Thuộc tính cơ bản → Thuộc tính không cơ bản");
  - 2 cạnh máy có theo chiều ngược: "Tính kế thừa → Phủ định biện chứng" (chiều này còn tranh cãi được) và "Chất → Kết cấu";
  - 1 cạnh vì neo của quy luật nằm ở câu giới thiệu sớm trong mục "Phân loại quy luật".

**3. Độ chính xác tụt: một phần lỗi thật, một phần do vàng nhiễu.** Tôi đọc từng cạnh máy có mà vàng không có:
- **xstk:** 9 cạnh nằm ngoài cả bao đóng vàng.
  - Khoảng 6 cạnh hợp lý mà vàng bỏ sót, ví dụ "Ước lượng điểm → Ước lượng không chệch" với câu trích "Thống kê G được gọi là ước lượng
    không chệch của θ nếu M(G) = θ", hay "Độ chính xác ε → Bài toán thuận".
  - 1 cạnh sai rõ: "Phương sai mẫu hiệu chỉnh → Phân phối chuẩn".
  - Còn lại không rõ ràng.
  - Với vàng mà hai người gán chỉ trùng 20/87 cạnh, độ chính xác 0,64 của xstk là cận dưới, không phải số thật.
- **doc-4:** 20 cạnh ngoài bao đóng vàng; khoảng 6–8 cạnh hợp lý, khoảng 8 cạnh không cần.
  - Kiểu lỗi chính là **khái niệm khung làm tiên quyết**, ví dụ "Phép biện chứng duy vật → Chất", "Phép biện chứng duy vật → Mặt đối lập",
    "Quy luật phổ biến → Quy luật xã hội". Lý do: câu định nghĩa trong giáo trình triết học hay mở đầu bằng "theo phép biện chứng duy vật…",
    và hợp đồng vé 12 nhận một lần nhắc nguyên văn trong cửa sổ định nghĩa làm bằng chứng.
  - 1 cạnh ngược do chọn sai câu neo: neo của "Kết cấu" là một câu về "Chất" có nhắc tới kết cấu, nên ra cạnh "Chất → Kết cấu".

**4. Tên module xstk sai mục.** Cây mục của xstk không tách được §2 (ước lượng) và §3 (kiểm định), nên tên module lấy tiêu đề chung "§1. Lý thuyết
mẫu". Đây là lỗi cấu trúc mục ở A1/A2.

## Đọc lộ trình

- **xstk** (9 module, 72 khái niệm):
  - thứ tự đúng mạch sách: tổng thể và mẫu → thống kê mẫu → tương quan, hồi quy → ước lượng → kiểm định;
  - dòng "cần:" phần lớn đúng, ví dụ "Phương sai mẫu hiệu chỉnh — cần: Phương sai mẫu", "Khoảng tin cậy — cần: Ước lượng khoảng, Độ tin cậy";
  - lỗi người học thấy ngay: tên module sai mục, và khái niệm cốt lõi của 2.2–2.4 nằm ngoài bài.
- **doc-4** (87 module, 489 khái niệm):
  - thứ tự bám giáo trình: triết học → lịch sử triết học → vật chất và ý thức → phép biện chứng (phạm trù, quy luật) → nhận thức → xã hội →
    con người;
  - tên module phần lớn tốt; vài tên yếu như "Tư tưởng triết học:", "Chương XI", "Phần II — …";
  - dòng "cần:" có nhiều khái niệm khung thừa, như "Chất — cần: Phép biện chứng duy vật, Khái niệm, Thuộc tính", "Lượng — cần: Triết học, Chất".

## Ý nghĩa và việc tiếp theo

- Kết quả này là kết quả chính của v3; tập giữ lại đã dùng xong. Cải tiến v4 cần **tập giữ lại mới** (tài liệu mới, vàng mới).
- Lỗi đã truy về khâu, để đưa vào hướng v4 (chưa làm; mỗi sửa phải đo trên tài liệu phát triển và tập giữ lại mới):
  1. **A2:** nhận đúng mục "Cách giải", "Lời giải", "Ví dụ" là nội dung, không phải đề cương.
  2. **C8:** hỏi mô hình cả với khái niệm chỉ có căn cứ ngoài nội dung, thay vì gán thẳng `mentioned_only`. Lỗ này gây hai lỗi: mục hành
     chính trong Tổng quan (doc-1) và khái niệm cốt lõi rơi khỏi bài (xstk).
  3. **R17:** cạnh ngược thứ tự sách hiện luôn bị làm mềm. Cần luật phân biệt "sách dùng trước khi định nghĩa" với "tiên quyết thật".
  4. **A8:** hạ cạnh có nguồn là khái niệm khung (khái niệm chung của cả môn); kiểm hướng cạnh khi câu neo nói về khái niệm khác.
  5. **A1/A2:** cấu trúc mục của tài liệu dạng bài giảng (§1, §2…).
  6. **Đánh giá:** vàng có hai người gán độc lập rất ít trùng (xstk 23%, doc-2 59%). Nên có chấm mù cạnh dư (T15) trên tập giữ lại để biết
     độ chính xác thật.
- Chi phí: doc-4 cả cuốn tốn gần 49 USD, riêng pass phụ khoảng 46 USD (thấp hơn dự toán 68,9 USD nhờ tỉa động), và chạy nhiều giờ. Điều này
  củng cố nguyên tắc số một của v4 (phút/cuốn, USD/cuốn).

Tệp chẩn đoán (không commit, trong `artifacts/holdout-v3/`): điểm JSON hai tài liệu, phân rã phạm vi, danh sách cạnh ngoài vàng kèm câu trích,
bảng đối chiếu Q3.
