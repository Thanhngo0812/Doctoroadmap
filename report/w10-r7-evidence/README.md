# W-10 Required R7 — bằng chứng 2026-10-26

Báo cáo: [w10-sua-required-r7-2026-10-26.md](../w10-sua-required-r7-2026-10-26.md).
Nguồn bàn giao mới: 1fc0f553bec808241388b722fa2c10a1c6ead33d, nhận main 163917ca7f0384ef383dd26acab2380f06efef6f. Commit sau mốc này chỉ được thêm báo cáo/bằng chứng.

## Bộ bàn giao sau nhận main

- gate-python-r7-main/{output.log,exit.json} và gate-python-r7-main.xml: cổng toàn repo, PostgreSQL bắt buộc, native exit/source SHA.
- gate-react-r7-main/{output.log,exit.json}, gate-react-r7-main.xml; gate-build-r7-main/{output.log,exit.json}.
- main-build-manifest.json: bundle thật đã build trước browser.
- browser-r7-main-run/{output.log,exit.json}: lệnh/native/source SHA.
- browser-r7-main/{audit.json,runtime.json}: HTTP/SSE thật, SQL độc lập, provider giả, DB UUID riêng và cleanup. Ảnh PNG và video WebM ở cùng bộ này; taste-inspect chứa ảnh/JSON inspector.
- postgresql-gate/: bản chép SQL của runner; copy-receipts ghi SHA nguồn/đích. Tệp gốc nằm local ở vé W-15/W-25, không đưa vào Git W-10.
- mutation-main-source-proof.json: so byte đích giữa mutation thực chạy ở 9bb90d9 và source 1fc0f55; không coi là chạy lại mutation trên HEAD mới.

## RED/GREEN và lịch sử

- rate-origin-red, late-submit-red, notice-red, notice-ui-red: native/log/JUnit đỏ có assertion thực.
- rate-origin-green1, late-submit-green1, admission-green3, physical-lock-green, submit-controls-green2: các lát xanh.
- sse-*-red/green: native assertion về terminal payload và required/type validation của harness.
- mutations-existing-final2/results.json, mutations-required-final2/results.json: 19 mutant, mã nguồn và byte phục hồi, native/JUnit từng ca.
- history/: audit/runtime/log gốc của các browser cũ. Các thư mục browser phát triển vẫn nguyên local; .gitignore chỉ loại ảnh/video cũ khỏi Git. Không dùng chúng thay bộ bàn giao browser-r7-main.
- gate-*-r7-final/delivery/handoff: các checkpoint trước main mới, giữ nguyên native và nguồn; không gán thành lượt kiểm mới.
- raw-text-2026-10-26.zip và raw-text-manifest.json: byte log/XML/JSON trước khi chuẩn hoá whitespace để Git kiểm được; normalization-receipts.json ghi SHA trước/sau cho các bản đọc trong Git.
- files-sha256.json: SHA các tệp bàn giao (trừ chính manifest).

## Chạy lại

Chạy từ gốc worktree W-10, dùng tên bằng chứng/basetemp mới; giữ các lượt cũ. Runner tự quản lý DB kiểm riêng, không seed DB phát triển. Mô hình/Mailer/MediaStore phải là giả.

```powershell
$env:W10_EVIDENCE_FOLDER='w10-r7-evidence'
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w10_capture.py gate-python-<ten-moi> C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w10-<ten-moi> --junitxml=report/w10-r7-evidence/gate-python-<ten-moi>.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
$env:W10_EVIDENCE_RUN='browser-<ten-moi>'
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w10_capture.py browser-<ten-moi>-run C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w10_web_runtime.py
node scripts/w10_sse_audit.cjs
```

Mutation chỉ khi không có gate/server trên cùng mã: đặt W10_R7_MUTATION_SUFFIX=-<ten-moi>, chạy scripts/w10_r7_mutation_checks.py; kiểm mã phục hồi trước cổng tiếp. Không dùng pytest trần trong worktree. Hướng dẫn mở service phát triển vẫn ở src/web/README.md; harness browser này tự dừng server/DB riêng khi kết thúc.
