# F22–F26 — Review `note.md`: sửa reading order và stitch ranh giới trang

Vòng review 3 · 2026-08-15 · Phạm vi: [`task/b0-va-cau-truc/note.md`](../task/b0-va-cau-truc/note.md)
Dữ liệu: `artifacts/*/nhap-mon-ml/v2`

Đây là thay đổi **ngoài phạm vi mọi ticket**, tự phát hiện tự sửa, và nó đụng vào `reading_order` — thứ mà
việc gán section đứng lên trên. Tôi kiểm bằng cách chạy lại, không đọc dấu tích.

---

## Phần đúng — đã kiểm chứng độc lập

| Khẳng định trong note | Cách tôi kiểm | Kết quả |
|---|---|---|
| 42 test xanh | chạy lại `pytest` | ✅ 42 dot, exit 0 |
| `153 + 12 + 5 = 170` | đếm trên tree v2 | ✅ khớp **chính xác** |
| I9 giữ nguyên | `full[start:end] == text` trên 49 chunk | ✅ **0/49** vi phạm |
| `order_index` đơn điệu | so với `sorted()` | ✅ đúng |
| 5 chỗ stitch | tìm cụm từ sau nối trong chunk | ✅ đủ 5, đọc lên **thành câu tự nhiên** |
| Không còn mảnh mồ côi | tìm node mở đầu `thập trong quá khứ` | ✅ 0 |
| Glyph lặp ≥3 lần | quét lại toàn bộ chunk | ✅ 0 còn sót |
| Figure/footnote còn nguyên | đếm theo loại | ✅ 8 figure, 3 footnote |
| `adapter_version=3`, `algorithm_id` giữ `v3` | đọc manifest | ✅ đúng, và lý do nêu trong note là chuẩn |

**Sắp lại trang 7 là đúng về mặt ngữ nghĩa.** Tôi đối chiếu bbox với nội dung:

```
        top      v1 (Docling)                    v2 (sau sửa)
      786.7   figure lychee                    figure lychee
      310.8   'trong đó:'          ────>       figure girl-cat
      280.0   list x là...                     figure hedgehog
      202.3   list y có thể...                 heading 1.1.2
      150.6   'Trong thực tế...'               'Con người có khả năng học...'
      786.1   figure girl-cat                  'Như vậy, bản chất... tìm một hàm'
      609.9   heading 1.1.2                    'trong đó:'
      576.6   'Con người có khả năng...'       list x là...
      417.0   'Như vậy, bản chất...'           list y có thể...
      780.6   figure hedgehog                  'Trong thực tế...'
```

v1 nhảy cóc giữa các vị trí dọc — hỏng rõ ràng. v2 giảm dần đều theo `top` và **đọc lên đúng mạch**: công
thức nằm trong 1.1.2, rồi `trong đó:` giải thích ký hiệu của chính công thức đó. Trước đây `trong đó:` bị tách
khỏi công thức nó giải thích.

**Chỉ 1 chunk đổi section**, và đổi theo hướng đúng: figure `'a small hedgehog…'` chuyển từ 1.1.2 về 1.1.1.
Ba ảnh DALL·E của Hình 2 giờ nằm cùng nhau trong 1.1.1 — đúng chỗ ví dụ chú thích ảnh được nêu.

**Và bằng chứng mạnh nhất cho tính an toàn:** tôi chạy `_is_single_column` trên cả 20 trang — **20/20 đều đủ
điều kiện sắp lại**, nhưng chỉ **1 trang** thật sự đổi thứ tự. Nghĩa là phép sắp lại **đồng ý với Docling ở
19/20 trang**. Nó không phải một phép sort liều.

Quyết định sửa ở adapter thay vì ở chunker (note §2) cũng đúng: sửa ở chunker sẽ tạo chunk có `char_span`
không liên tục.

---

## F22 🔴 — Regex gộp glyph **xoá mất chữ** khi đứng sau từ tiếng Việt

### Bằng chứng

```
'các c c c là nhãn lớp'   →  'các là nhãn lớp'      ← biến c BIẾN MẤT
'học c c c trong tập'     →  'học trong tập'         ← biến c BIẾN MẤT
'mỗi lớp c c c được gán'  →  'mỗi lớp c được gán'    ← đúng
```

Hai ca đầu **không phải gộp sai — là mất hẳn nội dung.**

### Nguyên nhân

```
(?<![A-Za-z])([A-Za-z])(?: \1){2,}
 ^^^^^^^^^^^ chỉ chặn chữ cái ASCII
```

`á`, `ọ`, `ư` **không thuộc** `[A-Za-z]`, nên lookbehind không chặn. Với `'các c c c'`:

1. Match bắt đầu tại chữ `c` **cuối từ "các"** (đứng trước nó là `á` — lookbehind cho qua)
2. Nuốt tiếp ` c c c`, tổng match là `"c c c c"`
3. Thay bằng `"c"` → `"cá"` + `"c"` = `"các"`

Ba ký hiệu toán đứng riêng bị nuốt sạch, và không có dấu vết nào để lần ra.

### Vì sao ticket 07 không bắt được

Tiêu chí nghiệm thu cuối của ticket 07 viết đúng:

> Nếu tìm được ca dương tính giả nào khác **trong tài liệu thật**, dừng và báo.

Họ tìm, không thấy, và báo đúng sự thật — tài liệu này **không** chứa cặp kề nhau đó. Vấn đề là tiêu chí bị
giới hạn ở *một tài liệu*. Đây là lỗi của tôi khi viết ticket, không phải của người làm.

### Vì sao đây không phải ca hiếm

Chữ cái kết thúc từ tiếng Việt trùng với ký hiệu toán thường gặp:

| Từ rất phổ biến | Kết thúc bằng | Ký hiệu toán trùng |
|---|---|---|
| các · học · việc · được · trước · nước | `c` | `c` — nhãn lớp |
| lần · tần · dần · gần · vẫn | `n` | `n` — cỡ mẫu |
| hàm · nhóm · điểm · tham | `m` | `m` — số chiều |
| trong · dùng · cũng · rằng | `g` | `g` — hàm |
| lớp · tập · bậc | `p` | `p` — xác suất |

`"lần n n n"`, `"hàm m m m"`, `"xác suất p p p"` — đều là câu tiếng Việt bình thường trong giáo trình ML.

### Sửa

Đổi lookbehind sang "không đứng sau **chữ cái bất kỳ**", không riêng ASCII:

```
(?<![^\W\d_])([A-Za-z])(?: \1){2,}
```

Và thêm ba ca vào bộ test hiện có: `'các c c c'`, `'học c c c'`, `'lần n n n'` — cả ba phải giữ nguyên ký
hiệu, chỉ gộp ba lần lặp thành một.

---

## F23 🔴 — Guard đa cột **chưa bao giờ chạy nhánh chặn**; fixture không kiểm được nó

### Bằng chứng

```
two-column.pdf  →  Docling parse  →  1 node

p1: 1 node   _is_single_column = True    ← guard KHÔNG chặn
ro=0 text 'Left column first. Left column second. Left ...'
```

Docling **gộp cả trang hai cột thành một node text duy nhất**. Một node thì không thể "tách rời theo chiều
ngang" với node nào cả, nên hàm trả `True` một cách tầm thường.

Bài test tích hợp vẫn xanh — nhưng nó xanh vì chuỗi text của node duy nhất tình cờ chứa các cụm từ đúng thứ
tự, **không phải vì guard hoạt động**.

`note.md` §2.1 viết:

> Fixture `two-column.pdf` bảo vệ nhánh này.

Khẳng định này **không đúng**. Fixture không chạm được tới nhánh đó.

### Và không chỗ nào khác chạm tới

- 20/20 trang của `nhap-mon-ml` → `True`
- `two-column.pdf` → `True`
- `smoke.pdf` → một cột, `True`

`_is_single_column` **chưa từng trả `False`** trong toàn bộ bộ test lẫn trên mọi dữ liệu thật. Toàn bộ cơ chế
an toàn mà thiết kế này dựa vào là **nhánh chết chưa từng thực thi**.

### Bản thân logic thì đúng

Tôi dựng tay hai node text tách rời hẳn theo chiều ngang:

```
trai  [70 … 280]     phai [320 … 530]
_is_single_column  ->  False     ✅
```

Nên đây **không phải lỗi logic — là lỗ hổng phủ test**. Cùng một dạng với F4 vòng một: một bài test hứa nhiều
hơn thứ nó làm, và người đọc sau sẽ tin rằng nhánh đó đã được canh.

### Sửa

Không sửa được bằng fixture PDF — Docling quyết định gộp hay không, ta không điều khiển được. Phải **unit
test thẳng `_is_single_column`** bằng node dựng tay:

- hai khối text tách rời ngang → `False`, và trang **giữ nguyên** thứ tự Docling
- một khối text cộng một figure bên cạnh → `True` (figure không tham gia nhận diện cột)
- có node thiếu `bbox` → `False`

Và sửa câu khẳng định trong `note.md` §2.1 cho khớp sự thật.

---

## F24 🟠 — Phép sắp không có dung sai dọc; thứ tự trong một hàng là **may**

### Bằng chứng

Khoá sắp xếp là `(-top, left, reading_order)`. Chênh lệch `top` dù nhỏ đến đâu cũng **áp đảo**, nên `left`
không bao giờ được hỏi tới với các khối nằm cùng một hàng.

Ba ảnh của Hình 2 trên trang 7 là **ba ảnh xếp ngang**, x không chồng nhau:

```
l= 78.2  t=786.7  r=209.9  b=674.6   cao=112.0
l=229.5  t=786.1  r=403.5  b=682.8   cao=103.2
l=441.5  t=780.6  r=536.1  b=688.4   cao= 92.2
```

Chênh `top` tổng cộng **6,1 point** trên các ảnh cao 92–112 point — tức khoảng 5% chiều cao. Chúng chồng nhau
theo chiều dọc gần như hoàn toàn. Rõ ràng là **một hàng**.

Kết quả hiện tại đúng — nhưng chỉ vì thứ tự `top` **tình cờ** trùng thứ tự `left`. Tôi nâng ảnh giữa lên 2
point rồi chạy lại chính hàm đó:

```
thực tế       ->  ['A-trai', 'B-giua', 'C-phai']    đúng
giữa cao +2pt ->  ['B-giua', 'A-trai', 'C-phai']    SAI
```

Hai point. Ảnh cao khác nhau vài point là chuyện thường của một hàng ảnh căn giữa hoặc căn đáy.

### Sửa

Gom thành **hàng** trước, rồi sắp trong hàng theo `left`. Tiêu chí gom đơn giản và đủ dùng: hai khối thuộc
cùng hàng nếu khoảng dọc của chúng chồng nhau quá một nửa chiều cao khối thấp hơn.

Kèm test: ba khối cùng hàng, `top` lệch vài point theo thứ tự **ngược** với `left` ⇒ kết quả vẫn phải theo
`left`.

---

## F25 🟡 — Chunk khai thiếu trang · **hoãn theo quyết định 2026-08-16**

`Chunk.page` là một số nguyên duy nhất, lấy từ block đầu của nhóm. Có **hai** nguyên nhân độc lập, không phải
một như note §2.3 nêu:

1. **Gộp block (ticket 09)** — nhóm gộp tới đích 256 token có thể vắt qua ranh giới trang. Có trước cả note.
2. **Stitch (note.md)** — một node giờ chứa text từ hai trang, giữ `page` của mảnh đầu.

### Số thật là 9, không phải 5

Note khai 5 — đó chỉ là nguyên nhân thứ hai. Tôi đếm lại cả hai trên artifact v3:

```
khai page= 3  thật ra trải [3, 4]   299tok   ← gộp
khai page= 7  thật ra trải [7, 8]   257tok   ← gộp
khai page= 7  thật ra trải [7, 8]   269tok   ← stitch
khai page= 9  thật ra trải [9,10]   277tok   ← stitch
khai page=11  thật ra trải [11,12]  226tok   ← stitch
khai page=12  thật ra trải [12,13]  268tok   ← stitch
khai page=14  thật ra trải [14,15]  298tok   ← gộp
khai page=17  thật ra trải [17,18]  318tok   ← gộp
khai page=19  thật ra trải [19,20]  399tok   ← stitch

TỔNG: 9/49 = 18% chunk khai thiếu trang
```

Con số 5 trong bản feedback đầu của tôi cũng sai — tôi lấy theo note và cho rằng chỉ stitch gây ra.

Ca nặng nhất: chunk khai **trang 19**, dài 399 token, chỗ nối ở 39% chiều dài — **61% nội dung nằm ở trang 20**.

### Mức độ — đo lại, nhẹ hơn tôi mô tả ban đầu

`page` **không bao giờ sai** với vai trò *trang bắt đầu*: nó luôn là trang của block đầu nhóm, đúng 49/49.
Đây là vấn đề **độ chính xác**, không phải đúng/sai, và sai số tối đa là **một trang**.

| Kiểm | Kết quả |
|---|---|
| Trang có nội dung nhưng không chunk nào khai | **0** — đủ 19/19 trang được khai (trang 2 là mục lục, vốn rỗng) |
| Tỉ lệ ký tự nằm đúng trang được khai | **87,4%** |
| Tỉ lệ nằm ở trang khác | 12,6% |

Ba cách dùng, chỉ một cách hỏng:

1. *"Chunk này bắt đầu ở trang mấy"* → **luôn đúng**.
2. *"Mở trang N để đọc chunk này"* → người đọc lật sang trang sau là thấy tiếp, như đọc sách bình thường.
   **Gần như không hỏng.**
3. *"Khái niệm X được dạy ở trang mấy"* → **lệch 1 trang** khi câu định nghĩa nằm ở phần đuôi tràn trang.
   Đây là ca duy nhất hỏng thật.

Bản feedback đầu của tôi mô tả ca 2 như một thất bại (*"mở trang 19 và không thấy khái niệm ở đâu"*). Nói quá —
lật trang là thấy.

### Quyết định: hoãn

Chốt ngày 2026-08-16: **chưa làm.** Lý do đúng là *chưa consumer nào đọc `page`* — B0.5 embed `text`, T1 đọc
window, bước M dùng `chunk_id`. `page` hiện chỉ để hiển thị.

Khi quay lại, ba điều cần biết:

- **Số là 9/49, không phải 5.** Và phải sửa **cả hai** nguyên nhân, không chỉ stitch.
- **`chunk_id` không đổi** — `page` không nằm trong khoá băm `(doc_id, section_id, text, split_index,
  occurrence)`. Không phải re-index gì cả.
- **Chi phí tăng tuyến tính theo số tài liệu đã ingest.** Sửa đủ đòi `DocumentNode` mang khoảng trang ⇒ bump
  `adapter_version` ⇒ parse lại. Hiện là ~150 giây cho một tài liệu; với 100 giáo trình đã ingest thì là
  khoảng 4 tiếng cho cùng bản sửa.

## F26 🟡 — `_is_single_column` quét toàn bộ cặp

Với 12 node một trang là 66 cặp — không đáng gì. Nhưng độ phức tạp là bình phương theo số node mỗi trang, và
tài liệu dày đặc hơn (slide, sách bài tập) có thể lên vài trăm node một trang. Chỉ cần sắp theo `left` rồi
quét một lượt là đủ. Ghi nhận, chưa cần làm.

---

## Kết luận

**Bản sửa này đúng hướng và làm cẩn thận.** Nó tự phát hiện một lỗi thật mà không ticket nào nêu, chọn đúng
tầng để sửa, kèm lý do vì sao không sửa ở chunker, và giữ nguyên mọi bất biến. Phần đối chiếu số liệu trong
note khớp chính xác với những gì tôi đo lại.

Nhưng hai chỗ phải sửa trước khi ingest tài liệu thứ hai:

- **F22** — regex xoá mất ký hiệu toán khi nó đứng sau từ tiếng Việt kết thúc bằng cùng chữ cái. Sửa lookbehind.
- **F23** — guard đa cột chưa từng chạy nhánh chặn. Không sửa được bằng fixture PDF; phải unit test thẳng.

F22 nguy hiểm hơn vì nó **mất dữ liệu im lặng**: không có cảnh báo, không có dấu vết, và chỉ lộ ra khi có
người đọc lại đúng đoạn đó.
