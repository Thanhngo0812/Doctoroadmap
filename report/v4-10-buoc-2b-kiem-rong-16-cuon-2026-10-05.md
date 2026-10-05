# v4-10 bước 2b — Kiểm rộng bộ đọc nhẹ trên 16 giáo trình, 8 lĩnh vực (2026-10-05)

**Câu hỏi của chủ dự án:** luật của bộ đọc nhẹ có đứng vững qua 8 lĩnh vực không? Phương án 2 được chọn ngày 2026-10-05.

**Dữ liệu.** 16 cuốn học của D-01 (`document-data/train/`, 2.990 trang): toán, hoá, sinh, CNTT, kinh tế, pháp luật, kỹ thuật, nông nghiệp.
Hai cuốn `test/` không được mở.

**Mốc so.** docling chạy qua đúng lệnh `ingest` của dự án, bộ đọc chữ pypdfium2, sơ đồ tiêu đề mặc định. Kết quả lưu ở kho artifact và
dùng lại cho D-01 bước 2.

**Bộ đọc nhẹ.** v4 (`scripts/thu-a1/doc_nhe.py`), chỉnh trên doc-1, doc-4, xstk trước khi gặp 16 cuốn này. Không chỉnh thêm sau khi xem kết
quả 16 cuốn.

**Cách so.** `scripts/thu-a1/doc_nhe_rong.py`; cùng cách đo như [bước 2](v4-10-buoc-2-bo-doc-nhe-2026-10-05.md).

## Tóm tắt

1. **docling-parse (bộ đọc chữ mặc định của luồng) giải mã hỏng d01-01** (Toán cao cấp 2).
   - Chữ ra thành "T'p c¡c ph†p bi,n Œi tuy,n t‰nh cıa V"; pdfium đọc cùng trang thành tiếng Việt chuẩn.
   - Đây là giáo trình tiếng Việt thứ hai bị docling-parse đọc hỏng, sau doc-4 (vỡ âm tiết).
   - Tỉ lệ token là âm tiết tiếng Việt hợp lệ tách rõ chữ hỏng với chữ sạch: chữ hỏng 0,32 (d01-01) và 0,71 (doc-4); chữ sạch 0,85–0,999 (pdfium,
     cả 16 cuốn).
   - Đề xuất: **mặc định pypdfium2 cho tài liệu tiếng Việt**, cộng lưới an toàn bằng tỉ lệ này, ngưỡng khoảng 0,8.
2. **Phần đọc chữ của bộ đọc nhẹ đứng vững qua 8 lĩnh vực.** Phủ từ so với docling: trung vị R 0,99 / P 0,97. Thấp nhất R 0,69 ở Toán A1, do
   công thức Word.
3. **Phần nhận tiêu đề không đứng vững.**
   - Tiêu đề: trung vị R 0,72, thấp nhất 0,17 (Nông nghiệp d01-15), 0,20 (Sinh học d01-06), 0,36 (Pháp luật d01-11). Độ chính xác vẫn cao
     (trung vị P 0,97).
   - Sách mới có nhiều kiểu tiêu đề không đánh số mà luật chỉnh trên 3 sách không bắt được.
   - Hệ quả ở mức chunk: trung vị chỉ 58% chunk rơi vào cùng mục lá với docling (thấp nhất 5%); 44% chunk trùng từ ít nhất 0,8.
4. **Bộ đọc nhẹ chưa thay được docling.** Nhanh hơn 55–450 lần, nhưng sai cấu trúc sẽ lan sang A2 (vai trò vùng), C8 và tên module.
   - Mục lục điện tử (bookmark) không cứu được: 7 cuốn đầu đều không có.
   - Hướng đáng thử nếu cần tốc độ: **học bộ nhận tiêu đề** từ nhãn docling trên chính 16 cuốn này (đặc trưng font, vị trí, khoảng cách,
     đánh số), đo bằng để riêng từng cuốn. Việc này không dùng LLM, hợp với seminar.

## Bảng theo cuốn

- Số giây docling/trang lấy từ manifest chunk. Bốn cuốn đầu ghi 0 vì manifest mới nhất là bản đã gán vai trò, không mang số đo parse.
- "CT/B/H" là tỉ lệ trang có công thức, bảng hoặc hình theo docling.
- "mảnh 1 chữ" là tỉ lệ token một chữ cái.

| cuốn | lĩnh vực | trang | nhẹ s/trang | docling s/trang | ký tự font toán | CT/B/H | chữ R / P | thứ tự | tiêu đề R / P | chunk ≥ 0,8 | ≥ 0,5 | cùng mục lá |
|---|---|---:|---:|---:|---:|---:|---|---:|---|---:|---:|---:|
| d01-01 | Toán | 237 | 0,013 | — | 21,1% | 91% | 0,98 / 0,94 | 0,93 | 0,89 / 0,95 | 0,41 | 0,87 | 0,77 |
| d01-02 | Toán | 199 | 0,016 | — | 13,1% | 94% | 0,69 / 0,98 | 0,75 | 0,75 / 0,73 | 0,29 | 0,77 | 0,55 |
| d01-03 | Hoá | 125 | 0,020 | — | 0,4% | 84% | 0,98 / 0,97 | 0,94 | 0,92 / 0,91 | 0,50 | 0,81 | 0,67 |
| d01-04 | Hoá | 178 | 0,025 | — | 0,2% | 67% | 0,98 / 0,90 | 0,90 | 0,67 / 0,97 | 0,27 | 0,74 | 0,43 |
| d01-05 | Sinh | 150 | 0,026 | 4,51 | 0,0% | 31% | 0,99 / 0,98 | 0,94 | 0,65 / 1,00 | 0,66 | 0,88 | 0,62 |
| d01-06 | Sinh | 171 | 0,033 | 6,43 | 0,0% | 29% | 0,95 / 0,97 | 0,86 | 0,20 / 0,82 | 0,27 | 0,67 | 0,11 |
| d01-07 | CNTT | 115 | 0,019 | 5,12 | 0,2% | 51% | 0,99 / 0,93 | 0,92 | 0,80 / 0,57 | 0,29 | 0,59 | 0,41 |
| d01-08 | CNTT | 237 | 0,043 | 4,12 | 0,1% | 52% | 0,99 / 0,99 | 0,96 | 0,94 / 0,97 | 0,73 | 0,86 | 0,83 |
| d01-09 | Kinh tế | 379 | 0,034 | 1,86 | 0,0% | 38% | 0,99 / 0,97 | 0,78 | 0,62 / 0,98 | 0,60 | 0,91 | 0,61 |
| d01-10 | Kinh tế | 260 | 0,022 | 3,17 | 0,4% | 55% | 0,99 / 0,97 | 0,92 | 0,81 / 0,98 | 0,59 | 0,85 | 0,77 |
| d01-11 | Pháp luật | 134 | 0,026 | 1,87 | 0,0% | 0% | 0,99 / 0,97 | 0,97 | 0,36 / 1,00 | 0,31 | 0,78 | 0,15 |
| d01-12 | Pháp luật | 101 | 0,028 | 1,91 | 0,0% | 0% | 1,00 / 0,96 | 0,93 | 0,78 / 1,00 | 0,77 | 0,92 | 0,76 |
| d01-13 | Kỹ thuật | 165 | 0,017 | 7,49 | 0,1% | 83% | 0,97 / 0,94 | 0,92 | 0,60 / 0,99 | 0,41 | 0,77 | 0,51 |
| d01-14 | Kỹ thuật | 262 | 0,016 | 4,93 | 0,0% | 68% | 0,99 / 0,96 | 0,94 | 0,75 / 0,85 | 0,46 | 0,73 | 0,48 |
| d01-15 | Nông nghiệp | 225 | 0,031 | 2,79 | 0,0% | 20% | 0,99 / 0,99 | 0,95 | 0,17 / 0,62 | 0,26 | 0,65 | 0,05 |
| d01-16 | Nông nghiệp | 52 | 0,019 | 3,28 | 0,0% | 27% | 0,98 / 0,98 | 0,95 | 0,69 / 0,96 | 0,60 | 0,79 | 0,66 |

**Thời gian docling.** Tổng 180 phút cho 16 cuốn, 1,9–7,5 giây/trang. Trong lúc chạy, máy còn chạy song song A3 → A9'' của D-01. Sách nhiều bảng
và hình (kỹ thuật, sinh học) chậm nhất.

## Đề xuất

1. **Bộ đọc chữ cho tiếng Việt:**
   - đổi mặc định sang pypdfium2;
   - thêm lưới an toàn sau A1: tỉ lệ âm tiết tiếng Việt hợp lệ dưới khoảng 0,8 thì cảnh báo và thử bộ đọc kia.
   Cần một vé cho nhân viên, nối vào vé 09 vì bộ đọc nằm trong khoá cache.
2. **Giữ docling cho A1.** Bộ đọc nhẹ chỉ là hướng nghiên cứu: học bộ nhận tiêu đề từ nhãn docling (16 cuốn, đo để riêng từng cuốn).
   Chưa đưa vào luồng.
3. **Tốc độ A1 trên máy chủ:** đo docling song song theo đoạn trang, hoặc dùng GPU, trên đúng phần cứng triển khai. Trên laptop 15 W không có
   lợi.
