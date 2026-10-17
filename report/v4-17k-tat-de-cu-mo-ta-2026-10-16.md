# Vé 17k — Mặc định tắt đề cử theo mô tả nháp

Ngày: 2026-10-16. Nguồn: `task/v4/17k-tat-de-cu-theo-mo-ta.md`, spec mục 3.1 và
báo cáo nghiệm thu 17i lượt 1. Chi phí mô hình của lượt cài đặt/kiểm thử: **0 USD**.

## Thay đổi

- Thêm `DOC2ROADMAP_MERGE_DESCRIPTION_ENABLED=false` trong `Settings` và `.env.example`.
  Đặt `true` để bật lại nguồn này trong chuỗi `gop`; README ghi cách bật.
- Manifest canonical ghi rõ `additional_nominations.semantic_enabled`. Công tắc tham gia
  băm config, nên hai trạng thái không dùng lẫn cache.
- Khi tắt, `DocumentExtraction.from_payload(..., include_embeddings=False)` không truy cập
  trường `candidate_embeddings`. Vì vậy không giải mã vector mô tả và không sinh cặp
  `description_similarity`, cả khi chạy stage và khi lập dự toán.
- Các nguồn đề cử tên/alias, viết tắt, tiền tố và bằng chứng vẫn dùng hàm miền cũ.
  Khi bật, vector A3 đã lưu được đọc như 17e, không embed thêm mô tả; top-k mặc định 3,
  ngưỡng mặc định 0,85 giữ nguyên. Hai test 17e cần vector nay bật công tắc rõ ràng.
- V3 giữ đường đọc cũ và không thêm công tắc vào config. V3 vẫn là chuỗi mặc định.

## Kiểm chứng

Test nền 17e/miền/cấu hình: **13 qua**. Tám ca mới trong
`tests/unit/application/test_canonical_patch_17k.py` đều đỏ trước sửa:
mặc định vẫn sinh cạnh mô tả; cả `execute` và `plan` truy cập vector; chưa có cấu hình
môi trường và chưa kiểm kiểu boolean. Sau sửa, **40 test tập trung qua**.

| Hợp đồng | Assertion chạy được trong file test 17k |
|---|---|
| Mặc định không cạnh/log/đếm từ mô tả; bằng chứng vẫn đề cử; bật thì có lại; đổi cache và tái dùng riêng hai trạng thái | `test_default_skips_description_pairs_and_toggle_changes_cache` |
| Không đọc trường vector khi chạy hoặc lập dự toán | `test_disabled_source_never_reads_stored_vectors` |
| Biến môi trường đi qua composition đến kết quả stage, giữ tham số top-k/ngưỡng | `test_environment_switch_reaches_composed_canonical` |
| Cấu hình nội bộ chỉ nhận boolean, tránh chuỗi `"false"` bị coi là bật | `test_description_switch_rejects_non_boolean_config` |

Đã thử sáu biến thể bỏ luật trong bộ nhớ, không sửa file nguồn:

- Ép luôn đọc vector: hai ca `execute`/`plan` đỏ tại lần truy cập trường bị chặn.
- Ép luôn bỏ vector: ca bật lại đỏ vì không có cạnh mô tả.
- Bỏ công tắc khỏi phép băm nhưng vẫn ghi vào config: ca bật lại lấy nhầm cache tắt,
  đỏ vì không có cạnh mô tả. Đây là kiểm kết quả thực, không chỉ so trường cấu hình.
- Composition bỏ qua biến môi trường: ca bật đỏ vì stage không sinh cạnh mô tả.
- Bỏ kiểm kiểu công tắc: cả ba giá trị `None`, `"false"`, `0` lọt và làm test đỏ.
- Tắt nhầm toàn bộ nguồn đề cử bổ sung: ca mặc định đỏ vì mất cặp chung bằng chứng.

Bốn test composition, bật/tắt/cache và v3 qua khi nạp riêng phần thay đổi 17k trong
`composition.py`; không module Pha B nào được nạp. Test v3
`test_v3_fixture_config_payload_and_existing_cache_are_unchanged` tiếp tục xác nhận config
SHA-256 `67f96297f5d209ad030123ad8057b26e04f6498bd8ae384f29ca334e0aa740a5`, payload
SHA-256 `ea9dcfe574b523f800f2583a0f778f1a30049631a8c632554b8d4159ae76fd34` và tái dùng cache.

Toàn bộ **1.557 test qua**, không bỏ test, trong 480,28 giây; gồm tám test tích hợp
Docling offline và các test preview localhost. Bảy cảnh báo là deprecation của SWIG/RapidOCR.
Lệnh: `.venv/Scripts/python.exe -m pytest -p no:cacheprovider --basetemp=tmp/pytest-17k-full-01 --junitxml=tmp/pytest-17k-full-01.xml`,
với `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`. `git diff --check` qua.

Thay đổi Pha B đang có trong `composition.py` được giữ nguyên; phạm vi vé này chỉ
thêm công tắc vào `build_canonical`. Patch riêng cho hunk này đã được kiểm áp dụng.
Không dùng test mô hình giả để thay cho lượt nghiệm thu nghiên cứu 17i.
