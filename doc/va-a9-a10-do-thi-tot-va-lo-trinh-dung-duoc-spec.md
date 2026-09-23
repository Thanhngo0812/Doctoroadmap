# Vá A9–A10: đồ thị tiên quyết dùng được và lộ trình học dùng được

**Nguồn chân lý:** spec này **vá** `doc/A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md` (D11, D12) và
`doc/spec-addendum.md` (A9, A10, §432). Chỗ nào hai bên khác nhau thì theo spec này.

**Căn cứ:** `report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md` (vòng 36) và hai phụ lục văn liệu của nó. Mọi số đo
trích trong spec đều dẫn về mục của báo cáo đó, không lặp lại phép đo ở đây.

**Chủ dự án chốt ngày 2026-09-22:** (1) sửa cả hai chặn của chương vàng, giữ hai giáo trình `doc-1` và `doc-2`
(mục 3C); (2) **stage là nhóm học song song được** — giữ bất biến, đổi thuật toán xếp tầng; (3) chu trình hai cạnh
được **gắn cờ nghi lỗi kiểu quan hệ và loại khỏi đồ thị con `requires`**, không giữ và cũng không gộp.

**Cập nhật cùng ngày:** chủ dự án đã **thay `doc-1` bằng một PDF khác** vì bản cũ hỏng lớp text. Bản mới là một
cuốn khác — *Bài giảng Đại số tuyến tính*, Đại học Hàng hải, 102 trang, 5 chương, **25,46%** ký tự có dấu, **0**
watermark — nên **chương vàng của `doc-1` phải chọn lại** (xem vé 19). V2 dưới đây đã viết lại theo đó.

**Status:** ready-for-agent

---

## Problem Statement

Chủ dự án muốn hai thứ: một **đồ thị tiên quyết đủ tốt để tin**, và một **lộ trình học thật sự dùng được**. Hiện
tại không có thứ nào, và lý do đã đo được chứ không còn là phỏng đoán.

**Lộ trình không dùng được.** Chạy trên `xstk-ch3-1`, A10 chia 98 khái niệm thành **63 chặng, trong đó 39 chặng chỉ
có đúng một khái niệm**. Đó không phải lộ trình học, đó là danh sách khái niệm có đánh số. Trần "5–8 khái niệm mỗi
chặng" mà spec đặt ra **chưa bao giờ bị chạm tới**: chặng lớn nhất trên toàn bộ bốn tài liệu là 5 khái niệm. Và thứ
tự các chặng gần như không liên quan tới thứ tự của chính giáo trình — trên `baocao-canhan`, lộ trình trùng thứ tự
sách ở **51,0%** số cặp, tức không phân biệt được với tung đồng xu.

**Đồ thị chưa tin được, và ta chưa có cách nói nó sai ở đâu.** Chưa có chỉ số nào đo "lộ trình này đúng hay sai".
Bộ vàng thử nghiệm cho thấy **11 trên 62 cạnh vàng bị lộ trình máy xếp ngược** — máy đặt *Phân phối chuẩn* sau
*Độ tin cậy của ước lượng* trong khi người gán nói phải trước — nhưng con số ấy hiện phải tính tay, không có lệnh
nào cho ra nó.

**Và bộ vàng — thứ dùng để phán mọi chuyện trên — đang bị chặn ở cả hai chương.** `doc-2` mục 3C mất chính các đối
tượng mà mục ấy nói về: `ℒ(V,W)`, `𝐅^{m,n}`, `ℳ`, `𝒫ₙ(𝐅)` đều bị guard tên ký hiệu loại (36 tên phân biệt, 47
lượt). `doc-1` bị A5 đoán `document_language=en` cho một giáo trình tiếng Việt, nên **61 trên 98 mô tả được viết
bằng tiếng Anh**, 51 mô tả bị viết lại theo luật ngôn ngữ sai.

Nếu không sửa, hệ quả dây chuyền là: người gán nhãn ngồi gán một chương mà pipeline không biết một nửa số khái
niệm trung tâm; rồi mọi số precision/recall đo trên bộ vàng ấy đều vô nghĩa; rồi lộ trình sinh ra từ đồ thị ấy
không ai kiểm được.

## Solution

Bốn việc, theo đúng thứ tự phụ thuộc.

**Một — mở khoá hai chương vàng.** A3 thôi loại khái niệm chỉ vì nó được gọi bằng ký hiệu có cấu trúc, và A5 thôi
đoán sai ngôn ngữ của giáo trình tiếng Việt. Điều kiện nhận: trên mục 3C của `doc-2`, các khái niệm `ℒ(V,W)`,
`𝐅^{m,n}`, `ℳ` **có mặt** trong bảng ứng viên, còn `3.65`, `6.49`, `i`, `0`, `{0}` **không có mặt**; và trên
`doc-1`, `document_language` là `vi` và mô tả viết bằng tiếng Việt.

**Hai — A9 nói đúng việc nó làm và làm đúng việc nó nói.** Đổi tên bước thành *kiểm tra tính nhất quán cấu trúc*
(vì "kiểm định" trong văn liệu nghĩa là kiểm trên biểu hiện học viên, thứ dự án không có). Gỡ chu trình bằng
**MFAS có trọng số** giải chính xác qua liệt kê chu trình đơn rồi phủ tập hợp, thay cho vét cạn theo tập con cạnh
vốn lặng lẽ rơi sang xấp xỉ khi SCC có hơn 16 cạnh. Bỏ `confidence` do mô hình tự khai khỏi thứ tự ưu tiên — trên
corpus của ta nó chỉ nhận ba giá trị, và văn liệu đo AUROC của nó xấp xỉ 0,5. Chu trình hai cạnh được gắn cờ nghi
lỗi kiểu quan hệ và **đưa ra khỏi đồ thị con `requires`** chờ người duyệt. Cổng chất lượng đếm cạnh **không thừa**,
hạ xuống mức chỉ còn bắt lỗi pipeline chết, và **luôn ghi số đo ra manifest** thay vì im lặng rơi fallback.

**Ba — A10 sinh lộ trình có hình dạng dùng được.** Bỏ phép giao với cụm chủ đề khỏi định nghĩa stage — đo được là
nó chỉ làm vụn mà không cải thiện chỉ số nào. Thay xếp tầng theo đường dài nhất bằng **xếp tầng Coffman–Graham có
trần độ rộng**, thứ giải đúng bài toán mà spec đang cố giải bằng tay. Giữ nguyên bất biến mà chủ dự án đã chốt:
**không cạnh tiên quyết nào được nằm gọn trong một stage** — stage vẫn là nhóm học song song được. Thêm **sàn** cỡ
stage, vì số đo cho thấy bệnh là quá nhỏ chứ không phải quá to.

**Bốn — có thước đo.** Hai chỉ số, đăng ký trước, tính được bằng code thuần: **Kendall τ** giữa thứ tự lộ trình và
thứ tự trình bày của giáo trình, và **tỉ lệ vi phạm cạnh vàng** — số cạnh vàng mà lộ trình xếp tiên quyết sau khái
niệm cần nó. Chỉ số thứ hai không tốn thêm một lượt gán nhãn nào ngoài bộ vàng vốn đã phải làm.

## User Stories

**Mở khoá chương vàng**

1. Là người gán nhãn, tôi muốn mọi khái niệm trung tâm của mục 3C có mặt trong bảng gán, để tôi không phải ghi
   quan hệ cho một khái niệm mà pipeline không biết.
2. Là người gán nhãn, tôi muốn bảng gán của `doc-1` viết bằng tiếng Việt, để tôi đọc được mô tả khái niệm mà tôi
   đang phán.
3. Là reviewer, tôi muốn biết chính xác những tên nào bị A3 loại và vì lý do gì, để tôi kiểm được rằng phần bị mất
   đúng là nhiễu chứ không phải khái niệm.
4. Là reviewer, tôi muốn số theorem (`3.65`, `6.49`) và ký hiệu trơ (`i`, `0`, `{0}`, `V`) tiếp tục bị loại, để
   bảng ứng viên không phình bằng rác.
5. Là người vận hành, tôi muốn khai được ngôn ngữ của tài liệu bằng một tham số tường minh khi máy đoán sai, để một
   lỗi mã chữ của trình phân tích không quyết định ngôn ngữ của cả giáo trình.
6. Là người vận hành, tôi muốn ngôn ngữ đã dùng và cách nó được quyết định (đoán hay khai) nằm trong manifest, để
   sau này đọc artifact biết ngay.
7. Là chủ dự án, tôi muốn bốn tài liệu phát triển giữ nguyên artifact khi tôi không khai gì thêm, để việc sửa này
   không buộc chạy lại toàn bộ corpus.
8. Là người viết báo cáo, tôi muốn biết tài liệu nào sinh bởi phiên bản A3 nào, để nói rõ corpus có nhiều cấu hình
   chứ không để người đọc tự phát hiện.

**A9 — kiểm tra tính nhất quán cấu trúc**

9. Là người đọc báo cáo, tôi muốn bước này được gọi là *kiểm tra tính nhất quán cấu trúc*, để không hiểu nhầm là
   dự án đã kiểm định quan hệ tiên quyết trên người học.
10. Là reviewer, tôi muốn chu trình được gỡ bằng nghiệm **chính xác** ở mọi cỡ đồ thị, để câu "giải tối ưu" trong
    báo cáo là câu đúng.
11. Là reviewer, tôi muốn artifact ghi rõ nghiệm gỡ chu trình là chính xác hay xấp xỉ, để một lượt chạy xấp xỉ
    không bị đọc nhầm thành tối ưu.
12. Là người vận hành, tôi muốn việc gỡ chu trình không treo dù SCC lớn tới đâu, để một tài liệu xấu không chặn cả
    lượt chạy.
13. Là reviewer, tôi muốn trọng số giữ cạnh được định nghĩa tường minh, để biết vì sao cạnh này bị gỡ chứ không
    phải cạnh kia.
14. Là reviewer, tôi muốn `confidence` do mô hình tự khai không tham gia quyết định gỡ cạnh, để kết quả không phụ
    thuộc một con số đã được đo là gần như vô nghĩa.
15. Là reviewer, tôi muốn tiêu chí phá hoà cuối cùng là tất định, để cùng đầu vào luôn cho cùng đầu ra.
16. Là người duyệt, tôi muốn cặp khái niệm đòi nhau hai chiều được gắn cờ **nghi lỗi kiểu quan hệ** và đưa ra khỏi
    đồ thị tiên quyết, để một quan hệ bộ phận–toàn thể bị đoán ngược không âm thầm định hình lộ trình.
17. Là người duyệt, tôi muốn thấy cả hai cạnh và bằng chứng của từng chiều trong cờ ấy, để phán được mà không phải
    mở lại artifact gốc.
18. Là reviewer, tôi muốn cổng chất lượng đếm cạnh **không thừa**, để một đồ thị gần đóng bắc cầu không qua cổng
    nhờ những cạnh không thêm cấu trúc nào.
19. Là người vận hành, tôi muốn số đo của cổng luôn nằm trong manifest kể cả khi cổng mở, để theo dõi được xu hướng
    giữa các tài liệu.
20. Là người vận hành, tôi muốn cổng không âm thầm chuyển sang lộ trình dự phòng, mà phải để lại cảnh báo đọc được.
21. Là reviewer, tôi muốn thứ tự các bước A9 được cố định — xử lý chu trình trước, đánh dấu bắc cầu sau — để bước
    đánh dấu chạy trên một đồ thị phi chu trình đúng như định nghĩa của nó đòi hỏi.
22. Là reviewer, tôi muốn cạnh bắc cầu tiếp tục chỉ bị **đánh dấu**, không bị xoá, vì phép đo cho thấy một cạnh sai
    có thể làm biến mất tới 25 cạnh đúng.
23. Là người duyệt, tôi muốn thấy phân bố kích thước các thành phần liên thông mạnh còn lại sau A9, để biết đồ thị
    có bệnh gì nặng hơn chu trình hai cạnh không.

**A10 — lộ trình**

24. Là người học, tôi muốn mỗi chặng có đủ khái niệm để thành một buổi học, chứ không phải một chặng một khái niệm.
25. Là người học, tôi muốn số chặng của một giáo trình ở mức đọc hết được, chứ không phải 63 chặng cho 98 khái niệm.
26. Là người học, tôi muốn các khái niệm trong cùng một chặng học được song song, tức không khái niệm nào trong
    chặng là tiên quyết của khái niệm khác cùng chặng.
27. Là người học, tôi muốn chặng đầu tiên không chứa một phần ba số khái niệm của cả cuốn sách.
28. Là reviewer, tôi muốn số chặng không bao giờ nhỏ hơn cận dưới lý thuyết, để phát hiện ngay nếu trần bị vi phạm.
29. Là reviewer, tôi muốn thuật toán xếp tầng được gọi đúng tên và kèm cận đã chứng minh, để phần phương pháp của
    báo cáo có chỗ dựa.
30. Là reviewer, tôi muốn trần và sàn cỡ chặng là **tham số** có ablation, không phải một con số viện dẫn tâm lý học.
31. Là reviewer, tôi muốn thứ tự giữa các chặng ngang hàng **không** được phá hoà bằng thứ tự chương, để thứ tự
    chương còn dùng được làm đối chứng đánh giá.
32. Là người học, tôi muốn biết khái niệm nào chưa từng được xét, phân biệt với khái niệm đã xét mà không có tiên
    quyết, để không tưởng nhầm một lỗ hổng độ phủ là một điểm khởi đầu.
33. Là người vận hành, tôi muốn "độ sâu tiên quyết" được gọi đúng tên thay vì "độ khó", vì không nguồn nào kiểm
    chứng rằng độ sâu đồ thị tương quan với độ khó.

**Thước đo**

34. Là reviewer, tôi muốn một lệnh cho ra Kendall τ giữa lộ trình và thứ tự trình bày của giáo trình, để không phải
    tính tay.
35. Là reviewer, tôi muốn τ được báo cáo kèm số cặp so được và số cặp bị loại vì hoà, để biết con số dựa trên bao
    nhiêu bằng chứng.
36. Là reviewer, tôi muốn **tỉ lệ vi phạm cạnh vàng** của lộ trình, để có một chỉ số nói thẳng lộ trình sai ở đâu.
37. Là reviewer, tôi muốn chạy được cùng phép đo trên lộ trình dựng từ **cạnh vàng** và từ **cạnh máy**, để tách
    "giáo trình sắp xếp kém" khỏi "đồ thị của ta nhiễu".
38. Là reviewer, tôi muốn danh sách cụ thể các cạnh vàng bị vi phạm kèm tên khái niệm, để đọc được ca sai chứ không
    chỉ thấy con số.
39. Là reviewer, tôi muốn so được nhiều cách gom chặng trên cùng dữ liệu, để lựa chọn thiết kế dựa trên số chứ
    không dựa trên lý lẽ.
40. Là chủ dự án, tôi muốn mọi phép đo này chạy được khi chặn mạng và không gọi mô hình, để lặp lại bao nhiêu lần
    cũng không tốn ngân sách.

## Implementation Decisions

### V1 — Luật đặt tên khi khái niệm được gọi bằng ký hiệu (A3)

Thay cho luật hiện tại "tên là ký hiệu thì loại entity", luật ba nhánh, xét theo thứ tự:

1. **Có alias là tên chữ** → lấy alias làm tên, giữ ký hiệu làm alias. *(đã cài ở `a3-section-conversation-v6`,
   giữ nguyên)*
2. **Không có alias chữ, nhưng tên ký hiệu là ký hiệu có cấu trúc** → **giữ entity, giữ nguyên tên ký hiệu**, và
   đánh dấu `name_kind = "symbol"` trên node để tầng sau biết.
3. **Không có alias chữ và tên là ký hiệu trơ** → loại như hiện nay, và ghi vào danh sách đã có.

Spec **không** quy định biểu thức chính quy cho "có cấu trúc". Nó quy định **điều kiện nhận**, và người cài chọn
predicate nào đạt được:

| Phải giữ (mục 3C, `doc-2`) | Phải loại |
|---|---|
| `ℒ(V,W)` · `ℒ(𝑉, 𝑊)` · `L(V, W)` · `ℒ(𝑉)` | `i` · `0` · `V` · `C` · `F` · `R` |
| `𝐅^{m,n}` · `F^m,n` · `F^n` · `𝐅 𝑛` | `{0}` |
| `𝒫(𝐅)` · `𝒫ₙ(𝐅)` · `𝒫 2(𝐑)` · `P4(R)` | `3.65` · `3.68` · `3.94` · `6.49` · `6.54` |
| `ℳ` · `B(V, W)` · `S ⊗ T` · `V^m` · `𝐶[-𝜋 , 𝜋]` | |

Hai ca cần phán riêng và người cài phải nêu lựa chọn trong vé: `V(2)` / `V(m)` (nhiều khả năng là thể hiện ký hiệu
chứ không phải khái niệm) và `𝛼𝑇` (tích vô hướng với toán tử). Mặc định đề xuất: loại cả hai, vì chúng không xuất
hiện như đối tượng được định nghĩa.

`ℳ` là ca khó nhất vì nó là một ký tự đơn. Nếu predicate thuần cú pháp không giữ được nó thì **dùng bằng chứng**:
một tên ký hiệu trơ vẫn được giữ khi nó có provenance ở một chunk mang tín hiệu định nghĩa — cùng bộ tín hiệu mà
stage `provenance` đã dùng. Đây là lựa chọn được phép; vé phải nói rõ đã dùng cách nào.

`algorithm_id` của A3 tăng một bậc. Bốn tài liệu phát triển **không** chạy lại; báo cáo ghi rõ corpus có nhiều cấu
hình A3 và tài liệu nào thuộc cấu hình nào.

### V2 — Cổng chất lượng chữ ở ingest *(viết lại ngày 2026-09-22, xem đính chính dưới)*

> **Đính chính.** Bản đầu của V2 nói gốc của ca `doc-1` là bộ đoán ngôn ngữ đọc nhầm ký tự vùng dùng riêng, và bảo
> sửa bộ đoán. **Sai.** Đọc thẳng chunk của `doc-1` cũ cho thấy **24 ký tự có dấu trên 42.087 ký tự chữ cái —
> 0,06%**, trong khi một giáo trình tiếng Việt thật ở mức 25%. Chữ trong lớp text của PDF đó **hỏng thật**: dấu bị
> nuốt hoặc thay bằng glyph sai (`Tính chất` → `T‰nh ch§t`, `CHƯƠNG` → `CH NG`). Bộ đoán ngôn ngữ **đoán đúng** —
> thứ đưa cho nó không còn là tiếng Việt. Sửa bộ đoán theo hướng cũ sẽ chỉ ép nó gọi một đống chữ hỏng là tiếng
> Việt. Chủ dự án đã thay `doc-1` bằng một PDF khác (2026-09-22) đo được **25,46%** ký tự có dấu.

Vấn đề thật không nằm ở A5 mà ở chỗ **không có ai kiểm chất lượng chữ**, nên một PDF hỏng font đi hết A1→A5 mà
không có một cảnh báo nào, và chỉ lộ ra khi người đọc mô tả. Nên luật là:

1. **Ingest đo chất lượng lớp text** và ghi vào manifest: số ký tự chữ cái, tỉ lệ ký tự có dấu, tỉ lệ ký tự vùng
   dùng riêng, tỉ lệ ký tự thay thế.
2. **Cổng cảnh báo:** tài liệu có tỉ lệ ký tự có dấu **gần bằng không** nhưng mật độ chữ cái bình thường là dấu
   hiệu lớp text hỏng font. Sinh cảnh báo đọc được, nêu số đo, và nói thẳng rằng tài liệu này **không đủ chất lượng
   làm nguồn bộ vàng**. Không tự ý dừng pipeline — chẩn đoán vẫn có giá trị.
3. **Lối khai tường minh ngôn ngữ** vẫn giữ: khai thì máy không đoán; manifest ghi cả giá trị lẫn cách quyết định
   (`detected` / `declared`); giá trị khai vào config hash.
4. `document_language` giữ nguyên thuật toán, chỉ **tính tỉ lệ dấu trên ký tự chữ cái đọc được** thay vì trên toàn
   văn bản.

Điều kiện nhận, đo trên dữ liệu thật đã có: **`doc-1` mới qua cổng** (25,46% dấu); **`doc-1` cũ bị cổng bắt**
(0,06% dấu, chunk còn lưu ở `artifacts/chunks/doc-1/v3`); `doc-2`, `doc-3` là tiếng Anh nên cổng **không** được báo
nhầm chúng — tức luật phải phân biệt "không có dấu vì là tiếng Anh" với "không có dấu vì chữ hỏng", và cách rẻ
nhất là chỉ báo khi **có khai báo ngôn ngữ có dấu** hoặc khi tỉ lệ ký tự thay thế/PUA bất thường.

Không khai gì và tài liệu bình thường → hành vi **y hệt hiện nay**; bốn tài liệu phát triển giữ artifact và
`reused=true`.

### V3 — Gỡ chu trình: MFAS có trọng số, giải chính xác

Đổi `_feedback_edges` sang ba bước:

1. Liệt kê **chu trình đơn** trong thành phần liên thông mạnh.
2. Giải bài **phủ tập hợp có trọng số**: chọn tập cạnh có tổng trọng số nhỏ nhất sao cho mọi chu trình bị cắt ít
   nhất một cạnh. Đây là công thức tương đương MFAS có trọng số.
3. Chỉ khi số chu trình vượt ngân sách mới rơi về heuristic tuyến tính, và artifact **phải** ghi nghiệm là xấp xỉ.

**Ngân sách đặt theo số chu trình đơn, không theo số node hay số cạnh.** Lý do: khoảng cách giữa hai đại lượng
chính là toàn bộ vấn đề — một thành phần 27 node / 60 cạnh có 2⁶⁰ tập con cạnh nhưng chỉ 177 chu trình đơn.

**Trọng số giữ cạnh** thay cho thứ tự từ điển bốn tiêu chí hiện nay. Ba tiêu chí, theo thứ tự trội giảm dần:
loại bằng chứng → thuận thứ tự trình bày → số nguồn độc lập đã đề cử. Cách mã hoá: mỗi tiêu chí một bậc cơ số đủ
lớn để tiêu chí trước luôn trội tiêu chí sau, nên "tối thiểu tổng trọng số cạnh bị gỡ" tái hiện đúng ưu tiên đã
chốt. **`confidence` bị bỏ khỏi trọng số.** Phá hoà cuối cùng bằng khoá cạnh theo thứ tự từ điển, để tái lập được.

Artifact ghi thêm, cho mỗi thành phần đã xử lý: số chu trình đơn, phương pháp (`exact` hay `approximate`), và tổng
trọng số đã gỡ.

### V4 — Chu trình hai cạnh: cờ nghi lỗi kiểu quan hệ

Thay hành vi "giữ cả hai cạnh, gắn cờ trung tính" bằng:

- Cặp `A → B` và `B → A` được **đưa ra khỏi đồ thị con `requires`** trước khi xếp tầng.
- Sinh một cờ **`suspected_relation_type_error`** mang: hai node, cả hai cạnh, bằng chứng của từng chiều, và lý do.
- Cặp ấy **không** tính vào cổng chất lượng, **không** tính vào mật độ cạnh, và **không** xuất hiện như tiên quyết
  trong lộ trình.
- Nếu người duyệt phán một chiều là đúng, chiều ấy quay lại đồ thị ở lượt sau qua đường xử lý tồn đọng đã có.

Lý do thay đổi, viết vào spec thay cho lý lẽ cũ: bộ dữ liệu mà spec đang dẫn **không** coi cạnh hai chiều là hợp lệ
— tác giả viết rằng các cặp ấy gợi ý nên gộp thành một khái niệm; và trong lý thuyết không gian tri thức, `A↔B`
kéo theo hai khái niệm có cùng tập trạng thái, tức cấu trúc mất tính phân biệt và mất tính well-graded mà A10 cần.
Ca thật duy nhất trên corpus (**ERD ↔ Thiết kế Cơ sở dữ liệu**) không phải hai nhãn đồng nghĩa mà là quan hệ
bộ phận–toàn thể bị đoán ngược, nên **gộp cũng sai** — do đó chọn hướng thứ ba.

Hệ quả cho A10: sau A9 đồ thị con `requires` là **DAG thật**, không còn thành phần liên thông mạnh nào. Bước co
thành phần ở A10 trở thành một **assertion** chứ không phải một phép biến đổi: còn thành phần nào lớn hơn một node
là lỗi của A9 và phải dừng.

### V5 — Thứ tự các bước A9

Cố định, và ghi thành assertion:

1. Xử lý tồn đọng · 2. chuẩn hoá sổ đăng ký kiểu · 3. tách thành phần liên thông mạnh · 4. tách cặp hai chiều ra
làm cờ · 5. gỡ chu trình còn lại bằng V3 · 6. **đánh dấu** cạnh bắc cầu · 7. cổng chất lượng · 8. gán cụm cho node mới.

Bước 6 phải chạy sau bước 5 vì rút gọn bắc cầu chỉ xác định duy nhất trên đồ thị phi chu trình. Giữ nguyên quyết
định **đánh dấu, không xoá**, và bổ sung vào phần biện minh: ngoài lý do quy trình duyệt, còn một lý do thống kê —
cạnh nhiễu ít bị bắc cầu hàm ý hơn cạnh thật, nên xoá cạnh thừa sẽ ưu tiên xoá cạnh đúng và giữ lại cạnh nhiễu.

### V6 — Cổng chất lượng

- Tử số đếm **cạnh không mang `redundant_via`**.
- Ngưỡng hạ xuống mức chỉ còn bắt **lỗi pipeline chết**, không còn phán xét chất lượng tài liệu. Đề xuất
  0,15 cạnh/node và 85% node cô lập; vé chốt con số cuối và ghi lý do.
- Manifest **luôn** ghi: số cạnh không thừa, số node học được, số node cô lập, tỉ lệ, và cổng mở hay đóng — kể cả
  khi mở.
- Cổng đóng thì sinh **cảnh báo đọc được**, không im lặng chuyển chế độ.
- Spec ghi rõ đây là chỗ **không có nguồn**: không tìm thấy công trình nào dùng ngưỡng mật độ để kích hoạt phương
  án dự phòng, và dải mật độ hợp lệ đã quan sát được trải từ 0,34 đến 5,89 cạnh/node.

### V7 — Xếp tầng có trần độ rộng (A10)

Thay xếp tầng theo đường dài nhất bằng **Coffman–Graham** với trần độ rộng `W`:

- Bài toán là *xếp tầng độ rộng tối thiểu*, tương đương lập lịch có ràng buộc thứ tự với việc dài một đơn vị.
  Nó NP-khó và không xấp xỉ được dưới 4/3; Coffman–Graham cho cận `(2 − 2/W)`. Báo cáo phải nêu tên bài toán và
  dẫn nguồn, không trình bày như một heuristic tự nghĩ.
- **Bất biến giữ nguyên:** không cạnh `requires` nào được nối hai khái niệm trong cùng một stage.
- Sau khi xếp tầng, thêm một bước **cân bằng**: khái niệm nào có nhiều tầng khả thi thì đẩy sang tầng ít khái niệm
  hơn. Không đổi tính hợp lệ, chạy tuyến tính.
- **Assertion:** số stage ≥ `max(độ dài xích dài nhất, ⌈n / W⌉)`. Vi phạm là lỗi cài đặt.

### V8 — Định nghĩa stage

- **Bỏ phép giao với cụm chủ đề.** `stage = một tầng` (cắt lát khi vượt trần). Cụm chủ đề chuyển vai: dùng để
  **đặt tên stage** và để **sắp thứ tự khái niệm bên trong stage**, không dùng để chia.
- Thêm **sàn** cỡ stage bên cạnh trần. Tầng nhỏ hơn sàn được gộp với tầng kề **chỉ khi** phép gộp không đưa hai
  đầu của một cạnh `requires` vào cùng stage; không gộp được thì để nguyên và ghi nhận.
- `W` (trần) và sàn là **tham số**, mặc định trần 8. Spec **không** viện dẫn tâm lý học cho con số này: nguồn gốc
  "7±2" đã bị chính tác giả của nó gọi là trùng hợp tai hại, và không có nguồn sơ cấp nào khuyến nghị cỡ mô-đun
  theo số khái niệm. Con số được bảo vệ bằng bảng ablation, không bằng trích dẫn.
- **Thứ tự giữa các stage ngang hàng không được phá hoà bằng vị trí chương.** Dùng tiêu chí không dính tới thứ tự
  trình bày — đề xuất: số khái niệm hậu duệ giảm dần, rồi khoá stage. Lý do: thứ tự chương là **đối chứng đánh giá**
  ở V9; dùng nó để phá hoà rồi lại dùng nó để chấm là nhiễm đối chứng.

### V9 — Hai chỉ số đánh giá lộ trình

Cả hai là **hàm thuần** trong tầng domain, cùng chỗ với bộ chấm bộ vàng hiện có, và chạy được khi chặn mạng.

**Kendall τ so thứ tự trình bày.** Trên mọi cặp khái niệm nằm ở hai stage khác nhau **và** có thứ tự trình bày khác
nhau: τ = (thuận − nghịch) / (thuận + nghịch). Báo cáo kèm **số cặp so được** và **số cặp bị loại vì hoà**. Ghi kèm
cảnh báo của chính tác giả chỉ số: phép đo dùng **một** văn bản tham chiếu, trong khi có thể có nhiều thứ tự chấp
nhận được.

**Tỉ lệ vi phạm cạnh vàng.** Với mỗi cạnh vàng `p → t`: lộ trình vi phạm nếu nó xếp `p` **sau** `t`. Trả về tỉ lệ
**và danh sách cạnh vi phạm kèm tên khái niệm**. Chỉ số này không cần thêm lượt gán nhãn nào.

Cả hai phải chạy được trên **hai tập cạnh** — cạnh vàng và cạnh máy — trên cùng tập khái niệm, vì chỉ so hai con số
ấy mới tách được "giáo trình sắp xếp kém" khỏi "đồ thị của ta nhiễu". Trên bộ vàng thử nghiệm, phép so ấy cho vàng
τ +0,803 và máy τ +0,603.

> **Sửa V9, 2026-09-23 — xem V14.** Chỉ số thứ tự nay là `learning_order_error` khắt khe trên **vàng hội ý**, và
> mọi so sánh giữa hai cách xếp ở A10 phải kèm phân bố nhiễu. Công thức "vi phạm / cặp đã xếp được thứ tự" ở trên
> giữ lại dưới tên `rate` để so với số cũ, không dùng làm cổng.

### V10 — Cách gọi tên, ghi vào spec và báo cáo

| Đang gọi | Gọi lại thành | Lý do |
|---|---|---|
| A9 "kiểm định đồ thị" | **kiểm tra tính nhất quán cấu trúc** | "kiểm định" trong văn liệu nghĩa là kiểm trên biểu hiện học viên |
| "độ khó" tính từ độ sâu DAG | **độ sâu tiên quyết** | không nguồn nào kiểm chứng tương quan với độ khó |
| "lộ trình học" trong bài báo | nói rõ là **một gradation được đóng gói thành stage** | "learning path" có định nghĩa hình thức khác: xích cực đại các trạng thái tri thức |

### V11 — Hai sửa nhỏ đi kèm

- **F113:** kiểm hợp đồng của pass phụ phải kiểm **từng phần tử** của danh sách cờ, không chỉ kiểu của danh sách.
  Hiện hai cờ rỗng `{}` lọt vào trang duyệt dưới dạng `{"status": "unresolved"}` không xử lý được.
- **F115:** bước bỏ dòng watermark chỉ chạm `text` và `raw_text`, nhưng node tài liệu còn có ô bảng và tiền tố ngữ
  cảnh. Hoặc mở rộng cho đủ các trường văn bản, hoặc đổi tên thuật toán cho khỏi hứa quá.

### V12 — Việc phải gỡ khỏi spec

Ba thứ spec đang mô tả mà mã không có: gắn node media vào stage, lượt LLM đặt tên stage, và trường độ khó. Gỡ khỏi
spec, hoặc cắt vé — không để spec mô tả một hệ thống không tồn tại. Nếu giữ phần media thì ghi rõ nó là heuristic
kỹ thuật: không tìm thấy nguồn ủng hộ lẫn phản bác.

### V13 — Phần phải viết vào Limitations của báo cáo

1. Dự án **không có dữ liệu học viên**, nên không kiểm định được theo nghĩa của văn liệu. Đường nâng cấp rẻ nhất
   cần khoảng 120 học viên tại một thời điểm.
2. Đồ thị tiên quyết tương ứng một–một với một cấu trúc mà hai người sáng lập lý thuyết không gian tri thức viết
   rằng "không có ý nghĩa sư phạm tốt". Không cần đổi mô hình, nhưng không thừa nhận thì là bỏ qua phản chứng đã
   công bố.
3. Thứ người học sẵn sàng học tiếp là một **tập phụ thuộc trạng thái từng người**, không phải một tầng chung. A10
   sinh một lộ trình cố định — đó là giản lược có chủ ý vì thiếu dữ liệu tương tác.
4. Ý tưởng dùng sắp xếp tô-pô để lập lộ trình học đã công bố từ thập niên 1970; đóng góp của dự án không nằm ở đó.

## Testing Decisions

**Thế nào là một test tốt ở đây:** nó phá được khi luật bị phá, và nó không biết gì về cách luật được cài. Mọi
test dưới đây đặt ở **seam đã có**, gọi hàm thuần với dữ liệu dựng tay, và khẳng định trên **đầu ra**, không trên
bước trung gian. Luật của dự án giữ nguyên: **test chỉ được nhận khi nó đỏ lúc phá đúng thứ nó giữ**, và mỗi vé
nộp danh sách đột biến đã thử kèm test nào bắt.

**Năm seam, tất cả đã tồn tại, không thêm seam mới.**

| Seam | Kiểu | Phủ phần nào | Prior art |
|---|---|---|---|
| Hàm phân loại tên trong tầng domain | hàm thuần trên chuỗi | V1 | test domain của A3 |
| Bước trích thực thể A3 | use case, mô hình giả | V1 | `test_a3_extract.py`, đã có ca guard ký hiệu của vé 17 |
| Hàm quyết định ngôn ngữ trong tầng domain | hàm thuần trên chunk | V2 | test quyết định canonical |
| Hàm luật kiểm tra nhất quán (A9) | hàm thuần, vào/ra dict | V3, V4, V5, V6 | `test_global_validation.py`, 9 test hiện có |
| Hàm dựng lộ trình (A10) | hàm thuần, vào/ra dict | V7, V8 | `test_roadmap.py`, 6 test hiện có |
| Bộ chấm bộ vàng trong tầng domain | hàm thuần | V9 | `test_gold_scoring.py` |

Ca phải có, viết dưới dạng hành vi:

- **V1:** mỗi tên trong bảng "phải giữ" cho ra một ứng viên có mặt; mỗi tên trong bảng "phải loại" thì không, và
  tên bị loại có mặt trong danh sách đã ghi. Ca alias chữ vẫn được ưu tiên làm tên. Danh sách bị loại không vượt trần.
- **V2:** văn bản tiếng Việt lẫn ký tự vùng dùng riêng vẫn ra `vi`; văn bản tiếng Anh ra `en`; khai báo tường minh
  thắng phép đoán; không khai thì kết quả và config hash không đổi so với trước.
- **V3:** một thành phần mà nghiệm tối ưu là gỡ **hai cạnh rẻ** thay vì **một cạnh đắt** phải cho ra hai cạnh rẻ —
  đây là ca phân biệt MFAS có trọng số với MFAS đếm cạnh, và luật cũ sẽ đỏ. Vượt ngân sách chu trình thì artifact
  ghi `approximate`. Cùng đầu vào cho cùng đầu ra qua nhiều lượt.
- **V4:** cặp hai chiều không xuất hiện trong cạnh `requires` đầu ra, có cờ mang đủ hai cạnh và bằng chứng, không
  ảnh hưởng cổng chất lượng, và A10 nhận được một DAG không còn thành phần liên thông mạnh nào.
- **V5:** cạnh bắc cầu vẫn được **đánh dấu** chứ không mất; đảo thứ tự hai bước làm test đỏ.
- **V6:** đồ thị mà mọi cạnh đều thừa thì **không** qua cổng; manifest có đủ số đo kể cả khi cổng mở; cổng đóng thì
  có cảnh báo.
- **V7:** không tầng nào vượt trần; không cạnh `requires` nào nối hai khái niệm cùng stage; số stage không nhỏ hơn
  cận dưới; bỏ bước cân bằng thì một ca có tầng lệch hẳn phải đỏ.
- **V8:** hai khái niệm khác cụm nhưng cùng tầng nằm **cùng** một stage (ca này đỏ với luật giao cụm hiện tại);
  tầng nhỏ hơn sàn được gộp **trừ khi** phép gộp phá bất biến; đổi thứ tự chương của đầu vào **không** đổi thứ tự
  stage.
- **V9:** τ của một lộ trình trùng khít thứ tự sách bằng 1, đảo ngược hoàn toàn bằng −1; cặp hoà bị loại và được
  đếm riêng; tỉ lệ vi phạm cạnh vàng bằng 0 khi lộ trình tôn trọng mọi cạnh vàng, và danh sách vi phạm nêu đúng cặp.

**Không ghi lại fixture hợp đồng nào** trong đợt này. Đổi prompt là đổi hành vi và phải theo luật riêng đã có; V1
và V2 **không** đổi prompt, chỉ đổi luật phía sau lời gọi.

## Out of Scope

- **Không** chuyển mô hình sang learning space của lý thuyết không gian tri thức. Thiếu dữ liệu học viên thì không
  ước lượng được; nó vào Limitations, không vào mã.
- **Không** dùng conformal prediction để lọc cạnh. Đó là hướng đúng về lâu dài và cần bộ vàng làm tập hiệu chuẩn,
  nhưng lớn hơn đợt này.
- **Không** thu dữ liệu người học, không kiểm định tiên đoán.
- **Không** chạy lại A1–A5 cho bốn tài liệu phát triển. Chúng giữ artifact hiện có; corpus có nhiều cấu hình A3 và
  báo cáo nói rõ điều đó.
- **Không** sửa lỗi mã chữ của trình phân tích ở phase B0. V2 chỉ làm bộ đoán ngôn ngữ miễn nhiễm với nó.
- **Không** đổi mô hình hay nhiệt độ: vẫn `gemini-3.1-flash-lite`, `temperature` 0.
- **Không** cài lượt LLM đặt tên stage trong đợt này; nếu chủ dự án muốn, cắt vé riêng sau — và khi đó phải kèm chỉ
  số ổn định thứ tự, vì đảo thứ tự đầu vào đã được đo là làm τ giữa hai đầu ra của cùng mô hình tụt xuống ~0,64.
- **Không** đổi định nghĩa stage sang "chặng đọc tuần tự". Chủ dự án đã chốt giữ nhóm học song song được.

## Further Notes

**Đường găng đi qua V1 và V2.** Mọi việc còn lại đo được trên artifact đã có, nhưng **bộ vàng thì không**: người
gán không ngồi xuống được cho tới khi hai chương sạch. Nên V1 và V2 phải xong trước, và điều kiện nhận của chúng là
điều kiện **đo trên chương vàng**, không phải trên test tổng hợp.

**V7 và V8 đi cùng nhau.** Bỏ phép giao cụm mà không có trần độ rộng thì tầng đầu phình; có trần mà vẫn giao cụm
thì vẫn vụn. Số đo cho cả hai cùng lúc: 63 → 16 stage, tầng đầu 12 → 8 khái niệm, không mất bất biến nào.

**V9 phải xong trước khi chạy thí nghiệm.** Nếu đo τ bằng lộ trình còn phá hoà theo thứ tự chương (V8) thì đối
chứng đã nhiễm và con số bỏ đi. Thứ tự đúng là V8 rồi mới V9.

**Ngân sách.** V1 buộc chạy lại A3 cho `doc-2` và có thể cho `doc-1`. Lượt A3 `doc-2` gần nhất tốn 1,38 USD. Tổng
đã dùng tới nay khoảng 4,21 USD trên trần 50 USD, nên còn dư — nhưng vé phải ghi số thật của từng lượt.

**Một rủi ro cần nói trước.** V1 giữ lại các tên ký hiệu có cấu trúc, tức bảng ứng viên của `doc-2` sẽ phình. Vé
phải đo số ứng viên trước/sau và kiểm rằng A4 vẫn hợp nhất được — guard của vé 17 ra đời chính vì ký hiệu lọt A3
từng làm A4 dừng. Nếu A4 lại dừng thì đó là thông tin, không phải thất bại: nó nói vấn đề nằm ở A4 chứ không ở A3.

## Sửa đổi sau đo lường (2026-09-23)

Các quyết định dưới đây thay phần tương ứng ở trên. Số liệu và chẩn đoán đầy đủ ở
`report/ke-hoach-dua-do-thi-toi-muc-dung-duoc.md`, mục 13–17.

### V14 — Chỉ số thứ tự và giao thức chấm

- **Chỉ số:** `learning_order_error = (ngược + cùng stage + thiếu đầu) / |vàng|`, trên **vàng hội ý**. Stage là tập
  học song song nên cùng stage chưa bảo đảm học trước; đầu cạnh vắng mặt khỏi lộ trình là lỗi, để việc bỏ node không
  làm mẫu số nhỏ đi. Vàng rỗng cho `None` — chưa đánh giá, không phải đạt.
- **Bộ chấm từ chối** vàng khác `doc_id`, khác phiên bản canonical hoặc chương, hoặc nhắc khái niệm đồ thị không có;
  ghim SHA-256 của mọi tệp đã đọc.
- **Tách phần tất định khỏi phần may rủi.** Cạnh vàng có đường đi trong đồ thị máy luôn được mọi cách xếp hợp lệ tôn
  trọng; cạnh vàng không có đường đi được đặt theo cách phá thế hoà của bộ xếp. Báo cả hai: **tỉ lệ cạnh vàng có đường
  đi** (chất lượng đồ thị, tất định) và U1 của lộ trình đã xuất.
- **Giao thức cho mọi thay đổi ở A10:** chấm so với **phân bố nhiễu** — 30 lần xếp lại cùng đồ thị với cách phá thế
  hoà ngẫu nhiên (hoán vị tên node) — và báo z. Đo được: `doc-1` v10 9,2% ± 2,6; `doc-2` v7 14,4% ± 3,0. Chênh cỡ một
  độ lệch chuẩn là nhiễu. Cổng dạng "U1 không được tăng" cho một can thiệp ở A10 là cổng sai.

### V15 — Cách phá thế hoà của A10 giữ nguyên, có ghi nhận

Cách phá thế hoà hiện tại (`node_id`) tệ hơn cả 30 cách ngẫu nhiên trên hai đồ thị thưa (z +1,67 và +1,77). Đặt vị
trí trong sách làm khoá chính khi đặt node (C9) tốt hơn cả 30 cách ngẫu nhiên trên `doc-1` v7 (z −2,78) nhưng không
giúp gì trên đồ thị dày sau C1 (z −0,65, **+4 stage**); chỉ dùng vị trí sách để phá thế hoà trong Coffman–Graham
(C9b) không hơn ngẫu nhiên. **V8 giữ nguyên** — thứ tự sách không vào bộ xếp — vì hai lý do: dùng nó để xếp rồi dùng
τ để chấm là nhiễm đối chứng, và đòn bẩy thật là recall của đồ thị: khi có đủ ràng buộc, cách phá thế hoà hết quan
trọng.

### V16 — Hai stage thử nghiệm, không nằm trong chuỗi mặc định

- `teaching` (C8): mỗi đoạn định nghĩa có thật sự dạy khái niệm không, hỏi riêng `kind` và `role`. Đạt cổng an toàn
  trên dữ liệu mới (loại nhầm 2/134), **trượt** cổng `doc-1` (bỏ lọt một node hành chính có công thức tính điểm).
  Nhãn `prior_knowledge` chưa đủ tin: kích nhầm bởi giả thiết định lý ("Suppose V is a complex inner product space").
- `verified` (C10): định nghĩa của đích có dùng tiên quyết không. **Trượt**: gỡ 3 cạnh đúng và 4 cạnh sai trong phạm
  vi chấm, giữ 23/29 cạnh dư với lý do hợp lý. Tiêu chí "định nghĩa dùng A" hẹp hơn khái niệm tiên quyết của người
  gán (họ tính cả tiên quyết để *làm* được bài).

Cả hai giữ mã và test để dùng cho phiên bản sau; chuỗi mặc định vẫn là `validated → stages`.

### V17 — Precision cạnh phải đo bằng chấm mù

Precision so với vàng đóng băng không phân biệt được máy sai với vàng thiếu: C10 và cách đọc của reviewer cùng cho thấy
phần lớn cạnh dư là quan hệ hợp lý mà vàng không ghi, hoặc trùng danh tính node. Quyết định chi tiền cho A8 (mở rộng
C1) dựa trên **chấm mù** — `scripts/cham-mu/` — không dựa trên precision so với vàng.
