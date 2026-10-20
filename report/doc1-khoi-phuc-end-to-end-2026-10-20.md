# Khôi phục dữ liệu phát triển và dựng lại doc-1 — 2026-10-20

Trạng thái: **đạt phạm vi khôi phục/dựng lại đã duyệt**. Dữ liệu đã kiểm, replay không gọi API, cổng cuối xanh. Fixture đã ghép main bằng `34d2257` và đẩy GitHub. Các giới hạn về lịch sử v45/v57, cache cũ và quiz offline được giữ rõ bên dưới.

## Phê duyệt và phạm vi

Chủ dự án đã duyệt trực tiếp: **“duyệt tất cả làm end to end khôi phục đi”**.
Tin nhắn này duyệt chạy lại doc-1 qua Vertex với ngân sách đề nghị 3 USD và xử lý fixture kiểm thử đã đề xuất. Không tìm thêm nguồn khôi phục cũ.

Trước khi chạy đã sao chép độc lập 816 tệp, 94.020.797 byte, đối chiếu SHA-256 từng tệp tại `document-data/development-recovery-2026-10-20/manifest-before-build.json`. Không dùng junction. Bản sao trước dựng được giữ nguyên.

Kết quả khôi phục lịch sử: doc-6 **122/122**, doc-1 **665/805**, tổng **787/927** tệp khớp SHA-256. 140 tệp lịch sử còn thiếu; dữ liệu dựng mới không được tính thay vào số khớp lịch sử này.

## Cách chạy

Chạy từ thư mục chung, nhánh main, mã sản phẩm tại `2bee226`. Harness `tmp/coord-doc1-rebuild-20261020/execute.py` gọi `build_document_runner(Settings(llm_transport="vertex"), allow_spend=True).execute(Path("doc-1.pdf"), "doc-1", language="vi")`.

Chuỗi: Nhe ingest → kiểm sớm → label-roles → A3 và A3′ → A4/A5, coverage=none, không vàng → roadmap → A12, concept-index và formulas PDF. Kho Pha B riêng: `artifacts/phase_b/doc-1-rebuild-20261020.json`; cấm mở kho live chung và tập giữ lại.

Bộ chặn chi phí giữ chỗ ngân sách trước mỗi lời gọi, tính lại theo token thực trả về, đồng bộ giữa các luồng và dừng lời gọi tiếp theo nếu thiếu usage. Kiểm thử RED: 3 lỗi được bắt; GREEN: 12 kiểm đạt, gồm 4 kiểm chặn ngân sách và 8 kiểm settings. Soát độc lập không phát hiện lỗi bắt buộc sửa; adapter Vertex embedding gửi một instance mỗi yêu cầu, phù hợp bộ đếm chi phí.

Lệnh thực thi:

```powershell
.venv/Scripts/python.exe -X utf8 tmp/coord-doc1-rebuild-20261020/execute.py
```

Nhật ký từng bước và từng lời gọi chỉ chứa metadata/usage tại `tmp/coord-doc1-rebuild-20261020/paid-progress.jsonl` và `paid-requests.jsonl`. Kết quả cuối ở `paid-result.json`; sẽ xuất bằng chứng nghiệm thu vào report khi chạy xong.

## Kết quả, chi phí và cổng kiểm

Kết quả cuối: **succeeded**, graph **v8**, đủ bốn bước của W-13. Tổng chi hai lượt **1,542275 USD**, gồm **1,35301175 USD** ở lượt bị 429 và **0,18926325 USD** ở lượt tiếp tục. Đã đối chiếu kết quả đã ghi trong SQLite bằng kết nối độc lập; không ghi dự toán thay tiền thật.

Tổng **3.423 HTTP attempt**: 1.479 sinh nội dung và 1.944 embedding. Có **3.348 phản hồi thành công**, đủ usage; **75 HTTP 429**. Giữ nguyên `usage_complete=false` của bộ đếm pipeline vì các yêu cầu lỗi không trả usage; không sửa cờ này thành true. Sổ HTTP độc lập đối chiếu đủ mọi phản hồi thành công và tổng tiền với kết quả từng lượt, không có phản hồi thành công thiếu usage. Đây là tiền tính từ token thực trả về theo đơn giá cấu hình, không phải dự toán trước chạy.

| Bước | HTTP attempt | Thành công | HTTP 429 | USD thực |
|---|---:|---:|---:|---:|
| Nhe ingest và kiểm sớm | 0 | 0 | 0 | 0 |
| label-roles | 18 | 17 | 1 | 0,01320350 |
| A3 và A3′ | 1.400 | 1.380 | 20 | 0,58022115 |
| A4/A5 | 1.010 | 977 | 33 | 0,47959865 |
| roadmap, gộp hai lượt | 772 | 751 | 21 | 0,46636645 |
| A12, concept-index, formulas | 223 | 223 | 0 | 0,00288525 |
| **Tổng** | **3.423** | **3.348** | **75** | **1,54227500** |

Hai lượt trả phí chạy 18 phút 28 giây và 6 phút 14 giây; từ bắt đầu lượt đầu đến kết thúc lượt tiếp tục khoảng **27 phút 28 giây**, gồm thời gian kiểm lỗi và khởi động lại. So với dự trù 1,18–2,67 USD, chi thực nằm trong khoảng và dưới trần 3 USD. Mốc doc-6 từ kho rỗng ở W-13 là 0,1203762 USD; đây là hai cuốn khác nhau nên không dùng tỷ lệ chi để kết luận hiệu năng.

Lượt 1 (06:52:10–07:10:39 UTC) dừng ở A8 sau 9 lần thử HTTP 429: **3.099 HTTP attempt, 1,35301175 USD** đã ghi trong DB. Ingest, roles, A3/A3′, A4 đã xong; graph đã lưu clusters v1 và mentions v2 cùng checkpoint main. Không đánh dấu lượt này thành công.

Lượt tiếp tục dùng `execute.py --resume`, giảm tối đa 4 lời gọi đồng thời, 60 yêu cầu/phút và 3 lần thử lại. Không đổi model, prompt, chuỗi xử lý hoặc điều kiện chất lượng. Bộ chặn cộng sẵn toàn bộ 1,35301175 USD đã chi vào cùng trần 3 USD; không đặt lại ngân sách. Roles, A3/A3′ và A4 xác minh `reused=true`, **0 lời gọi, 0 USD** trong phần chạy lại này. Nhật ký lỗi nhà cung cấp riêng giúp phân biệt giới hạn tốc độ và hạn mức nếu còn 429.

Cổng mã tại `a69ebe2`, worktree `tmp/doc1-recovery-fixtures`, dữ liệu được chép/đối chiếu từ snapshot trước dựng: **1.999 Python/PostgreSQL đạt, 0 fail, 1 Cloudinary live không bật**; **41 React đạt**, build thành công. Soát độc lập approve đúng commit `a69ebe2dce89dcb5ed2d64f82154f0f4069ed9f8`. Cổng dùng bản sao sau dựng được ghi riêng dưới đây.

## Kiểm sau dựng và bản sao cố định

- Graph v8 tải qua loader thật, đủ module và khái niệm; node trong module đều có thật. Label-roles giữ nguyên ID, văn bản, vị trí và mọi trường chunk ngoài role. Candidates không thiếu phủ và không có section lỗi; canonical khai báo coverage=none, không có gold_sheet_id.
- A12 có **302 assignment** cho 302 chunk; truy hồi khớp ID, nội dung và đường mục. Concept-index có đủ **223 node**, vector 768 chiều, không rỗng, đúng input hash.
- Đối chiếu độc lập ảnh với parse v6: **2.602 occurrence, 0 skip, 2.234 PNG duy nhất**. Mọi PNG được đọc, đối chiếu SHA-256 với media_id và giải mã pixel. Đây là kiểm tính toàn vẹn, chưa phải đánh giá thị giác từng crop. Ba phép thử phá bằng ảnh hỏng, mất ảnh, index lệch parse đều bị bắt sau sửa bộ kiểm; XML RED/GREEN được lưu trong bằng chứng.
- Replay toàn chuỗi với API và cấp header Vertex bị chặn: **succeeded**, cùng graph v8, **0 lần đụng transport, 0 model call, 0 USD**, 16,30 giây; DB lưu tiền thực 0. Roles, A3/A3′, A4, graph và concept-index đều dùng lại cache.
- Doc-6 kiểm lại **122/122 SHA-256**, gồm 121 tệp dưới thư mục doc-6 và PDF gốc. Bộ đếm đầu tiên chọn thiếu PDF nên báo assertion 121 so với 122; đã sửa phạm vi đếm, không sửa dữ liệu để vượt kiểm.

Bản sao sau dựng: **`document-data/development-rebuilt-2026-10-20`**, **3.081 tệp**, **195.556.758 byte**. Manifest: `report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json`. Đã chép từng tệp và đối chiếu SHA-256 ở nguồn/đích; không có liên kết.

Bản ZIP cố định: **`document-data/development-rebuilt-2026-10-20.zip`**, **54.795.577 byte**, SHA-256 **`3fd14ef0029ced7d679fe2303525d651a2427a862f355ad5d19598b775fc52f4`**. Đã kiểm CRC và SHA-256 từng entry so với manifest. Giữ cả bản trước dựng, bản sau dựng và ZIP; không dọn worktree cũ.

Đã chép/đối chiếu đủ **3.081 tệp** sang worktree mới `tmp/doc1-recovery-gate` tại đúng commit `a69ebe2`. Loader tại đây xác minh đang nhập mã trong `tmp/doc1-recovery-gate/src`, đọc được doc-1 v8 và doc-6 v29. Cổng toàn repo cuối: **1.999 đạt, 0 fail, 0 error, 1 skip Cloudinary live**, **runner returncode=0**; React **41/41 đạt**, build thành công.

Lần cổng sau dựng đầu đã có XML 1.999 đạt/1 skip, nhưng PowerShell chuyển cảnh báo stderr cuối tiến trình qua Tee thành mã thoát vỏ 1. Đã chạy lại runner bằng Python `subprocess.run`, lưu stdout/stderr vào tệp và ghi nguyên `returncode`: **0**, cùng 1.999 đạt/1 skip, 304,44 giây. Không hạ điều kiện kiểm hay bỏ ca để lấy xanh; giữ bằng chứng cả hai lượt.

## Lệnh và bằng chứng

Các lệnh chạy từ thư mục chung, trừ nhóm cổng kiểm chạy từ worktree ghi ở trên:

```powershell
.venv/Scripts/python.exe -X utf8 tmp/coord-doc1-rebuild-20261020/execute.py
.venv/Scripts/python.exe -X utf8 tmp/coord-doc1-rebuild-20261020/execute.py --resume
.venv/Scripts/python.exe -X utf8 tmp/coord-doc1-rebuild-20261020/verify.py
.venv/Scripts/python.exe -X utf8 tmp/coord-doc1-rebuild-20261020/replay.py
.venv/Scripts/python.exe -X utf8 tmp/coord-doc1-rebuild-20261020/snapshot.py
git worktree add --detach tmp/doc1-recovery-gate a69ebe2
```

Chép dữ liệu bằng `shutil.copyfile` theo từng đường dẫn của manifest; kiểm đường dẫn nằm trong nguồn/đích, không có symlink/junction ở tệp hay thư mục cha, rồi kiểm SHA-256 trước và sau chép. Kết quả ghi `copy-result.json`.

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-doc1-rebuild-20261020/verify_copy.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-rebuilt-final --junitxml=tmp/cong-rebuilt-final.xml
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-rebuilt-exitcode --junitxml=tmp/cong-rebuilt-exitcode.xml
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-doc1-rebuild-20261020/check_phase_b_cache.py
npm.cmd --prefix src/web/frontend ci --no-audit --no-fund
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
```

Kiểm guard qua cùng runner, chọn `tmp/coord-doc1-rebuild-20261020/test_budget_guard.py` hoặc `test_formula_guard.py` cùng `src/web/backend/tests/test_settings.py`; tham số `-o addopts= -q`, basetemp riêng cho RED/GREEN và XML tương ứng. Mỗi bộ GREEN có **12 kiểm đạt**. Hai kiểm quiz được tái hiện mất v45 trước sửa, sau sửa giữ nguyên mọi assertion và **30 kiểm đạt** cùng settings.

Bằng chứng bền vững tại **`report/doc1-rebuild-evidence-2026-10-20/`**: phê duyệt, kết quả từng lượt, HTTP ledger, nhật ký bước, DB sau chạy, XML RED/GREEN, kết quả replay, kiểm độc lập, manifest và hash ZIP. Mã harness dưới dạng `.py.txt` chỉ để đối chiếu lệnh đã chạy; không phải sửa mã sản phẩm.

## So sánh và quyết định fixture

Mốc v57 cũ có metadata đã lưu: 33 module, 205 khái niệm học được. Không còn manifest/live riêng được xác minh để đối chiếu số cạnh, node ID và tên module; không mở cache chung để bù số liệu.

Graph dựng mới hiện là **v8**, có **35 module, 223 khái niệm học được**. So với metadata v57: **+2 module, +18 khái niệm**. Có 475 `requires_edges`, 210 `main_edges`, 273 `secondary_edges`, 330 `topic_edges`, 256 `open_edges`; các tập này có thể chồng lặp, không cộng thành một số cạnh tổng. Số cạnh v57: không có dữ liệu đã xác minh để so.

Nguồn tên/mô tả mới: **33 tên LLM, 2 tên fallback; 3 mô tả LLM, 32 mô tả template**. Đây là số liệu bàn giao để tiếp tục đánh giá chất lượng; đợt khôi phục không thay quy tắc đặt tên/mô tả.

Cache Pha B cũ: **0 kho doc-1 riêng đã xác minh, 0 thẻ module cũ được đối chiếu, 0 tên module cũ được đối chiếu**; số khớp/không khớp: **không xác định**, không ghi 0 như thể đã so hết. Không dùng lại cache cũ. Kết quả kiểm kho mới theo node/chunk của graph v8 nằm dưới đây; không in nội dung cache trong báo cáo.

Sau yêu cầu nhắc lại của chủ dự án, đã kiểm thêm **kho mới** trên một bản chép: **35/35 thẻ module** khớp node và tên hiện tại, **35/35 ngữ cảnh tên** có cache, **0 lời gọi cần thiết**. Đổi thử một node ID gây **1 cache miss**, chứng minh ngữ cảnh lệch node không dùng lại tên cũ. CLI thật đã nhận đúng `--graph-version 8` và `--store` chỉ tới kho riêng; lệnh `phase-b names --dry-run` quay đúng đầu vào A10 v7 và cần 0 lời gọi. A12 vẫn đủ 302 assignment. Không mở `live.json`/`offline.json` chung, không gọi API và không sửa mã sản phẩm để đạt kiểm này.

Một kiểm thêm về quiz trên graph thật, ở chế độ cloze offline, yêu cầu 5 câu cho module lớn nhất: thực tế chỉ tạo **1 câu**, 4 khái niệm chưa có câu fallback hợp lệ. Probe ban đầu yêu cầu đủ 5 đã fail; đã giữ số liệu này như một giới hạn, không sửa kỳ vọng của hai kiểm hồi quy fixture. Các câu được tạo vẫn dùng đúng node của v8 và ẩn đáp án. Việc mọi module của cuốn thật luôn có đủ 5 câu chưa được nghiệm thu; không gọi LLM trả phí thêm trong phép kiểm cache này.

Cách chạy Pha B sau dựng được ghi tại `doc/du-lieu-phat-trien-va-fixture.md`. Kho cũ được giữ riêng; không xoá hay trộn dữ liệu của cuốn khác để xử lý doc-1.

## Ghép main và bàn giao

Nhánh `work/doc1-recovery-fixtures`, mốc đã soát **`a69ebe2dce89dcb5ed2d64f82154f0f4069ed9f8`**, được ghép `--no-ff` thành **`34d2257`**, đã đẩy origin/main. Đã xác nhận mã `src/` và `tests/` của commit ghép giống đúng đỉnh đã chạy cổng. Mã sản phẩm không thay đổi; chỉ thay phụ thuộc dữ liệu của hai test quiz và thêm fixture tổng hợp.

```text
git fetch origin main
git merge --no-ff a69ebe2 -m "merge(recovery): checked-in quiz fixture replaces lost v45 data; reviewed and full gates passed 2026-10-20"
git diff --exit-code a69ebe2 HEAD -- src tests
git push origin main
```

Các nhóm nhận main mới trước khi tiếp tục. Khi kiểm doc-1, dùng graph v8 và kho Pha B riêng theo runbook; không ghim v45/v57. Không dọn snapshot, ZIP hoặc worktree trong đợt này. Tổng tiền mới của đợt: **1,542275 USD**, đã ghi thêm tại mục 10 bàn giao.

Chủ dự án đã duyệt thay phụ thuộc quiz vào graph v45 ngoài repo bằng fixture nhỏ trong repo. Kiểm tích hợp dùng bản sao dữ liệu phát triển cố định kèm danh sách SHA-256; vào worktree bằng sao chép tệp, không tạo liên kết tới kho chung.
