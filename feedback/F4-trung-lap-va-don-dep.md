# F9 🟡 — `windows` được tính hai lần bằng hai đoạn code khác nhau

> **Đã xử lý 2026-08-14:** domain chỉ trả sections/chunks/text; application là nơi duy nhất gọi
> `assemble_windows`.

Không phải lỗi. Là rủi ro phân kỳ.

`chunk_document` đã dựng sẵn `windows` trước khi trả về:

```python
# domain/chunking.py
windows: dict[str, list[Chunk]] = defaultdict(list)
for chunk in chunks:
    windows[chunk.parent_section_id].append(chunk)
return ChunkingResult(..., windows=dict(windows))
```

Rồi `IngestDocument` **ghi đè** nó bằng một hàm khác:

```python
# application/use_cases/ingest_document.py
result.windows = assemble_windows(result.chunks)
```

```python
# application/windows.py
for chunk in sorted(chunks, key=lambda item: item.order_index):   # ← có sort
    windows[chunk.parent_section_id].append(chunk)
```

Hai bản **không giống hệt nhau**: bản ở tầng ứng dụng có `sorted(...)`, bản trong domain dựa vào việc `chunks`
vốn đã theo thứ tự append. Hôm nay cả hai cho cùng kết quả. Ngày nào đó ai đó đổi thứ tự duyệt trong
`chunk_document` thì hai bản lệch nhau, và bản nào thắng sẽ tuỳ vào việc đi qua use case hay gọi thẳng domain
— nghĩa là **test ở seam thuần và hành vi thật sẽ khác nhau**.

Chọn một trong hai:

- **Bỏ `windows` khỏi `ChunkingResult`**, để việc gom window là logic ứng dụng thuần tuý. Đúng với spec:
  *"gom window và ráp ngữ cảnh là logic ứng dụng"*. Nhưng test ở seam thuần đang dùng `output.windows`, nên
  phải sửa test.
- **Giữ trong domain, xoá `assemble_windows`.** Ít sửa hơn, nhưng đặt logic ứng dụng vào tầng miền.

Nghiêng về cách thứ nhất — spec đã nêu rõ vị trí của nó, và giữ `ChunkingResult` chỉ chứa dữ liệu thô sẽ gọn hơn.

---

## Vài chỗ nhỏ khác, không chặn gì

**`_sentence_groups` khó đọc.** Vòng lặp có hai lệnh `break` kiểm **cùng một** `candidate`, một cái trước
`end += 1` và một cái sau:

```python
if end > start and counter.count(candidate) > max_tokens:
    break
end += 1
if counter.count(candidate) > max_tokens:
    break
```

Tôi đã truy tay và **logic đúng** — cái thứ hai chỉ có tác dụng ở vòng đầu (`end == start`), để xử lý một câu
đơn lẻ dài hơn ngưỡng. Nhưng phải truy tay mới biết, và nó gọi `counter.count` hai lần trên cùng một chuỗi.
Tách trường hợp "câu đơn quá dài" ra khỏi vòng lặp sẽ vừa nhanh hơn vừa nói rõ ý định.

**`heading_depth` dùng `section_id` làm khoá.** Sau khi sửa F1, nếu `section_id` đổi cách sinh thì nhớ rà lại
chỗ này — nó là `dict[str, int | None]` khoá theo `section_id`.
