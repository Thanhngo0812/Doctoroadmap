# v4-15 — A1: đánh giá trên đáp án độc lập, chọn đường A1 cho sản phẩm theo luật định trước

**Nguồn chân lý:**
- [kiểm thử vé 12–14](../../report/kiem-thu-ve-12-13-14-a1-mo-rong-2026-10-08.md) mục 5;
- [vé 14](14-hoc-nhan-tieu-de.md) và các báo cáo `report/v4-14-*`;
- [D-02](D-02-dac-ta-nhan-cau-truc-a1.md) (sách và nhãn).

**Ai:** nhân viên làm pha 0–3 và 5; Claude chạy pha 4 (đánh giá khoá); chủ dự án gán nhãn D-02 và quyết định ·
**Phụ thuộc:** nhãn D-02 (tập phát triển trước); vé 13b nên xong trước pha 4 ·
**Chi phí mô hình:** 0 USD. Phép kiểm trả tiền ở pha 5 là tuỳ chọn, cần duyệt riêng.

**Trạng thái:** soạn 2026-10-08. Thay phần "A1 mở rộng" đang mở của vé 14.

## Vì sao (Claude, 2026-10-08)

- **Chuỗi R đã chững.**
  - 25 vòng trong hai ngày, đo bằng độ khớp với docling trên 19 cuốn đã xem nhiều lần.
  - Tỉ lệ chunk cùng mục lá chỉ từ 0,616 lên 0,642. doc-1 giảm từ 0,618 xuống 0,452, mà doc-1 là kiểu sách sạch chủ dự án nói sẽ dùng.
  - R20–R25 sửa từng trang cụ thể; có nguy cơ khớp riêng tập phát triển.
- **Chưa biết docling sai tới đâu.** Chưa từng đo docling trên đáp án độc lập. Có thể docling cũng chỉ đạt mức đó, khi ấy so "nhẹ với docling" là
  câu hỏi sai.
- **Có hai loại đầu vào.**
  - 16/20 sách mới là bản quét kèm lớp OCR, không có đậm hay font. Bộ đọc nhẹ mất tín hiệu mạnh nhất; mô hình bố cục của docling nhìn ảnh nên
    vẫn chạy.
  - A1 cần nhận ra loại đầu vào và chọn đường theo loại.
- **Tốc độ có giá trị nhưng có trần.** Trên laptop, docling khoảng 11 phút/cuốn; các khâu LLM khoảng 42 phút/cuốn (vé 12). Trong sản phẩm,
  Developer API chạy song song cao nên phần của A1 sẽ lớn hơn.

## Các phương án đem so

Đóng băng S1, S2, S3 (ghi hash mã, cấu hình, mô hình) **trước** pha 4.

| mã | phương án |
|---|---|
| S0 | sản phẩm hiện tại: docling 2.114, bộ đọc chữ pypdfium2, adapter 13, chunker mặc định |
| S1 | bộ đọc nhẹ, cấu hình tốt nhất của chuỗi R; chọn chỉ bằng dữ liệu phát triển |
| S2 | định tuyến: S1 cho PDF gốc, S0 cho bản quét. Có thể thêm cổng của R7: trang có bảng hay hình phức tạp thì dùng S0 |
| S3 | tuỳ chọn: lớp sửa cây mục theo mục lục, đặt trên S0 hoặc S1. Có mục lục điện tử thì dùng; không có thì đọc trang "MỤC LỤC" in sẵn và nối từng dòng mục lục với tiêu đề trong thân sách. 18/20 sách mới có trang mục lục. Không dùng LLM, hợp với seminar |
| S4 | chỉ để đo tốc độ, đầu ra phải y hệt S0: docling chạy song song theo đoạn trang (đã kiểm đầu ra y hệt ở vé 10) |

## Việc cần làm

### Pha 0 — đóng chuỗi R

- Viết một trang tổng kết R1–R25:
  - phần đã vào sản phẩm (giữ chữ lặp, nguồn chú thích hình, `declared-v1`);
  - cấu hình S1 tốt nhất, kèm hash;
  - các lỗi còn mở.
- Dừng sửa theo từng trang trên 19 cuốn cũ. Cập nhật trạng thái vé 14 trỏ sang vé này.

### Pha 1 — xuất phiếu D-02 và kiểm định dạng

- Viết script `scripts/a1-d02/` xuất `dong/`, `trang/`, `muc_luc_dien_tu` và trang mẫu L2 theo [D-02](D-02-dac-ta-nhan-cau-truc-a1.md).
  - Mã dòng lấy từ dòng pypdfium2. Dùng lại `page_lines` và `describe` của bộ đọc nhẹ, để mã dòng khớp với dòng mà S1 dùng.
- Viết script kiểm định dạng nhãn trả về.
- **Test:**
  - mã dòng ổn định giữa hai lần chạy;
  - mỗi ký tự có chữ của trang thuộc đúng một dòng;
  - chọn trang L2 tất định;
  - script kiểm bắt được nhãn sai mã dòng, `cha` sai cấp, trang L2 thiếu dòng. Các test này phải đỏ trước khi viết luật kiểm.
- Chạy trên 6 cuốn phát triển. Với tập khoá, bàn giao lệnh cho Claude chạy; **nhân viên không mở PDF hay đầu ra của tập khoá**.

### Pha 2 — bộ chấm, chạy trên tập phát triển

- **Căn đầu ra về mã dòng chuẩn theo trang và bbox:**
  - nút docling có trang và bbox;
  - dòng của bộ đọc nhẹ có dòng nguồn.

  Sau khi căn, mỗi mã dòng có vai trò và đường dẫn mục theo từng hệ.
- **Chỉ số theo từng cuốn.** Báo trung vị và cuốn tệ nhất, tách PDF gốc với bản quét.

| mã | chỉ số |
|---|---|
| M1 | P/R/F1 tiêu đề. Khớp khi tiêu đề của hệ phủ ít nhất một nửa số mã dòng của tiêu đề vàng, cùng trang |
| M2 | độ đúng của cha trên các tiêu đề khớp |
| **M3 (chính)** | độ đúng gán mục: tỉ lệ ký tự thân bài có mục sâu nhất trùng với vàng. Thân bài lấy theo L2 nếu có; nếu không thì là mọi dòng không phải đầu trang, chân trang |
| M4 | trên trang L2: P/R theo vai trò (bỏ đầu trang, chân trang và số trang; công thức; bảng; chú thích hình; tiêu đề) và Kendall tau của thứ tự đọc |
| M5 | giây/trang từ PDF tới chunk, ba lần chạy lúc máy rảnh; RAM đỉnh |
| M6 | tỉ lệ chunk cùng mục lá, tính lại theo vàng thay cho docling |

- Báo trên tập phát triển cho S0, S1, S2 (và S3 nếu làm). **Báo cả S0 so với vàng**: đây là lần đầu biết docling sai tới đâu.
- **Test chỉ số** bằng cây nhỏ tự dựng:
  - hệ hoàn hảo cho 1,0;
  - lệch một cấp chỉ làm giảm M2;
  - thiếu một tiêu đề làm giảm M1 và M3 đúng lượng tính tay;
  - giữ đầu trang làm giảm M4.

### Pha 3 — phát triển có kiểm soát trên tập phát triển

- Được cải tiến S1, S2, S3 bằng nhãn vàng phát triển.
  - Mỗi thay đổi đo trên cả 6 cuốn vàng phát triển và 19 cuốn bạc cũ.
  - Báo cả số giảm.
  - Không viết luật theo mã sách.
- **Bộ định tuyến** nhận ra PDF gốc, bản quét kèm OCR, và trang không có chữ, theo tín hiệu của chính PDF: chế độ hiển thị chữ 3 (ẩn),
  `GlyphLessFont`, ảnh phủ kín trang. Kiểm trên đủ 39 PDF đã biết loại.
- **Hạn mức:** tối đa 3 ngày làm việc, hoặc khi M3 trên tập phát triển không tăng qua hai vòng liên tiếp, thì đóng băng.

### Pha 4 — đánh giá khoá (Claude chạy một lần)

- Chạy trên tập khoá D-02 với cấu hình đóng băng và hash đã ghi. Claude công bố báo cáo.
- **Luật quyết định, ghi trước khi chạy.**
  - **PDF gốc:** S1 hoặc S2 thành mặc định nếu đạt đủ bốn điều:
    - M3 trung vị không thấp hơn S0 quá 0,02;
    - không cuốn nào thấp hơn S0 quá 0,10;
    - M1 F1 trung vị không thấp hơn S0 quá 0,03;
    - nhanh hơn S0 ít nhất 10 lần từ đầu tới cuối.

    Không đạt thì giữ S0 cho PDF gốc và đi theo hướng tăng tốc S4.
  - **S3:** nhận nếu M3 trung vị tăng ít nhất 0,03 và không cuốn nào giảm quá 0,05.
  - **Bản quét:** giữ S0, trừ khi phương án khác đạt cùng luật.
  - **Số cuốn:** tập khoá PDF gốc cần ít nhất 8 cuốn mới quyết định; với 4 cuốn hiện có, kết quả chỉ để tham khảo.

### Pha 5 — tích hợp theo quyết định

- **Cờ chọn đường:** `ingest --a1 {docling,nhe,tu-dong}`. Định danh đường A1 nằm trong khoá cache parse, như vé 09.
  - Mặc định chỉ đổi khi pha 4 đạt, và sau khi báo chủ dự án.
  - Tài liệu cũ chạy lại theo cờ đã khoá, không đổi.
- **Tốc độ S0** (nếu giữ S0): đo song song theo đoạn trang trên máy triển khai khi có; trong lúc chờ, báo số trên laptop.
- **Tuỳ chọn, cần duyệt chi** và quyền gửi sách D-02 lên Gemini: chạy A2 → A9'' trên 2 cuốn khoá với hai đường A1 rồi so:
  - vai trò vùng;
  - số khái niệm được dạy;
  - tên module.

  Ước khoảng 6–8 USD.

## Nghiệm thu

- Pha 0: trang tổng kết, cấu hình S1 đóng băng kèm hash.
- Pha 1: script xuất phiếu, script kiểm định dạng, test đỏ rồi xanh; phiếu của 6 cuốn phát triển.
- Pha 2: bộ chấm, test chỉ số, báo cáo tập phát triển có S0 so với vàng.
- Pha 4: báo cáo của Claude kết luận theo luật quyết định, kèm số từng cuốn.
- Pha 5: chỉ khi pha 4 đạt. Có test khoá cache; tài liệu cũ không đổi khoá.
- Không dùng LLM trong A1. Không mở `document-data/test/`. Nhân viên không mở tập khoá D-02.
