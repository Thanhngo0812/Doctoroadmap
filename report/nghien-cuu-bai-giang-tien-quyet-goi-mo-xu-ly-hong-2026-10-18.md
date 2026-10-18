# Nghiên cứu: bài giảng nhắc tiên quyết, gợi mở khái niệm sau, và xử lý bài hỏng hẳn (2026-10-18)

Trạng thái: xong — đã xong mục 1–8 (2026-10-18)

## 1. Tóm tắt khuyến nghị

Báo cáo trả lời hai yêu cầu của chủ dự án: bài giảng phải cho thấy tính tiên quyết ("gợi lại trước, gợi mở sau"), và bản lùi trích câu
không bao giờ hiện cho người học. Báo cáo chỉ bổ sung cho [nghiên cứu bài giảng 2026-10-11](nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md).
Không gọi mô hình (0 USD), không sửa mã. Đoạn *suy luận* là ý của người viết, chưa có thí nghiệm.

**Hiện trạng đo được:**
- Lượt thật 12 bài: 3 bài có tiên quyết, 0 bài có ý nhắc nền. Lý do: prompt không yêu cầu; tiên quyết thiếu câu neo thì K2 bỏ hết; 2/3 tiên
  quyết là `legacy_excerpt` (đồ thị cũ không có câu trích cạnh; một ca "vì sao" là dòng mục lục).
- Trên đồ thị chuỗi gộp, 86–97% khái niệm có tiên quyết hiển thị và 47–59% có khái niệm sau có câu trích. Câu trích cạnh bị cắt ở 120 ký
  tự với 41–67% cạnh.
- 5/12 bài hỏng cả hai lần; lần sửa cứu 1/6. **59% tiền bài giảng chi cho bài hỏng**; 0,00365 USD mỗi bài đạt. Bản lùi đang được ghi vào
  cache như bài thật (`single_flight`).

**Tám khuyến nghị:**
1. **Gợi lại trước, đầu bài, ngắn, gập được.** Mỗi tiên quyết (tối đa 3) một dòng: tên + "module m" do mã dựng; **một câu nối do LLM viết
   (≤ 35 âm tiết), chỉ dựa câu trích cạnh `Q#`**; câu trích và câu neo của tiên quyết gập sau nút "vì sao?" và "Nhớ lại định nghĩa".
   Căn cứ: organizer có hiệu ứng nhỏ nhưng dương (ES 0,17–0,21 với organizer viết, [Luiten 1979](https://files.eric.ed.gov/fulltext/ED171803.pdf));
   lợi lớn cho người mới, có hại nhỏ hơn cho người đã biết (d = +0,505 so với −0,428, [Tetzlaff 2025](https://doi.org/10.1016/j.learninstruc.2025.102142));
   gợi nhớ chỉ có ích khi có đáp án (không phản hồi và trả lời đúng ≤ 50%: g = 0,03, [Rowland 2014](https://doi.org/10.1037/a0037559)).
   Thêm khoảng 0,0003 USD mỗi bài (mục 4.3, 4.7).
2. **Không có câu trích cạnh thì không viết "vì sao".** Tiên quyết `legacy_excerpt` chỉ hiện tên, vị trí, câu neo. Ba luật mới bằng mã: K10
   (phủ nhắc nền, thiếu thì hiện phần mã dựng, không sinh lại), K11 (câu trích phải nằm trong `Q#`; không tên khái niệm thứ ba), K12 (độ dài;
   cấm "như bạn đã học"). Câu dẫn trung tính "Bài này dùng tới", vì hệ không theo dõi người học (mục 4.3, 4.6).
3. **Gợi mở sau do mã dựng, 0 USD.** Khối "Tiếp theo" cuối bài: 1–2 khái niệm sau theo cạnh `requires` có câu trích, ghi "module m", nút
   "vì sao?" hiện câu trích đã kiểm ở A8. Bỏ `used_later` khỏi prompt. Gợi mở có bằng chứng yếu nhất, và giá trị sử dụng nói thẳng có thể
   phản tác dụng ([Canning & Harackiewicz 2015](https://doi.org/10.1037/mot0000015)) (mục 4.4).
4. **Stream sau cổng (S3).** Giữ ý LLM trong bộ đệm tới khi có đủ 2 ý giải thích đạt (K8), rồi mới gửi; sau cổng, cắt cụt hay JSON dở không
   làm bài hỏng nữa. Bất biến có test: không bao giờ rút lại ý đã hiện. Nếu khoảng cổng → hết bài dưới 1 giây thì chọn chờ cả bài (mục 5.3).
5. **Khi hỏng hẳn: giữ phần mã dựng, thay phần LLM bằng lời nhắn không kỹ thuật và ba nút** "Đọc trang p trong sách", "Hỏi trợ lý", "Thử lại"
   (chỉ cho lỗi API tạm). Không câu nào trích từ đoạn dạy. Căn cứ: PAIR "return control to the user"; HAX G9, G10 (mục 5.5).
6. **Thử lại ít, ở một tầng, có nhiễu.** Nội dung: sinh lại 1 lần, đổi điều kiện (thử nhiệt độ 1,0). Truyền: 1 lần trên đường bấm, trần cả lần
   bấm khoảng 30 giây (hiện ca xấu nhất là 3 × 60 giây × 2 lần sinh). Bị chặn nội dung: 0 lần. Lần sửa thứ hai thêm khoảng 28% tiền mỗi bài
   mà chỉ giảm khoảng 7 điểm tỉ lệ hỏng (mục 5.4).
7. **Sửa cache:** không ghi `fallback`/`failed` vào cache bài; lỗi API giữ cache âm 60 giây; lỗi luật kiểm ghi bản ghi hỏng 24 giờ (bấm lại 0
   USD), tự hết khi prompt, luật hay mô hình đổi (mục 5.5).
8. **Nâng hợp đồng lên `lecture-2`:** `prerequisites[].recall` + `bridge` thay `note`; `why.status`; `next_up` thay `used_later`; bỏ
   `fallback`; thêm `failure {kind, retryable, retry_after_s, attempts, read_in_book}`; sự kiện `item` chỉ sau cổng; đo TTFT thật (hiện ghi 0)
   (mục 6).

**Chỉ số cần báo ở lượt đo kế tiếp:** USD mỗi bài **đạt** (gồm cả bài hỏng), tỉ lệ cổng mở ở lần 1, p50/p90 tới cổng và tới `final`, bảng
lý do hỏng theo luật K (SA-26), số ý bị rút lại (phải bằng 0) (mục 5.6).

**Chỗ không tìm được nguồn chính thức:** số ES của Stone 1983; mục "Looking ahead" cuối chương như chuẩn của giáo trình mở; trang mô tả "Up
next" của Khan Academy và trường "Recommended experience" của Coursera; nghiên cứu có đối chứng về stream từng ý của văn bản LLM; MiniCheck
và Check Grounding có hỗ trợ tiếng Việt không. Pre-training (d = 0,75) chỉ đọc qua đoạn trích; số của Richter 2016 qua nguồn thứ cấp.

## 2. Cơ sở sư phạm và bằng chứng

Mục này chỉ bổ sung cho [nghiên cứu bài giảng 2026-10-11](nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md), mục 3.2. Merrill 2002, Ausubel
1960, Mayer & Moreno 2003, Kalyuga 2003, Roediger & Karpicke 2006, Dunlosky 2013 đã có ở đó; ở đây không nhắc lại. Mọi nguồn truy cập
2026-10-18. Đoạn mở bằng *Suy luận:* là ý của người viết.

**Cách đọc cột "độ tin":**
- **mạnh:** phân tích gộp có cỡ hiệu ứng, nhiều nghiên cứu, kết quả ổn định;
- **vừa:** phân tích gộp cũ, hay tổng quan có hệ thống không gộp số, hay kết quả lệch theo điều kiện;
- **yếu:** một vài thí nghiệm nhỏ, hay chỉ có lý thuyết.

### 2.1 Bảng bằng chứng

| # | nguồn | thiết kế | cỡ hiệu ứng | độ tin | điều rút ra |
|---|---|---|---|---|---|
| P1 | Luiten, Ames, Ackerson, *AERJ* 17(2), 1980 ([ERIC EJ233231](https://eric.ed.gov/?id=EJ233231)); bản báo cáo đầy đủ 1979 ([ERIC ED171803, PDF](https://files.eric.ed.gov/fulltext/ED171803.pdf)) | phân tích gộp kiểu Glass, 135 nghiên cứu advance organizer; 110 cỡ hiệu ứng cho học, 50 cho nhớ lâu | học: ES = 0,21 (SE 0,04). Nhớ lâu tăng theo thời gian: 0,19 (≤ 7 ngày) → 0,38 (≥ 22 ngày). Organizer **viết**: 0,17 (k = 89); organizer **nói**: 0,37 (k = 21) (Bảng 1, 5 của bản 1979) | vừa (gộp cũ, không hiệu chỉnh thiên lệch xuất bản; nhiều nghiên cứu dùng cùng một bài kiểm cho học và nhớ) | Đoạn mở đầu bằng chữ có tác dụng **nhỏ nhưng dương**. Không kỳ vọng hiệu ứng lớn. |
| P2 | Stone, *J. Exp. Educ.* 51(4), 1983 ([Crossref](https://doi.org/10.1080/00220973.1983.11011862)); bản 1982 ([ERIC ED220476](https://eric.ed.gov/?id=ED220476)) | phân tích gộp kiểu Glass, nghiên cứu dài hạn | **không tìm thấy nguồn chính thức** cho số ES (chỉ đọc được tóm tắt ERIC). Tóm tắt nói: organizer gắn với học và nhớ tốt hơn; organizer **chỉ bằng chữ** và **trừu tượng** có ES thấp hơn; **không** giúp riêng người ít kiến thức nền | vừa | Ngược dự đoán của Ausubel ở hai điểm quan trọng với dự án: chữ trừu tượng yếu; người thiếu nền không được lợi thêm. |
| P3 | Mayer, "Twenty years of research on advance organizers", *Instructional Science* 8, 1979 ([ERIC EJ205236](https://eric.ed.gov/?id=EJ205236)); bản báo cáo 79-1 ([ERIC ED206691, PDF](https://files.eric.ed.gov/fulltext/ED206691.pdf)) | tổng quan 44 nghiên cứu (27 có nhóm chứng, 17 so organizer trước với sau) | không gộp số. Kết luận: "small but consistent advantages", rõ hơn khi tài liệu **lộn xộn hay lạ**, người học **thiếu nền**, và bài kiểm đo **chuyển giao xa** | vừa | Lợi nhất cho người mới và câu hỏi hiểu sâu; ít lợi khi tài liệu đã có thứ tự tốt (giáo trình). |
| P4 | Barnes & Clawson, *RER* 45(4), 1975 ([ERIC EJ135379](https://eric.ed.gov/?id=EJ135379)); phản biện: Lawton & Wanska 1977 ([EJ166909](https://eric.ed.gov/?id=EJ166909)), Ausubel 1978 ([EJ189544](https://eric.ed.gov/?id=EJ189544)), Mayer 1979 ([EJ205675](https://eric.ed.gov/?id=EJ205675)), McEneany 1990 ([EJ407863](https://eric.ed.gov/?id=EJ407863)) | đếm phiếu 32 nghiên cứu; các bài đáp lại | Barnes & Clawson kết luận organizer "nhìn chung không" giúp học; Mayer 1979 cho rằng cách đếm phiếu bỏ sót điều kiện; McEneany 1990 nghi ngờ cả định nghĩa "organizer" | — (tranh luận) | Phê bình chính: định nghĩa organizer mơ hồ; nhóm có organizer được thêm thông tin và thời gian. Thiết kế của dự án phải nói rõ "nhắc nền" là gì, đo được bằng mã. |
| P5 | Mayer, Bromage, *J. Educ. Psychol.* 72(2), 1980 ([DOI](https://doi.org/10.1037/0022-0663.72.2.209)); Mayer 1978 ([ERIC ED154376](https://eric.ed.gov/?id=ED154376)) | thí nghiệm sinh viên; organizer **trước** so với **sau** bài đọc; văn bản thứ tự logic so với ngẫu nhiên | không có số trong tóm tắt. Organizer trước giúp câu hỏi tích hợp; organizer sau giúp câu hỏi chi tiết trong đoạn. Văn bản đã logic thì organizer không thêm gì | vừa (vài thí nghiệm, cùng nhóm tác giả) | **Vị trí có ý nghĩa:** nhắc nền đặt **đầu bài** (tác động lúc mã hoá); gợi mở đặt **cuối bài** có vai trò khác (tóm, nối), không thay được nhắc nền. |
| P6 | Simonsmeier, Flaig, Deiglmayr, Schalk, Schneider, *Educ. Psychol.* 57(1), 2022 ([DOI](https://doi.org/10.1080/00461520.2021.1939700); [bản PDF của tác giả](https://www.uni-trier.de/fileadmin/fb1/prof/PSY/PAE/Team/Schneider/SimonsmeierEtAl2021.pdf)) | phân tích gộp 8.776 cỡ hiệu ứng | tương quan kiến thức trước–sau: r = 0,534. Tương quan kiến thức trước với **mức tăng chuẩn hoá**: r = −0,059, khoảng dự báo 95% [−0,688; 0,621] | mạnh | Có nền thì điểm cuối cao hơn, nhưng **không** chắc học nhanh hơn. Không có luật chung "càng nhắc nền càng tốt"; tác dụng tuỳ điều kiện. |
| P7 | Dochy, Segers, Buehl, *RER* 69(2), 1999 ([Crossref](https://doi.org/10.3102/00346543069002145)); Dochy 1988 ([ERIC ED387486](https://eric.ed.gov/?id=ED387486)) | tổng quan 183 tài liệu | không gộp số. Kiến thức nền "nhìn chung" có tác dụng dương; tác dụng thay đổi theo cách đo. Báo cáo 1988 dẫn kiến thức nền giải thích **30–60% phương sai** kết quả học | vừa | Kiến thức nền là biến mạnh nhất dự báo kết quả. Lý do để bài giảng nhắc tiên quyết, không phải bằng chứng rằng *nhắc* thì đủ. |
| P8 | Kostons & van der Werf, *BJEP* 85(3), 2015 ([DOI](https://doi.org/10.1111/bjep.12069)) | thí nghiệm 2×2, 88 học sinh tiểu học | kích hoạt kiến thức chủ đề **không** cải thiện điểm hiểu sau khi kiểm soát lượng kiến thức nền; kích hoạt kiến thức siêu nhận thức thì có | yếu (mẫu nhỏ, tiểu học) | Bằng chứng ngược: "nhắc lại" thụ động có thể không đủ. |
| P9 | Alvermann & Hynd, *J. Educ. Res.* 83(2), 1989 ([DOI](https://doi.org/10.1080/00220671.1989.10885937)) | thí nghiệm 62 sinh viên | chỉ kích hoạt kiến thức cũ kém hiệu quả hơn kích hoạt **rồi chỉ rõ chỗ khác** | yếu | Câu nhắc nền nên nói tiên quyết **được dùng thế nào** trong khái niệm đích, không chỉ nhắc nghĩa. |
| P10 | Mayer & Pilegard, chương "Segmenting, pretraining, and modality principles", *Cambridge Handbook of Multimedia Learning*, 2014 ([Cambridge](https://www.cambridge.org/core/books/cambridge-handbook-of-multimedia-learning/principles-for-managing-essential-processing-in-multimedia-learning-segmenting-pretraining-and-modality-principles/DD24C2F48B9B1277CE59F78276110258)) | tổng hợp thí nghiệm của nhóm Mayer | pre-training: đúng ở 13/16 phép thử, **trung vị d = 0,75** (bản 2005: 7/7, d = 0,92). Số đọc qua đoạn trích tóm tắt; trang Cambridge trả 429, chưa mở được | vừa (phần lớn là thí nghiệm của cùng một nhóm, bài kiểm chuyển giao ngay) | Cho biết **tên và đặc điểm** khái niệm thành phần trước bài chính có lợi. Tiên quyết của doc2roadmap đúng là "khái niệm thành phần". Áp từ đa phương tiện sang chữ là *suy luận*. |
| P11 | Alpizar, Adesope, Wong, *ETR&D* 68(5), 2020 ([Springer](https://link.springer.com/article/10.1007/s11423-020-09748-7)); Richter, Scheiter, Eitel, *Educ. Res. Rev.* 17, 2016 ([DOI](https://doi.org/10.1016/j.edurev.2015.12.003); số đọc qua [trang dữ liệu b2find](https://b2find.eudat.eu/dataset/edf0e3e7-9eee-56de-9e2f-904511bfe462)) | phân tích gộp signaling: 29 thí nghiệm, 44 cỡ hiệu ứng, n = 2.726; Richter: tín hiệu nối chữ–hình | Alpizar: **d = 0,38**. Richter: **r = 0,17** [0,11; 0,22] cho chuyển giao, **có điều tiết bởi kiến thức nền** | mạnh–vừa | Tín hiệu rõ (tiêu đề "Kiến thức nền", in đậm tên tiên quyết, nhãn "module m") có lợi nhỏ–vừa. |
| P12 | Tetzlaff, Simonsmeier, Peters, Brod, "A cornerstone of adaptivity – A meta-analysis of the expertise reversal effect", *Learning and Instruction* 98, 2025 ([DOI](https://doi.org/10.1016/j.learninstruc.2025.102142)) | phân tích gộp 60 thí nghiệm, 176 cỡ hiệu ứng, n = 5.924 | người **ít nền** học tốt hơn với hỗ trợ cao: **d = 0,505**. Người **nhiều nền** học tốt hơn với hỗ trợ thấp: **d = −0,428**. Không đối xứng: thêm hỗ trợ cho người mới lợi nhiều hơn bớt hỗ trợ cho người giỏi | mạnh | Expertise reversal là thật: nhắc thừa **có hại** cho người đã biết. Nhưng hại nhỏ hơn lợi cho người mới. Với một bài chung (không theo dõi trình độ): nhắc **ngắn**, có thể **gập**. |
| P13 | McNamara, Kintsch, Songer, Kintsch, *Cognition and Instruction* 14(1), 1996 ([DOI](https://doi.org/10.1207/s1532690xci1401_1)) | hai thí nghiệm, học sinh THCS, văn bản khoa học | người ít nền lợi từ văn bản mạch lạc (nói rõ quan hệ); người nhiều nền lợi từ văn bản ít mạch lạc, ở mức mô hình tình huống | vừa | Câu "vì sao cần tiên quyết" là phần "làm mạch lạc". Nên ngắn, không giảng lại tiên quyết. |
| P14 | Rowland, *Psychol. Bull.* 140(6), 2014 ([DOI](https://doi.org/10.1037/a0037559); [PDF](https://courseware.epfl.ch/assets/courseware/v1/fdde2f0aa590bf3b1324077a6bf1540c/asset-v1%3AEPFL%2BDEMO%2B2020%2Btype%40asset%2Bblock/Rowland2014-meta-analysis.pdf)) | phân tích gộp 159 cỡ hiệu ứng, 61 nghiên cứu, kiểm so với học lại | **g = 0,50** [0,42; 0,58]. Có phản hồi: g = 0,73; không phản hồi: g = 0,39. Không phản hồi **và** trả lời đúng ≤ 50%: **g = 0,03** (không có hiệu ứng) | mạnh | Câu hỏi gợi nhớ tiên quyết chỉ có ích khi **có đáp án hiện sau khi trả lời**. Người chưa học tiên quyết sẽ trả lời sai nhiều, nên đáp án là bắt buộc. |
| P15 | Adesope, Trevisan, Sundararajan, *RER* 87(3), 2017 ([DOI](https://doi.org/10.3102/0034654316689306)); Agarwal, Nunes, Blunt, *Educ. Psychol. Rev.* 33, 2021 ([Springer](https://link.springer.com/article/10.1007/s10648-021-09595-9)) | phân tích gộp luyện kiểm tra; tổng quan có hệ thống 50 thí nghiệm ở lớp học thật, 49 cỡ hiệu ứng, n = 5.374 | Adesope: luyện kiểm tra tốt hơn học lại và mọi điều kiện so sánh (số gộp chưa đọc được nguyên văn). Agarwal: **57%** cỡ hiệu ứng ở mức vừa hoặc lớn | mạnh | Gợi nhớ chủ động tốt hơn đọc lại. Nhưng đây là bằng chứng cho câu tự kiểm tra nói chung, không riêng cho tiên quyết. |
| P16 | Pan & Carpenter, *Educ. Psychol. Rev.* 35, 2023 ([Springer](https://link.springer.com/article/10.1007/s10648-023-09814-5)) | tổng quan prequestion / pretest | không gộp số. Hỏi trước khi học giúp học **nếu sau đó được học đáp án**, kể cả khi trả lời sai nhiều | vừa | Câu hỏi gợi nhớ đầu bài dùng được cả cho người **chưa** học tiên quyết, miễn là có đáp án ngay sau. |
| P17 | Hulleman & Harackiewicz, *Science* 326, 2009 ([DOI](https://doi.org/10.1126/science.1177067)); Canning & Harackiewicz, *Motivation Science* 1(1), 2015 ([DOI](https://doi.org/10.1037/mot0000015)) | thí nghiệm thực địa ngẫu nhiên (THPT); ba thí nghiệm phòng lab | Người học **tự viết** về giá trị sử dụng thì hứng thú và điểm tăng ở nhóm kỳ vọng thấp. **Được nói thẳng** "cái này hữu ích" thì **hại** hứng thú và kết quả ở người thiếu tự tin, trừ khi kèm tự viết | vừa | Dòng "học để làm gì" / gợi mở cuối bài nên **cụ thể, trung tính** ("khái niệm X ở module m dùng tới khái niệm này"), không cổ vũ kiểu "rất quan trọng". |

### 2.2 Tổng hợp cho câu hỏi của chủ dự án

Năm điều rút ra:
1. **Nhắc nền đầu bài có cơ sở, nhưng hiệu ứng nhỏ.**
   - Organizer viết có ES khoảng 0,17–0,21 (P1).
   - Pre-training có trung vị d = 0,75 nhưng từ thí nghiệm hẹp của một nhóm (P10).
   - Lợi nhất cho người mới và cho câu hỏi hiểu sâu (P3, P12).
2. **Nhắc thụ động yếu hơn nhắc có liên hệ.**
   - Kích hoạt kiến thức chủ đề thuần tuý có thể không giúp (P8).
   - Phải nói rõ tiên quyết được dùng ở đâu trong khái niệm đích (P9, P13).
   - *Suy luận:* câu "vì sao cần" bám câu trích của cạnh (`Q#`) đúng là phần có giá trị nhất. Câu "nhắc nghĩa" (`N#`) đứng thứ hai.
3. **Nhắc thừa có hại cho người đã biết, nhưng ít hơn lợi cho người mới** (P12: +0,505 so với −0,428).
   - Hệ thống không theo dõi trình độ, nên không chọn được người nào cần nhắc.
   - Cách giảm hại: ngắn (1–2 câu mỗi tiên quyết), có thể gập, tối đa 3 tiên quyết.
4. **Gợi nhớ chủ động tốt hơn nhắc lại, với điều kiện có đáp án** (P14, P15, P16).
   - Không có phản hồi mà người học trả lời đúng dưới một nửa thì không có hiệu ứng (P14: g = 0,03).
   - *Suy luận:* nếu thêm câu hỏi gợi nhớ tiên quyết thì đáp án phải là câu neo nguyên văn của tiên quyết, hiện sau khi người học bấm.
5. **Gợi mở cuối bài có bằng chứng yếu nhất.**
   - Không tìm thấy phân tích gộp nào đo riêng "preview / looking ahead / forward reference" cuối bài.
   - Bằng chứng gần nhất là organizer đặt sau (P5: giúp câu hỏi chi tiết, kém organizer trước ở câu hỏi tích hợp) và giá trị sử dụng (P17).
   - Giá trị sử dụng nói thẳng có thể phản tác dụng với người thiếu tự tin (P17). Nên gợi mở cụ thể, trung tính, có trích dẫn.
   - "Bridging" của Perkins & Salomon là khung lý thuyết về chuyển giao, không phải thí nghiệm. Báo cáo này không dẫn nó như bằng chứng.

*Suy luận:* bằng chứng ủng hộ yêu cầu "gợi lại trước" rõ hơn yêu cầu "gợi mở sau". Gợi mở sau nên coi là phần **định hướng** (người học biết
khái niệm này dẫn tới đâu trong lộ trình), giá rẻ, không phải phần học chính.

## 3. Sản phẩm và giáo trình thật

Chỉ dùng trang của chính sản phẩm hay nhà xuất bản, truy cập 2026-10-18. Trang nào chỉ chạy bằng JavaScript và không đọc được thì ghi rõ.

### 3.1 Bảng so sánh

| sản phẩm | nhắc trước (prerequisite / review) | gợi mở sau (up next / looking ahead) | có chặn không | nguồn |
|---|---|---|---|---|
| **OpenStax** Elementary Algebra 2e, Intermediate Algebra 2e | Đầu mỗi mục từ 2.1 có "Be Prepared": "Before you get started, take this readiness quiz." Mỗi câu kèm "If you missed this problem, review Example 1.54." Đáp án nằm trong sách lời giải | Không có mục "looking ahead" riêng trong lời tựa. Cuối chương có Key Concepts "linking back to the relevant Example(s) in case students need to review" | không | [mục 2.1 EA 2e](https://openstax.org/books/elementary-algebra-2e/pages/2-1-solve-equations-using-the-subtraction-and-addition-properties-of-equality); [lời tựa EA 2e](https://openstax.org/books/elementary-algebra-2e/pages/preface); [lời tựa IA 2e](https://openstax.org/books/intermediate-algebra-2e/pages/preface) |
| **Active Calculus** (Boelkins, giáo trình mở) | Mỗi mục mở bằng 2–3 "Motivating Questions" và một "Preview Activity" làm trước giờ học | Preview Activity "designed to foreshadow the upcoming ideas in the remainder of the section" — gợi mở **trong mục**, không phải sang mục sau | không | [Features of the Text](https://activecalculus.org/single/frontmatter-6.html) |
| **Khan Academy** | Khoá "Get Ready for Grade Level" (2020): "help students master the most important skills they'll need for the next grade", và giúp tìm lỗ hổng trước khi vào lớp. Sau mở rộng sang "Get ready for AP Calculus / AP Statistics" (2021) | Trang khoá học chạy bằng JavaScript, không đọc được phần "up next". **Không tìm thấy nguồn chính thức** mô tả nút "Up next" | Không chặn; có Course challenge để xếp chỗ | [bài của nhân viên KA 2020](https://support.khanacademy.org/hc/en-us/community/posts/360068507371); [bài 2021](https://support.khanacademy.org/hc/en-us/community/posts/360077988172). Trang trợ giúp về mastery trả 403 |
| **Brilliant** | Bài chẩn đoán lúc đăng ký đặt người học vào chủ đề "they have the prerequisites to understand". "No prerequisites required" ở mức toàn nền tảng | Learning Path có "A recommended topic order"; khi học nhanh thì gợi ý "accelerating ahead" | **Có**: nhảy cóc phải qua "level check that gates the later material" | [Course placement guide](https://brilliant.org/help/parents-and-families/course-placement-guide/) (cập nhật 2026-10-07); [What are Learning Paths?](https://brilliant.org/help/features/what-are-learning-paths); [Who is Brilliant for?](https://brilliant.org/help/using-brilliant/who-is-brilliant-for) |
| **Coursera** | Trang khoá học có nhãn "Beginner level" và "Recommended experience" (xem trên trang khoá "machine-learning"; nội dung nằm trong hộp bật lên, không đọc được bằng tải HTML) | Không thấy phần gợi mở trong trang khoá. Bài blog 2025: người học xem trước module đầu miễn phí | không | [trang khoá mẫu](https://www.coursera.org/learn/machine-learning); [blog xem trước khoá học](https://blog.coursera.org/introducing-courseras-new-course-preview-experience). **Không tìm thấy nguồn chính thức** của Coursera mô tả trường "Recommended experience" |
| **ALEKS** (McGraw Hill) | Đánh giá thích ứng 20–25 câu, ra "knowledge state" và "the problem types that the individual is ready to learn next". Dựa trên Knowledge Space Theory (Falmagne, Doignon) | Người học chỉ được làm "the topics they are ready to learn", tức chủ đề đã đủ tiên quyết | **Có**, theo mô hình kiến thức từng người | [Research behind ALEKS](https://www.aleks.com/about_aleks/research_behind); [Overview](https://www.aleks.com/about_aleks/overview) |

### 3.2 Điều rút ra

Bốn điểm:
- **Mẫu phổ biến nhất là "kiểm nhanh rồi trỏ về chỗ cũ".**
  - OpenStax không giảng lại tiên quyết. Nó hỏi 2–4 câu và trỏ về đúng ví dụ cũ ("review Example 1.54").
  - Cách này gần với doc2roadmap: mỗi tiên quyết đã có câu neo (`N#`) kèm trang.
  - *Suy luận:* "nhắc nền" nên ngắn và **trỏ về trang sách**, thay vì viết lại bài của tiên quyết.
- **Hệ có chặn (ALEKS, Brilliant) cần mô hình kiến thức từng người.**
  - Doc2roadmap không theo dõi tiến độ và không chặn (đề cương; [spec Pha B](../doc/pha-b-spec.md)).
  - Vì vậy không dùng được "ready to learn". Phần nhắc nền phải viết cho **cả hai** loại người học: đã học và chưa học tiên quyết.
- **Gợi mở sau ít được làm thành mục riêng.**
  - Active Calculus gợi mở ở đầu mục, cho nội dung **của chính mục đó**.
  - Brilliant, Khan Academy dùng thứ tự lộ trình (đường học, khoá kế tiếp), không viết câu gợi mở trong bài.
  - **Không tìm thấy nguồn chính thức** về mục "Looking ahead" cuối chương như một chuẩn của giáo trình mở (OpenStax, PreTeXt, LibreTexts).
  - *Suy luận:* doc2roadmap đã có lộ trình và `next_node_id`. Gợi mở sau nên là **dòng do mã dựng** (tên + "module m"), có thể thêm 1 câu trích. Không cần LLM viết đoạn văn.
- **Không sản phẩm nào trong bảng hiện bài giảng sinh tự động có kiểm nguồn**, nên không có mẫu thật để chép cho phần xử lý bài hỏng. Mục 5 dựa trên hướng dẫn thiết kế chung.

[CHÈN HÌNH 1 – Hai cách đặt tiên quyết trong một trang bài học. Bên trái "kiểu OpenStax": đầu bài có khung "Sẵn sàng chưa?" với 2–3 câu hỏi nhỏ, mỗi câu có dòng "Nếu sai, xem lại Ví dụ 1.54" trỏ về chỗ cũ. Bên phải "kiểu ALEKS": sơ đồ các chủ đề thành vòng tròn, chủ đề đã biết tô đậm, chủ đề "sẵn sàng học" viền sáng, chủ đề chưa đủ tiên quyết bị khoá. Chú thích dưới: doc2roadmap theo kiểu trái vì không theo dõi người học.]

## 4. Thiết kế phần nhắc nền và gợi mở cho doc2roadmap

### 4.1 Hiện trạng (đo 2026-10-18, 0 USD)

Số đo lấy từ `tmp/phaseb-live-group2-v2.json` (12 bài thật, ghi 2026-10-15) và từ `graph.json` bản mới nhất của sáu cuốn phát triển
(doc-1 v53, xstk-ch3-1 v64, doc-4 v23 dựng bằng chuỗi gộp; nhap-mon-ml v46, naive-bayes v45, doc-6 v17 là đồ thị cũ). Không gọi mô hình.

**Lượt thật: 3/12 bài có tiên quyết, 0/3 có ý nhắc nền.** Ba nguyên nhân, đọc từ mã và dữ liệu:
- **Prompt không yêu cầu.** `_SYSTEM` và trường `task` trong `lectures.py` không nhắc `prereq_notes`. Khối `limits` chỉ ghi tối đa 3. Lược đồ
  không có số tối thiểu. Mô hình bỏ trống là hợp lệ.
- **Tiên quyết không có câu neo thì không viết được.** K2 bắt `prereq` phải là nhãn `N#`. Ở doc-6, nút "CSDL" không có trường `anchor`
  (đồ thị v17 không nút nào có), nên `N` rỗng và mọi ý nhắc nền đều bị bỏ.
- **Đồ thị cũ không có câu trích cạnh.** 2/3 tiên quyết trong lượt thật là `citation_source = legacy_excerpt`
  (`warning = missing_edge_quote`). Khi đó mã lấy một đoạn có tên hai đầu làm "why". Ca doc-6: "why" là hai dòng mục lục
  ("Chương 1: Tổng quan về CSDL / Chương 2: Mô hình dữ liệu quan hệ"). Đó không phải bằng chứng quan hệ.

**Trên đồ thị hiện hành, nhắc nền là việc của gần như mọi bài:**

| cuốn | khái niệm có ≥ 1 tiên quyết hiển thị | phân bố 1 / 2 / 3 tiên quyết | khái niệm có ≥ 1 khái niệm sau (cạnh có câu trích) | cạnh: đích ở module sau / cùng module / trước | câu trích cạnh dài hơn 120 ký tự |
|---|---:|---|---:|---|---:|
| doc-1 v53 | 198/205 (97%) | 132 / 52 / 14 | 106/205 (52%) | 269 / 131 / 2 | 165/402 (41%) |
| xstk-ch3-1 v64 | 75/82 (91%) | 57 / 13 / 5 | 48/82 (59%) | 85 / 62 / 1 | 92/148 (62%) |
| doc-4 v23 | 426/495 (86%) | 240 / 140 / 46 | 231/495 (47%) | 622 / 286 / 31 | 629/939 (67%) |
| nhap-mon-ml v46, naive-bayes v45, doc-6 v17 | không có `display_prerequisites`; mã tự rút gọn bắc cầu và dùng `legacy_excerpt` | — | 0 (không cạnh nào có `quote`) | — | — |

Ba điều rút ra từ bảng:
- Trung bình khoảng 1,3–1,4 tiên quyết mỗi khái niệm có tiên quyết. Ý nhắc nền thêm khoảng 1–2 ý mỗi bài, không phải 3.
- **Chiều của `used_later` đã sửa** trong cây làm việc (`lectures.py` dòng 204 gọi `traverse(node_id, "requires", "out")`). Nhưng
  `traverse` bỏ cạnh không có `quote` (`learning_graph.py` dòng 235), nên trên đồ thị cũ `used_later` luôn rỗng.
- **Câu trích bị cắt cụt khi hiện.** `_bounded_quote` cắt ở 120 ký tự (`learning_graph.py` dòng 310). Với 41–67% cạnh, câu "vì sao"
  hiện cho người học là câu dở, ví dụ "…các phần tử của tổng thể được chia". K3 cho phép tới 200 ký tự.

Thêm hai điểm của mã hiện tại:
- `_trim_context` bỏ `used_later` ngay sau `exercise` khi ngữ cảnh vượt 2.500 token. Khối này chỉ là danh sách tên, không có câu trích.
- Mã thêm **toàn bộ chữ của chunk** chứa câu neo `N#` và câu trích `Q#` vào `sources`. Token vào cho phần nhắc nền vì vậy đã được trả
  sẵn. Bài "Phần tử" có tiên quyết tốn 3.490 token vào, các bài khác 1.474–2.367.

### 4.2 Nguyên tắc

Năm nguyên tắc, mỗi cái kèm căn cứ:
1. **Mã dựng phần nguyên văn, LLM chỉ viết một câu nối.**
   - Tên tiên quyết, ghi chú thứ tự, câu neo `N#`, câu trích cạnh `Q#`, trang: đều có sẵn, kiểm được, 0 USD.
   - LLM viết đúng một câu "dùng tới ra sao", bám câu trích của cạnh.
   - Căn cứ: P9, P13 (giá trị nằm ở câu nối); "Attribute First, then Generate" (chọn đoạn trước, sinh sau, đoạn đã chọn là trích dẫn;
     giảm gần một nửa thời gian kiểm của người, [ACL 2024](https://aclanthology.org/2024.acl-long.182/)).
2. **Không có câu trích cạnh thì không viết câu "vì sao".**
   - Áp cho `legacy_excerpt` và cho tiên quyết thiếu `Q#`.
   - Căn cứ: lỗi chính của STORM là nối sai các mẩu thông tin ([NAACL 2024](https://aclanthology.org/2024.naacl-long.347/)); Ocheja và cộng sự
     dùng đồ thị kiến thức để chọn mức giải thích tiên quyết, và báo LLM vẫn sinh lỗi "có thể đánh lừa học sinh"
     ([arXiv 2412.03856](https://arxiv.org/abs/2412.03856)).
3. **Ngắn và gập được.** Căn cứ: expertise reversal d = −0,428 với người đã biết (P12); người nhiều nền lợi từ văn bản ít giải thích (P13).
4. **Câu dẫn trung tính, không giả định người học đã học.** Hệ thống không theo dõi tiến độ. Viết "Bài này dùng tới", không viết "Bạn đã
   học". Mẫu OpenStax: hỏi nhanh rồi trỏ về đúng chỗ cũ (mục 3).
5. **Gợi mở sau do mã dựng, có câu trích, trung tính.** Căn cứ: bằng chứng yếu nhất trong mục 2; giá trị sử dụng nói thẳng có thể phản tác
   dụng (P17); LLM nhận thêm tên khái niệm sau là thêm nhiễu cùng chủ đề ([Shi, ICML 2023](https://arxiv.org/abs/2302.00093)).

### 4.3 Khối "Kiến thức nền" (đầu bài)

**Vị trí:** sau dòng "Bạn đang ở đâu", trước câu định nghĩa. Căn cứ: organizer đặt trước tác động lúc mã hoá (P5); OpenStax đặt "Be
Prepared" trước nội dung mục.

**Mỗi tiên quyết một dòng, tối đa 3 (Hasse), gồm:**

| phần | ai làm | nội dung | độ dài | hiện mặc định |
|---|---|---|---|---|
| tên + vị trí | mã | tên tiên quyết in đậm; "module m" / "cùng module, ngay trước" / "sách trình bày ở phần sau" | 1 dòng | mở |
| câu nối | LLM | một câu: khái niệm đích **dùng** tiên quyết thế nào, chỉ dựa câu trích `Q#` | ≤ 35 âm tiết | mở |
| câu trích cạnh | mã | câu `Q#` nguyên văn, trang (nút "vì sao?") | ≤ 200 ký tự | gập |
| nhắc lại định nghĩa | mã | câu neo `N#` nguyên văn của tiên quyết, trang, nút "mở bài của tiên quyết" | 1 câu | **gập**, nút "Nhớ lại định nghĩa" |

Lý do gập câu neo:
- Người đã biết bỏ qua được, nên giảm hại expertise reversal (P12).
- Người chưa biết bấm để xem. Đây là gợi nhớ có phản hồi: người học tự nhớ, rồi thấy đáp án (P14, P16). Không cần LLM, 0 USD.
- *Suy luận:* không có thí nghiệm nào đo đúng "nút nhớ lại" kiểu này; hiệu ứng thật phải đo bằng người (mục 4.8).

**Ba trường hợp đặc biệt:**

| trường hợp | ca thật | hiện gì |
|---|---|---|
| có `Q#` (`quoted_evidence`) và có `N#` | doc-1, xstk, doc-4 chuỗi gộp | đủ bốn phần |
| có `Q#`, thiếu `N#` (tiên quyết không có câu neo) | — | ba phần; thay "nhắc lại định nghĩa" bằng "xem trang p" nếu có chunk dạy, không thì bỏ |
| `legacy_excerpt` hoặc không có `Q#` | nhap-mon-ml, naive-bayes, doc-6 | chỉ tên + vị trí + "nhắc lại định nghĩa" nếu có `N#`. **Không câu nối, không nút "vì sao?"**. Không gửi tiên quyết này vào khối nhắc nền của prompt |

*Suy luận:* hiện đoạn `legacy_excerpt` như "vì sao" là trình bày một dòng mục lục thành bằng chứng. Báo cáo bài giảng 2026-10-11 đã cảnh báo
câu trích cạnh chỉ chứng minh định nghĩa *dùng* tiên quyết, không chứng minh phải học trước; đoạn không có câu trích còn yếu hơn thế.

**Người học có thể chưa học tiên quyết.** Không chặn, không hỏi. Bốn việc:
- Câu dẫn khối: "Bài này dùng tới". Không dùng "đã học".
- Ghi chú `module_truoc` hiện "ở module m", không hiện "đã học ở module m" như spec hiện ghi.
- Nút "Mở bài của X" dẫn sang bài giảng của tiên quyết (cùng hàm `make`, có cache).
- Câu nối của LLM không được giả định người học biết tiên quyết; chỉ dẫn hệ thống cấm cụm "như bạn đã biết", "như đã học". Luật K12 bên dưới
  kiểm cụm này bằng mã.

### 4.4 Khối "Tiếp theo" (cuối bài)

**Vị trí:** sau câu tự kiểm tra. Căn cứ: organizer đặt sau hợp với câu hỏi chi tiết, không thay được phần đầu (P5); phần này để định hướng.

**Nội dung, do mã dựng hết, 0 USD:**
- 1–2 khái niệm sau, lấy từ cạnh `requires` **có câu trích** mà khái niệm này là `source`.
- Thứ tự chọn:
  1. khái niệm kế trong dãy học (`next_node_id`) nếu nó là một khái niệm sau;
  2. rồi khái niệm ở module gần nhất phía sau;
  3. hoà thì theo `sequence_index`.
- Mỗi dòng: "**X** (module m) dùng tới khái niệm này" + nút "vì sao?" hiện câu trích cạnh (đã kiểm nguyên văn ở A8) + trang.
- Cạnh có đích ở module **trước** (0,3–3% cạnh): ghi "sách trình bày ở phần trước", không ghi "tiếp theo".
- Không có khái niệm sau có câu trích: chỉ hiện "Khái niệm kế trong lộ trình: Y" từ `next_node_id`, không kèm câu "dùng tới".

**Không đưa khối này vào prompt.** Bỏ `used_later` khỏi ngữ cảnh LLM. Lợi ba mặt:
- bớt nhiễu cùng chủ đề (Shi 2023);
- không còn chuyện bị cắt đầu tiên khi ngữ cảnh dài;
- bớt khoảng 10–40 token vào mỗi bài (ước theo độ dài tên).

**Phương án B (không khuyến nghị cho bản đầu):** LLM viết một câu gợi mở bám câu trích của cạnh sau, nhãn họ mới `L#`. Thêm khoảng 120 token ra
và 50–600 token vào mỗi khái niệm sau (tuỳ nạp câu trích hay cả chunk). Chỉ bật nếu chấm người thấy dòng mã dựng không đủ (mục 4.8).

### 4.5 Ví dụ minh hoạ (tự soạn, lĩnh vực tài chính cá nhân, không lấy từ sáu cuốn)

Giả sử một giáo trình có ba khái niệm: "Lãi suất" (module 1), "Lãi kép" (module 2), "Giá trị hiện tại" (module 3). Cạnh: Lãi suất → Lãi kép;
Lãi kép → Giá trị hiện tại. Các câu dưới đây là câu sách giả định.

Dữ liệu mã có sẵn cho bài "Lãi kép":
- `N1` (câu neo của "Lãi suất", trang 12): "Lãi suất là tỉ lệ phần trăm của số tiền gốc mà người vay trả cho người cho vay trong một kỳ."
- `Q1` (câu trích cạnh Lãi suất → Lãi kép, trang 31): "Với lãi kép, tiền lãi của mỗi kỳ được tính theo lãi suất trên cả gốc lẫn lãi
  đã nhập vào gốc ở các kỳ trước."
- Cạnh sau Lãi kép → Giá trị hiện tại, câu trích (trang 47): "Giá trị hiện tại thu được bằng cách chiết khấu khoản tiền tương lai theo công
  thức lãi kép."

LLM trả cho phần nhắc nền (một ý):

```json
{"prereq_notes": [
  {"prereq": "N1", "sources": ["Q1", "N1"],
   "quote": "tiền lãi của mỗi kỳ được tính theo lãi suất trên cả gốc lẫn lãi",
   "text": "Lãi kép áp lãi suất của từng kỳ lên cả tiền gốc và phần lãi đã nhập gốc.",
   "outside_document": false}
]}
```

Trang hiện:

> **Bài này dùng tới**
> - **Lãi suất** · module 1
>   Lãi kép áp lãi suất của từng kỳ lên cả tiền gốc và phần lãi đã nhập gốc. [vì sao? · tr. 31] [Nhớ lại định nghĩa · tr. 12] [Mở bài "Lãi suất"]
>
> … định nghĩa, giải thích, ví dụ, phân biệt, tự kiểm tra …
>
> **Tiếp theo**
> - **Giá trị hiện tại** (module 3) dùng tới khái niệm này. [vì sao? · tr. 47]

Hai ca hỏng mà luật phải bắt:
- LLM viết "Như bạn đã học, lãi suất…" → K12 bỏ ý (cụm giả định đã học).
- LLM viết "Lãi kép cũng cần khái niệm lạm phát…" mà "lạm phát" không có trong `Q1`, `N1` → K11 bỏ ý (tên khái niệm khác ngoài cặp).

[CHÈN HÌNH 2 – Bố cục một bài giảng từ trên xuống, tô màu theo ai làm: xám = mã dựng (vị trí, tên tiên quyết, câu neo gập, câu trích gập,
định nghĩa, khối "Tiếp theo"), xanh = LLM viết và đã qua luật (câu nối của nhắc nền, giải thích, ví dụ, phân biệt, tự kiểm tra). Mũi tên bên
trái ghi thứ tự sự kiện stream: `skeleton` tới trước (mọi khối xám), rồi từng `item` (khối xanh), cuối cùng `final`. Ghi chú bên phải: khối
"Bài này dùng tới" gập được, nút "Nhớ lại định nghĩa" mở câu neo.]

### 4.6 Luật kiểm bằng mã

Ba luật mới cho phần nhắc nền; khối "Tiếp theo" do mã dựng nên kiểm bằng test, không kiểm lúc chạy:

| # | luật | kiểm thế nào | khi hỏng |
|---|---|---|---|
| K10 | **phủ nhắc nền**: mỗi tiên quyết đủ điều kiện (có `Q#` `quoted_evidence` và có `N#`) có đúng 1 ý `prereq_notes` với `prereq` = nhãn `N#` của nó và `sources` chứa nhãn `Q#` của nó | sau stream, so tập `prereq` với tập tiên quyết đủ điều kiện | **không** sinh lại cả bài; dòng của tiên quyết đó hiện phần mã dựng, không câu nối; ghi `missing_prereq_note` vào nhật ký kiểm |
| K11 | **không bịa quan hệ**: `quote` tìm được nguyên văn trong chữ của `Q#` (không chỉ `N#`); `text` nhắc tên (hoặc alias) của tiên quyết; `text` không chứa tên khái niệm nào khác ngoài đích và tiên quyết đó (so với chỉ mục khái niệm, tên dài nhất trước, bỏ tên phổ biến như mục 6 spec) | chạy ngay khi ý đóng | bỏ ý |
| K12 | **độ dài và giọng**: `text` ≤ 35 âm tiết; không chứa cụm giả định đã học ("như bạn đã biết", "như đã học", "bạn đã học", "nhớ lại rằng"), danh sách cụm đặt trong `BSettings` | chạy ngay khi ý đóng | bỏ ý |

Sửa ba luật cũ:
- **K2:** giữ "`prereq` là `N#` có thật". Thêm: `prereq` phải thuộc tập tiên quyết đủ điều kiện (tiên quyết `legacy_excerpt` không được có ý).
- **K3:** với `prereq_notes`, nguồn đầu tiên phải là `Q#` (thứ tự trong ví dụ mục 4.5), để câu trích là bằng chứng quan hệ, không phải định
  nghĩa của tiên quyết.
- **K8:** không đổi. Thiếu nhắc nền không làm bài hỏng.

Test (mỗi test phải thấy đỏ trên mã hiện tại trước, theo mục 5 của AGENTS.md):
- Mô hình giả trả `prereq_notes = []` cho bài có 1 tiên quyết đủ điều kiện → nhật ký có `missing_prereq_note = 1`; trang vẫn có dòng mã dựng.
- Ý nhắc nền có `quote` chỉ nằm trong `N#` → K11 bỏ.
- Ý có tên một khái niệm thứ ba → K11 bỏ.
- Ý "Như bạn đã học, …" → K12 bỏ.
- Đồ thị A → B, A → C có câu trích, B kế ngay A trong dãy học: bài A có khối "Tiếp theo" = [B, C] theo đúng thứ tự; bài B không chứa A.
- Tiên quyết `legacy_excerpt`: không có nút "vì sao?", không có nhãn `Q#` trong prompt.
- Câu trích cạnh dài 180 ký tự hiện đủ, không bị cắt ở 120.

### 4.7 Chi phí (flash-lite, giá 0,25 / 1,50 USD cho 1 triệu token vào / ra)

Giả định, ghi rõ đo hay ước:
- Token vào: chunk của `N#`, `Q#` **đã nằm trong prompt hiện tại** (mục 4.1). Chỉ thêm chỉ dẫn cho nhắc nền: khoảng 60–100 token (*ước*).
- Token ra mỗi ý nhắc nền: câu ≤ 35 âm tiết khoảng 45 token, câu trích ≤ 200 ký tự khoảng 50–60 token, khoá JSON và nhãn khoảng 25 token,
  tổng khoảng 120–140 token (*ước*, phải đo bằng `usageMetadata`).
- Số ý mỗi bài: trung bình 1,3–1,4 ở bài có tiên quyết (đo, mục 4.1).

| phần | token vào thêm | token ra thêm | USD thêm mỗi bài | ghi chú |
|---|---:|---:|---:|---|
| nhắc nền (K10–K12) | 60–100 | 160–200 | khoảng 0,00026–0,00033 | bằng 15–25% chi một lời gọi trong lượt thật (0,00098–0,00199 USD) |
| bỏ `used_later` khỏi prompt | −10 đến −40 | 0 | khoảng −0,00001 | |
| khối "Tiếp theo" do mã dựng | 0 | 0 | 0 | |
| phương án B (LLM viết gợi mở, 1–2 câu) | 50–1.200 | 120–240 | khoảng 0,0002–0,0007 | không khuyến nghị cho bản đầu |

Nếu sinh hết sáu cuốn (khoảng 900 khái niệm), nhắc nền thêm khoảng 0,25–0,30 USD tổng (*ước*).

**Giảm thêm token ra:** cho phép ý nhắc nền để `quote` rỗng; mã tự gắn câu trích cạnh đã kiểm ở A8. Bớt khoảng 50–60 token mỗi ý
(khoảng −0,0001 USD mỗi bài). Đổi lại K3 không kiểm được câu nối bám đoạn nào trong `Q#`; câu trích cạnh vốn đã ngắn nên mất mát nhỏ.
*Suy luận*; nên hỏi chủ dự án (mục 7).

**Giây chờ:** khoá `prereq_notes` đứng đầu lược đồ, nên ý giải thích đầu tiên tới muộn hơn khoảng 1–1,5 giây (ước từ lượt thật: 387–768 token
ra trong 2,5–7,4 giây). Dòng mã dựng của tiên quyết đã hiện ở `skeleton`, nên người học không thấy khoảng trống. Nếu muốn ý giải thích tới
trước, đổi thứ tự khoá (giải thích trước, nhắc nền sau) và web vẫn đặt khối nhắc nền ở trên; Gemini 3 sinh theo thứ tự khoá của lược đồ
(trang Structured outputs, đọc ở báo cáo 2026-10-11 mục 3.6).

### 4.8 Đo gì để biết có ích

Ba độ đo, gộp vào giao thức chấm của báo cáo 2026-10-11 mục 6:
- **Tự động:** tỉ lệ tiên quyết đủ điều kiện có câu nối qua K10–K12; tỉ lệ ý bị K11, K12 bỏ; token và USD thêm.
- **Chấm người, theo ý:** câu nối có được câu trích cạnh đỡ trọn không (khung AIS); có nói quan hệ đúng chiều không; có giả định người học đã
  học không.
- **Hành vi trên web (khi có web):** tỉ lệ bấm "Nhớ lại định nghĩa", "Mở bài của X", "vì sao?" ở khối "Tiếp theo". *Suy luận:* tỉ lệ bấm
  thấp ở cả hai nút đầu là dấu hiệu khối nhắc nền nên gập mặc định.

### 4.9 Kiểm câu nối có được câu trích đỡ không (bổ sung cho báo cáo 2026-10-11 mục 3.3)

K3 chỉ kiểm câu trích nằm đúng chỗ, không kiểm câu nối có được câu trích đỡ trọn hay không. Ba công cụ mới, chưa có trong báo cáo trước:

| nguồn | là gì | số chính | dùng cho doc2roadmap |
|---|---|---|---|
| Slobodkin và cộng sự, "Attribute First, then Generate", ACL 2024 ([Anthology](https://aclanthology.org/2024.acl-long.182/)) | chọn đoạn nguồn trước, lập câu, rồi sinh từng câu theo đoạn đã chọn | trích dẫn gọn hơn, giữ chất lượng; giảm gần một nửa thời gian kiểm của người | đúng khuôn của câu nối: đoạn đã chọn sẵn là `Q#` |
| Tang, Laban, Durrett, "MiniCheck", EMNLP 2024 ([Anthology](https://aclanthology.org/2024.emnlp-main.499/)) | mô hình nhỏ (770M) kiểm một câu có được tài liệu đỡ không | đạt độ chính xác ngang GPT-4 trên LLM-AggreFact, rẻ hơn 400 lần | ứng viên kiểm offline cho câu nối và câu giải thích. Chưa biết chạy được với tiếng Việt; **không tìm thấy nguồn chính thức** về tiếng Việt |
| Google Cloud, "Check grounding with RAG", cập nhật 2026-10-13 ([trang](https://cloud.google.com/generative-ai-app-builder/docs/check-grounding)) | API trả điểm đỡ 0–1 và trích dẫn cho từng câu; câu chỉ đỡ một phần thì tính là không đỡ; tối đa 200 "fact", mỗi fact 10.000 ký tự | — | là dịch vụ Vertex AI Search, không phải Gemini Developer API; trang không nói hỗ trợ tiếng Việt; chi Vertex tính chung trần. Chỉ hợp cho lượt đo offline, không đặt trên đường bấm-chờ |

*Suy luận:* câu nối ngắn và chỉ dựa một câu trích, nên chấm người theo khung AIS trên một mẫu là đủ cho bản đầu. Công cụ tự động chỉ cần khi
số bài lớn.

## 5. Xử lý bài hỏng hẳn và stream

Quyết định đã có: **bản lùi trích câu không bao giờ hiện cho người học** (chủ dự án, ghi ở [SA-26](../task/sau-a10/26-bai-giang-chong-lap-ban-lui-sach.md)).
Mục này đề xuất hiện gì thay vào, có nên stream, thử lại mấy lần, đo gì. Nguồn truy cập 2026-10-18.

### 5.1 Hiện trạng (đo từ lượt thật, 0 USD)

**Số đo từ 18 lời gọi bài giảng của 12 bài** (`usage_rows` trong `tmp/phaseb-live-group2-v2.json`):

| chỉ số | giá trị |
|---|---|
| bài qua ngay lần 1 | 6/12 |
| bài qua ở lần sửa (lần 2) | 1/6 (doc-1 "Tập hợp") |
| bài hỏng cả hai lần → `fallback` | 5/12 |
| USD một lời gọi | 0,00098–0,00199; trung vị 0,00132; trung bình 0,00142 |
| USD của cả lượt bài giảng | 0,02553 cho 7 bài đạt, tức **0,00365 USD mỗi bài đạt** |
| USD đã chi cho 5 bài hỏng | 0,01495, tức **59%** tổng chi bài giảng |
| thời gian một lời gọi | trung vị 3,4 giây; 2,5–7,4 giây; một ca 22,7 giây |
| thời gian LLM của bài phải gọi hai lần | 5,6–10,4 giây |
| tốc độ ra | phần lớn 108–219 token/giây (ước bằng token ra / tổng thời gian, gồm cả TTFT) |
| TTFT | **không đo được**: `ttft_ms = 0` ở mọi dòng sổ chi |

**Năm điểm của mã hiện tại** (đọc 2026-10-18, chỉ đọc):
- **Bài lùi bị cache như bài thật.** `single_flight` trong `phase_b_store.py` (dòng 90–97) ghi vào cache mọi giá trị `generate()` trả về.
  Nhánh hỏng trả `status = fallback` chứ không ném lỗi, nên bản lùi nằm trong cache mãi tới khi khoá đổi. Spec ghi "không cache bản lỗi".
- **Cache âm chỉ áp cho lỗi ném ra** (lỗi API). Hỏng vì luật kiểm thì không có cache âm.
- **`status = failed` có trong hợp đồng nhưng mã không bao giờ trả.** Mọi đường hỏng về `fallback`.
- **Thử lại ở tầng truyền:** `infrastructure/llm/phase_b.py` (dòng 77–86) thử tối đa 3 lần cho 429, 503 và lỗi mạng, chờ 1 rồi 2 giây,
  **không có nhiễu**. Timeout mỗi lần 60 giây. Ca xấu nhất của một lần bấm: 3 × 60 giây ở tầng truyền, nhân 2 lần sinh ở tầng nội dung.
- **Ý đã stream được trộn vào bản lùi** (báo cáo kiểm thử mục 3.2). Khi bản lùi bị bỏ, các ý đã hiện mà bài lại hỏng là ca "hiện rồi rút
  lại".

*Suy luận:* lần sửa chỉ cứu được 1/6 bài. Ở nhiệt độ 0, cùng ngữ cảnh thì đầu ra gần giống nhau, nên thử lại cùng điều kiện ít tác dụng.
Mẫu quá nhỏ (6 ca) để kết luận; bảng lý do hỏng của SA-26 sẽ cho biết lỗi là ngẫu nhiên hay có hệ thống.

### 5.2 Hướng dẫn thiết kế liên quan

| nguồn | nói gì | áp cho bài hỏng |
|---|---|---|
| Google PAIR, *People + AI Guidebook*, chương "Errors + Graceful Failure" ([trang](https://pair.withgoogle.com/chapter/errors-failing/)) | Chia lỗi thành giới hạn hệ thống, lỗi ngữ cảnh, lỗi nền (background error: hệ sai mà không ai thấy). "Return control to the user": khi AI hỏng, đường đi tiếp dễ nhất thường là để người dùng tự làm. "Explain the system's limits while inviting people to continue forward." | Thông báo nói rõ giới hạn và đưa đường đi tiếp: đọc trang sách, hỏi trợ lý, thử lại. Bản lùi bị cấm hiện chính là để tránh lỗi nền (đoạn rác mà người học không nhận ra). |
| Amershi và cộng sự, "Guidelines for Human-AI Interaction", CHI 2019 ([DOI](https://doi.org/10.1145/3290605.3300233); [PDF](https://www.microsoft.com/en-us/research/uploads/prod/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf)) | 18 nguyên tắc, kiểm với 49 người thiết kế trên 20 sản phẩm. Nhóm "When wrong": G9 "Support efficient correction", G10 "Scope services when in doubt… gracefully degrade". G2 "Make clear how well the system can do what it can do". | G10: không chắc thì thu hẹp dịch vụ (chỉ hiện phần mã dựng đã kiểm), không đưa bài không đạt. G9: một nút thử lại, một nút báo lỗi. |
| Nielsen, "Response Times: The 3 Important Limits", 1993 ([NN/g](https://www.nngroup.com/articles/response-times-3-important-limits/)) | 0,1 giây: thấy tức thì; 1 giây: mạch nghĩ không đứt; 10 giây: giới hạn giữ chú ý. Quá 10 giây cần báo khi nào xong; thời gian biến động mạnh thì phản hồi càng quan trọng. | Bài một lời gọi (trung vị 3,4 giây) nằm giữa 1 và 10 giây. Bài hai lời gọi chạm 10 giây. Thêm lần thử thứ ba sẽ vượt 10 giây. |
| NN/g, "Progress Indicators Make a Slow System Less Insufferable", 2014 ([trang](https://www.nngroup.com/articles/progress-indicators/)); "Skeleton Screens 101", 2023, rà lại 2026-09-02 ([trang](https://www.nngroup.com/articles/skeleton-screens/)) | Dùng chỉ báo tiến trình cho thao tác quá khoảng 1 giây; vòng quay cho thao tác nhanh; thanh phần trăm cho ≥ 10 giây. Skeleton screen dùng cho tải cả trang dưới 10 giây. | Phần mã dựng hiện ngay; chỗ của phần LLM hiện khung xám (skeleton). Không cần thanh phần trăm vì thường dưới 10 giây. |
| Myers, CHI 1985 ([DOI](https://doi.org/10.1145/317456.317459)); Harrison và cộng sự, UIST 2007 ([DOI](https://doi.org/10.1145/1294211.1294231)); Mejtoft và cộng sự, ECCE 2018 ([DOI](https://doi.org/10.1145/3232078.3232086)) | Myers: người dùng thích có chỉ báo tiến trình (thí nghiệm). Harrison: cách thanh chạy đổi cảm nhận thời gian. Mejtoft: skeleton được chấm nhanh và dễ hơn vòng quay nhưng **không có khác biệt có ý nghĩa thống kê** | Bằng chứng cho skeleton là **yếu**: một nghiên cứu nhỏ, không có ý nghĩa thống kê. Dùng skeleton vì hợp bố cục, không vì đã chứng minh nhanh hơn. |
| NVIDIA, "Stream Smarter and Safer… NeMo Guardrails…" ([blog](https://developer.nvidia.com/blog/stream-smarter-and-safer-learn-how-nvidia-nemo-guardrails-enhance-llm-output-streaming/)) | Kiểm theo cụm khi stream; khi luật bắt lỗi, "the objectionable text might have already been sent to the user. It's the responsibility of the caller to manage this situation." | Xác nhận đánh đổi: stream trước khi kiểm xong thì có ca đã hiện rồi mới biết hỏng. |
| Gemini API, "Troubleshooting" và "API errors", cập nhật 2026-10-13 ([troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting); [errors](https://ai.google.dev/gemini-api/docs/api-errors)) | 429, 503: lùi theo hàm mũ (ví dụ 1, 2, 4, 8 giây), **thêm nhiễu**, chỉ thử lại lỗi tạm (429, 408, 5xx), đặt số lần tối đa. SDK Python mặc định thử tới 4 lần, chờ đầu khoảng 1 giây, tối đa 60 giây. Mã bị chặn như `recitation`, `safety`: "modify your input and retry". | Thử lại cùng đầu vào không giúp gì cho bài bị chặn nội dung. Bài giảng trích nguyên văn sách nên phải ghi `finishReason` để biết có ca `recitation` không. |
| Gemini API, "Billing" ([trang](https://ai.google.dev/gemini-api/docs/billing)) | "If your request fails with a 400 or 500 error, you won't be charged for the tokens used. However, the request will still count against your quota." | Bài hỏng vì luật kiểm là phản hồi 200, **bị tính đủ tiền**. Mỗi lần sinh lại là trả thêm khoảng 0,0014 USD. |
| AWS Builders' Library, "Timeouts, retries, and backoff with jitter" ([trang](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)); Google SRE Book, "Addressing Cascading Failures" ([trang](https://sre.google/sre-book/addressing-cascading-failures/)) | AWS: thử lại ở **một tầng** của hệ; giới hạn bằng token bucket; chỉ thử lại thao tác idempotent; thêm jitter. SRE: luôn lùi hàm mũ có ngẫu nhiên; giới hạn số lần mỗi yêu cầu; ngân sách thử lại toàn tiến trình (ví dụ 60 lần/phút); tránh thử lại ở nhiều tầng vì số lần nhân lên. | Hiện có hai tầng (truyền × nội dung = tối đa 6 lần gọi HTTP mỗi lần bấm), cộng nút "Thử lại" của người học là tầng ba. Sinh bài là idempotent theo `lecture_key` nhờ single-flight và cache. |

Không tìm thấy nghiên cứu có đối chứng nào so stream từng ý với hiện cả bài cho văn bản do LLM sinh. Các bài viết tìm được là blog của nhà
cung cấp, không có thí nghiệm (**không tìm thấy nguồn chính thức** cho câu "stream làm người dùng tin hơn").

### 5.3 Stream hay chờ: ba phương án

| phương án | người học thấy | rủi ro hiện rồi rút lại | giây tới chữ LLM đầu tiên (ước từ lượt thật) | độ phức tạp |
|---|---|---|---|---|
| S1. Stream từng ý ngay khi qua luật cục bộ (spec hiện tại) | ý hiện dần | **có**: bài hỏng K1, K6, K8 sau khi đã hiện ý | sớm nhất (TTFT + ý đầu; TTFT chưa đo) | đã có |
| S2. Chờ cả bài qua kiểm | skeleton tới hết, rồi cả bài một lần | không | bằng thời gian cả bài: trung vị 3,4 giây; bài cần sửa 5,6–10,4 giây | thấp nhất |
| **S3. Stream sau cổng (khuyến nghị)** | skeleton tới khi bài **chắc chắn đạt**, sau đó các ý còn lại stream | không, nếu luật được đổi như dưới | giữa S1 và S2 | vừa |

**S3 cụ thể:**
1. Máy chủ giữ các ý đã qua luật cục bộ trong bộ đệm, chưa gửi.
2. **Cổng mở** khi đủ điều kiện mà các ý sau không thể làm bài hỏng nữa. Đề xuất: đủ `lecture_min_explanations` (2) ý giải thích đạt, và mọi ý
   đã đóng đều đạt hay đã bị bỏ đúng luật.
3. Cổng mở: gửi một lần mọi ý trong bộ đệm, rồi stream các ý sau như S1.
4. **Đổi luật toàn bài để sau cổng không gì làm bài hỏng:**
   - bị cắt vì hết token (K6) sau cổng: giữ các ý đã đạt, bỏ phần dở, `status = ready`, thêm cảnh báo nội bộ `cat_cuoi`;
   - lặp (K6): xét theo từng ý như đã có (`_is_duplicate_idea`), bỏ ý lặp; không đánh hỏng cả bài;
   - JSON không đóng (K1) sau cổng: dùng các ý đã tách được, như trên.
5. Hết stream mà cổng chưa mở: không ý LLM nào đã hiện. Sinh lại một lần (mục 5.4) **từ đầu, không trộn** ý của lần trước. Vẫn hỏng thì
   `status = failed` (mục 5.5).

Bất biến kiểm bằng test: **không có sự kiện nào làm biến mất một ý đã gửi.** Test: mô hình giả bị cắt ở ý thứ 4 sau khi đã có 2 ý giải thích
đạt → bài `ready` với 3 ý; mô hình giả chỉ có 1 ý giải thích đạt → không có sự kiện `item` nào, rồi `failed`.

*Suy luận:* S3 giữ lợi ích stream cho phần sau của bài (ví dụ, phân biệt, tự kiểm tra) và loại hẳn ca rút lại. Nếu đo thấy khoảng cách giữa
"cổng mở" và "hết bài" dưới 1 giây ở p50, S2 đơn giản hơn mà gần như không thua; khi đó chọn S2. Cần số TTFT và giờ mở cổng thật (vé 13 chưa
có).

### 5.4 Thử lại

**Khuyến nghị:**

| tầng | khi nào | số lần | cách chờ | ghi chú |
|---|---|---|---|---|
| truyền (HTTP) | 429, 408, 500, 503, lỗi mạng | **1 lần** trên đường bấm-chờ; 2 lần cho tải trước chạy nền | 1 giây × nhiễu ngẫu nhiên (0,5–1,5) | sửa mã hiện tại: thêm nhiễu; trần thời gian **cả lần bấm** khoảng 25–30 giây (*suy luận*, lớn hơn ca chậm nhất đo được 22,7 giây); timeout 60 giây mỗi lần là quá dài cho người đang chờ |
| nội dung (luật K) | cổng S3 không mở, hay K1 trước cổng | **1 lần**, như hiện tại | ngay | lần sửa **đổi điều kiện**: gửi danh sách lỗi; *đề xuất thử* nhiệt độ mặc định 1,0 cho lần sửa, vì Google khuyên giữ mặc định với Gemini 3 (báo cáo 2026-10-11 mục 3.6) và lặp lại cùng điều kiện ở nhiệt độ 0 ít tác dụng (1/6) |
| bị chặn nội dung (`safety`, `recitation`…) | `finishReason` hay mã chặn | **0 lần** | — | Google bảo phải đổi đầu vào; ghi lý do, `failed` |
| người học bấm "Thử lại" | sau `failed` | không tự động | chỉ bật sau `retry_after_s` | cùng `lecture_key`, đi qua single-flight; xem mục 5.5 về cache lỗi |

Ngân sách: theo SRE, đặt một ngân sách thử lại cho cả tiến trình (ví dụ tối đa 10% số lời gọi bài giảng trong một phút là lời thử lại). Vượt
thì trả `failed` ngay, không gọi thêm.

**Chi phí và giây chờ của chính sách thử lại** (dùng số lượt thật: qua lần 1 là 50%, lần sửa cứu 17%; một lời gọi 0,00142 USD và 3,4 giây
trung vị; mẫu nhỏ nên chỉ là ước):

| chính sách nội dung | lời gọi trung bình mỗi bài | USD trung bình mỗi bài | tỉ lệ hỏng hẳn | giây của đường hỏng |
|---|---:|---:|---:|---:|
| không sửa | 1,00 | 0,00142 | 50% | khoảng 3,4 |
| **sửa 1 lần (khuyến nghị, như hiện tại)** | 1,50 | 0,00213 | 42% | khoảng 6,8 (đo: 5,6–10,4) |
| sửa 2 lần | 1,92 | 0,00272 | 35% | khoảng 10,2 |

Đọc bảng:
- Lần sửa thứ hai thêm khoảng 0,0006 USD mỗi bài (+28%) để giảm tỉ lệ hỏng khoảng 7 điểm, và đẩy đường hỏng qua mốc 10 giây của Nielsen.
- Đòn bẩy thật là **giảm tỉ lệ hỏng ở lần 1**: mỗi 10 điểm giảm ở lần 1 bớt khoảng 0,00014 USD mỗi bài và bớt hẳn một lời gọi chờ cho 10% số
  lượt bấm. Muốn vậy cần bảng lý do hỏng của SA-26.
- Lời gọi lỗi 4xx/5xx không bị tính tiền token (trang Billing), nên tầng truyền gần như chỉ tốn thời gian.

### 5.5 Khi bài hỏng hẳn: hiện gì

**Giữ nguyên phần do mã dựng.** Phần `skeleton` (vị trí, khối "Bài này dùng tới" phần mã, câu định nghĩa nguyên văn kèm trang, hình đã xác
nhận, khối "Tiếp theo") đã hiện trước khi gọi LLM ở mọi trường hợp. Đây là dữ liệu đã kiểm từ đồ thị, không phải bản lùi trích câu.
*Cần chủ dự án xác nhận* (mục 7, câu 1).

**Thay chỗ phần LLM bằng một khối thông báo**, không chứa câu nào trích từ đoạn dạy:

| loại hỏng | lời nhắn (đề xuất) | nút |
|---|---|---|
| lỗi API tạm (429, 503, hết thời gian) | "Hệ thống đang bận nên chưa tạo được phần giảng giải. Thử lại sau khoảng một phút." | **Thử lại** (bật sau `retry_after_s`), **Đọc trang p trong sách**, **Hỏi trợ lý** |
| không đạt luật trích nguồn sau lần sửa | "Chưa tạo được phần giảng giải đủ chuẩn trích nguồn cho khái niệm này. Bạn có thể đọc đoạn gốc trong sách." | **Đọc trang p trong sách**, **Hỏi trợ lý**, **Báo lỗi** (không có "Thử lại" ngay, xem dưới) |
| bị chặn nội dung | như dòng trên | như dòng trên |
| hết trần chi | "Đã dùng hết hạn mức tạo bài giảng." | **Đọc trang p**, **Hỏi trợ lý** nếu trợ lý còn trần |

Lý do từng chi tiết:
- **Không có từ kỹ thuật** (K8, JSON, mô hình). PAIR: "be human, not machine".
- **Nói giới hạn, đưa đường đi tiếp** (PAIR "Return control to the user"; HAX G9, G10).
- **Nút "Đọc trang p trong sách"** mở trình xem PDF ở trang của chunk dạy (`page`, offset ký tự đã có). Nó dẫn tới sách gốc, không hiện câu
  nào thay bài giảng, nên không phải bản lùi. *Cần chủ dự án xác nhận* (mục 7, câu 2).
- **Không "Thử lại" ngay cho lỗi luật kiểm**: cùng ngữ cảnh, cùng prompt, gần như chắc hỏng lại và tốn tiền (mục 5.4).

**Cache lỗi:**
- **Sửa ngay:** không ghi `fallback` hay `failed` vào cache bài (`single_flight` hiện ghi mọi giá trị trả về).
- Lỗi API: giữ cache âm 60 giây như spec.
- Lỗi luật kiểm: ghi một **bản ghi hỏng** theo `lecture_key`, sống lâu hơn (đề xuất 24 giờ; *suy luận*). Trong thời gian đó bấm lại thì trả
  `failed` ngay, 0 USD, 0 giây chờ LLM. Khoá đổi khi prompt, lược đồ, mô hình hay `validator_version` đổi, nên sửa prompt xong thì bài tự
  được sinh lại.
- Tải trước gặp bản ghi hỏng thì bỏ qua, không gọi.

[CHÈN HÌNH 3 – Sơ đồ trạng thái của một lần bấm bài giảng. Các ô: "bấm" → "skeleton (0 USD, < 0,1 giây)" → rẽ ba nhánh: "trúng cache → ready",
"có bản ghi hỏng → failed (0 USD)", "gọi LLM lần 1". Từ "gọi LLM lần 1": "cổng mở → stream phần còn lại → ready (vào cache)"; "cổng không mở →
gọi LLM lần 2 (đổi điều kiện)"; "lỗi API → thử lại truyền 1 lần → … → failed + cache âm 60 giây". Từ "gọi LLM lần 2": "cổng mở → ready"; "không
mở → failed + bản ghi hỏng 24 giờ". Ghi chú dưới: không nhánh nào hiện bản trích câu; không nhánh nào rút lại ý đã hiện.]

[CHÈN HÌNH 4 – Dòng thời gian (trục ngang 0–12 giây) của ba phương án S1, S2, S3 cho cùng một bài: vạch "skeleton" ở 0 giây; S1 có các chấm ý
từ khoảng 1,5 giây (minh hoạ, TTFT chưa đo); S2 có một khối ở khoảng 3,4 giây; S3 có khối ở lúc cổng mở rồi các chấm tiếp. Hàng thứ tư: bài phải sửa, kết thúc ở
khoảng 7 giây (đo 5,6–10,4). Vạch dọc ở 1 giây và 10 giây ghi "giới hạn Nielsen".]

### 5.6 Chỉ số cần đo

Đo ở lượt thật kế tiếp (sau SA-26), tách bài trúng cache và bài sinh mới:

| nhóm | chỉ số | ghi chú |
|---|---|---|
| giây | p50, p90 tới `skeleton`; tới lúc cổng mở; tới `final`; tới `failed` | cần TTFT thật (hiện ghi 0) |
| hỏng | tỉ lệ cổng mở ở lần 1; tỉ lệ lần sửa cứu được; tỉ lệ `failed` theo loại (API, luật, chặn, trần); luật làm hỏng theo K | bảng lý do hỏng là đầu vào sửa prompt |
| tiền | USD mỗi bài **đạt** (gồm cả lời gọi của bài hỏng); tỉ lệ chi cho bài hỏng (lượt thật: 59%) | chỉ số chính để báo chủ dự án |
| bất biến | số ý bị rút lại sau khi đã gửi | phải bằng 0; test và đếm ở lượt thật |
| người học (khi có web) | tỉ lệ bấm "Đọc trang p", "Hỏi trợ lý", "Thử lại" sau `failed`; tỉ lệ thử lại thành công | |
| cache | tỉ lệ lượt xem trúng cache; tỉ lệ tải trước trúng | tải trước làm phần lớn lượt bấm theo thứ tự trúng cache |

## 6. Đề xuất sửa spec ở mức trường

Đề xuất cho [spec Pha B](../doc/pha-b-spec.md) mục 8 (bài giảng), 13 (hợp đồng), 15 (cấu hình). Đây là đề xuất để tra hỏi, chưa phải spec.
Các mục đánh dấu **[hỏi]** chờ câu trả lời ở mục 7.

### 6.1 Phiên bản hợp đồng

- Đổi `contract_version` thành **`lecture-2`**: hình dạng `prerequisites[].note` và `used_later` đổi, `fallback` bị bỏ khỏi web.
- Khoá cache đã chứa phiên bản hợp đồng, nên mọi bài cũ (kể cả bản lùi đang nằm trong cache) tự hết hiệu lực.

### 6.2 Lược đồ LLM (`LECTURE_SCHEMA`)

| trường | hiện tại | đề xuất |
|---|---|---|
| `prereq_notes[]` | dùng chung `_grounded_item_schema` (có `relation`, `outside_document`); bắt buộc `text`, `sources`, `quote`, `outside_document` | lược đồ riêng `{prereq, sources, quote, text}`; bắt buộc `prereq`, `sources`, `text`; `prereq` là nhãn `N#`; `sources[0]` là nhãn `Q#` của tiên quyết đó; `quote` bắt buộc **[hỏi: cho phép rỗng để mã gắn câu trích cạnh?]**; bỏ `outside_document` (K7 đã cấm ở đây) |
| thứ tự khoá | `prereq_notes` → `explanation` → `example` → `contrasts` → `self_check` → `gaps` | giữ nguyên, trừ khi đo thấy ý giải thích đầu tới chậm quá 1,5 giây (mục 4.7) |
| `gaps` | có | giữ |

### 6.3 Lắp ngữ cảnh

| khối | hiện tại | đề xuất |
|---|---|---|
| `prerequisites` | mọi tiên quyết hiển thị, kèm `N`, `Q`, `quote`, `order_note`, `citation_source`, `warning`, `note` | thêm cờ `viet_cau_noi: true/false`. `true` chỉ khi `citation_source = quoted_evidence` và có `N`. Tiên quyết `legacy_excerpt` vẫn có tên trong ngữ cảnh nhưng **không** có nhãn `Q` |
| `used_later` | tối đa 3 tên; bỏ thứ hai khi vượt trần | **bỏ khỏi prompt** (mã dựng khối "Tiếp theo") |
| chỉ dẫn | không nhắc `prereq_notes` | thêm 3 câu: "Với mỗi tiên quyết có `viet_cau_noi = true`, viết đúng một ý trong `prereq_notes`: một câu nói khái niệm đích dùng tiên quyết đó thế nào, chỉ dựa câu trích `Q`. Không giả định người học đã học tiên quyết. Không nhắc khái niệm khác." |
| trần bỏ dần | bài tập → học để làm gì → cạnh mở → chunk định nghĩa thứ hai → cắt đuôi chunk định nghĩa thứ nhất | bài tập → cạnh mở → chunk định nghĩa thứ hai → cắt đuôi chunk định nghĩa thứ nhất. Không bao giờ cắt khối tiên quyết có `viet_cau_noi = true` |

### 6.4 Luật kiểm

Bảng luật mới và luật sửa (bổ sung bảng K1–K9 của spec):

| # | luật | khi hỏng | thay đổi |
|---|---|---|---|
| K1 | đúng lược đồ và số mục | trước cổng: sinh lại 1 lần, rồi `failed`. Sau cổng: giữ ý đã đạt, `ready` | bỏ "rồi về mốc trích câu" |
| K2 | như cũ; thêm: `prereq` thuộc tập `viet_cau_noi = true` | bỏ ý | sửa |
| K3 | như cũ; với `prereq_notes`, nguồn đầu tiên phải là `Q#` | bỏ ý | sửa |
| K6 | lặp và cắt cụt | lặp: bỏ ý (theo từng ý). Cắt cụt trước cổng: sinh lại 1 lần. Sau cổng: giữ ý đã đạt, `ready` | sửa |
| K8 | `explanation` ≥ 2 ý đạt | đây chính là **cổng**: chưa đạt khi hết stream thì sinh lại 1 lần (đổi điều kiện), rồi `failed` | bỏ "dùng mốc trích câu" |
| **K10** | phủ nhắc nền (mục 4.6) | không làm bài hỏng; dòng tiên quyết hiện phần mã dựng; ghi `missing_prereq_note` vào nhật ký kiểm | mới |
| **K11** | không bịa quan hệ (mục 4.6) | bỏ ý | mới |
| **K12** | ≤ `lecture_prereq_note_max_syllables` âm tiết; không có cụm trong `lecture_assumed_known_phrases` | bỏ ý | mới |

Ghi chú: K10–K12 đổi `lecture_validator_version`, nên khoá cache đổi (SA-26 đã yêu cầu khoá đổi khi luật đổi).

### 6.5 Hợp đồng `lecture-2`

**`prerequisites[]`** (mã dựng, gửi ở `skeleton`):

```json
{"node_id": "…", "name": "…", "module_index": 2,
 "order_note": "module_truoc | cung_module_truoc | sach_trinh_bay_sau",
 "why": {"status": "co_cau_trich | khong_co_cau_trich",
         "quote": "… (≤ 200 ký tự, không cắt ở 120)", "chunk_id": "…", "page": 31, "citation": {}},
 "recall": {"quote": "câu neo nguyên văn của tiên quyết", "chunk_id": "…", "page": 12, "citation": {}},
 "bridge": null}
```

- `why.status = khong_co_cau_trich` khi `legacy_excerpt` hay thiếu `Q`: web **không** hiện nút "vì sao?" và `why.quote = null`.
- `recall` thay cho `note` hiện tại (hiện `note.text` là câu neo do mã dựng, tên dễ nhầm với câu LLM). `recall = null` khi tiên quyết không
  có câu neo.
- `bridge` = câu nối của LLM `{text, citations, check}`, điền ở sự kiện `item` và `final`; `null` khi K10 thiếu hay `viet_cau_noi = false`.
- Web hiện `order_note = module_truoc` là "ở module m", không "đã học ở module m".

**`next_up[]`** (thay `used_later`, mã dựng, gửi ở `skeleton`, tối đa `lecture_max_next_up` = 2):

```json
{"node_id": "…", "name": "…", "module_index": 3,
 "relation": "dung_toi | ke_tiep_lo_trinh",
 "order_note": "module_sau | cung_module | sach_trinh_bay_truoc",
 "why": {"quote": "…", "chunk_id": "…", "page": 47, "citation": {}}}
```

- `relation = dung_toi`: có cạnh `requires` có câu trích từ khái niệm này tới khái niệm sau; `why` khác null.
- `relation = ke_tiep_lo_trinh`: không có cạnh như vậy, chỉ lấy `position.next_node_id`; `why = null`.

**`status`** ∈ {`ready`, `generating`, `no_source`, `failed`}.
- Bỏ `fallback` khỏi mọi phản hồi gửi web. Đường trích câu chỉ còn ở chế độ ngoại tuyến của trang xem thử và làm mốc ở vé 21; chế độ đó
  ghi `generation_mode = extractive`, không đi qua API web.

**`failure`** (mới; chỉ có khi `status = failed`):

```json
{"kind": "api_tam_thoi | khong_dat_luat | bi_chan | het_tran",
 "retryable": true, "retry_after_s": 60, "attempts": 2,
 "read_in_book": {"chunk_id": "…", "page": 31}}
```

- `read_in_book` trỏ tới chunk dạy đầu tiên, để web mở trình xem PDF đúng trang **[hỏi: có cho link này không]**.
- Mã luật K không gửi web; nằm ở nhật ký kiểm của SA-26.
- `retryable = false` với `khong_dat_luat`, `bi_chan` trong thời gian sống của bản ghi hỏng.

**`warnings`:** bỏ `ban_trich_cau`. Giữ `thieu_cong_thuc`, `khong_co_doan_day`.

**`usage`:** thêm `attempts` (số lời gọi nội dung), `transport_retries`; `ttft_ms` phải là số đo thật.

### 6.6 Sự kiện stream

| sự kiện | khi nào | nội dung | thay đổi |
|---|---|---|---|
| `skeleton` | ngay khi bấm | mọi phần mã dựng, gồm `prerequisites[].recall`, `why`, `next_up` | thêm trường |
| `progress` | khi bắt đầu lần sinh lại | `{"stage": "dang_viet_lai"}` | mới, tuỳ chọn; web có thể bỏ qua |
| `item` | **sau cổng** (mục 5.3): gửi một lượt các ý trong bộ đệm, rồi từng ý | `section_kind`, `item`; thêm `prereq_node_id` khi `section_kind = nhac_nen` | đổi thời điểm |
| `final` | hết | `status ∈ {ready, failed, no_source}`, có `failure` nếu `failed` | bỏ `fallback` |

Bất biến ghi vào spec, có test:
- Mọi ý trong các sự kiện `item` đều có trong `final`. Không sự kiện nào xoá ý đã gửi.
- `status = failed` thì không có sự kiện `item` nào trước đó.

### 6.7 Cache và thử lại

| mục | hiện tại | đề xuất |
|---|---|---|
| cache bài | ghi mọi giá trị trả về, kể cả `fallback` | chỉ ghi `ready` và `no_source` |
| cache âm | 60 giây, chỉ lỗi ném ra | giữ cho `api_tam_thoi` |
| bản ghi hỏng | không có | `khong_dat_luat`, `bi_chan`: `lecture_failure_ttl_seconds` (đề xuất 86.400) **[hỏi]** |
| thử lại truyền | 2 lần, chờ 1 và 2 giây, không nhiễu; timeout 60 giây mỗi lần | đường bấm: 1 lần, có nhiễu; tải trước: 2 lần, có nhiễu; trần cả lần bấm `lecture_deadline_seconds` (đề xuất 30) |
| sinh lại nội dung | 1 lần, cùng nhiệt độ | 1 lần; `lecture_repair_temperature` (đề xuất thử 1,0) **[hỏi]** |
| bị chặn | không phân biệt | 0 lần thử lại; ghi `finishReason` |
| ngân sách thử lại | không có | `retry_budget_ratio` (đề xuất 0,1 mỗi phút cho cả tiến trình) |

### 6.8 Cấu hình mới (`BSettings`, mục 15 spec)

| khoá | giá trị đề xuất | trong khoá cache |
|---|---|---|
| `lecture_prereq_note_max_syllables` | 35 | có |
| `lecture_assumed_known_phrases` | "như bạn đã biết", "như đã học", "bạn đã học", "nhớ lại rằng" | có |
| `lecture_max_next_up` | 2 | không (mã dựng, không vào prompt) |
| `edge_quote_display_max_chars` | 200 (bằng trần K3; thay số 120 của `_bounded_quote`) | không |
| `lecture_failure_ttl_seconds` | 86.400 | không |
| `lecture_deadline_seconds` | 30 | không |
| `lecture_transport_retries_interactive` / `_prefetch` | 1 / 2 | không |
| `lecture_repair_temperature` | 1,0 (thử) hoặc giữ 0 | có |
| `lecture_validator_version` | `lecture-validator-3` | có |

## 7. Câu hỏi mở cho chủ dự án

Mỗi câu kèm khuyến nghị và lý do ngắn, để dùng trong đợt tra hỏi.

**Bài hỏng hẳn**
1. **Khi bài hỏng, phần do mã dựng (vị trí, tên tiên quyết, câu định nghĩa nguyên văn kèm trang, hình đã xác nhận, khối "Tiếp theo") có
   được giữ không, hay cũng tính là "bản lùi"?**
   - Khuyến nghị: **giữ.** Phần này đã hiện ở `skeleton` trước mọi lời gọi, là dữ liệu đã kiểm từ đồ thị, không phải câu chọn bằng TextRank.
2. **Có cho nút "Đọc trang p trong sách" (mở PDF gốc đúng trang) khi bài hỏng không?**
   - Khuyến nghị: **có.** Nút này đưa người học về sách, không hiện câu nào thay bài giảng (PAIR: "return control to the user").
   - Cần quyết thêm: máy chủ có giữ PDF gốc không (câu 2 của báo cáo 2026-10-11).
3. **Stream: S1 (stream ngay), S2 (chờ cả bài) hay S3 (stream sau cổng K8)?**
   - Khuyến nghị: **S3**, kèm đổi K1, K6 để sau cổng không gì làm bài hỏng. Bảo đảm không bao giờ rút lại ý đã hiện.
   - Nếu đo thấy khoảng cách cổng → hết bài dưới 1 giây ở p50 thì chọn S2 cho đơn giản.
4. **Sinh lại tự động mấy lần?**
   - Khuyến nghị: **1 lần**, như hiện tại. Lần thứ hai thêm khoảng 28% tiền mỗi bài, chỉ giảm khoảng 7 điểm tỉ lệ hỏng, và đẩy đường hỏng
     qua 10 giây (mục 5.4).
5. **Lần sinh lại có đổi nhiệt độ sang mặc định 1,0 không?**
   - Khuyến nghị: **thử ở lượt đo kế tiếp, so với giữ 0.** Ở nhiệt độ 0, lần sửa chỉ cứu 1/6 bài; Google khuyên giữ mặc định cho Gemini 3.
6. **Bài hỏng vì luật kiểm có ghi bản ghi hỏng 24 giờ (bấm lại trả "chưa tạo được" ngay, 0 USD) không?**
   - Khuyến nghị: **có.** Thử lại cùng ngữ cảnh gần như chắc hỏng lại. Sửa prompt hay luật thì khoá đổi và bài tự sinh lại.
7. **Trên đường bấm-chờ, đặt trần 30 giây cho cả lần bấm và chỉ 1 lần thử lại ở tầng truyền?**
   - Khuyến nghị: **có.** Hiện ca xấu nhất là 3 × 60 giây ở tầng truyền, nhân 2 lần sinh. Tải trước chạy nền giữ 2 lần thử.

**Nhắc nền**

8. **Câu nối "dùng tới ra sao" do LLM viết (khoảng +0,0003 USD mỗi bài) hay chỉ hiện phần mã dựng (0 USD)?**
   - Khuyến nghị: **LLM viết, một câu, bám câu trích cạnh.** Câu nối là phần có giá trị nhất (P9, P13), và chi thêm nhỏ (15–25% một lời
     gọi).
9. **Thiếu câu nối (K10) thì làm gì?**
   - Khuyến nghị: **hiện dòng mã dựng, không sinh lại cả bài.** Sinh lại vì một câu nối thì đắt hơn giá trị nó đem lại.
10. **Câu neo của tiên quyết ("Nhớ lại định nghĩa") mặc định gập hay mở?**
    - Khuyến nghị: **gập.** Người đã biết bỏ qua được (expertise reversal); người chưa biết bấm để xem (gợi nhớ có phản hồi).
11. **Tiên quyết ở đồ thị cũ (`legacy_excerpt`, không có câu trích cạnh): chỉ hiện tên và vị trí, hay chạy lại ba cuốn cũ bằng chuỗi gộp?**
    - Khuyến nghị: **ở bài giảng, chỉ hiện tên, vị trí và câu neo; không câu nối, không nút "vì sao?".** Việc chạy lại nhap-mon-ml,
      naive-bayes, doc-6 là việc của phía pha A; báo cáo này không ước chi phí phần đó.
12. **Ý nhắc nền có bắt buộc `quote` không (bỏ đi thì bớt khoảng 0,0001 USD mỗi bài)?**
    - Khuyến nghị: **bắt buộc ở bản đầu**, để K3 biết câu nối bám đoạn nào trong câu trích cạnh. Xem lại sau lượt chấm người.
13. **Đổi câu dẫn thành "Bài này dùng tới" và ghi chú "ở module m" thay cho "đã học ở module m"?**
    - Khuyến nghị: **có**, vì hệ thống không biết người học đã học hay chưa.

**Gợi mở và hợp đồng**

14. **Khối "Tiếp theo": mã dựng 1–2 dòng có câu trích (0 USD), hay LLM viết câu gợi mở (phương án B)?**
    - Khuyến nghị: **mã dựng.** Bằng chứng cho gợi mở cuối bài yếu nhất; LLM viết thì thêm tiền và thêm rủi ro nối sai.
15. **Nâng hợp đồng lên `lecture-2` (đổi `note` → `recall` và `bridge`, `used_later` → `next_up`, bỏ `fallback`, thêm `failure`)?**
    - Khuyến nghị: **có, trước khi nhóm web dựng trang bài giảng.** Đổi sau sẽ tốn công hai lần.

## 8. Nguồn

Mọi nguồn truy cập ngày **2026-10-18**. Siêu dữ liệu kiểm qua Crossref, OpenAlex, ERIC hay arXiv. Mức đọc ghi sau mỗi nguồn. Nguồn đã có
ở [báo cáo 2026-10-11](nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md) mục 8 (Merrill, Ausubel 1960, Mayer & Moreno 2003, Kalyuga 2003,
Roediger & Karpicke 2006, Dunlosky 2013, ALCE, STORM, Shi 2023, tài liệu Gemini về structured output) không ghi lại.

**Advance organizer và kiến thức nền**
- [P1] J. Luiten, W. Ames, G. Ackerson, "A meta-analysis of the effects of advance organizers on learning and retention," *Am. Educ. Res. J.*,
  vol. 17, no. 2, pp. 211–218, 1980. https://doi.org/10.3102/00028312017002211 — tóm tắt ERIC EJ233231; **đọc toàn văn** bản báo cáo 1979
  (ERIC ED171803, https://files.eric.ed.gov/fulltext/ED171803.pdf), Bảng 1–6. Số trong bài lấy từ bản 1979; chưa đối chiếu bản AERJ.
- [P2] C. L. Stone, "A meta-analysis of advance organizer studies," *J. Exp. Educ.*, vol. 51, no. 4, pp. 194–199, 1983.
  https://doi.org/10.1080/00220973.1983.11011862 — **chỉ đọc tóm tắt** bản 1982 (ERIC ED220476). Không có số ES.
- [P3] R. E. Mayer, "Twenty years of research on advance organizers: Assimilation theory is still the best predictor of results," *Instr.
  Sci.*, vol. 8, no. 2, pp. 133–167, 1979. https://doi.org/10.1007/BF00117008 — **đọc toàn văn phần kết luận** bản báo cáo 79-1 (ERIC
  ED206691, https://files.eric.ed.gov/fulltext/ED206691.pdf).
- [P4] B. R. Barnes, E. U. Clawson, "Do advance organizers facilitate learning? …," *Rev. Educ. Res.*, vol. 45, no. 4, pp. 637–659, 1975.
  https://doi.org/10.3102/00346543045004637; J. T. Lawton, S. K. Wanska, *Rev. Educ. Res.*, 1977 (ERIC EJ166909); D. P. Ausubel, "In
  defense of advance organizers: A reply to the critics," *Rev. Educ. Res.*, 1978 (ERIC EJ189544); R. E. Mayer, "Can advance organizers
  influence meaningful learning?," *Rev. Educ. Res.*, 1979 (ERIC EJ205675); J. E. McEneany, *J. Res. Dev. Educ.*, 1990 (ERIC EJ407863) —
  **chỉ đọc tóm tắt ERIC**.
- [P5] R. E. Mayer, B. K. Bromage, "Different recall protocols for technical texts due to advance organizers," *J. Educ. Psychol.*, vol. 72,
  no. 2, pp. 209–225, 1980. https://doi.org/10.1037/0022-0663.72.2.209 — tóm tắt ERIC EJ229165; R. E. Mayer, "Can advance organizers
  counter the effects of text organization?," 1978 (ERIC ED154376) — **chỉ đọc tóm tắt**.
- [P6] B. A. Simonsmeier, M. Flaig, A. Deiglmayr, L. Schalk, M. Schneider, "Domain-specific prior knowledge and learning: A meta-analysis,"
  *Educ. Psychol.*, vol. 57, no. 1, pp. 31–54, 2022. https://doi.org/10.1080/00461520.2021.1939700 — **đọc tóm tắt** trên bản PDF của tác
  giả (https://www.uni-trier.de/fileadmin/fb1/prof/PSY/PAE/Team/Schneider/SimonsmeierEtAl2021.pdf).
- [P7] F. Dochy, M. Segers, M. M. Buehl, "The relation between assessment practices and outcomes of studies: The case of research on prior
  knowledge," *Rev. Educ. Res.*, vol. 69, no. 2, pp. 145–186, 1999. https://doi.org/10.3102/00346543069002145 — tóm tắt Crossref; F. J. R.
  C. Dochy, báo cáo 1988 (ERIC ED387486) — **chỉ đọc tóm tắt**.
- [P8] D. D. N. M. Kostons, G. P. C. van der Werf, "The effects of activating prior topic and metacognitive knowledge on text comprehension
  scores," *Br. J. Educ. Psychol.*, vol. 85, no. 3, pp. 264–275, 2015. https://doi.org/10.1111/bjep.12069 — **chỉ đọc tóm tắt**.
- [P9] D. E. Alvermann, C. R. Hynd, "Effects of prior knowledge activation modes and text structure on nonscience majors' comprehension of
  physics," *J. Educ. Res.*, vol. 83, no. 2, pp. 97–102, 1989. https://doi.org/10.1080/00220671.1989.10885937 — **chỉ đọc tóm tắt**.
- [P13] D. S. McNamara, E. Kintsch, N. B. Songer, W. Kintsch, "Are good texts always better? …," *Cogn. Instr.*, vol. 14, no. 1, pp. 1–43,
  1996. https://doi.org/10.1207/s1532690xci1401_1 — **chỉ đọc tóm tắt**.

**Pre-training, signaling, expertise reversal**
- [P10] R. E. Mayer, J. Pilegard, "Principles for managing essential processing in multimedia learning: Segmenting, pre-training, and
  modality principles," in *The Cambridge Handbook of Multimedia Learning*, 2nd ed., 2014.
  https://doi.org/10.1017/cbo9781139547369.016 — **chỉ đọc đoạn trích tóm tắt qua kết quả tìm kiếm**; trang Cambridge trả 429.
- [P11] D. Alpizar, O. O. Adesope, R. M. Wong, "A meta-analysis of signaling principle in multimedia learning environments," *Educ. Technol.
  Res. Dev.*, vol. 68, no. 5, pp. 2095–2119, 2020. https://doi.org/10.1007/s11423-020-09748-7 — **đọc tóm tắt** trên trang Springer;
  J. Richter, K. Scheiter, A. Eitel, "Signaling text-picture relations in multimedia learning: A comprehensive meta-analysis," *Educ. Res.
  Rev.*, vol. 17, pp. 19–36, 2016. https://doi.org/10.1016/j.edurev.2015.12.003 — số r = 0,17 đọc qua tóm tắt chép trên trang dữ liệu
  b2find (**nguồn thứ cấp**). S. Schneider và cộng sự, *Educ. Res. Rev.* 23, 2018 (https://doi.org/10.1016/j.edurev.2017.11.001) — không
  đọc được tóm tắt, không dẫn số.
- [P12] L. Tetzlaff, B. A. Simonsmeier, T. Peters, G. Brod, "A cornerstone of adaptivity – A meta-analysis of the expertise reversal effect,"
  *Learn. Instr.*, vol. 98, Art. no. 102142, 2025. https://doi.org/10.1016/j.learninstruc.2025.102142 — **đọc tóm tắt** (OpenAlex);
  S. Kalyuga, "Expertise reversal effect and its implications for learner-tailored instruction," *Educ. Psychol. Rev.*, vol. 19, no. 4,
  pp. 509–539, 2007. https://doi.org/10.1007/s10648-007-9054-3 — chỉ kiểm siêu dữ liệu.

**Gợi nhớ, hỏi trước, giá trị sử dụng**
- [P14] C. A. Rowland, "The effect of testing versus restudy on retention: A meta-analytic review of the testing effect," *Psychol. Bull.*,
  vol. 140, no. 6, pp. 1432–1463, 2014. https://doi.org/10.1037/a0037559 — **đọc toàn văn** phần phương pháp và kết quả (bản PDF trên
  courseware.epfl.ch).
- [P15] O. O. Adesope, D. A. Trevisan, N. Sundararajan, "Rethinking the use of tests: A meta-analysis of practice testing," *Rev. Educ.
  Res.*, vol. 87, no. 3, pp. 659–701, 2017. https://doi.org/10.3102/0034654316689306 — **chỉ đọc tóm tắt** (không có số); P. K. Agarwal,
  L. Nunes, J. R. Blunt, "Retrieval practice consistently benefits student learning…," *Educ. Psychol. Rev.*, vol. 33, no. 4, pp.
  1409–1453, 2021. https://doi.org/10.1007/s10648-021-09595-9 — **đọc tóm tắt**.
- [P16] S. C. Pan, S. K. Carpenter, "Prequestioning and pretesting effects: A review of empirical research, theoretical perspectives, and
  implications for educational practice," *Educ. Psychol. Rev.*, vol. 35, no. 4, 2023. https://doi.org/10.1007/s10648-023-09814-5 —
  **đọc tóm tắt**.
- [P17] C. S. Hulleman, J. M. Harackiewicz, "Promoting interest and performance in high school science classes," *Science*, vol. 326,
  no. 5958, pp. 1410–1412, 2009. https://doi.org/10.1126/science.1177067; E. A. Canning, J. M. Harackiewicz, "Teach it, don't preach it…,"
  *Motiv. Sci.*, vol. 1, no. 1, pp. 47–71, 2015. https://doi.org/10.1037/mot0000015 — **chỉ đọc tóm tắt**.

**Sản phẩm và giáo trình** (trang của chính sản phẩm)
- OpenStax, *Elementary Algebra 2e*, mục 2.1 và lời tựa; *Intermediate Algebra 2e*, lời tựa. https://openstax.org/books/elementary-algebra-2e/pages/2-1-solve-equations-using-the-subtraction-and-addition-properties-of-equality ;
  https://openstax.org/books/elementary-algebra-2e/pages/preface ; https://openstax.org/books/intermediate-algebra-2e/pages/preface
- M. Boelkins, *Active Calculus*, "Features of the Text." https://activecalculus.org/single/frontmatter-6.html
- Khan Academy (nhân viên đăng ở trang trợ giúp), "Update: Introducing Get Ready for Grade Level Math Courses!", 2020-06-16.
  https://support.khanacademy.org/hc/en-us/community/posts/360068507371 ; "Content Update: New Get ready for AP Calculus & Get ready for AP
  Statistics Courses", 2021-05-06. https://support.khanacademy.org/hc/en-us/community/posts/360077988172 — bài thứ hai chỉ đọc được câu đầu
  (lần tải sau bị chặn bởi trang kiểm trình duyệt).
- Brilliant, "Course placement guide" (cập nhật 2026-10-07), "What are Learning Paths?", "Who is Brilliant for?".
  https://brilliant.org/help/parents-and-families/course-placement-guide/ ; https://brilliant.org/help/features/what-are-learning-paths ;
  https://brilliant.org/help/using-brilliant/who-is-brilliant-for
- Coursera, trang khoá "Machine Learning" (https://www.coursera.org/learn/machine-learning) và blog "Introducing Coursera's new course
  preview experience" (https://blog.coursera.org/introducing-courseras-new-course-preview-experience) — chỉ đọc nhãn trên trang; blog chỉ
  đọc qua đoạn trích tìm kiếm.
- ALEKS, "The Research Behind ALEKS", "Overview." https://www.aleks.com/about_aleks/research_behind ; https://www.aleks.com/about_aleks/overview

**LLM, đồ thị kiến thức, kiểm trích dẫn**
- A. Slobodkin, E. Hirsch, A. Cattan, T. Schuster, I. Dagan, "Attribute first, then generate: Locally-attributable grounded text
  generation," in *Proc. 62nd ACL*, 2024, pp. 3309–3344. https://aclanthology.org/2024.acl-long.182/ — **đọc tóm tắt** (arXiv 2403.17104).
- L. Tang, P. Laban, G. Durrett, "MiniCheck: Efficient fact-checking of LLMs on grounding documents," in *Proc. EMNLP*, 2024, pp.
  8818–8847. https://aclanthology.org/2024.emnlp-main.499/ — **đọc tóm tắt** (arXiv 2404.10774).
- P. Ocheja, B. Flanagan, Y. Dai, H. Ogata, "How good is ChatGPT in giving adaptive guidance using knowledge graphs in e-learning
  environments?," arXiv:2412.03856, 2024. https://arxiv.org/abs/2412.03856 — **đọc tóm tắt**; bản arXiv, chưa thấy nơi đăng.
- Google Cloud, "Check grounding with RAG," cập nhật 2026-10-13. https://cloud.google.com/generative-ai-app-builder/docs/check-grounding —
  **đọc trang**.
- Không tìm thấy nghiên cứu nào sinh trọn bài giảng từ đồ thị tiên quyết rồi đánh giá trên người học (tìm 2026-10-18; báo cáo 2026-10-11 cũng
  ghi như vậy).

**Thiết kế khi AI hỏng, giây chờ**
- Google PAIR, *People + AI Guidebook*, "Errors + Graceful Failure." https://pair.withgoogle.com/chapter/errors-failing/ — **đọc trang**.
- S. Amershi *et al.*, "Guidelines for human-AI interaction," in *Proc. CHI*, 2019, pp. 1–13. https://doi.org/10.1145/3290605.3300233 —
  **đọc tóm tắt và bảng 18 nguyên tắc** (PDF trên trang Microsoft Research). Trang HAX Toolkit không tải được nội dung.
- J. Nielsen, "Response times: The 3 important limits," NN/g, 1993. https://www.nngroup.com/articles/response-times-3-important-limits/
- K. Sherwin, "Progress indicators make a slow system less insufferable," NN/g, 2014. https://www.nngroup.com/articles/progress-indicators/
- S. Tankala, "Skeleton screens 101," NN/g, 2023, rà lại 2026-09-02. https://www.nngroup.com/articles/skeleton-screens/
- B. A. Myers, "The importance of percent-done progress indicators for computer-human interfaces," in *Proc. CHI*, 1985, pp. 11–17.
  https://doi.org/10.1145/317456.317459 — **chỉ đọc tóm tắt**.
- C. Harrison, B. Amento, S. Kuznetsov, R. Bell, "Rethinking the progress bar," in *Proc. UIST*, 2007, pp. 115–118.
  https://doi.org/10.1145/1294211.1294231 — **chỉ đọc tóm tắt**.
- T. Mejtoft, A. Långström, U. Söderström, "The effect of skeleton screens," in *Proc. ECCE*, 2018, pp. 1–4.
  https://doi.org/10.1145/3232078.3232086 — **chỉ đọc tóm tắt**.
- NVIDIA, "Stream smarter and safer: Learn how NVIDIA NeMo Guardrails enhance LLM output streaming," NVIDIA Technical Blog.
  https://developer.nvidia.com/blog/stream-smarter-and-safer-learn-how-nvidia-nemo-guardrails-enhance-llm-output-streaming/ — **đọc trang**.
- Không tìm thấy nghiên cứu có đối chứng so stream từng ý với hiện cả bài cho văn bản LLM sinh.

**Thử lại, lỗi, giá**
- Google, Gemini API "Troubleshooting" và "API errors," cập nhật 2026-10-13. https://ai.google.dev/gemini-api/docs/troubleshooting ;
  https://ai.google.dev/gemini-api/docs/api-errors
- Google, Gemini API "Billing" (mục "Am I charged for failed requests?"). https://ai.google.dev/gemini-api/docs/billing
- Google, Gemini API "Pricing," cập nhật 2026-10-16: `gemini-3.1-flash-lite` 0,25 USD vào, 1,50 USD ra cho 1 triệu token (gồm token suy
  nghĩ). https://ai.google.dev/gemini-api/docs/pricing
- M. Brooker, "Timeouts, retries, and backoff with jitter," Amazon Builders' Library.
  https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
- Google, *Site Reliability Engineering*, ch. 22 "Addressing cascading failures." https://sre.google/sre-book/addressing-cascading-failures/

**Tài liệu, mã và dữ liệu nội bộ (chỉ đọc)**
- [Spec Pha B](../doc/pha-b-spec.md) mục 6, 8, 13, 15; [nghiên cứu bài giảng 2026-10-11](nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md);
  [kiểm thử Pha B 2026-10-18](kiem-thu-pha-b-2026-10-18.md) mục 3.2; [SA-26](../task/sau-a10/26-bai-giang-chong-lap-ban-lui-sach.md).
- Mã: `src/doc2roadmap/application/phase_b/lectures.py` (`_assemble`, `_trim_context`, `_valid_item`, `make`);
  `src/doc2roadmap/domain/learning_graph.py` (`why_here`, `traverse`, `_edge_citation`, `_bounded_quote`);
  `src/doc2roadmap/domain/phase_b_limits.py`; `src/doc2roadmap/infrastructure/artifacts/phase_b_store.py` (`single_flight`);
  `src/doc2roadmap/infrastructure/llm/phase_b.py` (`_request`). Đọc trên cây làm việc 2026-10-18, có tệp đang được sửa song song.
- Dữ liệu: `tmp/phaseb-live-group2-v2.json` (trường `operations`, `usage_rows`); `artifacts/graph/{doc-1/v53, xstk-ch3-1/v64, doc-4/v23,
  nhap-mon-ml/v46, naive-bayes/v45, doc-6/v17}/graph.json`. Không mở tập giữ lại, `d02-tap-khoa` hay phần `cache` của
  `artifacts/phase_b/live.json`.
