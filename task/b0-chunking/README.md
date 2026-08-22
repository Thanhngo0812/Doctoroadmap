# Task — Pha B0.1–B0.4: Chuẩn hoá, parse và cắt chunk

Nguồn: [`doc/B0-chunking-spec.md`](../../doc/B0-chunking-spec.md) · [ADR 0001](../../doc/adr/0001-dinh-danh-tat-dinh.md) · [`CONTEXT.md`](../../CONTEXT.md)

## Đồ thị chặn

```
01 khung dự án + kiểm chứng Docling
 │
 ├──────────────┐
 ▼              ▼
02 cây section  04 adapter parse thật
   + định danh     + đóng băng artifact
 ▼              │
03 luật cắt     │
   đầy đủ       │
 │              │
 └──────┬───────┘
        ▼
   05 lệnh ingest
        ▼
   06 lệnh inspect
```

**Hai nhánh chạy song song được.** `02`→`03` là logic thuần, không cần Docling. `04` là Docling, không cần
logic cắt chunk. Chúng chỉ gặp nhau ở `05`.

## Danh sách

| # | Ticket | Bị chặn bởi |
|---|---|---|
| [01](./01-khung-du-an-va-kiem-chung-docling.md) | Khung dự án + kiểm chứng Docling cài được | — |
| [02](./02-cay-section-va-dinh-danh-tat-dinh.md) | Cây section, gán cha, và định danh tất định | 01 |
| [03](./03-luat-cat-day-du.md) | Luật cắt đầy đủ: block dài, block ngắn, bảng và caption | 02 |
| [04](./04-adapter-parse-va-artifact.md) | Adapter parse thật + đóng băng artifact cây parse | 01 |
| [05](./05-lenh-ingest.md) | Lệnh `ingest` chạy đầu-cuối trên PDF thật | 03, 04 |
| [06](./06-lenh-inspect.md) | Lệnh `inspect` xem cây section và window | 05 |

## Bất biến — ticket nào phủ cái nào

I1–I10 lấy từ §11 của `doc/B0-ingestion-spec.md`. **I11 và I12 là bổ sung của spec mới** — chúng là hai bài
mà công thức định danh gốc trượt, xem ADR 0001.

| Bất biến | Nội dung | Ticket |
|---|---|---|
| I1 | Mỗi chunk thuộc đúng một window | 02 |
| I2 | Section cha là heading gần nhất | 02 |
| I3 | Window của cha không chứa chunk của con | 02 |
| I4 | Section không có nội dung trực tiếp thì không sinh window | 02 |
| I5 | Ingest lại cùng đầu vào cho cùng tập định danh | 02, kiểm lại ở 05 |
| I6 | Thứ tự đọc tăng đơn điệu | 02 |
| I7 | Không cắt ngang câu | 03 |
| I8 | Văn bản đã chuẩn hoá Unicode | 02 |
| I9 | Cắt chuỗi theo vị trí ra đúng nội dung chunk | 02 |
| I10 | Tài liệu không heading vẫn hợp lệ | 02 |
| **I11** | **Chèn đoạn vào đầu, phần không đổi giữ nguyên định danh** | 02, kiểm lại ở 05 |
| **I12** | **Đổi ngưỡng độ dài, chỉ block bị cắt lại mới đổi định danh** | 03 |
