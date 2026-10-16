# Vé 18c-1 — ngưỡng pass phụ ML tới điểm bất động

Ngày 2026-10-16. Chỉ sửa luật ngưỡng theo spec đã cập nhật sau lượt nghiệm thu 18d, không chỉnh theo vàng. Không đổi mô hình E5, bộ hiệu chỉnh,
82 đặc trưng, bộ khớp tên, luật chọn/tỉa cặp, validator hay merge của pass chính. Không mở D-01 hoặc hai sách khóa T-01. **0 lời gọi API, 0 USD**.
Mặc định sản phẩm vẫn là `llm`; 18d và quyết định đổi mặc định 18e chưa được thay thế bằng báo cáo triển khai này.

## Cách thực hiện

- Giữ t₀ tính trên chiều ứng viên chưa bị main tỉa. Chỉ tính đặc trưng, chấm và hiệu chỉnh một lần.
- Mỗi lượt lắp từ main, tỉa trước từng cặp như cũ, rồi tính t' từ **mọi chiều ứng viên của cặp được phán**: gồm cả cặp dưới ngưỡng/không có
  căn cứ, không chỉ chiều thắng hoặc cạnh được nhận. Không tính các cặp bị tỉa.
- k=0: chọn threshold null, không giữ cạnh thử; dừng ngay cả khi lắp lại không cạnh làm tập được phán tăng. Đây là luật dừng riêng của spec,
  không cố tìm thêm điểm bất động sau k=0.
- t'=t: dừng. Lặp ngưỡng: lấy lớn nhất trong đoạn lịch sử bắt đầu tại ngưỡng lặp, loại phần quá độ trước vòng.
- Tối đa **10 lượt thử**. Chạm giới hạn: lấy lớn nhất trong các ngưỡng đã thử, không lấy t' mới tính nhưng chưa thử.
- Nếu ngưỡng chọn khác ngưỡng lượt cuối, lắp lại một lần. Chỉ lưu cạnh, `secondary_log`, `executor_log` của kết quả cuối; giữ nguyên log main.
  Lượt lắp lại này không nằm trong số lượt thử. Không lưu artifact trung gian hoặc cộng chi phí giả.
- `threshold_history`, `threshold_iterations`, `threshold_oscillation`, `threshold_stop_reason`, `threshold_final_reassembled` trong stats.
  `expected_positive_count` là k sinh ra ngưỡng đã chọn (k=0 khi threshold null), không phải số cạnh được validator nhận. Khi dao động/giới hạn,
  không khẳng định ngưỡng cuối là điểm bất động.
- Config đổi luật thành `round-sum-isotonic-on-judged-directions-fixed-point-10-v1`; cache theo luật cũ không được tái dùng. Cache LLM không đổi.

Skill ponytail dẫn tới tách đúng vòng lắp cạnh hiện có thành một hàm dùng lại; không thêm framework tối ưu, cấu hình số vòng, phụ thuộc hay dịch vụ.

## Kiểm thử có thể bác bỏ

Bốn ca yêu cầu trong vé đều chạy qua `execute` với scorer/tokenizer giả; lần đầu trên mã cũ: **4 failed**. Sau sửa, **21 test stage passed**,
bao gồm toàn bộ test 18c cũ. Ca hội tụ được củng cố thêm bằng đồ thị không lặp cặp và xác suất tăng theo điểm, thay vì chỉ dùng cặp trùng.

| Luật | Test trong `tests/unit/application/test_build_secondary_ml_edges.py` | Hệ quả kiểm độc lập |
|---|---|---|
| Hội tụ, khác t₀ | `test_fixed_point_changes_initial_threshold_and_discards_trial_edges_and_logs` | t: 0,7 → 0,8; cạnh b→d của lượt thử biến mất; chỉ 2 cạnh/log nhận cuối |
| Dao động hai ngưỡng | `test_two_threshold_cycle_selects_larger_threshold_not_last_computed` | t: 0,8 ↔ 0,9; chỉ giữ c→d |
| k=0 sau tỉa | `test_zero_k_after_dynamic_pruning_removes_trial_edges_and_stops` | cạnh đã tạo thử bị bỏ, log cuối không tạo cạnh, k=0 |
| Giới hạn 10 lượt | `test_threshold_iteration_limit_is_ten_not_early_convergence_or_unbounded` | ngưỡng cuối 10/12, đúng hai cạnh cuối; thay giới hạn 11 thì trượt |
| Lắp lại ngưỡng đã chọn | `test_cycle_reassembles_chosen_threshold_instead_of_saving_last_trial` | lượt cuối thử 0,6 nhưng artifact dùng 0,8; không giữ cạnh a→b; bảo toàn log main |
| Chỉ lấy max trong vòng | `test_cycle_maximum_excludes_transient_threshold_before_cycle` | lịch sử 0,5 → 0,8 → 0,6 ↔ 0,7: chọn 0,7, không lấy 0,8 |
| Cache đổi luật | `test_fixed_point_rule_does_not_reuse_old_one_shot_cache` | cache giả lập luật 18c bị bỏ qua, tạo version mới |

Riêng ca giới hạn dùng seam selector để ép chuỗi tập được phán dài hơn 10; chấm điểm, lắp, validator, log và save vẫn qua `execute`. Các ca hội
tụ/dao động/k=0/lắp lại dùng selector và bộ kiểm thật trên đồ thị tổng hợp. Không giả rằng đồ thị thực chắc chắn phải chạm 10 lượt.

```powershell
$env:PYTHONPATH='src'
& .venv/Scripts/python.exe -m pytest tests/unit/application/test_build_secondary_ml_edges.py -q -o addopts= -p no:cacheprovider --basetemp tmp/pytest-18c1-more
& .venv/Scripts/python.exe scripts/pass-phu-ml/kiem_dot_bien_18bc.py
```

Đột biến trong bộ nhớ process con, không sửa source: **28/28 detected**, gồm 20 luật 18b/c và 8 luật mới: dùng lại tập main thay tập được phán,
chọn min của vòng, lấy max cả quá độ, bỏ dừng k=0 sau tỉa, tăng giới hạn thành 11, chọn min khi hết lượt, không lắp lại cuối, dùng khóa cache cũ.

## Hồi quy và chạy thử thực

**Toàn worktree:** lượt sandbox **1.381 passed / 3 failed**, lỗi chỉ ở test máy chủ Pha B vì localhost WinError 10013. Không sửa mã để né lỗi;
xin quyền chạy lại ngoài sandbox: **1.384 passed**, 7 cảnh báo thư viện, **189,25 giây**, exit 0.

```powershell
$env:PYTHONPATH='C:\Users\ngoco\Desktop\Doctoroadmap\src'
$env:PYTHONIOENCODING='utf-8'
& .venv/Scripts/python.exe -m pytest tests -q -o addopts= -p no:cacheprovider --basetemp tmp/pytest-18c1-full-approved
```

**Snapshot riêng phần commit:** chỉ stage sáu tệp của vé này; `git checkout-index --all --prefix=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/v4-18c1-index/`
xuất index vào thư mục mới, không ghi đè/revert worktree. Chạy cùng interpreter venv gốc, cwd và PYTHONPATH trỏ snapshot, basetemp riêng:
**1.202 passed**, 7 cảnh báo thư viện, **196,66 giây**, exit 0. Phần commit không cần mã Pha B đang dở. Sau kiểm này chỉ cập nhật Markdown bằng kết
quả đo; mã runtime và test giữ nguyên.

Chạy stage trên pass chính cũ trong **kho thử riêng** `tmp/v4-18c1-smoke`, không chạy A8 main, A9/A10 hoặc chấm nhãn vàng:

```powershell
$env:PYTHONPATH='src'
& .venv/Scripts/python.exe scripts/pass-phu-ml/thu_stage_san_pham.py doc-1 --output tmp/v4-18c1-smoke
& .venv/Scripts/python.exe scripts/pass-phu-ml/thu_stage_san_pham.py xstk-ch3-1 --output tmp/v4-18c1-smoke
& .venv/Scripts/python.exe scripts/pass-phu-ml/thu_stage_san_pham.py doc-4 --output tmp/v4-18c1-smoke
```

| Tài liệu | Main version | Chiều ứng viên sau main | Ngưỡng cuối | k | Lượt thử | Kết thúc | Cạnh pass phụ | Giây stage |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| doc-1 | 1 | 701 | 0,5342419314016353 | 214 | 3 | điểm bất động | 199 | 65,714 |
| xstk-ch3-1 | 41 | 203 | 0,538803689882039 | 71 | 2 | điểm bất động | 60 | 33,994 |
| doc-4 | 7 | 4.001 | 0,4762384152110359 | 857 | 4 | dao động | 749 | 463,479 |

Tất cả exit 0, tạo **v1** trong kho thử, manifest **0 lời gọi API**, secondary_usd **0**; execute kế tiếp cùng input tái dùng đúng v1. Kho thử
tham chiếu input main/chunk ở kho gốc, **không phải chuỗi lineage tự chứa**. Không lấy các phiên bản thử làm bản production mới.

Lịch sử ngưỡng (có trong stats; số lượt gồm lượt xác nhận t'=t):

- doc-1: 0,5620162673510672 → 0,5377513139023106 → 0,5342419314016353, rồi t'=t.
- xstk: 0,5406889347162543 → 0,538803689882039, rồi t'=t.
- doc-4: 0,5007263942966618 → 0,47648843596704943 → 0,4750878366574615 → 0,4762384152110359, rồi t' quay lại 0,4750878366574615.
  Chọn max của **hai ngưỡng trong vòng**, không lấy hai ngưỡng quá độ cao hơn. Ngưỡng chọn trùng lượt cuối nên không cần lắp lại.

Số cạnh trùng số mô phỏng Claude ghi trong 18d, nhưng **trùng số đếm không chứng minh trùng tập cạnh hoặc đạt E4**. Không tự chấm thay 18d.

**Thời gian:** các số trong bảng được đo khi máy còn chạy kiểm thử, doc-4 mất **7,72 phút**; không dùng lượt ấy để khẳng định đạt mục tiêu 5 phút.
Đo lại doc-4 riêng, sau khi hai bộ kiểm thử kết thúc:

```powershell
& .venv/Scripts/python.exe scripts/pass-phu-ml/thu_stage_san_pham.py doc-4 --output tmp/v4-18c1-timing
```

**244,5838187 giây = 4,08 phút**, exit 0, 749 cạnh, 4 lượt thử, cùng ngưỡng/vòng dao động; đạt mục tiêu stage dưới 5 phút trên máy này trong
lượt đo riêng. Pass phụ ML vẫn **0 lời gọi / 0 USD**. Mốc 18c cũ chỉ lắp một lượt (182,30 giây trong báo cáo nhân viên, 138 giây trong báo cáo
Claude); không quy chênh lệch thời gian của những lượt có tải nền khác nhau thành phép so tốc độ kiểm soát. Luật mới có tối đa 10 lượt nên không
hứa mọi tài liệu đều dưới 5 phút.

Hai lượt doc-4 độc lập (không tái dùng cache giữa hai kho) có **cùng config_hash và cùng SHA-256 payload**. Kiểm cả ba tài liệu: đúng một dòng log
cho mỗi cặp, pair_id không lặp, mọi dòng dùng ngưỡng cuối. Thời gian chỉ nằm trong manifest, không làm khác payload tất định. Lượt execute tiếp
theo ở mỗi kho dùng cache đúng v1.

## Việc còn lại của 18d

Claude chạy lại nghiệm thu E4/Q7/Q7b/bao đóng và chuỗi D-01 đầy đủ theo vé 18d. Nhân viên không tự nới tiêu chí xstk hay đánh dấu chất lượng đạt.
