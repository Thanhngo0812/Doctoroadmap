# 03 — Tra bảng Symbol về Unicode

**What to build:** Người đọc giáo trình thống kê thấy `σ`, `μ`, `χ` thay vì ô vuông hỏng mã. Truy vấn *"phương
sai σ²"* khớp được với chunk nói về nó. Và dòng tiêu đề cột của bảng hết hỏng — `Σ` cũng nằm trong số đó.

**653 ký tự vùng dùng riêng trong 80 trên 132 chunk — 61%.**

## Vì sao hỏng

PDF nhúng chữ Hy Lạp bằng font Symbol, một font ánh xạ mã Latin sang ký tự Hy Lạp. Khi trích xuất, các mã đó
rơi vào vùng `U+F000–U+F0FF` thay vì được đưa về Unicode thật. `U+F061` chính là `0xF000` cộng mã chữ `a`, mà
`a` trong bảng Symbol là **α**.

Mười ký tự hay gặp nhất: **α** (149), **→** (109), **μ** (90), **χ** (67), **σ** (43), **θ** (29), **ε** (18),
**∼**, **∈**, **≈**. Đó là toàn bộ bảng chữ cái của thống kê.

Đây **không phải mất chữ mà là hỏng chữ** — tệ hơn, vì không dấu vết nào báo.

## Đây là phỏng đoán, và phỏng đoán phải để lại dấu vết

Đã kiểm: **thư viện parse không cho biết font.** Đối tượng mục không có thuộc tính nào về font hay glyph; khối
xuất xứ chỉ có khung, khoảng ký tự và số trang. Nên ta đang **đoán** rằng font là Symbol.

Bằng chứng ủng hộ mạnh — ba mẫu giải mã đọc lại đúng hoàn hảo:

```
'ký hiệu là _ và phương sai D(X) … ký hiệu là _'   ->  'ký hiệu là μ … ký hiệu là σ'
'X _ N( _ ; _ 2 )'                                 ->  'X ∼ N( μ ; σ 2 )'
'| | n | _ x | _ x 2 |'                            ->  '| | n | Σ x | Σ x 2 |'
```

Nhưng đó là bằng chứng từ **một** tài liệu. Áp vô điều kiện là đúng — ký tự vùng dùng riêng **không có nghĩa
hợp lệ nào** trong văn bản đã trích, nên để nguyên là sai chắc chắn — nhưng phải ghi lại số ánh xạ và cảnh báo
phần còn sót, để tài liệu dùng font khác lộ ra ngay thay vì lại im lặng.

**Blocked by:** 01 — cần fixture có ký tự vùng dùng riêng thật để khẳng định 653 về không. 02 — cần phiên bản
mới, nếu không cây parse cũ bị dùng lại.

**Status:** completed — 2026-08-22

- [x] Bảng ánh xạ Adobe Symbol từ vùng `U+F000–U+F0FF` về Unicode thật, đặt ở **adapter parse**, cùng chỗ với
      việc gộp glyph lặp
- [x] **Chỉ áp cho nguồn PDF**
- [x] Áp cho **mọi** nội dung node, kể cả ô bảng
- [x] Số ký tự đã ánh xạ được ghi vào thống kê parse
- [x] Còn ký tự vùng dùng riêng sau khi tra ⇒ **một lý do cảnh báo**, kèm số lượng
- [x] **I22** — không chunk nào chứa ký tự vùng dùng riêng, trừ khi có cảnh báo tương ứng
- [x] Có test dựng tay: `U+F061` `U+F063` `U+F06D` `U+F073` ra `α` `χ` `μ` `σ`
- [x] Có test dựng tay: `U+F0B7` ra dấu chấm tròn
- [x] Có test: nguồn DOCX có ký tự vùng dùng riêng thì **không** tra bảng
- [x] Có test trên fixture hai: **653 về 0**, hoặc phần còn lại có cảnh báo kèm đúng số lượng
- [x] Có test: ô bảng cũng được sửa — `Σ` trong dòng tiêu đề cột
- [x] Bài đặc tả hiện trạng ở `01` được lật ở phần ký tự vùng dùng riêng
