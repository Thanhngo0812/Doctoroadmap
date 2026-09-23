# Kế hoạch đưa đồ thị tiên quyết tới mức dùng được

Vòng 42 · 2026-09-23 · Viết sau khi bộ vàng thật đã đóng băng và E1/E2/E3 đã chạy lần đầu.

Đây là **kế hoạch**, không phải báo cáo kết quả. Mọi con số trong đây đã đo và có đường dẫn về artifact; mọi câu
dự đoán được đánh dấu **[giả thuyết]**. Kế hoạch được phép chạm vào bất kỳ phase nào, kể cả phase đã đóng.

Nguồn số: `artifacts/a8-gold/<doc>-score-vang.json`, `artifacts/graph/<doc>/v6`, và các vòng 36–42 trong
`feedback/F19-a6-a10-cum-chu-de-va-tien-quyet.md`.

---

## 1. "Dùng được" nghĩa là gì — định nghĩa đo được

Không có định nghĩa này thì không biết khi nào dừng. Năm tiêu chí, mỗi cái có phép đo sẵn:

| # | Tiêu chí | Phép đo | Hiện tại | Ngưỡng đề xuất |
|---|---|---|---|---|
| **U1** | Lộ trình **không đặt tiên quyết sau** khái niệm cần nó | tỉ lệ vi phạm cạnh vàng (`a8-roadmap-score`) | **26,1%** / **15,2%** | **≤ 5%** |
| **U2** | Cạnh đề xuất phần lớn là cạnh thật | precision trực tiếp | **0,656** / **0,644** | **≥ 0,70 và không giảm** |
| **U3** | Không bỏ sót quá nửa quan hệ | recall trực tiếp | **0,525** / **0,475** | **≥ 0,70** |
| **U4** | Chặng đọc được như một buổi học | cỡ stage, stage đơn lẻ, cạnh trong stage | **đã đạt** | giữ: 0 stage đơn lẻ, 0 cạnh trong stage, số stage = cận dưới |
| **U5** | Không khái niệm nào rơi vào lộ trình mà chưa ai xét | `coverage_status` | **đã đạt** (0 node chưa xét) | giữ 0 |

**U1 là tiêu chí sản phẩm.** Một tiên quyết bị đặt sau sẽ chặn người học; một tiên quyết thiếu chỉ khiến họ đọc
sớm hơn cần. U2 và U3 là tiêu chí khoa học và là đường đi tới U1.

**U4 và U5 đã đạt sau vé 21** và phải được giữ như bất biến, không được đánh đổi lấy U1–U3.

---

## 2. Đang đứng ở đâu

| | `doc-1` Chương 3 (VN) | `doc-2` mục 3C (EN) |
|---|---|---|
| Bộ vàng | 40 cạnh · κ 0,611 / 0,733 | 61 cạnh · κ 0,813 / 0,818 |
| precision · recall · F1 | 0,656 · 0,525 · 0,583 | 0,644 · 0,475 · 0,547 |
| đúng / thừa / thiếu | 21 / 11 / 19 | 29 / 16 / 32 |
| vi phạm cạnh vàng của lộ trình | **26,1%** | **15,2%** |
| τ so mục lục | +0,087 | +0,125 |
| stage | 29, cỡ TB 7,8, 0 lẻ | 55, cỡ TB 8,0, 0 lẻ |

Chi phí đã dùng: **9,50 / 50 USD**.

---

## 3. Chuỗi chẩn đoán: cái gì đã chứng minh, cái gì chưa

**Đã chứng minh, có số:**

1. **Lỗi thứ tự của lộ trình hoàn toàn do cạnh thiếu.** 13/13 ca vi phạm là cạnh máy **không hề có** — không trực
   tiếp, không cả đường bắc cầu. A10 chưa từng xếp sai một cạnh nó biết.
2. **Cạnh sai không gây ra ca vi phạm nào** trong phạm vi bộ vàng. Với *tính đúng thứ tự*, recall là ràng buộc
   đang siết, không phải precision.
3. **Khi mô hình được nhìn thấy cặp, nó chuyển thành cạnh rất đáng tin:** 21/21 và 29/29 cạnh vàng tìm được đều
   từng có cơ hội (tiên quyết nằm trong `allowed`, đích nằm trong `target` của cùng một phiên).
4. **Luật bằng chứng của ta không cắt mất gì:** executor từ chối **0** cạnh vàng.
5. **63% cạnh thiếu chưa bao giờ có cơ hội nào** (9/19 và 23/32).
6. **78% cạnh tiên quyết là liên cụm** (31/40 và 48/61), trong khi D6 cấm pass phụ hỏi đúng vùng đó.
7. **Phiên của `doc-2` vụn bệnh lý:** 352 phiên cho 438 khái niệm, **57% phiên có ≤1 khái niệm đích**, và chỉ
   **7%** cặp vàng từng cùng phiên. Cơ chế "siêu section" mà D6 nói tới **chưa từng được cài**.
8. **Trần cứng:** cạnh "ngầm" — không bộ sinh nào với tới — chiếm **17,5%** và **23,0%** cạnh vàng.

**Chưa chứng minh:**

- Liệu hỏi theo cặp có chuyển được những cạnh mà trích mở đã bỏ qua hay không. **[giả thuyết]** có, vì hỏi thẳng
  một cặp là dạng câu hỏi khác hẳn trích mở.
- Liệu mở pass phụ có làm tụt precision không. **Đang đo.**
- Liệu gộp section có nâng recall của `doc-2` không. **[giả thuyết]** có, vì 93% cặp vàng chưa từng cùng phiên.

---

## 4. Bảy can thiệp, xếp theo sức mạnh bằng chứng

### C1 — Pass phụ thôi lọc theo cụm *(đang chạy)*

- **Phase:** A8 pass phụ · **Bằng chứng:** #6, 25/26 cạnh vàng thiếu nằm trong sổ là cặp liên cụm
- **Can thiệp:** bỏ điều kiện `same_cluster` ở tuyến `chapter`; giữ nguyên phép tỉa theo khả đạt
- **Giá:** ~12 USD cho hai tài liệu (đo từ telemetry: ~2.837 token/cặp)
- **Trần thu lại:** 26 cạnh vàng → recall tối đa ~0,80 / ~0,72
- **Rủi ro:** ngoại suy cho **~318 cạnh mới** trên `doc-1` trong khi đồ thị hiện có 337. Precision có thể tụt.
- **Biết nó có tác dụng bằng cách:** chấm lại, so **theo cặp trên cùng bộ vàng** (xem mục 6)

### C2 — Gộp section nhỏ thành "siêu section" ở pass chính

- **Phase:** A8 pass chính, `plan_main_sessions` · **Bằng chứng:** #7
- **Can thiệp:** khi một section có dưới `k` khái niệm đích, gộp với section kề **cùng cha** cho tới khi đạt `k`
  hoặc hết anh em. `k` là tham số, đề xuất mặc định 4 (cỡ phiên trung bình của ba tài liệu khoẻ là 3,2–4,6).
  Spec D6 đã viết "mỗi **(siêu) section** một phiên" — đây là cài phần còn thiếu, không phải đổi luật.
- **Giá:** chạy lại pass chính cho `doc-2`, ~1,4 USD
- **Kỳ vọng:** **[giả thuyết]** tỉ lệ cặp vàng từng cùng phiên tăng từ 7% lên mức của `doc-1` (52%)
- **Biết nó có tác dụng bằng cách:** đo lại tỉ lệ cơ hội trước khi tiêu tiền cho pass chính — **tính được offline
  mà không gọi mô hình**, chỉ cần chạy lại `plan_main_sessions` với `k` khác nhau và đếm

### C3 — Siết ngưỡng nhận, **chỉ nếu** C1 làm tụt precision

- **Phase:** A8 executor · **Bằng chứng:** chưa có, phụ thuộc kết quả C1
- **Cần cơ chế:** luật chuyển đã viết trước ở D9 — *khoảng cách precision ≥ 0,15, khoảng tin cậy không chứa 0, và
  recall không giảm quá 0,05*. **Không được nới luật này sau khi nhìn số.**
- **Đòn bẩy sẵn có:** cờ `evidence_hard`, số nguồn độc lập, `evidence_kind`
- **Cảnh báo:** `evidence_kind` gần suy biến (71–88% là `trong_dinh_nghia`) nên nó là đòn bẩy yếu; số nguồn độc
  lập là đòn bẩy mạnh hơn

### C4 — Dọn node ở A3/A4

- **Phase:** A3 · **Bằng chứng:** 12% (`doc-1`) và 7% (`doc-2`) tên node trông như **phát biểu** chứ không phải
  khái niệm (`dim F^m,n = mn`, `any two bases of a vector space have the same length`); `doc-1` có ba node tên
  `Tính chất 1`, `Tính chất 2`, `Tính chất 3` — vô nghĩa
- **CHẶN:** đổi A3 làm đổi `canonical` → đổi `concept_hash` → **vô hiệu hoá bộ vàng vừa gán** (F123). Việc này
  **phải đợi tới khi mọi thí nghiệm của đợt chạy xong**, hoặc làm trên một corpus riêng.
- **Kỳ vọng:** **[giả thuyết]** precision tăng, vì phát biểu và tính chất kéo theo cạnh giả

### C5 — Tìm bộ sinh cho vùng "ngầm"

- **Phase:** A6/A7/mention map · **Bằng chứng:** 23/51 cạnh thiếu **không nằm trong sổ cặp nào**; E1 xếp 17,5% và
  23,0% cạnh vàng vào loại "ngầm"
- **Trạng thái:** **chưa có can thiệp nào để đề xuất.** Đây là nghiên cứu, không phải sửa lỗi.
- **Việc làm được ngay và miễn phí:** đọc tay 10 cạnh "ngầm" của mỗi chương và mô tả chúng nối nhau bằng gì. Không
  có mô tả ấy thì mọi bộ sinh mới đều là đoán.

### C6 — Hỏi lại cặp mà trích mở đã bỏ qua dù có cơ hội

- **Phase:** A8 pass phụ · **Bằng chứng:** 10 (`doc-1`) + 9 (`doc-2`) cạnh vàng thiếu **đã có cơ hội** mà mô hình
  không nêu
- **Ghi chú:** C1 đã phủ một phần nhóm này (nếu cặp có trong sổ). Sau C1 phải **tách riêng** con số này ra để biết
  hỏi-theo-cặp có cứu được cạnh mà trích-mở bỏ qua hay không — đó chính là câu của **E6**.

### C7 — Đưa U1 thành cổng, không phải báo cáo

- **Phase:** A10 / quy trình · **Giá:** 0, không gọi mô hình
- **Can thiệp:** `a8-roadmap-score` chạy trong lượt build; lộ trình vi phạm quá ngưỡng thì **gắn cờ chặn**, không
  im lặng xuất bản. Cùng tinh thần cổng nhất quán cấu trúc của A9.
- **Chỉ áp được cho tài liệu có bộ vàng** — nên nó là cổng cho **corpus thí nghiệm**, không phải cho mọi tài liệu.

---

## 5. Thứ tự, điều kiện dừng, và ngân sách

| Bước | Việc | Giá | Điều kiện đi tiếp |
|---|---|---|---|
| 1 | C1 trên `doc-1` *(đang chạy)* | ~3 USD | precision **không giảm quá 0,05** |
| 2 | Chấm C1, so theo cặp | 0 | nếu precision tụt mạnh → dừng, sang C3 trước |
| 3 | C2 — đo offline `k` ∈ {2,3,4,6} trên `doc-2` | **0** | tỉ lệ cơ hội tăng rõ |
| 4 | C1 trên `doc-2` | ~9 USD | chỉ khi bước 2 đạt |
| 5 | C2 chạy thật trên `doc-2` | ~1,4 USD | chỉ khi bước 3 đạt |
| 6 | C6 tách số, trả lời E6 | 0 | — |
| 7 | C7 cổng | 0 | — |
| 8 | C4 dọn node | ~4 USD | **chỉ sau khi mọi thí nghiệm xong** (F123) |

Tổng dự kiến **~17 USD**, đưa ngân sách lên ~27/50.

**Điều kiện dừng cứng:** nếu sau bước 4 mà U1 vẫn trên 10%, **không tiêu thêm** cho recall. Lúc ấy vấn đề nằm ở
vùng "ngầm" (C5) và đó là nghiên cứu, không mua được bằng lời gọi mô hình.

---

## 6. Kỷ luật khoa học — phần quan trọng nhất của kế hoạch

**Bộ vàng nhỏ: n = 40 và 61.** Đây là ràng buộc chi phối mọi kết luận.

**Phải so theo cặp, không so khoảng tin cậy.** Trước/sau chạy trên **cùng một bộ vàng**, nên đây là so sánh **bắt
cặp**. Báo cáo **số cạnh vàng được thêm** và **số bị mất**, không phải hai khoảng tin cậy chồng lấn. Hai khoảng
chồng nhau ở n = 40 hầu như luôn xảy ra và sẽ che mất hiệu ứng thật. Dùng phép đếm bắt cặp kiểu McNemar.

**Không được tinh chỉnh ngưỡng trên bộ vàng.** Bộ vàng này là **tập kiểm**, không phải tập hiệu chuẩn. Nếu C3 cần
chọn ngưỡng thì:
- hiệu chuẩn trên `doc-1`, **kiểm trên `doc-2`**, và báo cáo cả hai;
- hoặc dùng bốn tài liệu phát triển làm tập hiệu chuẩn và giữ hai chương vàng hoàn toàn cho kiểm.
Mọi ngưỡng chọn sau khi nhìn số phải được **gọi tên là hậu nghiệm** trong báo cáo.

**Luật chuyển phải viết trước.** D9 đã có một luật viết trước; mọi can thiệp mới cũng phải có luật của nó **trước
khi đo**. Kế hoạch này chính là chỗ viết chúng ra.

**Phải báo cáo cả can thiệp thất bại.** Việc xếp hạng sổ cặp bằng tín hiệu rẻ đã thất bại trên `doc-2` (ngang
hoặc tệ hơn ngẫu nhiên) — câu "không được" ấy có giá trị bằng một kết quả, và đã được ghi.

**Tách theo chương, không gộp.** Hai giáo trình khác nhau tới mức E1 cho hai bức tranh gần như ngược nhau (`doc-1`
52,5% cạnh cục bộ; `doc-2` 6,6%). Gộp thành một con số là che mất phát hiện chính.

**Nói rõ bộ vàng là nhãn của một người có người thứ hai kiểm.** Hội ý giữ 100% cạnh của A1 và nhận đúng 2 cạnh của
A2 (F125). κ vẫn là số đo thật vì tính trước hội ý, nhưng tuyên bố phải khiêm tốn tương ứng.

---

## 7. Trần cứng — thứ kế hoạch này không thể vượt

1. **Recall không vượt được ~80%** (`doc-1`) và ~**77%** (`doc-2`): phần "ngầm" không bộ sinh nào với tới.
2. **U1 không thể về 0** chừng nào recall chưa gần trần, vì mọi ca vi phạm đều do cạnh thiếu.
3. **Không có dữ liệu học viên**, nên không kiểm định được theo nghĩa của văn liệu; mọi tuyên bố phải giới hạn ở
   *kiểm tra nhất quán cấu trúc* và *đối chiếu với nhãn người đọc văn bản*.
4. **n = 40 và 61** giới hạn cỡ hiệu ứng phát hiện được. Một cải tiến dưới ~5 cạnh sẽ không phân biệt nổi với
   nhiễu, kể cả khi so bắt cặp.

---

## 8. Việc làm được ngay mà không tốn đồng nào

Ba thứ nên làm trước khi tiêu thêm tiền:

1. **C2 bước đo offline** — chạy lại `plan_main_sessions` với `k` khác nhau và đếm tỉ lệ cặp vàng có cơ hội. Nó
   quyết định C2 có đáng không, và không gọi một lời mô hình nào.
2. **C5 đọc tay** — đọc 10 cạnh "ngầm" mỗi chương, mô tả chúng nối nhau bằng gì.
3. **C7 cổng** — nối `a8-roadmap-score` vào lượt build.

---

## 9. Kết quả đo offline của C2 (2026-09-23) — và nó đổi phán quyết

Chạy lại việc dựng phiên với một bước gộp: **hàng liền kề cùng chương được gộp cho tới khi phiên đạt `k` khái niệm
đích**. Không gọi một lời mô hình nào. "Có cơ hội" = tiên quyết nằm trong `allowed` và đích nằm trong `target` của
cùng một phiên — điều kiện mà **100%** cạnh vàng tìm được đều thoả.

**`doc-1` — gộp không đổi gì cả:**

| `k` | phiên | đích TB | phiên ≤1 | cơ hội / cạnh vàng | cơ hội / cạnh thiếu |
|---|---|---|---|---|---|
| 1 *(hiện tại)* | 66 | 3,6 | 16 | 30/40 (75%) | 9/19 (47%) |
| 3 | 50 | 4,6 | 2 | 30/40 | 9/19 |
| 8 | 28 | 8,2 | 1 | 30/40 | 9/19 |

**`doc-2` — gộp giúp nhiều:**

| `k` | phiên | đích TB | phiên ≤1 | cơ hội / cạnh vàng | cơ hội / cạnh thiếu |
|---|---|---|---|---|---|
| 1 *(hiện tại)* | 337 | 1,6 | **203** | 35/61 (57%) | **6/32 (19%)** |
| 3 | 153 | 3,4 | 6 | 42/61 (69%) | 13/32 (41%) |
| 6 | 91 | 5,5 | 3 | 43/61 (70%) | 14/32 (44%) |
| **8** | **76** | **6,5** | **8** | **46/61 (75%)** | **17/32 (53%)** |

*(Mô phỏng dựng lại hàng từ section nên lệch 1–3 cạnh so với `main_sessions` thật: ở `k=1` nó cho 35/61 và 30/40,
trong khi artifact thật cho 38/61 và 31/40. Dùng nó để **so tương đối**, không trích tuyệt đối.)*

### Ba điều đọc được

1. **C2 là can thiệp phụ thuộc hình dạng sách, không phải phụ thuộc ngôn ngữ.** Nó vô dụng với `doc-1` (section đã
   đủ lớn) và có giá trị lớn với `doc-2` (Axler đánh heading theo từng định lý, 203/337 phiên chỉ một khái niệm).
2. **Một luật duy nhất phục vụ được cả hai**, vì "gộp cho tới khi đạt `k`" **tự không làm gì** khi section đã đủ
   lớn. Không cần tham số riêng cho từng tài liệu. Đề xuất mặc định **`k = 6`**, gộp theo **chương** chứ không
   theo cha — gộp theo cha để lại 49 phiên đơn lẻ ở `k=8`, gộp theo chương chỉ còn 8.
3. **Gộp còn làm pass chính rẻ hơn**: `doc-2` từ 337 phiên xuống 76, `doc-1` từ 66 xuống 31.

### Phán quyết cập nhật cho C2

**Nâng C2 lên ngang C1 về mức ưu tiên**, và làm nó **trước** khi tiêu tiền C1 cho `doc-2`:

- Với `doc-2`, C2 đưa cạnh thiếu **có cơ hội** từ 6 lên 17 — gần bằng phần C1 hứa (15 cạnh nằm trong sổ cặp), mà
  giá chỉ **~1,4 USD** so với ~9 USD, và còn làm pass chính rẻ đi.
- Hai can thiệp **không chồng nhau**: C2 cho pass chính cơ hội thấy cặp; C1 cho pass phụ hỏi thẳng cặp. Nên chạy
  C2 trước rồi mới đo C1 trên phần còn lại — nếu không sẽ không biết công của cái nào.
- **[giả thuyết]** phiên lớn hơn có thể làm tụt precision vì mô hình có nhiều khái niệm hơn để nối. Không đo
  offline được. Phải chấm sau khi chạy, và luật chuyển của D9 áp cho cả ca này.

### Thứ tự sửa lại

| Bước | Việc | Giá | Ghi chú |
|---|---|---|---|
| 1 | C1 trên `doc-1` *(đang chạy)* | ~3 USD | đo C1 tách biệt, trên tài liệu mà C2 vô dụng — **đây là thiết kế sạch** |
| 2 | Chấm C1 trên `doc-1`, so bắt cặp | 0 | |
| 3 | **C2 trên `doc-2`, `k = 6`, gộp theo chương** | ~1,4 USD | rẻ hơn C1 sáu lần, hiệu quả tương đương |
| 4 | Chấm C2 trên `doc-2` | 0 | |
| 5 | C1 trên `doc-2` **sau** C2 | ~9 USD | chỉ khi bước 2 và 4 đều đạt |

Tình cờ mà may: `doc-1` là tài liệu C2 vô dụng, nên lượt C1 đang chạy trên nó là **một phép đo C1 sạch, không lẫn
tác dụng của C2**. Giữ nguyên thiết kế ấy.

---

## 10. Phản biện từ người đọc `doc-3` (2026-09-23) — kiểm từng ý

Một người ngoài đọc lộ trình `doc-3` và chỉ ra rằng **U4 và U5 chấm "đạt" cho một output tệ**, nên bộ tiêu chí
thiếu chiều đo. Tôi kiểm từng ý bằng số thay vì nhận hay bác cả gói.

### Đúng, và đã kiểm được

**Node rác có thật.** `doc-3` có 58 node học được, trong đó `GPA`, `Homework assignments`, `Final project`,
`Class participation` là **việc hành chính của môn học**, không phải khái niệm. Thêm `Top node`, `Middle node`,
`Bottom node` (mô tả vị trí trong một hình vẽ), `A single number`, `A few numbers`. Khoảng **10–12 trên 58 ≈ 20%**
node là rác — tệ hơn hẳn mức 7–12% "tên giống phát biểu" tôi đo trên `doc-1`/`doc-2`.

**Trùng lặp có thật**, dù ví dụ họ nêu không phải dạng chỉ-khác-hoa-thường: `output layer` và `Output layer node`
là hai node; `Machine Learning`, `Machine Learning Model`, `Machine learning concepts` là ba; `Independent
variables` và `Input variables` là hai.

**Và có một dạng trùng lặp kiểm được bằng máy, không cần mô hình:** hai node canonical cùng khai một `alias`. Đó
là lỗi hợp nhất của A4 **theo định nghĩa**. Đếm trên cả corpus:

| tài liệu | node | **alias đụng** | ví dụ |
|---|---|---|---|
| `doc-1` | 225 | 1 | `định lý 6` |
| `doc-2` | 438 | **6** | `additive identity`, `bilinear functional`, `finite-dimensional` |
| `doc-3` | 58 | 1 | `weights` dùng bởi cả `Coefficients` và `parameters` |
| `naive-bayes` | 34 | 1 | `likelihood` |
| ba tài liệu còn lại | | 0 | |

**U5 khuyến khích rác — đây là ý sắc nhất của họ và tôi nhận.** "0 node chưa xét" nghĩa là `GPA` đã được xét và
đưa vào lộ trình. Độ phủ cao trên một tập node bẩn không phải điểm tốt; U5 như đang viết **thưởng cho việc nhồi
rác vào lộ trình**.

**Tên stage không tồn tại.** Họ thấy `... · layer 4` vì A10 **chưa từng có lượt đặt tên stage** — `spec-addendum`
mô tả nó, mã không có. Tôi đã ghi việc này ở V12 nhưng xếp nó là "gỡ khỏi spec hoặc cắt vé"; người đọc thật cho
thấy nó là **lỗi người học thấy đầu tiên**.

### Một chỗ lập luận của họ không áp được vào ta, nhưng kết luận vẫn đúng qua đường khác

Họ viết: *"một cạnh vàng có thể khớp node này nhưng lệch node kia, gây nhiễu recall"*. Trong thiết kế của ta
**không có khe lệch ấy**: người gán **chọn node từ chính danh sách của hệ thống** trong file Excel, nên cạnh vàng
tham chiếu đúng `node_id` của hệ thống.

Nhưng kết luận của họ vẫn đúng, qua một cơ chế **mạnh hơn**: chính vì bộ vàng được gán **trên danh sách node của
hệ thống**, node rác **vô hình với mọi chỉ số cạnh theo đúng cấu tạo**. Người gán thấy `GPA` thì đơn giản là không
nối nó; `GPA` góp 0 vào precision và 0 vào recall. **Một tập node bẩn không bị phạt ở bất kỳ đâu.** Đó chính là lý
do U0 cần thiết — và là lý lẽ mạnh hơn cái họ đưa.

Trùng lặp thì có hại thật, qua đường khác: người gán nối cạnh vào **một** trong hai node trùng, máy có thể đã sinh
cạnh ở node kia. Đó là mất recall thật. **[giả thuyết]**, chưa đo.

### Một ý của họ đã được kiểm và **bị bác**

Họ đề xuất đo *"tỉ lệ cạnh prerequisite thực ra là is_a / part_of"*, nhắm vào lỗi kiểu "AI sau Deep Learning".
Tôi đo bằng dấu hiệu tên-chứa-nhau, rồi đối chiếu với bộ vàng:

| | cạnh trong phạm vi chấm | tên chứa nhau | **precision nhóm ấy** | precision nhóm còn lại |
|---|---|---|---|---|
| `doc-1` | 31 | 8 (26%) | 0,62 | 0,70 |
| `doc-2` | 44 | 12 (27%) | **0,92** | **0,56** |

**Trên `doc-2` nhóm ấy tốt hơn hẳn phần còn lại**, không tệ hơn. Người gán công nhận `matrix → matrix addition`,
`không gian véc tơ → véc tơ` là tiên quyết thật dù tên lồng nhau. Trên `doc-1` kém hơn chút nhưng n = 8, nằm trong
nhiễu. **Không có bằng chứng cho tác hại họ nghi.** Dạng lỗi ấy có tồn tại — ca `ERD ↔ Thiết kế CSDL` đúng là
bộ phận–toàn thể bị đoán ngược — nhưng nó hiếm, và **cờ chu trình hai cạnh đã bắt được nó**.

Giữ phép đo này làm **chẩn đoán**, không làm cổng, và báo cáo cả kết quả âm này.

### Một khuyến nghị của họ mà bằng chứng của tôi nói ngược

Họ khuyên *"giữ precision chặt và nới recall, vì cạnh sai hại hơn cạnh thiếu"*. Với **tính đúng thứ tự** thì số đo
nói ngược: **13/13 ca lộ trình xếp sai đều do cạnh thiếu; cạnh sai gây ra 0 ca.** Nên với U1, recall mới là ràng
buộc đang siết.

Lời khuyên của họ vẫn có thể đúng cho **những tác hại tôi chưa đo được** — một cạnh sai ép người học theo thứ tự
không cần thiết, dù nó không vi phạm cạnh vàng nào. Ghi lại là **câu hỏi mở**, và đừng đảo ưu tiên khi chưa có số.

### Bốn tiêu chí bổ sung — nhận

| # | Tiêu chí | Phép đo | Ngưỡng |
|---|---|---|---|
| **U0** | Tập node sạch | tỉ lệ node rác trên mẫu người chấm | ≤ 10% |
| **U0b** | Không trùng lặp | **số cặp node cùng khai một alias** (kiểm bằng máy, 0 lời gọi) | **= 0** |
| **U6** | Stage mạch lạc chủ đề | người hoặc mô hình chấm 1–5 | TB ≥ 4 |
| **U7** | Tên stage có nghĩa | có tên, và tên tóm đúng nội dung | ≥ 90% đạt |

**U0 là điều kiện tiên quyết cho U2 và U3**: đo cạnh trên tập node bẩn là đo trên nền đất lún. Nhưng **không** vì
thế mà vứt các con số hiện có — chúng đo đúng thứ chúng nói (precision/recall **của cạnh, trên tập node hiện
hành**), chỉ là chưa đủ để kết luận "lộ trình dùng được".

**U5 phải viết lại**: từ *"0 node chưa xét"* thành *"0 node chưa xét **trong số node đã qua U0**"*. Như cũ thì nó
thưởng cho rác.

**U0b là tiêu chí rẻ nhất trong toàn bộ danh sách** — 0 lời gọi mô hình, và corpus hiện có **9 vi phạm**.

---

## 11. Phản biện thứ hai — người đọc lộ trình `doc-1` v7 (2026-09-23)

Phản biện này đưa một giả thuyết cụ thể và kiểm được: **cạnh bị đảo hướng**. Tôi có bộ vàng cho đúng chương ấy nên
kiểm thẳng được.

### Giả thuyết đảo hướng: **bác bỏ**

| | |
|---|---|
| cạnh máy chạm khái niệm đã gán | 58 |
| khớp vàng **đúng** hướng | **21** |
| khớp vàng **ngược** hướng | **0** |
| cặp cả hai cùng có nhưng khác chiều | **0 / 21** |

Hướng cạnh đúng. Không có batch nào hiểu ngược schema.

### Nhưng quan sát của họ đúng, và nguyên nhân nằm chỗ khác

**`Véc tơ` ở layer 15** không do đảo hướng mà do đúng một cạnh:

> `Không gian véc tơ` → `Véc tơ` · `trong_dinh_nghia` · lý do: *"Vectors are defined as the elements of a vector
> space V."*

Giáo trình này **thật sự** định nghĩa véc tơ là phần tử của không gian véc tơ, ở vị trí 121 và 123 — cạnh **thuận**
thứ tự sách và **trung thành với sách**. Người phản biện so với *"thứ tự chuẩn của một giáo trình ĐSTT"*, tức một
chuẩn bên ngoài, chứ không so với cuốn này.

Đây là câu hỏi thật và chưa có câu trả lời trong spec: **"tiên quyết theo định nghĩa" khác "tiên quyết theo sư
phạm"**. Khi sách định nghĩa A bằng B, ta ghi B → A. Người học thì cần thấy véc tơ trước không gian véc tơ. Hai
thứ này mâu thuẫn nhau, và hiện ta chỉ ghi loại thứ nhất. **Đưa vào Limitations, và là câu hỏi mở cho đợt sau.**

**`Dạng toàn phương` ở layer 1** thì đúng là lỗi: nó có **0 cạnh vào** và 7 cạnh ra. Đây là lỗi recall trên khái
niệm chương cuối, đúng loại C1/C2 đang chữa.

### 29 tầng: **không phải do cạnh giả** — và chính họ đã đoán đúng độ sâu thật

| | |
|---|---|
| chuỗi phụ thuộc **thật** (bỏ cạnh thừa) | **10 bước** |
| ước lượng của người phản biện | "khoảng 10–12 bước" |
| node học được | 225 |
| `⌈225 / 8⌉` | **29** |
| số tầng thật | **29** |

**Số tầng bị ép bởi trần độ rộng, không bởi chuỗi phụ thuộc.** Đồ thị không phồng; nó sâu đúng mức họ đoán.

Hệ quả quan trọng: **cách sửa độ sâu không phải sửa cạnh mà là dọn node.** Chính điểm 2 và 3 của họ (node rác,
trùng lặp) là cách chữa điểm 5 của họ. Với ~120 node sạch và trần 8 thì còn 15 chặng; trần 12 thì còn 10 — đúng
con số họ kỳ vọng.

### Một phát hiện mới, do phản biện này gợi ra

**Đề cương đầu sách làm hỏng `first_order_index` của 49 / 225 khái niệm (22%).**

`Dạng toàn phương` có vị trí **10**, sớm hơn `Tập hợp` (19) — vì nó được **liệt kê trong đề cương chi tiết** ở đầu
sách, không phải vì nó được dạy ở đó. Cùng vùng ấy: `Số phức` (8), `Vành` (8), `Đa thức` (8), và cả ba node rác
`Thang điểm chữ`, `Thi viết rọc phách`, `Điểm đánh giá học phần`.

Đề cương gây **hai** thiệt hại cùng lúc: nó bơm node hành chính vào, **và** nó làm hỏng vị trí trình bày của một
phần năm số khái niệm. Mà vị trí ấy là thứ τ dùng làm đối chứng và là thứ phá thế hoà. **Một phần của τ = +0,087
trên `doc-1` là do ô nhiễm này, không phải do lộ trình sai.**

**Can thiệp mới — C8:** loại vùng đầu sách (bìa, mục lục, đề cương) khỏi nguồn provenance và khỏi `first_order_index`.
Phase B0/A4. Rẻ, không gọi mô hình, và sửa cùng lúc một phần node rác lẫn đối chứng τ.

### Ba ý còn lại

**U8 của họ chính là τ tôi đã cài** ở vé 22 (`a8-roadmap-score`). Giá trị đo được: `doc-1` **+0,087**, `doc-2`
**+0,125**. Họ đoán đúng rằng nó phải dương rõ rệt với một giáo trình, và nó **không** — nhưng nguyên nhân là ô
nhiễm đề cương cộng recall thấp, chứ không phải hướng cạnh.

**Luật chuẩn hoá tên tiếng Việt — nhận, và rất cụ thể.** `"2" ↔ "hai"`, `"(cột)" ↔ "hoặc cột"`, `"Véctơ" ↔ "Véc
tơ"`, bỏ tiền tố `"Hệ véc tơ"`. Đây là luật trước khi so embedding, đúng chỗ A4 đang yếu. Ghép vào **C4**.

**Prior theo thứ tự tài liệu — spec đã có**, ở D8: cạnh ngược thứ tự bị trừ 0,1, và spec tự ghi *"con số 0,1 là
tạm, không nguồn nào ủng hộ"*, để **E8** hiệu chỉnh trên bộ vàng. Giờ đã có bộ vàng nên E8 chạy được. Đề xuất của
họ trùng với việc đã lên kế hoạch; điều mới là **giờ hiệu chỉnh được bằng số**.

---

## 12. Phản biện thứ ba — phân loại "A trước B" (2026-09-23)

Phản biện này trả lời đúng câu tôi nhờ chủ dự án hỏi lại, **tự rút ba ý của chính họ**, và đưa ra một phân loại:
phụ thuộc định nghĩa (cứng) / lý do sư phạm (mềm) / quy ước (yếu nhất). Ba ý họ rút — `Véc tơ`→`Không gian véc
tơ`, `Cơ sở trực chuẩn`→`Gram-Schmidt`, `Xác định dương/âm` — trùng đúng ba chỗ tôi đã bác ở mục 11 bằng số.

### Phân loại của họ: ta đã có nhãn, nhưng chưa dùng

Cả bộ vàng lẫn cạnh máy **đã ghi sẵn loại bằng chứng**. Nên đề xuất "gold phải ghi loại và lý do" không phải việc
phải làm mới — mà là việc phải **đem ra dùng**. Đo trên dữ liệu đang có:

| | `noi_ro` | `trong_dinh_nghia` | `mach_trinh_bay` |
|---|---|---|---|
| vàng `doc-1` (40 cạnh) | 9 | 29 | **2** |
| vàng `doc-2` (61 cạnh) | 12 | 49 | **0** |
| máy `doc-1` (337 cạnh) | 7 | 311 | **19** |
| máy `doc-2` (864 cạnh) | — | 836 | **28** |

**Bộ vàng gần như không có cạnh mềm nào:** 38/40 và 61/61 là cạnh cứng. Người gán đã tự lọc quy ước ra từ đầu.
Nên "chỉ tính U1 trên cạnh `requires`" gần như không đổi gì: `doc-1` 24,3% → 22,9%, `doc-2` 18,3% → 18,3%.
Lo ngại "U1 phạt oan vì bộ vàng chứa thói quen của người gán" **không đúng với bộ vàng này**.

### Cơ chế họ lo: đã kiểm trên toàn kho, **chưa từng xảy ra**

Họ cảnh báo *"cạnh mềm có thể tạo vòng hợp lệ, nên nếu đưa vào sort cứng thì bước remove-cycle sẽ cắt nhầm"*.
Đếm trên **31 lượt chạy của 7 tài liệu**:

- chỉ 2 tài liệu từng bị cắt vòng (`baocao-canhan`, `naive-bayes`), tổng 31 cạnh bị cắt;
- **0/31 cạnh bị cắt là cạnh mềm** — tất cả đều là cạnh định nghĩa;
- trong đồ thị đã xuất, **0 cạnh mềm nào nằm trên bất kỳ vòng nào**.

Bỏ cạnh mềm khỏi ràng buộc cứng chỉ rút chuỗi dài nhất `doc-2` từ 21 xuống 20 bước, và không đổi gì ở `doc-1`.
Suy luận của họ đúng về mặt lý thuyết nhưng **lượng không đủ để thành nguyên nhân**: cạnh mềm chỉ chiếm 5,6% và
3,2%. Tách loại cạnh vẫn nên làm vì nó đúng về khái niệm, nhưng **không được tính nó là một can thiệp sửa lộ trình**.

### Năm vi phạm cứng họ liệt kê: **cả sáu đều là cạnh thiếu**

| cặp | lớp | máy có cạnh? |
|---|---|---|
| `Ma trận` → `Ma trận của dạng toàn phương` | 3 → 2 | **thiếu** |
| `Không gian véc tơ` → `Dạng toàn phương` | 8 → 1 | **thiếu** |
| `Nhân hai ma trận` → `Ma trận nghịch đảo` | 14 → 12 | **thiếu** |
| `Ma trận đơn vị` → `Ma trận nghịch đảo` | 16 → 12 | **thiếu** |
| `Toán tử tuyến tính` → `Véctơ riêng` | 19 → 15 | **thiếu** |
| `Định thức` → `Đa thức đặc trưng` | 5 → 5 | **thiếu** |

**Không cạnh nào sai chiều.** Khớp đúng chuỗi nhân quả đã chứng minh ở mục 3: vi phạm thứ tự là lỗ hổng recall,
không phải lỗi hướng.

### Đề xuất tách nghĩa `Véc tơ`: **đồ thị đã tách rồi, và nó không cứu được gì**

Họ đề nghị tách `Véc tơ` thành `Véc tơ n thành phần` (cụ thể) và gộp nghĩa trừu tượng vào `Không gian véc tơ`.
`doc-1` **đã có đủ cả hai node**: `Véc tơ` ở lớp 15 và `Véc tơ n thành phần` ở lớp **27** — nút cụ thể mà họ muốn
đặt lên trước lại nằm sau nút trừu tượng 12 lớp. Thuốc đã uống, triệu chứng nặng hơn. Nguyên nhân nằm ở chỗ khác,
và chính chỗ đó là phát hiện lớn nhất của vòng này.

### Nguyên nhân gốc **thứ hai**: bước xếp lớp, không phải bộ cạnh

`Véc tơ n thành phần` có **0 cạnh vào**. Cạnh chỉ ép nó xuống **lớp 1**. Nó nằm ở lớp 27 hoàn toàn do bước xếp lớp.
Đo tách bạch "lớp do cạnh ép" khỏi "lớp thực tế" trên cả `doc-1`:

- **143/225 khái niệm (64%) bị đẩy xuống dưới mức cạnh ép**, trung bình **12,5 lớp**;
- cạnh chỉ ép tối đa **15 lớp**, lộ trình có **29**;
- `Nhân hai ma trận` cạnh ép lớp 4 → thực tế 14; `Ma trận đơn vị` 7 → 16; `Toán tử tuyến tính` 10 → 19.

Ba cặp "vi phạm" họ nhìn thấy ở bảng trên **vẫn sẽ đảo ngược ngay cả khi cạnh thiếu được bổ sung**, vì thứ đẩy
chúng ra sau không phải tiên quyết mà là bộ xếp lớp.

Mã ở `src/doc2roadmap/domain/roadmap.py:36` xếp nút theo **nhãn Coffman–Graham**, một thứ tự thuần cấu trúc không
tham chiếu thứ tự sách; nút nào gặp lớp đầy thì bị đẩy tiếp xuống. CG **tối ưu đúng mục tiêu của nó** — 29 lớp
chính là cận dưới ⌈225/8⌉ nên không thể tốt hơn về số lớp. Vấn đề là mục tiêu ấy sai cho lộ trình học: **trong vô
số cách xếp 29 lớp hợp lệ, CG chọn một cách tuỳ ý thay vì cách bám sách nhất.**

### Can thiệp mới — C9: đổi tiêu chí phá thế hoà của bộ xếp lớp

Giữ nguyên ràng buộc tiên quyết và trần bề rộng; chỉ đổi thứ tự **đặt nút** khi lớp chưa đầy, từ nhãn CG sang
`(sàn cạnh ép, first_order_index)`. Sàn cạnh ép phải đứng trước trong khoá sắp xếp, nếu không cha có thể bị đặt
sau con và vòng lặp đặt nút vỡ. **Không gọi mô hình, không tốn tiền.**

Có **hai** chỗ vứt bỏ thứ tự sách chứ không phải một, nên phải tách đóng góp. Chạy qua đúng `build_roadmap` thật,
đủ cả `_balance`, `_merge_small`, `_order_stages`:

| biến thể | `doc-1` lớp / vi phạm | `doc-2` lớp / vi phạm |
|---|---|---|
| **A** hiện tại | 29 / **9** (22,5%) | 55 / **11** (18,0%) |
| **B** chỉ đổi xếp lớp (`_order_stages`) | 29 / **8** (20,0%) | 55 / **8** (13,1%) |
| **C** chỉ đổi xếp nút (`_coffman_graham`) | 30 / **5** (12,5%) | 56 / **4** (6,6%) |
| **D** đổi cả hai | 30 / **5** (12,5%) | 56 / **5** (8,2%) |

*(tỉ lệ theo thước đo khắt khe nhất: mẫu số tính cả cặp rơi vào cùng lớp)*

**Đổi chỗ đặt nút làm gần hết việc.** `_order_stages` cũng vứt thứ tự sách — nó phá thế hoà bằng `digest` băm nội
dung — nhưng sửa riêng nó chỉ được 1 và 3 cạnh. Và **D không tốt hơn C**: ở `doc-2` nó còn tệ hơn (5 so với 4).
Nên can thiệp là **C**, thay đổi nhỏ hơn và có bằng chứng độc lập mạnh hơn.

Giá phải trả trên hai tài liệu có bộ vàng: **đúng 1 lớp**, và **U5 không hề suy suyển** — `_merge_small` dọn sạch,
0 lớp một mình ở mọi biến thể.

> **Đính chính phép đo đầu tiên của tôi.** Lần đo đầu tôi chạy bộ xếp lớp trần, bỏ qua `_balance` và `_merge_small`,
> nên báo +2/+4 lớp và U5 vỡ ở 4 tài liệu. Cả hai con số đều sai vì phép đo không công bằng. Qua đường thật:
> +1 lớp, U5 nguyên vẹn. τ trong phép đo trần (+0,828 / +0,846) cũng là của thứ tự sách thuần, không phải của C.

### Nhưng C9 **không** là thắng lợi miễn phí trên toàn kho

Quét đủ 7 tài liệu qua đường thật:

| tài liệu | lớp A → C | lớp một mình A → C | τ A → C |
|---|---|---|---|
| `doc-1` | 29 → 30 | 0 → 0 | +0,087 → **+0,414** |
| `doc-2` | 55 → 56 | 0 → 0 | +0,125 → **+0,329** |
| `doc-3` | 8 → 9 | 0 → 0 | −0,019 → **+0,472** |
| `baocao-canhan` | 5 → 6 | 0 → 0 | +0,010 → +0,159 |
| `nhap-mon-ml` | 10 → 12 | 0 → **2** | +0,167 → +0,503 |
| `naive-bayes` | 6 → 7 | 0 → **1** | −0,090 → +0,199 |
| `xstk-ch3-1` | 13 → **16** | 0 → **1** | +0,179 → **+0,101** |

`xstk-ch3-1` **thụt lùi trên cả ba trục**: τ giảm, thêm 3 lớp, sinh lớp một mình — mà đó đúng là tài liệu vé 21
vừa đưa về tối ưu lý thuyết (63 lớp/39 lớp một mình → 13/0). Ba tài liệu nhỏ đều vỡ U5.

Hai điều rút ra. Thứ nhất, **bằng chứng độc lập (U1 so với bộ vàng) chỉ tồn tại cho `doc-1` và `doc-2`** — ở đó C9
thắng lớn và chắc. Trên năm tài liệu còn lại ta chỉ có τ, mà τ thì thiên vị sẵn cho C9. Thứ hai, τ **tụt** ở
`xstk-ch3-1` là dấu hiệu `first_order_index` của nó nhiễu nặng — đúng thứ C8 sinh ra để dọn.

**Kết luận điều kiện: C9 phải chạy sau C8, và phải có cổng theo từng tài liệu** — từ chối nếu số lớp phình quá
trần đã đặt, hoặc U5 sinh lớp một mình, hoặc τ giảm. Đây là lần đầu hai can thiệp có ràng buộc thứ tự cứng, và là
can thiệp đầu tiên trong kế hoạch **cần cổng riêng cho từng tài liệu** thay vì một phán quyết chung.

### Ý cuối của họ: đọc lại đoạn định nghĩa — **nhận, và nó đã có nửa hạ tầng**

Đề xuất *"với mỗi cạnh `requires` được đề xuất, đọc lại đoạn định nghĩa của B và hỏi: định nghĩa này có dùng A
không?"* là đúng tinh thần dự án: bám văn bản, không bám kiến thức nền của mô hình. Mỗi node đã có
`defining_chunk_ids`, nên đoạn cần đọc lại **đã sẵn**. Đây là một cổng hậu kiểm rẻ chạy trên 337 cạnh thay vì 3668
cặp. Xếp làm **C10**, sau C1 — vì trước hết phải biết C1 đẻ thêm bao nhiêu cạnh sai thì mới biết cổng này có đáng không.

### Thứ tự cập nhật lần hai

1. **C8** (đề cương) → **C9** (tiêu chí xếp nút) — cả hai không tốn tiền, C9 phụ thuộc C8, và trên hai tài liệu
   có bộ vàng thì C9 đang là can thiệp mạnh nhất đo được (vi phạm 22,5% → 12,5% và 18,0% → 6,6%, giá đúng 1 lớp).
   **Làm trước cả khi C1 chạy xong.** Nhưng C9 chỉ được bật cho tài liệu nào qua cổng riêng của nó —
   `xstk-ch3-1` hiện **trượt**, và phải đo lại sau C8 rồi mới quyết.
2. C1 (đang chạy) → chấm cặp đôi trước/sau.
3. C2 trên `doc-2`, rồi C1 trên `doc-2` nếu cả hai cổng qua.
4. C10 (đọc lại định nghĩa) — chỉ nếu C1 làm tụt precision.

**Tách loại cạnh cứng/mềm** vẫn làm, nhưng xuống hạng: nó đúng về khái niệm và rẻ, nhưng đã đo là **không phải
nguyên nhân** của bất kỳ triệu chứng nào đang thấy.

---

## 13. Thẩm định độc lập kế hoạch này (2026-09-23) — kiểm từng ý, và đính chính

Tài liệu [kien-nghi-luong-do-thi-va-roadmap-dat-chuan.md](kien-nghi-luong-do-thi-va-roadmap-dat-chuan.md)
thẩm định kế hoạch tại commit `deedbbb` và tự tái lập số liệu. Tôi kiểm lại **mọi khẳng định kiểm được** bằng mã
của dự án. **Cả năm đều đúng**, và ba trong số đó là lỗi của tôi.

### Đính chính

| Tôi đã nói | Đúng là | Kiểm bằng |
|---|---|---|
| Precision `doc-1` sau C1 là **0,500** | **0,473** (26 / 55) — tôi dùng phạm vi tự chế thay cho `score_edges` | `score_edges(..., targets=gold["targets"])` |
| C1 là "đổi ngang", "recall đáng giá hơn precision" | **C1 trượt cổng đã khoá trước**: mục 5 đặt "precision không giảm quá 0,05", thực tế giảm **0,183**. Lời biện hộ sau khi thấy số là đúng thứ mục 6 cấm | bảng dưới |
| Mục 12: ba cặp "vẫn sẽ đảo ngược ngay cả khi cạnh thiếu được bổ sung" | **Sai.** Cạnh đã nằm trong DAG thì không bộ xếp lớp hợp lệ nào đảo được. Bổ sung 19 cạnh vàng thiếu vào v7: **40/40 đúng thứ tự, 0 cùng lớp, vẫn 29 lớp** (đối chứng oracle, không đưa vào sản phẩm) | xếp lại qua `build_roadmap` |
| "Thước đo khắt khe nhất: vi phạm / (tôn trọng + vi phạm + cùng lớp)" | Khắt khe nhất phải tính **cùng lớp là lỗi**: stage là tập học song song, cùng stage chưa bảo đảm học trước | định nghĩa stage |
| U1 = 26,1% / 15,2% | Hai số đó chấm trên **vàng giao** (`gold_mode: intersection`, 23 / 46 cạnh), trong khi P/R chấm trên vàng hội ý — hai bảng khác đối tượng | trường `gold_mode` trong hai tệp `*-roadmap-score.json` |
| Mục 12 gọi "lớp một mình" là vỡ **U5** | Lớp một mình thuộc **U4**; U5 là độ phủ node | bảng U ở mục 1 |

Và C9 trên bộ cạnh **sau** C1: lỗi học trước **7,5% → 7,5%**, số lớp **30 → 34**. C1 đã hấp thụ toàn bộ lợi ích
của C9 trên `doc-1`; hiệu quả hai can thiệp **không cộng được**.

### U1 chính thức từ nay: `learning_order_error` trên vàng hội ý

`learning_order_error = (ngược + cùng lớp + thiếu đầu) / |vàng|`. Bộ vàng rỗng → **chưa đánh giá**, không phải
đạt. Đã cài vào `gold_order_violations` và `score_roadmap_order`; bộ chấm nay **từ chối** vàng khác `doc_id`,
khác phiên bản canonical, hoặc nhắc khái niệm đồ thị không có, và ghim SHA-256 của mọi tệp đã đọc. 7 test mới,
cả 7 đã được thấy đỏ trước khi có mã; toàn suite 485/485.

| | lớp | tôn trọng | ngược | cùng lớp | thiếu đầu | **U1** | chỉ số cũ | τ |
|---|---|---|---|---|---|---|---|---|
| `doc-1` v7 | 29 | 28 | 9 | 3 | 0 | **30,0%** | 24,3% | +0,087 |
| `doc-1` v10 (C1) | 30 | 37 | 1 | 2 | 0 | **7,5%** | 2,6% | +0,436 |
| `doc-2` v7 | 55 | 49 | 11 | 1 | 0 | **19,7%** | 18,3% | +0,125 |

Báo cáo đầy đủ: `artifacts/a8-gold/<doc>-v<n>-roadmap-score-vang.json`.

### Giải phẫu 29 cạnh dư của C1 — và giới hạn của chính phép chấm precision

Theo phạm vi chính thức: **10 suy ra được từ bao đóng vàng** (thừa nhưng vô hại cho thứ tự), **19 lạ**, **0 ngược
chiều**; 18 cạnh mới so với v7, không cạnh vàng nào mất. Đọc 19 cạnh lạ — **cách đọc của reviewer, chưa phải nhãn**:

| nhóm | ~số | ví dụ | can thiệp đúng chỗ |
|---|---|---|---|
| nhầm ví dụ / trường hợp riêng với định nghĩa | 4 | `Cộng ma trận → Không gian véc tơ`; `Véc tơ → Hàm thực liên tục` ("C[a,b] là một ví dụ") | C10 |
| nối bằng định lý hoặc động cơ, không phải định nghĩa | 4 | `Độc lập tuyến tính cực đại → Số chiều` (qua Định lý 2); `Hệ PT tuyến tính → Không gian véc tơ` ("motivated by") | C10 → quan hệ mềm |
| vướng danh tính node | 5 | `Hệ véc tơ độc lập tuyến tính` và `Độc lập tuyến tính` là hai node một khái niệm; `Phần tử trung hòa` hai nghĩa | xung đột danh tính |
| trông đúng mà vàng không có | 6 | `Vô hướng → Không gian véc tơ` (ba biến thể); `Nhóm → Phần tử trung hòa` | không phải lỗi máy? |

Nhóm cuối là điểm mấu chốt: **precision so với vàng đóng băng không phân biệt được "máy sai" với "vàng không
liệt kê"**. Người gán có thể đã cố ý không ghi `Vô hướng → Không gian véc tơ` vì coi `Trường` là tiên quyết trực
tiếp — đó là quyền của họ, và tôi không được tự "sửa" vàng. Cách đo đúng là **cho người gán chấm mù một mẫu**
gồm cạnh dư của máy trộn với cạnh đúng và cặp ngẫu nhiên làm đối chứng. Việc này cần người.

### Sổ chi phí

Mẻ C1 trên `doc-1` tốn **2,71 USD** (pass phụ; pass chính được tái dùng, 0,25 USD đã tính từ trước). Tổng đã
tiêu ≈ **12,2 / 50 USD**. Con số 9,50 ở mục 2 là số **trước** C1.

### Tập kiểm giữ lại

Hai chương vàng đã dùng để chẩn đoán, chọn can thiệp, so `k` và chọn C9 — nay chúng là **dữ liệu phát triển**.
Bộ gán `xstk-ch3-1-chuong-10-13` (A1, A2, hội ý; 18–20/09) mới chỉ dùng cho E1 ở vé 16, **chưa từng dùng để
chọn can thiệp A8/A10**. Nó là ứng viên tốt nhất hiện có cho tập giữ lại — nhưng không nguyên sơ, và phải được
**khoá từ bây giờ**: không mở nhãn cho tới lần xác nhận cuối. Chủ dự án quyết.

### Bộ tiêu chí sửa theo thẩm định

- **U1** = `learning_order_error` trên vàng hội ý, như trên.
- **U4** tách làm ba: *bắt buộc* (0 vi phạm cạnh cứng, không vượt trần, mỗi node đúng một lần); *mềm* (ít stage
  vụn, mỗi stage nhỏ có lý do); *hiệu suất* (báo số stage / cận dưới). Bỏ "số stage = cận dưới" khỏi phần bắt buộc:
  phản ví dụ 3 node → M → 3 node, W = 2 cần 5 stage trong khi cận dưới là 4, và stage chứa M buộc phải đơn lẻ.
- **U0b** = **0 xung đột danh tính chưa được xử lý**. Chung alias là lý do đưa cặp ra xét, không phải bằng chứng
  trùng: `ℒ(V,W)` và `Linear map` cùng alias `linear maps` mà một bên là tập các ánh xạ.
- **Nhãn bằng chứng không phải nhãn mức bắt buộc.** `trong_dinh_nghia` là *dạng* bằng chứng; cứng hay mềm phải
  do một bước kiểm quan hệ quyết, không suy thẳng từ nhãn.

### Thứ tự mới — nhận khung P0–P3 của bản thẩm định

1. **P0 — đã xong phần mã:** bộ chấm thứ tự, kiểm danh tính, ghim tệp. Phần còn lại: đổi tên U4/U0b trong mọi
   cổng, và ca `Matrix → Nonnegative integers` ở `doc-2` (máy và vàng ngược nhau, gây SCC khi gộp).
2. **P1a — C8 đo offline trước:** nhãn vai trò vùng văn bản, node đủ điều kiện lên lộ trình, vị trí dạy sạch —
   đo trên **bộ cạnh cố định**, chưa chạy lại A8. Chỉ chạy lại A8 nếu phép đo offline cho thấy đáng.
3. **P1b — C10:** hồ sơ chứa đoạn dạy của **cả hai** đầu, câu hỏi hẹp "định nghĩa của B có dùng A không", có quyền
   trả `unresolved`. **Cổng khoá trước:** gói C1 + C10 phải qua đúng cổng mà C1 một mình đã trượt — so với v7,
   precision giảm không quá 0,05 (tức ≥ 0,606), và mất không quá 1 trong 26 cạnh vàng đã tìm được. Không dời cột gôn.
4. **C1 không mở rộng sang `doc-2`** cho tới khi gói C1 + C10 qua cổng trên `doc-1`.
5. **P2:** C2 với planner thật và trần token; so CG / C9 / bộ xếp theo tập sẵn sàng trên **cùng đồ thị**; tên,
   mục tiêu và nguồn đọc của stage.
6. **P3:** xác nhận trên tập giữ lại; pilot người học.

Ý tưởng curriculum planner trong `feedbackd1.md`: nhận đánh giá ở mục 9 của bản thẩm định — làm một planner tĩnh
có ràng buộc cứng ở P2; **bác** tạo cạnh từ độ gần embedding (đối xứng, trong khi tiên quyết có hướng), điểm tự
báo của mô hình, và RL/BKT khi chưa có dữ liệu người học.

---

## 14. C8 sửa lại: kiểm **nguồn dạy** ở cấp (node, đoạn) — đăng ký trước khi chạy (2026-09-23)

### Đính chính thêm: ô nhiễm đề cương nhỏ hơn tôi báo sáu lần

Mục 11 nói **49/225 (22%)** khái niệm có vị trí trong vùng đầu sách. Ngưỡng tôi dùng (< 40) nuốt cả Chương 1, vốn
bắt đầu ở chunk 16. Đếm đúng ranh giới: **8/225 (3,6%)** — 3 node hành chính (`Thang điểm chữ`, `Thi viết rọc
phách`, `Điểm đánh giá học phần`, đứng lớp 1–2) và 5 khái niệm thật bị đề cương làm lệch vị trí (`Dạng toàn phương`,
`Vành`, `Đa thức`, `Số phức`, `Phân thức hữu tỉ`). Hệ quả: lý do "C8 phải chạy trước C9 vì 22% chỉ số hỏng" mất
phần lớn sức nặng.

### Vì sao không phân loại theo vùng

Rác của `doc-3` chỉ một phần nằm ở vùng hành chính (`Homework assignments`, `Final project` ở slide *Grading*;
`Python` ở slide *Prerequisites*). Phần còn lại là **nhãn trong ví dụ và hình vẽ giữa bài giảng**: `GPA`,
`Experience` (biến của bộ dữ liệu ví dụ), `Top/Middle/Bottom node` (nhãn hình). Phân loại vùng không bắt được.
Nên câu hỏi đặt ở cấp **(node, đoạn định nghĩa)**: đoạn này dạy khái niệm, chỉ nhắc tên, liệt kê nó như kiến thức
cần có trước, hay thứ này không phải kiến thức của môn học?

### Thiết kế

- Stage mới `teaching` giữa `validated` và `stages`: không chạy lại A8/A9. Ghi **thêm** `teaching_status`,
  `teaching_chunk_ids`, `teaching_order_index` — **không sửa** `defining_chunk_ids`, nên `concept_hash` của vàng
  đóng băng giữ nguyên.
- Năm phán quyết cho mỗi cặp: `teaches` / `mentions_only` / `prior_knowledge` / `not_subject_matter` / `uncertain`;
  `teaches`, `prior_knowledge`, `not_subject_matter` phải kèm câu trích **có thật trong đoạn**.
- **Chỉ loại khỏi stage hai trạng thái**: `not_subject_matter` và `prior_knowledge` (hiện ở danh sách "kiến thức
  nền"). Node chỉ được nhắc tên **vẫn giữ**, gắn cờ — vì `Neural Networks` của `doc-3` có đoạn định nghĩa duy nhất
  là một slide liệt kê, trong khi cả bài dạy về nó. Loại theo "không có đoạn dạy" sẽ xoá chủ đề chính của bài.
- Có `teaches` thì thắng mọi phán quyết khác (giữ node, gắn cờ mâu thuẫn).
- Cạnh qua node bị loại được **co lại** (A → X → B thành A → B), để bỏ node không làm mất ràng buộc học trước.
- ~1215 cặp trên cả 7 tài liệu, ~0,2 USD.

### Nhãn tham chiếu `doc-3`, khoá trước khi chạy

Cách đọc của reviewer, **không phải vàng**; chỉ dùng để quyết cổng của C8.

- **Phải loại (13):** Class participation, Final project, Homework assignments, Experience, GPA, Top node,
  Middle node, Bottom node, A few numbers, A single number, Multi-modal example, Python, Machine learning concepts.
- **Phải giữ (33):** Artificial Intelligence, Traditional approach, Polanyi's Paradox, Machine Learning,
  Classification and Regression Tree, Linear Regression, Machine Learning Model, Support Vector Machines,
  Gradient Boosted Machines, Neural Networks, Random Forests, Feature extraction, Deep Learning, GenAI,
  Logistic Regression, Independent variables, Coefficients, Intercept, linear functions, Layer, Dense,
  Activation function, Linear activation function, ReLU, Hidden layers, Input variables, Output variable,
  output layer, Sigmoid activation function, Input Layer, parameters, Feedforward neural network,
  Network architecture.
- **Lưng chừng, không chấm (12):** 34-layer plain, 34-layer residual, VGG-19, Sensor, Human bottleneck, Smart
  representations, Axon, Dendrite, Synapse, Stable Diffusion, MusicLM, Output layer node.

### Cổng nhận, khoá trước khi chạy

1. `doc-3`: loại **≥ 10/13** node phải loại, và loại nhầm **≤ 1/33** node phải giữ.
2. `doc-1`: loại cả 3 node hành chính; **U1 không được tăng** (tức 0 đầu cạnh vàng bị loại — bộ chấm mới tính đầu
   cạnh vắng mặt là lỗi); đọc tay **mọi** node bị loại, loại nhầm **≤ 2**.
3. Toàn kho: 0 cạnh cứng vi phạm trong lộ trình mới; số stage không tăng.

Trượt bất kỳ cổng nào thì **không** nhận C8, và đọc nguyên nhân trước khi sửa gì.
