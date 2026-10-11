# v4-14 — Bộ nhận tiêu đề học từ nhãn docling, cho bộ đọc PDF nhẹ (nghiên cứu và triển khai thử)

**Nguồn chân lý:**
- [kiểm rộng 16 cuốn](../../report/v4-10-buoc-2b-kiem-rong-16-cuon-2026-10-05.md);
- [bước 2: bộ đọc nhẹ](../../report/v4-10-buoc-2-bo-doc-nhe-2026-10-05.md);
- mã `scripts/thu-a1/doc_nhe.py`, `doc_nhe_rong.py`, `so_chunk_doc_nhe.py`.

**Ai:** nhân viên nghiên cứu, triển khai thử, **báo cáo cho Claude kiểm** · **Phụ thuộc:** — (A1 của 16 cuốn D-01 đã có trong kho) ·
**Chi phí mô hình:** 0 USD. Không dùng LLM; chạy CPU tại máy.

**Trạng thái hiện tại (2026-10-08): ĐÓNG chuỗi R1–R25; chuyển sang [vé 15](15-a1-danh-gia-doc-lap-chon-duong.md) theo yêu cầu mới của chủ dự án.** P0–P7 bên dưới là vòng 1 đã hoàn tất, không có nghĩa toàn A1 đã đạt. [Tổng kết và cấu hình S1](../../report/v4-15-dong-chuoi-r-2026-10-08.md) ghi phần đã vào sản phẩm, hash và lỗi còn mở. Dừng sửa theo trang trên 19 cuốn cũ; phát triển tiếp theo đáp án D-02 và hạn mức vé 15. Production adapter 13 giữ chữ lặp (R2-P), provenance caption (R3b), chunker có hợp đồng `declared-v1`; chưa đổi mặc định sang bộ nhẹ.

### Đợt A1 mở rộng — kế hoạch và nhật ký

- **2026-10-08 — R20–R25 đã triển khai và chạy đủ 19 sách:**
  [Báo cáo và bảng đầy đủ](../../report/v4-14-r20-r23-ket-qua-2026-10-08.md).
  R20 nối 27 cặp nhãn chương/tên trên 4 sách, strict leaf giảm ở 3 sách;
  không giấu các giảm hoặc gọi mọi tên chương đã hoàn chỉnh. R21 đổi 4 heading
  trong hình thành caption/text; d01-08 514→516/676, 18 sách không đổi.
  R22 tách 2 dòng Mã bài ở d01-06 p18/36 khỏi tên chương, không mất chữ.
  R23 ghép lại H3, kiểm toàn bộ parent_section_id thật, chunk text và multiset
  ref. Giữ 855 ImageRef, 13178 FormulaRef; 221 vị trí ảnh còn cảnh báo.
  Căn exact-match doc-4 giảm do nối tên; không dùng kết quả đó để tuyên bố cây tốt hơn.
  130 test A1/heading môi trường ML đã đạt; thêm test ghép xuyên suốt đạt riêng.
  Lượt regression trước R24: 1061 passed/5 skipped, gồm integration parser.
  [R24 đã xong](../../report/v4-14-r24-ket-qua-2026-10-08.md): nối đầy đủ tên
  chương d01-01 p176 theo chuỗi nguồn, giữ `n` và bbox superscript. Chuyển đúng
  một FormulaRef sang vai trò inline_script (13178→13177), kiểm Counter từng ID,
  không mất glyph; 19 sách không giảm thêm strict leaf. Đầu ra Section thực tế
  đã có tên đầy đủ. 10 test R24 và tổng 141 test A1/heading ML đạt, hash/snapshot
  R20–R24 khớp. [R25 đã đo xong](../../report/v4-14-r25-ket-qua-2026-10-08.md):
  55 hình có anchor mới theo body ngoài, 166 còn fallback cuối trang; giữ riêng
  55 cảnh báo thứ tự chữ nội hình chưa xác minh, không gọi 55 hình đã hoàn hảo.
  19 sách không giảm thêm strict leaf; giữ 855 ImageRef và 13177 FormulaRef.
  Đã xem thêm d01-03 p19, d01-05 p12, d01-06 p45 để đối chiếu vị trí hình.
  6 test R25 đỏ–xanh đạt; toàn nhóm A1/heading ML cuối lượt 147 passed,
  21 deselected. Các phép đo đã kết thúc, không có job nghiên cứu của lượt
  này chạy nền. Chưa nghiệm thu toàn A1: bảng/vector/reading order và nhãn
  hierarchy độc lập còn mở. R25 là nhánh default, không tự nhận H3 đã đo lại.
  Không đổi model, src hay cấu hình,
  không mở sách test, không chi API, không commit lẫn worktree.

- **Mới nhất R14–R19 (2026-10-07):** [R14/R14c](../../report/v4-14-r14-ket-qua-2026-10-07.md)
  đã triển khai bộ cha LightGBM riêng, nhưng H1 số mục/style thắng trên doc-4
  (139/171 so 131/171), **chưa promotion model**. Thêm hợp đồng API
  `declared-v1` đã kiểm: không ghi đè cây; mặc định/CLI không đổi. 19 hash
  ChunkingResult mặc định trước/sau giống nhau, 28 cây/884 payload truyền đúng.
- [R15](../../report/v4-14-r15-ket-qua-2026-10-07.md) và
  [R16](../../report/v4-14-r16-ket-qua-2026-10-07.md) đã chạy đủ 19 sách:
  giảm điểm lá ở R15 do trộn thay đổi guard tiêu đề với hierarchy; R16 giữ
  guard thì nội dung chunk/strict leaf giữ nguyên. Cây vẫn khác; strict leaf
  không đủ chấm cha–con. Snapshot giữ cả kết quả giảm, không đổi metric cũ.
- **R17 đã đo đủ 19 sách:** sửa prototype đọc `III.1`, `VI.2.1` và phân biệt `C.`
  trong dãy A/B/C với số La Mã; hai test đỏ trên H1 trước sửa, xanh ở H3.
  [Giao thức](../../report/v4-14-r17-giao-thuc-2026-10-07.md). Không train lại
  để đuổi theo doc-4; outline yếu có phần phẳng, không coi mọi bất đồng là lỗi.
  [Kết quả](../../report/v4-14-r17-ket-qua-2026-10-07.md): H3 142/171 đúng cha
  trên heading outline doc-4; toàn luồng 123/158 heading căn được, chưa đạt.
  Đã xem 5 trang PDF; p77 doc-4 cho thấy outline phẳng không phản ánh cây thật.
- **R18 đã chạy đủ:** [caption + hình học](../../report/v4-14-r18-ket-qua-2026-10-07.md),
  không chặn mọi formula/caption như veto cũ. Hai test đỏ trước sửa rồi xanh,
  đổi 100 cờ heading, 7/19 sách tăng strict leaf, 12 không đổi, 0 giảm.
  d01-08 0,64201→0,76036. Giữ nguyên model và threshold, không API. Đã xem
  ảnh p177/179 xác nhận hai caption bị nguồn bạc gán heading; không sửa vàng.
- **R19 đã ghép và kiểm đủ 19 sách:** [kết quả đầy đủ](../../report/v4-14-r19-ket-qua-2026-10-07.md)
  caption + native assets + H2/H3 sau guard. Kiểm hash bytes, source rows và
  multiset ImageRef downstream: **855/855 ref**; **221 vị trí chưa xác minh**
  vẫn có cảnh báo (không nhầm với 217 của grouping R6 cũ). Doc-4 H3 123/158
  đúng cha ở phần căn được; d01-08 H2 209/271 nhưng in-sample, không chọn theo
  ID cuốn. Ghép ảnh có cả ca giảm strict leaf, đã báo. Không nhận cả A1 chỉ
  từ điểm heading/chunk; chưa dựng bảng semantic hoặc ảnh vector hoàn chỉnh.
- **Điểm còn mở sau R19:** nhãn phân tầng độc lập đa sách, caption/diagram-text,
  nối nhãn chương với tên chương, reading order/bảng và vị trí hình chưa rõ.
  Giữ Docling mặc định. Không tự đánh dấu toàn vé hoàn tất hoặc bật bộ nhẹ;
  không cần xin lại quyền cho phần nghiên cứu CPU tiếp, nhưng kiểm nghiệm
  độc lập cuối cùng vẫn cần sách/nhãn mới như chủ dự án đã hẹn làm sau.
- **Kiểm chốt R19:** 1029 regression đạt, 5 skip, 8 integration deselected;
  103 test nhóm A1/heading trong môi trường ML đạt; 9 integration đã đạt sau
  thay đổi production (src không đổi thêm từ đó). Không cộng các lượt trùng.
  Hash mã/giao thức R14–R19 khớp snapshot, đủ 12 tệp kết quả/số đo, diff-check
  đạt. Các lượt R14–R19 và kiểm thử đã kết thúc, không có job nghiên cứu của
  lượt này còn chạy nền. Chưa commit. Tổng chi API đợt này **0 USD**.
- Kiểm chốt R17: **1026 regression đạt/5 skip/8 deselected**,
  **9 integration đạt**, **100 nhóm A1/heading môi trường ML đạt**; hai test
  R18 mới đạt riêng sau đó. Không cộng các lượt chồng nhau. 0 USD API, không mở
  `document-data/test/`, không sửa artifact production, chưa commit chung
  worktree bẩn. Toàn A1 vẫn **chưa nghiệm thu**.

- **Nhật ký sau trao đổi R13→R14:** R11/R12 đã chốt đủ kết quả,
  chưa chọn nhánh cân sách. [R12](../../report/v4-14-r12-ket-qua-2026-10-07.md)
  cấp nhãn bạc R1 vẫn chỉ strict leaf median 0,75878 với B2; không phải trần
  tối ưu. [R13](../../report/v4-14-r13-ket-qua-2026-10-07.md) bỏ 112 dòng
  running title d01-07, M2f+B2 strict leaf 0,19408→0,23026; 18 sách không đổi.
  Prototype chưa production, 14 test filter đạt.
- **R14 đã triển khai bộ chấm cha LightGBM + decoder cây có thứ tự.**
  [Giao thức](../../report/v4-14-r14-giao-thuc-phan-tang-2026-10-07.md): train
  từ outline yếu d01-08, bỏ từng nhánh gốc để kiểm; doc-4 chỉ kiểm ngoài.
  Đã fit 13 fold + full, doc-4 đúng cha 131/171 (0,7661), ancestor F1 0,7413.
  Đây là 171 heading căn được, chưa gồm lỗi phát hiện heading; không phải
  accuracy toàn A1. Đã bổ sung đối chứng số mục/style mạnh và kiểm đường
  truyền cây sang chunker ở R14b/R14c. 6 test decoder/nhãn/split đạt, có mutation đỏ
  chọn cha ở nhánh đã đóng. Không lấy level Docling phẳng làm vàng.

- **Nhật ký tại thời điểm R11/R12 (đã hoàn tất, xem kết quả ở trên).** R11 đã fit đủ 81 model
  cố định để tách tác động cân bằng sách/lớp khỏi đặc trưng; nhánh WB133 tăng
  F1 R1 thấp nhất LOBO 0,6414→0,6930 so ERM133 cùng đầu vào, giữ nguồn riêng
  thấp nhất 0,4207→0,4674. Chưa đạt toàn A1/chưa promotion. Đang đo B0/B2
  trên đủ 19 sách. [Giao thức R11](../../report/v4-14-r11-giao-thuc-2026-10-07.md).
- Tiếp tục R12, không dừng sau R: self-control chunk và can thiệp nhãn bạc
  để tách lỗi classifier khỏi lỗi grouping/cấu trúc. Không phải model ngoài
  mẫu hay trần tối ưu. [Giao thức R12](../../report/v4-14-r12-giao-thuc-2026-10-07.md).
  **996 regression đạt/3 skip ML/8 integration deselected; 81 test A1/heading
  trong môi trường ML đạt** (có thêm 2 test helper R12 sau lượt regression).
  Không mở test, không API, không đổi production trong lượt này.

- [Kế hoạch, nghiên cứu, quyền và kết quả từng vòng](../../report/v4-14-A1-mo-rong-2026-10-07.md).
- Phạm vi: bảo toàn chữ/ký hiệu → loại khối → thứ tự đọc → tiêu đề nhiều dòng/cấp mục → hình/bảng/caption → chất lượng chunk và chi phí đầu-cuối. Không đánh đồng F1 heading với chất lượng toàn A1.
- **R2 đã hoàn tất nghiên cứu/triển khai thử:** prototype riêng sửa cleanup phụ thuộc grouping, giữ provenance/bbox; kiểm đủ 19 sách/124.208 dòng. 152 tổ hợp sách–cờ–nhánh qua kiểm nội dung độc lập. Không sửa mã/cache/model vòng 1. Strict heading/leaf/chunk của nhánh chỉ sửa bảo toàn không đổi.
- Ablation hard veto formula/caption/code tăng median strict heading **0,7379→0,7636**, strict leaf **0,6159→0,6396**, nhưng làm d01-04/d01-16 giảm; phát hiện tên Vitamin K/Glycogen bị luật formula hiểu nhầm. **Chưa chọn hard veto, mặc định tắt.** Không chỉ báo median thuận lợi.
- 15 test mới R2; tổng nhóm A1 **33/33** xanh trong môi trường ML; regression **930 đạt/2 skip**, 5 integration không chạy. Đã có test đỏ hành vi cũ và bbox sai, rồi sửa xanh. **0 USD**, chưa đổi production. [Snapshot bảo toàn](../../report/v4-14-r2-bao-toan-2026-10-07.json), [snapshot chunk](../../report/v4-14-r2-chunk-2026-10-07.json).
- Điểm tiếp tục: **R3b sửa ontology/nguồn nhãn dựa trên review R3**, rồi R4 tuning có chia nhóm nguồn. Toàn A1 vẫn chưa nghiệm thu; không có script R2 chạy nền sau khi chốt.
- Các vòng sau: giao thức nhãn độc lập; ablation đặc trưng/mô hình có chia nhóm nguồn; giải mã cấu trúc; đường xử lý hình/bảng/trang khó; nghiệm thu toàn A1. Chi tiết và tiêu chí dừng trong báo cáo.
- **Quyền mở rộng tiếp theo (2026-10-07):** chủ dự án giao “cứ làm tới khi nào thấy ổn thì apply vô sản phẩm luôn, báo cáo là được”. Được tự tích hợp phần đã đủ bằng chứng vào production, không cần duyệt promotion riêng; vẫn phải có test/đo đầu-cuối, cache đúng và báo giới hạn. Đây không phải nghiệm thu sẵn bộ nhẹ/M2. Chi dịch vụ mới hoặc gửi sách sang nhà cung cấp khác vẫn cần duyệt; không dùng lại ngân sách A8 cho A1.
- **R2-P hoàn tất, đã tích hợp:** `preserve` mặc định giữ chữ lặp; `--pdf-text-policy legacy` tái lập cleanup/cache adapter 11, bản mới adapter 12 không dùng nhầm cache. Không ingest lại kho hay gọi API. 8 test đỏ trước sửa; cache mutation bị bắt; **944 regression đạt/2 skip**, **33/33 nhóm ML**, **9/9 thư mục integration** (có 1 tokenizer trùng regression), diff-check đạt. Bốn fixture giữ số mục/chunk/assets và cấu trúc; hai PDF đổi nội dung/ID có chủ đích. Không gọi 155 chữ tăng là 155 lỗi đã sửa: lặp do bộ đọc cũ cũng được giữ, cần hình học để khử đúng. [Báo cáo R2-P](../../report/v4-14-r2-production-2026-10-07.md), [snapshot](../../report/v4-14-r2-production-2026-10-07.json). Không có test/replay của đợt này còn chạy; chưa commit lẫn worktree các vé khác.

**Mốc vòng 1:** hoàn tất P0–P7 ngày 2026-10-07 sau khi chủ dự án duyệt [kế hoạch](../../report/v4-14-nghien-cuu-va-ke-hoach-A1-2026-10-07.md). Đã huấn luyện 61 model, đo đủ 16+3 tài liệu, rà 80 căn nhãn và 50 bất đồng. Chưa đạt mục tiêu thay A1; 0 USD API. [Báo cáo](../../report/v4-14-bo-nhan-tieu-de-2026-10-07.md), [snapshot](../../report/v4-14-so-do-2026-10-07.json). Các yêu cầu gốc bên dưới được giữ để đối chiếu lịch sử; phạm vi mở rộng không bị giới hạn ở phân loại heading.

### Cập nhật R3 (2026-10-07)

- **Xong công cụ căn nhãn/đo; ontology và review còn tiếp tục.** Căn đủ 19 sách/124.208 dòng theo bbox và token giữ dấu/số/chữ lặp, không dùng score M2. 69.500 dòng có nhãn bạc, **54.708 unknown (44,05%)**. Không có caption riêng; 103 node chỉ mang context caption nhưng thiếu bbox caption. Không lấy tăng unknown làm bằng chứng tăng precision.
- Tạo **271 phiếu review** (218 development/53 audit, không giao trang), xem ảnh 11 trang và ghi **14 đề xuất của agent, không vàng**; còn 257 chưa review. Xác nhận nhãn nguồn sai ở SQL→formula, viện dẫn→formula, list→footnote và math→text; thiếu loại chữ trong sơ đồ. **Chưa train/promote mô hình đa loại trên nhãn này.**
- Đã test 11 trường hợp, có phản ví dụ trên căn từ cũ và hai đột biến guard. Regression toàn dự án **955 đạt/2 skip ML**, 8 integration không chạy lại do không đổi production. **0 USD**, không sửa production thêm, không mở sách test. Không cần xin thêm quyền triển khai.
- [Giao thức, bảng 19 sách và quyết định](../../report/v4-14-r3-nhan-loai-khoi-2026-10-07.md), [snapshot](../../report/v4-14-r3-so-do-2026-10-07.json), [review từng ca](../../report/v4-14-r3-review-2026-10-07.json). Phiếu xem: `tmp/a1-v414-r3/review.html`.
- R3b tiếp theo: tách vai trò bố cục/nội dung, lấy provenance caption trước adaptation và xử lý nhóm diagram/table; sau đó đo mô hình với nhãn yếu/xác minh tách biệt. Bộ nhẹ chưa thay A1; không tự đánh dấu cả vé 14 hoàn tất.
- Chốt kiểm thử: **44/44 nhóm A1 trong môi trường ML đạt**, bao gồm 2 test skip ở production; diff-check và hash snapshot đạt. Không có job R3 chạy nền, không commit lẫn thay đổi các vé khác.

### R3b → R4 đang tiếp tục (2026-10-07)

- [R3b](../../report/v4-14-r3b-caption-2026-10-07.md): adapter 13 lưu tọa độ/charspan/liên kết caption chưa xác minh; 4 fixture giữ nguyên toàn cây (trừ metadata), chunk và ảnh. Pilot 4 trang có 5 caption/5 dòng căn được, không coi là accuracy ngoài mẫu. Không viết lại kho parse cũ.
- Tách layout-role/content-kind, giữ đề xuất agent riêng nhãn bạc. Chưa tự train đa loại trên nhãn nguồn đã biết có lỗi; 257 phiếu chưa review vẫn được ghi nhận.
- [Giao thức R4 đã chốt trước fit](../../report/v4-14-r4-giao-thuc-2026-10-07.md): đã xong **81 fit CPU**, 133 đặc trưng, so riêng nhãn R1/R3, không thay baseline cũ. Chọn E2 đo đầu-cuối: F1 R1 median 0,8876 (M2 0,8834), min 0,6995 (M2 0,2745). Giữ riêng nguồn vẫn có d01-15 chỉ 0,4365; chưa đạt/promotion model. Đang đo mới PDF→cây và chunk 19 sách.
- Kiểm thử sau R3b/R4: **969 regression đạt/3 skip ML**, **52/52 nhóm A1 trong môi trường ML**, **9/9 thư mục integration**; không cộng các lượt chồng nhau thành số test độc lập. `git diff --check` đạt.
- LightGBM vẫn là nền nghiên cứu phân loại dòng; A1 sản phẩm vẫn Docling. Không dùng F1 heading để nhận toàn A1; tiếp tục đo chunk/cấu trúc/thứ tự đọc/hình-bảng. **0 USD API**.

### R4 xong phép đo, tự chuyển R5a (2026-10-07)

- [Báo cáo R4 đầy đủ](../../report/v4-14-r4-ket-qua-2026-10-07.md), [số từng cuốn/nguồn và timing](../../report/v4-14-r4-so-do-2026-10-07.json). **Không promotion E2**: strict heading median 0,73793→0,76165, nhưng strict leaf 0,61595→0,61298, legacy leaf 0,742→0,715 và Jaccard≥0,8 0,637→0,616. Giữ cả ca giảm d01-01 0,6505→0,4059. Tốc độ đạt nhưng chưa đủ.
- [Giao thức R5a](../../report/v4-14-r5-giao-thuc-2026-10-07.md): LightGBM quan hệ nối dòng, không tăng/quét tham số R4. Đã fit 27 model trên 787 cặp bạc (147 nối/640 tách); ngoài mẫu LOBO false join 165→27, micro-F1 0,5946→0,8243. Mẫu ít/nhãn bạc nên chưa kết luận toàn cây tốt.
- Đang đo đầu-cuối 19 sách với cờ E2 cố định, so quy tắc cũ/typography/LightGBM nối dòng; giữ nguyên chữ, source rows, bbox, chunker. 5 test nối dòng đạt; có tái hiện quy tắc cũ nối nhầm style và mutation mất dòng bị bắt. Không dừng xin duyệt từng R; không gọi API.

### R5 → R6/R7 (2026-10-07)

- [R5 đã đo đủ cả E2 và M2](../../report/v4-14-r5-ket-qua-2026-10-07.md), [snapshot](../../report/v4-14-r5-so-do-2026-10-07.json). M2+B2: strict heading 0,73793→0,77381, strict leaf 0,61595→0,63933, Jaccard≥0,8 giữ 0,637; legacy leaf giảm 0,742→0,727. Chỉ giữ làm ứng viên, **chưa thay Docling**. Không huấn luyện hierarchy trên nhãn level=1 phẳng.
- [R6](../../report/v4-14-r6-giao-thuc-2026-10-07.md): đã trích 855/855 đối tượng raster có byte/refs; sửa lỗi giảm độ phân giải sau test đỏ, bản canonical ở `tmp/a1-v414-r6-native-resolution`. 638 placement có khoảng dọc rõ, 217 chưa xác minh; không gọi object raster là hình semantic hoàn chỉnh. 852 ảnh PNG khác nhau, 66.877.058 byte, 0 lỗi decode, ~30,89 giây trích asset (không phải parse toàn A1).
- [R7](../../report/v4-14-r7-giao-thuc-2026-10-07.md): cổng native bảo thủ depth 2 chuyển 2.746/3.365 trang sang chuyên dụng, phủ 1.046/1.047 trang có figure/table theo bạc. Ca lọt là cấu trúc hóa học trong Form lồng nhau; đang đo depth 15, không thêm model/không tuning theo ID sách. Không promotion luồng lai từ mỗi coverage này.
- Regression sau R5/R6: **979 đạt/3 skip ML**, 8 integration deselected; 5 test ảnh có test PDF 144dpi đỏ trên cách trích 72dpi rồi xanh ở bản giữ độ phân giải gốc. 0 USD API.

### Đang sửa bộ lọc đầu vào R8 (2026-10-07)

- [R6–R7 đã chốt số và giới hạn](../../report/v4-14-r6-r7-ket-qua-2026-10-07.md), [snapshot](../../report/v4-14-r6-r7-so-do-2026-10-07.json). Depth15 phủ 1.047/1.047 trang figure/table bạc nhưng phải fallback hơn 80%; chưa đủ lý do thay A1 bằng hybrid.
- [R8](../../report/v4-14-r8-giao-thuc-2026-10-07.md): audit toàn bộ 4.112 dòng bị lọc. Có heading chương/bài và dòng số ma trận bị loại trước LightGBM; đã đối chiếu 3 ảnh trang, không chỉ tin nhãn bạc. Nhiều dòng có nhãn text/heading thực ra vẫn là footer/header nên không khôi phục toàn bộ theo nhãn nguồn.
- Prototype mới lọc exact text/style/vị trí với mật độ xuất hiện; số trang phải là integer đơn + offset/style nhất quán. Không regex xóa cả ma trận hoặc mask số chương. 6 test mới/filter-grouping và 15 test R2 đạt, có phản ví dụ đỏ trên lọc cũ.
- Đang chuẩn bị dataset riêng `tmp/a1-v414-r8-model` rồi fit lại đúng M2 (27 split), không sửa R1 hoặc trộn E2. Full-raw-row metric tính cả heading bị filter bỏ để mẫu số không thiên vị. R2 chỉ thêm hook preparer; bản nguồn cũ đã snapshot. Không API, chưa promotion.

### R8 xong phép đo; R9 đang tách nguyên nhân (2026-10-07)

- [R8 đầy đủ](../../report/v4-14-r8-ket-qua-2026-10-07.md), [snapshot](../../report/v4-14-r8-so-do-2026-10-07.json): 54 fit hai nhánh b/c; R8c giữ thêm 326 dòng so cũ (31 heading và 7 nonheading căn được cả R1/R3, còn 288 không đủ hai nguồn). Không xóa thêm dòng cũ đang giữ. 341 running text kèm số trang được loại lại theo offset/style, không whitelist sách.
- **Chưa promotion model/filter vào A1 sản phẩm:** strict leaf doc-1 0,61809→0,41206, d01-01 0,65054→0,54839; giữ nội dung đúng không tự động làm chunk tốt. Không quay lại xóa ma trận để lấy điểm bạc cao hơn.
- 990 regression đạt/3 skip ML/8 integration deselected; 73 test nhóm A1 trong môi trường ML đạt (21 test ngoài phạm vi deselected). 10 test filter có 2 test R8c đỏ trước sửa rồi xanh. Không API, chưa commit lẫn vé khác.
- [R9](../../report/v4-14-r9-giao-thuc-2026-10-07.md) chạy tiếp ngay: cùng dòng R8c, tách M2 refit/M2 frozen/E2 frozen/mean cố định; mỗi nhánh so nối B0/B2. Không fit/quét tham số thêm; 8 tổ hợp đều phải báo. Dùng model loại đúng cuốn đang đo, giữ cổng text/bbox/order và mẫu số raw rows.

### R9–R10 hoàn tất phép đo/review đã định; tiếp tục nghiên cứu (2026-10-07)

- [R9](../../report/v4-14-r9-ket-qua-2026-10-07.md): 152 tổ hợp sách–nhánh giữ đủ source rows/text/bbox/order. d01-01 giảm chủ yếu sau refit; doc-1 còn giảm ngay khi chỉ đổi đầu vào. Không có nhánh chung đủ tốt, không chọn nhánh theo ID sách; ensemble không promotion.
- [R10](../../report/v4-14-r10-ket-qua-2026-10-07.md): xem thêm 54 phiếu ảnh, 38 development/16 audit, tổng 68/271 phiếu đã review. Còn 203 chưa xem. 47 đề xuất chắc/7 vừa, không gold, không tự đưa vào train. Xác nhận cần hai trục layout/content, TOC và ký hiệu kỹ thuật không nên ép vào lớp cũ.
- 3 test validator đỏ→xanh, kiểm đủ 54 ID/nguồn/ảnh; không đổi production. 0 USD API. Bước tiếp theo đang kiểm tài liệu và trọng số giữa sách/nguồn, không quét tham số theo cuốn thất bại.

### Bàn giao kết quả 2026-10-07

- M2 so M0, median 16 LOBO: F1 dòng **0,7553→0,8834**; cùng mục lá **0,581→0,742**; Jaccard ≥0,8 **0,430→0,637**. F1 thấp nhất M2 **0,2745** (d01-07), không bỏ cuốn xấu khỏi thống kê.
- Tốc độ đạt: M2 median **0,02494 giây/trang**, max median/cuốn trên 19 tài liệu **0,04673**. Full model 541.700 byte. Không lấy số inference riêng để báo tốc độ đọc PDF.
- 10 lượt giữ riêng nhóm nguồn; M3 bỏ context; oracle bạc; strict metric bên cạnh legacy; đủ bảng theo cuốn/lĩnh vực/external, thời gian/RAM/coverage và toàn vẹn.
- 915 test dự án đạt, 2 ML skip trong môi trường production, 5 integration deselected; **18/18 test vé 14** đạt trong môi trường ML. Fit lại full M2 cho score bằng đúng bản lưu trên cả ba external. `git diff --check` đạt.
- M2 giữ chữ/ký hiệu theo trang và danh sách hình trên 19/19 so M0, nhưng vẫn đổi sai loại công thức/chú thích; bộ nhẹ chưa dựng bảng, cấp mục/hình chưa đạt khả năng thay Docling. M3 có hai ca cleanup khác khi đổi grouping, đã báo rõ.
- Lệnh tái lập và điểm kiểm review: [README](../../scripts/doc-nhe/README.md). Model/dataset ở `tmp/doc-nhe-v414`; số đo và review đã xuất snapshot trong `report/`.
- **Kiến nghị:** chưa tích hợp A1. Chốt ontology/mẫu vàng heading độc lập, rồi xử lý multiline/cấp mục/caption–formula trước vòng nghiên cứu tiếp. Không tự tuning sau khi nhìn điểm kiểm, không chạy A2–A10 hoặc mở sách giữ lại.

## Vì sao (Claude, 2026-10-05)

Bộ đọc nhẹ (pypdfium2 cộng luật, không mô hình bố cục) nhanh hơn docling 55–450 lần. Một cuốn 400 trang mất khoảng 10–20 giây thay vì 10–20
phút. Trên 16 cuốn D-01, 8 lĩnh vực:
- **chữ đứng vững:** trùng docling trung vị R 0,99 / P 0,97;
- **tiêu đề thì không:** trung vị R 0,72, thấp nhất 0,17 (nông nghiệp), 0,20 (sinh học), 0,36 (pháp luật). Luật chỉnh trên 3 sách không bắt
  được các kiểu tiêu đề không đánh số của sách mới;
- hệ quả là chỉ trung vị 58% chunk rơi vào cùng mục lá với docling. Sai cấu trúc lan sang A2 (vai trò vùng), C8 và tên module.

Ý tưởng: thay luật tiêu đề bằng một **bộ phân loại học từ nhãn của docling** (nhãn bạc) trên chính 16 cuốn này. Mỗi dòng của bộ đọc nhẹ được
gán "tiêu đề hay không" theo cây docling; học trên đặc trưng bố cục rẻ. Hướng này cũng hợp seminar, vì cả Pha A không dùng LLM.

## Việc cần làm

### 1. Nghiên cứu ngắn, có nguồn

Đọc nguồn gốc (trang bài, mã nguồn) về nhận cấu trúc tài liệu PDF bằng đặc trưng bố cục, rồi ghi vào báo cáo cách mỗi hệ biểu diễn dòng, đặc
trưng, mô hình và cách đo. Gợi ý (phải tự kiểm lại, không tin tóm tắt):
- GROBID: CRF trên token có đặc trưng bố cục;
- CERMINE;
- các bài về gán nhãn dòng hay khối theo nhóm bố cục (VILA).

Kết luận cần chọn rõ: phân loại từng dòng (GBDT, hồi quy logistic) hay gán nhãn chuỗi (CRF), và vì sao.

### 2. Dữ liệu

- **Đơn vị:** dòng của bộ đọc nhẹ (`page_lines` → `describe` trong `doc_nhe.py`), kèm dòng trước và sau.
- **Nhãn:** khớp mỗi dòng với nút của cây docling cùng trang (`artifacts/parse_tree/d01-xx`, bản pypdfium2 mới nhất) theo chữ, cho phép
  tiêu đề docling nằm trọn trong dòng hoặc ngược lại.
  - Lớp tối thiểu: `tieu_de` (docling `section_header`/`title`) và `khac`.
  - Nếu làm được thì thêm: `dau_chan_trang` (dòng ở lề không khớp nút nào), `cong_thuc`, `danh_sach`.
  - Báo tỉ lệ dòng không khớp được, theo từng cuốn.
- Nhãn docling là **bạc**: docling cũng sai. Ví dụ doc-1 có "· Ví dụ 14." bị gán tiêu đề. Đọc tay khoảng 50 lỗi lớn nhất của mô hình để
  phân biệt mô hình sai với nhãn sai.
- **Không mở `document-data/test/`.** doc-1, doc-4, xstk chỉ dùng làm **kiểm ngoài**; không học trên chúng, vì luật v4 đã chỉnh trên chúng.

### 3. Đặc trưng

Không cần danh sách từ ngoài các mẫu đánh số đã có; đồ án chỉ làm tiếng Việt nên được dùng mẫu tiếng Việt.
- cỡ chữ so với thân bài của cuốn, đậm, nghiêng, tỉ lệ chữ hoa;
- độ dài (ký tự, từ), lề trái so với lề trang, căn giữa;
- khoảng trống trên và dưới so với chiều cao dòng;
- mẫu đánh số ("Chương", "Bài", "1.2", "I-", "A.", "a)"), kết thúc bằng dấu câu;
- tỉ lệ âm tiết tiếng Việt, tỉ lệ ký tự font toán, font đơn cách;
- vị trí trên trang, dòng có lặp qua các trang không;
- **ngữ cảnh**: các đặc trưng trên của dòng trước và dòng sau; dòng có khác font hay cỡ với hàng xóm không.

### 4. Mô hình và cách đo

- Chia **leave-one-book-out** trên 16 cuốn: cuốn đo không bao giờ nằm trong tập học. Báo theo từng cuốn và từng lĩnh vực, cả cuốn tệ nhất.
- Mức dòng: P/R/F1 tiêu đề so với docling; so với luật v4 hiện tại trên cùng dòng.
- **Đo đầu cuối bằng chính script đã có:** thay luật tiêu đề trong bộ đọc nhẹ bằng mô hình, chạy `doc_nhe_rong.py` và
  `so_chunk_doc_nhe.py` (cùng `chunk_document`, cùng tham số). Báo:
  - tiêu đề R/P;
  - tỉ lệ chunk cùng mục lá;
  - tỉ lệ chunk trùng từ từ 0,8;

  trên 16 cuốn và trên 3 tài liệu kiểm ngoài.
- Tốc độ: giây/trang **kể cả** suy luận mô hình; phải giữ dưới khoảng 0,1 giây/trang.

### 5. Triển khai thử

Mã ở `scripts/doc-nhe/` (hoặc mở rộng `scripts/thu-a1/`); chưa đưa vào `src/` và chưa đổi A1 của luồng.
- Mô hình huấn luyện lại được bằng một lệnh, seed cố định.
- Tệp mô hình nhỏ thì commit được; lớn thì để `tmp/` kèm lệnh dựng lại.
- Môi trường: dùng `tmp/venv-ml` (scikit-learn, lightgbm, underthesea). Không thêm gói vào `pyproject.toml` trong vé này.

## Nghiệm thu (chỉ tiêu để biết có đáng đưa vào luồng không, không phải cổng cứng)

- **Mục tiêu:**
  - tiêu đề F1 trung vị từ 0,9, cuốn tệ nhất từ 0,75;
  - chunk cùng mục lá trung vị từ 0,85;
  - chunk trùng từ từ 0,8 trung vị từ 0,7;
  - tốc độ dưới 0,1 giây/trang.

  Không đạt thì báo đủ số và phân tích lỗi; đó vẫn là kết quả nghiên cứu.
- **Báo cáo** `report/v4-14-bo-nhan-tieu-de-<ngày>.md`, gồm:
  - nguồn đã đọc;
  - bảng theo cuốn và lĩnh vực: luật v4 so với mô hình;
  - kiểm ngoài trên doc-1, doc-4, xstk;
  - lỗi tiêu biểu: mô hình sai hay nhãn docling sai;
  - độ quan trọng đặc trưng;
  - đề xuất có đưa vào A1 không, và cần gì thêm.
- Lệnh chạy lại được từ đầu; không đọc `document-data/test/`.
- **Báo cáo cho Claude kiểm thử** trước khi đề xuất đổi luồng.
