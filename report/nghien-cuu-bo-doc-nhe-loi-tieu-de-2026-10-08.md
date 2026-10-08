# Bộ đọc nhẹ (LightGBM cùng luật) có thay được docling cho PDF gốc không: số hiện có và chẩn đoán

Claude, 2026-10-08. Phạm vi sản phẩm đã chốt là PDF gốc. Hướng đi là bộ đọc nhẹ thay docling; quyết định vẫn theo luật pha 4 của
[vé 15](../task/v4/15-a1-danh-gia-doc-lap-chon-duong.md).

**Giới hạn của số trong báo cáo này:**
- Mỗi hệ mới chạy một lần.
- Nhãn là nhãn agentic (bạc).
- Lúc đo S0, CPU không rảnh.
- S1 lấy từ kho cũ `tmp/a1-v415/phase2-20261008`; S0 lấy từ kho mới `phase2b-20261008`, 5/54 lượt.
- M2 có thể lệch vì luật cha đổi giữa hai kho.

Báo cáo này chỉ để định hướng pha 3, không phải kết quả đánh giá.

## 1. Số trên tập phát triển

| Sách | M3 S1 | M3 S0 | chênh M3 | M1 S1 | M1 S0 | M2 S1 / S0 | giây/trang S1 / S0 | nhanh hơn |
|---|---:|---:|---:|---:|---:|---|---|---:|
| d01-02 | 0,829 | 0,869 | −0,040 | 0,815 | 0,798 | 0,15 / 0,19 | 0,53 / 2,67 | 5× |
| d01-06 | 0,764 | 0,810 | −0,046 | 0,819 | 0,905 | 0,45 / 0,31 | 0,20 / 5,33 | 27× |
| d01-07 | **0,229** | 0,769 | **−0,539** | 0,297 | 0,758 | 0,32 / 0,37 | 0,14 / 6,87 | 50× |
| d01-10 | 0,918 | 0,898 | +0,020 | 0,719 | 0,838 | 0,49 / 0,52 | 0,11 / 5,08 | 45× |
| d01-11 | **0,590** | 0,983 | **−0,393** | 0,678 | 0,888 | 0,13 / 0,07 | 0,14 / 2,42 | 18× |
| d01-15 | 0,770 | chưa đo | | 0,787 | | 0,48 / — | 0,16 / — | |

**Tốc độ: đạt.** Trung vị nhanh hơn 27×, nhưng d01-02 chỉ 5×.

**Chất lượng: chưa đạt**, theo luật pha 4 áp thử trên tập phát triển:
- M3 trung vị là 0,764 so với 0,869 (−0,105, luật cho phép −0,02).
- Hai cuốn thấp hơn S0 quá 0,10.
- M1 trung vị là 0,719 so với 0,838 (−0,119, luật cho phép −0,03).

Ba cuốn d01-02, d01-06, d01-10 có M3 sát S0. Hai cuốn sụp hẳn là d01-07 và d01-11.

**Cây cha–con: cả hai hệ đều kém** (M2 từ 0,07 đến 0,52). Đây là chỗ bộ đọc nhẹ có thể hơn docling.

## 2. Chẩn đoán hai cuốn sụp

**Cách làm.**
- Tiêu đề của hệ được tính là khớp khi có chung ít nhất một mã dòng với một tiêu đề agentic. Cách này lỏng hơn M1.
- Tiêu đề thừa được xếp nhóm bằng regex thô, nên số theo nhóm là xấp xỉ.
- Script nằm ở scratchpad của phiên, không đưa vào kho.

| | dự đoán | nhãn | khớp | thừa | thiếu |
|---|---:|---:|---:|---:|---:|
| d01-07 S1 | 910 | 166 | 160 | 750 | 6 |
| d01-07 S0 | 198 | 166 | 142 | 56 | 28 |
| d01-11 S1 | 291 | 243 | 191 | 100 | 58 |
| d01-11 S0 | 237 | 243 | 219 | 18 | 27 |

### d01-07: cờ "đậm" sai trên cả cuốn

- **Triệu chứng.** 99,2% dòng thân bài bị đánh dấu là đậm (`dam` trong phiếu D-02, cùng nguồn với đặc trưng của S1). Các cuốn khác chỉ 0,6–8%.
- **Nguyên nhân.**
  - Font là `TimesNewRoman` thường, tên không có "Bold".
  - Nhưng `FPDFText_GetFontWeight` của pdfium trả 704–740 cho gần hết ký tự (đã kiểm trang 10, 31, 61).
  - Luật `weight >= 600` ở [doc_nhe.py:118](../scripts/thu-a1/doc_nhe.py) nên coi cả cuốn là chữ đậm.
- **Hệ quả.**
  - Đậm chiếm 42% gain của mô hình, nên mô hình gọi phần lớn dòng câu văn là tiêu đề. Ví dụ: "bền (durability).", "đến mâu thuẫn.".
  - Khoảng 516 tiêu đề thừa là dòng ngắn của câu văn, và khoảng 118 là dòng dài.

### d01-11 (sách luật): nhầm khoản và điểm với tiêu đề, bỏ sót "Điều"

- **Thừa:** khoảng 62 dòng khoản đánh số ("1. Về kiến thức:", "2. Về kỹ năng:") và khoảng 22 dòng điểm ("đ) Các hình thức phù hợp khác.").
- **Thiếu:** 58 tiêu đề, phần lớn là "Điều N. …".
- **Vì sao M3 thấp:** thiếu tiêu đề Điều làm thân bài bị gán sang mục trước, nên M3 chỉ 0,59.
- **Đậm vẫn hoạt động ở cuốn này:** thân bài đậm 0,7%, tiêu đề đậm 84%. Lỗi nằm ở cách hiểu cách đánh số, không phải ở đặc trưng chữ.

## 3. Cỡ chữ hầu như không phân biệt được tiêu đề

| Sách | thân bài đậm | tiêu đề đậm | tiêu đề to hơn thân bài |
|---|---:|---:|---:|
| d01-02 | 0,6% | 84% | 11% |
| d01-06 | 4,9% | 32% | 42% |
| d01-07 | 99,2% (lỗi) | 100% | 23% |
| d01-10 | 8,0% | 99,7% | 0,3% |
| d01-11 | 0,7% | 84% | 0% |
| d01-15 | 4,0% | 16% | 0,2% |

- Giáo trình tiếng Việt ở đây thường in tiêu đề cùng cỡ chữ với thân bài. Tín hiệu chính là đậm, cách đánh số, vị trí, và mục lục.
- Các công cụ xếp hạng cấp tiêu đề theo cỡ chữ không hợp với loại sách này.
- d01-06 và d01-15 có nhiều tiêu đề không đậm (chỉ 32% và 16% là đậm). Pha 3 nên xem các tiêu đề này được nhận ra bằng gì.

## 4. Kết luận

- **Hướng LightGBM cùng luật làm được.**
  - Các hệ trích cấu trúc PDF gốc đã dùng thật đi theo cùng hướng: đặc trưng bố cục, mô hình nhẹ và luật (GROBID dùng CRF, CERMINE dùng SVM
    kèm luật).
  - Hai cuốn sụp có nguyên nhân cụ thể và sửa được bằng cơ chế chung, không cần luật theo mã sách.
- **Chưa đạt, ngay cả khi sửa xong hai cuốn.** M1 của d01-06 (−0,09) và d01-10 (−0,12) vẫn dưới ngưỡng −0,03.
- **Giới hạn của cách học hiện tại.** Mô hình đang học nhãn bạc của docling, nên trần của nó gần bằng docling. Đây cũng là lý do chuỗi R báo
  quá cao.

## 5. Đề xuất cho pha 3

Làm theo [giao thức pha 3](v4-15-giao-thuc-pha-3-2026-10-08.md): mỗi vòng một cơ chế, chấm trên 6 cuốn phát triển và 19 cuốn bạc, báo mọi
cuốn bị giảm.

1. **Chuẩn hoá cờ đậm theo cuốn.**
   - Lấy độ đậm trội của thân bài làm mốc; cờ đậm là độ đậm tương đối so với mốc đó.
   - Khi phần lớn dòng của cuốn đều đậm, không dùng độ đậm tuyệt đối mà dựa vào tên font và độ đậm tương đối.
   - Test: một PDF tổng hợp có chữ thường mà pdfium báo weight 700. Test phải đỏ trên mã hiện tại.
2. **Ngữ pháp đánh số tiếng Việt, làm cả luật lẫn đặc trưng.**
   - Phân biệt tiêu đề (Phần, Chương, Mục, Điều N., 1.1.) với khoản và điểm nằm trong một mục (1., a), đ)).
   - Dòng kết thúc bằng dấu ":" thường là câu dẫn.
   - Áp chung cho mọi sách, không theo mã sách.
3. **Dựng cây cha–con từ cách đánh số và mục lục** (S3 đặt trên S1). Đây là chỗ cả hai hệ đều kém, M2 từ 0,07 đến 0,52.
4. **Học trên nhãn độc lập.**
   - Hiệu chỉnh ngưỡng hoặc huấn luyện lại bằng nhãn D-02 phát triển, fold bỏ chính cuốn đang chấm.
   - Nhãn bạc docling chỉ dùng làm dữ liệu phụ.
   - Không dùng nhãn tập khoá.

Hạn mức của pha 3 vẫn giữ: tối đa ba ngày làm việc, hoặc dừng khi hai vòng liên tiếp không tăng M3. Luật pha 4 không đổi.
