# Spec: A4 / A5 — Hợp nhất thực thể (Tầng 2a) và mô tả chuẩn

**Trạng thái:** done
**Nguồn:** phiên grilling 6 vòng · Q1–Q29 (kèm Q21′, Q22′) · D1–D9 phiên chính điền, người dùng đã duyệt
**Nghiên cứu nền:** [`report/nghien-cuu-a4-a5-hop-nhat-thuc-the.md`](../report/nghien-cuu-a4-a5-hop-nhat-thuc-the.md)
**Chi phối bởi:** `spec-addendum.md` §0.1 (hệ kiểu mở) và Tầng 2a · ADR 0001 (định danh tất định) · ADR 0004
(đổi embedding là đổi tập node) · ADR 0005 (id theo ứng viên neo) · ADR 0006 (embedding chỉ đề cử) ·
`CONTEXT.md`: **Thực thể**, **Ứng viên**, **Node canonical**, **Tên chuẩn**, **Alias**, **Ký hiệu**,
**Cặp nghi trùng**, **Cụm ứng viên**

---

## Problem Statement

A3 đã ra bảng ứng viên cho bốn tài liệu: **377 ứng viên văn bản + 79 media**, mỗi ứng viên có câu bằng chứng
định vị được. Nhưng ứng viên sinh **theo section**: cùng một thực thể xuất hiện ở ba section là ba ứng viên.
Chưa gộp thì đồ thị có node trùng, 2b sẽ nối cạnh giữa hai bản sao của cùng một thứ, và lộ trình có mục lặp.

Ba khó khăn, đều đo được trên dữ liệu thật (báo cáo mục 2):

1. **Thiết kế cũ để embedding quyết định danh tính — và nó hỏng.** Với `gemini-embedding-001` trên
   `description_draft`, cosine giữa hai thực thể bất kỳ trong một tài liệu đã là 0,80. Luật *"≥ 0,95 gộp thẳng"*
   đúng 8/62 cặp; *"≥ 0,90"* làm một node nuốt 125/153 ứng viên; đồ thị ngưỡng 0,75 biến mỗi tài liệu thành đúng
   một cụm. 31 cặp khác tên đạt cosine ≥ 0,999 chỉ vì A3 viết cùng một câu mô tả cho các mục liệt kê.
2. **Gộp nhầm là lỗi câm.** Node gộp nhầm trông bình thường — đủ chunk, đủ alias, mô tả trôi chảy. Một thực thể
   biến mất khỏi lộ trình mà không tầng nào báo, và spec cũ không có thao tác tách.
3. **Mô tả chưa dùng được.** Draft của A3 là câu *vai trò tại chỗ được nhắc* (`Naïve Bayes` → *"thuật toán dùng
   để nhận dạng ký tự"*), có draft sai hẳn (một draft của `Kém khớp` tả quá khớp), và lẫn Việt/Anh theo tên thuật
   ngữ. Để mô hình viết lại tự do thì kiến thức nền của mô hình lọt vào đồ thị — đúng chỗ 2b đọc để suy tiên quyết.

## Solution

**Tầng 2a** gộp ứng viên thành **bảng node canonical**, rồi **A5** viết mô tả chuẩn cho từng node:

- Code chỉ tự gộp ứng viên **trùng tên khít**. Mọi tín hiệu khác — alias, tên gần giống, embedding của tên —
  chỉ **đề cử** cặp nghi trùng.
- Cặp nghi trùng gom thành **cụm ứng viên** nhỏ (≤ 9 nhóm). Mỗi cụm một lời gọi mô hình, phán bằng **câu bằng
  chứng nguyên văn**, chia cụm thành node, ghi quan hệ cha–con; phân vân thì không gộp.
- Cặp trùng bị chia sang hai cụm được phán lại bằng cụm nhỏ chứa đủ thành viên của hai node.
- Code lắp node: tên chuẩn, alias, ký hiệu, kiểu, id neo, nhật ký gộp đủ để tách lại.
- A5 viết mô tả **có trích dẫn từng câu**, dài theo lượng bằng chứng, theo ngôn ngữ chủ đạo của tài liệu, và
  gắn cờ khi các nguồn mâu thuẫn — dấu hiệu gộp nhầm.

Từ góc nhìn người dùng, sau đợt này:

- Một lệnh biến bảng ứng viên của một tài liệu thành **bảng node canonical có mô tả**, cạnh đề xuất đã ánh xạ về
  node, sẵn cho 2b.
- **Không gộp nhầm im lặng**: mọi lần gộp có lý do và bằng chứng trong nhật ký; phân vân, sai định dạng hay mâu
  thuẫn đều dẫn tới *không gộp* kèm cảnh báo.
- **Id node đứng yên** khi tên hay mô tả đổi, nên tiến độ học không gãy; id buộc phải đổi thì có bảng chuyển hướng.
- **Đo được**: bộ vàng gán mù, lệnh chấm P/R/F1, so hai lần chạy.
- **Chạy lại rẻ**: quyết định dùng lại theo băm đầu vào; đổi luật ngôn ngữ chỉ gọi lại A5.

## User Stories

1. Là **người dựng lộ trình**, tôi muốn các ứng viên trùng tên khít ở nhiều section được gộp thành một node mà
   không tốn lời gọi mô hình nào, để phần việc rõ ràng nhất không phải trả tiền.
2. Là **người dựng lộ trình**, tôi muốn `hoá` và `hóa` được coi là một tên, để hai cách bỏ dấu thanh không sinh
   hai node.
3. Là **người dựng lộ trình**, tôi muốn `tỷ lệ`/`tỉ lệ` và `giả thiết`/`giả thuyết` không tự gộp mà được đem cho
   mô hình phán, để hai từ có thể khác nghĩa không bị luật chuỗi gộp nhầm.
4. Là **người dựng lộ trình**, tôi muốn cosine không bao giờ tự gộp, để khái niệm anh em (`Ridge`/`LASSO`) và đối
   nghịch (`Quá khớp`/`Kém khớp`) không thành một node.
5. Là **người dựng lộ trình**, tôi muốn hai ứng viên nối nhau qua alias được đem cho mô hình phán thay vì gộp
   thẳng, để alias sai như *"hàm mật độ xác suất f(x) ~ likelihood"* không kéo hai thực thể làm một.
6. Là **người dựng lộ trình**, tôi muốn ký hiệu (`μ`, `x`, `P(A|B)`) không bao giờ dùng để đề cử hay gộp, để `F`
   và `f` không bị coi là một và `x` không nối mọi thứ trong tài liệu.
7. Là **người dựng lộ trình**, tôi muốn chữ viết tắt (`ML`, `JWT`) vẫn là alias, để tra cứu theo viết tắt vẫn dùng
   được.
8. Là **người dựng lộ trình**, tôi muốn cặp nghi trùng được đề cử qua ba kênh — alias, tên gần giống, tên gần
   nghĩa — để cặp trùng khác tên như `End-to-End testing`/`Kiểm thử End-to-End` có cơ hội được gộp.
9. Là **người vận hành**, tôi muốn đồ thị đề cử dựng theo láng giềng gần nhất thay vì ngưỡng cosine tuyệt đối, để
   đổi mô hình embedding không làm mọi ngưỡng mất nghĩa.
10. Là **người vận hành**, tôi muốn mỗi cụm ứng viên không vượt 9 nhóm, để mô hình không tụt chính xác vì quá tải.
11. Là **người vận hành**, tôi muốn nhóm không có cặp nghi trùng nào đi thẳng thành node, để không tốn lời gọi cho
    thứ không có gì để phán.
12. Là **người vận hành**, tôi muốn gom cụm tất định, để hai lần chạy cùng đầu vào ra cùng các cụm.
13. Là **người dựng lộ trình**, tôi muốn mô hình phán bằng câu bằng chứng nguyên văn chứ không bằng draft, để hai
    khái niệm có chung một câu mô tả chung chung không bị phán là một.
14. Là **người dựng lộ trình**, tôi muốn ứng viên có câu bằng chứng không nhắc tên được kèm toàn văn chunk nguồn,
    để mô hình có đủ ngữ cảnh mà không cần tự đi đọc.
15. Là **người dựng lộ trình**, tôi muốn quan hệ cha–con được ghi thành cạnh `subtype_of` có bằng chứng, để quan
    hệ phân loại không mất khi hai node được tách ra.
16. Là **người dựng lộ trình**, tôi muốn bước merge không đề xuất `requires`, để quyết định tiên quyết thuộc về
    đúng một tầng là 2b.
17. Là **người dựng lộ trình**, tôi muốn mô hình phân vân thì đánh `deferred` và không gộp, để lỗi câm không xảy
    ra đúng lúc mô hình không chắc.
18. Là **người dựng lộ trình**, tôi muốn cặp trùng bị chia sang hai cụm được phán lại với đủ ngữ cảnh hai node, để
    `Kiến trúc Hub - Client`/`Mô hình Hub - Client` không thành hai node.
19. Là **người dựng lộ trình**, tôi muốn gộp bắc cầu mà mâu thuẫn với một phán quyết đã có thì thành phần đó không
    gộp và phát cảnh báo, để một phán quyết không âm thầm đè phán quyết khác.
20. Là **người học**, tôi muốn node mang tên đầy đủ mà chính tài liệu dùng nhiều nhất, để tên trên lộ trình khớp với
    chữ tôi đọc trong giáo trình.
21. Là **người học**, tôi muốn node không bao giờ mang tên `μ`, `x` hay `ML` khi tài liệu có tên đầy đủ, để lộ trình
    đọc được.
22. Là **người dựng lộ trình**, tôi muốn alias chưa lọc không bao giờ thành tên chuẩn, để `xử lý tranh chấp dữ liệu`
    không thay `Race Condition`.
23. Là **người dựng lộ trình**, tôi muốn kiểu canonical lấy theo đa số sau khi chuẩn hoá tối thiểu, với luật hoà
    viết thành văn bản, để `định lý`/`theorem` không chia phiếu và kết quả hoà không phụ thuộc thứ tự ứng viên.
24. Là **người review (A13)**, tôi muốn cùng tên mà khác kiểu nằm hai phía `learnable` được đưa vào hàng review, để
    việc chọn kiểu không âm thầm đổi khả năng vào lộ trình.
25. Là **người học**, tôi muốn id node không đổi khi tên chuẩn hay mô tả đổi, để tiến độ học của tôi không mất.
26. Là **người vận hành**, tôi muốn khi id buộc phải đổi thì có bảng chuyển hướng từ id cũ sang id mới, để tham
    chiếu cũ vẫn tìm được node.
27. Là **người review (A13)**, tôi muốn mọi quyết định gộp có nhật ký — thành viên, nhãn, lý do, bằng chứng, mô
    hình, `prompt_hash` — để kiểm và gỡ được.
28. Là **người review (A13)**, tôi muốn dữ liệu đủ để tách một node đã gộp mà không phải trích lại, để thao tác tách
    sau này làm được.
29. Là **agent 2b**, tôi muốn cạnh đề xuất của A3 được ánh xạ về node canonical, bỏ cạnh tự nối, gộp cạnh trùng, để
    đầu vào của tôi không trỏ vào ứng viên đã biến mất.
30. Là **agent pha B**, tôi muốn cạnh media được nối lại về node canonical và trạng thái mồ côi được tính lại, để
    `get_media_for_concept` không trả hình của một node đã gộp mất.
31. Là **người dựng lộ trình**, tôi muốn mọi node trừ media — kể cả kiểu `tool`, `protocol` — có mô tả chuẩn, để UI,
    2b và quiz đều có mô tả.
32. Là **người dựng lộ trình**, tôi muốn node nhiều ứng viên được tổng hợp mô tả từ chunk bằng chứng theo thứ tự tài
    liệu, để định nghĩa đứng trước ví dụ.
33. Là **người vận hành**, tôi muốn node một ứng viên chỉ bị viết lại khi draft không được bằng chứng hỗ trợ hoặc sai
    ngôn ngữ, để không tốn lời gọi và không mở đường rò khi draft đã đúng.
34. Là **người dựng lộ trình**, tôi muốn mỗi câu mô tả kèm `chunk_id` và code từ chối id không thuộc node, để mọi câu
    tra lại được nguồn.
35. Là **người dựng lộ trình**, tôi muốn mô tả dài theo lượng bằng chứng và được phép ghi *"tài liệu không nói
    thêm"*, để mô hình không bịa cho đủ số câu.
36. Là **người học**, tôi muốn mô tả theo ngôn ngữ chủ đạo của tài liệu, để một giáo trình tiếng Việt không có nửa
    số mô tả bằng tiếng Anh.
37. Là **người review (A13)**, tôi muốn nguồn mâu thuẫn không bị hoà giải mà được gắn cờ `nghi_gop_nham`, để gộp nhầm
    có một van phát hiện.
38. Là **agent 2b**, tôi muốn `first_order_index` lấy từ chunk định nghĩa/giảng, còn chỗ chỉ nhắc tên thì nằm ở
    `first_mention_index`, để doc-order prior không bị một dòng tóm tắt đầu tài liệu kéo lệch.
39. Là **người vận hành**, tôi muốn chạy lại A5 — ví dụ khi đổi luật ngôn ngữ — mà không gọi lại mô hình của 2a, để
    chi phí và kết quả gộp không trôi theo.
40. Là **người vận hành**, tôi muốn quyết định được dùng lại theo băm đầu vào khi cụm không đổi, để sửa một section
    chỉ gọi lại những cụm thật sự đổi.
41. Là **người vận hành**, tôi muốn config hash của tầng `canonical` gồm mọi thứ ảnh hưởng kết quả, để đổi thứ gì
    thì ra phiên bản mới thay vì tái dùng im lặng.
42. Là **người vận hành**, tôi muốn manifest ghi tỉ lệ gộp, tỉ lệ `deferred`, cạnh bị cắt, cặp đã vá, cụm lớn nhất
    và Jaccard với lần chạy trước, để thấy ngay khi có gì bất thường.
43. Là **người vận hành**, tôi muốn so hai phiên bản `canonical` bằng Jaccard, để đo độ tái lập của merge như đã đo
    cho A3.
44. Là **người gán bộ vàng**, tôi muốn một file HTML chạy trên máy, hiện từng mục như khối nhóm có tên, alias và câu
    bằng chứng, có năm nút nhãn và tự lưu tiến độ, để gán 416 mục mà nội dung tài liệu không
    rời máy.
45. Là **người gán bộ vàng**, tôi muốn bảng gán không hiện gợi ý và được dựng trước lần chạy mô hình đầu tiên, để
    nhãn không bị kết quả máy dắt.
46. Là **người vận hành**, tôi muốn lệnh chấm trên bộ vàng ra P/R/F1 theo cặp và tỉ lệ cặp trùng mà đồ thị đề cử
    bắt được, để chọn tham số và mô hình bằng số.
47. Là **người vận hành**, tôi muốn đo độ đồng thuận giữa hai người gán, để biết bộ vàng đáng tin tới đâu.
48. Là **người vận hành**, tôi muốn A3 cảnh báo khi hai thực thể khác tên cùng section có draft trùng từng chữ, để
    gốc của các cặp cosine 1,000 hiện ra ở đúng tầng sinh ra nó.
49. Là **người vận hành**, tôi muốn A3 cảnh báo khi câu bằng chứng không chứa tên, alias hay ký hiệu của thực thể, để
    bằng chứng yếu hiện ra mà không mất ứng viên nào.
50. Là **người vận hành**, tôi muốn hai cảnh báo trên chạy được trên artifact A3 đã có, để không phải trích lại bốn
    tài liệu.
51. Là **người vận hành**, tôi muốn bước phán merge và A5 dùng mô hình cấu hình riêng, để trả thêm đúng ở bước dễ gộp
    nhầm mà không đổi bước khác.
52. Là **người vận hành**, tôi muốn đầu ra sai định dạng được thử lại một lần rồi mới đánh cả cụm `deferred`, để một
    lỗi định dạng không dẫn tới gộp bừa.
53. Là **người dựng lộ trình**, tôi muốn media không đi qua bước phán merge lẫn A5, để khử trùng media vẫn tất định
    theo `media_id` và mô tả ảnh không bị viết lại từ văn bản xung quanh.

## Implementation Decisions

### D1 — Vị trí trong pipeline và luồng *(Q1, Q22′, Q6)*

- **Một thiết kế merge duy nhất: Tầng 2a**, dùng chung cho cả pipeline cố định lẫn biến thể. Khác biệt giữa hai
  biến thể nằm ở suy luận cạnh (2b / A8), không ở merge.
- Luồng: **lớp tên → đồ thị đề cử → gom cụm → phán theo cụm → vá cặp bị chia → lắp node → A5**.
- Chạy theo tài liệu, trên **pool ứng viên toàn tài liệu** — đúng hàng rào D8 của spec A3: chưa trích hết thì
  chưa biết khái niệm chương 3 có bạn ở chương 8.
- **A5 là lời gọi riêng**, chạy sau khi bảng node đã chốt. Bước phán merge không chọn tên, không viết mô tả.
- A4 và A5 cùng ghi vào **một** artifact tầng `canonical` (D10 spec A3). Không thêm tầng thứ tư.
- Media bỏ qua cả hai bước: khử trùng theo `media_id`, mô tả đã chốt ở A3.
- 2b (hai nhánh theo chương / theo cụm chủ đề) là **đợt sau**.

### D2 — Quyền tự gộp của code, và ba loại tên thay thế *(Q2, Q3, D1, D2 · ADR 0006)*

- **Khoá tên** = chuẩn hoá B0 + casefold + gộp khoảng trắng + **quy vị trí dấu thanh về một kiểu**
  (`hoá` = `hóa`, `uỷ` = `ủy`). Không gộp `y`/`i` hay `thiết`/`thuyết` — hai cặp này để kênh n-gram đề cử.
- Ứng viên cùng khoá tên ⇒ code gộp thành **nhóm tên**. Đây là **quyền gộp duy nhất của code**; nhóm tên là đơn
  vị của mọi bước sau.
- Alias, n-gram, embedding **chỉ đề cử**. Không có ngưỡng cosine nào được gộp thẳng.
- Tên thay thế của một ứng viên được phân ba loại, **chỉ áp cho alias**:

  | Loại | Nhận biết | Dùng để |
  |---|---|---|
  | Tên gọi | có từ ngữ | đề cử; alias của node |
  | Viết tắt | toàn chữ hoa/số, có chữ cái (`ML`, `JWT`, `E2E`) | đề cử; alias của node; tên chuẩn chỉ khi không còn tên gọi |
  | **Ký hiệu** | không chứa từ ngữ nào: chữ cái đơn, biểu thức có ký tự Hy Lạp/toán (`μ`, `x σ n`, `t α`, `P(A\|B)`) | **không** đề cử, **không** gộp, **không** làm tên chuẩn, **không** casefold (`F` ≠ `f`); lưu riêng để hiển thị |

  Đo trên corpus: 128 alias = 89 tên gọi · 12 viết tắt · 27 ký hiệu. Hai alias chữ cái đơn `H`, `A` là ký hiệu
  theo đúng luật trên. Một lần nối nhầm đã xảy ra vì casefold:
  `F` (tỉ lệ mẫu tổng quát) và `f` (tỉ lệ mẫu) thành cùng khoá.

### D3 — Đồ thị đề cử và gom cụm *(Q10, Q25)*

- **Node** = nhóm tên. **Cạnh** = cặp nghi trùng từ ba kênh:

  | Kênh | Cạnh khi | Trọng số | Số cạnh (4 tài liệu) |
  |---|---|---|---:|
  | Alias | alias (không tính ký hiệu) của nhóm này trùng khoá tên hoặc alias của nhóm kia | 1 | 9 |
  | Tên gần giống | Jaccard 3-gram ký tự **không đệm biên** trên tên đã bỏ dấu và dấu câu ≥ 0,5 | max(cosine tên, 0,5) | 95 |
  | Tên gần nghĩa | mutual-3NN trên embedding **tên** | cosine tên | 222 |
  | **Hợp** | | | **256** |

- **Embedding tên do A4 tự tính** qua cổng embedding hiện có — `gemini-embedding-001`, 768 chiều,
  `SEMANTIC_SIMILARITY`. Vector nhóm = trung bình vector tên các thành viên, đã chuẩn hoá. Model, số chiều và công
  thức văn bản embed vào config hash của A4 (ADR 0004).
- **A3 không đổi và bỏ kênh mô tả ở A4.** Trong 100 cặp vàng lấy ngoài đồ thị không có cặp nào mang nhãn *cùng*,
  nên chưa có tín hiệu cần kênh này; xét lại khi có bộ vàng người độc lập. Vector `description_draft` của A3 vẫn
  dành cho quan hệ/chủ đề ở A6/A7, không dùng để đề cử đồng nhất.
- **Gom cụm**: Louvain có trọng số, **seed cố định**, độ phân giải 2. Cụm vượt **9 nhóm** thì chia lại ở độ phân
  giải cao hơn tới khi ≤ 9. Nhóm không có cạnh nào ⇒ thành node luôn, không qua mô hình (vẫn qua A5).
  Không dùng connected components: nó là single-linkage, và trên chính dữ liệu này nó xích cả tài liệu thành
  một cụm.
- Số đo đã chốt trên bộ vàng AI: **63 cụm cần gọi mô hình, cụm lớn nhất 7 nhóm, 38 cạnh bị cắt** với seed 42.
  Số cạnh bị cắt dao động 36–42 khi thử các seed 0, 1, 2, 3, 7, 42, 99, nên chỉ seed 42 là mốc tái lập.
- `networkx` được khai báo thành **phụ thuộc trực tiếp**, ghim phiên bản. Hàm Leiden của `networkx` chỉ là API
  chuyển tiếp, không có cài đặt; Leiden thật để A7 quyết.

### D4 — Phán theo cụm *(Q11, Q12, Q14, Q17, Q27, D4)*

- Mỗi cụm **một lời gọi**, không tool, không vòng lặp agent.
- **Đầu vào**, cho từng nhóm trong cụm: tên, alias (tên gọi + viết tắt), ký hiệu, `node_type` của các thành
  viên, `section_path`, tối đa 3 câu bằng chứng nguyên văn theo thứ tự tài liệu. Ứng viên có câu bằng chứng
  **không chứa** tên, alias hay ký hiệu của chính nó ⇒ kèm **toàn văn chunk nguồn**. **Không** đưa
  `description_draft`. Các nhóm xếp theo thứ tự tài liệu.
- **Rubric năm nhãn** (dùng chung cho bước vá ở D5):

  | Nhãn | Nghĩa | Kết quả |
  |---|---|---|
  | cùng | cùng một thực thể dù khác tên, cách dịch, dạng ký hiệu | chung node |
  | cha–con | rộng vs hẹp (`Regularization` / `L2 Regularization`) | hai node + quan hệ `subtype_of` con → cha, kèm lý do và `chunk_id` bằng chứng |
  | anh em / liên quan | đồng cấp hoặc chỉ liên quan (`Mutex` / `Pessimistic Locking`) | hai node; câu trích nêu quan hệ thì kèm quan hệ kiểu mở (`component_of`, `uses`, `statistic_of`…) |
  | khác | | hai node |
  | không chắc | | **không gộp**, `deferred` kèm lý do |

  Phân vân thì không gộp. **Không đề xuất `requires`.**
- **Đầu ra** *(ADR 0007)*: `nodes` (mỗi nhóm thuộc đúng một node hoặc nằm trong `deferred`), `relations` và
  `deferred`. Mô hình không chọn tên, không gộp alias, không viết mô tả.
  - Mỗi quan hệ có dạng `{source, target, edge_type, chunk_ids, reason}` và nối hai nhóm nằm ở **hai node khác nhau**.
  - `edge_type` là kiểu mở, đọc từ `source` sang `target`. `subtype_of` nghĩa là "là một loại / dạng / biến thể /
    trường hợp riêng của"; các quan hệ khác dùng tên snake_case ngắn.
  - Không bao giờ `requires` hay tên đồng nghĩa với nó.
- **Code kiểm đầu ra ba lớp**:
  1. **Phân hoạch:** mỗi nhóm đúng một lần trong `nodes` hoặc `deferred`, không có id lạ, mọi quyết định có lý do.
  2. **Nhất quán**, không cần nhãn:
     - R1: một quan hệ không đồng nhất nối hai nhóm mà mô hình đặt chung node ⇒ mâu thuẫn;
     - R2: một quan hệ đồng nhất (`same_as`, `equivalent_to`, `identical_to`, `synonym_of`, `alias_of`) nối hai node
       tách riêng ⇒ mâu thuẫn.

     Lớp 1 hoặc lớp 2 sai ⇒ thử lại **một lần**, kèm lỗi cụ thể; vẫn sai ⇒ cả cụm `deferred`, không gộp gì.
  3. **Từng quan hệ:**
     - hai đầu phải là hai node khác nhau và không `deferred`;
     - chỉ trích `chunk_id` của hai đầu, và có lý do;
     - kiểu không rỗng, không `requires` hay đồng nghĩa, không phải kiểu dành cho media.

     Quan hệ sai bị loại riêng, ghi `relation_rejected`; phân hoạch vẫn được áp.
- **Cache:** đầu ra trong nhật ký cũ không còn qua được luật kiểm hiện hành ⇒ coi như cache trượt và gọi lại mô hình
  (`<stage>_cache_invalid`), không dừng lượt chạy.
- **Kiểu do code quyết, không do mô hình**: chuẩn hoá tối thiểu chuỗi `node_type` (casefold, khoảng trắng, ánh xạ
  theo sổ đăng ký kiểu đã duyệt) rồi bỏ phiếu đa số. Hoà ⇒ kiểu **cụ thể hơn** `concept`, rồi kiểu được dùng nhiều
  hơn trong cả tài liệu, rồi thứ tự chữ cái; luật đã dùng ghi vào nhật ký. Đo: 12/60 nhóm tên nhiều ứng viên hoà
  phiếu, phần lớn `algorithm`/`concept` và `metric`/`concept`. Gộp kiểu theo nghĩa vẫn là việc tầng 3.
- `learnable`: bỏ phiếu lại chỉ trên ứng viên mang kiểu canonical, hoà chọn `true`; cùng tên khác kiểu nằm hai phía
  `learnable` ⇒ hàng review (§655–659, không đổi).
- **Mô hình**: cấu hình riêng cho bước phán merge (dùng chung cho bước vá). Khung prompt tiếng Anh, dữ liệu giữ
  nguyên ngôn ngữ tài liệu. Model, tham số sinh,
  khung prompt và schema vào `prompt_hash`, cùng khuôn A3.
  **Chốt 2026-09-12:** dùng `gemini-3.1-flash-lite` cho cả merge và A5. A/B cùng pipeline với
  `gemini-3.1-pro-preview` cho bước phán cho F1 gộp 0,795 so với 0,703; flash-lite cũng nhanh và rẻ hơn.

  **A/B lại theo F72 (2026-09-12)**, theo luật chọn viết trước khi chạy. Kết quả: **giữ prompt hiện hành và
  flash-lite**. Chủ dự án cũng chốt dùng flash-lite cho mọi khâu LLM trong giai đoạn dev.
  - **Prompt v2.1** coi biến thể từ vựng là bằng chứng đồng nhất: cắt cụt, thêm/bỏ từ đầu chung, viết tắt, dịch,
    hậu tố ký hiệu. Nó chỉ cho `subtype_of` khi bằng chứng nói "là một loại". Recall gộp lên 0,809, nhưng precision
    gộp tụt xuống 0,927 với flash-lite và 0,844 với Pro, vì mô hình gộp cả tên chung với tên riêng
    (`Giá trị tới hạn t α` / `Giá trị tới hạn`). Cả hai trượt cổng precision ≥ 0,95.
  - **Nhánh hậu kiểm v1.1** (prompt hiện hành cộng riêng luật subtype) cũng trượt: F1 gộp 0,694, precision subtype
    0,756. Nó còn làm mô hình ghi tên nhóm thay cho `group_id` (20 lượt thử hỏng).
  - **Giới hạn còn lại**: mặc định còn bỏ sót 16 cặp *cùng*. v2.1 kéo con số này xuống 9, cho thấy một phần do câu
    "chỉ bằng chứng nguyên văn" khiến mô hình tách biến thể từ vựng. Biến thể prompt sau phải đo trên **nhãn mới**,
    không đo trên bộ vàng đã dùng để chọn prompt.
  - Chi tiết ở báo cáo chạy thật, mục A/B.

  **Quan hệ kiểu mở (2026-09-14, ADR 0007).** Prompt phân hoạch là **v3**. So với v1, nó thay kênh `subtype_of` riêng
  bằng danh sách quan hệ kiểu mở, và thêm câu bắt dùng `group_id`. Có hai đợt, đều chạy flash-lite trên bốn tài liệu:
  - **Đợt 1**, chỉ prompt v3: precision gộp 0,809. Mô hình dùng node như nhóm chủ đề, và ghi quan hệ giữa chính các
    nhóm nó vừa gộp. Không nhận.
  - **Đợt 2**, v3 cộng luật nhất quán: 35 / 2 / 12, precision gộp 0,946, F1 0,833, precision `subtype_of` 0,658;
    quan hệ khác `subtype_of` có 70% đúng trên mẫu 30. Theo luật chấm viết trước thì trượt ngưỡng 0,95 đúng một ca;
    **chủ dự án chấp nhận**, để đổi lấy recall và quan hệ kiểu mở.

  Bản này chỉ thành mặc định sau một mẫu xác nhận và lượt chạy kho chính, với precision gộp ≥ 0,93.

  Giới hạn đã biết:
  - hai kiểu gộp sai hệ thống không mang tín hiệu mâu thuẫn: tên chung với tên riêng, và các bài toán anh em;
  - lượt thử lại hay tách cả node và làm mất cặp đúng (F83).

  Chi tiết ở `task/a4-quan-he-mo-2a/` và báo cáo chạy thật.

### D5 — Vá cặp bị chia hai cụm, và mâu thuẫn bắc cầu *(Q26, Q13)*

- Sau lượt phán cụm, với mỗi cạnh bị cắt, hợp **mọi nhóm tên thành viên** của hai node đã được phán ở hai đầu thành
  một cụm nhỏ rồi gọi lại đúng prompt, schema và validator phân hoạch của D4. Các cạnh nối cùng một cặp node chỉ tạo
  một lời gọi. Không dùng lô cặp hai nhóm: thiết kế cũ sinh cả 3/3 ca gộp sai của lần chạy đầu.
- Chỉ khi đầu ra hợp lệ đặt toàn bộ hai node vào cùng một node mới thêm quyết định *cùng*. Phân hoạch tách hoặc
  `deferred` thì không gộp; `deferred` ở đây được ghi cho **cặp node**, không đưa các nhóm đầu mút vào `deferred`
  toàn cục và không tháo những lần gộp đúng của lượt cụm.
- **Gộp bắc cầu có kiểm**: nếu các quyết định *cùng* còn tạo thành phần chứa một cặp đã bị tách rõ ở lượt cụm thì
  không gộp thành phần đó: đánh các nhóm liên quan `deferred`, phát cảnh báo và đếm số lần.
- Quan hệ trả về ở lượt vá được giữ như ở lượt cụm, cùng ba lớp kiểm của D4.
- Quan hệ chỉ được map về node sau khi đã chốt node. Hai đầu rơi vào cùng một node (vì lượt vá gộp chúng) thì quan hệ
  bị bỏ, đếm vào `relation_self_removed`.

### D6 — Lắp node canonical *(Q4, Q7, Q18, Q23, D3 · ADR 0005)*

- **Id**: băm tất định của doc và `candidate_id` của **ứng viên neo** — ứng viên có `first_order_index` của chính
  nó nhỏ nhất, hoà thì `candidate_id` nhỏ nhất. Giữa hai phiên bản, id cũ mất neo được ghi vào **bảng chuyển
  hướng** trỏ sang node chứa phần lớn thành viên cũ. Một id đã dùng không bao giờ cấp lại cho thực thể khác.
- **Tên chuẩn** — thay luật D5 cũ của spec A3:
  1. Ứng cử viên là **tên của các ứng viên** thuộc node; alias không tranh (alias chưa được lọc).
  2. **Xếp bậc**: tên gọi thuần chữ › tên gọi có token ký hiệu (`Phương sai tổng thể σ 2`) › viết tắt. Ký hiệu không
     bao giờ làm tên. Chỉ bậc cao nhất có mặt trong node được tranh.
  3. Chọn dạng có **tần suất xuất hiện cao nhất trong văn bản tài liệu**, khớp theo ranh giới từ trên văn bản đã
     chuẩn hoá, và **đếm không chồng lấn**: khoá tên dài được đếm rồi che trước, nên một lần xuất hiện của
     `Naïve Bayes Classification` không còn được tính cho `Naïve Bayes`.
  4. **Hoà**: nếu một tên nằm gọn trong tên kia thì chọn tên chứa nó (`Bernoulli Naive Bayes`, không phải
     `Bernoulli Naive` bị cắt cụt); còn lại chọn dạng xuất hiện sớm nhất.

  Áp nguyên văn luật cũ thì `x` (325 lần) thành tên của *Trung bình mẫu*, `α` thành tên của *Mức ý nghĩa*.
  Luật mới cho `Naïve Bayes Classification` (11) thay `Naïve Bayes` (chỉ 6 lần đứng riêng), và `Race Condition` (5)
  thay `Tranh chấp dữ liệu` (4) trong báo cáo tiếng Việt — đúng cách tác giả dùng chữ; dạng còn lại luôn là alias.
  Cái giá đã chấp nhận: `Tập huấn luyện` giữ làm tên dù alias `tập học` xuất hiện nhiều hơn (12 so với 9).

  **Sửa theo F73 (2026-09-12):** bản trước đếm chồng lấn, nên ghi nhầm `Naïve Bayes` 17 lần — gồm cả 11 lần nằm trong
  tên dài — và chọn tên cụt `Bernoulli Naive`. Biến thể "hoà thì luôn chọn tên dài hơn" đã bị loại: nó biến
  `Kiến trúc phân lớp` thành `Layered Architecture` chỉ vì chữ tiếng Anh dài hơn. Trên bốn tài liệu, luật mới đổi tên
  đúng 8 node và không đổi id hay thành viên nào.
- **Alias**: hợp mọi alias của thành viên (tên gọi + viết tắt) **và** tên của các ứng viên không được chọn làm tên
  chuẩn; mỗi alias giữ câu bằng chứng và ứng viên gốc. Lọc alias để dành cho vòng mention map.
- **Ký hiệu**: hợp riêng, phân biệt hoa thường.
- **Bằng chứng**: hợp `chunk_id` bằng chứng của mọi thành viên. `first_order_index` / `first_mention_index` theo D8.
- **Nhật ký gộp**: mọi quyết định — tự gộp theo tên, phán cụm, vá cặp, hoà kiểu, mâu thuẫn bắc cầu, thử lại / sai
  định dạng — với thành viên, nhãn, lý do, `chunk_id` bằng chứng, mô hình, `prompt_hash`, băm đầu vào. Kèm bảng
  thành viên node → ứng viên và danh sách `deferred`.
- **Thao tác tách** là việc của A13; đợt này chỉ bảo đảm dữ liệu đủ để tách mà không trích lại.

### D7 — Ánh xạ cạnh *(D5)*

- Cạnh đề xuất của A3 ánh xạ hai đầu mút ứng viên → node canonical. Hai đầu rơi vào cùng node ⇒ bỏ, có đếm. Nhiều
  cạnh cùng kiểu giữa cùng cặp node ⇒ gộp một, hợp bằng chứng, `confirmed` lấy OR.
- Cạnh media `illustrates` / `tabulates` theo cùng luật; tính lại media mồ côi (I-G2).
- **Quan hệ kiểu mở từ D4/D5 (kể cả `subtype_of`)** thành cạnh node–node với `proposal: true`, và được ghi vào sổ đăng
  ký kiểu (I-G3).
  - Mọi cạnh có `origins` ⊆ {`2a`, `a3`}.
  - Quan hệ 2a trùng bộ ba (nguồn, đích, kiểu) với cạnh A3 thì thành một cạnh, `origins: ["2a", "a3"]`: giữ nguyên các
    trường của A3, hợp `chunk_ids`, và thêm `reason` của 2a.
  - Quan hệ trùng nhau giữa các cụm hoặc lượt vá thì gộp làm một, giữ `reason` đầu tiên theo thứ tự xử lý.
  - Chỉ số so với A3: `relation_same_as_a3`, `relation_same_type_reversed_a3`, `relation_other_type_than_a3`,
    `relation_new_pair`.
- **Cặp đã có cạnh A3 mang nghĩa khác "là một loại"** — `component_of`, `uses`, `solves`, `prevents`, `causes`,
  `computed_by`, `contrasts_with`, bất kể chiều. *(F75)*
  - Luật: giữ cả hai cạnh; ghi `subtype_conflicts_a3` vào nhật ký, kèm kiểu cạnh A3, và vào chỉ số. Luật này chỉ xét
    quan hệ 2a có kiểu `subtype_of`.
  - Vì sao không xoá: đo trên bộ vàng, luật xoá bỏ 17 cạnh `subtype_of` đúng mà chỉ bắt được 2 cạnh sai. A3 hay gắn
    biến thể thành bộ phận (`Gaussian Naive Bayes` `component_of` `Naïve Bayes Classification`).
- **Chất lượng quan hệ 2a mà 2b nhận**, đo ở đợt 2:
  - `subtype_of` trên cặp có nhãn: 25 cạnh đúng, 13 cạnh sai, tức precision 0,658 (prompt v1 cũ là 0,635);
  - bắt được 27/47 cặp cha–con. Ba cặp bộ phận mà bộ vàng gán cha–con giờ được gắn đúng kiểu `component_of`;
  - quan hệ khác `subtype_of`: 70% đúng trên mẫu 30, do Claude gán.

  Vì vậy 2b coi mọi quan hệ 2a, cũng như cạnh A3, là **đề xuất cần kiểm lại**, không phải sự thật.
- `requires` do A3 đề xuất vẫn chỉ là đề xuất; 2b xác minh lại (§726). Không đổi.

### D8 — A5: mô tả chuẩn *(Q5, Q15, Q16, Q20, D6)*

- **Phạm vi**: mọi node trừ media, mọi kiểu, kể cả `learnable = false`.
- **Node nhiều ứng viên** ⇒ tổng hợp. **Node một ứng viên** ⇒ kiểm draft theo lô: draft được câu bằng chứng hỗ trợ
  **và** đúng ngôn ngữ ⇒ giữ nguyên; ngược lại ⇒ viết lại, chỉ từ bằng chứng. Cả corpus có 219/279 nhóm tên là
  đơn lẻ.
- **Đầu vào**: toàn văn chunk bằng chứng của node theo **thứ tự tài liệu**, trần khoảng 4k token — vượt thì giữ
  câu bằng chứng cộng chunk sớm nhất; kèm tên chuẩn, alias, ký hiệu, kiểu. Ở quy mô hiện tại, đọc toàn bộ chunk
  nguồn của mọi node chỉ khoảng 87 nghìn token.
- **Đầu ra**: **1–4 câu theo lượng bằng chứng**, mỗi câu kết thúc bằng một hoặc nhiều `chunk_id`; được phép ghi
  *"tài liệu không nói thêm"*. Kèm `defining_chunk_ids` — chunk **định nghĩa hoặc giảng** node — là tập con của
  các trích dẫn. Nguồn mâu thuẫn ⇒ **không hoà giải**, gắn cờ `nghi_gop_nham` kèm lý do.
- **Code kiểm**: mọi `chunk_id` trích dẫn thuộc node; `defining_chunk_ids` ⊆ trích dẫn. Sai ⇒ thử lại một lần; vẫn
  sai ⇒ giữ draft và gắn cờ.
- **`first_order_index`** = `order_index` nhỏ nhất trên `defining_chunk_ids`; rỗng ⇒ nhỏ nhất trên mọi ứng viên.
  **`first_mention_index`** = nhỏ nhất trên mọi ứng viên. Ví dụ thật: node `Race Condition` có ứng viên sớm nhất ở
  một danh sách tóm tắt chương I (#10), còn chỗ được tìm hiểu thật là #23.
- **Ngôn ngữ mô tả** = ngôn ngữ chủ đạo của phần văn xuôi: bỏ chunk mà mọi `block_types` đều thuộc
  {`table`, `code`, `formula`, `figure`}, rồi lấy đa số theo token; nếu không còn chunk nào thì dùng toàn bộ chunk.
  Một chunk là tiếng Việt khi ≥ 20% số từ mang dấu tiếng Việt. Luật `token-majority-prose-vi20-v2` chỉ áp cho mô
  tả; tên chuẩn theo D6. Cả bốn tài liệu, gồm `naive-bayes`, đều cho kết quả `vi`.
- **Mô hình**: cấu hình riêng, mặc định cùng model với A3. Không có lượt mô hình chấm mô tả; A13 lấy mẫu.

### D9 — Artifact, cache và chạy lại *(Q6, Q18, D9)*

- Một artifact `canonical/{doc}/v{n}` gồm: node, bảng thành viên, nhật ký quyết định, `deferred`, bảng chuyển
  hướng, cạnh đã ánh xạ, mô tả, chỉ số.
- **Config hash** gồm: phiên bản và config hash của artifact `candidates` nguồn; embedding tên (model, số chiều,
  công thức văn bản); tham số đồ thị (k, ngưỡng n-gram, độ phân giải, seed, trần cụm); model + `prompt_hash` của
  bước phán merge và của A5; luật ngôn ngữ; phiên bản thuật toán.
- **Cache theo băm đầu vào**: mỗi quyết định lưu băm của (model, `prompt_hash`, dữ liệu gửi đi). Lần chạy sau đọc
  nhật ký phiên bản trước; cụm, cặp hay node có băm trùng thì dùng lại, không gọi mô hình. Đổi luật ngôn ngữ chỉ
  gọi lại A5; sửa một section chỉ gọi lại những cụm chứa ứng viên của section đó.
- HTTP, timeout và lỗi đường truyền là `ModelTransportError`: dừng cả lượt chạy và không ghi artifact để lần sau có
  thể chạy lại. Phản hồi có nội dung nhưng sai schema/JSON được giữ nguyên trong `attempts` để chẩn đoán; phản hồi
  rỗng vẫn đi qua nhánh đầu ra sai.
- Manifest ghi chỉ số (D10) và `jaccard_previous`, cùng khuôn A3.

### D10 — Chỉ số, bộ vàng và lệnh *(Q21′, Q28, D8)*

- **Chỉ số trong manifest**: số ứng viên / nhóm tên / node; tỉ lệ gộp; tỉ lệ `deferred`; số cạnh đề cử theo kênh;
  số cụm và cụm lớn nhất; số cạnh bị cắt và số cặp đã vá; số mâu thuẫn bắc cầu; số lần hoà kiểu;
  `single_chunk_ratio` (chuyển từ A3 sang theo D11 spec A3); số node A5 tổng hợp / giữ draft / viết lại; số cờ
  `nghi_gop_nham`; số nhóm được gộp thêm, cạnh subtype bị loại, cặp hoãn, hai cảnh báo chất lượng A3; Jaccard node
  và Jaccard thành viên với lần chạy trước.
- **Bộ vàng**: bảng gán sinh từ đồ thị đề cử **trước lần chạy mô hình đầu tiên**, gồm mọi cạnh (256), 100 cặp ngẫu
  nhiên **ngoài** đồ thị (seed cố định, để đo cặp trùng nằm ngoài tầm đề cử) và mọi nhóm tên nhiều ứng viên (60,
  để soát đồng âm khác nghĩa). Năm nhãn như D4. Người dùng gán **mù**: bảng không hiện gợi ý, không hiện kết quả
  A4. Đóng băng thành fixture 416 mục mang cờ `blind_before_first_a4_run`, cùng khuôn bộ vàng A3. Bộ hiện tại do
  Claude gán theo yêu cầu chủ dự án, dùng làm mốc kỹ thuật chứ chưa phải nhãn người độc lập.
- **Công cụ gán**: một file HTML tự chứa, chạy trên máy, tự lưu tiến độ trong trình duyệt, xuất JSON đúng khuôn
  fixture. Nội dung tài liệu không gửi đi đâu.
- **Lệnh CLI**, cùng khuôn nhóm lệnh A3:
  - `a4` — chạy Tầng 2a rồi A5 cho một tài liệu, in chỉ số;
  - `a4-compare` — Jaccard node và thành viên giữa hai phiên bản `canonical`;
  - `a4-evaluate` — chấm trên bộ vàng: P/R/F1 theo cặp, tỉ lệ cặp trùng mà đồ thị đề cử bắt được, độ đồng thuận
    giữa hai người gán;
  - `a4-gold-sheet` — sinh file HTML gán nhãn cho một hoặc nhiều tài liệu.

### D11 — Hai cảnh báo trả về A3 *(Q8c, Q24, D7)*

| Tình huống | Hành động | Đo hiện tại |
|---|---|---|
| Hai thực thể khác tên cùng section có `description_draft` trùng từng chữ | cảnh báo, không loại | 6 câu dùng chung cho 19 tên |
| Câu bằng chứng không chứa tên, alias hay ký hiệu của thực thể (so trên văn bản bỏ dấu, không phân biệt hoa thường) | cảnh báo, không loại | 31/377 ứng viên |

Cả hai là **hàm thuần trên artifact A3**. A3 ghi chúng khi chạy mới; `a3-report` và A4 tính chúng trên artifact đã
có. **Không đổi `algorithm_id` của A3**, nên không phải trích lại bốn tài liệu.

### D12 — Cổng, cấu hình, phụ thuộc

- **Không thêm cổng mô hình mới.** Bước phán merge, bước vá và A5 dùng cổng hội thoại LLM hiện có, mỗi lời gọi một
  phiên một lượt. Embedding tên dùng cổng embedding hiện có.
- **Cấu hình mới**: model cho bước phán merge, model cho A5, tham số đồ thị. Tất cả vào config hash; key vẫn chỉ đọc
  từ biến môi trường như D16 spec A3.
- **Phụ thuộc mới**: `networkx`, trực tiếp, ghim phiên bản.
- **Logic thuần trong domain**: khoá tên, phân loại tên thay thế, n-gram, mutual-kNN, gom cụm có trần, luật tên
  chuẩn, bỏ phiếu kiểu, id neo và bảng chuyển hướng, kiểm đầu ra mô hình, ánh xạ cạnh, phát hiện mâu thuẫn bắc
  cầu, kiểm trích dẫn, luật ngôn ngữ, hai cảnh báo A3. Không cái nào cần mạng.

### D13 — Sửa tài liệu đi kèm

Đã sửa cùng spec này, để tài liệu không nói hai ý:

- `spec-addendum.md`: A4 và A5 trỏ về thiết kế này; sơ đồ và mục Tầng 2a viết lại; bảng ánh xạ nhãn tách A6 khỏi đồ
  thị đề cử (đồ thị đề cử đo **đồng nhất**, A6 đo **liên quan**); câu "cụm 2a co lại thành một node" sửa lại; hợp
  đồng prompt 2a và ví dụ JSON viết lại; luật 0,9 của 2b đọc câu bằng chứng nguyên văn; dòng MVP; bảng §0.1 thêm
  bước chuẩn hoá kiểu tối thiểu ở 2a.
- Spec A3: D5 (luật tên), D8 (vòng đời embed), D12 (hai cảnh báo mới).
- Trong phiên grill: `CONTEXT.md`, ADR 0005, ADR 0006, ghi chú cập nhật ADR 0004.

## Testing Decisions

**Test tốt kiểm hành vi ngoài seam, không kiểm cách làm.** Không khẳng định gì về nội dung prompt hay số lời gọi —
chỉ khẳng định: cho bảng ứng viên này vào, những ứng viên nào ra chung một node, tên gì, cạnh nào, cờ nào.

### Seam ① — Use case A4/A5 trên fixture (seam chính)

Đầu vào: fixture artifact `candidates` thật của `baocao-canhan` — nhỏ, đủ ca alias xuyên ngữ, cha–con, anh em, số
nhiều, tiền tố thể loại; cộng **phát lại embedding tên** qua cơ chế ghi–phát lại embedding của A3 (tra theo băm văn
bản); cộng một **mô hình giả "trọng tài"** viết tay, trả quyết định theo bảng nhãn cố định (nhóm → node), không gọi
mạng.

Khẳng định trên artifact `canonical` ra:

- nhóm nào chung node, tên chuẩn, alias, ký hiệu, kiểu (kể cả luật hoà);
- id giữ nguyên khi tên chuẩn đổi; bảng chuyển hướng khi neo đổi;
- cạnh ánh xạ: bỏ cạnh tự nối, gộp cạnh trùng, media nối lại;
- `deferred` khi trọng tài trả *không chắc*, khi trả sai định dạng hai lần, và khi gộp bắc cầu mâu thuẫn;
- cặp bị chia hai cụm được vá;
- mô tả có trích dẫn hợp lệ; trích dẫn ngoài node bị từ chối; `first_order_index` lấy từ `defining_chunk_ids`;
- chạy lại cùng đầu vào không gọi trọng tài lần nào; đổi luật ngôn ngữ chỉ gọi lại A5.

**Prior art**: bộ test use case A3 với phiên và bộ trích viết tay (`_Session`, `_Extractor`).

### Seam ② — Luật thuần domain

Các ca biên khó dựng qua fixture: khoá tên (`hoá`/`hóa` gộp, `tỷ`/`tỉ` không gộp); phân loại tên thay thế
(`F` ≠ `f`, `ML` là viết tắt, `Học` là tên gọi); n-gram; mutual-kNN; gom cụm tất định và chia lại khi vượt trần;
luật tên chuẩn (tần suất, hoà, viết tắt thua tên gọi, ký hiệu không bao giờ thắng); bỏ phiếu kiểu và luật hoà; id neo;
kiểm đầu ra mô hình; phát hiện mâu thuẫn bắc cầu; kiểm trích dẫn; luật ngôn ngữ; hai cảnh báo A3. Dựng đầu vào bằng
tay, chạy mili-giây.

**Prior art**: test domain của A3 (`test_a3_entities`) và `chunk_document`.

### Phát lại mô hình thật — dùng nguyên cơ chế ghi–phát lại hội thoại của A3

Bốn fixture **một lời gọi**, ghi từ mô hình thật trên `baocao-canhan`: một cụm, một cụm vá, một lời gọi A5 tổng
hợp, một lô A5 kiểm node đơn lẻ. Mỗi fixture là một phiên một lượt, nên cơ chế phát lại theo thứ tự của A3 dùng được
nguyên vẹn — không sửa hạ tầng. Test chỉ khẳng định **hình dạng** (schema hợp lệ, trích dẫn hợp lệ, không nhóm nào
mất), không khẳng định nhãn cụ thể. Không phát lại cả một tài liệu bằng mô hình thật: hành vi end-to-end đã có seam ①
với trọng tài giả.

`prompt_hash` dùng để chọn fixture phải **tính từ mã sản phẩm**, không đọc từ chính fixture — bài học F57: một guard
so fixture với chính nó thì không bao giờ hỏng.

### Lệnh chấm

Test `a4-evaluate` bằng một bộ vàng tay 8–10 cặp có P/R/F1 và độ đồng thuận tính sẵn bằng tay. Bộ vàng thật không
chạy trong test đơn vị — chạy tay bằng lệnh.

### Luật cứng

- **Không test nào gọi mạng.** Lời gọi thật chỉ ở kịch bản ghi fixture và lệnh chạy thật.
- **Mọi guard phải có test đi đúng nhánh nó bảo vệ** (AGENTS.md §5): sai định dạng hai lần ⇒ cả cụm không gộp; mâu
  thuẫn bắc cầu ⇒ không gộp; trích dẫn ngoài node ⇒ bị từ chối; ký hiệu không bao giờ nối hai nhóm.
- Đổi số trong bộ số vàng phải kèm giải thích trong cùng commit — luật đã có.

## Out of Scope

| Hoãn | Vì / chờ |
|---|---|
| 2b với hai nhánh (theo chương / theo cụm chủ đề) | Đợt sau; cần bảng node canonical của đợt này làm đầu vào |
| Cạnh media xuyên chunk (§121) | Chưa có cơ chế phát hiện; spec chỉ nói "hoãn tới sau merge" |
| Mention map và lọc alias | Người dùng là A6 và 2b; luật ký hiệu đã ghi sẵn cho nó |
| Leiden thật | A7 quyết; gom cụm 2a chưa chạm trần |
| Thao tác tách node | A13; đợt này chỉ bảo đảm dữ liệu đủ |
| Trường ký hiệu riêng trong schema A3 | A4 tự phân loại được; tách trường khi A3 trích lại |
| Kênh mô tả trong đồ thị đề cử | Quyết sau khi bộ vàng cho biết nó có bắt thêm cặp nào không |
| Lượt mô hình chấm mô tả A5 | Chưa có bộ kiểm tiếng Việt đã kiểm chứng; A13 lấy mẫu |
| A6 / A7 | Đồ thị liên quan và cụm chủ đề dùng mô tả A5, làm sau |
| Gộp xuyên tài liệu | Mỗi tài liệu là một lộ trình riêng |
| Tự nâng kiểu cạnh thành `requires` | Chỉ người ở A13 được nâng (§0.1) |

## Further Notes

- **Thứ tự làm gợi ý**: (1) luật domain, đồ thị đề cử, gom cụm — chưa cần mô hình; (2) bảng gán và bộ vàng: người
  dùng gán mù, song song với (1); (3) phán cụm và bước vá; (4) A5; (5) lệnh chấm, A/B model trên bộ vàng, rồi chốt
  tham số.
- **Tham số là điểm khởi đầu đã đo, chưa phải điểm chốt**: k = 3, ngưỡng n-gram 0,5, độ phân giải 2, trần 9. Tập
  bạc 25 cặp thiên về kênh tên vì một phần được rút từ chính top-list của kênh tên; bộ vàng mới là chỗ chốt.
- **Đã cân nhắc và bỏ**: phán theo cặp cho mọi cặp nghi trùng (A4 gốc §402) — bị thay bằng phán theo cụm ở Q22′,
  chỉ còn ở bước vá; tự gộp theo cosine — ADR 0006; connected components — xích; cho mô hình tool đọc chunk — thay bằng
  code đính kèm chunk cho đúng những ứng viên cần; phát lại hội thoại tra theo băm yêu cầu — không cần, vì hợp đồng với
  mô hình thật kiểm bằng vài fixture một lời gọi (duyệt ở bước chia ticket).
- **Vì sao cảnh báo mô tả trùng chỉ tính trong cùng section**: đếm trên cả tài liệu ra 7 câu / 21 tên, nhưng ca thứ bảy
  là hai section khác nhau tả `Khoảng ước lượng của phương sai tổng thể` và `Khoảng ước lượng của σ 2` bằng cùng một
  câu — một cặp **trùng thật**. Trong một section, câu dùng chung là dấu hiệu của mục liệt kê anh em; xuyên section thì
  không.
- **Hệ quả đáng biết**: tên chuẩn theo tần suất có thể là tiếng Anh trong tài liệu tiếng Việt (`Race Condition`).
  Đây là chủ ý của Q4 — giữ đúng cách tác giả dùng chữ — còn mô tả vẫn theo ngôn ngữ chủ đạo của tài liệu.
- **Liên quan tồn đọng**: F47 (độ hạt A3) vẫn mở, và nó ảnh hưởng thẳng tới tỉ lệ gộp; hai cảnh báo ở D11 là tín
  hiệu phụ cho nó.
