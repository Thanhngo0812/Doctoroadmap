# 03 — Luật cắt đầy đủ: block dài, block ngắn, bảng và caption

**What to build:** Mở rộng đường đi hẹp của ticket 02 thành luật cắt đầy đủ. Khối dài quá ngưỡng được cắt theo
ranh giới câu mà không cắt ngang câu nào; khối ngắn được giữ nguyên chứ không bị gộp; bảng ra một chunk duy
nhất kèm caption đi cùng. Kết thúc ticket, mọi luật cắt của spec đã có hiệu lực và đoạn trích dẫn nào lấy ra
cũng đọc được thành câu hoàn chỉnh.

Vẫn ở seam thuần — cây dựng bằng tay, không đụng thư viện parse.

**Blocked by:** 02 — cây section và định danh.

**Status:** completed

### Luật cắt

- [x] Khối vượt ngưỡng độ dài được cắt theo ranh giới câu, các mảnh chồng lấn nhau một câu
- [x] Các mảnh **giữ nguyên** section cha của khối gốc
- [x] Chỉ số mảnh tăng dần từ không, và nằm trong khoá băm định danh
- [x] Khối ngắn dưới ngưỡng được **giữ nguyên, không gộp** với khối bên cạnh — gộp sẽ phá vỡ nguyên tắc một
      khối là một đơn vị bằng chứng
- [x] Không bao giờ gộp hai khối khác section cha, kể cả khi cả hai đều ngắn
- [x] Bảng ra đúng một chunk, chuyển thành văn bản dạng bảng markdown, giữ quan hệ hàng cột
- [x] Caption của bảng và hình đi kèm khối tương ứng ở một trường ngữ cảnh riêng, **không** tính vào vị trí ký tự

> Trường ngữ cảnh cho caption có trong luật cắt của `doc/B0-ingestion-spec.md` §5.1 nhưng **thiếu trong bảng
> schema §6.2** của chính tài liệu đó. Spec mới bổ sung nó — đây không phải phát minh thêm.

### Đếm token và tách câu

- [x] Bộ đếm token dùng tokenizer SentencePiece dòng Gemma, nạp **cục bộ**, ghim phiên bản, file được vendor
      vào repo
- [x] **Không** có lời gọi mạng nào trong đường chạy cắt chunk — đếm token qua API biến mỗi khối thành một
      vòng gọi mạng và phá tính tất định của định danh
- [x] Bộ tách câu tiếng Việt dùng biểu thức chính quy cùng danh sách viết tắt tự quản, xử lý đúng `TS.` `GS.`
      `PGS.` `ThS.` `TP.` và số thập phân
- [x] Cả hai nằm sau giao diện trừu tượng khai báo ở **tầng miền**, không phải tầng ứng dụng — logic cắt chunk
      nằm trong miền và không được import ngược lên trên
- [x] Định danh tokenizer được ghi lại để biết khi nào phải cắt lại chunk

### Fixture

- [x] Fixture (c): tài liệu có heading nhảy cấp, ví dụ cấp một xuống thẳng cấp ba
- [x] Fixture (f): tài liệu có bảng kèm caption
- [x] Một fixture có khối dài vượt ngưỡng, để bài cắt thật sự chạy

### Bất biến

- [x] **I7** — mọi chunk kết thúc ở ranh giới câu hoặc hết khối; không chunk nào cắt ngang câu
- [x] **I12** — đổi ngưỡng độ dài khối từ 512 xuống 384, rồi khẳng định **chỉ** định danh của khối thật sự bị
      cắt lại mới đổi. Khối ngắn hơn ngưỡng không đi qua bước cắt nên định danh của chúng phải miễn nhiễm
- [x] I9 vẫn đúng sau khi có cắt mảnh: cắt chuỗi đầy đủ theo vị trí vẫn ra đúng nội dung từng mảnh
- [x] Toàn bộ bất biến của ticket 02 vẫn xanh
