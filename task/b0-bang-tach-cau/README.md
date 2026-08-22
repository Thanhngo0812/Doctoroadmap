# Task — Bảng thành công dân hạng nhất, và tách câu toàn cầu

**Status:** completed — 2026-08-21 · 6/6 ticket · 71 test xanh · đã đối chiếu sạch PDF và DOCX fixture.  
**Báo cáo:** [`note.md`](./note.md)

Nguồn: [`doc/B0-bang-va-tach-cau-spec.md`](../../doc/B0-bang-va-tach-cau-spec.md) ·
[ADR 0001](../../doc/adr/0001-dinh-danh-tat-dinh.md) ·
[ADR 0002](../../doc/adr/0002-anh-va-tham-chieu-ngoai-dinh-danh-chunk.md) · [`CONTEXT.md`](../../CONTEXT.md)

Hai vấn đề độc lập, cùng một bản chất: **bước ingest chưa giao đủ thứ mà các pha sau cần**, và cả hai đều
không lộ ra trên tài liệu thử nghiệm hiện có.

## Đồ thị chặn

```
01 schema + bump v5          02 table_id ở adapter        04 bộ tách câu toàn cầu
   (prefactor)                     │                            │
     │      │                      │                            │
     │      └──────────┬───────────┘                            │
     │                 ▼                                        │
     │      03 table_refs trên chunk                             │
     ▼                 │                                        │
05 cảnh báo + lý do    │                                        │
   vượt trần           │                                        │
     └─────────────────┼────────────────────────────────────────┘
                       ▼
          06 ADR + CONTEXT + đối chiếu cuối
```

**Ba nhánh gốc chạy song song được.** `01` là prefactor mở đường; `02`→`03` là nhánh bảng; `04` là nhánh tách
câu, hoàn toàn độc lập. Chúng gặp nhau ở `06`.

## Danh sách

| # | Ticket | Bị chặn bởi |
|---|---|---|
| [01](./01-mo-rong-schema-chunk.md) | Mở rộng schema chunk và bump `section-id-v5` | — |
| [02](./02-dinh-danh-bang.md) | Định danh bảng ở adapter | — |
| [03](./03-tham-chieu-bang.md) | Tham chiếu bảng có vị trí trên chunk | 01, 02 |
| [04](./04-tach-cau-toan-cau.md) | Bộ tách câu toàn cầu | — |
| [05](./05-canh-bao-vuot-tran.md) | Cảnh báo khi bộ tách bó tay và lý do vượt trần | 01 |
| [06](./06-adr-va-doi-chieu.md) | ADR 0002, từ điển và đối chiếu cuối | 03, 04, 05 |

## Bất biến mới

| Mã | Nội dung | Ticket |
|---|---|---|
| I17 | Khối vượt trần mà bộ tách chỉ trả về một ranh giới ⇒ **có lý do cảnh báo** | 05 |
| I18 | Mọi mảnh của một bảng bị cắt mang **cùng** định danh bảng | 03 |
| I19 | Đổi tham chiếu bảng mà giữ nguyên văn bản ⇒ định danh chunk **không đổi** | 03 |

**I17 là bài mà bản hiện tại trượt** — hiện nó lặng lẽ gắn cờ vượt trần rồi đi tiếp.

## Vì sao `01` là ticket riêng và mang bump

Cả hai nhánh đều đổi hình dạng artifact chunk: nhánh bảng thêm tham chiếu bảng, nhánh tách câu đổi cờ vượt
trần thành lý do. Nếu bump nằm trong một nhánh thì nhánh kia phải chờ, mất tính song song. Tách phần mở rộng
schema ra trước, hai nhánh sau chỉ việc điền vào.

## Cái bẫy đã gặp ở đợt trước, sẽ gặp lại ở `01`

Bản ghi chunk được dựng lại từ JSON bằng cách bung thẳng khoá thành tham số, trên một lớp dữ liệu có khe cố
định. Đợt trước đổi tên trường phân loại khối đã làm **mọi artifact chunk cũ không nạp được**, và lỗi hiện ra
là một ngoại lệ kiểu khó hiểu. Lần này đổi cờ vượt trần sẽ gây đúng chuyện đó.

## Dự đoán kiểm được, và nó là tiêu chí nghiệm thu mạnh nhất đợt

**Tập định danh chunk của tài liệu thử nghiệm không đổi sau đợt này.**

Tài liệu đó không có bảng nào, và bộ tách câu chưa từng chạy trên nó — mọi chunk có chỉ số mảnh bằng không,
khối lớn nhất 400 token dưới trần 512. Cả hai trường mới đều **ngoài khoá băm**. Nên chỉ *hình dạng* artifact
đổi.

Nếu tập định danh đổi thì có gì đó ngoài dự kiến, và phải tìm ra **trước khi** đóng đợt.

## Bối cảnh: bốn con số

| | |
|---|---|
| Khối CJK 800 token | bộ tách trả **1 câu** → 1 chunk vượt trần **56%** |
| Khối Hindi 961 token | bộ tách trả **1 câu** → vượt trần **87%** |
| `Dr. Smith met Mr. Jones. They agreed.` | cắt thành **4 câu** thay vì 2 |
| Bảng trong tài liệu thử nghiệm | **0** — phần bảng phải kiểm bằng fixture DOCX |
