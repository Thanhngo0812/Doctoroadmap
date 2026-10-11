# D-02 — công cụ vé 15, không thay mặc định sản phẩm

Chạy từ `C:\Users\ngoco\Desktop\Doctoroadmap`. Chi API của các lệnh dưới đây: 0 USD. Không dùng nhãn đánh giá để huấn luyện lại mô hình trong lượt baseline.

## Phiếu và nhãn

`artifacts/a1-d02/development/` có sáu cuốn phát triển. Xem chỉ đường trong `report/ban-giao-agentic-d02-pha-1b-2026-10-08.md`. Không mở `document-data/test/` hay tập khoá; lệnh xuất và định tuyến tập khoá do người giữ tập khoá chạy.

```powershell
.venv/Scripts/python.exe scripts/a1-d02/xuat_phieu.py --out artifacts/a1-d02/development
.venv/Scripts/python.exe scripts/a1-d02/kiem_nhan_d02.py --sach d01-02 --thu-muc artifacts/a1-d02/development
.venv/Scripts/python.exe scripts/a1-d02/kiem_nhan_d02.py --sach d01-02 --thu-muc artifacts/a1-d02/development --ban-duyet
```

Validator chỉ dùng thư viện chuẩn, chạy được với `python -S`. Không sửa đầu vào để qua kiểm. Cờ `--chi-cay` dành cho mốc L1 chưa có L2; nghiệm thu đầy đủ không dùng cờ đó.

Luật cha được chủ dự án duyệt 2026-10-08: chọn cha đang mở trong cùng nhánh logic; nhánh `mo_dau`/`hanh_chinh` không đóng nhánh nội dung. Chương sau mục lục vẫn có thể thuộc Phần trước mục lục. Một gốc nội dung mới vẫn đóng nhánh nội dung cũ; không cho phép quay về cha nội dung đã đóng.

`duyet/<sach>.jsonl` giữ **bản ghi đầy đủ** của tiêu đề/trang được sửa: có `id` thì thay tiêu đề cùng ID; không có `id` thì thay trang L2 cùng `trang`. Bản gốc agentic không ghi đè. Validator với `--ban-duyet` kiểm hợp đồng sau khi ghép bản sửa. Hiện cơ chế này chỉ hỗ trợ sửa bản ghi đã có, không thêm/xoá tiêu đề; nếu người duyệt cần thêm/xoá phải bổ sung giao thức và test trước.

Năm bản sửa cha d01-02 là sửa hợp đồng theo phép chủ dự án, **không** thay thế một lượt người duyệt nội dung cả sách. Không báo toàn bộ nhãn đã thành vàng.

## Baseline và điểm lưu

```powershell
.venv/Scripts/python.exe scripts/a1-d02/chay_pha_2.py --out tmp/a1-v415/phase2b-20261008 --runs 3
```

Sáu cuốn × ba hệ × ba lần = 54 tiến trình mới. Chạy tuần tự để không tự tạo cạnh tranh CPU giữa các hệ. S1/S2 dùng `tmp/venv-ml`, S0 dùng `.venv`; không cài thêm phụ thuộc. `HF_HUB_OFFLINE=1` tránh tải mô hình hoặc đưa nội dung ra ngoài; thiếu model local thì dừng báo lỗi.

- `inputs.json`: hash mã công cụ và các tệp dòng/nhãn/bản sửa. Không đổi mã hoặc nhãn giữa chừng.
- `<sach>/<S0|S1|S2>/run-<n>/prediction.json`: kết quả lần đo hoàn chỉnh.
- `tree.json`, `chunks.json`: đầu ra thật của lần chạy, không replay cache parse.
- `<sach>-<hệ>-<n>.log`: log, kể cả lỗi.
- `results.json`: số từng cuốn, M1–M4/M6 trên agentic và sau ghép sửa, timing/RAM từng lần, trung vị/cuốn tệ nhất.
- `progress.md`: bảng đọc nhanh, cập nhật sau mỗi lần chạy hoàn chỉnh.
- `running.lock`: PID tiến trình điều phối; ngăn chạy trùng trong cùng kho kết quả.

Chạy lại đúng lệnh sẽ tái dùng lần đo hoàn chỉnh; lần chưa hoàn chỉnh phải kiểm tra và bảo toàn riêng trước khi chạy lại. Sau crash, không tự xoá lock: kiểm PID/command line và tiến trình con đã dừng rồi mới xử lý. Nếu nguồn/mã thay đổi, dùng kho kết quả mới, không trộn hai lượt.

Không sửa cấu hình S1 cũ: bộ chạy kiểm hash `report/v4-15-s1-dong-bang-2026-10-08.json`; mô hình của từng cuốn phát triển là fold không chứa chính cuốn đó. Cây dựng mới d01-11 đã so đúng với R25 đóng băng.

M3 lấy thân bài trên các trang L2. M6 xét dòng trong chunk trên toàn phạm vi L1, không chỉ trang L2; trên trang có L2 loại các vai trò không phải thân bài/danh sách. Ngoài trang L2, phân vai độc lập chưa có nên dùng các dòng chuẩn trong chunk và công bố giới hạn này. Chunk không căn được vẫn nằm trong mẫu số. Không coi độ phủ căn thấp là điểm chất lượng cao.

Thời gian từ đọc PDF tới chunk gồm nạp mô hình/tokenizer; trừ thời gian căn dòng đánh giá. RAM đỉnh lấy ngay sau chunk, trước khi căn dòng; vẫn có dữ liệu dòng chuẩn đã nạp nên phải công bố phần overhead này. Trước mỗi tiến trình, đo tải CPU toàn máy một giây (`machine_cpu_before`); `idle_before` ghi nhận khi dưới 20%. Đây là quan sát trước chạy, không bảo đảm không có ứng dụng khác khởi động trong lúc đo. Ba lần chạy không tự chứng minh máy rảnh; kiểm nhật ký tải trước kết luận nhanh hơn 10× ở pha 4.

Lượt `phase2-20261008` cũ lưu 12 lần S1/S2 rồi dừng do công cụ gọi sai hợp đồng khởi tạo S0. Kết quả cũ bảo toàn để tra cứu; lượt `phase2b-20261008` sửa đúng `PipelineConfig`, bổ sung CPU và lấy RAM trước căn dòng, chạy lại từ đầu. Không trộn timing của hai lượt.

## Định tuyến

```powershell
.venv/Scripts/python.exe scripts/a1-d02/dinh_tuyen.py --manifest report/v4-15-router-development-2026-10-08.json --out tmp/a1-v415/router-development.json
```

Đã kiểm 19/19 PDF cũ và PDF tổng hợp (chữ hiện/chữ ẩn, GlyphLessFont, ảnh kín trang, trang không chữ). Manifest `report/v4-15-router-custodian-39-2026-10-08.json` giữ tên lịch sử nhưng đã đủ **43 cuốn: 27 gốc, 16 quét**; thêm bốn PDF gốc bằng tên tệp ngày 2026-10-09. Nhân viên không chạy manifest đó hoặc xem kết quả từng cuốn khoá.

Hợp đồng mới của vé 15: chỉ PDF gốc thuộc phạm vi; S2 cuối phải từ chối bản quét, không chuyển sang S0. `dinh_tuyen.py` đang khoá trong baseline `phase2b-20261008` vẫn dùng hành vi cũ (không gốc → S0); không sửa giữa 54 phép đo. Kết quả S2 trên sáu PDF gốc là mốc so sánh, **không nghiệm thu hành vi từ chối mới**. Phải có phiên bản, test và hash S2 cuối riêng trước pha 4; cổng ingest cho mọi đường thuộc pha 5.

## Giới hạn nghiệm thu

Pha 0–1 đã làm; baseline pha 2 đủ 54/54 (số đo bù M5 lưu riêng). Pha 3 có bốn vòng theo nhãn độc lập và hồi quy 19 sách; đã đóng băng R2 sau hai vòng không tăng M3. Còn người giữ tập khoá kiểm đủ 43 PDF, không tuyên bố 43/43 hoặc đã nghiệm thu toàn pha 3. Không đổi cờ A1/cache/mặc định ở đây. Pha 4 thuộc người giữ tập khoá; cờ chọn đường/mặc định pha 5 cần quyết định chủ dự án, còn cổng từ chối bản quét pha 5 là bắt buộc bất kể kết quả pha 4.

## Ứng viên cuối pha phát triển, 2026-10-09

`pha3.py` là runner 19 sách phát triển, không dùng nó để chạy sách khoá. R2 chuẩn hoá đậm và ngữ pháp Điều/khoản/điểm; R3 học LOBO bị loại, R4 cấp nút không đổi đầu ra chunk. Hash và bảng đầy đủ: `report/v4-15-pha-3-dong-bang-2026-10-09.json`, `report/v4-15-pha-3-chot-va-ban-giao-2026-10-09.md`.

Giao diện suy luận không đọc nhãn cho người giữ tập khoá:

```powershell
tmp/venv-ml/Scripts/python.exe scripts/a1-d02/xuat_s1_pha3.py --pdf PDF_GOC --sach MA_SACH --out THU_MUC_MOI
.venv/Scripts/python.exe scripts/a1-d02/router_native.py --manifest report/v4-15-router-custodian-39-2026-10-08.json --out tmp/a1-v415/custodian-only/router-43.json
```

Placeholder cần thay theo manifest D-02. Cổng từ chối ở giao diện nghiên cứu xảy ra trước parser/đầu ra; chưa thay cổng ingest sản phẩm. Nhân viên không chạy manifest custodian. M4 bỏ đầu/chân/số trang cần kiểm ID `evaluation_excluded` tường minh với `scripts/doc-nhe/cham_loai_bien_d02.py`; không coi ID thiếu căn là bị loại đúng.
