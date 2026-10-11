# A1 R3 — ontology và căn nhãn loại khối

## Giao thức trước phép đo

Ngày 2026-10-07, tiếp sau R2-P. Câu hỏi: có thể tạo nhãn bạc đa loại có provenance và nhận biết trường hợp không chắc, thay vì dùng luật formula yếu làm veto tuyệt đối không? Đơn vị quan sát là dòng; đơn vị khái quát là sách/nguồn, **không phải 124 nghìn mẫu độc lập**.

Kho: 19 sách phát triển đã xem ở R2, manifest/hash vòng 1. Không mở sách test. Không dùng dự đoán/điểm M2 để tạo nhãn hay chọn mẫu. Không thay parser production, không sửa cache/model v1. Không API, không huấn luyện trước khi có báo cáo căn nhãn. Đây là phép kiểm thiết kế/dữ liệu, không phải bằng chứng mô hình mới tốt hơn.

Ontology R3 gồm `heading`, `text`, `formula`, `caption`, `list_item`, `code`, `table`, `footnote`. `title`/`section_header` gom heading; paragraph/text gom text. Chưa suy diễn header/footer từ dòng đã bị loại; audit R3 chỉ trên dòng giữ lại, ghi số dòng loại của v1 riêng. Figure không phải lớp dòng văn bản: audit hình thuộc R6. Nhãn chưa biết không ép thành text.

Luật căn phiên bản `a1-r3-block-labels-v1`:

- Cùng trang, hộp dòng/nút hợp lệ theo toạ độ PDF gốc dưới trái. Giao hộp chiếm ít nhất 50% diện tích dòng. Không chỉ so trung điểm với slack để ghép cột lân cận.
- Chuẩn hoá NFC, whitespace và Symbol/font Việt như R2. Giữ hoa/thường, số, dấu và số lần lặp: `x+x` khác `x-x`, `G G G` khác `G`. Không gọi cleanup legacy để tạo nhãn mới.
- Exact token sequence hoặc toàn dòng là đoạn token liên tiếp trong nút với ít nhất hai token chữ/số, hoặc ít nhất tám chữ. Không lấy một từ chung ngắn hay một nút tiêu đề nhúng trong dòng dài để gán nhãn cả dòng.
- Giữ tất cả node ứng viên. Khác loại → ambiguous; nhiều node cùng loại có thể cho nhãn loại nhưng không coi đó là một parent/heading ID duy nhất. Có node khác loại giao hộp mạnh và cùng phần chữ thì cũng bác nhãn đơn.
- Bảng căn theo ô; công thức dùng raw text. Nút không có bbox, không có text, loại chưa hỗ trợ không tạo nhãn. Ghi lý do unknown, các node ứng viên và tỷ lệ giao hộp.

Mẫu review: mỗi sách tối đa 2 dòng/lớp có nhãn (8 lớp) + 4 dòng unknown; chọn thứ tự SHA-256(seed=42, book, page, row) trong từng tầng, không có fallback lấp đầy lớp vắng. Ghi mẫu thiếu và mẫu số từng tầng. Mẫu chủ động cho lỗi đã biết (Vitamin K/Glycogen) phải tách khỏi mẫu đo; không gộp làm accuracy. Packet hiển thị dòng và hàng xóm trước, nhãn bạc trong tệp riêng. Đây là che gợi ý model cho người review, **không khôi phục được tính mù của kho đã xem**.

Chia vai trò review theo trang: hash(book,page,seed) mod 5 = 0 giữ cho audit, phần còn lại development; dòng trên cùng trang không đi hai vai trò. Cả hai vẫn là phát triển, chưa gọi test kín. Các dòng được agent nhận xét chỉ là đề xuất, không vàng. Chưa có hai người đọc độc lập, không báo kappa hay độ chính xác thật.

Nghiệm thu R3 kỹ thuật: test đỏ cho mất ký hiệu/ghép nhầm cột/nhãn hỗn hợp; phân vùng trang không giao; sample ổn định khi đảo thứ tự đầu vào; hash input và tổng số dòng khớp; bảng nhãn/unknown/bất đồng theo từng sách. Nếu nhãn công thức/bảng quá ít hoặc sai, không tuyên bố có dữ liệu đa loại đủ để thay production.

Skill `scientific-critical-thinking` chi phối việc tách nhãn bạc khỏi chân lý, đơn vị độc lập và protocol chọn mẫu. Dùng nguồn đã xác minh ở [báo cáo tổng](v4-14-A1-mo-rong-2026-10-07.md), không coi skill là bằng chứng parser tốt.

## Kết quả

Đã hoàn tất bộ căn nhãn và phép đo trên **19/19 sách, 124.208 dòng giữ lại**, 11,20 giây trên cache (không phải tốc độ parse PDF). **4.112 dòng đã bị filter v1 loại trước đó không nằm trong audit này.** Script không đọc hoặc dùng dự đoán M2. Snapshot: [v4-14-r3-so-do-2026-10-07.json](v4-14-r3-so-do-2026-10-07.json).

| Nhãn | Dòng |
|---|---:|
| text | 41.290 |
| list_item | 13.698 |
| formula | 6.740 |
| heading | 4.987 |
| table | 2.021 |
| code | 638 |
| footnote | 126 |
| caption | **0** |
| unknown | **54.708 (44,05%)** |

Căn exact: 10.755; contained: 58.745. Unknown gồm 51.258 unmatched, 3.440 partial, 9 loại chưa hỗ trợ, 1 ambiguous. Căn v1 có 44.779 unknown (36,05%); R3 từ chối thêm nhiều trường hợp để giữ dấu/hoa/thường/ràng buộc hộp. **Unknown tăng không chứng minh precision tăng**, cần đối chiếu độc lập. Không đổi phép đo rồi tuyên bố thắng.

| Sách | Dòng | Heading | Formula | Code | Table | Unknown | Tỷ lệ unknown |
|---|---:|---:|---:|---:|---:|---:|---:|
| d01-01 | 19709 | 239 | 3440 | 9 | 28 | 13088 | 66,41% |
| d01-02 | 11412 | 263 | 1763 | 0 | 2 | 8249 | 72,28% |
| d01-03 | 3417 | 229 | 211 | 9 | 113 | 1547 | 45,27% |
| d01-04 | 5477 | 179 | 17 | 0 | 65 | 2687 | 49,06% |
| d01-05 | 4422 | 283 | 8 | 0 | 102 | 969 | 21,91% |
| d01-06 | 5364 | 272 | 8 | 0 | 213 | 1685 | 31,41% |
| d01-07 | 3604 | 213 | 7 | 332 | 210 | 1026 | 28,47% |
| d01-08 | 8629 | 320 | 6 | 267 | 104 | 1683 | 19,50% |
| d01-09 | 11294 | 209 | 29 | 0 | 53 | 4405 | 39,00% |
| d01-10 | 6803 | 409 | 200 | 0 | 180 | 2481 | 36,47% |
| d01-11 | 4061 | 292 | 0 | 0 | 0 | 1609 | 39,62% |
| d01-12 | 3220 | 197 | 0 | 0 | 0 | 636 | 19,75% |
| d01-13 | 3446 | 300 | 12 | 0 | 71 | 1229 | 35,66% |
| d01-14 | 5068 | 392 | 6 | 21 | 83 | 1668 | 32,91% |
| d01-15 | 7426 | 560 | 0 | 0 | 443 | 1694 | 22,81% |
| d01-16 | 1377 | 117 | 0 | 0 | 45 | 360 | 26,14% |
| doc-1 | 8037 | 110 | 726 | 0 | 148 | 5942 | 73,93% |
| doc-4 | 7859 | 335 | 0 | 0 | 0 | 1728 | 21,99% |
| xstk-ch3-1 | 3583 | 68 | 307 | 0 | 161 | 2022 | 56,43% |

### Phát hiện về nhãn và ontology

1. **Caption không có lớp riêng trong cây đã lưu.** Có 103 node mang `context_prefix`, nhưng không có hộp caption riêng; không lấy bbox hình làm bbox chú thích để bịa nhãn. Cần lấy provenance từ đầu ra Docling trước adaptation hoặc kiểm native row với nguồn ảnh trang.
2. **Khớp hoàn toàn vẫn có thể sai loại.** D01-04 trang PDF 138, trích dẫn `(Phạm Thu Cúc, 2002)` dưới Hình 5.4 được Docling gọi formula; hình trang cho thấy đây là viện dẫn nguồn. Không sửa bằng whitelist tên tác giả.
3. **Code không nhất thiết là font đơn cách.** D01-07 trang 47: hai dòng `sp_addrole` và tham số tùy chọn dùng chữ đậm/nghiêng, bị gọi formula. Chỉ thêm cờ monospace không đủ.
4. **Vị trí cuối trang không đủ để gọi footnote.** D01-02 trang 15: `* Cho hàm số dưới dạng bảng` là mục thứ ba của danh sách trong thân bài, không chú thích cuối trang.
5. **Dòng có thể chỉ là mảnh của công thức hai chiều.** D01-02 trang 76: `x arctgx dx x arctgx` là mảnh phép biến đổi tích phân, nhưng nhãn nguồn text. Cần loại khối đi cùng quan hệ dòng→khối, không chỉ phân loại chuỗi.
6. **Thiếu `diagram_text`.** D01-06 trang 90: `Điện cực pH` nằm trong sơ đồ, không phải body/caption/formula. Không ép về một lớp hiện có. Ontology tám lớp ban đầu chưa đủ cho toàn A1.

Các tiêu đề đã biết lỗi luật ở R2 (`Vitamin K`, `Vitamin Q`, `Glycogen`, `Cellulose`) đều căn exact thành heading trong R3. Đây chỉ xác nhận luật formula cũ đã phủ quyết sai một nguồn heading, **không phải số nghiệm thu mô hình mới**.

### Review đã thực hiện và mức tin cậy

Tạo **271 phiếu**, 218 development/53 audit theo trang; giao trang giữa hai vai trò bằng **0**. Không lấp lớp vắng bằng lớp khác. Phiếu tách text/context khỏi key nhãn bạc. HTML tại `tmp/a1-v414-r3/review.html`.

Đã xem ảnh **11 trang**, ghi **14 đề xuất nhãn**: 8 ca được chọn có chủ đích trên 5 trang, cộng 6 ca đầu theo thứ tự hash của phần audit trên 6 trang. Các ca chủ đích đã biết nhãn nguồn; trong 6 ca audit có một nhãn từng xuất hiện ở lượt đọc text, vì vậy **không gọi review mù hoàn toàn**. Còn **257 phiếu chưa review**, không mặc nhiên chấp nhận. [Ghi nhận từng ca](v4-14-r3-review-2026-10-07.json).

Agent đơn lẻ, không gán nhãn vàng; không dùng 14 đề xuất này để sửa cache hoặc train model. Không tính accuracy/kappa từ mẫu chủ đích nhỏ. Poppler cảnh báo thiếu display font Symbol/ArialUnicode; ảnh đủ xem bố cục của các ví dụ nêu trên, chưa đủ để xác nhận phiên âm từng glyph công thức. Tệp PNG trong `tmp/pdfs/a1-r3/` giữ làm bằng chứng review, không phải tài liệu nguồn mới.

### Quyết định tiếp theo

**Nhận bộ căn nhãn và công cụ review vào công cụ nghiên cứu; chưa nhận nhãn đa loại làm ground truth, chưa train/promote bộ phân loại đa loại.** R3 kỹ thuật căn nhãn hoàn tất, phần hoàn thiện ontology/review còn tiếp tục (R3b).

R3b sẽ tách hai trục: vai trò bố cục (body/heading/caption/footnote/table-cell/diagram-text) và nội dung (prose/math/code/mixed); giữ quan hệ parent/asset và cờ chất lượng text. Cần lấy caption provenance chưa qua adaptation, tách nhãn yếu khỏi nhãn được xác minh, mở rộng review theo lớp/nguồn còn thiếu. Không dùng nhãn agent đơn lẻ để tuyên bố kiểm độc lập. Sau đó R4 mới so mô hình/đặc trưng, có nhóm nguồn và ablation; không vội fit thêm cây để học lại nhãn sai.

Không cần người dùng duyệt lại quyền triển khai; không có khoản chi mới chờ duyệt. Bước tiếp theo dùng CPU/cache hiện có trước, sách mới vẫn sau cùng. A1 production giữ nguyên R2-P; không sửa `src/` trong R3.

### Kiểm thử và tái lập

- 11 test R3 đạt: ký hiệu/hoa/thường/lặp, cột/trang, dòng hỗn hợp, raw formula/table, bbox thiếu/sai, nhiều node cùng lớp, sample ổn định, phân vai trang, chặn output đè baseline/production.
- Test hành vi cũ: `x+x` với `raw_text=x-x` bị word-only alignment gán nhãn 0 thay vì unknown; assertion mới thật sự bác hành vi cũ. Lần fixture đầu thiếu `raw_text` nên không tái hiện, đã sửa fixture và chạy lại; không tính lỗi import thiếu module ban đầu là test đỏ logic.
- Hai đột biến thay coverage bằng 1 và tokenization bằng hàm cũ đều bị test bắt. Không nới assertion để qua.
- Regression toàn dự án: **955 đạt, 2 skip ML, 8 integration deselected**, 81,28 giây. Không chạy lại integration vì không đổi production trong R3; mốc R2-P có 9/9 test ở thư mục integration đã đạt. Không có lời gọi API; chi **0 USD**.
- Nhóm A1 trong môi trường ML: **44/44 đạt**, 5,00 giây (11 R3 + 33 R2/vòng 1), bao gồm hai test bị skip ở môi trường production; không cộng các lượt thành test độc lập. `git diff --check`, hash mã nguồn snapshot, tập ID packet/key và trạng thái review còn trống đều kiểm đạt. Không còn job R3 chạy nền khi chốt.

```powershell
.venv/Scripts/python.exe scripts/doc-nhe/nhan_khoi_r3.py --out tmp/a1-v414-r3-luot-moi
.venv/Scripts/python.exe -m pytest tests/unit/presentation/test_a1_block_labels.py -q -o addopts= -p no:cacheprovider --basetemp tmp/pytest-r3-luot-moi
```

Output phải là thư mục trống riêng dưới `tmp/`; script từ chối đè baseline hoặc kết quả cũ. Manifest xác minh hash PDF/tree/chunk, dataset phải khớp book/fingerprint. Snapshot ghi hash mã nguồn và dataset; không ghi kết quả R3 chồng lên snapshot R2.
