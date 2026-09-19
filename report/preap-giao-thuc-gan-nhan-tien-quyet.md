# PREAP — giao thức gán nhãn quan hệ tiên quyết theo giáo trình

2026-09-16 · Phục vụ vé [`task/a6-a8-tien-quyet/04`](../task/a6-a8-tien-quyet/04-bo-vang-excel-va-huong-dan-gan.md) ·
Liên quan: ADR [0009](../doc/adr/0009-nhan-vang-tien-quyet-bam-van-ban.md), spec
[A6–A8](../doc/A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md) mục D13, hướng dẫn cho người gán
[`doc/huong-dan-gan-nhan-tien-quyet.md`](../doc/huong-dan-gan-nhan-tien-quyet.md)

**Nguồn chính:** C. Alzetta, I. Torre, F. Koceva. *Annotation Protocol for Textbook Enrichment with Prerequisite
Knowledge Graph.* Technology, Knowledge and Learning **29**, 197–228 (2024; đăng trực tuyến 21/9/2023).
[doi:10.1007/s10758-023-09682-6](https://doi.org/10.1007/s10758-023-09682-6). Bài mở theo **CC BY 4.0**. Báo cáo này
đọc **toàn văn** bài đó. Mọi con số dưới đây lấy từ toàn văn, trừ chỗ ghi khác. Câu mở đầu bằng *Nhận xét:* là ý
kiến của người viết báo cáo này, không phải của tác giả PREAP.

---

## Tóm tắt

- **PREAP** (*PRErequisite Annotation Protocol*) là một giao thức để **người** gán nhãn quan hệ tiên quyết giữa các
  khái niệm **trong một giáo trình cụ thể**, sao cho bộ dữ liệu làm ra đáng tin, so sánh được và dùng lại được.
- Ý tưởng cốt lõi là **gán theo giáo trình, trong lúc đọc** (*textbook-driven in-context annotation*): người gán ghi
  quan hệ dựa trên **cách tác giả sách trình bày**, không dựa trên hiểu biết riêng của họ.
- So với hai cách gán thủ công khác trên năm đoạn giáo trình, PREAP cho **độ đồng thuận κ 0,45–0,71**, so với
  0,16–0,60 (gán mọi cặp theo hiểu biết) và 0,01–0,27 (gán mọi cặp có kèm văn bản). Nó **nhanh hơn 43% và 29%**, và
  được giáo viên chấm **chính xác hơn** và **khớp văn bản hơn** một cách có ý nghĩa thống kê. Độ đầy đủ thì ngang nhau.
- Hai phương pháp tự động (RefD, burst analysis) kém xa cả ba cách thủ công.
- Trong một dự án thật trên một chương 20.964 token, bốn người gán đạt κ trung bình 0,60, lên 0,62 sau rà soát; hơn
  một nửa số quan hệ được rà soát bị sửa hoặc xoá.
- **Với doc2roadmap**, PREAP giải đúng vấn đề của 2b: rubric 2b đòi bằng chứng trong tài liệu, nên bộ vàng cũng phải
  bám tài liệu. Dự án giữ các nguyên tắc cốt lõi của PREAP và đổi một số chi tiết cho hợp hoàn cảnh (mục 11).

---

## 1. PREAP giải bài toán gì

### 1.1 Quan hệ tiên quyết và đồ thị tiên quyết

Bài lấy định nghĩa của Liang et al. (2017): **quan hệ tiên quyết** (*prerequisite relation*, PR) là một quan hệ
phụ thuộc hai ngôi giữa một **khái niệm tiên quyết** và một **khái niệm đích**, trong đó khái niệm tiên quyết phải
được biết thì mới hiểu được khái niệm đích. Ký hiệu B ≺ C đọc là *"B là tiên quyết của C"*. Ví dụ của bài: *phép
cộng* ≺ *phép nhân*.

Tập quan hệ tiên quyết của một giáo trình vẽ được thành **đồ thị tiên quyết** (*PR graph*): node là khái niệm, cạnh
là quan hệ tiên quyết — gần với *educational concept map*.

Bài giữ ba tính chất hình thức:

| Tính chất | Nghĩa |
|---|---|
| Không phản xạ | A ≺ B thì A khác B |
| Bất đối xứng | A ≺ B thì không thể có B ≺ A |
| Bắc cầu | A ≺ B và B ≺ C thì A ≺ C |

Nhờ tính bắc cầu, PREAP **không bắt** người gán ghi các cạnh suy ra được; chúng được giữ ngầm. Nhờ tính bất đối
xứng, các cặp ngược chiều được suy là không phải tiên quyết.

### 1.2 "Khái niệm" là gì trong PREAP

Khái niệm được gắn với **thuật ngữ**: đơn vị từ vựng một hay nhiều từ, nghĩa không mơ hồ trong ngữ cảnh — cụ thể là
**cụm danh từ** mang nghĩa chuyên ngành. Sổ tay gán nhãn mô tả khái niệm là *"viên gạch của việc học, thứ học sinh
phải hiểu để nắm một môn"*; có thể rộng (*đại số*) hoặc rất hẹp (*bán kính*, *mẫu số của phân số*).

### 1.3 Vấn đề của các bộ vàng tiên quyết trước PREAP

Theo bài:

- **Độ đồng thuận thấp.** Nhiều bộ công bố có κ khoảng 0,30 (bài dẫn Chaplot et al. 2016, Fabbri et al. 2018).
- **Không có quy trình tái lập được.** Bộ dữ liệu ít được mô tả; hướng dẫn gán thường không có, hoặc chỉ là một định
  nghĩa ngây thơ về quan hệ tiên quyết.
- **Gán theo hiểu biết của người gán, không theo văn bản.** Cách phổ biến là cho chuyên gia hay nghiên cứu sinh gán
  **mọi cặp** trong một danh sách khái niệm cho trước (hoặc một mẫu ngẫu nhiên các cặp), dựa vào hiểu biết chuyên
  môn, cùng lắm tra một bộ tài liệu khi phân vân. Cách đó không nhìn vào việc khái niệm được sắp xếp thế nào trong
  một văn bản cụ thể.
- **Khó so sánh.** Các bộ gán nhãn cho những thứ rất khác nhau: môn đại học, MOOC, video, trang Wikipedia, thuật ngữ
  trong văn bản…

Tác giả nói rõ hai hướng gán **bổ sung cho nhau**: gán theo miền, không bám văn bản, hợp với hệ gia sư dùng cho mọi
giáo trình; gán theo giáo trình hợp với việc làm dữ liệu huấn luyện và kiểm cho công cụ xử lý văn bản, vì mỗi ví dụ
phải gắn được với một đoạn văn.

### 1.4 Hai mục tiêu của PREAP

1. Một quy trình kỹ nghệ tri thức cho việc gán tiên quyết và tạo bộ dữ liệu, để giảm mơ hồ của nhiệm vụ gán, từ đó
   có bộ dữ liệu đáng tin và nhất quán hơn.
2. Một quy trình **gán theo giáo trình**: gán khái niệm và quan hệ **chỉ dựa trên nội dung văn bản**, để làm lộ ra
   nguyên tắc thiết kế bài giảng nằm dưới cách tác giả tổ chức nội dung.

---

## 2. Giao thức được thiết kế thế nào

- Khung phương pháp: **MATTER** (Pustejovsky 2006; Ide & Pustejovsky 2017), một vòng lặp để làm kho ngữ liệu gán
  nhãn cho học máy; tác giả dùng nhất là phần khuyến nghị về định nghĩa mô hình và định nghĩa nhiệm vụ gán.
- Vòng thiết kế bốn bước: **định nghĩa → thử → đánh giá → sửa**. Đánh giá gồm cả định lượng (đồng thuận, phân tích
  bộ dữ liệu) lẫn định tính (nhóm thảo luận với người gán) để tìm chỗ hướng dẫn chưa rõ.
- **Ba vòng, khoảng hai năm.** Mỗi vòng dùng cùng một giáo trình nhập môn khoa học máy tính (Brookshear & Brylow
  2015), với **bốn học viên cao học ngành khoa học máy tính, khác nhau ở mỗi vòng**.
- Cuối cùng là một đợt đánh giá với chuyên gia giáo dục (mục 5).
- Để phục vụ việc thử và đánh giá, nhóm làm công cụ **PRAT** (mục 9).

---

## 3. Bốn nhóm việc của một dự án gán nhãn theo PREAP

Một dự án PREAP có người (hoặc nhóm) **quản lý dự án** và các **người gán**. Giao thức đặc tả bốn nhóm việc.

### 3.1 Quản lý dự án

Người quản lý quyết:

1. **Mục tiêu và đặc điểm gán:** dự án làm ra để dùng vào việc gì, miền nào, ngôn ngữ nào.
2. **Chọn giáo trình, và công cụ gán** nếu có.
3. **Tuyển và huấn luyện người gán:** người gán phải đủ chuyên môn để hiểu nội dung sách; có một **đợt gán thử** để
   huấn luyện và kiểm họ đã hiểu hướng dẫn chưa.
4. **Điều phối** các việc còn lại, đặc biệt là việc tạo bộ vàng.

### 3.2 Gán nhãn

**Sổ tay gán nhãn** gồm hai phần bổ sung cho nhau:

- **Annotation Guidelines (AG):** việc gán diễn ra thế nào.
- **Knowledge Elicitation Questions (KEQ):** câu hỏi và ví dụ để gỡ các ca phân vân.

Cả hai được đưa cho người gán trong đợt gán thử, và luôn mở được trong suốt quá trình gán. Việc gán có hai phần.

**(a) Gán khái niệm.** Có hai cách:

| Cách | Mô tả | Khuyến nghị của tác giả |
|---|---|---|
| **Tách riêng** (*autonomous*) | Danh sách khái niệm làm trước, bằng tay hoặc (bán) tự động, rồi đưa cho người gán | Nên có chuyên gia miền duyệt danh sách khi lấy tự động |
| **Đồng thời** (*simultaneous*) | Người gán vừa tìm khái niệm vừa gán quan hệ | Có vẻ tiết kiệm thời gian nhưng cho nhãn kém nhất quán, đồng thuận thấp hơn, phải rà soát nặng; chỉ dùng khi dự án cần bộ dữ liệu giàu hơn là nhất quán |

**(b) Gán quan hệ tiên quyết — trong ngữ cảnh.**

- Người gán ghi quan hệ **trong lúc đọc** văn bản giáo trình, **dựa vào lời giải thích trong sách**, không dựa vào
  hiểu biết của mình.
- Mục tiêu là ghi lại **quan điểm của tác giả sách**: khái niệm nào nên được trình bày, và trình bày thế nào, để học
  sinh hiểu được khái niệm đích. Đây là lý do gọi là *textbook-driven*.
- Phải giữ ba tính chất hình thức ở mục 1.1.
- **Không bắt gán các cặp không phải tiên quyết**, khác với các bộ dữ liệu gán mọi cặp.
- **Trọng số (đề xuất mở rộng):** gắn cho mỗi quan hệ một mức *mạnh* (sách trình bày tiên quyết là tuyệt đối cần) hay
  *yếu* (giúp hiểu sâu hơn nhưng không bắt buộc). Tác giả ghi rõ đây mới là bản nháp đang được đánh giá.
- KEQ đưa ví dụ về các quan hệ từ vựng thường **đi kèm** quan hệ tiên quyết — **từ hạ vị, từ thượng vị, quan hệ bộ
  phận–toàn thể** — và các quan hệ ngữ nghĩa như **nhân quả**, **thời gian**. Mục đích là tạo cách hiểu chung về quan
  hệ tiên quyết, không phải một danh sách luật.

### 3.3 Rà soát

Bài dẫn văn liệu cho thấy gán tay dễ sai, nên PREAP đòi một bước rà soát sau khi gán, cũng hai phần:

- **Rà soát khái niệm:** khi danh sách lấy (bán) tự động, nên có chuyên gia miền duyệt. Bài dẫn Chau et al. (2020a):
  chuyên gia cho nhãn chất lượng cao, ít bị các ca khó làm khó, và nhận ra lỗi tự động tốt hơn người ngoài ngành.
- **Rà soát quan hệ — trong ngữ cảnh:** người gán **đọc lại đoạn văn** chỗ mình đã ghi quan hệ rồi mới quyết giữ,
  xoá hay sửa. Mỗi người tự rà soát nhãn của mình.
- **Rà soát một phần:** vì rà soát tốn thời gian, có thể chỉ rà các cặp dễ sai nhất, tức **cặp có đồng thuận thấp**.
  Khi đó **không được cho người gán biết** tiêu chí chọn mẫu, để tránh rà soát thiên lệch. Nếu phát hiện khái niệm
  sai thì phải rà **mọi** quan hệ trực tiếp và gián tiếp dính tới khái niệm đó.

### 3.4 Sau khi gán: tạo bộ vàng

Người quản lý làm bốn việc:

1. **Đánh giá đồng thuận** (mục 4).
2. **Gộp nhãn** của các người gán theo một tiêu chí phù hợp.
3. **Rà soát bộ vàng sau khi gộp**, ví dụ tìm vòng trong đồ thị.
4. **Phát hành:** siêu dữ liệu và tài liệu mô tả, để chia sẻ và dùng lại.

Ba việc đầu không cần nếu chỉ có một người gán, nhưng bài không khuyến khích chỉ dùng một người.

**Gộp nhãn:**

| Cách | Khi nào hợp | Cái giá |
|---|---|---|
| **Hợp** (∪): lấy mọi quan hệ có ít nhất một người ghi | Khi cần phân tích mọi chỗ người gán thấy quan hệ, ví dụ tìm mẫu ngôn ngữ; hoặc khi người gán rất đáng tin và đã rà soát | Không nên dùng khi người gán ít kinh nghiệm hoặc chưa rà soát |
| **Giao** (∩): chỉ lấy quan hệ mọi người cùng ghi | Khi cần chắc chắn và đồng thuận cao | Bộ dữ liệu nhỏ hơn, nhất là khi đồng thuận thấp |
| **Thảo luận** | Bài coi đây là thực hành tốt khi làm được: người gán bàn các ca lệch để đi tới một đồ thị thống nhất (như Wang et al. 2021 làm cho khái niệm) | Tốn thời gian của người |

**Phát hành:** PREAP khuyên mô tả bộ dữ liệu theo nguyên tắc **Linked Data** của W3C (từ vựng chuẩn, định danh tài
nguyên bằng URI/IRI). Dự án mẫu dùng lớp `schema.org/Dataset` (dựa trên W3C Data Catalog Vocabulary), mã hoá
JSON-LD; các bộ dữ liệu còn được chú thích theo W3C Web Annotation Vocabulary.

---

## 4. Tính độ đồng thuận có kể bắc cầu

Đây là chi tiết kỹ thuật quan trọng nhất của PREAP khi dùng lại.

**Vấn đề.** Cohen κ thông thường chỉ so nhãn hai người đặt cho **cùng một mục**. Nó bỏ qua **đồng thuận ngầm** do
tính bắc cầu: người thứ nhất ghi A ≺ C, người thứ hai ghi A ≺ B và B ≺ C — thực chất họ đồng ý về A ≺ C, nhưng κ
thường sẽ tính là lệch. Bài cũng nhắc κ có điểm yếu khi phân bố lệch mạnh — đúng hoàn cảnh ở đây, vì cặp tiên quyết
hiếm.

**Luật của PREAP.** Hai người được coi là **đồng ý về A ≺ C** trong hai trường hợp: (i) cả hai cùng ghi A ≺ C;
(ii) một người ghi A ≺ C, người kia ghi A ≺ B và B ≺ C. Chú thích của bài: trong trường hợp (ii), hai người được coi
là đồng ý về A ≺ C, **nhưng không** đồng ý về A ≺ B hay B ≺ C.

**Cách tính:**

1. Lấy danh mục khái niệm T đã dùng khi gán.
2. Tập mục cần chấm P là **mọi cặp có thứ tự** trong T — gồm cả A ≺ B lẫn B ≺ A.
3. Với mỗi người gán, một cặp p là **dương** nếu người đó ghi tay, **hoặc suy ra được bằng bắc cầu** từ nhãn của họ;
   còn lại là âm.
4. Tính Cohen κ cho từng cặp người gán: κ = (P₀ − Pₑ) / (1 − Pₑ), trong đó P₀ là tỉ lệ cặp được hai người gán giống
   nhau trên mọi cặp, Pₑ là xác suất trùng do ngẫu nhiên.
5. Với cả nhóm người gán, dùng biến thể **Fleiss κ**.

*Ví dụ nhỏ (người viết báo cáo dựng để minh hoạ).* T = {A, B, C}, có 6 cặp có thứ tự. Người 1 ghi A ≺ B, B ≺ C, nên
sau bắc cầu có ba cặp dương: A ≺ B, B ≺ C, A ≺ C. Người 2 ghi A ≺ C và B ≺ C. Hai người cùng dương ở A ≺ C và B ≺ C,
cùng âm ở ba cặp ngược, và lệch ở A ≺ B. P₀ = 5/6.

Bài dẫn thang của Landis & Koch (1977) để đọc κ: mức *slight* ở các phương pháp gán mọi cặp, mức *moderate* và
*substantial* ở PREAP.

---

## 5. Đánh giá giao thức

### 5.1 Câu hỏi nghiên cứu

- **RQ1.1** — Quan hệ có được các người gán ghi **nhất quán** không? Đo bằng độ đồng thuận.
- **RQ1.2** — Bộ vàng sau khi gộp có **đầy đủ** và **chính xác** không? Đo bằng đánh giá của giáo viên.
- **RQ2** — Nhãn có **khớp văn bản** không, tức có đúng các khái niệm tiên quyết mà tác giả sách dùng để giải thích
  khái niệm đích? Đo bằng đánh giá của giáo viên, cộng mức **hữu ích** qua phỏng vấn.
- Cộng thêm **thời gian gán**.

### 5.2 Các phương pháp so sánh

| Mã | Loại | Cách làm |
|---|---|---|
| **PREAP** | thủ công | Như mục 3 |
| **MMP** | thủ công | Gán **mọi cặp** trong danh sách khái niệm cho trước, **theo hiểu biết** của người gán (theo Li et al. 2019) |
| **MMT** | thủ công | Như MMP nhưng **có văn bản** để kiểm. Tác giả tự dựng biến thể này vì không tìm được cách gán theo giáo trình nào trong văn liệu |
| **RefD** | tự động | Liang et al. (2015), dựa vào liên kết giữa các trang Wikipedia — tức tri thức ngoài văn bản |
| **Burst** | tự động | Adorni et al. (2019), dùng burst analysis để tìm đoạn văn nơi mỗi khái niệm nổi bật rồi khai thác mẫu thời gian giữa chúng |

Để công bằng, mọi phương pháp dùng **cùng một danh sách khái niệm**, lấy theo cách *tách riêng, bán tự động* của
PREAP.

### 5.3 Dữ liệu và người tham gia

**Năm đoạn văn**, trích từ giáo trình đại học dành cho sinh viên **không** học chuyên ngành đó:

| Miền | Token | Khái niệm | PR của PREAP | MMP | MMT | RefD | Burst |
|---|---:|---:|---:|---:|---:|---:|---:|
| Đại số | 253 | 23 | 22 | 287 | 161 | 68 | 28 |
| Thống kê | 243 | 14 | 25 | 73 | 93 | 23 | 9 |
| Sinh học | 135 | 23 | 24 | 124 | 95 | 86 | 27 |
| Hoá sinh | 286 | 16 | 29 | 108 | 97 | 37 | 49 |
| Khảo cổ | 208 | 18 | 25 | 115 | 114 | 0 | 17 |

Số quan hệ ở đây là của bộ vàng sau khi gộp bằng **hợp**. *Nhận xét:* gán mọi cặp cho ra nhiều gấp 3–13 lần số quan
hệ của PREAP trên cùng văn bản.

- **Người gán:** 6 người, hai người mỗi nhóm miền; trình độ sau đại học; 25–49 tuổi, trung bình 29,8. Mỗi người gán
  theo cả ba cách thủ công, **đổi thứ tự** để tránh thiên lệch. Tổng cộng 30 bộ nhãn cá nhân, gộp thành 15 bộ vàng.
- **Người đánh giá:** 12 giảng viên đại học chia theo miền (32–65 tuổi, trung bình 45,4) và một chuyên gia sư phạm
  (47 tuổi).

### 5.4 Cách giáo viên chấm

Mỗi giáo viên gặp riêng nhóm nghiên cứu, trung bình 130 phút. Họ có khoảng một giờ để xem các đồ thị, rồi đọc văn bản
nguồn và chấm, rồi phỏng vấn mở.

- **Độ đầy đủ:** giáo viên tự vẽ bản đồ tiên quyết như khi giảng cho học sinh (được xem các đồ thị và được sửa bản đồ
  của mình). Với mỗi quan hệ trong bản đồ đó: *tốt* nếu đồ thị được chấm có đường đi trực tiếp hoặc gián tiếp; *chấp
  nhận được* nếu hai khái niệm không nối nhưng nhất quán với đồ thị; không điểm nếu khác. Điểm được chuẩn hoá theo số
  quan hệ giáo viên vẽ rồi quy về **thang năm mức**.
- **Độ chính xác:** giáo viên chấm các **đường đi ba node** chọn ngẫu nhiên, thay vì từng cặp, cho khớp với tính bắc
  cầu. *Rất tốt* nếu cả hai cạnh đúng; *tốt* nếu một cạnh đúng, cạnh kia sai nhẹ nhưng nhất quán; *kém* nếu khác.
- **Khớp văn bản:** giáo viên đọc văn bản, ghi cho mỗi khái niệm các khái niệm tiên quyết **mà văn bản dùng để giải
  thích nó**, rồi kiểm các quan hệ đó có trong đồ thị không.
- **Hữu ích:** hỏi qua phỏng vấn.

### 5.5 Kết quả

**Độ đồng thuận và thời gian** (bảng 2 của bài):

| Miền | κ PREAP | κ MMP | κ MMT | Phút PREAP | Phút MMP | Phút MMT |
|---|---:|---:|---:|---:|---:|---:|
| Đại số | 0,60 | 0,17 | 0,23 | 20 (± 2,83) | 31,5 (± 9,20) | 24 (± 1,41) |
| Thống kê | 0,61 | 0,31 | 0,01 | 15 (± 2,83) | 18,5 (± 4,95) | 20 (± 0) |
| Sinh học | 0,71 | 0,60 | 0,27 | 13 (± 2,83) | 30 (± 7,07) | 23 (± 2,83) |
| Hoá sinh | 0,45 | 0,16 | 0,22 | 19 (± 1,41) | 35,5 (± 3,53) | 26,5 (± 2,12) |
| Khảo cổ | 0,53 | 0,22 | 0,22 | 21,5 (± 0,71) | 38,5 (± 2,12) | 31 (± 1,41) |

- PREAP đồng thuận cao hơn ở cả năm miền. Trừ sinh học với MMP, MMP và MMT chỉ ở mức *slight*; PREAP lên *moderate*
  và *substantial*.
- **Thời gian:** PREAP nhanh hơn **43%** so với MMP và **29%** so với MMT. ANOVA một chiều: F(2,27) = 12,57, η² = 0,48,
  p < 0,001. Tukey: PREAP–MMP p < 0,001; PREAP–MMT p = 0,027; MMP–MMT không có ý nghĩa (p = 0,080).

**Độ đầy đủ, độ chính xác, khớp văn bản** (phụ lục, bảng 6; điểm trung bình trên 15 lượt chấm, thang năm mức, giá
trị lớn nhất quan sát được là 4,0):

| Chỉ số | PREAP | MMP | MMT | RefD | Burst |
|---|---:|---:|---:|---:|---:|
| Đầy đủ | 3,2 (SD 0,2) | 3,2 (0,2) | 3,2 (0,2) | 0,6 (0,3) | 0,6 (0,3) |
| Chính xác | **3,5** (0,3) | 2,2 (0,4) | 2,6 (0,4) | 0,3 (0,3) | 0,4 (0,3) |

- **Đầy đủ:** Kruskal–Wallis χ²(4) = 53,98, p < 0,001. Mann–Whitney không thấy khác biệt giữa các cách thủ công; mỗi
  cách thủ công hơn mỗi cách tự động với p < 0,001, vẫn giữ sau hiệu chỉnh Bonferroni (α = 0,005).
- **Chính xác:** χ²(4) = 64,43, p < 0,001. PREAP hơn cả MMP và MMT (p < 0,001). Khác biệt MMP–MMT (p = 0,014) mất ý
  nghĩa sau Bonferroni.
- **Khớp văn bản:** χ²(4) = 65,63, p < 0,001. PREAP hơn MMP và MMT (p < 0,001); MMP khác MMT (p = 0,0027); giữ sau
  Bonferroni. Bản văn bản trích từ PDF chỉ đọc được 6/15 dòng của bảng này: ở 6 dòng đó PREAP được 3,2–3,7, MMP
  2,3–2,9, MMT 2,7–3,1, RefD 0,6–0,8, Burst 0,2–0,7. Báo cáo này không nêu trung bình của chỉ số này vì không đọc
  được đủ bảng.
- *Nhận xét:* bài viết "sáu phương pháp" ở phần kiểm định, nhưng bảng chỉ có năm và bậc tự do 4 ứng với năm nhóm.
- **Không thấy khác biệt lặp lại giữa các miền** ở bất kỳ chỉ số nào.

**Hữu ích** (phỏng vấn): 9/12 giáo viên cho rằng đồ thị tiên quyết gắn với văn bản **có tiềm năng rất hữu ích** cho
giáo dục; 3 người nói còn tuỳ nhiều yếu tố. 77% cho rằng nó hỗ trợ được người học; 85% cho rằng nó giúp giáo viên sắp
xếp nội dung bài giảng. Chuyên gia sư phạm lưu ý khó dùng trực tiếp đồ thị lớn, nên chia thành đồ thị con, và đồ thị
chỉ hữu ích khi chính xác.

### 5.6 Lỗi đặc trưng

- **Của PREAP — lỗi chính giáo viên tìm thấy:** khái niệm được **nhắc trong lúc giải thích** khái niệm khác bị gán
  thành tiên quyết, trong khi nó chỉ là giải thích bổ sung. Ví dụ: câu *"Đại số sơ cấp khác số học ở việc dùng trừu
  tượng, như dùng chữ thay cho số"* bị gán thành *đại số sơ cấp* là tiên quyết của *chữ* và *số*; ba giáo viên chỉ ra
  điều ngược lại mới đúng — chữ và số là tiên quyết của phép trừu tượng. Một ví dụ khác ở khảo cổ học khiến giáo viên
  nghi ngờ *đường viền ranh giới* là tiên quyết của *lớp trầm tích*.
- **Của MMP và MMT:** độ chính xác thấp hơn chủ yếu vì **đường đi không nhất quán**. Tác giả cho rằng việc phải xét
  từng cặp khiến người gán **tìm ra nhiều quan hệ hơn mức cần**; ví dụ giáo viên chấm sai hoặc chỉ tạm chấp nhận các
  quan hệ *sản phẩm* – *enzyme*, *sản phẩm* – *năng lượng hoạt hoá* trong bộ MMP hoá sinh.

---

## 6. Dự án mẫu

Tác giả áp dụng đủ quy trình ở vòng phát triển cuối.

**Quản lý dự án**

- Mục tiêu: bộ vàng để phân tích ngôn ngữ của các quan hệ tiên quyết, và để kiểm một hệ học tiên quyết tự động dựa trên
  đặc trưng ngôn ngữ.
- Văn bản: **chương 4, *Networking and the Internet*** của giáo trình Brookshear & Brylow (2015), **20.964 token, 780
  câu**. Công cụ: PRAT.
- Người gán: **bốn học viên cao học** khoa học máy tính — thạo nội dung nhưng chưa từng gán nhãn. Có huấn luyện: người
  quản lý giải thích hướng dẫn, mỗi người gán thử, rồi cả nhóm so và bàn các nhãn thử.

**Gán nhãn**

- Mỗi người gán **độc lập**, không hỏi nhau.
- Khái niệm: cách **tách riêng, bán tự động**. Văn bản qua phân tích hình thái–cú pháp (UDPipe) rồi trích thuật ngữ bằng
  nền tảng Text-To-Knowledge2, ra **185** thuật ngữ ứng viên. Người quản lý duyệt tay theo hướng dẫn PREAP: bỏ các mục
  không phải khái niệm (*busy channel*, *own network*, *term gateway*, *same machine*), thêm mục thiếu (*router*), còn
  **140** khái niệm.
- Quan hệ: gán trên PRAT. Người gán chọn **lần xuất hiện của khái niệm đích trong văn bản**, nhập khái niệm tiên quyết
  và trọng số. Mỗi quan hệ lưu kèm **mã câu** nơi khái niệm đích xuất hiện.

| Người gán | Số quan hệ | Mạnh | Yếu | Đã rà | Xoá | Sửa |
|---|---:|---:|---:|---:|---:|---:|
| A1 | 141 | 96,45% | 3,54% | 39 (27,66%) | 11 | 4 |
| A2 | 257 | 84,82% | 15,17% | 85 (33,07%) | 21 | 25 |
| A3 | 199 | 89,45% | 10,55% | 50 (25,12%) | 15 | 10 |
| A4 | 163 | 90,18% | 9,82% | 46 (28,22%) | 20 | 9 |

- Số quan hệ mỗi người khác nhau nhiều, nhưng tỉ lệ mạnh/yếu khá giống nhau.
- **Rà soát:** mỗi người chỉ rà các quan hệ **chỉ mình ghi**. Trong số đã rà, tỉ lệ bị xoá hoặc sửa lần lượt là 38,46%,
  54,12%, 50,00%, 63,04% — **trung bình hơn một nửa**. Tác giả dùng con số này để nhấn mạnh rà soát là bắt buộc.

**Đồng thuận và bộ vàng**

- Cohen κ theo cặp, trung bình **0,60** trước rà soát, **0,62** sau; tăng ở mọi cặp người gán. Fleiss κ **0,43 → 0,45**.
- Gộp bằng **hợp**: **385** cặp. Tác giả biện minh: mục tiêu là phân tích ngôn ngữ và huấn luyện; người gán thạo nội
  dung; đồng thuận đủ; đã rà soát. Trọng số không được dùng trong dự án này vì vẫn là đề xuất.
- **Rà soát bộ vàng:** dùng công cụ trực quan của PRAT để tìm **vòng** và **đường đi quá dài** sinh ra khi gộp, rồi
  giải bằng **thảo luận giữa các người gán** do người quản lý dẫn.
- **Phát hành:** kèm tài liệu, siêu dữ liệu `schema.org/Dataset` dạng JSON-LD.

---

## 7. Ba cách gán khái niệm, và tác dụng lên học máy

Tác giả chạy thêm hai dự án trên cùng văn bản, cùng cách gộp, mỗi dự án bốn người gán khác, chỉ khác cách gán khái
niệm.

| Cách | Bộ | Khái niệm | Quan hệ | κ |
|---|---|---:|---:|---:|
| Tách riêng, tự động | v1 | 185 | 2.252 | 0,40 |
| Tách riêng, bán tự động | v2 | 132 | 1.974 | 0,62 |
| Đồng thời, thủ công | v3 | 353 | 6.768 | 0,25 |

- v3 có thêm khái niệm do người gán tự thêm (đồng thuận trên khái niệm 0,71), nên lớn hơn hẳn — và **kém nhất quán
  nhất**.
- *Nhận xét:* bài nói v2 **là** dự án mẫu ở mục 6, nhưng số liệu khác (132 so với 140 khái niệm, 1.974 so với 385 quan
  hệ). Bài không giải thích. Có thể bảng này đếm cả quan hệ suy bằng bắc cầu, nhưng đó chỉ là suy đoán.

**Huấn luyện một mô hình học tiên quyết** (mô hình học sâu và thiết lập của Alzetta et al. 2019: đặc trưng từ vựng —
word embedding — và đặc trưng toàn cục — số lần xuất hiện, độ giống từ vựng — lấy từ văn bản thô, không dùng tri
thức ngoài; kiểm chéo 5 phần):

| Bộ | Precision | Recall | F1 | Accuracy |
|---|---:|---:|---:|---:|
| v1 | 83,75% | 87,85% | 85,71 | 85,34% |
| v2 | **87,87%** | **89,67%** | **88,73** | **88,60%** |
| v3 | 65,08% | 87,94% | 74,79 | 70,36% |

Cả ba vượt baseline Zero Rule (accuracy 50%, F1 66,66).

**Khuyến nghị rút ra:**

- **Tách riêng việc gán khái niệm**, trừ khi dự án cần bộ dữ liệu giàu hơn là nhất quán.
- Giữa tự động và bán tự động: bán tự động tốt hơn nhưng tốn thêm thời gian duyệt. Nếu mục tiêu là **dữ liệu huấn
  luyện**, lấy khái niệm tự động có thể chấp nhận được, vì người gán sẽ không nối quan hệ tới các mục không phải khái
  niệm. Nếu đồ thị **được dùng trực tiếp**, hoặc làm **đáp án để đánh giá**, thì độ đúng và độ nhất quán phải được
  ưu tiên.

---

## 8. Giới hạn

**Tác giả tự nêu:**

- Đã thử trên nhiều miền và không thấy khác biệt lặp lại, nhưng **không khẳng định** giao thức hợp mọi miền.
- **Trọng số** mạnh/yếu vẫn là đề xuất cần nghiên cứu thêm (người gán thì muốn có nó).
- Gán trên **nhiều giáo trình** cùng chủ đề rồi gộp sẽ hữu ích, nhưng cần chiến lược gộp cẩn thận.
- Cần thêm thí nghiệm về cách lấy khái niệm tự động, về cách hoà giải khi người gán sửa danh sách khái niệm, và về việc
  dùng người không chuyên để giảm chi phí.

**Nhận xét thêm của người viết báo cáo này:**

- Đợt đánh giá dùng **đoạn văn rất ngắn** (135–286 token, 14–23 khái niệm). Kết quả về thời gian và đồng thuận chưa
  chắc giữ nguyên trên cả một chương dài; dự án mẫu (20.964 token) có κ 0,60–0,62 nhưng không có số thời gian.
- Mỗi miền chỉ có **hai người gán**, và mỗi người gán cùng một văn bản theo ba cách (có đổi thứ tự). Lần gán sau có
  thể được lợi từ việc đã đọc văn bản.
- Bộ vàng của đợt đánh giá gộp bằng **hợp**, nên số quan hệ của MMP/MMT phình ra một phần do cách gộp.
- Mọi văn bản đánh giá là giáo trình **tiếng Anh**. Không có dữ liệu nào về tiếng Việt.
- Giáo viên chấm **sau khi đã xem các đồ thị**, và được sửa bản đồ của mình trong lúc xem.

---

## 9. Tài nguyên đi kèm

- **Kho GitHub** [`IntAIEdu/PRAT`](https://github.com/IntAIEdu/PRAT/) (theo mục 8 của bài): sổ tay gán nhãn cho người
  gán, đặc tả cho người quản lý dự án, dữ liệu và văn bản dùng khi đánh giá, dữ liệu dự án mẫu (danh sách khái niệm,
  bộ quan hệ, văn bản thô, siêu dữ liệu JSON-LD), dữ liệu thí nghiệm học máy, và công cụ PRAT.
- **Giấy phép:** bài báo mở theo CC BY 4.0. Theo báo cáo nghiên cứu vòng 29 (kiểm ở commit `4ea5bc4`), **kho mã không
  có tệp giấy phép**, nên dự án không chép mã hay tài liệu từ kho đó; chỉ dùng **giao thức** như bài báo mô tả.
- **PRAT** được mô tả riêng trong: C. Alzetta, I. Torre. *Prerequisite Relations Annotation Tool: Annotation and
  analysis of educational relations in texts.* Journal of the Association for Information Science and Technology
  **76**(7), 2025. [doi:10.1002/asi.24992](https://doi.org/10.1002/asi.24992) *(chỉ đọc abstract)*: công cụ gán quan
  hệ tiên quyết dựa trên một giao thức đã được kiểm chứng, giúp ghi, phân tích và trực quan hoá cấu trúc tiên quyết;
  có nghiên cứu người dùng với người dùng nhiều nền tảng khác nhau.

---

## 10. Vì sao PREAP quan trọng với doc2roadmap

1. **2b và bộ vàng phải đo cùng một thứ.** Rubric 2b chỉ cho tạo cạnh `requires` khi có **bằng chứng trong tài liệu**.
   Nếu bộ vàng được gán theo hiểu biết chuyên môn, như phần lớn bộ công bố, thì một hệ bịa cạnh từ kiến thức nền sẽ
   được thưởng. Báo cáo nghiên cứu vòng 29 dẫn Yang et al. (2024): GPT-4 không đọc văn bản nào vẫn vượt baseline có
   giám sát trên LectureBankCD. PREAP là giao thức duy nhất tìm được làm bộ vàng **bám văn bản**.
2. **Nó làm được phép đo "cạnh tiên quyết nằm ở đâu"** (E1). Mỗi quan hệ PREAP gắn với một chỗ trong sách, nên biết
   được cạnh vàng nằm trong cùng chunk, cùng mục, cùng chương hay xuyên chương.
3. **Nó cho trần chất lượng có số.** κ của PREAP (0,45–0,71; dự án mẫu 0,60–0,62) là mốc để đọc kết quả của 2b: chấm
   máy như một người gán thứ ba, so κ(máy, người) với κ(người, người).
4. **Nó rẻ hơn gán mọi cặp**, cả về thời gian lẫn độ nhiễu, đúng thứ dự án cần vì người gán là đường găng.
5. **Tiếng Việt chưa có bộ nào như vậy.** Một bộ vàng kiểu PREAP trên giáo trình tiếng Việt là đóng góp đứng được, dù
   cuối cùng dự án chọn luồng 2b nào.

---

## 11. Dự án áp dụng PREAP thế nào

| Điểm của PREAP | doc2roadmap | Lý do |
|---|---|---|
| Gán theo giáo trình, trong lúc đọc | **Giữ nguyên** | Cốt lõi của giao thức |
| Danh sách khái niệm tách riêng, bán tự động | **Giữ**: danh sách là node canonical học được của A3–A5; người gán không sửa danh sách mà **ghi cờ** | Đúng cách PREAP khuyên cho đồ thị dùng làm đáp án. Cờ vừa sửa danh sách, vừa làm mẫu kiểm A4 trên tài liệu mới |
| Không gán cặp không phải tiên quyết; cạnh bắc cầu để ngầm | **Giữ**; hướng dẫn nhắc chỉ ghi tiên quyết trực tiếp | — |
| Ba tính chất hình thức | **Giữ**, và **kiểm bằng code**: tự nối, cặp trùng, vòng mọi độ dài đều là lỗi | PREAP rà vòng bằng mắt trên PRAT; dự án kiểm tự động trên nhãn từng người |
| Trọng số mạnh/yếu | **Giữ, không bắt buộc**: cột *Mức cần* (Bắt buộc / Hữu ích) | PREAP còn coi là đề xuất; dự án chỉ dùng để phân tích thêm |
| Sổ tay AG + KEQ | Gộp thành **một** tài liệu hướng dẫn tiếng Việt, có mục ca khó theo tinh thần KEQ, với ví dụ học máy và thống kê | Hai người gán, một tài liệu dễ theo hơn |
| Đợt gán thử để huấn luyện | **Giữ**: gán thử vài trang của một chương **khác** chương làm vàng, so nhau với người quản lý, rồi bỏ nhãn thử (bước 0 của hướng dẫn) | Theo PREAP. Dùng chương khác để buổi bàn không làm lộ đáp án của chương vàng |
| Rà soát trong ngữ cảnh, từng người | **Giữ, bắt buộc, rà toàn bộ** nhãn của mình | Hai người, chương vừa phải: rà hết khả thi; PREAP cho thấy hơn một nửa số cạnh được rà bị sửa |
| Đo độ đồng thuận có kể bắc cầu | **Giữ nguyên** cách tính | Không có nó thì κ phạt oan cách ghi khác nhau của cùng một ý |
| Gộp bằng hợp (dự án mẫu) | **Đổi**: bộ vàng chính là kết quả **hội ý**; số trên hợp và giao báo cáo kèm | Bộ vàng dùng làm **đáp án để chấm**, nên cần đồng thuận; PREAP cũng coi thảo luận là thực hành tốt |
| Công cụ PRAT, gán trên văn bản | **Đổi**: file Excel sinh từ artifact; người gán đọc sách gốc | Kho PRAT không có giấy phép; Excel quen thuộc và chạy trên máy, không đưa nội dung sách lên dịch vụ ngoài |
| Quan hệ gắn với mã câu nơi khái niệm đích xuất hiện | **Đổi**: người gán ghi **vị trí trong sách** (trang, mục) | Người gán đọc sách giấy/PDF, không đọc bản đã cắt câu |
| Phạm vi: một đoạn văn hoặc một chương | **Mở rộng có kiểm soát**: khái niệm đích là khái niệm **dạy trong chương đã chọn**, khái niệm cần biết trước là **bất kỳ khái niệm nào của tài liệu** | Không có vậy thì mất đúng các cạnh xuyên chương mà E1 cần đo |
| — | **Thêm**: cột *Loại bằng chứng* (Nói rõ / Trong định nghĩa, cần để hiểu / Mạch trình bày) | Khớp với rubric 2b, nên so được máy và người theo từng loại bằng chứng |
| — | **Thêm**: gán **mù** với đầu ra của máy | PREAP không đặt ra tình huống này; ở dự án, máy chạy trước nên phải cấm xem |
| — | **Thêm**: ghi **thời gian** gán và rà soát ngay trong file | PREAP đo thời gian; dự án cần số thật trên chương dài, vì đánh giá của PREAP chỉ trên đoạn ngắn |
| Phát hành theo Linked Data | **Để sau**: bộ vàng lưu JSON có phiên bản artifact và mã danh sách khái niệm | Chưa có nhu cầu chia sẻ ra ngoài; nếu công bố thì bổ sung siêu dữ liệu |

---

## 12. Rủi ro khi áp dụng, và cách đỡ

| Rủi ro | Vì sao | Cách đỡ |
|---|---|---|
| Danh sách khái niệm do máy làm kéo lệch bộ vàng | Khái niệm máy bỏ sót thì không thể thành cạnh vàng; mọi số P/R của 2b là **có điều kiện** trên danh sách đó | Cờ *Thiếu khái niệm* và *Node gộp sai*; báo cáo ghi rõ giới hạn này |
| Một chương dài hơn nhiều so với đoạn văn PREAP đã đánh giá | Thời gian và độ đồng thuận có thể khác | Thí điểm một chương, ghi thời gian thật; chia nhiều buổi |
| Mở rộng đầu *cần biết trước* ra cả tài liệu làm tăng tải | Người gán phải nhớ khái niệm của chương khác | Danh sách chọn có tìm kiếm; sheet Khái niệm ghi nơi dạy của từng khái niệm |
| Chỉ hai người gán | Độ đồng thuận có độ bất định lớn | Báo cáo κ kèm khoảng tin cậy; hội ý thay vì hợp |
| Lỗi đặc trưng của PREAP (nhắc trong định nghĩa ≠ tiên quyết; sai chiều) | Giáo viên tìm thấy lỗi này nhiều nhất | Loại bằng chứng *Trong định nghĩa* bắt buộc kèm điều kiện "cần để hiểu"; ca khó số 1 trong hướng dẫn |
| Người gán bị neo theo máy | Máy đã chạy trước | File không chứa cạnh nào của pipeline; cấm xem đầu ra trước khi nộp; test bảo đảm điều này |
| Tiếng Việt chưa có tiền lệ | Mọi kết quả của PREAP là trên tiếng Anh | Báo cáo coi mọi con số κ của đợt này là số đo mới, không phải kỳ vọng |
