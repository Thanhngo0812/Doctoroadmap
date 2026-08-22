# 06 — Lọc tiêu đề: luật lặp lại và gạch đầu dòng

**What to build:** `Trong đó:` thôi là section, kể cả khi nó **viết hoa**. Và **23 trên 67 section** vốn là
gạch đầu dòng biến mất khỏi cây.

Bộ lọc tiêu đề giả bị vượt qua bằng **hai** đường khác nhau, và mỗi đường cần một luật riêng.

## Đường một — cụm nối viết hoa

Luật hiện tại loại tiêu đề khi *kết thúc bằng dấu hai chấm **và** không đánh số **và** ký tự đầu là chữ thường*.
`Trong đó:` viết hoa nên qua được — đúng cụm đã vá ở một đợt trước, chỉ khác chữ hoa.

Cách vá cũ là thêm một danh sách cụm từ tiếng Việt. **Không làm thế** — nó lặp lại đúng sai lầm của bộ tách câu
mang tên một ngôn ngữ, và hệ thống này phục vụ mọi giáo trình.

**Luật mới, không cần biết ngôn ngữ nào:** một tiêu đề ứng viên **không đánh số** mà văn bản của nó xuất hiện
**từ hai lần trở lên** trong các khối thân bài của cùng tài liệu ⇒ là cụm nối, hạ xuống khối văn bản thường.

Đo trên **cả hai** tài liệu, ngưỡng hai tách hoàn hảo:

| Tiêu đề | Lần xuất hiện trong thân bài | Thật ra là |
|---|---:|---|
| `Chú ý .` | **11** | cụm nối |
| `Trong đó:` | **10** | cụm nối |
| `trong đó:` | **4** | cụm nối |
| `Làm sạch dữ liệu` | 1 | **tiêu đề thật** |
| `Giải` | 1 | **tiêu đề thật** |
| `TẬP THỂ TÁC GIẢ:` · `a) Chọn kiểu mô hình:` · các mục đánh số | **0** | tiêu đề thật |

Luật này **tự hiệu chỉnh theo từng tài liệu** — dùng chính bằng chứng trong tài liệu đó — và chạy được với chữ
Hán, Ả Rập, Thái vì không cần khái niệm hoa/thường.

**Rủi ro đã biết:** một tiêu đề ngắn trùng từ thông dụng sẽ bị oan — ví dụ mục tên `Overfitting` mà thân bài
nhắc từ đó nhiều lần. Giảm bằng cách **miễn trừ hoàn toàn tiêu đề có đánh số**, đúng quy ước đã dùng ở mọi luật
khác trong bộ lọc.

Luật cũ **được giữ**. Hai luật độc lập và cộng dồn.

## Đường hai — gạch đầu dòng

```
L3  '<dấu chấm tròn> T ổng thể'
L3  '<dấu chấm tròn> Mẫu'
L3  '<dấu chấm tròn> Tỉ lệ mẫu'
```

Dấu chấm tròn của font Symbol rơi vào vùng dùng riêng, nên luật *"ký tự đầu là chữ thường"* không nhận ra — ký
tự đầu là một mã hỏng.

Sau khi tra bảng Symbol, tiêu đề bắt đầu bằng một **dấu liệt kê** — chấm tròn, ô vuông, gạch ngang và các dấu
tương đương trong khối ký hiệu Unicode — thì không phải tiêu đề.

**Luật này phải chạy sau khi tra bảng Symbol.** Đó là lý do ticket bị chặn bởi `03`.

**Blocked by:** 03 — trước khi tra bảng, dấu chấm tròn còn là một mã vùng dùng riêng mà không luật nào nhận ra.

**Status:** completed — 2026-08-22

- [x] Tiêu đề ứng viên **không đánh số** mà văn bản xuất hiện **≥2 lần** trong khối thân bài ⇒ hạ xuống văn bản thường
- [x] Tiêu đề **có đánh số** được **miễn trừ hoàn toàn** khỏi luật này
- [x] Tiêu đề bắt đầu bằng **dấu liệt kê** ⇒ hạ xuống văn bản thường
- [x] **Không** dùng danh sách cụm từ của bất kỳ ngôn ngữ nào
- [x] Luật cũ — dấu hai chấm, không đánh số, chữ thường — **được giữ nguyên**
- [x] Mỗi lần loại ghi một lý do cảnh báo kèm nguyên văn
- [x] Có test: tiêu đề không đánh số lặp **2 lần** ⇒ bị loại
- [x] Có test: tiêu đề không đánh số lặp **1 lần** ⇒ **được giữ**
- [x] Có test: tiêu đề **có đánh số** lặp 5 lần ⇒ **được giữ**
- [x] Có test: tiêu đề bắt đầu bằng dấu liệt kê ⇒ bị loại
- [x] Có test hồi quy trên tài liệu một: `Làm sạch dữ liệu`, `TẬP THỂ TÁC GIẢ:`, `a) Chọn kiểu mô hình:` **vẫn giữ**
- [x] Có test trên fixture hai: `Trong đó:` và `Chú ý .` **bị loại**; **không** section nào bắt đầu bằng dấu liệt kê
- [x] Nội dung nằm sau một tiêu đề bị loại quay về đúng section cha, không mất và không lạc
