# Spec đánh giá Pha A: luồng chuẩn, vàng người neo văn bản, hợp đồng đánh giá chung

**Ngày:** 2026-10-26 · **Trạng thái:** ready-for-agent · **ADR:** [0029](adr/0029-danh-gia-pha-a-hop-dong-danh-gia-va-vang-neo-van-ban.md) ·
**Kế hoạch:** `report/ke-hoach-danh-gia-pha-a-2026-10-26.md` (39 quyết định Q1–Q39, mục 15) · **Văn liệu:**
`report/nghien-cuu-phuong-phap-danh-gia-pha-a-2026-10-26.md` ("VL §n") · **Bản hội đồng:** `evaluation/trinh-bay-hoi-dong.md` · **Bảo vệ:** 2026-11-14

## Vấn đề

Chủ dự án phải trình bày chất lượng Pha A trước hội đồng ngày 2026-11-14. Thước hiện có không đủ để bảo vệ, vì năm lý do:
- **Mẫu nhỏ:** vàng tiên quyết tiếng Việt chỉ có ở năm cuốn, mỗi cuốn 26–47 đích.
- **Phần lớn không do người làm:** chỉ vàng A8 là của người. A1 là agentic; Q3, vàng A4 và câu neo là của Claude hoặc AI.
- **Phụ thuộc pipeline:** danh sách khái niệm lấy từ canonical, nên P/R có điều kiện trên tập khái niệm của máy. Vàng phải chuyển id mỗi lần A4
  đổi, và không chấm được hệ khác.
- **Không còn sạch:** mọi vàng phát triển đã dùng để chỉnh luồng.
- **Thiếu khâu và thiếu đối chứng:** chưa có thước cho A2, trạng thái dạy, lỗi tách và gộp, trần ứng viên. Chưa có baseline, kể cả câu
  "vì sao không hỏi thẳng LLM". Thống kê đang tính theo cạnh, dù cạnh trong cùng cuốn không độc lập.

Mã chấm cũng rải rác ở nhiều script nghiên cứu, mỗi script đọc artifact theo một kiểu, nên không có một lệnh chạy lại toàn bộ.

## Giải pháp

Dựng một **luồng đánh giá duy nhất** trong thư mục `evaluation/`. Mọi hệ được so (hệ chính, baseline, ablation, oracle, sau này cả bản seminar
không LLM) đều xuất ra một **hợp đồng đánh giá** chung. Bộ chấm chỉ đọc hợp đồng đó cộng **vàng neo văn bản**: vàng do sinh viên chuyên ngành gán
độc lập, ghi theo trang và câu nguyên văn, không lấy danh sách khái niệm của máy. Bước **căn khái niệm** ghép đầu ra máy với vàng, theo luật
viết trước, có nhật ký.

Tập thử gồm 8 giáo trình đầy đủ, mỗi chủ đề một cuốn: toán, lý, hoá, sinh, văn, công nghệ thông tin, kinh tế, luật. Hệ chạy trên cả cuốn.
Phạm vi vàng chia hai mức:
- cấu trúc mục và vai trò vùng: gán cả cuốn;
- khái niệm và quan hệ: gán trên 3 chương bốc theo seed.

Số liệu được báo theo cuốn, có khoảng tin cậy bootstrap phân cấp, ba phép kiểm định chính thức khai trước, quy lỗi theo khâu, và chi phí đi
cùng chất lượng. Giao thức được chốt và ghi hash trước khi chạy tập thử.

## User stories

1. Là thành viên hội đồng, tôi muốn biết lộ trình có dạy đủ khái niệm trọng yếu của một giáo trình chưa từng thấy không, để đánh giá giá trị
   của hệ.
2. Là thành viên hội đồng, tôi muốn biết lộ trình có đặt khái niệm tiên quyết trước khái niệm cần nó không, đo trên quan hệ do người gán.
3. Là thành viên hội đồng, tôi muốn thấy hệ được so với lộ trình theo mục lục, để biết hệ thêm được gì so với cách đơn giản nhất.
4. Là thành viên hội đồng, tôi muốn thấy hệ được so với việc hỏi thẳng một mô hình ngôn ngữ, để biết vì sao cần mười bước.
5. Là thành viên hội đồng, tôi muốn biết mỗi khái niệm và quan hệ có dẫn về đúng câu trong sách không, vì người học cần kiểm lại được.
6. Là thành viên hội đồng, tôi muốn biết đáp án chuẩn do ai làm, làm thế nào, và hai người gán đồng ý với nhau tới đâu.
7. Là thành viên hội đồng, tôi muốn thấy khoảng tin cậy và kiểm định đúng cách cho dữ liệu ít cuốn, để biết chênh lệch có thật không.
8. Là thành viên hội đồng, tôi muốn biết lỗi cuối cùng bắt nguồn từ khâu nào, để thấy nhóm hiểu hệ của mình.
9. Là thành viên hội đồng, tôi muốn biết tạo một lộ trình mất bao nhiêu phút và bao nhiêu tiền cho một giáo trình thật.
10. Là thành viên hội đồng, tôi muốn biết kết quả có ổn định khi chạy lại với đầu vào đổi thứ tự mà nghĩa không đổi.
11. Là thành viên hội đồng, tôi muốn chắc rằng thước đo và luật chấm được chốt trước khi nhóm thấy kết quả.
12. Là chủ dự án, tôi muốn một lệnh chạy lại toàn bộ đánh giá từ PDF tới bảng, để tái lập khi cần.
13. Là chủ dự án, tôi muốn số liệu của từng khâu A1–A10, để trình bày và để chọn khâu nâng cấp.
14. Là chủ dự án, tôi muốn biết trên tập phát triển, trước ngày đóng băng, liệu B5 có hơn luồng không, để không bị bất ngờ trước hội đồng.
15. Là chủ dự án, tôi muốn phiếu gán dễ dùng cho sinh viên không biết lập trình, có danh sách chọn sẵn.
16. Là chủ dự án, tôi muốn chuyển phiếu bất đồng giữa hai sinh viên mà không phải phán nội dung chuyên môn.
17. Là chủ dự án, tôi muốn biết trước dự toán tiền và giờ chạy của mỗi lượt, để duyệt chi.
18. Là chủ dự án, tôi muốn bảng và hình cho báo cáo được sinh tự động từ kết quả, đúng quy định đánh số của trường.
19. Là chủ dự án, tôi muốn phiếu mô tả bộ dữ liệu (datasheet) và mục khai việc dùng AI, theo danh mục báo cáo có trách nhiệm.
20. Là sinh viên gán, tôi muốn hướng dẫn rõ thế nào là một khái niệm, thế nào là quan hệ bám văn bản, kèm ví dụ ngoài môn của tôi.
21. Là sinh viên gán, tôi muốn ghi tên khác của khái niệm và chép câu định nghĩa kèm trang, mà không phải gõ mã.
22. Là sinh viên gán, tôi muốn chọn khái niệm đích và nguồn từ kho đã chốt, để không gõ lại tên.
23. Là sinh viên gán, tôi muốn ghi được khái niệm nguồn nằm ngoài 3 chương bốc, bằng tên và trang định nghĩa.
24. Là sinh viên gán, tôi muốn đánh dấu quan hệ tôi biết nhưng sách không viết ra, mà không làm bẩn phần bám văn bản.
25. Là sinh viên gán, tôi muốn đánh dấu chỗ không chắc.
26. Là sinh viên gán, tôi muốn nộp theo từng chương, để phần đã xong được dùng dù phần sau trễ.
27. Là sinh viên gán, tôi muốn phiếu phán mù không cho biết đầu ra thuộc hệ nào.
28. Là sinh viên duyệt cấu trúc, tôi muốn bản nháp cây mục và vai trò đặt cạnh trang sách, để duyệt nhanh.
29. Là Claude, người giữ sổ tập thử, tôi muốn vàng tập thử nằm ngoài repo, có SHA-256, và mọi script chạy trên tập thử chỉ in trường số trong
    allowlist.
30. Là Claude, tôi muốn căn khái niệm tự động phần lớn, phần còn lại phán mù tên hệ, có nhật ký từng ca.
31. Là Claude, tôi muốn bộ chấm mới ra đúng số của bộ chấm cũ trên cùng đầu vào, để chứng minh không đổi phép đo ngầm.
32. Là Claude, tôi muốn bộ phát lại A9 → A10 tái tạo đúng dãy học đã lưu khi không đổi cạnh, để các ablation phát lại đáng tin.
33. Là Claude, tôi muốn mỗi cạnh vàng bị mất được quy tự động về khâu đầu tiên làm hỏng nó.
34. Là Claude, tôi muốn phân tích công suất bằng mô phỏng trên số liệu tập phát triển, trước khi chốt giao thức.
35. Là Claude, tôi muốn mỗi lượt chạy có bản ghi: commit, hash cấu hình, mô hình, transport, seed, ngày, chi, thời gian theo khâu kể cả giây
    chờ embedding.
36. Là agent cài đặt, tôi muốn ba seam rõ ràng, có fixture nhỏ, để viết test đỏ trên mã chưa có.
37. Là agent cài đặt, tôi muốn các công tắc thêm vào pipeline mặc định tắt và đầu ra y hệt khi tắt.
38. Là nhóm seminar, tôi muốn bản Pha A không LLM chỉ cần xuất hợp đồng đánh giá là được chấm trên cùng vàng.
39. Là người học (gián tiếp), tôi muốn lộ trình được kiểm bằng người học khác cùng ngành, theo rubric dễ hiểu.
40. Là thành viên hội đồng, tôi muốn biết bước suy luận chính, bước phụ, luật R17, bộ đọc nhẹ đóng góp bao nhiêu.
41. Là thành viên hội đồng, tôi muốn biết với khái niệm đúng hoàn toàn thì A8 làm được tới đâu, và với quan hệ đúng hoàn toàn thì cách xếp
    lộ trình tốt tới đâu.
42. Là chủ dự án, tôi muốn khi lịch trễ có thứ tự cắt việc định sẵn (ablation docling → K xuống 3 → cắt ở ranh giới chương), không cắt phương
    pháp.

## Quyết định cài đặt

### 1. Kiến trúc và ba seam

Gói đánh giá nằm riêng trong `evaluation/`, không trộn vào mã pipeline. Nó có ba seam để test:
- **Seam xuất:** kho artifact của một lượt chạy → hợp đồng đánh giá. Đây là adapter duy nhất đọc artifact pipeline, kể cả usage đặt tên module
  ghi ở kho Pha B.
- **Seam chấm:** hợp đồng đánh giá + vàng + bảng căn + giao thức → bảng chỉ số theo cuốn và chương, quy lỗi, thống kê. Phần này thuần: không
  gọi mô hình, không đọc kho, không nhập mã pipeline. Phần lớn test nằm ở đây.
- **Seam phiếu:** manifest sách và bản nháp → phiếu Excel cho người gán; phiếu đã điền → vàng JSON qua validator; hai bản gán → phiếu bất đồng
  → vàng hội ý.

Phần điều phối lượt chạy (gọi CLI pipeline với kho mới, dry-run, sổ chi) là lớp mỏng phía trên, kiểm bằng dry-run và một lượt nhỏ thật trên tập
phát triển. Không có seam thứ tư.

### 2. Hợp đồng đánh giá `danh-gia-xuat-1`

Mỗi lượt chạy của một hệ trên một cuốn cho ra một tệp JSON. Hợp đồng gồm các phần sau; phần nào hệ không có (ví dụ B5 không có cây mục) thì để
`null`, và các thước của phần đó báo "không áp".
- **định danh:** `doc_id`, SHA-256 PDF, số trang; tên hệ, biến thể, lượt nhiễu; commit, hash cấu hình, mô hình, transport, ngày chạy.
- **cấu trúc:** tiêu đề (chữ, cấp, cha, trang, mã dòng nếu có); mục có vai trò vùng; đoạn văn (chunk) với trang, đường mục, vai trò.
- **khái niệm:** mã, tên chuẩn, tên khác, kiểu, trạng thái dạy theo sáu giá trị của A5, câu neo (trang, câu nguyên văn, mã chunk), có trong dãy
  học không, vị trí trong dãy, module; ứng viên A3 gốc gộp vào node (cho thước A4 và B4).
- **cạnh:** nguồn, đích, nguồn gốc (pass chính, pass phụ, luật, baseline), cứng hay mềm, lý do làm mềm (R17 hay khác), câu bằng chứng (trang, câu
  nguyên văn).
- **cặp ứng viên:** các cặp pass phụ đã xét, kèm điểm ML và quyết định; cửa sổ định nghĩa của từng đích (cho thước trần ứng viên và quy lỗi).
- **lộ trình:** dãy học; module (mã, tên, thành viên).
- **chi phí:** theo khâu: giây chạy, giây chờ embedding, số lời gọi mô hình, token vào và ra, số lời gọi embedding, USD; cộng tổng.

Câu nguyên văn trong hợp đồng là chữ đúng như hệ đã có (câu neo lấy từ chunk), không chuẩn hoá. Vị trí chung để so với vàng là **trang cộng câu
nguyên văn**, khớp mờ trong trang (mục 7), không dùng offset ký tự của một bộ đọc cụ thể.

### 3. Bộ xuất cho hệ chính và biến thể

Bộ xuất đọc kho artifact theo đúng chuỗi phiên bản của lượt chạy (graph ở stage `stages`, canonical, chunks đã gán vai trò, ứng viên, manifest
từng stage). Graph artifact đã có hầu hết trường cần (node có `aliases`, `anchor`, `teaching_status`, `sequence_index`, `module_id`; đồ thị có cạnh
pass chính, cạnh pass phụ, cạnh mềm, dãy học, module, mention map).

Chi phí lấy từ đo đạc từng stage đã có (vé 02), cộng chi đặt tên module ghi ở usage của kho Pha B mà lượt chạy dùng. Kho Pha B của mỗi lượt là kho
riêng trong thư mục lượt, không phải kho chung.

**Thay đổi nhỏ trong pipeline:** bộ đo stage thêm bộ đếm **giây chờ embedding** (tổng thời gian nằm trong lời gọi embedding), để báo phút/cuốn có
và không có phần chờ trên Vertex. Bộ đếm chỉ ghi telemetry, không vào payload hay khoá cache.

### 4. Bộ sách và bốc chương

Mỗi cuốn có một bản ghi manifest gồm các trường:
- mã sách, chủ đề, tập (phát triển hay thử);
- SHA-256 PDF, số trang, quyền sử dụng;
- **danh sách chương lấy từ mục lục in**: số, tên, trang đầu, trang cuối, cộng cờ mở đầu, bài tập, phụ lục;
- chương đã bốc, seed.

PDF không vào git.

**Luật bốc chương**, ghi vào giao thức trước khi bốc:
- bốc 3 chương: một trong một phần ba đầu, một ở giữa, một ở cuối;
- chỉ bốc trong các chương thoả luật lọc: dài từ N trang trở lên, không phải chương mở đầu, không phải chương chỉ có bài tập hay phụ lục;
- luật lọc chỉ dùng danh sách chương của manifest, không đọc nội dung, không nhìn đầu ra máy;
- seed ghi trong giao thức.

Tập phát triển gồm xstk ch10–13, doc-1 ch10–12, và một khoảng chương `nhap-mon-ml` bốc cùng luật.

Trước khi bốc, Claude kiểm mỗi PDF là PDF gốc bằng bộ định tuyến đã có, và chỉ in số. Sách không được thuộc D-01, T-01 hay tập phát triển.

### 5. Vàng: năm lớp

Mọi tệp vàng có SHA-256 và ghi phiên bản giao thức gán. Vàng tập thử nằm ngoài repo, trong sổ người giữ của Claude; repo chỉ giữ hash. Vàng tập
phát triển được commit.

- **G1 cấu trúc:** cây mục cả cuốn. Dùng lại định dạng và công cụ của D-02 (bảng dòng theo trang có mã dòng, cây mục trỏ mã dòng), để bộ chấm
  M1/M2/M3 đã có (vé 15) chấm được. Bản nháp do Codex làm từ PDF và bảng dòng, không lấy từ đầu ra A1 của hệ. Một sinh viên duyệt đủ; sinh viên
  thứ hai duyệt lại khoảng 30% số mục để đo đồng thuận. Không có trang L2, nên M4 không áp.
- **G2 vai trò vùng:** vai trò của từng mục G1 (`noi_dung`, `bai_tap`, `de_cuong`, `mo_dau`, `hanh_chinh`, `cuoi_sach`), cách làm như G1.
- **Lỗi cài sẵn trong nháp G1, G2:** người giữ cài 3–5 lỗi đã biết vào bản nháp mỗi cuốn, ghi riêng. Tỉ lệ người duyệt bắt được lỗi cài cho
  biết họ có duyệt thật hay chỉ gật đầu. Lỗi cài được gỡ khỏi vàng cuối.
- **G3 kho khái niệm**, trên 3 chương bốc. Mỗi dòng gồm:
  - chương, tên khái niệm, tên khác;
  - trạng thái: dạy ở đây, dạy qua ví dụ, chỉ nhắc, kiến thức nền;
  - trang và câu định nghĩa chép nguyên văn;
  - cờ không chắc, ghi chú.

  "Khái niệm" theo định nghĩa ở mục 6.2 của kế hoạch: đơn vị kiến thức có tên mà người học phải nắm. Hai sinh viên gán độc lập, rồi hội ý, rồi
  chốt thành **kho chốt**; mỗi khái niệm có mã `G-<sách>-<số>`.
- **G4 quan hệ tiên quyết**, gán sau khi kho chốt. Mỗi dòng gồm:
  - đích: chọn từ kho chốt;
  - nguồn: chọn từ kho chốt, hoặc ghi "ngoài" kèm tên và trang định nghĩa;
  - loại: "văn bản thể hiện" hay "kiến thức chuyên môn";
  - câu bằng chứng và trang;
  - cờ không chắc.

  Hai sinh viên gán độc lập, rồi hội ý. Chỉ số chính chấm trên quan hệ "văn bản thể hiện".
- **G5 phán mù đầu ra máy**, sau khi chạy tập thử. Có ba loại phiếu:
  - (a) khái niệm máy không căn được vào vàng: tối đa 60 mục mỗi cuốn, gộp từ mọi hệ được phán, mã ngẫu nhiên. Phán: dạy, chỉ nhắc, không
    phải khái niệm, rác.
  - (b) cạnh máy nằm ngoài vàng: tối đa 100 mục mỗi hệ mỗi cuốn, theo cách TExEval-2 (VL §6.3). Phán: cần, không cần, ngược chiều. Trộn khoảng
    10% câu đối chứng là cạnh vàng của chính người phán, và 10% cặp ngẫu nhiên không có cạnh.
  - (c) lộ trình: rubric Likert 7 mức có neo cho từng module, cộng so sánh cặp mù hệ chính với B1 và hệ chính với B5, trái phải xáo ngẫu nhiên.

  Hai sinh viên phán mọi mục. Hệ được phán là hệ chính, B1 và B5.
- **Phiếu kiểm căn:** 20% số ca căn tay (mục 7), một sinh viên mỗi chủ đề phán độc lập, phiếu không hiện phán của Claude.

### 6. Phiếu và hội ý

Phiếu là Excel có danh sách chọn sẵn (trạng thái, loại, khái niệm của kho chốt) và cột mã ẩn. Validator chạy phía người giữ khi phiếu về: kiểm
cột bắt buộc, giá trị trong danh sách, trang trong phạm vi chương, câu chép có nằm trong trang đó không (khớp mờ, chỉ cảnh báo). Phiếu sai thì
gửi lại, không sửa hộ.

**Hội ý không gặp mặt:**
1. Trước hết, hai danh sách khái niệm G3 được căn với nhau bằng luật tự động (mục 7). Cặp còn lại Claude đề xuất "có phải cùng khái niệm không"
   và đưa vào phiếu.
2. Phiếu bất đồng chỉ gồm mục hai người ghi khác nhau, kèm câu trích của mỗi bên. Mỗi người ghi "giữ" hoặc "bỏ" cùng một dòng lý do.
3. Luật chốt:
   - cả hai "giữ" thì vào vàng;
   - cả hai "bỏ" thì loại;
   - còn lại là **tranh chấp**: không vào vàng chính, nhưng có trong **vàng hợp** và không có trong **vàng giao**.

Chỉ một vòng. Chủ dự án chỉ chuyển phiếu.

Gán và nộp theo thứ tự chương. Cặp nào không xong trước ngày đóng băng thì vàng chỉ phủ các chương đã đủ hai người. Bộ chấm giới hạn phạm vi đích
theo các chương đó.

### 7. Căn khái niệm

Đầu ra của bước căn là **bảng căn**: mỗi cặp (khái niệm vàng, node máy) có một quan hệ `khop`, `may_rong_hon`, `may_hep_hon` hoặc
`khong_khop`, kèm nguồn quyết định (luật nào, hay phán tay) và nhật ký.

**Luật tự động**, chạy theo thứ tự:
1. Trùng tên chuẩn hoặc tên khác sau chuẩn hoá. Chuẩn hoá gồm NFC, chữ thường, gộp khoảng trắng, bỏ dấu câu ở hai đầu; giữ dấu tiếng Việt.
   Khớp theo ranh giới âm tiết, cùng phép biến đổi cho tên và câu, đúng bài học lỗi chữ "y" (vòng 2 pass phụ, mục 8.11).
2. Câu neo của máy trùng câu định nghĩa vàng: cùng trang, độ giống ký tự sau chuẩn hoá vượt ngưỡng khai trong giao thức.
3. Ký hiệu không dùng để căn, theo định nghĩa "Ký hiệu" trong `CONTEXT.md`.

**Phán tay:** Claude phán các ca còn lại trên một bảng gộp node của mọi hệ, mỗi node mang mã ngẫu nhiên, không lộ tên hệ. Phán tay chỉ cần cho
cặp có ứng viên gần (tên chung âm tiết, hay câu neo cùng trang); các khái niệm vàng không có ứng viên gần thì là `khong_khop` mặc định. Phán tay
được ghi nhật ký, và 20% số ca được sinh viên phán lại độc lập (phiếu kiểm căn).

Các khái niệm nguồn "ngoài" của G4 được căn theo cùng luật, dùng trang định nghĩa ghi kèm.

### 8. Thước

Mỗi thước được tính trên từng chương rồi gộp lên cuốn bằng cộng số đếm. Trung bình chung là trung bình macro theo cuốn. Hai mức căn được báo:
- **nghiêm:** chỉ `khop`;
- **nới:** `khop` cộng `may_rong_hon` và `may_hep_hon`.

Chỉ số chính dùng mức nghiêm.

| Khâu | Thước chính | Định nghĩa | Thước phụ |
|---|---|---|---|
| A1 | M3 | tỉ lệ ký tự thân bài có mục sâu nhất trùng G1, theo bộ chấm D-02 | M1 F1 tiêu đề (khớp khi phủ ≥ nửa dòng, cùng trang); F1 "complete entry" (tiêu đề + cấp + trang); M2 trên tiêu đề khớp, ghi mẫu số; giây/trang |
| A2 | recall `noi_dung` | tỉ lệ mục, và tỉ lệ ký tự, mà G2 gán `noi_dung` được hệ cũng gán `noi_dung` | macro-F1 sáu vai trò; ma trận nhầm lẫn; **lỗi có hại**: tỉ lệ khái niệm G3 có câu định nghĩa nằm trong mục hệ gán khác `noi_dung` |
| A3 | độ phủ khái niệm | tỉ lệ khái niệm G3 trạng thái dạy ở đây hoặc qua ví dụ có node máy căn `khop` | độ chính xác theo G5(a); khái niệm bịa |
| A4 | tỉ lệ tách, tỉ lệ gộp nhầm | tách: khái niệm vàng căn `khop` với ≥ 2 node trong dãy học; gộp nhầm: node căn `khop` với ≥ 2 khái niệm vàng | P/R kiểu B-cubed trên khái niệm căn được |
| A5 | câu neo đúng | node căn `khop` có câu neo trùng câu định nghĩa vàng (đúng câu); cùng chunk thì tính ở mức nới | trạng thái dạy: độ chính xác trên phần không `uncertain` và độ phủ; ma trận nhầm lẫn (ánh xạ sáu giá trị máy sang bốn giá trị vàng ghi trong giao thức) |
| A6/A7 | trần ứng viên | tỉ lệ cạnh G4 (hai đầu căn được) có cặp nằm trong tập cặp pass phụ đã xét, hoặc nguồn nằm trong cửa sổ định nghĩa của đích | — |
| A8 | F1 quan hệ | P/R/F1 cạnh trực tiếp, sau khi ánh xạ cạnh máy qua bảng căn; phạm vi: cạnh G4 "văn bản thể hiện" có đích trong chương bốc; cạnh máy có đích căn vào đích vàng trong phạm vi | P/R bao đóng; precision hiệu chỉnh theo G5(b); máy so với **từng** sinh viên; pass phụ: PR-AUC trên phân phối cặp ứng viên thật |
| A9/A10 | Q6 | (cạnh vàng bị đặt ngược, hoặc có đầu không có trong dãy học) / tổng cạnh vàng trong phạm vi | Q7, Q7b; số chu trình (phải 0), số thành phần liên thông; τ so mục lục (chẩn đoán); rubric và so sánh cặp G5(c) |
| Đầu-cuối | độ phủ khái niệm trong dãy học, cộng Q6 | độ phủ: như A3 nhưng node phải nằm trong dãy học | — |
| Truy nguyên | tỉ lệ bằng chứng có thật | câu neo và câu bằng chứng của hệ khớp mờ được trong văn bản trang ghi kèm, theo ngưỡng giao thức | tỉ lệ khái niệm bịa (tên và mọi tên khác đều không có trong văn bản sách); tỉ lệ khái niệm và cạnh có bằng chứng |
| So với B5 | (Q38, chỉ mô tả) | — | độ phủ theo vị trí chương và độ dài sách; tỉ lệ tách giữa các chương; độ ổn định qua K lượt |
| Chi phí | phút/cuốn, USD/cuốn | tổng các khâu; phút báo cả có và không có giây chờ embedding | theo khâu; lời gọi; token; phút/trang, USD/trang |
| Ổn định | khoảng của chỉ số chính qua K = 5 lượt | min–max và trung bình | Jaccard trung bình của tập cạnh giữa các lượt; tỉ lệ cạnh có mặt ở cả K lượt |

**Đồng thuận người gán:**
- G3, G4: F1 giữa hai người, tức PSA = 2a/(2a+b+c) (VL §6.2). G4 báo cả bản có tín dụng bắc cầu theo luật PREAP.
- G1, G2: Cohen κ cộng % đồng ý.
- Trạng thái dạy: Cohen κ cộng ma trận giữa người.
- Likert: Krippendorff α thứ bậc.
- Phiếu kiểm căn: % đồng ý giữa người và Claude, cộng κ.

**Trần người:** F1 hệ so với từng sinh viên, đặt cạnh F1 giữa hai sinh viên. So với vàng hội ý không cùng thước với F1 người–người (VL §6.4).

### 9. Thống kê

- **Khoảng tin cậy:** bootstrap phân cấp. Mỗi vòng lấy lại cuốn có hoàn lại, rồi lấy lại chương trong mỗi cuốn đã lấy, tính lại thước theo cuốn từ
  số đếm, rồi lấy trung bình macro. 10.000 vòng, khoảng phân vị 95%, seed cố định. Dùng bộ sinh LCG tất định đã có trong lõi chấm, để số giống
  nhau trên mọi máy.
- **So hai hệ:** kiểm định hoán vị ghép cặp phân tầng. Đơn vị hoán vị là chương; mỗi lần hoán vị đổi nhãn hai hệ trong từng chương với xác suất ½,
  rồi tính lại hiệu trung bình macro theo cuốn. 10.000 lần, hai phía.
- **Ba phép kiểm định chính thức, hiệu chỉnh Holm:**
  1. Q6 hệ chính so với B1;
  2. F1 quan hệ hệ chính so với B5;
  3. tỉ lệ bằng chứng có thật hệ chính so với B5.

  Mọi so sánh khác chỉ mô tả, kèm cỡ hiệu ứng và CI.
- **Sign test theo cuốn:** nhị thức chính xác, chỉ để bổ sung. Với 8 cuốn, p < 0,05 chỉ khi cả 8/8 cùng chiều.
- **Nhiễu:** chênh lệch nhỏ hơn dải K lượt không được tuyên bố là hơn.
- **Phân tích công suất bằng mô phỏng:** dùng phương sai đo trên tập phát triển và lượt gán thử. Chạy trước khi chốt giao thức, để báo hiệu ứng
  nhỏ nhất phát hiện được.

### 10. Quy lỗi theo khâu

Mỗi cạnh vàng trong phạm vi mà lộ trình làm sai (thiếu, ngược, hay có đầu ngoài dãy học) được gán vào lý do **đầu tiên** trên chuỗi sau. Mỗi điều
kiện kiểm được từ hợp đồng đánh giá cộng vàng.
1. Câu định nghĩa của một đầu nằm trong mục mà hệ cắt sai hay gán vai trò khác `noi_dung` (A1, A2).
2. Một đầu không có node căn `khop` (A3).
3. Một đầu bị tách hoặc gộp nhầm (A4).
4. Một đầu có trạng thái làm nó ra khỏi dãy học (A5).
5. Cặp không nằm trong tập cặp đã xét, và nguồn không nằm trong cửa sổ định nghĩa của đích (A6/A7).
6. A8 không đề xuất cạnh.
7. Cạnh có nhưng bị làm mềm (R17) hay mất ở A9, hoặc dãy học đặt ngược (A10).

Cạnh máy ngoài vàng được xếp loại: đúng theo G5(b), ngược chiều, bắc cầu của cạnh vàng, hay sai hẳn. Kết quả là bảng thác nước theo cuốn và tổng.

### 11. Hệ được so

Bảng dưới liệt kê mọi hệ, cách chạy và chi phí:

| Hệ | Cách chạy | Chi |
|---|---|---|
| Hệ chính | luồng mặc định từ PDF, kho mới cho mỗi cuốn | có |
| B1 mục lục | node của hệ chính, xếp theo vị trí dạy, không cạnh | 0 |
| B2 luật đơn giản | trên node của hệ chính: cạnh X → Y khi tên X (hay tên khác) xuất hiện trong cửa sổ định nghĩa của Y và X dạy trước Y; dùng bộ khớp tên theo âm tiết đã có; dãy học qua A10 | 0 |
| B3 tiêu đề | mỗi tiêu đề A1 của hệ chính (bỏ số mục) là một khái niệm | 0 |
| B4 gộp theo tên | ứng viên A3 của hệ chính gộp chỉ khi trùng tên sau chuẩn hoá | 0 |
| B5 LLM đọc thẳng | flash-lite đọc văn bản sách, trả khái niệm, câu định nghĩa nguyên văn, quan hệ kèm câu bằng chứng, lộ trình theo lược đồ JSON; B5a một lời gọi cả cuốn, B5b mỗi chương một lời gọi kèm danh sách khái niệm chương trước; chọn sau dry-run trên tập phát triển (Q36) | có, nhỏ |
| docling | `--a1 docling`, chạy lại cả chuỗi, chỉ 3–4 cuốn | có |
| pass phụ LLM | `secondary_mode = llm`, chỉ trên cặp có đích thuộc chương bốc | có |
| tắt R17 | phát lại A9 → A10 không làm mềm cạnh ngược thứ tự sách | 0 |
| bỏ cạnh pass chính | phát lại A9 → A10 chỉ với cạnh pass phụ | 0 |
| bỏ cạnh pass phụ | phát lại A9 → A10 chỉ với cạnh pass chính | 0 |
| tắt A2, tắt lọc A5 | chỉ khi lịch còn chỗ; chạy lại từ khâu tương ứng | có |
| oracle A8 | kho khái niệm G3 dựng thành canonical (câu neo gắn vào chunk chứa câu định nghĩa), chạy A6 → A10 | có, nhỏ |
| oracle A10 | cạnh G4 vào thẳng hàm dãy học của A10, trên node của hệ chính | 0 |

Ghi chú về các ablation phát lại:
- **"Bỏ pass chính" làm theo cạnh, không theo khâu.** Pass phụ ML lấy đặc trưng từ đầu ra pass chính, nên không chạy được pass phụ khi bỏ cả khâu
  pass chính.
- **Bộ phát lại A9 → A10** dùng lại cách của script E4 và tắt R17 (`scripts/pass-phu-ml`): tên khái niệm dùng lại phản hồi đã ghi, không gọi mạng.
  Điều kiện tiên quyết: phát lại với cạnh không đổi phải ra đúng dãy học và cạnh đã lưu.

Yêu cầu riêng cho B5:
- Lời nhắc được viết và thử trên tập phát triển, có lược đồ đầu ra, yêu cầu trích câu nguyên văn. Lời nhắc chốt được ghi nguyên văn vào giao thức
  trước ngày đóng băng.
- B5 chạy K lượt nhiễu bằng K định dạng lời nhắc giữ nghĩa.
- Bộ chuyển đầu ra B5 sang hợp đồng là một adapter của seam xuất.

### 12. Công tắc mới trong pipeline

Mọi công tắc dưới đây có mặc định tắt. Khi tắt, đầu ra phải y hệt hiện tại.
- **Seed xáo ngữ cảnh pass chính:** xáo thứ tự khối ngữ cảnh giữ nghĩa trong lời nhắc pass chính, như cờ `--xao` của script 19j. Dùng cho K = 5
  lượt nhiễu.
- **Bộ lọc cặp pass phụ theo đích:** danh sách đích được phép; chỉ dùng cho ablation pass phụ LLM.
- **Bộ đếm giây chờ embedding** (mục 3).
- **Tắt A2, tắt lọc trạng thái dạy A5:** chỉ cài nếu lịch còn chỗ.

### 13. Điều phối lượt chạy

Mỗi lượt có một thư mục lượt, chứa:
- kho artifact mới, không dùng lại cache của lượt phát triển;
- kho Pha B riêng;
- bản ghi lượt: commit, hash cấu hình, mô hình, transport, seed, ngày;
- dry-run và dự toán trước khi chi;
- sổ chi thật;
- hợp đồng đánh giá xuất ra.

Luật chạy:
- **Transport:** Vertex, mô hình `gemini-3.1-flash-lite`.
- **Song song:** các cuốn chạy song song, mỗi cuốn một kho.
- **Chạy tiếp sau sự cố:** lượt ngắt giữa chừng chạy tiếp từ điểm lưu, không đổi cấu hình. Không xoá hay sinh lại bản đã xong.
- **Tái dùng thượng nguồn:** biến thể chỉ đổi khâu sau (nhiễu, R17, bỏ cạnh, oracle A10) dùng chung thượng nguồn của lượt chính. Biến thể đổi
  khâu đầu (docling, tắt A2) có kho riêng.

### 14. Giữ mù và allowlist

Các luật giữ mù:
- Mọi lệnh chạy trên tập thử chỉ in trường số hay bool trong allowlist. Không in tên, mô tả, câu, hay dict lồng của manifest. Test có chuỗi bí mật giả
  cài trong trường lồng, và phải thấy đỏ trên bản in ngây thơ.
- Vàng tập thử, phiếu của sinh viên và kết quả theo khái niệm của tập thử nằm ngoài repo. Repo chỉ giữ hash và bảng số tổng.
- Agent cài đặt không được giao đường dẫn hay dữ liệu tập thử. Họ làm trên fixture và tập phát triển.

### 15. Giao thức đăng ký trước

Một tệp giao thức trong `evaluation/`, commit trước ngày 07/11, có SHA-256 trong bản ghi mọi lượt tập thử. Tệp gồm:
- RQ;
- chỉ số chính từng khâu và ba phép kiểm định;
- ánh xạ trạng thái sáu sang bốn giá trị;
- ngưỡng khớp mờ;
- luật căn;
- N trang và seed bốc chương;
- K;
- lời nhắc B5 nguyên văn;
- luật xử lý tranh chấp;
- thứ tự cắt khi trễ.

Mọi đổi sau ngày đó được ghi là hậu kiểm.

### 16. Báo cáo

Bộ sinh bảng và hình đọc kết quả, rồi điền các bảng khung ở mục 13 của bản hội đồng: bảng 9 đầu-cuối, bảng 10 từng khâu, bảng 11 ablation, bảng
12 người học. Nó cũng vẽ Hình 3 (điểm theo cuốn, có CI) và Hình 4 (thác nước quy lỗi), theo hướng dẫn `dataviz`. Datasheet cho bộ vàng theo mẫu
Gebru và mục D của danh mục ACL, kèm mục khai việc dùng AI.

## Quyết định kiểm thử

**Test tốt là test hành vi ngoài qua seam:** cho đầu vào nhỏ dựng tay, so với số tính tay. Không test hàm riêng. Mỗi điều kiện bảo vệ phải thấy đỏ
ít nhất một lần (AGENTS.md mục 5). Vé ghi "test đỏ trên mã cũ" khi sửa pipeline.

Seam chấm (phần lớn test):
- Mỗi thước có một fixture ba cuốn, mỗi cuốn hai chương, vài khái niệm và cạnh, với số đáp án tính tay. Có ca biên:
  - mẫu số 0 thì trả `None`, không trả 0;
  - đầu cạnh không căn được;
  - tranh chấp;
  - cạnh mềm;
  - khái niệm bị tách.
- **Phép đối chiếu bộ chấm cũ:** đổi vàng A8 cũ của doc-1 và xstk sang định dạng mới (danh sách khái niệm thành kho khái niệm, id cũ thành bảng
  căn), rồi chấm graph đã ghim. Q6, Q7, Q7b, P/R trực tiếp và bao đóng phải bằng đúng số của bộ chấm cũ.
- **Thống kê:** bootstrap và hoán vị tất định theo seed, cho ra cùng một số trên hai lần chạy. Hoán vị trên hai hệ giống hệt nhau cho p = 1. Hai
  hệ khác xa nhau ở mọi chương cho p < 0,001. Holm tính đúng trên ví dụ sách giáo khoa. Sign test khớp bảng nhị thức.
- **Đồng thuận:** PSA khớp ví dụ của Hripcsak và Rothschild. Tín dụng bắc cầu khớp luật PREAP trên ví dụ dựng tay.
- **Quy lỗi:** mỗi lý do 1–7 có một ca dựng tay rơi đúng vào lý do đó, và không rơi vào lý do sau.

Seam xuất:
- Kho artifact fixture nhỏ (dùng fixture graph đã có của Pha B nếu đủ trường) → hợp đồng đúng lược đồ; trường thiếu thì báo lỗi rõ, không điền
  ngầm.
- Chi đặt tên module lấy đúng từ usage kho Pha B của lượt.
- **Bộ phát lại A9 → A10:** với cạnh không đổi, ra đúng `sequence` và `requires_edges` đã lưu.

Seam phiếu:
- Sinh phiếu rồi đọc lại phải ra cùng dữ liệu (round-trip).
- Validator bắt từng loại lỗi: giá trị ngoài danh sách, trang ngoài chương, cột trống.
- Phiếu bất đồng áp đúng luật chốt ba nhánh.
- Phiếu G5 có đúng tỉ lệ câu đối chứng và không lộ tên hệ.

Pipeline:
- Mỗi công tắc mới khi tắt cho đầu ra y hệt. Có test so artifact trước và sau trên fixture.
- Công tắc xáo cho đầu vào lời nhắc khác nhưng cùng tập khối.
- Bộ đếm giây chờ embedding chỉ ở telemetry, không đổi khoá cache.

Allowlist: script tập thử có test bí mật giả trong `stats` lồng.

B5: parser chạy trên phản hồi đã ghi, không gọi mạng; JSON hỏng thì báo lỗi và lượt đó tính là thất bại, không vá.

**Tiền lệ trong repo:**
- test lõi chấm vàng A8 và roadmap order;
- bộ chấm D-02 và test của nó (vé 15);
- checker T-01 có bí mật giả;
- validator nhãn D-01 chỉ dùng thư viện chuẩn;
- script phát lại E4 và tắt R17;
- fixture quiz Pha B.

**Cổng:** toàn repo qua runner sẵn có, có `--basetemp`. Test của gói đánh giá chạy trong cổng đó.

## Ngoài phạm vi

- Đánh giá Pha B (bài giảng, trợ lý, quiz, tài liệu): làm khi chủ dự án bảo. Hợp đồng và cách giữ tập thử dùng lại được.
- Cài bản Pha A không LLM của seminar. Chỉ bảo đảm hợp đồng đủ trung lập để bản đó xuất được.
- Đo thời gian trên Developer API; T-01; pha 4 của vé 15 trên tập khoá D-02 như một việc riêng.
- Các nâng cấp pipeline mà vòng phát triển chỉ ra: mỗi cái một spec ngắn và vé riêng trong cửa sổ 01–06/11, kể cả hướng lai nếu B5 hơn (Q39).
- Benchmark nước ngoài hay bộ dịch: không dùng làm vàng (kế hoạch, mục trả lời ngày 2026-10-26; ADR 0009).
- Giao diện web cho phiếu gán; sinh viên dùng Excel.

## Ghi chú thêm

- **Lịch** (kế hoạch mục 13):
  - spec và vé, hướng dẫn gán 26–28/10;
  - công cụ 29/10–02/11; gán thử xstk 29–30/10;
  - G3 31/10–03/11, G4 03–06/11, vàng đóng băng 06/11;
  - B5 trên tập phát triển 01/11; vòng nâng cấp 01–06/11;
  - đóng băng mã và giao thức 07/11;
  - chạy tập thử 07–09/11; G5 và kiểm căn 09–10/11;
  - phân tích và viết 10–13/11.
- **Thứ tự ưu tiên cài đặt** để kịp gán và chạy:
  1. seam phiếu (G3, G4), vì người gán cần từ 29/10;
  2. bộ xuất và lõi chấm, đối chiếu với bộ chấm cũ;
  3. căn và quy lỗi;
  4. thống kê;
  5. B5, oracle, công tắc nhiễu;
  6. phiếu G5 và bộ sinh bảng, hình.
- **Chi:** chủ dự án duyệt theo nhu cầu. Ước 110–280 USD cả đợt; dry-run chốt từng lượt. Thời gian chạy trên Vertex là ràng buộc chặt hơn tiền.
- **Bản hội đồng** `evaluation/trinh-bay-hoi-dong.md` phải được cập nhật song song mỗi khi spec hay kết quả đổi.
- **Quy trình:** vé chia bằng `to-tickets`. Agent Sonnet cài, tối đa hai agent song song trên hai worktree không chung tệp; Claude tự cài
  validator và thống kê, có agent soát độc lập. Claude nghiệm thu: đọc diff, chạy lại test, tự viết phép phá. Ghép trên main local, không push.
