# 05c — Nhãn vùng mới tới canonical khi A3 ghim bản chunk đã có nhãn

Ngày 2026-10-17. Nhân viên chỉ sửa mã và chạy test; chi phí mô hình **0 USD**.
Không chạy lệnh ghi kho `artifacts/`, không chạy lại nhãn/canonical/roadmap trên
T-01 hoặc D-01. Nhánh B đang chạy được để nguyên.

## Bản sửa

`JsonArtifactStore.load_role_chunks(doc, N)` lấy bản gốc R từ metadata của N
nếu N là bản nhãn. Sau đó chọn bản nhãn **mới hơn N**, gán từ đúng R. Nếu N
chưa nhãn thì R chính là N, giữ đường 05b. Không có bản mới phù hợp thì trả N,
không quay lùi về một bản nhãn cũ hơn.

Mọi bản thay thế vẫn phải có cùng `source_hash` và cùng danh sách
`(chunk_id, text, char_start, char_end)` với N. Bản mới khớp nguồn gán nhưng
sai danh tính hoặc source bị từ chối; không âm thầm quay về nhãn cũ.

Không đổi mã thuật toán chunk, cấu hình chunk/A3, nội dung chunk hoặc prompt.
`anchor_chunks_version` đã nằm trong config canonical nên chọn nhãn mới tự
làm đổi config hash canonical. Lời gọi gộp và mô tả tiếp tục tái dùng nhật ký.

`Canonicalize.plan` bổ sung `anchor_chunks_version=<version>` trong `note`
của pha `anchor`, cả khi có cache lẫn khi cần chạy lại. CLI `a4 --dry-run`
đã in `note`, vì vậy không cần đổi schema chung `StagePlan` hoặc mã CLI.
Không đưa ghi chú kế hoạch vào config/payload canonical.

## Kiểm chứng trên kho tạm

Test mới: `tests/unit/application/test_role_chunks_05c.py`, **14 ca**:

- `test_labeled_a3_input_uses_latest_relabel_from_its_original_chunks`: v1
  chưa nhãn, v2/v3 cùng gán từ v1; nạp nhãn của v2 phải trả v3. Trên mã cũ
  đã thấy trả nhầm **v2**. Việc đọc không ghi lại tệp.
- `test_unlabeled_05b_input_still_uses_labels_from_that_version`: đầu vào
  chưa nhãn vẫn nhận bản gán mới nhất từ chính nó.
- `test_no_newer_sibling_returns_requested_labels_not_an_older_sibling`:
  không có bản mới hợp lệ thì giữ bản đã ghim, bỏ qua bản gán từ nguồn khác.
- `test_newer_labels_cannot_change_chunk_identity_or_source`: 10 trường hợp
  gồm đầu vào có/chưa nhãn, mỗi trường `chunk_id`, `text`, `char_start`,
  `char_end`, `source_hash` bị đổi đều phải bị từ chối.
- `test_canonical_and_cli_dry_run_follow_new_sibling_without_invalidating_a3`:
  A3 trên bản nhãn v2, canonical đầu dùng v2 và không neo vì vùng mở đầu;
  có v3 cùng nguồn gốc thì dry-run báo v3, không ghi tệp hoặc gọi mô hình;
  execute dùng mô hình/embedding giả sinh canonical mới có neo và khái niệm
  được dạy. Số lời gọi gộp/mô tả không tăng; mọi JSON ứng viên A3 và chunk gốc
  giữ nguyên bytes. Cả version nhãn trong plan cache hit cũng được kiểm.

**Red trước sửa:** 7 failed, 7 passed, 8,10 giây;
`tmp/pytest-05c-red.xml`. Gồm ca chọn nhãn v3, năm ca từ chối bản nhãn mới
hỏng khi A3 ghim nhãn, và thông tin version trong kế hoạch.

**Green tập trung:** 62 passed, 20,64 giây;
`tmp/pytest-05c-green.xml`. Gồm test mới, nhãn vùng, canonical gộp, các hash
đóng băng 19n và hồi quy 05a.

**Toàn kho:** 1.572 passed, 7 cảnh báo deprecation, 277,92 giây, exit 0;
`tmp/pytest-05c-full.xml`. Không có lỗi hoặc test bị bỏ qua. `git diff --check` qua.

## Cách ly kho đang chạy

Toàn bộ dữ liệu dựng/test mới dùng `tmp_path` trong `tmp/pytest-05c-*`, mô hình
giả hoặc replay fixture phát triển. Không đọc nội dung hai cuốn T-01.
Không gọi CLI ngoài pytest trên kho chính, không chi API.

Lượt green tập trung và toàn kho dùng audit hook cục bộ
`tmp/05c/sitecustomize.py`, nạp qua `PYTHONPATH=tmp/05c`, chặn thao tác ghi,
tạo thư mục, xoá, đổi tên hoặc sửa metadata trong `artifacts/` của repo.
Đã thử nhánh chặn: mở tệp ghi bị từ chối **trước khi tạo tệp**. Guard chỉ thuộc
tiến trình test và tiến trình con kế thừa môi trường, không tác động tiến trình
nhánh B đang chạy. Không đổi quyền filesystem, `.env` hoặc cấu hình sản phẩm.

Lệnh toàn kho:

```powershell
$env:PYTHONPATH='tmp/05c'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=tmp/pytest-05c-full --junitxml=tmp/pytest-05c-full.xml --tb=short
```

Phần production chỉ sửa hai file: bộ nạp artifact và kế hoạch canonical.
Mã 05c chưa commit; HEAD nền khi bắt đầu `986ff12` không chứa bản sửa.
Các số kiểm toàn kho phản ánh workspace kết hợp hiện có (có cả công việc
A1/D-01/Pha B và test script T-01b), không phải checkout sạch của commit 05c.
Claude chạy nhánh C sau khi ghim mã và sau khi lượt hiện tại cho phép; không
coi hết khoảng 1,5–2 giờ là tự có quyền ghi kho chính.
