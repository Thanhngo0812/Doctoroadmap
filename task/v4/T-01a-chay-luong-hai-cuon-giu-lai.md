# T-01a — Chạy luồng tới A5 trên hai cuốn giữ lại, sinh file gán vàng

**Nguồn chân lý:**
- [kế hoạch vòng 2, mục 5.1](../../report/nghien-cuu-pass-phu-vong-2-ke-hoach-2026-10-10.md);
- [vé 04 chuỗi A6–A8](../a6-a8-tien-quyet/04-bo-vang-excel-va-huong-dan-gan.md): file Excel gán mù và các lệnh `a8-gold-*`;
- [T10b v3](../v3-lo-trinh-doc-duoc/T10b-chay-tap-giu-lai.md): luật chạy tập giữ lại mà không đọc nội dung;
- `CONTEXT.md`, mục "Lệnh bậc 1–3".

**Ai:** nhân viên chạy · chủ dự án xác nhận quyền, duyệt chi, chọn chương, tìm hai người gán · Claude chỉ đọc báo cáo số đếm, không xem nội dung.

**Chi phí mô hình:** A2, A3, A4/A5 trên hai cuốn ngắn (92 và 113 trang), qua Vertex, ước dưới 2 USD. **Trần của vé: 5 USD.** Chạm trần thì dừng và báo.

**Trạng thái:** 2026-10-11, **đã xong chạy A1–A5 và sinh/giao bốn phiếu trống; chờ hai người gán độc lập**. Checker sửa báo ĐẠT cả hai cuốn, canonical v1 complete. Chủ dự án chấp nhận sự cố mất mù cuốn đầu. Checker đã sửa allowlist, test đỏ trước/xanh sau. Không ghi nhận d01-t01 là sạch; mã pipeline giữ nguyên `ff797eb`. Tổng LLM đo được **1,942178 USD**, thiếu token 1 lời gọi A3 và chưa quy đổi embedding; không coi đây là hóa đơn đầy đủ.
- **Điều kiện 1 đạt:** ngày 2026-10-11, chủ dự án xác nhận quyền dùng hai cuốn, kể cả gửi lên Gemini.
- **Điều kiện 2 đang làm:** chủ dự án đã giao nhân viên commit phần việc đang làm dở.
- **Nhân viên kiểm trước chạy 2026-10-11:** mốc A1 đã commit `ff797eb`, Settings đúng Vertex/Flash Lite; nhưng còn mã D-01/checkpoint/retry chưa commit ở `src/`, `scripts/`, nên chưa đạt điều kiện cây sạch. Chưa chạy hoặc chi trên hai cuốn. Xem [báo cáo điều kiện](../../report/v4-T01a-2026-10-11.md); chờ quyết định đóng mốc mã còn lại hoặc chạy checkout sạch ghim commit A1.
- **Cập nhật sau khi chủ dự án giao quyền chọn phương án:** dùng worktree sạch `tmp/t01a-clean-ff797eb`, HEAD `ff797eb`, giữ nguyên `.env`; không đưa mã dở D-01 vào lượt giữ lại. Test tại checkout sạch **1.107 passed**, exit 0. Điều kiện 2 đạt trên checkout chạy. A1 d01-t01 bắt đầu, đúng Docling/pypdfium2/legacy; chưa chi API, chưa chạy d01-t02. Sau A2 dry-run chờ chủ dự án duyệt dự toán theo vé.
- **Mốc 11:02 ngày 2026-10-11:** A1 d01-t01 exit 0, parse v1/chunks v1, adapter 11, không cảnh báo chữ. A2 dry-run: 5 lời gọi, **0,010431 USD** trước retry; chờ duyệt, đề nghị trần 0,05 USD cho A2 cuốn đầu. Tổng chi mới 0 USD; chưa chạy d01-t02, A3–A5 hoặc roadmap.
- **Cập nhật A2:** chủ dự án duyệt trần 0,05 USD; A2 d01-t01 exit 0, chunks v2, 5 lời gọi, 25.241/2.815 token vào/ra, **0,01053275 USD** đo được. Tiếp tục A3 → A4/A5 theo vé trong trần toàn lượt 5 USD; chưa chạy d01-t02. Số 429 chưa đo được.
- **Mốc dừng sau A5:** candidates v1 (118/118 mục, 0 thất bại), canonical v1 complete (419 nút); checker exit 0/ĐẠT nhưng in nguyên stats có nội dung lồng, trái hợp đồng chỉ metadata. Tổng LLM **0,82737350 USD**, embedding 51.074 token chưa quy đổi USD, 429 chưa đo. Không chạy tiếp, không sửa runtime/checker, chưa xuất chương/Excel. Chi tiết sự cố và số đo trong [báo cáo T-01a](../../report/v4-T01a-2026-10-11.md); cần quyết định xử lý tính mù trước cuốn thứ hai.
- **Sau quyết định chủ dự án:** chấp nhận ngoại lệ mất mù cuốn đầu và tiếp tục; chỉ sửa checker báo cáo, không sửa pipeline/.env/prompt. Test hồi quy dữ liệu giả đỏ trên bản cũ, xanh sau sửa; kiểm lại d01-t01 ĐẠT. Đã xuất danh sách chương cấp 1 vào artifacts/a8-gold cho chủ dự án (không mở), chờ chọn chương. A1 d01-t02 bắt đầu; chưa chi LLM thêm, chưa sinh Excel.
- **Ngoại lệ chọn chương do chủ dự án yêu cầu:** giao agent riêng xem danh sách chương để chọn phạm vi và sinh hai phiếu trống, không đọc sách/artifact ngữ nghĩa, không gán nhãn hoặc chấm. Nhân viên chính chỉ nhận số đếm và hash. Ngoại lệ này không khôi phục tính mù của cuốn đầu.
- **Phiếu cuốn đầu đã giao:** cấp 1, dải số 36-40, 46 khái niệm đích / 331 nguồn, hai phiếu A1/A2 dưới artifacts/a8-gold. Nhân viên không mở phiếu; SHA-256 ghi trong báo cáo. Chờ hai người gán độc lập, không chấm hoặc hội ý trước khi nhận phiếu.
- **Cuốn thứ hai:** A1 exit 0, parse v1/chunks v1, adapter 11, không cảnh báo chữ, 389,75 giây. A2 dry-run 8 lời gọi, **0,01827 USD** trước retry; đề nghị trần A2 **0,10 USD**, chờ duyệt theo vé. Không có pipeline đang chạy; tổng LLM vẫn **0,82737350 USD** chưa gồm embedding.
- **Sau duyệt A2 cuốn thứ hai:** chủ dự án duyệt 0,10 USD; A2 exit 0, chunks v2, 8 lời gọi, **0,02083700 USD** theo token. A3 đang chạy; tổng LLM xác nhận **0,84821050 USD** chưa gồm embedding/A3 đang chạy. Không đổi pipeline hoặc cấu hình.
- **Hai cuốn qua A5:** d01-t02 candidates v1, 210/210 mục, 0 thất bại; canonical v1 complete, 464 nút. Hậu kiểm hai cuốn exit 0/ĐẠT, không graph. Tổng LLM đo được **1,942178 USD**; A3 d01-t02 thiếu usage của 1 lời gọi, embedding 150.289 token chưa quy đổi USD, 429 chưa đo. Không có pipeline đang chạy. Agent đang sinh hai phiếu trống cuốn thứ hai.
- **Bàn giao bốn phiếu:** d01-t01 cấp 1/dải 36-40 (46 đích), d01-t02 cấp 1/mã 10 (37 đích); mỗi cuốn đủ phiếu trống A1/A2. SHA-256 và lệnh trong báo cáo. Chưa có vàng người hoặc hội ý/gộp, không chấm; không có pipeline đang chạy. Theo vé chỉ commit báo cáo, không stage sách/phiếu hoặc sửa riêng của chủ dự án.
- **Mốc báo cáo:** commit **e13a6b1** chỉ chứa `report/v4-T01a-2026-10-11.md`, không chứa sách/phiếu. Checker hậu kiểm đã sửa và test xanh ở cây gốc còn chưa commit, đúng phạm vi chỉ commit báo cáo của vé; không dùng checker cũ của checkout ghim để in metadata. Trạng thái vé cập nhật trong worktree, không gộp với commit báo cáo.
- **2026-10-17 (Claude kiểm, chỉ xem tên tệp, kích thước, thời gian sửa và SHA):** hai người đã nộp phiếu ngày 2026-10-15, là bốn tệp `d01-t01-chuong-36-40-A{1,2}-output.xlsx` và `d01-t02-chuong-10-A{1,2}-output.xlsx`. Bốn phiếu trống gốc giữ nguyên SHA lúc giao. Chưa chạy bước 8.
- **Claude kiểm 2026-10-11: đạt phần chạy và giao phiếu** → [báo cáo vòng 2, mục 8.8](../../report/nghien-cuu-pass-phu-vong-2-ke-hoach-2026-10-10.md).
  - Checker ĐẠT hai cuốn. Tám hash khớp. Checkout ghim `ff797eb` sạch. Chi đo được 1,94 USD, phần chưa đo không đủ vượt trần 5 USD.
  - Sự cố mất mù d01-t01 là lỗi checker của Claude. Bản vá allowlist của nhân viên đúng: test đỏ trên bản cũ, xanh trên bản vá. Claude commit bản vá
    và test.
  - Còn bước 8 khi hai người nộp phiếu.

## Vì sao

T-01 là tập giữ lại của v4: hai cuốn mới với vàng người, chọn trước khi chỉnh vòng 2 của pass phụ không LLM. Kết luận chất lượng cuối của vòng 2
chỉ đo trên tập này.

Bộ vàng gắn với danh sách khái niệm của luồng. Lệnh `a8-gold-sheet` đòi canonical đã qua A5 (`stage=complete`), vì cần "nơi dạy" của từng khái
niệm. Vì vậy phải chạy luồng tới A5 trước, rồi người mới gán được.

## Phạm vi

| mã sách | tệp | lĩnh vực |
|---|---|---|
| `d01-t01` | `document-data/test/t01-con-trung-dai-cuong.pdf` | Sinh học |
| `d01-t02` | `document-data/test/t02-thanh-toan-quoc-te.pdf` | Kinh tế |

**Không làm trong vé này:**
- chạy `roadmap` (A6 trở đi), A8, A9, A10;
- xuất phiếu D-01;
- đưa hai cuốn cho agentic.

Các bước sau A5 làm ở vé đánh giá vòng 2, sau khi khoá cấu hình.

## Điều kiện trước khi chạy (tất cả phải đúng)

1. **Chủ dự án xác nhận quyền dùng hai cuốn**, kể cả gửi lên Gemini qua Vertex. `document-data/manifest.json` đang ghi
   `rights: unconfirmed_blinded`. Ghi xác nhận vào manifest hoặc báo cáo.
2. **Mã chạy đã commit, test xanh.** Các cờ `--a1` và `--pdf-text-policy` hiện chỉ có trong thay đổi chưa commit (vé 13b, 14, 16).
   - Commit phần việc đang làm dở trước, theo vé của nó.
   - Cây làm việc sạch ở `src/`, `scripts/`, `pyproject.toml`, `uv.lock`.
   - Ghi hash commit vào báo cáo.
   - Chạy toàn bộ test với `--basetemp` (xem `CONTEXT.md`).
3. `.env` dùng `llm_transport=vertex`, mô hình `gemini-3.1-flash-lite`.

## Luật trong suốt vé

- **Không đọc nội dung.** Không mở PDF, chunk, ứng viên, canonical hay file Excel của hai cuốn. Báo cáo, commit và tin nhắn gửi Claude chỉ chứa
  lệnh, phiên bản, số đếm, chi phí. Không chép tên khái niệm, tiêu đề mục hay câu chữ.
- **Không đổi gì giữa các bước:** mã, prompt, cờ, `.env`. Lỗi chặn thì dừng và báo; bản sửa là hậu kiểm, ghi "không sạch".
- **Từng cuốn một:** `d01-t01` trước, rồi `d01-t02`. Chạy song song làm tăng 429.
- Không bọc lệnh bằng `timeout`.
- Danh sách chương và file Excel chỉ giao chủ dự án. Không commit, không gửi Claude.

## Việc cần làm

Lệnh mẫu cho `d01-t01`, chạy trong PowerShell ở gốc repo. Với `d01-t02` thì thay mã sách và tệp.

```powershell
$env:UV_CACHE_DIR='.uv-cache-local'
$DOC='d01-t01'; $PDF='document-data/test/t01-con-trung-dai-cuong.pdf'
```

### 1. A1: đọc PDF, giống hệt D-01

```powershell
.\.tools\uv.exe run doc2roadmap ingest $PDF --doc-id $DOC --a1 docling --pdf-backend pypdfium2 --pdf-text-policy legacy
```

- Phải đúng cấu hình 16 cuốn D-01 đã dùng: `docling:2.114.0+pypdfium2`, adapter 11, sơ đồ tiêu đề mặc định (không `--heading-scheme`).
  - Mô hình vòng 2 học trên đặc trưng của D-01, nên đọc khác đi sẽ lẫn tác động của A1 vào kết quả đo.
  - Đây là lý do không dùng bộ đọc nhẹ mặc định mới của vé 16.
- **Cổng chất lượng chữ từ chối thì dừng và báo** số liệu của cổng (không chép chữ). Không tự thêm `--allow-text-quality-reason`; chủ dự án quyết.

### 2. A2: vai trò vùng

```powershell
.\.tools\uv.exe run doc2roadmap label-roles --doc-id $DOC --dry-run
.\.tools\uv.exe run doc2roadmap label-roles --doc-id $DOC --allow-spend
```

Gửi chủ dự án dự toán của lượt dry-run, chờ duyệt rồi mới chạy `--allow-spend`.

### 3. A3: trích ứng viên

```powershell
.\.tools\uv.exe run doc2roadmap a3 --doc-id $DOC
```

Phải thoát mã 0, không `coverage_incomplete`. Mục hỏng thì chạy lại lệnh: lượt sau tái dùng các mục đã xong.

### 4. A4/A5: canonical đầy đủ

```powershell
.\.tools\uv.exe run doc2roadmap a4 --doc-id $DOC --gold tests/fixtures/a4/gold-blind.json --no-gold-for-doc --language vi
```

- **Không dùng `--names-only`** như vé 12. Bản `names` không qua A5, nên `a8-gold-sheet` sẽ từ chối.
- Đây đúng là lệnh đã tạo canonical v1 của doc-4 (`gold_sheet_id` `473a0039…`, `a4_gold_coverage: none`).
- Ghi lại version canonical in ra. Mọi lệnh `a8-gold-*` về sau đều truyền `--canonical-version <v>` này.

### 5. Kiểm, chỉ in metadata

```powershell
.\.venv\Scripts\python.exe -I scripts/t01/kiem_t01a.py d01-t01 d01-t02
```

- Script in phiên bản, adapter, stage, số đếm và chi phí; không in nội dung. Thoát mã 1 khi lệch vé.
- Script kiểm sáu điểm:
  - A1 giống D-01;
  - canonical `stage=complete`;
  - A4 chạy với bộ vàng `gold-blind.json` và `--no-gold-for-doc`;
  - `--language vi`;
  - A3 chạy `gemini-3.1-flash-lite` qua Vertex;
  - chưa có artifact `graph`.
- Dán nguyên kết quả vào báo cáo.
- Chi từng khâu: `scripts/do-chi-phi/bao_cao.py <doc>`. Báo một tổng; khâu thiếu số token thì ghi "thiếu", không ghi 0.

### 6. Danh sách chương cho chủ dự án

```powershell
.\.tools\uv.exe run doc2roadmap a8-gold-sheet --doc-id $DOC --canonical-version <v> --list-chapters --chapter-level 1
```

- Kết quả có tiêu đề chương, tức nội dung sách. Gửi riêng chủ dự án, không ghi vào báo cáo.
- Nếu cấp 1 không giống chương (ví dụ cả cuốn một mục, hoặc lẫn trang bìa), chạy thêm `--chapter-level 2` và gửi cả hai.
- Chủ dự án chọn mỗi cuốn một chương hoặc một dải mục. Mốc tham khảo: các chương vàng cũ có 26–47 khái niệm đích.

### 7. Sinh file gán, sau khi chủ dự án chọn

```powershell
.\.tools\uv.exe run doc2roadmap a8-gold-sheet --doc-id $DOC --canonical-version <v> --chapter-level <n> --chapter <chương> --annotator A1
.\.tools\uv.exe run doc2roadmap a8-gold-sheet --doc-id $DOC --canonical-version <v> --chapter-level <n> --chapter <chương> --annotator A2
```

- Không dùng `--graph`. Lệnh kiểm và gộp về sau cũng không dùng.
- Giao hai file cho chủ dự án, không mở.
- Ghi SHA-256 của từng file vào báo cáo.

### 8. Khi hai người gán nộp file (làm theo vé 04)

Lần lượt:
1. `a8-gold-check` từng file với `--output`, ra JSON của A1 và A2. File lỗi thì trả người gán, kèm thông báo lỗi.
2. `a8-gold-merge` với hai `--gold` để sinh file hội ý.
3. Sau khi hai người hội ý xong: `a8-gold-merge --file <file hội ý đã điền> --output <vàng cuối>.json`.
4. Ghi SHA-256 của JSON vàng cuối.

Mọi tệp vàng nằm trong `artifacts/a8-gold/`, không commit. Không chạy `a8-score` hay lệnh chấm nào trên hai cuốn này.

## Báo cáo (`report/v4-T01a-<ngày>.md`, chỉ số liệu)

Báo cáo gồm:
- hash commit; mọi lệnh chép nguyên; version các artifact tạo ra; "chạy" hay "tái dùng";
- kết quả `kiem_t01a.py`;
- số lời gọi, số 429, chi từng khâu và tổng chi;
- đã gửi danh sách chương (ngày giờ) và đã giao file gán; SHA-256 các file;
- mọi sự cố.

## Nghiệm thu

Claude kiểm bằng báo cáo và bằng lệnh chỉ in metadata, không mở nội dung:
- `kiem_t01a.py d01-t01 d01-t02` in "ĐẠT" cho cả hai cuốn, mã thoát 0;
- tổng chi ≤ 5 USD;
- hai cặp file gán A1/A2 đã giao, có SHA-256;
- `git status` không có tệp nào của hai cuốn: chỉ báo cáo được commit;
- điều kiện 1 và 2 có ghi trong báo cáo.
