# Task — Lưu ảnh và tham chiếu ảnh trong chunk

**Status:** completed — 2026-08-20 · 7/7 ticket · 51 test xanh · đã ingest sạch và đối chiếu PDF thật.

**Báo cáo bàn giao:** [`note.md`](./note.md)

Nguồn: [`doc/B0-anh-va-tham-chieu-spec.md`](../../doc/B0-anh-va-tham-chieu-spec.md) ·
[ADR 0001](../../doc/adr/0001-dinh-danh-tat-dinh.md) · [`CONTEXT.md`](../../CONTEXT.md)

Chốt từ phiên grilling 2026-08-16 (Q1–Q13). Đợt này lần đầu tiên đưa **pixel** vào hệ thống — trước nay chỉ
có chữ.

## Đồ thị chặn

```
01 cổng parse mang ảnh       03 chú thích mồ côi       04 block_types + bump v4
   (prefactor)                                                   │
        │                          │                             ▼
        ▼                          │                    05 gộp hình và bảng
02 fixture + trích/lưu ảnh         │                             │
        │                          │                             │
        └──────────────┬───────────┼─────────────────────────────┘
                       ▼           │
          06 image_refs có vị trí  │
                       │           │
                       └─────┬─────┘
                             ▼
              07 CONTEXT + ADR 0002 + đối chiếu
```

**Ba nhánh chạy song song được.** `01`→`02` là nhánh ảnh. `03` độc lập hoàn toàn. `04`→`05` là nhánh chunker
thuần. Chúng gặp nhau ở `06` và `07`.

## Danh sách

| # | Ticket | Bị chặn bởi |
|---|---|---|
| [01](./01-cong-parse-mang-anh.md) | Cổng parse mang được ảnh | — |
| [02](./02-trich-va-luu-anh.md) | **Trích, lưu ảnh và thay fixture** | 01 |
| [03](./03-chu-thich-mo-coi.md) | Chú thích mồ côi và thống kê chú thích | — |
| [04](./04-block-types.md) | `block_types` và bump `algorithm_id` v4 | — |
| [05](./05-gop-hinh-va-bang.md) | Gộp hình và bảng như khối thường | 04 |
| [06](./06-image-refs-co-vi-tri.md) | Tham chiếu ảnh có vị trí, ngoài khoá băm | 02, 05 |
| [07](./07-adr-va-doi-chieu.md) | CONTEXT, ADR 0002 và đối chiếu tài liệu thật | 03, 06 |

## Vì sao fixture **không** là ticket riêng

Kế hoạch ban đầu tách fixture thành ticket riêng chạy trước. Thử thật thì **hỏng**: thay fixture một mình làm
2 test đỏ, vì bật ảnh khiến `export_to_markdown()` đổi hành vi. Một lát cắt phải tự nghiệm thu được, nên fixture
đi cùng ticket `02`.

## Mìn đã gỡ trước, ghi lại để khỏi giẫm

Bật trích ảnh **đổi hành vi** của bản xuất markdown: trước trả một dòng thông báo lỗi ngắn, sau trả **nguyên
ảnh nhúng base64**, 33–296 KB mỗi hình. Adapter hiện dùng nó làm nhánh dự phòng khi hình không có chú thích.

Đo thật trên fixture có ảnh:

```
p9 len=295568  '![Image](data:image/png;base64,iVBORw0KGgoAAAANSUhEU…'
```

**295.568 ký tự base64 trở thành nội dung một node.** Nó sẽ thành chunk, được đếm token, và được embed.
Ticket `02` phải **gỡ hẳn** nhánh dự phòng đó, không chỉ thêm chuỗi thay thế.

## Bối cảnh: bốn con số

| | |
|---|---|
| Chi phí trích ảnh | **144,0 s** so với ~146 s không trích — trong nhiễu |
| Chín ảnh của tài liệu thử | **0,78 MB** PNG ở scale 2,0 |
| Fixture kèm ảnh | 0,22 MB → **1,49 MB**, nạp 0,04 s → 0,11 s, khôi phục **9/9** |
| Chunk hình hiện tại | 6–52 token, trung vị **13** |
