# 01 — Chạy thử có dự toán

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R10 · **Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** 0

**Trạng thái:** **đạt** — Claude kiểm thử 2026-09-26 (mục cuối)

## Vì sao
Sự cố 2026-09-26: `roadmap --allow-spend` chạy lại pass phụ A8 cho doc-2 (≈ 7,4 USD nếu để hết) mà không ai thấy trước. Chốt chặn
hiện chỉ báo stage **đầu tiên** định chi.

## Việc cần làm
- `roadmap --doc-id X --dry-run`: không gọi mô hình; đi qua chuỗi, với mỗi stage cho biết **tái dùng** (artifact cache có sẵn),
  **sẽ chạy** kèm số việc còn thiếu (cặp/khái niệm/phiên chưa có trong checkpoint) và USD ước theo giá trong `prerequisite_prompt`,
  hoặc **chưa biết** (phụ thuộc stage trước chưa có artifact).
- Mỗi use case trả tiền có phương thức lập kế hoạch thuần (đọc cache và checkpoint, đếm việc còn thiếu), dùng chung cho `--dry-run`.

## Tệp liên quan
`presentation/cli/main.py`, `composition.py`, `application/use_cases/build_learning_graph.py`, các use case A8/neo/danh tính.

## Nghiệm thu
- Test: chuỗi giả có stage cache và stage thiếu → báo đúng trạng thái từng stage; không lời gọi mô hình nào (mô hình giả ném lỗi
  nếu bị gọi).
- **Tôi kiểm:** `--dry-run` trên doc-2 phải báo pass phụ "sẽ chạy" với số cặp ≈ phần còn thiếu của checkpoint `secondary-9bb6…`.

## Kiểm thử của nhân viên

Đã thấy test đỏ trước sửa; `test_roadmap_plan.py` kiểm chuỗi cache/thiếu/chưa biết, mọi use case trả tiền không gọi
model/embed và không ghi, trừ checkpoint đúng nguồn, dry-run thắng allow-spend. Kiểm cả `SpendGuard` của embedding.
Doc-2 báo đúng `secondary-9bb6…`: 9.360 cặp còn lại, 2.650 cặp cắt ngay, 6.710 cần phán hai chiều,
ước 7,179442 USD; các stage sau báo chưa biết. So SHA-256/mtime 78 file trước–sau không đổi. Không chạy A8.
Chi tiết và giới hạn dự toán: [báo cáo](../../report/v3-01-03-10-ket-qua-2026-09-26.md).

## Kiểm thử (Claude, 2026-09-26) — đạt

- Đọc diff: mọi `plan()` dùng chung nhánh cấu hình/cache với `execute()` và trả về trước lời gọi mô hình và mọi lệnh ghi;
  `SpendGuard` bọc thêm `embed`; `--dry-run` thắng `--allow-spend`.
- Test: toàn bộ 660 test (unit + tích hợp) xanh. Trong sandbox phải chạy kèm `--basetemp` vì pytest không được đọc thư mục tạm
  mặc định; đó là lỗi quyền của môi trường, không phải lỗi mã. Đột biến 4/4 bị test bắt: dry-run không còn thắng allow-spend;
  plan pass phụ đi tiếp vào nhánh chạy thật; plan neo bỏ qua checkpoint; `SpendGuard` không chặn embedding.
- `roadmap --doc-id doc-2 --dry-run` chạy thật: pass phụ "sẽ chạy", checkpoint `secondary-9bb6…`, 9.360 cặp (2.650 cắt ngay,
  6.710 phán hai chiều), ước 7,18 USD; các stage sau "chưa biết". Chụp toàn bộ 1.600 file `artifacts/` trước và sau (cỡ, mtime,
  SHA-256 của 180 file doc-2): không file nào thêm, bớt hay đổi.
- Dry-run thêm năm tài liệu:
  - doc-1 và doc-6: identity "sẽ chạy" (378 và 31 cặp), vì `a10-identity-v2` đổi cấu hình;
  - nhap-mon-ml, doc-3, naive-bayes: pass phụ "sẽ chạy" (1.041 / 231 / 124 cặp; ước 1,99 / 0,12 / 0,25 USD). Tình trạng này có từ
    trước: artifact còn ở `a8-secondary-pass-v3`, thuật toán lên v4 từ F126 ngày 23/9, không do vé 03.

  Đây đúng là thông tin mà sự cố 0,64 USD thiếu.
- Giới hạn, chấp nhận: khi chưa có checkpoint, dự toán lấy 512 token output mỗi lời gọi nên cao hơn thực tế (identity doc-1 ước
  0,36 USD, bản thử chi thật 0,094 USD, khoảng 3,8 lần). Ước cao thì an toàn hơn ước thấp, nên không cần sửa.
