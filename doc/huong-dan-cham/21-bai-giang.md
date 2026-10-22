# Hướng dẫn chấm bài giảng (SA-21)

Đọc [luật chung](00-chung.md) trước. Giao thức gốc: [báo cáo bài giảng](../../report/nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md), mục 6.3–6.4;
vé [SA-21](../../task/sau-a10/21-danh-gia-bai-giang.md). Cấu trúc bài: [spec Pha B2](../pha-b2-spec.md), mục 6 (`lecture-2`).

**Thời gian:** phần 1 khoảng 7,5 giờ (50 khái niệm), phần 2 khoảng 2,5 giờ. Chấm thử: 2 khái niệm. Nên chia 8–10 buổi.

## 1. Việc này để làm gì

Khi người học bấm vào một khái niệm trên lộ trình, hệ thống mở một **bài giảng ngắn** về khái niệm đó. Ta muốn biết bốn điều:
- bài do mô hình viết có đúng, trung thực, có ích hơn bản chỉ trích câu sách không;
- đồ thị tiên quyết có giúp bài tốt hơn không;
- cách đặt nhiệt độ của mô hình có làm bài lặp ý không;
- ví dụ ngoài sách có gây sai không.

## 2. Bạn nhận được gì

- `phieu-sa21-<mã>.html`: để **đọc**. Mỗi khái niệm một mục, gồm phần đầu và 4–5 bản bài giảng.
  - **Phần đầu,** giống nhau cho mọi bản: tên khái niệm, module, câu định nghĩa nguyên văn kèm trang, ảnh công thức nếu có.
  - **Các bản bài giảng** A, B, C, D (có khi thêm E), thứ tự ngẫu nhiên. Mỗi bản có thể có các khối:
    - **gợi lại tiên quyết:** khái niệm cần biết trước, kèm câu nối;
    - **giải thích;**
    - **ví dụ;**
    - **phân biệt** với khái niệm gần;
    - **tiếp theo:** khái niệm học sau.

    Không phải bản nào cũng có đủ các khối; thiếu khối là một phần của bản đó.
  - **Nhãn nguồn** `[S1]`, `[Q2]`…: bấm vào thì hiện câu trích từ sách kèm trang.
  - **Ví dụ ngoài sách:** nằm trong khung ghi rõ "ngoài sách".
- `cham-sa21-<mã>.xlsx`, với hai sheet chấm: **Chấm bài** (phần 1) và **Chấm ý** (phần 2).

## 3. Phần 1: chấm từng bản rồi xếp hạng

Sheet **Chấm bài**: mỗi khái niệm là một nhóm dòng liền nhau, mỗi dòng một bản.

**Bước 1 — đọc và chấm từng bản** (cột vàng):

| cột | giá trị | nghĩa |
|---|---|---|
| `so_y_sai` | `0`, `1`, `2`, `3+` | số ý **sai so với sách**: nói ngược sách, nhầm khái niệm, công thức sai. Ý sách không nói nhưng không sai thì không tính ở đây (phần 2 mới chấm) |
| `su_pham` | 1–5 | bản này giúp người học hiểu khái niệm tới đâu (thang ở dưới) |
| `doc_duoc` | 1–5 | mạch lạc, đúng tiếng Việt, không lặp ý (thang ở dưới) |
| `do_dai` | `ngan_qua` / `vua` / `dai_qua` | so với lượng cần để hiểu khái niệm này |
| `cau_noi` | `dat` / `co_loi` / trống | chỉ khi bản có câu nối trong khối gợi lại. `co_loi` nếu **một** câu nối sai quan hệ, trích sai nguồn, hay bịa |
| `goi_lai_tiep_theo` | `co_ich` / `trung_tinh` / `thua` / trống | chỉ khi bản có khối gợi lại hay khối tiếp theo: hai khối này có giúp người học không |
| `ngoai_sach` | `dung` / `gay_hieu_lam` / `sai` / trống | chỉ khi bản có ví dụ ngoài sách. **Chấm bằng hiểu biết chung**, vì sách không có ví dụ này |

Thang `su_pham`:
- **5:** hiểu rõ hơn hẳn so với chỉ đọc câu định nghĩa. Gợi lại đúng nền cần có, giải thích làm sáng ý khó, ví dụ hay phần phân biệt thật sự có ích.
- **3:** có ích, nhưng phần lớn chỉ nhắc lại định nghĩa, hoặc có khối thừa.
- **1:** không giúp gì, hoặc làm rối thêm.

Thang `doc_duoc`:
- **5:** trôi chảy như người dạy viết, không lặp.
- **3:** đọc được nhưng có chỗ vụng, lặp ý, hay câu cụt.
- **1:** khó đọc, lủng củng, lặp nhiều.

Dùng 2 và 4 cho mức giữa.

**Bước 2 — xếp hạng** (cột `hang`, ghi ở mọi dòng của nhóm):
- Câu hỏi: nếu bạn là người học và muốn hiểu khái niệm này, bạn **muốn đọc bản nào nhất**?
- 1 là tốt nhất, được để bằng hạng.
- Xếp hạng sau khi đã chấm cả nhóm. Một bản có ý sai thì khó có thể đứng hạng 1.

## 4. Phần 2: chấm từng ý có được nguồn đỡ không

**Mở phần 2 sau khi đã nộp phần 1.** Phần 2 nằm trong tệp riêng `cham-sa21-y-<mã>.xlsx`, đi kèm `phieu-sa21-y-<mã>.html`.

Mỗi dòng là **một ý** của một bài giảng, cùng các câu trích nguồn mà ý đó dẫn. Không có nhãn bản. Bạn có thể nhận ra bài đã đọc ở phần 1; điều đó không
sao.

| cột | giá trị | nghĩa |
|---|---|---|
| `duoc_do` | `tron` / `mot_phan` / `khong` | các câu trích **mà ý này dẫn** có chống đỡ ý không (theo khung AIS: "theo nguồn này, có thể nói như vậy không?") |

- `tron`: mọi điều ý nói đều suy ra được từ câu trích.
- `mot_phan`: một phần ý được đỡ; phần còn lại thêm điều câu trích không nói.
- `khong`: câu trích không nói điều đó, hay nói khác đi.

Chỉ xét câu trích mà ý dẫn. Ý đúng theo phần khác của sách nhưng **không** theo câu trích mà nó dẫn thì là `khong`: trích dẫn sai là lỗi.

## 5. Ca khó

- **Bản chỉ gồm câu trích nguyên văn.** Thường `so_y_sai = 0` và `doc_duoc` không cao. Chấm `su_pham` thật: chép đúng câu sách có thể vẫn ít giúp người
  học.
- **Bản ngắn hơn hẳn các bản khác.** Ngắn không phải lỗi. `do_dai = ngan_qua` chỉ khi thiếu điều cần để hiểu.
- **Công thức.** So với ảnh công thức gốc ở phần đầu. Công thức chép sai ký hiệu là ý sai.
- **Hai bản gần giống hệt nhau.** Có thể xảy ra. Chấm từng bản như bình thường, được để bằng hạng.
- **Câu nối nói đúng nhưng không dẫn đúng tiên quyết:** `cau_noi = co_loi`, ghi lý do.

## 6. Kết quả của bạn được dùng thế nào

Từ thứ hạng, Claude tính bản thiết kế chính thắng từng bản so sánh ở bao nhiêu khái niệm. Luật quyết định đã viết trước, ở mục 6.4 của báo cáo và trong
vé SA-21:
- tỉ lệ ý không được nguồn đỡ (phần 2) phải ≤ 5%;
- bản theo nhiệt độ khác thắng ở chấm mù thì đề xuất đổi nhiệt độ;
- ví dụ ngoài sách sai hoặc gây hiểu lầm quá 5% thì đề xuất tắt.
