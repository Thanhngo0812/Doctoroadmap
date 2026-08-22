# Task — Chữ Hy Lạp, công thức, và lọc tiêu đề không cần biết ngôn ngữ

**Status:** completed — 2026-08-22 · 7/7 ticket · 97 test xanh · đã ingest sạch và đối chiếu hai PDF thật.

Nguồn: [`doc/B0-symbol-va-cong-thuc-spec.md`](../../doc/B0-symbol-va-cong-thuc-spec.md) ·
[báo cáo F30–F33](../../feedback/F14-xstk-chat-luong-chunk.md) ·
[ADR 0001](../../doc/adr/0001-dinh-danh-tat-dinh.md) ·
[ADR 0002](../../doc/adr/0002-anh-va-tham-chieu-ngoai-dinh-danh-chunk.md) · [`CONTEXT.md`](../../CONTEXT.md)

Tài liệu thứ hai đi qua đường ống. **Cơ chế chạy tốt, nội dung thì hỏng.**

## Đồ thị chặn

```
01 fixture xstk          02 schema + bump
   (prefactor)              (prefactor)
     │      │                 │   │   │
     └──────┼─────────────────┤   │   │
            ▼                 ▼   │   │
     03 tra bảng Symbol   04 trường thô     │
            │              + công thức      │
            ▼                    │          ▼
     06 lọc tiêu đề              │    05 gom cảnh báo
            └─────────┬──────────┴──────────┘
                      ▼
          07 ADR + CONTEXT + đối chiếu
```

## Danh sách

| # | Ticket | Bị chặn bởi |
|---|---|---|
| [01](./01-fixture-xstk.md) | Fixture thứ hai từ tài liệu xstk | — |
| [02](./02-schema-va-bump.md) | Mở rộng schema và bump phiên bản | — |
| [03](./03-tra-bang-symbol.md) | Tra bảng Symbol về Unicode | 01, 02 |
| [04](./04-truong-tho-va-cong-thuc.md) | Đọc trường thô và đưa công thức quay lại | 01, 02 |
| [05](./05-gom-canh-bao.md) | Gom cảnh báo trùng lặp | 02 |
| [06](./06-loc-tieu-de.md) | Lọc tiêu đề: luật lặp lại và gạch đầu dòng | 03 |
| [07](./07-adr-va-doi-chieu.md) | ADR 0002, từ điển và đối chiếu hai tài liệu | 03, 04, 05, 06 |

## Bất biến mới

| Mã | Nội dung | Ticket |
|---|---|---|
| I22 | Không chunk nào chứa ký tự vùng dùng riêng, trừ khi có cảnh báo tương ứng | 03 |
| I23 | Node có trường thô khác rỗng **không bao giờ** bị bỏ im lặng | 04 |
| I24 | Đổi tham chiếu công thức mà giữ nguyên văn bản ⇒ định danh chunk **không đổi** | 04 |

## Bốn con số mở đầu

| | |
|---|---|
| Ký tự vùng dùng riêng | **653** trong **80/132** chunk |
| Công thức bị bỏ | **264**, mà **263** có chữ ở trường thô |
| Section thật ra là gạch đầu dòng | **23/67** |
| Dòng cảnh báo giống hệt nhau | **264** — hai cảnh báo thật bị chôn giữa đó |

## Vì sao `04` không tách được làm đôi

Đọc trường thô mà chưa xử lý công thức thì **8.280 token cháo chữ** đổ thẳng vào chunk — trạng thái **tệ hơn**
hiện tại. Hai nửa phải cùng landing.

## Vì sao `02` mang bump

Ba ticket đổi artifact: `04` đổi hình dạng chunk, `05` đổi nội dung manifest, `06` đổi tập section. Để bump
trong một nhánh thì hai nhánh kia phải chờ. Và nếu **không** bump thì artifact cũ bị dùng lại im lặng — đúng
con lỗi F21.

## `01` lần này an toàn, khác đợt ảnh

Đợt ảnh tôi **thay** fixture và làm hai test đỏ ngay. Lần này là **thêm** fixture thứ hai, không đụng cái cũ.

## Dự đoán kiểm được — tiêu chí mạnh nhất đợt

Đây là lần đầu **cả hai** tài liệu đổi định danh chunk, nhưng mức độ rất khác nhau:

- **Tài liệu hai**: đổi gần hết — 653 ký tự được sửa, 263 node quay lại.
- **Tài liệu một**: nó có **0** ký tự vùng dùng riêng và **0** tiêu đề lặp ≥2 lần. Chỉ **hai nhóm chunk** được
  phép đổi: nhóm chứa **một công thức khôi phục**, và nhóm chứa **dấu hiệu hình không có chú thích** (vì dấu
  hiệu đổi sang dạng trung tính ngôn ngữ). Đổi nhiều hơn thế ⇒ **dừng và tìm ra vì sao**.
