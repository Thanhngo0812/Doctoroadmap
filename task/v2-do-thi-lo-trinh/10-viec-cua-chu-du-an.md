# 10 — [Chủ dự án] Việc của người trong đợt v2

**Nguồn chân lý:** spec v2, mục *Tiêu chí nghiệm thu đã chốt* và W18

**What to build:** các phán đoán mà chỉ người làm được — vì người viết hệ thống không mù được với kết quả của nó (ADR 0009).
Không phải việc cho agent. Vé này tồn tại để các cạnh chặn tới cổng nhận của vé 04–07 hiện rõ.

**Luật chung cho mọi việc dưới đây**

- **Mù và độc lập.** Không mở bộ vàng cũ, không mở lộ trình máy của phần đang chấm, không trao đổi với người kia trước
  khi cả hai xong.
- **Ghi giờ thật** lúc bắt đầu và lúc xong vào ô ghi chú của tệp (luật dự án: không ước lượng).
- **Không mở tập giữ lại** `artifacts/a8-gold/xstk-ch3-1-chuong-10-13-*` cho tới vé 07.
- Làm xong thì báo tôi tên tệp; tôi chấm bằng script có sẵn và dán số vào vé tương ứng.

## Tóm tắt

| | việc | ai | thời lượng | làm khi nào | chặn |
|---|---|---|---|---|---|
| **T1** | chấm mù cạnh dư | 2 người, riêng | ~30–40 phút / người | **ngay** | vé 06; quyết định C1 cho `doc-2` |
| **T2** | đưa hai tài liệu mới N1, N2 | chủ dự án | ~10 phút | **ngay** | vé 04 (N1), vé 07 (N2) |
| **T7** | liệt kê mù khái niệm trọng yếu | 1 người | ~15 phút / phần × 6 | **ngay** — trước khi xem lộ trình mới | Q3 |
| T6 | chấm độ mạch lạc module (A/B) | 2 người, riêng | ~30 phút / người | sau vé 02 (tôi báo) | Q8 |
| T3 | gán nhãn khái niệm mù trên N1 | 1 người | ~20 phút | sau khi tôi nhập N1 (tôi báo) | cổng vé 04 |
| T4 | kiểm tay 50 câu neo | 1 người | ~25 phút | sau vé 04 | Q9 |
| T5 | duyệt các gộp khái niệm chạm bộ vàng | chủ dự án | ~10 phút | sau vé 05 | cổng vé 05 |
| T11 | chấm mù vòng hai (cạnh mới) | 2 người, riêng | ~15 phút / người | sau vé 06 | cổng vé 06 |
| T8 | gán vàng cạnh cho N2 (tập giữ lại) | 2 người + hội ý | ~1,5–2 giờ / người + ~30 phút | sau vé 04–05 | vé 07 |
| T10 | duyệt cấu hình khoá | chủ dự án | ~10 phút | trước vé 07 | vé 07 |

Ba việc đầu làm được ngay và không phụ thuộc gì.

### Trạng thái (2026-09-24)

| | trạng thái |
|---|---|
| T1 | **xong** — hai người thật, riêng (chủ dự án xác nhận); không ghi giờ. Kết quả ở vé 06 |
| T2 | **N2 xong**: `doc-4.pdf` (giáo trình Triết học Mác–Lênin, 214 trang); chương gán vàng đề xuất: Chương VIII. **N1 còn thiếu** — tiêu chí chi tiết ở mục T2 |
| T4 | **xong** — phán quyết người, AI hỗ trợ ghi; không có giờ làm thật. Q9 44/48 |
| T5 | **xong** — như T4. 4/4 gộp chạm vàng được duyệt; `Trace` "Không chắc" → giữ tách |
| T3 | **sẵn sàng**: `nhan-khai-niem-doc-5.xlsx` — 25 khái niệm của doc-5 (N1), khoảng 5–10 phút; phải do người, trước khi tôi chạy neo trên doc-5 |
| T6 | **nhận 2026-09-25** — Q8: 4,40 / 4,20 (stage cũ 1,70 / 1,95); bản A2 ghi "AI thực hiện" → chờ xác nhận nguồn |
| T7 | **nhận nhưng chưa dùng được**: tệp ghi "AI đọc độc lập; chưa được người chấm xác nhận", và đọc **trang in** thay vì trang PDF (doc-2 lệch 14 trang, doc-1 lệch 1) — cần làm lại theo trang PDF, do người |
| T8 | **phần 1 xong**: A1 65 cạnh / 13 cờ, A2 53 cạnh / 2 cờ, không lỗi, không ghi giờ. **Phần 2 — hội ý**: `doc-4-chuong-8-hoi-y.xlsx`, 41 dòng trùng, **36 dòng lệch** cần hai người cùng quyết |
| T11 | **xong 2026-09-25** — pass cạnh ngầm trượt cổng 2 (17–58% "không làm sai thứ tự học"), không bật |
| T10 | chưa tới lượt |

Luật ghi giờ: bảng nhận ngày 2026-09-24 có mốc giờ là của AI hỗ trợ ghi, không phải của người. Từ nay xin ghi giờ người
bắt đầu / xong ở ô ghi chú dòng đầu, tách khỏi mọi mốc giờ do công cụ sinh.

## T1 — Chấm mù cạnh dư

**Vì sao:** precision so với bộ vàng không phân biệt được "máy sai" với "vàng không ghi". Chỉ người đọc mù mới trả lời
được cạnh dư của máy có làm sai thứ tự học không. Kết quả quyết có chi ~7,4 USD cho C1 trên `doc-2` hay không.

1. Mỗi người chép hai tệp thành bản riêng: `artifacts/a8-gold/cham-mu-doc-1.xlsx` → `cham-mu-doc-1-A1.xlsx` (người
   thứ hai: `-A2.xlsx`); tương tự `cham-mu-doc-2.xlsx`.
2. Đọc sheet **Hướng dẫn**. Ở sheet **Cặp**, mỗi dòng chọn một phán quyết trong ô **Phán quyết** (danh sách thả xuống,
   sáu lựa chọn). Tra nơi dạy và câu định nghĩa ở sheet **Khái niệm**.
3. Không chắc thì chọn *Không chắc* — đừng đoán. Mọi dòng phải có phán quyết.
4. Tổng 87 cặp (57 + 30).

## T2 — Đưa hai tài liệu mới

- **N1 — để kiểm lần đầu gói neo định nghĩa.** Một bài giảng dạng slide, **có** trang hành chính (điểm số, bài tập, giới
  thiệu giảng viên) **và** có ví dụ dùng bảng dữ liệu hoặc hình có nhãn. 30–80 trang; tiếng Việt hoặc tiếng Anh; khác các
  tài liệu đang có. Đây là chỗ C8 từng bỏ lọt rác, nên tài liệu càng "bẩn" càng tốt cho phép thử.
  Danh sách kiểm (bổ sung 2026-09-24, sau khi doc-4 được xếp vào N2):
  - **Dạng:** PDF xuất từ slide bài giảng đại học (PowerPoint / Beamer), không phải giáo trình văn xuôi.
  - **Có trang "rác" thật:** giới thiệu môn học / đề cương, thang điểm hoặc cách đánh giá, lịch học, thông tin giảng viên,
    bài tập về nhà. Ít nhất 3 trang loại này.
  - **Có ví dụ cụ thể:** bảng dữ liệu, hình có nhãn (sơ đồ, biểu đồ), ví dụ tính toán với tên biến / giá trị riêng.
  - **Môn khác các tài liệu đã có:** không phải đại số tuyến tính, học máy nhập môn, Naive Bayes, xác suất thống kê,
    triết học, báo cáo dự án phần mềm. Ví dụ hợp: Cơ sở dữ liệu, Mạng máy tính, Cấu trúc dữ liệu và giải thuật, Kinh tế
    vi mô, Hệ điều hành — buổi 1–3 của một môn (thường có sẵn trang giới thiệu môn).
  - **Cỡ:** 30–80 trang slide, 40–80 khái niệm.
  - **Có chữ thật trong PDF** (bôi đen chọn được chữ), không phải ảnh chụp.
  - Nếu gộp nhiều tệp slide thành một PDF thì giữ nguyên thứ tự buổi học.
- **N2 — tập giữ lại.** Một chương giáo trình hoặc bộ slide khác môn và khác nguồn với N1, khoảng 30–60 khái niệm.
- Gửi tôi đường dẫn hai tệp PDF. Tôi nhập bằng `ingest` và chạy tới bảng khái niệm; chi phí A3–A4 ước ~1 USD mỗi tài liệu,
  tôi dán số thật. **Đừng đọc kỹ N2 trước T8** để lúc gán vàng vẫn là lần đọc đầu.

## T7 — Liệt kê mù khái niệm trọng yếu

**Vì sao:** mọi phép chấm hiện có chỉ chấm trên danh sách khái niệm do máy đưa ra, nên không phát hiện được khái niệm
quan trọng mà máy chưa từng trích (Q3).

Sáu phần, bốc ngẫu nhiên với seed cố định (số trang là trang của tệp PDF):

| tài liệu | phần | trang |
|---|---|---|
| `doc-1` | 2.5 Hệ phương trình tuyến tính | 31–39 |
| `doc-1` | 3.4 Không gian con — Hạng của một hệ véc tơ | 54–59 |
| `doc-1` | 3.5 Không gian véc tơ Euclid | 60–66 |
| `doc-2` | Chapter 3 | 65–72 |
| `doc-2` | Chapter 5 | 146–153 |
| `doc-2` | Chapter 9 | 346–353 |

Với mỗi phần: đọc các trang đó, rồi viết danh sách **khái niệm mà người học phải nắm được từ chính các trang này** — mỗi
dòng một tên, theo cách tài liệu gọi. Không liệt kê khái niệm chỉ được nhắc qua. Không mở danh sách khái niệm của máy.
Ghi vào một tệp văn bản `artifacts/a8-gold/liet-ke-mu.md`, mỗi phần một tiêu đề. Nên do người thứ hai làm.

**Sẵn sàng (2026-09-24):** tệp mẫu `artifacts/a8-gold/liet-ke-mu.md` đã có sáu tiêu đề và chỗ ghi giờ. Chấm bằng
`scripts/liet-ke-mu/cham_q3.py`: khớp đúng tên/alias thì tính tự động; còn lại script sinh `liet-ke-mu-doi-chieu.xlsx` với
ba khái niệm máy gần nhất, người điền cột xác nhận (tên khái niệm máy, hoặc «Không có») rồi chạy lại để ra Q3.

## T6 — Chấm độ mạch lạc module

**Đã sẵn sàng (2026-09-24).** `artifacts/a8-gold/cham-module.xlsx`: 20 đơn vị từ lộ trình cũ và 20 từ lộ trình mới, xáo trộn,
ẩn tên hệ thống. Sheet **Đơn vị** chỉ hiện danh sách khái niệm (không tên, không thứ tự — tên và thứ tự sẽ để lộ hệ
thống); chấm **độ mạch lạc** 1–5. Xong hẳn sheet đó rồi mới mở sheet **Tên module** (15 module khác), chấm tên đúng /
một phần / không. Hai người, riêng; lưu thành `cham-module-A1.xlsx`, `cham-module-A2.xlsx`.

## T3 — Gán nhãn khái niệm mù trên N1

Sau khi nhập N1 tôi sinh `artifacts/a8-gold/nhan-khai-niem-N1.xlsx` (~60 khái niệm, kèm nơi xuất hiện). Mỗi dòng chọn:
*Giữ — được dạy* / *Giữ — chỉ được nhắc* / *Loại — hành chính của khoá học* / *Loại — chi tiết của một ví dụ, hình hoặc bộ
dữ liệu* / *Loại — người, tổ chức, siêu dữ liệu* / *Kiến thức nền cần có trước* / *Không chắc*. Phải xong **trước** khi tôi
chạy gói neo trên N1.

## T4 — Kiểm tay 50 câu neo

**Sẵn sàng (2026-09-24):** `artifacts/a8-gold/kiem-cau-neo.xlsx` — 50 khái niệm ngẫu nhiên trên 6 tài liệu (không có
`xstk-ch3-1`, tài liệu tập giữ lại), mỗi dòng có câu neo trong ngữ cảnh, trang và mục. Khoá: `kiem-cau-neo-khoa.json`.
Chọn: *Đúng nơi dạy* / *Sai — chỉ nhắc qua* / *Sai — nói về nghĩa khác* / *Không chắc*.

## T5 — Duyệt gộp khái niệm

**Sẵn sàng (2026-09-24):** `artifacts/a8-gold/duyet-danh-tinh.xlsx` — 10 cặp (4 chạm vàng, bắt buộc; 6 còn lại nên duyệt),
mỗi dòng có hai câu neo và đề xuất của hệ thống. Chọn *Đồng ý gộp* /
*Không gộp* / *Là hai nghĩa khác nhau*.

## T11 — Chấm mù vòng hai

Như T1, trên khoảng 30 cặp gồm cạnh mới của vé 06 trộn với cạnh đúng và cặp ngẫu nhiên.

## T8 — Gán vàng cạnh cho N2

Như lần gán vàng `doc-1` / `doc-2`: tôi sinh bảng gán bằng `a8-gold-sheet` cho một chương của N2 **sau khi** danh sách khái
niệm đã ổn định (vé 04–05); hai người gán riêng theo [hướng dẫn gán nhãn](../../doc/huong-dan-gan-nhan-tien-quyet.md), rồi
hội ý. Kết quả khoá lại, chỉ mở ở vé 07.

## T10 — Duyệt cấu hình khoá

Trước vé 07 tôi đưa: commit, `prompt_hash` từng khâu, tham số, ngưỡng. Bạn xác nhận không đổi gì nữa; từ đó mọi thay đổi là
hậu kiểm.
