# 06 — Tham chiếu ảnh có vị trí, ngoài khoá băm

**What to build:** Từ một chunk, truy ra được **những bức hình nằm trong nó và chỗ chúng đứng**. Đây là mảnh
cuối để sau này hiện hình minh hoạ đúng chỗ trong đoạn văn cho người học, thay vì dồn hết xuống cuối.

Hình dạng đã chốt trong phiên grilling:

```
image_refs: [ { image_id, char_start }, … ]
```

`char_start` dùng **cùng hệ toạ độ** với vị trí ký tự sẵn có của chunk — offset trong chuỗi văn bản đầy đủ của
tài liệu. Không phát sinh khái niệm toạ độ mới.

Danh sách chứa **định danh**, không chứa đường dẫn. Đường dẫn là chi tiết của kho lưu trữ; đổi bố trí thư mục
hay chuyển sang lưu trữ đám mây không được phép làm sinh lại artifact chunk.

## Quyết định trung tâm của cả đợt

**Tham chiếu ảnh không tham gia khoá băm định danh chunk.**

Đây là thứ khiến điểm yếu "đổi độ phân giải trích ảnh làm đổi mọi định danh ảnh" trở nên chấp nhận được: định
danh chunk **không gãy theo**. Hai quyết định này chỉ đúng khi đi cùng nhau, và ticket `07` sẽ ghi chúng vào
ADR như một khối — để lần sau không ai "dọn dẹp" tham chiếu ảnh vào khoá băm.

Vì sao vị trí chứ không phải danh sách phẳng: sau ticket `05`, một chunk gộp có thể chứa **nhiều** khối hình,
và không phải cái nào cũng có chú thích. Nhìn phần văn bản không đoán được tham chiếu nào ứng với chỗ nào, vì
danh sách loại khối là **tập hợp**, không nhớ thứ tự.

**Blocked by:** 02 — cần định danh ảnh trên node. 05 — vị trí chỉ có ý nghĩa khi một chunk chứa được nhiều hình.

**Status:** completed — 2026-08-20

- [x] Chunk mang danh sách tham chiếu ảnh, mỗi tham chiếu gồm định danh ảnh và vị trí ký tự
- [x] Vị trí dùng cùng hệ toạ độ với vị trí ký tự sẵn có của chunk
- [x] Tham chiếu chứa **định danh**, không chứa đường dẫn
- [x] **Tham chiếu ảnh không nằm trong khoá băm định danh chunk**
- [x] Có test: chunk gộp chứa hai hình ⇒ hai tham chiếu, vị trí đúng theo thứ tự xuất hiện
- [x] Có test: chunk chứa một hình có chú thích và một hình không chú thích ⇒ phân biệt được tham chiếu nào ở đâu
- [x] Có test: **đổi tập tham chiếu ảnh mà giữ nguyên phần văn bản thì định danh chunk không đổi** — bài này là hiện thân của quyết định trung tâm
- [x] Có test ở tầng ingest: tham chiếu ảnh sống sót qua vòng lưu rồi nạp lại
- [x] Chunk không chứa hình nào thì danh sách rỗng, không phải thiếu trường
