# Kế hoạch tối ưu thời gian ingest

**Ngày đo:** 2026-09-02

**Phạm vi:** ingest lạnh và tái ingest PDF/DOCX của pha B0

**Nguyên tắc:** ưu tiên cache và cấu hình sẵn có; không đổi chất lượng đầu ra chỉ để lấy một con số nhanh.

## 1. Kết luận ngắn

Nút thắt của ingest lạnh là `DocumentConverter.convert()`, không phải chunker hay ghi JSON. Với tài liệu đã
ingest, cache hiện có đã giảm thời gian 94–99,75%. Với tài liệu mới, cơ hội lớn nhất là tắt OCR có chủ đích
cho PDF có text layer đầy đủ và thử TableFormer FAST cho tài liệu nhiều bảng. Cả hai phải qua số-vàng trước
khi đổi mặc định.

Không nên chạy lạnh cả bốn tài liệu song song trên máy hiện tại: máy có 8 core vật lý/16 logical, khoảng
15,4 GB RAM nhưng lúc đo chỉ còn khoảng 4,4 GB khả dụng, và PyTorch không thấy CUDA.

## 2. Baseline đo thật

Mỗi tài liệu được ingest bằng một process CLI mới, artifact root mới và `doc_id` mới nên chắc chắn cache miss.
Thời gian gồm đọc file, khởi tạo dependency, Docling, adapter, chunk/window và ghi artifact.

| Tài liệu | Trang | Section / chunk | Ingest lạnh | Cache-hit median | Giảm khi dùng cache |
|---|---:|---:|---:|---:|---:|
| `nhap_mon_hoc_may...pdf` | 20 | 27 / 41 | 203,584 s | 1,001 s | 99,51% |
| `xstk-ch3-1.pdf` | 59 | 43 / 126 | 245,689 s | 1,326 s | 99,46% |
| `Baocaocanhan_NgoCongThanh.docx` | — | 27 / 26 | 14,965 s | 0,884 s | 94,09% |
| `5_Naive Bayes Classifier.pdf` | 36 | 32 / 40 | 352,430 s | 0,882 s | 99,75% |
| **Tổng lạnh tuần tự** | | | **816,668 s — 13 phút 37 giây** | | |

Cache-hit được đo ba process độc lập cho mỗi tài liệu và lấy median. Artifact của bốn tài liệu chỉ khoảng
3,32 MiB; dung lượng và JSON I/O không phải nút thắt.

## 3. Bằng chứng từ code và profile

| Quan sát | Bằng chứng | Hệ quả |
|---|---|---|
| Parse cache được kiểm trước Docling | [`ingest_document.py`](../src/doc2roadmap/application/use_cases/ingest_document.py), đoạn `find_parse()` | Giữ nguyên artifact root + `doc_id` là tối ưu lớn nhất và không cần sửa code. |
| Chunk cache được kiểm sau khi đã chunk | `chunk_document()` chạy trước `save_chunks()` trong cùng file | Warm run vẫn tốn 98–740 ms chunk và khoảng 456 ms nạp tokenizer. |
| CLI chỉ nhận một file và dựng dependency mới | [`main.py`](../src/doc2roadmap/presentation/cli/main.py), [`composition.py`](../src/doc2roadmap/composition.py) | Mỗi process lại nạp pipeline/model; batch cùng process chưa tận dụng converter cache. |
| Parser đã cache converter trong instance | [`docling_parser.py`](../src/doc2roadmap/infrastructure/parsing/docling_parser.py), `_get_converter()` | Có thể thêm batch mà không cần abstraction/parser mới. |
| OCR và nhận dạng bảng đang bật mặc định | `_new_converter()` chỉ đặt ảnh; Docling mặc định `do_ocr=True`, `do_table_structure=True`, TableFormer ACCURATE | PDF có text nhúng vẫn có thể mất nhiều phút cho OCR/bảng. |
| Xuất markdown bảng tạo serializer lặp | `_table_text()` được gọi 51 lần trên XSTK | Reuse một serializer có thể tiết kiệm khoảng 4 giây cho XSTK mà giữ output byte-for-byte. |

Micro-profile cache-hit:

| Công đoạn | Khoảng thời gian |
|---|---:|
| Khởi tạo SentencePiece mỗi process | 456 ms |
| Đọc source + SHA-256 | 2–7 ms |
| Tìm/nạp parse artifact | 4–28 ms |
| Chạy lại `chunk_document()` | 98–740 ms |
| Nạp chunk artifact đã tồn tại | 3–17 ms |

## 4. Thử nghiệm cấu hình Docling

Kiểm text layer bằng `pypdfium2` đã có trong môi trường:

| PDF | Trang có trên 20 ký tự native text | Tổng ký tự native | Nhận định |
|---|---:|---:|---|
| Nhập môn ML | 20/20 | 36.810 | Ứng viên tắt OCR, nhưng phải review khác biệt text. |
| XSTK | 59/59 | 98.524 | Ứng viên tắt OCR tốt. |
| Naive Bayes | 34/36, có trang bằng 0 | 9.587 | Không tắt OCR toàn tài liệu. |

Kết quả A/B `do_ocr=False` giữ nguyên scale ảnh và nhận dạng bảng:

| Tài liệu | Docling convert không OCR | So với gold | Kết luận |
|---|---:|---|---|
| Nhập môn ML | 43,705 s | Đúng 27 section, 41 chunk, 9 ảnh, 1 công thức và 23.759 chữ cái; **digest chunk đổi** | Tiềm năng khoảng 4–5×, chưa an toàn để bật mặc định. Cần diff text trước. |
| XSTK | 221,774 s | Đúng toàn bộ 43 section, 126 chunk, 5 ảnh, 51 bảng, 263 công thức, 53.219 chữ cái và digest | An toàn trên corpus hiện tại nhưng chỉ nhanh hơn khoảng 24 giây; nhận dạng bảng mới là nút thắt. |

Profile XSTK không OCR ghi `pipeline_total=220,235 s`, trong đó tổng thời gian các batch
`table_structure=205,188 s`. Các stage chạy pipeline song song nên không cộng các tổng stage với nhau; con số
này chỉ dùng để xác định điểm nóng.

## 5. Bảng kế hoạch triển khai

| Ưu tiên | Việc | Loại | Lợi ích dự kiến | Rủi ro | Tiêu chí hoàn thành |
|---:|---|---|---|---|---|
| P0 | Chuẩn hoá vận hành: luôn tái dùng đúng `artifact_dir`, `doc_id`, source và parser config | Không sửa code | Tái ingest còn 0,88–1,33 s; giảm 94–99,75% | Không | CLI báo “tái dùng parse tree”; không sinh parse version mới. |
| P1 | Thêm benchmark lạnh/warm dùng native `ConversionResult.timings` của Docling | Test/tool nhỏ | Biết chính xác OCR/layout/table trên từng corpus; tránh tối ưu đoán | Không đổi production | Báo wall time và `page_parse/ocr/layout/table/doc_assemble`; root lạnh luôn mới. |
| P2 | Thêm lệnh ingest batch tuần tự, dựng `IngestDocument` đúng một lần | Sửa nhỏ CLI | Tránh nạp converter/model lại cho từng file; lợi rõ hơn với nhiều file ngắn | Thấp | Output/gold giống ingest từng file; lỗi một file được báo rõ; đo tổng bốn file thấp hơn baseline. |
| P3 | Thêm lookup chunk cache trước `chunk_document()` và lazy-load tokenizer | Sửa use case/composition | Warm run dự kiến giảm thêm khoảng 0,5–1,2 s | Thấp | Cache hit không gọi parser, chunker hoặc tokenizer; median mục tiêu dưới 0,35 s. |
| P4 | Reuse một `MarkdownDocSerializer` cho mọi bảng trong một document | Sửa adapter nhỏ | Tiết kiệm khoảng 4 s trên XSTK | Thấp | Markdown 51 bảng XSTK và 13 bảng slide giống byte-for-byte; gold đứng yên. |
| P5 | Thêm profile OCR `on/off`, mặc định vẫn `on`; đưa lựa chọn vào parser-config hash | Cấu hình parser | Nhập môn ML có tiềm năng giảm khoảng 160 s; XSTK khoảng 24 s | Trung bình: mất text trong ảnh | Gold/ref/letter count phải đứng yên; riêng Nhập môn phải giải thích và duyệt mọi diff trước khi dùng `off`. |
| P6 | A/B `TableFormerMode.FAST` trên XSTK và Naive Bayes | Cấu hình parser | Tiềm năng cao trên 51/13 bảng | Trung bình–cao: đổi cell/span/table ID | Giữ đủ 51/13 table refs; so từng `table_id`, markdown và digest; chỉ nhận nếu không suy giảm. |
| P7 | A/B `DOCLING_NUM_THREADS=4` và `8` | Cấu hình runtime | Có thể tăng throughput CPU | Thấp về chất lượng, chưa chắc nhanh do oversubscribe | Chạy ba vòng/cấu hình, lấy median; chỉ nhận nếu nhanh hơn ít nhất 10% và output giống gold. |
| P8 | Cân nhắc `images_scale=1.0` | Thay semantics ảnh | Giảm render, RAM và dung lượng | Trung bình: ảnh mờ hơn, image ID đổi | Chỉ làm khi đánh giá ảnh chứng minh scale 1 đủ; regenerate fixture và bump parser config/version. |

Thứ tự thực hiện đề xuất: **P0 → P1 → P2 → P3/P4 → P5 → P6 → P7**. P8 để sau vì ảnh là output bắt
buộc và hiện chưa có bằng chứng scale 2 là điểm nóng chính.

## 6. Những việc không nên làm lúc này

| Ý tưởng | Quyết định | Lý do |
|---|---|---|
| Chạy lạnh bốn process song song | Chưa làm | RAM khả dụng khoảng 4,4 GB; bốn pipeline PyTorch/OCR dễ swap hoặc lỗi. Chỉ thử hai worker sau khi đo peak RAM. |
| Tắt nhận dạng bảng | Không làm | Vi phạm output bắt buộc 51 bảng XSTK và 13 bảng slide. |
| Tắt trích ảnh | Không làm | Vi phạm contract ảnh và không xử lý điểm nóng OCR/table. |
| Tối ưu JSON, SHA hoặc temporary file trước | Không làm | Chỉ tốn mili-giây so với 15–352 giây Docling. |
| Cache parse toàn cục xuyên `doc_id` | Chưa làm | Đổi kiến trúc/ownership; chỉ đáng làm khi đo thấy nhiều source trùng dưới alias khác nhau. |
| Chỉ đặt `device="cuda"` | Không làm | PyTorch hiện là CPU-only và máy không có CUDA khả dụng; cấu hình đơn thuần sẽ lỗi. |

## 7. Cổng chất lượng bắt buộc

Mọi thay đổi có thể ảnh hưởng parse phải:

1. tham gia `parser_config_hash`, và bump adapter nếu thay semantics mặc định;
2. chạy số-vàng bốn tài liệu: section, chunk, ảnh/bảng/công thức, PUA, chữ cái, digest và warning;
3. giữ I9 (`char_start:char_end == chunk.text`) và không có ID trùng;
4. đo lạnh trên artifact root mới, rồi đo cache-hit ba lần lấy median;
5. chỉ nhận tối ưu khi nhanh hơn có ý nghĩa và không che mất nội dung.

## 8. Artifact của lượt đo

- Benchmark lạnh và ảnh DOCX:
  `tmp/b0-docx-full-ingest-benchmark-20260902/`.
- Diagnostic cache tạo parse/chunk hợp lệ `baocao-canhan/v3` trong `artifacts/`; không sửa source code.
