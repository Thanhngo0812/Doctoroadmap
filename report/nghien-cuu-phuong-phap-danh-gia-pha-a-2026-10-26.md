Trạng thái: xong — đã xong mục 0–14 và danh mục tài liệu tham khảo

# Nghiên cứu phương pháp đánh giá Pha A — 2026-10-26

## 0. Tóm tắt khuyến nghị (viết cuối)

Mười khuyến nghị quan trọng nhất, theo thứ tự ưu tiên. Chi tiết và nguồn ở mục 13.
1. **Đồng thuận A8 báo bằng PSA/F1 giữa hai người, không bằng κ.** Khi chỉ ghi cặp dương, κ không tính được; F1 giữa hai người bằng đồng thuận dương đặc hiệu [35]. Số hiện có cho PSA ≈ 0,35–0,42 (nếu "20/87" là chung/hợp); báo thêm bản có tín dụng bắc cầu như PREAP [34].
2. **Trần người cùng thước:** so máy với từng người bằng F1, đặt cạnh F1 người–người; không so máy với vàng hội ý rồi gọi là "gần trần người".
3. **Cạnh trong một cuốn không độc lập.** Bỏ Wilson/bootstrap theo cạnh trên số gộp nhiều cuốn; dùng bootstrap trong từng cuốn hoặc hai tầng [55]; so hai hệ bằng randomization ghép cặp phân tầng theo cuốn [52].
4. **Với ≤ 5 cuốn không thể có kết luận "có ý nghĩa ở mức 0,05" xuyên cuốn** bằng sign test (p tối thiểu = 2·0,5ⁿ). Trình bày kết quả xuyên cuốn là mô tả; khái quát sang môn khác cần thêm sách [48], [50].
5. **Nhiễu LLM là sàn của mọi so sánh.** Chuẩn hoá E4 thành K nhiễu loạn giữ nghĩa khai trước; báo trung bình, khoảng và độ ổn định [59], [60]; không tuyên bố cải thiện nhỏ hơn ±0,15.
6. **Không dùng tập kiểm cân bằng cho pass phụ.** PRELEARN, LectureBank, RefD cân bằng âm/dương nên thổi precision [29], [32], [33]; báo PR-AUC và P/R tại ngưỡng trên phân phối ứng viên thật; chia theo cuốn để tránh rò rỉ bắc cầu.
7. **Giữ chấm mù cạnh dư và tính "precision hiệu chỉnh"** như TExEval-2 chấm tay quan hệ mới [37]; vàng không đầy đủ phạt oan cạnh đúng.
8. **Ablation oracle + bảng thác nước quy lỗi:** thay A1, A2, A3+A4 bằng vàng từng mức để đo trần và đóng góp; quy mỗi cạnh vàng bị mất về khâu đầu tiên làm hỏng nó [63], [65]. Không đặt số oracle cạnh số đầu-cuối [63], [64].
9. **Ba tầng nhãn, ba tên gọi:** vàng người / bạc agentic + duyệt / bạc. Bạc cho phát triển; số cuối đo trên vàng người; hiệu chuẩn bạc bằng mẫu vàng, nếu có ba người thì chạy alt-test [57], [58].
10. **Chi phí là thước hạng nhất và giao thức phải đăng ký trước.** Mỗi lần chạy ghi phút/cuốn (tách chờ quota), USD/cuốn, số lời gọi, phiên bản mô hình; vẽ đường chất lượng–chi phí [66], [67]; commit giao thức đánh giá cuối trước khi mở tập khoá [71]; datasheet cho từng bộ vàng [69], [70].

Thước theo khâu, tóm gọn: A1 giữ M3 làm chính, thêm "complete entry" F1 [1], [2]; A2 thêm vàng và recall `noi_dung`; A3 giữ recall danh sách mù, thêm luật khớp hai mức và precision bằng pool [12], [14]; A4 báo precision gộp và recall ước lượng phân tầng [23]; A5 coi `uncertain` là từ chối, báo độ phủ + độ chính xác có chọn lọc [27]; A9/A10 giữ Q6/Q7, τ chỉ chẩn đoán.

## 1. Cấu trúc tài liệu và đọc PDF

Quy ước trong tệp: "**Nguồn nói**" là điều đã đọc trong bản gốc; "**Suy luận**" là đánh giá của tôi cho dự án.

### 1.1 Văn liệu chuẩn

Có bốn họ thước đáng dùng cho A1.

**(a) Trích mục lục sách — ICDAR Book Structure Extraction (2009–2013).** Nguồn nói [1]:
- Thước theo tiêu đề (title-based): ghép mục của hệ với mục vàng bằng khoảng cách sửa (edit distance) trên chuỗi tiêu đề, để chịu được biến thể như "3 His Birth…" và "Chapter 3: His Birth…".
- Sau khi ghép tiêu đề, kiểm thêm **độ sâu** (level) và **trang đích** (link). Một mục là "khớp trọn" (complete entry) khi cả độ sâu lẫn số trang đều đúng.
- P/R/F tính **cho từng cuốn rồi lấy trung bình trên các cuốn** (macro theo tài liệu). Bảng điểm báo bốn cột: Titles, Levels, Links, Complete entries.
- Thước thứ hai (link-based, của XRCE) ghép mục chủ yếu theo trang đích thay vì chuỗi; điểm cao hơn vì lỗi chữ trong tiêu đề không làm hỏng cả mục.
- Ban tổ chức nêu hướng tương lai là thêm đánh giá định tính về độ hữu dụng của mục lục, ngoài P/R.

**(b) FinTOC (2019–2022), mục lục tài liệu tài chính PDF có lớp chữ.** Nguồn nói [2]:
- Hai việc: nhận tiêu đề (title detection, TD) và dựng mục lục (TOC generation, gán độ sâu).
- TD chấm bằng F1; một tiêu đề máy là đúng khi khớp tiêu đề vàng theo Levenshtein chuẩn với ngưỡng 0,852.
- TOC chấm bằng **trung bình điều hoà của Inex F1 và Inex level accuracy**. Inex F1 coi mục đúng khi khớp tiêu đề và cùng số trang. Level accuracy = số mục đúng trang và đúng độ sâu chia cho số mục đúng trang.
- Điểm tính **theo từng tài liệu rồi lấy trung bình** trên tập kín.
- Thước này chuyển thể từ script ICDAR 2013 (thay Levenshtein tuỳ biến bằng Levenshtein chuẩn).

**(c) Dựng lại cấu trúc phân cấp — HRDoc và Comp-HRDoc.** Nguồn nói [3], [4]:
- HRDoc gán nhãn **từng dòng** (semantic unit) và quan hệ cha–con giữa các dòng. Phân loại dòng chấm bằng F1 theo từng lớp (bảng có cột Micro và Macro F1).
- Cấu trúc cây chấm bằng **Semantic-TEDS (STEDS)**: `STEDS = 1 − TED(T, T̂) / max(|T|, |T̂|)`, với TED là khoảng cách sửa cây (tree edit distance) và một nút khớp trọn khi **cả nhãn lẫn chữ** giống vàng [3].
- Comp-HRDoc dùng STEDS (micro và macro) cho cả trích mục lục và dựng cây, chấm đầu-cuối (không dựa vào thứ tự đọc vàng). Thứ tự đọc chấm bằng REDS: khoảng cách sửa kiểu Levenshtein giữa nhóm máy và nhóm vàng (ghép nhóm bằng thuật toán Hungary), chuẩn hoá theo số đơn vị cơ bản, lấy 1 trừ đi [4]. Bài [4] là bản arXiv "submitted to Pattern Recognition"; tôi chưa xác nhận bản đã in.

**(d) Phân tích trang PDF tổng quát — OmniDocBench, DocLayNet, ReadingBank.**
- OmniDocBench (CVPR 2025) [5]: văn bản chấm bằng khoảng cách sửa chuẩn hoá (normalized edit distance), trung bình theo trang. **Thứ tự đọc cũng chấm bằng khoảng cách sửa chuẩn hoá, chỉ trên thành phần chữ**; bảng, hình và phần bị bỏ qua không tính. Trước khi chấm có bước "Adjacency Search Match": gộp/tách đoạn ở cả vàng và máy để tìm ghép tốt nhất, tránh phạt oan do cách cắt đoạn. Đầu trang, chân trang, số trang, chú thích hình được **ghép nhưng không tính điểm** vì các hệ xử lý không thống nhất. Bộ có trang giáo trình (textbook) và báo kết quả theo kiểu bố cục (một cột, nhiều cột).
- DocLayNet (KDD 2022) [7]: bố cục chấm bằng mAP@0.5–0.95 trên hộp có nhãn. Một phần trang được gán hai–ba lần để đo **đồng thuận người bằng chính thước mAP**; các mô hình kém đồng thuận người khoảng 10%.
- LayoutReader/ReadingBank (EMNLP 2021) [6]: thứ tự đọc chấm bằng BLEU mức trang và **ARD (Average Relative Distance)**: với mỗi phần tử vàng, lấy độ lệch vị trí; phần tử bị thiếu bị phạt bằng độ dài dãy vàng n.

**(e) Thứ tự và phân đoạn.**
- Kendall tau [8]: `τ = 1 − 2·S(π, σ) / (N(N−1)/2)`, S là số phép đổi chỗ kề nhau cần để biến thứ tự này thành thứ tự kia, N là số phần tử; miền [−1, 1]; cần hiệu chỉnh khi có đồng hạng. Lapata cho thấy τ tương quan với điểm người (r = 0,45) và thời gian đọc (r = −0,48), gần mức đồng thuận giữa người (r trung bình 0,56). Tau đòi hai dãy cùng tập phần tử.
- Phân đoạn văn bản: P/R trên ranh giới không nhạy với "trượt gần" (near miss). Pk (Beeferman và cộng sự) phạt bỏ sót nặng hơn thêm thừa và bỏ qua số ranh giới trong cửa sổ; WindowDiff sửa các lỗi đó [9].

### 1.2 Đối chiếu với M1–M5

Bảng sau đặt thước hiện có cạnh thước văn liệu gần nhất.

| Thước hiện có | Văn liệu gần nhất | Khác biệt chính |
|---|---|---|
| M1 P/R/F1 tiêu đề (phủ ≥ nửa dòng, cùng trang) | ICDAR "Titles", FinTOC TD F1 [1], [2] | Văn liệu ghép bằng Levenshtein có ngưỡng; dự án ghép theo phủ dòng. Cả hai đều cần cùng trang/đích. |
| M2 độ đúng cha | ICDAR "Levels", FinTOC level accuracy, HRDoc quan hệ cha [1]–[3] | Văn liệu tính độ sâu **có điều kiện** trên mục đã ghép đúng; nên nói rõ mẫu số của M2. |
| M3 tỉ lệ ký tự thân bài có mục sâu nhất đúng | Không tìm thấy thước trùng khớp | Gần nhất là STEDS (cây có chữ) [3] và Pk/WindowDiff (ranh giới) [9]. |
| M4 vai trò dòng + Kendall tau | HRDoc F1 theo lớp dòng [3]; OmniDocBench edit distance thứ tự [5]; ARD [6]; τ [8] | τ không phạt phần tử bị thiếu; edit distance/ARD có phạt. |
| M5 giây/trang, RAM | Không là thước chính ở các benchmark trên | Xem mục 12. |

**Suy luận cho dự án.**
- **Giữ M3 làm thước chính.** Nó đo đúng thứ khâu sau cần (mỗi ký tự thân bài rơi vào đúng mục lá), có trọng số theo độ dài nên lỗi ở mục dài nặng hơn. Tôi không thấy văn liệu có thước y hệt; khi báo cáo nên gọi nó là "độ chính xác gán ký tự vào mục lá" (character-weighted leaf-section accuracy) và **tự định nghĩa bằng công thức**, không gán cho nguồn nào.
- **Thêm một thước có trong văn liệu để so được:** "complete entry F1" kiểu ICDAR/FinTOC (tiêu đề + độ sâu + trang) hoặc STEDS trên cây mục. Cài STEDS cần thư viện tree edit distance (APTED của Pawlik & Augsten, mà [3] dẫn); "complete entry F1" rẻ hơn và đủ.
- **Báo macro theo cuốn** như ICDAR và FinTOC [1], [2], kèm micro. Với 6–8 cuốn, macro cho mỗi cuốn một phiếu, tránh một cuốn dày át cả tập.
- **M2 nêu rõ mẫu số:** "trong các tiêu đề ghép đúng" (như level accuracy [2]) hay "trên mọi tiêu đề vàng". Hai cách cho số khác nhau.
- **M4:** τ tính trên phần tử chung nên bỏ qua dòng bị mất. Báo kèm tỉ lệ dòng bị mất hoặc dùng edit distance chuẩn hoá như [5] để phạt cả mất lẫn sai chỗ. Học theo [5]: đầu/chân trang ghép nhưng không tính.
- **Đồng thuận người cho A1:** DocLayNet [7] đo đồng thuận bằng chính thước chấm máy. Nếu có trang được hai người gán, tính M1/M3 giữa hai người làm **trần người** để đặt số máy vào bối cảnh. Nhãn D-02 là agentic + duyệt agentic, nên đây là trần "bạc–bạc", phải ghi rõ.

## 2. Vai trò vùng

### 2.1 Văn liệu

Đây là bài phân loại đa lớp thông thường; văn liệu chuẩn chủ yếu bàn cách lấy trung bình.
- **Macro-F1 có hai công thức.** Nguồn nói [10]: "averaged F1" là trung bình cộng các F1 theo lớp; "F1 of averages" là trung bình điều hoà của P trung bình và R trung bình. Hai cách lệch nhau tới 0,5 và có thể đảo thứ hạng hệ; cách thứ hai "dễ dãi" với bộ phân loại lệch, nhất là khi dữ liệu mất cân bằng. Tác giả khuyên dùng **trung bình cộng các F1 theo lớp**, và ít nhất phải ghi rõ công thức.
- HRDoc [3] chấm phân loại vai trò **dòng** bằng F1 theo từng lớp, báo cả micro và macro. Đây là tiền lệ gần nhất cho M4 và cho A2 nếu đơn vị là dòng.
- DocLayNet [7] báo đồng thuận người **theo từng lớp**; lớp khó (Picture) có đồng thuận thấp hơn hẳn lớp dễ (Page-footer). Bài học: đồng thuận và điểm máy nên báo theo lớp, không chỉ một số gộp.

### 2.2 Suy luận cho A2

Các điểm sau là khuyến nghị của tôi, không phải điều nguồn nói.
- **Đơn vị đo:** section là đơn vị quyết định nên chấm theo section. Nhưng lỗi trên section dài đắt hơn; báo kèm **bản có trọng số ký tự** (giống tinh thần M3).
- **Chi phí lệch:** lỗi đắt nhất là gán nhầm `noi_dung` thành lớp khác, vì nội dung bị loại khỏi trích khái niệm. Sự cố mất 29/62 cạnh vàng là loại lỗi này. Vì vậy báo riêng **recall của `noi_dung`** (theo section và theo ký tự) như chỉ số chính, macro-F1 là phụ.
- **Thước hạ nguồn:** đếm số khái niệm vàng/cạnh vàng nằm trong vùng bị gán sai. Đây là cách đo "lỗi A2 làm mất bao nhiêu ở A8", nối sang ablation oracle ở mục 11.
- **Lớp hiếm** (`de_cuong`, `hanh_chinh`…): báo **số đếm tuyệt đối và support** cho từng lớp, kèm ma trận nhầm lẫn. Với vài chục section, F1 của lớp có 3–5 mẫu không ổn định; gộp thành hai tầng để có một số tin được: (1) nội dung vs không nội dung, (2) sáu lớp chi tiết chỉ để chẩn đoán.
- **Vàng:** chưa có. Cần một người gán section của các cuốn phát triển theo phiếu ngắn; có thể tiền gán bằng luật rồi người sửa (như OmniDocBench làm với bố cục [5]), nhưng phải ghi rõ đó là "người sửa bản máy", vì tiền gán gây thiên lệch neo.
- **Bất ổn LLM theo cách gom lô:** đây là câu hỏi độ ổn định, không phải độ đúng. Đo bằng tỉ lệ section đổi nhãn giữa các cách gom lô (xem mục 10).

## 3. Trích khái niệm

### 3.1 Văn liệu

A3 gần nhất với trích cụm từ khoá (keyphrase extraction) và chú giải khái niệm cho giáo trình. Có năm điểm chuẩn.

**(a) Khớp chính xác là chuẩn truyền thống.** Nguồn nói [11] (SemEval-2010 Task 5): hệ nộp danh sách xếp hạng 15 cụm mỗi bài; chấm bằng **khớp chính xác sau khi stem** (Porter), P/R/F **micro** ở top 5, 10, 15; xếp hạng theo F@15. Người gán được dặn chỉ chọn cụm có trong văn bản, nhưng vẫn có 15% cụm của người đọc không xuất hiện nguyên văn, nên **trần recall chỉ 85%**. Điểm tốt nhất chỉ 27,5% F: thước khớp chính xác rất khắt khe.

**(b) Khớp chính xác đánh giá thấp hệ.** Nguồn nói [12]: khớp chính xác bỏ qua biến thể hình thái, cụm lồng nhau và đồng nghĩa. Tác giả đề xuất khớp gần gồm Morph (số nhiều), Includes (cụm máy chứa trọn cụm vàng) và PartOf (cụm máy là phần của cụm vàng). Bốn giám khảo chấp nhận 96% cặp Morph, 80% cặp Includes, nhưng chỉ 44% cặp PartOf; nên họ chỉ giữ Exact ∪ Morph ∪ Includes (đồng thuận người 83%). Họ cũng đề xuất **R-precision** (precision khi số cụm lấy bằng số cụm vàng) vì cắt cố định top-k làm méo kết quả khi số cụm vàng mỗi tài liệu khác nhau.

**(c) Khớp ngữ nghĩa.** Nguồn nói [13] (KPEval): `SemP = (1/|P|) Σ_p max_y sim(p, y)`, `SemR = (1/|Y|) Σ_y max_p sim(p, y)`, SemF1 là trung bình điều hoà; sim là cosine trên embedding cụm (mô hình mpnet tinh chỉnh SimCSE). SemF1 tương quan với người tốt hơn F1 khớp chính xác (Kendall τ mức cụm 0,735 so với 0,590 trên KP20k). Đồng thuận người ở mức Krippendorff α ≈ 0,74–0,77. Tác giả kết luận đánh giá cũ **đánh giá thấp LLM**.

**(d) Vàng không đầy đủ — pooling kiểu TREC.** Nguồn nói [14]: bộ kiểm TREC dựng bằng pooling (gộp kết quả đầu của nhiều hệ, người chỉ phán phần gộp); các thước thông thường **không bền khi phán định thiếu nhiều**; bpref chỉ dùng tài liệu đã phán nên bền hơn. Điều kiện để bpref hợp lệ: xác suất một mục vào pool độc lập với việc nó đúng hay sai; một hệ "mới lạ" không góp vào pool có thể bị chấm oan. Bài cũng nhắc Zobel đã chỉ ra thiên lệch chống lại hệ không góp vào pool.

**(e) Chú giải khái niệm giáo trình.** Nguồn nói [15]: chú giải khái niệm theo kiểu tự phát (ad hoc) cho đồng thuận thấp, cả với chuyên gia lẫn crowdworker. Nhóm Pittsburgh xây quy trình có **sổ mã (codebook)** cập nhật sau mỗi vòng; 10 luật, không thêm luật nào sau vòng 9. Phát hiện then chốt: **nguyên nhân chính của đồng thuận thấp trước hội ý là người gán vô tình bỏ sót khái niệm mà họ đồng ý là nên gán**; họ thêm bước "soát khái niệm bị bỏ sót" sau khi gán độc lập. Wang và cộng sự (DocEng 2015) cũng dựng vàng bằng cách người gán khái niệm quan trọng cho từng chương của ba giáo trình [16] (chỉ đọc tóm tắt).

### 3.2 Đối chiếu với thước Q3 "liệt kê mù"

Q3 hiện là **recall trên danh sách người liệt kê**. Đây là đúng kiểu vàng của [11], [15], nhưng thiếu ba thứ.

| Vấn đề | Văn liệu nói | Hệ quả cho Q3 |
|---|---|---|
| Luật khớp | Exact rất khắt khe; Morph/Includes được người chấp nhận, PartOf thì không [12] | Phải ghi luật khớp bằng văn bản; báo cả "nghiêm" và "nới" |
| Chỉ có recall | Danh sách người không đầy đủ; precision trên danh sách sẽ thấp oan | Precision cần phán riêng trên pool [14] |
| Người bỏ sót | Bỏ sót là nguồn bất đồng chính [15] | Một người liệt kê thì mẫu số recall thiếu; cần bước soát |

**Suy luận cho dự án.**
- **Giữ Q3 (recall trên danh sách mù)** làm chỉ số chính cho A3, vì A3 là khâu "đừng bỏ sót"; khâu sau còn lọc.
- **Luật khớp hai mức:** (1) nghiêm = trùng sau chuẩn hoá (NFC, chữ thường, bỏ dấu câu, giữ dấu tiếng Việt); (2) nới = thêm Includes và biến thể viết tắt/tên tiếng Anh–Việt đã khai trong alias, **không** tự nhận PartOf [12]. Cặp mơ hồ do người phán và đếm riêng.
- **Precision bằng pooling:** gộp danh sách người + đầu ra mọi biến thể hệ đang so → người phán mù từng mục (khái niệm trọng yếu / khái niệm phụ / không phải khái niệm / sai độ hạt). Precision = tỉ lệ mục máy được phán đúng; recall tương đối = so với hợp mọi mục đúng. Hệ đem so phải **có góp vào pool** [14].
- **Vàng hai người + bước soát bỏ sót** [15]: hai người liệt kê độc lập, rồi mỗi người xem danh sách người kia và quyết giữ/bỏ, rồi hội ý. Báo đồng thuận trước và sau soát bằng F1 cặp người (mục 8).
- **Không dùng F1@k:** A3 xuất tập không xếp hạng; dùng P/R/F trên tập. Nếu có điểm tin cậy thì báo thêm R-precision [12].
- **SemF1 [13] chỉ để chẩn đoán:** embedding tiếng Việt chưa được kiểm định cho thuật ngữ chuyên ngành, và khớp mềm khó giải thích trước hội đồng.
- **Độ hạt:** định nghĩa "khái niệm trọng yếu" trong sổ mã kèm ví dụ dương/âm; tách lỗi độ hạt (quá rộng/quá hẹp) khỏi lỗi sai hẳn khi phán pool.

## 4. Hợp nhất thực thể

### 4.1 Bốn họ thước

A4 là gom cụm các chuỗi ứng viên thành node canonical, nên dùng được thước của đồng tham chiếu (coreference) và hợp nhất bản ghi (entity resolution, ER). Bảng sau tóm tắt điều các nguồn gốc nói.

| Thước | Định nghĩa (nguồn) | Ưu | Nhược (nguồn) |
|---|---|---|---|
| Pairwise P/R/F | Tập cặp cùng cụm của hệ so với của vàng; P = \|cặp chung\| / \|cặp hệ\| [22] | Dễ giải thích; thông dụng nhất trong ER [22] | Lạc quan; cụm lớn chiếm số cặp bậc hai nên lỗi ở cụm nhỏ gần như không thấy [22] |
| MUC | Đếm số liên kết tối thiểu phải thêm để lớp tương đương của hệ khớp vàng (recall) và ngược lại (precision) [17] | Không cần tính bao đóng; không bị "hiệu ứng nhận diện mention" [19] | Kém phân biệt nhất; không phân biệt gộp hai singleton với gộp hai thực thể lớn [19] |
| B-cubed (B³) | Tính P/R cho từng phần tử rồi lấy trung bình [19] | Theo Amigó và cộng sự, là thước duy nhất thoả mọi ràng buộc hình thức của họ [20] | Hệ để mọi phần tử đứng riêng được precision 100%; gộp tất cả được recall 100% [19] |
| CEAF | Ghép một–một thực thể hệ với thực thể vàng bằng Kuhn–Munkres, rồi tính F [18] | Đối xứng, dễ giải thích hơn ACE-value [18] | Bị hiệu ứng nhận diện mention [19] |

Ba điểm phương pháp quan trọng từ nguồn gốc:
- **Các thước mâu thuẫn nhau.** Menestrina và cộng sự cho thấy pairwise F1, cluster F1 và các thước khác thường xếp hạng hệ khác nhau; không thước nào tốt hơn mọi thước, nên phải chọn theo ứng dụng [21]. Họ đề xuất GMD (generalized merge distance), khoảng cách sửa dựa trên tách/gộp cụm với chi phí cấu hình được; pairwise F1 tính được từ GMD [21].
- **Không lấy trung bình nhiều thước kém.** CoNLL xếp hạng bằng trung bình MUC, B³, CEAF; Moosavi & Strube lập luận trung bình ba thước không tin cậy không cho một số tin cậy, và làm mất khả năng phân tích P/R. Họ đề xuất LEA [19].
- **Hiệu ứng nhận diện mention (mention identification effect).** Khi tập mention của hệ khác tập vàng, P/R của B³, CEAF, BLANC trở nên phản trực giác (bỏ bớt mention sai lại làm recall đổi) [19].

### 4.2 Khi vàng chỉ là mẫu cặp

Văn liệu ER coi đây là bài toán ước lượng dưới mất cân bằng lớp.
- Nguồn nói [23]: cặp trùng và không trùng mất cân bằng cực mạnh, nên ước lượng nhất quán đòi rất nhiều nhãn. OASIS lấy mẫu theo phân phối lệch có chủ đích (importance sampling) và cập nhật dần; ước lượng P, R, F hội tụ về giá trị thật; giảm tới 83% công gán.
- Suy luận: **precision của phép gộp** ước lượng được bằng mẫu ngẫu nhiên đơn giản từ các cặp máy đã gộp. **Recall** (gộp bị bỏ sót) cần mẫu từ các cặp máy *không* gộp; phần lớn chúng hiển nhiên khác nhau, nên phải **phân tầng theo điểm tương đồng** (tên/alias/vector) và gán trọng số ngược xác suất chọn khi cộng lại.

### 4.3 Suy luận cho A4

Các khuyến nghị sau là của tôi.
- **Chấm A4 có điều kiện trên đầu ra A3.** Dùng chính tập ứng viên của máy làm tập mention; người chỉ phán cách gom. Như vậy tránh hiệu ứng nhận diện mention [19] và tách lỗi A3 khỏi lỗi A4.
- **Báo P và R riêng, không chỉ F.** Với đồ thị tiên quyết, **gộp sai** (hai khái niệm khác nhau thành một node) làm hỏng cạnh của cả hai, đắt hơn **gộp sót** (hai node trùng nhau). Đây đúng là tình huống "chọn thước theo ứng dụng" của [21].
- **Chỉ số chính:** precision gộp theo cặp (trên mẫu cặp máy gộp, CI Wilson) và **B³ precision/recall** trên các cuốn có vàng cụm đầy đủ. Phụ: pairwise F, MUC, số cụm sai hẳn.
- **Thước "gộp sai mà vàng phát hiện" hiện có:** giữ, đổi tên cho chuẩn thành "precision gộp (pairwise)", và nêu cách lấy mẫu. Thêm **recall ước lượng** trên mẫu phân tầng cặp không gộp.
- **Vàng:** bộ vàng A4 hiện do Claude gán nên là **bạc**. Lấy một mẫu cặp (ví dụ 150–200 cặp, phân tầng) cho người phán độc lập; đo đồng thuận người–Claude bằng kappa trên cặp (bài nhị phân, có cả hai lớp). Nếu đồng thuận cao, có thể dùng bạc cho phát triển và vàng người cho số cuối.

## 5. Câu neo và trạng thái dạy

### 5.1 Trích câu định nghĩa

Văn liệu chuẩn gần nhất là DEFT/DeftEval (SemEval-2020 Task 6) và WCL. Các điểm nguồn nói:
- **DEFT lấy dữ liệu từ giáo trình mở** (cnx.org), chọn cửa sổ ba câu quanh từ in đậm [24], [25]. Ba nhiệm vụ con: (1) phân loại câu có định nghĩa hay không, (2) gán nhãn chuỗi BIO cho thuật ngữ/định nghĩa, (3) trích cặp thuật ngữ–định nghĩa [24].
- **Đồng thuận người thấp cho phần định nghĩa.** DEFT đo bằng Krippendorff α biến thể với khoảng cách MASI để tính phần chồng lấn: trên giáo trình, α = 0,80 cho thuật ngữ nhưng chỉ **0,50 cho định nghĩa** [25]. Sau giai đoạn huấn luyện, mỗi câu chỉ một người gán.
- **Thiết kế bài kiểm có thể thổi điểm.** Nhiệm vụ 3 có trung vị F1 0,9043; ban tổ chức thừa nhận là do cửa sổ ba câu quá hẹp, thường chỉ có một cặp thuật ngữ–định nghĩa nên ghép gần như hiển nhiên [24].
- **Precision bằng người phán, recall bằng mẫu.** Trên kho web lớn, Navigli & Velardi phán tay đầu ra của từng hệ để có precision; recall chỉ **ước lượng** bằng cách đọc tay 50.000 câu (tìm được 99 định nghĩa); họ **không tính F1 vì recall là ước lượng** [26].

### 5.2 Phân loại đa lớp có lớp "không chắc"

Lớp `uncertain` về bản chất là **từ chối trả lời** (reject option). Nguồn nói [27]: bộ phân loại chọn lọc được mô tả bằng **độ phủ** (coverage, tỉ lệ mẫu không bị từ chối) và **rủi ro chọn lọc** (selective risk, tỉ lệ sai trên phần không bị từ chối); hai đại lượng đánh đổi nhau, và đường rủi ro–độ phủ (risk–coverage curve) mô tả trọn hiệu năng.

### 5.3 Suy luận cho A5

Các khuyến nghị sau là của tôi.
- **Thước hiện có "câu neo đúng 79/84"** là precision theo phán định (giống cách [26] chấm precision). Giữ, nhưng: (1) người phán phải là người, không phải Claude, cho số cuối; (2) ghi rõ tiêu chí "đúng": câu neo có **chứa thông tin đủ để rút ra mô tả** hay chỉ **nhắc tới** khái niệm.
- **Thêm recall câu định nghĩa** cho khái niệm `defined_here`: người đánh dấu câu định nghĩa trong chương mẫu; máy đúng nếu câu neo trùng câu đó (đơn vị câu, không cần khớp span). Nếu không đánh dấu hết được, ước lượng recall trên mẫu như [26] và **không gộp thành F1**.
- **Trạng thái dạy:** báo ma trận nhầm lẫn 5×5 trên các lớp quyết định, **độ phủ** = 1 − tỉ lệ `uncertain`, và **độ chính xác/macro-F1 trên phần được phủ** [27]. Báo riêng "máy nói `uncertain` khi người chắc chắn" và "máy chắc chắn khi người nói `uncertain`".
- **Gộp lớp khi chấm phụ:** nhiều quyết định hạ nguồn chỉ cần biết khái niệm "được dạy ở đây" (`defined_here` + `introduced_by_example`) hay không. Báo thêm bản hai lớp này để có số ổn định hơn khi mẫu nhỏ.
- **Đồng thuận người:** với 6 lớp danh nghĩa, dùng Krippendorff α (nominal) hoặc Cohen κ cho hai người; báo thêm đồng thuận theo từng lớp vì `defined_here` dễ hơn `introduced_by_example`. Mốc DEFT (α = 0,50 cho định nghĩa [25]) nhắc rằng trần người có thể thấp; báo trần người trước khi đánh giá máy.
- **Tránh thổi điểm kiểu DEFT:** nếu chấm câu neo chỉ trong cửa sổ hẹp quanh vị trí khái niệm, điểm sẽ cao giả. Nên chấm trên cả section.

## 6. Quan hệ tiên quyết

### 6.1 Các bộ dữ liệu và giao thức

Bảng sau so các bộ chuẩn theo cách dựng vàng và cách chấm; mọi ô lấy từ bài gốc.

| Bộ / bài | Nguồn khái niệm | Cặp được gán | Đồng thuận người | Cách chấm |
|---|---|---|---|---|
| CrowdComp, Talukdar & Cohen 2012 [28] | Trang Wikipedia | Chỉ cặp trang **có siêu liên kết**, lấy mẫu tới 400 cặp/miền; 4 lựa chọn gồm "Don't know" | κ trung bình 0,54 (5 miền, AMT) | Phân loại cặp |
| RefD, Liang và cộng sự 2015 [29] | Wikipedia; thêm bộ Course | CrowdComp + cặp môn học | — | Accuracy, P/R/F1; **cân bằng lớp bằng oversampling** cả khi kiểm |
| MOOC, Pan và cộng sự 2017 [30] | Khái niệm khoá Coursera (gán tay) | **Mẫu ngẫu nhiên 25% mọi cặp**; 3 người, 3 nhãn (A→B, B→A, không) | κ trung bình theo cặp người | P/R/F1 |
| Gordon và cộng sự 2016 [31] | Chủ đề từ ACL Anthology | Cặp chủ đề, thang "Somewhat/Very much" | Tương quan Pearson | Precision top-k cạnh |
| LectureBank, Li và cộng sự 2019 [32] | 208 chủ đề NLP | **Mọi cặp**, nhị phân, vàng = **giao** của 2 người | Ghi rằng Fabbri và cộng sự gán ba mức trên cùng cặp chỉ đạt κ ≈ 0,3 | P/R/F1; tập kiểm = 10% cặp dương + **số âm bằng số dương** |
| AL-CPL → ITA-PREREQ → PRELEARN 2020 [33] | Thuật ngữ giáo trình có trang Wikipedia | Mở rộng bằng **âm đảo chiều** (B,A) và **dương bắc cầu** (A,C) | — | Accuracy/F1; **tập kiểm cân bằng 50/50**, dù toàn bộ dữ liệu chỉ ~23% dương |
| PREAP, Alzetta, Torre & Koceva 2024 [34] | Thuật ngữ trong giáo trình (bước riêng) | **Chỉ ghi cặp dương bám văn bản**; cặp không ghi coi là không quan hệ; cặp bắc cầu ngầm | Cohen κ trung bình 0,60 → 0,62 sau rà; Fleiss κ 0,43 → 0,45 | So với 4 phương pháp gán khác; giáo viên chấm **đường 3 nút** |

Ba điểm từ PREAP đáng lưu ý vì giao thức của dự án đi theo kiểu này [34]:
- **Đồng thuận có tính bắc cầu.** Hai người được coi là đồng ý về A→C nếu cả hai cùng ghi A→C, **hoặc** một người ghi A→C còn người kia ghi A→B và B→C. κ tính trên **mọi cặp** của tập thuật ngữ, cặp không ghi là "không quan hệ". PREAP cũng nhận xét κ có điểm yếu khi phân phối lệch.
- **Gán khái niệm tách khỏi gán quan hệ.** Khi người gán được thêm khái niệm trong lúc gán quan hệ (biến thể v3), κ tụt còn 0,25 so với 0,62 (v2); tác giả khuyên tách hai bước.
- **Gộp vàng.** PREAP lấy **hợp** (union) bốn bản đã rà làm vàng vì mục tiêu là phân tích ngôn ngữ; họ nêu giao (intersection) là đầu kia của phổ và khuyên hội ý khi có thể.

### 6.2 Đồng thuận khi chỉ ghi cặp dương

Nguồn nói [35]:
- Trong bài toán không xác định được số ca âm, **κ không tính được**.
- **F1 giữa hai người bằng đúng "đồng thuận dương đặc hiệu"** (positive specific agreement), `PSA = 2a / (2a + b + c)`, với a là số cặp cả hai cùng ghi, b và c là số cặp chỉ một người ghi. Đổi vai người làm "vàng" không đổi kết quả.
- Khi số ca âm rất lớn, **κ tiến tới PSA**. Tác giả khuyên dùng PSA/F1; tốt hơn nữa là làm riêng một nghiên cứu đo lường có tập ca xác định.

**Suy luận:** κ của PREAP tính trên mọi cặp thuật ngữ, nơi số cặp âm áp đảo, nên về số học gần với PSA [35]. Áp vào số liệu dự án (giả định "20/87" nghĩa là 20 cạnh chung trên 87 cạnh hợp):

| Cuốn | Chung (a) / hợp (a + b + c) | 2a + b + c | PSA = F1 giữa hai người |
|---|---|---|---|
| Cuốn phát triển | 20 / 87 | 2·20 + 67 = 107 | 40/107 ≈ 0,37 |
| Giữ lại 1 | 30 / 112 | 2·30 + 82 = 142 | 60/142 ≈ 0,42 |
| Giữ lại 2 | 18 / 84 | 2·18 + 66 = 102 | 36/102 ≈ 0,35 |

Các số này thấp hơn PREAP (≈ 0,60) nhưng cùng vùng với các bộ gán mọi cặp mà PREAP dẫn (≈ 0,30) [34]. Chưa tính tín dụng bắc cầu; tính lại theo luật của PREAP có thể tăng PSA và nên báo cả hai.

### 6.3 Cạm bẫy khi chấm

Các cạm bẫy sau có bằng chứng trực tiếp trong nguồn.
- **Tập kiểm cân bằng thổi precision.** PRELEARN cân bằng 50/50 chỉ ở tập kiểm dù dữ liệu tự nhiên ~23% dương [33]; LectureBank thêm số âm bằng số dương [32]; RefD cân bằng bằng oversampling [29]. Precision và accuracy trên tập như vậy không phản ánh tỉ lệ thật, nơi đa số cặp khái niệm trong một cuốn sách không có quan hệ. (Suy luận: với tỉ lệ dương thật vài phần trăm, cùng một bộ phân loại sẽ có precision thấp hơn nhiều.)
- **Lọc ứng viên làm thu hẹp bài toán.** CrowdComp chỉ xét cặp có siêu liên kết [28]; điều này làm bài dễ hơn bài "mọi cặp".
- **Rò rỉ qua bắc cầu.** AL-CPL/ITA-PREREQ sinh thêm cặp dương bằng bắc cầu và âm bằng đảo chiều [33]; Liang và cộng sự cũng dùng bao đóng để suy nhãn trong học chủ động [36]. Suy luận: nếu chia train/test ngẫu nhiên theo cặp, cặp (A,C) ở tập kiểm có thể suy ra từ (A,B), (B,C) ở tập huấn luyện. Phải chia theo cuốn/chương.
- **Vàng không đầy đủ phạt oan cạnh đúng.** TExEval-2 nói rõ hệ có thể tìm ra quan hệ đúng mà vàng không có; họ **chấm tay tối đa 100 quan hệ mới chọn ngẫu nhiên** cho mỗi hệ để ước lượng precision phần ngoài vàng [37]. Le & Abel cũng ghi nhận dự đoán hợp lý ngoài tập chuyên gia bị tính là sai [39].
- **Chấm trên bao đóng phạt lặp.** Trong phân loại phân cấp, thêm toàn bộ tổ tiên vào tập nhãn "phạt quá tay lỗi ở nút có nhiều tổ tiên" [38]. Suy luận: P/R trên bao đóng bắc cầu cũng vậy — một cạnh sai gần gốc sinh ra nhiều cạnh bao đóng sai; một cạnh thiếu ở giữa chuỗi làm mất nhiều cạnh bao đóng.

### 6.4 Suy luận cho A8

Các khuyến nghị sau là của tôi.
- **Thay mọi chỗ báo κ cho A8 bằng PSA/F1 giữa người** [35], kèm bản có tín dụng bắc cầu theo [34]. Ghi rõ tử/mẫu.
- **Trần người cùng thước:** so máy với *từng* người bằng F1, đặt cạnh F1 người–người. So máy với vàng hội ý thì không cùng thước với F1 người–người, vì vàng hội ý được dựng từ chính hai người.
- **Giữ P/R/F1 cạnh trực tiếp làm chỉ số chính**, chỉ trong phạm vi chương có vàng và chỉ trên cặp có cả hai đầu thuộc tập khái niệm đã đối chiếu. Gọi đúng tên: "P/R có điều kiện trên tập khái niệm của pipeline".
- **Giữ P/R bao đóng làm phụ**, báo kèm bao đóng của vàng và của máy tính cùng cách; nêu cạm bẫy [38].
- **Giữ chấm mù cạnh dư** như TExEval-2 [37]: mẫu ngẫu nhiên cạnh máy không có trong vàng, người phán mù "cần/hợp lý/sai". Báo "precision hiệu chỉnh" = (cạnh khớp vàng + ước lượng cạnh dư đúng) / tổng cạnh máy, có CI.
- **Pass phụ LightGBM:** không báo accuracy hay F1 trên tập cân bằng. Báo PR-AUC và P/R tại ngưỡng vận hành trên **phân phối ứng viên thật** của các cuốn giữ lại; chia theo cuốn để tránh rò rỉ bắc cầu.
- **Nhiễu đầu vào (E4 ±0,15)** lớn hơn nhiều khác biệt thường thấy giữa hai biến thể; mọi so sánh A8 phải dùng kiểm định ghép cặp theo cuốn và trung bình trên nhiều lần xáo (mục 9, 10).

## 7. Lộ trình và thứ tự học

### 7.1 Thước tự động

Có ba họ thước tự động cho một dãy học.
- **Tương quan thứ hạng với một thứ tự tham chiếu.** Kendall τ là thước chuẩn cho bài sắp xếp thông tin; τ tương quan với điểm người và thời gian đọc [8]. Giới hạn: cần một thứ tự tham chiếu đáng tin, hai dãy phải cùng tập phần tử, và cần hiệu chỉnh khi có đồng hạng (ví dụ nhiều khái niệm cùng module) [8].
- **Vi phạm ràng buộc.** Khi tham chiếu là một đồ thị tiên quyết (thứ tự bộ phận) chứ không phải một dãy, thước tự nhiên là tỉ lệ cạnh vàng bị vi phạm. Tôi không tìm được nguồn gốc nào chuẩn hoá thước này cho lộ trình học; Q6 là định nghĩa riêng của dự án và nên trình bày bằng công thức.
- **Thước cấu trúc đồ thị.** TExEval kiểm đồ thị có phải DAG không, đếm chu trình, thành phần liên thông và nút trung gian, và đưa tính không chu trình vào xếp hạng [37].

### 7.2 Đánh giá người

Nguồn nói (van der Lee và cộng sự [40]):
- Khảo sát INLG/ACL: trung vị **4 người chấm** và **100 mục**; chỉ 55% bài nêu số người chấm; chỉ 33% bài có kiểm định thống kê.
- Khuyến nghị: ít nhất 2 người (càng nhiều càng tốt); báo **đồng thuận kèm CI và kèm phần trăm đồng ý**; dùng **thang Likert 7 mức nhiều mục** hoặc **xếp hạng liên tục**; chạy thử (pilot) trước; **xáo thứ tự trình bày** để tránh hiệu ứng thứ tự; tách nghiên cứu **thăm dò** (chỉ phân tích mô tả) khỏi nghiên cứu **khẳng định** (cân nhắc đăng ký trước, kiểm định phù hợp).
- RankME [41]: đánh giá tương đối kết hợp thang liên tục cho xếp hạng **tin cậy và nhất quán hơn** thang Likert truyền thống; kết hợp ước lượng Bayes (TrueSkill) để xếp nhiều hệ.
- Howcroft và cộng sự [42]: sau 20 năm, đánh giá người trong NLG thiếu định nghĩa chuẩn cho tiêu chí và thiếu chi tiết báo cáo (số người chấm, số đầu ra, số phiếu); họ đề xuất **phiếu mô tả đánh giá** và tên tiêu chí chuẩn hoá.
- PREAP cho giáo viên chấm **đường ba nút** chọn ngẫu nhiên, vì quan hệ tiên quyết có tính bắc cầu [34]. Đây là tiền lệ trực tiếp cho chấm người trên lộ trình.

### 7.3 Suy luận cho A9/A10

Các khuyến nghị sau là của tôi.
- **Q6 (vi phạm thứ tự):** giữ làm chỉ số chính cho lộ trình. Báo riêng ba thành phần (ngược, cùng bậc, ngoài lộ trình) với **cùng mẫu số** là tổng cạnh vàng trong phạm vi; kèm CI bootstrap theo cuốn (mục 9).
- **Q7/Q7b:** đây là recall và precision của **tập tổ tiên** cho mỗi đích, tức P/R bao đóng giới hạn quanh đích. Giữ; nhắc cạm bẫy phạt lặp [38]; lấy trung bình theo đích rồi theo cuốn.
- **Kendall τ so với mục lục:** giữ ở vai trò chẩn đoán như hiện nay. Mục lục không phải vàng của "thứ tự học tốt nhất"; τ cao chỉ nói lộ trình bám sách.
- **Thêm kiểm tra cấu trúc:** số chu trình (phải bằng 0 sau A9), số thành phần liên thông, độ sâu dài nhất [37].
- **Chấm người theo cặp mù A/B:** đưa giáo viên hai lộ trình cho cùng mục tiêu (máy vs mục lục, hoặc hai biến thể), xáo trái/phải, hỏi "lộ trình nào giúp người mới học tốt hơn" kèm lý do. Kiểm định bằng sign test hai phía trên số phiếu thắng (loại hoà). Nếu hỏi thang điểm, dùng Likert 7 mức có neo lời và báo Krippendorff α thứ bậc (ordinal) [43].
- **Chấm đường ngắn:** mẫu ngẫu nhiên đường ba nút trong đồ thị máy, giáo viên phán "đúng cả hai cạnh / đúng một / sai" như PREAP [34]. Rẻ hơn chấm cả lộ trình và gần với cách người học dùng.
- **Thăm dò hay khẳng định:** với 2–8 cuốn và vài giáo viên, nên trình bày chấm người là **nghiên cứu thăm dò** [40], trừ khi đăng ký trước giả thuyết và cỡ mẫu.

## 8. Đồng thuận người gán

### 8.1 Các hệ số

Bảng sau tóm tắt các hệ số và lúc dùng, theo nguồn gốc.

| Hệ số | Dùng khi | Ghi chú từ nguồn |
|---|---|---|
| Phần trăm đồng ý | Luôn báo kèm | Dễ hiểu; thiên về chiều có ít lớp [43]; van der Lee khuyên báo kèm hệ số hiệu chỉnh [40] |
| Cohen κ | Hai người, nhãn danh nghĩa, có đủ ca âm | Kỳ vọng ngẫu nhiên tính theo phân phối riêng của từng người [43] |
| Scott π / Fleiss κ (multi-π) | Nhiều người | Kỳ vọng tính trên phân phối gộp; Artstein & Poesio cho rằng khác biệt với κ nhỏ dần khi tăng số người [43] |
| Krippendorff α | Mọi số người, thiếu dữ liệu, mọi mức đo (danh nghĩa, thứ bậc, khoảng) qua hàm khoảng cách | Phân phối của α không biết trước nên CI lấy bằng bootstrap [43]; Hayes & Krippendorff đề nghị α làm chuẩn [44] |
| κ có trọng số (Cohen 1968) | Nhãn thứ bậc | Cách dùng trọng số giống α [43] |
| Gwet AC1 | Phân phối lệch mạnh | Ít bị ảnh hưởng bởi tỉ lệ hiện mắc (prevalence) hơn κ; giữ gần phần trăm đồng ý [45]; công thức gốc ở [46] |
| PSA / F1 giữa hai người | Không xác định được số ca âm (chỉ ghi ca dương) | Bằng F1; κ tiến tới PSA khi ca âm rất nhiều [35] |

### 8.2 Nghịch lý κ khi lớp lệch

Nguồn nói [43]: khi dữ liệu dồn vào một lớp, đồng ý kỳ vọng rất cao, nên κ có thể thấp dù phần trăm đồng ý cao (nghịch lý mà Feinstein & Cicchetti nêu, theo [43]). Artstein & Poesio lập luận đây **là hành vi đúng**: độ tin cậy là khả năng phân biệt lớp, và phép thử thực sự là có đồng ý được trên **lớp hiếm** hay không. Wongpakaran và cộng sự (có Gwet đồng tác giả) đo trên cùng dữ liệu chẩn đoán: κ dao động 0–1,00 còn AC1 0,752–1,000; AC1 ít đổi theo tỉ lệ hiện mắc [45].

**Suy luận:** hai quan điểm này không mâu thuẫn hoàn toàn. Khi lớp lệch, báo **cả κ (hoặc α) lẫn AC1 lẫn phần trăm đồng ý**, kèm phân phối biên của từng người; người đọc tự thấy vì sao các số khác nhau. Không chọn hệ số sau khi xem số.

### 8.3 Ngưỡng diễn giải và tranh cãi

Nguồn nói [43]:
- Thang Landis & Koch (1977) phổ biến trong y khoa, coi trên 0,4 là chấp nhận được.
- Ngôn ngữ học tính toán thường theo Krippendorff qua Carletta: "K > 0,8 là tin cậy tốt, 0,67 < K < 0,8 cho phép kết luận tạm".
- Artstein & Poesio nhận xét chọn ngưỡng "vẫn chỉ là nghệ thuật đen", và mức đồng thuận phù hợp cho xây tài nguyên có thể khác cho nghiên cứu ngôn ngữ. Họ cũng nêu: kiểm định "κ khác 0" là vô nghĩa; thứ cần báo là **khoảng tin cậy**.
- Khuyến nghị của Krippendorff (theo [43]): ít nhất ba người gán, chọn theo tiêu chí rõ, làm độc lập theo sổ mã viết sẵn; mẫu đủ để mỗi lớp có ít nhất năm lần đồng ý ngẫu nhiên. Artstein & Poesio khuyên **tăng số người gán** để giảm thiên lệch cá nhân.

### 8.4 Suy luận cho dự án

Bảng sau chọn hệ số cho từng khâu.

| Khâu | Hệ số chính | Phụ |
|---|---|---|
| A1 tiêu đề, A2 vai trò | Cohen κ (2 người) hoặc α (≥ 3) | % đồng ý; κ theo lớp |
| A3 danh sách khái niệm | PSA/F1 giữa người, trước và sau bước soát | Jaccard |
| A4 cặp gộp | κ trên cặp ứng viên (có cả hai lớp) | AC1 nếu lệch |
| A5 trạng thái dạy | α danh nghĩa | Ma trận nhầm lẫn giữa người |
| A8 cạnh tiên quyết | PSA/F1 giữa người, có và không có tín dụng bắc cầu | κ trên mọi cặp kiểu PREAP, ghi rõ nó xấp xỉ PSA |
| Chấm lộ trình (Likert) | α thứ bậc, CI bootstrap | % đồng ý chính xác và ±1 mức |

Ghi chú bắt buộc khi báo: số người, ai là người gán (người hay agentic), số mục, CI. **Đồng thuận agentic–agentic không phải đồng thuận người**; kappa A–B 0,47–0,56 của D-01 là đồng thuận giữa hai lượt Codex, phải gọi đúng tên.

## 9. Thống kê khi ít tài liệu

### 9.1 Nguồn nói gì

Các điểm sau lấy từ bài gốc.
- **Khoảng tin cậy cho một tỉ lệ.** Brown, Cai & DasGupta: độ phủ của khoảng Wald thất thường, các khuyến cáo sách giáo khoa về độ an toàn của nó không đáng tin; với n nhỏ nên dùng **Wilson** hoặc Jeffreys, với n lớn dùng Agresti–Coull [54] (chỉ đọc tóm tắt).
- **Bootstrap ghép cặp.** Koehn dùng bootstrap trên câu để tính ý nghĩa thống kê cho BLEU; ông ghi nhận độ khó dịch **tụ theo cụm** (cùng chủ đề, cùng văn phong trong các câu liền nhau), nên tập kiểm lấy rải từ nhiều phần của kho cho phương sai nhỏ hơn tập liền khối [47].
- **Ý nghĩa thống kê không chuyển sang miền khác.** Berg-Kirkpatrick và cộng sự: p-value bootstrap hiệu chỉnh tốt khi dữ liệu mới rút i.i.d. cùng phân phối với tập kiểm, nhưng **khả năng dự báo giảm mạnh khi miền dữ liệu mới khác tập kiểm** [48].
- **Chọn kiểm định.** Dror và cộng sự đưa cây quyết định: biết phân phối thống kê → kiểm định tham số; không biết và dữ liệu nhỏ → bootstrap hoặc randomization; dữ liệu lớn → kiểm định phi tham số không lấy mẫu (sign, Wilcoxon). Họ lưu ý bootstrap **kém hiệu quả khi tập kiểm nhỏ** vì giả định tập kiểm gần phân phối tổng thể; và nêu **quan sát phụ thuộc** (câu cùng bài, cùng tác giả) là vấn đề mở mà các kiểm định thông dụng không xử lý [49].
- **Đừng giả định hai hệ độc lập.** Yeh: nhiều kiểm định đánh giá thấp ý nghĩa vì coi kết quả hai hệ là độc lập, trong khi chúng tương quan dương; với P và F (dạng phức tạp) nên dùng **kiểm định randomization** [52].
- **Nhiều tập dữ liệu.** Dror và cộng sự (2017): cách phổ biến "đếm số tập mà A thắng B có ý nghĩa" **không chặn được xác suất có ít nhất một kết luận sai**. Họ đề xuất phân tích tái lập (replicability analysis) dựa trên kiểm định giao một phần (partial conjunction): Bonferroni khi các tập phụ thuộc, Fisher (mạnh hơn) khi độc lập; `p_Bonferroni(u/N) = (N − u + 1) · p_(u)` [50].
- **Công suất thống kê.** Card và cộng sự: thí nghiệm thiếu công suất phổ biến trong NLP, khiến khó phân biệt nhiễu với cải thiện thật và **làm tăng khả năng phóng đại kết quả**; khuyên làm **phân tích công suất bằng mô phỏng trước khi đánh giá**, và với đánh giá người phải lập kế hoạch phân tích và cỡ mẫu trước [51].
- **p-value dễ vỡ.** Søgaard và cộng sự: kết quả ý nghĩa thống kê theo chuẩn hiện hành không đáng tin, rất nhạy với cỡ mẫu, biến phụ (độ dài câu) và việc có nhiều thước; dưới giả định lý tưởng cần ngưỡng 0,0025 để giữ dương tính giả dưới 5% [53].
- **Dữ liệu lồng nhau.** Saravanan và cộng sự: kiểm định coi các đo đạc lồng nhau là độc lập có thể cho **tỉ lệ dương tính giả trên 45%** dù đặt mức 5%; bootstrap phân cấp (lấy mẫu lần lượt qua các tầng) giữ được sai lầm loại I [55].

### 9.2 Áp vào cấu trúc dữ liệu của dự án

Dữ liệu dự án lồng ba tầng: cuốn → chương → cạnh/khái niệm. Suy luận của tôi:
- **Cạnh không độc lập.** Các cạnh cùng cuốn chia chung văn phong, chung người gán, chung một lần chạy pipeline; đúng loại phụ thuộc mà [47], [49], [55] cảnh báo. **Wilson hoặc bootstrap theo cạnh trên số gộp nhiều cuốn sẽ cho CI quá hẹp.**
- **Bootstrap theo cuốn với 2–8 cuốn gần như vô dụng.** Với 2 cuốn chỉ có 3 tập lấy lại khác nhau ({A,A}, {A,B}, {B,B}); với 6–8 cuốn phân phối bootstrap vẫn rất thô. Đây là giới hạn của dữ liệu, không phải của phương pháp.
- **Sign test theo cuốn có sàn p.** Nếu cả n cuốn đều nghiêng về hệ A, p hai phía = 2 · 0,5ⁿ: n = 4 → 0,125; n = 5 → 0,0625; n = 6 → 0,031; n = 8 → 0,0078. **Với ≤ 5 cuốn không thể có kết luận "có ý nghĩa ở mức 0,05" xuyên cuốn**, dù hiệu ứng lớn đến đâu.
- **Nhiễu đầu vào là sàn của mọi so sánh.** E4 dao động tới ±0,15; hiệu ứng nhỏ hơn mức này không phân biệt được với nhiễu.

### 9.3 Khuyến nghị cụ thể cho n tài liệu 2–8

Bảng sau là khuyến nghị của tôi, theo loại câu hỏi.

| Câu hỏi | Cách báo | Diễn giải đúng |
|---|---|---|
| Hệ đạt bao nhiêu trên **chính các cuốn này**? | Số theo từng cuốn + gộp; CI bootstrap **hai tầng** (cuốn, rồi chương/cạnh trong cuốn) hoặc bootstrap theo cạnh **trong từng cuốn** | Suy luận có điều kiện trên tập cuốn; không khái quát sang môn khác [48] |
| Một tỉ lệ trên mẫu ngẫu nhiên đơn trong một cuốn (ví dụ precision cạnh dư được chấm mù) | Wilson 95% [54] | Hợp lệ vì mẫu được rút ngẫu nhiên, độc lập |
| Hệ A có hơn hệ B **trên các cuốn này**? | Paired bootstrap hoặc approximate randomization **theo cạnh, phân tầng theo cuốn** (chỉ hoán vị/lấy lại trong cùng cuốn) [47], [49], [52] | "A hơn B trên các cuốn đã thử" |
| A có hơn B **nói chung**? | Bảng thắng/thua theo cuốn; sign test hoặc partial conjunction (Bonferroni) [50]; nói rõ sàn p | Với ≤ 5 cuốn: chỉ mô tả, không tuyên bố ý nghĩa thống kê |
| Có đáng chạy thí nghiệm không? | Mô phỏng công suất trước: với số cạnh, số cuốn và nhiễu E4 hiện có, hiệu ứng nhỏ nhất phát hiện được là bao nhiêu [51] | Nếu MDE lớn hơn hiệu ứng mong đợi thì đổi thiết kế (thêm chương có vàng) chứ không chạy |
| Nhiều thước, nhiều biến thể | Holm hoặc Bonferroni trên họ so sánh khai trước; ưu tiên **một thước chính** cho mỗi khâu | Giảm rủi ro "chọn thước sau khi xem số" [53] |

Thêm ba quy tắc trình bày:
- Báo **cỡ hiệu ứng + CI** trước, p-value sau; dùng chữ "có ý nghĩa" chỉ theo nghĩa thống kê [49].
- Dữ liệu hai cuốn giữ lại chỉ dùng **một lần** cho số cuối; mọi lựa chọn thước, ngưỡng, biến thể phải chốt trên cuốn phát triển.
- Khi cần CI cho số gộp nhiều cuốn, ưu tiên bootstrap hai tầng [55] và ghi kèm số cuốn; nếu chỉ có 2 cuốn thì báo hai số riêng và khoảng của mỗi cuốn, không gộp.

## 10. LLM không tất định và nhãn bạc

### 10.1 Biến thiên của LLM

Các điểm nguồn nói:
- **"Tất định" không thật sự tất định.** Atil và cộng sự chạy năm LLM cấu hình tất định trên tám tác vụ, mỗi tác vụ 10 lần: không mô hình nào cho accuracy lặp lại ổn định trên mọi tác vụ, càng không cho chuỗi đầu ra giống hệt; accuracy dao động tới 15% giữa các lần chạy. Họ đề xuất đo bằng tỉ lệ đồng ý toàn phần trên đầu ra thô (TARr@N) và trên đáp án đã tách (TARa@N) [59].
- **Nhạy với định dạng giữ nghĩa.** Sclar và cộng sự: đổi định dạng prompt mà không đổi nghĩa có thể làm lệch tới 76 điểm accuracy (LLaMA-2-13B); độ nhạy không mất đi khi tăng cỡ mô hình, số ví dụ hay sau instruction tuning. Họ khuyên **báo khoảng hiệu năng trên nhiều định dạng hợp lý** thay vì một định dạng; định dạng tốt cho mô hình này chỉ tương quan yếu với mô hình khác [60].

**Suy luận cho dự án.** Pass chính A8 cho cùng kết quả khi chạy lặp với cùng đầu vào; nhưng đổi thứ tự ngữ cảnh (giữ nghĩa) làm số dao động tới ±0,15 (E4). Đây đúng là loại nhạy cảm [60] mô tả, và lớp LLM ở A2 nhạy theo cách gom lô cũng vậy. Hệ quả:
- Một lần chạy chỉ là **một mẫu** từ phân phối đầu ra. Báo **trung bình và khoảng** trên K lần nhiễu loạn giữ nghĩa (xáo thứ tự section, đổi cách gom lô), K khai trước (ví dụ 5).
- Đo **độ ổn định** riêng khỏi độ đúng: tỉ lệ cạnh (hoặc nhãn section) giữ nguyên qua K lần, theo tinh thần TARa@N [59]; và tỉ lệ cạnh xuất hiện ở ít nhất k/K lần.
- So hai biến thể A và B phải trên **cùng tập nhiễu loạn** (ghép cặp), rồi mới kiểm định (mục 9).
- Vì nhà cung cấp có thể đổi hạ tầng, ghi phiên bản mô hình, ngày chạy, transport (Vertex/Developer API) cùng mọi số [59].

### 10.2 LLM làm người gán và giám khảo

Các điểm nguồn nói:
- **Giám khảo LLM có thiên lệch.** Zheng và cộng sự nêu thiên lệch vị trí (position), độ dài (verbosity), tự ưu ái (self-enhancement) và giới hạn suy luận; GPT-4 đồng ý với người trên 80%, ngang mức người–người, trong bối cảnh chấm trợ lý chat [56].
- **Độ tin cậy đổi theo tác vụ.** Bavaresco và cộng sự (20 bộ, 11 LLM): biến thiên lớn theo mô hình và bộ dữ liệu, phụ thuộc thuộc tính được chấm, chuyên môn người chấm và nguồn văn bản; kết luận **phải kiểm định LLM với người cho từng tác vụ trước khi dùng** [58].
- **Thủ tục thống kê để thay người.** Calderon, Reichart & Dror đề xuất alt-test: bỏ lần lượt từng người, so xem LLM hay người bị bỏ ra khớp nhóm còn lại tốt hơn; tính tỉ lệ thắng với kiểm soát FDR. Họ khuyên **ít nhất ba người gán** (hai người thì không có tín hiệu đồng thuận), tối thiểu 30 mục cho giả định chuẩn, thường đủ trong khoảng 50–150 mục tuỳ tham số chi phí ε [57].
- **Lỗi nhãn ở tập kiểm làm đảo thứ hạng.** Northcutt và cộng sự ước lượng ít nhất 3,3% lỗi nhãn trên 10 bộ kiểm phổ biến; khi tỉ lệ nhãn sai tăng vài điểm phần trăm, mô hình nhỏ có thể vượt mô hình lớn [61].

### 10.3 Suy luận: báo nhãn bạc thế nào

Các khuyến nghị sau là của tôi.
- **Ba tầng nhãn, ba tên gọi.** (1) *Vàng người*: người gán độc lập, có đo đồng thuận. (2) *Bạc agentic + duyệt*: LLM/agent gán, có người hoặc agent duyệt. (3) *Bạc agentic*: không duyệt. Mỗi bảng số ghi rõ tầng. Đồng thuận giữa hai lượt Codex (κ 0,47–0,56) là **độ ổn định của người gán máy**, không phải độ tin cậy người.
- **Dùng bạc cho phát triển, vàng cho số cuối.** Bạc dùng để huấn luyện pass phụ, chọn ngưỡng, so biến thể sơ bộ. Số đưa hội đồng phải đo trên vàng người.
- **Hiệu chuẩn bạc bằng một mẫu vàng.** Trên một mẫu chung, báo đồng thuận người–người và người–bạc cạnh nhau. Nếu đủ ba người, chạy alt-test [57]; nếu chỉ hai người, báo "bạc đồng ý với mỗi người ở mức X, hai người đồng ý với nhau ở mức Y" và nói rõ đây chưa phải phép thử thay thế.
- **Claude làm giám khảo (câu neo 79/84, chấm cạnh dư):** đây là LLM-as-judge. Áp biện pháp của [56]: chấm mù nguồn, xáo thứ tự, không cho thấy độ dài/điểm của hệ; với số cuối, lấy mẫu cho người chấm lại và báo đồng thuận người–Claude.
- **Lỗi nhãn ở vàng nhỏ:** với vàng chỉ vài chục đến vài trăm cạnh, vài lỗi nhãn đủ đảo thứ tự hai biến thể gần nhau [61]. Đừng tuyên bố thắng khi chênh lệch nhỏ hơn số lỗi nhãn ước lượng được từ bất đồng giữa người.

## 11. Quy lỗi theo khâu, ablation oracle

### 11.1 Nguồn nói gì

Các điểm sau lấy từ bài gốc.
- **Lỗi dồn qua pipeline.** Finkel, Manning & Ng: kiến trúc pipeline chọn 1-best tham lam làm lỗi lan và cộng dồn qua từng tầng, hạ hiệu năng đầu-cuối của các bài phức hợp [62].
- **Thay một khâu bằng thông tin hoàn hảo đổi hẳn bài toán.** Stoyanov và cộng sự đo tác động của từng bài con (nhận diện thực thể, xác định anaphora, nhận diện phần tử đồng tham chiếu) bằng cách cho hệ dùng **nhãn vàng** của bài con đó; dùng phần tử vàng "giải quyết một phần lớn bài toán". Họ chỉ ra con số 91,5 F (dùng thông tin hoàn hảo cho nhiều bài con) và 71,3 F (đầu-cuối) **không so được với nhau** vì giả định đánh giá khác nhau [63].
- **Trộn thiết lập đánh giá dẫn tới so sánh sai.** Taillé và cộng sự: nhiều bài trích quan hệ đầu-cuối so sánh với công trình trước dưới thiết lập khác nhau (Strict / Boundaries / Relaxed); lỗi phổ biến nhất làm **thổi kết quả khoảng 5%** trên ACE05; họ kêu gọi báo rõ thiết lập và thống kê dữ liệu [64].
- **Phân loại lỗi tự động.** Kummerfeld & Klein: thước đo chỉ định lượng lỗi chứ không phân tích; họ xây công cụ xếp lỗi đồng tham chiếu vào các loại trực quan rồi so phân bố lỗi giữa nhiều hệ [65].

### 11.2 Suy luận: thiết kế ablation oracle cho Pha A

Ablation oracle là thay đầu ra của một khâu bằng vàng rồi chạy tiếp các khâu sau, đo thay đổi ở thước hạ nguồn (thường là F1 cạnh A8 và Q6/Q7). Bảng sau đề xuất các mức; mỗi mức trả lời một câu hỏi.

| Mức | Thay bằng vàng | Câu hỏi trả lời | Vàng cần có |
|---|---|---|---|
| E0 | Không thay (đầu-cuối) | Hệ thật đạt bao nhiêu | Vàng cạnh A8 |
| O1 | Cây mục (A1) | Lỗi đọc PDF làm mất bao nhiêu cạnh | Vàng D-02 |
| O2 | Vai trò section (A2) | Ví dụ sự cố mất 29/62 cạnh: lặp lại có hệ thống | Vàng vai trò (chưa có) |
| O3 | Tập khái niệm (A3+A4) | Trần của A8 khi khái niệm hoàn hảo; tách "A8 suy luận kém" khỏi "thiếu nút" | Danh sách khái niệm vàng của chương |
| O4 | Bản đồ mention (A6/A7) | Ngữ cảnh đưa vào A8 có đủ không | Khó dựng; có thể bỏ |

Cách chạy và báo:
- **Một oracle mỗi lần và oracle cộng dồn** (O1, O1+O2, O1+O2+O3). Hiệu ứng không cộng tuyến tính; thứ tự cộng dồn ảnh hưởng tới phần quy cho từng khâu, nên khai thứ tự trước.
- **Không đặt số oracle cạnh số đầu-cuối như thể cùng loại** [63]. Bảng kết quả ghi rõ cột "thiết lập" như [64] khuyên.
- **Coi chừng lệch phân phối:** tên khái niệm vàng có thể khác văn phong tên máy sinh; A8 có thể phản ứng khác. Ghi nhận như một hạn chế.

### 11.3 Suy luận: quy lỗi theo khâu đầu tiên hỏng

Song song với oracle, có thể quy từng cạnh vàng bị bỏ sót về **khâu đầu tiên làm hỏng nó**, theo tinh thần phân loại lỗi của [65]. Cách làm:
1. Lấy mỗi cạnh vàng (A→B) mà máy không có.
2. Đi xuôi pipeline, dừng ở khâu đầu tiên mà điều kiện cần bị vi phạm: (a) đoạn chứa A hoặc B bị A1/A2 loại khỏi nội dung; (b) A3 không trích A hoặc B; (c) A4 gộp sai hoặc tách đôi; (d) A6/A7 không đưa ngữ cảnh liên quan; (e) A8 không suy ra cạnh; (f) A9/A10 bỏ hoặc làm mềm cạnh.
3. Báo bảng thác nước: bao nhiêu phần trăm cạnh vàng mất ở mỗi khâu.

Tương tự, mỗi cạnh máy không có trong vàng được xếp loại: đúng nhưng vàng thiếu (từ chấm mù), sai hướng, bắc cầu của cạnh vàng, sai hẳn. Hai bảng này cho hội đồng thấy **nên đầu tư vào khâu nào**, điều mà một F1 đầu-cuối không nói được.

## 12. Chi phí, thời gian, tái lập, tài liệu hoá dữ liệu

### 12.1 Nguồn nói gì

Các điểm sau lấy từ bài gốc.
- **Show your work.** Dodge và cộng sự: điểm trên tập kiểm một mình không đủ để kết luận mô hình nào tốt hơn; nên báo **hiệu năng kỳ vọng theo ngân sách tính toán** (số lần thử siêu tham số hoặc thời gian); họ tìm thấy các so sánh đã công bố sẽ đổi kết luận nếu ngân sách khác đi. Danh mục báo cáo của họ gồm: hạ tầng tính toán, **thời gian chạy trung bình** mỗi phương pháp, chi tiết chia train/val/test, hiệu năng validation tương ứng mỗi số test, liên kết mã [66].
- **Green AI.** Schwartz và cộng sự đề nghị đưa **hiệu quả thành tiêu chí đánh giá ngang với độ chính xác**, và báo **"giá tiền"** (chi phí tài chính) của việc phát triển, huấn luyện và chạy mô hình [67].
- **Danh mục ACL Responsible NLP.** Mục C: số tham số, ngân sách tính toán, hạ tầng ("ước lượng còn hơn không"); siêu tham số và tập dùng để tinh chỉnh (không tinh chỉnh trên tập kiểm); **thanh sai số và nói rõ là một lần chạy, max hay trung bình**; phiên bản thư viện. Mục D: toàn văn hướng dẫn cho người gán, cách tuyển, tiền công, đồng thuận, nhân khẩu học người gán. Mục E: có dùng trợ lý AI hay không [68].
- **Datasheets for Datasets.** Bảy nhóm câu hỏi: động cơ, thành phần, quy trình thu thập, tiền xử lý/làm sạch/gán nhãn, mục đích dùng, phân phối, bảo trì [69].
- **Data Statements.** Bender & Friedman: lý do tuyển chọn, biến thể ngôn ngữ, nhân khẩu người nói, **nhân khẩu người gán**, tình huống ngôn ngữ, đặc điểm văn bản, chất lượng ghi âm, phụ lục nguồn gốc [70].
- **Đăng ký trước.** van Miltenburg và cộng sự: đăng ký trước là nêu điều sẽ làm và điều dự kiến tìm thấy trước khi làm; phổ biến trong y khoa và tâm lý học nhưng hiếm trong NLP; họ đề xuất bộ câu hỏi đăng ký trước cho từng loại nghiên cứu [71]. van der Lee và cộng sự khuyên đăng ký trước cho đánh giá người mang tính khẳng định [40].
- **Cách chia dữ liệu.** Gorman & Bedrick: không tái lập được một số thứ hạng của chín bộ gán từ loại khi dùng các phép chia ngẫu nhiên thay cho phép chia chuẩn [72]. Søgaard và cộng sự: chia ngẫu nhiên cũng cho ước lượng **quá lạc quan**; lý tưởng là **nhiều tập kiểm độc lập**, nếu không được thì nhiều phép chia lệch có chủ đích [73].

### 12.2 Suy luận cho dự án

Các khuyến nghị sau là của tôi.

**Chi phí và thời gian là thước hạng nhất**, đúng với ưu tiên sản phẩm và với [67]. Mỗi lần chạy đánh giá ghi một dòng:

| Trường | Ghi chú |
|---|---|
| Phút/cuốn (wall-clock) | Tách phần chờ embedding do quota khỏi phần xử lý; ghi transport (Vertex hay Developer API) |
| USD/cuốn | Tính từ token vào/ra theo bảng giá ghi ngày; tách theo khâu A2/A3/A4/A5/A8 |
| Số lời gọi LLM/cuốn | Chỉ số dẫn chi phí chính |
| Giây/trang, RAM cho A1 | Như M5 |
| Mô hình, phiên bản, ngày chạy | Phục vụ tái lập [59], [68] |

- **Báo đường cong chất lượng–chi phí**, không chỉ một điểm: ví dụ F1 A8 theo USD/cuốn cho các cấu hình (pass chính đơn, pass chính + pass phụ, các mức gom lô). Đây là tinh thần "hiệu năng theo ngân sách" của [66].
- **Chi phí đánh giá cũng phải báo:** giờ người gán, số người, cách tuyển, hướng dẫn gán đầy đủ (mục D của [68]).
- **Khai việc dùng AI:** nhãn agentic (Codex), giám khảo Claude, tác tử Sonnet rà soát phải ghi ở mục "dùng trợ lý AI" (mục E của [68]) và trong datasheet.
- **Datasheet cho từng bộ vàng** (D-02, vàng A8, vàng A4, D-01 bạc): bảy nhóm của [69] cộng mục nhân khẩu/chuyên môn người gán của [70]. Ghi rõ tầng nhãn (vàng người, bạc agentic + duyệt, bạc).
- **Đăng ký trước giao thức đánh giá cuối** [71]: thước chính mỗi khâu, cách khớp, cách tính CI, kiểm định, số lần nhiễu loạn K, tập cuốn giữ lại. Ghi vào một tệp có ngày, commit trước khi mở tập giữ lại.
- **Chia theo tài liệu:** mọi tập dev/test tách theo cuốn, không theo cặp hay cạnh. Hai cuốn giữ lại (T-01) và tập khoá niêm phong đóng vai "nhiều tập kiểm độc lập" mà [73] khuyên; mỗi tập chỉ dùng một lần cho số cuối.

## 13. Bảng khuyến nghị theo khâu và đối chiếu thước hiện có

### 13.1 Bảng khuyến nghị

Bảng dưới là khuyến nghị của tôi, tổng hợp từ mục 1–12. Cột "cỡ mẫu" là mức tối thiểu hợp lý theo kinh nghiệm văn liệu, không phải kết quả phân tích công suất; nên chạy mô phỏng công suất [51] trước khi chốt.

| Khâu | Đơn vị | Chỉ số chính | Chỉ số phụ | Vàng cần | Cỡ mẫu tối thiểu hợp lý | Đồng thuận báo thế nào | CI / kiểm định | Nguồn |
|---|---|---|---|---|---|---|---|---|
| A1 đọc PDF, cây mục | Ký tự thân bài; tiêu đề; dòng | M3 độ chính xác gán ký tự vào mục lá (macro theo cuốn) | M1 F1 tiêu đề; "complete entry" F1 (tiêu đề + độ sâu + trang); M2 có mẫu số rõ; M4 F1 vai trò dòng + τ + tỉ lệ dòng mất; M5 | Người (D-02 hiện là bạc agentic + duyệt) | 6 cuốn dev + tập khoá; ≥ 20 trang gán đôi để đo trần | κ vai trò dòng; M1/M3 giữa hai người làm trần | Theo cuốn; bootstrap trong cuốn | [1]–[9] |
| A2 vai trò vùng | Section; thêm bản trọng số ký tự | Recall `noi_dung` (section và ký tự) | Macro-F1 (trung bình F1 theo lớp), ma trận nhầm lẫn, support; số khái niệm/cạnh vàng rơi vào vùng sai | Người (chưa có) | Toàn bộ section của ≥ 4 cuốn; gán đôi ≥ 1 cuốn | Cohen κ + % đồng ý; theo lớp | Wilson cho recall trong cuốn; báo số đếm lớp hiếm | [3], [7], [10] |
| A3 trích khái niệm | Khái niệm trong chương mẫu | Recall trên danh sách mù (khớp nghiêm và nới) | Precision bằng pool người phán; R-precision nếu có điểm; SemF1 chỉ chẩn đoán | Người, 2 người + bước soát bỏ sót | ≥ 3 chương, ~80 khái niệm/chương; pool ≥ 100 mục máy | PSA/F1 giữa người, trước và sau soát | Wilson theo chương; bootstrap hai tầng khi gộp | [11]–[15] |
| A4 hợp nhất | Cặp ứng viên; cụm | Precision gộp (cặp) | Recall ước lượng trên mẫu phân tầng; B³ P/R; MUC | Người trên mẫu (vàng Claude hiện là bạc) | 150–200 cặp phân tầng theo độ tương đồng | κ trên cặp; AC1 nếu lệch | Wilson cho precision; trọng số ngược xác suất chọn cho recall | [17]–[23] |
| A5 câu neo | Khái niệm | Precision câu neo theo phán định người | Recall câu định nghĩa cho `defined_here` (ước lượng, không gộp F1) | Người | ≥ 100 khái niệm, gán đôi ≥ 50 | κ/α danh nghĩa | Wilson | [24]–[26] |
| A5 trạng thái dạy | Khái niệm | Độ chính xác trên phần được phủ + độ phủ (1 − `uncertain`) | Ma trận nhầm lẫn 5×5; bản hai lớp "được dạy ở đây"; macro-F1 | Người | Như trên | α danh nghĩa, theo lớp | Wilson; bootstrap trong cuốn | [27], [43] |
| A6/A7 mention map | Mention | (Không có vàng) chẩn đoán qua oracle O4 | Kiểm tay 50 mention ngẫu nhiên | — | 50 mention | — | Wilson | [63] |
| A8 pass chính | Cạnh trực tiếp trong chương có vàng | P/R/F1 cạnh trực tiếp (có điều kiện trên tập khái niệm) | P/R bao đóng; precision hiệu chỉnh nhờ chấm mù cạnh dư; bảng thác nước quy lỗi | Người, giao thức PREAP | Chương vàng hiện có; ≤ 100 cạnh dư chấm mù mỗi cấu hình | PSA/F1 giữa người, có và không tín dụng bắc cầu; máy so với **từng** người | Bootstrap trong cuốn; randomization ghép cặp phân tầng; bảng thắng/thua theo cuốn | [28]–[39] |
| A8 pass phụ (LightGBM) | Cặp ứng viên | PR-AUC trên phân phối ứng viên thật | P/R tại ngưỡng vận hành; không báo accuracy/F1 cân bằng | Người (huấn luyện có thể bằng bạc) | Toàn bộ cặp ứng viên của cuốn giữ lại | — | Bootstrap trong cuốn | [29], [32], [33] |
| A9/A10 lộ trình | Cạnh vàng; đích; lộ trình | Q6 tỉ lệ cạnh vàng bị vi phạm | Q7/Q7b; số chu trình, thành phần liên thông; τ so mục lục (chẩn đoán) | Người | Mọi cạnh vàng trong phạm vi | — | Bootstrap trong cuốn | [8], [37], [38] |
| Chấm người lộ trình | Cặp lộ trình; đường 3 nút | Tỉ lệ thắng A/B mù | Likert 7 mức có neo; đường 3 nút đúng/sai | Giáo viên | ≥ 3 người; ≥ 30 phiếu so sánh (cần kiểm công suất) | α thứ bậc + % đồng ý | Sign test; báo như nghiên cứu thăm dò nếu ít cuốn | [34], [40]–[43] |
| Chi phí, thời gian | Cuốn | Phút/cuốn, USD/cuốn | Số lời gọi LLM, token theo khâu; đường chất lượng–chi phí | — | Mọi cuốn chạy | — | Trung bình ± độ lệch qua K lần | [66]–[68] |
| Nhiễu LLM | Lần chạy | Khoảng của chỉ số chính qua K nhiễu loạn giữ nghĩa | Tỉ lệ cạnh/nhãn ổn định | — | K khai trước (ví dụ 5) | — | Ghép cặp theo nhiễu loạn | [59], [60] |

### 13.2 Đối chiếu thước hiện có

Bảng sau ghi giữ, sửa hay thay cho từng thước đã có, và vì sao.

| Thước hiện có | Quyết định | Lý do |
|---|---|---|
| M1 P/R/F1 tiêu đề | Giữ, sửa | Tương ứng "Titles"/TD F1 [1], [2]; thêm "complete entry" F1 và báo macro theo cuốn để so được với văn liệu |
| M2 độ đúng cha | Giữ, sửa | Tương ứng level accuracy [2]; phải nêu mẫu số (trên tiêu đề ghép đúng hay trên mọi tiêu đề vàng) |
| M3 ký tự thân bài đúng mục lá | Giữ làm chính | Đo đúng thứ khâu sau cần; không có thước trùng trong văn liệu nên tự định nghĩa bằng công thức |
| M4 vai trò dòng + τ | Giữ, sửa | τ bỏ qua phần tử bị mất [6], [8]; thêm tỉ lệ dòng mất hoặc edit distance chuẩn hoá [5]; F1 theo lớp như [3] |
| M5 giây/trang, RAM | Giữ | Đưa vào bảng chi phí chung [67] |
| A2 (chưa có thước) | Thêm mới | Sự cố 29/62 cạnh cho thấy cần recall `noi_dung` và thước hạ nguồn |
| Q3 liệt kê mù | Giữ, sửa | Đúng kiểu vàng của [11], [15]; thêm luật khớp hai mức [12], precision bằng pool [14], hai người + soát bỏ sót [15] |
| A4 "gộp sai mà vàng phát hiện" | Giữ, sửa | Là precision gộp; thêm recall ước lượng phân tầng [23], B³ [19], [20]; vàng Claude là bạc, cần mẫu người |
| A5 "câu neo đúng 79/84" | Giữ, sửa | Là precision theo phán định như [26]; người phán cho số cuối; thêm recall định nghĩa |
| A5 trạng thái dạy | Sửa | Coi `uncertain` là từ chối: báo độ phủ + độ chính xác có chọn lọc [27] |
| Giao thức vàng A8 kiểu PREAP | Giữ | Khớp [34]; thêm tín dụng bắc cầu khi đo đồng thuận |
| Đồng thuận A8 (đếm cạnh chung) | Thay bằng PSA/F1 | κ không tính được khi không có ca âm xác định [35]; PSA ≈ 0,35–0,42 trên số hiện có (giả định chung/hợp) |
| P/R/F1 cạnh trực tiếp | Giữ làm chính | Chuẩn của mọi bộ ở 6.1; ghi rõ "có điều kiện trên tập khái niệm" |
| P/R bao đóng | Giữ làm phụ | Hợp với tính bắc cầu [34], nhưng phạt lặp ở nút nhiều tổ tiên [38] |
| E4 xáo ngữ cảnh | Giữ, nâng cấp | Đúng tinh thần [60]; chuẩn hoá thành K lần khai trước, báo trung bình + khoảng + độ ổn định [59] |
| Chấm mù cạnh dư | Giữ | Trùng với chấm tay quan hệ mới của TExEval-2 [37]; dùng để tính precision hiệu chỉnh |
| Q6 | Giữ làm chính | Thước ràng buộc tự nhiên; tự định nghĩa bằng công thức, cùng mẫu số cho ba thành phần |
| Q7/Q7b | Giữ | Là P/R tập tổ tiên quanh đích; nêu cạm bẫy [38] |
| Kendall τ so mục lục | Giữ (chẩn đoán) | τ là thước chuẩn [8], nhưng mục lục không phải vàng thứ tự học |
| CI Wilson 95% | Giữ có điều kiện | Đúng cho tỉ lệ trên mẫu ngẫu nhiên độc lập [54]; sai khi gộp cạnh nhiều cuốn |
| Bootstrap LCG theo cạnh | Sửa | Cạnh trong cuốn phụ thuộc [47], [49], [55]; dùng bootstrap trong cuốn hoặc hai tầng; so hai hệ bằng randomization ghép cặp phân tầng [52] |
| κ A–B 0,47–0,56 của D-01 | Giữ, đổi tên | Là độ ổn định giữa hai lượt người gán máy, không phải đồng thuận người [57], [58] |

## 14. Câu hỏi mở

Các câu sau cần chủ dự án trả lời trước khi chốt giao thức đánh giá cuối.
1. **"20/87", "30/112", "18/84" nghĩa là gì?** Tôi giả định là số cạnh chung / số cạnh hợp. Nếu mẫu số là tổng hai danh sách hay danh sách một người, PSA ở mục 6.2 phải tính lại.
2. **Có thêm được người gán thứ ba cho A8 và A3 không?** Alt-test [57] và khuyến nghị Krippendorff (theo [43]) đều cần ít nhất ba người. Với hai người, chỉ báo được đồng thuận, không kiểm được việc thay người bằng LLM.
3. **Ngân sách giờ người cho vàng mới:** vai trò section (A2), mẫu cặp A4, recall câu định nghĩa (A5). Cần biết để chọn cỡ mẫu ở bảng 13.1.
4. **Vàng A8 lấy hợp, giao hay hội ý?** PREAP lấy hợp [34]; LectureBank lấy giao [32]; dự án đang hội ý. Cách chọn đổi trực tiếp recall và precision của máy; phải chốt trước khi mở tập giữ lại.
5. **Chương có phải đơn vị độc lập không?** Nếu coi được, bootstrap theo chương có nhiều cụm hơn theo cuốn; nhưng cùng cuốn thì cùng văn phong và cùng người gán, nên tôi nghiêng về không.
6. **Có đăng ký trước giao thức không, và ở đâu?** Đề xuất một tệp trong repo, commit trước khi chạy trên tập khoá [71].
7. **Ai là "giáo viên" chấm lộ trình?** Cần người có chuyên môn môn học tiếng Việt; số người và cách tuyển phải ghi theo mục D của [68].
8. **Phút/cuốn có tính thời gian chờ quota embedding không?** Đề xuất báo cả hai: tổng và phần xử lý (đúng ghi chú về quota Vertex).
9. **M3 và Q6 là thước tự định nghĩa.** Hội đồng có thể hỏi "vì sao không dùng thước chuẩn"; câu trả lời đề xuất: báo kèm thước gần nhất có trong văn liệu ("complete entry" F1, P/R cạnh) để so được, và giữ M3/Q6 vì chúng đo đúng điều sản phẩm cần.
10. **Có nên đưa SemF1 [13] hay khớp embedding vào A3 không?** Cần embedding tiếng Việt đã kiểm cho thuật ngữ chuyên ngành; nếu không có, chỉ để chẩn đoán.

Nguồn chưa đọc bản đầy đủ (chỉ đọc tóm tắt hoặc trích qua nguồn khác): [16] Wang và cộng sự 2015; [20] Amigó và cộng sự 2009; [44] Hayes & Krippendorff 2007; [46] Gwet 2008; [54] Brown, Cai & DasGupta 2001. Feinstein & Cicchetti 1990 và Landis & Koch 1977 chỉ được nhắc qua [43]. Bộ AL-CPL gốc (Liang và cộng sự 2018) chỉ được mô tả qua [33].

## Tài liệu tham khảo (IEEE)

[1] A. Doucet, G. Kazai, S. Colutto, and G. Mühlberger, "Overview of the ICDAR 2013 Competition on Book Structure Extraction," in *Proc. 12th Int. Conf. Document Analysis and Recognition (ICDAR)*, Washington, DC, USA, 2013. [Online]. Available: http://www.cs.helsinki.fi/u/doucet/papers/ICDAR2013.pdf

[2] I. El Maarouf, J. Kang, A. Ait Azzi, S. Bellato, M. Gan, and M. El-Haj, "The Financial Document Structure Extraction Shared Task (FinTOC 2021)," in *Proc. 3rd Financial Narrative Processing Workshop (FNP 2021)*, 2021, pp. 111–119. [Online]. Available: https://aclanthology.org/2021.fnp-1.21

[3] J. Ma, J. Du, P. Hu, Z. Zhang, J. Zhang, H. Zhu, and C. Liu, "HRDoc: Dataset and Baseline Method Toward Hierarchical Reconstruction of Document Structures," in *Proc. AAAI Conf. Artificial Intelligence*, 2023. arXiv:2303.13839. [Online]. Available: https://ojs.aaai.org/index.php/AAAI/article/view/25277

[4] J. Wang, K. Hu, Z. Zhong, L. Sun, and Q. Huo, "Detect-Order-Construct: A Tree Construction based Approach for Hierarchical Document Structure Analysis," arXiv:2401.11874, 2024. [Online]. Available: https://arxiv.org/abs/2401.11874

[5] L. Ouyang *et al.*, "OmniDocBench: Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations," in *Proc. IEEE/CVF Conf. Computer Vision and Pattern Recognition (CVPR)*, 2025. arXiv:2412.07626. [Online]. Available: https://openaccess.thecvf.com/content/CVPR2025/papers/Ouyang_OmniDocBench_Benchmarking_Diverse_PDF_Document_Parsing_with_Comprehensive_Annotations_CVPR_2025_paper.pdf

[6] Z. Wang, Y. Xu, L. Cui, J. Shang, and F. Wei, "LayoutReader: Pre-training of Text and Layout for Reading Order Detection," in *Proc. EMNLP*, 2021, pp. 4735–4744, doi: 10.18653/v1/2021.emnlp-main.389.

[7] B. Pfitzmann, C. Auer, M. Dolfi, A. S. Nassar, and P. W. J. Staar, "DocLayNet: A Large Human-Annotated Dataset for Document-Layout Analysis," in *Proc. ACM SIGKDD (KDD)*, 2022. arXiv:2206.01062. [Online]. Available: https://arxiv.org/abs/2206.01062

[8] M. Lapata, "Automatic Evaluation of Information Ordering: Kendall's Tau," *Computational Linguistics*, vol. 32, no. 4, pp. 471–484, 2006, doi: 10.1162/coli.2006.32.4.471.

[9] L. Pevzner and M. A. Hearst, "A Critique and Improvement of an Evaluation Metric for Text Segmentation," *Computational Linguistics*, vol. 28, no. 1, pp. 19–36, 2002, doi: 10.1162/089120102317341756.

[10] J. Opitz and S. Burst, "Macro F1 and Macro F1," arXiv:1911.03347, 2019 (rev. 2021). [Online]. Available: https://arxiv.org/abs/1911.03347

[11] S. N. Kim, O. Medelyan, M.-Y. Kan, and T. Baldwin, "SemEval-2010 Task 5: Automatic Keyphrase Extraction from Scientific Articles," in *Proc. 5th Int. Workshop on Semantic Evaluation (SemEval)*, 2010, pp. 21–26. [Online]. Available: https://aclanthology.org/S10-1004

[12] T. Zesch and I. Gurevych, "Approximate Matching for Evaluating Keyphrase Extraction," in *Proc. RANLP*, 2009, pp. 484–489. [Online]. Available: https://aclanthology.org/R09-1086

[13] D. Wu, D. Yin, and K.-W. Chang, "KPEval: Towards Fine-Grained Semantic-Based Keyphrase Evaluation," in *Findings of ACL 2024*, 2024, pp. 1959–1981, doi: 10.18653/v1/2024.findings-acl.117.

[14] C. Buckley and E. M. Voorhees, "Retrieval Evaluation with Incomplete Information," in *Proc. 27th ACM SIGIR*, 2004, pp. 25–32, doi: 10.1145/1008992.1009000.

[15] M. Wang, H. Chau, K. Thaker, P. Brusilovsky, and D. He, "Concept Annotation for Intelligent Textbooks," arXiv:2005.11422, 2020. [Online]. Available: https://arxiv.org/abs/2005.11422

[16] S. Wang *et al.*, "Concept Hierarchy Extraction from Textbooks," in *Proc. ACM Symp. Document Engineering (DocEng)*, 2015. (Chỉ đọc tóm tắt.) [Online]. Available: https://pure.psu.edu/en/publications/concept-hierarchy-extraction-from-textbooks/

[17] M. Vilain, J. Burger, J. Aberdeen, D. Connolly, and L. Hirschman, "A Model-Theoretic Coreference Scoring Scheme," in *Proc. 6th Message Understanding Conf. (MUC-6)*, 1995. [Online]. Available: https://aclanthology.org/M95-1005

[18] X. Luo, "On Coreference Resolution Performance Metrics," in *Proc. HLT/EMNLP*, 2005. [Online]. Available: https://aclanthology.org/H05-1004

[19] N. S. Moosavi and M. Strube, "Which Coreference Evaluation Metric Do You Trust? A Proposal for a Link-based Entity Aware Metric," in *Proc. 54th ACL*, 2016, pp. 632–642. [Online]. Available: https://aclanthology.org/P16-1060

[20] E. Amigó, J. Gonzalo, J. Artiles, and F. Verdejo, "A comparison of extrinsic clustering evaluation metrics based on formal constraints," *Information Retrieval*, vol. 12, no. 4, pp. 461–486, 2009, doi: 10.1007/s10791-008-9066-8. (Chỉ đọc tóm tắt.)

[21] D. Menestrina, S. E. Whang, and H. Garcia-Molina, "Evaluating Entity Resolution Results," *Proc. VLDB Endowment*, vol. 3, no. 1, 2010. [Online]. Available: https://vldb.org/pvldb/vol3/R18.pdf

[22] M. Barnes, "A Practitioner's Guide to Evaluating Entity Resolution Results," arXiv:1509.04238, 2015. [Online]. Available: https://arxiv.org/abs/1509.04238

[23] N. G. Marchant and B. I. P. Rubinstein, "In Search of an Entity Resolution OASIS: Optimal Asymptotic Sequential Importance Sampling," arXiv:1703.00617, 2017. [Online]. Available: https://arxiv.org/abs/1703.00617

[24] S. Spala, N. A. Miller, F. Dernoncourt, and C. Dockhorn, "SemEval-2020 Task 6: Definition extraction from free text with the DEFT corpus," in *Proc. 14th Workshop on Semantic Evaluation (SemEval)*, 2020. [Online]. Available: https://aclanthology.org/2020.semeval-1.41

[25] S. Spala, N. A. Miller, Y. Yang, F. Dernoncourt, and C. Dockhorn, "DEFT: A corpus for definition extraction in free- and semi-structured text," in *Proc. 13th Linguistic Annotation Workshop (LAW)*, 2019. [Online]. Available: https://aclanthology.org/W19-4015

[26] R. Navigli and P. Velardi, "Learning Word-Class Lattices for Definition and Hypernym Extraction," in *Proc. 48th ACL*, 2010, pp. 1318–1327. [Online]. Available: https://aclanthology.org/P10-1134

[27] Y. Geifman and R. El-Yaniv, "Selective Classification for Deep Neural Networks," in *Advances in Neural Information Processing Systems (NeurIPS)*, 2017. arXiv:1705.08500. [Online]. Available: https://papers.neurips.cc/paper_files/paper/2017/file/4a8423d5e91fda00bb7e46540e2b0cf1-Paper.pdf

[28] P. P. Talukdar and W. W. Cohen, "Crowdsourced Comprehension: Predicting Prerequisite Structure in Wikipedia," in *Proc. 7th Workshop on Building Educational Applications Using NLP (BEA)*, 2012. [Online]. Available: https://aclanthology.org/W12-2037

[29] C. Liang, Z. Wu, W. Huang, and C. L. Giles, "Measuring Prerequisite Relations Among Concepts," in *Proc. EMNLP*, 2015. [Online]. Available: https://aclanthology.org/D15-1193

[30] L. Pan, C. Li, J. Li, and J. Tang, "Prerequisite Relation Learning for Concepts in MOOCs," in *Proc. 55th ACL*, 2017. [Online]. Available: https://aclanthology.org/P17-1133

[31] J. Gordon, L. Zhu, A. Galstyan, P. Natarajan, and G. Burns, "Modeling Concept Dependencies in a Scientific Corpus," in *Proc. 54th ACL*, 2016. [Online]. Available: https://aclanthology.org/P16-1082

[32] I. Li, A. R. Fabbri, R. R. Tung, and D. R. Radev, "What Should I Learn First: Introducing LectureBank for NLP Education and Prerequisite Chain Learning," in *Proc. AAAI*, 2019. arXiv:1811.12181. [Online]. Available: https://arxiv.org/abs/1811.12181

[33] C. Alzetta, A. Miaschi, F. Dell'Orletta, F. Koceva, and I. Torre, "PRELEARN @ EVALITA 2020: Overview of the Prerequisite Relation Learning Task for Italian," in *Proc. EVALITA 2020*, 2020. [Online]. Available: https://aclanthology.org/2020.evalita-1.54

[34] C. Alzetta, I. Torre, and F. Koceva, "Annotation Protocol for Textbook Enrichment with Prerequisite Knowledge Graph," *Technology, Knowledge and Learning*, vol. 29, pp. 197–228, 2024, doi: 10.1007/s10758-023-09682-6.

[35] G. Hripcsak and A. S. Rothschild, "Agreement, the F-Measure, and Reliability in Information Retrieval," *J. Am. Med. Inform. Assoc.*, vol. 12, no. 3, pp. 296–298, 2005, doi: 10.1197/jamia.M1733.

[36] C. Liang, J. Ye, H. Zhao, B. Pursel, and C. L. Giles, "Active Learning of Strict Partial Orders: A Case Study on Concept Prerequisite Relations," arXiv:1801.06481, 2018. [Online]. Available: https://arxiv.org/abs/1801.06481

[37] G. Bordea, E. Lefever, and P. Buitelaar, "SemEval-2016 Task 13: Taxonomy Extraction Evaluation (TExEval-2)," in *Proc. 10th Int. Workshop on Semantic Evaluation (SemEval)*, 2016. [Online]. Available: https://aclanthology.org/S16-1168

[38] A. Kosmopoulos, I. Partalas, E. Gaussier, G. Paliouras, and I. Androutsopoulos, "Evaluation Measures for Hierarchical Classification: a unified view and novel approaches," arXiv:1306.6802, 2013. [Online]. Available: https://arxiv.org/abs/1306.6802

[39] N. L. Le and M.-H. Abel, "How Well Do LLMs Predict Prerequisite Skills? Zero-Shot Comparison to Expert-Defined Concepts," arXiv:2507.18479, 2025. [Online]. Available: https://arxiv.org/abs/2507.18479

[40] C. van der Lee, A. Gatt, E. van Miltenburg, S. Wubben, and E. Krahmer, "Best practices for the human evaluation of automatically generated text," in *Proc. 12th Int. Conf. Natural Language Generation (INLG)*, 2019. [Online]. Available: https://aclanthology.org/W19-8643

[41] J. Novikova, O. Dušek, and V. Rieser, "RankME: Reliable Human Ratings for Natural Language Generation," in *Proc. NAACL-HLT*, 2018. [Online]. Available: https://aclanthology.org/N18-2012

[42] D. M. Howcroft *et al.*, "Twenty Years of Confusion in Human Evaluation: NLG Needs Evaluation Sheets and Standardised Definitions," in *Proc. 13th INLG*, 2020. [Online]. Available: https://aclanthology.org/2020.inlg-1.23

[43] R. Artstein and M. Poesio, "Inter-Coder Agreement for Computational Linguistics," *Computational Linguistics*, vol. 34, no. 4, pp. 555–596, 2008. [Online]. Available: https://aclanthology.org/J08-4004

[44] A. F. Hayes and K. Krippendorff, "Answering the Call for a Standard Reliability Measure for Coding Data," *Communication Methods and Measures*, vol. 1, no. 1, pp. 77–89, 2007, doi: 10.1080/19312450709336664. (Chỉ đọc tóm tắt.)

[45] N. Wongpakaran, T. Wongpakaran, D. Wedding, and K. L. Gwet, "A comparison of Cohen's Kappa and Gwet's AC1 when calculating inter-rater reliability coefficients: a study conducted with personality disorder samples," *BMC Medical Research Methodology*, vol. 13, art. 61, 2013, doi: 10.1186/1471-2288-13-61.

[46] K. L. Gwet, "Computing inter-rater reliability and its variance in the presence of high agreement," *British J. Mathematical and Statistical Psychology*, vol. 61, no. 1, pp. 29–48, 2008. (Chưa đọc bản đầy đủ.)

[47] P. Koehn, "Statistical Significance Tests for Machine Translation Evaluation," in *Proc. EMNLP*, 2004. [Online]. Available: https://aclanthology.org/W04-3250

[48] T. Berg-Kirkpatrick, D. Burkett, and D. Klein, "An Empirical Investigation of Statistical Significance in NLP," in *Proc. EMNLP-CoNLL*, 2012. [Online]. Available: https://aclanthology.org/D12-1091

[49] R. Dror, G. Baumer, S. Shlomov, and R. Reichart, "The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing," in *Proc. 56th ACL*, 2018. [Online]. Available: https://aclanthology.org/P18-1128

[50] R. Dror, G. Baumer, M. Bogomolov, and R. Reichart, "Replicability Analysis for Natural Language Processing: Testing Significance with Multiple Datasets," *Trans. Assoc. Comput. Linguistics*, vol. 5, 2017. [Online]. Available: https://aclanthology.org/Q17-1033

[51] D. Card, P. Henderson, U. Khandelwal, R. Jia, K. Mahowald, and D. Jurafsky, "With Little Power Comes Great Responsibility," in *Proc. EMNLP*, 2020. [Online]. Available: https://aclanthology.org/2020.emnlp-main.745

[52] A. Yeh, "More accurate tests for the statistical significance of result differences," in *Proc. COLING*, 2000. [Online]. Available: https://aclanthology.org/C00-2137

[53] A. Søgaard, A. Johannsen, B. Plank, D. Hovy, and H. Martinez, "What's in a p-value in NLP?," in *Proc. CoNLL*, 2014. [Online]. Available: https://aclanthology.org/W14-1601

[54] L. D. Brown, T. T. Cai, and A. DasGupta, "Interval Estimation for a Binomial Proportion," *Statistical Science*, vol. 16, no. 2, pp. 101–133, 2001, doi: 10.1214/ss/1009213286. (Chỉ đọc tóm tắt.)

[55] V. Saravanan, G. J. Berman, and S. J. Sober, "Application of the hierarchical bootstrap to multi-level data in neuroscience," arXiv:2007.07797, 2020. [Online]. Available: https://arxiv.org/abs/2007.07797

[56] L. Zheng *et al.*, "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena," in *Advances in Neural Information Processing Systems (NeurIPS), Datasets and Benchmarks Track*, 2023. arXiv:2306.05685. [Online]. Available: https://arxiv.org/abs/2306.05685

[57] N. Calderon, R. Reichart, and R. Dror, "The Alternative Annotator Test for LLM-as-a-Judge: How to Statistically Justify Replacing Human Annotators with LLMs," arXiv:2501.10970, 2025. [Online]. Available: https://arxiv.org/abs/2501.10970

[58] A. Bavaresco *et al.*, "LLMs instead of Human Judges? A Large Scale Empirical Study across 20 NLP Evaluation Tasks," in *Proc. 63rd ACL*, 2025. arXiv:2406.18403. [Online]. Available: https://arxiv.org/abs/2406.18403

[59] B. Atil *et al.*, "Non-Determinism of 'Deterministic' LLM Settings," arXiv:2408.04667, 2024 (rev. 2025). [Online]. Available: https://arxiv.org/abs/2408.04667

[60] M. Sclar, Y. Choi, Y. Tsvetkov, and A. Suhr, "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I learned to start worrying about prompt formatting," in *Proc. ICLR*, 2024. arXiv:2310.11324. [Online]. Available: https://arxiv.org/abs/2310.11324

[61] C. G. Northcutt, A. Athalye, and J. Mueller, "Pervasive Label Errors in Test Sets Destabilize Machine Learning Benchmarks," in *NeurIPS Datasets and Benchmarks Track*, 2021. arXiv:2103.14749. [Online]. Available: https://arxiv.org/abs/2103.14749

[62] J. R. Finkel, C. D. Manning, and A. Y. Ng, "Solving the Problem of Cascading Errors: Approximate Bayesian Inference for Linguistic Annotation Pipelines," in *Proc. EMNLP*, 2006. [Online]. Available: https://aclanthology.org/W06-1673

[63] V. Stoyanov, N. Gilbert, C. Cardie, and E. Riloff, "Conundrums in Noun Phrase Coreference Resolution: Making Sense of the State-of-the-Art," in *Proc. ACL-IJCNLP*, 2009. [Online]. Available: https://aclanthology.org/P09-1074

[64] B. Taillé, V. Guigue, G. Scoutheeten, and P. Gallinari, "Let's Stop Incorrect Comparisons in End-to-end Relation Extraction!," in *Proc. EMNLP*, 2020. [Online]. Available: https://aclanthology.org/2020.emnlp-main.301

[65] J. K. Kummerfeld and D. Klein, "Error-Driven Analysis of Challenges in Coreference Resolution," in *Proc. EMNLP*, 2013. [Online]. Available: https://aclanthology.org/D13-1027

[66] J. Dodge, S. Gururangan, D. Card, R. Schwartz, and N. A. Smith, "Show Your Work: Improved Reporting of Experimental Results," in *Proc. EMNLP-IJCNLP*, 2019. [Online]. Available: https://aclanthology.org/D19-1224

[67] R. Schwartz, J. Dodge, N. A. Smith, and O. Etzioni, "Green AI," arXiv:1907.10597, 2019. [Online]. Available: https://arxiv.org/abs/1907.10597

[68] ACL Rolling Review, "Responsible NLP Research Checklist." [Online]. Available: https://aclrollingreview.org/responsibleNLPresearch/ (truy cập 2026-10-26)

[69] T. Gebru *et al.*, "Datasheets for Datasets," arXiv:1803.09010, 2018 (bản in: *Commun. ACM*, 2021, theo ghi chú trên arXiv). [Online]. Available: https://arxiv.org/abs/1803.09010

[70] E. M. Bender and B. Friedman, "Data Statements for Natural Language Processing: Toward Mitigating System Bias and Enabling Better Science," *Trans. Assoc. Comput. Linguistics*, vol. 6, 2018. [Online]. Available: https://aclanthology.org/Q18-1041

[71] E. van Miltenburg, C. van der Lee, and E. Krahmer, "Preregistering NLP research," in *Proc. NAACL-HLT*, 2021. [Online]. Available: https://aclanthology.org/2021.naacl-main.51

[72] K. Gorman and S. Bedrick, "We need to talk about standard splits," in *Proc. 57th ACL*, 2019. [Online]. Available: https://aclanthology.org/P19-1267

[73] A. Søgaard, S. Ebert, J. Bastings, and K. Filippova, "We Need to Talk About Random Splits," in *Proc. EACL*, 2021. [Online]. Available: https://aclanthology.org/2021.eacl-main.156
