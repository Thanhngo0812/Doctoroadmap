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
