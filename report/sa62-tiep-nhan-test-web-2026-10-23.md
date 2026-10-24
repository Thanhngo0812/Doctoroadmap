# SA-62 — bàn giao test web tương thích port PostgreSQL — 2026-10-23

Codex thực hiện đề nghị Claude do chủ dự án chuyển: commit test vào chính `work/sa62-port-kho-pha-b`, chạy cổng, ghi mục 10.
Lời bàn giao cho phép người điều phối tự ghép và ghi lại mục 10; chỉ dùng quyền này khi đúng mốc review/main/cổng xanh.
Không tự đổi mã composition đã nghiệm thu hoặc mở chi.

## Mốc và phạm vi

- Lõi đã nghiệm thu `266dbdcfa369a0cc02637bff92e37208d7f7daad`.
- Nhận main `ecd98c25b2038a853252b7fe123317699b0a9014` vào chính nhánh SA-62 tại `97266c1c1f62aee40b6931a2146d163cee01f5f5`.
- Hai test âm và trace accounting đã có trên main qua `e85427a`; nhận chúng bằng merge, không viết lại hoặc nới assertion.
- Test dương mới commit **`ce5f581a685754f2c8bcc93664047dd159ad5eb7`**, chỉ thêm 40 dòng trong
  `src/web/backend/tests/test_real_build_w15.py`. Đây là mốc mã được chạy cổng cuối.

## Ba phép kiểm web

1. `test_real_default_requires_core_port_before_claim_or_provider`: tiêm `PipelineWithoutStorePort` có chữ ký cũ, constructor sẽ raise nếu bị gọi.
   Vẫn đòi CoreBuildPortUnavailable trước constructor/provider/claim; build giữ queued, không có attempt.
2. `test_real_worker_composition_uses_pg_version_and_never_claims_without_port`: giữ ca âm factory cũ, ca worker dùng PG/version cùng nguồn và queue rỗng.
3. **Mới:** `test_real_default_factory_injects_web_postgres_before_provider`:
   - `make_real_worker` không truyền pipeline_factory, chọn `DocumentPipeline` thật của SA-62; RealBuildRuntime/runner tạo được.
   - Adapter execute dựng pipeline thật với `allow_spend=False`; chỉ thay bước đọc bằng hook dừng có chủ đích.
   - Hook kiểm nhận PostgresPhaseBStore, ghi cache qua chính `_phase_b_store()` của pipeline. Một store/kết nối PG độc lập đọc đúng dữ liệu.
   - Hook ném BuildRejected trước provider và các bước dựng tiếp; kết quả rejected đúng mã, recorder đúng một lần, 0 model calls/USD, 0 attempt/ledger.
   - Guards JsonPhaseBStore/SqliteBuildLog/ADC/model/embedding/SMTP/Cloudinary vẫn bật; mọi tài nguyên PG được đóng trong finally.

Ca mới chứng minh đường factory mặc định → adapter → pipeline → store PG, không chỉ so danh tính thuộc tính.
Nó dừng ở bước đọc, **không** thay bằng chứng các bước roadmap/learning_prep của test SA-62 hoặc nghiệm thu toàn W-15.

## RED/GREEN và review

- Bỏ tiêm kho trong adapter (`phase_b_store=None`) trên bản kiểm: **native exit 1, đúng 1 assertion fail, 0 setup error**.
  Nguồn adapter phục hồi cùng SHA-256 trước GREEN/full gate; không commit phép phá.
- Ba test trọng tâm sau phục hồi: **3 pass, native exit 0**. Lượt này chạy trước commit test, trên cùng nội dung sau đó commit tại ce5f581;
  cổng toàn repo trên đúng ce5f581 là căn cứ cuối cùng, không nhận commit cha có test chưa commit là mốc bàn giao.
- Review độc lập test mới: approve, không Required; đã kiểm quan hệ nhân quả, guard, cleanup và giới hạn phạm vi; reviewer không chạy PG/provider thêm.

## Cổng trên đúng mốc và bàn giao ghép

Đã kiểm lại **3.144 tệp** theo manifest/SHA nguồn và đích, không links/learner live store/tập giữ lại.
`package.json`/lock không đổi so với cổng SA-62 trước; dùng node_modules đã npm ci tại worktree này.

Trên đúng `ce5f581`: **2.305 Python đạt, 0 fail/error, 1 Cloudinary live không bật; 143 React đạt, build thành công**, mọi native exit 0.
Pytest 663,04 s, wrapper 678,67 s; không lấy thời gian cổng thành phút/cuốn. Mọi pytest qua runner, PostgreSQL bắt buộc, không skip/thay assert để đạt.

**Ghép/đẩy `9ac2a85`:** Codex dùng quyền tự ghép trong lời bàn giao. Ngay trước lệnh ghép, main đã nhận SA-64 tại `1d91b0b`;
Codex thiếu chặn khi hash nền đổi nên đã ghép khi chưa chạy cổng trên tổ hợp mới. Ghi rõ thiếu sót này, không lấy 2.305 test làm kết quả của tổ hợp mới.
Đã nhận main vào chính worktree SA-62 tại **`14110c0e5a49aa2395b5f3be5555ca7c002315a0`**, mã trùng main sau ghép,
và chạy lại full Python/PostgreSQL, React/build với basetemp/JUnit riêng.
**Kiểm chứng sau ghép xanh:** **2.355 Python đạt, 0 fail/error, 1 Cloudinary live không bật; 143 React đạt, build thành công**, mọi native exit0.
Pytest 651,87 s/wrapper 667,41 s trên đúng `14110c0`; source/test/script/design của main sau ghép khớp mốc kiểm này.
Không sửa mã composition hoặc assertion để làm xanh; giữ nguyên lượt trước và metadata của cả hai lượt.

Lệnh cổng từ worktree `tmp/sa62-port-kho-pha-b`:

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/sa62-web-full-20261023 --junitxml=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-sa62-port-tests-20261023/full.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-sa62-port-tests-20261023/react.xml
npm.cmd --prefix src/web/frontend run build
```

Khi ghép phải kiểm main mới nhất; main đổi thì nhận lại và chạy cổng đúng quy trình. Quyết định/commit ghép được ghi sau khi có kết quả.
**SA-62 đã ghép và đẩy main tại `9ac2a85`**, không cần Claude ghép lại. Hồ sơ/evidence không đổi mã đã kiểm.
Đã kiểm nguồn/test/script/design không đổi sau cổng; chưa có paid build, dry-run thật hay nghiệm thu toàn W-15.

Bằng chứng lưu Git:

- [JUnit sau ghép](sa62-web-test-evidence-2026-10-23/full-postmerge.xml), [native exit/commit/lệnh](sa62-web-test-evidence-2026-10-23/full-postmerge-exit.json).
- [React](sa62-web-test-evidence-2026-10-23/react-postmerge.xml), [build](sa62-web-test-evidence-2026-10-23/build-postmerge-exit.json).
- [RED bỏ tiêm kho và SHA phục hồi](sa62-web-test-evidence-2026-10-23/injection-red-result.json), [ba test GREEN](sa62-web-test-evidence-2026-10-23/focused-green.xml).
- [SQL nguồn chi duy nhất](sa62-web-test-evidence-2026-10-23/sql-postmerge/single-build-charge.json), [tổng hợp](sa62-web-test-evidence-2026-10-23/summary.json), [SHA từng tệp](sa62-web-test-evidence-2026-10-23/manifest.json).

Raw giữ ở scratch; văn bản lưu UTF-8/LF/bỏ khoảng trắng cuối dòng, JSON so lại giá trị và JUnit so số ca/fail/error/skip.
`normalization.json` ghi cả hash raw/archive; số tiền trong SQL là fake, chi dịch vụ ngoài0USD.

## Hợp đồng giữ nguyên

- Tổng build duy nhất là delta DocumentPipeline.usage(); trace counted_in=build giữ raw trong extra nhưng không cộng vào tổng provider.
  Web đã đặt cột tiền/token typed của trace về 0; bảng chi đọc raw vẫn phải lọc cờ. Không sửa số lịch sử.
- DailySpendGuard Pha B không tính module_title/embedding của dựng; guard build web riêng. Không đổi budget.py.
- Giữ kế hoạch lecture-3/answer-3 theo ADR 0025/0026, Vertex và mọi giới hạn quyền/identity/version. SA-64 đã vào main;
  answer-3 thuộc SA-66, không được nhận là đã cài trong đợt port SA-62.
- Artifact Pha A vẫn ở kho tệp, không chuyển graph/chunks/manifest/index vào DB.
- **Chi dịch vụ ngoài mới 0 USD**; không dọn worktree/snapshot/ZIP hoặc stage sáu tệp đang sửa của phiên khác tại root.
