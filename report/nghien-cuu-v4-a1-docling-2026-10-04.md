# Nghiên cứu v4 — khâu A1 đọc PDF bằng docling 2.114: tốc độ, công thức, cây mục

Ngày: 2026-10-04 · Người viết: Claude (tác tử nghiên cứu) · Liên quan: v4 R-03, dòng A1 trong `task/v4/00-ke-hoach.md` [D7].

Báo cáo này trả lời bốn câu hỏi về khâu A1 dựa trên nguồn gốc: trước hết là mã docling đã cài (2.114.0) cùng các gói đi kèm, sau đó là tài liệu chính thức, bài báo gốc và thẻ mô hình. Tôi chỉ đọc mã, liệt kê tệp và chạy vài lệnh `python -c` nhỏ để in giá trị mặc định; không chạy đo hiệu năng, không gọi API trả tiền, không gửi nội dung tài liệu dự án ra ngoài. Ký hiệu `[M…]` là tệp mã đã cài, `[D…]` là tệp của dự án, `[L…]` là lệnh chạy tại máy ngày 2026-10-04, `[W…]` là trang web đọc ngày 2026-10-04; danh mục đầy đủ ở mục "Nguồn". Số dòng là của bản đã cài.

## Tóm tắt

Tám kết luận sau đây có căn cứ chi tiết ở các mục 1–4:

- **Pipeline song song theo trang đã là mặc định.** Trong 2.114, `PdfFormatOption` dùng `StandardPdfPipeline`, vốn là pipeline năm khâu, mỗi khâu một luồng, nối bằng hàng đợi có giới hạn; `ThreadedStandardPdfPipeline` chỉ là bí danh của nó và `ThreadedPdfPipelineOptions` không thêm trường nào [M1, M2, M6, L1]. Cấu hình `song_song_trang` trong script đo dở vì thế chỉ khác ở cỡ lô.
- **OCR có chạy trên PDF có lớp chữ, nhưng chỉ trên vùng ảnh bitmap.** docling quyết định OCR theo phần diện tích trang bị ảnh bitmap phủ (trên 5% thì OCR từng vùng ảnh, trên 75% thì OCR cả trang, đều ở 216 dpi), không xét trang đã có chữ hay chưa [M7, M9]. Phép đo cũ "tắt OCR không giúp" làm trên PDF tự sinh không có ảnh nên không thể thấy lợi; trên giáo trình thật có hình (7,2 giây/trang), log cho thấy RapidOCR đã chạy [D4, D5]. Đây là ứng viên tăng tốc lớn nhất, cần đo lại trên sách có hình.
- **Trên máy này OCR gần như không mang lại gì cho dự án.** Engine tự chọn là RapidOCR chạy torch với mô hình tiếng Trung PP-OCRv4, mà từ điển của nó thiếu 58 trên 67 chữ cái thường riêng của tiếng Việt (chữ có dấu và đ) [M8, M9, L5]; chữ OCR nằm trong hình cũng không tới được adapter, vì adapter duyệt `iterate_items()` mà hàm này mặc định không đi vào con của hình [D1, M33].
- **Số luồng là đòn bẩy "chỉ đổi tốc độ" đáng thử nhất, nhưng phải kiểm.** `num_threads` mặc định 4 trong khi máy có 8 nhân vật lý, và docling khuyên đặt bằng số nhân vật lý [M4, L3]. Không có bảo đảm đầu ra giống từng bit, vì thứ tự phép cộng dấu phẩy động có thể đổi theo số luồng và theo thành phần lô, mà lô layout trong pipeline đa luồng hình thành theo thời điểm [W17, M1].
- **Mọi tuỳ chọn tăng tốc khác đều đổi đầu ra.** Gồm TableFormer FAST (trọng số khác), mô hình bố cục egret-m (nhanh khoảng 1,9 lần trên CPU nhưng mAP thấp hơn heron 1,1–2,6 điểm theo bài báo), backend docling-parse đa luồng (bộ vẽ trang khác) và `images_scale` (đổi byte ảnh hình) [M43, W7, M18, D1].
- **Công thức:** `do_formula_enrichment=True` dùng CodeFormulaV2 (Idefics3 khoảng 0,3 tỉ tham số, BF16, giấy phép CDLA-Permissive-2.0) sinh LaTeX tự hồi quy cho từng vùng FORMULA, chạy sau khi lắp xong tài liệu nên cộng thẳng vào thời gian; không có số tốc độ chính thức [M23, M24, W8, W9]. Trên Windows CPU có hai rủi ro: `torch.compile` bật mặc định, và lỗi suy luận bị nuốt thành chuỗi rỗng [M26, M27, M23].
- **Cây mục:** mô hình bố cục chỉ gắn nhãn tiêu đề, không có cấp, nên mọi tiêu đề PDF ra cấp 1; bản 2.114 có sẵn `HeadingHierarchyOptions` (tắt mặc định) suy cấp theo bookmark, rồi đánh số, rồi cỡ chữ, và xếp `§ 1` vào họ "article" [M29, M3, W1]. Từ khoá chương, phần chỉ có tiếng Anh, và bước này chỉ đổi cấp của mục đã là tiêu đề.
- **Bộ nhớ parse của dự án không biết tuỳ chọn pipeline.** `parser_config` chỉ gồm `identifier` (phiên bản docling và backend), `adapter_version`, `image_scale` [D2, D1]; đổi tuỳ chọn mà không ghi vào đây thì parse cũ bị dùng lại âm thầm. Engine OCR tự chọn cũng phụ thuộc gói đã cài: chỉ cần có thêm `onnxruntime` là engine đổi trong khi định danh parser giữ nguyên [M8].

## 0. Phiên bản, máy và độ tin của tài liệu

Môi trường đọc được tại máy như sau [L1, L2, L3]:

- docling 2.114.0 (kèm docling-slim 2.114.0), docling-core 2.91.0, docling-ibm-models 3.14.0, docling-parse 7.12.1, torch 2.13.0+cpu, transformers 5.8.1, rapidocr 3.9.2, pypdfium2 5.12.1; không cài `onnxruntime`, `easyocr`, `tesserocr`; Python 3.12.11 (bản thường, không free-threaded).
- CPU AMD Ryzen 7 7730U, 8 nhân vật lý, 16 luồng logic, RAM 15,4 GB; torch là bản CPU, không có CUDA, MPS hay XPU, và `torch.get_num_threads()` mặc định 8.
- Mô hình đã tải sẵn: heron (bố cục), TableFormer accurate và fast (docling-models v2.3.0), RapidOCR torch PP-OCRv4 tiếng Trung và ONNX PP-OCRv6 (bản ONNX không dùng được vì thiếu `onnxruntime`); chưa có CodeFormulaV2, egret hay bản ONNX của heron [M41, M42, M43].

docling 2.114.0 phát hành 2026-07-20, bản mới nhất là 2.133.0 (2026-10-03) [W13]. Trang tài liệu chính thức mô tả bản mới nhất: ví dụ `use_reading_order_separators` và `NativePdfPipeline` có trong tài liệu [W1] nhưng không có trong bản đã cài [L4]. Vì vậy mọi kết luận về hành vi lấy mã đã cài làm chuẩn; tài liệu và bài báo chỉ dùng cho số đo và ý định thiết kế.

## 1. Tuỳ chọn tốc độ trong docling 2.114

### 1.1 Pipeline thực sự đang chạy

`DoclingParser._new_converter` dựng `PdfFormatOption(pipeline_options=PdfPipelineOptions(images_scale=2.0, generate_picture_images=True))` [D1 dòng 135–149]. `PdfFormatOption` mặc định có `pipeline_cls = StandardPdfPipeline` và `backend = DoclingParseDocumentBackend` [M6 dòng 216–219]; mặc định này đã được xác nhận khi chạy [L1].

`StandardPdfPipeline` là pipeline đa luồng gồm năm khâu `preprocess → ocr → layout → table → assemble`, mỗi khâu một luồng thợ, nối bằng `ThreadedQueue` có giới hạn `queue_max_size`; một luồng sản xuất đẩy từng trang vào khâu đầu [M1 `_create_run_ctx` dòng 682–739, `ThreadedPipelineStage` dòng 216–255, `_build_document` dòng 764–938]. Khâu `preprocess` và `assemble` có lô cố định 1; ba khâu còn lại dùng `ocr_batch_size`, `layout_batch_size`, `table_batch_size` [M1 dòng 411, 691–723]. Sau khi mọi trang xong, mức tài liệu chạy tuần tự: thứ tự đọc, suy cấp tiêu đề, cắt ảnh hình [M1 `_assemble_document` dòng 997–1058], rồi các bước làm giàu như công thức [M22 `_enrich_document` dòng 111–133].

Song song ở đây là chồng lấp giữa các khâu của cùng một tài liệu, không phải chia trang cho nhiều bản sao của một khâu: mỗi khâu chỉ xử lý một lô tại một thời điểm. `ThreadedStandardPdfPipeline` chỉ là lớp con rỗng "Backwards compatible import" [M2 dòng 1–5], và `ThreadedPdfPipelineOptions` không thêm trường nào so với `PdfPipelineOptions` [M3 dòng 1982–1993; L1].

Về câu hỏi "pipeline song song có cho kết quả y hệt pipeline tuần tự không": bản tuần tự cũ `LegacyStandardPdfPipeline` dùng cùng các mô hình và cùng hậu xử lý [M21 dòng 88–103], nên khác biệt chỉ đến từ ba chỗ đọc được trong mã:

- Thứ tự trang trong kết quả của bản đa luồng được sắp lại theo số trang trước khi lắp, nên không phụ thuộc trang nào xong trước [M1 `_integrate_results` dòng 949–951].
- Lô layout của bản đa luồng hình thành theo thời điểm: `get_batch` lấy tối đa `size` trang đang có ngay khi có ít nhất một trang [M1 dòng 184–201], còn bản cũ chia lô cố định theo `settings.perf.page_batch_size` = 4 [M22 dòng 264–266]. Nếu suy luận theo lô không bất biến về số học thì hai cách có thể khác ở bit cuối (chưa xác nhận).
- Bản cũ có lỗi khi cắt ảnh hình: `page_ix = element.prov[0].page_no - 1` rồi đem so với `p.page_no` vốn đánh số từ 1, nên ảnh hình lấy nhầm trang trước, và hình ở trang 1 làm hỏng phép `assert` [M21 dòng 221–228]. Không nên dùng bản cũ làm mốc so sánh khi bật `generate_picture_images`.

### 1.2 `AcceleratorOptions`: số luồng và thiết bị

Mặc định là `AcceleratorOptions(num_threads=4, device="auto")` [M4 dòng 32–55; L1]. Docstring của `num_threads` ghi "Recommended: number of physical CPU cores"; giá trị đọc được từ biến môi trường `DOCLING_NUM_THREADS`, và khi biến này không có thì lấy `OMP_NUM_THREADS` [M4 dòng 35–41, 81–110]. Tài liệu chính thức cũng ghi mặc định 4 luồng CPU [W1], và ví dụ chính thức đặt `num_threads=8, device=CPU` kèm bật đo thời gian [W4].

Các điểm cần biết khi đổi số luồng, đọc từ mã:

- Số luồng được áp bằng `torch.set_num_threads` lúc khởi tạo `LayoutPredictor` và `TFPredictor` [M11 dòng 59–60; M15 dòng 123–124], tức là thiết lập toàn tiến trình. RapidOCR bản torch không tự đặt số luồng nên dùng chung giá trị này [M41]. Hệ quả: trong một tiến trình, pipeline khởi tạo sau cùng quyết định số luồng cho mọi pipeline, nên mỗi cấu hình phải đo ở một tiến trình riêng.
- Giá trị mặc định của `accelerator_options` là một đối tượng `AcceleratorOptions()` tạo lúc import `pipeline_options` [M3 dòng 1184–1192], nên đặt biến môi trường sau khi đã import docling không có tác dụng với giá trị mặc định (suy ra từ mã). An toàn nhất là truyền `AcceleratorOptions(num_threads=…)` tường minh như script đo dở đang làm [D6 dòng 24].
- `device="auto"` đi qua `decide_device`: chọn CUDA, rồi MPS, rồi XPU nếu có, không thì CPU [M38]; máy này chỉ có CPU [L2]. Tài liệu GPU chính thức cho 7,9 trang/giây (RTX 5090) và 4,2 trang/giây (RTX 5070) với pipeline chuẩn tắt OCR [W2], nhưng đó là quyết định phần cứng triển khai, không áp dụng cho máy này.

Số đo chính thức về tác động của số luồng: Bảng 1 của báo cáo kỹ thuật (225 trang, OCR tắt) cho 375 giây ở 4 luồng và 244 giây ở 16 luồng trên Xeon E5-2690 với backend docling-parse (1,54 lần), 239 và 143 giây với pypdfium (1,67 lần), còn trên M3 Max chỉ 177 và 167 giây (1,06 lần) [W5]. Số đó thuộc docling năm 2024 với mô hình bố cục cũ, nên chỉ cho biết khoảng lợi ích, không thay được phép đo tại máy.

Về việc có đổi đầu ra không: số luồng không đổi logic nào trong docling. Tuy vậy tài liệu oneMKL của Intel liệt kê "variation in number of threads" là một yếu tố làm đổi thứ tự phép tính dấu phẩy động, và khi đó "the computed results may differ" [W17]; PyTorch cũng không bảo đảm tái lập hoàn toàn giữa các nền tảng [W16]. Vì vậy `num_threads` thuộc nhóm "kỳ vọng y hệt, bắt buộc kiểm" (mục 4.2).

### 1.3 Lô, hàng đợi và song song nhiều tài liệu

Giá trị mặc định là `ocr_batch_size = layout_batch_size = table_batch_size = 4`, `batch_polling_interval_seconds = 0.5`, `queue_max_size = 100` [M3 dòng 1908–1960; L1]. Đọc mã cho thấy các điểm sau:

- Chỉ khâu layout thực sự suy luận theo lô (`predict_batch` trên cả danh sách ảnh trang) [M10 dòng 181–184; M11 dòng 180–266]. Khâu OCR lặp từng trang [M9 `__call__` dòng 478–553], khâu bảng lặp từng trang và từng bảng [M14 `predict_tables` dòng 186–260], nên tăng `ocr_batch_size` hay `table_batch_size` không làm suy luận nhanh hơn trên CPU (suy ra từ mã).
- Tài liệu chính thức chỉ khuyên lô 64 cho GPU [W2]; không có khuyến nghị hay số đo cho CPU.
- `settings.perf.page_batch_size` (cờ `--page-batch-size` của CLI) không được `StandardPdfPipeline` dùng; nó chỉ dùng trong `PaginatedPipeline`, ví dụ bản tuần tự cũ [M22 dòng 264–266; M37 dòng 1048].
- `queue_max_size` và `batch_polling_interval_seconds` chỉ điều phối lịch chạy, nhưng có thể làm đổi thành phần lô layout, nên mang cùng loại rủi ro bit cuối như mục 1.1.
- Song song nhiều tài liệu trong một tiến trình: `convert_all` chỉ dùng `ThreadPoolExecutor` khi `doc_batch_concurrency > 1` và `doc_batch_size > 1` [M6 dòng 673–681], và chú thích ghi "Warning: Experimental! No benefit expected without free-threaded python." [M5 dòng 31]. Muốn song song nhiều sách thì dùng nhiều tiến trình; cách này giữ đầu ra từng sách nếu số luồng mỗi tiến trình như nhau, nhưng không giảm phút cho một cuốn.
- Chia một cuốn thành nhiều khoảng trang cho nhiều tiến trình sẽ đổi đầu ra ở biên cắt: bước gộp của thứ tự đọc nối khối TEXT qua ranh giới trang [M32 `predict_merges` dòng 171–211], và adapter dò tiêu đề đầu trang lặp dựa trên vị trí lặp ở ít nhất 3 trang [D1 dòng 419–425].

### 1.4 OCR: docling quyết định chạy OCR thế nào trên PDF có lớp chữ

Mặc định `do_ocr=True` với `OcrAutoOptions(lang=[], force_full_page_ocr=False, bitmap_area_threshold=0.05)` [M3 dòng 1770–1779, 1817–1825; L1].

**Engine nào được chọn.** `OcrAutoModel` thử lần lượt: ocrmac trên macOS, Nemotron trên Linux, RapidOCR với onnxruntime nếu import được `onnxruntime`, EasyOCR, cuối cùng RapidOCR với torch [M8 dòng 44–140]. Máy này chạy Windows, không có `onnxruntime` và `easyocr` [L1], nên rơi vào RapidOCR torch; `RapidOcrOptions` mặc định `lang=["chinese"]` [M3 dòng 237–245], ứng với bộ mô hình torch PP-OCRv4 mobile tiếng Trung [M9 dòng 41, 49–60]. Các tệp `ch_PP-OCRv4_det_mobile.pth` và `ch_PP-OCRv4_rec_mobile.pth` có sẵn trong `rapidocr/models` (ghi ngày 2026-08-13), cho thấy engine này đã từng chạy [M41]. Từ điển nhận dạng `ppocr_keys_v1.txt` có 6.623 ký hiệu nhưng trong 67 chữ cái thường riêng của tiếng Việt (chữ có dấu và đ) chỉ có 9 chữ `à á è é ì í ò ó ú` [L5]; những chữ như `ư ơ đ ê ô ă â` không thể xuất hiện trong kết quả OCR.

**Quyết định vùng OCR.** `BaseOcrModel.get_ocr_rects` [M7 dòng 49–127] làm như sau:

1. Lấy các hình chữ nhật ảnh bitmap của trang từ backend; với docling-parse là `bitmap_resources`, lấy mọi ảnh có diện tích dương [M18 dòng 185–201].
2. Vẽ chúng lên một mặt nạ nhị phân cỡ trang, giãn bằng nhân 20×20 để nhập các ảnh gần nhau, rồi tính phần diện tích trang bị phủ [M7 dòng 30, 55–101]. Vì đo trên mặt nạ đã giãn, phần phủ lớn hơn diện tích ảnh thật.
3. Nếu `force_full_page_ocr` bật hoặc phần phủ lớn hơn `max(0.75, bitmap_area_threshold)` thì OCR cả trang; nếu lớn hơn `bitmap_area_threshold` (0,05) thì OCR từng vùng đã giãn; còn lại không OCR [M7 dòng 110–127].

Việc trang đã có lớp chữ hay chưa không được xét. Một trang chữ có một hình chụp lớn vẫn bị OCR vùng hình; một trang có ảnh nền phủ trên 75% bị OCR cả trang dù chữ đã có sẵn.

**Chi phí và đường đi của chữ OCR.** Mỗi vùng được vẽ lại ở hệ số 3 (216 dpi) [M9 dòng 328, 494–500]; với backend docling-parse, pypdfium2 thực ra vẽ ở 1,5 lần hệ số rồi thu nhỏ, dưới khoá toàn cục `pypdfium2_lock` [M18 dòng 203–237]. Ô chữ OCR nào giao với bất kỳ ô chữ gốc nào của PDF đều bị bỏ [M7 `_filter_ocr_cells` dòng 130–154, `_combine_cells` dòng 187–201]. Các ô còn lại được gán vào cụm bố cục có độ chồng lớn nhất (tối thiểu 0,2); ô không thuộc cụm nào thành cụm TEXT mồ côi [M13 dòng 289–306, 605–637]; cụm thường nằm ít nhất 80% trong cụm PICTURE thành con của hình [M13 dòng 343–348]. Adapter lấy mục bằng `document.iterate_items()` [D1 dòng 410], mà hàm này mặc định `traverse_pictures=False` [M33 dòng 3305–3309]. Do đó chữ OCR chỉ tới được `DocumentNode` trong ba trường hợp: cụm mồ côi không nằm đủ 80% trong hình; vùng chỉ có ảnh mà mô hình bố cục gắn nhãn TEXT, FORMULA hay TABLE (ví dụ công thức dán dưới dạng ảnh); và trang quét.

**Bằng chứng về thời gian.** Bài AAAI đo docling 2.5.2 trên x86 CPU 8 luồng: "transcribing a page with EasyOCR took … 13 s on the x86 CPU", và "Disabling OCR saves 60% of runtime on the x86 CPU" [W6]; báo cáo kỹ thuật ghi EasyOCR mất "upwards of 30 seconds per page" ở 216 dpi [W5]. Đó là EasyOCR, không phải RapidOCR, nên chỉ cho biết bậc độ lớn. Trong dự án, phép đo cũ cho 1,8 giây/trang trên PDF tự sinh và thấy `do_ocr=False` không nhanh hơn [D4 dòng 49–58, 71–85]; nhưng chính ghi chú đó đã đính chính rằng bench "chạy trên PDF tự sinh, không có ảnh nào, nên OCR không có gì để làm", còn giáo trình thật `nhap-mon-ml` có hình đo được 7,2 giây/trang [D4 dòng 43–46]. Log của lần đo thật có dòng `RapidOCR returned empty result!` [D5 dòng 132–133]; dòng này nằm trong vòng lặp qua các vùng OCR nên chỉ phát ra khi `get_ocr_rects` trả về ít nhất một vùng [M9 dòng 491–509]. Vậy OCR đã chạy trên giáo trình đó, và kết luận "tắt OCR không giúp" trong F5 không áp dụng cho sách có hình. Giả thuyết cần đo: phần lớn khoảng chênh 1,8 → 7,2 giây/trang là OCR vùng hình (chưa xác nhận; bảng và mục lục cũng có thể góp phần).

**Có đổi đầu ra không.** Có, nhưng chỉ trên trang có ảnh bitmap phủ trên 5%, và chỉ ở những mục nhận chữ OCR như trên. Với tiếng Việt, phần chữ đó lại thiếu dấu do từ điển, nên nhiều khả năng bỏ OCR làm mất chữ rác hơn là mất nội dung (chưa xác nhận, phải đọc từng khác biệt). Một phương án giữa là `bitmap_area_threshold=0.75`: khi đó chỉ trang có ảnh phủ trên 75%, gần như trang quét, mới bị OCR, và OCR cả trang [M7 dòng 110–127]; `OcrAutoModel` chuyển ngưỡng này sang engine được chọn [M8 dòng 88–97, 126–135]. Tắt OCR còn bỏ luôn việc nạp mô hình RapidOCR, vì engine chỉ được tạo khi `enabled` [M8 dòng 44; M1 dòng 655–664].

**Rủi ro tái lập.** Vì engine được chọn theo gói đã cài, chỉ cần một gói khác kéo theo `onnxruntime` là engine đổi sang RapidOCR ONNX PP-OCRv6 [M8 dòng 83–102; M9 dòng 42–47], trong khi `identifier` của parser chỉ ghi phiên bản docling và backend [D1 dòng 157–160]. Nếu giữ OCR, nên ghim engine tường minh, ví dụ `RapidOcrOptions(backend="torch")`.

### 1.5 Bảng: `do_table_structure`, `TableFormerMode`, `do_cell_matching`

Mặc định `do_table_structure=True` và `TableStructureOptions(mode=ACCURATE, do_cell_matching=True)` [M3 dòng 122–143, 1761–1769, 1808–1816; L1]. Trọng số lấy từ `docling-project/docling-models` bản `v2.3.0` [M14 dòng 100–108]. Theo cấu hình đã tải, ACCURATE có 6 lớp mã hoá và 6 lớp giải mã (tệp 212,8 MB), FAST có 4 và 2 lớp (tệp 145,5 MB), cùng xương sống ResNet-18 và ảnh vào 448 điểm; giấy phép CDLA-Permissive-2.0 [M43].

Đặc điểm chạy đọc từ mã:

- TableFormer chỉ chạy trên trang có cụm TABLE hoặc DOCUMENT_INDEX (mục lục) [M14 dòng 203–216], nên trang mục lục của giáo trình cũng tốn thời gian bảng.
- Mỗi bảng được dự đoán riêng (`multi_table_predict` với một hộp) [M14 dòng 227–260], trên ảnh trang ở hệ số 2,0 [M14 dòng 93, 221–225] được thu về cao 1024 điểm trước khi cắt [M15 dòng 474]. Với `images_scale=2.0`, ảnh này lấy lại từ bộ nhớ đệm của trang [M17 dòng 500–502].
- `do_cell_matching=True` khớp ô dự đoán với ô chữ của PDF; `False` lấy chữ từ backend theo hộp dự đoán [M14 dòng 258–269; W1].
- `do_table_structure=False` khiến bảng thành `Table` rỗng, không ô, không chữ [M34 dòng 200–210], tức mất nội dung bảng.

Số đo chính thức: "Typical tables require between 2 and 6 seconds" trên CPU, không ghi chế độ [W5]; TableFormer FAST mất 1,74 giây mỗi bảng trên x86 CPU 8 luồng [W6]. Không có nguồn chính thức so sánh trực tiếp FAST với ACCURATE trên cùng máy, nên hệ số tăng tốc là chưa xác nhận. FAST dùng trọng số khác nên chắc chắn đổi đầu ra; tài liệu ghi ACCURATE là mặc định và cho chất lượng tốt hơn [W1; M3 dòng 135–143].

### 1.6 Ảnh: `images_scale`, `generate_picture_images`, `generate_page_images`

Mặc định `images_scale=1.0`, `generate_picture_images=False`, `generate_page_images=False`; dự án dùng `images_scale=2.0` và bật `generate_picture_images` [M3 dòng 1846–1873; D1 dòng 141].

Cơ chế đọc từ mã:

- Khâu `preprocess` luôn vẽ ảnh trang ở hệ số 1,0 cho mô hình bố cục và vẽ thêm ở `images_scale` [M16 dòng 52–66]; mỗi lần vẽ dùng pypdfium2 ở 1,5 lần hệ số rồi thu nhỏ, với cả hai backend [M18 dòng 203–237; M20 dòng 357–391].
- Khi bật `generate_picture_images` (hoặc `generate_page_images`), `keep_images=True` và ảnh trang của mọi trang được giữ tới cuối để cắt ảnh hình [M1 dòng 585–589, 666–676, 1020–1058]. Ước lượng thô theo kích thước ảnh RGB không nén của trang A4: khoảng 1,5 MB ở hệ số 1 và 6,0 MB ở hệ số 2, tức khoảng 3 GB cho 400 trang (ước lượng, chưa đo; máy có 15,4 GB [L3]).
- TableFormer luôn dùng hệ số 2,0 và làm giàu công thức luôn cắt ở hệ số 1,67, độc lập với `images_scale` [M14 dòng 93; M23 dòng 68].

Về đầu ra: `images_scale` chỉ đổi byte ảnh hình (và ảnh trang nếu bật). Adapter băm byte PNG thành `image_id` [D1 dòng 497–500]; `chunk_id` băm `doc_id`, `section_id`, chữ, chỉ số tách và lần xuất hiện [D3 dòng 102–109], còn chữ của nút hình là chú thích hoặc `[figure]` [D1 dòng 496]; vì vậy `chunk_id` không đổi nhưng tài sản ảnh đổi. `image_scale` đã nằm trong `parser_config`, nên đổi giá trị sẽ buộc parse lại [D2 dòng 210–214]. Tắt `generate_picture_images` làm mất byte ảnh hình và adapter ghi cảnh báo `missing_image` [D1 dòng 497–507]. Lợi ích tốc độ của việc hạ `images_scale` có lẽ nhỏ, vì khâu vẽ chạy chồng với khâu layout (chưa xác nhận; xem `timings["page_parse"]` ở mục 4).

### 1.7 Mô hình bố cục

Mặc định là heron: `LayoutOptions.model_spec = DOCLING_LAYOUT_HERON` (`docling-project/docling-layout-heron`) [M3 dòng 1419–1450; M12 dòng 91–96]. Cấu hình đã tải cho thấy `RTDetrV2ForObjectDetection`, xương sống ResNet-50 (độ sâu [3, 4, 6, 3]), 300 truy vấn, float32, tệp 171,66 MB, ảnh vào thu về 640×640 không đệm, giấy phép Apache-2.0 [M42]. Ảnh đưa vào là ảnh trang hệ số 1,0, tức 72 dpi [M10 dòng 172]; ngưỡng tin cậy gốc 0,3 [M11 dòng 31], sau đó hậu xử lý lọc theo ngưỡng riêng từng nhãn 0,45–0,5 [M13 dòng 175–193].

Các mô hình thay thế có sẵn trong 2.114 gồm heron-101, egret-medium/large/xlarge và mô hình cũ [M12 dòng 84–124]. Bảng dưới lấy từ Bảng 2, 3 và 5 của bài "Advanced Layout Analysis Models for Docling" [W7]; thời gian CPU đo trên AMD EPYC 7763, 4 luồng, lô 32, ảnh 640×640:

| Mô hình | Kiến trúc | Tham số | mAP DocLayNet / v2 / canonical | CPU giây/ảnh (trung bình) |
|---|---|---|---|---|
| heron (mặc định) | RT-DETRv2-r50vd | 42,9 M | 0,699 / 0,751 / 0,776 | 0,643 |
| heron-101 | RT-DETRv2-r101vd | 76,7 M | 0,696 / 0,758 / 0,780 | 0,988 |
| egret-m | D-FINE-m | 19,5 M | 0,686 / 0,725 / 0,765 | 0,334 |
| egret-l | D-FINE-l | 31,2 M | 0,672 / 0,724 / 0,747 | 0,472 |
| egret-x | D-FINE-x | 62,7 M | 0,671 / 0,727 / 0,753 | 0,808 |
| old-docling | RT-DETRv1-r50vd | 42,9 M | 0,505 / 0,667 / 0,541 | 0,603 |

egret-m là bản nhẹ duy nhất nhanh hơn rõ (khoảng 1,9 lần trên CPU), đổi lại mAP thấp hơn heron 1,3 / 2,6 / 1,1 điểm; thẻ mô hình ghi Apache-2.0 và 19,5 M tham số [W12]. Docstring của `LayoutOptions` gợi ý egret large/xlarge "for higher accuracy on complex documents" [M3 dòng 1426–1429], nhưng Bảng 3 của bài báo cho heron cao hơn cả hai trên cả ba tập [W7]; tôi theo bài báo.

Còn một đường khác là `LayoutObjectDetectionOptions` với engine ONNX Runtime và kho `docling-layout-heron-onnx` [M24 dòng 990–1006; M3 dòng 1453–1494; M39]. Đường này cần cài `onnxruntime`, mặc định `create_orphan_clusters=False` khác với `LayoutOptions` [M3 dòng 1472–1480], và tôi không tìm thấy số đo chính thức so ONNX với torch trên CPU (chưa xác nhận). Mọi thay đổi mô hình hay engine bố cục đều đổi cụm, tức đổi đầu ra.

### 1.8 Bộ đọc PDF

Backend mặc định `DoclingParseDocumentBackend` dùng docling-parse để giải mã ô chữ và ảnh bitmap, dùng pypdfium2 để vẽ trang và đo kích thước [M18 dòng 82–355]. Báo cáo kỹ thuật mô tả pypdfium "faster and more memory efficient than the default docling-parse backend" nhưng cho "worse quality results, especially in table structure recovery" [W5]; dự án dùng pypdfium2 cho doc-4 vì docling-parse tách rời âm tiết [D1 dòng 122–125].

Hai tuỳ chọn backend trong 2.114 đáng chú ý:

- `PdfBackendOptions.enforce_same_font` (mặc định `True`) có mô tả "Disable this when PDFs use separate fonts for base glyphs and diacritics that should remain in the same text cell" [M19 dòng 167–179]; giá trị được đưa vào `DecodeConfig` của docling-parse [M18 dòng 48–58, 283–290; M44 dòng 245–281]. Mô tả này khớp đúng triệu chứng "Ph ươ ng pháp" của doc-4, nên đáng thử như một sửa chất lượng, có thể cho phép bỏ nhánh pypdfium2 (đổi đầu ra; chưa thử trên doc-4). Cách truyền: `PdfFormatOption(pipeline_options=…, backend_options=PdfBackendOptions(enforce_same_font=False))` [M6 dòng 216–219].
- `ThreadedDoclingParseDocumentBackend` (với `ThreadedDoclingParseBackendOptions.parser_threads`, mặc định lấy `AcceleratorOptions().num_threads`) giải mã và vẽ trang bằng luồng gốc của docling-parse [M18 dòng 458–560; M19 dòng 182–194]. Nó vẽ ảnh trang bằng bộ vẽ của docling-parse thay vì pypdfium2 [M18 dòng 446–449], nên ảnh vào mô hình bố cục khác và đầu ra đổi. Backend này thành mặc định từ v2.123.0 [W14], và chỉ đáng thử nếu `page_parse` là nút thắt.

### 1.9 Giới hạn trang và thời gian

`convert(..., page_range=(a, b))` chỉ xử lý các trang trong khoảng [M1 dòng 755–762]; `max_num_pages` loại bỏ cả tài liệu nếu vượt chứ không cắt bớt [M35 dòng 205–213]; `document_timeout` (mặc định không đặt) dừng và trả `PARTIAL_SUCCESS` với các trang còn thiếu [M3 dòng 1171–1183; M1 dòng 847–863]. Các tuỳ chọn này hữu ích cho đo thử, không phải đòn bẩy cho sản phẩm.

### 1.10 Tuỳ chọn không giúp hoặc có hại

Các tuỳ chọn sau dễ bị thử nhầm nên ghi lại:

- `force_backend_text` không được `StandardPdfPipeline` dùng; chỉ pipeline VLM đọc nó (grep chỉ thấy trong `docling/pipeline/vlm_pipeline.py`) [M3 dòng 1798–1807].
- `layout_options.skip_cell_assignment=True` khiến cụm không có ô chữ, tức mất chữ [M13 dòng 249–260, 276–287].
- `force_full_page_ocr=True` OCR cả trang và thay hẳn ô chữ gốc bằng ô OCR [M7 dòng 110–122, 177–195]: chậm hơn và tệ hơn với PDF có lớp chữ.
- `generate_parsed_pages=True` chỉ tốn thêm bộ nhớ; chỉ cần khi dùng tín hiệu cỡ chữ ở mục 3 [M3 dòng 1883–1892].

### 1.11 Bảng tổng hợp

Bảng dưới gom mặc định, tác động tốc độ có nguồn và câu trả lời "có đổi đầu ra không":

| Tuỳ chọn | Mặc định 2.114 | Dự án | Tác động tốc độ (nguồn) | Đổi đầu ra? |
|---|---|---|---|---|
| `num_threads` | 4 | 4 | 4→16 luồng nhanh 1,06–1,67 lần toàn pipeline [W5] | Không đổi logic; có thể khác bit cuối, phải kiểm |
| `device` | auto (máy này: cpu) | auto | GPU 4,2–7,9 trang/giây [W2]; không áp dụng | — |
| `layout_batch_size` | 4 | 4 | Chỉ có khuyến nghị cho GPU [W2] | Có thể khác bit cuối |
| `ocr_batch_size`, `table_batch_size` | 4 | 4 | Gần như không, vì lặp từng trang và từng bảng [M9, M14] | Không |
| `queue_max_size`, `batch_polling_interval_seconds` | 100; 0,5 | mặc định | Gần như không | Không đổi logic |
| `do_ocr=False` | True | True | Bớt 60% thời gian (EasyOCR, x86) [W6]; giả thuyết nút thắt của sách có hình [D4, D5] | Có, trên trang có ảnh phủ >5% |
| `bitmap_area_threshold=0.75` | 0,05 | 0,05 | Như trên nhưng giữ OCR trang quét | Có, ít hơn |
| `TableFormerMode.FAST` | ACCURATE | ACCURATE | 1,74 giây/bảng ở FAST [W6]; 2–6 giây/bảng, không ghi chế độ [W5] | Có |
| `do_cell_matching=False` | True | True | Không có số | Có |
| `images_scale=1.0` | 1,0 | 2,0 | Có lẽ nhỏ; bớt khoảng 3 GB RAM cho 400 trang (ước lượng) | Có (byte ảnh hình) |
| egret-m | heron | heron | Khâu layout 0,334 so với 0,643 giây/ảnh [W7] | Có |
| Backend docling-parse đa luồng | không | không | Chỉ khi `page_parse` là nút thắt | Có |
| `doc_batch_concurrency` | 1 | 1 | "No benefit expected without free-threaded python" [M5] | — |

## 2. Nhận dạng công thức chạy tại máy

### 2.1 Công thức trong đầu ra hiện nay

Khi không bật làm giàu, cụm FORMULA được thêm bằng `add_text(label=FORMULA, text="", orig=cap_text)`: chữ rỗng, chữ gốc của PDF nằm ở `orig` [M31 dòng 392–397]; khi xuất Markdown, docling-core ghi `<!-- formula-not-decoded -->` [M45 dòng 293]. Adapter lấy `text or raw_text`, băm thành `formula_id`, và ghi chữ của nút là `[formula]` [D1 dòng 533–536]. Công thức chỉ thành mục FORMULA khi mô hình bố cục gắn nhãn vùng đó là công thức; công thức nằm trong dòng của đoạn văn vẫn là ô chữ thường của cụm TEXT (suy ra từ cách gán ô vào cụm [M13 dòng 605–637]). Vì vậy làm giàu công thức chỉ chạm tới công thức đứng riêng.

### 2.2 `do_formula_enrichment` trong 2.114

Bật bằng `PdfPipelineOptions(do_formula_enrichment=True)`, mặc định `False` [M3 dòng 1789–1797]. Khi đó `StandardPdfPipeline` thêm `CodeFormulaVlmModel` vào đầu chuỗi làm giàu, với tuỳ chọn mặc định là preset `codeformulav2` [M1 dòng 621–642; M3 dòng 1063–1065, 1836–1845]. Thông tin mô hình và cách chạy:

- Mô hình là `docling-project/CodeFormulaV2` [M24 dòng 1530–1552]. Thẻ mô hình ghi 0,3 B tham số, BF16, giấy phép CDLA-Permissive-2.0, huấn luyện trên SynthCodeNet và SynthFormulaNet, ảnh vào 120 DPI, đầu ra là mã LaTeX cho công thức [W8]. Tệp cấu hình là `Idefics3ForConditionalGeneration` với bộ mã hoá ảnh 512 điểm, mảnh 16, 12 lớp, và mô hình ngôn ngữ kiểu llama 30 lớp, chiều ẩn 576 [W9].
- Mỗi lô 5 phần tử; ảnh cắt từ backend trang ở hệ số 1,67 (120 dpi), nới hộp 18% [M23 dòng 67–69; M28 dòng 181–218]. Lời nhắc là `<formula>` [M23 dòng 135–152]; giải mã tham lam (`temperature=0.0`), tối đa 2048 token mới [M23 dòng 256–267].
- LaTeX ghi đè `item.text`, còn `orig` giữ chữ PDF [M23 dòng 283–287].
- Nếu suy luận lỗi, mã chỉ ghi log rồi trả chuỗi rỗng cho cả lô [M23 dòng 275–277]: lỗi bị nuốt im lặng thành công thức rỗng.
- Làm giàu chạy ở mức tài liệu, sau khi mọi trang đã xong, tuần tự từng lô [M22 dòng 111–133]; nó không chồng với các khâu theo trang nên thời gian cộng thẳng vào tổng. Bật nó cũng giữ backend của mọi trang mở tới cuối [M1 dòng 644–652].

Trang "Enrichment features" của tài liệu vẫn dẫn tới thẻ `ds4sd/CodeFormula` (bản 1: MIT, 0,2 B, gốc SAM và OPT) [W3, W10], trong khi bản 2.114 mặc định dùng CodeFormulaV2 [M3 dòng 1063–1065]; tôi theo mã.

### 2.3 Rủi ro khi chạy trên Windows CPU

Preset dùng engine `AUTO_INLINE`; trên Windows không có CUDA, engine này chọn Transformers [M25 `_select_engine` dòng 71–151]. Hai điểm cần đề phòng khi đo:

- `TransformersVlmEngineOptions.compile_model` mặc định lấy `settings.inference.compile_torch_models`, vốn là `True` [M27 dòng 84–87; M5 dòng 55], và engine bọc mô hình bằng `torch.compile` khi cờ này bật [M26 dòng 266–277]. Trên Windows, việc biên dịch có thể cần bộ công cụ C++ của máy (chưa xác nhận trên máy này); nếu hỏng ở lần gọi đầu, lỗi sẽ bị nuốt thành công thức rỗng như ở 2.2.
- Kiểu số lấy từ preset là `bfloat16` [M24 dòng 1545; M26 dòng 232–238]; trên CPU không có lệnh BF16 gốc, BF16 có thể chậm hơn float32 (chưa xác nhận).

Có thể ghi đè bằng `CodeFormulaVlmOptions.from_preset("codeformulav2", engine_options=TransformersVlmEngineOptions(compile_model=False, torch_dtype="float32"))` [M24 dòng 623–660; M27] (chưa chạy thử). Khi đo phải đếm số công thức có `text` rỗng sau làm giàu để bắt lỗi im lặng.

### 2.4 Thời gian

Không có số tốc độ chính thức cho CodeFormulaV2; tài liệu chỉ cảnh báo các bước làm giàu "may increase the processing time consistently" [W3]. Theo cơ chế ở 2.2, thời gian xấp xỉ tỉ lệ với số mục FORMULA nhân với độ dài LaTeX sinh ra, vì mỗi công thức là một lần sinh tự hồi quy. Cần đo giây/công thức trên 30–50 công thức mẫu của doc-1 trước khi quyết định.

### 2.5 Lựa chọn mở khác

Trong docling 2.114 chỉ có hai preset cho công thức và mã: `codeformulav2` và `granite_docling` [M3 dòng 1037–1039]. `granite_docling` dùng `ibm-granite/granite-docling-258M` [M24 dòng 925–946, 1554–1565]: Apache 2.0, 258 M tham số, siglip2-base-patch16-512 cộng Granite 165M, hỗ trợ lệnh "Convert formula to LaTeX." [W11]. Mã docling luôn gửi lời nhắc `<formula>` bất kể preset [M23 dòng 147–150], nên việc Granite-Docling có hiểu lời nhắc này không là chưa xác nhận.

Ngoài docling có các mô hình mở chạy tại máy, nhưng phải tự tích hợp và kéo thêm chồng phụ thuộc khác:

- PP-FormulaNet của PaddleOCR/PaddleX (Apache-2.0): tài liệu PaddleX cho thời gian CPU mỗi công thức từ 254 ms (PP-FormulaNet-S) tới khoảng 3.126 ms (PP-FormulaNet_plus-L) trên Xeon Gold 6271C 8 luồng; bản plus-M mất 1.616 ms với Zh-BLEU 89,76% [W18].
- UniMERNet (Apache-2.0): ba cỡ từ 441 MB tới 1,3 GB, không công bố tốc độ [W19].
- LaTeX-OCR, tức pix2tex (MIT): bộ mã hoá ViT có xương sống ResNet và bộ giải mã transformer, BLEU 0,88 [W20].

### 2.6 Ảnh hưởng tới chunk

Vì adapter luôn ghi `[formula]` vào chữ của nút công thức [D1 dòng 533–536], bật làm giàu một mình chỉ đổi `raw_text` và `formula_id` của nút công thức, không đổi chữ chunk, nên theo `_chunk_id` thì `chunk_id` không đổi [D3 dòng 102–109]. Muốn LaTeX giúp cửa sổ định nghĩa (doc-1: 71% có `[formula]` [D7]) thì phải sửa adapter hoặc khâu cắt chunk để đưa LaTeX vào chữ: đó là thay đổi đầu ra, cần tăng `ADAPTER_VERSION` và chạy lại các khâu sau.

## 3. Nhận diện tiêu đề và cây mục

### 3.1 Mặc định: mọi tiêu đề PDF ở cấp 1

Mô hình bố cục chỉ gắn nhãn SECTION_HEADER (và TITLE), không có cấp; mã docling ghi rõ "every heading produced by the PDF path defaults to level=1 and the document hierarchy is flattened" [M3 dòng 1650–1652; M29 dòng 3–5]. Bước thứ tự đọc gọi `add_heading(text=…, prov=…)` [M31 dòng 386–391] với `level=1` mặc định [M33 dòng 1917–1921]. Adapter lấy `item.level`, nên mọi tiêu đề từ PDF vào dự án đều cấp 1 [D1 dòng 478–483]; cây mục hiện do dự án tự dựng.

### 3.2 `HeadingHierarchyOptions`

Bản 2.114 có sẵn bước suy cấp `HeadingHierarchyModel`, thêm từ v2.106.0 với ghi chú "Infer PDF heading levels so the hierarchy isn't flattened" (#3633) [W14]. Mặc định `enabled=False`, `use_bookmarks=True`, `use_numbering=True`, `use_style=True`, `numbering_schemes=None`, `max_level=6`, `bookmark_match_threshold=0.8` [M3 dòng 1647–1741; L1]. Bước này chạy ngay sau thứ tự đọc [M1 dòng 1008–1009], và mục lục PDF chỉ được đọc khi nó bật [M1 dòng 777–781]. Tài liệu chính thức có mục "Recover PDF heading levels" với đúng API này, kèm dòng `generate_parsed_pages = True  # required by the font-style signal` [W1].

Thuật toán đọc từ mã [M29] dùng ba tín hiệu theo thứ tự ưu tiên:

- Bookmark: so khớp mờ tiêu đề (SequenceMatcher, có thử bỏ số đầu dòng, nâng điểm lên 0,92 khi chuỗi này chứa chuỗi kia) và lọc theo trang; ngưỡng tăng thêm 0,1 khi bookmark không có trang; mục danh sách khớp chắc được nâng thành tiêu đề [M29 dòng 278–293, 309–391]. Mục lục đọc qua docling-parse chỉ có tên và cây, không có trang hay toạ độ [M30 docstring và `extract_outline_from_docling_parse` dòng 146], còn qua pypdfium2 thì có trang và vị trí [M30 `extract_outline_from_pdfium` dòng 95].
- Đánh số: thứ tự họ `part > chapter > article > roman_u > arabic > alpha_u > alpha_l > roman_l`, số chấm (1.1, 1.1.1) xếp dưới `arabic` theo độ sâu [M29 dòng 43–52, 177–198]. Từ khoá là tiếng Anh: `part|title|book`, `chapter`, `article|section|clause|schedule|annex|appendix|rule`; mẫu `^§+\s*\d` được xếp vào họ `article` [M29 dòng 63–74, 108–130]. Các mức có mặt được nén thành cấp liên tục [M29 dòng 193–198].
- Cỡ chữ: trung vị chiều cao các dòng chữ PDF chồng lên tiêu đề, làm tròn, cỡ lớn hơn là cấp cao hơn [M29 dòng 201–248]; cần `generate_parsed_pages=True`, nếu không tín hiệu này bị bỏ qua im lặng [M3 dòng 1664–1667, 1701–1710].

Bước này chỉ viết lại cấp: không thêm, bớt hay đổi thứ tự mục, trừ việc nâng mục danh sách khớp bookmark; tiêu đề không có tín hiệu nào giữ nguyên cấp [M29 dòng 21–25, 427–471]. Lõi `assign_heading_levels(document, parsed_pages=None, outline=None)` chạy được trên một `DoclingDocument` trần [M29 dòng 394–401, 427–445], nên có thể thử tín hiệu đánh số trên tài liệu đã chuyển đổi và lưu JSON mà không chạy lại A1.

### 3.3 Áp vào tài liệu dự án

Ba nhận xét cho dự án:

- Với tài liệu bài giảng dạng `§1.`, `§2.`: nếu docling gắn nhãn các dòng này là SECTION_HEADER, tín hiệu đánh số xếp chúng vào họ `article`, trên `1.` và `1.1` [M29 dòng 43–52, 68]. Nếu chúng bị gắn nhãn TEXT thì bước này không cứu được, vì chỉ mục danh sách khớp bookmark mới được nâng [M29 dòng 374–388]. Việc đầu tiên nên làm là xem nhãn của các dòng `§` trong `DoclingDocument` của xstk.
- Từ khoá chương, phần chỉ có tiếng Anh; "Chương 1", "Phần I" không khớp họ từ khoá nào, và vì không mở đầu bằng số nên cũng không có dấu đánh số, sẽ rơi xuống tín hiệu cỡ chữ (suy ra từ các regex [M29 dòng 63–74, 108–130]). Số, `§`, bookmark và cỡ chữ không phụ thuộc ngôn ngữ, phù hợp nguyên tắc đa ngôn ngữ của dự án.
- Bật bước này đổi `level` của nút tiêu đề, kéo theo `section_id` và `chunk_id` [D3 dòng 102–109]. Chi phí ở mức tài liệu: đánh số và cỡ chữ tuyến tính theo số tiêu đề, còn bookmark tốn số bookmark nhân số ứng viên phép so khớp chuỗi (chưa đo).

## 4. Khuyến nghị đo tại máy

### 4.1 Vệ sinh đo

Các quy tắc sau giúp số đo so được với nhau:

- Mỗi cấu hình chạy ở một tiến trình riêng, vì `torch.set_num_threads` áp cho cả tiến trình và pipeline tạo sau ghi đè pipeline tạo trước [M11, M15].
- Bật `settings.debug.profile_pipeline_timings = True` trước khi convert, rồi đọc `res.timings[k].count` và `res.timings[k].total()` [M36 dòng 42–67; W4]. Các khoá có trong pipeline này: `page_parse` (mỗi trang: vẽ ảnh và giải mã) [M16 dòng 45], `ocr` (mỗi trang) [M9 dòng 490], `layout` (mỗi lô, chỉ phần suy luận) [M10 dòng 181], `table_structure` (mỗi trang) [M14 dòng 196], `page_assemble` [M34 dòng 161], `reading_order` [M31 dòng 444], `doc_assemble` [M1 dòng 999], `doc_enrich` [M22 dòng 122], `pipeline_total` [M22 dòng 74–76]. Các khâu chạy chồng nhau nên tổng từng khâu có thể vượt `pipeline_total`; khâu có tổng lớn nhất là nút thắt.
- Đếm số trang đã OCR: `ocr` ghi một mẫu cho mỗi trang, và trang không có vùng ảnh chỉ tốn thời gian của `get_ocr_rects` nên gần bằng 0; xem phân bố `res.timings["ocr"].times` để tách hai nhóm.
- Khởi động một trang trước khi bấm giờ (script đã làm), và gọi docling trực tiếp để không trúng bộ nhớ parse của dự án [D2 dòng 242].
- Bản làm việc chưa commit lúc tôi đọc đã có thay đổi của một vé khác: `ingest_document.py` ghi `parse_runtime_seconds` vào manifest của parse và `docling_parser.py` thêm `page_count` vào `parse_stats` [D2 dòng 246–258, 297–299; D1 dòng 586]. Hai số này cho phút/cuốn ở mức ingest, nhưng không tách được khâu bên trong docling.
- Bộ đo nên có `nhap-mon-ml` (nhiều hình, chính tài liệu 7,2 giây/trang), doc-1 (công thức), một tài liệu nhiều bảng và mục lục, xstk (`§`), doc-4 (nhánh pypdfium2). Ngoài khoảng 40–50 trang để so nhanh, chạy cả cuốn ít nhất một lần để có phút/cuốn.
- Máy là CPU di động [L3], nên chạy xen kẽ các cấu hình và lặp lại để thấy nhiễu do nhiệt.

### 4.2 Cách kiểm "đầu ra y hệt"

Nên kiểm bốn tầng, từ chặt nhất tới tầng quyết định:

1. Dấu vân tay `DoclingDocument`: băm `export_to_dict()` sau khi bỏ `origin` và `name` (tên tệp tạm khác nhau giữa các lần), so chặt với `coord_precision=None` và so nới với `coord_precision=2` để tách rung toạ độ khỏi khác biệt cấu trúc [M33 dòng 3648–3655].
2. So từng mục: lập danh sách `(nhãn, text, orig, level, trang, hộp làm tròn, ô bảng)` bằng `iterate_items(traverse_pictures=True)`, rồi dùng `difflib` để chỉ ra mục khác; thêm diff Markdown để người đọc.
3. Tầng adapter: băm danh sách nút từ `DoclingParser().adapt(document, filename)` theo `node_type, text, raw_text, level, page, table_rows, image_id, formula_id` [D1 dòng 407–604].
4. Tầng chunk: chạy `chunk_document` với đúng counter, splitter và tham số như ingest, rồi so tập `chunk_id` [D3 dòng 390; D2]. Tầng 4 giống nhau nghĩa là không phải chạy lại khâu sau; tầng 1 giống nhau mới là "chỉ đổi tốc độ" đúng nghĩa.

Trước mọi so sánh, chạy cấu hình hiện tại hai lần. Nếu tầng 1 đã khác giữa hai lần thì mốc vốn không tất định (do thành phần lô layout, mục 1.1), và khi đó nên thử thêm `layout_batch_size=1` để cố định lô. Đoạn mã gợi ý cho tầng 1 và 2 (chưa chạy):

```python
import difflib, hashlib, json

def van_tay(doc, coord_precision=None):
    d = doc.export_to_dict(coord_precision=coord_precision)
    for khoa in ("origin", "name"):
        d.pop(khoa, None)
    goc = json.dumps(d, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(goc.encode("utf-8")).hexdigest()

def cac_muc(doc):
    hang = []
    for item, _ in doc.iterate_items(traverse_pictures=True):
        prov = item.prov[0] if getattr(item, "prov", None) else None
        grid = getattr(getattr(item, "data", None), "grid", None)
        hang.append(repr((
            str(getattr(item.label, "value", item.label)),
            getattr(item, "text", None), getattr(item, "orig", None), getattr(item, "level", None),
            prov.page_no if prov else None,
            tuple(round(v, 1) for v in prov.bbox.as_tuple()) if prov else None,
            [[c.text for c in row] for row in grid] if grid else None,
        )))
    return hang

khac = list(difflib.unified_diff(cac_muc(doc_moc), cac_muc(doc_thu), lineterm=""))
```

### 4.3 Thứ tự cấu hình

Thứ tự dưới đặt các cấu hình kỳ vọng chỉ đổi tốc độ lên trước, rồi tới cấu hình đổi đầu ra theo mức lợi dự kiến; mỗi bước so với mốc theo mục 4.2:

1. Mốc: cấu hình hiện tại, chạy hai lần, bật đo thời gian; ghi thời gian từng khâu, số trang đã OCR, số trang có bảng hoặc mục lục.
2. `num_threads=8` (số nhân vật lý), thêm 6 và 16 để thấy đường cong; kỳ vọng y hệt, phải kiểm cả bốn tầng.
3. `layout_batch_size` bằng 1, 8, 16; kỳ vọng lợi nhỏ trên CPU, đồng thời trả lời câu hỏi tất định.
4. `do_ocr=False`: kỳ vọng lợi lớn nhất trên sách nhiều hình; đọc từng mục khác biệt và phân loại thành "rác OCR" hay "nội dung thật bị mất" (công thức dạng ảnh, bảng dạng ảnh, trang quét).
5. Nếu bước 4 làm mất nội dung của trang quét: `bitmap_area_threshold=0.75`.
6. Chỉ khi `table_structure` chiếm phần lớn thời gian: `TableFormerMode.FAST`, so bảng từng ô (trọng số FAST đã có sẵn trong bộ nhớ đệm [M43]).
7. Chỉ khi `layout` vẫn chiếm phần lớn sau các bước 2–5: egret-m (cần tải mô hình), kèm đánh giá chất lượng đầy đủ.
8. Chỉ khi `page_parse` là nút thắt: backend docling-parse đa luồng.
9. Chỉ khi thiếu RAM: `images_scale=1.0`.

Song song với dãy trên là các phép thử chất lượng; chúng tốn thêm thời gian chứ không bớt:

- `enforce_same_font=False` với docling-parse trên doc-4, so với nhánh pypdfium2 hiện tại.
- Suy cấp tiêu đề: trước hết chạy `assign_heading_levels` (chỉ đánh số) trên JSON đã lưu của xstk và `nhap-mon-ml`, sau đó mới bật đủ ba tín hiệu với `generate_parsed_pages=True`.
- Làm giàu công thức trên 30–50 công thức của doc-1 với `compile_model=False`, so float32 với bfloat16; ghi giây/công thức và số công thức rỗng.

### 4.4 Dự kiến lợi ích

Bảng dưới chỉ là kỳ vọng để xếp thứ tự đo, không thay được số đo:

| Cấu hình | Khâu chịu tác động | Số có nguồn | Ước lượng cho máy này | Độ tin |
|---|---|---|---|---|
| `do_ocr=False` | ocr | Tắt OCR bớt 60% thời gian (EasyOCR, x86) [W6]; 1,8 so với 7,2 giây/trang [D4, D5] | Tới khoảng 4 lần trên sách nhiều hình, nếu khoảng chênh đến từ OCR | Trung bình |
| `num_threads=8` | layout, bảng, OCR torch | 4→16 luồng: 1,06–1,67 lần [W5] | 1,0–1,5 lần phần suy luận | Thấp–trung bình |
| `layout_batch_size` | layout | Chỉ có số cho GPU [W2] | 0–10% | Thấp |
| TableFormer FAST | bảng, mục lục | 1,74 giây/bảng ở FAST [W6] | Chỉ trên trang bảng | Thấp |
| egret-m | layout | 0,334 so với 0,643 giây/ảnh [W7] | Khoảng 1,9 lần khâu layout | Trung bình |
| `images_scale=1.0` | page_parse, RAM | Không có | Nhỏ; bớt khoảng 3 GB RAM cho 400 trang | Thấp |

Một kịch bản lạc quan, chưa xác nhận: nếu OCR giải thích khoảng chênh giữa 1,8 và 7,2 giây/trang và số luồng cho thêm khoảng 1,3 lần, sách 400 trang nhiều hình giảm từ khoảng 48 phút xuống khoảng 9–12 phút, còn đầu ra chỉ khác ở chữ OCR.

### 4.5 Nhận xét về script đo dở

Script `tmp/thu-a1/do_toc_do_parse.py` [D6] dùng được làm khung, với các sửa sau:

- Docstring ghi đường chạy `scripts/thu-a1/…` nhưng tệp nằm ở `tmp/thu-a1/` [D6 dòng 7].
- Thang cấu hình cộng dồn (`khong_ocr` đã gồm 16 luồng, `bang_nhanh` gồm cả tắt OCR, và tiếp tục như vậy) [D6 dòng 23–44], nên không quy được khác biệt đầu ra về từng tuỳ chọn; nên đổi một yếu tố mỗi lần so với mốc, rồi mới chạy tổ hợp tốt nhất.
- `song_song_trang` dùng `ThreadedStandardPdfPipeline`, chính là pipeline mặc định [M2]; thực chất nó chỉ đổi cỡ lô từ 4 lên 8, trên nền đã tắt OCR, dùng FAST và ảnh hệ số 1.
- Mọi cấu hình chạy trong một tiến trình, nên số luồng của cấu hình sau có thể rò sang cấu hình trước [M11, M15].
- Jaccard trên tập dòng Markdown đo độ giống, không kiểm "y hệt"; nên thêm bốn tầng ở mục 4.2.
- `num_threads=16` là số luồng logic; nên thử 8 trước.
- Chưa bật `profile_pipeline_timings`, nên chưa biết khâu nào là nút thắt.

## Đề xuất cho v4

Các đề xuất dưới xếp theo lợi trên phút/cuốn và giữ nguyên tắc không hạ chất lượng:

1. **Vé đo A1 (Claude tự đo):** chạy dãy ở mục 4.3 trên bộ tài liệu ở mục 4.1, kiểm bốn tầng ở mục 4.2, ghi phút/cuốn và thời gian từng khâu. Đây là điều kiện trước mọi quyết định dưới.
2. **Số luồng:** nếu `num_threads=8` y hệt ở tầng 1 và nhanh hơn, đặt tường minh trong `_new_converter`; khi tầng 1 y hệt thì không cần đổi `parser_config`. Nếu chỉ tầng 4 y hệt, vẫn dùng được nhưng nên ghi nhận là parse có thể khác ở bit cuối khi chạy lại.
3. **OCR với PDF có lớp chữ:** nếu khác biệt của `do_ocr=False` chỉ là chữ OCR rác, tắt OCR (hoặc chỉ giữ OCR trang quét bằng `bitmap_area_threshold=0.75`) và ghi tuỳ chọn vào `parser_config` theo kiểu "chỉ ghi khi khác mặc định", như dự án đã làm với `strip_lines` và `heading_scheme` [D2 dòng 215–217, 238–241]; gom việc chạy lại các khâu sau vào cùng một lượt với các thay đổi đầu ra khác của v4. Nếu giữ OCR, ghim engine tường minh.
4. **Quy tắc chung cho mọi tuỳ chọn đổi đầu ra:** đưa tuỳ chọn vào `parser_config` (hoặc tăng `ADAPTER_VERSION`), vì bộ nhớ parse tra theo `parser_config_hash` [D2 dòng 210–218, 242].
5. **Chất lượng doc-4:** thử `enforce_same_font=False`; nếu chữ liền như pypdfium2 mà bảng tốt hơn, cân nhắc bỏ nhánh pypdfium2 (đổi đầu ra của doc-4).
6. **Cây mục:** thử `HeadingHierarchyModel` ngoại tuyến trên xstk và `nhap-mon-ml`; nếu cấp đúng, quyết định adapter dùng `level` của docling hay giữ cách dựng cây hiện tại. Kiểm trước nhãn của các dòng `§`.
7. **Công thức:** đo giây/công thức; nếu chấp nhận được, quyết định đưa LaTeX vào chữ chunk (đổi chunk) hay chỉ chạy cho công thức trong cửa sổ định nghĩa (cần thiết kế riêng).
8. **Không nâng cấp docling trong v4**, trừ khi gom vào một lượt chạy lại lớn. Các bản sau 2.114 có thay đổi về tốc độ: 2.116.0 chuyển sang "Layout-driven OCR pipeline with configurable OCR modes" [W14, W15], 2.122.0 "Speed up layout and table cell matching" (PR #3380 ghi đầu ra cũ và mới khớp nhau trên bench tổng hợp) [W14, W15]. Nhưng chúng cũng đổi đầu ra: 2.123.0 mặc định backend docling-parse đa luồng, 2.128.0 "Refactor the docling-parse backend to remove pypdfium", 2.132.0 cập nhật thuật toán thứ tự đọc [W14]. `identifier` chứa phiên bản docling nên nâng cấp tự động buộc parse lại [D1 dòng 157–160].

## Điểm còn chưa xác nhận

Các điểm sau cần số đo tại máy hoặc nguồn khác trước khi dùng làm căn cứ:

- Phần của OCR trong 7,2 giây/trang của `nhap-mon-ml` (giả thuyết từ mã và log, chưa đo theo khâu).
- `num_threads` và cỡ lô layout có cho đầu ra giống từng bit không; mốc hiện tại có tất định giữa hai lần chạy không.
- Hệ số tăng tốc của số luồng, của FAST so với ACCURATE, và của ONNX so với torch trên máy này.
- `do_ocr=False` có làm mất nội dung thật nào trong bộ tài liệu dự án không.
- `enforce_same_font=False` có chữa được tách âm tiết của doc-4 không.
- Nhãn docling gán cho các dòng `§1.`, `§2.` của xstk.
- Giây/công thức của CodeFormulaV2 trên CPU này; `torch.compile` có chạy được trên Windows của dự án không; BF16 có chậm hơn float32 không.
- Granite-Docling có hiểu lời nhắc `<formula>` không.
- Mức RAM thực khi giữ ảnh trang hệ số 2 cho 400 trang (con số 3 GB là ước lượng).
- Các mục CHANGELOG chưa đối chiếu trang phát hành: 2.126.0 cập nhật thuật toán thứ tự đọc, 2.131.0 dựng chỉ mục đối tượng trang một lần cho pypdfium2, 2.133.0 cho chọn cỡ mô hình RapidOCR [W21].

## Nguồn

Mã đã cài, đường dẫn tính từ `C:\Users\ngoco\Desktop\Doctoroadmap\.venv\Lib\site-packages\` (docling 2.114.0, docling-core 2.91.0, docling-ibm-models 3.14.0, docling-parse 7.12.1, rapidocr 3.9.2), đọc ngày 2026-10-04:

- [M1] `docling/pipeline/standard_pdf_pipeline.py` — `ThreadedQueue.get_batch`, `ThreadedPipelineStage`, `PreprocessThreadedStage`, `StandardPdfPipeline` (`_init_models`, `_make_ocr_model`, `_release_page_resources`, `_create_run_ctx`, `_build_document`, `_integrate_results`, `_assemble_document`).
- [M2] `docling/pipeline/threaded_standard_pdf_pipeline.py` — `ThreadedStandardPdfPipeline`.
- [M3] `docling/datamodel/pipeline_options.py` — `TableFormerMode`, `TableStructureOptions`, `OcrOptions`, `OcrAutoOptions`, `RapidOcrOptions`, `CodeFormulaVlmOptions`, `PipelineOptions`, `LayoutOptions`, `LayoutObjectDetectionOptions`, `HeadingHierarchyOptions`, `PdfPipelineOptions`, `ThreadedPdfPipelineOptions`.
- [M4] `docling/datamodel/accelerator_options.py` — `AcceleratorOptions`, `check_alternative_envvars`.
- [M5] `docling/datamodel/settings.py` — `BatchConcurrencySettings`, `DebugSettings`, `InferenceSettings`.
- [M6] `docling/document_converter.py` — `FormatOption`, `PdfFormatOption`, `DocumentConverter._convert`, `_get_pipeline`.
- [M7] `docling/models/base_ocr_model.py` — `BaseOcrModel.get_ocr_rects`, `_filter_ocr_cells`, `post_process_cells`, `_combine_cells`.
- [M8] `docling/models/stages/ocr/auto_ocr_model.py` — `OcrAutoModel.__init__`.
- [M9] `docling/models/stages/ocr/rapid_ocr_model.py` — bảng đường dẫn mô hình, `RapidOcrModel.__init__` (`self.scale = 3`), `RapidOcrModel.__call__`.
- [M10] `docling/models/stages/layout/layout_model.py` — `LayoutModel.__init__`, `predict_layout`.
- [M11] `docling_ibm_models/layoutmodel/layout_predictor.py` — `LayoutPredictor.__init__` (`base_threshold`, `torch.set_num_threads`), `predict_batch`.
- [M12] `docling/datamodel/layout_model_specs.py` — `DOCLING_LAYOUT_HERON`, `DOCLING_LAYOUT_EGRET_*`, `DOCLING_LAYOUT_HERON_101`, `DOCLING_LAYOUT_V2`.
- [M13] `docling/utils/layout_postprocessor.py` — `LayoutPostprocessor.CONFIDENCE_THRESHOLDS`, `postprocess`, `_process_regular_clusters`, `_process_special_clusters`, `_assign_cells_to_clusters`.
- [M14] `docling/models/stages/table_structure/table_structure_model.py` — `TableStructureModel.__init__`, `download_models`, `predict_tables`.
- [M15] `docling_ibm_models/tableformer/data_management/tf_predictor.py` — `TFPredictor.__init__`, `multi_table_predict`.
- [M16] `docling/models/stages/page_preprocessing/page_preprocessing_model.py` — `PagePreprocessingModel.__call__`, `_populate_page_images`.
- [M17] `docling/datamodel/base_models.py` — `Page.get_image`.
- [M18] `docling/backend/docling_parse_backend.py` — `_make_docling_parse_decode_config`, `_make_docling_parse_page_content_config`, `DoclingParsePageBackend.get_bitmap_rects`, `get_page_image`, `DoclingParseDocumentBackend`, `ThreadedDoclingParsePageBackend`, `ThreadedDoclingParseDocumentBackend`.
- [M19] `docling/datamodel/backend_options.py` — `PdfBackendOptions`, `ThreadedDoclingParseBackendOptions`.
- [M20] `docling/backend/pypdfium2_backend.py` — `PyPdfiumPageBackend.get_page_image`.
- [M21] `docling/pipeline/legacy_standard_pdf_pipeline.py` — `LegacyStandardPdfPipeline.__init__`, `_assemble_document`.
- [M22] `docling/pipeline/base_pipeline.py` — `BasePipeline.execute`, `_enrich_document`, `PaginatedPipeline._build_document`.
- [M23] `docling/models/stages/code_formula/code_formula_vlm_model.py` — `CodeFormulaVlmModel`.
- [M24] `docling/datamodel/stage_model_specs.py` — `StagePresetMixin.from_preset`, `GRANITE_DOCLING_MODEL_SPEC_BASE`, `OBJECT_DETECTION_LAYOUT_HERON`, `CODE_FORMULA_CODEFORMULAV2`, `CODE_FORMULA_GRANITE_DOCLING`.
- [M25] `docling/models/inference_engines/vlm/auto_inline_engine.py` — `AutoInlineVlmEngine._select_engine`, `initialize`.
- [M26] `docling/models/inference_engines/vlm/transformers_engine.py` — nạp mô hình, `torch_dtype`, `torch.compile`.
- [M27] `docling/datamodel/vlm_engine_options.py` — `TransformersVlmEngineOptions` (`compile_model`, `torch_dtype`).
- [M28] `docling/models/base_model.py` — `BaseItemAndImageEnrichmentModel.prepare_element`.
- [M29] `docling/models/stages/heading_hierarchy/heading_hierarchy_model.py` — `_parse_marker`, `_infer_from_numbering`, `_infer_from_style`, `_match_score`, `_infer_from_bookmarks`, `HeadingHierarchyModel.assign_heading_levels`.
- [M30] `docling/utils/pdf_outline.py` — `extract_outline_from_pdfium`, `extract_outline_from_docling_parse`.
- [M31] `docling/models/stages/reading_order/readingorder_model.py` — `_handle_text_element`, `ReadingOrderModel.__call__`.
- [M32] `docling_ibm_models/reading_order/reading_order_rb.py` — `predict_merges`.
- [M33] `docling_core/types/doc/document.py` — `DoclingDocument.add_heading`, `iterate_items`, `export_to_dict`.
- [M34] `docling/models/stages/page_assemble/page_assemble_model.py` — `PageAssembleModel.__call__`.
- [M35] `docling/datamodel/document.py` — kiểm `max_num_pages` trong `InputDocument`.
- [M36] `docling/utils/profiling.py` — `TimeRecorder`, `ProfilingItem`.
- [M37] `docling/cli/main.py` — tuỳ chọn `num_threads`, `--page-batch-size`.
- [M38] `docling/utils/accelerator_utils.py` — `decide_device`.
- [M39] `docling/models/stages/layout/layout_object_detection_model.py`, `docling/models/inference_engines/object_detection/onnxruntime_engine.py` — đường bố cục qua engine phát hiện đối tượng.
- [M41] `rapidocr/models/` (tệp mô hình PP-OCRv4 torch, PP-OCRv6 ONNX, `ppocr_keys_v1.txt`) và `rapidocr/inference_engine/pytorch/` (không gọi `set_num_threads`).
- [M42] Bộ nhớ đệm Hugging Face `C:\Users\ngoco\.cache\huggingface\hub\models--docling-project--docling-layout-heron\snapshots\8f39ad3c0b4c58e9c2d2c84a38465abf757272d8\` — `config.json`, `preprocessor_config.json`, `README.md`, kích thước `model.safetensors`.
- [M43] Bộ nhớ đệm Hugging Face `C:\Users\ngoco\.cache\huggingface\hub\models--docling-project--docling-models\snapshots\fc0f2d45e2218ea24bce5045f58a389aed16dc23\` — `model_artifacts/tableformer/{accurate,fast}/tm_config.json`, kích thước tệp trọng số, `README.md`.
- [M44] `docling_parse/pdf_parser.py` — `DecodeConfig`, `_compile_decode_config`.
- [M45] `docling_core/transforms/serializer/markdown.py` — chuỗi `<!-- formula-not-decoded -->`.

Tệp của dự án, đọc ngày 2026-10-04; số dòng là của bản làm việc lúc đọc, có cả thay đổi chưa commit của một vé chạy song song:

- [D1] `src/doc2roadmap/infrastructure/parsing/docling_parser.py` — `PDF_BACKENDS`, `DoclingParser._new_converter`, `identifier`, `adapt`, hằng `IMAGE_SCALE`, `FORMULA_TEXT`.
- [D2] `src/doc2roadmap/application/use_cases/ingest_document.py` — dựng `parser_config`, `config`, gọi `find_parse` (dòng 209–242).
- [D3] `src/doc2roadmap/domain/chunking.py` — `_chunk_id` (dòng 102–109), `chunk_document` (dòng 390).
- [D4] `feedback/F5-hieu-nang-docling.md` — số đo 1,8 giây/trang, đính chính 7,2 giây/trang, phép thử `do_ocr=False`.
- [D5] `feedback/F8-chunk-vun-va-mat-mat-im-lang.md` — bảng 1,83 và 7,23 giây/trang, log RapidOCR (dòng 117–133).
- [D6] `tmp/thu-a1/do_toc_do_parse.py` — script đo dở.
- [D7] `task/v4/00-ke-hoach.md` — dòng 29 (A1).

Lệnh chạy tại máy ngày 2026-10-04 (không đo hiệu năng):

- [L1] `.venv/Scripts/python.exe -c …` in phiên bản gói qua `importlib.metadata` và giá trị mặc định của `PdfPipelineOptions`, `ThreadedPdfPipelineOptions`, `HeadingHierarchyOptions`, `TableStructureOptions`, `OcrAutoOptions`, `RapidOcrOptions`, `LayoutOptions`, `CodeFormulaVlmOptions`, `PdfBackendOptions`, `settings`, `PdfFormatOption`.
- [L2] `python -c` in thông tin torch: `2.13.0+cpu`, `torch.version.cuda=None`, `cuda.is_available()=False`, XPU không có, `os.cpu_count()=16`, `torch.get_num_threads()=8`.
- [L3] PowerShell `Get-CimInstance Win32_ComputerSystem` và `Win32_Processor`: AMD Ryzen 7 7730U, 8 nhân, 16 luồng logic, RAM 15,4 GB.
- [L4] grep `use_reading_order_separators|NativePdfPipeline` trong `docling`, `docling_core`, `docling_ibm_models` đã cài: không có kết quả.
- [L5] Đếm 67 chữ cái thường riêng của tiếng Việt (chữ có dấu và đ) trong `rapidocr/models/ppocr_keys_v1.txt`: có 9, thiếu 58; tệp có 6.623 ký hiệu.

Trang web, đọc ngày 2026-10-04:

- [W1] https://docling-project.github.io/docling/usage/advanced_options/ — mục "Control PDF table extraction options", "Recover PDF heading levels", "Use visible PDF rules for reading order", "Extract the native content of a PDF", "Limit resource usage".
- [W2] https://docling-project.github.io/docling/usage/gpu/ — cấu hình lô cho GPU và bảng trang/giây.
- [W3] https://docling-project.github.io/docling/usage/enrichments/ — "Formula Understanding", cảnh báo thời gian.
- [W4] https://raw.githubusercontent.com/docling-project/docling/main/docs/examples/run_with_accelerator.py — ví dụ chính thức về `AcceleratorOptions` và `profile_pipeline_timings`.
- [W5] https://arxiv.org/html/2408.09869v5 — Auer và cộng sự, "Docling Technical Report", bản 5 (2024-12-09): Bảng 1, OCR 216 dpi, TableFormer 2–6 giây, so sánh pypdfium.
- [W6] https://arxiv.org/html/2501.17887v1 — "Docling: An Efficient Open-Source Toolkit for AI-driven Document Conversion": mục "Profiling Docling's AI Pipeline" (docling 2.5.2).
- [W7] https://arxiv.org/html/2509.11720 — Livathinos và cộng sự, "Advanced Layout Analysis Models for Docling": Bảng 2, 3, 5.
- [W8] https://huggingface.co/docling-project/CodeFormulaV2 — thẻ mô hình.
- [W9] https://huggingface.co/docling-project/CodeFormulaV2/raw/main/config.json — tệp cấu hình.
- [W10] https://huggingface.co/ds4sd/CodeFormula — thẻ mô hình bản 1.
- [W11] https://huggingface.co/ibm-granite/granite-docling-258M — thẻ mô hình.
- [W12] https://huggingface.co/docling-project/docling-layout-egret-medium — thẻ mô hình.
- [W13] https://pypi.org/project/docling/#history và https://pypi.org/pypi/docling/2.114.0/json — ngày phát hành.
- [W14] Ghi chú phát hành: https://github.com/docling-project/docling/releases/tag/v2.106.0, https://github.com/docling-project/docling/releases/tag/v2.116.0, https://github.com/docling-project/docling/releases/tag/v2.122.0, https://github.com/docling-project/docling/releases/tag/v2.123.0, https://github.com/docling-project/docling/releases/tag/v2.128.0, https://github.com/docling-project/docling/releases/tag/v2.132.0.
- [W15] https://github.com/docling-project/docling/pull/3380 và https://github.com/docling-project/docling/pull/3710.
- [W16] https://docs.pytorch.org/docs/2.14/notes/randomness.html — PyTorch, "Reproducibility".
- [W17] https://www.intel.com/content/www/us/en/docs/onemkl/developer-guide-linux/2023-2/obtaining-numerically-reproducible-results.html — oneMKL, "Obtaining Numerically Reproducible Results".
- [W18] https://paddlepaddle.github.io/PaddleX/3.3/en/module_usage/tutorials/ocr_modules/formula_recognition.html — PaddleX, "Formula Recognition".
- [W19] https://github.com/opendatalab/UniMERNet — README.
- [W20] https://github.com/lukas-blecher/LaTeX-OCR — README.
- [W21] https://raw.githubusercontent.com/docling-project/docling/main/CHANGELOG.md — CHANGELOG.
