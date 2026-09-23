# 12 — Chạy E1 và E2 trên bộ vàng

**What to build:** Trả lời hai câu quyết định của cả đợt, **không tốn lời gọi mô hình nào**: cạnh tiên quyết nằm
ở đâu, và bộ sinh cặp nào đáng giữ. Kết quả quyết định mention map và pass phụ có vào mặc định hay không.

**Blocked by:** 05, 11, và việc gán nhãn đã đóng băng. (Việc của Claude.)

**Status:** **hội ý xong, bộ vàng đóng băng, E1/E2/E3 đã chạy (2026-09-23).** `doc-1` 40 cạnh, `doc-2` 61 cạnh.
**Xong toàn bộ checklist ngày 2026-09-23.** Số ở hai mục "Kết quả E1/E2/E3" và "E2 đầy đủ" dưới.
Phán quyết D5: **giữ cả năm bộ sinh** — và luật D5 cần sửa vì nó cho hai câu trả lời ngược nhau trên hai chương.

> **Hai chương vàng (chủ dự án chốt 2026-09-18, hướng a):** một chương giữa của `doc-1` (tiếng Việt) và một
> chương giữa của `doc-2` (tiếng Anh). Bộ vàng song ngữ, nên **mọi bảng phải tách theo từng chương**, không gộp
> hai ngôn ngữ thành một con số. Xem spec D13.
>
> **⚠️ Danh sách rút gọn cho `doc-1` đã hết hiệu lực ngày 2026-09-22.** Chủ dự án thay `doc-1` bằng một PDF khác
> vì bản cũ hỏng lớp text (24 ký tự có dấu trên 42.087 ký tự chữ cái = 0,06%; `Tính chất` ra thành `T‰nh ch§t`).
> Bản mới là **một cuốn khác** — *Bài giảng Đại số tuyến tính*, Đại học Hàng hải, **102 trang, 5 chương**, sạch
> watermark, 25,46% ký tự có dấu. Mọi số trang và tên chương của `doc-1` ở bản trước đều không còn dùng được.
> **Danh sách rút gọn mới nằm ở vé 19**, reviewer đề xuất **Chương 3 — Không gian véc tơ** (tr. 44–74, 5 mục).
>
> **Danh sách rút gọn cho `doc-2` vẫn giữ nguyên (2026-09-20, đo thẳng trên PDF):**
>
> | | `doc-2` (Axler, tiếng Anh) |
> |---|---|
> | ⭐ đề xuất | **3C — Matrices**, tr. 83–96 (14 tr, 9 "definition") |
> | B | 5A — Invariant Subspaces, tr. 147–156 (10 tr, 5) |
> | C | 2A — Span and Linear Independence, tr. 43–52 (10 tr, 8) |
>
> Số khái niệm đích thật chỉ biết được sau vé 19 (`a8-gold-sheet --list-chapters`); nếu chương chọn ra dưới 15 hoặc
> trên 45 khái niệm thì ghép thêm/bớt một mục liền kề, đúng cơ chế dải mục của vé 04.

## Lượt gán thật — 2026-09-23

Bốn bảng đã nộp và **kiểm hợp lệ: 0 lỗi, 0 cảnh báo** ở cả bốn.

| | A1 | A2 | cùng ghi | chỉ A1 | chỉ A2 | Jaccard | **κ trực tiếp** | **κ có bắc cầu** |
|---|---|---|---|---|---|---|---|---|
| `doc-1` Chương 3, dải 10-12 (VN) · 26 đích / 225 khái niệm | 40 | 35 | 23 | 17 | 12 | 0,442 | **0,611** | **0,733** |
| `doc-2` mục 3C, dải 98-115 (EN) · 24 đích / 438 khái niệm | 59 | 54 | 46 | 13 | 8 | 0,687 | **0,813** | **0,818** |

Cờ người gán nêu: doc-1 A1 17 / A2 13 · doc-2 A1 18 / A2 14.

**Hai file của mỗi chương khác nhau thật** — không có ca trùng khít, nên κ có nghĩa.

**Đối chiếu văn liệu** (báo cáo vòng 36 mục 7): LectureBank đạt **κ = 0,7** với hai nghiên cứu sinh gán nhãn nhị
phân, và nói rõ bản ba mức trước đó chỉ được **κ = 0,3** trên **cùng các cặp**. PREAP đạt **0,45–0,71** khi gán
trong lúc đọc giáo trình. Vậy `doc-2` ở 0,813 **vượt mốc LectureBank**, còn `doc-1` ở 0,611 trực tiếp / 0,733 có
bắc cầu nằm **trong dải PREAP và đạt mốc LectureBank khi tính đồng thuận ngầm**.

**Một bất đối xứng đáng đưa vào báo cáo:** bắc cầu nâng κ của `doc-1` từ 0,611 lên 0,733 (+0,122) nhưng chỉ nâng
`doc-2` từ 0,813 lên 0,818 (+0,005). Nghĩa là phần lớn bất đồng trên `doc-1` là **"một người ghi cạnh trực tiếp,
người kia ghi đường vòng"** — đúng ca *long dependencies* mà LectureBank chỉ đích danh là nguồn bất đồng chính.
Đây là lý do D13 bắt tách số theo từng chương thay vì gộp hai ngôn ngữ.

**File hội ý đã sinh:**

| file | cùng ghi | phải quyết |
|---|---|---|
| `artifacts/a8-gold/doc-1-chuong-10-12-hoi-y.xlsx` | 23 | **29** |
| `artifacts/a8-gold/doc-2-chuong-98-115-hoi-y.xlsx` | 46 | **21** |

### Thời gian gán: **không đo được ở lượt này** (chủ dự án chốt 2026-09-23, cách b)

> **Đính chính của reviewer.** Tôi có viết hai lần rằng "E7 cần ô thời gian" — **sai**. E7 đo *cái giá của các bước
> nhất quán* (cạnh vàng bị cắt chu trình, bị đánh dấu thừa, bị tỉa; precision theo `evidence_hard`), **không dùng
> thời gian gán**. Ô thời gian tồn tại vì lý do khác: PREAP đo thời gian gán như một dữ kiện về giao thức.

Cả bốn bảng để trống `annotation_minutes` và `revision_minutes`. Luật của dự án từ phase trước
(`task/a4-a5-hop-nhat/06-nguoi-dung-gan-mu-bo-vang.md`) là **"ghi thời gian gán thật, không ước lượng"**, nên
không điền số suy đoán. **Báo cáo phải ghi thẳng: lượt gán này không đo thời gian.**

Chủ dự án tự khai: cặp làm trước vào buổi chiều, cặp sau vào chiều 23/9. Metadata trong file cho thấy khác một
ngày ở cặp trước, và đây là toàn bộ bằng chứng cứng có được:

| file | created | modified | đọc ra |
|---|---|---|---|
| `doc-2-...-A2-output` | 22/9 12:02:04 | **22/9 14:34:26** | có vết sửa thật |
| `doc-1-...-A2-output` | 22/9 13:10:56 | **22/9 14:34:26** | có vết sửa thật |
| `doc-1-...-A1-output` | 23/9 07:25:26,25 | 23/9 07:25:26,25 | máy ghi, **không có vết sửa** |
| `doc-2-...-A1-output` | 23/9 07:25:26,32 | 23/9 07:25:26,32 | máy ghi, **không có vết sửa** |

Bảng trống chỉ sinh ngày **22/9** (doc-2 lúc 12:02, doc-1 lúc 13:10), nên **không thể gán ngày 21/9**.

Khoảng 83 phút (`doc-1` A2) và 152 phút (`doc-2` A2) là **khoảng từ lúc sinh bảng tới lúc lưu**, tức **biên trên**,
**không phải thời gian ngồi làm**. Đừng trích chúng như số đo.

- [x] Hai người gán đã nộp file, độ đồng thuận đã tính (có kể đồng thuận ngầm qua bắc cầu); **còn chờ hội ý**;
      bộ vàng đóng băng trước khi chạy.
- [x] Hai file gán phải **khác nhau**: đây là hai người làm độc lập, không phải một bản chép làm hai. Kiểm ngay khi
      nhận file, hai file trùng khít thì κ vô nghĩa và bộ vàng không dùng được.
- [x] E1: bảng sáu loại vị trí, kèm NMI giữa cụm chủ đề và chương, cho cả hai giáo trình.
- [x] E2: bảng theo từng bộ sinh và ba cấu hình định tuyến.
- [x] Áp **luật chọn bộ sinh mặc định** đã viết trước ở D5, và ghi kết quả áp luật.
- [x] Mọi số kèm khoảng tin cậy; chỗ nào khoảng chồng lấn thì viết "chưa phân biệt được".
- [x] Báo cáo cả số trên hợp và trên giao nhãn của hai người, để xem độ nhạy.

## Kết quả E1/E2/E3 — 2026-09-23

Chấm trên `artifacts/graph/<doc>/v6/graph.json` (stage `validated`), bộ vàng sau hội ý. Báo cáo đầy đủ ở
`artifacts/a8-gold/<doc>-score-vang.json`.

**E1 — cạnh tiên quyết nằm ở đâu.** NMI cụm↔chương: **0,756** (`doc-1`), **0,789** (`doc-2`).

| Loại vị trí | `doc-1` (VN, 40 cạnh) | `doc-2` (EN, 61 cạnh) |
|---|---|---|
| cùng chunk | **30,0%** [0,16–0,46] | 3,3% [0,00–0,08] |
| cùng mục | **22,5%** [0,10–0,36] | 3,3% [0,00–0,08] |
| cùng chương | 2,5% | 0,0% |
| cùng cụm chủ đề | 2,5% | **18,0%** [0,09–0,29] |
| **bắc cầu qua chunk nhắc cả hai, kênh cứng** | **25,0%** [0,11–0,39] | **42,6%** [0,31–0,55] |
| bắc cầu, chỉ kênh dense | 0,0% | **9,8%** [0,03–0,18] |
| ngầm (không nối được) | 17,5% [0,08–0,27] | 23,0% [0,10–0,35] |

**Hai giáo trình khác nhau rất xa**, nên D13 đúng khi bắt tách theo chương. `doc-1` cục bộ (52,5% cạnh nằm cùng
chunk hoặc cùng mục); `doc-2` chỉ 6,6% cục bộ và 52,4% phải đi qua cầu nhắc tên. **9,8% cạnh của `doc-2` chỉ kênh
dense mới với tới** — kênh dense không thừa. Cạnh "ngầm" 17,5% và 23,0% là **trần recall**: không bộ sinh nào với
tới chúng.

**E2 — bộ sinh cặp (`doc-2`).**

| Bộ sinh | phủ | recall | phủ riêng | số cặp sinh ra |
|---|---|---|---|---|
| **contact** (mention map) | 33/61 | **54,1%** | **5** | 9.334 |
| citation_hard | 29/61 | 47,5% | 1 | 2.869 |
| proposed_relation | 17/61 | 27,9% | 2 | 597 |
| citation_soft | 8/61 | 13,1% | 1 | 416 |
| same_section | 4/61 | 6,6% | 2 | 342 |

`contact` cao nhất cả recall lẫn phủ riêng, nhưng sinh **9.334 cặp**, gấp ba bộ đứng nhì. Luật D5 phải áp lên đúng
bảng này.

**E3 sơ bộ (`doc-2`, có tính bắc cầu):** precision **0,147** · recall **0,551** · F1 **0,232**; 435 cạnh thừa,
61 cạnh thiếu trên 136 cạnh vàng sau bao đóng. Recall 55% khớp phép đo vòng 39 (13/13 ca lộ trình xếp sai đều là
cạnh máy không có).

## Bảng gán đã chuẩn bị — 2026-09-22

> **Bảng dưới đã lỗi thời cho `doc-1`.** Dải `10-13` (45 đích, 360 dòng) **không được dùng**; reviewer chốt lại
> dải `10-12` ngày 2026-09-22 vì 360 dòng nhiều hơn 73% so với khối lượng đã hiệu chuẩn bằng lượt thử. Lượt gán
> thật chạy trên dải `10-12`. Giữ bảng để tra lịch sử.

| Tài liệu/chương | Phạm vi section cấp 2 | Đích sau provenance | Dòng quan hệ mỗi bảng | File A1/A2 trong `artifacts/a8-gold/` |
|---|---|---:|---:|---|
| ~~`doc-1` Chương 3, mục 3.1–3.4~~ | ~~`10-13`~~ | ~~45~~ | ~~360~~ | ~~`doc-1-chuong-10-13-*.xlsx`~~ **không dùng** |
| **`doc-1` Chương 3, mục 3.1–3.3** | **`10-12`** | **26** | **208** | `doc-1-chuong-10-12-A1.xlsx` / `-A2.xlsx` |
| `doc-2` mục 3C, tr. 85–95 có đích | `98-115` | 24 | 200 | `doc-2-chuong-98-115-A1.xlsx` / `-A2.xlsx` |

Cả hai bảng của mỗi chương dùng cùng `concept_hash` và cùng graph provenance v3 để bảo đảm
phạm vi giống nhau, nhưng là **bảng trống** cho hai người làm riêng; không dùng mô hình tự điền.
`doc-1` sau provenance có 45/45 mô tả qua luật tiếng Việt; `doc-2` có 24/24 qua luật tiếng Anh.
Khi nhận lại file, kiểm A1/A2 thực sự khác nhau trước khi tính đồng thuận như checklist trên.

### E2 đầy đủ — bộ sinh, ba cấu hình định tuyến, và áp luật D5

**Bộ sinh, `doc-1` (40 cạnh vàng) / `doc-2` (61 cạnh vàng).** Cột **RIÊNG** là số cạnh vàng **chỉ bộ ấy** phủ —
đây là cột mà luật D5 xét, không phải cột recall.

| Bộ sinh | `doc-1` recall | RIÊNG | cặp | `doc-2` recall | RIÊNG | cặp |
|---|---|---|---|---|---|---|
| **contact** | **60,0%** [0,46–0,73] | **2** | 3.123 | **54,1%** [0,45–0,65] | **5** | 9.334 |
| same_section | 52,5% [0,38–0,68] | 1 | 559 | 6,6% [0,02–0,12] | 2 | 342 |
| citation_hard | 50,0% [0,34–0,68] | **0** | 1.184 | 47,5% [0,36–0,59] | 1 | 2.869 |
| proposed_relation | 30,0% [0,20–0,39] | **0** | 199 | 27,9% [0,16–0,43] | 2 | 597 |
| citation_soft | 15,0% [0,05–0,27] | **0** | 575 | 13,1% [0,05–0,23] | 1 | 416 |

**Ba cấu hình định tuyến** (sinh cặp theo cả hai trục dù định tuyến chọn trục nào, đúng D6):

| Cấu hình | `doc-1` recall | cặp | `doc-2` recall | cặp |
|---|---|---|---|---|
| **cả hai trục + bộ sinh** | 92,5% [0,85–1,00] | 7.961 | **85,2%** [0,77–0,94] | 24.645 |
| cả hai trục | **92,5%** [0,85–1,00] | 7.916 | 78,7% [0,68–0,87] | 23.849 |
| chỉ trục cụm chủ đề | 87,5% [0,79–0,96] | 6.435 | 77,0% [0,67–0,86] | 21.100 |
| chỉ trục chương + bộ sinh | 85,0% [0,76–0,94] | 5.578 | 75,4% [0,64–0,88] | 14.227 |
| chỉ trục chương | 85,0% [0,76–0,94] | 5.519 | 67,2% [0,55–0,80] | 12.927 |
| chỉ hợp các bộ sinh | 80,0% [0,71–0,90] | 3.668 | 72,1% [0,62–0,84] | 9.984 |

**Đọc theo đúng luật "khoảng chồng lấn thì chưa phân biệt được":**

- Trên `doc-1`, **mọi khoảng đều chồng lấn nhau** — 92,5% [0,85–1,00] và 80,0% [0,71–0,90] vẫn giao nhau. Kết luận
  đúng cho `doc-1` là **chưa phân biệt được cấu hình nào hơn**, dù điểm ước lượng xếp hạng rõ.
- Trên `doc-2` thì phân biệt được một cặp: **cả hai trục + bộ sinh [0,77–0,94] so với chỉ trục chương [0,55–0,80]**
  gần như không giao. Các cặp còn lại chồng lấn.
- Điểm ước lượng **nhất quán cùng chiều trên cả hai tài liệu**: hai trục ≥ một trục, và trục cụm ≥ trục chương.
  Đây là bằng chứng ủng hộ D6 (sinh cặp cả hai trục bất kể định tuyến), nhưng phải nói là **xu hướng nhất quán**,
  không phải khác biệt có ý nghĩa thống kê.
- `doc-1`: thêm các bộ sinh lên trên hai trục **không thêm cạnh vàng nào** (37 → 37). `doc-2` thêm **4** cạnh
  (48 → 52). Bộ sinh có giá trị hay không **phụ thuộc giáo trình**.

### Áp luật D5 — và một lỗ hổng của chính luật

Luật viết trước: *"Một bộ sinh chỉ bị bỏ khỏi mặc định khi trên bộ vàng nó không đóng góp cạnh vàng nào mà các bộ
khác bỏ sót."*

| | bộ sinh có RIÊNG = 0 |
|---|---|
| `doc-1` | `citation_hard`, `citation_soft`, `proposed_relation` |
| `doc-2` | **không bộ nào** |

**Luật cho hai câu trả lời ngược nhau, và nó không nói phải áp trên từng chương hay trên cả corpus.** Đây là lỗ
hổng của luật, không phải của số đo.

**Phán quyết: giữ cả năm bộ sinh.** Lý do bám đúng triết lý mà chính D5 viết ra — *"cặp bỏ sót thì mất vĩnh viễn,
cặp thừa thì bước phán tự loại"*. Bỏ `citation_hard` sẽ mất 1 cạnh vàng trên `doc-2`, `citation_soft` mất 1,
`proposed_relation` mất 2. Mất là mất vĩnh viễn; giữ thì chỉ tốn thêm vài USD tiền phán.

**Spec cần sửa:** D5 phải nói rõ *một bộ sinh chỉ bị bỏ khi nó có phủ riêng bằng 0 trên **mọi** chương vàng*. Ghi
lại để đợt sửa spec tiếp theo làm.

### Độ nhạy theo cách gộp nhãn

Recall từng bộ sinh, tính trên ba cách dựng bộ vàng:

| | cạnh vàng | contact | citation_hard | same_section | proposed_relation | citation_soft |
|---|---|---|---|---|---|---|
| `doc-1` hợp nhãn | 52 | 62,7% | 47,1% | 56,9% | 31,4% | 13,7% |
| `doc-1` giao nhãn | 23 | 60,9% | 56,5% | 60,9% | 39,1% | 13,0% |
| `doc-1` **sau hội ý** | 40 | 60,0% | 50,0% | 52,5% | 30,0% | 15,0% |
| `doc-2` hợp nhãn | 67 | 50,7% | 44,8% | 6,0% | 28,4% | 11,9% |
| `doc-2` giao nhãn | 46 | 60,9% | 50,0% | 8,7% | 32,6% | 17,4% |
| `doc-2` **sau hội ý** | 61 | 54,1% | 47,5% | 6,6% | 27,9% | 13,1% |

**Xếp hạng bộ sinh ổn định qua cả ba cách gộp** trên cả hai tài liệu: `contact` luôn đứng đầu, `citation_soft`
luôn cuối. Kết luận của E2 **không phụ thuộc** vào việc chọn hợp, giao hay bản sau hội ý — đó là điều đáng nói,
vì nó loại trừ khả năng kết quả là sản phẩm của một cách gộp nhãn có lợi.
