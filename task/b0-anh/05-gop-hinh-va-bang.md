# 05 — Gộp hình và bảng như khối thường

**What to build:** Chú thích hình thôi đứng một mình. Hiện tám chunk hình dài 6–52 token, trung vị **13**, kẹp
giữa những chunk 233 và 259 token — chúng sẽ thành vector 13 token, gần như vô nghĩa, và ba trong số đó là câu
lệnh sinh ảnh bằng tiếng Anh giữa một corpus tiếng Việt.

Sau ticket này, chú thích hình hoà vào đoạn văn quanh nó, còn bảng nhỏ cũng vậy — vì cả hai đều thuộc mạch văn
thật.

## Không thêm tham số nào

Việc này là **một dòng**: hình và bảng hiện nằm ngoài tập loại khối được phép gộp, chỉ cần đưa chúng vào.

Luật hiện có đã lo phần còn lại: nhóm đóng lại khi thêm khối kế tiếp sẽ vượt trần token, nên một bảng vài
nghìn token tự động bị đẩy ra đứng riêng rồi đi tiếp vào đường cắt theo hàng. Bảng tám mươi token thì gộp như
đoạn văn. **Hành vi mong muốn đã có sẵn trong luật hiện tại** — thêm ngưỡng mới là thêm một thứ phải hiệu chỉnh
mà không đổi được gì.

Cước chú **vẫn đứng riêng**: nó thuộc chân trang, không thuộc mạch văn.

**Blocked by:** 04 — chunk gộp chứa cả đoạn văn lẫn hình cần khai đúng thành phần; landing trước `04` sẽ tạo
ra những chunk mang nhãn đoạn văn mà bên trong có hình, tức là làm lỗi cũ nặng thêm.

**Status:** completed — 2026-08-20

- [x] Hình và bảng vào tập loại khối được phép gộp; cước chú **không**
- [x] **Không thêm tham số ngưỡng nào**
- [x] Bảng lớn vẫn đứng riêng và vẫn đi qua đường cắt theo hàng như cũ
- [x] Bất biến trần token vẫn xanh
- [x] Bất biến "gộp không vắt qua ranh giới section" vẫn xanh
- [x] Có test: một chú thích hình kẹp giữa hai đoạn văn ngắn ⇒ ra **một** chunk, không phải ba
- [x] Có test: một bảng nhỏ gộp được với đoạn văn liền trước
- [x] Có test: một bảng lớn hơn trần **vẫn** đứng riêng rồi bị cắt theo hàng
- [x] Có test: cước chú kẹp giữa hai đoạn văn **vẫn không** bị gộp
- [x] Trên tài liệu thật: không còn chunk nào dưới 32 token chỉ vì nó là chú thích hình
