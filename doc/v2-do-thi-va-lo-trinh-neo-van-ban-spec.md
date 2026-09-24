# v2 — Đồ thị và lộ trình neo vào văn bản

Spec triển khai cho [kế hoạch v2](../report/ke-hoach-v2-do-thi-va-lo-trinh-chuan.md). Quyết định kiến trúc ở
[ADR 0010](adr/0010-lo-trinh-la-day-hoc-chia-module.md). Vé ở [`task/v2-do-thi-lo-trinh/`](../task/v2-do-thi-lo-trinh/00-ke-hoach.md).
Chủ dự án đã duyệt toàn bộ hướng và ngưỡng ngày 2026-09-23.

## Problem Statement

Lộ trình hiện tại sai thứ tự ở mọi cặp khái niệm mà đồ thị không có cạnh, vì bộ xếp tầng tối ưu số tầng rồi đặt các cặp
ấy theo một cách phá thế hoà tuỳ ý; tầng gần như không bao giờ nằm gọn trong một mục của sách. Đồ thị còn thiếu 20–44%
ràng buộc so với bộ vàng. Khái niệm không có neo định nghĩa đáng tin, nên mọi bước đọc "đoạn dạy khái niệm" — loại khái
niệm rác, phán cạnh, nguồn đọc, vị trí dạy — đều đọc nhầm đoạn *dùng*. Và các thước đo hiện có không đủ để nói kết quả
"chuẩn": precision so với bộ vàng không phân biệt máy sai với vàng thiếu, U1 dao động theo may rủi của bộ xếp, chưa có
tập giữ lại sạch, chưa có phép đo nào cho khái niệm.

## Solution

Neo mọi thứ vào văn bản, dùng mô hình cho phần văn bản không tự nói:

- **Thứ tự** neo vào thứ tự dạy của tài liệu: lộ trình là một dãy học (sắp topo ưu tiên vị trí dạy) chia thành module.
- **Khái niệm** neo vào câu định nghĩa nguyên văn; trạng thái "có lên lộ trình không" là thuộc tính của khái niệm.
- **Danh tính** quyết trên hai câu neo, ghi thành bản đồ ở tầng graph.
- **Cạnh ứng viên** lấy từ tên được nhắc trong câu neo; mô hình chỉ phán cặp.
- **Đo** bằng mười tiêu chí Q1–Q10 đã chốt, chấm mù bằng người ở chỗ bộ vàng không đủ, và xác nhận một lần trên tập giữ
  lại với cấu hình đã khoá.

## Tiêu chí nghiệm thu đã chốt (2026-09-23)

| | tiêu chí | phép đo | ngưỡng |
|---|---|---|---|
| Q1 | khái niệm trên lộ trình là kiến thức môn học | kiểm tay mẫu ngẫu nhiên 50 khái niệm / tài liệu | ≥ 97% |
| Q2 | không trùng, không đa nghĩa chưa xử lý | xung đột danh tính còn mở trong phạm vi xuất bản | 0 |
| Q3 | không sót khái niệm trọng yếu | người đọc liệt kê mù trên mục lấy mẫu | ≥ 90% |
| Q4 | cạnh đúng | chấm mù: "không làm sai thứ tự học"; ngược chiều | ≥ 0,90; ≤ 5% |
| Q5 | đủ ràng buộc | tỉ lệ cạnh vàng có đường đi trong đồ thị máy | ≥ 85% |
| Q6 | thứ tự lộ trình | (ngược + thiếu đầu) / \|vàng\| trên dãy học | ≤ 5% |
| Q7 | lộ trình tới mục tiêu | trung bình tỉ lệ tổ tiên-vàng có trong tổ tiên-máy; tỉ lệ đích đủ trọn | ≥ 95%; ≥ 80% |
| Q8 | module mạch lạc | thang 1–5, hai người chấm mù A/B; chỉ số tự động chỉ để kiểm tra tỉnh táo | ≥ 4 / 5 |
| Q9 | nguồn đọc đúng | kiểm tay mẫu 50 câu neo | ≥ 90% |
| Q10 | khái quát | Q1–Q9 trên tập giữ lại, cấu hình đã khoá | đạt Q1–Q9 |

Với mẫu nhỏ, mỗi con số báo kèm khoảng tin cậy Wilson 95%. Điểm ước lượng đạt ngưỡng nhưng khoảng tin cậy còn chứa vùng
trượt thì kết luận là **chưa đủ bằng chứng**, không ép thành đạt. Q8 bỏ ngưỡng tự động đề xuất lúc đầu: chia module theo
ranh giới mục thì tự tối ưu đúng chỉ số đó (ADR 0010).

## User Stories

1. Là người học, tôi muốn lộ trình đi theo thứ tự cuốn sách trừ chỗ sách đặt một khái niệm trước tiên quyết của nó, để
   tôi không phải nhảy lung tung trong sách.
2. Là người học, tôi muốn mỗi module là một buổi học mạch lạc, có tên nói đúng nội dung, để biết buổi này học gì.
3. Là người học, tôi muốn thứ tự bên trong module rõ ràng, thay vì một nhóm "học song song" mà thật ra có phụ thuộc.
4. Là người học, tôi muốn chọn một khái niệm đích và nhận đúng các khái niệm cần học trước nó, theo thứ tự, để không phải
   học cả cuốn.
5. Là người học, tôi muốn mỗi khái niệm trỏ tới đúng câu và đoạn dạy nó, không trỏ vào đề cương hay một câu nhắc qua.
6. Là người học, tôi không muốn thấy `GPA`, `Thang điểm chữ` hay nhãn trong hình trên lộ trình.
7. Là người học, tôi không muốn cùng một khái niệm xuất hiện hai lần dưới hai tên.
8. Là người học, tôi muốn biết vì sao một khái niệm đứng ở vị trí đó (nó cần những gì).
9. Là chủ dự án, tôi muốn mọi lần chạy tốn tiền phải được cho phép rõ ràng, để một thay đổi thuật toán không lặng lẽ tiêu
   tiền.
10. Là chủ dự án, tôi muốn mỗi can thiệp có cổng nhận khoá trước khi chạy, và kết quả trượt được ghi nguyên.
11. Là chủ dự án, tôi muốn biết chính xác mình cần làm gì, bao lâu, trước ngày nào, và việc đó chặn bước nào.
12. Là người đánh giá, tôi muốn đọc được artifact cũ bằng bộ chấm mới, để so lịch sử.
13. Là người đánh giá, tôi muốn con số chính không phụ thuộc may rủi phá thế hoà.
14. Là người đánh giá, tôi muốn một tập giữ lại chưa từng được nhìn để xác nhận lần cuối.
15. Là người viết báo cáo, tôi muốn mỗi con số có đường dẫn tới script, commit và SHA-256 của đầu vào.

## Implementation Decisions

### Gói F — chặn chi tiêu ngầm

**W1 — Mô hình trả tiền được bọc bởi một chốt chặn.** `composition.build_learning_graph(allow_spend=False)` bọc mô hình
Gemini bằng `SpendGuard`; lời gọi `start_session` đầu tiên ném `SpendNotAllowed` khi chưa được phép. Bộ điều phối bắt lỗi
đó và gắn tên stage đang chạy. Lệnh `roadmap` có cờ `--allow-spend`; thiếu cờ thì in stage nào định gọi mô hình và thoát
mã khác 0. Stage đã có cache không gọi mô hình nên chạy lại bình thường. Lý do cụ thể: sau F126, chạy `roadmap` trên bất
kỳ tài liệu nào ngoài `doc-1` sẽ chạy lại pass phụ theo luật mới (~7,4 USD cho `doc-2`).

*Đã cân nhắc:* dự toán số lời gọi trước khi chạy. Cần sửa cả bốn use case trả tiền để công bố khối lượng; để sau, vì chốt
chặn đã đủ ngăn chi ngầm.

### Gói A — A10 neo sách

**W2 — Dãy học.** Sắp topo bằng Kahn với hàng đợi ưu tiên theo khoá vị trí `(chỉ số chunk dạy, vị trí ký tự trong chunk,
node_id)`. Chỉ số chunk dạy lấy theo thứ tự: câu neo (gói B, khi có) → `teaching_order_index` → `first_order_index`. Vị trí
ký tự là `char_start` nhỏ nhất của đoạn căn cứ (`evidence`) nằm trong chunk đó; không có thì xếp sau các khái niệm có vị trí
trong cùng chunk. Kết quả là phần mở rộng tuyến tính gần thứ tự dạy nhất theo nghĩa từ điển; mọi cạnh `requires` (kể cả
cạnh co qua node bị loại) đi từ trước ra sau.

*Đã cân nhắc:* tối ưu khoảng cách Kendall tới thứ tự sách — khó hơn và chưa có bằng chứng hơn; Coffman–Graham — xem ADR.

**W3 — Chia module bằng quy hoạch động.** Chia dãy thành đoạn liền mạch, mỗi đoạn ≤ `W` (mặc định 8, giữ trần hiện có).
Chi phí một phương án = Σ module `[1 + α·((W − cỡ)/W)² + λ_mục·(số mục − 1) + λ_chương·(số chương − 1) +
λ_nhỏ·max(0, sàn − cỡ)]` + Σ vết cắt nằm giữa hai khái niệm cùng mục `λ_cắt`. Mặc định `α = 1, λ_mục = 2, λ_chương = 4,
λ_cắt = 1, sàn = 3, λ_nhỏ = 2`. Bài toán giống ngắt dòng Knuth–Plass: `O(n·W²)`, tối ưu toàn cục, tính bằng số nguyên
(nhân `W²`) để ca hoà là hoà thật; khi hoà, module phía trước đầy hơn (20 khái niệm phẳng → 7 + 7 + 6).

*Phạt dưới sàn thêm sau lần chạy đầu trên bảy tài liệu*: không có nó, một khái niệm bị đồ thị kéo từ mục khác lên thành
module đứng một mình — 13 module như vậy trên `doc-1`, 13 trên `doc-2`. Đây là quan sát cấu trúc, không phải chỉnh trên
bộ vàng (Q6 không phụ thuộc cách chia module). Có phạt: `doc-1` còn 3 (đều ở ranh giới cấu trúc: node hành chính trong
đề cương, khái niệm chỉ dạy trong mục bài tập, nút cuối của chuỗi dài nhất), `doc-2` 0.

Các hệ số là **mặc định thiết kế, không chỉnh trên bộ vàng**: Q6 không phụ thuộc cách chia module, còn độ mạch lạc chỉ
được chấm bằng người (Q8). Lý do từng hệ số: `α` bậc hai ưu tiên module đầy và cân (12 khái niệm → 6 + 6, không 8 + 4);
`λ_mục = 2` làm hai mục 4 khái niệm thành hai module thay vì một module lai; `λ_chương` lớn để gần như không bao giờ vắt
qua chương.

**W4 — Cấp mục chọn theo từng tài liệu.** Mục của một khái niệm là tổ tiên ở cấp ℓ của section chứa chunk dạy nó. Cấp đủ
điều kiện là cấp có trung vị số khái niệm mỗi mục ≥ `W/2`. "Mục" = cấp đủ điều kiện sâu nhất; "chương" = cấp đủ điều kiện
nông nhất. Không cấp nào đủ điều kiện (slide phẳng: mỗi slide 1–2 khái niệm) thì tắt cả hai phạt, chỉ còn phạt cỡ. Lý do
đo được: cấp 2 của sách Axler mịn gần bằng một khái niệm mỗi mục; dùng nó cho ra 97 module vụn.

**W5 — Nhãn và siêu dữ liệu module.** `module_id = module_NNN` theo thứ tự. `title` = tiêu đề mục chiếm nhiều khái niệm
nhất; module vắt qua nhiều mục thì ghép hai tiêu đề đầu bằng " · " — không đặt một tên đẹp để che việc trộn. Mỗi module có
`node_ids` theo thứ tự dãy, `section_ids`, `first_order_index`. Mỗi khái niệm có `sequence_index`, `module_id` và danh
sách tiên quyết trực tiếp (để trả lời "vì sao đứng ở đây").

**W6 — Hợp đồng artifact.** Stage `stages` của artifact graph giữ tên stage pipeline, nhưng payload đổi: `sequence`,
`modules`, `chunk_module_map` (chunk → module sớm nhất trong số các khái niệm nó dạy, kèm mọi module) thay `stages`,
`chunk_stage_map`. `algorithm_id = a10-book-anchored-sequence-v1`. Trang `roadmap.html` hiện module có thứ tự, kiến thức
nền và danh sách bị loại. Bộ chấm đọc `sequence` nếu có, không thì đọc `stages` cũ.

**W7 — Coffman–Graham thành biến thể đối chứng.** Hàm `build_roadmap` cũ ở tầng domain giữ nguyên cùng test; chỉ thôi được
gọi từ chuỗi sản phẩm. Thí nghiệm so sánh gọi nó trực tiếp.

**W8 — Hợp đồng đánh giá đổi theo.** Q6 = `gold_order_violations` trên dãy (mỗi khái niệm một vị trí), nên rổ cùng stage
luôn bằng 0 và lỗi = (ngược + thiếu đầu) / |vàng|. τ so thứ tự dạy được báo dưới tên **độ bám sách**. Điều V8 cấm đưa thứ
tự chương vào bộ xếp được bỏ: lý do cấm là nhiễm đối chứng τ, và đối chứng độc lập nay là Q6. Q6 tất định nên không cần
giao thức nhiễu V14 (giao thức đó vẫn áp cho mọi so sánh dùng Coffman–Graham).

### Gói E — lộ trình tới mục tiêu

**W9 — Lọc lộ trình toàn cục theo tổ tiên.** Với tập đích `T`: giữ các khái niệm thuộc `T` ∪ tổ tiên của `T` trong
chính các module của lộ trình toàn cục, theo đúng thứ tự; bỏ module rỗng. **Không chia module lại**: người học vẫn định
hướng trong cùng khung buổi học với lộ trình đầy đủ ("module 12: chỉ cần 5 trong 8 khái niệm"). Dãy con của một phần mở
rộng tuyến tính vẫn là phần mở rộng tuyến tính của đồ thị con, nên mọi cạnh vẫn đi trước ra sau. Lệnh
`roadmap-target --graph <artifact> --concept <tên, alias hoặc mã>`; một tên khớp nhiều khái niệm thì báo lỗi, không đoán.

**W10 — Q7.** Với mỗi đích vàng có tiên quyết: phủ = |tổ-tiên-vàng ∩ tổ-tiên-máy| / |tổ-tiên-vàng| trên bao đóng bắc cầu.
Báo trung bình, số đích đủ trọn, và cỡ trung vị của tổ tiên máy (để thấy lộ trình có phình không).

### Gói B — neo định nghĩa

**W11 — Ứng viên câu, không phải cả chunk.** Mỗi khái niệm: gom chunk định nghĩa hiện có, chunk có mention cứng, chunk
căn cứ A3; tách câu; giữ câu có tên hoặc alias (so sau NFKC và bỏ khoảng trắng, vì PDF toán cho `𝑉 𝑚` thay `Vm`) và
câu chứa câu trích căn cứ A3 (khớp theo câu trích, không theo offset — offset căn cứ tính trên toàn văn bản); xếp câu
căn cứ và câu có tín hiệu định nghĩa (đã có trong provenance: "là", "được gọi là", "we define", "is called", …)
trước, rồi theo vị trí; lấy tối đa 6 câu từ các chunk khác nhau, kèm một câu ngữ cảnh mỗi phía. Chỉ khớp tên nguyên
văn thì 98/438 khái niệm doc-2 và 22/225 doc-1 không có ứng viên nào (tên mô tả do mô hình đặt, ký hiệu toán); sau
sửa còn 1 và 0 — phần còn lại là khái niệm không có căn cứ A3 (ảnh).

**W12 — Một lời gọi cho mỗi khái niệm, trạng thái là thuộc tính của khái niệm.** Mô hình thấy mọi ứng viên cùng lúc và trả:
câu neo (mã ứng viên + câu trích nguyên văn, kiểm chuỗi bằng mã) hoặc không; và trạng thái `defined_here` /
`introduced_by_example` / `mentioned_only` / `prior_knowledge` / `not_subject_matter` / `uncertain`. `prior_knowledge` chỉ
hợp lệ khi câu trích chứa tín hiệu tường minh (danh sách mẫu kiểm bằng mã: "recall", "previous course", "familiar with",
"đã học", "nhắc lại", …). Luật cố định: có câu neo thì giữ. Đây là C8 v3; nó khắc phục hai lỗi đã đo của v2 (gộp trạng thái
theo từng đoạn, và `prior_knowledge` kích bởi giả thiết định lý).

**W13 — Chạy ở hạ nguồn trước, dời lên thượng nguồn sau.** Lúc đầu stage neo chạy sau `validated` (thay `teaching` v2),
đủ để chấm và dùng cho A10. Khi gói D cần câu neo cho dossier phán cặp, stage neo dời lên trước A8 cùng lần chạy lại A8
duy nhất của gói D. Stage neo chỉ phụ thuộc node, chunk, mention map — không phụ thuộc cạnh — nên dời được.

### Gói C — danh tính

**W14 — Ứng viên và phán.** Ứng viên: hai khái niệm chung tên hoặc alias sau chuẩn hoá; tên này chứa tên kia với tiền tố
chung chung (`Hệ véc tơ …`); hai khái niệm cùng câu neo; một tên có hai câu neo khác nghĩa. Phán trên hai câu neo:
`same` / `different` / `sense_split`. Chung alias chỉ là lý do đưa ra xét.

**W15 — Bản đồ danh tính ở tầng graph, gộp xong phải gỡ chu trình lại.** Kết quả là bản đồ `node_id → node đại diện`
(và nhãn phân nghĩa cho `sense_split`), không sửa canonical. Gộp có thể sinh chu trình (a → b → a' với a' gộp vào a), nên
bản đồ áp **trước** A9 khi dời lên thượng nguồn, còn ở hạ nguồn thì chạy lại hàm gỡ chu trình của A9 (thuần, không gọi mô
hình) sau khi áp. Bộ chấm áp cùng bản đồ lên bộ vàng; tệp vàng không bị sửa. Mọi gộp chạm khái niệm của bộ vàng phải được
chủ dự án duyệt.
Chỉ gộp nhóm mà **mọi cặp** đều được phán `same` — phán theo cặp không bắc cầu được (a≈b, b≈c chưa cho a≈c); nhóm
thiếu phán là nhóm mở, tính vào Q2. Đại diện là khái niệm được dạy sớm nhất. Đo trên lượt 2 của vé 04: "cùng câu neo"
chiếm 57/60 ứng viên doc-1, và mọi cặp đọc tay đầu tiên đều là khái niệm khác nhau định nghĩa chung một câu
(bốn phép biến đổi sơ cấp; tiên nghiệm / hợp lý / hậu nghiệm), nên phán là bắt buộc.

### Gói D — recall có mục tiêu

**W16 — Hỏi cặp theo lợi suất.** (1) Cặp mà câu neo của B nhắc tên A. (2) Phiên pass chính gộp mục vụn (C2), dùng đúng
`plan_main_sessions` có trần token. (3) Chỉ khi (1)–(2) chưa đạt Q5 mới mở rộng sang toàn bộ cặp nghi vấn (C1). Phán cặp
dùng pass phụ hiện có (hai chiều, hoà giải), dossier thêm câu neo của hai đầu.

**W17 — Một lần chạy lại A8 cho mỗi tài liệu.** Neo (B) và bản đồ danh tính (C) dời lên trước A8 cùng lúc với bộ sinh ứng
viên mới, để mỗi tài liệu chỉ trả tiền A8 một lần. Mọi lần chạy đi qua chốt chặn W1.

### Gói G — đánh giá khép kín

**W18 — Ba tập, ba vai.** *Phát triển*: `doc-1`, `doc-2` (bộ vàng cạnh), `doc-3` (nhãn khái niệm đã nhìn thấy), ba tài liệu
của cổng A C8. *Kiểm mới cho gói B*: tài liệu N1 do chủ dự án cung cấp, gán nhãn khái niệm mù trước khi chạy. *Giữ lại*:
`xstk-ch3-1` (bộ vàng chương 10–13 đã gán, chưa từng dùng để chọn can thiệp — khoá từ nay) và một chương N2 gán vàng (2026-09-24: `doc-4`, giáo trình Triết học Mác–Lênin, Chương VIII — 47 khái niệm đích)
mới. Tập giữ lại chỉ mở một lần, với cấu hình đã khoá.

**W19 — Mỗi con số mang theo nguồn gốc.** Commit, đường dẫn và SHA-256 của artifact và nhãn, `algorithm_id`, `prompt_hash`,
chi phí thật. Bộ chấm đã ghim SHA-256 (V14); script phân tích ghi đường dẫn trong kế hoạch.

## Testing Decisions

- **Hàm thuần có test đỏ trước.** Dãy học: mọi cạnh đi trước ra sau; không cạnh thì dãy = thứ tự dạy; sách đặt ngược một
  cạnh thì dãy sửa đúng cặp đó và không xáo phần còn lại; đảo thứ tự đầu vào không đổi kết quả; có chu trình thì báo lỗi.
  Chia module: không module nào vượt `W`; nối các module lại đúng bằng dãy; hai mục 4 khái niệm thành hai module; 12 khái
  niệm cùng mục thành 6 + 6; tài liệu phẳng chỉ chia theo cỡ; tất định.
- **Bất biến trên artifact thật**, kiểm bằng assertion độc lập trên cả bảy tài liệu: mọi khái niệm đủ điều kiện xuất hiện
  đúng một lần; 0 cạnh cứng đi ngược dãy; module ≤ `W`.
- **Đột biến**: bỏ ràng buộc cạnh khỏi hàng đợi, đổi khoá vị trí, bỏ phạt mục — mỗi đột biến phải làm đỏ ít nhất một test.
- **Chốt chặn chi tiêu**: mô hình giả bọc chốt chặn → lời gọi đầu ném lỗi có tên stage; có cờ cho phép thì chạy; stage có
  cache không bị chặn.
- **Bộ chấm**: đọc artifact mới (`sequence`) và cũ (`stages`) cho cùng số trên cùng dữ liệu cũ; Q7 trên đồ thị đồ chơi có
  đáp án tính tay.

## Out of Scope

- Cá nhân hoá theo người học, mô hình người học, RL — cần dữ liệu học viên chưa có.
- Sinh mục tiêu, tóm tắt, quiz cho module (A11) — sau khi module ổn định.
- Gắn media vào module; đổi tên trường `stage_id` của chỉ mục vector (làm cùng A12).
- Sửa canonical hoặc bộ vàng đóng băng.
- Tuyên bố "học song song" trong module — chỉ làm khi có thước đo khắt khe tương ứng.

## Further Notes

- Chi phí dự kiến: F, A, E 0 USD; B ~0,3–0,6 USD; C ~0,1 USD; D ~1–3 USD toàn kho; C1 cho `doc-2` ≤ 7,4 USD nếu cần;
  xác nhận ~1–2 USD. Số dư ≈ 36 USD.
- Việc của chủ dự án, thời lượng và thứ tự: [`task/v2-do-thi-lo-trinh/10-viec-cua-chu-du-an.md`](../task/v2-do-thi-lo-trinh/10-viec-cua-chu-du-an.md).
- Spec tổng (`spec-addendum.md` A10–A13, Pha B), `CONTEXT.md` và spec A9–A10 được cập nhật **cùng commit** với phần mã
  tương ứng, không trước.
