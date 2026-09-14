# 06 — Ngữ cảnh lời gọi: tổ tiên vào, lân cận ra, công thức thô vào

**What to build:** Trích trên tài liệu toán không còn đọc văn bản thủng lỗ chỗ. **66% chunk của
`xstk-ch3-1` chứa dấu `[formula]`** — 263 dấu — và hiện mô hình chỉ thấy dấu, không thấy toán.

## Ba luật ngữ cảnh

| Thành phần | Vào ngữ cảnh trích? | Vào `text` chunk? | Vào embedding? |
|---|:---:|:---:|:---:|
| `section_path` (tiêu đề tổ tiên) | ✅ | ❌ | ✅ (ghép lúc embed) |
| Văn bản chunk của section | ✅ | — | ✅ |
| Nội dung section **lân cận** | ❌ | ❌ | ❌ |
| **Nội dung thô công thức** | ✅ | ❌ | ❌ |

**Vì sao loại section lân cận** — không phải để tiết kiệm, mà vì nó **xung đột với luật bằng chứng
ticket 02**: mô hình thấy văn bản bên cạnh sẽ trích câu từ đó, code chỉ dò trong chunk của section này,
nên khái niệm bị loại oan. Ngữ cảnh tổ tiên là **tiêu đề**, không tạo nguồn trích dẫn giả.

**Vì sao công thức thô chỉ vào ngữ cảnh** — nội dung thô lộn xộn thứ tự
(`'X x1 x2 .  .  . xk ni n1 n2 .  .  . nk'`) và tổng **8.280 token**, tức +28% cháo chữ nếu đưa vào
phần được embed. Nhưng đọc cùng câu *"thường được xác định dưới dạng bảng"* thì nhận ra ngay đó là bảng
tần số. **Lộn xộn mà có mặt vẫn hơn vắng mặt.**

**Blocked by:** 03 — cần hình dạng lời gọi đã ổn định.

**Status:** done

- [x] Lời gọi nhận `section_path` đầy đủ; ví dụ thật:
      `THỐNG KÊ TOÁN §1. LÝ THUYẾT MẪU > 1.3. Các số đặc trưng của mẫu cụ thể`
- [x] Lời gọi **không** nhận nội dung section lân cận
- [x] Nội dung thô công thức của chunk trong section được bơm vào ngữ cảnh, gắn với vị trí dấu
- [x] Nội dung thô **không** vào `text` chunk và **không** vào bất kỳ vector nào
- [x] Có test: chunk có `formula_refs` ⇒ ngữ cảnh chứa nội dung thô tương ứng
- [x] Có test: `text` chunk và đầu vào embedding **không đổi** sau ticket này — số vàng B0 đứng yên
- [x] Ghi lại số section được bơm công thức và tổng token bơm thêm

> **Đường leo nếu chưa đủ:** nếu bộ vàng (ticket 11) cho thấy khái niệm sót **tập trung ở chương nhiều
> công thức**, phương án tiếp theo là cắt **ảnh vùng công thức theo bbox** và đi đường đa phương thức
> của ticket 05. Đó là **ticket B0 mới** — B0 phải lưu thêm ảnh cắt — không thuộc đợt này.
