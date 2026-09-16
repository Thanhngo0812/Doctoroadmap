# Spec: A6–A8 — Cụm chủ đề, mention map và suy luận tiên quyết (Tầng 2b)

**Trạng thái:** draft — chờ nhân viên triển khai
**Nguồn:** phiên grilling 6 vòng, Q1–Q30, 2026-09-15/16; chủ dự án đã duyệt từng câu
**Nghiên cứu nền:** [`report/nghien-cuu-a6-a8-cum-chu-de-va-2b.md`](../report/nghien-cuu-a6-a8-cum-chu-de-va-2b.md)
**Chi phối bởi:** `spec-addendum.md` §0.1 (hệ kiểu mở, cờ `learnable`, ba bất biến), A6–A10 và Tầng 2b ·
ADR 0001 (định danh tất định) · ADR 0004 (đổi embedding là đổi tập node) · ADR 0006 (embedding chỉ đề cử) ·
ADR 0007 (2a đề xuất quan hệ kiểu mở) · **ADR 0008** và **ADR 0009** viết cùng spec này
**Ngôn ngữ chung:** `CONTEXT.md` — **Provenance**, **Mention**, **Mention map**, **Viện dẫn**, **Cặp chạm**,
**Cặp nghi tiên quyết**, **Boundary concept**, **Cụm chủ đề**, **Định tuyến**, **Pass chính**, **Pass phụ**,
**Khái niệm đích**, **Requires**, **Stage**
**Thay thế:** `spec-preview.md` §6–§8 (bước C, M, T2b) cho phần thiết kế. Preview giữ làm hồ sơ lịch sử.

---

## Problem Statement

A4/A5 đã xong: bốn tài liệu có bảng node canonical, mỗi node có tên chuẩn, alias, mô tả và provenance. Nhưng
**chưa có đồ thị tiên quyết**, nên chưa có lộ trình học — thứ duy nhất người dùng cuối thật sự cần.

Số trên kho chính hiện tại:

| Tài liệu | chunk | section | node | `learnable` | media | cạnh | `requires` |
|---|---:|---:|---:|---:|---:|---:|---:|
| baocao-canhan | 26 | 27 | 39 | 36 | 3 | 25 | 0 |
| naive-bayes | 40 | 32 | 48 | 34 | 14 | 57 | 2 |
| nhap-mon-ml | 41 | 27 | 84 | 75 | 9 | 67 | 1 |
| xstk-ch3-1 | 126 | 43 | 151 | 98 | 53 | 137 | 7 |

Mọi cạnh `requires` ít ỏi đó đến từ đề xuất của A3, chưa ai kiểm. Không có A8 thì A9 không có gì để validate,
A10 không có gì để xếp tầng, và pha B không có gì để mở khoá.

Năm khó khăn, mỗi cái đều có số hoặc nguồn:

1. **Không gian cặp là bậc hai.** Một giáo trình 250 khái niệm học được có hơn 31.000 cặp vô hướng. Hỏi mô hình
   từng cặp là được về tiền (mục D14) nhưng không được về độ trễ và độ chính xác: gán theo cặp sinh thừa quan hệ
   và cho độ đồng thuận thấp nhất trong PREAP (κ 0,16–0,60 so với 0,45–0,71).
2. **Luật dựng cạnh của A6 hiện hành hỏng trên dữ liệu thật.** `spec-addendum` §451 (A6, kênh similarity) ghi *"cosine của embedding
   description ≥ 0,75"*. Với `gemini-embedding-001`, cosine giữa hai thực thể bất kỳ đã khoảng 0,80; 92,5% cặp
   vượt 0,75. Mỗi tài liệu thành đúng một cụm, tức A7 không chia được gì.
3. **Trần cỡ cụm không tự cứng.** Mã nguồn GraphRAG 3.1.2 gom bằng Leiden phân cấp với `max_cluster_size = 10`,
   nhưng graspologic-native giữ nguyên cụm *"không chẻ được nữa"*, và mặc định **bỏ mọi nút ngoài thành phần liên
   thông lớn nhất**. Chép nguyên cách đó thì khái niệm lẻ mất cụm, còn cụm dày vẫn quá lớn cho một lời gọi.
4. **Provenance không đủ để dò cặp xuyên vùng.** `chunk_ids` trả lời *"khái niệm được dạy ở đâu"*. Quan hệ tiên
   quyết xuyên chương lại có hình dạng *"dạy ở chương 3, dùng lại ở chương 8"*. Dùng provenance để dò là tự bịt
   mắt đúng chỗ cần nhìn.
5. **Bộ vàng tiên quyết sẵn có đo sai thứ.** Các bộ phổ biến cho người gán dùng kiến thức nền; GPT-4 zero-shot
   **không đọc văn bản nào** đạt F1 0,777 trên LectureBankCD, hơn baseline có giám sát 0,747, và thêm tài liệu
   vào prompt còn làm kết quả giảm. Chấm 2b bằng bộ vàng kiểu đó là thưởng cho đúng thứ 2b phải chặn.

## Solution

Một luồng **A6 → A7 → M → A8 → A9 → A10**, trong đó mọi bước không cần phán đoán đều là code tất định, và mô
hình chỉ xuất hiện ở hai loại lượt:

- **A6 — đồ thị chủ đề.** Ba kênh có trọng số: đồng xuất hiện của provenance, láng giềng gần nhất trên vector mô
  tả A5, và media đồng vị trí. Không ngưỡng cosine tuyệt đối nào.
- **A7 — cụm chủ đề.** Leiden với hàm mục tiêu CPM và **trần cứng đếm theo khái niệm**, media cỡ 0. Mọi node
  nhận `cluster_id`, kể cả node lẻ.
- **M — mention map.** Kênh khớp tên chính xác (không bỏ dấu) cộng kênh ngữ nghĩa (chuẩn hoá hai phía), cộng hạt
  giống provenance. Từ đó code dựng **viện dẫn** (có hướng) và **cặp chạm** (vô hướng), rồi ra **cặp nghi tiên
  quyết**.
- **A8 — hai loại lượt.** **Pass chính trích mở**: mỗi (siêu) section của chương, hoặc mỗi cụm chủ đề, một lời
  gọi, không tool; mô hình được hỏi theo **khái niệm đích** kiểu PREAP. **Pass phụ chỉ kiểm cặp**: chỉ phán các
  cặp nghi tiên quyết nằm vắt ngang trục của pass chính.
- **A9 — tầng 3.** Chu trình giải theo thành phần liên thông mạnh, không theo "cạnh nào đến trước thì thắng".
  Cạnh thừa chỉ được **đánh dấu**, không xoá.
- **A10 — lộ trình.** Xếp tầng Kahn trên đúng cạnh `requires` của node `learnable`, stage là giao của tầng với
  cụm chủ đề.

Song song với sản phẩm là phần đo, vì đầu ra của đợt này còn là một **báo cáo thực nghiệm**:

- **Bộ vàng bám văn bản** theo giao thức PREAP: hai người gán mù trên file Excel do code sinh, hội ý các chỗ
  lệch, và bộ vàng **chỉ dùng để kiểm**.
- **Luật chấm viết trước khi đo**, gồm luật chọn bộ sinh cặp mặc định và luật đổi mặc định giữa trích mở với
  kiểm cặp.
- **Hai thí nghiệm quyết định nhất không tốn một lời gọi mô hình nào**: cạnh tiên quyết nằm ở đâu (E1), và bộ
  sinh cặp nào giữ được cạnh vàng với ít cặp nhất (E2).

## User Stories

**Người học (đầu ra cuối)**

1. Là người học, tôi muốn tài liệu của mình được chia thành các stage học tuần tự, để biết nên học gì trước.
2. Là người học, tôi muốn mỗi stage chỉ có 5–8 khái niệm, để học xong trong một lần ngồi.
3. Là người học, tôi muốn các khái niệm trong một stage thuộc cùng một mảng chủ đề, để không nhảy chủ đề giữa chừng.
4. Là người học, tôi muốn mỗi quan hệ tiên quyết trỏ được về đoạn văn trong chính tài liệu, để kiểm chứng khi thấy lạ.
5. Là người học, tôi muốn hình và bảng không bao giờ bị coi là thứ phải học trước, để lộ trình không có mục vô nghĩa.
6. Là người học, tôi muốn lộ trình không có vòng lặp, để không gặp cảnh A đòi B mà B lại đòi A.
7. Là người học, tôi muốn tài liệu không có cấu trúc tiên quyết rõ vẫn cho tôi một lộ trình theo thứ tự chương, thay vì một đồ thị rỗng.

**Chủ dự án, với tư cách người làm nghiên cứu thực nghiệm**

8. Là chủ dự án, tôi muốn biết cạnh tiên quyết của một giáo trình nằm ở đâu — cùng chunk, cùng mục, cùng chương, cùng cụm, nối qua một lần nhắc, hay ngầm — để biết pass phụ và mention map có đáng làm không.
9. Là chủ dự án, tôi muốn con số đó tính được mà không tốn một lời gọi mô hình nào, để quyết định trước khi tiêu tiền.
10. Là chủ dự án, tôi muốn mỗi bộ sinh cặp có số recall riêng và số cặp riêng, để biết cái nào đáng giữ.
11. Là chủ dự án, tôi muốn biết phần recall mà **chỉ riêng** một bộ sinh có, để bỏ được bộ sinh thừa.
12. Là chủ dự án, tôi muốn so trích mở với kiểm cặp trên cùng bộ vàng, để lựa chọn thiết kế của mình thành một phát hiện có số, không phải một giả định.
13. Là chủ dự án, tôi muốn luật đổi mặc định được viết trước khi thấy số, để không tự chiều mình.
14. Là chủ dự án, tôi muốn mọi chỉ số kèm khoảng tin cậy, để không tuyên bố "tốt hơn" khi chỉ là nhiễu.
15. Là chủ dự án, tôi muốn biết mô hình khẳng định được bao nhiêu cạnh khi **không** được đọc văn bản, để đo mức rò rỉ kiến thức nền.
16. Là chủ dự án, tôi muốn mọi lượt chạy ghi số lời gọi và chi phí cộng dồn, để giữ trong trần 50 USD.
17. Là chủ dự án, tôi muốn chạy lại toàn bộ khi chặn mạng cho kết quả y hệt, để báo cáo nói được chữ "tái lập".
18. Là chủ dự án, tôi muốn báo cáo ghi rõ đâu là số đo, đâu là suy luận, để người phản biện phân biệt được.

**Người gán nhãn**

19. Là người gán nhãn, tôi muốn một file Excel mở ra là làm được ngay, để không phải học công cụ mới.
20. Là người gán nhãn, tôi muốn danh sách khái niệm có sẵn kèm nơi dạy (chương, mục, trang), để tìm đúng chỗ trong sách.
21. Là người gán nhãn, tôi muốn chọn khái niệm từ danh sách thay vì gõ tay, để không gõ sai tên.
22. Là người gán nhãn, tôi muốn **không** thấy cạnh nào do máy đề xuất, để nhãn của tôi không bị neo theo máy.
23. Là người gán nhãn, tôi muốn chỉ ghi cặp có quan hệ, không phải duyệt hết mọi cặp, để không kiệt sức.
24. Là người gán nhãn, tôi muốn đánh dấu được "không phải khái niệm", "thiếu khái niệm" và "node gộp sai", để lỗi của bước trước không biến thành lỗi của tôi.
25. Là người gán nhãn, tôi muốn ghi vị trí trong sách và loại bằng chứng cho mỗi cạnh, để lúc hội ý còn nhớ mình dựa vào đâu.
26. Là người gán nhãn, tôi muốn gán được cả quan hệ trỏ về khái niệm của chương trước, để không mất đúng phần thú vị nhất.
27. Là người gán nhãn thứ hai, tôi muốn làm trên bản sao riêng, để hai người không thấy nhãn của nhau trước khi hội ý.
28. Là chủ dự án, tôi muốn độ đồng thuận tính cả đồng thuận ngầm qua bắc cầu, để không bị phạt oan vì một người ghi cạnh trực tiếp còn người kia ghi đường vòng.

**Người vận hành pipeline**

29. Là người vận hành, tôi muốn một lệnh chạy hết A6 đến A10 cho một tài liệu, để không phải nhớ thứ tự các bước.
30. Là người vận hành, tôi muốn dừng được ở bước mention map mà không gọi mô hình, để chạy phần đo rẻ trước.
31. Là người vận hành, tôi muốn chạy lại khi không đổi gì thì dùng lại artifact cũ và tốn 0 lời gọi, như A3 và A4.
32. Là người vận hành, tôi muốn đổi mô hình hay đổi embedding thì sinh phiên bản artifact mới, không âm thầm trộn.
33. Là người vận hành, tôi muốn mọi tham số gom cụm nằm trong manifest, để biết một artifact được sinh ra bằng cấu hình nào.
34. Là người vận hành, tôi muốn lượt chạy hỏng giữa chừng thì phục hồi được từ checkpoint, để không mất tiền đã tiêu.

**Nhân viên triển khai, và người đọc code sau này**

35. Là người triển khai, tôi muốn luật phán đoán nằm trong module thuần, để test được mà không cần mô hình.
36. Là người triển khai, tôi muốn executor từ chối cạnh sai luật và trả lỗi cụ thể, để không phải dặn dò trong prompt.
37. Là người triển khai, tôi muốn mô hình trả **loại bằng chứng** còn code quy ra số, để không phụ thuộc con số mô hình tự khai.
38. Là người triển khai, tôi muốn cạnh nào cũng truy được về nguồn đã đề cử nó, để đo được bộ sinh.
39. Là người triển khai, tôi muốn phiên bản thư viện gom cụm được ghim và ghi vào manifest, để kết quả không đổi khi ai đó nâng cấp.
40. Là người triển khai, tôi muốn mọi kiểm tra cấu trúc nằm trong code chứ không trong prompt, để hệ kiểu mở vẫn an toàn.

**Tầng sau (A9, A10, pha B)**

41. Là tầng validate, tôi muốn chỉ đọc cạnh `requires` trên node `learnable`, để media và quan hệ kiểu mở không làm hỏng chu trình hay cổng chất lượng.
42. Là tầng validate, tôi muốn cạnh thừa được đánh dấu thay vì bị xoá, để lúc người duyệt gỡ một cạnh sai thì cạnh đúng không biến mất theo.
43. Là tầng lộ trình, tôi muốn biết node nào không có tiên quyết vì thật sự không có, chứ không phải vì 2b chưa xét tới nó.
44. Là pha B, tôi muốn mỗi chunk mang `stage_id`, để tutor chỉ đọc phần người học đã mở khoá.
45. Là người duyệt ở A13, tôi muốn xem được nhật ký quyết định của từng cạnh, gồm bằng chứng, nguồn đề cử và lượt phán, để sửa mà không phải chạy lại.

## Implementation Decisions

### D1 — Một use case, một tầng artifact, bốn stage *(Q4, seam ①)*

- Toàn bộ A6 → A10 nằm trong **một use case**, giống cách `Canonicalize` gộp lớp tên, đề cử và phán. Lý do: các
  bước dùng chung một artifact và một khoá cấu hình; tách ra bốn use case chỉ nhân bốn lần chỗ nối.
- Đầu vào: bảng node canonical mới nhất, chunks, sections và chỉ mục truy hồi của cùng `doc_id`.
- Đầu ra ghi vào **tầng artifact `graph`** đã có sẵn trong store nhưng chưa ai dùng. `stage` tăng dần và là một
  phần của manifest:

  | `stage` | Có gì | Gọi mô hình |
  |---|---|---|
  | `clusters` | đồ thị chủ đề A6, `cluster_id` của mọi node | không |
  | `mentions` | mention map, viện dẫn, cặp chạm, cặp nghi tiên quyết | không |
  | `edges` | cạnh `requires` từ pass chính và pass phụ, nhật ký phán | có |
  | `stages` | sau A9 và A10: cạnh đã validate, tầng, stage, `stage_id` gắn về chunk | có |

- Lệnh: một lệnh chạy cả luồng, có tuỳ chọn **dừng ở một stage**. Dừng ở `mentions` là cấu hình chạy được toàn
  bộ E1 và E2 mà không tốn lời gọi nào.
- Cache và phiên bản theo đúng luật của A3/A4: khoá cấu hình băm trên **nội dung** — prompt, schema, `model_id`,
  tham số sinh, mọi tham số A6/A7/M, `embedding_model_id` và số chiều (ADR 0004), phiên bản thư viện gom cụm.
  Không đổi gì thì `reused=true`, 0 lời gọi.
- Checkpoint sau mỗi phiên của pass chính và mỗi phiên của pass phụ, để lượt chạy hỏng giữa chừng không mất phần
  đã trả tiền.

### D2 — A6: đồ thị chủ đề dựng bằng ba kênh, không ngưỡng tuyệt đối *(sửa `spec-addendum` §451 (A6, kênh similarity))*

Chạy trên **đồ thị đầy đủ**, mọi `node_type`, kể cả media.

| Kênh | Cách tính | Vì sao |
|---|---|---|
| Đồng xuất hiện | hai node có provenance chung một chunk (trọng số cao) hoặc chung một mục (thấp hơn), chuẩn hoá bằng PMI/NPMI | Kênh duy nhất hoàn toàn dựa vào tài liệu; PMI phạt đúng các node xuất hiện khắp nơi |
| Độ gần ngữ nghĩa | **mutual-kNN** trên vector mô tả A5, k nhỏ, **không có sàn cosine** | Nền cosine của dự án là 0,80; ngưỡng tuyệt đối nối cả tài liệu thành một cụm. Đây vẫn là quyền **đề cử**, không phải quyền quyết (ADR 0006) |
| Media đồng vị trí | tham chiếu hình và bảng của chunk, trọng số `1/(bậc−1)`, cảnh báo khi bậc ≥ 5 | Tác giả tự tay đặt các khái niệm đó vào chung một hình; không phụ thuộc mô hình embedding |

- Ba kênh **tự chuẩn hoá rồi mới hợp**; không cộng hai thang khác nhau vào một số.
- Luật hạ trọng số theo bậc áp cho **cả chunk**: một chunk nhắc quá nhiều khái niệm thì mỗi liên kết trong đó ít
  mang tin hơn.
- Cắt cạnh theo **phân vị**, không theo ngưỡng tuyệt đối. Tham số phân vị vào manifest.
- Vector mô tả A5 được embed với kiểu `SEMANTIC_SIMILARITY`, vì đây là phép so đối xứng node với node.

### D3 — A7: Leiden, hàm mục tiêu CPM, trần cứng đếm theo khái niệm *(sửa `spec-addendum` §464–§468 (A7))*

- **Leiden, không Louvain.** Louvain có thể sinh cộng đồng liên thông kém hoặc không liên thông; Leiden bảo đảm
  mọi cộng đồng liên thông.
- **Hàm mục tiêu CPM**, vì tham số giữ nguyên nghĩa ở mọi cấp: cộng đồng phải đặc hơn ngưỡng, giữa các cộng đồng
  thưa hơn ngưỡng. Modularity đổi nghĩa khi chạy đệ quy trên đồ thị con, và mắc giới hạn phân giải.
- **Trần cứng trong lúc tối ưu**, không phải lượt chẻ hậu kỳ: cỡ cụm tính bằng tổng cỡ node, node `learnable`
  cỡ 1 và media cỡ 0, trần 12. Luật "đếm theo concept, không đếm media" của addendum §468 do đó thành một tham
  số, không cần vòng đệ quy — và không rơi vào ca "không chẻ được nữa" của thư viện GraphRAG đang dùng.
- **Không lọc thành phần liên thông lớn nhất.** Mọi node phải có `cluster_id`, kể cả khái niệm lẻ và media mồ côi.
- **Cụm 1–2 khái niệm sáp nhập vào cụm gần nhất**, với "gần nhất" định nghĩa theo thứ tự: tổng trọng số cạnh
  sang cụm kia, rồi cosine tới tâm embedding của cụm, rồi thứ tự tài liệu. Luật phải tất định.
- Manifest ghi: tên thư viện, **phiên bản**, hàm mục tiêu, độ phân giải, seed, trần, và **thứ tự cạnh** đưa vào
  thuật toán. Chính GraphRAG phải ghim phiên bản thư viện gom cụm vì bản mới đổi kết quả cụm; ta ghi lại để biết.
- Node mới sinh ở tầng 3 chỉ được **gán incremental** vào cụm gần nhất, không chạy lại Leiden.

### D4 — M: mention map hai kênh, ba mức, và tín hiệu có hướng *(Q5, Q10, Q12)*

**Kênh exact** — khớp nhiều mẫu trên tên chuẩn và alias của node `learnable`:

- Chuẩn hoá: NFC, casefold, thống nhất vị trí dấu thanh, biến thể i/y. **Không bỏ dấu** — 95% từ tiếng Việt
  mang dấu và 80% số đó thành mơ hồ khi bỏ dấu; ở lớp tên của A4, nới thêm bỏ dấu chỉ gộp thêm đúng một nhóm.
- Khớp theo ranh giới từ, **ưu tiên khớp dài nhất bên trái**, bỏ khớp lồng. Chữ Việt cách nhau theo âm tiết, nên
  không có luật này thì tên một âm tiết khớp trong mọi tên dài chứa nó.
- **Ký hiệu không dùng để khớp mention** (`CONTEXT.md`: Ký hiệu). Tên quá chung bị loại khỏi kênh này.

**Kênh dense** — bắt cách diễn đạt lại:

- Embed **mô tả node theo kiểu `RETRIEVAL_QUERY`**, so với vector chunk `RETRIEVAL_DOCUMENT` có sẵn trong chỉ
  mục. Đây là bài truy hồi bất đối xứng; so vector `SEMANTIC_SIMILARITY` với `RETRIEVAL_DOCUMENT` là so hai
  thước đo khác nhau.
- Lọc **theo từng hàng** bằng z-score và top-k, **cộng chuẩn hoá phía chunk**: trừ cả độ gần trung bình của node
  lẫn của chunk, kiểu CSLS. Chunk tổng quan hay bảng ký hiệu gần mọi node một chút, nên chỉ chuẩn hoá một phía
  không chặn được.
- Kênh này **chỉ đề cử**. Một mention mềm không bao giờ tự thành cạnh.

**Ba mức tin, ghi rõ trong mention map:** `định nghĩa` (chunk thuộc provenance) > `trích` (chunk mà A3 lấy ứng
viên ra nhưng không dạy) > `nhắc` (chỉ do kênh exact hoặc dense bắt được). Độ tin tuyệt đối chỉ dành cho mức
`định nghĩa`.

**Đầu ra dẫn xuất, đều là code thuần:**

- **Viện dẫn** — có hướng: B được nhắc trong provenance của A, tức bằng chứng B có thể cần trước A.
- **Cặp chạm** — vô hướng: hai khái niệm thuộc hai cụm chủ đề khác nhau cùng được nhắc trong một chunk.
- **Sổ cặp cụm**: hai bộ đếm **tách rời** cho kênh exact và kênh dense, không trộn hai thang khác nhau bằng một
  phép lấy nhỏ nhất. Trọng số hạ theo số khái niệm trong chunk. Ngưỡng mở phiên là **tương đối** (trọng số trung
  bình) hoặc top-k mỗi cụm, không phải một con số tuyệt đối lệch theo độ dài tài liệu.
- **Cờ khái niệm thiếu**: cụm từ lặp nhiều mà không khớp node nào thì ghi cờ cho tầng 3 — chạy ngược cùng một
  hạ tầng.

### D5 — Bộ sinh cặp nghi tiên quyết, và luật mặc định viết trước khi đo *(Q13)*

Bốn nguồn đề cử, mọi cặp đều ghi nguồn:

1. hai khái niệm có provenance trong cùng một section;
2. **viện dẫn**;
3. **cặp chạm**;
4. quan hệ đề xuất còn lại của A3 và 2a, gồm cả `subtype_of`. Chúng vẫn chỉ là đề xuất: precision `subtype_of`
   đo được là 0,658, các kiểu khác đúng khoảng 70% trên mẫu 30.

**Luật mặc định:** hợp mọi bộ sinh. Một bộ sinh chỉ bị bỏ khỏi mặc định khi trên bộ vàng nó **không đóng góp cạnh
vàng nào mà các bộ khác bỏ sót**. Giữ đúng triết lý của 2a: cặp bỏ sót thì mất vĩnh viễn, cặp thừa thì bước phán
tự loại, và chi phí phán ở quy mô giáo trình chỉ vài USD.

Báo cáo cho từng bộ sinh: số cặp, recall cạnh vàng, và phần recall **chỉ riêng nó** có.

### D6 — Định tuyến *(Q14, Q18; sửa `spec-addendum` §738 (Tầng 2b, tài liệu ngắn))*

| Điều kiện | Pass chính | Pass phụ |
|---|---|---|
| ≤ 20 khái niệm học được trong cả tài liệu | một phiên duy nhất | không |
| Cây khai báo có phân cấp thật | theo **chương**: mỗi (siêu) section một phiên, tuần tự trong chương, các chương song song | quét **cùng cụm chủ đề**: cặp nghi tiên quyết cùng cụm chưa có đường nối |
| Cây thoái hoá hoặc không có heading | theo **cụm chủ đề**: mỗi cụm một phiên, song song | **liên cụm**: cặp nghi tiên quyết từ sổ cặp cụm |

- Ngưỡng đếm theo **khái niệm học được**, không theo số trang: bốn tài liệu cũ có 36, 34, 75 và 98 khái niệm học
  được, nên luật "dưới 50 trang" cũ sẽ dồn 75 khái niệm vào một lời gọi. 20 là tham số, ghi vào manifest.
- **Cặp nghi tiên quyết vẫn được sinh theo cả hai trục** dù định tuyến chọn trục nào. Định tuyến chỉ quyết cặp
  nào nằm chung một phiên, và trục nào là pass chính. Nhờ vậy E2 so được ba cấu hình — chỉ trục chương, chỉ trục
  cụm, hợp cả hai — mà không cần gọi mô hình.
- Lựa chọn định tuyến và lý do ghi vào manifest.

### D7 — Pass chính: trích mở, một lời gọi mỗi phiên, không tool *(Q9, Q19, Q20 · ADR 0008)*

**Đơn vị phiên:** một (siêu) section của chương, hoặc một cụm chủ đề, theo định tuyến ở D6.

**Mô hình nhận:**

1. **nguyên văn chunk** của đơn vị đang xét (với nhánh cụm: chunk định nghĩa của các node trong cụm);
2. **khái niệm đích** — node `learnable` có provenance ở đây, kèm tên chuẩn, alias, mô tả A5;
3. **khái niệm được nhắc ở đây nhưng dạy nơi khác**, lấy từ mention map, kèm nơi dạy;
4. cạnh đã tạo ở các phiên trước **trong cùng chương** (nhánh chương) — đây là trạng thái duy nhất được truyền;
5. quan hệ đề xuất liên quan của A3 và 2a, kèm `origins`.

**Câu hỏi, đúng tinh thần PREAP:** *với mỗi khái niệm đích, cần biết khái niệm nào trong danh sách để hiểu nó
**như đoạn này trình bày**?* Không hỏi theo kiến thức nền.

**Hợp đồng đầu ra** — một batch JSON duy nhất mỗi phiên:

```json
{
  "edges": [
    {"target": "cpt_backprop", "prerequisite": "cpt_chainrule",
     "evidence_kind": "noi_ro", "chunk_ids": ["c_0232"],
     "reason": "đoạn này nói backprop áp dụng chain rule"}
  ],
  "flags": [{"kind": "missing_node", "name": "Bias-Variance Tradeoff", "chunk_ids": ["c_0044"]}]
}
```

- `target` và `prerequisite` **bắt buộc nằm trong danh sách** của phiên. Khái niệm ngoài danh sách chỉ được ghi
  cờ, không thành cạnh, và không được tự tạo node.
- **Không tool.** Không tìm node, không đọc thêm chunk, không thêm cạnh đồng bộ. Danh sách khái niệm đã do
  mention map lo, văn bản đã bơm sẵn, chu trình giải ở tầng 3.
- **Chỉ sinh `requires`.** Quan hệ kiểu mở vẫn là việc của 2a (ADR 0007). Đây là chỗ spec này **hẹp hơn**
  `spec-addendum` §494 (A8, loại cạnh mở): 2b không đặt thêm kiểu cạnh mới, vì phần đo của đợt này chấm trên `requires`.
- Nhánh chương chạy **tuần tự trong chương**, các chương song song. Nhánh cụm: mỗi cụm một phiên khép kín, song
  song hoàn toàn.
- Mô hình **không** trả số confidence. Nó trả `evidence_kind`; code quy ra số theo D10.

### D8 — Pass phụ: chỉ kiểm cặp nghi tiên quyết *(Q9, Q13 · ADR 0008)*

- Đầu vào là **hồ sơ theo cặp**, không phải hai danh sách rời: mỗi cặp kèm nguồn đề cử, trọng số của từng kênh,
  chunk bằng chứng nguyên văn, mô tả hai node, thứ tự provenance, và đường đi gián tiếp đã có (nếu có).
- Mô hình chỉ được phán **trong danh sách cặp**. Thấy quan hệ ngoài danh sách thì ghi cờ.
- **Bốn phán quyết:** tạo cạnh (kèm chiều), không có quan hệ trực tiếp, đã có đường gián tiếp, hoặc hoãn.
- **Chống thiên vị vị trí:** mỗi cặp hỏi ở **cả hai thứ tự**, hoặc hỏi một thứ tự chuẩn rồi kiểm nhất quán; hai
  lần lệch nhau thì hoãn. Văn liệu đo được mô hình đổi kết luận khi đảo vị trí trong 35–76% số ca tuỳ mô hình.
- **Tỉa theo reachability chỉ khi mọi cạnh trên đường đi đều có bằng chứng tường minh.** Còn lại thì đưa đường đi
  vào hồ sơ để mô hình tự xét. Mọi cặp bị tỉa đều ghi log để kiểm mẫu.
- Cặp bị từ chối cũng ghi log: đó là thước **precision** của bộ sinh. Recall của bộ sinh phải đo riêng bằng mẫu
  cặp **ngoài** bộ sinh (D14).

### D9 — Executor: mọi kiểm tra cấu trúc nằm trong code *(Q15)*

| Kiểm tra | Hành động khi vi phạm |
|---|---|
| Node id không có trong bảng canonical | từ chối thao tác |
| Một đầu cạnh `learnable = false` | từ chối (bất biến I-G1) |
| Chunk bằng chứng không tồn tại | từ chối |
| **Chunk bằng chứng không nhắc cả hai đầu cạnh** (tra mention map) | từ chối |
| Cạnh tự nối, hoặc trùng cạnh đã có | bỏ, ghi log |
| `evidence_kind` ngoài danh sách | từ chối |
| Tên quan hệ đồng nghĩa `requires` | từ chối, báo dùng `requires` |

- **Một lượt retry duy nhất** cho các thao tác lỗi; thao tác đã nhận không chạy lại.
- Phiên **ghi đề xuất vào một nhật ký chỉ-thêm**, không sửa trực tiếp đồ thị. Một bộ gộp tất định áp theo khoá
  (phiên, thứ tự thao tác), nên kết quả không phụ thuộc phiên nào chạy xong trước.
- **Không chặn chu trình đồng bộ trong lúc thêm cạnh.** Chặn kiểu đó nghĩa là "cạnh nào đến trước thì thắng";
  chu trình giải ở tầng 3 khi đã thấy đủ bằng chứng của mọi phía (D11).

### D10 — Loại bằng chứng, chiều cạnh và thứ tự tài liệu *(Q15; sửa `spec-addendum` §815 (Tầng 2b, rubric confidence))*

| `evidence_kind` | Nghĩa | Confidence do code gán |
|---|---|---|
| `noi_ro` | văn bản nói thẳng rằng cần biết B trước để hiểu A | 0,9 |
| `trong_dinh_nghia` | B nằm trong câu định nghĩa nguyên văn của A **và cần để hiểu câu đó** | 0,9 |
| `mach_trinh_bay` | suy luận mạnh từ mạch trình bày của đoạn | 0,7 |
| `suy_doan` | suy đoán | code từ chối, không tạo cạnh |

- Điều kiện *"cần để hiểu"* là bắt buộc với `trong_dinh_nghia`: lỗi chính mà giáo viên tìm thấy trong bộ vàng
  PREAP là khái niệm được nhắc khi giải thích khái niệm khác nhưng chỉ là giải thích thêm.
- Câu định nghĩa lấy từ **văn bản tài liệu**, không lấy từ mô tả A5 — mô tả do mô hình viết có thể mang kiến thức
  nền của chính nó.
- **Thứ tự lấy từ provenance**, không lấy từ lần nhắc đầu tiên. Mỗi cạnh ghi `order_relation` ∈ {thuận, ngược,
  cùng chunk}.
- Cạnh ngược thứ tự chỉ được tạo khi có bằng chứng tường minh, và bị trừ 0,1. **Con số 0,1 là tạm**: không nguồn
  nào ủng hộ nó, nên E8 hiệu chỉnh lại trên bộ vàng, và báo cáo ghi rõ nó được hiệu chỉnh sau.
- Tín hiệu chiều thứ hai, rẻ và độc lập: **viện dẫn**. Cạnh thuận theo viện dẫn được ghi nhận trong nhật ký để
  E8 đo.

### D11 — Tầng 3 (A9): giải mâu thuẫn khi đã thấy toàn cảnh *(Q15)*

Theo thứ tự:

1. **Xử lý tồn đọng:** cặp hoãn của 2b, cụm hoãn của 2a, cờ khái niệm thiếu (tạo node nếu đủ bằng chứng), cờ node
   sai do người gán nhãn đánh dấu.
2. **Chuẩn hoá sổ đăng ký kiểu** như `spec-addendum` §857 (Tầng 3, sổ đăng ký kiểu): gom tên kiểu gần nghĩa, gắn cờ kiểu dùng một lần,
   **không** tự quy tên nghi đồng nghĩa `requires` về `requires`.
3. **Chu trình, chạy trên đúng đồ thị con `requires` của node `learnable`:** tìm thành phần liên thông mạnh; với
   mỗi thành phần, chọn tập cạnh phải gỡ bằng tìm kiếm vét cạn trong thành phần đó (thành phần trong một tài liệu
   thường nhỏ). Thứ tự ưu tiên **giữ** cạnh: loại bằng chứng (`noi_ro` > `trong_dinh_nghia` > `mach_trinh_bay`),
   rồi thuận thứ tự provenance, rồi số nguồn độc lập đã đề cử, rồi confidence. Không dùng confidence làm tiêu chí
   đầu tiên: nó do mô hình tự khai và thường quá tự tin.
4. **Chu trình hai cạnh là tín hiệu danh tính trước đã:** hai khái niệm đòi nhau thường là cặp anh em hoặc cặp
   nghi trùng mà 2a chưa tách đúng. Ghi cờ cho A13 trước khi nghĩ tới cắt cạnh. Trong một bộ dữ liệu tiên quyết
   công bố, 4% cạnh là hai chiều và tác giả coi đó là hợp lệ.
5. **Cổng chất lượng** như `spec-addendum` §522 (A9, quality gate): chỉ đếm cạnh `requires`, mẫu số là node `learnable`. Không đạt
   thì rơi về lộ trình theo thứ tự chương.
6. **Cạnh thừa chỉ được đánh dấu.** Ghi `redundant_via` trỏ vào đường đi gián tiếp; **không xoá**. Xếp tầng chỉ
   phụ thuộc tính đến được nên không đổi; còn xoá thì lúc người duyệt gỡ một cạnh sai, cạnh trực tiếp đúng đã
   biến mất và không tự quay lại.
7. **Gán cluster incremental** cho node mới ở bước 1.

### D12 — A10 và trang xem *(Q6)*

- Xếp tầng Kahn **chỉ trên đồ thị con `requires` của node `learnable`**.
- Stage = giao của một tầng với một cụm chủ đề, trần 5–8 khái niệm.
- **Phân biệt hai loại node không có tiên quyết:** node đã được xét mà không tìm thấy tiên quyết, và node chưa
  từng nằm trong phiên nào. Mỗi node ghi các phiên đã xét nó. Loại thứ hai là lỗi phủ, phải báo, không được lặng
  lẽ rơi vào tầng 1.
- Gắn `stage_id` ngược về chunk: chunk thuộc nhiều stage thì lấy stage sớm nhất, kèm danh sách đầy đủ.
- **Trang xem tĩnh** sinh từ artifact: danh sách stage, khái niệm trong từng stage, cạnh kèm chunk bằng chứng,
  cờ và cạnh bị đánh dấu thừa. Là trang tĩnh để đọc và kiểm, không phải ứng dụng.

### D13 — Bộ vàng tiên quyết bám văn bản *(Q3, Q11, Q22, Q26, Q27, Q28 · ADR 0009)*

- **Giao thức PREAP:** người gán đọc chương và ghi quan hệ tiên quyết **trong lúc đọc**, dựa trên cách tài liệu
  trình bày, không dựa vào kiến thức nền.
- **Phạm vi:** một **chương giữa** mỗi giáo trình. Khái niệm đích là node `learnable` có provenance trong chương
  đó; đầu được cần có thể là **bất kỳ node nào của cả tài liệu**, nên cạnh xuyên chương vào được bộ vàng.
- **Công cụ:** một lệnh sinh **file Excel** từ artifact, mở bằng Excel 365. Sheet hướng dẫn; sheet khái niệm
  (khoá, kèm nơi dạy: chương, mục, trang); sheet quan hệ (chọn từ danh sách, kèm vị trí trong sách, loại bằng
  chứng, ghi chú); sheet cờ (không phải khái niệm, thiếu khái niệm, node gộp sai). Một ô ẩn ghi phiên bản artifact
  để lúc chấm biết file khớp với bảng node nào. `openpyxl` được khai thành phụ thuộc trực tiếp.
- **Mù:** file không chứa cạnh nào của pipeline. Người gán không xem đầu ra 2b cho tới khi bộ vàng đóng băng.
- **Hai người gán độc lập**, mỗi người một bản sao. Tính độ đồng thuận **có kể đồng thuận ngầm qua bắc cầu**, rồi
  hai người **hội ý** các cạnh lệch; bộ vàng chính là kết quả hội ý. Số trên hợp và trên giao báo cáo kèm để xem
  độ nhạy.
- **Chỉ dùng để kiểm.** Việc phát triển prompt 2b làm trên bốn tài liệu cũ và các chương không có vàng.
- **Cờ node sai** thu được ở đây dùng luôn làm mẫu kiểm A4 trên tài liệu mới; đợt này không gán vàng A4 mới.
- Tài liệu phẳng **không có vàng**; nó chỉ dùng để chạy nhánh cụm và kiểm mẫu định tính.
- **E5** (nhãn mention trên 40–60 chunk) chỉ làm **sau khi** xong nhãn tiên quyết. Không kịp thì ghi thành giới
  hạn, không hạ xuống nhãn máy.

### D14 — Thí nghiệm và luật chấm, viết trước khi đo *(Q8, Q13, Q21, Q28, Q30)*

| # | Câu hỏi | Cách đo | Lời gọi mô hình |
|---|---|---|---|
| E1 | Cạnh tiên quyết nằm ở đâu? | Trên vàng, chia cạnh theo sáu loại vị trí: cùng chunk · cùng mục · cùng chương · cùng cụm · xuyên cả hai nhưng có chunk nhắc cả hai (exact / chỉ dense) · ngầm. Kèm NMI giữa cụm chủ đề và chương | 0 |
| E2 | Bộ sinh nào giữ được cạnh vàng với ít cặp nhất? | Mỗi bộ sinh và mỗi tổ hợp: số cặp, recall, recall chỉ riêng nó. Gồm ba cấu hình định tuyến: chỉ trục chương, chỉ trục cụm, hợp cả hai | 0 |
| E3 | Chất lượng phán quyết | P/R/F1 trên cạnh trực tiếp **và** trên bao đóng bắc cầu; lời gọi, token, USD; ba lượt chạy để đo Jaccard cạnh | có |
| E4 | Rò rỉ kiến thức nền | Cùng cặp, hỏi **không kèm văn bản** rồi so với có văn bản; đếm cạnh mô hình vẫn khẳng định mà vàng không có | có |
| E5 | Nhận diện mention | P/R của kênh exact (có và không bỏ dấu), thêm kênh dense, thêm khử nhập nhằng | 0 |
| E6 | Trích mở đối đầu kiểm cặp | Chạy lại đúng danh sách khái niệm của các phiên có vàng theo kiểu kiểm cặp; so P/R/F1 | có |
| E7 | Cái giá của các bước nhất quán | Cạnh vàng bị cắt chu trình, bị đánh dấu thừa, hoặc bị tỉa reachability | 0 |
| E8 | Thứ tự tài liệu | Tỉ lệ cạnh vàng ngược thứ tự provenance và ngược viện dẫn; hiệu chỉnh mức trừ | 0 |

**Luật viết trước:**

- **Chọn bộ sinh mặc định:** như D5.
- **Đổi mặc định sang kiểm cặp** chỉ khi kiểm cặp hơn trích mở **≥ 0,05 F1**, khoảng tin cậy của hiệu **không
  chứa 0**, và recall không thấp hơn. Ngoài ra giữ trích mở, báo cáo ghi số của cả hai.
- **Mọi chỉ số kèm khoảng tin cậy 95%**, bootstrap lấy mẫu lại theo khái niệm đích. Khoảng chồng lấn thì viết
  "chưa phân biệt được", không viết "tốt hơn".
- **Tách dev và test:** hai chương vàng chạy **một lần**. Mọi prompt, ngưỡng và luật đóng băng trước khi mở vàng.
  Thay đổi nào sau khi thấy số đều phải ghi rõ là **sau khi thấy số** và báo cáo tách riêng.

### D15 — Cấu hình, chi phí, tái lập

- Mọi khâu LLM dùng `gemini-3.1-flash-lite`, `temperature` 0. Không chạy mô hình mạnh hơn trừ khi chủ dự án yêu cầu.
- Embedding: `gemini-embedding-001`. Đợt này thêm hai lượt embed — mô tả node kiểu `SEMANTIC_SIMILARITY` cho A6,
  và mô tả node kiểu `RETRIEVAL_QUERY` cho kênh dense. Cả hai đã được chủ dự án duyệt; chi phí không đáng kể.
- **Trần chi phí cho cả giai đoạn: 50 USD.** Mỗi lượt chạy in số lời gọi và chi phí cộng dồn; sắp chạm trần thì
  dừng và hỏi.
- Tái lập: cache theo hash đầu vào như A4; chạy lại khi chặn mạng phải cho `reused=true` và 0 lời gọi; ba lượt
  chạy đo Jaccard cạnh. Lưu ý sẵn trong báo cáo: `temperature` 0 **không** bảo đảm tất định ở mọi hạ tầng, dù
  A4 đã đạt 217/217 quyết định giống hệt qua ba lượt.

### D17 — Phụ thuộc mới và đường lui *(kiểm trên môi trường hiện tại, 2026-09-16)*

| Cần gì | Hiện trạng | Quyết định |
|---|---|---|
| Thư viện Leiden có ràng buộc cỡ cộng đồng (D3) | **chưa có** trong môi trường; A4 đang dùng Louvain của `networkx` | Thêm phụ thuộc, cài một lần khi có mạng. **Đường lui nếu không cài được:** giữ Louvain của `networkx` cộng một lượt chẻ tất định theo trần, và manifest phải ghi rõ hàm mục tiêu là modularity cùng cảnh báo ở D3 |
| Khớp nhiều mẫu cho kênh exact (D4) | thư viện Aho-Corasick **chưa có** | **Tự cài trong module luật thuần**, không thêm phụ thuộc nhị phân: bảng mẫu chỉ vài trăm tên, và tự cài thì kiểm được luật khớp dài nhất, bỏ khớp lồng, bỏ ký hiệu |
| Vector chunk cho kênh dense (D4) | **đã có sẵn** trong artifact truy hồi: 768 chiều, kiểu `RETRIEVAL_DOCUMENT` | Dùng lại, không embed lại chunk. Chỉ phía node là lượt embedding mới |
| Sinh và đọc file Excel (D13) | `openpyxl` **đã có** trong môi trường, do docling kéo vào | Khai thành phụ thuộc trực tiếp thay vì dựa vào phụ thuộc bắc cầu |
| Tính toán ma trận cho kênh dense | `numpy` **đã có** | Dùng lại |

Mọi phụ thuộc mới phải cài được một lần rồi chạy được khi **chặn mạng**, vì toàn bộ test và mọi bước nghiệm thu
chạy ở chế độ chặn mạng.

### D16 — ADR và tài liệu đi kèm

- **ADR 0008 — 2b: pass chính trích mở, pass phụ kiểm cặp, không tool.** Ghi rõ đánh đổi: văn liệu cho thấy trích
  mở rải thừa quan hệ tiên quyết còn kiểm cặp thì precision cao recall thấp; dự án chọn trích mở cho pass chính
  và **đo lại lựa chọn đó** bằng E6.
- **ADR 0009 — Bộ vàng tiên quyết bám văn bản.** Gán mù theo PREAP, hai người, hội ý, chỉ dùng để kiểm. Khác các
  bộ vàng tiên quyết phổ biến, và đổi ý thì phải gán lại từ đầu.
- `spec-addendum.md`: A6, A7, A8 và Tầng 2b trỏ sang spec này; ghi rõ ba chỗ spec này **sửa** addendum (ngưỡng
  cosine ở §451 (A6, kênh similarity), luật trần cụm ở §467–§468, luật "dưới 50 trang" ở §738 (Tầng 2b, tài liệu ngắn)) và một chỗ spec này **hẹp hơn** (§494 (A8, loại cạnh mở):
  2b không sinh kiểu cạnh mới).
- `CONTEXT.md` đã cập nhật trong phiên grilling: provenance, mention, cặp chạm, viện dẫn, cặp nghi tiên quyết,
  định tuyến, pass chính, pass phụ, khái niệm đích.
- Sau lượt chạy thật: một báo cáo luồng chi tiết cho 2b, theo mẫu `report/luong-chi-tiet-agent-2a.md`.

---

## Testing Decisions

**Test tốt ở dự án này là gì.** Test kiểm **hành vi nhìn thấy được từ bên ngoài một seam**: artifact sinh ra,
quyết định code đưa ra, lỗi code trả về. Không kiểm cấu trúc nội bộ, không kiểm số lần gọi hàm riêng. Mọi test
chạy **khi chặn mạng**, không ghi lại fixture, và không phụ thuộc thứ tự chạy. Một test chỉ được nhận khi nó
**đỏ lúc phá đúng thứ nó giữ** — đợt trước nhận 13 đột biến, đợt này cũng vậy.

**Seam ① — use case A6→A10 trên fixture (seam chính, mới).**

- Dựng store JSON trên thư mục tạm từ fixture, `ReplayEmbedding` cho vector, `FakeModel` cho hai loại phiên —
  đúng khuôn của test A4 hiện có.
- Kiểm: bốn stage sinh đúng thứ tự và dừng đúng chỗ khi được yêu cầu; dừng ở `mentions` thì `FakeModel`
  **không nhận lời gọi nào**; chạy lại không đổi gì thì `reused=true` và 0 lời gọi; đổi tham số A6/A7/M hay đổi
  `embedding_model_id` thì sinh phiên bản mới; checkpoint cho phép chạy tiếp sau khi hỏng giữa chừng.
- Kiểm hành vi đầu ra: mọi node có `cluster_id`; không cụm nào vượt trần đếm theo khái niệm; media không bao giờ
  là đầu của `requires`; cạnh nào cũng có chunk bằng chứng nhắc cả hai đầu; cạnh thừa được đánh dấu chứ không
  biến mất; node chưa từng được xét thì bị báo, không lặng lẽ vào tầng 1.

**Seam ② — module luật thuần (kiểu `canonical_decisions`).**

- Khớp mention: khớp dài nhất bên trái, bỏ khớp lồng, **không bỏ dấu**, bỏ qua ký hiệu.
- Dựng viện dẫn, cặp chạm, sổ cặp cụm: trọng số hạ theo số khái niệm trong chunk; hai bộ đếm tách rời; ngưỡng
  tương đối.
- Kiểm từng thao tác của executor: đủ bảy luật ở D9, mỗi luật một test.
- Quy `evidence_kind` ra confidence; `suy_doan` bị từ chối; `order_relation` tính từ provenance.
- Giải chu trình theo thành phần liên thông mạnh, đúng thứ tự ưu tiên giữ cạnh; chu trình hai cạnh ra cờ danh
  tính chứ không cắt.
- Đánh dấu cạnh thừa, xếp tầng Kahn, cắt stage theo trần.

**Seam ③ — fixture hợp đồng LLM (đã có, kiểu `test_a4_llm_contract`).**

- Ghi một phiên pass chính và một phiên pass phụ trên tài liệu thật, rồi phát lại offline. Fixture chốt **hợp
  đồng**: schema, khoá, và việc `prompt_hash` tính từ prompt sản phẩm chứ không lấy từ fixture.
- Đổi prompt là đổi hành vi: phải ghi lại fixture, chạy lại, và chấm theo luật viết trước — đúng quy ước trong
  `prompts/README.md`.

**Seam ④ — bộ vàng và chấm (kiểu `a4_gold`).**

- Sinh file Excel từ artifact: đủ sheet, danh sách chọn đúng phạm vi (đích là khái niệm của chương, đầu kia là
  mọi khái niệm), **không rò rỉ cạnh nào của pipeline**, ô phiên bản artifact đúng.
- Đọc ngược file Excel: bắt được cạnh trỏ tới khái niệm không tồn tại, cặp trùng, cạnh tự nối, và file gán cho
  phiên bản artifact khác.
- Chấm: P/R/F1 trên cạnh trực tiếp và trên bao đóng; sáu loại vị trí của E1; recall theo bộ sinh và recall riêng
  của E2; bootstrap cho khoảng tin cậy trên một ví dụ dựng sẵn.

**Kiểm thử tích hợp có sẵn phải tiếp tục xanh:** toàn bộ 299 test hiện tại, và fixture A3/A4 không được ghi lại.

## Out of Scope

- **Pha B** — tutor, quiz, mở khoá, adaptive. Chỉ chuẩn bị `stage_id` trên chunk cho nó.
- **Ứng dụng tương tác.** Đợt này chỉ có trang xem tĩnh sinh từ artifact.
- **Đo lại A4 bằng bộ vàng mới trên tài liệu dài.** Chỉ dùng cờ node sai thu được trong lúc duyệt khái niệm.
- **F83** (lượt thử lại của 2a tách cả node) và **hai kiểu gộp sai hệ thống** của 2a. Để sau mốc, cần nhãn mới.
- **Mô hình mạnh hơn flash-lite.**
- **Khử nhập nhằng mention bằng embedding câu** — chỉ là một ablation của E5 nếu còn thời gian.
- **Tự giàu alias** — 2b được ghi đề xuất alias, nhưng không nạp lại vào kênh exact trong cùng lượt chạy, và phải
  qua duyệt. Bootstrapping không kiểm soát là đường dẫn tới trôi ngữ nghĩa.
- **Bộ vàng cho tài liệu phẳng.**
- **Đồ thị nhiều tài liệu.** Mọi thứ trong đợt này ở phạm vi một `doc_id`.
- **Tuyên bố cơ chế mới.** Báo cáo tuyên bố tổ hợp, phép đo và bộ dữ liệu; không tuyên bố phân nhánh hay mention
  map là cơ chế chưa ai có.

## Further Notes

- **Chất lượng đứng trên hạn chót.** Mốc là 2026-10-03 và chủ dự án đã nói sẽ dời nếu cần. Không cắt phương pháp
  — nhãn vàng người gán, luật viết trước, tách dev/test, khoảng tin cậy, ablation — để kịp lịch.
- **Đường găng là việc gán nhãn**, không phải code. Vì vậy công cụ gán nhãn và hướng dẫn phải xong trước phần
  chấm, và file Excel chỉ phụ thuộc stage `clusters` chứ không chờ 2b.
- **Chia việc:** Claude làm spec, ADR, hướng dẫn gán nhãn, bộ sinh file Excel, bộ chấm E1/E2 và review. Nhân viên
  làm A6/A7, mention map, 2b, A9/A10 và trang xem.
- **Thứ tự đáng làm trước:** E1 và E2 không tốn lời gọi mô hình nào mà trả lời được hai câu quyết định — mention
  map có đáng làm không, và pass phụ có đáng chạy không.
- **Điều gì sẽ chứng minh thiết kế này sai:** nếu E1 cho thấy gần hết cạnh tiên quyết nằm trong cùng một chương
  thì pass phụ của nhánh chương gần như vô ích; nếu E2 cho thấy chỉ riêng trục chương đã giữ gần hết cạnh vàng
  thì mention map chỉ còn là tiện ích; nếu E4 cho thấy mô hình khẳng định phần lớn cạnh mà không cần đọc văn bản
  thì mọi con số P/R phải đọc lại theo hướng khác. Cả ba khả năng đều là kết quả hợp lệ để báo cáo.
- **Nguồn của từng chỗ sửa spec** nằm trong báo cáo nghiên cứu, mục 5.2, mỗi dòng một công trình hoặc một đoạn
  mã nguồn.
