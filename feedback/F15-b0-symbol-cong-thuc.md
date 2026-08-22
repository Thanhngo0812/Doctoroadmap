# F34 — Review đợt Symbol và công thức

Vòng review 8 · 2026-08-22 · Phạm vi: [`task/b0-symbol-cong-thuc/`](../task/b0-symbol-cong-thuc/) 7/7 ticket

## Kết luận

**Tiêu chí mạnh nhất đợt khớp chính xác**, và lần này tôi kiểm được **trực tiếp** vì cả hai tài liệu còn giữ
artifact cũ lẫn mới — không phải tin một hash nào.

Một phát hiện nhỏ, và hai chỗ mô tả trong bản bàn giao thiếu chính xác.

## Tiêu chí mạnh nhất — so trực tiếp v1 với v2

Spec dự đoán: tài liệu một chỉ **hai nhóm chunk** được phép đổi định danh.

```
chunk        : 41 -> 41
id giữ nguyên: 39/41
id đổi       : 2
```

Và hai chunk đó đúng là hai nhóm được phép:

```
261tok ['text','formula','list_item'] refs_f=1   <- chunk chứa công thức khôi phục
 41tok ['figure']                     refs_i=2   <- chunk chứa dấu hiệu hình không chú thích
```

Không cần suy luận: **39/41 giữ nguyên, 2 đổi, và cả hai đổi vì đúng lý do đã dự đoán.**

## Kiểm chứng độc lập

| Khẳng định | Kết quả |
|---|---|
| Test | ✅ **97 passed**, exit 0 |
| Tài liệu một: 39/41 id giữ nguyên | ✅ so trực tiếp v1↔v2 |
| Tài liệu hai: 263 công thức, 51 bảng | ✅ 263 `formula_refs`, 51 `table_refs`, 5 `image_refs` |
| Section giảm | ✅ 67 → 42 — đúng 23 gạch đầu dòng cộng hai cụm nối |
| `Trong đó:` còn là section | ✅ **không** |
| Section bắt đầu bằng dấu liệt kê | ✅ **0** |
| **I9** trên tài liệu hai | ✅ **0/126** vi phạm |
| **I20** | ✅ 0 chunk vượt 6000 |
| `formula_refs` trỏ đúng | ✅ **0** lệch span · **0** ref không tìm thấy node |
| Định danh trùng | ✅ 0 chunk · 0 section |
| Bump | ✅ adapter 7, `section-id-v7`, mỗi thứ một lần |
| Ánh xạ Symbol | ✅ `symbol_characters_mapped: 2368` |

**Không thoái lui trên tài liệu một:** I9 0/41 · cây 4 cấp · 5/5 chỗ nối câu qua trang · glyph lặp 0 ·
9 tham chiếu hình · caption `Hình 2` còn nguyên.

## Chỗ làm tốt

**Bảng tra lấy từ nguồn chính thức của Unicode**, không gõ tay. Tôi đề nghị "bảng Adobe Symbol khoảng 190 mục"
và họ đi lấy đúng tệp chuẩn. Kết quả: 2368 ký tự được ánh xạ, và chỉ **2** ký tự còn sót trong toàn bộ văn bản
chunk.

**Cảnh báo phân loại rõ**: `rejected_heading_bullet` và `rejected_heading_repeated` là hai lý do riêng, nên
nhìn danh sách là biết luật nào đã bắt cái gì.

---

## F34 🟡 — Cảnh báo có kèm nguyên văn không bao giờ được khử trùng lặp

### Hiện tượng

Dựng 300 tiêu đề gạch đầu dòng **giống hệt nhau**:

```
300 heading '• gach dau dong'  ->  300 dòng cảnh báo
    rejected_heading_bullet: • gach dau dong
    rejected_heading_bullet: • gach dau dong
    … (300 lần)
```

### Cơ chế

Bản triển khai chia cảnh báo làm hai nhóm: loại **có kèm nguyên văn** thì **không bao giờ** gom, loại còn lại
thì khử trùng lặp kèm `×N`.

Test của họ dùng `empty_node: dropped formula` — loại không kèm nguyên văn — nên `×300` chạy đúng, và hai cảnh
báo `orphan_caption` khác nguyên văn được giữ riêng. **Đúng cả hai tiêu chí trong ticket tôi viết.**

### Chỗ hở

Khi nguyên văn **trùng nhau**, giữ cả 300 dòng không bảo toàn thêm thông tin nào — nó chỉ lặp lại một chuỗi.

Trên tài liệu thật, 24 tiêu đề gạch đầu dòng đều **khác nhau** nên danh sách ra 29 dòng, đọc được. Nhưng một
giáo trình có cùng một tiêu đề gạch đầu dòng lặp ở nhiều chương sẽ làm ngập lại đúng như trước.

### Đây là hai tiêu chí trong ticket của tôi mâu thuẫn nhau

Ticket `05` đòi *"gom cảnh báo cùng loại thành một dòng kèm số đếm"* **và** *"cảnh báo có kèm nguyên văn vẫn
giữ được nguyên văn của từng ca"*. Hai điều đó xung đột khi nguyên văn trùng nhau, và ticket không nói cách gỡ.

### Sửa

Khử trùng lặp theo **chuỗi đầy đủ**, không theo loại: hai cảnh báo khác nguyên văn thì giữ cả hai; ba trăm cảnh
báo **giống hệt nhau** thì một dòng kèm số đếm. Vừa giữ được nguyên văn vừa không ngập.

---

## Hai chỗ mô tả trong bản bàn giao thiếu chính xác

**"Còn hai glyph U+F0E7 không có Unicode tương đương."** Đo lại:

```
trong chunk text        : 2 ký tự, 1 mã   (U+F0E7)
trên mọi trường của node: 78 ký tự, 12 mã (U+F0E7, F0F7, F0E9, F0F9, F0EA, …)
```

Nên **12 mã phân biệt**, không phải một; con số 2 là số ký tự lọt vào văn bản chunk, còn 78 là tổng trên mọi
trường kể cả nội dung thô của công thức. Hai con số đo hai thứ khác nhau và bản bàn giao trộn chúng.

Và **chúng có Unicode tương đương**: đó là các mảnh ngoặc nhọn nhiều dòng, Unicode 3.2 đã thêm ở dải
`U+23A7–U+23AD`. Tệp ánh xạ chính thức của Adobe ra đời trước dải đó nên nó trỏ về vùng dùng riêng của Adobe —
vẫn là ký tự vùng dùng riêng. Đây là **giới hạn của bảng chuẩn**, không phải của Unicode.

Ảnh hưởng: 2 ký tự trong hơn 30 nghìn token, và **có cảnh báo** nên không im lặng. Không đáng sửa ngay; đáng
ghi cho đúng.

## Hai quan sát, không phải lỗi

**`formula_id` phân biệt: 225/263.** Ba mươi tám công thức dùng chung định danh với công thức khác vì **nội
dung thô của chúng giống hệt nhau** — đó là hành vi đúng của định danh băm theo nội dung, y như hai bức hình
giống hệt sẽ có cùng định danh. Với bước trích khái niệm sau này, hai công thức giống nhau là **một** thực thể
xuất hiện ở hai chỗ, và đó là cách hiểu đúng.

**`pages_reordered` nhảy từ 3 lên 9.** Công thức giờ là node có khung toạ độ nên **tham gia phép sắp lại thứ tự
đọc** — sáu trang nữa đổi thứ tự. Không ai dự đoán chuyện này, kể cả tôi. Nó hợp lý: công thức phải nằm đúng
chỗ trong mạch đọc. Nhưng nó có nghĩa là việc đưa công thức quay lại đã **đổi thứ tự các khối văn bản sẵn có**
trên sáu trang, và điều đó không được nêu trong ticket nào.

Bất biến vị trí ký tự và thứ tự chunk đều xanh, nên không có dấu hiệu hỏng. Ghi lại để nếu sau này thấy nội
dung lạc chỗ ở tài liệu nhiều công thức thì biết chỗ mà nhìn.
