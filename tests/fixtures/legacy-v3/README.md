# Fixture đọc artifact v3 sau 19n

`baocao-canhan.json` đóng băng canonical và graph danh tính do harness của
`test_phase_b_gop_graph_19e.py` sinh trước khi gỡ stage ở 19n, từ mã `2c93c5a`.
Đầu vào là fixture trích xuất/chunk của `baocao-canhan`; mô hình và embedding
trong harness là giả. Đây không phải artifact của một lượt gọi mô hình thật.

Harness cũ xoá `requires_edges` và đặt `cluster_id="fixture-cluster"` trên các
node của graph danh tính trong bộ nhớ trước khi dựng A10. Snapshot giữ đúng
đầu vào này; `roadmap_payload_hash` là hash của đầu ra A10 trước khi dọn mã.
Graph có một mục `identity_map` khác rỗng, cùng `merged_nodes` tương ứng.

`tests/legacy_v3.py` nạp snapshot vào kho tạm, không cần gọi lại stage đã gỡ.
Các assertion chạy được:

- `test_cleanup_19n.py::test_a8_still_reads_frozen_v3_identity_artifact`:
  A8 giữ bản đồ danh tính, thực sự hoàn thành các phiên pass chính.
- `test_cleanup_19n.py::test_scorers_still_read_frozen_v3_and_apply_its_identity_map`:
  E1/E2 đọc graph; E4 chuyển cạnh alias thành tự nối, báo loại đúng một cạnh,
  không sửa tệp vàng.
- `test_phase_b_gop_graph_19e.py::test_phase_b_loader_and_lecture_context_accept_real_roadmap[v3]`:
  A10 giữ đúng hash cũ; Pha B nạp được neo, nơi dạy và citation để dựng bài giảng.

Các hash của mặc định canonical gộp, `--names-only` và `--prepare` được đóng băng
riêng trong `test_cleanup_19n.py`; chỉ config của canonical đầy đủ thay đổi do
19o bỏ các mục cấu hình cũ.
