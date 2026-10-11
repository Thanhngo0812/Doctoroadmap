# T-01a — Chạy luồng tới A5 trên hai cuốn giữ lại, sinh file gán vàng

**Nguồn chân lý:**
- [kế hoạch vòng 2, mục 5.1](../../report/nghien-cuu-pass-phu-vong-2-ke-hoach-2026-10-10.md);
- [vé 04 chuỗi A6–A8](../a6-a8-tien-quyet/04-bo-vang-excel-va-huong-dan-gan.md): file Excel gán mù và các lệnh `a8-gold-*`;
- [T10b v3](../v3-lo-trinh-doc-duoc/T10b-chay-tap-giu-lai.md): luật chạy tập giữ lại mà không đọc nội dung;
- `CONTEXT.md`, mục "Lệnh bậc 1–3".

**Ai:** nhân viên chạy · chủ dự án xác nhận quyền, duyệt chi, chọn chương, tìm hai người gán · Claude chỉ đọc báo cáo số đếm, không xem nội dung.

**Chi phí mô hình:** A2, A3, A4/A5 trên hai cuốn ngắn (92 và 113 trang), qua Vertex, ước dưới 2 USD. **Trần của vé: 5 USD.** Chạm trần thì dừng và báo.

**Trạng thái:** soạn 2026-10-11, chờ giao.

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
