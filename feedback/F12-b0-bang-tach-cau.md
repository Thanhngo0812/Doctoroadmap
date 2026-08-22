# F28 — Review đợt bảng và tách câu toàn cầu

Vòng review 5 · 2026-08-21 · Phạm vi: [`task/b0-bang-tach-cau/`](../task/b0-bang-tach-cau/) 6/6 ticket + `note.md`

**Trạng thái:** ✅ Đã xử lý xong F28 ngày 2026-08-21. Ca chữ cái đơn là follow-up riêng trong chính feedback,
không phải tiêu chí đóng F28, và được ghi nhận vì còn đánh đổi ngữ nghĩa.

## Kết luận

**Mọi khẳng định đều đúng khi tôi đo lại, không thoái lui nào qua bốn đợt trước.** Tiêu chí nghiệm thu mạnh
nhất — tập định danh chunk không đổi — được xác nhận bằng **hai đường độc lập**.

Một phát hiện nhỏ, và **một đính chính cho chính tôi**.

## Kiểm chứng độc lập

| Khẳng định | Cách kiểm | Kết quả |
|---|---|---|
| 71 test xanh | chạy `pytest` | ✅ 71 passed, exit 0 |
| **Tập chunk ID không đổi** | băm tập 41 id, so với hash nhân viên khai | ✅ `726dce8b…d3d7a5` **khớp chính xác** |
| " " | **hai chunk ID tôi ghi lại từ trước đợt này** trong hội thoại | ✅ cả hai **vẫn còn**, cùng token count và số tham chiếu hình |
| `table_refs` ngoài khoá băm | tính lại id bằng công thức **không có** `table_refs` và `oversize_reason` | ✅ **41/41** khớp |
| Bộ tách câu toàn cầu | chạy lại **đúng 10 ca** trong spec | ✅ **10/10**, gồm ca hồi quy tiếng Việt |
| Vị trí trả về trỏ chuỗi gốc | cắt chuỗi tại span | ✅ đúng, masking giữ nguyên độ dài |
| Bảng DOCX có định danh | parse fixture thật | ✅ `table_id` 64 hex, `table_rows` còn nguyên 2 hàng |
| Tham chiếu bảng đúng vị trí | cắt chuỗi tại offset | ✅ offset 50 → `'\| Name \| Value \|'`, id ref == id node |
| **I18** mảnh bảng cùng định danh | dựng bảng 41 hàng, cắt theo hàng | ✅ 3 mảnh, **1** định danh phân biệt |
| **I17** cảnh báo khi bó tay | khối 600 từ không dấu kết câu | ✅ `oversize_reason='sentence_splitter_no_boundary'` **và** cảnh báo nêu rõ section |
| Hàng bảng quá dài | dựng hàng 700 từ | ✅ `oversize_reason='table_row_exceeds_max_tokens'`, **không** cảnh báo — đúng ngoại lệ đã biết |
| Cái bẫy `from_dict` | nạp artifact chunk kiểu cũ | ✅ `ValueError` **tường minh**: *"schema cũ có oversize=true nhưng không lưu lý do; hãy ingest lại"* |
| Phiên bản | đọc manifest | ✅ `adapter_version=6`, `section-id-v5`, bump đúng một lần |

**Không thoái lui:** char-span **0/41** vi phạm · glyph lặp 0 · cây section 4 cấp · 5/5 chỗ nối câu qua trang ·
base64 0 · tham chiếu hình 9/9 resolve, 0 lệch span · 0 id trùng.

## Ba chỗ làm rất tốt

**1. Cái bẫy `from_dict` được xử lý đúng cách.** Ticket yêu cầu *"hoặc chuyển đổi được, hoặc báo lỗi tường
minh"*. Họ chọn báo lỗi, và thông báo nói luôn **phải làm gì**: `hãy ingest lại`. Không phải `TypeError` khó
hiểu như lần trước.

**2. `I17` không chỉ bật cờ mà còn nêu vị trí.** Cảnh báo là `sentence_splitter_no_boundary: section 1` — có
section để đi tìm, đúng tinh thần *"lý do đọc lên là hiểu phải đi xem chỗ nào"*.

**3. Phân biệt đúng hai loại vượt trần.** Hàng bảng quá dài thì ghi lý do nhưng **không** cảnh báo, vì đó là
ngoại lệ đã biết; bộ tách bó tay thì cảnh báo, vì đó là chữ viết chưa hỗ trợ. Hai thứ trông giống nhau về mặt
số liệu nhưng khác hẳn về ý nghĩa, và họ tách đúng.

---

## Đính chính: tôi sai về `ponytail` ở vòng 3

Vòng 3 tôi viết:

> Marker này xuất hiện **đúng một lần** trong toàn repo và không thuộc quy ước nào (`TODO`, `FIXME`, `NOTE`,
> `HACK`). Một dấu mà không ai grep thì bằng không có dấu. Đổi sang `# NOTE:` là xong.

**Sai.** `ponytail` là quy ước thật của dự án — có hẳn một họ skill trong `.agents/skills/`: `ponytail`,
`ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`, `ponytail-review`. Nó đánh dấu chỗ đã cân
nhắc và **cố ý chọn phương án tối giản**, kèm điều kiện để xem lại.

Tôi grep trong `src/` và `tests/` rồi kết luận, mà không grep `.agents/`. Lời khuyên đổi sang `NOTE:` sẽ **xoá
mất thông tin**, không phải làm rõ nó.

Mục 8 của `note.md` liệt kê năm quyết định tối giản theo quy ước này, và cả năm đều đúng — đặc biệt *"không
giữ song song `oversize` và `oversize_reason`, tránh hai nguồn sự thật có thể lệch nhau"*, đúng điều tôi hỏi ở
lúc chia ticket.

---

## F28 🟡 — Bộ tách câu chưa dùng luật mà bộ nối câu đã dùng

### Hiện tượng

Bộ tách cắt tại dấu kết câu **kể cả khi từ ngay sau bắt đầu bằng chữ thường**:

```
'Anh ấy do dự… rồi quyết định làm. Xong.'
  -> 'Anh ấy do dự…' / 'rồi quyết định làm.' / 'Xong.'          3 câu, đúng phải là 2

'U.S.A. là viết tắt. Ai cũng biết.'
  -> 'U.S.A.' / 'là viết tắt.' / 'Ai cũng biết.'                 3 câu, đúng phải là 2

'Anh nói "tuyệt!" rồi đi. Hết chuyện.'
  -> 'Anh nói "tuyệt!"' / 'rồi đi.' / 'Hết chuyện.'              3 câu, đúng phải là 2
```

Một gốc chung: **chữ thường ngay sau dấu kết câu gần như không bao giờ là ranh giới câu thật** trong chữ Latin
và tiếng Việt.

### Chỗ đáng nói: dự án **đã có** luật này, ở chỗ khác

Bộ nối câu qua ranh giới trang dùng đúng nguyên tắc đó và dùng đúng — nó chỉ nối khi *"ký tự đầu tiên của node
sau là chữ thường"*. Hai thành phần giải cùng một bài toán con, một cái biết luật, một cái không.

### Mức độ: thấp

Đo trên văn bản thật, chạy splitter **trong từng block** như cách dùng thật:

```
18 block có dấu chấm lửng  ·  1 chỗ cắt nhầm
```

Ca duy nhất: `(thông qua các quan sát bằng mắt, tai, ...)` bị cắt khỏi `từ bên ngoài, rồi thực hiện…`.

Và bộ tách **chưa từng chạy** trên corpus này — mọi chunk có chỉ số mảnh bằng không. Nên tác động hôm nay bằng
không; đây là chuyện của tài liệu tiếp theo.

*(Lần đo đầu tôi chạy splitter trên toàn văn có `\n` giữa các block và ra 6 ca. Năm trong đó là ranh giới
block, không phải lỗi. Con số đúng là 1.)*

### Kèm theo: chữ cái đơn

```
'Định nghĩa T. P. E. rất nổi tiếng.'
  -> 'Định nghĩa T.' / 'P. E.' / 'rất nổi tiếng.'
```

Ảnh hưởng tới tên viết tắt (`J. Smith`, `A. Einstein`) và ký hiệu toán có dấu chấm. Cùng mức độ thấp, và luật
chữ-thường ở trên **không** xử lý được ca này — cần một luật riêng cho chữ cái đơn viết hoa.

### Đề nghị

Không gấp. Khi làm thì thêm một điều kiện: **không cắt nếu ký tự có nghĩa đầu tiên sau dấu là chữ thường**.
Một luật, xử lý được cả ba ca đầu, và nó nhất quán với thứ bộ nối câu đã làm.

Ca chữ cái đơn thì cân nhắc riêng — nó có đánh đổi thật, vì `Xem chương T.` cũng có thể là hết câu.

### Kết quả xử lý

`UnicodeSentenceSplitter` giờ bỏ qua boundary nếu ký tự chữ-số có nghĩa tiếp theo là chữ thường. Ba ca review
`do dự… rồi`, `U.S.A. là` và `"tuyệt!" rồi` đều được khóa bằng regression test và trả đúng hai câu.
Toàn bộ suite sau xử lý: **85 passed, 5 dependency warnings**.

Không thêm luật cho chữ cái viết hoa đơn (`J. Smith`, `T. P. E.`): feedback cũng xác định đây là luật riêng có
đánh đổi thật, còn task hiện tại không đưa ra tiêu chí phân biệt với câu kết thúc như `Xem chương T.`. Tự đoán
thêm heuristic ở đây sẽ trái nguyên tắc thay đổi tối thiểu và có thể tạo regression khó thấy.
