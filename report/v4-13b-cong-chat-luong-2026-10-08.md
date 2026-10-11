# v4-13b — Nghiệm thu cổng chất lượng chữ và tái lập T10

Ngày: 2026-10-08. **Hoàn tất phạm vi vé 13b; 0 USD API mới.** A1 nghiên cứu mở rộng vẫn tạm dừng theo yêu cầu chủ dự án.

## Kết quả

- Thêm tỉ lệ chữ cái ngoài Latin/Hy Lạp **sau NFKC**, ngưỡng **≥1%**, tối thiểu **100 chữ cái**; kiểm toàn văn và từng trang. NFKC chỉ dùng tính chỉ số, không biến đổi văn bản lưu.
- Giữ nguyên chốt vỡ âm tiết: dưới 80% âm tiết hợp lệ **và** ít nhất 1% dấu hiệu tách; giữ chốt ký tự lạ, vùng riêng, VNI.
- Không truyền `--pdf-backend`: tự chọn, bắt đầu pypdfium2. Truyền rõ: ghim bộ đọc, tuyệt đối không thử bộ đọc khác. Có lỗi thì dừng, hoặc dùng đúng bộ đọc khi có lý do được duyệt.
- Dry-run chưa có cây ghi **“chưa đo”**, `selected_backend=null`, có `planned_backend`; không coi đó là bản sạch. Một bản đã đo có lỗi không bị bản chưa đo thay thế trong xếp hạng.
- Cổng nhận đúng loại nút `title`, bỏ loại không tồn tại `heading`. Bảng báo cáo vé 13 đã được thay bằng đủ 42 hàng sau sửa VNI.
- T10 và script sinh bảng có cờ legacy cho cả hai tài liệu, lý do xstk đã duyệt, phân biệt parse v3 với chunks v2.

## Phạm vi và cách đo

Lệnh: `.venv/Scripts/python.exe scripts/thu-a1/do_chu_v413b.py`.

Đọc lớp chữ **toàn bộ 3.426 trang PDF × hai bộ đọc**, trên 16 sách train D-01 và năm PDF cũ. Pypdfium2 dùng text page; docling-parse dùng `DecodeConfig(enforce_same_font=True)`, các textline cell. Không chạy mô hình bố cục/OCR mới, không gọi LLM/embedding; không đọc hai sách trong `document-data/test/`.

Đồng thời đọc cây parse mà **chunks mới nhất của từng tài liệu ghim**, không lấy parse mới nhất tùy tiện. Có **3.353 trang có nút văn bản**, trong đó **3.229 trang ≥100 chữ cái NFKC**. Không phải mọi trang PDF đều có nút được cổng xét. Xstk ở phép kiểm cây ghim vẫn là parse v2 của chunks v5; dry-run T10 riêng tái dùng v3 đúng cấu hình legacy, không đổi chunks đó.

Dữ liệu đầy đủ từng lần đọc, PDF SHA-256, trang mẫu, chỉ số và thời gian: `tmp/thu-a1/v413b/<doc-id>.json`. Toàn bộ trang cây ghim: `pinned.json` cùng thư mục. [Số đo lưu cùng báo cáo](v4-13b-so-do-2026-10-08.json) chứa đủ 42 hàng, các phiên bản cây ghim và bảng ngưỡng.

**Hai miền đo không đồng nhất:** số toàn PDF bên dưới có thể chứa công thức/bảng; cổng sản phẩm chỉ xét paragraph/title/list_item/text/section_header. Trường `warnings` trong số đo PDF thô là chốt nền của `_text_quality`, không đại diện toàn bộ quyết định của `tree_text_quality`.

## Chọn ngưỡng và kiểm bắt nhầm

| Ngưỡng ngoài Latin/Hy Lạp | Bản PDF vượt / 42 | Trang cây ghim vượt / 3.229 | Trang ngoài d01-05 |
|---|---:|---:|---|
| 0,5% | 6 | 46 | naive-bayes: 6; d01-13: 41, 77 |
| **1,0%** | **6** | **23** | **0** |
| 1,5% | 6 | 8 | 0 |
| 2,0% | 6 | 4 | 0 |

Chọn 1%: bắt đủ sáu bản docling-parse d01-05/06/11/13/15/16 (toàn văn 14,512–18,943%); bắt thêm 23 trang có lỗi cục bộ trong cây d01-05. Ngưỡng 1,5–2% bỏ thêm nhiều trang cùng kiểu lỗi; 0,5% đưa ba trang sách khác vào diện cần thẩm định.

Đã xem mẫu từ chứa chữ ngoài Latin/Hy Lạp trên **từng trang trong 23 trang được bắt**: đều có chữ thay hệ chữ trong từ Việt, như `сủа`, `nghiệт`, `ВÀI TẬР`, `quаng`, `gibbereӏӏin`, `Ѕinh`. **0/23 trang gắn cờ được xác định là bắt nhầm qua kiểm mẫu từ này**; **0 trang mới bị chốt này bắt ở 20 cuốn còn lại**. Đây là kiểm thủ công trên chính kho chọn ngưỡng, không phải FPR=0 trên vàng độc lập, và không tuyên bố 20 cuốn kia sạch mọi loại lỗi.

23 trang d01-05: **26, 27, 46, 49, 50, 51, 52, 56, 74, 81, 85, 86, 87, 95, 102, 105, 106, 108, 142, 143, 144, 145, 150**.
Ba trang vé chỉ đích danh: 85 = **2,225%**, 108 = **2,281%**, 145 = **2,814%**. Toàn cây chỉ **0,351%**, cho thấy vì sao phải có kiểm từng trang.

Không thêm chốt “âm tiết thấp là bác” đứng riêng: toàn PDF naive-bayes chỉ 77,70–77,88%; thuật ngữ Anh/hoá, ký hiệu và token hóa cũng kéo điểm xuống. Không đủ nhãn độc lập để xem điểm đó là lỗi font. Giữ luật kết hợp hiện tại, không dùng dữ liệu này để tự thêm ngưỡng chặn mới.

### Bảng toàn PDF (không phải mẫu bảy trang)

| Tài liệu | Bộ đọc | Trang PDF | Âm tiết hợp lệ % | Ngoài Latin/Hy Lạp % | Ký tự lạ % | VNI |
|---|---|---:|---:|---:|---:|---:|
| doc-1 | pypdfium2 | 102 | 94.14 | 0.000 | 0.000 | 0 |
| doc-1 | docling-parse | 102 | 96.52 | 0.000 | 0.000 | 0 |
| doc-4 | pypdfium2 | 214 | 98.89 | 0.000 | 0.000 | 0 |
| doc-4 | docling-parse | 214 | 70.33 | 0.000 | 0.000 | 0 |
| doc-6 | pypdfium2 | 25 | 90.70 | 0.000 | 0.000 | 0 |
| doc-6 | docling-parse | 25 | 87.66 | 0.000 | 0.000 | 0 |
| xstk-ch3-1 | pypdfium2 | 59 | 96.67 | 0.000 | 0.000 | 8 |
| xstk-ch3-1 | docling-parse | 59 | 97.05 | 0.000 | 0.000 | 8 |
| naive-bayes | pypdfium2 | 36 | 77.70 | 0.000 | 0.000 | 17 |
| naive-bayes | docling-parse | 36 | 77.88 | 0.000 | 0.000 | 17 |
| d01-01 | pypdfium2 | 237 | 95.56 | 0.000 | 0.000 | 0 |
| d01-01 | docling-parse | 237 | 35.65 | 0.000 | 2.051 | 1 |
| d01-02 | pypdfium2 | 199 | 78.18 | 0.000 | 0.000 | 1191 |
| d01-02 | docling-parse | 199 | 68.60 | 0.000 | 0.000 | 1203 |
| d01-03 | pypdfium2 | 125 | 90.61 | 0.000 | 0.000 | 0 |
| d01-03 | docling-parse | 125 | 74.37 | 0.000 | 0.000 | 0 |
| d01-04 | pypdfium2 | 178 | 84.68 | 0.000 | 0.000 | 0 |
| d01-04 | docling-parse | 178 | 84.63 | 0.000 | 0.000 | 0 |
| d01-05 | pypdfium2 | 150 | 94.66 | 0.374 | 0.000 | 21 |
| d01-05 | docling-parse | 150 | 45.96 | 15.938 | 0.000 | 21 |
| d01-06 | pypdfium2 | 171 | 91.30 | 0.000 | 0.000 | 2 |
| d01-06 | docling-parse | 171 | 41.67 | 14.512 | 0.000 | 2 |
| d01-07 | pypdfium2 | 115 | 85.43 | 0.000 | 0.000 | 6 |
| d01-07 | docling-parse | 115 | 85.09 | 0.000 | 0.000 | 6 |
| d01-08 | pypdfium2 | 237 | 96.45 | 0.000 | 0.000 | 0 |
| d01-08 | docling-parse | 237 | 70.71 | 0.000 | 0.000 | 0 |
| d01-09 | pypdfium2 | 379 | 99.10 | 0.000 | 0.000 | 0 |
| d01-09 | docling-parse | 379 | 71.34 | 0.000 | 0.000 | 0 |
| d01-10 | pypdfium2 | 260 | 96.51 | 0.000 | 0.000 | 0 |
| d01-10 | docling-parse | 260 | 96.86 | 0.000 | 0.000 | 0 |
| d01-11 | pypdfium2 | 134 | 99.80 | 0.000 | 0.000 | 0 |
| d01-11 | docling-parse | 134 | 35.03 | 18.943 | 0.000 | 0 |
| d01-12 | pypdfium2 | 101 | 99.92 | 0.000 | 0.000 | 0 |
| d01-12 | docling-parse | 101 | 99.92 | 0.000 | 0.000 | 0 |
| d01-13 | pypdfium2 | 165 | 98.36 | 0.000 | 0.000 | 0 |
| d01-13 | docling-parse | 165 | 47.54 | 14.547 | 0.000 | 0 |
| d01-14 | pypdfium2 | 262 | 94.94 | 0.000 | 0.028 | 27 |
| d01-14 | docling-parse | 262 | 94.96 | 0.000 | 0.026 | 27 |
| d01-15 | pypdfium2 | 225 | 94.63 | 0.019 | 0.000 | 0 |
| d01-15 | docling-parse | 225 | 45.63 | 15.294 | 0.000 | 0 |
| d01-16 | pypdfium2 | 52 | 95.57 | 0.000 | 0.000 | 0 |
| d01-16 | docling-parse | 52 | 43.90 | 16.495 | 0.000 | 0 |

### Tất cả cây parse ghim được kiểm

| Tài liệu | Parse / chunks | Trang có văn bản / ≥100 chữ | Ngoài Latin/Hy Lạp toàn cây % | Trang ≥1% |
|---|---|---:|---:|---:|
| doc-1 | v5 / v7 | 98 / 96 | 0.000 | 0 |
| doc-4 | v2 / v6 | 211 / 205 | 0.000 | 0 |
| doc-6 | v2 / v4 | 25 / 18 | 0.000 | 0 |
| xstk-ch3-1 | v2 / v5 | 59 / 58 | 0.000 | 0 |
| naive-bayes | v1 / v3 | 35 / 26 | 0.015 | 0 |
| d01-01 | v2 / v3 | 233 / 222 | 0.000 | 0 |
| d01-02 | v2 / v6 | 195 / 161 | 0.000 | 0 |
| d01-03 | v1 / v2 | 125 / 119 | 0.000 | 0 |
| d01-04 | v2 / v4 | 172 / 165 | 0.000 | 0 |
| d01-05 | v2 / v4 | 145 / 143 | 0.351 | 23 |
| d01-06 | v2 / v3 | 168 / 162 | 0.000 | 0 |
| d01-07 | v2 / v3 | 111 / 107 | 0.000 | 0 |
| d01-08 | v1 / v2 | 237 / 237 | 0.000 | 0 |
| d01-09 | v1 / v2 | 361 / 355 | 0.000 | 0 |
| d01-10 | v1 / v2 | 260 / 259 | 0.000 | 0 |
| d01-11 | v1 / v2 | 133 / 132 | 0.000 | 0 |
| d01-12 | v1 / v2 | 97 / 96 | 0.000 | 0 |
| d01-13 | v1 / v2 | 159 / 156 | 0.023 | 0 |
| d01-14 | v2 / v3 | 257 / 246 | 0.000 | 0 |
| d01-15 | v2 / v3 | 223 / 218 | 0.003 | 0 |
| d01-16 | v1 / v2 | 49 / 48 | 0.000 | 0 |

## T10, lý do và bảo toàn cache

Chủ dự án đã duyệt nguyên văn:

> Tái lập T10 trên văn bản xstk đã khóa; chấp nhận lỗi chữ VNI đã ghi nhận ở trang 3, không làm sạch hoặc đổi bộ đọc

Lệnh đã kiểm:

```powershell
.venv/Scripts/python.exe -m doc2roadmap.presentation.cli.main ingest xstk-ch3-1.pdf --doc-id xstk-ch3-1 --pdf-backend docling-parse --pdf-text-policy legacy --allow-text-quality-reason "Tái lập T10 trên văn bản xstk đã khóa; chấp nhận lỗi chữ VNI đã ghi nhận ở trang 3, không làm sạch hoặc đổi bộ đọc" --dry-run
```

Kết quả: exit 0, `parse=tái dùng`, **parse v3**, adapter 11, `mode=pinned`, đúng **một attempt docling-parse**, không parse mới. Hash:

`4b897c487e4570a11d6fbca40c6a34212d02e2f6631d630e446c8c7750344acd`

Vẫn báo VNI trang 3 (4 mẫu, 1,4388%); lý do không xóa cảnh báo. Bỏ cờ lý do thì lệnh thật thoát khác 0, nêu chỉ số và gợi ý, vẫn không fallback. Chủ dự án **chấp nhận v3 đúng khóa cache**; parse v2 cũ adapter 7 không khớp adapter 11, không sửa khóa để ép tái dùng.

`scripts/khoa-cau-hinh/tao_bang.py --nhap` đã chạy thành công; bản nháp có legacy cho xstk/doc-4 và lý do xstk. Không tái khóa toàn bộ phương pháp khi cây làm việc còn các thay đổi chưa commit. Các bước trả tiền dùng chunks xstk cũ chưa lưu lý do phải truyền cùng cờ lý do, không áp mặc định cho cuốn khác.

**51/51 manifest parse giữ nguyên cả byte SHA-256 lẫn parser_config_hash**, kiểm bằng:
`.venv/Scripts/python.exe scripts/thu-a1/do_chu_v413b.py --cached-only`.
Baseline hợp lệ: `tmp/thu-a1/v413b/parse-manifests-before.json`, chụp trước dry-run thật. Lượt script ban đầu trỏ nhầm `artifacts/parse`, tạo baseline rỗng `manifests-before.json` và in “0”; đã sửa sang `artifacts/parse_tree`, thêm assert không rỗng. **Không dùng kết quả 0 đó làm bằng chứng**.

Không sửa/reingest artifact D-01 hay xstk. Con số **39/5.541 phiếu**, không có tên khái niệm dính lỗi, là kết quả kiểm của chủ dự án ghi trong vé, không phải lượt đo lại nhãn trong công việc này. Không chạy lại stage trả tiền.

## Kiểm thử có thể bác bỏ

Tệp mới: `tests/unit/application/test_v413b_text_quality.py`.

| Bất biến | Assertion/test |
|---|---|
| Câu Kirin thật bị bắt ở toàn cây và trang | `test_cyrillic_corruption_in_real_sentence_is_rejected` |
| NFKC µ, chữ toán Latin/Greek không bị tính nhầm | `test_nfkc_micro_and_mathematical_greek_or_latin_are_not_foreign_letters` |
| title được kiểm, heading giả không được dùng | `test_title_is_checked_and_fictitious_heading_type_is_not` |
| CLI ghim không đổi backend/parse lại; thiếu lý do không xuất chunks; có lý do lưu đúng parse | `test_cli_pinned_backend_never_switches_or_reparses_cached_vni` (hai nhánh) |
| Không chọn bản chưa đo làm sạch | `test_unknown_quality_is_not_selected_as_clean_in_dry_run` |
| Lỗi cục bộ không bị toàn cuốn pha loãng, trang dưới 100 chữ miễn chốt này | `test_local_script_corruption_not_diluted_and_pages_under_100_are_exempt` |
| Dry-run mới không parse, trạng thái chưa đo rõ ràng | `test_new_unmeasured_dry_run_reports_unknown_without_parsing` |
| Auto bắt đầu pdfium, mode không vào khóa parse | `test_mode_does_not_change_parse_key_and_auto_starts_with_pdfium` |

Đã chạy bộ hồi quy ban đầu trên hành vi cũ: **6 ca đỏ** sau khi sửa lỗi fixture; gồm nhánh ghim gọi backend kia và nhánh chưa đo bị chọn. Sau sửa, nhóm trọng điểm **58 passed**. Test CLI cũ chuyển kỳ vọng default thành `None` (auto); test fallback bỏ cờ ghim; các fixture VNI dùng loại nút title có thật.

Toàn bộ suite:
```powershell
.venv/Scripts/python.exe -m pytest tests -q -o addopts= -p no:cacheprovider --basetemp tmp/test-13b-all
```
**1.090 passed, 5 skipped, 7 cảnh báo deprecation; 183,21 giây**, exit 0. Không tuyên bố năm test bị bỏ qua đã chạy. Không thay parser_config hay adapter_version.

Kiểm cuối: `git diff --check` exit 0; JSON báo cáo đủ 21 × 2 lượt đo; bảng mẫu báo cáo vé 13 đủ 42 hàng; đối chiếu cache sau cả hai dry-run vẫn **51 manifest không đổi**. Chưa commit các thay đổi, không gom phần đang sửa của vé khác.

## Giới hạn còn lại

- Chốt hệ chữ dựa trên tên Unicode sau NFKC, phù hợp phạm vi sách Việt/Latin và ký hiệu Hy Lạp đang kiểm; không phải bộ nhận diện ngôn ngữ tổng quát. Sách viết thật bằng Kirin/Hán cần chính sách ngôn ngữ riêng trước khi mở rộng kho.
- Lỗi dưới 1%, trang quá ngắn và chữ Latin bị thay bằng chữ Latin khác vẫn có thể lọt. Không tuyên bố A1 đạt hoàn hảo hay mọi PDF đọc đúng.
- Đây là hoàn tất **13b**, không phải tiếp tục tự ý vé 14 hay đổi hướng A1. Không phát sinh phụ thuộc mới; sửa tại cổng/chọn bộ đọc dùng chung theo skill ponytail.
