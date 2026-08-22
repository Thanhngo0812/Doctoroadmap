# F5–F6 — Lệch giữa tài liệu và code

> **Đã xử lý 2026-08-14:** chốt heading không thuộc `normalized_full_text` và sửa tài liệu để khớp offset,
> dấu nối `\n`, công thức ID cùng cách tuần tự hoá JSON của code.

Hai mục này **không phải lỗi lập trình**. Một cái là quyết định thiết kế chưa được ghi lại, một cái là lỗi
trong tài liệu **do tôi viết**.

---

## F5 🟠 — `normalized_full_text` loại bỏ heading

### Hiện trạng

```
Tài liệu:  [heading "Chương 2"] [đoạn "Preamble chương."] [heading "2.1"] [đoạn "Nội dung mục."]

normalized_full_text = 'Preamble chương.\nNội dung mục.'
                        ^ không có "Chương 2", không có "2.1"
```

Trong `chunk_document`, nhánh xử lý heading kết thúc bằng `continue` trước khi chạm vào `full_parts`, nên chỉ
khối không phải heading mới góp mặt vào chuỗi đầy đủ.

### Điều này **không** làm hỏng gì

Bất biến I9 vẫn đúng tuyệt đối — tôi đã kiểm:

```
full[chunk.char_start : chunk.char_end] == chunk.text     → True với mọi chunk
```

Cách làm hiện tại **tự nhất quán**: chunk chỉ sinh ra từ khối không phải heading, nên một chuỗi đầy đủ chỉ
gồm khối không phải heading là hợp lý.

### Nhưng nó lệch mô hình đã ghi

`doc/B0-phan-tich-luong.md` mô tả heading **có** chiếm chỗ trong chuỗi:

```
n0: [  0,  26)   "Chương 2: Mô hình ngôn ngữ"    ← tài liệu nói heading nằm ở đây
n1: [ 28, 143)   "Chương này trình bày…"
```

Và spec gốc gọi nó là *"normalized text"* của tài liệu, ngụ ý toàn văn.

**Hệ quả thực tế:** không tái dựng được tài liệu từ `normalized_full_text`. Khi cần hiện một chunk kèm bối
cảnh xung quanh — chức năng trích dẫn cho người học ở pha sau — tiêu đề mục sẽ không có ở đó, phải đi lấy
riêng từ bảng `sections`.

### Cần bạn chốt

| Phương án | Được | Mất |
|---|---|---|
| **Giữ nguyên** (loại heading) | Đơn giản, mọi span là span của chunk thật | Không tái dựng được toàn văn; phải sửa tài liệu |
| **Đưa heading vào** | Chuỗi đúng nghĩa toàn văn, trích dẫn có ngữ cảnh | Có vùng span không thuộc chunk nào; phải sửa code |

Tôi nghiêng về **giữ nguyên và sửa tài liệu** — chuỗi đầy đủ tồn tại để phục vụ `char_span` của chunk, mà
tiêu đề thì đã sống đầy đủ trong bảng `sections` với cả `section_path`. Nhưng đây là quyết định của bạn.

---

## F6 🟠 — Hash trong `doc/B0-phan-tich-luong.md` sai. Lỗi của tôi.

### Sai thế nào

Tài liệu ghi:

```
c(preamble chương)  →  c_835cc1499cf34245e24bde8e
```

và khẳng định *"Bạn chạy lại đúng công thức sẽ ra đúng những giá trị đó."*

Chạy thật trên code:

```
doc ghi : c_835cc1499cf34245e24bde8e
code ra : c_94b9bf52ab63e8b240684254     ← lệch
```

### Vì sao lệch

Tôi tính hash theo cách tài liệu mô tả — nối các thành phần bằng `|`, và nối `section_path` bằng `U+001F`:

```python
key = f"{doc_id}|{US.join(path)}|{text}|{split}|{occurrence}"
```

Bản triển khai dùng JSON:

```python
payload = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
```

### Cách của code **tốt hơn** cách tôi viết trong tài liệu

Tôi đã cảnh báo trong tài liệu rằng nối bằng `" > "` sẽ gây đụng độ, và đề xuất `U+001F` để tránh. Nhưng
`U+001F` chỉ là *rất khó xuất hiện* trong tiêu đề, không phải *không thể*. JSON thì **bất nhập nhằng theo cấu
trúc** — nó tự thoát ký tự và giữ nguyên ranh giới mảng, nên `["A","B"]` và `["A > B"]` không bao giờ băm
trùng nhau, với mọi nội dung đầu vào.

Nói cách khác, người viết code đã chọn phương án mạnh hơn phương án tôi đặc tả. **Không cần sửa code.**

### Mọi offset trong mục 5 của tài liệu cũng sai

Hai nguyên nhân cộng lại, và cái thứ hai nặng hơn nhiều:

- **Dấu phân cách:** tài liệu nói nối bằng `\n\n`, code dùng `\n`.
- **Heading bị loại hẳn** khỏi chuỗi đầy đủ — xem F5.

Nên đây không phải lệch một hai ký tự. Chạy thật trên chính ví dụ của tài liệu:

```
tài liệu ghi :  n1 (preamble chương) ở [ 28, 143)
thực tế      :  n1 (preamble chương) ở [  0, 115)
```

Đoạn preamble trở thành **thứ đầu tiên** trong chuỗi, vì heading `"Chương 2: Mô hình ngôn ngữ"` đứng trước nó
không góp mặt. Toàn bộ bảng offset ở mục 5 phải tính lại chứ không dịch được bằng một hằng số.

### Việc cần làm

Sửa `doc/B0-phan-tich-luong.md`: tính lại toàn bộ hash và offset **từ chính code**, mô tả đúng cách JSON hoá,
và chỉnh mục 5 theo kết luận của F5. Tôi làm việc này, không phải bạn.

Bài học rút ra cho lần sau: tài liệu **không nên** in ra giá trị băm cụ thể trừ khi nó được sinh từ chính code
và có test giữ cho nó khỏi trôi. Con số cụ thể trong tài liệu viết tay sẽ lệch ngay lần refactor đầu tiên.
