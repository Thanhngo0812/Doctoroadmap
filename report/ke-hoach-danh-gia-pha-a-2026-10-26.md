Trạng thái: thiết kế đã được chủ dự án xác nhận ngày 2026-10-26, sau sáu vòng tra hỏi (mục 15). Bước kế: spec (`to-spec`), rồi vé.
Bản trình bày cho hội đồng nằm ở `evaluation/trinh-bay-hoi-dong.md` và được cập nhật song song: kế hoạch này đổi thì bản đó đổi theo.
**Sửa cùng ngày (Q30–Q33):** tập thử đổi từ 16 cuốn 50–70 trang sang **8 giáo trình đầy đủ, mỗi chủ đề một cuốn, cỡ 150–300 trang**. G1, G2
gán cả cuốn; G3, G4 gán trên 3 chương bốc theo seed. Các mục dưới đã sửa theo.

# Kế hoạch đánh giá Pha A dựng lại từ đầu — 2026-10-26

Chủ dự án quyết dựng lại toàn bộ đánh giá Pha A (A1 → A10) trong một luồng chuẩn, đặt ở thư mục `evaluation/`, để báo cáo đề tài
trước hội đồng ngày **2026-11-14**. Lý do: phần lớn thước đã có chỉ chạy trên mẫu nhỏ và còn thiếu nhiều khâu. Tài liệu này kiểm kê
hiện trạng bằng số, rồi ghi thiết kế đã chốt: dữ liệu, người gán, vàng, thước, thống kê, hệ được so, vòng nâng cấp, lịch và chi.

Cơ sở văn liệu nằm ở [nghiên cứu phương pháp đánh giá Pha A](nghien-cuu-phuong-phap-danh-gia-pha-a-2026-10-26.md), gồm 73 nguồn
kiểu IEEE. Các mục dưới đây dẫn tới số mục trong báo cáo đó, ký hiệu "VL §n".

Tài liệu này là báo cáo nghiên cứu, chưa phải spec. Spec (`doc/`) và vé (`task/`) viết sau khi chủ dự án nạp `to-spec` và `to-tickets`.

## 0. Tóm tắt

Thiết kế có năm ý chính:
- **Một luồng duy nhất:** sách → chạy hệ với cấu hình đóng băng → xuất ra một **hợp đồng đánh giá** chung → căn với vàng → chấm từng
  khâu → thống kê theo cuốn → quy lỗi → bảng và hình. Mọi hệ cùng xuất một hợp đồng: bản đồ án, bản seminar không LLM, baseline,
  ablation và oracle.
- **Vàng người, neo vào văn bản.** Sinh viên chuyên ngành ghi cây mục và vai trò vùng của cả cuốn; trên 3 chương bốc, họ ghi khái niệm,
  câu định nghĩa, trạng thái dạy và cạnh tiên quyết theo trang và câu. Vàng không lấy danh sách khái niệm của máy, nên không phải chuyển id khi A4 đổi, và chấm được mọi hệ
  trên cùng vàng.
- **Gán hai giai đoạn:** chốt kho khái niệm (G3) trước, rồi mới gán cạnh (G4). PREAP đo được: cho người gán thêm khái niệm trong lúc
  gán quan hệ thì κ tụt từ 0,62 xuống 0,25 (VL §6.1).
- **Tập thử mới: 8 giáo trình đầy đủ, mỗi chủ đề một cuốn**, cỡ 150–300 trang, gán đôi độc lập. Hệ chạy trên cả cuốn, nên phút/cuốn và
  USD/cuốn đại diện cho sản phẩm. Tập phát triển cũng do sinh viên gán theo cùng giao thức, để vòng nâng cấp dựa trên vàng người.
- **Thống kê theo cuốn, không theo cạnh.** Bootstrap phân cấp; so hai hệ bằng hoán vị ghép cặp trong cùng cuốn; mọi số đặt cạnh
  trần người. Giao thức được chốt và ghi hash trước khi chấm.

## 1. Hiện trạng: thước đã có và vì sao chưa đủ

Bảng dưới kiểm kê theo tệp trong repo ngày 2026-10-26. Cột "ai gán" ghi đúng nguồn nhãn.

| Khâu | Thước hiện có | Dữ liệu | Ai gán | Cỡ | Vấn đề cho hội đồng |
|---|---|---|---|---|---|
| A1 đọc PDF | M1 tiêu đề, M2 cha, M3 gán mục theo ký tự, M4 vai trò dòng, M5 giây/trang (vé 15) | 6 cuốn phát triển; tập khoá 8 cuốn niêm phong | agentic + duyệt agentic | 1.719 nhãn L1, 48 trang L2 (phát triển) | không phải vàng người; R2 trượt c1, c3 của luật pha 4 (đánh đổi do chủ dự án chọn) |
| A2 vai trò vùng | không có thước | — | — | — | từng làm mất 29/62 cạnh vàng xstk; lớp LLM đổi theo cách gom lô dù temperature 0 |
| A3 trích khái niệm | Q3 liệt kê mù, chỉ đo độ phủ | doc-1, doc-2 (6 mục); xstk, doc-4 (84 khái niệm) | AI đọc độc lập (phát triển), Claude (giữ lại v3) | 75 dòng + 84 | không phải người; không đo độ chính xác |
| A4 hợp nhất | vàng A4; "gộp sai mà vàng phát hiện" | 4 cuốn, canonical v1/v2 của chuỗi cũ | Claude | 416 mục | không phải người; gắn id chuỗi v3 đã gỡ; chỉ là cận dưới |
| A5 câu neo | phiếu kiểm neo; Claude đọc | 6 cuốn (có 2 cuốn tiếng Anh) | Claude | 50 mục; 79/84 | không phải người |
| A5 trạng thái dạy | không có thước riêng | — | — | — | — |
| A6/A7 cụm, mention | không đo trực tiếp | — | — | — | không biết trần ứng viên của pass phụ |
| A8 tiên quyết | P/R/F1 trực tiếp và bao đóng; E4 | doc-1 40 cạnh/26 đích, doc-4 72/47, xstk 62/26, doc-2 61/24 (tiếng Anh); T-01 69/46 và 36/37 | **người**, hai người + hội ý | 1–4 chương mỗi cuốn | vàng phát triển đã dùng để chỉnh; danh sách khái niệm lấy từ pipeline |
| A9/A10 lộ trình | Q6, Q7, Q7b, τ so mục lục, chấm mù cạnh dư, bảng kiểm R11 | dẫn từ vàng A8; chấm mù cũ doc-1, doc-2 | người (chấm mù cũ) | như A8 | chưa có đánh giá người cho lộ trình và module bản hiện tại |
| Chi phí, thời gian | thời gian từng stage (vé 02); sổ token | mọi lượt | máy | — | Vertex làm méo phút/cuốn (embedding 11–16 s/request); chi đặt tên module nằm ở kho Pha B |

Bảng trên cho thấy năm vấn đề cấu trúc:
1. **Mẫu nhỏ, ít cuốn.** Vàng tiên quyết tiếng Việt chỉ có ba cuốn phát triển và hai cuốn giữ lại, mỗi cuốn 26–47 đích. Với 5 cuốn trở
   xuống, sign test theo cuốn không bao giờ đạt p < 0,05 (VL §9.2).
2. **Không còn sạch.** Mọi vàng phát triển đã dùng để chỉnh luồng. T-01 đã dùng một lần cho số cuối, và d01-t01 đã mất mù một phần.
3. **Vàng phụ thuộc pipeline.** P/R là có điều kiện trên tập khái niệm của máy, phải chuyển id mỗi lần A4 đổi, và không chấm được hệ khác.
4. **Phần lớn không phải vàng người.** Chỉ vàng tiên quyết A8 là của người.
5. **Thiếu khâu và thiếu đối chứng:** chưa có thước A2, trạng thái dạy, lỗi tách và gộp A4, trần ứng viên A6/A7, độ chính xác A3, đánh
   giá người cho lộ trình; chưa có baseline; thống kê tính theo cạnh.

**Đồng thuận cũ tính lại đúng cách.** Văn liệu khuyên báo đồng thuận cạnh bằng F1 giữa hai người, vì khi chỉ ghi cặp dương thì κ không
tính được (VL §6.2). Báo cáo giữ lại v3 ghi "cùng chọn 20, khác nhau 67", tức chung/hợp = 20/87. F1 cũ vì vậy là 0,37 (xstk), 0,42 và
0,35 (hai cuốn T-01). Mức tham chiếu của PREAP là khoảng 0,60.

## 2. Câu hỏi nghiên cứu

Sáu câu hỏi, mỗi câu có số đo và phép thống kê ở mục 8 và 10:

| RQ | Câu hỏi | Trả lời bằng |
|---|---|---|
| RQ1 | Trên giáo trình tiếng Việt chưa từng thấy, lộ trình có dạy đủ khái niệm trọng yếu và tôn trọng quan hệ tiên quyết thật không? | độ phủ khái niệm vàng trong dãy học, Q6, đánh giá người; so với baseline |
| RQ2 | Từng khâu tốt tới đâu, và lỗi cuối bắt nguồn từ khâu nào? | thước từng khâu, quy lỗi từng cạnh vàng bị mất, oracle |
| RQ3 | Hệ tốn bao nhiêu phút và USD cho một cuốn, chia theo khâu? | sổ chi, thời gian, số lời gọi trên 8 giáo trình đầy đủ; phút/trang, USD/trang |
| RQ4 | Các quyết định thiết kế chính đóng góp bao nhiêu? | ablation |
| RQ5 | Kết quả ổn định tới đâu trước nhiễu đầu vào giữ nghĩa? | K = 5 lượt xáo pass chính |
| RQ6 | (seminar) Thay LLM bằng ML/DL ở từng khâu thì được và mất gì? | cùng vàng, cùng hợp đồng xuất |

## 3. Nguyên tắc thiết kế

Các nguyên tắc dưới đây lấy từ bài học các đợt trước và từ văn liệu:
- **Một cửa vào:** mọi hệ chỉ giao cho bộ chấm một tệp xuất theo hợp đồng đánh giá. Bộ chấm không nhập mã pipeline.
- **Vàng neo vào văn bản:** mọi nhãn ghi trang và câu nguyên văn. Việc khớp đầu ra máy với vàng là bước căn riêng, có luật viết trước
  và nhật ký.
- **Tách phát triển và thử theo cuốn.** Vàng tập thử để ngoài repo, Claude giữ sổ. Script chạy trên tập thử chỉ in trường số trong
  allowlist; test của script có chuỗi bí mật giả.
- **Chốt giao thức trước khi chấm** (VL §12): chỉ số chính, luật quyết, CI, luật căn, K; kèm commit và SHA-256 của vàng. Đổi sau khi
  thấy số thì báo tách riêng là hậu kiểm.
- **Ba tầng nhãn, ba tên gọi** (VL §10.3): vàng người; bạc agentic có người duyệt (G1, G2); bạc. Mọi bảng ghi tầng.
- **Đơn vị thống kê là cuốn.** Cạnh và khái niệm trong cùng cuốn không độc lập.
- **Chất lượng đi cùng chi phí:** mỗi bảng có phút/cuốn, USD/cuốn và transport.
- **Tái lập bằng một lệnh**, từ PDF tới bảng, với kho artifact mới, không dùng lại cache của lượt phát triển.

## 4. Kiến trúc `evaluation/`

### 4.1 Luồng

```text
bo-sach (manifest, SHA-256, 3 chương bốc theo seed)
   │
   ▼
chạy hệ (cấu hình đóng băng, kho artifact mới, Vertex) ──► sổ chi và thời gian từng khâu
   │
   ▼
bộ xuất ──► hợp đồng đánh giá (JSON chuẩn, mọi hệ như nhau)
   │
   ▼
căn máy ↔ vàng (luật tự động viết trước + Claude phán mù tên hệ, có nhật ký; người kiểm 20%)
   │
   ▼
chấm từng lớp: G1 cấu trúc · G2 vai trò · G3 khái niệm/neo/trạng thái · G4 cạnh · G5 phán mù · lộ trình
   │
   ▼
thống kê (bootstrap phân cấp, hoán vị ghép cặp, đồng thuận) ──► quy lỗi theo khâu, oracle
   │
   ▼
bảng, hình, phụ lục, datasheet
```

### 4.2 Thư mục (phác thảo; tên cụ thể chốt ở spec)

```text
evaluation/
  README.md            luồng, lệnh chạy, luật mù; cửa vào duy nhất
  giao-thuc/           giao thức chốt trước, bản có hash
    huong-dan-gan/     hướng dẫn cho sinh viên: G1–G5, rubric lộ trình, phiếu bất đồng; ví dụ tự soạn ngoài 8 chủ đề
  bo-sach/             manifest dev/test: mã sách, SHA-256 PDF, chủ đề, số trang, chương bốc, quyền; datasheet
  vang/
    schema/            JSON Schema từng lớp + validator chỉ dùng thư viện chuẩn
    dev/               vàng phát triển (commit)
                       vàng thử nằm ngoài repo, chỉ hash trong repo
  danhgia/             gói Python: xuất, căn, chỉ số, quy lỗi, thống kê, đồng thuận
  baseline/            B1–B4
  chay/                cấu hình từng lượt (dev, test, ablation, oracle, nhiễu), sổ chi; artifact lớn ngoài git
  bang-hinh/           sinh bảng và hình cho báo cáo
  tests/               test có phép phá; test allowlist có bí mật giả
```

Mã chấm cũ (`domain/gold_scoring.py`, `use_cases/a8_score.py`, `scripts/cham-*`, `scripts/t01/cham_t01b.py`) là điểm xuất phát. Trên cùng
đầu vào, bộ chấm mới phải ra đúng số của bộ cũ ở các chỉ số trùng nhau (Q6, Q7, Q7b, P/R bao đóng) trước khi dùng vàng mới.

### 4.3 Hợp đồng đánh giá (nội dung tối thiểu)

Graph artifact hiện đã có gần đủ trường (`aliases`, `anchor`, `teaching_status`, `sequence_index`, `module_id`, cạnh, dãy học, module).
Hợp đồng chuẩn hoá chúng thành:
- **tài liệu:** `doc_id`, SHA-256 PDF, số trang;
- **cấu trúc:** tiêu đề (chữ, cấp, cha, trang), mục có vai trò;
- **khái niệm:** tên, tên khác, trạng thái dạy, câu neo (trang, câu nguyên văn), có trong dãy học không, vị trí, module;
- **cạnh:** nguồn, đích, cứng hay mềm, câu bằng chứng; cặp ứng viên của pass phụ cùng điểm số;
- **lộ trình:** dãy học, module (tên, thành viên);
- **chi phí:** theo khâu: giây, giây chờ embedding, USD, số lời gọi, token; mô hình, transport, commit, hash cấu hình.

Vị trí chung giữa hệ và vàng là **trang cộng câu nguyên văn**, khớp mờ trong trang. Vì vậy docling và bộ đọc nhẹ chấm được trên cùng
vàng. Hợp đồng phải trung lập, không gắn với graph artifact của bản LLM, để bản seminar xuất được.

## 5. Bộ sách

Bộ sách chia làm hai tập:
- **Tập thử: 8 giáo trình đầy đủ, mỗi chủ đề một cuốn** (toán, lý, hoá, sinh, văn, công nghệ thông tin, kinh tế, luật; Q34 thay triết
  bằng công nghệ thông tin), cỡ 150–300 trang, tránh cuốn
  trên 400 trang. Chủ dự án đang chuẩn bị sách; cuốn nào của tập khoá D-02 hợp chủ đề thì dùng được (đã có quyền và nhãn A1 agentic, vẫn
  phải duyệt lại theo G1). Điều kiện:
  - là PDF gốc (Claude kiểm bằng bộ định tuyến, chỉ in số);
  - không thuộc D-01 (đã dùng huấn luyện pass phụ ML và bộ nhận tiêu đề), T-01 hay tập phát triển;
  - quyền sử dụng đã xác nhận;
  - sách văn là giáo trình lý luận văn học hay ngôn ngữ học, không phải tuyển tập tác phẩm;
  - sách công nghệ thông tin không trùng hai cuốn CNTT của D-01 (hệ quản trị cơ sở dữ liệu, hệ điều hành) hay hai cuốn học máy của tập
    phát triển. Pass phụ ML đã học trên D-01, trong đó có sách CNTT, nên báo cáo ghi rõ đây là cùng ngành nhưng khác cuốn. Sách CNTT hay có
    khối mã nguồn; dry-run sẽ xem A1/A2 xử lý chúng thế nào.
- **Bốc chương:** hệ chạy trên cả cuốn. G1, G2 gán cả cuốn. G3, G4 gán trên **3 chương bốc theo seed** (một chương phần đầu, một phần
  giữa, một phần cuối, khoảng 25–30% cuốn). Cạnh được lấy nguồn từ bất kỳ phần nào trước đó của sách, nên quan hệ xuyên chương vẫn vào vàng
  dù 3 chương không liên quan nhau. Luật bốc ghi vào giao thức trước khi bốc. Ba chương mỗi cuốn cho tầng thứ hai của bootstrap phân cấp.
  - **Không chọn chương theo "nhiều quan hệ"** (Q37): chọn như vậy phải đọc trước nội dung hoặc nhìn đầu ra máy, làm kết quả thiên lệch.
  - **Luật lọc không nhìn nội dung,** chỉ dựa vào cây mục G1: chương phải dài từ N trang trở lên (N chốt trong giao thức), không phải chương
    mở đầu, không phải chương chỉ có bài tập hay phụ lục.
  - **Nguồn ngoài 3 chương** được ghi kèm vị trí: tên khái niệm và trang nơi nó được định nghĩa, để bước căn ghép được với node máy.
- **Tập phát triển (Q35):** xstk ch10–13 (gồm chương gán thử) và doc-1 ch10–12, hai khoảng toán đã có vàng A8 cũ của người nên so được
  giao thức cũ với mới; cộng một khoảng chương của `nhap-mon-ml` (nhập môn học máy, thuộc CNTT), bốc theo seed, cỡ tương đương, để tập phát
  triển không chỉ có sách toán. doc-4 ch8 bỏ vì tập thử không còn môn triết. Sinh viên gán theo giao thức mới (mục 6).
- **T-01 bỏ khỏi đợt này.** Không chấm, không báo.

## 6. Người gán và năm lớp vàng

### 6.1 Người gán

Cách tổ chức người gán đã chốt như sau:
- **Tập thử:** mỗi chủ đề có 2 sinh viên đại học chuyên ngành, ưu tiên năm 3–4 đã học môn. Hai người gán cuốn của chủ đề, độc lập. Báo cáo gọi là "sinh viên chuyên ngành", không gọi là chuyên gia.
- **Tập phát triển:** ưu tiên sinh viên toán và CNTT **khác** các cặp gán tập thử, hai người mỗi khoảng chương. Nếu không có thì chính
  cặp toán và cặp CNTT gán phát triển trước (29/10–01/11), rồi mới gán tập thử.
- **Mù:** người gán không xem đầu ra máy của sách mình gán (kể cả trên web demo) cho tới khi vàng tập thử đóng băng. Vòng nâng cấp do
  Claude và agent làm.
- **Datasheet:** thông tin người gán ghi ẩn danh theo mã (T1, T2, L1…): ngành, năm học, có trả công hay không (VL §12).

### 6.2 Năm lớp

| Lớp | Nội dung | Ai gán | Đồng thuận |
|---|---|---|---|
| G1 cấu trúc | cây mục cả cuốn: tiêu đề, cấp, cha, trang | Codex làm nháp, **không** lấy từ đầu ra A1 của hệ; một sinh viên duyệt đủ | sinh viên thứ hai duyệt lại khoảng 30% số mục |
| G2 vai trò vùng | vai trò từng mục cả cuốn (`noi_dung`, `bai_tap`, `de_cuong`, `mo_dau`, `hanh_chinh`, `cuoi_sach`) | Codex nháp, không lấy từ A2 của hệ; sinh viên duyệt đủ | như G1; Cohen κ và % đồng ý |
| G3 kho khái niệm | trên 3 chương bốc: khái niệm được dạy; câu định nghĩa (trang, câu nguyên văn); trạng thái (dạy ở đây, dạy qua ví dụ, chỉ nhắc, kiến thức nền); tên khác | hai sinh viên độc lập → hội ý → **kho chốt** | F1 giữa hai người trước hội ý |
| G4 cạnh tiên quyết | cạnh X → Y theo PREAP, đích là khái niệm của 3 chương bốc, nguồn ở bất kỳ phần nào trước đó (nguồn ngoài 3 chương ghi kèm trang định nghĩa); kèm câu bằng chứng; cờ "văn bản thể hiện" hay "kiến thức chuyên môn" | hai sinh viên độc lập → hội ý | F1 giữa hai người, có và không tính bắc cầu |
| G5 phán mù | (a) khái niệm máy không căn được: dạy, chỉ nhắc, không phải khái niệm, rác; (b) cạnh máy ngoài vàng: cần, không cần, ngược; (c) rubric lộ trình theo module (Likert 7 mức có neo) và so sánh cặp mù hệ chính với B1 | chính hai sinh viên, mù tên hệ, phiếu có **câu đối chứng** (cạnh vàng của chính họ, cặp ngẫu nhiên) trộn lẫn | hai người phán mọi mục; α thứ bậc cho Likert |

**Khái niệm trong G3** gồm đơn vị kiến thức có tên mà người học phải nắm: khái niệm, định nghĩa, định lý hay định luật có tên, phương pháp
hay quy trình có tên, công thức có tên, phân loại. Không tính ví dụ cụ thể, bài tập, tên người hay tác phẩm (trừ khi là đối tượng học),
ký hiệu đứng một mình. Khái niệm gộp và thành phần được ghi riêng nếu sách dạy riêng từng cái.

**Chỉ số chính chấm trên cạnh bám văn bản.** Cạnh "kiến thức chuyên môn" báo riêng, cho biết hệ bỏ sót bao nhiêu tiên quyết mà sách không
viết ra.

### 6.3 Quy trình gán

Quy trình gán gồm các luật sau:
- Phiếu Excel kèm validator chỉ dùng thư viện chuẩn. Phiếu có câu kiểm biết trước đáp án.
- **Gán thử:** cặp toán gán một chương xstk ngày 29–30/10. Claude đo giờ và đồng thuận thật, sửa hướng dẫn trước khi 14 người còn lại
  bắt đầu ngày 31/10.
- **Gán và nộp theo thứ tự chương.** Cặp nào không xong trước 06/11 thì cắt ở ranh giới chương: vàng chỉ phủ các chương đã gán đủ hai
  người; phần chưa gán không tính là lỗi của hệ.
- **Hội ý không gặp mặt:** Claude sinh phiếu bất đồng (chỉ mục hai người ghi khác, kèm câu trích hai bên); mỗi người ghi "giữ" hoặc "bỏ"
  cùng một dòng lý do; chủ dự án chuyển phiếu một vòng và không phán nội dung. Ca còn bất đồng ghi là **tranh chấp**, bỏ khỏi vàng
  chính, và báo thêm số trên vàng hợp và vàng giao.
- **Công ước lượng** (thô; lượt thử đo lại): mỗi sinh viên khoảng 15–25 giờ cho cuốn của mình (duyệt G1/G2 cả cuốn, G3 và G4 trên 3
  chương, hội ý), cộng 4–5 giờ cho G5 và kiểm phần căn.

## 7. Căn khái niệm máy với vàng

Luật căn chạy theo hai bước:
1. **Tự động**, luật viết trước: trùng tên hoặc tên khác sau chuẩn hoá; câu neo của máy trùng câu định nghĩa vàng (cùng trang, khớp mờ).
2. **Phán tay** cho ca còn lại: khớp, máy rộng hơn, máy hẹp hơn, hay không khớp. Claude phán, không biết node thuộc hệ nào, ghi nhật ký
   từng ca. Một sinh viên mỗi chủ đề phán độc lập 20% số ca trên phiếu mù (09–10/11), rồi so hai bản.

Báo cáo ghi tỉ lệ căn tự động, tỉ lệ căn tay, và độ khớp giữa người và Claude trên mẫu 20%. Luật xử lý ca "rộng hơn" và "hẹp hơn" trong
từng chỉ số được chốt trong giao thức.

## 8. Thước đo theo khâu

Mỗi khâu có một chỉ số chính, theo bảng 13.1 của VL; công thức chính xác chốt trong giao thức. "Chính" là chỉ số được báo trước; chỉ hai
đến ba phép so được kiểm định chính thức (mục 10).

| Khâu | Chỉ số chính | Chỉ số phụ | Vàng |
|---|---|---|---|
| A1 | M3: tỉ lệ ký tự thân bài về đúng mục lá | M1 F1 tiêu đề, F1 "complete entry" (tiêu đề + cấp + trang); M2 có mẫu số rõ; giây/trang, RAM | G1 |
| A2 | recall `noi_dung`, theo mục và theo ký tự | macro-F1, ma trận nhầm lẫn; **lỗi có hại**: tỉ lệ khái niệm vàng có câu định nghĩa nằm trong vùng bị gán không phải nội dung | G2, G3 |
| A3 | độ phủ khái niệm G3, khớp nghiêm và khớp nới | độ chính xác theo phán G5(a) | G3, G5 |
| A4 | tỉ lệ tách và tỉ lệ gộp nhầm theo khái niệm vàng | P/R kiểu B-cubed | G3 |
| A5 | câu neo đúng (trùng câu định nghĩa vàng, hoặc cùng đoạn) | trạng thái dạy: độ chính xác trên phần được phủ và độ phủ (coi `uncertain` là từ chối); ma trận nhầm lẫn | G3 |
| A6/A7 | trần ứng viên: tỉ lệ cạnh vàng có cặp trong tập ứng viên pass phụ, hoặc có nguồn trong cửa sổ định nghĩa | — | G4 |
| A8 | F1 cạnh trực tiếp, trên khái niệm căn được, vàng hội ý, cạnh bám văn bản | P/R bao đóng; precision hiệu chỉnh từ G5(b); pass phụ: PR-AUC trên phân phối cặp ứng viên thật; máy so với **từng** sinh viên, đặt cạnh F1 giữa hai người | G4, G5 |
| A9/A10 | Q6 lỗi thứ tự học (ngược, cùng bậc, ngoài lộ trình; cùng mẫu số) | Q7, Q7b; số chu trình, thành phần liên thông; τ so mục lục (chẩn đoán); G5(c) rubric và so sánh cặp (báo như nghiên cứu thăm dò) | G4, G5 |
| Đầu-cuối | độ phủ khái niệm vàng trong dãy học, cộng Q6 | đánh giá người tổng thể | G3, G4, G5 |
| Truy nguyên | **tỉ lệ bằng chứng có thật**: câu định nghĩa và câu bằng chứng mà hệ trích có nằm nguyên văn trong sách không (khớp mờ trong trang) | tỉ lệ khái niệm bịa (tên không xuất hiện trong sách); tỉ lệ khái niệm và cạnh có bằng chứng | văn bản sách |
| Chi phí | phút/cuốn (tổng và trừ chờ embedding), USD/cuốn | theo khâu; lời gọi; token; phút/trang, USD/trang; đường chất lượng–chi phí | sổ chi |
| Ổn định | trung bình và khoảng của chỉ số chính qua K = 5 lượt | tỉ lệ cạnh giữ nguyên qua các lượt | lượt xáo |

M3 và Q6 không có thước trùng trong văn liệu (VL §13.2). Báo cáo định nghĩa chúng bằng công thức và báo kèm thước gần nhất có trong văn
liệu (F1 "complete entry", P/R cạnh).

## 9. Hệ được so

Mỗi nhóm hệ dưới đây trả lời một RQ:
- **Hệ chính** (RQ1–3): sản phẩm lúc đóng băng (bộ đọc nhẹ, chuỗi gộp, pass chính LLM, pass phụ ML).
- **Baseline** (RQ1); B1–B4 gần như 0 USD:
  - B1: thứ tự sách (dãy học bằng thứ tự dạy, không cạnh);
  - B2: cạnh "X được nhắc trong cửa sổ định nghĩa Y, X dạy trước Y", không học;
  - B3: khái niệm lấy từ tiêu đề mục;
  - B4: gộp chỉ theo tên chuẩn hoá;
  - **B5: LLM đọc thẳng** (Q36): cùng mô hình flash-lite đọc sách và trả luôn khái niệm, câu định nghĩa, quan hệ tiên quyết, lộ trình,
    không qua 10 bước. B5a là một lời gọi cho cả cuốn; B5b là mỗi chương một lời gọi, kèm danh sách khái niệm các chương trước. Chọn B5a
    hay B5b sau khi dry-run thử trên một cuốn phát triển xem đầu ra có vượt trần token không. B5 xuất cùng hợp đồng đánh giá; không có cây
    mục và vai trò nên các thước A1, A2 không áp. Đây là phép so trả lời câu "vì sao cần 10 bước". Nếu B5 đạt gần hệ chính ở thước chất
    lượng, báo đúng như vậy; giá trị của luồng khi đó nằm ở truy nguyên, độ ổn định và khả năng thay khâu bằng mô hình không LLM.
  - **B5 phải công bằng, không phải hình nộm:** lời nhắc viết và thử trên tập phát triển, có lược đồ đầu ra, có hướng dẫn trích câu nguyên
    văn. B5 cũng chạy K lượt nhiễu giữ nghĩa (ví dụ đổi định dạng lời nhắc; chốt ở spec) để so độ ổn định.
  - **Thước phụ khai trước khi so với B5** (Q38), chỉ mô tả, không kiểm định: tỉ lệ khái niệm bịa; độ phủ khái niệm theo độ dài sách (B5a có
    thể chạm trần token đầu ra ở sách dài); tỉ lệ tách giữa các chương (B5b dễ đặt hai tên cho một khái niệm); độ ổn định qua K lượt. Dự
    đoán trước của Claude: luồng hơn ở truy nguyên và khái niệm bịa, B5 hơn ở chi phí; các thước khác chưa rõ. Không thêm thước nào sau khi
    thấy số.
- **Ablation** (RQ4):
  - docling thay bộ đọc nhẹ, chạy lại cả chuỗi, chỉ trên 3–4 cuốn;
  - pass phụ LLM thay ML, chỉ trên các cặp có đích nằm trong 3 chương bốc;
  - bỏ pass chính;
  - tắt R17 (luật làm mềm cạnh ngược thứ tự sách);
  - nếu lịch 07–09/11 còn chỗ: tắt gán vai trò vùng A2 (mọi mục là nội dung), và tắt lọc trạng thái dạy A5 (mọi khái niệm trích được vào
    lộ trình).
- **Oracle** (RQ2): A8 chạy trên kho khái niệm vàng; A10 chạy trên cạnh vàng. Số oracle báo trong cột "thiết lập" riêng, không đặt
  ngang số đầu-cuối (VL §11).
- **Seminar** (RQ6): khâu không LLM nào có thì cắm vào, cùng hợp đồng xuất.

Lượt chi phí riêng trên doc-4 bỏ, vì sách thử nay đã là giáo trình đầy đủ. Thiếu thời gian thì bỏ ablation docling trước.

## 10. Thống kê

Theo VL §9 và §10:
- Chỉ số tính **theo từng cuốn** (mỗi cuốn là một chủ đề); báo bảng từng cuốn và trung bình macro. Không kết luận riêng cho từng ngành.
- CI 95% bằng **bootstrap phân cấp** (lấy mẫu lại cuốn, rồi chương trong cuốn), seed cố định, dùng bộ sinh số LCG tất định đã có. Wilson
  chỉ dùng cho tỉ lệ trên mẫu ngẫu nhiên đơn trong một cuốn (ví dụ phán G5).
- **So hai hệ:** hoán vị ghép cặp, chỉ hoán vị trong cùng cuốn; kèm sign test theo cuốn. Với 8 cuốn, sign test chỉ đạt p < 0,05 khi cả
  8/8 cuốn cùng chiều (p = 0,0078); 7/8 cho p ≈ 0,07. Vì vậy kết luận chính dựa trên hoán vị ghép cặp phân tầng theo cuốn và chương; sign
  test chỉ để bổ sung. Chỉ hai đến ba phép so được kiểm định chính thức, khai trong giao thức. Ba phép kiểm định chính thức
  (Q36), hiệu chỉnh Holm trên cả ba: Q6 hệ chính so với B1; F1 quan hệ hệ chính so với B5; tỉ lệ bằng chứng có thật hệ chính so với B5.
  Các phép so khác (B2–B4, pass phụ ML so với LLM, các ablation) chỉ mô tả.
- **Phân tích công suất bằng mô phỏng** trước khi chốt giao thức, dựa trên phương sai đo ở tập phát triển và lượt thử gán.
- **Nhiễu:** K = 5 lượt xáo ngữ cảnh pass chính giữ nghĩa, khai trước; so hai hệ trên cùng tập lượt xáo. Lượt chạy trễ thì giảm về K = 3 và
  ghi rõ. A2 ghim một bản nhãn cho lượt chính; độ bất ổn A2 đo trên tập phát triển, báo riêng.
- **Cỡ hiệu ứng cộng CI trước, p sau.** Chênh lệch nhỏ hơn dải nhiễu thì không tuyên bố hơn.

## 11. Quy lỗi theo khâu

Mỗi cạnh vàng bị mất, hoặc bị xếp sai thứ tự, được gán vào **lý do đầu tiên** trên chuỗi sau:

| Thứ tự | Lý do | Kiểm bằng |
|---|---|---|
| 1 | câu định nghĩa rơi vào mục mà A1 cắt sai, hoặc A2 gán sai vai trò | G1, G2 |
| 2 | đầu cạnh không được trích (A3) | căn G3 |
| 3 | đầu cạnh bị gộp nhầm hoặc tách (A4) | G3 |
| 4 | trạng thái dạy sai, khái niệm ra khỏi dãy học (A5) | G3 |
| 5 | cặp không vào tập ứng viên (A6/A7) | tập cặp, cửa sổ |
| 6 | A8 không đề xuất cạnh | đồ thị |
| 7 | A10 làm mềm cạnh (R17) hoặc xếp cùng bậc | lộ trình |

Cạnh máy ngoài vàng được xếp loại: đúng nhưng vàng thiếu (theo G5), sai chiều, bắc cầu của cạnh vàng, hay sai hẳn. Bảng quy lỗi cộng hiệu
số oracle trả lời RQ2, và là căn cứ chọn khâu nâng cấp.

## 12. Vòng nâng cấp

Vòng nâng cấp theo bốn luật:
- **Chẩn đoán từ trên xuống, sửa từ dưới lên:** đo cả chuỗi trên tập phát triển cùng oracle, quy lỗi, rồi sửa theo thứ tự thượng nguồn
  trong số các khâu làm mất điểm. Mỗi lần sửa, đo lại cả chuỗi.
- **Khâu "không ổn"** khi thoả ít nhất một điều kiện: (i) gây từ 15% số khái niệm hoặc cạnh vàng bị mất trở lên trong bảng quy lỗi; (ii)
  thua baseline tương ứng; (iii) thấp hơn trần người hơn 0,15 ở chỉ số chính.
- Chỉ chỉnh dựa trên tập phát triển, trong cửa sổ **01–06/11**. **Đóng băng mã và cấu hình ngày 07/11.** Sửa nào không xong ghi vào báo cáo
  là hướng phát triển, kèm số quy lỗi.
- Mỗi sửa đi theo quy trình: spec ngắn → vé → agent Sonnet cài → Claude nghiệm thu.
- **B5 chạy trên tập phát triển ngày 01/11** (Q39), đầu cửa sổ nâng cấp. Nếu B5 hơn luồng ở F1 quan hệ, vòng nâng cấp ưu tiên thử **hướng
  lai**: giữ khung truy nguyên (câu neo có mã, gộp trên cả cuốn), cho A8 hoặc A3 ngữ cảnh dài như B5. Hệ chính lúc đóng băng là bản đã nâng
  cấp, và vẫn được so với B5 trên tập thử.

Ứng viên đã biết từ trước: A2 lớp nhãn LLM không ổn định theo cách gom lô; R17 ở sách xã hội; khái niệm khung làm tiên quyết và neo sai câu
ở A8/A5; cây mục dạng bài giảng ở A1/A2.

## 13. Lịch

Lịch theo ngày bảo vệ 2026-11-14:

| Ngày | Việc | Ai |
|---|---|---|
| 26–28/10 | spec và vé công cụ; hướng dẫn gán bản 1 (chủ dự án duyệt trước 29/10); gom 8 cuốn, kiểm PDF gốc và quyền; bốc chương theo seed | Claude, chủ dự án |
| 29/10–02/11 | agent cài công cụ; gán thử xstk (29–30/10), sửa hướng dẫn; gán tập phát triển (tới 01/11) | agent, Claude, sinh viên |
| 31/10–03/11 | G3 tập thử, hội ý | sinh viên, chủ dự án chuyển phiếu |
| 03–06/11 | G4 tập thử, hội ý; G1, G2 duyệt; đóng băng vàng, ghi hash | sinh viên, Claude giữ sổ |
| 01–06/11 | B5 trên tập phát triển (01/11); đánh giá tập phát triển cùng oracle, quy lỗi; vòng nâng cấp | Claude, agent |
| 07/11 | đóng băng mã, cấu hình, giao thức; dry-run chi | Claude; chủ dự án duyệt chi |
| 07–09/11 | chạy 8 cuốn: hệ chính, baseline, ablation, oracle, K = 5 | Claude |
| 09–10/11 | G5 phán mù; kiểm 20% phần căn | sinh viên |
| 10–13/11 | thống kê, quy lỗi, bảng và hình, chương đánh giá, datasheet, slide | Claude, chủ dự án |

Vàng đóng băng (06/11) trước khi chạy tập thử (07/11). Mọi lượt chạy trên Vertex; phút/cuốn báo cả tổng lẫn phần trừ chờ embedding.

## 14. Chi và công cụ

Về chi và công cụ:
- **Chi LLM:** chủ dự án cho dùng theo nhu cầu và duyệt từng lượt; mỗi lượt có dry-run trước. Ước lượng thô, biên rộng:
  - hệ chính 8 giáo trình đầy đủ: khoảng 25–60 USD;
  - 4 lượt xáo thêm cho pass chính: khoảng 15–60 USD;
  - ablation docling trên 3–4 cuốn: khoảng 15–30 USD; pass phụ LLM trên cặp của 3 chương bốc: khoảng 15–40 USD;
  - oracle, bỏ pass chính, tắt R17: dưới 20 USD;
  - B5 LLM đọc thẳng: vài lời gọi mỗi cuốn, ước dưới 10 USD cả 8 cuốn; ablation A2, A5 (nếu chạy): khoảng 10–30 USD;
  - tập phát triển và nâng cấp: khoảng 10–30 USD.

  Tổng vào khoảng 110–280 USD. Dry-run sẽ chốt số. Thời gian chạy là ràng buộc chặt hơn tiền: trên Vertex, một giáo trình 300 trang có thể
  mất vài giờ vì chờ embedding.
- **Cài công cụ:** Claude viết spec và vé; hai agent Sonnet cài song song trên hai worktree, chia khối không chung tệp; Claude tự cài
  validator và phần thống kê, agent soát độc lập. Claude nghiệm thu đủ: đọc diff, chạy lại test, tự viết phép phá.
- **Tài liệu kèm:** datasheet cho bộ vàng (VL §12); mục khai việc dùng AI: Codex nháp G1/G2, Claude căn khái niệm, Sonnet rà soát.

## 15. Quyết định đã chốt qua tra hỏi (2026-10-26)

| # | Quyết định |
|---|---|
| Q1 | Mức A: hai người độc lập, rồi hội ý |
| Q2 | Chỉ Pha A; Pha B khi chủ dự án bảo |
| Q3 | Chủ dự án gom sách |
| Q4 | Chi theo nhu cầu, chủ dự án duyệt |
| Q5 | Mọi lượt chạy Vertex, tách phần chờ embedding |
| Q6 | Luật "không ổn" ba điều kiện; cửa sổ 01–06/11; đóng băng 07/11 |
| Q7 | Claude căn phần không tự động, mù tên hệ; người kiểm 20% |
| Q8 | Khung dùng chung cho seminar |
| Q9 | Gán thử trên xstk |
| Q10 | Bỏ T-01 khỏi đợt này |
| Q11 | 2 người cùng ngành mỗi chủ đề, gán cuốn của chủ đề (ban đầu là hai cuốn, nay một cuốn theo Q30); hội ý qua chủ dự án |
| Q12 | G1, G2: Codex nháp, người duyệt đủ |
| Q13 | G5: chính hai sinh viên phán, mù, có câu đối chứng (Claude chọn theo uỷ quyền) |
| Q14 | 4 baseline, 4 ablation, 2 oracle; cắt docling trước |
| Q15 | Nhiễu pass chính; A2 ghim nhãn |
| Q16 | Hai agent song song; Claude cài validator và thống kê |
| Q17 | Hội ý một vòng; ca còn lại là tranh chấp, báo vàng hợp và giao |
| Q18 | Cạnh gắn cờ văn bản / kiến thức; chỉ số chính trên cạnh văn bản |
| Q19 | ~~Gán cả cuốn; sách 50–70 trang~~ → thay bằng Q30, Q31 |
| Q20 | Cặp toán gán thử; phiếu Excel kèm validator |
| Q21 | ~~Nhận sách trọn và đoạn cắt~~ → không còn áp dụng: sách thử là giáo trình đầy đủ |
| Q22 | Gán theo thứ tự chương; không kịp thì cắt ở ranh giới chương |
| Q23 | Định nghĩa "khái niệm" như mục 6.2 |
| Q24 | ~~Báo theo trang, cộng lượt chi phí doc-4~~ → báo theo cuốn và theo trang; bỏ lượt doc-4 (Q32) |
| Q25 | K = 5 |
| Q26 | Người gán là sinh viên đại học chuyên ngành, ghi ẩn danh |
| Q27 | Sinh viên gán cả tập phát triển |
| Q28 | Một sinh viên mỗi chủ đề kiểm 20% phần căn, phiếu mù |
| Q29 | Sinh viên khác cho tập phát triển nếu có; không thì cặp toán, triết làm trước, có thể bỏ doc-4 ch8 |
| Q30 | Tập thử: mỗi chủ đề một giáo trình đầy đủ, cỡ 150–300 trang, tránh trên 400 trang |
| Q31 | Hệ chạy cả cuốn; G1, G2 cả cuốn; G3, G4 trên 3 chương bốc theo seed |
| Q32 | Pass phụ LLM chỉ trên cặp của 3 chương; docling 3–4 cuốn hoặc bỏ; giữ K = 5; bỏ lượt doc-4 |
| Q33 | Chủ dự án đang chuẩn bị sách; dùng được cuốn khoá D-02 nếu hợp chủ đề |
| Q34 | Thay triết học bằng công nghệ thông tin trong 8 chủ đề |
| Q35 | Tập phát triển: bỏ doc-4 ch8, thay bằng một khoảng chương `nhap-mon-ml` do sinh viên CNTT gán; Q29 áp cho cặp toán và cặp CNTT |
| Q36 | Thêm B5 "LLM đọc thẳng" (B5a hoặc B5b sau dry-run); vào ba phép kiểm định chính thức; thêm thước truy nguyên; ablation A2, A5 nếu còn chỗ |
| Q37 | Bốc 3 chương đầu, giữa, cuối theo seed; luật lọc không nhìn nội dung; nguồn ngoài 3 chương ghi kèm trang |
| Q38 | Khai trước bốn thước phụ khi so với B5: khái niệm bịa, độ phủ theo độ dài sách, tỉ lệ tách giữa chương, độ ổn định; B5 chạy K lượt |
| Q39 | B5 chạy trên tập phát triển ngày 01/11; B5 hơn ở F1 quan hệ thì ưu tiên nâng cấp theo hướng lai, trước đóng băng 07/11 |

## 16. Rủi ro

Các rủi ro đã biết:
- **Bước căn có thể quyết định điểm** vì máy và người gọi tên khác độ hạt. Giảm bằng luật viết trước, nhật ký, kiểm 20% và báo tỉ lệ căn.
- **Đồng thuận cạnh có thể vẫn thấp** dù gán hai giai đoạn. Khi đó báo trung thực, đặt điểm hệ cạnh trần người.
- **Sinh viên không phải chuyên gia.** Giảm bằng giao thức bám văn bản, cờ "kiến thức chuyên môn", câu kiểm và câu đối chứng.
- **Chỉ 8 cuốn, mỗi chủ đề một cuốn.** Thống kê xuyên cuốn yếu hơn; không kết luận riêng cho từng ngành. Bù một phần bằng tầng chương trong
  bootstrap phân cấp.
- **Vàng quan hệ chỉ phủ 3 chương mỗi cuốn**, không phải cả cuốn. Số A3–A8 có điều kiện trên các chương bốc; G1, G2 vẫn phủ cả cuốn.
- **Thời gian chạy giáo trình đầy đủ trên Vertex.** Lượt 07–09/11 có thể chật; chạy song song nhiều cuốn và dry-run sớm để ước giờ.
- **Lịch 19 ngày.** Thứ tự cắt khi trễ: ablation docling → bớt K về 3 → cắt ở ranh giới chương. Không cắt phương pháp.
- **Đánh giá Pha B** chưa nằm trong kế hoạch này; hợp đồng xuất và cách giữ tập thử dùng lại được.
