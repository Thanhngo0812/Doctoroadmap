# 09 — Gộp leaf block theo đích kích thước

**What to build:** Người dùng bước truy hồi nhận về chunk cỡ **hai trăm năm mươi token** thay vì sáu mươi hai,
và không còn chunk ba token nào. Ngân sách token thôi bị bỏ phí tám lần.

Hiện kích thước chunk **không do ai chọn** — luật một leaf block là một chunk khiến nó bằng kích thước đoạn văn
mà tác giả giáo trình viết ra. Trần năm trăm mười hai chưa bao giờ chạm, nên luật cắt theo câu chưa từng chạy.
Một phần năm số chunk ngắn hơn ngưỡng tối thiểu, nhỏ nhất là ba token. Vector của văn bản ngắn rất kém ổn định.

Cái đang thiếu không phải trần mà là **đích**: thêm tham số đích, gộp các leaf block liền kề trong cùng một
section cho tới khi đạt đích. Tham số ngưỡng tối thiểu bị bỏ hẳn — nó chưa từng có hành vi nào.

Đo trên tài liệu thật, gộp trong cùng section:

| Đích | Số chunk | Trung vị | Dưới 32 token |
|---|---:|---:|---:|
| hiện tại | 132 | 62 | 27 |
| **256** | **39** | **270** | **4** |
| 512 | 31 | 316 | 3 |

Chọn 256 chứ không 512 vì ở 512 có chunk chạm 511 — bắt đầu nuốt gần trọn một section và mất khả năng định vị
bằng chứng.

**Không chồng lấn giữa các chunk gộp.** Ranh giới ở đây là ranh giới đoạn văn, vốn đã là ranh giới ngữ nghĩa —
khác cửa sổ trượt cố định nơi chồng lấn tồn tại để cứu câu bị cắt giữa. Cần ngữ cảnh rộng hơn thì đã có window.

**Blocked by:** 04 và 05 — gộp trong cùng section chỉ có nghĩa khi cây section đã đúng và tiêu đề giả đã bị
loại; nếu không thì việc gộp sẽ diễn ra quanh những ranh giới sai.

**Status:** completed

- [x] Tham số ngưỡng tối thiểu bị bỏ khỏi cấu hình; thêm tham số **đích**, mặc định hai trăm năm mươi sáu
- [x] Đi theo thứ tự đọc, tích luỹ leaf block trong cùng một section; đóng nhóm khi thêm block kế tiếp sẽ vượt
      trần, hoặc khi nhóm đã đạt đích
- [x] **Không bao giờ** gộp qua ranh giới section
- [x] Chỉ khối văn bản và mục danh sách mới gộp được với nhau; bảng, hình và cước chú luôn đứng một mình
- [x] Nhóm cuối của một section ngắn hơn đích thì giữ nguyên — không còn gì để gộp cùng
- [x] Khối đơn lẻ dài hơn trần vẫn đi qua đường cắt theo ranh giới câu như cũ, và chỉ đường đó mới sinh chỉ số
      mảnh khác không
- [x] **I16** — không chunk nào chứa leaf block thuộc hai section khác nhau
- [x] Bài kiểm vị trí ký tự hiện có được mở rộng cho chunk gộp: cắt chuỗi đầy đủ theo vị trí vẫn ra đúng nội
      dung chunk
- [x] Có test: nhóm đóng lại khi đạt đích, không chờ tới trần
- [x] Có test: một cước chú nằm giữa hai đoạn văn **không** bị gộp vào đoạn nào
- [x] Có test: hai section liền nhau, mỗi bên một block ngắn ⇒ ra **hai** chunk, không phải một
- [x] Mọi tham số trong cấu hình đều thật sự ảnh hưởng tới đầu ra — đổi đích thì kết quả phải khác
- [x] Các bài kiểm ổn định định danh hiện có vẫn xanh

> **Hệ quả cho định danh, ticket 11 sẽ ghi vào ADR:** gộp làm các block dính vào nhau trong khoá băm. Trước
> đây sửa block thứ nhất chỉ đổi định danh của chính nó; sau khi gộp thì nó đổi định danh của cả nhóm. Đây là
> mất mát thật về tính ổn định, đổi lấy chất lượng vector.
