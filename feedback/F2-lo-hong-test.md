# F2–F4, F7–F8 — Lỗ hổng trong bộ test

> **Đã xử lý 2026-08-14:** bổ sung kiểm tra section/parent ID, occurrence, ranh giới câu và thay hai test
> kiến trúc bằng kiểm tra import dựa trên AST.

Bộ test **21 bài đều xanh** và phủ đủ I1–I12 như ticket yêu cầu. Những mục dưới đây không phải "test sai" mà là
**test không bảo vệ được thứ nó trông như đang bảo vệ**.

---

## F2 🟠 — I11 chỉ kiểm `chunk_id`, bỏ quên `section_id`

```python
def test_inserting_a_block_at_start_keeps_unchanged_ids() -> None:
    original_by_text = {chunk.text: chunk.chunk_id for chunk in original.chunks}
    inserted_by_text = {chunk.text: chunk.chunk_id for chunk in inserted.chunks}
    assert all(inserted_by_text[text] == chunk_id for text, chunk_id in original_by_text.items())
```

[ADR 0001](../doc/adr/0001-dinh-danh-tat-dinh.md) vá **hai** định danh, không phải một: `chunk_id` **và**
`section_id`. Lý do vá `section_id` được ghi rõ — nếu nó đổi qua mỗi lần ingest thì khoá ngoại
`parent_section_id` gãy, kể cả khi `chunk_id` hoàn toàn ổn định.

Test này chỉ bảo vệ một nửa. Tôi đã kiểm bằng tay và `section_id` **đang ổn định đúng** — nhưng không có gì
giữ cho nó tiếp tục như vậy.

**Thêm:**
```python
assert {s.title: s.section_id for s in original.sections} \
    == {s.title: s.section_id for s in inserted.sections}
# và parent_section_id của từng chunk cũng không đổi
```

---

## F3 🟠 — `occurrence` không có một test nào

`occurrence` tồn tại để hai đoạn văn **trùng nội dung trong cùng một section** không nhận cùng một `chunk_id`.
Nếu nó hỏng — ví dụ ai đó "dọn dẹp" và bỏ nó khỏi khoá băm — hai chunk sẽ **trùng khoá chính**, và mọi kho
lưu trữ khoá theo `chunk_id` sẽ âm thầm gộp chúng làm một. Mất chunk, không có lỗi nào được ném.

Không fixture nào hiện có chứa hai khối trùng nội dung. Cơ chế này đang chạy **không có lưới**.

Tôi đã kiểm tay: nó hoạt động đúng.
```
order= 1  id=c_7051dcc13fd586081401ae58  'Xem lại phần trước.'
order= 3  id=c_62077f2be4ceaaaaaaa76328  'Xem lại phần trước.'   ← khác nhau, đúng
```

**Thêm:** một fixture có hai đoạn trùng nội dung trong cùng section, khẳng định số `chunk_id` phân biệt bằng
số chunk.

---

## F4 🟠 — Tên test nói dối về thứ nó kiểm

```python
def test_domain_does_not_import_project_or_external_packages() -> None:
    for path in Path("src/doc2roadmap/domain").glob("*.py"):
        ...
        assert all(not name.name.startswith("doc2roadmap") for name in node.names)
```

Tên hứa hai điều. Thân hàm chỉ kiểm **một**: không import `doc2roadmap`. Nó **không** kiểm external package.
Hôm nay ai đó viết `import torch` vào `domain/chunking.py` thì test này **vẫn xanh**.

Một test có tên hứa nhiều hơn nó làm thì **nguy hiểm hơn không có test**, vì lần sau người đọc sẽ tin rằng
tầng miền đã được canh và không kiểm lại.

Hai cách sửa, chọn một: đổi tên cho khớp thân hàm, hoặc bổ sung danh sách trắng module chuẩn
(`re`, `unicodedata`, `hashlib`, `json`, `dataclasses`, `typing`, `collections`) và bắt mọi import ngoài đó.
Cách thứ hai đúng tinh thần "tầng miền không phụ thuộc gì" hơn.

Cũng nên mở rộng `glob("*.py")` thành `rglob("*.py")` — hiện tại thư mục con trong `domain/` không được quét.

---

## F7 🟡 — Test kiến trúc lọt lưới

```python
if "doc2roadmap.application" in text and "doc2roadmap.infrastructure" in text:
```

Đòi **cả hai** chuỗi cùng có mặt. Một module ở tầng ứng dụng lỡ import thẳng
`doc2roadmap.infrastructure.parsing` mà **không** import gì từ `doc2roadmap.application` sẽ lọt qua — đúng
kiểu vi phạm phân tầng mà test này sinh ra để bắt.

Nên phân tích bằng `ast` như test bên trên, và ra luật theo tầng: tầng ứng dụng không được import
`infrastructure`; chỉ `composition` được phép import cả hai.

---

## F8 🟡 — I7 khẳng định quá yếu

```python
assert all(chunk.text.endswith(".") for chunk in output.chunks)  # I7
```

Fixture là `"Một hai ba. Bốn năm sáu. Bảy tám chín."` — mọi câu đều kết thúc bằng dấu chấm, nên khẳng định này
gần như không thể sai. Nó **không** chứng minh "không cắt ngang câu".

Rủi ro thực tế **thấp**, vì `VietnameseSentenceSplitter` đã có test riêng rất tốt cho đúng ca khó:

```python
text = 'TS. An đo 3.14 đơn vị. PGS. Bình nói "đồng ý!" Câu cuối?'
```

Nhưng để I7 thật sự là I7, nên cắt một khối **có chứa** `TS.` và `3.14` rồi khẳng định không mảnh nào kết thúc
giữa chừng — tức là nối các mảnh lại phải phủ đúng tập ranh giới câu.
