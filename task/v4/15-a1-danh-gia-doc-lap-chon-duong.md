# v4-15 — A1: đánh giá trên đáp án độc lập, chọn đường A1 cho sản phẩm theo luật định trước

**Nguồn chân lý:**
- [kiểm thử vé 12–14](../../report/kiem-thu-ve-12-13-14-a1-mo-rong-2026-10-08.md) mục 5;
- [vé 14](14-hoc-nhan-tieu-de.md) và các báo cáo `report/v4-14-*`;
- [D-02](D-02-dac-ta-nhan-cau-truc-a1.md) (sách và nhãn).

**Ai:** nhân viên làm pha 0, 1, 2, 3 và 5; agentic gán nhãn và chủ dự án duyệt ở pha 1b; Claude chạy pha 4 (đánh giá khoá); chủ dự án quyết định ·
**Phụ thuộc:** nhãn D-02 (tập phát triển trước); vé 13b nên xong trước pha 4 ·
**Chi phí mô hình:** 0 USD. Phép kiểm trả tiền ở pha 5 là tuỳ chọn, cần duyệt riêng.

**Chủ dự án chốt 2026-10-10:**
- Đổi mặc định A1 sang bộ đọc nhẹ R2 ngay, không chờ pha 4.
- Đây là đánh đổi tốc độ và nguồn lực. Trên tập phát triển R2 trượt c1 (M3 thấp hơn 0,065) và c3 (M1 thấp hơn 0,043) của luật pha 4, nên không ghi là đạt.
- Pha 4 hoãn; tập khoá giữ niêm phong cho một lần đánh giá sau.
- Pha 5 và nghiên cứu cây cha–con chuyển sang [vé 16](16-a1-bo-doc-nhe-mac-dinh-va-cay-cha-con.md).
- Kiểm thử pha 0–3: [báo cáo](../../report/kiem-thu-ve-15-pha-0-3-2026-10-10.md).

**Cập nhật mới nhất — 2026-10-09:** pha 0–1 hoàn tất phần nhân viên; đã nhận 1.719 nhãn L1/48 trang L2 nhưng chưa duyệt ngữ nghĩa toàn bộ. Pha 2 đủ 54/54 fresh runs và đã hoàn tất bảy lượt M5 bù riêng; mỗi hệ/cuốn có ba lượt CPU trước chạy dưới 20%, không ghi đè kết quả cũ. Pha 3 đã chấm bốn vòng trên đủ sáu sách D-02 và 19 sách bạc, R3/R4 không tăng M3 nên dừng theo luật, đóng băng **R2-native-only** (M3 trung vị 0,7995 so với R25 0,7666). Không nhận mô hình D-02 mới hoặc S3. 60 test xanh, hash/smoke suy luận R2 và audit M4 đã kiểm. Router mới 19/19 sách cũ và test tổng hợp đạt; **còn người giữ tập khoá kiểm 43/43**, nhân viên không mở 24 PDF mới/đầu ra từng cuốn. Chưa ghi toàn pha 3 nghiệm thu, chưa làm pha 4–5, mặc định sản phẩm vẫn S0. [Baseline](../../report/v4-15-pha-2-ket-qua-2026-10-09.md), [chốt phát triển/suy giảm](../../report/v4-15-pha-3-chot-va-ban-giao-2026-10-09.md), [lệnh bàn giao](../../report/v4-15-ban-giao-nguoi-giu-tap-khoa-2026-10-09.md), [hash ứng viên](../../report/v4-15-pha-3-dong-bang-2026-10-09.json). Các dòng 2026-10-08 bên dưới là lịch sử.

**Trạng thái (2026-10-08):** pha 0 đã đóng chuỗi R và ghi hash S1; pha 1 đủ phiếu sáu sách. Pha 1b nhận đủ 1.719 tiêu đề và 48 trang L2 (đã loại dòng trống khi đếm); chủ dự án đã duyệt ưu tiên cha logic, năm chương d01-02 được hiệu chỉnh riêng, không ghi đè nhãn agentic. Pha 2: kho cũ lưu 12 lần S1/S2 rồi dừng do wrapper S0 gọi sai constructor; đã sửa với test đỏ/xanh. Kho mới `tmp/a1-v415/phase2b-20261008` chạy lại 54 lần đo, S0 đã vào parse thật, có CPU/RAM; chưa hoàn tất. Pha 3 định tuyến đúng 19/19 PDF cũ, còn 20 PDF mới do người giữ tập khoá kiểm; chưa đổi sản phẩm hoặc làm pha 4–5. Chi tiết: [sửa cha và lượt đo](../../report/v4-15-sua-cha-va-chay-pha-2-2026-10-08.md), [tiếp nhận 1b](../../report/v4-15-tiep-nhan-nhan-1b-2026-10-08.md), [giao thức pha 3](../../report/v4-15-giao-thuc-pha-3-2026-10-08.md). Thay phần "A1 mở rộng" đang mở của vé 14.

**Kiểm cuối 2026-10-09:** bảy lượt M5 bù đã hoàn tất, mỗi hệ/cuốn đủ ba lượt CPU trước chạy dưới 20% (không chứng minh rảnh suốt pipeline). Audit M4 loại biên sửa cách đọc `evaluation_excluded`, giữ số gốc riêng; test đột biến bắt được predicate sai. 60 test xanh; CLI suy luận R2 chạy PDF phát triển thật và tiêu đề/chunk khớp kết quả chọn. Không còn pipeline đo nào của đợt này. [Audit M4/M5](../../report/v4-15-m5-bo-sung-va-m4-loai-bien-2026-10-09.md). Còn cổng router 43/43 do người giữ tập khoá chạy trước nghiệm thu toàn pha 3.

**Tạm dừng theo chủ dự án, cuối giờ làm 2026-10-08:** đã lưu 5/54 lượt pha 2 (9,26%); d01-15 S0 lần 1 chưa hoàn tất. Đã xác nhận không còn tiến trình đo và gỡ lock cũ, giữ mọi checkpoint/log. Chờ chủ dự án mở máy và yêu cầu chạy tiếp; không tự khởi động lại.

**Tiếp tục theo chủ dự án, 2026-10-09:** đã xác nhận không có pipeline trùng, chạy lại đúng baseline từ năm checkpoint, bắt đầu d01-15 S0 lần 1. Giữ hash mã/nhãn cũ, không đổi runtime giữa phép đo. Đã đọc yêu cầu mới của pha 3 và chẩn đoán tiêu đề; đồng bộ giao thức, bổ sung manifest đủ 43 cuốn theo tên tệp (không mở PDF khoá). Router baseline cũ còn nhánh S0 cho bản quét; chỉ dùng làm mốc cũ, chưa nhận là S2 cuối theo yêu cầu từ chối bản quét.

## Vì sao (Claude, 2026-10-08)

**Tiếp tục sau mất điện, 2026-10-09:** checkpoint giữ 37/54 lượt (68,52%). Đã kiểm không còn pipeline và gỡ riêng lock cũ PID 28516; d01-06 S0 lần 3 chưa có thư mục kết quả. Theo yêu cầu chủ dự án, chạy tiếp đúng lệnh/kho baseline, không đổi mã hoặc cấu hình; lượt bị ngắt chạy lại, 37 lượt hoàn chỉnh tái dùng. Chi API 0 USD.

- **Chuỗi R đã chững.**
  - 25 vòng trong hai ngày, đo bằng độ khớp với docling trên 19 cuốn đã xem nhiều lần.
  - Tỉ lệ chunk cùng mục lá chỉ từ 0,616 lên 0,642. doc-1 giảm từ 0,618 xuống 0,452, mà doc-1 là kiểu sách sạch chủ dự án nói sẽ dùng.
  - R20–R25 sửa từng trang cụ thể; có nguy cơ khớp riêng tập phát triển.
- **Chưa biết docling sai tới đâu.** Chưa từng đo docling trên đáp án độc lập. Có thể docling cũng chỉ đạt mức đó, khi ấy so "nhẹ với docling" là
  câu hỏi sai.
- **Phạm vi chỉ có PDF gốc** (chủ dự án chốt; ghi vào vé ngày 2026-10-08, trước khi có số của tập khoá).
  - 16/20 sách mới là bản quét kèm lớp OCR, không có đậm hay font. Bộ đọc nhẹ mất tín hiệu mạnh nhất ở loại này.
  - Bản quét nằm ngoài sản phẩm. A1 chỉ cần nhận ra bản quét để từ chối, không cần chọn đường cho nó.
  - Hướng đi là bộ đọc nhẹ thay docling cho PDF gốc. Thay hay không vẫn theo luật pha 4.
- **Tốc độ có giá trị nhưng có trần.** Trên laptop, docling khoảng 11 phút/cuốn; các khâu LLM khoảng 42 phút/cuốn (vé 12). Trong sản phẩm,
  Developer API chạy song song cao nên phần của A1 sẽ lớn hơn.

## Các phương án đem so

Đóng băng S1, S2, S3 (ghi hash mã, cấu hình, mô hình) **trước** pha 4.

| mã | phương án |
|---|---|
| S0 | sản phẩm hiện tại: docling 2.114, bộ đọc chữ pypdfium2, adapter 13, chunker mặc định |
| S1 | bộ đọc nhẹ, cấu hình tốt nhất của chuỗi R; chọn chỉ bằng dữ liệu phát triển |
| S2 | S1 kèm bộ định tuyến: PDF gốc đi S1, bản quét bị từ chối. Có thể thêm cổng của R7: trang có bảng hay hình phức tạp thì dùng S0 |
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
- Tên tệp xuất ra theo đúng [hướng dẫn gán D-02](../../report/huong-dan-agentic-gan-nhan-d02.md) mục 1: `dong/`, `trang/`,
  `chon-trang-mau/`, `muc_luc_dien_tu/`.
- Viết script kiểm `kiem_nhan_d02.py`.
  - Chạy được bằng lệnh `python kiem_nhan_d02.py --sach <sach> --thu-muc <dir>`, chỉ dùng thư viện chuẩn, vì agentic chạy nó ở máy khác.
  - Kiểm đủ luật ở mục 2.6 và 3.3 của hướng dẫn, kể cả luật khớp giữa vai trò `tieu_de` của trang mẫu và cây mục.
  - In "ĐẠT" khi không có lỗi.
- **Test:**
  - mã dòng ổn định giữa hai lần chạy;
  - mỗi ký tự có chữ của trang thuộc đúng một dòng;
  - chọn trang L2 tất định;
  - script kiểm bắt được nhãn sai mã dòng, `cha` sai cấp, trang L2 thiếu dòng. Các test này phải đỏ trước khi viết luật kiểm.
- Chạy trên 6 cuốn phát triển. Với tập khoá, bàn giao lệnh cho Claude chạy; **nhân viên không mở PDF hay đầu ra của tập khoá**.

### Pha 1b — agentic gán nhãn, chủ dự án duyệt (không phải việc của nhân viên)

Pha 2–4 cần đáp án. Đáp án do agentic gán theo [D-02](D-02-dac-ta-nhan-cau-truc-a1.md), mục "Quyền và thứ tự làm".

- **Đưa agentic:** chỉ [hướng dẫn gán D-02](../../report/huong-dan-agentic-gan-nhan-d02.md), thư mục phiếu của từng cuốn và
  `kiem_nhan_d02.py`. Không đưa đặc tả D-02, vé này, hay đầu ra của docling và bộ đọc nhẹ.
- **Agentic làm, cho từng cuốn:**
  - L1, cây mục: mỗi tiêu đề một dòng gồm mã dòng, `cap`, `cha`;
  - L2, 8 trang mẫu: vai trò và thứ tự đọc của mọi dòng. Bắt buộc với tập khoá. Với tập phát triển, D-02 để tuỳ chọn, nhưng nên làm để M4
    được thử trước pha 4;
  - tự chạy `kiem_nhan_d02.py` tới khi in "ĐẠT" rồi mới nộp.
- **Thứ tự:**
  1. Đợt 1: L1 của 6 cuốn phát triển, xong trước pha 2 để nhân viên có đáp án viết bộ chấm.
  2. Đợt 2: L1 và L2 của 8 cuốn khoá gốc; bản quét không gán nhãn. Claude xuất phiếu tập khoá và giao chủ dự án; nhãn tập khoá nộp thẳng cho
     Claude, nhân viên không thấy.
- **Chủ dự án duyệt mẫu** theo D-02, mục "Người duyệt": sửa ghi vào `duyet/<sach>.jsonl`. Phần người sửa là vàng, phần còn lại là bạc.
- **Điều kiện trước:** chủ dự án xác nhận quyền dùng 8 cuốn khoá gốc và dịch vụ agentic, vì agentic gửi chữ và ảnh trang ra dịch vụ ngoài.

### Pha 2 — bộ chấm, chạy trên tập phát triển

- **Căn đầu ra về mã dòng chuẩn theo trang và bbox:**
  - nút docling có trang và bbox;
  - dòng của bộ đọc nhẹ có dòng nguồn.

  Sau khi căn, mỗi mã dòng có vai trò và đường dẫn mục theo từng hệ.
- **Chỉ số theo từng cuốn.** Báo trung vị và cuốn tệ nhất. Chỉ chấm PDF gốc.

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
  `GlyphLessFont`, ảnh phủ kín trang. Bản quét bị từ chối.
  - Kiểm trên đủ 43 PDF đã biết loại: 27 gốc, 16 quét.
  - Manifest `report/v4-15-router-custodian-39-2026-10-08.json` mới có 39 cuốn, thiếu 4 cuốn khoá gốc:
    `new-doc-2/toan-hoc/dai-so-tuyen-tinh-bui-xuan-dieu-hust.pdf`, `new-doc-2/toan-hoc/giai-tich-1-le-chi-ngoc-hust.pdf`,
    `new-doc-3/kinh-te-vi-mo-1-ptit.pdf`, `new-doc-3/luat-kinh-doanh-ptit.pdf` (đều dưới `document-data/`). Nhân viên thêm theo tên tệp,
    không mở tệp.
- **Hạn mức:** tối đa 3 ngày làm việc, hoặc khi M3 trên tập phát triển không tăng qua hai vòng liên tiếp, thì đóng băng.
- **Điểm bắt đầu:** [chẩn đoán lỗi tiêu đề của bộ đọc nhẹ](../../report/nghien-cuu-bo-doc-nhe-loi-tieu-de-2026-10-08.md), mục 5:
  chuẩn hoá cờ đậm theo cuốn, ngữ pháp đánh số, cây cha–con từ đánh số và mục lục, học trên nhãn D-02 theo fold bỏ chính cuốn.

### Pha 4 — đánh giá khoá (Claude chạy một lần)

- Chạy trên tập khoá D-02 với cấu hình đóng băng và hash đã ghi. Claude công bố báo cáo.
- **Luật quyết định, ghi trước khi chạy.** Ngày 2026-10-08 sửa luật bản quét và dòng số cuốn theo phạm vi PDF gốc, trước khi có số của
  tập khoá; luật cho PDF gốc giữ nguyên.
  - **PDF gốc:** S1 hoặc S2 thành mặc định nếu đạt đủ bốn điều:
    - M3 trung vị không thấp hơn S0 quá 0,02;
    - không cuốn nào thấp hơn S0 quá 0,10;
    - M1 F1 trung vị không thấp hơn S0 quá 0,03;
    - nhanh hơn S0 ít nhất 10 lần từ đầu tới cuối.

    Không đạt thì giữ S0 cho PDF gốc và đi theo hướng tăng tốc S4.
  - **S3:** nhận nếu M3 trung vị tăng ít nhất 0,03 và không cuốn nào giảm quá 0,05.
  - **Bản quét:** ngoài phạm vi, không chấm chất lượng. Bộ định tuyến đóng băng phải đúng trên cả 43 PDF đã biết loại; từ chối nhầm một PDF
    gốc là lỗi chặn.
  - **Số cuốn:** tập khoá PDF gốc có 8 cuốn, đủ ngưỡng 8 cuốn để quyết định.

### Pha 5 — tích hợp theo quyết định

- **Cờ chọn đường:** `ingest --a1 {docling,nhe,tu-dong}`. Định danh đường A1 nằm trong khoá cache parse, như vé 09.
  - Mặc định chỉ đổi khi pha 4 đạt, và sau khi báo chủ dự án.
  - Tài liệu cũ chạy lại theo cờ đã khoá, không đổi.
- **Cổng phạm vi**, làm bất kể kết quả pha 4, áp cho mọi đường A1: ingest gặp bản quét thì dừng trước A2, báo rõ tệp là bản quét và nằm
  ngoài phạm vi. Test: PDF tổng hợp (chữ ẩn, `GlyphLessFont`, ảnh phủ kín trang) bị từ chối; PDF gốc đi tiếp.
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
- Pha 5: cổng phạm vi bản quét có test, làm bất kể kết quả pha 4. Phần cờ chọn đường chỉ làm khi pha 4 đạt; có test khoá cache; tài liệu cũ
  không đổi khoá.
- Không dùng LLM trong A1. Không mở `document-data/test/`. Nhân viên không mở tập khoá D-02.
