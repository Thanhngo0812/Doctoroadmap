# Báo cáo triển khai B0 DOCX và dọn dẹp

Ngày hoàn tất: 2026-08-29. Ponytail được áp dụng theo hướng chỉ sửa hai seam production đã có: adapter
Docling và `chunk_document`; không thêm dependency hoặc tầng abstraction mới.

## 1. Bằng chứng trước khi sửa

- Baseline: **97 test xanh**.
- Hai fixture mới được ghi từ đúng source hiện tại. Bộ số-vàng hiện trạng chạy xanh trước khi đổi luật.
- Sau khi thêm regression test nhưng trước khi sửa production: **10 test đỏ**, đúng các nhánh ảnh DOCX, nối
  run, bullet PUA, heading level, lọc dot/TOC, warning grouping và I25. Test tài liệu sạch không warning thừa
  vẫn xanh, chứng minh guard không chỉ kiểm cờ do code vừa gán.
- Cây cuối: **115 test xanh, 5 warning dependency**, không có failure.

## 2. Fixture và khám phá

| Fixture | Item | Ảnh/bảng/công thức | Kích thước | Thời gian parse ghi fixture |
|---|---:|---:|---:|---:|
| `baocao-canhan.json` | 396 | 3 / 0 / 0 | 1.677.534 byte | 11,61 giây |
| `naive-bayes.json` | 224 | 2 / 13 / 32 | 670.440 byte | 465,38 giây |

Câu hỏi khám phá ticket 01: **có**. Cả 3/3 picture item của DOCX mang pixel sau round-trip, nên adapter trích
thẳng từ `DoclingDocument`; không cần đọc riêng `word/media/`. Source có ba PNG tổng 793.660 byte.

OOXML còn có 4 DrawingML drawing nhưng chỉ 3 image blip; drawing thứ tư là `wordprocessingShape`. Vì shape
không thành picture item, parser kiểm tín hiệu này từ source và đưa `missing_image` vào manifest, hướng dẫn
LibreOffice. Ảnh raster vẫn trích đủ dù không cài LibreOffice.

Slide có 72 U+F097 đi vào chunk cũ: 71 ở đầu `list_item` và 1 text item chỉ chứa bullet. Adapter gỡ cả hai
dạng bullet không mang nội dung; hai heading và raw formula có PUA ở vị trí khác vẫn giữ và được
`remaining_private_use: 5` giám sát.

## 3. Thay đổi production

### Adapter 7 → 8

- Trích ảnh và `missing_image` chạy trên mọi định dạng; cờ PDF chỉ còn sửa glyph/order.
- DOCX có `wordprocessingShape` phát cảnh báo hệ thống cần LibreOffice.
- Nối node không bbox theo chuỗi khi node trước chưa kết câu; không nối sang list item/dấu liệt kê/đánh số,
  không nối dòng mục lục kết thúc bằng số trang, và không chạy trên node PDF có bbox.
- Dấu câu mở đầu như `,` được gắn không có space thừa. Ca thật thành
  `+ Triển khai dự án bằng Docker Compose, thực hiện kiểm thử...`.
- Gỡ PUA bullet sau Symbol mapping; `U+F0B7` vẫn ánh xạ thành `•`, PUA giữa câu vẫn giữ.
- Parse stats mới: `runs_stitched`, `stripped_pua_bullets`. DOCX thật ghi 56 lần nối; slide ghi 72 bullet.

### Chunk algorithm `section-id-v7` → `section-id-v8`

- Level heading dùng thứ tự: đánh số text/chuỗi chương tự hiệu chỉnh → raw level nếu cây có ít nhất hai level
  → fallback cũ. Mục chữ cái nhận một chữ cái Unicode với `.`/`)`; explicit numbering luôn thắng raw level.
- Chuỗi chương cần ít nhất hai heading chung tiền tố có chữ trước số khác nhau và một heading khác chen giữa;
  chuỗi lồng nhau nhận cấp ngoài + 1. Thành viên được miễn heuristic heading lặp. Không còn danh sách từ khoá
  theo ngôn ngữ; tiền tố chỉ có ký hiệu như `§` không tạo chuỗi.
- Block text dài ít nhất 100 ký tự, tỉ lệ Unicode letter dưới 10% bị loại kèm excerpt. `x = 5` sống.
- Vùng TOC là chuỗi ít nhất hai block liền nhau có số trang và đa số nội dung khớp heading của chính tài liệu;
  một câu chỉ nhắc một heading không bị loại. Node parse và section MỤC LỤC/NHẬN XÉT vẫn tồn tại.
- Warning chỉ gom khi toàn chuỗi giống hệt; raw khác nhau giữ riêng, thứ tự lần đầu ổn định.
- I25: bảng vượt trần văn xuôi 512 nhưng được trần bảng giữ nguyên mang
  `table_kept_whole_above_text_limit`. Đây là cách hiểu theo checklist ticket 08: bảng 513 token phải khai lý
  do, dù vẫn dưới trần bảng 2048. Row quá dài, câu không ranh và hard cap giữ lý do riêng.

## 4. Đối chiếu bốn tài liệu thật

Mỗi source được parse lại bằng Docling thật vào artifact root mới, không dùng parse cache cũ. Cả bốn manifest
ghi adapter 8 và `section-id-v8`.

| Tài liệu | Section | Chunk | Ảnh / bảng / công thức | PUA chunk | Digest chunk ID |
|---|---:|---:|---:|---:|---|
| nhap-mon-ml | 27 | 41 | 9 / 0 / 1 | 0 | `1f69ad2e…5074` |
| xstk-ch3-1 | 43 | 126 | 5 / 51 / 263 | 2 | `f12e2c21…9f9` |
| baocao-canhan | 27 | 26 | 3 / 0 / 0 | 0 | `b8f40f85…a7b0` |
| naive-bayes | 32 | 40 | 2 / 13 / 32 | 0 | `384df010…65a4` |

Kết quả bảng ảnh hưởng chéo:

- Hai giáo trình: danh sách chunk ID cũ v2 và mới **bằng nhau từng phần tử**, không chỉ cùng số lượng.
- DOCX: 30 → 26 chunk đúng bốn chunk rác; 27 section giữ nguyên số lượng, toàn bộ mục chữ cái về level 2 và
  mang tên CHƯƠNG trong `section_path`; 3 image ref; 56 run nối.
- Sau khi loại chính xác dot/TOC khỏi output cũ, chuỗi **10.486 chữ cái nội dung thật giữ nguyên và đúng thứ
  tự** trong output mới; không mất câu văn thật.
- Slide: 72 → 0 PUA trong chunk; 32 formula, 13 table, 2 image và 40 chunk giữ nguyên. Warning
  `Naïve Bayes Classification ×7` còn một dòng; bảng 513 token có lý do I25.
- I9 = 0 và chunk ID trùng = 0 cho cả bốn.
- Sau khi thay danh sách từ khoá bằng chuỗi tự hiệu chỉnh, số-vàng của cả bốn tài liệu vẫn đứng yên mọi cột và
  mọi digest. Test riêng khóa `CHƯƠNG I/II/III`, `第1章/第2章`, running header, `Bài tập 1/2` sát nhau và hai
  chuỗi lồng nhau.

Số-vàng cuối nằm ở `tests/unit/test_four_document_regression.py`; đổi số phải kèm giải thích trong cùng commit.

## 5. Tài liệu cập nhật

- ADR 0002: marker/ref suy giảm và `missing_image` bắt buộc.
- ADR 0003: tin dữ liệu khai báo, suy diễn là dự phòng.
- README: ảnh DOCX và LibreOffice tuỳ chọn.
- CONTEXT: cây khai báo, cây thoái hoá, run định dạng, khối phi ngôn ngữ.
- Báo cáo luồng: nhánh DOCX, heading priority, filter, warning grouping, I25 và version 8.

## 6. Gap chấp nhận của chuỗi chương

- Phụ lục không đánh số, chỉ xuất hiện một lần: PDF phẳng không tạo được chuỗi nên đi fallback; DOCX có cây
  khai báo vẫn dùng raw level.
- Tài liệu chỉ trích một chương: không đủ hai số khác nhau nên đi luật thường.
- Guard bao trùm ưu tiên tránh nâng nhầm nhãn đánh số đứng sát nhau hơn là đoán một chương đơn lẻ.
