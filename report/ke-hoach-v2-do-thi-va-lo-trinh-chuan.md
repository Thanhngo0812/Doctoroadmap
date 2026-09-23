# Kế hoạch v2 — đồ thị và lộ trình chuẩn, không bám luồng cũ

Ngày 2026-09-23. Thay phần "việc tiếp theo" của [kế hoạch đưa đồ thị tới mức dùng được](ke-hoach-dua-do-thi-toi-muc-dung-duoc.md)
(mục 1–18 vẫn là nhật ký và bằng chứng). Mọi con số dưới đây đo trên artifact thật, bằng mã trong repo hoặc script ghi
đường dẫn; không có con số nào là ước lượng trừ khi ghi rõ.

> **Cập nhật 2026-09-23:** chủ dự án duyệt toàn bộ kế hoạch và ngưỡng. Thiết kế chi tiết ở
> [`doc/v2-do-thi-va-lo-trinh-neo-van-ban-spec.md`](../doc/v2-do-thi-va-lo-trinh-neo-van-ban-spec.md), vé ở
> [`task/v2-do-thi-lo-trinh/`](../task/v2-do-thi-lo-trinh/00-ke-hoach.md), việc của chủ dự án ở vé 10. Q8 bỏ ngưỡng tự
> động (chia module theo mục tự tối ưu chỉ số đó); chỉ còn ngưỡng chấm người ≥ 4/5.

## 0. Tóm tắt

Sau 18 mục thí nghiệm, lỗi của sản phẩm quy về **bốn gốc**, và luồng hiện tại đặt sai trọng tâm ở hai gốc:

1. **Tầng lộ trình (A10) xếp sai thứ ưu tiên.** Coffman–Graham tối ưu *số stage* rồi xáo thứ tự sách ở mọi cặp không có
   cạnh. Đo lại: chỉ cần sắp topo **ưu tiên vị trí trong sách** là lỗi thứ tự giảm **10,0% → 5,0%** (`doc-1`) và
   **14,8% → 8,2%** (`doc-2`), không tốn đồng nào. Định nghĩa "stage = nhóm học song song" là thứ khiến một thứ tự tốt
   bị băm thành 98–142 stage; phải đổi đơn vị trình bày sang **module có thứ tự bên trong**.
2. **Recall cạnh vẫn là nút thắt của thứ tự.** Tỉ lệ cạnh vàng có đường đi trong đồ thị máy: `doc-1` 80% (sau C1),
   `doc-2` 56%. Lộ trình tới một mục tiêu đủ trọn tập cần học: 9/24 và **0/23** đích.
3. **Node thiếu neo định nghĩa.** Provenance hay trỏ vào đoạn *dùng* thay vì đoạn *dạy*, làm hỏng dây chuyền: loại nhầm
   khái niệm (C8), hồ sơ phán cạnh (C10), nguồn đọc, vị trí dạy, và cả bộ dò cạnh rẻ nhất.
4. **Thước đo chưa đủ để nói "chuẩn".** Precision so với vàng không phân biệt máy sai với vàng thiếu; U1 của CG dao
   động ±2,6–3,0 điểm chỉ vì cách phá thế hoà; chưa có tập giữ lại sạch và chưa có thước đo nào cho node.

Kế hoạch: **neo mọi thứ vào văn bản** — thứ tự vào thứ tự dạy của sách, khái niệm vào câu định nghĩa nguyên văn, cạnh
vào câu nhắc tên trong định nghĩa — rồi dùng mô hình cho đúng phần mà văn bản không tự nói ra. Bảy gói công việc,
tổng dự chi ≈ 4–12 USD trên số dư ≈ 36 USD.

## 1. "Chuẩn" nghĩa là gì — tiêu chí đo được

Bộ U0–U7 cũ trộn thứ đo được với thứ không, và vài tiêu chí đo nhiễu (mục 17 kế hoạch cũ). Đề xuất thay bằng mười tiêu
chí, mỗi tiêu chí có **một phép đo cụ thể**. Ngưỡng là **mục tiêu đề xuất**, chủ dự án chốt trước lần xác nhận cuối;
không dùng chúng để đổi cách gọi kết quả cũ.

| | tiêu chí | phép đo | hiện tại (`doc-1` / `doc-2`) | mục tiêu đề xuất |
|---|---|---|---|---|
| Q1 | node trên lộ trình là kiến thức môn học | kiểm tay mẫu ngẫu nhiên 50 node / tài liệu | chưa đo | ≥ 97% |
| Q2 | không trùng, không đa nghĩa chưa xử lý | số xung đột danh tính còn mở trong phạm vi xuất bản | ≥ 9 (alias) + trùng tên đã thấy | 0 |
| Q3 | không sót khái niệm trọng yếu | người đọc liệt kê mù trên mục lấy mẫu, so với node máy | chưa đo | ≥ 90% |
| Q4 | cạnh đúng | chấm mù (`scripts/cham-mu/`): tỉ lệ "không làm sai thứ tự học"; tỉ lệ ngược chiều | đang chờ người gán | ≥ 0,90; ngược ≤ 5% |
| Q5 | đủ ràng buộc | tỉ lệ cạnh vàng có đường đi trong đồ thị máy | 80% / 56% | ≥ 85% |
| Q6 | thứ tự lộ trình | `U1_tuyến tính` = (ngược + thiếu đầu) / \|vàng\| trên dãy học | 5,0% / 8,2% (với A10 mới) | ≤ 5% |
| Q7 | lộ trình tới mục tiêu | trung bình tỉ lệ tổ tiên-vàng có trong tổ tiên-máy; số đích đủ trọn | 89%, 9/24 / 58%, 0/23 | ≥ 95%; ≥ 80% đích |
| Q8 | module mạch lạc | tỉ lệ module nằm gọn trong một mục (tự động) + thang 1–5 hai người chấm mù | 16/34 (A10 mới) vs 1/30 (CG) | ≥ 60%; ≥ 4/5 |
| Q9 | nguồn đọc đúng | kiểm tay mẫu neo định nghĩa | chưa đo | ≥ 90% |
| Q10 | khái quát | Q1–Q9 trên tập giữ lại, cấu hình đã khoá | chưa đo | trong dung sai đã chốt |

Q6 thay U1 cũ vì A10 mới trình bày một **dãy có thứ tự**; nó tất định (không phụ thuộc may rủi phá thế hoà), nên không
cần giao thức nhiễu. Q5 là phần **tất định của chất lượng đồ thị**, tách khỏi A10.

## 2. Chẩn đoán — lỗi đến từ đâu

| tầng | triệu chứng | bằng chứng | gốc |
|---|---|---|---|
| node | rác trên lộ trình (`GPA`, `Thang điểm chữ`, nhãn hình) | ~20% node `doc-3`; 3 node `doc-1` | trích khái niệm từ mọi đoạn, kể cả đề cương và ví dụ |
| node | loại nhầm khái niệm được dạy | C8 v2 trên `doc-2`: 3/6 ca kích bởi "Suppose V is…" | provenance trỏ vào đoạn dùng |
| node | trùng / đa nghĩa | `Hệ véc tơ độc lập tuyến tính` ≡ `Độc lập tuyến tính`; `Véc tơ`; 9 alias trùng | danh tính theo tên, không theo định nghĩa |
| cạnh | thiếu ràng buộc | Q5 80% / 56%; 13/13 lỗi thứ tự ban đầu là cạnh thiếu | bộ sinh cặp phủ ~77–80%; phiên pass chính không thấy cặp |
| cạnh | "dư" so với vàng | 29 cạnh dư `doc-1`: 10 suy ra được, 0 ngược chiều, phần lớn hợp lý | vàng không liệt kê hết + trùng danh tính |
| A10 | thứ tự lệch sách, stage lộn xộn | CG xáo thứ tự ở cặp không cạnh; 1/30 stage nằm gọn một mục | tối ưu số stage, bỏ qua thứ tự dạy |
| đo | con số không phân định được | precision so vàng; U1 ± 2,6–3,0 | vàng một phần; thước đo phụ thuộc phá thế hoà |

## 3. Bốn phát hiện của lần phân tích này

**3.1. Đồ thị + thứ tự sách là thứ tự tốt nhất đo được.** Cùng tập node và cạnh (`doc-1` v14, `doc-2` v9):

| | `doc-1` | `doc-2` |
|---|---|---|
| sách tự đặt ngược cạnh vàng | 5 / 40 | 7 / 61 |
| **sắp topo ưu tiên vị trí sách** (dãy) | **2 / 40** | **5 / 61** |
| CG, đọc mỗi stage theo sách | 2 / 40 | 9 / 61 |

Sách là một thứ tự do chuyên gia soạn nhưng sai ~12% cạnh vàng; đồ thị sửa được **3/5** và **2/7** chỗ sai đó. Đây là
giá trị đồ thị đem lại so với "đọc sách từ đầu" — và là con số mà bản thẩm định đòi (*baseline theo nơi dạy*).

**3.2. Khái niệm "stage song song" là thứ phá hỏng thứ tự tốt.** Cắt dãy tốt thành các nhóm không chứa cạnh thì ra 98
(`doc-1`) và 142 (`doc-2`) stage; CG giữ được 30/54 stage bằng cách hy sinh thứ tự. Gom dãy thành **module liền mạch
có thứ tự bên trong** (≤ 8 khái niệm, ưu tiên cắt ở ranh giới mục): `doc-1` 34 module, **16/34** nằm gọn một mục, so
với **1/30** stage của CG. Trên `doc-2` cách cắt thử quá vụn (97 module) vì cấp mục của sách Axler rất mịn — cấp mục dùng
để cắt phải chọn theo từng tài liệu.

**3.3. Cạnh "nằm trong định nghĩa" dò được 37–48% mà không gọi mô hình.** Bộ vàng có 29/40 và 49/61 cạnh loại này; bộ
dò bắt được 14/29 và 18/49 trong số đó. Dò
"câu căn cứ nguyên văn của B nhắc tên hoặc alias của A": bắn 71 và 69 cặp, trúng 16 và 22 cạnh vàng (P 0,23 / 0,32), và
chỉ ra **2 và 4 cạnh vàng mà máy chưa có**. Quá nhiễu để làm cạnh, nhưng là **bộ sinh ứng viên rẻ nhất**: C1 phải hỏi
9 984 cặp (~7,4 USD) cho `doc-2`. Recall của bộ dò bị kìm vì câu căn cứ hiện là câu A3 dùng để trích, không phải câu định
nghĩa — neo định nghĩa (gói B) sẽ nâng nó.

**3.4. Lộ trình tới một mục tiêu — giá trị riêng của đồ thị — đang phụ thuộc hẳn vào recall.** `doc-1` sau C1 phủ 89%
tập cần học; `doc-2` 58%. Chuỗi dài nhất 26 bước của `doc-1` là xương sống thật của giáo trình (`Tập hợp → … → Ma trận
nghịch đảo → Hệ PT tuyến tính → Không gian véc tơ → … → Định lý về số chiều`), không phải cạnh rác chồng lên nhau.

## 4. Kiến trúc đề xuất

```text
B0  parse / chunk  (giữ; mục lục đã được bỏ)
A3–A4  khái niệm canonical  (giữ; không sửa để vàng đóng băng còn dùng được)
 ↓
[B] NEO ĐỊNH NGHĨA — mỗi node: câu dạy nguyên văn, vị trí dạy, trạng thái
      dạy ở đây / chỉ được nhắc / kiến thức nền có tín hiệu tường minh / không phải kiến thức môn học
      → thay provenance mơ hồ và C8; cấp vị trí cho A10, nguồn đọc, hồ sơ phán cạnh, bộ dò cạnh
[C] DANH TÍNH — bản đồ gộp/tách ở tầng graph (không sửa canonical), phán trên hai câu định nghĩa
 ↓
A8  cạnh: pass chính (giữ) + [D] ứng viên có mục tiêu (nhắc tên trong câu định nghĩa, gộp mục vụn C2)
      → phán cặp hai chiều như pass phụ hiện có
A9  nhất quán cấu trúc (giữ)
 ↓
[A] A10 NEO SÁCH — sắp topo ưu tiên vị trí dạy → module liền mạch (quy hoạch động, bám mục) → thứ tự bên trong module
[E] LỘ TRÌNH TỚI MỤC TIÊU — tổ tiên của đích, cùng thứ tự và cách chia module của [A]
 ↓
trình bày: tên module, mục tiêu, nguồn đọc từ neo, vì sao khái niệm đứng ở đó (cạnh vào)
```

Hai nguyên tắc xuyên suốt:

- **Văn bản làm chứng, mô hình làm phần còn lại.** Thứ tự dạy, câu định nghĩa, tên được nhắc trong định nghĩa đều là
  sự kiện kiểm được bằng mã. Mô hình chỉ phán chỗ văn bản không tự nói — và mọi phán quyết khẳng định phải kèm câu trích
  có thật.
- **Không sửa canonical trong đợt này.** Gộp/tách, loại node, vị trí dạy đều là lớp chú thích có version ở tầng graph,
  có bản đồ ID. Bộ vàng đóng băng tiếp tục chấm được; mọi ánh xạ vàng sang node mới là tệp riêng, không ghi đè.

## 5. Các gói công việc

### A — A10 neo sách (0 USD, làm trước)

**Thiết kế.**

1. *Dãy học*: sắp topo đồ thị `requires` bằng Kahn với hàng đợi ưu tiên theo vị trí dạy (neo định nghĩa khi có, tạm
   thời `teaching_order_index` rồi `first_order_index`), phá hoà bằng `node_id`. Đây là phần mở rộng tuyến tính gần
   thứ tự sách nhất theo nghĩa từ điển; luôn tôn trọng mọi cạnh.
2. *Module*: chia dãy thành đoạn liền mạch bằng quy hoạch động kiểu ngắt dòng (Knuth–Plass): chi phí = số module + phạt
   mỗi lần một module vắt qua ranh giới mục + phạt module dưới sàn; ràng buộc cứng ≤ W (mặc định 8). Cấp mục dùng để phạt
   chọn theo tài liệu: cấp sâu nhất mà trung vị số khái niệm mỗi mục ≥ W/2.
3. *Trình bày*: danh sách có thứ tự trong module; không tuyên bố "học song song" ở bản đầu (tuyên bố đó phải được chấm
   bằng thước đo khắt khe như `same_stage`).
4. `stage` cũ vẫn tính được như chú thích; CONTEXT.md thêm thuật ngữ **Module**.

**Hợp đồng đánh giá đổi theo:** τ so thứ tự sách từ nay là **độ bám sách**, không phải bằng chứng chất lượng (bản thẩm
định §3.8). V8 của spec A9–A10 được sửa có ghi lý do: lý do cấm cũ là nhiễm đối chứng τ, và đối chứng độc lập nay là
Q6 trên bộ vàng.

**Tài liệu mà thứ tự trình bày không đáng tin** (danh sách phẳng, tài liệu tra cứu): dãy học vẫn tôn trọng mọi cạnh; chỉ
phần phá hoà mất nghĩa. Phát hiện bằng tỉ lệ cạnh máy đi ngược thứ tự sách, ngưỡng chốt trước; khi vượt thì báo và
dùng phá hoà trung tính.

**Cổng.** Trên hai chương phát triển: Q6 không tệ hơn CG; Q8 tự động ≥ CG; 0 cạnh cứng bị vi phạm; mọi node đủ điều kiện
xuất hiện đúng một lần. Kết luận khái quát chỉ trên tập giữ lại (gói G).

### B — Neo định nghĩa cho từng node (~0,3–0,6 USD)

**Vấn đề.** `defining_chunk_ids` thường là đoạn dùng; C8 hỏi mô hình về đoạn dùng nên loại nhầm; bộ dò cạnh chỉ có câu
A3 dùng để trích.

**Thiết kế.** Với mỗi node: gom ứng viên từ đoạn định nghĩa hiện có + đoạn có mention cứng + đoạn căn cứ A3; lọc câu theo
tín hiệu định nghĩa (đã có sẵn trong provenance: "là", "được gọi là", "we define", "is called", …) và vị trí; một lời
gọi cho mỗi node trả về **một câu neo nguyên văn** (kiểm chuỗi bằng mã) hoặc: *chỉ được nhắc*, *kiến thức nền* (bắt buộc
có tín hiệu tường minh như "recall from a previous course", "requires familiarity with"), *không phải kiến thức môn học*.
Trạng thái node là thuộc tính của node (khắc phục lỗi gộp của C8 v2), với luật: có câu neo thì giữ.

**Dùng cho:** vị trí dạy (gói A), loại node (thay C8), nguồn đọc (Q9), hồ sơ phán cạnh (gói D), bộ dò cạnh (gói D), phán
danh tính (gói C).

**Cổng.** Kiểm tay 50 neo ngẫu nhiên trên ≥ 3 tài liệu: đúng câu dạy ≥ 90%. Loại node: trên nhãn `doc-3` đã khoá (bằng
chứng phát triển) và trên một nhãn node **mới** gán mù trước khi chạy.

### C — Danh tính: gộp, tách, đa nghĩa (~0,1 USD + người duyệt)

**Ứng viên:** alias trùng, tên chứa nhau (`Hệ véc tơ độc lập tuyến tính` / `Độc lập tuyến tính`), hai node cùng câu neo,
một tên có hai câu neo khác nghĩa. **Phán** trên hai câu neo: gộp / giữ tách và sửa alias / tách nghĩa có ngữ cảnh.
Chung alias là lý do đưa ra xét, không phải bằng chứng trùng. **Kết quả** là bản đồ ID ở tầng graph; A10 và bộ chấm áp
cùng bản đồ; vàng được ánh xạ sang tệp mới, ca tách nghĩa đánh dấu cần gán lại.

**Cổng.** Q2 = 0 xung đột mở trong phạm vi xuất bản; mọi gộp chạm node của bộ vàng được người duyệt.

### D — Recall có mục tiêu (~1–3 USD toàn kho)

**Vấn đề.** C1 hỏi mọi cặp nghi vấn (9 984 cặp cho `doc-2`) — đắt, và phần lớn cặp trống.

**Thiết kế.** Hỏi cặp theo thứ tự lợi suất: (1) cặp mà câu neo của B nhắc A; (2) phiên pass chính gộp mục vụn (C2, dùng
đúng `plan_main_sessions` có trần token — bản thẩm định §3.7); (3) chỉ khi (1)–(2) không đủ Q5 mới mở rộng sang toàn bộ
cặp nghi vấn (C1). Phán cặp dùng đúng pass phụ hiện có (hai chiều, hoà giải), hồ sơ thêm câu neo của hai đầu.

**Cổng.** Q5 tăng trên cả hai chương; chấm mù trên cạnh mới đạt ngưỡng Q4 (luật đã khoá ở kế hoạch cũ mục 18); báo
recall tăng trên mỗi USD để so với C1.

### E — Lộ trình tới mục tiêu (0 USD)

Tổ tiên của đích trong đồ thị (sau bản đồ danh tính), sắp và chia module theo gói A. Đo Q7 trên mọi đích có tiên quyết
vàng. Đây là tính năng mà "đọc sách từ đầu" không làm được, nên là nơi đồ thị phải chứng minh giá trị.

### F — An toàn vận hành (0 USD, làm cùng A)

- **Chạy khô có dự toán**: lệnh `roadmap` in stage nào sẽ tính lại, số lời gọi và USD ước lượng, và **không** chạy stage
  trả tiền nếu thiếu cờ cho phép. Lý do cụ thể: đổi thuật toán pass phụ (F126) khiến chạy `roadmap` trên **bất kỳ** tài
  liệu nào ngoài `doc-1` sẽ lặng lẽ chạy C1 (~7,4 USD cho `doc-2`).
- **Con trỏ bản hiện hành** cho từng tài liệu: sau các thí nghiệm, phiên bản mới nhất của `doc-1` (v16) và `doc-2` (v11)
  là lộ trình **có C10 đã bị loại**. Bản hiện hành đúng là `doc-1` v14, `doc-2` v9, `doc-3` v11, `baocao-canhan` v99,
  `naive-bayes` v29, `nhap-mon-ml` v29, `xstk-ch3-1` v29.

### G — Đánh giá khép kín (chủ yếu là việc của người)

| việc | ai | khi nào |
|---|---|---|
| chấm mù cạnh (đã có bảng) | hai người gán | ngay — quyết gói D và C1 |
| nhãn node gán mù trên một tài liệu mới (≈ 60 node) | một người | trước khi chạy gói B |
| liệt kê mù khái niệm trọng yếu, 3 mục lấy mẫu mỗi tài liệu | một người | trước lần xác nhận |
| chấm mạch lạc và tên module, thang 1–5, A/B ẩn tên hệ thống | hai người | sau gói A |
| tập giữ lại: khoá `xstk-ch3-1` (đã gán, chưa dùng để chọn); thêm một chương từ tài liệu dạng slide | chủ dự án | trước lần xác nhận |

Lần xác nhận cuối chạy **một** cấu hình đã khoá (commit, hash prompt, tham số) trên tập giữ lại; thất bại được ghi nguyên.

## 6. Thứ tự, phụ thuộc, ngân sách

```text
F ─┐
A ─┴─→ E
B ─→ C ─→ D ─→ (chấm mù) ─→ C1 cho doc-2 nếu cần
                                   ↓
                            G: xác nhận trên tập giữ lại
```

| bước | gói | chi phí | phụ thuộc |
|---|---|---|---|
| 1 | F + A | 0 USD | — |
| 2 | E | 0 USD | A |
| 3 | B | ~0,3–0,6 USD | nhãn node mới (người) |
| 4 | C | ~0,1 USD | B |
| 5 | D | ~1–3 USD | B, C; chấm mù |
| 6 | C1 cho `doc-2` | ≤ 7,4 USD | chỉ khi D chưa đủ Q5 **và** chấm mù qua luật đã khoá |
| 7 | xác nhận | ~1–2 USD | tất cả |

Dự chi ≈ **4–12 USD**; số dư ≈ **36 USD** (đã tiêu ≈ 13,8 / 50).

## 7. Những gì không làm, và vì sao

- **Không quay lại C10.** Tiêu chí "định nghĩa của B có dùng A" hẹp hơn khái niệm tiên quyết của người gán; bộ lọc tự
  động không nâng được precision khi vàng thiếu.
- **Không dùng độ gần embedding làm cạnh** (đối xứng, trong khi tiên quyết có hướng); không dùng điểm tự báo của mô hình.
- **Không thêm GNN/RL/BKT** khi chưa có dữ liệu người học (bản thẩm định §9.7).
- **Không sửa canonical hay bộ vàng đóng băng** trong đợt này; mọi thay đổi danh tính đi qua bản đồ ID có version.
- **Không tối ưu số stage làm mục tiêu chính.** Với 222 khái niệm và trần 8, ~30 module là tự nhiên — một học kỳ có
  ~30 buổi. Vấn đề chưa bao giờ là số lượng, mà là mỗi đơn vị có mạch lạc và đúng thứ tự không.

## 8. Cần chủ dự án

1. Duyệt hướng: đổi đơn vị trình bày từ *stage song song* sang *module có thứ tự* (gói A) — đây là thay đổi hợp đồng sản
   phẩm, không chỉ thuật toán.
2. Chốt ngưỡng Q1–Q10 trước lần xác nhận (có thể giữ nguyên đề xuất).
3. Người: chấm mù (đang làm), nhãn node mới cho gói B, và một chương giữ lại dạng slide.

## Phụ lục — tái lập các con số

Chạy từ gốc repo bằng `.venv/Scripts/python.exe`; chỉ đọc artifact, không gọi mô hình.

| con số | script |
|---|---|
| §3.1 sách / sắp topo ưu tiên sách / CG; §3.2 số stage khi cắt không chứa cạnh | `scripts/phan-tich-v2/baseline_sach.py` |
| §3.1 CG đọc theo sách; §3.2 module và độ mạch lạc; §3.4 chuỗi dài nhất | `scripts/phan-tich-v2/module_thu.py` |
| §3.3 bộ dò cạnh nhắc tên trong câu căn cứ | `scripts/phan-tich-v2/dinh_nghia_nhac_ten.py` |
| §0, §2 sàn nhiễu U1 qua 30 cách phá thế hoà | `scripts/phan-tich-v2/san_nhieu_u1.py` |
| kế hoạch cũ §17: CG / C9 / C9b so với phân bố nhiễu | `scripts/phan-tich-v2/c9b.py` |

Lộ trình dùng để đo: `doc-1` v14 và `doc-2` v9 (chuỗi hiện hành, có C8 v2), trừ các phép đo nhiễu dùng v10 / v7.
