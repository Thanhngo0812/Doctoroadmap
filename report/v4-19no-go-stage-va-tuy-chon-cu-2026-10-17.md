# 19n–19o — Gỡ stage và tuỳ chọn cũ

Ngày 2026-10-17. Làm 19n trước, 19o sau. **Mã và test xong; chi phí mô hình 0 USD.**
Chưa tạo commit triển khai: chờ ghép cùng sửa khuôn T10a trong `CONTEXT.md` do
chủ dự án/Claude nhận làm. Không sửa `CONTEXT.md` trong lượt này.

## Thay đổi 19n

- Gỡ stage provenance, neo/C8 và danh tính; gỡ cả triển khai kiểm teaching cũ,
  schema/prompt chỉ dùng cho những stage này và các export tương ứng.
- Gỡ đường gọi mô hình A4/A5 v3. A4 đầy đủ luôn dùng chuỗi gộp; giữ nguyên đường
  lớp tên và đề cử `--names-only`/`--prepare` phục vụ D-01 đóng băng.
- Orchestrator mới chỉ còn `clusters → mentions → main_edges → secondary_edges
  → validated → concept_labels → stages → module_titles`. Bỏ ba điểm dừng cũ và
  `--identity-review`; CLI từ chối chúng trước khi đọc artifact/gọi mô hình.
  `roadmap` mới gặp canonical v3 thì yêu cầu chạy lại A4 đầy đủ.
- Chuyển nguyên logic `quote_is_verbatim` sang `domain/quotes.py`, sửa import
  của Pha B trong cùng đợt. Chuyển `VERIFY_SCHEMA`, `HUMAN_VERDICT` và
  `load_identity_review` sang `application/identity_review.py` cho canonical.
  Giữ miền danh tính dùng chung và toàn bộ AnchorCore.
- Tách `EvaluationStore`, `BudgetStop`, `MeteredGemini` khỏi runner danh tính
  đã gỡ sang `scripts/doc-lo-trinh/evaluation_runtime.py`; sửa các import phụ thuộc.
  So AST ba lớp với mã cũ: giống hệt. Giữ các test giữ chỗ ngân sách trước mạng,
  sổ chi khi lỗi, retry và đọc artifact A8.

A8, A10, bộ chấm và Pha B vẫn đọc artifact v3 có `identity_map` trực tiếp.
Các runner lịch sử thực sự dựng lại stage đã gỡ cần checkout trước 19n
(`2c93c5a` có đủ mã). Không thêm lại stub stage cũ. Runner tái lập cổng 19l
vốn nhập mã từ worktree ghim riêng vẫn là bằng chứng lịch sử, không được chạy
bằng API hiện tại. Phần T10a của `CONTEXT.md` cần ghi giới hạn này trước commit chung.

## Thay đổi 19o

- Gỡ neo gom trong A5: schema, prompt ghép và nhánh thu neo từ mô tả/kiểm.
- Gỡ nguồn đề cử từ vector mô tả nháp và các tham số bật/tắt, top-k, ngưỡng.
  A4 không đọc `candidate_embeddings` nữa, cả execute lẫn plan.
- Gỡ gom lô phán sửa: cỡ lô, prompt/schema lô và bộ kiểm từng mục; mỗi mục dùng
  một lời phán riêng như mặc định đã nghiệm thu.
- Bỏ selector chuỗi/chế độ neo khỏi CLI, composition và constructor tương ứng.
  Metadata `upstream_chain="gop"` vẫn có trong artifact để các bộ đọc nhận dạng.
- Bỏ sáu trường Settings và `.env.example`: `upstream_chain`, `anchor_batch_mode`,
  `merge_description_enabled`, `merge_description_top_k`,
  `merge_description_min_similarity`, `canonical_repair_batch_size`.
  Biến cũ trong môi trường hoặc dotenv bị bỏ qua kèm cảnh báo nêu tên, không in giá trị.
  README và danh mục prompt đã cập nhật.

Các bộ đếm cũ `description_similarity=0`, `repair_batch_count`,
`repair_batch_call_count`, `repair_fallback_items=0` chỉ giữ hình dạng payload
để đầu ra mặc định giống hệt trước khi dọn; không còn cấu hình hay thuật toán
thử nghiệm tương ứng.

## Bằng chứng đầu ra

Đóng băng đầu ra trước khi sửa, trên fixture trích xuất/chunk thật của
`baocao-canhan` với mô hình/embedding giả. `test_cleanup_19n.py` kiểm trực tiếp
hash sau khi gỡ:

| Đường chạy | SHA-256 payload giữ nguyên |
|---|---|
| Chỉ lớp tên | `d3a5fd15b70878f6e42ed20a225165b1ef88a695084674e68a8342b4e96f9bf0` |
| Prepare | `69d80e1fc461769b331605dcf38959c71443b1f5587616694d0e5e5548ddc94f` |
| Canonical gộp mặc định | `9de0e3c923b11b6bfccf4b6302ea1f2fa58b50207334ec532ed4827044c08462` |
| A10 đọc fixture v3 đóng băng | `824717ed14ba3283d361e16e8995d5718e3ef1eb656239ab90a774e3f9914150` |

Config hash của names-only (`0f968b149375e842e990a03993380848c69857f470df919d7ca6b1fffffb86dc`)
và prepare (`bc5429b5fb6118264e183854789da967fa1270030cd8fc1c379c2a2889a5454f`)
cũng giữ nguyên. Config canonical đầy đủ đổi vì đã bỏ các mục ở 19o.

Fixture v3 mới ở `tests/fixtures/legacy-v3/baocao-canhan.json` có nguồn mã
`2c93c5a`, một ánh xạ danh tính và node đã gộp tương ứng. Đây là snapshot
harness kiểm thử, không phải kết quả một lượt gọi mô hình thật. README cùng
thư mục ghi rõ hai chuẩn hoá của harness cũ (xoá cạnh tiên quyết, ghim cụm)
và tên từng assertion A8/A10/bộ chấm/Pha B.

## Kiểm thử

- Trước sửa 19n, đã thấy **5 ca đỏ** cho API v3/điểm dừng cũ/module quote.
  Trước sửa 19o, đã thấy **15 ca đỏ** cho Settings, môi trường/dotenv,
  CLI và constructor cũ. Các ca này đã xanh sau khi sửa.
- Nhóm hồi quy liên quan: **89 passed**; nhóm A4 tổng quát: **48 passed**.
- Toàn kho sau dọn: **1.535 passed, 7 warnings**, 261,76 giây, exit 0;
  JUnit: `tmp/pytest-19no-final.xml`.
- Bổ sung sau khi lượt toàn kho đã thu thập test: **1 passed**, 3,74 giây,
  `test_scorers_still_read_frozen_v3_and_apply_its_identity_map`;
  JUnit: `tmp/pytest-19no-legacy-scorers.xml`. Ca này kiểm E1/E2 đọc graph v3,
  E4 bỏ đúng một cạnh alias thành tự nối và không sửa tệp vàng.
- Import mọi module trong gói bằng `pkgutil.walk_packages` đã qua.
  `git diff --check` qua. Không sửa logic hàm quote/bộ nạp review khi di chuyển
  (so AST với mã cũ).

Lệnh toàn kho:

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=tmp/pytest-19no-final --junitxml=tmp/pytest-19no-final.xml --tb=short
```

Lượt đầu toàn kho tìm thấy 12 lỗi: hai replay prompt partition v3 đã gỡ,
chín import helper ngân sách qua runner danh tính cũ, một assertion CLI cũ.
Đã gỡ hai replay đúng nhánh bị xoá, giữ replay describe/check cùng kiểm hash;
tách helper và sửa assertion CLI. Không đổi bản ghi mô hình để ép replay qua.
Test chỉ dành cho tính năng đã gỡ được gỡ cùng; các kiểm AnchorCore, quote,
review, retry, ngân sách, đọc/chấm artifact cũ vẫn chạy.

Toàn kho được kiểm trên workspace hiện có, gồm cả thay đổi A1/D-01/Pha B
đang dở từ trước; đây không phải kết quả của một checkout commit triển khai sạch.
HEAD hiện tại `3637d94` thêm tài liệu/vé 05, không chứa mã 19n–19o.
Không gán HEAD đó làm commit sinh artifact. Không chạy cổng, gọi API thật hay
ghi vào kho artifact chính trong lượt này; chỉ dùng fixture và kho tạm.
