# 03 — Trần cứng và cắt cưỡng bức

**What to build:** **Không chunk nào** vượt trần cứng. Không ngoại lệ, không miễn trừ, không *"trừ khi có lý
do"*. Hết cách cắt thì cắt cưỡng bức và ghi rõ đã làm vậy.

Đây là thứ bảo đảm lời gọi nhúng không bao giờ hỏng vì kích thước.

## Lỗ đang có

Một khối văn xuôi không cắt được — chữ viết không có dấu kết câu nào, hoặc một câu dài bất thường — hiện thành
một chunk lớn **tuỳ ý**, được gắn lý do, rồi đi tiếp. Không có gì chặn nó ở 6000 hay 60000 token.

Một hàng bảng đơn lẻ quá dài cũng vậy.

## Luật cắt cưỡng bức

Sau khi mọi đường cắt theo loại đã chạy, mảnh nào còn vượt trần cứng thì bị cắt cưỡng bức. **Trần thắng tuyệt
đối:**

```
lùi lại tìm khoảng trắng trong cửa sổ 10% trước điểm trần
  thấy   -> cắt tại đó
  không  -> cắt đúng tại điểm trần, tại ranh giới ký tự
```

Không đi tìm khoảng trắng **sau** điểm trần. Nếu ưu tiên ranh giới từ hơn trần thì bất biến canh nó phải có
dung sai, và một bất biến có dung sai thì yếu đi đúng chỗ nó cần mạnh nhất.

Chữ viết không dùng khoảng trắng — Trung, Nhật, Thái — sẽ **luôn** rơi vào nhánh thứ hai. Đó là hành vi đúng,
không phải thiếu sót.

## Hai điều cắt cưỡng bức không được phép làm

**Không tách dấu phụ khỏi ký tự gốc.** Với tiếng Việt điều đó làm vỡ chữ; với chữ viết khác nó sinh ký tự không
hợp lệ. Ranh giới ký tự ở đây nghĩa là ranh giới **cụm ký tự có nghĩa**, không phải ranh giới byte.

**Không phá bất biến vị trí ký tự.** Các mảnh cắt cưỡng bức phải liền mạch trong chuỗi văn bản đầy đủ, và cắt
chuỗi theo vị trí vẫn ra đúng nội dung từng mảnh.

## Lý do vượt trần có thêm một giá trị

| Lý do | Khi nào |
|---|---|
| hàng bảng vượt trần | đã có |
| bộ tách câu không tìm được ranh giới | đã có |
| **cắt cưỡng bức theo trần cứng** | **mới** |

## Bất biến này khác các bất biến trước ở một điểm

Bất biến trần token trước đây không bao giờ đỏ được, vì cờ vượt trần được tự bật đúng lúc điều kiện xảy ra —
dạng lỗi dự án đã gặp **ba lần**. Trần cứng **không có lối thoát nào**, nên bất biến canh nó đỏ được thật: một
lỗi sinh ra chunk bảy nghìn token sẽ làm nó đỏ.

**Blocked by:** 01 — cần tham số trần cứng đã tồn tại. Độc lập với ticket `02`.

**Status:** completed — 2026-08-21

- [x] Sau mọi đường cắt theo loại, mảnh nào còn vượt trần cứng thì bị cắt cưỡng bức
- [x] Cắt cưỡng bức lùi tìm khoảng trắng trong cửa sổ **10%** trước điểm trần; không thấy thì cắt tại điểm trần
- [x] **Không** tìm khoảng trắng sau điểm trần — trần thắng tuyệt đối
- [x] Cắt cưỡng bức **không bao giờ** tách một dấu phụ khỏi ký tự gốc
- [x] Chunk bị cắt cưỡng bức mang một lý do **riêng biệt**, phân biệt với hai loại vượt trần đã biết
- [x] Chỉ số mảnh tăng dần với các mảnh cắt cưỡng bức, nên định danh của chúng phân biệt được
- [x] Bất biến vị trí ký tự vẫn đúng với mọi mảnh cắt cưỡng bức
- [x] **I20** — **không chunk nào** vượt trần cứng. Không ngoại lệ
- [x] Có test: khối văn xuôi không có dấu kết câu, vượt trần cứng ⇒ cắt cưỡng bức, mọi mảnh dưới trần cứng
- [x] Có test: một hàng bảng vượt trần cứng ⇒ cắt cưỡng bức, mọi mảnh dưới trần cứng
- [x] Có test: cắt cưỡng bức trên chuỗi tiếng Việt ⇒ **không** ký tự nào bị vỡ dấu
- [x] Có test: cắt cưỡng bức trên chuỗi không có khoảng trắng ⇒ vẫn cắt được, tại ranh giới ký tự
- [x] Có test: khối vừa dưới trần cứng ⇒ **không** bị cắt cưỡng bức, **không** mang lý do đó
