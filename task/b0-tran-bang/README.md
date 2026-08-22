# Task — Ba trần token thay vì một

Nguồn: [`doc/B0-tran-bang-spec.md`](../../doc/B0-tran-bang-spec.md) ·
[ADR 0001](../../doc/adr/0001-dinh-danh-tat-dinh.md) ·
[ADR 0002](../../doc/adr/0002-anh-va-tham-chieu-ngoai-dinh-danh-chunk.md) · [`CONTEXT.md`](../../CONTEXT.md)

**Trạng thái:** ✅ Hoàn thành 4/4 ticket ngày 2026-08-21. Xem [báo cáo nghiệm thu](./note.md).

Một trần token đang phục vụ hai loại nội dung có bản chất khác hẳn nhau, và nó sai với một trong hai.

## Đồ thị chặn

```
01 ba tham số vào cấu hình + bump
        (prefactor)
         │        │
         ▼        ▼
02 trần bảng    03 trần cứng
   + trần gộp      + cắt cưỡng bức
         └────┬───┘
              ▼
     04 đối chiếu + tài liệu
```

**Hai nhánh chạy song song được.** `01` mang bump để `02` và `03` không chặn nhau.

## Danh sách

| # | Ticket | Bị chặn bởi |
|---|---|---|
| [01](./01-ba-tham-so-tran.md) | Ba tham số trần vào cấu hình và bump | — |
| [02](./02-tran-bang-va-tran-gop.md) | Trần bảng và trần gộp | 01 |
| [03](./03-tran-cung-va-cat-cuong-buc.md) | Trần cứng và cắt cưỡng bức | 01 |
| [04](./04-doi-chieu-va-tai-lieu.md) | Đối chiếu và tài liệu | 02, 03 |

## Ba trần, mỗi trần một câu hỏi

| Tham số | Mặc định | Trả lời câu hỏi |
|---|---:|---|
| `max_tokens` | 512 | bao nhiêu chữ thành một đơn vị truy hồi tốt |
| `max_table_tokens` | **2048** | bảng lớn cỡ nào thì vẫn nên nằm gọn một chỗ |
| `hard_cap_tokens` | **6000** | ngưỡng nào chắc chắn an toàn với mô hình nhúng |

## Bất biến mới

| Mã | Nội dung | Ticket |
|---|---|---|
| I20 | **Không chunk nào vượt trần cứng.** Không ngoại lệ | 03 |
| I21 | Chunk vượt trần áp dụng của nó ⇒ mang một lý do tường minh | 02 |

`I15` cũ **chưa từng tồn tại dưới dạng test có nhãn** — chỉ có vài khẳng định rời rạc không đánh số. Nên đây là
**viết mới**, không phải sửa.

## Số đo mở đầu

| Bảng | Vượt 512 | Vượt 2048 | Vượt 8192 |
|---|---:|---:|---:|
| 4 cột, ô ngắn | **20 hàng** | 79 hàng | 307 hàng |
| 6 cột, ô mô tả dài | **11 hàng** | 45 hàng | 175 hàng |

Trần hiện tại cắt một bảng **mười một hàng**. Giới hạn của mô hình nhúng là **8192**, và ta đếm bằng tokenizer
**Gemma** chứ không phải của Gemini — nên 6000 là biên an toàn, không phải con số tuỳ tiện.

## Câu dẫn bảng đang bị bỏ lại

```
 22 token  ['text']            <- "Bảng 1 dưới đây so sánh…" BỊ BỎ LẠI MỘT MÌNH
499 token  ['table']
217 token  ['table','text']
```

Nâng trần *cắt* **không** sửa việc này — trần *gộp* là chuyện khác. Đó là nửa thứ hai của ticket `02`.

## Dự đoán kiểm được

**Tập định danh chunk của tài liệu thử nghiệm không đổi.** Tài liệu không có bảng, khối lớn nhất 400 token dưới
cả ba trần. Chỉ hình dạng cấu hình đổi. Nếu tập định danh đổi thì **dừng và tìm ra vì sao** trước khi đóng đợt.

## Điều cần nhớ suốt đợt

**Cắt chunk không phải cắt bảng.** Cấu trúc hàng cột sống trong cây parse, nguyên vẹn, khoá theo định danh
bảng; mọi mảnh của một bảng bị cắt mang cùng định danh và lặp dòng tiêu đề cột. Thứ bị chia là **đơn vị truy
hồi**, không phải **dữ liệu**.
