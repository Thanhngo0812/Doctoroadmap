# F16–F18 🟡 — Bỏ node im lặng, heading dính chữ, và chunk quá vụn

Vòng review 2 · 2026-08-15 · Kèm **hai đính chính cho kết luận vòng 1 của chính tôi**

---

## F16 🟡 — 11 node bị bỏ, không chỗ nào ghi lại

Đếm trực tiếp trên Docling trước khi qua bộ lọc của adapter:

```
TỔNG ITEM DOCLING TRẢ VỀ: 170
  GIỮ                : 159   {section_header:27, text:85, picture:9, list_item:35, footnote:3}
  BỎ (lọc của ta)    :   9   {caption: 9}
  BỎ (text rỗng)     :   2   {document_index: 1, formula: 1}
```

Ba loại, ba mức độ:

| Node | Số | Đánh giá |
|---|---|---|
| `caption` | 9 | ✅ **Đúng.** Bị bỏ có chủ đích ở `docling_parser.py:86`, và quay lại qua `context_prefix` |
| `document_index` | 1 | ✅ **May.** Đây là trang MỤC LỤC. Docling trả nó dưới dạng object có `.text` rỗng nên bị loại ở dòng 114 — ta không muốn TOC thành chunk, nhưng ta **loại nó vì tình cờ**, không vì có luật |
| `formula` | 1 | ❌ **Mất nội dung.** Xem F15 |

Trang 2 (MỤC LỤC) chỉ có 2 item và cả hai đều không sinh chunk — đó là lý do section `MỤCLỤC` rỗng. Không mất
trang nào: cả 20/20 trang đều có node.

**Sửa:** manifest nên ghi lại số node bị bỏ theo nhãn.

```json
"parse_stats": {
  "items_total": 170,
  "nodes_kept": 159,
  "dropped": {"caption": 9, "document_index": 1, "formula": 1}
}
```

Rẻ, và lần sau nhìn một dòng là biết tài liệu nào bị nuốt mất thứ gì. Hiện tại muốn biết phải chạy lại Docling
144 giây.

---

## F17 🟡 — `MỤCLỤC`, `MỞĐẦU` — mất dấu cách trong tiêu đề

Đã truy nguồn: **lỗi của Docling, không phải normalization của ta.** Parse tree thô đã dính sẵn:

```
RAW ro=5 type=section_header: 'MỤCLỤC'
RAW ro=6 type=section_header: 'MỞĐẦU'
```

Nguyên nhân: hai tiêu đề này giãn chữ (letter-spacing) trong PDF; trình trích xuất mất ranh giới từ. Chỉ 2/27
heading dính, và cả hai đều là front matter.

**Không chặn gì**, nhưng ghi lại vì: tiêu đề đi vào `section_path` → vào `section_id` → và sẽ vào tiền tố ngữ
cảnh khi embed (§13.3). Một tiêu đề sai chính tả trong tiền tố làm giảm chất lượng vector của **mọi** chunk
dưới nó.

Không nên sửa bằng từ điển tách từ tiếng Việt ở pha này — quá nặng so với lợi ích. Ghi nhận, và nếu sau này
thấy nhiều tài liệu dính thì mới xử lý.

---

## F18 🟡 — 20% chunk quá ngắn để đứng một mình

```
n=132  tổng=9195 token  min=3  max=242  trung vị=62.5

     <8 :  1
   8-15 :  4
  16-31 : 22       ← 27 chunk (20%) dưới min_tokens=32
  32-63 : 40
 64-127 : 51
128-255 : 14
  >=256 :  0       ← không block nào chạm max_tokens=512
```

Chunk nhỏ nhất là 3 token: `'trong đó:'`. Rồi `'P P P : Độ chính xác của mô tả'` (10 token), rồi
`'PGS.TS. THÂN QUANG KHOÁT'` (12 token).

Thêm 15/132 chunk (11%) mở đầu bằng từ nối — `Trong đó`, `Do đó`, `Như vậy`, `Điều này`, `Hình` — nghĩa là
chúng **tham chiếu ngược** ra ngoài chính mình. Đọc một mình thì không hiểu.

### Đây là chỗ tôi khen sai ở vòng 1

Vòng trước tôi ghi `del min_tokens` vào mục **"làm tốt hơn yêu cầu"**, lập luận rằng luật "1 leaf block =
1 chunk" khiến `min_tokens` không có hành vi nào, nên `del` kèm chú thích là trung thực hơn viết một nhánh
`if` vô nghĩa.

Lập luận đó đúng **về code**. Nhưng nó đúng vì fixture tổng hợp của tôi toàn đoạn văn dài đều. Dữ liệu thật
nói khác: **1/5 chunk quá ngắn để làm một đơn vị truy hồi.** Với nhánh RAG, một vector 3 token là nhiễu thuần —
nó sẽ khớp với đủ thứ vì gần như không mang thông tin.

Nói thẳng: đó không phải quyết định tốt được ghi nhận, đó là **một lỗ hổng chưa lộ**. Tôi khen nó vì chỉ nhìn
code và fixture.

### Sửa: luật gộp khối ngắn liền kề

Gộp các block liên tiếp **trong cùng một section** cho tới khi đạt `min_tokens`, không vượt `max_tokens`,
không bao giờ gộp qua ranh giới section. `split_index` giữ nguyên vai trò; cần thêm cách ghi *chunk này gồm
mấy block gốc* để `char_span` vẫn truy ngược được.

Ba điều phải chốt **trước khi** code:

1. **Có gộp qua `block_type` khác nhau không?** Gộp một `list_item` với đoạn `text` phía trước thường đúng
   (câu dẫn + gạch đầu dòng là một ý). Gộp `footnote` vào thân bài thì sai.
2. **Chunk cuối section ngắn hơn ngưỡng thì sao?** Không còn gì để gộp cùng. Giữ nguyên, hay gộp ngược lên?
3. **`char_span` sau khi gộp.** Các block gốc không liền nhau tuyệt đối trong `normalized_full_text` — giữa
   chúng có `\n`. Gộp 3 block thì span là `[đầu block 1, cuối block 3)` và bao gồm cả các `\n` — I9 vẫn thoả
   nếu `text` cũng chứa các `\n` đó.

Và như F11: **đổi luật gộp làm đổi mọi `chunk_id`.** Phải nằm cùng một đợt với F11 + F15, bump
`algorithm_id` một lần duy nhất.

---

## Đính chính: Docling chậm gấp 4 lần con số tôi đưa ở vòng 1

`feedback/F5-hieu-nang-docling.md` ghi **~1.8 giây/trang** ở trạng thái ổn định, suy ra 500 trang ≈ 15 phút.

Đo trên tài liệu thật này:

| | Trang | Giây | Giây/trang |
|---|---:|---:|---:|
| PDF tổng hợp (bench vòng 1) | 50 | 91.5 | **1.83** |
| `nhap-mon-ml` (thật, có hình) | 20 | 144.6 | **7.23** |

**Gấp 3,9 lần.** Nguyên nhân nhìn thấy trong log:

```
[RapidOCR] main.py:132: The text detection result is empty
RapidOCR returned empty result!
```

OCR **có chạy** trên vùng ảnh. PDF bench của tôi sinh bằng script, không có ảnh nào, nên không có vùng nào để
OCR — bench đo một tài liệu dễ hơn thực tế rất nhiều.

**Suy lại cho giáo trình thật (có hình, có công thức):**

| Tài liệu | Vòng 1 (sai) | Đo lại |
|---|---|---|
| 100 trang | ~3 phút | **~12 phút** |
| 300 trang | ~9 phút | **~36 phút** |
| 500 trang | ~15 phút | **~60 phút** |

Điều này **không** đổi kết luận nào — nó chỉ làm quyết định đóng băng `parse_tree` (D14) đúng hơn nữa: chênh
lệch giữa parse và re-chunk giờ là bảy bậc độ lớn chứ không phải sáu. Nhưng con số 15 phút thì phải bỏ.

Bài học lặp lại y hệt F6 vòng trước: **số đo trên dữ liệu tự sinh không thay được số đo trên dữ liệu thật.**
Lần đó là hash trong tài liệu, lần này là benchmark. Cùng một sai lầm ở hai dạng.

---

## Những thứ chạy đúng trên dữ liệu thật

Không phải mọi thứ đều hỏng. Kiểm trên chính 132 chunk này:

| Bất biến | Kết quả |
|---|---|
| **I9** `full[start:end] == text` | ✅ **0/132 vi phạm** |
| `chunk_id` duy nhất | ✅ 0 trùng |
| `section_id` duy nhất | ✅ 0 trùng |
| **Bản vá F1** (nội dung trùng trong cùng section) | ✅ `'Có thể đưa nhu cầu này về bài toán học máy như sau:'` xuất hiện **2 lần trong cùng section**, nhận **2 `chunk_id` khác nhau** |
| Phủ trang | ✅ 20/20 trang đều có node |
| Tái dùng artifact | ✅ `parse_tree` v1 dùng lại, không parse lại |
| `max_tokens` | ✅ không block nào chạm 512, luật cắt câu không cần chạy (`split_index` toàn bộ = 0) |

Đáng chú ý: **F1 được xác nhận trên dữ liệu thật, không phải trên probe dựng tay.** Tài liệu này tình cờ có
đúng ca đó, và bản vá xử lý đúng.
