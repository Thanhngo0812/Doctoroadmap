# 19d–19e: mặc định neo, CLI và tích hợp Pha B

Ngày kiểm chứng: 2026-10-17. Dùng fixture tài liệu thật, vector lưu sẵn và mô hình giả; chi phí mô hình 0 USD. Chỉ ghi kho thử của pytest.

## 19d

`Settings`, `.env.example` và hàm dựng canonical mặc định dùng neo `single`. Chế độ `a5` vẫn chọn tường minh được. Chuỗi thượng nguồn mặc định vẫn là `v3`; việc đổi sang `gop` thuộc 19m.

Lệnh `a4 --names-only` và `a4 --prepare` tự chọn `v3` khi không truyền chuỗi tường minh, kể cả cấu hình môi trường là `gop`. Truyền `--upstream-chain gop` cùng hai chế độ này vẫn báo lỗi. Hàm dựng stage cũng chọn `v3` cho `prepare` không có chuỗi tường minh.

`tests/unit/presentation/test_canonical_defaults_19d.py` có 8 trường hợp:

- `test_default_gop_uses_individual_anchor_calls`: thực thi chuỗi gộp, kiểm lời neo riêng và lời mô tả không nhận ứng viên neo trong A5.
- `test_incomplete_cli_uses_v3_under_gop_default`: hai chế độ × ba lựa chọn chuỗi, kiểm mã thoát và artifact được ghi bằng CLI thật.
- `test_default_chain_stays_v3_until_gate_19m`: giữ cổng đổi mặc định.

Trước sửa, 3 trường hợp đỏ do mặc định `a5` và hai chế độ tự nhận `gop`. Hai phép phá luật trong bộ nhớ cũng làm test đỏ đúng nhánh: ép `v3` đè lên lựa chọn `gop` tường minh; bỏ fallback trong hàm dựng `prepare`. Không sửa tệp nguồn để chạy các phép phá luật này.

Nhóm 19d, CLI và băm v3 đóng băng: 17 test qua. Chế độ A5 chọn tường minh cùng replay teaching và canonical v3: 10 test qua.

## 19e

`test_phase_b_loader_and_lecture_context_accept_real_roadmap` trong `tests/unit/application/test_phase_b_gop_graph_19e.py` chạy hai nhánh:

- `gop`: canonical → các stage đồ thị → `stages`, từ fixture thật `baocao-canhan`, mô hình giả và ML giả; không có `identity_map`.
- `v3`: canonical cũ → replay teaching đã lưu → bước danh tính thật với mô hình giả → `stages`; có ít nhất một cặp gộp và `identity_map` không rỗng.

Cả hai đi qua `load_learning_graph` của Pha B và `_assemble` của bài giảng. Với mọi node được dạy, test so câu neo/chunk dạy với artifact nguồn, kiểm định nghĩa và trích dẫn đúng chunk. Fixture A4 có chunk thật nhưng không đóng gói parse; test tạo parse thử từ chính các đoạn chữ và số trang đó để bộ nạp truy nguồn. Không sửa nguồn Pha B.

## Phép đo đặt tên module của 19f

Composition bọc stage đặt tên module đang được sử dụng bằng bộ đo stage có sẵn. `test_composed_module_naming_records_time_outside_semantic_payload` thực thi stage thật qua composition, không dùng mô hình trả phí: trước sửa đỏ vì manifest thiếu `stats`; sau sửa có `stats.runtime_seconds`. Số trường thời gian trong payload không tăng, config không thêm thời gian. Các trường thời gian cũ trong `cluster_stats` được giữ nguyên.

Lệnh kiểm tra cuối cho 19d, 19e và phép đo đặt tên module:

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/application/test_phase_b_gop_graph_19e.py tests/unit/presentation/test_canonical_defaults_19d.py -p no:cacheprovider --basetemp=tmp/pytest-19def-green-06 --tb=short
```

Kết quả: **11 test qua**, 18,13 giây. Kiểm toàn kho cuối: **1.617 test qua**, mã thoát 0, 458,03 giây; xem [báo cáo tích hợp](v4-19-phan-tich-va-kiem-chung-2026-10-17.md).
