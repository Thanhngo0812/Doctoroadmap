# F53 — Quyết định learnable bền qua các lần chạy

## Cách dùng

Registry quyết định của người nằm tại `<DOC2ROADMAP_ARTIFACT_DIR>/type_registry.json`
(mặc định `artifacts/type_registry.json`), dùng chung cho các tài liệu trong cùng kho artifact.
Tạo hoặc sửa tệp này khi review kiểu ở A13. Ví dụ **minh họa**, không phải quyết định đã duyệt:

```json
{
  "node_types": {
    "tool": {"learnable": false, "reviewed": true},
    "component": {"learnable": false, "reviewed": false}
  }
}
```

Chỉ mục có `reviewed: true` mới thắng suy diễn. Không có tệp, không có kiểu, hoặc
`reviewed: false` thì vẫn dùng dự đoán và bỏ phiếu F50. Không tự chuyển suy diễn thành
quyết định đã duyệt. Chưa tự phán quyết Makefile/ReadPump/WritePump thay người dùng.
Giao diện A13 chưa được triển khai; thao tác review hiện tại là sửa JSON.

Mỗi lần `extract`/`a3` đọc lại registry trước khi kiểm tra cache. Bản chụp các quyết định
được lưu trong config và stats; nội dung này tham gia `config_hash`. Đổi quyết định
làm cache cũ không khớp, không cần `--force`. Thuật toán lên `a3-section-conversation-v3`
để không tái dùng artifact cũ thiếu cảnh báo. Prompt và `prompt_hash` không đổi.
Registry không bị tiến trình trích xuất ghi đè. Artifact cũ vẫn giữ nguyên cho đối chiếu.

Quyết định áp dụng trước embedding, metrics và registry thống kê của từng tài liệu.
Kiểu chưa duyệt có 1–2 ứng viên phát `learnable_low_confidence: <type> (<count>)`.
Không cảnh báo figure/table: hai kiểu này do code quy định `learnable=false`, không
phải suy diễn ít phiếu. Registry từ chối chỉnh hai kiểu dành riêng này, tên chưa chuẩn hóa,
và giá trị không phải boolean; không âm thầm bỏ qua tệp sai.

## Kiểm chứng

Bộ test đầy đủ: **202 passed**, gồm 5 integration test, 67,28 giây.
Lệnh: `.venv/Scripts/python.exe -m pytest --basetemp tmp/pytest-f53-full -p no:cacheprovider`.

- `test_reviewed_type_survives_runs_and_invalidates_cache`: đã thấy thất bại trên code
  cũ vì vẫn tái dùng cache sau khi ghi quyết định; sau sửa kiểm tra mất cache, 0 embedding,
  0 node học được, giữ tệp qua instance mới, và cho embedding trở lại khi người đổi quyết định.
- `test_low_confidence_threshold_for_unreviewed_types`: ngưỡng 2/3 ứng viên và mục chưa
  duyệt không được ghi đè dự đoán. Cảnh báo thiếu cũng đã được thấy thất bại trên code cũ.
- `test_registry_only_loads_explicit_human_decisions`: thiếu tệp và lọc trạng thái duyệt.
- `test_registry_rejects_invalid_decisions`: dữ liệu sai cấu trúc, sai boolean, sai tên,
  và kiểu media dành riêng đều bị từ chối.

Không gọi lại mô hình thật: F53 thay thứ tự ưu tiên dữ liệu hậu xử lý, không đổi prompt;
test dùng phản hồi cố định để cô lập nguyên nhân. Số corpus vòng 15 là số lịch sử,
không phải kết quả chạy lại F53.

## Còn mở

F47 chưa được giải quyết: cần hiệu chỉnh few-shot riêng cho giáo trình xác suất và báo cáo
kỹ thuật, rồi chạy A/B recall/mật độ trên corpus. Không đổi prompt chung hoặc tuyên bố
mật độ đã được sửa chỉ nhờ registry.
