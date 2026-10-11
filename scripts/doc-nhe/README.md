# v4-14: nhận tiêu đề A1, thí nghiệm CPU

Chỉ là bộ đọc thử; **không thay parser production**. Không dùng LLM/embedding và
không mở sách `document-data/test/`. Chỉ 16 PDF train trong manifest và ba PDF
phát triển cũ `doc-1`, `doc-4`, `xstk-ch3-1` được phép đọc.

## Mốc mới nhất: R20–R25 (2026-10-08)

[Vé và trạng thái](../../task/v4/14-hoc-nhan-tieu-de.md) là điểm vào.
[R20–R23](../../report/v4-14-r20-r23-ket-qua-2026-10-08.md) sửa nhóm chương,
vai trò chữ trong hình, metadata mã bài và đo cây sau ghép;
[R24](../../report/v4-14-r24-ket-qua-2026-10-08.md) nối tên có superscript;
[R25](../../report/v4-14-r25-ket-qua-2026-10-08.md) đặt hình theo body ngoài.
Đều giữ model LightGBM M2f/B2, replay 19 sách từ cache, không phải phép đo
thời gian parse mới hoặc kiểm mù. Không thay Docling production.

Các script `do_noi_chuong_r20.py`, `do_vai_tro_r21.py`, `do_ma_bai_r22.py`,
`do_cay_r23.py`, `do_ten_chuong_math_r24.py`, `do_vi_tri_hinh_r25.py` nhận
`--out` mới và kiểm đầu vào canonical dưới `tmp/a1-v414-r*`. Không ghi đè
snapshot hoặc thay model sau khi đóng số. `source_rows` luôn theo dữ liệu đã
lọc margin R13, không phải số dòng nguyên bản PDF.

R25 giữ 855 ImageRef/13177 FormulaRef; số giảm một ref ở R24 là chuyển
superscript bị gán nhầm formula sang heading, có audit nguồn và Counter ID.
55 ảnh chuyển sang anchor ngoài, nhưng vẫn cảnh báo thứ tự chữ nội hình;
166 ảnh còn fallback cuối trang. Không coi bundle nghiên cứu này là sản phẩm
PDF→roadmap đã hoàn chỉnh hay một bộ đọc dùng được độc lập ngoài kho cache.

## Chạy lại

Từ gốc repo, dùng môi trường đã có `tmp/venv-ml` (Python 3.12.11,
scikit-learn 1.9.1, LightGBM 4.7.0, NumPy 2.5.2, joblib 1.6.0).
Script nối `.venv/Lib/site-packages` **sau** site-packages của môi trường ML để
dùng pypdfium2 5.12.1, Docling adapter, tokenizer và chunker đã cài.
Không cần thêm dependency vào `pyproject.toml`.

Một lệnh tiếp tục toàn bộ thí nghiệm đã duyệt:

```powershell
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/chay.py --out tmp/doc-nhe-v414
```

Với thư mục đầu ra mới, cùng lệnh dựng dữ liệu rồi **dừng trước huấn luyện** để
kiểm 80 căn nhãn. Đọc `alignment-review-80.json`, đối chiếu nút cây và PDF khi
cần; ghi `alignment-review-80-reviewed.json` với `sample_sha256`, phương pháp,
người kiểm và `reviews` đủ `sample: 1..80`, kết luận/lý do từng mẫu.
Không tự tạo xác nhận đã kiểm. Lặp lại cùng lệnh sau khi kiểm xong.
Đây là điểm kiểm thủ công có chủ đích, không phải quy trình hoàn toàn tự động.

Các bước riêng:

```powershell
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_tieu_de.py prepare
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_tieu_de.py train
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/danh_gia.py
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/bao_cao.py errors
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/bao_cao.py summary
```

Sau khi rà và lưu 50 nhận xét thật, chạy `bao_cao.py audit` để kiểm bảo toàn
chuỗi token/trang, số hình, công thức và tổng hợp coverage/gain. Có thể xuất bản
snapshot số đo bằng `bao_cao.py summary --snapshot report/ten-luot-do.json`.
Snapshot yêu cầu đủ `audit.json`, `e2e.json` và hai tệp review; không tự sinh
review. Nó giữ số đếm/TP/FP/FN, min/max từng lần đo và SHA-256 nguồn dùng lại.

Seed cố định 42 trong mã; không có cờ `--seed`. Không chạy nhiều bản benchmark
cùng lúc. Dùng `--book d01-01` với `danh_gia.py` khi chỉ cần đo lại một cuốn.
Giữ nguyên nguồn/chunker/tokenizer và thư viện để so thời gian/điểm có ý nghĩa.
Muốn kiểm phiên bản nguồn khác thì dùng `--out` mới; không sửa kết quả cũ.

## Thiết kế và đầu ra

- `manifest.json`: ghim PDF/cây/chunk-config và SHA-256; nguồn thay đổi bị bác.
- `datasets/`: dòng, bố cục, nhãn bạc 1/0/-1, nguồn căn nhãn, coverage.
  `-1` không dùng cho fit hoặc F1 có điều kiện.
- `models/`: 48 LOBO + 10 giữ riêng publisher + 3 full16 = 61 model; JSON ghi
  train/heldout, threshold, dự đoán ngoài train, importance, hash và dung lượng.
- `evaluation/`, `e2e.json`: cả 19 cuốn, năm phương án M0/M1/M2/M3/silver oracle;
  cùng chunker/config; metrics cũ và strict; ba lần đọc PDF mới cho mỗi mô hình.
- `errors-50.json`: 25 FP + 25 FN theo nhãn bạc, có ngữ cảnh và nút nguồn;
  kiểm riêng vào `errors-50-reviewed.json`. Không dùng để điều chỉnh điểm đã đo.
- `summary.json`: trung vị/min trên 16 sách, không trộn ba bộ phát triển cũ.

M1 logistic balanced + scaler train-only. M2 LightGBM balanced, 300 cây,
15 lá/cây, learning rate 0.05, min child 30, CPU 2 luồng. M3 bỏ hàng xóm.
Cả ba dùng threshold 0.5; score **không phải xác suất đã hiệu chỉnh**.
M2 có 73 đặc trưng; M3 có 23. Không chứa ID sách hay nhãn Docling.

`danh_gia.py` tái sử dụng hàm so sánh cũ từ `scripts/thu-a1/`, không sửa phép
đo lịch sử. Strict heading ghép một-một cùng trang, nguyên token, tỷ lệ ≥0.8.
Strict leaf chỉ cho đối sánh nội dung Jaccard ≥0.5 trong ±2 trang, tên mục lá
giống chuỗi token có thứ tự; mẫu số vẫn là toàn bộ chunk gốc.

Cache dataset/model có fingerprint mã feature/parser; evaluator có fingerprint
riêng. Đây là harness nghiên cứu, không phải hệ quản lý thí nghiệm tổng quát:
thay thư viện, chunker hoặc tokenizer thì chủ động dùng thư mục mới.
Các file joblib chỉ được nạp từ kết quả tự tạo ở đây; không nạp model lạ.

## Kiểm thử và giới hạn

```powershell
tmp/venv-ml/Scripts/python.exe -c "import sys; sys.path.extend(['src','.venv/Lib/site-packages']); import pytest; raise SystemExit(pytest.main(['tests/unit/presentation/test_heading_learning.py','tests/unit/presentation/test_heading_evaluation.py','tests/unit/presentation/test_doc_nhe_heading_hook.py','-q','-o','addopts=','-p','no:cacheprovider','--basetemp','tmp/pytest-v414']))"
```

Baseline parser được bảo vệ bằng hash ba fixture PDF trước khi thêm hook.
Các phản ví dụ metric strict đã chạy đỏ trên hành vi cũ. Mỗi benchmark so
toàn bộ nút trích mới với suy luận OOF đã lưu; không đo tốc độ trên cache dòng.

Nhãn bạc không phải nhãn vàng. Bộ đọc vẫn chưa dựng bảng, cấp mục còn theo luật,
hình vẫn nối cuối cây; công thức/chú thích có thể bị model nhận thành tiêu đề.
Không dùng kết quả này để khẳng định roadmap cuối đạt chất lượng: chưa chạy
A2–A10 và không có lời gọi trả phí trong vé.
# A1 mở rộng — vòng R2 (2026-10-07)

Prototype riêng `cau_truc_r2.py`; không sửa parser mặc định hay fingerprint model vòng 1.
Kế hoạch/kết quả: `report/v4-14-A1-mo-rong-2026-10-07.md`; trạng thái chính ở vé v4-14.

```powershell
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/do_r2.py --out tmp/a1-v414-r2/canonical
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/chunk_r2.py --out tmp/a1-v414-r2/canonical
```

Đầu vào mặc định chỉ đọc `tmp/doc-nhe-v414`, kiểm hash PDF/tree/chunk manifest, model và nguồn cũ;
không mở PDF test, không huấn luyện lại, không gọi API. Lưu `replay.json` và `chunks.json` cùng số từng sách.
Các số `grouping_seconds_only` không phải thời gian PDF→cây; `seconds` là thời gian chạy phép đo, cũng không phải tốc độ parser.

R2-text chuẩn hoá Symbol/font Việt từng dòng, không xóa chuỗi ký tự lặp chỉ dựa vào regex.
R2-protected là ablation bảo vệ formula/caption/monospace; mặc định **tắt**, chưa được chọn làm giải pháp.
`source_rows` trỏ đến dòng **sau** lọc header/footer; bbox dùng `[left, top, right, bottom]`, gốc PDF ở dưới trái.
Hình vẫn ở cuối như vòng 1, chưa có image assets/table recognition/reading-order mới. Các node R2 là dữ liệu nghiên cứu,
chưa phải artifact production; bộ chuyển chunk được giữ giống v1 cho cả ba nhánh để không trộn hai thay đổi.

Không tái dùng kết quả nếu mã/config đầu vào thay đổi; chọn thư mục mới và kiểm hash nguồn được ghi trong JSON.

## R2-P — adapter production (2026-10-07)

Đã tích hợp riêng chính sách giữ chữ lặp vào adapter 12; không tích hợp bộ đọc nhẹ/M2.
Tái lập parse cũ dùng `ingest ... --pdf-text-policy legacy` cùng backend/tuỳ chọn đã khoá.
Chạy audit offline bốn raw fixture và mọi span/asset/layout:

```powershell
.venv/Scripts/python.exe scripts/doc-nhe/do_bao_toan_production.py --out tmp/a1-preservation/replay.json
```

Đây là phép đo bảo toàn/tương thích, không phải benchmark chất lượng OCR. Các snapshot R2 trước đó giữ nguyên,
hash production parser đã đổi; không ghi đè snapshot cũ. Xem `report/v4-14-r2-production-2026-10-07.md`.

## R3 — nhãn loại khối và review

```powershell
.venv/Scripts/python.exe scripts/doc-nhe/nhan_khoi_r3.py --out tmp/a1-v414-r3-luot-moi
```

Dùng manifest/dataset đã khoá của vòng 1, không đọc dự đoán. Căn bbox và token giữ ký hiệu/hoa-thường/lặp;
không căn được giữ unknown. Output phải mới, dưới `tmp/`, không được đè baseline/production.
`labels/` chứa node nguồn và căn hình học; `review-packet.json`/`review.html` giấu nhãn,
`review-key.json` giữ key riêng. Chia development/audit theo trang, không chia từng dòng.
Mẫu này vẫn thuộc kho phát triển đã xem, không phải test mù mới; nhãn Docling không phải ground truth.

Đo lần đầu: 271 phiếu, 14 đề xuất agent sau xem ảnh, chưa đủ review toàn bộ/huấn luyện đa loại.
Caption mất bbox ở adaptation cũ, code/citation có nhãn bạc formula sai; xem báo cáo R3 trước khi dùng dữ liệu.
Không có mô hình R3 hay job nền; bước kế tiếp R3b hoàn thiện ontology/nguồn nhãn.

## R3b và R4

R3b đã giữ caption provenance trong adapter production 13; node/chunk/ảnh không
đổi trên bốn raw fixture, legacy 11 không đổi. Báo cáo:
`report/v4-14-r3b-caption-2026-10-07.md`. Không diễn giải source label là vàng.

```powershell
.venv/Scripts/python.exe scripts/doc-nhe/thu_caption_r3b.py --out tmp/a1-v414-r3b/pilot-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_r4.py --out tmp/a1-v414-r4
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/tong_ket_r4.py --out tmp/a1-v414-r4
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/do_r4.py --out tmp/a1-v414-r4
```

R4: 81 fit cố định theo `report/v4-14-r4-giao-thuc-2026-10-07.md`, 133 đặc trưng;
R1/R3 là hai mặt nạ bạc, không phải hai test độc lập. Model checkpoint có hash
mã/dữ liệu/protocol/package; chỉ resume đúng đầu vào, không ghi đè baseline.
E2 được chọn để đo đầu-cuối theo median/min LOBO. Mỗi lần đo PDF→cây đọc mới
PDF 3 lượt, kiểm output bằng đúng replay score ngoài mẫu. Đo chunk riêng, không
lấy thời gian grouping từ cache báo là tốc độ parse. Cây nhẹ vẫn thiếu bảng và
image bytes; các round này chưa thay parser production.

## R5–R8: cấu trúc, ảnh, cổng trang, lọc lề

```powershell
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_noi_r5.py --out tmp/a1-v414-r5-luot-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/do_noi_r5.py --out tmp/a1-v414-r5 --row-variant M2
.venv/Scripts/python.exe scripts/doc-nhe/do_hinh_r6.py --out tmp/a1-v414-r6-luot-moi
.venv/Scripts/python.exe scripts/doc-nhe/cong_trang_r7.py --out tmp/a1-v414-r7/gate-moi.json --depth 15
.venv/Scripts/python.exe scripts/doc-nhe/do_loc_le_r8.py --out tmp/a1-v414-r8-luot-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_loc_le_r8.py prepare --out tmp/a1-v414-r8-model-luot-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_loc_le_r8.py train --out tmp/a1-v414-r8-model-luot-moi
```

Các phép đo không ghi đè kết quả cũ; chọn output mới nếu đã chạy. R5 B2 là
LightGBM quan hệ nối dòng, không phải tăng cây của classifier dòng. R6 canonical
phải giữ native resolution; `tmp/a1-v414-r6` đời đầu bị loại do 72dpi, dùng bản
`-native-resolution`. R7 cổng không chứng minh trang qua cổng đã đúng toàn A1.
R8 đổi bộ lọc trước classifier, ghi riêng raw-index và nhãn bạc toàn raw rows;
không so F1 với mẫu số khác mà bỏ qua heading đã bị filter xóa.

Default grouping R2 không đổi; hook preparer mới chỉ dùng R8. Bản trước hook
lưu trong `tmp/a1-v414-r8/cau_truc_r2-before-filter-hook.py` để truy lại hash
các phép đo trước. Không sửa snapshot/model v1 để ép cache tương thích.

R8c bổ sung running text có số trang; protocol và output tách khỏi R8b:

```powershell
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_loc_le_r8c.py prepare --out tmp/a1-v414-r8c-luot-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_loc_le_r8c.py train --out tmp/a1-v414-r8c-luot-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/do_loc_le_r8_model.py --variant c --out tmp/a1-v414-r8c-luot-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/doi_chung_r9.py --out tmp/a1-v414-r9-luot-moi
```

R8c prepare ghim dataset R8b canonical; R9 ghim R8c/R1/R4/R5 canonical và kiểm
hash/split trước dự đoán. R8c không tự sửa dataset/model R8b. Evaluator R8b
trước thêm lựa chọn c lưu `tmp/a1-v414-r8-model/evaluator-before-r8c.py`.
Tất cả phép đo từ cached rows ở R8/R9 không phải benchmark thời gian parse.

## R10–R12: review, trọng số sách và đối chứng nhãn

R10 có 54 phiếu đã xem, lưu đề xuất hai trục trong
`report/v4-14-r10-review-2026-10-07.json`; không đưa chúng vào train hoặc gọi
là vàng. Selection/render và kiểm hash ở `xem_nhan_r10.py`/`kiem_nhan_r10.py`.

```powershell
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_can_sach_r11.py --out tmp/a1-v414-r11
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/do_can_sach_r11.py --out tmp/a1-v414-r11-e2e-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/doi_chung_nhan_r12.py --out tmp/a1-v414-r12-moi
```

R11 fit resume chỉ khi toàn bộ fingerprint khớp; evaluator mặc định ghim
R11 canonical (`--source` để chỉ output fit khác), R8c và model nối R5.
R12 là can thiệp dùng nhãn cuốn đang đo để chẩn đoán, không phải model được
phép triển khai. Cả hai evaluator yêu cầu output mới; không ghi đè snapshot.

## R13–R17: lọc dòng biên, phân tầng và hợp đồng chunk

```powershell
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/do_loc_bien_r13.py --out tmp/a1-v414-r13-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/hoc_cay_r14.py --out tmp/a1-v414-r14-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/doi_chung_cay_r14b.py --out tmp/a1-v414-r14b-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/do_cay_day_du_r15.py --out tmp/a1-v414-r15-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/do_tach_nhan_cay_r16.py --out tmp/a1-v414-r16-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/do_so_muc_r17.py --out tmp/a1-v414-r17-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/do_caption_hinh_r18.py --out tmp/a1-v414-r18-moi
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/ghep_ung_vien_r19.py --out tmp/a1-v414-r19-moi
```

Các evaluator dùng đầu vào canonical ghim trong script; đổi `--out` chỉ đổi
nơi ghi kết quả, không tự trỏ sang model `-moi`. Giữ snapshot/mã cũ, không sửa
model R1/R4/R5 để ép hash. R14 train cha chỉ d01-08, doc-4 chỉ đối chiếu;
R15 H2 của d01-08 in-sample. R16 chiếu cha sau guard, R17 dựng H3 sau guard.

`heading_scheme="declared-v1"` là API cho cây đã xác định độ sâu, bỏ mọi
heuristic thay cây. Không expose CLI/không bật mặc định. Nó không tự lọc
heading giả: gọi sai hợp đồng làm giảm chất lượng như R15 đã đo. R16 giữ
nội dung/ID/đường mục khi truyền cây cũ, trừ số level được nén về độ sâu thực.
Đo strict leaf không đủ nhận hierarchy; dùng cha–con/đường đầy đủ và ghi rõ
nhãn bạc/outline không hoàn chỉnh. Không có model mới được promotion.

R18 giữ M2f/B2, chỉ thử caption có prefix số và raster gần phía trên; không
xóa chữ hoặc chặn mọi công thức. Cả baseline và nhánh mới đều qua kiểm bảo
toàn source rows/bbox/text. Mọi dòng đổi cờ và nhãn bạc được ghi vào snapshot.
