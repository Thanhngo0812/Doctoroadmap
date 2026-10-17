# Vé 05b — Chạy lại xstk và doc-4 sau khi sửa luật đề cương lặp (2026-10-17)

Người chạy: Claude. Vé [05b](../task/v4/05b-chay-lai-xstk-doc4.md); nghiên cứu ở [báo cáo vé 05](v4-05-a2-de-cuong-lap-2026-10-17.md).
**Chi thật khoảng 0,21 USD** (Vertex, gemini-3.1-flash-lite, temperature 0); chủ dự án duyệt bước 1.

## Phán: đạt. xstk tốt lên rõ; doc-4 không cần chạy lại đồ thị

| xstk | Cổng 19l (graph v56) | 05b (graph v64) |
|---|---|---|
| Khái niệm đích trong dãy học | 16/25 | **20/25** |
| Cạnh vàng có cả hai đầu trong dãy học | 32/62 | **50/62** |
| Q6 (lỗi thứ tự, thấp là tốt) | 0,541 | **0,262** |
| Q7 | 0,225 | **0,314** |
| Q7b | 0,380 | **0,628** |
| P / R trực tiếp | 0,286 / 0,111 | **0,333 / 0,194** |
| P / R bao đóng | 0,538 / 0,126 | **0,682 / 0,270** |
| Cạnh bao đóng đúng / vàng | 14 / 111 | **30 / 111** |
| Gộp sai mà vàng phát hiện | 1 | 1 |

- **Mức lệch:** R bao đóng 0,270 nằm trong dải 0,26–0,32 của 19j và cao hơn mọi lượt trước: v3 18d 0,163; 17i pha A 0,248. Mức tăng lớn hơn hẳn nhiễu
  đầu vào đã đo ở cổng 19l, và đi đúng hướng mô phỏng (trần 59/62 cạnh trong phạm vi).
- **doc-4:**
  - nhãn mới làm đổi câu ứng viên của 24 khái niệm, không khái niệm nào thuộc vàng;
  - chạy lại đồ thị doc-4 tốn khoảng 1,4 USD mà E4 không đo được lợi gì. **Không chạy bước 2.** Bản nhãn mới sẽ được dùng ở lần `a4` doc-4 kế tiếp.

## 1. Mã và cách chạy

- **Commit mã:** `36b81ff2bb5cfc18fffc4fca5d13cdc3beca6a71`, gồm 19n, 19o và 05a.
- **Checkout sạch:** chạy từ `tmp/v4-05b/ma`. Trên checkout này toàn bộ test qua (1.403 test).
- **Script chạy:** `scripts/a2-de-cuong/chay_tu_commit.py` dừng nếu worktree bẩn, sai commit, hoặc import nhầm mã của thư mục làm việc. Gốc lệnh
  vẫn là repo chính.
- **Lệnh**, theo khuôn T10 (gán nhãn trên cây mới rồi chuyển sang chunk mà A3 đã dùng). Mỗi bước có chi đều dry-run trước:
  - xstk: `label-roles --chunks-version 3`, rồi `--chunks-version 2 --transfer-from-chunks-version 6`, rồi `a4`, rồi `roadmap`. Thêm cờ
    `--allow-text-quality-reason` như cổng;
  - doc-4: `label-roles --chunks-version 4`, rồi `--chunks-version 3 --transfer-from-chunks-version 7`.

| Bước | Lời gọi | USD | Giây |
|---|---|---|---|
| xstk nhãn vùng, chunk v3 | 2 | 0,004 | 12 |
| xstk chuyển nhãn sang chunk v2 | 0 | 0 | 3 |
| xstk `a4` (canonical v9) | 41 lời neo; gộp và mô tả tái dùng hết | 0,030 | 141 |
| xstk `roadmap` (graph v57–v64) | 47 lời pass chính; pass phụ là ML | 0,141 | 196 |
| doc-4 nhãn vùng, chunk v4 | 8 | 0,033 | 30 |
| doc-4 chuyển nhãn sang chunk v3 | 0 | 0 | 6 |
| **Tổng** | | **khoảng 0,21** | |

Embedding qua Vertex (106 tên ở `a4`, 347 văn bản ở stage cụm và mention) tốn dưới 0,01 USD, nhưng chiếm phần lớn thời gian của stage cụm (151 giây).

## 2. Nhãn vùng

**xstk.**
- Lớp LLM gán **cả 13 mục "Cách giải" là `noi_dung`**. Không mục nào khác đổi nhãn.
- Sau khi chuyển nhãn, 48 chunk đổi từ `de_cuong` sang `noi_dung` (khớp 126/126 chunk), đúng con số mô phỏng.

**doc-4.**
- **Câu hỏi ôn tập:** cả 10 mục ra `bai_tap`.
- **19 mục lớp LLM từng gán `de_cuong` nay thành `noi_dung`.** Trong đó có đủ 6 mục nội dung mà nghiên cứu (mục 4) ghi là gán nhầm, ví dụ "Ý thức
  xã hội", "2. Cấp độ của quá trình nhận thức".
  - Lý do: tiêu đề được gom lô khác đi nên được hỏi lại.
  - Như vậy lớp nhãn LLM **không ổn định theo cách gom lô**, dù temperature bằng 0.
- **Một mục đổi theo chiều xấu:** "IV- Quy luật phủ định của phủ định" từ `noi_dung` thành `de_cuong`. Mục này không có chunk nào đổi vai trò.
- **Ở mức chunk:** 17 chunk `de_cuong` → `bai_tap`, 8 chunk `de_cuong` → `noi_dung`, không chunk nào thành `de_cuong`.

## 3. Neo và trạng thái dạy ở xstk (canonical v8 → v9)

12 khái niệm đổi trạng thái: 10 "chỉ nhắc" → "được dạy", 1 "không chắc" → "được dạy", 1 "được dạy" → "chỉ nhắc". Claude đọc từng lời phán.

**Khái niệm vàng chuyển sang "được dạy".** Câu neo đều là câu công thức hoặc định nghĩa trong "Cách giải":
- Khoảng ước lượng của μ; Khoảng ước lượng của phương sai tổng thể;
- Độ chính xác; Độ chính xác ε; Độ chính xác trong ước lượng tỉ lệ;
- Xác định kích thước mẫu ("Nếu gọi N là kích thước mẫu để có phép ước lượng μ với độ tin cậy 1 -α và độ chính xác ε").

**Khái niệm ngoài vàng chuyển sang "được dạy":**
- "Giá trị tới hạn χα^2", "Tiêu chuẩn kiểm định χ 0 2", "Ước lượng trung bình", "Ước lượng phương sai": được dạy thật. Câu neo của "Ước lượng
  phương sai" là đề bài ví dụ, hơi yếu.
- **"Phân phối Poisson": sai.** Lời phán là `introduced_by_example`, dựa trên một ví dụ kiểm định ("H : X có phân phối Poisson ℘ ( λ )"). Chương
  này chỉ dùng khái niệm đó, không dạy. Đây là điểm yếu đã biết của luật C8 với ví dụ có lời giải. Kết quả là dãy học thừa 1 khái niệm.

**"Phân phối chuẩn": "được dạy" → "chỉ nhắc".** Báo cáo quy lỗi ngày 2026-10-12 đã đọc và ghi rằng xstk-ch3-1 chỉ dùng khái niệm này, nên đây là sửa
đúng. Khi câu ứng viên có thêm câu từ "Cách giải", lời phán đổi theo.

**12 cạnh vàng vẫn ngoài dãy học:**

| Khái niệm | Số cạnh | Đọc |
|---|---|---|
| Bài toán tìm kích thước mẫu | 3 | tên chỉ có trong câu giới thiệu ở mục 2.3; phần dạy ở mục 2.4 mang tên khác |
| Xác định kích thước mẫu trong ước lượng trung bình | 3 | ứng viên duy nhất là dòng gạch đầu dòng "• Xác định … Bài toán ."; lời phán: "chỉ là tiêu đề" |
| Phân phối chuẩn | 4 | chỉ được dùng; phán đúng theo văn bản, dù người gán vàng coi là tiên quyết |
| Phân phối Student, Phân phối χ 2 | 1 + 1 | chỉ được dùng qua bảng phụ lục |

## 4. Hai phần đã hoãn, xem lại bằng kết quả thật

- **Câu ứng viên cho mục dạy phía sau (phần 3):**
  - còn đúng hai khái niệm "kích thước mẫu", giữ **6 cạnh vàng** ngoài dãy học;
  - "Xác định kích thước mẫu trong ước lượng trung bình" có thể sửa bằng một luật chung. Hiện luật nhận khối mang tên chỉ xét 3 dòng đầu chunk;
    nếu xét cả dòng tiêu đề ngắn ở giữa chunk thì khái niệm này có ứng viên kèm ngữ cảnh phần dạy;
  - "Bài toán tìm kích thước mẫu" vẫn không có luật chung nào nối được;
  - **đề xuất:** để làm nghiên cứu sau, thử trước bằng một phép hỏi lại vài lời (dưới 0,01 USD), chưa mở vé.
- **Luật bỏ qua khái niệm ngoài vùng nội dung:** sau 05b, xstk không còn khái niệm vàng nào bị mã gạt. Hai ca sai ở doc-4 ("Triết học cận đại",
  "Triết học trung cổ") đã có ứng viên nhờ nhãn mới. Giữ kết luận cũ: **không sửa luật.**

## 5. doc-4: vì sao không chạy bước 2

`scripts/a2-de-cuong/mo_phong_doc4.py` dựng lại câu ứng viên neo với bản nhãn v6 (canonical của cổng; khớp nhật ký 626/626) và với bản nhãn mới v8.
- **24 khái niệm đổi câu ứng viên**, 0 khái niệm thuộc vàng.
  - 22 khái niệm đã "được dạy" có thêm chunk định nghĩa, ví dụ "Ý thức xã hội", "Hình thái ý thức xã hội", "Cơ sở hạ tầng".
  - 2 khái niệm từng bị mã gạt nay có ứng viên.
- **Chi phí nếu chạy lại:** `a4` doc-4 chỉ tốn khoảng 24 lời neo, nhưng kéo theo `roadmap` doc-4 khoảng 1,4 USD (số của cổng). Bộ vàng không đo được
  lợi ích này. Để tới lần chạy doc-4 kế tiếp; khi đó canonical sẽ dùng bản nhãn v8.

## 6. Nguồn gốc artifact

Mọi artifact mới sinh từ commit `36b81ff`. Đường dẫn, SHA-256 manifest và payload ở `scripts/a2-de-cuong/nguon-goc-05b.json`.

| Artifact | Ghi chú |
|---|---|
| chunks xstk-ch3-1 v6 | nhãn vùng trên chunk v3 |
| chunks xstk-ch3-1 v7 | nhãn chuyển sang chunk v2; canonical v9 dùng bản này |
| canonical xstk-ch3-1 v9 | `anchor_chunks_version` 7 |
| graph xstk-ch3-1 v57–v64 | chuỗi đồ thị đầy đủ, kể cả tên module |
| chunks doc-4 v7, v8 | nhãn trên chunk v4, rồi chuyển sang chunk v3; chưa canonical nào dùng |

## 7. Việc tiếp theo của hàng 05

- **Số cuối:** đo trên T-01 khi có vàng, bằng script chỉ in trường trong allowlist.
- **Còn mở, chưa mở vé:**
  - câu ứng viên cho dòng tiêu đề giữa chunk (mục 4);
  - "introduced_by_example" từ ví dụ có lời giải (Phân phối Poisson);
  - lớp nhãn LLM của A2 không ổn định theo cách gom lô;
  - R17;
  - khái niệm khung làm tiên quyết.

## Script

| Script | Việc |
|---|---|
| `chay_tu_commit.py` | chạy CLI bằng mã ghim |
| `so_trang_thai.py` | so trạng thái dạy giữa hai canonical, kèm lời phán neo của khái niệm vàng |
| `mo_phong_doc4.py` | so câu ứng viên neo doc-4 giữa hai bản nhãn |
| `nguon_goc_05b.py` | bảng nguồn gốc artifact |
