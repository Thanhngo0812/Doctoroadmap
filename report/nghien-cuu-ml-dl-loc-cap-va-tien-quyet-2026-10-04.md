# Nghiên cứu ML/DL: lọc cặp trước pass phụ (v4) và học tiên quyết không LLM (seminar) — 2026-10-04

Đây là vé R-02 của [kế hoạch v4](../task/v4/00-ke-hoach.md). Báo cáo trả lời sáu câu hỏi chủ dự án giao ngày 2026-10-04, chỉ dựa trên
nguồn gốc: bài ở hội nghị, tạp chí (ACL Anthology, AAAI, PVLDB, ICLR…), arXiv, trang chính thức của công cụ và bộ dữ liệu, mã nguồn.
Mọi nguồn được đọc ngày 2026-10-04. PDF được tải về máy và đọc bằng `pdftotext`; mọi bảng số đã được đối chiếu lại bằng ảnh trang, vì
công cụ tóm tắt web đã bịa số cho một bài (CPRL) trong lượt đọc đầu. Không có nội dung giáo trình hay dữ liệu dự án nào được gửi lên công
cụ tìm kiếm. Không chạy mã dự án, không gọi API trả tiền.

Báo cáo dùng các quy ước sau:
- Mỗi nhận định và con số từ văn liệu có link tới trang bài ngay tại chỗ; tên đầy đủ tác giả, tên bài, nơi đăng nằm ở mục [Nguồn](#10-nguồn).
- Mục Nguồn ghi mức đọc của từng bài: *đọc toàn văn*, *chỉ đọc tóm tắt*, *chỉ kiểm siêu dữ liệu* (qua Crossref), hoặc **chưa xác minh**. Số
  chỉ thấy qua đoạn trích của công cụ tìm kiếm được ghi **chưa xác nhận**.
- "Số đo dự án" dẫn về tệp trong repo. Đoạn mở đầu bằng *Suy luận:* là ý kiến của người viết, chưa có thí nghiệm.
- Tỉ lệ dương ghi "tính từ số của bài" là phép chia tôi tự làm trên số bài công bố.

---

## Tóm tắt

Chín ý chính của báo cáo:
1. **Chưa có công trình nào làm đúng bài "lọc cặp tiên quyết trước khi hỏi LLM trên giáo trình", nhưng ba dòng văn liệu đã giải bài cùng
   dạng.** Cascade của Viola và Jones chỉnh ngưỡng từng tầng để gần như không bỏ mẫu dương ([CVPR 2001](https://doi.org/10.1109/CVPR.2001.990517)).
   Blocking trong entity resolution đo bằng pair completeness (độ hồi tưởng) và reduction ratio ([ACM CSUR 2020](https://arxiv.org/abs/1905.06167)).
   SUPG chọn ngưỡng cho mô hình rẻ sao cho đạt mục tiêu recall với xác suất lỗi chặn trước, chỉ dùng một ngân sách nhỏ lời gọi "oracle" đắt
   ([PVLDB 2020](https://arxiv.org/abs/2004.00827)). Gần nhất về miền là ACE: xếp hạng cặp khái niệm bằng "tham chiếu ngữ nghĩa", chuyên gia chỉ
   duyệt phần đầu bảng xếp hạng ([JEDM 2024](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737)).
2. **ACE cho một con số cảnh báo.** Bộ chấm một tín hiệu của ACE chỉ đạt recall 1 trên bộ University Course khi gửi đi 68% số cặp; trên
   Metacademy, bớt 50% công duyệt thì path recall còn khoảng 0,9 ([JEDM 2024](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737)).
   Mức bớt lời gọi của bộ lọc dự án vì vậy phải đo trên nhật ký, không suy ra được từ văn liệu.
3. **Tín hiệu bất đối xứng mạnh hơn độ giống, nhưng không được dùng làm luật cứng.** Bỏ nhóm đặc trưng cấu trúc làm F1 tụt 9,2 điểm, bỏ độ
   liên quan ngữ nghĩa chỉ tụt 1,4 ([Pan và cộng sự, ACL 2017](https://aclanthology.org/P17-1133/)). RefD có precision cao nhưng recall chỉ
   0,19–0,42 trên bảy bộ ([Jia và cộng sự, NAACL 2021](https://aclanthology.org/2021.naacl-main.164/)). Trong dự án, chỉ khoảng một nửa cạnh vàng có
   tên tiên quyết nguyên văn trong cửa sổ định nghĩa ([spec v3, R12](../doc/v3-lo-trinh-doc-duoc-spec.md)). Với mục tiêu recall, "tham chiếu ngữ
   nghĩa" bằng embedding nâng path recall trung bình của ACE từ 0,485 lên 0,684.
4. **Nên bắt đầu bằng mô hình cây trên đặc trưng; bỏ GNN học theo từng tài liệu.** Random forest tốt nhất ở Pan 2017 và
   [AL-CPL (AAAI 2018)](https://ojs.aaai.org/index.php/AAAI/article/view/11396). Ở PRELEARN, XGBoost trên đặc trưng đạt accuracy 0,866, sát BERT
   0,887, và ban tổ chức kết luận bộ dự báo quan trọng hơn mô hình ([EVALITA 2020](https://aclanthology.org/2020.evalita-1.54/)). Với khái niệm chưa
   thấy lúc huấn luyện, VGAE và CPRL chỉ còn F1 0,48–0,54, còn cross-encoder BERT trên nội dung đạt 0,73–0,77
   ([Zhu & Zamani, EMNLP 2022](https://aclanthology.org/2022.emnlp-main.585/)). Mỗi giáo trình mới gồm toàn khái niệm chưa thấy.
5. **Số F1 công bố không mang sang được, và bộ lọc phải được chấm bằng recall theo từng tài liệu.** Phần lớn bộ đánh giá cân bằng lớp hoặc lấy
   mẫu âm là cặp ngẫu nhiên cộng cặp đảo chiều, trong khi tỉ lệ dương thật chỉ vài phần trăm: LectureBank 2,2% (tính từ số của bài), MOOCCube
   6%. Đổi miền làm F1 của CPRL tụt từ 0,79–0,80 xuống 0,22–0,64, và accuracy tốt nhất ở PRELEARN tụt từ 0,887 xuống 0,690.
6. **Ngưỡng nên chọn ngoài mẫu theo tài liệu, rồi kiểm mẫu trên từng tài liệu mới.** Tám tài liệu phát triển là quá ít để có bảo đảm kiểu
   conformal tính theo tài liệu. SUPG cho cách hỏi LLM một mẫu nhỏ cặp dưới ngưỡng để có cận tin cậy cho recall của chính tài liệu đó.
   *Suy luận:* chứng nhận được recall ≥ 0,95 cho một cuốn cỡ doc-4 cần cỡ 500 lời gọi kiểm; chứng nhận ≥ 0,99 cần cỡ 2.600 lời gọi (mục 7.5).
7. **Chưng cất nhãn LLM vào mô hình nhỏ có bằng chứng tốt, nhưng học trò không vượt được trần recall của thầy.** Nhãn GPT-3 rẻ hơn nhãn người
   50–96% để mô hình hạ nguồn đạt cùng chất lượng ([Findings EMNLP 2021](https://aclanthology.org/2021.findings-emnlp.354/)). Học trò của
   Cache & Distil bền với nhiễu trong nhãn LLM ([Findings ACL 2024](https://arxiv.org/abs/2310.13561)). GLiNER, một bộ mã hoá cỡ BERT học từ
   nhãn ChatGPT, vượt ChatGPT ở NER zero-shot ([NAACL 2024](https://aclanthology.org/2024.naacl-long.300/)). Bộ lọc chỉ giữ được cạnh mà LLM tìm ra,
   và bản seminar sẽ chép cả lỗi của thầy, ví dụ A2 gán mục "Cách giải" của xstk thành đề cương.
8. **Seminar tiếng Việt đủ công cụ nhưng thiếu dữ liệu gán nhãn.** VnCoreNLP tách từ F1 97,90 ([NAACL 2018](https://aclanthology.org/N18-5012/));
   PhoBERT giới hạn 256 token và đòi văn bản đã tách từ ([README](https://github.com/VinAIResearch/PhoBERT)); BamiBERT nhận 2.048 token, không cần
   tách từ, nhưng mới là preprint 7/2026 ([arXiv 2607.02259](https://arxiv.org/abs/2607.02259)); multilingual-e5-large-instruct dẫn VN-MTEB với điểm
   trung bình 67,99 ([Findings EACL 2026](https://aclanthology.org/2026.findings-eacl.86/)). Tìm kiếm ngày 2026-10-04 không thấy bộ dữ liệu công khai
   nào về tiên quyết hay trích định nghĩa cho tiếng Việt. Vì vậy phải dùng nhãn bạc từ nhật ký LLM để học, và vàng người mới để đo.
9. **Việc đầu tiên tốn 0 USD.** Dựng bảng cặp × đặc trưng × phán quyết từ nhật ký tám tài liệu. Vẽ đường recall–tỉ lệ bớt cho từng luật đơn và
   cho mô hình huấn luyện chia theo tài liệu. Phát lại A9→A10 để đo Q6, Q7 và bao đóng trên vàng; liệt kê từng cạnh vàng bị lọc; mô phỏng kiểm
   mẫu theo tài liệu. Chỉ chi tiền khi đã có các đường cong này.

---

## 1. Bối cảnh: dự án cần gì từ văn liệu

A8 pass phụ hỏi `gemini-3.1-flash-lite` từng cặp khái niệm ứng viên, hai thứ tự trình bày, rồi gộp hai phán quyết. Bộ lọc v4 sẽ đứng trước
lời gọi này. Bản seminar cần một bộ phân loại thay hẳn lời gọi đó.

Bốn ràng buộc rút từ số đo dự án:
- **Tiền.** Ở doc-4 (giáo trình trọn cuốn), pass phụ tốn 43.190 lời gọi và 45,92 USD, tức 91% tiền của cả cuốn; 85,5% cặp được cả hai thứ tự trả
  "không quan hệ"; hỏi lười thứ tự thứ hai (v4-01) bớt 38% bản ghi lời gọi mà không mất cạnh nào
  ([nghiên cứu tiền và thời gian](nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md)).
- **Recall là ràng buộc đang siết.** Trên hai chương vàng, 13/13 ca sai thứ tự học là do thiếu cạnh. Khi mô hình được thấy cặp, 21/21 và 29/29 cạnh
  vàng đều được tìm ra. 78% cạnh tiên quyết là liên cụm (31/40 và 48/61), và cạnh "ngầm" mà không bộ sinh ứng viên nào với tới chiếm 17,5% và 23,0%
  cạnh vàng ([kế hoạch đưa đồ thị tới mức dùng được](ke-hoach-dua-do-thi-toi-muc-dung-duoc.md)). Luật cũ chỉ hỏi cặp cùng cụm đã bỏ 78% cạnh
  vàng (F126, chú thích trong [`secondary.py`](../src/doc2roadmap/domain/secondary.py)).
- **Cửa sổ định nghĩa.** Cạnh cứng `can_de_hieu` phải có câu trích nguyên văn trong cửa sổ gồm câu neo, tối đa bốn câu trước và hai câu sau.
  Chỉ khoảng một nửa cạnh vàng có tên tiên quyết nguyên văn trong cửa sổ. Đo trên doc-1: cạnh có tên trong cửa sổ đúng theo bao đóng vàng
  0,88, không có tên thì 0,50 ([spec v3, R12](../doc/v3-lo-trinh-doc-duoc-spec.md)).
- **Đa ngôn ngữ.** Luồng sản phẩm không được chứa danh sách từ hay regex của một ngôn ngữ ([spec v3](../doc/v3-lo-trinh-doc-duoc-spec.md),
  mục "Nguyên tắc: tài liệu đa ngôn ngữ"). Bản seminar được miễn điều này vì chỉ làm tiếng Việt.

Dữ liệu sẵn có cho học máy gồm ba lớp. Thứ nhất, mỗi cặp ứng viên mang nhãn nguồn `same_section`, `citation_hard`, `citation_soft`, `contact`,
`proposed_relation` ([`mentions.py`](../src/doc2roadmap/domain/mentions.py)). Thứ hai, hồ sơ cặp chứa đoạn bằng chứng, cửa sổ định nghĩa, mô tả,
thứ tự provenance, trọng số kênh `exact`/`dense` của cặp cụm và đường gián tiếp ([`secondary.py`](../src/doc2roadmap/domain/secondary.py)).
Thứ ba, phán quyết của mô hình gồm `decision` ∈ {`create`, `no_direct_relation`, `indirect_path`, `defer`}, chiều cạnh, `prerequisite_kind`,
`evidence_kind`, câu trích và `chunk_ids`. Ở doc-2, 9.513 cặp được hỏi và 1.060 cặp thành cạnh
([kết quả vé 12](ket-qua-v3-12-cuoi-2026-10-03.md)).

---

## 2. Câu hỏi 1 — Học quan hệ tiên quyết giữa khái niệm

Phần này lần lại từng bài gốc. Bản đồ rộng hơn, gồm cả các bài thời LLM như Graphusion, đã có ở
[báo cáo A6–A8](nghien-cuu-a6-a8-cum-chu-de-va-2b.md) mục 3 và không lặp lại ở đây.

### 2.1 Sáu hướng chính và kết quả định lượng

Bảng dưới xếp các hướng theo loại mô hình; mọi số đã đối chiếu với bảng trong toàn văn trừ chỗ ghi khác.

| Hướng | Công trình | Kết quả báo cáo | Điều cần giữ cho dự án |
|---|---|---|---|
| Đặc trưng thủ công, không học | RefD ([EMNLP 2015](https://aclanthology.org/D15-1193/)) | bộ Course: F1 74,7/75,1 (CS), 71,9/66,7 (MATH), so với MaxEnt 66,1 và 63,1; CrowdComp, huấn luyện khác miền: accuracy 60,0/61,2 so với MaxEnt 60,4 | công thức chỉ cần một hàm "A tham chiếu B": *"links in Wikipedia, mentions in books, citations in papers"* |
| Đặc trưng thủ công, không học | Pal, Arora & Goyal ([arXiv 2011.10337](https://arxiv.org/abs/2011.10337), preprint) | vị trí trong sách + luật thứ tự cứng: AUPRC 0,69–0,75 so với RefD 0,35–0,73 | luật cứng cấm mọi cạnh ngược thứ tự sách |
| Có giám sát trên đặc trưng | Pan và cộng sự ([ACL 2017](https://aclanthology.org/P17-1133/)) | random forest F1 72,6 (ML), 72,5 (DSA), 71,1 (CAL); hơn SVM, NB, LR 7,0/11,1/8,3 điểm F1 trung bình | cây hợp hơn tổ hợp tuyến tính vì mỗi đặc trưng là "một bộ phân loại yếu độc lập" |
| Có giám sát trên đặc trưng | AL-CPL ([AAAI 2018](https://ojs.aaai.org/index.php/AAAI/article/view/11396)) | random forest F1 76,7/89,5/69,9/88,6, AUC 92,2–97,8 (bốn miền) | bộ dữ liệu lấy từ concept map của giáo trình |
| Mạng cặp (Siamese) | PREREQ ([IAAI 2019](https://arxiv.org/abs/1811.12640)) | University Course: P 46,76, R 91,64, F1 59,68; NPTEL: F1 60,73 | recall cao, precision thấp |
| GNN, VGAE | LectureBank ([AAAI 2019](https://arxiv.org/abs/1811.12181)); R-VGAE ([COLING 2020](https://aclanthology.org/2020.coling-main.99/)); CPRL ([NAACL 2021](https://aclanthology.org/2021.naacl-main.164/)) | LectureBank: VGAE R 0,895–0,921 nhưng P 0,545–0,599; SVM trên Doc2Vec có F1 cao nhất 0,740–0,761. CPRL (R-GCN + Siamese + đặc trưng cặp): F1 0,630–0,860 trên bảy bộ | học biểu diễn cho từng khái niệm của một đồ thị cố định |
| Mô hình ngôn ngữ huấn luyện sẵn | PRELEARN ([EVALITA 2020](https://aclanthology.org/2020.evalita-1.54/)); Zhu & Zamani ([EMNLP 2022](https://aclanthology.org/2022.emnlp-main.585/)) | BERT tiếng Ý: accuracy 0,887 trong miền, 0,690 khác miền (tập kiểm tra cân bằng); cross-encoder BERT cho khái niệm chưa thấy: F1 0,732–0,767 | đầu vào là tên kèm một đoạn văn mô tả khái niệm |
| LLM | ACE ([JEDM 2024](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737)) | University Course: GPT-4o-mini zero-shot P 86,70, R 35,80; thêm RAG: P 87,23, R 61,11, F1 71,92 | LLM hỏi theo cặp: precision cao, recall thấp |

### 2.2 Công trình trên giáo trình và sách

Wang và cộng sự ([CIKM 2016](https://www.microsoft.com/en-us/research/publication/using-prerequisites-extract-concept-maps-textbooks/)) dựng concept map
từ giáo trình, suy tiên quyết bằng Wikipedia và tối ưu đồng thời hai bài toán con. Tôi chỉ đọc được tóm tắt: máy chủ PSU từ chối kết nối, còn ACM DL
chặn tải. Đặc trưng giáo trình của bài này được hai bài sau mô tả lại. Pan và cộng sự ghi bài dùng *"3 Textbook features and 6 Wikipedia
features"*; bản chỉ dùng ba đặc trưng giáo trình, họ gọi là T-SRI, đạt F1 62,1–64,0 trên dữ liệu Coursera ([ACL 2017](https://aclanthology.org/P17-1133/)).
CPRL dùng lại "ToC distance" ([NAACL 2021](https://aclanthology.org/2021.naacl-main.164/)).

Các công trình còn lại có dữ liệu giáo trình cụ thể:
- **AL-CPL** lấy concept map giáo trình của Wang và cộng sự cho bốn miền (data mining, hình học, vật lý, tiền giải tích; 89–224 khái niệm,
  826–2.060 cặp có nhãn). Chuyên gia sửa các nhãn vi phạm thứ tự bộ phận, rồi bộ dữ liệu được mở rộng: thêm (B, A) làm âm nếu (A, B) dương, thêm
  (A, C) làm dương nếu (A, B) và (B, C) dương ([AAAI 2018](https://ojs.aaai.org/index.php/AAAI/article/view/11396)). Một đặc trưng văn bản của bài là
  "A có xuất hiện trong câu đầu của trang B không", với lý do câu đầu *"is usually the definition of the concept"*.
- **CPRL** dựng bộ Textbook từ sáu giáo trình tiếng Trung cho mỗi miền (giải tích, cấu trúc dữ liệu, vật lý): 84–139 khái niệm, 439–623 quan hệ.
  Đặc trưng cặp gồm LOrd (RefD tính trên chuỗi học liệu), khoảng cách mục lục, trùng đầu từ, khoảng cách độ phức tạp. Gộp sáu giáo trình cùng miền
  bằng bỏ phiếu làm kết quả tăng rõ (Hình 6) ([NAACL 2021](https://aclanthology.org/2021.naacl-main.164/)). Bài ghi bộ dữ liệu *"will be publicly
  available later"*.
- **Pal, Arora & Goyal** coi khái niệm xuất hiện đúng một lần trong một mục là "tham chiếu hay ví dụ", xuất hiện hơn một lần là "được bàn". Họ áp
  luật cứng: khái niệm xuất hiện trước không bao giờ nhận khái niệm xuất hiện sau làm tiên quyết. Luật này làm AUPRC tăng rõ (Hình 4)
  ([arXiv 2011.10337](https://arxiv.org/abs/2011.10337), preprint chưa bình duyệt).
- **PREAP** là giao thức gán nhãn trong lúc đọc giáo trình. Đồng thuận giữa người gán theo PREAP là 0,45–0,71 trên năm miền. Gán mọi cặp khái niệm theo
  kiến thức nền chỉ đạt 0,16–0,60, và gán mọi cặp có kèm văn bản chỉ đạt 0,01–0,27. Hai phương pháp tự động (RefD và burst analysis) kém mọi cách gán
  tay cả về độ đầy đủ lẫn độ chính xác ([Technology, Knowledge and Learning 2023](https://doi.org/10.1007/s10758-023-09682-6)).
- Labutov và cộng sự có bài về kỹ thuật bán giám sát để khai phá kết quả học và tiên quyết ([KDD 2017](https://doi.org/10.1145/3097983.3098187)).
  Tôi chỉ kiểm được siêu dữ liệu, nên việc bài có dùng giáo trình hay không **chưa xác minh**.

*Suy luận:* luật thứ tự cứng của Pal và cộng sự xung đột với số đo dự án. Ở doc-4 (triết học), 5 cạnh vàng mà máy đã tìm đúng bị làm mềm vì ngược
thứ tự sách, do sách nêu quy luật trước rồi mới định nghĩa thành phần ([kết quả tập giữ lại v3](ket-qua-tap-giu-lai-v3-2026-10-04.md)). Vị trí trong
sách chỉ nên là đặc trưng mềm của bộ lọc, không được thành luật lọc.

### 2.3 Bộ dữ liệu công khai và mức hiệu năng

Bảng dưới cho thấy cỡ, tỉ lệ dương và cách đánh giá; cột cuối là kết quả tốt nhất tôi đọc được trong các bài ở mục 2.1.

| Bộ dữ liệu | Văn bản nguồn | Cỡ | Tỉ lệ dương | Cách đánh giá | Kết quả tốt nhất đã đọc |
|---|---|---|---|---|---|
| CrowdComp ([BEA 2012](https://aclanthology.org/W12-2037/)) | Wikipedia, 5 miền | 1.600 cặp, 206 dương (Bảng 1 của RefD) | ≈ 13% (tính từ số của bài) | huấn luyện khác miền, cân bằng bằng oversampling | accuracy 61,2 (RefD, TF-IDF) |
| Course ([EMNLP 2015](https://aclanthology.org/D15-1193/)) | trang môn học, nối với Wikipedia | CS 678 cặp/108 dương; MATH 658/75 | 16% và 11% (tính từ số của bài) | 5-fold trong miền | F1 75,1 (CS), 71,9 (MATH) |
| University Course ([AAAI 2017](https://ojs.aaai.org/index.php/AAAI/article/view/10550)) | mô tả 654 môn CS của 11 trường Mỹ | 1.008 cặp khái niệm dương | — | âm = cặp ngẫu nhiên + cặp đảo | F1 0,723 (CPRL) |
| MOOC ([ACL 2017](https://aclanthology.org/P17-1133/)) | phụ đề Coursera: ML, DSA, CAL | 128–244 khái niệm; gán 25% mọi cặp | 23–31% (tính từ Bảng 1) | 5-fold; κ 0,59–0,65 | F1 72,6 / 72,5 / 71,1 |
| AL-CPL ([AAAI 2018](https://ojs.aaai.org/index.php/AAAI/article/view/11396)) | concept map giáo trình, 4 miền | 826–2.060 cặp có nhãn | 25–35% trên cặp có nhãn (tập con, đã mở rộng bắc cầu) | 5-fold | F1 69,9–89,5 |
| LectureBank ([AAAI 2019](https://arxiv.org/abs/1811.12181)) | 1.352 tệp bài giảng NLP | 208 khái niệm, 921 cạnh; κ 0,7 | 921 dương / 41.829 âm ≈ 2,2% (tính từ số của bài) | tập kiểm tra cân bằng | F1 0,761 (SVM); 0,860 (CPRL) |
| ITA-PREREQ / PRELEARN ([EVALITA 2020](https://aclanthology.org/2020.evalita-1.54/)) | trang Wikipedia tiếng Ý của các khái niệm AL-CPL | 457 khái niệm, 6.607 cặp | 22,91% (sau mở rộng) | tập kiểm tra cân bằng 50/50 | accuracy 0,887 trong miền, 0,690 khác miền |
| MOOCCube ([ACL 2020](https://aclanthology.org/2020.acl-main.285/)) | MOOC tiếng Trung | 3.500 cặp gán tay | *"only 6% of concept pairs maintain a solid prerequisite relation"* | — | F1 0,688 (PREREQ-S) |
| Textbook của CPRL ([NAACL 2021](https://aclanthology.org/2021.naacl-main.164/)) | 6 giáo trình tiếng Trung × 3 miền | 84–139 khái niệm, 439–623 quan hệ | — | âm ngẫu nhiên + đảo, oversampling 3,5× | F1 0,788–0,802 |

Bảng này cho ba điểm cần nhớ khi đọc số:
- **Số F1 bị thổi lên vì cách lấy âm.** LectureBank, PRELEARN và CPRL chấm trên tập cân bằng hoặc tập có âm là cặp ngẫu nhiên cộng cặp đảo. Trong
  một giáo trình thật, dương hiếm hơn nhiều: LectureBank khoảng 2,2%, MOOCCube 6%. Theo ACE, đồ thị chuyên gia thường có 5–15% cặp vô hướng là cạnh
  trực tiếp ([JEDM 2024](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737)).
- **Nhãn của gần hết các bộ được gán theo kiến thức nền, không bám văn bản.** Ví dụ, người gán của Pan và cộng sự dựa vào *"their own knowledge
  background and additional textbook resources"*. Vàng của dự án bám câu chữ giáo trình, nên gần với PREAP hơn.
- **Không có bộ nào bằng tiếng Việt.** Hai lượt tìm kiếm ngày 2026-10-04 không thấy bộ dữ liệu tiên quyết tiếng Việt công khai.

### 2.4 Đặc trưng nào mang tín hiệu

Các phép bỏ đặc trưng và xếp hạng độ quan trọng trong văn liệu cho cùng một hình ảnh:
- Pan và cộng sự, trên bộ ML: bỏ khoảng cách độ phức tạp (Cld) làm F1 tụt 7,4; bỏ bất đối xứng phân bố tụt 3,2; bỏ khoảng cách vị trí trung bình tụt
  2,4; bỏ độ liên quan ngữ nghĩa chỉ tụt 1,4. Theo nhóm: cấu trúc −9,2, ngữ cảnh −5,0, ngữ nghĩa −1,4 ([ACL 2017](https://aclanthology.org/P17-1133/)).
- AL-CPL: các đặc trưng đứng đầu là chênh PageRank, chênh authority, RefD, *"# mentions of A in B"* và *"A in B's 1st sentence"*. Bài viết:
  *"symmetric pairwise features such as similarity and PMI are not important in current in-domain classification setting"*, nhưng dự đoán chúng
  quan trọng hơn khi phân loại khác miền ([AAAI 2018](https://ojs.aaai.org/index.php/AAAI/article/view/11396)).
- CPRL, Bảng 1: RefD có precision 0,666–0,950 nhưng recall chỉ 0,188–0,415 trên bảy bộ; tác giả viết RefD *"obtains a higher precision, but a lower
  recall"* ([NAACL 2021](https://aclanthology.org/2021.naacl-main.164/)).
- Pan và cộng sự: mẫu hyponym có precision 67–71 nhưng recall 15–18; RefD trên tập con Wikipedia có precision 73,4–77,8, recall 42,8–44,8.
- PRELEARN: đường cơ sở chỉ dùng hai đặc trưng nhị phân "tên B có trong trang A" và ngược lại đạt accuracy 0,586 trong miền, 0,525 khác miền
  ([EVALITA 2020](https://aclanthology.org/2020.evalita-1.54/)).
- ACE: khi xếp hạng cặp để chuyên gia duyệt, tham chiếu ngữ nghĩa (embedding) cho path recall trung bình 0,684, tham chiếu chính xác (khớp tên)
  0,485, thứ tự ngẫu nhiên 0,385 ([JEDM 2024](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737)).

*Suy luận:* để quyết một cạnh, tín hiệu bất đối xứng (ai nhắc ai, ai phủ rộng hơn) mạnh hơn độ giống. Nhưng bộ lọc chỉ cần **không bỏ sót**, và
khớp tên chính xác có recall thấp. Vì vậy embedding (tham chiếu ngữ nghĩa) phải đi cùng khớp tên.

### 2.5 Chuyển sang tài liệu và miền mới

Đây là điểm quyết định cho cả hai mục đích, vì sản phẩm luôn gặp giáo trình mới:
- **CPRL, Bảng 4:** huấn luyện ở một miền giáo trình rồi dùng cho miền khác, F1 tụt từ 0,788–0,802 xuống 0,219–0,640. Tác giả viết *"F-scores drop
  severely"*. Bản dùng data programming, tức các hàm gán nhãn là ngưỡng trên LOrd, khoảng cách mục lục và độ phức tạp, giữ được F1 0,587–0,692 khi
  đổi miền ([NAACL 2021](https://aclanthology.org/2021.naacl-main.164/)).
- **PRELEARN:** mọi hệ đều tụt khi đổi miền. BERT tụt từ 0,887 xuống 0,690, tổ hợp đặc trưng độ phức tạp và embedding Wikidata từ 0,856 xuống
  0,668 ([EVALITA 2020](https://aclanthology.org/2020.evalita-1.54/)).
- **Zhu & Zamani:** khi 10% khái niệm bị giữ lại khỏi huấn luyện, mô hình đồ thị gần như đoán mò: VGAE F1 0,481–0,520, CPRL 0,479–0,543. Cross-encoder
  BERT trên "tên + đoạn Wikipedia truy hồi" đạt 0,732–0,767. Bỏ phần truy hồi đoạn văn thì F1 trên LectureBank tụt từ 0,757 xuống 0,511
  ([EMNLP 2022](https://aclanthology.org/2022.emnlp-main.585/)).

*Suy luận:* mô hình học biểu diễn riêng cho từng khái niệm (VGAE, R-GCN, embedding nút) không dùng được cho bộ lọc, vì mỗi tài liệu mới là một
đồ thị mới. Mô hình phải học trên **đặc trưng của cặp** tính được từ chính tài liệu, hoặc trên **nội dung** (tên và cửa sổ định nghĩa) bằng
cross-encoder. Đặc trưng cấu trúc thô (vị trí, độ phủ, tham chiếu) chịu đổi miền tốt hơn biểu diễn đã học, như kết quả data programming của CPRL.

### 2.6 Thời LLM

LLM hỏi theo cặp có precision cao nhưng recall thấp. Trên University Course, GPT-4o-mini zero-shot đạt P 86,70, R 35,80; thêm RAG Wikipedia
được P 87,23, R 61,11, F1 71,92; LLaMA 3 đạt R 62,68. Bộ chấm tham chiếu ngữ nghĩa của ACE, ở ngưỡng gửi 68% cặp, đạt R 1,0 nhưng P chỉ 46,13
([JEDM 2024](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737)). Theo tóm tắt của Yang và cộng sự, LLM zero-shot khôi phục
đồ thị khái niệm ngang các phương pháp có giám sát, hơn khoảng 3% F1 ([arXiv 2402.14293](https://arxiv.org/abs/2402.14293)). Các bài gần đây hơn
như GKROM ([AAAI 2025](https://doi.org/10.1609/aaai.v39i2.32156)) và ProPRL ([arXiv 2608.03006](https://arxiv.org/abs/2608.03006)) vẫn đi theo hướng
GNN hoặc đồ thị tri thức; tôi chỉ đọc tóm tắt của hai bài này.

### 2.7 Hệ quả cho dự án

*Suy luận:* bốn hệ quả cho thiết kế:
- Không có bộ dữ liệu ngoài nào dùng được để huấn luyện bộ lọc. Nguồn nhãn duy nhất là nhật ký pass phụ của dự án: hàng chục nghìn cặp mỗi
  tài liệu, nhãn do LLM gán.
- Đặc trưng nên lấy theo văn liệu: tham chiếu có hướng, nhắc tên trong câu định nghĩa, độ phủ, vị trí, độ quan trọng trên đồ thị nhắc tên, cộng
  tham chiếu ngữ nghĩa bằng embedding.
- Mô hình khởi đầu là cây tăng cường hoặc random forest. Bỏ GNN theo tài liệu.
- Chấm bằng recall trên cặp LLM-dương theo từng tài liệu, tập kiểm tra giữ đúng phân bố thật, chia theo tài liệu (leave-one-document-out).

---

## 3. Câu hỏi 2 — Cascade, chưng cất và đặt ngưỡng theo độ hồi tưởng

### 3.1 Sáu khuôn giảm lời gọi đắt

Văn liệu có sáu khuôn gần với bài lọc cặp của dự án; cột cuối nói chỗ khác.

| Khuôn | Công trình | Cơ chế | Số liệu | Khác với bài của dự án |
|---|---|---|---|---|
| Cascade bộ phân loại | Viola & Jones ([CVPR 2001](https://doi.org/10.1109/CVPR.2001.990517)) | mỗi tầng hạ ngưỡng *"to minimize false negatives"*; tầng sau chỉ xét mẫu tầng trước cho qua | tầng đầu 2 đặc trưng giữ 100% mặt trên tập kiểm định, dương giả 40%; 38 tầng, trung bình 10 đặc trưng mỗi cửa sổ | cùng mục tiêu: bỏ sớm phần lớn âm, gần như không bỏ dương |
| Cascade LLM | FrugalGPT ([arXiv 2305.05176](https://arxiv.org/abs/2305.05176)) | gọi LLM rẻ trước; DistilBERT hồi quy chấm câu trả lời; dưới ngưỡng thì gọi LLM đắt hơn | để ngang LLM tốt nhất, tiết kiệm 98,3% (HEADLINES), 73,3% (OVERRULING), 59,2% (COQA) | tầng đầu của dự án là bộ phân loại, không phải LLM |
| Hai tầng theo độ bất định | Ramírez, Birch & Titov ([COLM 2024](https://arxiv.org/abs/2405.02134)) | dùng margin của mô hình nhỏ để quyết có gọi mô hình lớn | thắng 25/27 thiết lập so với router và cascade đã học | như trên |
| Chưng cất trực tuyến (neural caching) | Cache & Distil ([Findings ACL 2024](https://arxiv.org/abs/2310.13561)) | học trò T5 học liên tục từ nhãn LLM; chính sách học chủ động quyết hỏi LLM | Margin Sampling và Query by Committee tốt đều; T5 với 5.000 nhãn vàng ≈ LLM | giả định luồng yêu cầu i.i.d.; dự án có dịch chuyển theo tài liệu |
| Proxy + oracle có bảo đảm | SUPG ([PVLDB 2020](https://arxiv.org/abs/2004.00827)) | chọn ngưỡng proxy đạt mục tiêu recall hoặc precision với xác suất lỗi δ, dùng s lời gọi oracle | cách cũ không bảo đảm: đòi precision 90% thì hơn nửa số lượt trả dưới 65%, có lượt chỉ 20% | khớp nhất với bài của dự án |
| Blocking ER | Papadakis và cộng sự ([ACM CSUR 2020](https://arxiv.org/abs/1905.06167)) | chặn cặp không có triển vọng trước bước so khớp đắt | đo bằng PC (recall), PQ (precision), RR = 1 − số cặp còn lại / số cặp gốc | cùng thước đo; dự án có thể mượn nguyên |

Hai công trình gần miền giáo dục cũng dùng mô hình trong vòng lặp. MOOCCube cho mô hình gán các cặp chưa gán, rồi gán lại bằng tay những cặp có
độ tin thấp, qua nhiều vòng ([ACL 2020](https://aclanthology.org/2020.acl-main.285/)). ACE cho chuyên gia duyệt phần đầu bảng xếp hạng và suy thêm
cạnh bằng tính bắc cầu ([JEDM 2024](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737)).

### 3.2 Đặt ngưỡng theo độ hồi tưởng

Văn liệu có bốn cách đặt ngưỡng, từ đơn giản đến có bảo đảm:
- **Ngưỡng trên tập kiểm định.** Viola và Jones chỉnh ngưỡng mỗi tầng để giảm âm tính giả và thêm đặc trưng cho tới khi đạt tỉ lệ phát hiện và tỉ lệ
  dương giả mục tiêu; các tỉ lệ này *"are determined by testing the detector on a validation set"* ([CVPR 2001](https://doi.org/10.1109/CVPR.2001.990517)).
  Cách này chỉ đúng khi dữ liệu mới có cùng phân bố.
- **Hiệu chỉnh xác suất** (Platt, isotonic) làm điểm của mô hình thành xác suất đọc được, nhờ đó ngưỡng mang sang giữa các lần huấn luyện dễ hơn
  ([Niculescu-Mizil & Caruana, ICML 2005](https://doi.org/10.1145/1102351.1102430)). Bước này không thay được việc đo recall.
- **Conformal risk control** kiểm soát kỳ vọng của mọi hàm mất mát đơn điệu, trong đó có tỉ lệ âm tính giả, và chặt tới mức O(1/n)
  ([ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/f3549ef9b5ff520a7e41ff3cc306ab2b-Abstract-Conference.html)). Bảo đảm này cần dữ
  liệu hiệu chỉnh và dữ liệu mới hoán đổi được cho nhau.
- **SUPG** lấy mẫu một phần dữ liệu của chính truy vấn để hỏi oracle, ước lượng ngưỡng bằng khoảng tin cậy có hiệu chỉnh đa giả thuyết, và cho bảo
  đảm "đạt recall γ với xác suất ít nhất 1 − δ". Lấy mẫu tỉ lệ với căn bậc hai của điểm proxy hiệu quả hơn lấy mẫu đều khi điểm proxy đáng tin.
  Bài thử mục tiêu recall tới 0,95, và ghi rằng cách căn bậc hai hơn cách tỉ lệ thuận *"in all cases, except for high recall settings"*
  ([PVLDB 2020](https://arxiv.org/abs/2004.00827)).

*Suy luận:* với dự án, mỗi tài liệu là một "truy vấn" và phân bố cặp khác hẳn giữa các cuốn: doc-4 có 22.972 cặp, xstk 942. Conformal tính theo
tài liệu chỉ có tám điểm hiệu chỉnh, nên bảo đảm rất lỏng. Cách hợp hơn có hai bước. Bước một chọn ngưỡng ngoài mẫu theo tài liệu
(leave-one-document-out). Bước hai kiểm mẫu trên từng tài liệu mới theo kiểu SUPG, vì pha "hỏi LLM" vốn đã có sẵn trong luồng. Mục 7.5 tính chi
phí của bước kiểm.

### 3.3 Bằng chứng định lượng về tiết kiệm và chất lượng

Các số dưới đây đo trên bài toán khác, chỉ cho biết cỡ của mức tiết kiệm đã được báo cáo.

| Công trình | Tiết kiệm | Chất lượng giữ được |
|---|---|---|
| FrugalGPT ([arXiv 2305.05176](https://arxiv.org/abs/2305.05176)) | 59,2–98,3% chi phí | ngang LLM tốt nhất; hoặc hơn GPT-4 tới 4% accuracy ở cùng chi phí (theo tóm tắt) |
| Nhãn GPT-3 ([Findings EMNLP 2021](https://aclanthology.org/2021.findings-emnlp.354/)) | rẻ hơn nhãn người 50–96% | mô hình hạ nguồn đạt cùng chất lượng (theo tóm tắt) |
| ChatGPT gán nhãn ([PNAS 2023](https://doi.org/10.1073/pnas.2305016120)) | dưới 0,003 USD mỗi nhãn, rẻ khoảng 30 lần MTurk | accuracy zero-shot hơn crowd worker khoảng 25 điểm trên bốn bộ (theo tóm tắt) |
| Viola & Jones ([CVPR 2001](https://doi.org/10.1109/CVPR.2001.990517)) | trung bình 10 đặc trưng mỗi cửa sổ trên hơn 6.000 đặc trưng của cascade | nhanh hơn hệ Rowley và cộng sự khoảng 15 lần |
| ACE ([JEDM 2024](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737)) | bớt 50% cặp phải duyệt (Metacademy) | path recall ≈ 90% |
| SUPG ([PVLDB 2020](https://arxiv.org/abs/2004.00827)) | ngân sách oracle cố định | chất lượng kết quả tốt hơn tới 30 lần so với cách không bảo đảm (theo tóm tắt) |

### 3.4 Chưng cất nhãn LLM vào mô hình nhỏ

Bằng chứng ủng hộ việc học từ nhãn LLM:
- Khái niệm chưng cất (học trò học theo đầu ra của thầy) có từ [Hinton, Vinyals & Dean (2015)](https://arxiv.org/abs/1503.02531).
- Distilling step-by-step: T5 770M vượt PaLM 540B few-shot trên một benchmark, chỉ dùng 80% dữ liệu, nhờ học thêm lời giải thích của LLM
  ([Findings ACL 2023](https://aclanthology.org/2023.findings-acl.507/)).
- GLiNER: bộ mã hoá hai chiều (DeBERTa-v3) học trên Pile-NER, tức văn bản do ChatGPT gán thực thể, vượt ChatGPT ở NER zero-shot. Trên MultiCoNER, mô hình
  hơn ChatGPT ở 8/10 ngôn ngữ không có trong dữ liệu huấn luyện; bản đa ngôn ngữ dùng mDeBERTa-v3-base
  ([NAACL 2024](https://aclanthology.org/2024.naacl-long.300/)).
- Cache & Distil: *"the student appears robust to the noise introduced by an LLM"*. Thí nghiệm bỏ hết nhãn LLM sai chỉ cải thiện vừa phải, tức hiện
  tượng học trò lặp lại lỗi của thầy có ảnh hưởng hạn chế. Lợi ích lớn nhất của thầy nằm ở các mẫu học trò không chắc (margin thấp)
  ([Findings ACL 2024](https://arxiv.org/abs/2310.13561)).
- CPRL tạo nhãn huấn luyện bằng data programming (Snorkel) từ các hàm gán nhãn là ngưỡng trên đặc trưng, và đạt kết quả gần bản có giám sát
  ([NAACL 2021](https://aclanthology.org/2021.naacl-main.164/); Snorkel: [PVLDB 2017](https://doi.org/10.14778/3157794.3157797)).
- Confident learning ước lượng phân bố chung của nhãn nhiễu và nhãn đúng để tìm nhãn sai, không phụ thuộc mô hình hay kiểu dữ liệu
  ([JAIR 2021](https://doi.org/10.1613/jair.1.12125)). Có thể dùng để tìm phán quyết LLM đáng ngờ trong nhật ký.

Văn liệu cũng cho ba giới hạn:
- Học trò học trên nhãn LLM thì chỉ học được ranh giới của LLM. ACE cho thấy LLM hỏi theo cặp có recall chỉ 36–63% so với vàng; bộ lọc không lấy lại
  được cạnh mà chính LLM bỏ.
- Cache & Distil giả định luồng yêu cầu i.i.d. và ghi rằng thực tế phân bố đổi theo thời gian. Ở dự án, phân bố đổi theo tài liệu.
- Lỗi có hệ thống của thầy truyền sang học trò. Đó là lý do đo bằng vàng người, như ranh giới seminar đã chốt.

### 3.5 Hệ quả cho dự án

*Suy luận:* khuôn đúng cho v4 là **cascade hai tầng có kiểm mẫu**. Tầng một là bộ phân loại rẻ, ngưỡng đặt nghiêng hẳn về recall. Tầng hai là LLM như
hiện nay. Một mẫu nhỏ cặp dưới ngưỡng vẫn được gửi LLM để đo recall của chính tài liệu đó. Chính sách "gọi LLM khi học trò không chắc" của
Cache & Distil và Ramírez và cộng sự hợp với bản seminar, nơi bộ phân loại thay LLM, hơn là với bộ lọc.

---

## 4. Câu hỏi 3 — Trích thuật ngữ, câu định nghĩa và viết tắt không dùng LLM sinh văn bản

### 4.1 Trích thuật ngữ

Bốn kết quả chính về trích thuật ngữ:
- **C-value/NC-value** kết hợp thông tin ngôn ngữ (mẫu từ loại) với thống kê tần suất, nhạy với thuật ngữ lồng nhau, và được thiết kế độc lập miền
  ([International Journal on Digital Libraries 2000](https://doi.org/10.1007/s007999900023)).
- **ACTER và TermEval 2020:** bộ dữ liệu ba ngôn ngữ (Anh, Pháp, Hà Lan), bốn miền. Bộ này ghi nhận đồng thuận giữa người gán thấp, vì ranh giới
  giữa thuật ngữ và ngôn ngữ chung không rõ ([Language Resources and Evaluation 2020](https://doi.org/10.1007/s10579-019-09453-9);
  [CompuTerm 2020](https://aclanthology.org/2020.computerm-1.12/)).
- **Gán nhãn chuỗi bằng XLM-R ở mức câu** đạt F1 58,3 (tiếng Anh), 57,6 (tiếng Pháp), 69,8 (tiếng Hà Lan) trên miền kiểm tra của ACTER, so với kết quả
  tốt nhất của TermEval là 46,7, 48,1 và 18,7. Chuyển ngôn ngữ zero-shot mạnh: *"models trained on a single language often outperform those trained on
  all three languages"* ([Findings ACL-IJCNLP 2021](https://aclanthology.org/2021.findings-acl.316/)).
- **Tiếng Việt:** Vo và cộng sự trích thuật ngữ y khoa từ bệnh án điện tử tiếng Việt bằng mẫu ngôn ngữ mở, C-value và PMI để tách thuật ngữ lồng,
  không cần dữ liệu gán nhãn. Bài đạt precision khoảng 74%, recall khoảng 92% ([Terminology 2022](https://doi.org/10.1075/term.20037.vo), chỉ đọc tóm tắt).

*Suy luận:* cho A3 của seminar, ghép hai nguồn ứng viên. C-value cộng mẫu từ loại (sau VnCoreNLP) cho recall. Bộ gán nhãn chuỗi (PhoBERT hoặc XLM-R)
học từ các khái niệm A3 đã trích, theo đúng cách GLiNER học từ nhãn ChatGPT, cho độ chính xác. Thước đo vẫn là Q3 (khái niệm trọng yếu) trên vàng người.

### 4.2 Trích câu định nghĩa

Ba nguồn chính về trích định nghĩa:
- **WCL:** 4.619 câu Wikipedia (1.908 câu định nghĩa). Mô hình mạng từ–lớp đạt precision 98,81–99,88 nhưng recall chỉ 42,09–60,74. Tác giả viết mẫu
  "X is a Y" *"is inherently very noisy"* ([ACL 2010](https://aclanthology.org/P10-1134/)).
- **DEFT:** 2.443 câu hợp đồng và 21.303 câu giáo trình mở cnx.org (sinh học, lịch sử, vật lý, tâm lý, kinh tế, xã hội học, chính phủ). 28% câu
  giáo trình chứa định nghĩa. *"roughly 50% of term-definition pairs appeared across sentence boundaries"*, và nhiều định nghĩa trong giáo trình không có
  từ báo kiểu "X là Y" ([LAW 2019](https://aclanthology.org/W19-4015/)).
- **SemEval-2020 Task 6 (DeftEval):** ở nhiệm vụ con "câu này có chứa định nghĩa không" có 56 đội. Điểm chính thức cao nhất 0,8783, hạng năm 0,8444,
  trung vị khoảng 0,78; bài tổng quan chỉ ghi "score", tên thước đo (nhiều khả năng là F1) **chưa xác nhận**. Phần lớn hệ dùng BERT, RoBERTa hoặc XLNet
  ([SemEval 2020](https://aclanthology.org/2020.semeval-1.41/)).

*Suy luận:* số "50% cặp thuật ngữ–định nghĩa vắt qua ranh giới câu" của DEFT ủng hộ cửa sổ định nghĩa nhiều câu của R12. Tìm kiếm ngày 2026-10-04
không thấy bộ dữ liệu trích định nghĩa tiếng Việt công khai. Nguồn nhãn bạc gần nhất là câu neo của bước C8 trong nhật ký dự án: mỗi khái niệm được
dạy có một câu neo do LLM chọn và mã đã kiểm có trong văn bản.

### 4.3 Nhận diện viết tắt

Hai nguồn chính về viết tắt:
- **Schwartz & Hearst:** thuật toán đơn giản, không cần dữ liệu huấn luyện, đạt precision 96% và recall 82% trên một bộ chuẩn, 95% và 82% trên một bộ
  lớn hơn ([PSB 2003](https://psb.stanford.edu/psb-online/proceedings/psb03/schwartz.pdf)).
- **MACRONYM** có phần tiếng Việt ở miền khoa học (luận văn CNTT): 800 câu, đồng thuận 0,791, 270 viết tắt nhưng chỉ 61 dạng đầy đủ. F1 tiếng Việt:
  luật 53,44, mBERT 58,71, XLM-R 59,13; huấn luyện bằng tiếng Anh rồi dùng cho tiếng Việt, XLM-R còn 51,44. Bất đồng chính giữa người gán là viết tắt
  lập từ chữ đầu của **thuật ngữ tiếng Anh** trong khi dạng đầy đủ viết bằng tiếng Việt ([COLING 2022](https://aclanthology.org/2022.coling-1.292/)).

*Suy luận:* sách CNTT tiếng Việt hay viết kiểu "mạng nơ-ron tích chập (CNN)". Luật khớp chữ đầu theo dạng đầy đủ tiếng Việt sẽ trượt các trường hợp này.
Cần thêm nhánh khớp với cụm tiếng Anh đứng gần, hoặc với alias tiếng Anh mà A3 đã trích. Luật của MACRONYM nhận viết tắt bằng thuộc tính chữ hoa
(*"more than 60% characters as uppercase letters"*), nên không chạy được với chữ viết không có chữ hoa.

### 4.4 Chuyển sang tiếng Việt bằng XLM-R

Bốn chỉ báo về chuyển ngôn ngữ sang tiếng Việt:
- Tiếng Việt là ngôn ngữ giàu dữ liệu trong CC-100 của XLM-R: 24.757 triệu token, 137,3 GiB ([ACL 2020](https://aclanthology.org/2020.acl-main.747/)).
- XNLI, huấn luyện bằng tiếng Anh: XLM-R đạt 89,1 trên tiếng Anh, 80,8 trên tiếng Việt. Khi huấn luyện trên dữ liệu dịch máy của mọi ngôn ngữ, tiếng
  Việt lên 83,7 ([ACL 2020](https://aclanthology.org/2020.acl-main.747/)).
- Trên tác vụ tiếng Việt, PhoBERT-base hơn XLM-R-base: từ loại 96,7 so với 96,2, phân tích phụ thuộc LAS 78,77 so với 76,46, NER 93,6 so với 92,0
  ([Findings EMNLP 2020](https://aclanthology.org/2020.findings-emnlp.92/)).
- Viết tắt (MACRONYM): huấn luyện bằng tiếng Anh rồi dùng cho tiếng Việt kém huấn luyện bằng tiếng Việt 7,7 điểm F1 (51,44 so với 59,13).

*Suy luận:* có dữ liệu huấn luyện tiếng Việt thì hơn chuyển zero-shot từ tiếng Anh 2,9 điểm (XNLI, dữ liệu dịch máy) và 7,7 điểm (MACRONYM). Seminar
đã có nhãn bạc tiếng Việt từ nhật ký, vì vậy nên huấn luyện thẳng bằng tiếng Việt và dùng dữ liệu tiếng Anh (doc-2, doc-3) làm phần bổ sung, không làm
nguồn chính.

---

## 5. Câu hỏi 4 — Công cụ NLP tiếng Việt

Bảng dưới gom các công cụ cho seminar, kèm ràng buộc thực tế đọc từ trang chính thức.

| Công cụ | Chức năng | Số đo công bố | Ràng buộc | Nguồn |
|---|---|---|---|---|
| VnCoreNLP (gồm RDRsegmenter) | tách từ, từ loại, NER, phân tích phụ thuộc | tách từ F1 97,90 (62 nghìn từ/giây); từ loại 95,88; NER 88,55 (VLSP 2016); phụ thuộc trên VnDT LAS 73,39, UAS 79,02 với từ loại vàng, LAS 70,10 với từ loại tự động | Java 1.8+; giấy phép GPL v3 | [NAACL 2018](https://aclanthology.org/N18-5012/); [README, LICENSE](https://github.com/vncorenlp/VnCoreNLP) |
| PhoBERT | bộ mã hoá RoBERTa tiếng Việt | từ loại 96,7/96,8; LAS 78,77 (base); NER 93,6/94,7; NLI 78,5/80,0 | tối đa 256 token; *"INPUT TEXT MUST BE ALREADY WORD-SEGMENTED"*, khuyên dùng đúng RDRsegmenter như lúc tiền huấn luyện; base và large 135M/370M, giấy phép MIT; base-v2 giấy phép AGPL v3 | [Findings EMNLP 2020](https://aclanthology.org/2020.findings-emnlp.92/); [README](https://github.com/VinAIResearch/PhoBERT) |
| PhoNLP | học đa nhiệm từ loại, NER, phụ thuộc trên PhoBERT | hơn fine-tune từng tác vụ riêng (theo tóm tắt) | Apache 2.0 (theo tóm tắt) | [NAACL 2021 demo](https://aclanthology.org/2021.naacl-demos.1/) |
| BamiBERT | bộ mã hoá BERT tiếng Việt, 0,1 tỉ tham số | tốt nhất 11/15 chỉ số trên 8 benchmark tiếng Việt (theo tóm tắt) | 2.048 token; không cần tách từ; 129 GB văn bản; preprint 2/7/2026; giấy phép BSD-3-Clause-Clear kèm Qualcomm Responsible AI License | [arXiv 2607.02259](https://arxiv.org/abs/2607.02259); [thẻ mô hình](https://huggingface.co/Qualcomm-AI-Research/BamiBERT) |
| underthesea | tách câu, chuẩn hoá, tách từ, từ loại, chunk, NER, phân loại, phân tích phụ thuộc | README không công bố số đo | Apache-2.0; từ v9.3.0 có thêm module agent gọi LLM, seminar không được dùng phần này | [README](https://github.com/undertheseanlp/underthesea) |
| Trankit | pipeline đa ngôn ngữ trên XLM-R | UD Vietnamese-VTB (UD 2.5), đầu cuối từ văn bản thô: từ 94,88; UPOS 89,70; UAS 71,07; LAS 65,37 | 90 pipeline cho 56 ngôn ngữ | [EACL 2021 demo](https://aclanthology.org/2021.eacl-demos.10/); [trang hiệu năng](https://trankit.readthedocs.io/en/latest/performance.html) |
| Stanza | pipeline đa ngôn ngữ | v1.5.1 trên UD 2.12, Vietnamese-VTB: từ 88,02; UPOS 81,48; UAS 58,82; LAS 51,49 | — | [trang hiệu năng](https://stanfordnlp.github.io/stanza/performance.html) |
| multilingual-e5 (small/base/large, large-instruct) | embedding câu đa ngôn ngữ | VN-MTEB trung bình: large-instruct 67,99 (cao nhất bảng), large 63,87, base 62,42, small 60,66 | cắt ở 512 token; large-instruct là XLM-R 24 lớp, 1.024 chiều, giấy phép MIT | [arXiv 2402.05672](https://arxiv.org/abs/2402.05672); [thẻ mô hình](https://huggingface.co/intfloat/multilingual-e5-large-instruct); [VN-MTEB](https://aclanthology.org/2026.findings-eacl.86/) |
| BGE-M3 | embedding dense, sparse và multi-vector | VN-MTEB trung bình 64,90 | hơn 100 ngôn ngữ; tới 8.192 token | [Findings ACL 2024](https://aclanthology.org/2024.findings-acl.137/) |
| Embedding riêng tiếng Việt | — | VN-MTEB: halong-embedding 61,60; vietnamese-bi-encoder 54,89; sup-SimCSE-VN-phobert-base 50,59 | — | [Findings EACL 2026](https://aclanthology.org/2026.findings-eacl.86/) |

Bốn lưu ý khi đọc bảng:
- Số của VnCoreNLP đo trên VnDT với tách từ vàng; số của Trankit và Stanza đo đầu cuối trên UD Vietnamese-VTB từ văn bản thô. Hai nhóm số không so
  trực tiếp được với nhau.
- VN-MTEB dịch máy 41 bộ từ MTEB bằng LLM rồi lọc, nên đo năng lực trên tiếng Việt dịch, không phải văn giáo trình
  ([Findings EACL 2026](https://aclanthology.org/2026.findings-eacl.86/)).
- PhoBERT tối đa 256 token. Một cặp gồm hai cửa sổ định nghĩa (mỗi cửa sổ tới 7 câu) dễ vượt giới hạn này, nên phải cắt hoặc mã hoá từng bên riêng.
  BamiBERT (2.048 token) hoặc multilingual-e5 (512 token) đỡ vấn đề này.
- Giấy phép GPL v3 của VnCoreNLP và AGPL v3 của PhoBERT-base-v2 không cản việc học trong seminar. Chúng chỉ quan trọng nếu mã seminar được đưa vào
  sản phẩm; sản phẩm thì phải đa ngôn ngữ nên vốn không dùng các công cụ riêng tiếng Việt.

*Suy luận:* bộ khởi đầu cho seminar gồm VnCoreNLP (tách từ, từ loại, phụ thuộc) cho đặc trưng và ứng viên thuật ngữ, multilingual-e5-large-instruct cho
embedding, PhoBERT-base cho cross-encoder ngắn. BamiBERT là phương án thay PhoBERT khi cần ngữ cảnh dài, sau khi tự kiểm trên vàng của dự án.

---

## 6. Câu hỏi 5 — Gom khái niệm trùng và gán vai trò vùng văn bản

### 6.1 Gom khái niệm trùng (entity resolution)

[Báo cáo A4/A5](nghien-cuu-a4-a5-hop-nhat-thuc-the.md) đã khảo kỹ ER bằng LLM, blocking và cách đo. Phần này chỉ bổ sung phần không dùng LLM:
- **Ditto** coi so khớp thực thể là phân loại cặp chuỗi, fine-tune BERT hoặc RoBERTa, hơn các phương pháp trước tới 29% F1 và đạt mức tốt nhất trước đó
  với nhiều nhất một nửa dữ liệu gán nhãn ([PVLDB 2020](https://doi.org/10.14778/3421424.3421431)).
- **SapBERT** học metric "tự căn chỉnh" để các tên đồng nghĩa của cùng một khái niệm UMLS nằm gần nhau, đạt mức tốt nhất trên sáu bộ liên kết thực thể
  y sinh ([NAACL 2021](https://aclanthology.org/2021.naacl-main.334/)). Đây là khuôn để học bi-encoder từ các nhóm tên đã gộp.
- **Thước đo blocking:** PC (recall), PQ (precision), RR ([ACM CSUR 2020](https://arxiv.org/abs/1905.06167)).

*Suy luận:* bản seminar có thể thay A9'' bằng hai tầng. Tầng chặn hợp các kênh (khớp chuỗi sau chuẩn hoá, viết tắt, bi-encoder multilingual-e5 trên tên
và câu neo), đo bằng PC/RR. Tầng quyết là cross-encoder kiểu Ditto học từ quyết định danh tính trong nhật ký (`same` sau lượt xác minh R8b) và từ các
cặp chủ dự án đã duyệt (T14). Tiêu chí "cùng ngoại diên" của R8b khó học từ ít nhãn, nên ca khó (trường hợp riêng, bằng nhau nhờ định lý) vẫn phải để
người duyệt.

### 6.2 Gán vai trò vùng văn bản

Ba công trình gần nhất về phân loại vai trò của câu hoặc mục:
- **PubMed 200k RCT:** khoảng 200.000 tóm tắt, 2,3 triệu câu, mỗi câu một trong năm nhãn vai trò (bối cảnh, mục tiêu, phương pháp, kết quả, kết luận)
  ([IJCNLP 2017](https://aclanthology.org/I17-2052/)).
- **Cohan và cộng sự:** BERT phân loại chuỗi câu theo ngữ cảnh mà không cần mã hoá phân cấp hay CRF, đạt mức tốt nhất trên bốn bộ
  ([EMNLP-IJCNLP 2019](https://aclanthology.org/D19-1383/)).
- **SECTOR:** vừa tách vừa gán chủ đề cho mục; bộ WikiSection có 242 nghìn mục tiếng Anh và tiếng Đức; F1 71,6% cho 30 chủ đề, hơn bộ phân loại CNN
  29,5 điểm ([TACL 2019](https://aclanthology.org/Q19-1011/)).

Không bài nào phân loại đúng tập vai trò của dự án (nội dung, bài tập, lời giải, đề cương, mở đầu, hành chính, cuối sách) trên giáo trình.

*Suy luận:* A2 của seminar là bài phân loại chuỗi trên cây mục. Mỗi tiêu đề có đặc trưng cấu trúc đã có trong R1 và R2 (vị trí so với chuỗi chương, mẫu
đánh số, độ dài thân, tỉ lệ câu hỏi, khớp mục lục) cộng embedding của tiêu đề và vài dòng đầu. Mô hình là GBDT, sau đó BERT theo kiểu Cohan và cộng sự
nếu cần. Nhãn bạc lấy từ A2; phải sửa tay những vùng LLM gán sai trước khi học, ví dụ 48/126 đoạn "Cách giải" của xstk bị gán đề cương
([kết quả tập giữ lại v3](ket-qua-tap-giu-lai-v3-2026-10-04.md)). Thước đo ưu tiên là recall của `noi_dung`, vì vùng dạy bị loại thì kéo theo lỗi ở C8
và R5.

---

## 7. Đề xuất cho v4 (bộ lọc cặp)

### 7.1 Đặt bài và chỉ số

Bộ lọc chấm mọi cặp mà `select_secondary_pairs` chọn. Cặp có điểm từ ngưỡng trở lên được hỏi LLM như hiện nay (kể cả hỏi lười của v4-01); cặp dưới ngưỡng
bị bỏ, trừ mẫu kiểm. Bộ lọc không tạo được cạnh, nên rủi ro chất lượng chủ yếu nằm ở recall; A9 và A10 có thể đổi kết quả khi bớt cạnh, nên vẫn phải
phát lại hai khâu này.

*Suy luận:* các chỉ số nên báo cho mỗi tài liệu, theo cách chia leave-one-document-out:
- **PC_d:** tỉ lệ cặp LLM-dương được giữ lại. Mục tiêu PC_d ≥ 0,99, báo kèm cận dưới Wilson 95%; báo cả tài liệu tệ nhất, không chỉ trung bình.
  Tính riêng cho cạnh cứng `can_de_hieu`.
- **RR_d:** tỉ lệ cặp không phải hỏi, quy ra lời gọi, USD và phút bớt được.
- **Cạnh vàng mất do lọc:** liệt kê từng cạnh vàng mà v3 tìm được nhưng bộ lọc bỏ, kèm loại căn cứ và câu trích.
- **Q6, Q7 và bao đóng P/R trên vàng người,** trước và sau lọc, bằng cách phát lại A9→A10 trên tập cạnh còn lại.
- **Phân rã cạnh mất** theo `evidence_kind`, `prerequisite_kind`, liên cụm hay cùng cụm, thuận hay ngược thứ tự sách, và có hay không tên tiên quyết
  trong cửa sổ định nghĩa. Đây là chỗ bài học F126 sẽ lộ ra nếu lặp lại.

### 7.2 Nhãn huấn luyện

*Suy luận:* với hỏi lười, cạnh của một cặp được giữ lại ra y hệt v3. Recall của bộ lọc vì vậy chỉ phụ thuộc việc cặp có được hỏi hay không. Đề xuất
cách gán nhãn như sau:
- **Dương để huấn luyện:** thứ tự đầu trả `create`. Đây là tập lớn hơn tập cạnh cuối, gồm cả cặp sau đó bị hoãn vì hai thứ tự lệch nhau, nên làm bộ
  lọc thận trọng hơn.
- **Dương để đo:** cặp thành cạnh sau khi gộp hai thứ tự (cả `can_de_hieu` và `cong_cu`), cộng một thước đo riêng cho `can_de_hieu`.
- **Âm:** thứ tự đầu trả `no_direct_relation` hoặc `indirect_path`.
- **Loại khỏi huấn luyện:** cặp mà thứ tự đầu lỗi sau mọi lần thử lại. Ở doc-4, 2.710 cặp (12%) bị hoãn vì phản hồi không hợp lệ ở ít nhất một thứ tự
  ([nghiên cứu tiền và thời gian](nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md)); số cặp lỗi ngay ở thứ tự đầu phải đếm lại từ nhật ký. Báo nhóm này riêng,
  vì nó có thể chứa dương. Vé v4-04 (đọc nhật ký phản hồi lỗi) sẽ cho biết thêm.
- Mỗi cặp là một đơn vị. Hai thứ tự của cùng cặp không được nằm ở hai phía của phép chia.

### 7.3 Đặc trưng

Mọi đặc trưng dưới đây tính được từ artifact sẵn có, không cần danh sách từ của ngôn ngữ nào. Cột thứ ba ghi căn cứ trong văn liệu.

| Nhóm | Đặc trưng | Căn cứ | Đã có trong artifact? |
|---|---|---|---|
| Nguồn ứng viên | cờ và số lượng `same_section`, `citation_hard`, `citation_soft`, `contact`, `proposed_relation`; trọng số kênh `exact`/`dense` của cặp cụm; cặp cụm có được chọn không | blocking nhiều lược đồ ([CSUR 2020](https://arxiv.org/abs/1905.06167)) | có ([`mentions.py`](../src/doc2roadmap/domain/mentions.py)) |
| Tham chiếu có hướng | số lần A được nhắc trong cửa sổ định nghĩa của B và ngược lại; A có trong câu neo của B không; LOrd/RefD tính trên chunk | RefD; AL-CPL ("# mentions of A in B", "A in B's 1st sentence"); LOrd của CPRL | tính từ mention map và cửa sổ |
| Tham chiếu ngữ nghĩa | cosine lớn nhất giữa embedding tên và mô tả của A với từng câu trong cửa sổ của B, và ngược lại; cosine mô tả–mô tả chuẩn hoá hai phía | ACE (CSR so với CER); AL-CPL (độ giống đối xứng yếu khi quyết, hữu ích khi đổi miền) | cần embed câu của cửa sổ (Gemini embedding, rẻ) |
| Vị trí trong sách | chênh thứ tự provenance (chuẩn hoá theo số chunk); cùng chương hay mục; khoảng cách trên cây mục lục; A được dạy trước B không | khoảng cách mục lục (Wang 2016, qua CPRL); Apd của Pan; Pal | có (`provenance_order`, cây mục) |
| Độ phủ, độ phức tạp | số chunk và mục nhắc mỗi khái niệm; khoảng từ lần nhắc đầu tới lần cuối; KL giữa hai phân bố; chênh A − B | Cld của Pan (đặc trưng mạnh nhất, −7,4 F1); CldFreq, CldDist của CPRL | tính từ mention map |
| Đồ thị | chênh PageRank và bậc vào trên đồ thị nhắc tên; có đường gián tiếp không tường minh từ pass chính | AL-CPL (chênh PageRank đứng đầu) | tính từ đồ thị sẵn có |
| Từ vựng | trùng token, trùng đầu hoặc đuôi tên theo ranh giới từ Unicode (bigram ký tự cho chữ viết không cách từ, như R15) | head matching của CPRL | tính được |
| Thuộc tính nút | `teaching_status`; vai trò vùng của chunk định nghĩa; loại nút | — (dự án) | có |

*Suy luận:* mọi đặc trưng đếm phải chuẩn hoá theo cỡ tài liệu, vì số cặp chênh nhau 24 lần giữa xstk và doc-4. Embedding câu cửa sổ dùng Gemini embedding
cho sản phẩm; đây không phải sinh văn bản, và báo cáo tiền và thời gian xếp chi phí embedding vào loại "rất nhỏ"
([nghiên cứu tiền và thời gian](nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md)). Riêng kênh dense của mention map đang so hai không gian embed khác task
type ([báo cáo A6–A8](nghien-cuu-a6-a8-cum-chu-de-va-2b.md), Tóm tắt); bộ lọc học được cách hiệu chỉnh, nhưng phân bố có thể lệch giữa các cuốn.

### 7.4 Mô hình theo bậc

*Suy luận:* làm theo bậc, mỗi bậc chỉ lên khi bậc trước không đạt:
- **Bậc 0, luật "luôn hỏi":** cặp có tín hiệu mạnh luôn được hỏi bất kể điểm, ví dụ `proposed_relation`, hoặc `citation_hard` mà tên nằm trong cửa sổ định
  nghĩa. Đây là tầng giữ 100% của Viola–Jones, và chỉ được làm luật sau khi đo trên nhật ký rằng nó không làm giảm RR đáng kể.
- **Bậc 1, hồi quy logistic, rồi cây tăng cường (XGBoost hoặc LightGBM) trên đặc trưng ở 7.3:** trọng số lớp thay cho oversampling, hiệu chỉnh xác suất
  bằng isotonic trên dự đoán ngoài mẫu. Căn cứ: random forest dẫn ở Pan và AL-CPL; XGBoost của B4DS sát BERT ở PRELEARN
  ([XGBoost, KDD 2016](https://doi.org/10.1145/2939672.2939785)).
- **Bậc 2, chỉ khi bậc 1 không đạt RR mong muốn ở PC 0,99:** cross-encoder đa ngôn ngữ (multilingual-e5 hoặc XLM-R) trên "tên + cửa sổ định nghĩa" của
  hai khái niệm, theo Zhu & Zamani. Chi phí CPU của bậc này trên 23 nghìn cặp chưa đo; phải đo trước khi chọn, vì phút/cuốn là chỉ số số một.
- **Không dùng** GNN hay embedding nút học theo tài liệu (mục 2.5).

### 7.5 Ngưỡng và kiểm mẫu trên từng tài liệu

Quy trình đề xuất gồm bốn bước:
1. **Chọn ngưỡng ngoài mẫu.** Với mỗi tài liệu giữ ra trong leave-one-document-out, tìm ngưỡng lớn nhất còn giữ PC ≥ 0,99. Ngưỡng sản phẩm là ngưỡng thận
   trọng nhất trong các tài liệu (hoặc phân vị thấp), không phải ngưỡng trung bình.
2. **Chạy trên tài liệu mới.** Hỏi LLM mọi cặp từ ngưỡng trở lên. Số dương trong phần này, gọi là P_trên, biết chính xác sau khi chạy.
3. **Kiểm mẫu phần dưới ngưỡng.** Lấy m cặp dưới ngưỡng, có trọng số nghiêng về vùng gần ngưỡng, và hỏi LLM như cặp thường. SUPG ghi cách căn bậc hai
   không còn hơn cách tỉ lệ thuận ở mục tiêu recall cao, nên cách lấy mẫu phải chọn bằng E5. Ước lượng số dương còn sót P_dưới kèm cận trên tin cậy.
   Mọi cạnh tìm được trong mẫu kiểm được giữ.
4. **Quyết.** Nếu cận dưới của PC = P_trên / (P_trên + P_dưới) thấp hơn mục tiêu, hạ ngưỡng thêm một bậc, hỏi tiếp, và ghi cảnh báo vào manifest.

*Suy luận:* chi phí kiểm mẫu tính được bằng "quy tắc ba": không thấy dương nào trong m mẫu thì cận trên 95% của tỉ lệ dương xấp xỉ 3/m
([Hanley, JAMA 1983](https://doi.org/10.1001/jama.1983.03330370053031)). Lấy doc-4 làm ví dụ, với hai giả định chưa đo: khoảng 1.600 cặp LLM-dương
(7%, theo mức 6–8% của đề bài R-02), và bộ lọc bỏ 60% cặp, tức khoảng 13.800 cặp dưới ngưỡng. Khi đó:
- m = 500 và không thấy dương nào → P_dưới ≤ khoảng 83 → chứng nhận được PC ≥ 0,95;
- muốn chứng nhận PC ≥ 0,99 thì P_dưới phải ≤ khoảng 16, tức cần khoảng 2.600 mẫu sạch (lấy mẫu đều), cỡ 2,8 USD theo giá trung bình 0,00106 USD mỗi lời
  gọi của pass phụ doc-4 trong v3.

Vì vậy kiểm mẫu nên làm **giám sát** ở mức 0,95 với vài trăm lời gọi, còn mức 0,99 dựa vào ngưỡng ngoài mẫu và vào đo định kỳ trên tài liệu có đủ nhật
ký. Lấy mẫu có trọng số quanh ngưỡng giảm được m nếu dương sót tập trung gần ngưỡng; điều này phải kiểm trên nhật ký (E5 ở 7.7).

### 7.6 Ước lượng lợi ích

*Suy luận, chưa đo:* chi phí pass phụ sau lọc xấp xỉ c × [(1 − RR) × N + K₂ + m]. Ở đây N là số cặp, K₂ là số lời gọi thứ tự hai (xấp xỉ số cặp mà thứ
tự đầu trả `create`, gần như không đổi vì bộ lọc giữ gần hết các cặp đó), m là số lời gọi kiểm mẫu, c ≈ 0,00106 USD mỗi lời gọi (45,92 USD / 43.190 lời
gọi, doc-4, v3). Với doc-4 (N = 22.972), giả định K₂ ≈ 2.300 (10% số cặp) và m = 500, kết quả như sau.

| RR | Lời gọi ước tính | USD ước tính | Ghi chú |
|---:|---:|---:|---|
| 0 (chỉ v4-01, m = 0) | ≈ 25.300 | ≈ 26,9 | gần ước tính 28 USD của [báo cáo tiền và thời gian](nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md) |
| 0,5 | ≈ 14.300 | ≈ 15,2 | |
| 0,7 | ≈ 9.700 | ≈ 10,3 | |
| 0,85 | ≈ 6.200 | ≈ 6,6 | |
| lọc hoàn hảo (chỉ hỏi khoảng 10% cặp mà thứ tự đầu trả `create`) | ≈ 5.100 | ≈ 5,4 | cận dưới lý thuyết dưới cùng giả định |

Trên Gemini Developer API bậc 1, một việc tốn X USD cần ít nhất khoảng X phút, nên số phút giảm theo cùng tỉ lệ
([báo cáo tiền và thời gian](nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md)). Hồ sơ cặp gọn (vé 03) giảm c, nên cộng dồn được với bộ lọc. Số RR
thực tế có thể thấp: bộ chấm một tín hiệu của ACE phải gửi 68% cặp mới đạt recall 1.

### 7.7 Thí nghiệm 0 USD trên nhật ký

Bảng dưới là chuỗi thí nghiệm nên làm trước mọi khoản chi; tất cả dùng nhật ký và artifact đã có của tám tài liệu.

| Mã | Việc | Đầu ra | Đọc kết quả thế nào |
|---|---|---|---|
| E0 | dựng bảng cặp × đặc trưng × phán quyết (thứ tự đầu, gộp hai thứ tự, loại căn cứ, loại tiên quyết) cho tám tài liệu; gắn cờ cạnh vàng | một bảng parquet mỗi tài liệu, có `config_id` của bộ trích đặc trưng | kiểm số cặp khớp manifest |
| E1 | đường PC–RR cho từng luật đơn (có nhắc tên trong cửa sổ, cùng chương, từng nguồn ứng viên, ngưỡng embedding) | đồ thị PC theo RR mỗi tài liệu | đường cơ sở; cho biết luật nào nguy hiểm, kiểu F126 |
| E2 | hồi quy logistic và GBDT, leave-one-document-out | RR tại PC = 0,99 mỗi tài liệu; tài liệu tệ nhất | quyết có cần bậc 2 không |
| E3 | phân rã cạnh bị lọc ở ngưỡng chọn (theo loại căn cứ, liên cụm, ngược thứ tự sách, không có tên trong cửa sổ) | bảng và danh sách cạnh | đọc từng cạnh vàng mất |
| E4 | phát lại A9→A10 trên tập cạnh sau lọc | Q6, Q7, bao đóng P/R trước và sau trên vàng doc-1, doc-2, xstk, doc-4 | thay đổi phải nằm trong khoảng tin cậy; liệt kê cạnh vàng mất |
| E5 | mô phỏng kiểm mẫu: rút m cặp dưới ngưỡng từ nhật ký (lấy mẫu đều và căn bậc hai), tính cận trên P_dưới | độ phủ của cận tin cậy qua nhiều lần rút | chọn m cho mức giám sát 0,95 |
| E6 | mô hình chi phí và thời gian theo 7.6 với số thật của từng tài liệu | USD/cuốn, phút/cuốn | báo chủ dự án quyết ngưỡng |

*Suy luận:* nhật ký của doc-4 và xstk được dùng làm dữ liệu huấn luyện vì tập giữ lại v3 đã chấm xong; từ v4 hai tài liệu này là tài liệu phát triển
([kế hoạch v4](../task/v4/00-ke-hoach.md)). Kết luận cuối về chất lượng vẫn cần tập giữ lại v4 mới (vé T-01).

### 7.8 Triển khai

*Suy luận:* nên triển khai theo ba bước:
- **Chế độ bóng:** bộ lọc chấm và ghi điểm vào `secondary_log` nhưng mọi cặp vẫn được hỏi; dùng một lượt chạy đã có kế hoạch, không chạy riêng.
- **Chế độ bật** sau khi E2–E5 đạt và chủ dự án duyệt ngưỡng; ghi `filter_model_id`, ngưỡng, m và cận tin cậy PC vào manifest; cache theo `algorithm_id`
  mới như v4-01.
- **Fixture đa ngôn ngữ:** đặc trưng phải chạy trên fixture có chữ viết không Latin và chữ viết không cách từ (theo nguyên tắc của spec v3). Mô hình chỉ học
  từ tài liệu tiếng Việt và tiếng Anh, nên với ngôn ngữ khác phải dựa vào kiểm mẫu tới khi có tài liệu T19.

---

## 8. Đề xuất cho seminar (Pha A không LLM, tiếng Việt)

### 8.1 Ranh giới và dữ liệu

Ranh giới đã chốt (đề bài R-02; chủ dự án trả lời ngày 2026-10-02): được dùng bộ mã hoá cỡ BERT; được dùng nhãn do LLM tạo để huấn luyện; đo bằng vàng
người; chỉ tài liệu tiếng Việt, cho phép xen thuật ngữ tiếng Anh. Theo quy ước chung của dự án, nội dung giáo trình không gửi ra dịch vụ ngoài: huấn luyện
tại máy, hoặc hỏi chủ dự án trước khi dùng Colab hay Kaggle.

Dữ liệu cho seminar gồm ba phần:
- **Nhãn bạc** từ nhật ký v3 của các tài liệu tiếng Việt: doc-1, doc-6, naive-bayes, nhap-mon-ml, cùng xstk và doc-4 nếu chủ dự án cho phép (xem câu hỏi
  mở ở mục 9).
- **Nhãn bổ sung** từ doc-2 và doc-3 (tiếng Anh), chỉ làm phần phụ (mục 4.4).
- **Vàng người** để đo: doc-1 (chương vàng), cộng xstk và doc-4 nếu được dùng; cần thêm vàng tiếng Việt mới làm tập kiểm tra cuối.

### 8.2 Thay từng khâu

Bảng dưới đề xuất thay từng khâu đang dùng LLM; mọi dòng đều bắt đầu bằng mô hình đơn giản.

| Khâu | LLM đang làm | Thay bằng | Nhãn để học | Đo |
|---|---|---|---|---|
| A2 vai trò vùng | gán nhãn tiêu đề mà luật cấu trúc chưa quyết | phân loại chuỗi tiêu đề: GBDT trên đặc trưng cấu trúc và embedding, sau đó BERT theo kiểu Cohan và cộng sự | nhãn A2 trong nhật ký, đã sửa tay vùng sai | F1 theo vai trò; recall `noi_dung` |
| A3 khái niệm | trích khái niệm và câu căn cứ | ứng viên C-value cộng mẫu từ loại (VnCoreNLP), hợp với gán nhãn BIO (PhoBERT) | khái niệm và câu căn cứ A3 | Q3 trên khái niệm vàng |
| Viết tắt | trong A3 và A5 | luật Schwartz–Hearst, thêm nhánh chữ đầu của thuật ngữ tiếng Anh | — | P/R trên mẫu gán tay |
| A4/A5/A9'' danh tính | đề cử, phán `same`, xác minh | tầng chặn (chuỗi, viết tắt, bi-encoder multilingual-e5) và cross-encoder kiểu Ditto | quyết định danh tính trong nhật ký và cặp T14 | PC/RR tầng chặn; P/R theo cặp |
| A5 mô tả | sinh mô tả | trích: dùng câu neo hoặc cửa sổ định nghĩa làm mô tả | — | đọc |
| C8 neo | chọn câu neo và loại | xếp hạng câu ứng viên bằng bộ phân loại câu định nghĩa (PhoBERT) | câu neo trong nhật ký | câu neo top-1 đúng so với vàng |
| A6/A7 | embedding Gemini | multilingual-e5 hoặc BGE-M3 tại máy; giữ Leiden | — | NMI cụm–chương như v3 |
| A8 tiên quyết | pass chính và pass phụ | bộ phân loại cặp và bộ chọn câu căn cứ (8.3) | phán quyết pass phụ | Q6, Q7, bao đóng P/R trên vàng |
| Tên module | chọn 2–3 tên khái niệm | luật trích: tiêu đề mục hoặc tên khái niệm trung tâm | — | bảng kiểm R11 |

### 8.3 A8 không dùng LLM

*Suy luận:* thiết kế đề xuất cho A8 gồm bốn phần:
- **Bộ phân loại ba lớp** (không cạnh, A → B, B → A) trên các đặc trưng ở 7.3, rồi cross-encoder PhoBERT hoặc BamiBERT trên hai cửa sổ định nghĩa. Bộ lọc v4
  là bản đầu, chỉ khác ở đầu ra và ngưỡng: ở đây ngưỡng chọn theo F1 hoặc precision trên vàng, không theo recall.
- **Bộ chọn câu căn cứ:** với mỗi cạnh dự đoán, chọn một câu trong cửa sổ định nghĩa của đích làm căn cứ. Câu trích của LLM trong nhật ký là nhãn
  "rationale" cho bước này, theo cách ERASER đánh giá rationale bằng mức khớp với rationale của người và mức trung thực
  ([ACL 2020](https://aclanthology.org/2020.acl-main.408/)). Như vậy vẫn giữ được hợp đồng R12 (câu nguyên văn trong cửa sổ) mà không sinh văn bản.
- **Loại cạnh:** `can_de_hieu` hay `cong_cu` là một đầu ra phụ, học từ `prerequisite_kind`.
- **Nhất quán toàn cục:** giữ A9 và A10 như v3 (gỡ chu trình, R17, rút gọn bắc cầu).

### 8.4 Cách đo

*Suy luận:* bốn điểm về cách đo:
- Chia theo tài liệu (leave-one-document-out); không bao giờ để cặp của cùng một tài liệu nằm ở cả tập học và tập đo.
- Báo Q6, Q7, bao đóng P/R kèm Wilson 95%, đặt cạnh đồ thị LLM v3 trên cùng vàng.
- Chấm mô hình như người gán thứ ba: κ giữa mô hình và từng người, so với κ giữa hai người. Ở xstk, hai người gán chỉ cùng chọn 20 cạnh và khác nhau 67
  cạnh ([kết quả tập giữ lại v3](ket-qua-tap-giu-lai-v3-2026-10-04.md)); PREAP báo đồng thuận 0,45–0,71
  ([TKL 2023](https://doi.org/10.1007/s10758-023-09682-6)). Mô hình không thể "vượt" trần này một cách có nghĩa.
- Báo riêng độ khớp với nhãn LLM, vì độ khớp này chỉ cho biết học trò giống thầy tới đâu.

### 8.5 Thứ tự làm

*Suy luận:* thứ tự hợp lý cho seminar:
1. Dùng chung bảng E0 của v4, huấn luyện A8 ba lớp bằng GBDT trên tài liệu tiếng Việt, đo trên vàng doc-1. Đây là kết quả đầu tiên để báo cáo.
2. Thêm bộ chọn câu căn cứ và cross-encoder; so với bậc GBDT.
3. Thay C8 (câu định nghĩa) và A2 (vai trò vùng), vì hai khâu này quyết vị trí dạy và dãy học.
4. Thay A3 và danh tính, khâu tốn công gán nhãn nhất.
5. Làm vàng tiếng Việt mới cho phép đo cuối.

---

## 9. Rủi ro và câu hỏi mở

Các rủi ro chính, xếp theo mức nghiêm trọng:
- **Lọc nhầm làm mất độ phủ.** Đây là rủi ro số một: luật cũ chỉ hỏi cặp cùng cụm đã bỏ 78% cạnh vàng. Cạnh liên cụm, cạnh không có tên trong cửa sổ, và
  cạnh ngược thứ tự sách là các nhóm dễ bị lọc nhất; E3 phải phân rã đúng các nhóm này.
- **Dịch chuyển theo tài liệu và theo miền.** CPRL tụt từ 0,79–0,80 xuống 0,22–0,64 khi đổi miền, PRELEARN từ 0,887 xuống 0,690. Một cuốn luật học hay sinh
  học có thể làm bộ lọc hỏng lặng lẽ; kiểm mẫu theo tài liệu là lưới an toàn.
- **Trần của thầy.** Bộ lọc chỉ giữ được cạnh LLM tìm ra. Bản seminar chép cả lỗi có hệ thống của LLM: khái niệm khung làm tiên quyết ở doc-4, vùng "Cách
  giải" bị gán đề cương ở xstk.
- **Nhãn không ổn định.** Phán quyết LLM có thể đổi giữa các lượt chạy. Dùng "thứ tự đầu trả `create`" làm dương giúp bộ lọc thận trọng hơn, nhưng không
  khử được hết.
- **Phản hồi lỗi.** Ở doc-4, 12% cặp bị hoãn vì phản hồi lỗi ở ít nhất một thứ tự; cặp lỗi ngay ở thứ tự đầu không có nhãn. Nếu nhóm này chứa nhiều
  dương, recall đo trên phần có nhãn sẽ lạc quan.
- **Đa ngôn ngữ.** Mô hình học từ tài liệu tiếng Việt và tiếng Anh; phân bố đặc trưng ở chữ viết không cách từ (bigram ký tự) có thể khác hẳn.
- **Thời gian chạy.** Cross-encoder trên mọi cặp có thể tốn thêm phút trên CPU. Phải đo trước khi chọn bậc 2.
- **Vàng nhỏ và nhiễu.** Mỗi tài liệu chỉ có vài chục cạnh vàng, nên khoảng tin cậy của Q7 rộng. Thước đo chính của bộ lọc phải là PC trên hàng nghìn cặp
  LLM-dương, cộng việc đọc từng cạnh vàng mất.
- **Giấy phép trong seminar:** GPL v3 (VnCoreNLP) và AGPL v3 (PhoBERT-base-v2) không được lọt vào mã sản phẩm.

Các câu hỏi mở cần chủ dự án quyết:
- **Mục tiêu PC:** 0,98 hay 0,99, tính trên mọi cạnh hay chỉ cạnh cứng `can_de_hieu`?
- **Kiểm mẫu:** chấp nhận chi phí kiểm mẫu cỡ 500 lời gọi mỗi cuốn để giám sát ở mức 0,95 không? Có cần chứng nhận 0,99 (cỡ 2.600 lời gọi) cho cuốn lớn không?
- **xstk và doc-4 trong seminar:** kế hoạch v4 coi hai tài liệu này là tài liệu phát triển, nhưng ghi chú đã thống nhất về seminar (2026-10-02) nói không dùng
  tập giữ lại v3 để chỉnh bản seminar. Seminar có được dùng nhật ký và vàng của hai tài liệu này không?
- **Bậc 2:** nếu GBDT không đạt RR mong muốn, có chấp nhận thêm vài phút CPU mỗi cuốn cho cross-encoder không?
- **Phần cứng seminar:** máy có GPU để fine-tune PhoBERT hay BamiBERT tại máy không? Nếu không, có được dùng Colab hay Kaggle (gửi văn bản giáo trình ra ngoài)?
- **Vàng tiếng Việt mới:** ai gán, cho tài liệu nào, theo giao thức nào (PREAP hay giao thức hiện tại)?

---

## 10. Nguồn

Mức đọc ghi cuối mỗi dòng. Mọi trang được mở ngày 2026-10-04.

Các nguồn về học quan hệ tiên quyết:
- Partha Talukdar, William Cohen. *Crowdsourced Comprehension: Predicting Prerequisite Structure in Wikipedia.* BEA 2012. https://aclanthology.org/W12-2037/ — chỉ kiểm trang bài; số liệu lấy qua Bảng 1 của RefD.
- Chen Liang, Zhaohui Wu, Wenyi Huang, C. Lee Giles. *Measuring Prerequisite Relations Among Concepts.* EMNLP 2015. https://aclanthology.org/D15-1193/ — đọc toàn văn.
- Shuting Wang, Alexander G. Ororbia, Zhaohui Wu, Kyle Williams, Chen Liang, Bart Pursel, C. Lee Giles. *Using Prerequisites to Extract Concept Maps from Textbooks.* CIKM 2016. https://doi.org/10.1145/2983323.2983725 · https://www.microsoft.com/en-us/research/publication/using-prerequisites-extract-concept-maps-textbooks/ — chỉ đọc tóm tắt (máy chủ PSU từ chối kết nối, ACM DL chặn tải).
- Chen Liang, Jianbo Ye, Zhaohui Wu, Bart Pursel, C. Lee Giles. *Recovering Concept Prerequisite Relations from University Course Dependencies.* AAAI 2017. https://ojs.aaai.org/index.php/AAAI/article/view/10550 — chỉ đọc tóm tắt; số liệu bộ dữ liệu lấy qua CPRL.
- Liangming Pan, Chengjiang Li, Juanzi Li, Jie Tang. *Prerequisite Relation Learning for Concepts in MOOCs.* ACL 2017. https://aclanthology.org/P17-1133/ — đọc toàn văn.
- Igor Labutov, Yun Huang, Peter Brusilovsky, Daqing He. *Semi-Supervised Techniques for Mining Learning Outcomes and Prerequisites.* KDD 2017. https://doi.org/10.1145/3097983.3098187 — chỉ kiểm siêu dữ liệu.
- Chen Liang, Jianbo Ye, Shuting Wang, Bart Pursel, C. Lee Giles. *Investigating Active Learning for Concept Prerequisite Learning.* AAAI 2018 (EAAI). https://ojs.aaai.org/index.php/AAAI/article/view/11396 — đọc toàn văn.
- Irene Li, Alexander R. Fabbri, Robert R. Tung, Dragomir R. Radev. *What Should I Learn First: Introducing LectureBank for NLP Education and Prerequisite Chain Learning.* AAAI 2019. https://arxiv.org/abs/1811.12181 — đọc toàn văn (bản arXiv v1).
- Sudeshna Roy, Meghana Madhyastha, Sheril Lawrence, Vaibhav Rajan. *Inferring Concept Prerequisite Relations from Online Educational Resources.* IAAI 2019. https://arxiv.org/abs/1811.12640 — đọc toàn văn.
- Alessio Miaschi, Chiara Alzetta, Franco Alberto Cardillo, Felice Dell'Orletta. *Linguistically-Driven Strategy for Concept Prerequisites Learning on Italian.* BEA 2019. https://aclanthology.org/W19-4430/ — chỉ đọc tóm tắt.
- Jifan Yu và cộng sự. *MOOCCube: A Large-scale Data Repository for NLP Applications in MOOCs.* ACL 2020. https://aclanthology.org/2020.acl-main.285/ — đọc toàn văn phần dữ liệu và kết quả.
- Irene Li, Alexander Fabbri, Swapnil Hingmire, Dragomir Radev. *R-VGAE: Relational-variational Graph Autoencoder for Unsupervised Prerequisite Chain Learning.* COLING 2020. https://aclanthology.org/2020.coling-main.99/ — đọc tóm tắt và phần thiết lập.
- Chiara Alzetta, Alessio Miaschi, Felice Dell'Orletta, Frosina Koceva, Ilaria Torre. *PRELEARN @ EVALITA 2020: Overview of the Prerequisite Relation Learning Task for Italian.* EVALITA 2020. https://aclanthology.org/2020.evalita-1.54/ — đọc toàn văn.
- Shivam Pal, Vipul Arora, Pawan Goyal. *Finding Prerequisite Relations between Concepts using Textbook.* arXiv 2011.10337, 2020 (preprint). https://arxiv.org/abs/2011.10337 — đọc toàn văn.
- Chenghao Jia, Yongliang Shen, Yechun Tang, Lu Sun, Weiming Lu. *Heterogeneous Graph Neural Networks for Concept Prerequisite Relation Learning in Educational Data.* NAACL 2021. https://aclanthology.org/2021.naacl-main.164/ — đọc toàn văn; bảng đối chiếu bằng ảnh trang.
- Irene Li, Vanessa Yan, Tianxiao Li, Rihao Qu, Dragomir Radev. *Unsupervised Cross-Domain Prerequisite Chain Learning using Variational Graph Autoencoders.* ACL-IJCNLP 2021 (short). https://aclanthology.org/2021.acl-short.127/ — chỉ đọc tóm tắt.
- Yaxin Zhu, Hamed Zamani. *Predicting Prerequisite Relations for Unseen Concepts.* EMNLP 2022. https://aclanthology.org/2022.emnlp-main.585/ — đọc toàn văn phần bảng.
- Chiara Alzetta, Ilaria Torre, Frosina Koceva. *Annotation Protocol for Textbook Enrichment with Prerequisite Knowledge Graph.* Technology, Knowledge and Learning 29(1):197–228, 2023. https://doi.org/10.1007/s10758-023-09682-6 — đọc toàn văn phần đánh giá.
- Mehmet Cem Aytekin, Yücel Saygın. *ACE: AI-Assisted Construction of Educational Knowledge Graphs with Prerequisite Relations.* Journal of Educational Data Mining 16(2), 2024. https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737 — đọc toàn văn phần thí nghiệm.
- Rui Yang và cộng sự. *Leveraging Large Language Models for Concept Graph Recovery and Question Answering in NLP Education.* arXiv 2402.14293, 2024. https://arxiv.org/abs/2402.14293 — chỉ đọc tóm tắt.
- Youheng Bai, Zitao Liu, Teng Guo, Mingliang Hou, Kui Xiao. *Prerequisite Relation Learning: A Survey and Outlook.* ACM Computing Surveys, 2025. https://doi.org/10.1145/3733593 — chỉ đọc tóm tắt (Crossref).
- Miao Zhang và cộng sự. *Learning Concept Prerequisite Relation via Global Knowledge Relation Optimization (GKROM).* AAAI 2025. https://doi.org/10.1609/aaai.v39i2.32156 — chỉ đọc tóm tắt.
- Xinghe Cheng, Jiapu Wang, Chaobo He, Ruihai Dong, Quanlong Guan. *ProPRL: Property-Aware Prerequisite Relation Learning in Educational Knowledge Graphs.* arXiv 2608.03006, 2026 (preprint). https://arxiv.org/abs/2608.03006 — chỉ đọc tóm tắt.

Các nguồn về cascade, chưng cất và đặt ngưỡng:
- Paul Viola, Michael Jones. *Rapid Object Detection using a Boosted Cascade of Simple Features.* CVPR 2001. https://doi.org/10.1109/CVPR.2001.990517 — đọc toàn văn (bản tác giả: https://www.cs.cmu.edu/~efros/courses/LBMV07/Papers/viola-cvpr-01.pdf).
- Alexandru Niculescu-Mizil, Rich Caruana. *Predicting Good Probabilities with Supervised Learning.* ICML 2005. https://doi.org/10.1145/1102351.1102430 — chỉ kiểm siêu dữ liệu.
- Geoffrey Hinton, Oriol Vinyals, Jeff Dean. *Distilling the Knowledge in a Neural Network.* NIPS 2014 Deep Learning Workshop; arXiv 1503.02531. https://arxiv.org/abs/1503.02531 — chỉ đọc tóm tắt.
- Tianqi Chen, Carlos Guestrin. *XGBoost: A Scalable Tree Boosting System.* KDD 2016. https://doi.org/10.1145/2939672.2939785 — chỉ kiểm siêu dữ liệu.
- Alexander Ratner, Stephen H. Bach, Henry Ehrenberg, Jason Fries, Sen Wu, Christopher Ré. *Snorkel: Rapid Training Data Creation with Weak Supervision.* PVLDB 11(3):269–282, 2017. https://doi.org/10.14778/3157794.3157797 — chỉ kiểm siêu dữ liệu.
- Daniel Kang, Edward Gan, Peter Bailis, Tatsunori Hashimoto, Matei Zaharia. *Approximate Selection with Guarantees using Proxies (SUPG).* PVLDB 13, 2020, tr. 1990–2003. https://doi.org/10.14778/3407790.3407804 · https://arxiv.org/abs/2004.00827 — đọc toàn văn các phần phương pháp và thí nghiệm recall.
- George Papadakis, Dimitrios Skoutas, Emmanouil Thanos, Themis Palpanas. *Blocking and Filtering Techniques for Entity Resolution: A Survey.* ACM Computing Surveys 53(2):1–42, 2020. https://doi.org/10.1145/3377455 · https://arxiv.org/abs/1905.06167 — đọc phần định nghĩa thước đo.
- Shuohang Wang, Yang Liu, Yichong Xu, Chenguang Zhu, Michael Zeng. *Want To Reduce Labeling Cost? GPT-3 Can Help.* Findings of EMNLP 2021. https://aclanthology.org/2021.findings-emnlp.354/ — chỉ đọc tóm tắt.
- Curtis Northcutt, Lu Jiang, Isaac Chuang. *Confident Learning: Estimating Uncertainty in Dataset Labels.* JAIR 70:1373–1411, 2021. https://doi.org/10.1613/jair.1.12125 — chỉ đọc tóm tắt (Crossref).
- Lingjiao Chen, Matei Zaharia, James Zou. *FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance.* arXiv 2305.05176, 2023. https://arxiv.org/abs/2305.05176 — đọc toàn văn bản v1 (6 trang). Nơi đăng TMLR 2024 chỉ thấy qua kết quả tìm kiếm, OpenReview chặn truy cập: **chưa xác minh**.
- Cheng-Yu Hsieh và cộng sự. *Distilling Step-by-Step! Outperforming Larger Language Models with Less Training Data and Smaller Model Sizes.* Findings of ACL 2023. https://aclanthology.org/2023.findings-acl.507/ — chỉ đọc tóm tắt.
- Fabrizio Gilardi, Meysam Alizadeh, Maël Kubli. *ChatGPT Outperforms Crowd Workers for Text-Annotation Tasks.* PNAS 120(30), 2023. https://doi.org/10.1073/pnas.2305016120 — chỉ đọc tóm tắt (Crossref).
- Guillem Ramírez, Matthias Lindemann, Alexandra Birch, Ivan Titov. *Cache & Distil: Optimising API Calls to Large Language Models.* Findings of ACL 2024. https://arxiv.org/abs/2310.13561 — đọc toàn văn.
- Guillem Ramírez, Alexandra Birch, Ivan Titov. *Optimising Calls to Large Language Models with Uncertainty-Based Two-Tier Selection.* COLM 2024. https://arxiv.org/abs/2405.02134 — chỉ đọc tóm tắt.
- Anastasios Angelopoulos, Stephen Bates, Adam Fisch, Lihua Lei, Tal Schuster. *Conformal Risk Control.* ICLR 2024. https://proceedings.iclr.cc/paper_files/paper/2024/hash/f3549ef9b5ff520a7e41ff3cc306ab2b-Abstract-Conference.html — chỉ đọc tóm tắt.
- James A. Hanley (và Abby Lippman-Hand). *If Nothing Goes Wrong, Is Everything All Right? Interpreting Zero Numerators.* JAMA 249(13), 1983. https://doi.org/10.1001/jama.1983.03330370053031 — chỉ kiểm siêu dữ liệu; Crossref chỉ liệt kê một tác giả, tên đồng tác giả **chưa xác minh**.

Các nguồn về trích thuật ngữ, định nghĩa, viết tắt:
- Katerina Frantzi, Sophia Ananiadou, Hideki Mima. *Automatic Recognition of Multi-Word Terms: the C-value/NC-value Method.* International Journal on Digital Libraries 3:115–130, 2000. https://doi.org/10.1007/s007999900023 — chỉ đọc tóm tắt.
- Roberto Navigli, Paola Velardi. *Learning Word-Class Lattices for Definition and Hypernym Extraction.* ACL 2010. https://aclanthology.org/P10-1134/ — đọc toàn văn phần thí nghiệm.
- Ariel S. Schwartz, Marti A. Hearst. *A Simple Algorithm for Identifying Abbreviation Definitions in Biomedical Text.* PSB 8:451–462, 2003. https://psb.stanford.edu/psb-online/proceedings/psb03/schwartz.pdf — đọc tóm tắt và phần đầu.
- Sasha Spala, Nicholas A. Miller, Yiming Yang, Franck Dernoncourt, Carl Dockhorn. *DEFT: A Corpus for Definition Extraction in Free- and Semi-structured Text.* LAW 2019. https://aclanthology.org/W19-4015/ — đọc toàn văn phần dữ liệu.
- Sasha Spala, Nicholas Miller, Franck Dernoncourt, Carl Dockhorn. *SemEval-2020 Task 6: Definition Extraction from Free Text with the DEFT Corpus.* SemEval 2020. https://aclanthology.org/2020.semeval-1.41/ — đọc toàn văn.
- Ayla Rigouts Terryn, Véronique Hoste, Els Lefever. *In No Uncertain Terms: a Dataset for Monolingual and Multilingual Automatic Term Extraction from Comparable Corpora.* Language Resources and Evaluation 54:385–418, 2020. https://doi.org/10.1007/s10579-019-09453-9 — chỉ đọc tóm tắt.
- Ayla Rigouts Terryn, Véronique Hoste, Patrick Drouin, Els Lefever. *TermEval 2020: Shared Task on Automatic Term Extraction Using the Annotated Corpora for Term Extraction Research (ACTER) Dataset.* CompuTerm 2020. https://aclanthology.org/2020.computerm-1.12/ — chỉ đọc tóm tắt.
- Christian Lang, Lennart Wachowiak, Barbara Heinisch, Dagmar Gromann. *Transforming Term Extraction: Transformer-Based Approaches to Multilingual Term Extraction Across Domains.* Findings of ACL-IJCNLP 2021. https://aclanthology.org/2021.findings-acl.316/ — đọc toàn văn phần kết quả.
- Chau Vo, Tru Cao, Ngoc Truong, Trung Ngo, Dai Bui. *Automatic Medical Term Extraction from Vietnamese Clinical Texts.* Terminology 28(2):299–327, 2022. https://doi.org/10.1075/term.20037.vo — chỉ đọc tóm tắt (Crossref).
- Amir Pouran Ben Veyseh, Nicole Meister, Seunghyun Yoon, Rajiv Jain, Franck Dernoncourt, Thien Huu Nguyen. *MACRONYM: A Large-Scale Dataset for Multilingual and Multi-Domain Acronym Extraction.* COLING 2022. https://aclanthology.org/2022.coling-1.292/ — đọc toàn văn.
- Urchade Zaratiana, Nadi Tomeh, Pierre Holat, Thierry Charnois. *GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer.* NAACL 2024. https://aclanthology.org/2024.naacl-long.300/ — đọc toàn văn phần dữ liệu và kết quả.
- Jay DeYoung và cộng sự. *ERASER: A Benchmark to Evaluate Rationalized NLP Models.* ACL 2020. https://aclanthology.org/2020.acl-main.408/ — chỉ đọc tóm tắt.

Các nguồn về công cụ và mô hình tiếng Việt, đa ngôn ngữ:
- Thanh Vu, Dat Quoc Nguyen, Dai Quoc Nguyen, Mark Dras, Mark Johnson. *VnCoreNLP: A Vietnamese Natural Language Processing Toolkit.* NAACL 2018 Demonstrations. https://aclanthology.org/N18-5012/ — đọc toàn văn; README và LICENSE: https://github.com/vncorenlp/VnCoreNLP.
- Dat Quoc Nguyen, Anh Tuan Nguyen. *PhoBERT: Pre-trained Language Models for Vietnamese.* Findings of EMNLP 2020. https://aclanthology.org/2020.findings-emnlp.92/ — đọc toàn văn; README: https://github.com/VinAIResearch/PhoBERT.
- Alexis Conneau và cộng sự. *Unsupervised Cross-lingual Representation Learning at Scale (XLM-R).* ACL 2020. https://aclanthology.org/2020.acl-main.747/ — đọc các bảng XNLI và CC-100.
- Linh The Nguyen, Dat Quoc Nguyen. *PhoNLP: A Joint Multi-task Learning Model for Vietnamese Part-of-Speech Tagging, Named Entity Recognition and Dependency Parsing.* NAACL 2021 Demonstrations. https://aclanthology.org/2021.naacl-demos.1/ — chỉ đọc tóm tắt.
- Minh Van Nguyen, Viet Dac Lai, Amir Pouran Ben Veyseh, Thien Huu Nguyen. *Trankit: A Light-Weight Transformer-based Toolkit for Multilingual Natural Language Processing.* EACL 2021 Demonstrations. https://aclanthology.org/2021.eacl-demos.10/ — chỉ đọc tóm tắt; trang hiệu năng: https://trankit.readthedocs.io/en/latest/performance.html.
- Stanza, trang hiệu năng chính thức (v1.5.1 trên UD 2.12). https://stanfordnlp.github.io/stanza/performance.html — đọc bảng.
- underthesea, README trên GitHub (nhánh main, cập nhật 2026-10-03). https://github.com/undertheseanlp/underthesea — đọc.
- Dat Quoc Nguyen, Thinh Pham, Chi Tran, Linh The Nguyen. *BamiBERT: A New BERT-based Language Model for Vietnamese.* arXiv 2607.02259, 2026 (preprint). https://arxiv.org/abs/2607.02259 — chỉ đọc tóm tắt; thẻ mô hình: https://huggingface.co/Qualcomm-AI-Research/BamiBERT.
- Liang Wang, Nan Yang, Xiaolong Huang, Linjun Yang, Rangan Majumder, Furu Wei. *Multilingual E5 Text Embeddings: A Technical Report.* arXiv 2402.05672, 2024. https://arxiv.org/abs/2402.05672 — chỉ đọc tóm tắt; thẻ mô hình: https://huggingface.co/intfloat/multilingual-e5-large-instruct.
- Jianlyu Chen, Shitao Xiao, Peitian Zhang, Kun Luo, Defu Lian, Zheng Liu. *M3-Embedding (BGE-M3).* Findings of ACL 2024. https://aclanthology.org/2024.findings-acl.137/ — chỉ đọc tóm tắt.
- Loc Pham, Tung Luu, Thu Vo, Minh Nguyen, Viet Hoang. *VN-MTEB: Vietnamese Massive Text Embedding Benchmark.* Findings of EACL 2026, tr. 1705–1725. https://aclanthology.org/2026.findings-eacl.86/ — đọc Bảng 3.

Các nguồn về gom trùng và vai trò vùng:
- Yuliang Li, Jinfeng Li, Yoshihiko Suhara, AnHai Doan, Wang-Chiew Tan. *Deep Entity Matching with Pre-Trained Language Models (Ditto).* PVLDB 14(1):50–60, 2020. https://doi.org/10.14778/3421424.3421431 · https://arxiv.org/abs/2004.00584 — chỉ đọc tóm tắt.
- Fangyu Liu, Ehsan Shareghi, Zaiqiao Meng, Marco Basaldella, Nigel Collier. *Self-Alignment Pretraining for Biomedical Entity Representations (SapBERT).* NAACL 2021. https://aclanthology.org/2021.naacl-main.334/ — chỉ đọc tóm tắt.
- Franck Dernoncourt, Ji Young Lee. *PubMed 200k RCT: a Dataset for Sequential Sentence Classification in Medical Abstracts.* IJCNLP 2017. https://aclanthology.org/I17-2052/ — chỉ đọc tóm tắt.
- Arman Cohan, Iz Beltagy, Daniel King, Bhavana Dalvi, Dan Weld. *Pretrained Language Models for Sequential Sentence Classification.* EMNLP-IJCNLP 2019. https://aclanthology.org/D19-1383/ — chỉ đọc tóm tắt.
- Sebastian Arnold, Rudolf Schneider, Philippe Cudré-Mauroux, Felix A. Gers, Alexander Löser. *SECTOR: A Neural Model for Coherent Topic Segmentation and Classification.* TACL 2019. https://aclanthology.org/Q19-1011/ — chỉ đọc tóm tắt.

Các tài liệu nội bộ của dự án được dẫn:
- [Nghiên cứu v4: tiền và thời gian](nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md) — chi phí pass phụ, hỏi lười, phản hồi lỗi.
- [Kết quả tập giữ lại v3](ket-qua-tap-giu-lai-v3-2026-10-04.md) — lỗi A2 "Cách giải", R17 ở doc-4, vàng nhiễu.
- [Kế hoạch đưa đồ thị tới mức dùng được](ke-hoach-dua-do-thi-toi-muc-dung-duoc.md) — recall là ràng buộc siết, 78% cạnh liên cụm, cạnh ngầm.
- [Kết quả vé 12, lượt cuối](ket-qua-v3-12-cuoi-2026-10-03.md) — doc-2: 9.513 cặp, 1.060 cạnh pass phụ.
- [Spec v3](../doc/v3-lo-trinh-doc-duoc-spec.md) — R12 (cửa sổ định nghĩa), R17, nguyên tắc đa ngôn ngữ.
- [Kế hoạch v4](../task/v4/00-ke-hoach.md) và [kế hoạch v3, mục "Hướng v4"](../task/v3-lo-trinh-doc-duoc/00-ke-hoach.md) — vé R-02, ý tưởng bộ lọc cặp.
- [Báo cáo A6–A8](nghien-cuu-a6-a8-cum-chu-de-va-2b.md) và [báo cáo A4/A5](nghien-cuu-a4-a5-hop-nhat-thuc-the.md) — văn liệu tiên quyết thời LLM, ER và blocking.
- Mã: [`mentions.py`](../src/doc2roadmap/domain/mentions.py) (nguồn cặp ứng viên), [`secondary.py`](../src/doc2roadmap/domain/secondary.py) (hồ sơ cặp, kiểm và gộp phán quyết).
