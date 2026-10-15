# D-04b — Hướng dẫn gán nhãn cạnh ngược cho agentic, kèm thử gán

**Nguồn chân lý:** [đặc tả D-04](D-04-dac-ta-nhan-canh-nguoc.md), bước 3; mẫu [hướng dẫn agentic D-01](../../report/huong-dan-agentic-gan-nhan-d01.md).
**Ai:** Claude · **Chi phí mô hình:** 0 USD · **Chặn bởi:** D-04a · **Trạng thái:** xong 2026-10-15

## Vì sao

Agentic không được đọc đặc tả D-04, vì mục "Cách Claude dùng nhãn" nêu các luật đang được đo. Agentic cần một hướng dẫn riêng, tự đủ. D-01 cho thấy
hướng dẫn chưa thử trước sinh lỗi có hệ thống (căn cứ là câu định nghĩa X), phải gán lại 240 phiếu.

## Cần làm

- Viết hướng dẫn gán cho agentic theo mẫu D-01. Nội dung gồm: câu hỏi, bảy nhãn kèm phép thử, luật chung, định dạng trả về, cách chạy bộ kiểm định
  dạng, cách chia lô cho subagent, và quy ước hai lượt độc lập. Không nêu luật E8, nguồn cặp hay hệ đề xuất.
- Ví dụ trong hướng dẫn lấy từ phiếu **không** nằm trong bộ phiếu giao đi, hoặc viết ví dụ giả.
- Claude tự gán thử 30 phiếu: 10 doc-4, 10 nguồn 2 cùng chương, 10 nguồn 2 khác chương. Ghi chỗ mơ hồ giữa các nhãn (nhất là `can_hoc_truoc`,
  `du_tai_cho`, `kien_thuc_nen`), rồi sửa hướng dẫn. 30 nhãn thử này không dùng để đo.
- Gói giao chủ dự án gồm phiếu, hướng dẫn và bộ kiểm định dạng. Không có khoá.

## Nghiệm thu

- [x] Hướng dẫn tự đủ: một agent chỉ đọc hướng dẫn và phiếu là gán được, không cần đặc tả.
- [x] Không ví dụ nào trùng cặp (X, Y) của phiếu giao đi; kiểm bằng script, không bằng mắt.
- [x] 30 nhãn thử qua được bộ kiểm định dạng. Ghi chép thử gán liệt kê từng chỗ đã sửa trong hướng dẫn.
- [x] Gói giao không chứa khoá, đặc tả hay báo cáo vòng 2.

## Kết quả (Claude, 2026-10-15)

- Hướng dẫn: [huong-dan-agentic-gan-nhan-d04.md](../../report/huong-dan-agentic-gan-nhan-d04.md), bản 1.0.
- Bộ kiểm định dạng thêm `--mot-phan` (kiểm từng lô khi đang gán dở), có test.
- Gói giao ở `tmp/d04-goi-giao/`, gồm đúng ba tệp: phiếu, hướng dẫn, bộ kiểm. Không có khoá.
- **Thử gán 30 phiếu** (10 doc-4, 10 nguồn 2 cùng chương, 10 nguồn 2 khác chương; nhãn ở `tmp/d04-thu-30-nhan.jsonl`, qua bộ kiểm; không dùng
  để đo): `can_hoc_truoc` 0, `du_tai_cho` 5, `kien_thuc_nen` 7, `nghia_khac` 8, `khong_tien_quyet` 8, `nguoc` 2.
- **Những chỗ mơ hồ đã đưa vào hướng dẫn:**
  - Bộ nhãn không có "công cụ": X chỉ ở ví dụ hay câu áp dụng → `khong_tien_quyet` (ca 1).
  - Đoạn văn Y không gọi tên X → `khong_tien_quyet`, trừ khi mô tả rõ X (ca 2).
  - Từ rất chung: tách nghĩa thường (`kien_thuc_nen`) khỏi nghĩa hẹp mà đoạn văn X định nghĩa (`nghia_khac`) (ca 3).
  - Trùng chữ khác nghĩa, một phần của thuật ngữ khác, tính từ, bí danh sai → `nghia_khac` (ca 4).
  - Từ khung định nghĩa ("là một … dùng để chỉ") → `kien_thuc_nen` (ca 5).
  - Ranh giới `du_tai_cho` / `kien_thuc_nen`: `du_tai_cho` đòi một câu cụ thể giải thích X (ca 8).
  - Thuật ngữ đọc theo chữ là hiểu (ca 9).
  - Trùng khái niệm → `khong_tien_quyet`, `ly_do` mở đầu "trùng khái niệm" (quy trình, bước 3).
  - Phiếu lặp: gán độc lập (mục 8).
- **Ví dụ không trùng phiếu:** kiểm bằng script. Không cặp (X, Y) ví dụ nào trùng cặp phiếu. Các tên dẫn trong ca khó ban đầu lấy từ phiếu thử
  ("Nhân tố chủ quan", "Liệt kê", "hình biểu diễn"…) đã thay bằng tên bịa; tên còn trùng chỉ là từ chung không kèm nhãn ("thời gian", "giá cả").
- **Hai tín hiệu sớm** (30 phiếu, chưa phải số đo):
  - Không phiếu nào là `can_hoc_truoc`. Nếu nhãn hai lượt cũng vậy, kết luận của E8 sẽ là giữ R17.
  - 8/30 là `nghia_khac`. Trong đó có lỗi khớp tên của luồng: viết tắt "DO" (oxy hoà tan) khớp chữ "do" (bởi vì) vì bộ khớp không phân biệt chữ
    hoa và chữ thường, và vài bí danh sai do gộp thực thể. Các cặp này là dương giả của E5 (agentic D-01 gán `khong`, E5 vẫn đề xuất). Ghi lại
    để xét ở bộ khớp tên của pass phụ.
