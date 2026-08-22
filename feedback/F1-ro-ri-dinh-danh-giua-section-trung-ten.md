# F1 🔴 — Rò rỉ định danh giữa hai section trùng tên

> **Đã xử lý 2026-08-14:** chunk dùng `parent_section_id` và occurrence được đếm riêng trong từng section;
> regression test giữ nguyên ID của section anh em khi sửa section đứng trước.

**Mức:** Cao — phá đúng lời hứa mà [ADR 0001](../doc/adr/0001-dinh-danh-tat-dinh.md) tồn tại để giữ.
**Trạng thái:** đã xác minh bằng cách chạy, không phải suy đoán.

## Hiện tượng

Sửa nội dung trong section `"Bài tập"` của **chương 1** làm **đổi `chunk_id`** của một chunk nằm trong section
`"Bài tập"` của **chương 2** — dù chunk đó không bị sửa một chữ nào, cũng không đổi section cha.

## Tái hiện

```python
# Tài liệu: hai section anh em TRÙNG TÊN "Bài tập"
def build(them_doan_vao_chuong_1: bool):
    nodes = []
    add("section_header", "Bài tập", level=1)      # ← "Bài tập" thứ nhất
    add("paragraph",      "Làm lại ví dụ.")
    if them_doan_vao_chuong_1:
        add("paragraph",  "Làm lại ví dụ.")        # ← chỉ THÊM ở chương 1
    add("section_header", "Bài tập", level=1)      # ← "Bài tập" thứ hai
    add("paragraph",      "Làm lại ví dụ.")        # ← chunk ta quan tâm
    return nodes
```

Kết quả thật:

```
Chunk cuối (nằm trong "Bài tập" THỨ HAI), nội dung 'Làm lại ví dụ.'
  trước  : c_7837f86c4f4fac63231fa0f8
  sau    : c_0e735fa5f235829f38d91ce0     ← ĐỔI
```

## Nguyên nhân

Hai chỗ cộng lại mới thành lỗi.

**Thứ nhất — `section_path` không phải khoá duy nhất.** Hai section anh em trùng tên có **đường dẫn giống hệt
nhau**; chúng chỉ được phân biệt bởi `occurrence` bên trong `section_id`:

```
section 'Bài tập'  path=['Bài tập']  id=s_ccd9da8d80062aca89e2af0d
section 'Bài tập'  path=['Bài tập']  id=s_e774b1bbfbd64e1d13450e47
        └─ trùng nhau ─┘             └─ khác nhau, nhờ occurrence ─┘
```

**Thứ hai — `chunk_id` băm `section_path` chứ không băm `section_id`**, nên bộ đếm `occurrence` của chunk cũng
phải khoá theo `section_path`:

```python
# src/doc2roadmap/domain/chunking.py
occurrence_key = (tuple(owner.section_path), chunk_text, split_index)
                       ^^^^^^^^^^^^^^^^^^^ dùng chung cho MỌI section trùng tên
occurrence = chunk_occurrences[occurrence_key]
chunk_occurrences[occurrence_key] += 1
```

Hệ quả: mọi section trùng tên **dùng chung một bộ đếm**. Chunk `"Làm lại ví dụ."` trong "Bài tập" thứ hai nhận
`occurrence = 1` khi chương 1 có một bản, và `occurrence = 2` khi chương 1 có hai bản. Định danh của nó phụ
thuộc vào **số lần đoạn văn đó xuất hiện ở một section khác** — tức là phụ thuộc vào vị trí, đúng thứ ADR 0001
đặt ra để loại bỏ.

## Vì sao đây không phải ca hiếm

Giáo trình tiếng Việt lặp lại tiêu đề ở mỗi chương gần như là quy tắc:

> `Bài tập` · `Tóm tắt` · `Tóm tắt chương` · `Kết luận` · `Câu hỏi ôn tập` · `Tài liệu tham khảo`

Và nội dung lặp trong các mục đó cũng rất thường: `"Xem lại phần trước."`, `"Làm lại ví dụ."`,
`"Trả lời các câu hỏi sau."`

Một cuốn 12 chương với mục `Bài tập` mỗi chương là **12 section chia nhau một bộ đếm**. Sửa bài tập chương 3
làm gãy định danh ở chương 4 tới 12.

## Vì sao 21 test đều xanh

Không fixture nào có hai section anh em trùng tên. Bốn fixture hiện có — cây chuẩn §4.5, heading nhảy cấp,
tài liệu phẳng, bảng kèm caption — đều có tiêu đề phân biệt. Bất biến I11 vẫn đúng trong phạm vi chúng kiểm.

Đây không phải lỗi của người viết test: ticket 02 và 03 **không** liệt kê ca này. Nó lọt qua khe giữa hai tài
liệu — spec gốc không nhắc, spec mới cũng không.

## Đề xuất sửa

**Băm `section_id` thay vì `section_path`.** `section_id` đã mang sẵn `occurrence` phân biệt các section trùng
tên, nên nó là khoá duy nhất thật sự:

```python
# chunk_id: dùng owner.section_id thay cho owner.section_path
_chunk_id(doc_id, owner.section_id, chunk_text, split_index, occurrence)

# và bộ đếm khoá theo section_id — mỗi section một bộ đếm riêng
occurrence_key = (owner.section_id, chunk_text, split_index)
```

Sau khi sửa, `occurrence` chỉ còn làm đúng việc nó sinh ra để làm: phân biệt các đoạn văn **trùng nội dung
trong cùng một section**.

**Đánh đổi cần biết:** `section_id` được băm từ `section_path`, nên đổi tên tiêu đề vẫn làm đổi định danh mọi
chunk bên dưới — đúng như ADR 0001 đã ghi nhận và chấp nhận. Bản sửa này **không** làm điểm yếu đó nặng thêm;
nó chỉ bịt đường rò rỉ **ngang** giữa các section khác nhau.

**Sửa bây giờ là rẻ nhất.** Chưa có artifact nào tồn tại, chưa bước nào phía sau tham chiếu `chunk_id`. Để tới
khi T1 đã ghi bằng chứng thì mọi tham chiếu đã lưu sẽ gãy.

## Test cần thêm

```
Cho một tài liệu có hai section anh em trùng tên, mỗi section chứa một đoạn văn trùng nội dung:

  1. Mọi chunk_id phải phân biệt   (chống đụng độ)
  2. Thêm một đoạn trùng nội dung vào section THỨ NHẤT
     → chunk_id trong section THỨ HAI phải GIỮ NGUYÊN   (đây là bài bắt được F1)
  3. Mọi section_id phải phân biệt
```

Bài số 2 chính là I11 mở rộng sang trục ngang. I11 hiện tại chỉ kiểm trục dọc — chèn vào **đầu tài liệu**.
