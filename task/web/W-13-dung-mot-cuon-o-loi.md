# W-13 — Use case `build_document`: dựng một cuốn ở lõi

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 4 ("Dựng một cuốn ở lõi", luồng, kiểm sớm); [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md);
[chạy lại doc-6](../../report/pha-b-chay-lai-doc6-chuoi-gop-2026-10-18.md) (chuỗi lệnh đã chạy thật); [Pha B CLI](../../doc/pha-b-cli.md).
**Ai:** nhân viên lõi · phối hợp phiên pha A · người soát kiểm · **Chi phí mô hình:** kiểm cache 0 USD; chạy thật đã được chủ dự án duyệt · **Chặn bởi:** không ·
**Trạng thái:** đạt nghiệm thu phạm vi W-13; điều phối đã kiểm độc lập · [soát sau bổ sung](../../report/dieu-phoi-kiem-lai-w13-w24-2026-10-19.md), [bàn giao](../../report/w13-hoan-tat-doc6-2026-10-19.md).
Doc-6 đã dựng xong từ kho rỗng và tái dùng cache thành công ở 0 USD; đã đo đủ sáu PDF gốc, không còn hai điểm chờ cache/nguồn PDF.

**Bổ sung sau phê duyệt chi:** 1.878 unit test và 69 test tập trung đạt, 4/4 mutation bị bắt; SQLite có số chi từng lượt. Lượt dựng kho rỗng 0,1203762 USD có đủ usage; tổng chi quy đổi ghi nhận 0,2329025 USD, lượt chép cache lịch sử có cờ thiếu usage. Các ghi chú điều phối bên dưới là checkpoint trước lượt bổ sung này.

**Điều phối kiểm sau bổ sung 2026-10-19:** đã chạy lại hai kho doc-6, đủ bốn bước, graph 37/8 giữ nguyên, 0 lời gọi mô hình và 0 USD;
kiểm DB/artifact/hash PDF đạt. W-13/kiến trúc + token W-24 tổng 83 test đạt; bỏ bản sửa cache làm test hồi quy đỏ.
Gỡ điểm chờ W-13; lõi tiếp tục W-05 sau checkpoint W-01, W-15 vẫn chờ W-14. Các checkpoint cũ ở báo cáo soát ba nhóm là lịch sử trước bổ sung.

## Vì sao

Hiện dựng một cuốn cần chạy tay nhiều lệnh, và `a4` đòi đường dẫn bộ vàng kể cả khi cuốn không có vàng. Web cần một hàm duy nhất: chạy từng bước, báo
tiến trình, dry-run được, chạy tiếp từ bước lỗi.

**Chủ dự án chốt trong phiên W-13 ngày 2026-10-19:** người dùng thả tệp rồi bấm xác nhận mới dựng. Không cần dự toán; không hiện chi phí cho người dùng.
Ghi usage/chi phí của lượt chạy vào DB khi kết thúc, kể cả lỗi hoặc huỷ. Giữ `--dry-run` làm công cụ kiểm nội bộ 0 USD, không tính tổng dự toán.
Kế hoạch và danh sách giao ba Luna nằm ở `tasks/plan.md`, `tasks/todo.md`.

## Cần làm

**Chuỗi chuẩn cho sách mới** (Claude xác nhận 2026-10-19, trả lời câu hỏi của nhân viên lõi; căn cứ ở cuối mục):

| bước công khai | lệnh tương ứng | tiền |
|---|---|---|
| `doc_reading` | `ingest` (bộ đọc nhẹ mặc định `--a1 nhe`) rồi kiểm sớm: bản quét, ngôn ngữ, cổng chất lượng chữ | 0 USD |
| `concepts` | `label-roles` → `a3` (A3 trích ứng viên và A3′ chỉ mục truy hồi, chạy song song trong cùng lệnh) → `a4 --language vi` (A4 cộng neo A5) | có |
| `graph` | `roadmap` (A6…A10 và tên module) | có |
| `learning_prep` | `phase-b a12`, `phase-b concept-index`, `phase-b formulas --pdf` (chỉ khi có PDF) | embedding |

- **`label-roles` bắt buộc,** chạy một lần, ngay sau kiểm sớm và **trước `a3`**. Không có trường hợp bỏ bước. Dry-run báo 0 mục chờ nhãn (cấu trúc đã phủ
  hết) thì bước này 0 lời gọi, 0 USD; ghi vào báo cáo vé lần chạy đó có tạo bản chunk nhãn mới hay không.
- **Không dùng cấu hình đọc của T-01a** (`--a1 docling --pdf-backend pypdfium2 …`). Cấu hình đó chỉ để T-01 so được với D-01. Sách mới dùng bộ đọc nhẹ mặc định.
- **Cổng chất lượng chữ** (`require_text_quality`) từ chối thì bản dựng `rejected` với mã `chu_loi`, 0 USD. **Không** tự truyền
  `allow_text_quality_reason`; chỉ chủ dự án được quyết, như T-01a.
- **A3′ bắt buộc,** vì Pha B (`search`, A12) đọc chỉ mục truy hồi qua `load_latest_retrieval`.

**Căn cứ** cho thứ tự `label-roles`:
- Nhãn nghĩa là lớp phủ: không đổi `chunk_id`, văn bản, offset (spec addendum, "Vai trò vùng văn bản"). A3–A8 đọc bản chunk N. Phần neo A5 trong `a4`,
  A9, A10, tên module và Pha B đọc nhãn qua `load_role_chunks`.
- **Neo trong `a4` lọc chunk theo `role == noi_dung`** (`anchor_core`). Nên `label-roles` phải xong **trước `a4`**. Chạy sau thì neo tính theo nhãn cấu trúc,
  còn A9 và A10 thấy nhãn nghĩa: hai bên lệch nhau.
- **Trước `a3`** là kiểu T-01/D-01, đúng thứ tự chuỗi đã nghiệm thu T-01 ngày 2026-10-18 (vé T-01a: bước 2 `label-roles`, bước 3 `a3`). Lỗi gán lại nhãn của
  kiểu này đã sửa ở 05c (commit `8655791`). Kiểu 05b (nhãn sau A3, trước A4) cũng đúng, nhưng chỉ dùng để vá sách cũ.
- **Bỏ `label-roles` thì** mục không có bằng chứng cấu trúc mặc định thành `noi_dung`. Đề cương, hành chính, mở đầu, bài tập bị coi là nội dung dạy, nên neo,
  chunk dạy, tên module và bài giảng lấy nhầm. Ví dụ doc-6: 16 nút "chỉ được nhắc tới" là mục đề cương ở các slide đầu.
- **Dry-run nội bộ sau `doc_reading`** chỉ báo phụ thuộc/artifact đã có hoặc chưa có; không gọi mô hình và không lấy artifact cũ làm bằng chứng cuốn mới đã sẵn sàng.

**Use case `build_document`** ở application, gọi các use case Pha A và Pha B có sẵn; **không** gọi CLI qua tiến trình con. Tham số:
- đường dẫn tệp, `doc_id`, ngôn ngữ `vi`;
- hàm báo tiến trình `(step, detail)`;
- hàm hỏi cờ huỷ, kiểm ở ranh giới bước;
- chế độ `dry_run`.

**Cấu hình đường gọi:** use case nhận cấu hình/phụ thuộc từ bên gọi; web/worker **tạm dùng Vertex AI** (`llm_transport=vertex`) cho cả sinh và embedding,
theo chủ dự án cập nhật 2026-10-19. Project/location và ADC ở máy chủ, không bắt buộc Gemini API key. Giữ chọn transport qua cấu hình, không khoá cứng
trong lõi; chỉ chuyển sang Developer API khi chủ dự án yêu cầu chuẩn bị demo, không tự chuyển khi lỗi.

**Bốn bước công khai** khớp spec chức năng: `doc_reading`, `concepts`, `graph`, `learning_prep`.

**Kiểm sớm sau `doc_reading`**, 0 USD:
- bản quét: ký tự chữ trung bình mỗi trang < 150 (hiệu chỉnh từ 200 theo phép đo W-13, doc-6 là 179,8), hay > 50% số trang không có chữ;
- ngôn ngữ: tỉ lệ ký tự có dấu tiếng Việt trên ký tự chữ < `vi_min_diacritic_ratio`.
- **Chỉnh ngưỡng** trên sáu cuốn phát triển, cộng hai tệp tiếng Anh và một PDF chỉ có ảnh tạo trong test. Ghi số đo của từng tệp vào báo cáo.

**Dry-run:** chạy `doc_reading` thật (0 USD), rồi kiểm trạng thái phụ thuộc cho các bước còn lại. Không ghi graph hoặc gọi sinh/embedding, không trả dự toán.
Kết quả ghi số lời gọi/usage thực tế của lượt chạy; thiếu usage thì ghi rõ `usage_complete=false`.

**Ghi DB:** application nhận callback ghi `BuildResult` để worker W-14 nối DB web. CLI cục bộ dùng SQLite ở `artifact_dir/builds.sqlite3` (stdlib).
Chi phí tính từ token nhà cung cấp thực trả và bảng giá hiện có; đây không phải hoá đơn của nhà cung cấp. Không cộng lại chi lịch sử trong artifact/cache.

**Chạy tiếp:** gọi lại sau lỗi thì các bước đã xong không gọi lại mô hình, nhờ cache và checkpoint của Pha A. Kiểm bằng đếm lời gọi.

**Không cần vàng** (Claude chốt 2026-10-19, thay cách tạm dùng fixture ngày 2026-10-18):
- Chế độ sản phẩm **không đọc tệp vàng nào**. `build_document` gọi thẳng `Canonicalize.execute(doc_id, a4_gold_coverage="none", gold_sheet_id=None,
  declared_language="vi")`, không gọi `load_gold`.
- **Căn cứ:**
  - trong `Canonicalize`, `a4_gold_coverage` và `gold_sheet_id` chỉ ghi vào manifest; chúng không vào băm cấu hình, không đổi phép tính;
  - cổng `--gold` của CLI `a4` là kỷ luật đánh giá: vàng phải gán mù trước khi có đầu ra mô hình, áp cho sách dùng để đo. Sách người dùng tải lên không có
    vàng, nên `none` là ghi đúng sự thật;
  - cách tạm cũ (fixture `gold-blind.json` cộng `require_complete=True`) hỏng trên kho mới, vì đòi artifact của bốn cuốn cũ.
- **Không sửa tệp của phiên pha A:** CLI `a4` giữ nguyên cổng. Báo phiên pha A để biết; không còn là yêu cầu chặn.
- `gold_sheet_id = None`, không dùng mã của sheet giả.

**`pipeline_version`:** commit hiện hành cộng băm của cấu hình chuỗi. Trả về cùng kết quả.

**Port `BuildRunner`** bọc use case này cho W-14. **Bản giả** của port (dùng ở W-14 và mọi test web) chép artifact sẵn có của một cuốn phát triển sang
`doc_id` mới, báo đủ bốn bước, và 0 USD.

**CLI:** `doc2roadmap build --file … --doc-id … [--dry-run] [--allow-spend]`, cho người soát chạy tay.

## Tiêu chí nghiệm thu

- [x] Chuỗi chạy đúng thứ tự trong bảng ở mục "Cần làm". Có test với use case giả từng bước:
  - đổi chỗ `label-roles` ra sau `a4` thì test đỏ;
  - bỏ `label-roles` thì test đỏ.
- [x] Cổng chất lượng chữ từ chối thì `rejected` với `chu_loi`, 0 lời gọi mô hình. Không có đường nào truyền `allow_text_quality_reason`.
- [x] Dựng chạy được trên **kho mới rỗng**, không có artifact của cuốn cũ nào. Thấy đỏ trên mã đang gọi `load_gold`.
- [x] Manifest canonical có `a4_gold_coverage: none`, `gold_sheet_id: null`. Test trỏ đường dẫn vàng sang một tệp không tồn tại mà vẫn xanh.
- [x] doc-6: băm cấu hình canonical của `build_document` bằng băm của lần chạy CLI trước, nên tái dùng (`reused`), 0 lời gọi mô hình.
- [x] `build --dry-run` trên doc-6 chạy đọc/kiểm đầu vào, trả trạng thái phụ thuộc, 0 USD, không ghi phiên bản đồ thị mới và không trả dự toán.
- [x] Kết quả thành công/lỗi/huỷ được ghi DB, có usage của lượt hiện tại và cờ chỉ rõ phần usage thiếu; không hiện dự toán/chi phí cho người học.
- [x] Chạy thật trên doc-6, **chỉ dùng cache sẵn có**: số lời gọi mô hình tính tiền là 0, hoặc báo số nhỏ trước khi chạy để chủ dự án duyệt.
- [x] PDF chỉ có ảnh bị dừng ở `ban_quet` sau `doc_reading`; tệp tiếng Anh bị dừng ở `ngon_ngu_khong_ho_tro`; 0 lời gọi mô hình. Thấy đỏ trước khi có kiểm
  sớm.
- [x] Cờ huỷ bật trong bước 2 thì không bước nào bắt đầu sau đó (test với use case giả từng bước).
- [x] Lỗi giả ở bước 3 rồi chạy lại: bước 1 và 2 không gọi lại mô hình.
- [x] Bản giả của `BuildRunner` qua cùng test hợp đồng của port như bản thật ở chế độ dry-run.
- [x] Test nối dây đường dựng từ web theo cấu hình tạm thời: sinh/embedding nhận `vertex`, bản sai truyền `developer_api` làm test đỏ. Kiểm bằng mô hình
  và xác thực giả, không gọi mạng hay chi tiền; không tự chuyển trước chỉ thị chuẩn bị demo.
- [x] Không mở tập giữ lại; test không dùng tệp của `document-data/test/`.

## Ngoài vé

Hàng đợi và worker (W-14). Đo USD/cuốn trên cuốn mới hoàn toàn (W-15). OCR bản quét.
