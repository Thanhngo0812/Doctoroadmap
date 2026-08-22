# F29 — Review đợt ba trần token

Vòng review 6 · 2026-08-21 · Phạm vi: [`task/b0-tran-bang/`](../task/b0-tran-bang/) 4/4 ticket + `note.md`

## Kết luận

**48/48 tiêu chí tick, 0 bỏ sót, và mọi khẳng định đều đúng khi tôi đo lại.** Không thoái lui nào qua năm đợt
trước.

Một phát hiện, và nó là **lỗ hổng trong ticket tôi viết**, không phải trong việc họ làm.

## Kiểm chứng độc lập

| Khẳng định | Cách kiểm | Kết quả |
|---|---|---|
| Test | chạy `pytest` | ✅ **85 passed**, exit 0 |
| **Tập chunk ID không đổi** | so với hash **tôi tự đo trước đợt** | ✅ `726dce8b…d3d7a5` **khớp từng byte** |
| " " | hai chunk ID tôi ghi từ nhiều đợt trước | ✅ cả hai còn nguyên |
| Ba trần | đọc manifest | ✅ `max_tokens=512`, `max_table_tokens=2048`, `hard_cap_tokens=6000` |
| Bump đúng một lần | manifest | ✅ `section-id-v6`; `adapter_version` giữ **6**, không đổi |
| **Bảng 11 hàng 6 cột** | dựng và chunk | ✅ **1 chunk** (529 tok) — ca mở đầu spec, đã sửa |
| Câu dẫn gộp cùng bảng | bảng 30 hàng + câu dẫn | ✅ `698tok ['text','table']` |
| Bảng nhỏ không hút văn xuôi | bảng 4 hàng + 6 đoạn văn | ✅ max **319**, không gần 2048 |
| Văn xuôi không hưởng trần bảng | khối 830 token | ✅ cắt thành 508+336, mọi mảnh ≤ 512 |
| **I20** không ngoại lệ | khối 22.891 token không dấu kết câu | ✅ 4 mảnh, max **5996**, mọi mảnh ≤ 6000 |
| CJK không khoảng trắng | khối 7200 token, 0 dấu cách | ✅ 2 mảnh, max **đúng 6000**, ghép lại **y hệt gốc** |
| Hàng bảng vượt trần cứng | hàng 4500 từ | ✅ 4 mảnh, max 5997 |
| **Không vỡ dấu tiếng Việt** | quét ký tự đầu mọi mảnh | ✅ **0** mảnh bắt đầu bằng dấu phụ |
| Cắt rơi vào ranh giới từ | đọc đuôi từng mảnh | ✅ `'…từ1420 '` — cửa sổ lùi tìm được khoảng trắng |
| **I9 với mảnh cắt cưỡng bức** | `full[start:end] == text` | ✅ **0 vi phạm**, span liền mạch, khoảng trống 0 |
| Phân biệt hai loại vượt trần | khối 4891 tok dưới trần cứng | ✅ `sentence_splitter_no_boundary`, **không** phải cắt cưỡng bức |

**Không thoái lui:** char-span 0/41 · glyph 0 · cây 4 cấp · 5/5 nối câu qua trang · base64 0 · 9/9 tham chiếu
hình resolve · caption `Hình 2` còn · 0 id trùng.

## Ba chỗ làm rất tốt

**1. Cắt cưỡng bức giữ được I9.** Đây là chỗ dễ hỏng nhất và họ làm đúng: span của các mảnh liền mạch, khoảng
trống bằng **0** — không phải 1 như giữa hai leaf block, vì cắt xảy ra *trong* một block nên không có ký tự
xuống dòng chen vào. Chi tiết đó không có trong ticket; họ tự suy ra.

**2. Phân biệt đúng hai lý do.** Khối 4891 token dưới trần cứng nhận `sentence_splitter_no_boundary`; khối
vượt trần cứng nhận `hard_cap_forced_split`. Không lẫn.

**3. Báo cáo thường trực cũng được cập nhật**, không chỉ `note.md` — kể cả hash `726dce8b…` ghi thẳng vào mục
đối chiếu, và lịch sử phiên bản qua ba đợt.

---

## F29 🟡 — Cắt cưỡng bức xảy ra **im lặng** khi bộ tách câu chạy tốt

### Hiện tượng

```
khối 13.903 token · bộ tách tách được 2 câu (CHẠY TỐT)
-> 4 chunk, 3 mảnh mang lý do 'hard_cap_forced_split'
   structure_warnings: []          <- RỖNG
```

Một câu khổng lồ nằm giữa các câu bình thường. Bộ tách **không bó tay** — nó tìm được ranh giới. Nhưng câu
khổng lồ vẫn vượt trần cứng nên bị cắt cưỡng bức, và **không có cảnh báo nào**.

### Vì sao đáng nói

Mức độ nghiêm trọng **ngược** với mức độ ồn ào:

| Chuyện gì | Hậu quả | Có kêu không |
|---|---|---|
| Bộ tách bó tay | một chunk to, ranh giới ngữ nghĩa **còn nguyên** | ✅ có |
| **Cắt cưỡng bức** | cắt giữa câu tại một vị trí tuỳ ý, ranh giới ngữ nghĩa **bị phá** | ❌ **không** |

Cắt cưỡng bức là thao tác phá hoại nhất trong toàn bộ đường ống. Nó chỉ kêu khi **tình cờ** đi kèm một lỗi
khác — đúng ca tôi thử đầu tiên, nên suýt nữa tôi kết luận là có cảnh báo.

Thông tin **không mất**: mỗi chunk mang `oversize_reason`, quét là thấy. Nhưng thứ người vận hành nhìn —
manifest và dòng lệnh — thì im.

### Đây là lỗi của tôi

Ticket `03` tôi viết chỉ yêu cầu *"chunk bị cắt cưỡng bức mang một lý do riêng biệt"*. Không có dòng nào đòi
cảnh báo ở mức tài liệu. Họ làm đúng **toàn bộ** những gì ticket ghi.

Đợt trước tôi viết ticket cho cảnh báo khi bộ tách bó tay và nghĩ rằng thế là đủ. Không đủ — tôi bỏ sót đúng ca
mà bộ tách thành công.

### Mức độ: thấp

Trên corpus hiện tại **không bao giờ** xảy ra — khối lớn nhất 400 token. Đây là chuyện của tài liệu có một câu
dài bất thường, ví dụ một danh sách rất dài không có dấu chấm, hoặc dữ liệu bị dán nhầm vào thân bài.

### Đề nghị

Thêm một lý do cảnh báo khi có mảnh nào bị cắt cưỡng bức, kèm số trang hoặc mục — đúng khuôn của
`sentence_splitter_no_boundary`. Một dòng, và nó biến thao tác phá hoại nhất thành thao tác ồn ào nhất.
