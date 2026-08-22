# Task — Vá pha B0 sau khi đo trên tài liệu thật

**Status:** completed — 2026-08-16 · 44 test xanh · đã đối chiếu lại PDF `nhap-mon-ml` sau feedback F10.

**Bổ sung sau bàn giao:** [`note.md`](./note.md) — sửa reading order, stitch câu bị đứt tại ranh giới trang và xử lý
[`feedback F10`](../../feedback/F10-note-sua-reading-order.md).

Nguồn: [`doc/B0-va-cau-truc-spec.md`](../../doc/B0-va-cau-truc-spec.md) · [feedback vòng 2](../../feedback/README.md) ·
[ADR 0001](../../doc/adr/0001-dinh-danh-tat-dinh.md) · [`CONTEXT.md`](../../CONTEXT.md)

Đợt trước ([`task/b0-chunking/`](../b0-chunking/)) dựng xong pha B0 và 25 test đều xanh. Đợt này vá những gì
chỉ lộ ra khi đưa một giáo trình thật vào — **không bài test nào trong số 25 bài bắt được cái nào**.

## Đồ thị chặn

```
01 phiên bản adapter      02 khung test fixture      03 cảnh báo + bump v3
   (F21)                     (prefactor)                (F12)
    │                            │                          │
    └─────────────┬──────────────┘                          ▼
                  ▼                                04 suy cấp heading (F11)
        06 hình sạch      (F13)                             ▼
        07 gộp glyph      (F15)                    05 lọc tiêu đề giả (F14)
        08 thống kê parse (F16)                             ▼
                  │                                09 gộp block, đích 256 (F18+F19)
                  │                                         ▼
                  │                                10 cắt bảng + I15 (F20)
                  └──────────────┬──────────────────────────┘
                                 ▼
                    11 ADR + đối chiếu tài liệu thật
```

**Ba nhánh chạy song song được.** `01`+`02` là hạ tầng, mở đường cho nhánh adapter `06`/`07`/`08`. Nhánh
`03`→`04`→`05`→`09`→`10` là logic thuần trong tầng miền, không cần Docling. Chúng chỉ gặp nhau ở `11`.

## Danh sách

| # | Ticket | Bị chặn bởi | Vá |
|---|---|---|---|
| [01](./01-phien-ban-adapter.md) | Adapter công bố phiên bản của riêng nó | — | F21 |
| [02](./02-khung-test-parse-that.md) | Khung test nuôi bằng kết quả parse thật | — | *prefactor* |
| [03](./03-canh-bao-cau-truc.md) | Cảnh báo cấu trúc thành danh sách lý do | — | F12 |
| [04](./04-suy-cap-heading.md) | Suy cấp heading từ cách đánh số | 03 | **F11** |
| [05](./05-loc-tieu-de-gia.md) | Lọc tiêu đề giả | 04 | F14 |
| [06](./06-hinh-sach.md) | Hình sạch, không còn thông báo lỗi trong nội dung | 01, 02 | F13 |
| [07](./07-gop-glyph-lap.md) | Gộp ký hiệu toán bị nhân bản glyph | 01, 02 | F15 |
| [08](./08-thong-ke-parse.md) | Thống kê node bị bỏ vào manifest | 01, 02 | F16 |
| [09](./09-gop-leaf-block.md) | Gộp leaf block theo đích kích thước | 04, 05 | F18, F19 |
| [10](./10-cat-bang-theo-hang.md) | Cắt bảng theo hàng và bất biến trần token | 09 | F20 |
| [11](./11-adr-va-doi-chieu-cuoi.md) | Cập nhật ADR và đối chiếu trên tài liệu thật | 04–10 | — |

## Bất biến mới

| Mã | Nội dung | Ticket |
|---|---|---|
| I13 | Mọi heading cùng cấp một + tiêu đề đánh số ⇒ cây ba cấp | 04 |
| I14 | Mọi heading cùng cấp một + tiêu đề **không** đánh số ⇒ có cảnh báo cây phẳng | 04 |
| I15 | Không chunk nào vượt trần token, trừ khi được đánh dấu tường minh | 10 |
| I16 | Gộp không bao giờ tạo chunk có leaf block thuộc hai section | 09 |

**I13 là bài mà bản hiện tại trượt.** Đó là lý do nó đáng viết trước.

## Vì sao `01` phải chạy trước mọi ticket đụng adapter

Hash cấu hình parse hiện phụ thuộc **duy nhất** vào phiên bản thư viện Docling. Sửa mã adapter mà thư viện giữ
nguyên phiên bản thì hash không đổi, nên lần ingest sau tìm thấy cây parse cũ và **dùng lại**. Người làm ticket
`06`, `07`, `08` sẽ sửa đúng, chạy lại, thấy kết quả y hệt, và tưởng mình viết sai.

## Vì sao bump `section-id-v2` → `v3` nằm ở `03` chứ không ở cuối

`03` đổi *hình dạng* artifact chunk, nên nó phải bump vì lý do riêng của nó. Bump sớm thì cả năm mục
F11 · F14 · F15 · F18 · F19 nằm gọn dưới `v3` — đúng yêu cầu "một lần bump". Bump ở cuối sẽ để lại một quãng
giữa các ticket mà artifact cũ bị dùng lại im lặng, tức là tái tạo đúng con lỗi F21 ở dạng khác.

Trong lúc chạy đợt này, **xoá artifact cũ trước mỗi lần ingest lại**.

## Bối cảnh: bốn con số đáng nhớ

| | |
|---|---|
| Heading của tài liệu thật, toàn bộ ở cấp 1 | **27/27** |
| Chunk có `section_path` chỉ dài một phần tử | **132/132** |
| Trung vị token mỗi chunk, trần là 512 | **62,5** |
| Chunk dính ký hiệu toán nhân bản | **29/132 = 22%** |
