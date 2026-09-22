# Spec: A3 / A3' — Trích thực thể và nhánh chỉ mục vector

**Trạng thái:** ready-for-agent
**Nguồn:** phiên grilling 5 vòng · 31 quyết định (Q1–Q31)
**Nghiên cứu nền:** [`report/nghien-cuu-a3-trich-xuat-thuc-the.md`](../report/nghien-cuu-a3-trich-xuat-thuc-the.md)
**Chi phối bởi:** `spec-addendum.md` §0.1 (hệ kiểu mở) · ADR 0001 (định danh tất định) · ADR 0002
(tham chiếu ngoài khoá băm) · ADR 0003 (tin dữ liệu khai báo)

---

## Problem Statement

B0 đã xong: bốn tài liệu ra **116 section có nội dung, 233 chunk, 48.694 token**, cộng 19 hình, 60 bảng,
258 công thức đều có định danh băm nội dung và vị trí ký tự. Nhưng đó vẫn là **văn bản phẳng có cấu
trúc** — chưa có khái niệm, chưa có quan hệ, chưa có gì để dựng lộ trình học.

Người dùng cần bước biến văn bản thành **thực thể có nguồn gốc kiểm chứng được**. Ba khó khăn cụ thể:

1. **Recall của bước này là trần cứng cho toàn bộ lộ trình.** Khái niệm bỏ sót ở đây không bao giờ
   xuất hiện lại — bước merge chỉ gộp cái đã có, bước suy luận cạnh chỉ nối cái đã có.
2. **Không có phép đo nào.** Vòng review 11 và 12 đều kết luận: dự án có kỷ luật hiếm thấy ở B0
   (25 bất biến, số vàng bốn tài liệu) nhưng chưa có một con số nào nói chất lượng trích xuất ra sao.
   Để A3 chạy không thước đo là bước lùi so với chính mình.
3. **Tầng này không thể tất định.** Bốn LLM cùng một corpus cho đồ thị chồng lấn **6–11%**. Dự án vừa
   dựng cả kiến trúc tất định cho B0 rồi sẽ đặt lên trên nó một tầng mà đổi mô hình là đổi hai phần ba
   nội dung.

## Solution

Một bước A3 chạy **theo section**, mỗi section một hội thoại ba giai đoạn — trích, quét lại, kiểm định —
sinh ra thực thể **đa kiểu** kèm bằng chứng **được code xác minh**, không phải kèm lời hứa của mô hình.
Song song, A3' dựng chỉ mục vector và BM25 mà không chờ A3 một giây nào.

Từ góc nhìn người dùng, sau đợt này:

- Ingest một giáo trình ra **bảng ứng viên thực thể** với mỗi mục có câu bằng chứng **định vị được**
  trong chunk nguồn — mở ra là tra lại được, không phải tin.
- Thực thể **không chỉ có khái niệm**: hình và bảng thành node, và mô hình được tự đặt kiểu mới
  (`theorem`, `algorithm`, `definition`…) khi thấy cần.
- **Đo được chất lượng**: mật độ trích, tỉ lệ có bằng chứng, độ ổn định giữa hai lần chạy — thay vì
  đoán.
- **Chạy lại rẻ**: đổi prompt suy luận cạnh không phải trích lại 116 section; ba tầng artifact đóng
  băng độc lập, đúng khuôn `parse_tree` / `chunks` của B0.
- **Hỏng thì kêu**: quá 40% section trích ra rỗng thì dừng; section lỗi dai dẳng thì chặn không cho
  đóng băng artifact thủng.

## User Stories

1. Là **người dựng lộ trình**, tôi muốn mỗi khái niệm trích ra có câu bằng chứng định vị được trong
   chunk nguồn, để mở ra tra lại được thay vì phải tin mô hình.
2. Là **người dựng lộ trình**, tôi muốn khái niệm bịa bị loại tự động bằng code, để đồ thị không có
   node không tồn tại trong tài liệu.
3. Là **người dựng lộ trình**, tôi muốn bước trích quét lại nhiều lượt, để khái niệm nằm giữa đoạn
   không bị bỏ sót ngay từ đầu chuỗi.
4. Là **người dựng lộ trình**, tôi muốn bước quét lại dừng khi không còn gì mới, để mô hình không bị ép
   sản xuất thêm bằng cách bịa.
5. Là **người vận hành**, tôi muốn thấy số node mới theo từng vòng quét lại, để nhận ra khi mô hình
   đang bịa (chuỗi phẳng hoặc tăng) thay vì đang nhớ ra (chuỗi giảm dần).
6. Là **người dựng lộ trình**, tôi muốn một lượt kiểm định riêng soát cả khái niệm lẫn cạnh đề xuất,
   để loại thứ chỉ được *nhắc* khỏi thứ thật sự được *giảng*.
7. Là **người hiệu chỉnh prompt**, tôi muốn đo được mật độ node học được trên 1000 token, để biết prompt
   đang trích thô hay mịn thay vì đoán.
8. Là **người hiệu chỉnh prompt**, tôi muốn ví dụ few-shot nằm trong khoá băm artifact, để sửa ví dụ là
   artifact cũ bị vô hiệu chứ không bị tái dùng im lặng.
9. Là **người trích xuất**, tôi muốn mô hình tự đặt kiểu node mới, để đồ thị giàu hơn danh sách kiểu tôi
   nghĩ ra được lúc viết spec.
10. Là **người trích xuất**, tôi muốn kiểu node mới được ghi vào sổ đăng ký kèm số lần dùng, để kiểu lạ
    xuất hiện một lần được soi còn kiểu dùng nhiều được công nhận.
11. Là **người trích xuất**, tôi muốn hình và bảng thành node lấy thẳng từ tham chiếu B0, để đường media
    tất định thay vì phụ thuộc mô hình có nhận ra hay không.
12. Là **người trích xuất**, tôi muốn ảnh được đưa thẳng vào prompt cùng văn bản, để mô hình nhìn và đọc
    đồng thời thay vì mô tả mù rồi mới kiểm.
13. Là **người trích xuất**, tôi muốn prompt hỏi *cái nhìn thấy được* trong ảnh, để mô hình không chép
    lại văn bản xung quanh rồi gọi đó là mô tả ảnh.
14. Là **người trích xuất tài liệu toán**, tôi muốn nội dung thô công thức có mặt trong ngữ cảnh trích,
    để 66% chunk có lỗ công thức vẫn đọc được ý.
15. Là **mô hình embedding**, tôi muốn nội dung thô công thức **không** vào văn bản chunk, để 28% cháo
    chữ không nhiễm vào vector.
16. Là **người trích xuất**, tôi muốn lời gọi nhận tiêu đề tổ tiên nhưng **không** nhận nội dung section
    lân cận, để mô hình không trích câu bằng chứng từ nơi code không dò tới.
17. Là **người đọc đồ thị**, tôi muốn tên khái niệm giữ dạng phổ biến nhất trong tài liệu và alias gom cả
    hai ngôn ngữ, để người đọc sách tiếng Việt không bị hiện thuật ngữ Anh trần trụi.
18. Là **người dựng đồ thị**, tôi muốn alias chỉ được nhận khi có mặt trong văn bản, để không sinh viết
    tắt tự động đụng nghĩa với thứ khác.
19. Là **người dựng lộ trình**, tôi muốn gọi độ sâu trong DAG là **độ sâu tiên quyết**, không suy ra
    độ khó nhận thức của người học từ đại lượng cấu trúc này.
20. Là **người vận hành**, tôi muốn section trích ra rỗng có cảnh báo, để phân biệt mục thủ tục với lỗi
    prompt.
21. Là **người vận hành**, tôi muốn pipeline dừng khi quá 40% section rỗng, để không chạy hết 116 section
    rồi mới biết prompt hỏng.
22. Là **người vận hành**, tôi muốn section gọi lỗi được thử lại ở cuối, để lỗi mạng thoáng qua không
    thành lỗ hổng vĩnh viễn.
23. Là **người vận hành**, tôi muốn artifact **không được đóng băng** khi còn section lỗi, để lần chạy
    sau không tái dùng bản thủng mà không ai biết.
24. Là **người chỉnh prompt suy luận cạnh**, tôi muốn không phải trích lại 116 section, để vòng lặp thử
    nghiệm tính bằng phút chứ không phải bằng giờ.
25. Là **người review**, tôi muốn ba tầng artifact có phiên bản độc lập, để nhìn diff là biết tầng nào đổi.
26. Là **người review**, tôi muốn manifest ghi mô hình nào sinh ra đồ thị này, để đồ thị của hai mô hình
    khác nhau không bị nhầm là một.
27. Là **người review**, tôi muốn đo Jaccard giữa hai lần chạy, để biết tầng này ổn định tới đâu thay vì
    giả định nó ổn định.
28. Là **người review**, tôi muốn khoá so Jaccard là tên chuẩn hoá cộng giao alias, để phép đo không dùng
    chính embedding đang bị nghi ngờ mà làm đẹp số.
29. Là **người chấm chất lượng**, tôi muốn bộ vàng gán mù trên hai chương thuộc hai thể loại, để đo được
    recall thật thay vì đo lại chính output.
30. Là **người chấm chất lượng**, tôi muốn section dùng để hiệu chỉnh độ hạt bị loại khỏi bộ chấm, để một
    mẫu không đóng hai vai.
31. Là **người dùng gia sư ở pha B**, tôi muốn chunk được embed kèm tiền tố đường dẫn section, để truy hồi
    biết đoạn này thuộc chương nào.
32. Là **người bảo trì**, tôi muốn tiền tố ghép ở thời điểm embed chứ không vào `text`, để định danh chunk
    không đổi và quyết định này đảo ngược được.
33. Là **người dùng gia sư**, tôi muốn truy hồi lai vector và BM25, để hỏi `P(A|B)` hay `sync.Mutex` không
    bị trượt.
34. Là **người bảo trì**, tôi muốn một cổng embedding duy nhất gọi từ bốn chỗ, để ghim phiên bản mô hình
    một nơi.
35. Là **người bảo trì**, tôi muốn hiểu rằng đổi mô hình embedding là đổi **tập node** chứ không chỉ đổi
    chất lượng tìm kiếm, để không đổi nó tuỳ tiện.
36. Là **người phát triển**, tôi muốn phản hồi mô hình được ghi lại thành fixture, để bộ test chạy trong
    vài giây và không tốn tiền mỗi lần chạy.
37. Là **người phát triển**, tôi muốn bộ test không bao giờ gọi mạng thật, để kết quả không đổi theo
    ngày và không phụ thuộc hạn mức API.
38. Là **người vận hành**, tôi muốn A3' chạy song song hoàn toàn với A3, để nhánh vector không chờ nhánh
    đồ thị.
39. Là **người vận hành**, tôi muốn API key đọc từ biến môi trường và không bao giờ vào repo, để một
    lần lỡ commit không thành sự cố.

## Implementation Decisions

### D1 — Đơn vị và luồng ba giai đoạn *(Q2a, Q3c, Q11c, Q22c, Q30b)*

**Một section = một hội thoại**, ba giai đoạn trong cùng ngữ cảnh:

```
1. TRÍCH      -> node (đa kiểu) + cạnh đề xuất, mỗi thứ kèm CÂU TRÍCH nguyên văn
2. QUÉT LẠI   -> "còn gì chưa liệt kê?"
                 dừng khi một vòng thêm 0 node mới · trần 5 vòng
                 prompt nêu rõ "không còn gì" là câu trả lời tốt và được chờ đợi
3. KIỂM ĐỊNH  -> theo lô, soát CẢ node LẪN cạnh: được giảng, hay chỉ được nhắc?
```

Không dùng "hỏi mô hình đã hết chưa" làm điều kiện dừng — **đếm node mới là tín hiệu khách quan**,
không phụ thuộc mô hình tự đánh giá. Ghi **chuỗi node-mới-mỗi-vòng** vào thống kê, không chỉ ghi tổng:
giảm dần (`5→2→0`) là lành mạnh; phẳng hoặc tăng (`3→3→4`) là dấu mô hình sản xuất để làm vừa lòng.

Section không dùng ngưỡng kích thước để bỏ quét lại — kích thước không phải đại diện cho độ giàu.

### D2 — Ngữ cảnh của một lời gọi *(Q27b, Q28b, Q15)*

| Thành phần | Vào ngữ cảnh? | Vào `text` chunk? | Vào embedding? |
|---|:---:|:---:|:---:|
| `section_path` (tiêu đề tổ tiên) | ✅ | ❌ | ✅ (ghép lúc embed) |
| Văn bản chunk của section | ✅ | — | ✅ |
| Nội dung section **lân cận** | ❌ | ❌ | ❌ |
| **Ảnh** của section | ✅ (đa phương thức) | ❌ | ❌ |
| **Nội dung thô công thức** | ✅ | ❌ | ❌ |

Loại section lân cận không phải để tiết kiệm — nó **xung đột với luật bằng chứng D3**: mô hình thấy
văn bản bên cạnh sẽ trích câu từ đó, mà code chỉ dò trong chunk của section này, nên khái niệm bị loại
oan. Ngữ cảnh tổ tiên là **tiêu đề**, không tạo nguồn trích dẫn giả.

Nội dung thô công thức lộn xộn thứ tự (`'X x1 x2 . . . xk ni n1 n2 . . . nk'`) nhưng đọc cùng văn bản
xung quanh thì nhận ra được — **66% chunk của tài liệu thống kê có lỗ công thức**, để trống là đọc
văn bản thủng.

### D3 — Bằng chứng: mô hình chép, code xác minh *(Q4c, Q12b)*

Áp cho **node, cạnh và alias** — không riêng cạnh như bản spec cũ.

```
LLM chép câu nguyên văn
  -> code chuẩn hoá bằng ĐÚNG bộ chuẩn hoá B0 (NFC · gộp khoảng trắng · bỏ phân biệt hoa thường)
  -> dò trong chunk nguồn
  -> thấy: tính span, lưu cùng node
  -> không thấy: LOẠI, đếm vào thống kê
```

**Không so mờ.** So mờ mở cửa cho ảo giác một phần — mô hình bịa một câu na ná câu thật vẫn lọt, mà
đó đúng là thứ luật này sinh ra để chặn. Tỉ lệ bị loại cao là tín hiệu prompt hỏng, đáng biết.

Đây là mở rộng của bất biến I9 ở B0 (`normalized_full_text[span] == chunk.text`) từ chunk sang node.

### D4 — Hệ kiểu mở, mồi bằng ví dụ *(Q13b)*

Prompt mồi **5–6 kiểu mẫu** (`concept`, `theorem`, `algorithm`, `definition`, `metric`, `method`) và nói rõ
**được đặt kiểu mới**. Không đưa danh sách đóng.

Mỗi entity bắt buộc trả `learnable`: `true` khi người học phải học và hoàn thành node, `false` khi node
chỉ là bối cảnh. `dataset` không nằm trong danh sách mồi vì thường là bối cảnh; artifact cũ thiếu trường
vẫn đọc theo mặc định bảo toàn recall là `true`.

Trong một `node_type`, cờ được bỏ phiếu theo số ứng viên; hoà mới ưu tiên `true`. Cùng tên chuẩn hoá có
nhiều kiểu mà cờ trái nhau phải sinh warning, không tự giải quyết ở A3. Tầng 2a chọn kiểu canonical
tường minh theo luật merge rồi mới chốt lại `learnable`.

`edge_type` cũng là hệ mở. Prompt mồi `example_of`, `contrasts_with`, `component_of`, `computed_by`,
`uses`; riêng quan hệ tiên quyết phải dùng đúng tên `requires`. Báo cáo tách số loại cạnh có evidence do
LLM sinh khỏi `illustrates`/`tabulates` tất định do code sinh.

`figure` và `table` là **tên dành riêng do code giữ** — ứng viên media sinh từ `image_refs`/`table_refs`
của B0, LLM không đụng tới. Công thức **không** thành node ở vòng này (258 cái, nội dung lộn xộn).

Chỉ số canh bùng nổ kiểu: **số kiểu phân biệt / số node**.

### D5 — Tên và alias *(Q6c, Q29c)*

- Tên chuẩn = **tên gọi đầy đủ xuất hiện nhiều nhất trong văn bản tài liệu**, chọn **trong tên của các ứng
  viên** thuộc node; alias gom cả hai ngôn ngữ nhưng không tranh làm tên chuẩn; viết tắt chỉ làm tên khi không
  còn tên gọi nào; ký hiệu không bao giờ. *(Sửa 2026-09-11 theo spec A4/A5 D6: áp nguyên văn luật cũ thì `x`
  (325 lần) thành tên của "Trung bình mẫu", `α` thành tên của "Mức ý nghĩa". Cách đếm không chồng lấn và luật hoà:
  xem D6 spec A4/A5, sửa theo F73.)*
- **Ký hiệu không phải alias**: `μ`, `x`, `t α`, `P(A|B)` không dùng để gộp hay khớp tên (`CONTEXT.md`). Đợt A4 tự
  phân loại chúng bằng code; tách thành trường riêng khi A3 trích lại.
- Alias đến từ **cả hai nguồn**: LLM đề xuất lúc trích, và hợp nhất tên khi merge ở 2a.
- LLM chỉ được đề xuất alias **có mặt trong văn bản** — cùng kỷ luật bằng chứng D3.
- **Cấm tự sinh viết tắt.** `NB` suy từ *Naive Bayes* sẽ đụng với mọi thứ viết tắt `NB` khác; chỉ nhận
  viết tắt khi tài liệu thật sự dùng.

Lý do alias phải có nguồn LLM chứ không chỉ nguồn merge: alias xuất hiện **cùng câu** với tên chính
(*"quá khớp (overfitting)"*) không bao giờ thành hai ứng viên riêng để merge phát hiện.

### D6 — Bỏ `difficulty` *(Q14b)*

Trường `difficulty` do LLM ước lượng **biến khỏi schema**. Độ khó tính từ **độ sâu trong DAG** sau A10 —
thứ cần 5 tiên quyết thì khó hơn thứ cần 0. Tất định, miễn phí, và không trôi khi đổi mô hình.

### D7 — Ảnh đi thẳng vào prompt *(Q15)*

Không có bước "mô tả ảnh" riêng. Ảnh của section đính kèm ngay trong lời gọi trích.

- **10% section mang ảnh** (13/129) nên chi phí thêm là nhỏ.
- Neo ngữ cảnh xảy ra **trong lúc** mô tả, không phải kiểm sau — chặt hơn mô tả mù rồi lọc.
- Cho phép trích khái niệm **hình dạy mà văn bản không nói** — thứ đường tách hai bước không moi được.
- **Ảnh có chú thích vẫn đưa vào**: chú thích làm `description`, nhưng ảnh vẫn phải có mặt vì nó có thể
  dạy thứ chú thích không nói. 8/19 hình có chú thích, 11 không.
- Mỗi media ref đi vào prompt kèm `media_id`, `chunk_id`, `char_start` và tình trạng caption; không dựa
  vào dấu `[figure]` vì ảnh có caption dùng chính caption thay dấu.
- Cùng lượt trích, mô hình trả tập con thực thể mà media thật sự minh họa. Code chỉ gắn
  `confirmed: true` lên cạnh đồng-vị-trí đã có; tập rỗng/một/nhiều đều hợp lệ và không tạo/xóa cạnh.
- Khái niệm chỉ có trong ảnh dùng `media_evidence_id` đã đính kèm làm provenance; ID không thuộc section
  bị code loại như evidence văn bản không khớp.

**Chốt chặn bắt buộc:** prompt hỏi **cái nhìn thấy được** (trục ghi gì, mấy đường, nhãn nào, hình dạng
ra sao), **không** hỏi ý nghĩa — chống mô hình chép lại văn bản xung quanh rồi gọi là mô tả ảnh.

`caption_source` ∈ `original` · `generated_multimodal` · `generated_from_content` · `none`, trong đó
`none` là trạng thái hỏng phải đếm, retry và chặn đóng băng nếu còn tồn tại.

**Hệ quả:** mô hình trích phải là mô hình đa phương thức.

### D8 — Vòng đời mô tả và bốn thời điểm embed *(Q16c, Q18b, Q26b, Q8b)*

```
B0 chunk sẵn sàng
   ├─► ① EMBED CHUNK (233) + dựng BM25        A3' — song song, không chờ ai
   └─► A3 trích, 116 section song song
            │
       ═══ HÀNG RÀO: chờ đủ toàn tài liệu ═══
            ├─► ② EMBED description_draft  (chưa bước nào dùng — xem ghi chú dưới)
            ├─► ⑤ EMBED tên, do A4 tự tính  ──► đồ thị đề cử 2a ──► merge
            └─► ③ EMBED mô tả media
                     └─► A5 mô tả chuẩn ──► ④ EMBED description
                              └─► cạnh A6 · cluster A7 · mention map · tra cứu pha B
```

- **Node học được ⇒ hai bản mô tả**: nháp ở tầng `candidates`, chuẩn ở tầng `canonical`. Phân tầng
  artifact tự nó là chỗ chứa đúng cho hai bản — không ghi đè, không mất dấu.
- **Node media ⇒ một bản, chốt tại A3.** Không qua A5: cho A5 viết lại nghĩa là để mô hình suy diễn về
  nội dung ảnh từ văn bản xung quanh, đúng ảo giác D7 sinh ra để chặn.
- **Hàng rào không tránh được**: 2a gom cụm trên pool ứng viên **toàn tài liệu**, nên chưa trích hết thì
  chưa biết khái niệm ở chương 3 có bạn ở chương 8 hay không.
- **Một cổng embedding duy nhất**, gọi từ bốn chỗ. Ghim `embedding_model_id` một nơi.
- **Ngữ cảnh khi embed**: ghép `section_path` **ở thời điểm embed**, `text` giữ nguyên ⇒ băm không đổi,
  quyết định **đảo ngược được**.
- **Không** embed cạnh (không phải đích truy hồi). Cluster dùng centroid. Stage embed ở A11.

> **Hệ quả phải ghi vào ADR:** embedding quyết định **blocking merge**, nên đổi mô hình embedding là
> **đổi tập node** — cặp nào lọt vào cùng cụm đổi ⇒ merge đổi ⇒ cluster đổi ⇒ mention map đổi. Bán kính
> rộng hơn nhiều so với "tìm kiếm hơi khác".
>
> *Cập nhật 2026-09-11:* đã ghi thành ADR 0004. Theo ADR 0006, vector đề cử cặp nghi trùng giờ là **vector tên**
> do A4 tự embed (⑤); vector `description_draft` (②) đo *"được nhắc trong bối cảnh nào"* chứ không đo *"là cái
> gì"* — 31 cặp khác tên đạt cosine ≥ 0,999 vì chung một câu mô tả — nên hiện chưa bước nào dùng nó.

### D9 — Truy hồi lai *(Q7a, Q21a)*

- Mô hình embedding: **Gemini**. Chấp nhận mất late chunking vĩnh viễn (đòi truy cập tầng token); ghi
  là đường nâng cấp, mở lại khi bộ vàng đo thấy truy hồi tiếng Việt yếu.
- **BM25 có**, dùng `tsvector` mặc định (`simple`), **không** thêm bộ tách từ tiếng Việt. Lý do BM25 được
  thêm là bù cho vector ở **thuật ngữ chính xác, ký hiệu, tên riêng** — `Naïve Bayes`, `P(A|B)`,
  `sync.Mutex` — những thứ khớp nguyên chuỗi, không cần tách từ. Thêm phụ thuộc mang tên ngôn ngữ là
  đúng thứ dự án đã bác ba lần ở B0.

### D10 — Ba tầng artifact và `prompt_hash` *(Q20c, Q23c)*

```
candidates/{doc}/v{n}   <- đổi prompt trích       ⇒ chỉ nhích tầng này
canonical/{doc}/v{n}    <- đổi ngưỡng merge       ⇒ chỉ nhích tầng này
graph/{doc}/v{n}        <- đổi prompt suy cạnh    ⇒ chỉ nhích tầng này
```

`prompt_hash` gồm: template + **ví dụ few-shot** + `model_id` + tham số sinh + định nghĩa schema +
danh sách kiểu mồi.

Ví dụ few-shot **bắt buộc** phải vào hash — chúng là **núm vặn độ hạt** (D11). Sửa ví dụ mà hash không
thấy thì artifact cũ được tái dùng im lặng và người sửa tưởng ví dụ không có tác dụng. Đây đúng bài học
`adapter_version` mà B0 đã trả giá để học.

Các khối prompt là tệp UTF-8 cạnh module và được nạp lúc dựng use case. Scaffolding hướng dẫn dùng tiếng
Anh; đoạn corpus trong few-shot giữ nguyên tiếng Việt. Bộ few-shot có thể được chọn bằng
`DOC2ROADMAP_EXTRACTION_FEW_SHOT` hoặc `--few-shot`; hash băm **nội dung**, không băm đường dẫn.

Manifest ghi: `model_id`, `embedding_model_id`, `prompt_hash`, và **Jaccard so với lần chạy trước**.

### D11 — Độ hạt là thứ được **đo**, không phải thứ được **khai** *(Q1b)*

Không có tham số `granularity`. Núm vặn thật là **ví dụ few-shot**, và núm mạnh nhất là **ví dụ phủ
định** — ranh giới nằm ở ca biên, không ở ca rõ.

Núm này là dữ liệu vận hành, không phải mã nguồn: thay tệp few-shot rồi chạy lại cùng CLI để A/B. Không
thêm một tham số số học giả tạo cho độ hạt.

| Chỉ số | Thô | **Đích** | Mịn |
|---|---|---|---|
| Node `learnable` / 1000 token | 3–5 | **8–15** | 20+ |
| Trên corpus 48.694 token | 146–243 | **390–730** | 970+ |
| Trên mỗi section | 1–2 | **3–6** | 8+ |
| Tỉ lệ ứng viên có tên trùng xuyên section | cao | vừa | thấp |

Đếm phải **tách `learnable` khỏi tổng** — kiểu mở làm tổng phồng lên trông như mịn trong khi mật độ
khái niệm học được vẫn thô.

Chỉ số cuối dùng chuẩn hoá so node A3 (B0 + casefold + bỏ dấu câu) rồi đếm tỉ lệ ứng viên `learnable` có tên xuất hiện ở ít nhất hai
section. Nó là bóng đo được của tỉ lệ merge. `single_chunk_ratio` không đo ở A3 vì mỗi ứng viên trước
merge vốn chỉ có một chunk/section nguồn; chuyển chỉ số đó sang 2a sau khi hợp nhất provenance.

### D12 — Cổng chặn và chính sách lỗi *(Q19c, Q25c)*

| Tình huống | Hành động |
|---|---|
| Section trích ra 0 node | Cảnh báo `empty_extraction` kèm tên section, gom theo khuôn cảnh báo B0 |
| **> 40% section rỗng** | **Dừng pipeline** — prompt hỏng hoặc tài liệu không phải giáo trình |
| JSON hỏng | **1 lượt sửa** kèm thông báo lỗi cụ thể, đúng khuôn executor 2b |
| Lỗi mạng / giới hạn tần suất | Lùi theo cấp số nhân |
| Section lỗi dai dẳng | Thử lại ở **cuối**; vẫn lỗi ⇒ ghi `coverage_incomplete` và **CHẶN đóng băng artifact** |
| Hai thực thể khác tên cùng section có `description_draft` trùng từng chữ | Cảnh báo, không loại *(thêm 2026-09-11, spec A4/A5 D11)* |
| Câu bằng chứng không chứa tên, alias hay ký hiệu của thực thể | Cảnh báo, không loại *(thêm 2026-09-11, spec A4/A5 D11)* |

Hai cảnh báo cuối là hàm thuần trên artifact: A3 ghi khi chạy mới; `a3-report` và A4 tính trên artifact đã có,
nên thêm chúng **không** đổi `algorithm_id` và không phải trích lại.

Điều cuối là điểm mấu chốt: bỏ qua section lỗi rồi vẫn đóng băng nghĩa là lần chạy sau thấy hash khớp,
tái dùng bản thủng, **không ai biết**. Artifact có lỗ tệ hơn không có artifact.

### D13 — Đo độ ổn định *(Q9c, Q17b)*

Ghim `model_id` vào manifest ngang hàng `tokenizer_id` của B0, và đo **Jaccard giữa hai lần chạy**:

```
Jaccard(A,B) = |A ∩ B| / |A ∪ B|
```

**Khoá so: tên chuẩn hoá (thường hoá + bỏ dấu câu) cộng giao tập alias.** Không dùng embedding để khớp —
đó là dùng chính thứ đang bị nghi ngờ để chấm điểm sự ổn định, vòng luẩn quẩn làm đẹp số giả tạo.

Báo cáo **hai số riêng**: Jaccard node và Jaccard cạnh. Cạnh luôn thấp hơn nhiều vì sai lệch node nhân
lên ở cạnh.

### D14 — Bộ vàng *(Q10b, Q24b, Q31b)*

- **Phạm vi**: 1 chương `nhap-mon-ml` (văn xuôi) + 1 chương `xstk-ch3-1` (đặc công thức). Hai giáo trình
  là thể loại đích; DOCX và slide là ca biên. Trục văn-xuôi-vs-công-thức là trục quyết định độ hạt có
  chuyển giao được hay không.
- **Cách gán**: gán 1 section trước để hiệu chỉnh độ hạt → **section đó bị loại khỏi bộ chấm** → phần
  còn lại gán **mù** trước khi chạy A3.
- Gán mù là bắt buộc: sửa output thành bộ vàng thì đo recall trên thứ dẫn xuất từ chính output — vòng
  luẩn quẩn, con số đẹp một cách vô nghĩa.
- **Chỉ số**: recall node · tỉ lệ có bằng chứng · Jaccard hai lần chạy · tỉ lệ merge ở 2a · chuỗi
  node-mới-mỗi-vòng-quét-lại.

### D15 — Cổng và adapter mới

Theo đúng quy ước sẵn có (`application/ports/` cho cổng I/O có `identifier` và phiên bản;
`domain/ports.py` cho protocol thuần):

- **Cổng trích thực thể** — nhận ngữ cảnh section (văn bản, tiêu đề tổ tiên, ảnh, nội dung thô công
  thức), trả về các lượt hội thoại. Có `identifier` và `model_id`.
- **Cổng embedding** — một cổng duy nhất, có `identifier` và `embedding_model_id`.
- **Kho artifact mở rộng** — ba tầng mới `candidates` / `canonical` / `graph`, mỗi tầng có
  `find_*` và `save_*` theo khuôn `find_parse` / `find_chunks` đang có.
- **Logic thuần trong domain**: xác minh bằng chứng, luật dừng quét lại, chỉ số mật độ, cổng chặn,
  sổ đăng ký kiểu, phép tính Jaccard. Không cái nào cần mạng.

### D16 — Bí mật và cấu hình

API key đọc từ **biến môi trường**, nạp qua `Settings` như mọi cấu hình khác của dự án. `.env` đã nằm
trong `.gitignore` từ B0; `.env.example` được bổ sung **tên biến với giá trị rỗng**, không bao giờ chứa
giá trị thật.

Key **không vào** `prompt_hash`, không vào manifest, không vào log — chỉ `model_id` được ghi. Adapter
thiếu key thì báo lỗi rõ ràng ngay lúc dựng, **không** để lỗi nổ giữa chừng khi đã chạy 80 section.

## Testing Decisions

**Test tốt kiểm hành vi ngoài seam, không kiểm cách làm.** Không khẳng định gì về nội dung prompt hay
số lượt gọi — chỉ khẳng định: cho ngữ cảnh này vào, ra thực thể này với bằng chứng định vị được.

### Seam ① — Thuần domain

Gánh D3 (xác minh bằng chứng), D11 (chỉ số mật độ), D12 (cổng chặn), D13 (Jaccard), D4 (sổ đăng ký
kiểu), luật dừng quét lại của D1. Dựng đầu vào bằng tay, chạy mili-giây, tất định tuyệt đối.

**Prior art**: bộ test `chunk_document` hiện có — cùng hình dạng, cùng cách dựng fixture tay.

### Seam ② — Ghi–phát lại hội thoại LLM

Tái dùng đúng cơ chế B0 đã chứng minh: fixture Docling thay 220 giây parse bằng 0,11 giây phát lại.

Ghi **toàn bộ hội thoại** của một section — lượt trích, các lượt quét lại, lượt kiểm định — thành một
fixture, đặt cạnh `tests/fixtures/docling/`. Bản ghi là **nhật ký nhiều lượt có thứ tự**: phát lại phải
trả đúng lượt thứ n cho lời gọi thứ n, vì luật dừng quét lại phụ thuộc nội dung từng lượt.

Vô hiệu hoá khi `prompt_hash` đổi.

### Seam ③ — Ghi–phát lại vector embedding, **cơ chế riêng**

**Không dùng chung cơ chế với seam ②.** Hai bản ghi khác hình dạng về bản chất:

| | Seam ② LLM | Seam ③ Embedding |
|---|---|---|
| Hình dạng bản ghi | nhật ký hội thoại **có thứ tự**, payload JSON dài ngắn khác nhau | từ điển **văn bản → vector**, cùng số chiều |
| Tra cứu | theo lượt thứ n | theo băm của văn bản đầu vào |
| Trạng thái | có — lượt sau phụ thuộc lượt trước | không — thuần hàm |
| Vô hiệu hoá bởi | `prompt_hash` | `embedding_model_id` |
| Ai dùng | test A3 | test A3', **và test blocking/merge ở đợt sau** |

Ép chung một cơ chế buộc phía embedding mang theo trạng thái hội thoại nó không có, và buộc phía LLM
chấp nhận tra cứu theo băm đầu vào trong khi cùng một đầu vào ở hai lượt khác nhau phải cho hai kết quả
khác nhau. Hai cơ chế nhỏ rõ ràng hơn một cơ chế phải chiều cả hai.

Bản ghi embedding còn có một vai riêng: đợt merge cần **vector thật** để test đồ thị đề cử — một từ điển
văn bản→vector dùng lại được nguyên vẹn, còn nhật ký hội thoại thì không. *(Cập nhật 2026-09-11: đợt merge dùng
vector **tên** theo láng giềng gần nhất, không dùng ngưỡng 0,75/0,95 — spec A4/A5 D3.)*

**Prior art cho cả hai**: `tests/fixtures/docling/*.json` và `load_docling_fixture`.

### Bộ số vàng, mở rộng từ B0

Bộ số vàng bốn tài liệu hiện có ghim section/chunk/refs. Thêm cột cho A3 khi fixture phản hồi đã có:
số node theo kiểu, số node `learnable`, mật độ trên 1000 token, tỉ lệ có bằng chứng, số kiểu phân biệt.
Đổi số phải kèm giải thích trong cùng commit — luật đã có.

### Luật cứng: bộ test không gọi mạng

Mọi test chạy trên fixture đã ghi. Lời gọi thật chỉ xảy ra ở **hai chỗ tường minh**: kịch bản ghi
fixture, và lệnh ingest thật. Không test nào được phép gọi mạng — cùng lý do B0 tách seam adapter khỏi
seam thuần: test phụ thuộc mô hình vừa chậm, vừa tốn tiền, vừa đổi kết quả khi nhà cung cấp cập nhật, và
đúng lúc đó bộ test bảo vệ bất biến mất hết giá trị.

Ghi fixture nên là việc làm **sớm** — có key rồi thì ghi ngay ở ticket đầu, rồi mọi ticket sau chạy trên
bản ghi. Đây đúng thứ tự B0 đã dùng và trả lương.

## Out of Scope

- **A4/2a merge, A5 mô tả chuẩn, A6–A8 đồ thị**: spec này dừng ở **ứng viên đã kiểm định** và **chỉ mục
  vector**. D8 mô tả bốn thời điểm embed để thấy toàn cảnh, nhưng ② ④ thuộc đợt merge.
- **Cạnh `requires` thật sự vào đồ thị**: A3 chỉ **đề xuất**; executor 2b duyệt (`spec-addendum` §0.1).
- **Công thức thành node**: 258 cái, nội dung lộn xộn thứ tự. Giữ làm bằng chứng của khái niệm.
- **Ảnh cắt vùng công thức theo bbox**: đường leo nếu bộ vàng cho thấy khái niệm sót tập trung ở chương
  nhiều công thức. Đó là **ticket B0 mới** (B0 phải lưu ảnh cắt), không thuộc spec này.
- **Ngữ cảnh sinh bởi LLM cho từng chunk** (Anthropic bản đầy đủ): D8 dùng bản `section_path` miễn phí.
  Nâng cấp sau không phải embed lại vì đổi định danh — chỉ vì đổi nội dung embed.
- **Late chunking**: đòi mô hình tự host truy cập tầng token; xung đột với D9.
- **Bộ câu hỏi ~50 câu đo recall@k đầu-cuối**: chỉ có nghĩa khi gia sư pha B đã chạy.
- **Tách từ tiếng Việt cho BM25**: mở lại khi có số liệu (D9).
- **Mở dần giai đoạn**: hàng rào merge ở D8 làm tính năng này khó hơn spec-addendum ngụ ý — chưa trích
  hết thì chưa có bảng node chuẩn. Thuộc A10/T4, ghi để khi làm tới đó không tưởng nó miễn phí.

## Further Notes

**Số đo neo spec** (corpus bốn tài liệu, 2026-08-29):

```
116/129 section có nội dung · median 215 token · max 3.390 · 48.694 token
233 chunk · 19 hình (8 có chú thích, 11 không) · 60 bảng · 258 công thức
13/129 section mang ảnh = 10%
66% chunk của xstk chứa dấu [formula] — 263 dấu
dự kiến: 390–730 node học được · ~460 lượt gọi (xấu nhất 812) · ~1.100–1.800 vector
```

**Section quá dài không phải vấn đề** — max 3.390 token, chỉ 2/116 vượt 2.000, 0 vượt 4.000. Vừa mọi
cửa sổ ngữ cảnh kể cả khi quét lại gửi nhiều lượt.

**Bốn việc phát sinh cần theo dõi:**

1. Mô hình trích phải **đa phương thức** (hệ quả D7).
2. `difficulty` **biến khỏi schema A3** — spec-addendum phải sửa theo (D6).
3. Đường leo Q28→(c) là **ticket B0**, không phải ticket A3.
4. `.env.example` cần thêm tên biến API key với **giá trị rỗng** (D16). File này đang chỉ có sáu tham số
   cắt chunk, không bí mật nào — giữ nguyên tính chất đó.

**Bài học B0 được áp lại trong spec này**, ghi để người triển khai nhận ra khuôn:

| Bài học B0 | Áp ở đây |
|---|---|
| `adapter_version` bump tay, đổi mã thì cây cũ không bị dùng lại im lặng | `prompt_hash` phải chứa ví dụ few-shot (D10) |
| I9 — vị trí ký tự phải khớp toàn văn | Bằng chứng phải định vị được trong chunk (D3) |
| Ghi–phát lại fixture: 220 giây → 0,11 giây | Ghi–phát lại phản hồi mô hình (Seam ②) |
| Cảnh báo không đọc được thì bằng không có | Cổng chặn 40%, `coverage_incomplete` (D12) |
| Không danh sách mang tên ngôn ngữ | BM25 không thêm bộ tách từ tiếng Việt (D9) |

**Về seam — đã chốt:** **ba seam**. ① thuần domain · ② ghi–phát lại hội thoại LLM · ③ ghi–phát lại
vector embedding, **cơ chế riêng**. Nhiều hơn B0 một seam, và lý do chính đáng: hai nhà cung cấp có hình
dạng bản ghi khác nhau về bản chất (có thứ tự/có trạng thái vs thuần hàm), lại vô hiệu hoá bởi hai khoá
khác nhau. Bản ghi embedding còn phải sống tiếp sang đợt merge để test blocking ở ngưỡng thật.
