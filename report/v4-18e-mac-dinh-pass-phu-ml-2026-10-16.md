# Vé 18e — mặc định pass phụ là ML

Ngày 2026-10-16. Điều kiện mở đã có: 18d đạt ở `27b80c3`, chủ dự án duyệt; ADR 0015 và CONTEXT do Claude cập nhật ở `8b891c4`.
Phạm vi nhân viên: đổi mặc định, đồng bộ cấu hình mẫu/hướng dẫn và kiểm thử. **0 lời gọi API / 0 USD**.

## Thay đổi

- Chỉ một dòng runtime: `Settings.secondary_mode` từ `llm` thành `ml`. Không sửa composition hoặc stage ML/LLM.
- `.env.example` dùng `DOC2ROADMAP_SECONDARY_MODE=ml`. Chủ dự án yêu cầu thêm việc đồng bộ `.env` thật trong lượt này: đã thêm đúng dòng
  `DOC2ROADMAP_SECONDARY_MODE=ml`, giữ nguyên mọi giá trị khác. Tệp `.env` vẫn được Git bỏ qua, **không commit hoặc in khóa bí mật**.
- Không có override thì chuỗi chọn `BuildSecondaryMLEdges`, sinh algorithm_id `a8-secondary-ml-v1` với mode `ml`.
- Biến môi trường hoặc `.env` đặt rõ `llm` vẫn được tôn trọng. Muốn bỏ override trong PowerShell:

```powershell
Remove-Item Env:DOC2ROADMAP_SECONDARY_MODE -ErrorAction SilentlyContinue
.\.tools\uv.exe run doc2roadmap roadmap --doc-id <ma-tai-lieu> --dry-run
```

Nếu `.env` ở máy khác còn dòng ghim `llm`, người chạy bỏ dòng đó hoặc đổi thành `ml`. Các khâu khác ngoài pass phụ vẫn qua cổng chi như trước; không nói cả
roadmap là miễn phí. Không thêm cờ CLI hoặc phụ thuộc, không huấn luyện/chấm lại E5. ADR/CONTEXT đã đúng, không viết lại phần Claude.

## Nghiệm thu hành vi, đỏ trước xanh sau

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
& .venv/Scripts/python.exe -m pytest tests/unit/presentation/test_secondary_ml_cli.py tests/unit/test_a3_config.py -q -o addopts= -p no:cacheprovider --basetemp tmp/pytest-18e-green
```

Trước đổi runtime/cấu hình mẫu: **3 failed, 3 passed**. Không chỉ kiểm một cờ tự gán: CLI mặc định đi vào nhánh LLM và trả lỗi SpendGuard, nên
test sinh artifact thực sự đỏ. Sau sửa: **6 passed**, 2 cảnh báo thư viện, **25,28 giây**, exit 0.

- `test_configuration_default_validation_and_ml_composition_without_allow_spend`: không truyền `secondary_mode`, bỏ env override và không đọc
  dotenv riêng; mặc định `ml`, chọn stage ML, chạy offline; biến môi trường `llm` chọn lại được stage LLM. Giá trị lạ vẫn bị bác.
- `test_roadmap_cli_without_mode_option_runs_ml_and_produces_ml_artifact`: gọi **`main(["roadmap", "--doc-id", "doc"])`**, không cờ chọn mode,
  không `--allow-spend`, không `--stop-after`; đi qua CLI/composition/orchestrator thật, tới stage ML thật. Artifact lưu qua Store trong bộ nhớ
  có algorithm_id `a8-secondary-ml-v1`, mode `ml`, một cạnh được validator pass chính nhận, secondary_usd=0; scorer chạy đúng một lần và lưu đúng
  một graph. Cũng kiểm các stage sau pass phụ được orchestrator gọi đúng thứ tự.
- `test_example_lists_every_setting_and_keeps_api_key_empty`: cấu hình mẫu và giá trị mặc định đều phải là `ml`, vẫn đủ mọi key và để API key rỗng.

Giới hạn rõ: đây là kiểm chuỗi trên dữ liệu tổng hợp, scorer/tokenizer giả, các stage ngoài pass phụ giả lập cache. Không tự nhận là chạy lại sách
mới từ PDF, không thay nghiệm thu chất lượng hay chuỗi thật D-01 mà Claude đã chạy ở 18d. Đường ML và mô hình không đổi từ mốc đã nghiệm thu.

## Hồi quy và phạm vi commit

Chạy toàn bộ tests ngoài sandbox để các test localhost Pha B không bị WinError 10013 đã biết:

```powershell
$env:PYTHONPATH='C:\Users\ngoco\Desktop\Doctoroadmap\src'
$env:PYTHONIOENCODING='utf-8'
& .venv/Scripts/python.exe -m pytest tests -q -o addopts= -p no:cacheprovider --basetemp tmp/pytest-18e-full-approved
```

**1.385 passed**, 7 cảnh báo thư viện, **187,14 giây**, exit 0. Kiểm đọc cấu hình thật sau khi đồng bộ `.env`, không có env override trong process:

```powershell
$env:PYTHONPATH='src'
Remove-Item Env:DOC2ROADMAP_SECONDARY_MODE -ErrorAction SilentlyContinue
& .venv/Scripts/python.exe -c 'from doc2roadmap.config import Settings; mode = Settings().secondary_mode; assert mode == "ml"; print("workspace .env secondary_mode:", mode)'
```

Exit 0, chỉ in `workspace .env secondary_mode: ml`, không in giá trị khác. `.env` vẫn được Git bỏ qua.

Chỉ stage tám tệp vé này; không lấy những thay đổi Pha B hoặc công việc khác đang dở trong cùng worktree. Đã xuất snapshot index riêng ở
`tmp/v4-18e-index` bằng `git checkout-index --all --prefix=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/v4-18e-index/`, không ghi đè hoặc revert worktree.
Chạy toàn bộ tests ở cwd snapshot với PYTHONPATH trỏ src snapshot, interpreter venv gốc, basetemp `tmp/pytest-18e-index` ở cây gốc:
**1.203 passed**, 7 cảnh báo thư viện, **205,06 giây**, exit 0. Phần commit không cần mã Pha B chưa commit. Sau kiểm này chỉ cập nhật Markdown;
mã runtime/test giữ nguyên. `.env` thật không có trong index hay snapshot, nên kiểm này cũng xác nhận hoạt động theo mặc định `ml` không nhờ
override cục bộ. `git diff --check` sạch trên các tệp của vé.
