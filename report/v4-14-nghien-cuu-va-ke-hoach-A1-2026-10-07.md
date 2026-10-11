# v4-14 — Nghiên cứu và kế hoạch bộ nhận tiêu đề cho A1

Ngày: **2026-10-07** · **Chủ dự án đã duyệt; P0–P7 đã triển khai và đo xong.** Nội dung dưới đây giữ lại kế hoạch trước thí nghiệm, không phải kết quả nghiệm thu. Xem [báo cáo hoàn tất](v4-14-bo-nhan-tieu-de-2026-10-07.md): tốc độ đạt, chất lượng chưa đủ để thay A1; không tích hợp production.

Vé gốc: [14-hoc-nhan-tieu-de.md](../task/v4/14-hoc-nhan-tieu-de.md). Chủ dự án cho phép mở rộng hướng nghiên cứu, yêu cầu lập kế hoạch trước; sau đó đã duyệt bằng lời nhắn “duyệt, triển khai đi”. Các đoạn nói “chờ duyệt/chưa triển khai” bên dưới là nhật ký thời điểm bàn giao kế hoạch, không phải trạng thái hiện tại.

## 1. Kết luận đề xuất

**Nên thử mô hình phân loại dòng bằng đặc trưng bố cục, với LightGBM là ứng viên chính và hồi quy logistic là mốc học máy.** Giữ luật v4 làm mốc hiện hữu. Đơn vị suy luận là dòng PDF; bổ sung tín hiệu của dòng trước/sau cùng trang. Chưa cần CRF hay Transformer trong vòng đầu.

Lý do chọn là sự phù hợp với dự án: đã có lớp chữ, bộ trích dòng, nhãn bạc và môi trường CPU. Tiêu đề thường phụ thuộc tổ hợp cỡ chữ tương đối, độ đậm, khoảng cách, đánh số và vị trí. LightGBM có thể học tổ hợp đó mà không cần xây dựng lại bộ đọc. Đây là **giả thuyết cần đo**, chưa có kết quả mô hình trên 16 cuốn.

Đề xuất mở rộng vé ở **thiết kế nghiệm thu**, trước khi tăng độ phức tạp mô hình:

1. Ghim dữ liệu và căn nhãn bằng cả chữ, trang, vị trí; tách dòng chưa xác định khỏi lớp âm.
2. Giữ LOBO theo vé, thêm phép kiểm giữ riêng nhóm trường/nhà xuất bản để phát hiện học thuộc mẫu trình bày.
3. Giữ thước đo cũ để đối chiếu, đồng thời thêm thước đo không cho tiêu đề sai trang, trùng lặp hoặc chunk không chung nội dung được tính đúng.
4. Đo thử “gán tiêu đề bằng nhãn bạc đã căn được” để phân biệt lỗi phân loại với lỗi gom dòng/cấp mục.
5. Kết luận riêng về **bộ nhận tiêu đề** và **toàn bộ A1**. Không đổi mặc định A1 chỉ vì F1 tiêu đề tăng.

Phạm vi xin duyệt trong tài liệu này: **P0–P7 ở mục 6, CPU tại máy, 0 USD lời gọi mô hình**, xuất báo cáo cho sếp kiểm. Việc đưa vào luồng chính là quyết định sau báo cáo.

## 2. Nguồn khoa học đã kiểm

Đây là tra cứu có mục tiêu, không phải tổng quan hệ thống hay khẳng định đã tìm hết công trình liên quan. Đọc nguồn gốc để chọn thiết kế, không lấy số điểm ở tài liệu khoa học tiếng Anh làm bảo đảm cho giáo trình tiếng Việt.

| Nguồn | Biểu diễn, đặc trưng và mô hình | Cách đo, điều áp dụng vào dự án |
|---|---|---|
| [GROBID: How GROBID works](https://grobid.readthedocs.io/en/latest/Principles/), phần sequence labeling và layout tokens; [mã FeaturesVectorFulltext](https://raw.githubusercontent.com/kermitt2/grobid/master/grobid-core/src/main/java/org/grobid/core/features/FeaturesVectorFulltext.java) | Chuỗi mô hình; bộ phân vùng làm ở mức dòng, một số bộ khác ở mức token. Layout token mang chữ, font/cỡ/kiểu và hộp vị trí; có đặc trưng khoảng cách, thụt lề, vị trí tương đối. Có CRF và các lựa chọn học sâu. | Tài liệu giải thích cần bộ kiểm riêng và cảnh báo việc dùng lại bộ kiểm để chỉnh mô hình. Áp dụng đặc trưng tương đối và đánh giá tách sách; không suy diễn rằng CRF luôn tốt hơn GBDT. |
| Tkaczyk, Szostek, Fedoryszak, Dendek, Bolikowski (2015), [CERMINE](https://doi.org/10.1007/s10032-015-0249-8), §§4.2, 5.1–5.3 | Cây ký tự/từ/dòng/vùng; phân loại vùng bằng SVM. Xét 97 đặc trưng ban đầu về hình học, định dạng, từ vựng, chuỗi và thống kê chữ. Nhãn GROTOAP2 được căn từ JATS tới PDF bằng Smith–Waterman. | Báo P/R theo lớp và cross-validation. Nhãn tự động có sai số. Áp dụng nguyên tắc căn nhãn và báo coverage; không sao chép từ khóa metadata bài báo vào giáo trình. |
| Shen, Lo, Wang, Kuehl, Weld, Downey (2022), [VILA, TACL 10:376–392](https://aclanthology.org/2022.tacl-1.22/), [toàn văn](https://aclanthology.org/2022.tacl-1.22.pdf), [mã tác giả](https://github.com/allenai/VILA) | I-VILA đưa ranh giới nhóm dòng/khối vào đầu vào; H-VILA mã hóa nhóm theo phân cấp. Giả định token trong một nhóm thường cùng loại. | Đo macro-F1 và độ không nhất quán trong nhóm. §8 chỉ ra nhóm bị chia sai gây lỗi; §5.3 không tính PDF-to-text vào tốc độ mô hình. Ta dùng dòng/ngữ cảnh nhưng đo cả trích PDF; chưa dùng Transformer của VILA. |
| Ke và cộng sự (2017), [LightGBM, NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html) | GBDT tối ưu hiệu quả tính toán; bài trình bày GOSS và EFB. | Là căn cứ chọn họ mô hình cho đặc trưng số và CPU; không chứng minh hiệu quả nhận tiêu đề của dự án. Cấu hình dự kiến dùng GBDT thông thường, không mặc nhiên tuyên bố đã bật GOSS. |

### Quyết định giữa các phương án

| Phương án | Vai trò trong kế hoạch | Lý do |
|---|---|---|
| Luật v4 hiện có | Mốc bắt buộc | Đo trực tiếp lợi ích so với hệ đang nghiên cứu. |
| Logistic + đặc trưng dòng/ngữ cảnh | Mốc học máy | Rẻ, dễ kiểm tra hệ số; cho biết một ranh giới tuyến tính đã đủ chưa. |
| LightGBM + cùng đặc trưng | Ứng viên chính | Có sẵn trong môi trường; biểu diễn tương tác phi tuyến giữa font, khoảng cách, đánh số. |
| CRF | Hướng dự phòng trong báo cáo, chưa triển khai vòng này | Hợp khi lỗi chủ yếu là tính nhất quán chuỗi hoặc tiêu đề nhiều dòng; cần chứng minh vấn đề này trước khi thêm bộ gán nhãn chuỗi. |
| VILA/LayoutLM hoặc mô hình ảnh bố cục | Chưa chọn cho vòng CPU đầu tiên | Khác ngân sách tính toán và dữ liệu. Chưa có bằng chứng rằng chúng cần thiết để sửa nút thắt hiện tại. |

Skill `paper-lookup` được dùng để chọn nguồn, kiểm mã định danh và ghi lại truy vấn; `ponytail` ảnh hưởng quyết định tái sử dụng parser/chunker và bắt đầu bằng hai mô hình có sẵn. Nguồn phần mềm kỹ năng: Kassis, Agarwal, He, Patel, Brueckner (2026), [Scientific Agent Skills](https://arxiv.org/abs/2609.00065). Hồ sơ arXiv đã xác minh là v2, chưa ghi phiên bản xuất bản trên tạp chí; liên kết trỏ bản hiện hành.

## 3. Những gì đã kiểm trong dự án

### Dữ liệu hiện có

- 16 sách học, 8 lĩnh vực; metadata/cây hiện có ghi **2.990 trang, 33.027 nút, 4.698 nút tiêu đề bạc**. Đây là số nút Docling, **chưa phải số dòng được gán nhãn để học**.
- Bản parse pypdfium2 mới nhất: d01-01/02 v2; d01-03 v1; d01-04–07 v2; d01-08–13 v1; d01-14/15 v2; d01-16 v1.
- Bảy cây có `reviewed_text_cleanup`: d01-02/04/05/06/07/14/15. Nhãn đã sửa chữ có thể khác dòng đọc trực tiếp từ PDF. Không áp bảng sửa riêng từng cuốn như một năng lực tổng quát của mô hình.
- Manifest có **10 nhóm trường/nhà xuất bản**; riêng Trường Cao đẳng Đà Lạt có 7 sách: d01-05/06/11/13/14/15/16. Đây là nguy cơ trùng khuôn bố cục dù đã tách theo sách. Trường Đại học Đà Lạt là nhóm khác.
- Kiểm ngoài dự kiến ghim doc-1 parse v5, doc-4 v3, xstk-ch3-1 v3. Metadata hai bản doc-1/xstk ghi adapter `docling:2.114.0`, không ghi hậu tố pypdfium2; doc-4 có pypdfium2. Phải ghi khác biệt này khi chấm. Không tự chạy lại Docling để làm các mốc giống nhau.
- doc-1/doc-4/xstk đã được dùng chỉnh luật v4: gọi đúng là **kiểm chuyển giao trên bộ phát triển cũ**, không gọi kiểm mù mới. Hai PDF dưới `document-data/test/` chưa được mở trong công việc này và tiếp tục giữ riêng.

### Mã và điểm cần bảo vệ

- `scripts/thu-a1/doc_nhe.py`: trích ký tự → dòng → lọc lề → phân loại → gom nút. Luật tiêu đề đang nằm trong `parse`; có thể tách một điểm thay thế quyết định tiêu đề mà giữ đường mặc định.
- `doc_nhe.compare`: tìm tiêu đề trên toàn cuốn, dùng chứa chuỗi và có thể khớp nhiều-một. Vì vậy số cũ phù hợp so lịch sử nhưng quá dễ để nghiệm thu mới.
- `so_chunk_doc_nhe.compare`: tìm chunk theo Jaccard trong ±2 trang; vẫn tính cùng mục lá ngay cả khi Jaccard bằng 0, và so tập từ của tên mục bỏ thứ tự.
- `doc_nhe_rong.py` và `so_chunk_doc_nhe.py`: đã dùng đúng `chunk_document` và tokenizer. Nên tái sử dụng các hàm đó trong harness mới.
- Bộ đọc nhẹ chưa nhận bảng; luật mức tiêu đề còn đơn giản; hình được thêm sau các nút chữ. Những giới hạn này có thể giữ chất lượng chunk thấp ngay cả khi nhận diện tiêu đề tốt.
- `tmp/venv-ml` hiện có Python 3.12.11, LightGBM 4.7.0, scikit-learn 1.9.1, NumPy 2.5.2, joblib 1.6.0, underthesea 9.5.0; không có metadata pypdfium2 trong môi trường này. Phải chốt cách dùng dependency đã cài ở P0, không âm thầm đổi `pyproject.toml`.

## 4. Thiết kế dữ liệu và chống rò rỉ

### 4.1 Ghim và tái lập

Một manifest thí nghiệm ghi: ID sách, lĩnh vực, nhóm nguồn, đường dẫn được phép, SHA-256 PDF/cây, parse version, backend, cleaning, config chunk, phiên bản thư viện, mã nguồn thí nghiệm và seed 42. `latest` chỉ dùng lúc lập manifest; các lệnh sau đọc phiên bản đã ghim. Đổi dữ liệu/cấu hình thì tạo lượt đo mới, không ghi đè kết quả cũ.

Chỉ cho phép 16 đường dẫn `split=train` nằm thực sự trong `document-data/train/`, cộng ba đường dẫn kiểm ngoài cố định. Kiểm đường dẫn sau resolve; không duyệt đệ quy thư mục sách test. Model/dataset/kết quả ở `tmp/doc-nhe-v414/`; báo cáo và mã tái lập nằm trong repo.

### 4.2 Dòng và nhãn bạc

Trích toàn bộ dòng thô bằng `page_lines` → `describe`, giữ trang, hộp, font và văn bản trước/sau chuẩn hóa. Ghi riêng số dòng lề bị bộ đọc cũ bỏ; đánh giá số tiêu đề bạc bị mất ngay ở bước này. Tập phân loại chính là những dòng bộ đọc thực sự đưa đến bước nhận tiêu đề.

Nhãn tối thiểu: `tieu_de=1`, `khac=0`, `unknown=-1`. Không thêm phân lớp công thức/danh sách trong vòng đầu nếu không cần cho quyết định tiêu đề.

Quy tắc căn dự kiến, chốt bằng fixture trước khi chấm mô hình:

1. Chuẩn hóa chung NFC, khoảng trắng và phép làm sạch glyph đã dùng bởi bộ đọc; giữ raw text để truy ngược. Chưa dùng sửa chữ theo ID cuốn.
2. Chỉ so trong cùng trang. Chuẩn hóa hộp PDF về cùng hệ tọa độ; xác minh bằng ví dụ hình trước khi dùng.
3. Ưu tiên chuỗi token bằng nhau. Cho phép chứa **nguyên token liên tiếp** khi một nút trải nhiều dòng; phần được chứa phải có ít nhất 2 token hoặc 8 ký tự chữ. Chuỗi ngắn hơn chỉ xét exact cùng vị trí, không cho `1` khớp `11 Tổng quan`.
4. Khi có bbox, cần hỗ trợ về vị trí: tâm dòng nằm trong hộp nút với sai số tối đa nửa chiều cao dòng; không dùng một tiêu đề ở góc khác để gán dòng cùng chữ. Các ngưỡng này được cố định trước LOBO, không chọn lại theo điểm cuốn kiểm.
5. Nếu dòng chứa cả tiêu đề và đoạn thân bài không thể tách đáng tin, hoặc hai nút khác loại cùng giải thích dòng, gán `unknown`. `khac` chỉ khi đã có đối sánh không-tiêu-đề đáng tin.
6. Báo matched/unmatched/ambiguous trên **tất cả dòng**, trên dòng giữ lại và coverage của tiêu đề bạc theo từng cuốn. P/R/F1 trên dòng đã căn được phải ghi rõ mẫu số có điều kiện.

Nhãn bạc sai và lỗi căn nhãn là hai vấn đề riêng. Không sửa nhãn kiểm theo dự đoán của mô hình để nâng điểm; các trường hợp cần duyệt được xuất kèm trang/bbox/nút nguồn.

Trước khi qua P2, kiểm **80 dòng, 5 dòng/cuốn**: hai đối sánh tiêu đề (ưu tiên có exact), một đối sánh không-tiêu-đề, một containment và một unknown/ambiguous nếu có. Chọn bằng seed 42 trong các tầng; ghi tầng thiếu và cách bù, ưu tiên phủ ca nhiều dòng, glyph sửa và cùng chữ khác vị trí. Lưu kết luận/lý do của từng mẫu cùng số lỗi căn nhãn. Lỗi cơ chế như sai trang, sai hệ tọa độ, chứa một phần số hoặc gán unknown thành âm phải được sửa và có test tái hiện trước khi học. Coverage thấp hoặc nhãn bạc còn tranh cãi được phép tiếp tục nghiên cứu với cảnh báo, nhưng không đủ căn cứ đề xuất tích hợp.

### 4.3 Đặc trưng

Nhóm bản thân dòng: cỡ chữ/chữ thân bài, đậm, nghiêng; tỉ lệ hoa/chữ/số/ký hiệu; số ký tự và token; lề và độ rộng tương đối; độ lệch khỏi tâm trang; khoảng trống trên/dưới theo chiều cao dòng; mẫu đánh số có sẵn; dấu kết câu; dấu tiếng Việt; font toán/đơn cách; vị trí trang; số trang có dòng lặp.

Nhóm ngữ cảnh: bản sao các đặc trưng bố cục chính của dòng trước/sau **cùng trang**, độ chênh cỡ chữ và font, cờ đầu/cuối trang. Không đi qua ranh giới trang một cách ngầm định.

Không đưa ID sách, tác giả/nhà xuất bản, tên tài liệu, nhãn Docling, raw font name được mã hóa theo cuốn hay nội dung tiêu đề đầy đủ vào feature vector. Có thể dùng “font giống hàng xóm” và “font toán” thay cho danh tính font. Chuẩn hóa tương đối bằng thống kê không nhãn của chính cuốn được phép vì khi suy luận cũng có cả cuốn; scaler học từ tập mẫu chỉ fit trên train.

Tỉ lệ token có dấu tiếng Việt hiện có là tín hiệu rẻ, **không đồng nghĩa** tỉ lệ âm tiết hợp lệ. Nếu thêm kiểm âm tiết hợp lệ, phải đặt tên riêng và đo chi phí; không gọi underthesea từng dòng nếu lợi ích chưa được chứng minh.

## 5. Thí nghiệm và thước đo định trước

### 5.1 Mô hình, chia tập

- M0: luật v4, giữ nguyên đầu ra mặc định.
- M1: logistic, `C=1`, `class_weight=balanced`, tối đa 1.000 vòng; scaler train-only.
- M2: LightGBM, 300 cây, 15 lá tối đa/cây, learning rate 0,05, min child samples 30, `class_weight=balanced`, seed 42, CPU 2 luồng; threshold 0,5. Đây là cấu hình đề xuất ban đầu, không phải cấu hình đã tối ưu.
- M3 (ablation): M2 bỏ đặc trưng hàng xóm, để đo ngữ cảnh có ích thật hay không. Không dùng ablation để chọn lại ngưỡng trên cuốn kiểm.
- LOBO 16 lượt: học 15 cuốn, dự đoán cuốn còn lại. Mọi fit, weighting, scaler chỉ thấy train. Dòng unknown không được tự chuyển thành âm tính.
- Kiểm nhóm nguồn: M2 giữ riêng lần lượt 10 nhóm publisher trong manifest; báo macro theo nhóm và từng cuốn. Đây là phép kiểm về nguồn, chưa khẳng định đúng bằng chia theo template thực tế.
- Full model học 16 cuốn dùng cho ba tài liệu kiểm ngoài. Ba tài liệu không tham gia chọn feature, ngưỡng hay early stopping. Cấu hình được chốt trước khi mở bảng điểm của chúng.
- Không tìm siêu tham số theo outer-LOBO. Nếu kết quả dẫn đến phiên bản thứ hai, phải ghi đó là vòng phát triển mới; mọi tuning dùng chia theo sách bên trong train hoặc để nghiên cứu tiếp sau báo cáo.

Ngưỡng quyết định **0,5 áp dụng cho M1/M2/M3**. Với `class_weight=balanced`, điểm mô hình chưa phải xác suất đúng đã hiệu chỉnh; dùng điểm để xếp thứ tự rà lỗi, không diễn giải là phần trăm chắc chắn.

### 5.2 Bốn tầng đo

| Tầng | Số cần báo | Vì sao |
|---|---|---|
| Căn nhãn | Dòng thô/giữ lại, matched/unmatched/ambiguous, số tiêu đề bạc được phủ/bị lọc | Tránh đạt F1 cao bằng cách chỉ chấm các ca dễ. |
| Dòng | TP/FP/FN, P/R/F1 lớp tiêu đề của M0/M1/M2/M3; mỗi cuốn, lĩnh vực; median và min | Accuracy toàn dòng bị lớp thân bài áp đảo. Không chỉ báo một micro-score. |
| Cây/chunk | Chạy cùng `chunk_document`, tokenizer, tham số ghim; báo heading R/P legacy và strict, cùng mục lá legacy/strict, Jaccard ≥0,8/0,5 hai chiều | Xác minh lợi ích ở đầu vào các bước sau. |
| Vận hành/toàn vẹn | Giây/cuốn, giây/trang, phút/cuốn, RAM đỉnh, kích thước model; chữ/công thức/bảng/hình và thứ tự đọc | Ngăn cải thiện một điểm bằng mất nội dung hoặc đổi phạm vi đo tốc độ. |

Strict heading: ghép một-một trong cùng trang, ưu tiên exact normalized token; containment có ranh giới và phần ngắn/độ dài phần dài ≥0,8. Có thể dùng matching hai phía tối đa để tránh thứ tự tham lam làm đổi điểm. Dòng tiêu đề bị tách/gộp sẽ chịu phạt ở phép đo nút này; báo riêng lỗi tách/gộp cùng với F1 dòng, không trộn hai đơn vị.

Strict leaf: chỉ xét đối sánh chunk trong ±2 trang có Jaccard ≥0,5, chọn ổn định khi hòa; tên mục lá phải bằng chuỗi token chuẩn hóa giữ đúng thứ tự. Báo cả tỷ lệ đối sánh đủ điều kiện và tỷ lệ đúng trên toàn bộ chunk gốc. Mẫu số chính không chỉ gồm các chunk đã ghép thành công.

Thêm chẩn đoán “silver oracle”: ở những dòng có nhãn chắc, dùng nhãn bạc thay quyết định mô hình; dòng unknown giữ luật v4. Chạy lại grouping/chunk để thấy khoảng cách còn lại do cấu trúc. **Đây là chẩn đoán có sử dụng nhãn kiểm, không phải mô hình triển khai hay upper bound tuyệt đối.**

Mọi bảng cây/chunk cho 16 sách phải dùng **dự đoán ngoài tập học của fold tương ứng**, kể cả khi model full16 đã được tạo. Bảng giữ riêng publisher dùng model đã loại cả nhóm đó. Chỉ ba tài liệu kiểm ngoài được chấm bằng full16.

Tốc độ: sau một lượt warm-up nhỏ, **cả 19 tài liệu** đo ba lần, xử lý tuần tự để tránh nhiễu do tranh CPU; 16 sách dùng model LOBO tương ứng. Mỗi lần đọc lại PDF, gồm trích dòng, feature, inference, gom nút; không tái dùng dataset đã cache trong thời gian công bố. Báo median cùng min/max, tách thời gian nạp model và chunk/scoring. Thời gian huấn luyện và dựng dataset báo riêng. Số lịch sử của Docling chỉ là tham khảo nếu điều kiện máy khác.

### 5.3 Kiểm 50 bất đồng và độ tin cậy

Sau khi giữ cố định kết quả LOBO, xuất 50 bất đồng: 25 sai dương, 25 sai âm nếu đủ; phân tầng qua sách/lĩnh vực, kiểu đánh số và điểm mô hình, không quá 5 mẫu/cuốn khi có đủ mẫu. Seed 42; nếu một tầng thiếu thì ghi cách bù. Mẫu gồm dòng trước/sau, trang/bbox, nhãn bạc, dự đoán, điểm và nguồn căn nhãn.

Người kiểm/agent đọc nội dung và bố cục để đánh dấu: lỗi mô hình; lỗi nhãn Docling; lỗi căn dòng; chữ hỏng; chưa phân xử. Agent review được ghi đúng là agent review, rồi bàn giao sếp kiểm; không tự gọi thành nhãn vàng đã được con người chứng nhận. Không suy ra độ chính xác toàn tập từ mẫu “50 bất đồng lớn”.

Độ quan trọng đặc trưng: báo gain của M2 và hệ số chuẩn hóa M1, gom theo nhóm feature; so với ablation M3. Không xem gain là quan hệ nhân quả, cũng không dùng bảng importance của full model để tuyên bố khả năng tổng quát hóa.

## 6. Kế hoạch triển khai sau khi được duyệt

| Bước | Công việc và tệp dự kiến | Phụ thuộc | Đầu ra/điều kiện xong |
|---|---|---|---|
| **P0 — Khóa mốc** | Lập manifest trong `tmp/doc-nhe-v414/`; ghi phiên bản, hash, môi trường. Chốt cách dùng pypdfium2/tokenizer đã có với `tmp/venv-ml`. | Duyệt kế hoạch | Đủ 16+3 nguồn hợp lệ; kiểm hash; không truy cập sách test; mô tả rõ backend khác nhau. |
| **P1 — Cổng đo** | Viết assertions trong `tests/unit/presentation/test_heading_evaluation.py`; thêm strict metrics trong `scripts/doc-nhe/danh_gia.py`. | P0 | Bốn phản ví dụ ở mục 7 thất bại dưới cách chấm cũ và qua cách chấm mới; legacy còn nguyên. |
| **P2 — Dòng và nhãn** | Hook tối thiểu `scripts/thu-a1/doc_nhe.py`; dựng dữ liệu/nhãn/coverage ở `scripts/doc-nhe/hoc_tieu_de.py`. | P0; P1 có thể song song | Đường mặc định cho output như cũ; kiểm 80 căn nhãn theo mục 4.2, sửa lỗi cơ chế có test; dataset và provenance đủ. |
| **P3 — Học và dự đoán** | M1/M2/M3, 16 LOBO; lưu model, dự đoán và log mỗi fold; full16 cho kiểm ngoài; M2 theo 10 nhóm nguồn. | P2 đạt kiểm căn nhãn | Không leakage; dự đoán ngoài train cho đủ 16 sách; lặp seed cho output ổn định; hội tụ hoặc cảnh báo rõ. |
| **P4 — Cây và chunk** | Harness gọi lại logic `doc_nhe_rong`/`so_chunk_doc_nhe`; cùng config cho M0/M1/M2/M3; thêm silver-oracle chẩn đoán. | P1, P3 | Bảng từng cuốn và từng lĩnh vực, tất cả mẫu số; nguồn và config hai phía cùng ghim. |
| **P5 — Kiểm ngoài và tốc độ** | Chấm ba tài liệu phát triển cũ; đo parse+inference cả 19 tài liệu tuần tự ba lần; kích thước model/RAM; các đếm chữ/media. | P4, mô hình đã khóa | Bảng 3 tài liệu riêng; không chọn lại cấu hình theo điểm ngoài; công bố phút/cuốn và 0 USD/cuốn của bước thử. |
| **P6 — Rà lỗi** | Xuất và đọc 50 bất đồng; đối chiếu grouping/hierarchy với silver oracle; phân tích các sách tệ nhất và nguồn chưa thấy. | P3–P5 | Phân loại nguyên nhân có bằng chứng; rõ tác động tới nội dung, không chỉ tiêu đề. |
| **P7 — Bàn giao** | README lệnh tái lập; báo cáo `report/v4-14-bo-nhan-tieu-de-<ngày>.md`; cập nhật vé 14; chạy kiểm thử liên quan, `git diff --check`. | P6 | Sếp có đủ số để chọn tiếp tục/đổi hướng/đề xuất tích hợp. Không tự sửa `src/` hay đổi A1 mặc định. |

Phân công có thể tách ba nhánh: dữ liệu/mô hình; hook/harness; kiểm độc lập/nghiên cứu. Mỗi nhánh sở hữu tệp riêng; chạy huấn luyện/benchmark nặng tuần tự trên laptop. Kiểm độc lập không sửa dữ liệu kiểm.

Các giao diện lệnh dự kiến, **chưa phải lệnh đã triển khai**:

```powershell
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_tieu_de.py prepare --out tmp/doc-nhe-v414
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_tieu_de.py train --out tmp/doc-nhe-v414 --seed 42
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/danh_gia.py --out tmp/doc-nhe-v414
```

README cuối sẽ cung cấp một lệnh chạy đầy đủ từ đầu, cùng lựa chọn chạy lại riêng một bước. Checkpoint theo sách/fold; chỉ tái dùng khi hash dữ liệu, features và config khớp. Chưa cam kết số phút huấn luyện trước khi biết tổng dòng; P2/P3 sẽ đo một lượt nhỏ rồi dự báo phần còn lại bằng số thực. Không có tiến trình dài nào được khởi chạy ở giai đoạn lập kế hoạch này.

## 7. Kiểm thử bắt buộc và điều kiện ra quyết định

Các tên dưới đây là assertions **dự kiến phải triển khai**, chưa được báo là test đã xanh:

Kiểm chẩn đoán chỉ đọc ngày 2026-10-07 đã gọi trực tiếp các hàm hiện có với bốn phản ví dụ: wrong-page, partial-number và duplicate đều cho legacy P=R=1; cặp chunk `alpha`/`beta` cùng tên mục cho Jaccard=0 nhưng `cung_muc_la=1`. Đây là bằng chứng lỗi phép đo; chưa phải kết quả sửa hay một lượt nghiệm thu mô hình.

| Invariant | Assertion dự kiến | Bằng chứng cần có |
|---|---|---|
| Tiêu đề sai trang không đúng | `test_heading_match_rejects_wrong_page` | Cùng chữ trang 1 và trang 9 cho TP=0; legacy đang có thể P/R=1. |
| Không khớp một phần số | `test_heading_match_uses_token_boundaries` | `1` và `11 Tổng quan` không được tính khớp. |
| Không thưởng dự đoán lặp | `test_heading_match_is_one_to_one` | 3 dự đoán giống và 1 nhãn: tối đa 1 TP, 2 FP. |
| Chunk không chung nội dung không đúng mục | `test_leaf_match_requires_content_overlap` | Jaccard=0 nhưng cùng tên mục: strict leaf=0. |
| Nhãn thiếu không bị biến thành âm | `test_unmatched_and_conflicting_rows_remain_unknown` | Match sai trang/loại mơ hồ trả -1; không vào tập fit. |
| Bbox đúng hệ tọa độ | `test_alignment_uses_same_page_geometry` | Hai dòng giống chữ tại hai vị trí; chỉ vị trí tương ứng được nhận. |
| Không rò rỉ cuốn kiểm | `test_lobo_excludes_heldout_and_unknown_labels` | Quan sát trực tiếp sample IDs truyền vào fit/scaler; loại heldout và -1. |
| Ngữ cảnh không qua trang/nhãn | `test_features_ignore_labels_and_cross_page_neighbors` | Đổi nhãn không đổi X; dòng đầu trang không mang feature dòng cuối trang trước. |
| Không chạm sách giữ lại | `test_manifest_rejects_non_allowlisted_paths` | Đường test/traversal/symlink ra ngoài allowlist bị từ chối trước khi mở file. |
| Hook không đổi mốc | `test_baseline_serialized_tree_unchanged` | Hash output cũ/mới trên fixture có tiêu đề, công thức và nhiều cột bằng nhau khi không bật model. |
| Gọi model đúng số dòng | `test_predictor_count_and_heading_override` | Đủ dòng, thiếu dòng bị bắt; một mẫu promote/demote thật sự đổi cấu trúc mong đợi. |
| Tái lập và cache đúng | `test_model_roundtrip_and_dataset_fingerprint` | Save/load dự đoán như nhau; đổi tree/feature config buộc cache cũ không được dùng. |

Mục tiêu gốc của vé giữ nguyên: F1 tiêu đề dòng median ≥0,90, thấp nhất ≥0,75; cùng mục lá legacy median ≥0,85; tỷ lệ chunk trùng từ ≥0,8 median ≥0,70; parse+inference <0,1 giây/trang. Thêm bảng strict, coverage và kiểm nhóm nguồn để giải thích các mục tiêu, không âm thầm thay định nghĩa số cũ.

**Nghiệm thu nghiên cứu:** đủ thí nghiệm, nguồn, lệnh tái lập, phân tích lỗi, chi phí/thời gian và test. Không đạt mục tiêu chất lượng vẫn có thể hoàn tất vé với kết luận không nên tích hợp.

**Đề xuất đưa vào A1:** chỉ xem xét khi số đo chặt, coverage và kiểm nhóm nguồn không cho thấy lợi ích giả; không mất chữ/media, và báo rõ mức hỗ trợ bảng/công thức/thứ tự đọc/cấp mục. Cần sếp kiểm độc lập và một kế hoạch thử các khâu sau trên bộ vàng phù hợp. Việc này thay chunk nên không thể tự coi lộ trình cuối vẫn tương đương. Chưa có ngân sách hay lịch chạy A3/A8 trong kế hoạch này.

Nếu title F1 tăng mà chunk vẫn kém, ưu tiên sửa lỗi cấu trúc đã chứng minh (gom tiêu đề nhiều dòng, cấp mục, thứ tự đọc) trong kế hoạch vòng tiếp theo. Nếu lỗi tập trung ở sách cùng nguồn bị giữ riêng, ưu tiên thêm/kiểm nhãn đa dạng. Chỉ đề xuất CRF khi rà lỗi cho thấy quan hệ chuỗi là nút thắt; chỉ mở nghiên cứu bảng/công thức khi phạm vi sản phẩm cần thay Docling ở các sách đó.

## 8. Nhật ký tra cứu và trạng thái bàn giao

Ngày truy cập: **2026-10-07**. Không dùng API key riêng, không gọi LLM/embedding trả phí.

| Nguồn tra | Endpoint/tham số | Kết quả thực tế |
|---|---|---|
| arXiv tìm theo tên | `https://export.arxiv.org/api/query`, `search_query=ti:VILA AND all:document`, `max_results=5` | `total_results=0`, không coi là bài không tồn tại. Chuyển sang tìm nguồn chính thức ACL rồi dùng ID. |
| arXiv theo ID | cùng endpoint, `id_list=2106.00676,2609.00065` | 2/2 hồ sơ: VILA v3 và Scientific Agent Skills v2; parser Atom của skill xác minh hình dạng phản hồi. |
| Crossref | `https://api.crossref.org/works`, `query.bibliographic=CERMINE automatic extraction of structured metadata from scientific literature`, `rows=3`, `select=DOI,title,author,published,URL` | 3 mục trả về; đúng bài 2015 có DOI `10.1007/s10032-015-0249-8`. Tổng tìm mờ rất lớn không phải số bài liên quan; không phân trang vì đây là tra định danh có mục tiêu. |
| Nguồn toàn văn/mã | ACL Anthology PDF và repo VILA; bài Springer CERMINE; tài liệu GROBID và file Java; NeurIPS LightGBM | Đọc các phần phương pháp/đo liên quan; phân biệt tài liệu phần mềm hiện tại với bài xuất bản. |

Payload API lưu tại `tmp/doc-nhe-v414/research/`: `arxiv-vila.xml`, `arxiv-records.xml`, `crossref-cermine.json`. Lần gọi mạng đầu bị sandbox chặn DNS, đã chạy lại bằng quyền mạng; truy cập trang GitHub/MIT có lúc báo cache miss, dùng nguồn raw/ACL/Springer tương ứng. Không diễn giải các lỗi truy cập thành khoảng trống nghiên cứu.

**Mã nháp trước yêu cầu chờ duyệt:** một hook parser và hai file test đã được viết dở theo yêu cầu triển khai ban đầu. Chúng đã được cất ở `tmp/doc-nhe-v414/paused-draft/`; nội dung `scripts/thu-a1/doc_nhe.py` đã trả về mốc trước lượt này (`git diff --exit-code -- scripts/thu-a1/doc_nhe.py` đạt). Chưa có `hoc_tieu_de.py`, mô hình đã học, dataset hay bảng điểm mới. Không ghi đè các sửa đổi vé 12/13 hoặc tệp khác của chủ dự án. **Không được dùng mã nháp làm bằng chứng nghiệm thu.**

Điểm dừng: chủ dự án đọc và duyệt P0–P7; sau đó mới triển khai kế hoạch được duyệt.

Kiểm trước bàn giao kế hoạch: 16/16 hash PDF khớp manifest của các cây nêu ở mục 3; tổng nút/tiêu đề đã đối chiếu lại; `git diff --check` đạt. Không chạy lại bộ test toàn dự án vì lượt này chỉ bàn giao tài liệu và đã cất mã nháp khỏi đường hoạt động.
