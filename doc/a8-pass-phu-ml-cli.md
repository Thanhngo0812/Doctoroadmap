# Pass phụ ML — lệnh cho vé 18b/18c

Đã cài đường chạy E5, nhưng **mặc định vẫn là `llm`**. Chỉ đổi mặc định theo vé 18e sau nghiệm thu 18d và chủ dự án duyệt.

## Xuất bảng 82 đặc trưng

```powershell
.\.tools\uv.exe run doc2roadmap a8-secondary-features --doc-id doc-4 --main-version 7 --output-dir tmp/v4-18b-features
```

Đầu vào phải là graph pass chính hoàn chỉnh, **không phải phiên bản pass phụ**. CSV gồm định danh cặp/hai đầu, tên hai đầu, cờ `ung_vien` và đúng
82 đặc trưng theo thứ tự E5. Ô thiếu giữ rỗng; bản chấm đổi rỗng/None/NaN thành −1. Không đọc nhãn hoặc gọi LLM/embedding. Đầu ra có tên khái niệm,
nên người chạy tự chọn nơi lưu, không commit bảng giáo trình.

Với kho graph khác kho chunk, truyền cả hai đường:

```powershell
.\.tools\uv.exe run doc2roadmap a8-secondary-features --doc-id doc-1 --main-version 1 --artifacts artifacts/v3-r12-final-evaluation --chunks-artifacts artifacts --output-dir tmp/v4-18b-features
.\.tools\uv.exe run doc2roadmap a8-secondary-features --doc-id nhap-mon-ml --main-version 1 --artifacts artifacts/v3-r12-final-evaluation --chunks-artifacts artifacts --output-dir tmp/v4-18b-features
.\.tools\uv.exe run doc2roadmap a8-secondary-features --doc-id xstk-ch3-1 --main-version 41 --output-dir tmp/v4-18b-features
```

Tự kiểm với bảng nghiên cứu bốn tài liệu phát triển, chỉ in số đếm/sai lệch:

```powershell
.\.tools\uv.exe run python scripts/pass-phu-ml/kiem_khop_san_pham.py
```

Lệnh này cần các CSV nghiên cứu địa phương; sản phẩm không phụ thuộc các CSV ấy hoặc script nghiên cứu khi chạy stage.

## Chọn chế độ cho chuỗi đồ thị

```powershell
$env:DOC2ROADMAP_SECONDARY_MODE='ml'
.\.tools\uv.exe run doc2roadmap roadmap --doc-id <ma-tai-lieu> --dry-run
```

Giá trị hợp lệ: `llm`, `ml`; mặc định `llm`. Không cần sửa `.env` để thử. Đường `ml` tạo algorithm_id `a8-secondary-ml-v1`, có mode/model hash/
calibration hash/feature list/tokenizer/rules trong config và khóa cache riêng. Đường LLM cũ giữ nguyên config/cache/luật phán, không mất checkpoint
hay tự buộc chạy lại bản cũ chỉ vì thêm chế độ mới.

**Chỉ pass phụ ML là 0 lời gọi, 0 USD và không cần `--allow-spend`.** Pass chính, embedding và các khâu đặt tên trong cùng chuỗi vẫn có thể tốn tiền;
cổng chi cũ vẫn chặn khi chưa cho phép. Dry-run của cả chuỗi có thể còn chi phí ở các khâu đó hoặc `unknown` nếu chưa có đúng artifact đầu vào.

Stage từ chối pass chính chưa hoàn chỉnh. Theo vé **18c-1**, ngưỡng khởi đầu tính trên chiều ứng viên chưa bị cạnh pass chính tỉa: k = round(tổng
xác suất hiệu chỉnh), ngưỡng là điểm thứ k giảm dần. Mỗi lượt lắp lại từ cạnh main, rồi tính lại ngưỡng trên **hai chiều ứng viên của các cặp
không bị tỉa** ở lượt ấy (kể cả cặp dưới ngưỡng hoặc không có căn cứ). Dừng ở điểm bất động; dao động thì chọn ngưỡng lớn nhất **trong vòng**,
không lấy ngưỡng quá độ trước vòng. Tối đa 10 lượt thử; chạm giới hạn thì chọn ngưỡng lớn nhất đã thử. k = 0 thì threshold null, không tạo cạnh
và dừng. Nếu chọn ngưỡng khác lượt cuối, lắp lại một lần bằng ngưỡng đã chọn. Chỉ lưu cạnh và nhật ký của lượt cuối này.

`stats` có `threshold_history` (các ngưỡng đã thử trong tối đa 10 lượt), `threshold_iterations`, `threshold_oscillation`, `threshold_stop_reason`
(`fixed_point`, `cycle`, `zero_positive`, `iteration_limit`), `threshold_final_reassembled`, `threshold` và `expected_positive_count` (k sinh ra
ngưỡng đã chọn, không phải số cạnh cuối). Lượt lắp lại cuối nếu cần không tính vào số lượt thử. Khóa cache mang luật
`round-sum-isotonic-on-judged-directions-fixed-point-10-v1`, không tái dùng artifact tính ngưỡng một lần của 18c.

Trong mỗi lượt, tỉa lại trước từng cặp; chọn chiều điểm cao hơn, thử câu trích gần neo trước, chỉ nhận cạnh cứng qua
`validate_main_proposals(require_kind=True)`. Hòa điểm chọn theo bộ `(score, source_id, target_id)` lớn nhất, như bộ lắp cạnh nghiên cứu.
Không fallback sang LLM hoặc `cong_cu`. Đặc trưng/điểm/hiệu chỉnh chỉ tính **một lần**, không chấm lại mô hình ở từng lượt lắp.

Tệp mô hình mặc định: `vendor/a8-pass-phu-ml/{model.txt,manifest.json}` trong source checkout, hoặc `doc2roadmap/infrastructure/secondary_models/`
trong wheel. Không dùng pickle, không tự học lại hay tải mô hình lúc suy luận. Bộ tách từ `underthesea==9.5.0` dùng CRF đóng gói trong thư viện,
cache theo câu. Đừng tự đổi model/tokenizer/rule nếu muốn dùng đúng mốc E5; đổi chúng phải đổi fingerprint rồi nghiệm thu lại.

## Công cụ kiểm triển khai

```powershell
.\.tools\uv.exe run --extra dev python scripts/pass-phu-ml/kiem_dot_bien_18bc.py
.\.tools\uv.exe run python scripts/pass-phu-ml/thu_stage_san_pham.py doc-4 --output tmp/v4-18c-smoke
```

Lệnh thứ nhất chỉ dùng unit test dữ liệu giả, sửa mã trong bộ nhớ của process con rồi bỏ đi; không sửa source. Lệnh thứ hai chỉ cho bốn tài liệu
phát triển, đọc pass chính cũ và ghi graph vào kho thử riêng, không chạy lại pass chính hoặc chấm vàng. Nghiệm thu Q7/Q7b/bao đóng và chuỗi D-01
đầy đủ thuộc vé 18d; hai sách khóa T-01 không dùng để chỉnh hoặc kiểm triển khai.

Kiểm lại luật điểm bất động 18c-1 trong kho riêng (không ghi đè mốc 18c):

```powershell
.\.tools\uv.exe run python scripts/pass-phu-ml/thu_stage_san_pham.py doc-1 --output tmp/v4-18c1-smoke
.\.tools\uv.exe run python scripts/pass-phu-ml/thu_stage_san_pham.py doc-4 --output tmp/v4-18c1-smoke
```
