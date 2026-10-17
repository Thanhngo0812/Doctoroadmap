# 19f–19h: chuẩn bị neo và chạy đồng thời

Ngày kiểm chứng: 2026-10-17. Mọi lời gọi mô hình trong kiểm tra dùng mô hình giả hoặc HTTP giả; chi phí mô hình 0 USD.

## 19f

Chuẩn hoá tên để dò nguyên văn được dùng chung theo chunk. Phép dò vẫn chạy độc lập từng node để giữ trường hợp tên dài chứa tên ngắn; dùng một lượt dò chọn tên dài nhất cho cả tài liệu sẽ đổi vùng ứng viên. Các phép chuẩn hoá ký hiệu và tách câu cũng được nhớ tạm trong một lần dựng lõi neo, rồi giải phóng sau khi dựng xong.

Đo trên canonical doc-4 v3 và chunk vai trò ghim theo A3, đọc từ `tmp/v4-17i/artifacts`, chỉ ghi kết quả đo vào `tmp/19fh`. Không gọi embedding hoặc mô hình, không ghi artifact vào kho chính. Hai lượt đo nối tiếp, không chạy đồng thời với phép đo CPU lớn của vé khác:

| Phép đo | Trước | Sau |
|---|---:|---:|
| `prepare_anchors`, 630 node / 671 chunk | 257,525952 giây | 38,666610 giây |
| Chi phí mô hình | 0 USD | 0 USD |

Nhanh hơn 6,66 lần, giảm 85,0%. Băm ứng viên cả hai lượt là `6870fc9160b05c0b138b77affd70084f72caaa98b649398f9bd0c51249df1551`; băm vùng ngoài nội dung là `f8230364600dd8433afd6645826d71b1b5726ca49a2c8e39ee92bc91bb7fce1d`.

Fixture thật baocao-canhan cũng giữ băm ứng viên `f6207a4d9dd6f34490168538ed21727a97f6b399fd35e8143a3a5d0b1f48338b`. Các test:

- `test_real_fixture_anchor_candidates_keep_the_frozen_before_hash`: so băm ứng viên trước khi tối ưu với kết quả mới.
- `test_document_text_is_normalized_once_and_nested_names_stay_independent`: mã cũ đỏ vì chuẩn hoá NFKC cùng chunk 4 lần; mã mới đúng một lần. Đồng thời giữ được ứng viên của cả tên ngắn lẫn tên dài.
- `test_canonical_manifest_measures_cpu_without_putting_time_into_cache_or_payload`: mã cũ đỏ do thiếu số đo CPU; mã mới có `build_nodes`, `additional_nominations`, `nomination_graph`, `prepare_anchors`. Thời gian không lọt vào payload hoặc config.
- `test_real_document_teaching_payload_and_cache_key_match_before_extraction` và `test_v3_fixture_config_payload_and_existing_cache_are_unchanged`: giữ nguyên payload và cache v3 đã đóng băng.

Chạy nhóm neo, canonical, miền neo và đặt tên module: 60 test qua. Việc đo stage đặt tên module thực tế được nối ở composition; không sửa nguồn Pha B. Test tích hợp `test_composed_module_naming_records_time_outside_semantic_payload` đã đỏ trước khi bọc bộ đo (thiếu `stats`) và xanh sau sửa, kiểm thời gian chỉ thêm vào manifest. Bộ 19d–19e cùng phép đo này: 11 test qua, 18,13 giây.

## 19h

Đã bắt đầu sau khi phần chuẩn bị neo của 19f đạt các phép kiểm và đo trên doc-4. Đường canonical chạy một nhóm chờ chung cho neo và xác minh prior, với số worker do cấu hình giới hạn. Lõi mặc định vẫn chia lô 8 để đường teaching giữ checkpoint; không thêm trường vào config hoặc khoá cache.

Các test mới ở `tests/unit/application/test_canonical_concurrency_19h.py`:

- `test_canonical_anchor_concurrency_reaches_configured_limit_and_is_deterministic`, hai trạng thái `defined_here` / `prior_knowledge`: mã cũ đỏ ở đỉnh 8 thay vì 16. Mã mới đạt 16 cho cả neo và xác minh prior; băm toàn bộ node, nhật ký và metrics bằng chạy tuần tự, thứ tự nhật ký neo theo node_id.
- `test_canonical_anchor_requests_still_pass_existing_model_limiter`: 24 lời chạy qua extractor thật, HTTP giả, worker 16, limiter 3; đỉnh HTTP thực tế và đỉnh limiter cùng bằng 3. Thử bỏ limiter trong một tiến trình kiểm tra riêng làm guard đỏ: đỉnh HTTP tăng lên 16, limiter không quan sát lời nào. Không sửa nguồn limiter để tạo phép thử này.
- `test_teaching_keeps_eight_node_checkpoints_and_deterministic_order`: giữ checkpoint 8/16/24 node và thứ tự node_id tất định.
- `test_canonical_concurrency_reuses_the_same_cache`: chạy 1 worker rồi đổi 16 worker vẫn tái dùng đúng artifact, không có lời mô hình mới.

Nhóm 19f/19h, replay v3 và limiter: 14 test qua. Nhóm chế độ A5 giữ lại, replay teaching và băm canonical v3: 10 test qua sau khi chọn `anchor_batch_mode='a5'` tường minh theo mặc định mới của vé 19d. Kiểm toàn kho cuối: **1.617 test qua**, mã thoát 0, 458,03 giây; xem [báo cáo tích hợp](v4-19-phan-tich-va-kiem-chung-2026-10-17.md).
