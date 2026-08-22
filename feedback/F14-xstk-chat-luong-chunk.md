# F30–F33 — Soi chất lượng chunk trên `xstk-ch3-1`

Vòng review 7 · 2026-08-21 · Dữ liệu: `artifacts/*/xstk-ch3-1/v1`
Nguồn: `xstk-ch3-1.pdf` — Xác suất thống kê, chương 3, **59 trang**

Đây là **tài liệu thứ hai** đi qua đường ống, và là tài liệu đầu tiên có bảng thật. Nó chất vấn những giả định
mà `nhap-mon-ml` không chạm tới.

## Kết luận một dòng

**Cơ chế chạy tốt, nội dung thì hỏng.** Mọi bất biến đều xanh, bảng hoạt động đúng lần đầu gặp dữ liệu thật,
phân bố token chuẩn. Nhưng **61% số chunk chứa ký tự hỏng mã**, và đó là toàn bộ chữ Hy Lạp của một giáo trình
thống kê.

## Quy mô

| | `nhap-mon-ml` | `xstk-ch3-1` |
|---|---:|---:|
| Trang | 20 | **59** |
| Item Docling | 170 | **992** |
| Node giữ lại | 155 | **724** |
| Section | 26 | **67** |
| Chunk | 41 | **132** |
| Bảng | **0** | **51** |
| Trung vị token | 259 | **261** |
| Token mỗi trang | 447 | 503 |
| **Công thức bị bỏ** (nội dung nằm ở `.orig`) | 1 | **264** |
| **Ký tự hỏng mã** | 0 | **653** |

## Phần chạy đúng — kiểm bằng đo, không đọc

| Bất biến | Kết quả |
|---|---|
| **I9** vị trí ký tự | ✅ **0/132** vi phạm |
| **I20** không vượt trần cứng | ✅ 0 chunk vượt 6000 |
| Định danh trùng | ✅ 0 chunk · 0 section |
| `oversize_reason` | ✅ **0** chunk phải gắn lý do |
| Cây section | ✅ 3 cấp, `section_path` dài 2–3 ở 131/132 chunk |
| Phân bố token | ✅ trung vị **261**, max **535**, 77/132 nằm trong dải 256–511 |

**Bảng hoạt động đúng ngay lần đầu gặp dữ liệu thật.** 51 bảng, 51 tham chiếu, markdown dựng chuẩn:

```
| x i | n i | n i x i | n i x i 2 |
| --- | --- | --- | --- |
| x 1 | n 1 | x 1 n 1 | x 1 2 n 1 |
```

Và **trần bảng phát huy tác dụng**: hai chunk 535 và 525 token — trên trần văn xuôi 512, dưới trần bảng 2048.
Với luật cũ chúng đã bị cắt đôi.

---

## F30 🔴 — Chữ Hy Lạp của thống kê bị hỏng mã

### Bằng chứng

**653 ký tự vùng dùng riêng trong 80/132 chunk — 61%.**

```
'ký hiệu là  và phương sai D(X) là phương sai tổng thể, ký hiệu là '
'X  N(  ;  2 )'
'Do  0 2 >  2 nên ta đưa ra quyết định: Bác bỏ H'
'| | n |  x |  x 2 |'
```

Mười ký tự hay gặp nhất:

| Mã | Số lần | Thật ra là |
|---|---:|---|
| `U+F061` | 149 | **α** |
| `U+F0AE` | 109 | **→** |
| `U+F06D` | 90 | **μ** |
| `U+F063` | 67 | **χ** |
| `U+F073` | 43 | **σ** |
| `U+F071` | 29 | **θ** |
| `U+F065` | 18 | **ε** |
| `U+F07E` | 8 | **∼** |
| `U+F0CE` | 8 | **∈** |
| `U+F0BB` | 8 | **≈** |

### Nguyên nhân

PDF nhúng chữ Hy Lạp bằng **font Symbol**, một font ánh xạ mã Latin sang ký tự Hy Lạp. Khi trích xuất, các mã
đó rơi vào **vùng dùng riêng** `U+F000–U+F0FF` thay vì được ánh xạ về Unicode thật. `U+F061` chính là
`0xF000 + 0x61`, tức chữ `a` trong bảng mã Symbol — và `a` trong Symbol là **α**.

### Đây là ánh xạ tất định, không phải đoán

Tôi giải mã theo bảng Adobe Symbol và đọc lại trong ngữ cảnh:

```
hiện tại : 'ký hiệu là  và phương sai D(X) … ký hiệu là '
giải mã  : 'ký hiệu là μ và phương sai D(X) … ký hiệu là σ'

hiện tại : 'X  N(  ;  2 )'
giải mã  : 'X ∼ N( μ ; σ 2 )'

hiện tại : '| | n |  x |  x 2 |'
giải mã  : '| | n | Σ x | Σ x 2 |'
```

Cả ba đọc lên **đúng hoàn hảo**. `X ∼ N(μ; σ²)` là ký hiệu trung tâm nhất của một giáo trình thống kê.

Bảng mã tôi gõ tay từ trí nhớ đã phủ **92%** trong một lần thử. Bảng Adobe Symbol đầy đủ — một chuẩn công bố
công khai, khoảng 190 mục — sẽ phủ gần như toàn bộ.

### Vì sao nghiêm trọng

Đây **không phải mất chữ, mà là hỏng chữ** — tệ hơn, vì không có dấu vết nào báo. Hệ quả:

- Truy vấn *"phương sai σ²"* **không khớp** với chunk chứa ``
- Bước trích khái niệm sẽ thấy ký tự rác thay vì tên khái niệm
- Tokenizer cắt PUA thành mảnh vô nghĩa, làm loãng vector
- **Bảng cũng dính** — `Σ` trong dòng tiêu đề cột bị hỏng

Với `nhap-mon-ml` con số này là **0**, nên bốn đợt vá vừa rồi không có cơ hội gặp nó.

### Sửa

Bảng tra Symbol → Unicode, đặt ở **adapter** cùng chỗ với việc gộp glyph lặp — cùng bản chất: hiện vật của
trích xuất PDF, không phải chuẩn hoá ngôn ngữ. Chỉ áp cho nguồn PDF.

Kèm **cảnh báo** khi còn ký tự PUA sau khi tra bảng, để lần sau gặp font khác thì biết ngay thay vì lại im lặng.

---

## F31 🔴 — 264 công thức bị bỏ vì **đọc nhầm thuộc tính**, và danh sách cảnh báo bị ngập

> **Cập nhật sau khi chạy Docling trực tiếp:** nội dung công thức **không hề mất** — nó nằm ở một thuộc tính
> khác mà adapter không đọc.
>
> ```
> .text khác rỗng : 0/264
> .orig khác rỗng : 263/264      <- NỘI DUNG NẰM Ở ĐÂY
>
> ví dụ:  .text = ''
>         .orig = 'X x1 x2 .  .  . xk ni n1 n2 .  .  . nk'
> ```
>
> Adapter đọc `.text`, thấy rỗng, bỏ node. Đây là **đọc nhầm trường**, cùng loại với mìn base64 ở đợt ảnh:
> gọi đúng API nhưng lấy sai thuộc tính. Nâng mức từ 🟠 lên 🔴 và chuyển việc sửa từ ô *"công lớn"* sang ô
> *"công nhỏ, giá trị lớn"*.
>
> Và nó **không phải chuyện riêng của công thức**: luật `nếu text rỗng thì bỏ` áp cho **mọi** loại node. Bất kỳ
> loại nào Docling để `.text` rỗng mà đặt chữ ở `.orig` đều bị bỏ im lặng. Ở `nhap-mon-ml` đúng một công thức
> rơi vào đó nên tôi xếp 🟡; ở đây là 264.



**264 trên 992 item Docling là `formula`, và tất cả bị bỏ** vì `.text` rỗng — 27% tài liệu.

Trong một giáo trình toán, công thức **là** nội dung. Và nội dung đó vẫn nằm nguyên trong `.orig`, chỉ là
adapter không đọc tới.

### Và cảnh báo bị ngập đúng nghĩa

`structure_warnings` có **264 dòng giống hệt nhau**:

```
"empty_node: dropped formula"
"empty_node: dropped formula"
… (264 lần)
"orphan_caption: Chú ý . Với mẫu hai chiều như sau:"     <- lọt giữa đống này
"empty_node: dropped formula"
"orphan_caption: Trong đó: m j = n 1j + n 2j + ..."      <- và cái này
```

Hai cảnh báo **chú thích mồ côi** — loại lỗi mà đợt trước ta bỏ công vá — nằm lẫn giữa 264 dòng lặp và **không
ai nhìn thấy**. Cơ chế cảnh báo tự đánh bại chính nó.

### Sửa

**Gom cảnh báo cùng loại thành một dòng kèm số đếm**: `empty_node: dropped formula ×264`. Một dòng, và hai
cảnh báo chú thích mồ côi lập tức nổi lên.

Và **đọc `.orig` khi `.text` rỗng** — một dòng ở adapter, khôi phục 263 node.

Luật `nếu text rỗng thì bỏ` nên đổi thành: thử `.text`, rồi `.orig`, chỉ bỏ khi **cả hai** rỗng. Nó áp cho
mọi loại node chứ không riêng công thức.

---

## F32 🟠 — Gạch đầu dòng trở thành section

**23 trên 67 section** thật ra là gạch đầu dòng:

```
L3  ' T ổng thể'
L3  ' Mẫu'
L3  ' Mẫu tổng quát và mẫu cụ thể'
L3  ' Tỉ lệ mẫu'
```

`U+F0B7` là **dấu chấm tròn** của font Symbol — tức đây là các gạch đầu dòng bị Docling gán nhãn tiêu đề.

Bộ lọc tiêu đề giả không bắt được vì luật hiện tại đòi *"ký tự đầu là chữ thường"* — mà ký tự đầu ở đây là dấu
chấm tròn hỏng mã, không phải chữ thường.

**23/60 window có section cha là một gạch đầu dòng.** Đường dẫn section của các chunk đó vì thế mang một mục
vô nghĩa.

### Và `Trong đó:` quay lại

```
L3  'Chú ý .'
L3  'Trong đó:'
```

Đúng cụm từ đã vá ở đợt hai, nhưng lần này **viết hoa** — `Trong đó:` chứ không phải `trong đó:`. Luật lọc
kiểm chữ thường ở ký tự đầu nên nó lọt.

### Sửa

Hai điều, cả hai đều nhỏ:

- Sau khi tra bảng Symbol (F30), tiêu đề bắt đầu bằng **dấu chấm tròn hoặc ký hiệu liệt kê** thì không phải
  tiêu đề — hạ xuống khối văn bản thường
- Luật *"kết thúc bằng dấu hai chấm và không đánh số"* nên **bỏ điều kiện chữ thường**, hoặc thêm một danh
  sách cụm nối thường gặp: `Trong đó`, `Chú ý`, `Ta có`, `Khi đó`, `Suy ra`

Điều thứ hai có rủi ro dương tính giả — `TẬP THỂ TÁC GIẢ:` ở tài liệu trước là tiêu đề thật và kết thúc bằng
dấu hai chấm. Nên dùng danh sách cụm nối thì an toàn hơn bỏ hẳn điều kiện.

---

## F33 🟡 — Khoảng trắng chèn giữa từ

```
' T ổng thể'     ->  phải là 'Tổng thể'
```

Cùng họ với lỗi `MỤCLỤC` ở tài liệu trước, nhưng ngược chiều: lần đó **mất** dấu cách, lần này **thừa**.

Tôi thử đếm bằng mẫu *chữ hoa + khoảng trắng + phần còn lại* và ra 272 chỗ — nhưng phần lớn là **dương tính
giả**: `X và`, `Y theo`, `X là` đều hợp lệ, vì `X` và `Y` là tên biến. **Con số thật tôi chưa đo được**, chỉ
xác nhận được vài ca bằng mắt.

Không chặn gì, và cùng lý do đã hoãn F17: cần từ điển tiếng Việt mới đếm đúng, mà chi phí đó lớn hơn lợi ích
hiện tại.

---

## Việc nên làm, xếp theo giá trị trên công sức

| Việc | Công | Giá trị |
|---|---|---|
| **Bảng tra Symbol → Unicode** | nhỏ — một bảng tra, ~190 mục, chuẩn công khai | **rất lớn** — sửa 61% số chunk |
| **Gom cảnh báo trùng lặp** | rất nhỏ — một dòng | lớn — làm hai cảnh báo bị chôn nổi lên |
| **Loại gạch đầu dòng khỏi tiêu đề** | nhỏ — sau khi có bảng Symbol | vừa — sửa 23/67 section |
| **Danh sách cụm nối cho lọc tiêu đề** | nhỏ | vừa |
| Cảnh báo khi còn PUA sau khi tra | rất nhỏ | vừa — chặn im lặng lần sau |
| **Đọc `.orig` khi `.text` rỗng** | rất nhỏ — một dòng | **rất lớn** — khôi phục 263 node bị bỏ |
