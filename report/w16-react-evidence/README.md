# W-16 React — bằng chứng 2026-10-26

Báo cáo: [w16-react-muc-dung-2026-10-26.md](../w16-react-muc-dung-2026-10-26.md).

Source toàn bộ mã/test/harness: **012abea28a32272a91aaccfa54823037652af28a**, main nền 788b600eedc44a161b6ed4c59e88bd59226aa86f. Hồ sơ sau mốc này không đổi src/scripts.

- gate-python-final: lượt full native 1 vì thiếu PDF train W-15, giữ nguyên.
- candidate-control và w15-candidate-copy.json: bổ sung fixture theo metadata đã nhận, test lỗi xanh; không PDF trong Git.
- gate-python-repeat: lượt full sau fixture, basetemp mới.
- gate-react-final, gate-build-final và bundle-final.json: toàn React/build và SHA bundle trước browser.
- browser-final-run: native/lệnh/source SHA; browser-final: JSON HTTP/SSE/SQL, ảnh và video thật. Provider/clock/ledger giả, app/core/PG thật, DB UUID riêng.
- browser-final-summary.json, design-review.json: phạm vi Axe, contrast, reduced-motion, console và các lưu ý thị giác, không thay JSON/raw gốc.
- mutation-null-final: assertion fail đúng một ca trên source cuối, SHA nguồn/phá/phục hồi.
- usage-red, chat-limit-red: hành vi cũ đỏ. focused-green*: giữ các lượt setup lỗi/matcher và hồi quy đã sửa; không tính setup lỗi làm RED nghiệp vụ.
- timezone-la-control và timezone-control.json: UI vẫn dùng giờ Việt Nam khi timezone host khác.
- fixture-copy.json: hai manifest W-06, 3.145 bản chép độc lập có SHA. Không CLI learner store hoặc dữ liệu live.
- history: log/runtime/audit các smoke cũ; ảnh/video phát triển vẫn giữ local, được ignore để không trộn bộ ảnh cuối.
- raw-text.zip + raw-text-manifest.json: byte gốc log/XML/JSON; normalization-receipts.json: log/XML bản đọc Git nếu có chuẩn hoá whitespace; files-sha256.json kiểm tệp bàn giao, không tự băm chính nó.

Các tệp SQL mà full gate tự sinh dưới report/w15-evidence/sql và report/w25-evidence/sql được giữ local; bản chép của W-16 kèm receipt trong postgresql-gate. Không stage đường dẫn vé khác, không dọn basetemp/worktree/snapshot/ZIP.

## Lệnh

Từ gốc worktree W-16, dùng label và basetemp mới cho lượt mới. Chỉ một full PG gate một lúc; không mutation cùng server/gate.

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w16_capture.py gate-python-<moi> C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w16-<moi> --junitxml=report/w16-react-evidence/gate-python-<moi>.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
$env:W16_EVIDENCE_RUN='browser-<moi>'
$env:W16_BROWSER_SMOKE='0'
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w16_capture.py browser-<moi>-run C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w16_web_runtime.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w16_mutation_check.py mutation-<moi>
```

Browser runtime tự dừng server và gỡ đúng DB UUID của nó; không cần hoặc được seed DB phát triển để tạo ảnh. Hướng dẫn mở backend/frontend dành cho chủ dự án ở đầu src/web/README.md. Chưa làm React W-04 trước khi W-16 được điều phối nhận.

Đợt cuối: 2.824 Python, 229 React/build, browser 66 ảnh/66 Axe, native đều 0 trên source 012abea. ZIP giữ 245 tệp text gốc; 17 bản đọc log/XML/text được chuẩn hoá (có receipt encoding/hash). SHA trong copy-history-receipts là byte nguyên gốc trước chuẩn hoá; đối chiếu bản gốc trong ZIP và bản hiện hành trong files-sha256.json.
