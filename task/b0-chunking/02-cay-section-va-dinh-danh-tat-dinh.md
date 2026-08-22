# 02 — Cây section, gán cha, và định danh tất định

**What to build:** Đưa vào một cây tài liệu, nhận ra sections và chunks — mỗi chunk biết section cha trực tiếp
của nó, và mỗi cái mang một định danh sống sót qua các lần ingest lại. Ở ticket này một khối là một chunk;
việc cắt khối dài để sang ticket 03.

Đây là tracer bullet chính: một đường đi hẹp nhưng hoàn chỉnh qua toàn bộ lõi thuần. Không đụng thư viện parse,
không đụng đĩa, không đụng mạng — cây tài liệu dựng bằng tay ngay trong test, nên chạy trong mili-giây và tất
định tuyệt đối.

**Blocked by:** 01 — khung dự án.

**Status:** completed

### Chuẩn hoá văn bản

- [x] Chuẩn hoá chạy trên text của **từng khối một**, rồi nối các khối đã chuẩn hoá theo thứ tự đọc — **không**
      nối trước rồi chuẩn hoá sau
- [x] Vị trí ký tự của mỗi chunk là offset tích luỹ trong chuỗi nối đó
- [x] Các phép bắt buộc: chuẩn hoá Unicode về dạng tổ hợp sẵn, chuẩn hoá khoảng trắng, gỡ dấu gạch nối mềm và
      nối lại từ bị ngắt cuối dòng, chuẩn hoá dấu nháy và gạch ngang
- [x] **Không** hạ chữ thường, **không** bỏ dấu — hai phép này huỷ ngữ nghĩa tiếng Việt

### Gán section cha

- [x] Section cha của một khối là heading đang mở gần nhất bao quanh nó
- [x] Ngăn xếp heading: khi gặp heading mới thì **lấy ra** mọi heading có cấp lớn hơn hoặc bằng **trước**, rồi
      mới **đẩy** heading mới vào — lấy phần tử đỉnh sau khi đã làm xong cả hai
- [x] Nội dung trực tiếp của một section là các khối từ ngay sau heading đó tới ngay trước heading con đầu
      tiên, **không** phải toàn bộ subtree
- [x] Heading nhảy cấp không cần chèn section ảo; luật lấy-ra vẫn xử lý đúng
- [x] Heading con có cấp nhỏ hơn cha thì kẹp về ngay dưới cha và bật cờ cảnh báo cấu trúc trên tài liệu
- [x] Cấp thô mà parser trả về được lưu bên cạnh cấp đã chuẩn hoá, để truy vết

### Định danh

- [x] Băm theo nội dung và đường dẫn, **không** băm theo vị trí:
      ```
      section_id = "s_" + blake2b(doc_id | section_path | section_occurrence)
      chunk_id   = "c_" + blake2b(doc_id | parent_section_id | normalized_text | split_index | chunk_occurrence)
      ```
- [x] `section_occurrence` đếm section trùng đường dẫn; `chunk_occurrence` đếm chunk trùng nội dung và chỉ số
      mảnh trong đúng một `parent_section_id`, theo thứ tự đọc
- [x] Định danh tài liệu là tham số truyền vào, **không** được suy ra từ hash nội dung file
- [x] Vị trí ký tự vẫn được lưu để phục vụ trích dẫn, chỉ là không nằm trong phép băm

### Fixture

- [x] Fixture (a): cây có preamble chương và preamble mục, dựng đúng ví dụ đối chiếu §4.5 của
      `doc/B0-ingestion-spec.md` — bốn window `s_2` `s_21` `s_211` `s_212`
- [x] Fixture (d): tài liệu phẳng, không có heading nào

### Bất biến

- [x] **I1** — mỗi chunk thuộc đúng một window: tổng kích thước các window bằng số chunk, và các tập rời nhau
- [x] **I2** — section cha là heading gần nhất: trên fixture (a), khối đầu trỏ về section chương, khối trong
      mục trỏ về section mục, khối trong mục con trỏ về section mục con
- [x] **I3** — window của section chương **chỉ** gồm hai đoạn preamble, **không** gồm khối của các mục con
- [x] **I4** — section không có nội dung trực tiếp thì không sinh window; không có window rỗng nào
- [x] **I5** — chạy hai lần trên cùng cây cho **đúng** tập định danh
- [x] **I6** — thứ tự đọc tăng đơn điệu, khớp thứ tự đọc thủ công của fixture
- [x] **I8** — mọi chunk có văn bản đã chuẩn hoá Unicode
- [x] **I9** — cắt chuỗi đầy đủ theo vị trí ký tự ra đúng nội dung chunk
- [x] **I10** — trên fixture (d), mọi chunk trỏ về section gốc và tạo thành đúng một window
- [x] **I11** — chèn một đoạn vào **đầu** fixture (a), rồi khẳng định mọi định danh của phần **không đổi** vẫn
      **giữ nguyên**. Đây là bài mà công thức gốc trượt; xem ADR 0001
