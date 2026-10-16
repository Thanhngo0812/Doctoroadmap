# 18c — Stage pass phụ chế độ `ml`

**Nguồn chân lý:** [spec pass phụ không LLM](../../doc/a8-pass-phu-ml-spec.md), mục 1, 4 và 5.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 18a, 18b · **Trạng thái:** đã cài/test xanh 2026-10-16, sẵn sàng Claude nghiệm thu 18d

## Vì sao

Đây là vé nối mọi thứ lại: chuỗi đồ thị chạy được pass phụ không LLM, ra artifact cùng hợp đồng với bản LLM.

## Cần làm

- Tuỳ chọn cấu hình chế độ pass phụ: `llm` (mặc định) hoặc `ml`. Chế độ nằm trong khoá cache.
- Thư mục mô hình của 18a được đóng gói vào wheel, giống mô hình A1 nhẹ.
- Cổng chấm điểm ở tầng ứng dụng. Bản cài LightGBM ở hạ tầng nạp tệp của 18a, và dừng với lỗi rõ khi tệp thiếu, sai băm, hay danh sách đặc trưng
  không khớp.
- Stage `a8-secondary-ml-v1`, đứng đúng chỗ pass phụ LLM:
  - ngưỡng theo từng tài liệu: k = tổng xác suất đã hiệu chỉnh trên ứng viên của các cặp còn lại sau khi tỉa bằng cạnh pass chính; ngưỡng là điểm
    của ứng viên thứ k;
  - duyệt cặp theo thứ tự hàm chọn cặp trả về, tỉa trước mỗi cặp giống bản LLM;
  - mỗi cặp chọn chiều điểm cao hơn;
  - chỉ tạo cạnh cứng `can_de_hieu` / `trong_dinh_nghia`, với câu trích đầu tiên qua bộ kiểm hợp đồng của pass chính, thử theo khoảng cách tới câu neo;
  - nhật ký từng cặp ghi trạng thái (`created`, `below_threshold`, `no_evidence`, các trạng thái tỉa), điểm hai chiều, ngưỡng và câu trích;
  - `stats` và `cost_summary` theo spec mục 5.
- Config và manifest ghi phiên bản và băm mô hình, danh sách đặc trưng, bộ tách từ, luật ứng viên, luật ngưỡng và luật tỉa.
- `--dry-run` báo 0 lời gọi, 0 USD. Chế độ `ml` không cần `--allow-spend` cho pass phụ.

## Nghiệm thu

- [x] Test qua `execute` của stage, với kho artifact trong bộ nhớ, bộ chấm điểm giả và bộ tách từ giả:
  - cặp trên ngưỡng có câu hợp lệ thì thành cạnh cứng;
  - cặp dưới ngưỡng ghi `below_threshold`;
  - cặp không có câu qua bộ kiểm ghi `no_evidence`;
  - cạnh mới tỉa các cặp phía sau;
  - chiều điểm cao hơn được chọn;
  - ca ngưỡng có k = 0;
  - không có cạnh mềm hay `cong_cu`;
  - pass chính chưa hoàn chỉnh thì từ chối;
  - chạy lại thì dùng cache;
  - hai lần chạy cùng băm payload.
- [x] Test bản cài LightGBM trên tệp mô hình nhỏ dựng trong test: kiểm băm, thứ tự đặc trưng, và nội suy của bộ hiệu chỉnh.
- [x] Mỗi luật có ít nhất một test thấy nó trượt khi luật bị bỏ (AGENTS.md mục 5).
- [x] Toàn bộ test cũ vẫn qua. Chế độ `llm` không đổi hành vi.

## Bàn giao nhân viên 2026-10-16

- `DOC2ROADMAP_SECONDARY_MODE=ml` nối stage mới qua composition; mặc định vẫn `llm`. Đường LLM giữ nguyên mã/cache/checkpoint; ML có mode và
  algorithm/model/calibration/tokenizer/rules riêng trong khóa cache. Không sửa `.env` thật.
- Bộ chấm offline kiểm tệp/hash/feature và nội suy JSON; mô hình 18a đóng vào wheel. Đã cài wheel ở tmp riêng, chặn socket và nạp/chấm/tách từ đạt.
- Toàn bộ worktree: **1.377 passed**, exit 0, 7 cảnh báo thư viện. Kiểm đột biến dữ liệu giả: **20/20 detected**, lệnh tái lập trong báo cáo.
- Snapshot riêng đúng phần sắp commit (không mã Pha B chưa commit): **1.195 passed**, exit 0; commit có thể kiểm độc lập.
- Kiểm vận hành doc-4 trong kho thử riêng: **182,30 giây**, **715 cạnh pass phụ**, 0 API/0 USD, lần sau dùng cache. Không chạy A9/A10 hoặc chấm vàng;
  số chất lượng và chuỗi D-01 đầy đủ để Claude làm ở 18d. Chưa đổi mặc định hoặc làm 18e.
- Xem [báo cáo](../../report/v4-18bc-pass-phu-ml-2026-10-16.md) và [hướng dẫn CLI](../../doc/a8-pass-phu-ml-cli.md).
