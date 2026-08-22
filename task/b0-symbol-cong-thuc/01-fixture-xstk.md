# 01 — Fixture thứ hai từ tài liệu xstk

**What to build:** Bộ test có một fixture thứ hai chứa **653 ký tự vùng dùng riêng, 264 công thức và 51 bảng** —
những thứ mà fixture hiện có **không có một cái nào**. Kết thúc ticket, ba ticket sau khẳng định được số liệu
đầu-cuối trên dữ liệu thật thay vì trên chuỗi dựng tay.

Đây là **prefactor**: nó không sửa lỗi nào, nó làm `03` và `04` kiểm được.

## Vì sao fixture hiện có không đủ

```
                    tài liệu một   tài liệu hai
ảnh                       9              5
bảng                      0             51
công thức                 1            264
ký tự vùng dùng riêng     0            653
```

Dùng fixture hiện có để khẳng định *"653 ký tự về không"* hay *"263 node quay lại"* là **không thể**. Bốn đợt vá
trước chạy trên tài liệu một, và đó chính là lý do hai lỗi nặng nhất sống sót qua cả bốn.

## Vòng ghi–đọc đã được kiểm trước

Điều kiện sống còn là fixture phải giữ được **trường thô** — không có nó thì `04` không kiểm được. Đã chạy thử:

```
992 -> 992 item · khác biệt 0
công thức giữ được trường thô sau nạp lại : 263/264
ký tự vùng dùng riêng sống sót            : 1771
fixture                                   : 1,51 MB
```

Tài liệu nguồn **đã nằm trong dự án**, nên việc sinh lại tái lập được. Parse mất khoảng **221 giây**.

## Ticket này khác đợt ảnh ở một điểm quan trọng

Đợt ảnh **thay** fixture và làm hai test đỏ ngay lập tức. Lần này là **thêm** fixture thứ hai; fixture cũ và mọi
test đang dùng nó **không được đụng tới**.

**Blocked by:** Không — bắt đầu ngay.

**Status:** completed — 2026-08-22

- [x] Sinh fixture thứ hai từ tài liệu nguồn trong dự án, cùng cấu hình trích ảnh với fixture hiện có
- [x] Chỗ nạp fixture dùng chung nhận thêm fixture thứ hai, không phá cách nạp cái cũ
- [x] Ghi chú nguồn gốc cho fixture mới: sinh từ đâu, bằng cấu hình nào, chứa gì, khi nào phải sinh lại
- [x] Có **bài đặc tả hiện trạng** ghi đúng những gì đang sai, để ba ticket sau lật: **653** ký tự vùng dùng
      riêng, **264** công thức có trường đã dọn rỗng, **23** tiêu đề bắt đầu bằng dấu liệt kê hỏng mã
- [x] Có test: vòng ghi–đọc giữ nguyên số mục và giữ được trường thô của công thức
- [x] Test chạy trong nhóm test nhanh, không nằm trong nhóm cần chạy thư viện parse thật
- [x] Fixture cũ và mọi test đang dùng nó **không đổi một dòng nào**
- [x] Toàn bộ bộ test vẫn xanh
