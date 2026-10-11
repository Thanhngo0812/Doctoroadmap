# v4-16 — A1: bộ đọc nhẹ thành mặc định; nghiên cứu cây cha–con

**Nguồn chân lý:**
- [vé 15](15-a1-danh-gia-doc-lap-chon-duong.md): đóng băng R2 ở pha 3, pha 5 cũ;
- [kiểm thử vé 15, pha 0–3](../../report/kiem-thu-ve-15-pha-0-3-2026-10-10.md);
- [chốt pha 3](../../report/v4-15-pha-3-chot-va-ban-giao-2026-10-09.md);
- [D-02](D-02-dac-ta-nhan-cau-truc-a1.md): nhãn phát triển;
- `CONTEXT.md`, mục "Cây mục khai báo (`declared-v1`)";
- [kiểm thử vé 13b](../../report/kiem-thu-ve-13b-2026-10-08.md): F1, F2.

**Ai:** nhân viên làm cả hai pha; Claude kiểm khi chủ dự án giao · **Chi phí mô hình:** 0 USD, không LLM ·
**Hạn mức:** pha 2 tối đa 3 ngày làm việc (xem mục pha 2).

**Trạng thái nhân viên 2026-10-10:** **hoàn tất pha 1 phía nhân viên**. Suite 1.185 test xanh và test DOCX bổ sung xanh; tương đương cùng mô hình full đạt 6/6 cuốn; dry-run xstk/doc-4 giữ parse v3; kiểm cuối 51 manifest parse không đổi. Wheel đã build và kiểm hash tài sản; test chọn đường/cache bắt được đột biến, nhóm CLI chạy lại đạt 12/12. Đủ 12/12 phép đo mới ở `tmp/a1-v416/phase1-idle-20261010`, driver exit 0 lúc 18:43; trung vị nhẹ 0,264 phút/260,6 MiB, Docling 12,561 phút/3.470,6 MiB. Báo cáo có bảng đếm bảng/công thức/hình và giới hạn phép đo. Pha 2 chưa bắt đầu; Claude kiểm lại 43 PDF khi được giao, nhân viên không mở tập khóa. Báo cáo: [v4-16 pha 1](../../report/v4-16-pha-1-2026-10-10.md).

**Mốc commit 2026-10-11:** theo yêu cầu chủ dự án, gom phần A1 vé 13b, 14 và pha 1 vé 16 (kèm phụ thuộc mã replay/benchmark D-02) thành commit riêng. Snapshot staging đã kiểm độc lập: **1.107 test xanh**; toàn worktree trước đóng mốc **1.188 test xanh**. Không commit sách, nhãn, `.gitignore`, tài liệu riêng hoặc sửa checkpoint/retry D-01. Không mở pha 2.

## Quyết định của chủ dự án, 2026-10-10

- **Đổi mặc định A1 sang bộ đọc nhẹ ngay**, không chờ pha 4 của vé 15.
- **Đây là đánh đổi có chủ đích, không phải "đạt luật pha 4".** Trên 6 cuốn phát triển (trung vị theo cuốn), R2 so với docling (S0):

  | | docling (S0) | bộ đọc nhẹ (R2) |
  |---|---:|---:|
  | M3, gán mục cho chữ | 0,865 | 0,800 |
  | M1, nhận tiêu đề | 0,844 | 0,801 |
  | M2, cha đúng | 0,34 | 0,33 |
  | thời gian | khoảng 12 phút/cuốn | nhanh hơn khoảng 36 lần |
  | RAM đỉnh | 3,5 GB | 0,25 GB |

  R2 trượt hai điều chất lượng của luật pha 4 (M3, M1). Báo cáo và đồ án phải ghi đúng như vậy.
- **Docling vẫn là đường chọn tường minh.** Tài liệu cũ đã khoá giữ đường docling.
- **Chủ dự án và Claude tạm dừng việc A1** để dồn nguồn lực cho khâu khác. Pha 4 của vé 15 hoãn; tập khoá giữ niêm phong cho một lần đánh giá sau (Claude chạy khi chủ dự án yêu cầu).
- **Cây cha–con là điểm yếu nhất của cả hai bộ đọc**, nên là việc nghiên cứu của pha 2. Cây này ảnh hưởng tới tên module ở A10 (lỗi "tên module theo cây mục hỏng" của v3) và tới mọi khâu dùng đường dẫn mục.

## Pha 1 — đưa bộ đọc nhẹ vào sản phẩm (làm trước)

**Chốt bổ sung của chủ dự án trong chat, 2026-10-10:** nghiệm thu tương đương khi cả adapter sản phẩm và R2 nghiên cứu dùng cùng mô hình `full`. R2 pha 3 trên sáu cuốn dùng mô hình bỏ-cuốn, nên đầu ra lịch sử không thể đồng thời giữ nguyên khi đổi sang `full`. Báo riêng khác biệt lịch sử; không đưa luật chọn mô hình theo mã sách vào sản phẩm. Đây là điều chỉnh tiêu chí tương đương tại 1.1, không thay đổi mô hình hay mục tiêu pha 2.

### 1.1 Adapter sản phẩm

- Đưa R2 đã đóng băng vào `src/doc2roadmap/infrastructure/parsing/` thành một `DocumentParser` trả `ParsedDocument(tree, images)` như adapter docling. R2 có fingerprint `182b6bd6…`, gồm R25 cộng chuẩn hoá đậm cộng ngữ pháp Điều/khoản/điểm.
- **Mô hình LightGBM** (bản `full`, của bộ nhận tiêu đề và bộ nối) chuyển khỏi `tmp/` sang chỗ có phiên bản, ví dụ `vendor/a1-nhe/`, kèm SHA-256. Thiếu tệp hoặc lệch hash thì dừng.
- **Phụ thuộc** khai báo vào môi trường chính (`pyproject`/`.venv`). Sản phẩm không còn cần `tmp/venv-ml`.
- **Ảnh:** hiện `extract_assets` ghi ra thư mục. Adapter phải trả ảnh theo đúng hợp đồng `ParsedDocument.images` để artifact store lưu như đường docling.
- **Bằng chứng tương đương:** trên 6 cuốn phát triển, cây và chunk của adapter giống hệt đầu ra R2 pha 3 (`tmp/a1-v415/phase3g-20261009/grammar/<sach>`). Ngoại lệ duy nhất là chữ của dòng có ký tự ngoài BMP (mục 1.4). Có test hồi quy trên một cuốn nhỏ.
- **Báo khác biệt** so với docling trên 6 cuốn: số nút bảng, công thức, hình. Chủ dự án cần biết phần đánh đổi này; đây không phải điều kiện chặn.

### 1.2 Chọn đường A1 và khoá cache

- `ingest --a1 {nhe,docling}`, mặc định `nhe`.
- Đường A1, phiên bản adapter và hash mô hình nằm trong khoá cache parse (như vé 09). Đổi đường thì không được tái dùng parse của đường kia.
- `--pdf-backend`, `--pdf-text-policy` và các cờ pipeline docling chỉ áp cho `--a1 docling`. Dùng với `nhe` thì báo lỗi rõ.
- **Tài liệu cũ không đổi.** Mọi lệnh tái lập đã khoá phải thêm `--a1 docling` tường minh: T10 (xstk, doc-4), các script D-01, khuôn lệnh bậc 1–3 trong `CONTEXT.md`, `T10-cau-hinh-khoa.md`, `scripts/khoa-cau-hinh/tao_bang.py`.
  - Script gọi thẳng `build_ingest`/`DoclingParser` (ví dụ `scripts/thu-a1/lam_sach_d01.py`) giữ đúng hành vi cũ.
  - Kiểm như vé 09/13b: mọi manifest parse cũ giữ nguyên byte và `parser_config_hash`; dry-run lệnh T10 xstk vẫn tái dùng parse v3 đã khoá.
- **Sửa luôn hai việc còn mở của vé 13b**, vì chạm cùng chỗ:
  - **F1:** trong `test_unknown_quality_is_not_selected_as_clean_in_dry_run`, khẳng định `selected_backend == 'docling-parse'` và `reason != 'unmeasured'`. Test hiện tại không đỏ được khi bản chưa đo bị xếp lên đầu.
  - **F2:** thêm cờ lý do của bảng khoá vào khuôn lệnh xstk trong `CONTEXT.md` (dòng 327, 331, 333 và câu ở dòng 337).

### 1.3 Cổng phạm vi: từ chối bản quét, nhận đúng PDF gốc

- **Cổng chung:** áp cho mọi đường A1. Ingest gặp PDF không phải PDF gốc thì dừng trước A2, báo rõ bản quét nằm ngoài phạm vi.
- **Dùng tín hiệu của bộ định tuyến vé 15, nhưng sửa một lỗi.** Khi chạy trên 43 PDF đã biết loại, bộ định tuyến từ chối nhầm một PDF gốc.
  - **Vì sao:** luật hiện tại chỉ xếp `native` khi *mọi* trang có nội dung đều là trang gốc. Một PDF gốc có trang là ảnh phủ kín trang mà không có chữ (bìa trước, bìa sau, trang hình toàn trang) vì thế bị xếp `mixed` và bị từ chối.
  - **Cần sửa thành:**
    - trang ảnh không chữ không tự biến sách gốc thành bản quét;
    - chỉ trang có lớp chữ OCR (chữ ẩn render mode 3, hoặc `GlyphLessFont`) mới là dấu hiệu bản quét;
    - sách mà phần lớn trang là ảnh không chữ vẫn bị từ chối.
- **Test (đỏ trước khi sửa):** PDF tổng hợp gốc có trang bìa là ảnh không chữ phải được nhận; bản quét có lớp OCR bị từ chối; bản quét không chữ bị từ chối; trang trắng không ảnh hưởng kết quả.
- Sau khi sửa, Claude chạy lại 43 PDF đã biết loại. Lần chạy này không còn là kiểm mù.

### 1.4 Ký tự ngoài BMP

- **Vấn đề:** `FPDFText_GetUnicode` của pdfium trả mỗi ký tự ngoài BMP thành hai mã UTF-16 rời. `doc_nhe.page_lines` hiện để chúng thành surrogate rời trong chữ, nên ghi JSON UTF-8 sẽ lỗi.
- **Sửa:** gộp cặp surrogate thành một ký tự. Không đổi cách cắt dòng, nên mã dòng không đổi.
- **Test:** PDF tổng hợp có ký tự ngoài BMP, ví dụ U+1F7B5 hoặc chữ toán 𝑥.

### 1.5 Cổng chất lượng chữ

- Đường `nhe` qua cùng cổng chữ của vé 13/13b như đường docling.
- Có cảnh báo thì dừng, in chỉ số, gợi ý `--a1 docling` hoặc `--allow-text-quality-reason`. Không tự đổi đường.

### Nghiệm thu pha 1

- **Test đỏ rồi xanh** cho: cờ chọn đường, khoá cache, cổng phạm vi, ký tự ngoài BMP, và F1.
- **Toàn bộ test xanh.**
- **Tương đương R2** trên 6 cuốn phát triển.
- **Manifest parse cũ** giữ nguyên.
- **Đo phút/cuốn và RAM đỉnh** của hai đường trên 6 cuốn phát triển, một lần, lúc máy rảnh. Đây là nguyên tắc số một của v4.
- **Báo cáo:** `report/v4-16-pha-1-...md`.

## Pha 2 — nghiên cứu cây cha–con cho bộ đọc nhẹ

### Vì sao

- **M2 (cha đúng trên các tiêu đề khớp) thấp ở cả hai bộ đọc:** docling 0,07–0,69 theo cuốn, R2 trung vị 0,33.
- **R4 của vé 15 không đổi được chỉ số nào.** R4 gán `level` cho nút, nhưng chunker hiện tại tự suy cấp. Muốn giữ cây đã quyết thì phải truyền qua hợp đồng `declared-v1` (`CONTEXT.md`): chunker giữ đúng tập tiêu đề và quan hệ cha–con đã khai báo, không chạy luật bác tiêu đề.

### Việc cần làm

Làm theo thứ tự, mỗi bước đo trên cùng bộ dữ liệu.

1. **Đo trước và phân loại lỗi M2** của R2 (và S0) trên 6 cuốn phát triển. Tách:
   - sai cấp;
   - sai cha do thiếu hoặc thừa tiêu đề ở trên;
   - sai nhánh mở đầu/hành chính (luật cha của D-02: nhánh `mo_dau`/`hanh_chinh` không đóng nhánh nội dung);
   - sai do tiêu đề nhiều dòng.

   Bảng lỗi này quyết định bước nào đáng làm.
2. **Ngữ pháp đánh số theo cuốn.** Nhận các kiểu:
   - Phần, Chương, Bài, Tuần kèm số La Mã hoặc số;
   - số thập phân `1.2.3`;
   - `I.`, `A.`, `a)`, `1)`;
   - `Điều N.`

   Thứ tự xuất hiện lần đầu của các kiểu trong cuốn cho ra cấp, theo kiểu ngăn xếp. Độ sâu của số thập phân cho cấp tương đối. Cha là tiêu đề đang mở có cấp nhỏ hơn đúng 1 trong cùng nhánh (như luật D-02). Sách bỏ qua một bậc đánh số thì vẫn tính cấp liên tiếp.
3. **Mục lục.** Dùng bookmark nếu có cấp, không thì đọc trang "MỤC LỤC" in sẵn: dòng có chấm dẫn hoặc số trang, thụt lề, đánh số. Ở 20 sách mới của D-02, 18 cuốn có trang mục lục.
   - Nối từng mục với tiêu đề trong thân sách: so chữ đã chuẩn hoá, giữ thứ tự, ước độ lệch giữa số trang in và số trang PDF theo cuốn.
   - Mục khớp thì lấy cấp theo mục lục, và được dùng làm bằng chứng đây là tiêu đề.
   - Mục lục lệch thân sách (thiếu chương, khác tên) thì bỏ qua mục không khớp, không bịa tiêu đề.
4. **Tiêu đề không đánh số và không có trong mục lục.** Xếp cấp theo trình bày trong chính cuốn: cỡ chữ, đậm, in hoa, thụt lề; phải nhất quán với các cấp đã biết từ bước 2–3. Mục không đánh số ngay dưới chương (ví dụ "Câu hỏi ôn tập chương 3") là con của chương đó.
5. **Truyền cây qua `declared-v1`.** Có test chunker giữ đúng cây đã khai báo.
6. **Không có mục lục và không có đánh số:** giữ hành vi R2. Không được làm cuốn đó tệ hơn.

### Dữ liệu và đánh giá

- **Nhãn:** 6 cuốn phát triển D-02, kèm 5 bản sửa cha của d01-02. Đây là nhãn agentic có duyệt bằng agentic, không gọi là vàng người.
- **Hồi quy:** 19 cuốn bạc cũ. Mục đích là không lỗi, và M1, M6 không sụp. M2 so với docling không có nghĩa, vì cây của docling sai.
- **Test cây tự dựng:**
  - Chương → 1.1 → 1.1.1 → a);
  - Phần → Mục lục → Chương (nhánh mở đầu);
  - Chương → Mục → Điều;
  - bỏ bậc đánh số;
  - tiêu đề hai dòng.
- **Chỉ số:**
  - M2 là chính;
  - M1, M3, M6 không được giảm;
  - thời gian/cuốn.

  Báo từng cuốn, trung vị, cuốn tệ nhất, và mọi cuốn giảm.
- **Mục tiêu:**
  - M2 trung vị ≥ 0,70 trên 6 cuốn phát triển, không cuốn nào dưới 0,50;
  - M1 và M3 trung vị không giảm quá 0,01 so với R2;
  - thời gian tăng không quá 10%.

  Không đạt thì báo trung thực, kèm bảng lỗi.

### Luật làm việc

- Không LLM.
- Không viết luật theo mã sách. Ngưỡng dùng chung cho mọi cuốn.
- Nếu có phần học, chia fold bỏ chính cuốn.
- Ghi mọi thử nghiệm, kể cả thử nghiệm không tăng.
- **Dừng** khi hết 3 ngày làm việc, hoặc khi M2 trung vị không tăng qua hai vòng liên tiếp. Khi dừng thì đóng băng, ghi hash như vé 15.
- **Không mở tập khoá D-02.** Sau khi đóng băng, Claude có thể đánh giá một lần trên tập khoá nếu chủ dự án yêu cầu.
- **Vào sản phẩm:** nếu đạt mục tiêu thì làm phiên bản adapter mới (khoá cache đổi theo) và đặt làm mặc định, sau khi báo chủ dự án. Bản cũ vẫn tái lập được.
- **Đọc trước:** hai nguồn sau là điểm bắt đầu; kiểm lại trích dẫn trước khi đưa vào báo cáo.
  - H. Déjean và J.-L. Meunier, "On tables of contents and how to recognize them" (IJDAR, 2009): nhận và nối mục lục.
  - Loạt cuộc thi ICDAR Book Structure Extraction 2009–2013 (A. Doucet và cộng sự): cách đo cấu trúc sách.

### Nghiệm thu pha 2

- Bảng lỗi trước và sau.
- Chỉ số từng cuốn trên 6 cuốn phát triển và 19 cuốn bạc.
- Test cây tự dựng, đỏ rồi xanh.
- Bản đóng băng có hash.
- **Báo cáo:** `report/v4-16-pha-2-...md`.

Hướng này hợp với seminar Pha A không LLM; giữ kết quả và mã ở dạng trình bày được.
