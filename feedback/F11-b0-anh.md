# F27 — Review đợt B0 ảnh

Vòng review 4 · 2026-08-20 · Phạm vi: [`task/b0-anh/`](../task/b0-anh/) 7/7 ticket + `note.md` + `report/`

**Trạng thái:** ✅ Đã xử lý ngày 2026-08-21.

## Kết luận

**Đợt sạch nhất từ đầu dự án.** Mọi con số nhân viên khai đều khớp chính xác khi tôi đo lại, không có thoái lui
nào ở ba đợt trước, và họ **tìm ra một lỗi nghiêm trọng mà tôi bỏ sót** khi viết ticket.

Đúng **một** mục cần xử lý, và nó không nằm trong phạm vi đợt này.

## Kiểm chứng độc lập — chạy lại, không đọc dấu tích

| Khẳng định | Cách kiểm | Kết quả |
|---|---|---|
| 51 test xanh | chạy `pytest` | ✅ 51 passed, exit 0 |
| **Mìn base64 đã gỡ** | quét độ dài text mọi node | ✅ **0** node > 2000 ký tự; dài nhất **940**; 0 node/chunk chứa `base64` |
| 9 PNG, 821.359 byte | đếm file, cộng byte | ✅ khớp **đến từng byte** |
| Định danh = băm nội dung | tính lại sha256 từng file | ✅ tên file == sha256 nội dung, 9/9 |
| 9/9 ref resolve | mở từng file theo `image_id` | ✅ 0 thiếu; 0 ảnh mồ côi không ai trỏ |
| `char_start` đúng chỗ | cắt chuỗi tại offset | ✅ 0 ref nằm ngoài span chunk; offset trỏ đúng đầu caption |
| **`image_refs` ngoài khoá băm** | **tính lại `chunk_id` bằng công thức không có `image_refs`** | ✅ **41/41 khớp** |
| `block_types` | đếm theo loại | ✅ 16 chunk đa loại; **14 chunk có `list_item`** (trước: 0); trường cũ đã biến mất |
| Cước chú vẫn riêng | lọc chunk có footnote | ✅ 3 chunk, **0** cái gộp chung loại khác |
| Caption mồ côi `Hình 2` | tìm nguyên văn | ✅ có trong cả cây parse lẫn chunk |
| Ảnh phải trang 9 | đếm node figure trang 9 | ✅ 2 node — `Hình 3` và `[Hình không có chú thích]` |
| 41 chunk, 259/400 token | đo lại | ✅ khớp; **0/41** vi phạm char-span; **0** chunk chỉ-figure dưới 32 token |
| `adapter_version=5`, `section-id-v4`, `image_scale=2.0` | đọc manifest | ✅ đủ ba, `image_scale` nằm trong cấu hình parse |

**Không thoái lui ở ba đợt trước:** glyph lặp còn sót **0** · `trong đó:` không còn là section · cây section
**4 cấp** · `CHƯƠNG 1` có 4 section con · **5/5** chỗ stitch còn nguyên · `order_index` đơn điệu · 0 định danh
trùng · 0 chunk vượt trần.

## Ba chỗ làm rất tốt

### 1. Chunk trang 7 — cả giá trị của đợt gói trong một chunk

```
p7  40tok  types=['figure','text']  3 ảnh
    offset   0  'lychee-inspired spherical chair'
    offset  32  'a girl giving cat a gentle hug'
    offset  63  'a small hedgehog holding a piece of watermelon'
    + 'Hình 2: Tập các bức ảnh và các mô tả về chúng.'
```

Trước đợt này: **ba chunk rời 6–8 token** bằng tiếng Anh, và caption `Hình 2` **mất hẳn** khỏi hệ thống. Sau:
một chunk duy nhất, ba tham chiếu ảnh trỏ đúng offset, và caption chung của cụm nằm ngay cạnh cụm nó mô tả.

### 2. Thống kê caption phân biệt đúng hai loại

```json
"captions": { "total": 9, "recovered": 8, "orphaned": 1 }
```

Đây chính là con số mà nếu có từ hai vòng trước thì lỗi mất caption `Hình 2` **đã lộ ra ngay**, thay vì phải
chờ tới lúc soi tay. Và `structure_warnings` giờ có bốn lý do đọc lên là biết đi xem chỗ nào — trong đó
`orphan_caption` kèm nguyên văn.

### 3. ADR 0002 viết đúng thứ khó viết

Bốn quyết định ghi thành **một khối, nói rõ không áp dụng riêng lẻ**; điểm yếu ghi thẳng kèm **lý do vì sao
chấp nhận được**; năm phương án bị loại đều có lý do cụ thể. Đây là bản ADR tốt nhất trong repo.

`CONTEXT.md` cũng đã sửa đúng chỗ lệch: mục `Chunk` không còn nói nó là *một khối lá*.

---

## F27 🔴 — `.gitignore` che mất source code

**Nhân viên tự tìm ra khi viết báo cáo, và cố ý không sửa vì ngoài phạm vi.** Tôi xác nhận: lỗi thật.

```
$ git check-ignore -v src/doc2roadmap/infrastructure/artifacts/json_store.py
.gitignore:10:artifacts/    src/doc2roadmap/infrastructure/artifacts/json_store.py
```

Mẫu `artifacts/` **không có dấu gạch chéo đầu**, nên nó khớp **mọi** thư mục tên `artifacts` ở mọi độ sâu —
kể cả package hạ tầng. Đúng hai file bị che, và đó là **toàn bộ** package kho lưu trữ:

```
src/doc2roadmap/infrastructure/artifacts/__init__.py
src/doc2roadmap/infrastructure/artifacts/json_store.py
```

**Vì sao nghiêm trọng:** repo **chưa từng commit gì** — chỉ có một commit `Initial commit` với `README.md`. Lần
`git add` đầu tiên sẽ âm thầm bỏ qua package này. Code chạy bình thường ở máy local, test xanh, và người clone
về sẽ gặp `ModuleNotFoundError` ở tầng mà không ai nghĩ là thiếu.

**Sửa:** neo mẫu vào gốc — `/artifacts/` thay cho `artifacts/`. Một ký tự.

Cùng lúc nên rà lại các mẫu khác trong `.gitignore` theo cùng tiêu chí: mẫu nào có ý chỉ thư mục gốc thì phải
có gạch chéo đầu.

### Kết quả xử lý

Đã đổi đúng một pattern thành `/artifacts/`. `git check-ignore` hiện không còn khớp
`src/doc2roadmap/infrastructure/artifacts/json_store.py`, trong khi file dưới output root `artifacts/` vẫn bị
ignore. Các pattern còn lại không có bằng chứng che source nên được giữ nguyên, tránh mở rộng diff ngoài F27.

---

## Ghi nhận, không phải lỗi

**Hai chunk ảnh nhỏ (40 và 45 token) là hành vi đúng, không phải gộp sót.** Cả hai đều nằm cuối section và
đứng ngay sau một cước chú:

```
#8  footnote 18tok   <- không gộp được, buộc đóng nhóm
#9  3 ảnh    40tok   <- nội dung CUỐI của section 1.1.1
#10 section khác     <- gộp không vắt qua ranh giới section
```

Đây là hệ quả trực tiếp của quyết định giữ cước chú đứng riêng — **do tôi đề xuất ở Q3 phiên grill**, không
phải lựa chọn của người làm. Nếu về sau thấy khó chịu thì cân nhắc cho cước chú gộp được; nhưng 40 token vẫn
tốt hơn hẳn ba chunk 6–8 token trước đây.

**`'Ởgiai đoạn mô hình hoá'`** — lỗi mất dấu cách trong thân bài vẫn còn. Cùng loại F17, đã chốt ngoài phạm vi.

**`report/luong-xu-ly-tai-lieu.md` (1032 dòng) nằm ngoài mọi ticket.** Tôi rà mục 12 — các giới hạn nêu ở
12.2–12.10 đều đúng và không cái nào là khẳng định khống. Ba mục đáng để lead đọc: artifact nhiều file chưa
atomic ở cấp thư mục, chưa có khoá cho ingest đồng thời, và cache chunk kiểm tra muộn hơn cache parse.
