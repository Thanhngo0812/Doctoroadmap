# 04 — Neo định nghĩa (C8 v3)

**Nguồn chân lý:** spec v2, W11–W13

**What to build:** mỗi khái niệm có một câu neo nguyên văn nơi tài liệu dạy nó, và một trạng thái là thuộc tính của khái
niệm. Thay stage `teaching` v2.

**Blocked by:** vé 10 — T2 (tài liệu N1) và T3 (nhãn khái niệm mù trên N1). Có thể viết mã và chạy trên dữ liệu phát
triển trước; cổng chỉ chấm được khi có nhãn N1.

**Status:** ready (viết mã); cổng chờ T3

## Cổng nhận (khoá trước khi chạy trên N1)

1. **Q9 — câu neo đúng:** kiểm tay 50 khái niệm ngẫu nhiên trên ≥ 3 tài liệu (vé 10, T4): câu neo là nơi tài liệu dạy
   khái niệm ≥ 90%.
2. **Loại khái niệm trên N1 (nhãn mù):** loại đúng ≥ 80% khái niệm phải loại; loại nhầm ≤ 2% khái niệm phải giữ.
3. **Không làm mất vàng:** 0 đầu cạnh vàng của hai chương phát triển bị loại.
4. Báo kèm (bằng chứng phát triển, không phải cổng): nhãn `doc-3` đã khoá, và ba tài liệu cổng A của C8.

## Acceptance

- [ ] Tách câu và chọn ứng viên (W11) là hàm thuần có test.
- [ ] Prompt `a10/teaching.txt` v3, schema, kiểm câu trích bằng mã, kiểm tín hiệu tường minh cho `prior_knowledge`.
- [ ] Đổi sổ đăng ký hash prompt có chủ đích; README prompt ghi v3.
- [ ] Sửa spec provenance và `spec-addendum.md` A3–A5 (neo định nghĩa) cùng commit.

## Nhật ký chạy trên dữ liệu phát triển (không phải cổng)

### Lượt 1 — 2026-09-24, 0,427 USD (`scripts/phan-tich-v2/chay_neo.py`)

| tài liệu | kết quả |
|---|---|
| doc-1 | loại đúng **3/3** node hành chính, không loại gì khác; Q6 **2,5%** (A10 neo sách với C8 v2: 5,0%); 0 thiếu đầu; Q7 89% |
| doc-2 | Q6 **9,8%** (C8 v2: 8,2%); 0 thiếu đầu; **98/438 "unchecked"** |
| doc-3 (nhãn đã nhìn) | loại đúng 8/13, loại nhầm **0/33** |
| baocao-canhan | loại nhầm 1: `Thiết kế Cơ sở dữ liệu` |
| naive-bayes, nhap-mon-ml, xstk-ch3-1 | loại nhầm 0 |

**Lỗi tìm ra:** "unchecked" không phải phán quyết mà là *không có ứng viên* — bộ chọn câu chỉ khớp tên nguyên văn. Hụt
hai loại: ký hiệu toán (`Addition on 𝑉1 × ⋯ × 𝑉 𝑚` ≠ `V1 × ⋯ × Vm`) và tên mô tả do mô hình đặt (`Hàng hoặc cột tỷ lệ`,
câu sách là "Có hai hàng (hay hai cột) tỷ lệ"). 97/98 khái niệm đó có câu căn cứ A3 đã kiểm. Khái niệm "unchecked" giữ vị
trí cũ, nên lượt 1 là trộn hai quy tắc định vị — số Q6 doc-2 không đọc được như hiệu quả của neo.

**Sửa (W11):** khớp tên sau NFKC + bỏ khoảng trắng; câu chứa câu trích căn cứ A3 luôn là ứng viên, xếp cùng hạng câu có tín
hiệu định nghĩa. Đếm offline: không ứng viên còn doc-1 0/225, doc-2 1/438, doc-3 4/58 (không có căn cứ), còn lại 0.

### Lượt 2 — khoá trước khi chạy (2026-09-24)

Dữ liệu phát triển, không phải cổng; ghi trước để không đọc kết quả theo ý muốn. Coi lượt 2 là **hồi quy** nếu bất kỳ:
- doc-1: loại nhầm bất kỳ node nào ngoài 3 node hành chính, hoặc bỏ sót node hành chính nào;
- doc-3: loại nhầm > 0/33;
- doc-1 hoặc doc-2: có đầu cạnh vàng bị loại (thiếu đầu > 0);
- ba tài liệu cổng A của C8 (baocao-canhan, naive-bayes, nhap-mon-ml): loại nhầm tổng > 1.

Q6 doc-2 báo cả hai lượt kèm sàn nhiễu U1 (±3,0 điểm); chênh trong sàn nhiễu không được gọi là cải thiện hay tụt.

### Lượt 2 — kết quả, 0,491 USD

| tài liệu | teaching → stages | kết quả |
|---|---|---|
| doc-1 | v21 → v22 | có neo 202/225; loại 3/3 hành chính **+ `det(Y)`**; Q6 5,0%; 0 thiếu đầu; Q7 89%; bám sách +0,922 |
| doc-2 | v16 → v17 | có neo 322/438; unchecked **1** (lượt 1: 98); Q6 8,2%; 0 thiếu đầu; Q7 58% |
| doc-3 | v16 → v17 | loại đúng 6/13 (lượt 1: 8/13), loại nhầm 0/33 |
| baocao-canhan / naive-bayes / nhap-mon-ml | v104 / v34 / v34 | loại nhầm 1 (`API foundation`) / 0 / 0 |
| xstk-ch3-1 | v34 → v35 | loại `Chương trình REG`, `chương trình SD` (tên phần mềm) |

Đối chiếu tiêu chí khoá trước:
1. doc-1 loại nhầm ngoài 3 node hành chính — **kích hoạt**: `det(Y)` ("Tính det(Y), biết:", một câu bài tập; node có 2
   cạnh, không phải đầu cạnh vàng). Có lý để loại, nhưng tiêu chí ghi "bất kỳ node nào" nên ghi là kích hoạt, không đọc lại.
2. doc-3 loại nhầm 0/33 — đạt.
3. Thiếu đầu cạnh vàng 0 trên cả hai chương — đạt.
4. Ba tài liệu cổng A loại nhầm tổng 1 — đạt (ngưỡng > 1).

Đọc: Q6 hai lượt (doc-1 2,5% → 5,0%; doc-2 9,8% → 8,2%) đều nằm trong sàn nhiễu U1 (±2,6 / ±3,0 điểm; một cạnh vàng doc-1 là
2,5 điểm) — **chưa có bằng chứng neo cải thiện Q6 so với C8 v2**. Cái lượt 2 sửa được là cơ chế: vị trí mọi khái niệm giờ
đến từ một quy tắc duy nhất. Loại đúng doc-3 giảm 8 → 6/13: bắt thêm `GPA`, nhưng lọt `Top node`, `Bottom node` (nay có
câu neo từ căn cứ A3 và bị phán `taught` — node minh hoạ sơ đồ mạng) và `Experience` (`mentioned_only`). Giả thuyết (chưa kiểm): thêm ứng
viên làm mô hình dễ tìm được một câu "dạy" cho node minh hoạ. Neo C8 v3 vẫn
**không vào chuỗi mặc định**; quyết định chờ T3 (nhãn N1) và T4 (kiểm câu neo, bảng `kiem-cau-neo.xlsx` từ lượt 2).

**Điểm yếu thấy khi tạo bảng T4 (chưa sửa, để T4 đo đúng bản đã chạy):** bộ tách câu W11 không cắt ở xuống dòng, nên trên
PDF toán một "câu neo" có thể là cả khối nhiều dòng (ví dụ doc-1 `Nhân một hàng hoặc một cột với số k`: khối gồm "Cho ma
trận / Tính det(A^2010) / … Nếu cộng nhiều hàng …"). Nếu T4 cho tỉ lệ sai cao ở các dòng loại này, sửa tách câu trước khi
chạy N1.

**Quyết định chủ dự án (2026-09-24):** loại `det(Y)` là **đúng** — câu bài tập ("Tính det(Y), biết:") không phải khái
niệm để dạy. Tiêu chí 1 của lượt 2 vẫn ghi là đã kích hoạt như lúc chạy; quyết định này là phán xét của chủ dự án về
node đó, không phải sửa tiêu chí. Nhãn N1 (T3) có sẵn lựa chọn *Loại — chi tiết của một ví dụ* cho loại node này.

### T4 — kết quả nhận 2026-09-24 (`scripts/cham-neo/cham_bang.py`)

**Nguồn nhãn:** phán quyết của người (đồng nghiệp chủ dự án); AI chỉ hỗ trợ ghi vào bảng — chủ dự án xác nhận
2026-09-24. Mốc "Lượt phân tích AI 00:03–00:14 UTC" ở ô ghi chú dòng 1 là giờ của AI, **không có giờ làm thật của người**.
(Bản ghi đầu của mục này nói "AI, không phải người" — đã sai, sửa theo xác nhận.)

- Q9 theo nhãn AI: đúng nơi dạy 44/48 = 92% (Wilson 95% 80%–97%), không chắc 2. Cận dưới 80% < 90%: ngay cả khi coi là
  nhãn người, 48 dòng chưa đủ để khẳng định ≥ 90%.
- Theo tài liệu: doc-1 12/12, doc-2 11/12, doc-3 6/6, nhap-mon-ml 7/7, naive-bayes 5/6, **baocao-canhan 3/5**.
- Câu neo nhiều dòng 26/28 so một dòng 18/20 — **điểm yếu tách câu tôi ghi trước không thấy trong dữ liệu này**.
- Bốn dòng sai đều là "chỉ nhắc qua": `Cauchy sequence` (dùng như kiến thức sẵn có), `Dữ liệu liên tục`,
  `Pessimistic Locking`, `Concurrency` (báo cáo kể việc đã làm, không dạy).

**Cổng 1 (Q9):** ước lượng điểm 44/48 = 92% ≥ 90% nên đạt theo chữ của cổng; nhưng Wilson 95% là 80%–97%, chứa vùng trượt — theo luật của vé 07 ("khoảng chứa vùng trượt thì chưa đủ bằng chứng") thì Q9 **chưa đủ bằng chứng**. Cỡ mẫu để cận dưới Wilson ≥ 90%: ≈ 830 dòng nếu tỉ lệ thật 92%, ≈ 127 nếu 95%, ≈ 69 nếu 97% — với tỉ lệ quanh 92% thì kiểm thêm không phải cách khả thi; đường thực tế là nâng chất lượng neo (4 lỗi đều "chỉ nhắc qua"). Cổng 2–3
vẫn chờ N1 (T2 phần N1, T3). doc-4 đã nhận nhưng chủ dự án xếp vào vai N2.

## N1 = doc-5 (nhận 2026-09-24, kiểm 2026-09-25)

`doc-5.pdf`: slide "Chương 3 — Đại số quan hệ", môn Cơ sở dữ liệu (ĐH CNTT), 31 trang, chữ thật. Đạt: dạng slide, khác
môn, nhiều ví dụ dùng bảng dữ liệu riêng (NHANVIEN/NV001…, TAIXE, KETQUATHI, S#/P#) và 9 "Câu hỏi" bài tập. **Không đạt:
không có trang hành chính nào** (đề cương, điểm, lịch, giảng viên) — "điểm thi" chỉ nằm trong bảng ví dụ. Hệ quả: cổng 2
("loại đúng ≥ 80% khái niệm phải loại") trên N1 chủ yếu đo việc loại **chi tiết của ví dụ**; loại trang hành chính không
được kiểm trên dữ liệu mới, chỉ có bằng chứng phát triển (doc-1 3/3). Ghi trước khi chạy.
Quy trình: nhập → A3 → A4 → bảng nhãn T3 → **người** gán nhãn → mới chạy neo trên doc-5.

**Nhập doc-5 (2026-09-25):** chunks v1 (42 chunk, 6,5k token; ký hiệu Symbol dịch đúng σ π × ÷ ∪ ∩, thiếu ⋈), A3 0,090 USD,
A4 0,024 USD. Canonical v1: 71 node = 25 khái niệm `learnable` + 22 bảng + 24 hình. **Cả 25 khái niệm learnable đều là kiến
thức môn học** (các phép toán đại số quan hệ); A3 đã tách mọi dữ liệu ví dụ thành node bảng/hình không learnable và không
trích thực thể ví dụ nào. Hệ quả cho cổng 2 trên N1: "loại nhầm ≤ 2%" đo được trên 25 khái niệm (một lần loại nhầm là
trượt); "loại đúng ≥ 80% khái niệm phải loại" **gần như không có mẫu số** — N1 này không kiểm được vế loại.
Bảng T3: `artifacts/a8-gold/nhan-khai-niem-doc-5.xlsx` (25 dòng, không hiện mô tả A5 để không lộ đáp án), khoá
`nhan-khai-niem-doc-5-khoa.json`. Chưa chạy neo trên doc-5.

### N1 doc-5 — khoá trước khi chạy neo (2026-09-25)

Nhãn T3 (`nhan-khai-niem-doc-5-output.xlsx`, SHA-256 ghi ở báo cáo chạy): 25 khái niệm, **19 "Giữ — được dạy", 6 "Giữ — chỉ được
nhắc", 0 phải loại**. Ghi chú dòng 1 có câu "Bản này do AI gán"; chủ dự án xác nhận AI chỉ hỗ trợ ghi.
- **Cổng 2, vế loại nhầm:** ≤ 2% khái niệm phải giữ → với 25 khái niệm là **0 lần loại** (`prior_knowledge` hoặc
  `not_subject_matter`). Một lần loại là trượt.
- **Cổng 2, vế loại đúng:** không có mẫu số trên doc-5 — **không chấm**, không tính là đạt.
- **Cổng 3:** doc-5 không có vàng cạnh — không áp dụng.
- **Báo kèm, không phải cổng:** khớp "được dạy" ↔ `taught` và "chỉ được nhắc" ↔ `mentioned_only` giữa C8 v3 và nhãn; cùng
  các số đó cho C8 v2 (bản tạm đang bật) để so.
Chạy: `roadmap --allow-spend` cho doc-5 tới đồ thị validated (chuỗi mặc định, có C8 v2), rồi neo C8 v3 trên validated đó.

### N1 doc-5 — kết quả (2026-09-25, `scripts/phan-tich-v2/cham_n1.py`)

Chuỗi mặc định doc-5: validated v6 → C8 v2 v7 → stages v8 (25 khái niệm, 4 module), 0,105 USD. Neo C8 v3: teaching v9, 0,014
USD. Nhãn T3 SHA-256 `3fb3e3f3c19dca94…`.

| | C8 v3 (neo) | C8 v2 (bản tạm) |
|---|---|---|
| loại nhầm (cổng: 0/25) | **0/25** | 0/25 |
| loại đúng | không có mẫu số | không có mẫu số |
| "được dạy" → `taught` | 17/19 | 16/19 |
| "chỉ được nhắc" → `mentioned_only` | 2/6 | 3/6 |

Vế loại nhầm **đạt theo chữ**; 0/25 có cận trên Wilson 95% 13% nên theo luật khoảng thì **chưa đủ bằng chứng** cho "≤ 2%" — cần
gộp thêm N1 (doc-6). Vế loại đúng chưa chấm được. Trên doc-5, v3 và v2 ngang nhau.

## N1 bổ sung = doc-6 (nhận 2026-09-25)

`doc-6.pdf`: slide buổi 1 cùng môn Cơ sở dữ liệu (ĐH CNTT) — "Chương 1 — Tổng quan về CSDL", 25 trang. Có trang thông tin
môn (thời lượng, khoa, trường), trang **đề cương liệt kê các chương sau** (SQL, ràng buộc toàn vẹn, phụ thuộc hàm, dạng chuẩn)
và slide "Nội dung" lặp 6 lần; không có trang điểm số/lịch. Bộ đọc mặc định vỡ chữ (tách âm tiết 3,6%) → nhập lại
`--pdf-backend pypdfium2` (chunks v2, 27 chunk, 1,5k token). A3 0,057 USD, A4 0,014 USD: 28 khái niệm learnable + 11 hình.
Bảng T3: `artifacts/a8-gold/nhan-khai-niem-doc-6.xlsx`. Cổng 2 (hai vế) chấm trên **doc-5 + doc-6 gộp**; khoá: loại nhầm
≤ 2% khái niệm phải giữ (gộp 53 khái niệm → tối đa 1 lần loại nhầm), loại đúng ≥ 80% khái niệm phải loại (nếu mẫu số ≥ 1).

### Lượt 3 — khoá trước khi chạy (2026-09-25): bỏ dấu LaTeX và gộp gạch nối khi so tên (W11)

Chẩn đoán Q6 doc-2 (stages v21): 6/6 vi phạm đều là "vị trí dạy của tiên quyết nằm sau đích và máy không có cạnh sửa"; 4/6 do
nút không có câu neo nên vị trí rơi về chunk dùng muộn — `𝐅^{m,n}` (định nghĩa thật ở chunk 356 "… is denoted by 𝐅 𝑚 , 𝑛",
nhưng tên `f^{m,n}` không khớp văn bản `fm,n` vì `^{ }`) gây 3 vi phạm. Sửa `_compact`: bỏ `^ _ { } \`, gộp – — − về `-`.
Đếm offline: thêm 10 nút doc-2 tìm thấy tên trong văn bản, 2 nút xstk (chỉ đếm khớp tên), 0 ở tài liệu khác.
Chạy: neo trên doc-1, doc-2, doc-3, naive-bayes, nhap-mon-ml, baocao-canhan, doc-5 (không chạy xstk — tập giữ lại); rồi
danh tính (áp quyết định T5) và A10 cho doc-1, doc-2. Coi là **hồi quy** nếu bất kỳ:
- doc-1 loại nhầm ngoài 3 node hành chính và `det(Y)` (chủ dự án đã xác nhận `det(Y)` đúng);
- doc-3 loại nhầm > 0/33; ba tài liệu cổng A loại nhầm tổng > 1; doc-5 loại nhầm > 0/25;
- thiếu đầu cạnh vàng > 0 trên doc-1 hoặc doc-2.
Kỳ vọng (không phải cổng): các vi phạm Q6 doc-2 dính `𝐅^{m,n}` biến mất nếu nút này nhận câu neo ở chunk 356. Q6 báo kèm sàn
nhiễu U1.

### Lượt 3 — kết quả, 0,468 USD (`scripts/phan-tich-v2/chay_luot3.py`)

Tiêu chí hồi quy **đạt hết**: doc-1 không loại gì ngoài 3 node hành chính và `det(Y)`; doc-3 loại nhầm 0/33 (loại đúng 6/13);
cổng A loại nhầm tổng 1 (`API foundation`); doc-5 0/25; thiếu đầu cạnh vàng 0. Q6 doc-1 2,6%, doc-2 9,8% — **kỳ vọng không
thành**: `𝐅^{m,n}` vẫn `mentioned_only`. **Lỗi đo của tôi:** phép đếm offline tìm tên trên *mọi* chunk, còn bộ chọn câu chỉ tìm
trong chunk đã gom (định nghĩa, mention cứng, căn cứ A3) — chunk 356 không thuộc các chunk đó vì mention map A6 cũng so tên
kiểu cũ. Sửa luật so tên là cần nhưng chưa đủ.

### Lượt 4 — khoá trước khi chạy (2026-09-25): tìm tên ký hiệu trên toàn tài liệu

Đo đúng thứ sẽ đổi (tập câu ứng viên) trên ba phương án: tìm mọi tên trên toàn tài liệu → doc-2 122 nút đổi (khớp nhầm
"Addition" trong "additional"); chỉ nút thiếu câu tín hiệu → 87; **chỉ tên ký hiệu** (chữ số, `^ _ { } , ( )`, ký tự đổi khi
NFKC) → **doc-2 26, doc-1 3, mọi tài liệu khác 0**, và `𝐅^{m,n}` nhận câu định nghĩa chunk 356 làm ứng viên đầu. Chọn phương án
cuối (`symbolic_name_chunks`). Chỉ chạy doc-1, doc-2 — tài liệu khác 0 nút đổi ứng viên nên kết quả lượt 3 giữ nguyên.
Tiêu chí hồi quy như lượt 3 (doc-1; thiếu đầu cạnh vàng = 0). Kỳ vọng (không phải cổng): vi phạm dính `𝐅^{m,n}` biến mất.

### Lượt 4 — kết quả, 0,366 USD

| | teaching → identity → stages | Q6 | Q7 | ghi chú |
|---|---|---|---|---|
| doc-1 | v33 → v34 → v35 | 2,6% (1/39) | 90% (9/23 đích đủ) | loại: đúng 3 node hành chính + `det(Y)` |
| doc-2 | v27 → v28 → v29 | **4,9% (3/61)** — lượt 3: 9,8% | 58% (0/23) | `𝐅^{m,n}` taught tại chunk 356 |

Tiêu chí hồi quy đạt (doc-1; thiếu đầu 0). Kỳ vọng thành: ba vi phạm dính `𝐅^{m,n}` biến mất; mức giảm 4,9 điểm vượt sàn nhiễu
U1 (±3,0) và có cơ chế truy được. Q6 doc-2 đạt ngưỡng ≤ 5% theo ước lượng điểm; Wilson 95% của 3/61 là 1,7–13,5% nên theo luật
khoảng là **chưa đủ bằng chứng**. Ba vi phạm còn lại: `Column-row factorization` không có câu neo (vị trí rơi về chunk 379, trước
`Column rank` 385); `Operator` — sách đặt ngược thật (định nghĩa ở 5.1, dùng từ chương 3); `Nonnegative integers → Matrix` —
cạnh vàng đáng ngờ, máy có đường ngược.
So với C8 v2 (chuỗi mặc định hiện hành, trước identity): Q6 doc-1 5,0% → 2,6%, doc-2 8,2% → 4,9%.

### N1 doc-6 — kết quả (2026-09-26)

Nhãn T3 (`nhan-khai-niem-doc-6-output.xlsx`, SHA-256 `7862027cd1779b8f…`): 17 "được dạy", 10 "chỉ được nhắc", 1 "không chắc",
**0 phải loại**. **Ô ghi chú dòng 1 ghi: "BẢN THAM KHẢO DO AI GÁN — KHÔNG PHẢI NHÃN NGƯỜI"** — trái với xác nhận trước của chủ dự
án; chờ xác nhận lại. Chuỗi mặc định doc-6: validated v6 → C8 v2 v7 → stages v8 (28 khái niệm, 4 module). Neo C8 v3: teaching v9,
0,011 USD.

| | C8 v3 (neo) | C8 v2 |
|---|---|---|
| loại nhầm | **0/27** | 0/27 |
| "được dạy" → `taught` | 12/17 | 13/17 |
| "chỉ được nhắc" → `mentioned_only` | 10/10 | 10/10 |

**Cổng 2 gộp N1 (doc-5 + doc-6):** loại nhầm **0/52** — đạt theo điểm (≤ 1 cho phép); Wilson 95% 0–6,9% nên theo luật khoảng
chưa đủ bằng chứng cho "≤ 2%". **Vế loại đúng: không đo được** — cả hai tài liệu N1 đều có 0 khái niệm phải loại, vì A3 đã tách
dữ liệu ví dụ thành bảng/hình và không trích tổ chức/người thành khái niệm learnable. Bằng chứng về vế này chỉ có trên dữ liệu
phát triển và là **điểm yếu**: doc-3 loại đúng 6/13 (C8 v3) — dưới 80%; doc-1 3/3 node hành chính.
