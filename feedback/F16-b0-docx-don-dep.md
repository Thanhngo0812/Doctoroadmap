# F41–F43 — Review đợt DOCX và dọn dẹp

Vòng review 10 · 2026-08-29 · Phạm vi: [`task/b0-docx-don-dep/`](../task/b0-docx-don-dep/) 10/10 ticket
(cả ticket 10 chuỗi chương thêm sau)

## Kết luận

**Về nội dung kỹ thuật, đây là đợt sạch nhất từ trước tới nay** — mọi tiêu chí tôi đo lại độc lập đều khớp,
vài chỗ khớp đến mức số học nội tại tự xác nhận lẫn nhau. Nhưng **một checkbox của ticket đóng đợt không
đúng sự thật** (F41): ingest thật chưa hề chạy, kho artifact vẫn là đời cũ. Và kỷ luật commit-kèm-giải-thích
mà chính đợt này dựng lên đã không được dùng lần nào (F42).

## Kiểm chứng độc lập

| Khẳng định | Kết quả |
|---|---|
| Test | ✅ **115 passed**, exit 0 (97 → 115, +18) |
| Nhích phiên bản đúng một lần mỗi tầng | ✅ adapter 7→8 · `section-id-v8` |
| Giáo trình: không một định danh chunk nào đổi | ✅ so **trực tiếp** artifact v2 ↔ replay: 41/41, 126/126 giống hệt cả thứ tự |
| DOCX: cây hai cấp đủ 27 section | ✅ 17 mục chữ cái, **0** ở cấp gốc |
| Nối run | ✅ `'…bằng Docker Compose, thực hiện kiểm thử…'` liền mạch · mở-đầu-giữa-câu 25 → **2** · `runs_stitched: 56` và **269 − 56 = 213 node** — số học tự khớp |
| Lọc rác | ✅ chunk chấm 2→0, chunk mục lục 2→0 · bảo toàn chữ cái **732 = 390 + 342, khớp từng ký tự** |
| Ảnh DOCX | ✅ 3 PNG trích, 3 dấu `[figure]` = 3 `image_refs`, không dấu mồ côi |
| Slide | ✅ PUA trong chunk 72 → **0** · `stripped_pua_bullets: 72` · chunk 513 token mang `oversize_reason: table_kept_whole_above_text_limit` (I25 sống) · cảnh báo gom `×7` (F34 sống) |
| Từ khoá chương | ✅ biến mất khỏi mã nguồn; luật chuỗi có test La Mã, tiền tố lạ, running header, lồng nhau |
| Bốn tài liệu đứng yên với ticket 10 | ✅ số vàng bốn tài liệu không dịch cột nào |
| ADR 0003 · ADR 0002 · README · từ điển · báo cáo thường trực | ✅ đủ, đúng khuôn |
| Câu khám phá ticket 01 | ✅ trả lời trong README fixture: 3/3 picture mang dữ liệu, kèm sha256 nguồn và cỡ đúng từng byte |

## Chỗ làm tốt hơn mong đợi

**Cảnh báo DrawingML đặt đúng tầng.** Fixture không có byte OOXML nên nhánh "hình vẽ không render được"
không thể kiểm bằng replay — họ đặt phép dò ở `parse()`, nơi có byte nguồn, dò chuỗi schema trong zip, kèm
test dựng DOCX giả. Tôi chạy thêm phép dò **trên file thật**: `_has_drawingml_shape → True`, file có đúng cả
`wordprocessingShape` (logo) lẫn `drawingml/2006/picture` (3 PNG). Thiết kế vượt chữ của ticket.

**Guard ngoài ticket:** *"tiền tố chỉ có ký hiệu không tạo chuỗi"* trong ADR 0003 — chặn một lớp nhận nhầm
mà ticket 10 không nghĩ tới.

---

## F41 🔴 — Ticket 09 tick "ingest thật bốn tài liệu" nhưng kho artifact chứng minh ngược lại

### Bằng chứng

```
nhap-mon-ml : chunks v1 (08-21) · v2 (08-22)     ← đời adapter 7, vòng 8
baocao      : chunks v1 · v2 (08-29 01:34/02:26) ← TÔI sinh, trước đợt, adapter 7
naive-bayes : chunks v1 (08-29 01:40)            ← TÔI sinh, trước đợt — không có cả v2
```

Adapter nhích 8, thuật toán nhích v8 ⇒ ingest thật **phải** sinh phiên bản mới. Không tồn tại phiên bản nào.
Checkbox *"[x] Ingest thật bốn tài liệu trên cây sạch; artifact phiên bản mới sinh đúng một lần"* — sai.

### Cái gì thật, cái gì chưa

Phần đối chiếu **nội dung** làm trên fixture là hợp lệ — tôi tự replay và mọi con số khớp. Cái chưa có:

1. **Chuỗi ingest thật** (Docling parse thật → adapter 8 → artifact v3) chưa chạm bốn tài liệu thật.
   Riêng nhánh DrawingML tôi đã kiểm hộ trực tiếp; phần còn lại của chuỗi vẫn nợ.
2. **Artifact trên đĩa là đời cũ** — ai `inspect` lúc này thấy cây DOCX gãy của tuần trước.
3. Một checkbox sai làm giảm giá trị của cả bàn giao — dự án này review bằng niềm tin vào ticket đã tick.

### Sửa

Chạy `ingest` thật cả bốn, xác nhận mỗi tầng sinh đúng một phiên bản mới, `inspect` đối chiếu cây DOCX,
xác nhận cảnh báo `missing_image` xuất hiện trong artifact thật. Ước lượng: ~10 phút máy chạy.

## F42 🟡 — Kỷ luật "đổi số vàng kèm giải thích trong cùng commit" chưa từng được dùng

Không một commit nào trong toàn đợt — tất cả là một khối working-tree. Ticket 02 dựng đúng cơ chế
*"diff của số vàng chính là biên bản review"*, nhiều ticket hứa *"liệt kê trong commit"* — nhưng không có
commit thì không có diff, không có biên bản; tôi chỉ review được **trạng thái cuối**, không thấy được từng
cú dịch chuyển qua từng ticket. May là trạng thái cuối đo lại đều khớp. Cơ chế then chốt của đợt bị bỏ
không dùng ngay lần đầu tiên có nó.

Đề nghị từ đợt sau: mỗi ticket một commit, số vàng dịch trong commit nào thì lời giải thích nằm trong
message của commit đó.

## F43 🟢 — Ghi nhận: `missing_image` cho DrawingML nói "có thứ không render được", không nói mất gì

Logo DrawingML **không bao giờ thành picture item** — Docling vứt từ tầng parse, nên "phần còn lại" cần
`missing_image` ở mức node là **rỗng** trên corpus hiện tại (checkbox ticket 03 mô tả một tập rỗng — không
sai, nhưng dễ đọc nhầm là đã có ca thật). Cảnh báo OOXML-level bù đúng chỗ, nhưng chỉ nói *tài liệu có hình
vẽ không render được*, không nói **ở đâu, mất bao nhiêu**. Chấp nhận được cho hiện tại; ghi lại để đừng
tưởng có cảnh báo nghĩa là có đủ thông tin.

## Hai chỗ tôi phải sửa số của chính mình

- **"67 → 42 section" ở vòng 8 phải đọc là 42 không tính root** — artifact v2 có **43 entry** (42 + root),
  và số vàng ghim 43 là đúng. Tôi đã nghi số vàng sai trước khi nghi cách đếm của mình.
- Phép bảo toàn chữ cái lần đo đầu lệch 342 vì tôi **đếm sót chunk mục-lục thứ hai** (nó không chứa hai
  chuỗi mốc tôi dò). Đếm lại theo section: khớp từng ký tự. Lần thứ tư trong dự án: số lạ thì đo lại bằng
  đường khác trước khi kết luận.
