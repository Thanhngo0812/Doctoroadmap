# v4-10 bước 2 — Bộ đọc PDF nhẹ thay docling: thử nghiệm (2026-10-05)

**Câu hỏi của chủ dự án (2026-10-05):** có nên bỏ docling không? Đầu vào sau này là PDF sạch có lớp chữ.

**Câu hỏi đo:** một bộ đọc chỉ dùng lớp chữ (font, cỡ, vị trí) cộng luật, không mô hình học, có cho cây tài liệu và chunk đủ gần docling không,
và nhanh hơn bao nhiêu?

**Phạm vi.** 0 USD, tại máy. Ba giáo trình tiếng Việt: doc-1 (đại số tuyến tính, LaTeX), xstk (xác suất thống kê, Word), doc-4 (triết học,
chữ thuần).

**Mã.**
- `scripts/thu-a1/doc_nhe.py`: bộ đọc nhẹ, khoảng 330 dòng, pypdfium2 (giấy phép Apache-2.0/BSD-3), so ở mức cây.
- `scripts/thu-a1/so_chunk_doc_nhe.py`: so ở mức chunk.

## Tóm tắt

1. **Nhanh hơn 35–150 lần.**
   - Bộ đọc nhẹ: 0,014–0,046 giây/trang. docling (thợ đã nạp mô hình): 1,4–3,2 giây/trang trên máy này.
   - Một cuốn 400 trang: khoảng 10–20 giây so với 10–20 phút.
2. **Chữ gần như trùng docling.**
   - Phủ từ hai chiều 0,95–0,99; thứ tự đọc theo trang 0,87–0,94.
   - Ở doc-4, chữ của bộ đọc nhẹ **sạch hơn** docling: cây docling còn âm tiết vỡ ("v ật", "ất"), bộ đọc nhẹ ra "vật".
3. **Sách chữ thuần (doc-4) gần như thay được ngay.**
   - Tiêu đề R 0,93 / P 0,98.
   - 95% chunk docling có chunk nhẹ trùng từ ít nhất một nửa; 75% trùng ít nhất 0,8.
   - 89% chunk nằm cùng mục lá.
4. **Sách toán và thống kê (doc-1, xstk) chưa thay được.**
   - Công thức bị cắt vụn: phủ từ công thức 0,18–0,58.
   - Bảng chưa nhận: xstk có 51 bảng.
   - Chỉ 44–51% chunk trùng ít nhất 0,8.
5. **Chạy lai theo trang vô ích với sách toán.** 90–98% trang của doc-1 và xstk có công thức, bảng hoặc hình, nên vẫn phải chạy docling gần hết
   sách.
6. **Chọn bộ đọc theo cả cuốn thì khả thi.**
   - Tín hiệu là tỉ lệ ký tự thuộc font toán; tính mất dưới 5 giây mỗi cuốn.
   - Cuốn có tín hiệu toán (doc-1 20,5%, doc-2 20,9%, xstk 2,6% ký tự; 78–97% trang) dùng docling.
   - Cuốn 0% (doc-4, doc-6) dùng bộ đọc nhẹ.
7. **Chưa biết chất lượng ở các khâu sau.** Khái niệm, cạnh và lộ trình khi chạy trên chunk nhẹ chưa đo được nếu không tốn tiền: cần chạy A3 → A8
   pass chính trên doc-4, khoảng 4–5 USD, rồi ánh xạ lại vàng. Đề xuất ở mục 5.

## 1. Bộ đọc nhẹ làm gì

Ba vòng chỉnh luật: v0, v1, v2–v3. Mỗi vòng sửa đúng lỗi đọc được từ phép so; xem phần đầu `doc_nhe.py`.
- **Ký tự:** đọc mã, hộp lỏng, tên font, độ đậm của từng ký tự.
  - Cỡ chữ đo bằng chiều cao hộp, vì doc-4 ghi cỡ 1 và phóng chữ bằng ma trận.
  - Làm sạch chữ bằng chính `DoclingParser._clean_text` của dự án (ánh xạ ký tự Symbol ở vùng riêng).
- **Đầu trang, chân trang:** dòng ở 8% trên hoặc dưới, lặp ở ít nhất 3 trang, hoặc chỉ là số trang.
- **Công thức:**
  - ít nhất 60% ký tự thuộc font toán (CM* của LaTeX, Symbol, Euclid…) và rất ít chữ thường;
  - hoặc dòng không có chữ cái nhưng có ký hiệu toán;
  - dòng công thức cách nhau tới 2,5 dòng thì gộp.
- **Tiêu đề:**
  - mẫu đánh số tiếng Việt ("Chương", "Phần", "§", "1.2", "I-", "A.") kèm chữ đậm hoặc chữ to;
  - "a)" in đậm;
  - dòng đậm mở đầu bằng dấu đầu dòng;
  - dòng đậm ngắn đứng riêng;
  - dòng nhãn chương ("Chương I") để riêng như docling.
- **Mục danh sách:** ký hiệu đầu dòng, kể cả dấu đầu dòng ở vùng ký tự riêng của font Symbol.
- **Đoạn văn:** gom dòng liền nhau; ngắt khi cách dòng lớn, hoặc thụt đầu dòng so với lề trái của trang sau một câu đã kết thúc.
- **Chưa làm:** bảng, chú thích hình đầy đủ, bố cục hai cột.

## 2. So ở mức cây

Mốc là cây docling mà chunk của luồng đang ghim: doc-1 parse v5, doc-4 parse v2, xstk parse v2.
- Phủ từ đếm theo túi từ, tách chữ khỏi số, vì hai bộ đọc đặt khoảng trắng quanh chỉ số khác nhau ("x 1" và "x1").
- Hai tiêu đề được coi là khớp khi giống ít nhất 0,85, hoặc một tiêu đề nằm trọn trong tiêu đề kia.

| | doc-1 | doc-4 | xstk |
|---|---|---|---|
| giây/trang: nhẹ · docling | 0,015 · 2,25–2,58 | 0,044 · 1,37–1,86 | 0,024 · 3,0–3,2 |
| phủ từ R / P | 0,954 / 0,959 | 0,992 / 0,995 | 0,967 / 0,972 |
| thứ tự đọc theo trang | 0,923 | 0,870 | 0,943 |
| tiêu đề R / P (docling · nhẹ) | 0,972 / 0,865 (109 · 141) | 0,934 / 0,982 (304 · 275) | 0,881 / 0,982 (67 · 55) |
| công thức: phủ từ (nút docling · nhẹ) | 0,584 (562 · 2.341) | — | 0,179 (263 · 281) |
| bảng (docling · nhẹ) | 5 · 0 | 0 · 0 | 51 · 0 |

## 3. So ở mức chunk

Cả hai cây đi qua đúng `chunk_document` của dự án:
- tokenizer Gemma tại máy;
- tham số đọc từ manifest chunk đã ghim (512/256 token, `heading_scheme` của doc-4 là `vn-textbook`);
- không áp `strip_lines` cho bên nào.

| | doc-4 | doc-1 | xstk |
|---|---|---|---|
| số chunk docling · nhẹ | 671 · 729 | 199 · 286 | 126 · 147 |
| chunk docling có chunk nhẹ trùng từ ≥ 0,8 / ≥ 0,5 | 0,745 / 0,948 | 0,508 / 0,940 | 0,437 / 0,905 |
| chiều ngược (chunk nhẹ) ≥ 0,8 / ≥ 0,5 | 0,687 / 0,878 | 0,353 / 0,713 | 0,374 / 0,796 |
| Jaccard trung bình | 0,873 | 0,779 | 0,738 |
| cùng mục lá | 0,890 | 0,859 | 0,754 |

So chuỗi đường mục y hệt cho số rất thấp (0,0–0,37), nhưng chủ yếu do cách đặt mức. Ví dụ docling có "Chương I > Khái lược về Triết học", bộ đọc
nhẹ có "Chương I Khái lược về Triết học"; trong lần đo này luật nhãn chương đã được sửa theo đúng mẫu đó. Thước đo "cùng mục lá" phản ánh sát
hơn chunk có rơi vào đúng mục không.

## 4. Song song docling trên máy này (vé 10, lượt 2)

`scripts/thu-a1/do_a1_chia_doan.py`: 40 trang đầu mỗi tài liệu.
- Chia cuốn thành đoạn trang, mỗi đoạn một tiến trình, rồi ghép bằng `DoclingDocument.concatenate`, sau đó adapt một lần.
- So với 8 luồng và tắt OCR.

| tài liệu | mốc 1×4 luồng | chia đôi 2×4 | 1×8, tắt OCR | 2×4, tắt OCR | mốc lần 2 |
|---|---|---|---|---|---|
| doc-1 (giây/trang) | 2,25 | 2,70 | 2,58 | 2,43 | 2,58 |
| doc-4 | 1,37 | 1,48 | 1,54 | 1,54 | 1,86 |
| xstk | 3,14 | 3,12 | 3,01 | 3,17 | 3,08 |

- **Đầu ra y hệt ở mọi cấu hình**: thứ tự mục và băm adapter trùng mốc; JSON khứ hồi không đổi đầu ra. Chia đoạn rồi ghép là an toàn.
- **Không nhanh hơn trên máy này.** Mọi khác biệt nhỏ hơn nhiễu: mốc chạy hai lần lệch 15–35%.
  - CPU Ryzen 7 7730U là chip laptop 15 W. Cấu hình mặc định đã dùng hết ngân sách điện và nhiệt.
  - Máy còn Chrome và ứng dụng Codex chạy nền, khoảng 20% CPU.
  - Mỗi thợ dùng 1,7–2,3 GB RAM; cấu hình 4 thợ bị bỏ vì thiếu RAM.
- Trên máy chủ nhiều nhân hơn, chia đoạn có thể có lợi, nhưng phải đo trên đúng phần cứng triển khai.
- GPU: tài liệu chính thức của docling báo 4–8 trang/giây (R-03). Đó là quyết định hạ tầng.

## 5. Đề xuất

1. **Giữ docling cho sách toán, thống kê và làm đường dự phòng.** Trên máy này không có tuỳ chọn nào làm docling nhanh hơn rõ.
2. **Bộ đọc nhẹ cho sách chữ, chọn theo cả cuốn bằng tín hiệu font toán.** Trước khi đưa vào luồng phải đo ở các khâu sau. Đề xuất thí nghiệm có
   tốn tiền, chờ chủ dự án duyệt:
   - chạy doc-4 bằng chunk nhẹ qua A2 → A8 pass chính (khoảng 4–5 USD theo mức v3), pass phụ không LLM, A9 → A10;
   - ánh xạ vàng doc-4 sang khái niệm mới theo tên;
   - so Q3, Q6, Q7, bao đóng với lượt docling.
3. **Nếu muốn bộ đọc nhẹ cho cả sách toán:**
   - gom công thức theo font (LaTeX dễ: CMMI, CMSY, CMEX; Word khó hơn: Symbol cộng Times nghiêng);
   - nhận bảng bằng đường kẻ (đối tượng đường của pdfium).

   Đây là nghiên cứu riêng, khối lượng vừa phải; nên chờ biết kết quả bước 2.
4. **Rủi ro bộ đọc luật:** bố cục ngoài mẫu (hai cột, khung bên lề, bảng trong sách chữ) chưa gặp trong ba sách này. Lưới an toàn là kiểm cây sau
   khi đọc: tỉ lệ tiêu đề trên số trang, số đoạn quá dài, tỉ lệ ký tự vùng riêng. Lệch thì chuyển sang docling.

## 6. Chạy lại

```
.venv/Scripts/python.exe scripts/thu-a1/doc_nhe.py [--tai-lieu=doc-1,doc-4,xstk]          # so mức cây, ghi tmp/thu-a1/doc-nhe/
.venv/Scripts/python.exe scripts/thu-a1/so_chunk_doc_nhe.py [--tai-lieu=doc-4,doc-1,xstk]  # so mức chunk
.venv/Scripts/python.exe scripts/thu-a1/do_a1_chia_doan.py --trang=40                      # song song docling, khoảng 50 phút
```

pypdfium2 5.12.1, docling 2.114.0, docling-core 2.91.0.
