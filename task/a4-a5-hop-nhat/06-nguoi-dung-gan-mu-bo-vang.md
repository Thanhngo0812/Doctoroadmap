# 06 — [Người dùng] Gán mù bộ vàng A4

**What to build:** Người dùng mở bảng gán do ticket 05 sinh ra, gán mù 416 mục (ước chừng 1,5–2 giờ, mỗi mục
15–20 giây), xuất JSON, và đóng băng thành fixture bộ vàng A4. **Không phải việc cho agent** — ticket này tồn tại để
cạnh chặn tới lần chạy thật đầu tiên (14) hiện rõ.

## Vì sao người dùng gán, không phải nhân viên

Nhân viên là người viết A4 nên không mù được với kết quả của nó. Gán mù là bắt buộc: sửa đầu ra thành bộ vàng thì
đo trên chính thứ dẫn xuất từ đầu ra — vòng luẩn quẩn, con số đẹp một cách vô nghĩa (D14 spec A3).

Nhãn tay ở phụ lục A của báo cáo đóng vai người gán thứ hai, để đo độ đồng thuận giữa hai người.

**Blocked by:** 05 — Bảng gán bộ vàng `a4-gold-sheet`

**Status:** done — Claude gán thay theo xác nhận của chủ dự án

**Xác nhận tiếp của chủ dự án:** dùng nguyên bộ nhãn này để đánh giá và chạy A4/A5.
Loader đã hỗ trợ bảng cũ có kiểm chứng provenance; không sửa nhãn hoặc thời gian gán.
Không yêu cầu gán lại theo bảng v2. Vẫn ghi rõ đây là nhãn AI, không phải đánh giá người độc lập.

**Bàn giao 2026-09-11:** bảng `artifacts/a4-gold.html` đã có **416 mục**, chưa gán.
Không có lời gọi mô hình phán A4/A5 thật nào. Đợi người dùng gán và xuất JSON; chưa ghi thời gian
gán hoặc tự đặt nhãn. [Trạng thái chi tiết](../../feedback/F18-a4-a5-hop-nhat.md).

**Gán 2026-09-11 — Claude gán thay chủ dự án, theo yêu cầu trực tiếp.** Người gán không phải người, và không độc lập
với thiết kế: Claude viết rubric, spec và phụ lục A. Bộ vàng này đo mô hình khớp **cách Claude đọc rubric**, chưa phải
cách chủ dự án đọc.

- File `artifacts/a4-gold.json` (gitignore); bản đóng băng `tests/fixtures/a4/gold-blind.json`, trùng từng byte.
  Mục nào có lý do ngắn thì mang trường `note`; bộ nạp bỏ qua trường này.
- Thời gian thật theo đồng hồ máy (+07:00): bắt đầu 16:22:16, gán xong 16:37:56, xuất 16:38:45. Khoảng 16 phút,
  không so được với 1,5–2 giờ của một người.
- Phân bố: 47 *cùng* · 47 *cha–con* · 164 *liên quan* · 94 *khác* · 4 *không chắc*. 60 nhóm tên đều là *một thực thể*,
  không có đồng âm: tầng gộp theo tên đúng 60/60 trên bộ này.
- 47/47 cặp *cùng* nằm trong đồ thị đề cử; 0/100 cặp ngẫu nhiên ngoài đồ thị là *cùng*. Mẫu 100 cặp chỉ loại được tỉ lệ
  bỏ sót lớn (quy tắc ba: dưới khoảng 3% số cặp ngoài đồ thị), không chứng minh đề cử đủ.
- Phụ lục A **không** làm được người gán thứ hai, vì cùng một người gán. 38/53 mục bạc trùng mục của bảng. Khớp chính xác
  29/38 (κ 0,554), nhưng 8/9 chỗ lệch là do script chuyển đổi: cặp đối nghịch/đối xứng thành *khác*, còn cha–con không
  có chiều thành *không chắc*. Trên trục gộp (*cùng* hay không) khớp 37/38. Lệch thật duy nhất là mục #5
  `Branching`/`Branching strategy`: phụ lục để mơ hồ, bộ vàng xếp *cùng* vì cả hai bằng chứng cùng tả quy chuẩn phân
  nhánh của nhóm.

Quy ước đã dùng, để người soát phản bác:

- *Cùng*: khác nhau chỉ ở tiền tố (Bài toán, Vấn đề, Giao thức, Kỹ thuật), hậu tố ký hiệu, chính tả (tỷ/tỉ), ngôn ngữ,
  tên bị cắt cụt; một tên với phương trình của nó; hai tên mà tài liệu tự đồng nhất ("kiểu (lớp) mô hình H").
- *Cha–con*: trường hợp riêng dưới tên chung (khoảng ước lượng của σ² dưới khoảng ước lượng), loại con (Gaussian NB
  dưới NB), thao tác con của tiền xử lý dữ liệu. Một **bước** của thủ tục thì là *liên quan*, không phải con.
- *Không chắc* (4 mục: #78, #132, #202, #260): phương pháp và sản phẩm của nó (Ước lượng X / Khoảng ước lượng của X);
  Công thức Bayes và dạng tổng quát.
- *Liên quan*: anh em, đối nghịch, đối xứng, thống kê và tham số tương ứng, các bước kế nhau.
- Ranh giới *liên quan*/*khác* không vào chỉ số chấm mô hình nào, chỉ vào độ đồng thuận. Ranh giới *liên quan*/*cha–con*
  thì có: nó vào `subtype_incorrect`.

- [x] Gán **trước** mọi lần chạy mô hình của A4 trên các tài liệu này, và không mở artifact `canonical` có quyết định
      mô hình nào trước khi gán xong. *Artifact canonical lúc gán chỉ có stage `names`/`nominations`.*
- [x] Mọi mục đều có nhãn. Phân vân thì chọn *không chắc*, không đoán.
- [ ] File JSON qua bộ nạp của ticket 05 không lỗi; đóng băng vào thư mục fixture và commit. *Qua `load_gold(...,
      require_complete=True)` và đã đóng băng; **chưa commit**, chờ chủ dự án.*
- [x] Ghi thời gian gán **thật** vào ticket, không ước lượng.
- [x] *(Đề xuất, không chặn 14)* Chủ dự án gán mù khoảng 50 mục rút ngẫu nhiên, bỏ các mục trùng phụ lục A, để có
      độ đồng thuận người–Claude thật.
