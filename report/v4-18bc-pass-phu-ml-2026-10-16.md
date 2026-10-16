# Vé 18b/18c — đưa E5 vào sản phẩm

Ngày 2026-10-16. Phạm vi: đặc trưng + CLI xuất bảng (18b), cổng/bản cài chấm điểm và stage ML (18c). **0 lời gọi API, 0 USD** cho công việc này.
Không học lại mô hình, không đọc dữ liệu nhãn D-01, không mở hai sách khóa hoặc nhãn T-01, không đổi mặc định LLM. Mô hình dùng đúng tệp 18a.

## Thay đổi và luật giữ nguyên

- Miền `secondary_features.py`: đúng thứ tự 82 đặc trưng của E5, không `main_*`, nhận hàm tách từ được tiêm vào; giữ exact + ranh giới từ,
  chuẩn hóa từng âm tiết, bí danh của nghiên cứu, cùng cách tính PageRank/cửa sổ/cues/RefD. NetworkX là hàm tính đồ thị xác định đã có trong dự án,
  được cho phép riêng cho module này trong test kiến trúc, không đưa underthesea/hạ tầng/I/O vào miền.
- Hạ tầng tokenizer: underthesea **9.5.0**, CRF đóng gói sẵn, cache theo câu; lockfile chỉ thêm underthesea và underthesea-core.
- `a8-secondary-features`: đọc đúng phiên bản pass chính hoàn chỉnh, CSV ở nơi người chạy chọn, không đọc vàng/nhãn, không tạo graph hoặc gọi mô hình.
- Cổng `SecondaryScorer` ở tầng ứng dụng; bản LightGBM đọc model văn bản + JSON 18a, kiểm hash/thứ tự feature/giá trị thiếu/calibration. Nội suy
  tuyến tính kẹp hai đầu. Kiểm header trước C++ loader để lỗi thứ tự feature không làm abort Python.
- `BuildSecondaryMLEdges`: cùng vị trí pass phụ, select_secondary_pairs và bộ kiểm/gộp của pass chính. Ngưỡng tính trên ứng viên sau tỉa bằng main;
  k làm tròn tổng xác suất; k=0 không cạnh. Tỉa động trước từng cặp, chỉ nhận `can_de_hieu` / `trong_dinh_nghia`, thử quote gần neo trước.
  Nhật ký có điểm hai chiều (null nếu không có chiều ứng viên/đã bị tỉa từ main), ngưỡng, chiều chọn và quote; không có fallback LLM/cạnh mềm.
- Mode `DOC2ROADMAP_SECONDARY_MODE={llm,ml}`, mặc định **llm**. ML có algorithm/config/model/calibration/tokenizer/rule fingerprint riêng.
  **Mã BuildSecondaryEdges LLM không đổi**, nên cache và checkpoint LLM cũ không bị vô hiệu hóa. Các khâu trả tiền khác vẫn qua SpendGuard.
- Wheel force-include tệp E5. Không đổi `.env` thật; không gộp thay đổi Pha B đang dở ở composition/CLI hay các tệp khác.

Hướng dẫn lệnh: [doc/a8-pass-phu-ml-cli.md](../doc/a8-pass-phu-ml-cli.md).

## Đối chiếu 18b — tự kiểm, chờ Claude ký nghiệm thu

Xuất bằng mã sản phẩm, cùng phiên bản pass chính tạo bảng nghiên cứu:

```powershell
.\.tools\uv.exe run doc2roadmap a8-secondary-features --doc-id doc-1 --main-version 1 --artifacts artifacts/v3-r12-final-evaluation --chunks-artifacts artifacts --output-dir tmp/v4-18b-features
.\.tools\uv.exe run doc2roadmap a8-secondary-features --doc-id nhap-mon-ml --main-version 1 --artifacts artifacts/v3-r12-final-evaluation --chunks-artifacts artifacts --output-dir tmp/v4-18b-features
.\.tools\uv.exe run doc2roadmap a8-secondary-features --doc-id xstk-ch3-1 --main-version 41 --output-dir tmp/v4-18b-features
.\.tools\uv.exe run doc2roadmap a8-secondary-features --doc-id doc-4 --main-version 7 --output-dir tmp/v4-18b-features
.\.tools\uv.exe run python scripts/pass-phu-ml/kiem_khop_san_pham.py
```

Lệnh thực tế dùng `.venv/Scripts/python.exe -m doc2roadmap.presentation.cli.main` với `PYTHONPATH=src`, cùng tham số. So với CSV nghiên cứu đã có,
không chạy lại học mô hình. Script so không import mã tính đặc trưng nghiên cứu; đọc CSV, lấy cờ ứng viên theo luật nghiên cứu và dựng
các cột one-hot vai trò. Chỉ in số đếm, không chép tên khái niệm hoặc câu giáo trình vào báo cáo.

| Tài liệu | Main version | Dòng hai chiều | Ứng viên | Cùng tập ứng viên | Sai lệch max trên 82 feature của dòng ứng viên |
|---|---:|---:|---:|---|---:|
| doc-1 | 1 | 6.942 | 1.018 | có | 0 |
| nhap-mon-ml | 1 | 1.994 | 209 | có | 0 |
| xstk-ch3-1 | 41 | 1.884 | 298 | có | 0 |
| doc-4 | 7 | 45.944 | 4.652 | có | 0 |

Tất cả exit 0, đạt ngưỡng 1e-9; không dùng `--khop-sach`. CSV nằm trong tmp, không commit.

## Kiểm thử

- Miền: bộ tách từ giả, tên một âm tiết trong từ ghép, âm tiết y, exact + từ, hợp đồng/learnable, thứ tự/mục/chương, ô thiếu và one-hot vai trò.
- Stage execute trên Store trong bộ nhớ: cạnh thật/không cạnh, dưới ngưỡng thực (không chỉ k=0), no_evidence qua bộ kiểm thật, cạnh mới tỉa cặp sau
  bằng cạnh trực tiếp và đường cứng, chiều điểm cao hơn, câu gần neo và fallback quote, main chưa xong, cache, tất định, đổi fingerprint mất cache.
- Bản cài: mô hình LightGBM nhỏ dựng trong test, ô rỗng phân biệt được với 0, kiểm hash và hai loại lệch feature, calibration nội suy/kẹp, tệp thiếu.
- CLI/composition: CSV đủ 82 cột/ô trống, từ chối pass phụ làm đầu vào, mode mặc định/giá trị sai, nối stage ML và execute không allow-spend bằng
  scorer/tokenizer giả, nhánh LLM cũ vẫn chọn được.
- Kiến trúc: miền không import underthesea hoặc hạ tầng, ứng dụng không import hạ tầng.

**Đột biến:** `scripts/pass-phu-ml/kiem_dot_bien_18bc.py`, chạy test dữ liệu giả với source thay trong bộ nhớ process con, không sửa file. Kết quả
**20/20 detected**: ranh giới từ, chuẩn hóa y, hợp đồng ứng viên, main hoàn chỉnh, cache, k=0, so ngưỡng, tỉa main, tỉa động, chiều cao hơn, cạnh cứng,
loại căn cứ, bộ kiểm quote, gần neo, thử quote tiếp, tất định, băm model, thứ tự feature, ô thiếu và nội suy calibration.

Lượt đầu bắt 19/20: test ô thiếu cũ cho −1 và 0 cùng lá. Đã sửa dữ liệu mô hình nhỏ để hai giá trị khác nhánh và thêm assert kết quả dự đoán phải
khác; chạy lại bắt đủ 20/20. Không thay quy tắc sản phẩm để chiều theo test. Lỗi header LightGBM trước đó làm abort process test; thêm kiểm header
trước loader, test lệch thứ tự nay trả ValueError rõ.

**Toàn bộ tests:** lượt sandbox 1.370 passed/3 failed do localhost WinError 10013 ở test Pha B, không phải lỗi logic. Chạy lại ngoài sandbox:

```powershell
$env:PYTHONPATH='C:\Users\ngoco\Desktop\Doctoroadmap\src'
$env:PYTHONIOENCODING='utf-8'
& .venv/Scripts/python.exe -m pytest tests -q -o addopts= -p no:cacheprovider --basetemp tmp/pytest-v4-18bc-full-approved-20261016
```

**1.377 passed**, 7 cảnh báo thư viện, **188,97 giây**, exit 0. Đây là test của toàn worktree (có các thay đổi Pha B của chủ dự án), không tự
commit phần ngoài phạm vi.

**Kiểm độc lập phần sắp commit:** stage riêng 24 tệp, chỉ chọn bốn hunk ML trong composition/CLI, không lấy hunk Pha B. Dùng `git checkout-index
--all --prefix=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/v4-18bc-index/` xuất snapshot vào thư mục mới (không ghi đè cây làm việc). Cwd snapshot,
`PYTHONPATH` trỏ src snapshot, interpreter venv đã cài; chạy toàn bộ tests với `--basetemp tmp/pytest-18bc-index-20261016` ở cây gốc:
**1.195 passed**, 7 cảnh báo thư viện, **155,03 giây**, exit 0. Vì vậy phần commit không cần các thay đổi Pha B chưa commit. Không thêm .env thật,
sách, bảng giáo trình hay artifact vào snapshot/commit. Sau bước này chỉ bổ sung số đo vào Markdown, không đổi mã runtime/test.

## Đóng gói/offline

`uv build --wheel --out-dir tmp/v4-18bc-wheel`, cài wheel `--no-deps --target tmp/v4-18bc-installed`; chạy Python `-I`, đặt installed-target đầu
sys.path, thay socket.connect bằng hàm báo lỗi. Kết quả: package được import từ **v4-18bc-installed**, nạp `e5-d01-a-v1`, đủ **82 features**,
chấm được một dòng và tách được câu tiếng Việt; không kết nối mạng. Build/cài lần sandbox bị chặn tạo launcher, chạy lại bằng quyền đã duyệt thì đạt.

Kiểm lại trên **wheel từ snapshot index sạch**: build ở cwd `tmp/v4-18bc-index`, output `tmp/v4-18bc-wheel-clean`, cài `--no-deps --target
tmp/v4-18bc-installed-clean`. Chạy Python `-I` với socket.connect bị chặn; import đúng **v4-18bc-installed-clean**, nạp/chấm E5 đủ 82 feature và
tách từ tiếng Việt đạt, exit 0. Bản đóng gói này không chứa mã Pha B đang dở. Không thay đổi venv hoặc dữ liệu sản phẩm bằng wheel thử.

## Bàn giao 18d / giới hạn

Kiểm vận hành offline trên doc-4, không chạy pass chính hoặc A9/A10:

```powershell
& .venv/Scripts/python.exe scripts/pass-phu-ml/thu_stage_san_pham.py doc-4 --output tmp/v4-18c-smoke
```

Exit 0; graph thử **v1**, không tái dùng ở lần đầu; thời gian stage **182,3026278 giây (3,04 phút)**, trong lúc máy còn chạy bộ test khác.
Lần execute kế tiếp cùng đầu vào dùng cache, không thêm phiên bản. Số đo:

| Chỉ số | Giá trị |
|---|---:|
| Tổng cặp / hoàn tất | 22.972 / 22.972 |
| Chiều ứng viên sau tỉa bằng main | 4.001 |
| k hiệu chỉnh làm tròn | 1.326 |
| Ngưỡng | 0,5007263942966618 |
| Cặp bị tỉa (main + cạnh mới) | 4.548 |
| Dưới ngưỡng | 17.636 |
| Không có câu qua hợp đồng | 73 |
| Cạnh pass phụ tạo | 715 |
| Lời gọi API / USD pass phụ | 0 / 0 |

Các số evidence_hard/evidence_soft trong stats bao gồm **cạnh main đã có**, không được đọc là ML tạo cạnh mềm. ML chỉ tạo can_de_hieu /
trong_dinh_nghia. Không so 715 cạnh với kết quả E4 cũ để kết luận chất lượng; tập tính ngưỡng mới khác tập câu LLM đã hỏi, đúng khác biệt đã
ghi trong spec. Kho thử không phải toàn chuỗi tự chứa: upstream/chunks tham chiếu mốc cũ, script cấp artifact main rõ khi chạy lại.

- Chưa chấm E4/Q7/Q7b/bao đóng, chưa chạy chuỗi đầy đủ trên D-01 và không chỉnh tham số theo vàng. Những việc đó thuộc Claude/vé 18d.
- Chưa đổi mặc định, chưa sửa ADR/CONTEXT theo 18e. Chi pass phụ ML là 0, không đồng nghĩa cả roadmap là 0 USD.
- Skill ponytail dẫn tới tái dùng selector, definition_window, validator/merge, StagePlan và store/cơ chế đo hiện có; không thêm phụ thuộc torch,
  pickle, dịch vụ, trainer hoặc runner production khác.
