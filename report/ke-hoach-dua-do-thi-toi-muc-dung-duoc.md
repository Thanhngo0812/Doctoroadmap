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
