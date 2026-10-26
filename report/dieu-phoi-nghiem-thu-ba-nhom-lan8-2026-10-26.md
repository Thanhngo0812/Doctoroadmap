# Điều phối — nghiệm thu ba nhóm lần 8, 2026-10-26

Kết luận: **W-10 đạt**, nhận **mốc backend W-04** và **guard thiết kế D-R7-02**.
W-04 còn React; W-16 còn React; **W-23 chưa đạt**. Chưa nghiệm thu triển khai production.
Đã ghép **local 1be7e1c** từ đỉnh kiểm ee5a75f; không push theo quyết định chủ dự án 24/10.
Chi nhà cung cấp mới **0 USD**. [Lời giao ba nhóm](lenh-giao-viec-ba-nhom-lan8-2026-10-26.md).

## 1. Mốc và phạm vi

| Nhóm | Commit ghim | Phán xét |
|---|---|---|
| Web W-10 | aaf68eb6795c929169e5212a05093d8d817c76e3 | Đạt; đóng R-W10-1/R-W10-2 và khoảng trống thu body SSE R7 |
| Lõi W-04 | c1f2fe9c813b81af66cfb61ce47a0fe760279de9; mã b8cb7de | Đạt backend; toàn vé còn hồ sơ React |
| Thiết kế | feb5f5e1ac847b8b8bfa0db726b4d26142859f6d | Đạt guard JS; đính chính D-R8-01 đã ghi, W-23 còn mở |

Nền main local 153c577 đã có **SA-61 ghép ab5c2fa** do Claude; trạng thái “SA-61 còn nhánh” ở các cập nhật cũ là lịch sử.
Chưa đổi transport web: vẫn Vertex. Codex không chạy lại thử thật Developer API, W-15 hoặc khôi phục artifact.
Đặt cửa phối hợp c8c2d2b tại bàn giao mục 8; tạo worktree mới tmp/coord-r8-acceptance-20261026,
nhận ba commit trên tuần tự; không đổi nhánh root hoặc thư mục nhân viên.

OpenAPI hai nhánh tự ghép; đã tái sinh bằng scripts/w10_export_contract.py từ app kết hợp, không có diff.
**54 operation**, giữ đủ route W-04 và W-10. Không migration mới, head PG vẫn w11_0007.
Mã/script/test/design tích hợp khớp commit ghim sau chuẩn hoá LF/CRLF, chỉ OpenAPI hợp nhất hai nhánh khác bản riêng từng nhóm;
không nói checksum bytes bản checkout CRLF bằng blob LF. Xem product-comparison.json và openapi-operations.json.

## 2. Cổng độc lập trên đúng bản tích hợp

| Kiểm | Kết quả |
|---|---|
| Runner Python toàn repo, PostgreSQL bắt buộc | 2.824 đạt, 0 fail/0 error; 1 Cloudinary live skip và 1 replay answer-2 xfail kế thừa |
| React | 219 đạt, 0 fail |
| Build React | native 0 |
| Browser HTTP/PG/core thật, model/mail/media giả | 12 cấu hình,96 ảnh,3 video; native 0 |

Python trong đó có **49 W-04**, **5 admission W-10**, các ca content, **64 presentation**, **13 W-16**;
số cụ thể và tên skip có trong gate-summary.json/JUnit. Không thêm skip/xfail hoặc giảm assertion/timeout.
Cổng nguồn ee5a75fe571d62803387429677c2b87201baf654; lệnh/cwd/native/thời gian trong runs/*-exit.json.
Cổng tác giả 2.775/2.808 không dùng thay cổng điều phối.

Lượt đầu Docker Desktop chưa chạy, cổng 5433 không có listener: browser native 1/connection timeout;
full xuất hiện lỗi setup PG, dừng có kiểm soát native 4294967295, chưa có JUnit đầy đủ. Giữ nguyên logs,
không tính là RED chức năng hoặc bỏ lỗi. Khởi động Docker Desktop ẩn và đúng service db-test hiện hành
bằng docker compose --env-file src/web/.env -f src/web/docker-compose.yml up -d --no-recreate db-test;
pg_isready xác nhận rồi chạy lại toàn cổng với basetemp/folder mới. Không tạo lại volume hoặc dọn DB cũ.

Fixture: chép thường 3.144 tệp đúng manifest/SHA allowlist sáu sách, không learner store;
PDF candidate dùng trong test giả: 1.054.520 bytes, SHA 1f019766e74a747d293c15ad5bc86b2ea90420b49a8437cf27c1f6805656a627,
không link/hardlink. Chỉ dùng input phát triển cố định, không đọc cache sống hoặc tập giữ lại.

## 3. W-10 — hai lỗi đã đóng

**R-W10-1:** admission web dùng chung PostgreSQL cho button và tool make_document, theo actor/xuyên khóa.
Trước: 10 lượt từ nút rồi chat sinh tài liệu thứ 11. Sau: 10 lượt từ nút, lượt thứ 11 trả 429; chat không tăng model/doc row,
phản hồi có cảnh báo nghiệp vụ an toàn và còn sau reload. Ca trợ lý→button, replay client_turn_id,
người khác/owner giả, hai runtime tranh suất cuối và connection giữ advisory lock đều có assertion HTTP/SQL/model độc lập.
Guard sinh/cache/retry/ngân sách vẫn do core; adapter web chỉ hạn tần suất và dịch lỗi nghiệp vụ.

**R-W10-2:** mỗi lần submit có token gắn course/attempt/mục lịch sử, hủy hiệu lực khi route đổi/unmount;
callback success/error/finally/focus cũ không ghi vào lượt mới. Browser giữ fetch completion sau HTTP thật đã
commit PG, Back sang attempt khác đang pending: kết quả cũ bị bỏ qua, Forward đọc đúng kết quả đã lưu.
Review độc lập 33 React và 1 ca cùng attempt/khác mục lịch sử đạt; bỏ guard success/error/finally gây 3/3/4 assertion fail,
bỏ khóa lịch sử gây 1 assertion fail. Probe runtime/core/admission stub có mutant bypass làm số tài liệu 2→3 bị bắt;
probe này ngoại tuyến, PG thật được chứng minh riêng trong cổng điều phối.

Giữ phần W-10 đã đúng: đề công khai không đáp án, owner/cuốn, xáo phương án, nộp nguyên tử/idempotent,
progress rollback, Markdown/GFM/KaTeX/nguồn, library group độc lập origin, phạm vi 6 module không gọi model,
đóng dialog vẫn dựng/lưu xong, reload/history/focus và ngân hàng quiz dùng lại.
Review năm trục không có Required/Critical chức năng mới. 616 tệp evidence,544 raw ZIP members,
4 cổng × 772 source SHA và 19 mutation tác giả được kiểm provenance; không gán lại lượt cũ thành chạy ở HEAD mới.

## 4. W-04 — nhận backend, chưa nhận toàn vé

PATCH /me trim tên 1–60 và forbid payload thừa; POST /me/password cần mật khẩu hiện tại,
A thành công giữ A/hủy B; POST /auth/logout-all hủy A+B/xóa cookie. Actor/session từ máy chủ,
không nhận owner/session_id của client. Sai mật khẩu không đổi hash/phiên/audit; giữ Origin/CSRF,
Argon2id/luật W-02, phản hồi public/no-store và bảo mật cookie.

Account lock/transaction đọc lại phiên và trạng thái trước ghi, ngăn phiên vừa bị thu hồi/reset/disabled.
Hash/thu hồi/audit cùng transaction; PG fault audit rollback cả ba. Reset W-03 vẫn hủy mọi phiên.
Cổng có49 ca W-04 gồm fake và PG, hai cookieclient độc lập, tài khoản khác giữ nguyên,
đăng nhập mật khẩu cũ/mới và replay cookie đã thu hồi. Review riêng 24 fake/HTTP +5 probe đạt,
đổi mật khẩu cạnh tranh chỉ một thành công; hai mutant kiểm mật khẩu và hủy nhầm A đều assertionfail,
phục hồi source/control xanh. Probe reviewer không là PG; cổng điều phối bổ sung PG thật.
143/143 tệp evidence khớp cả raw và bản đóng gói,8 source SHA và10 mutation tác giả có provenance.
Không thay core/gateway/React/schema hoặc tạo migration rỗng. Web còn ba khối hồ sơ sau W-16.

## 5. Thiết kế — guard đạt; W-23 chưa đạt

Node VM chạy script trích từ HTML thật, lấy bốn card chéo từ markup và kiểm here/elsewhere/all,
5→6→5 nút/cảnh báo.64 test độc lập đạt; đảo ===→!==, đưa bộ lọc origin cũ và >5→>=5 đều
1 assertion fail/0 setup/native 1, phục hồi đúng SHA. **Đóng D-R7-02**; không giao lại source/token/branding/math đã nhận.
Các lỗi thiết lập scratch reviewer được giữ/không tính là lỗi sản phẩm.

**D-R8-01, Required về hồ sơ W-23: đã đính chính bảng dòng 52–56 trong báo cáo thiết kế, chưa nhận W-23.**
Ảnh self-check React là Đại số và đã mở; HTML là catalog có self-check gập. Viewer React ở modal giữa tablet,
HTML viewer inline. Các anchor generating/chat-answered/chat-options được viện dẫn không tồn tại;
menu React chỉ Đổi tên/Xóa. Không dùng các cặp khác state/crop để kết luận khớp token/khoảng cách/tương tác.
10 PNG/2 WEBM đều tồn tại và SHA root/worker khớp, không phải mất artifact; runtime origin/frontend reuse proof được ghi rõ.
Nguồn ảnh/video lịch sử giữ nguyên; điều phối sửa tài liệu, không tự viết UI sản phẩm.

**D-R8-02, Optional coverage:** VM đang gọi hàm bằng tham số cứng. Chỉ đổi onclick here→button/elsewhere→assistant
vẫn 64 pass; nên thêm guard handler/markup. Nguồn hiện tại wiring đúng và đã có kiểm tab browser R7,
không là lỗi sản phẩm hoặc điều kiện mở lại source đã nhận.

## 6. Browser, thị giác và giới hạn bằng chứng

12 cấu hình = 390/768/1280 × sáng/tối × motion thường/giảm.96 ảnh, 65 lượt Axe/0 violation,
73 phép đo tương phản thủ công thấp nhất 5,8448:1; 0 overflow/vùng bấm lỗi/pageerror ở các assertion đã chạy.
Đã xem trực tiếp quiz desktop/mobile, documentmobile và noticechatmobile; chữ đọc rõ, thương hiệu/token nhất quán.
Taste inspector appmode không FAIL, 1 WARN generic familymath (cả 3 cỡ); Be Vietnam Pro và KaTeX_Main có trong fontsLoaded.
Thanh submit sticky trong fullPageảnh có thể nằm giữa ảnh dài vì bám viewport; không suy ảnh dài là viewport.

250 HTTP records,27 SSE bodies đủ:26 terminal có payload theo public contract,1 AbortError chủ ý tại disconnect-document,
0 missing body/0 pending rejection/0 privacy failure. Tee ghi body trước giao ứng dụng, không mất khi đổi URL.
Điều phối còn quét đệ quy độc lập355 payload JSON/SSE,112 payload đề quiz: không private/modelvalidation/answerkey trước nộp.
Không gọi phép kiểm này là triển khai toàn bộ JSON Schema hoặc chứng minh mọi input production.
135 console messages được phân loại:3 HTTP401,1 HTTP404 quyền,1 ERR_FAILED chủ ý,65 Axe CSP font và65 Axe CSP inline-style.
Có3 WinError10054 từ callback Windows đóng socket trong log server; browser-native 0, không pageerror,
terminal/persistence/SQL assertions đều đạt. Không gọi console/log là trống, không nới CSP để làm xanh.

SQL connection độc lập:28 documents/14 quiz attempts/14 submissions/6 progress đúng learner fixture,
6 quiz_gen +6 quiz_verify cho14 lần làm (bank reuse),28 document/27 validation/2 assistant ledger rows đều 0 USD.
Dùng graphv8 doc-1 từ fixture cố định, không lượt W-15 mới. FakeMailer/ScriptedModel/LocalImageMedia,
không SMTP/Cloudinary/ADC/provider/embedding thật; viewer nguồn kiểm UI/quyền với ảnh giả, không kiểm chất lượng dịch vụ live.
Browser DB UUID riêng đã được harness kết thúc và đối chiếu pg_database không còn; port 8020 đóng/server thread dừng.
Ảnh/video raw giữ tại worktree mới; browser-local-files.json có path/bytes/SHA cho toàn bộ tệp.

## 7. Kế hoạch kế tiếp và điều kiện nhận

| Nhóm | Việc tiếp | Xong khi |
|---|---|---|
| Web | React W-16 → nghiệm thu → React W-04 | usage-1 không USD/ba trạng thái/dải reset/cachedcontent; hồ sơ đúng A/B/cookie/fields, ảnh và browserPG |
| Lõi | Backend W-12: lời mời email, mẫu thư, migration và hook xác minh tối thiểu | đúng người/email/TTL/duplicate/rate/capacity/race/audit, HTTP/PG/RED-GREEN; UI do web sau |
| Thiết kế | W-23 đúng ảnh/state/viewport và hỗ trợ mẫu W-16/W-04/W-12 | bảng lệch có hai ảnh/nguồn/state/cách xử lý, video tương tác, không Cloud |

Từng vé/nhánh riêng từ main local cuối. Không mở W-17 trước W-16 đầy đủ; W-18/W-19/W-20 còn mở,
W-21 chưa đến lượt. W-19 đã đủ W-08/09/10 nhưng xếp sau usage/account nếu chỉ một phiên web.
Lõi làm backend W-12 là phân công điều phối, không chuyển trách nhiệm frontend hoặc tự nhận toàn vé.
Không bật đề xuấtbuild 5 USD/ngày/3 lượt tháng, không đổi giá/transport hoặc tái dùng phê duyệt paid cũ.

## 8. Lệnh, lưu bằng chứng và Git

Lệnh đầy đủ/cwd/commit/native/thời gian có trong [bộ bằng chứng](coord-ba-nhom-lan8-evidence-2026-10-26/manifest.json).
Cổng chính từ gốc worktree:

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/coord-r8-full-ready --junitxml=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r8-tools-20261026/runs/full-ready.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r8-tools-20261026/runs/react.xml
npm.cmd --prefix src/web/frontend run build
W10_EVIDENCE_RUN=browser-coord-r8-ready W10_EVIDENCE_FOLDER=w10-r7-evidence python scripts/w10_web_runtime.py
```

Dòng browser minh họa env; lệnh PowerShell thực được ghi trong hồ sơ chạy. Evidence text bản đọc chuẩn UTF-8/LF,
bỏ space/tab cuối dòng và dòng trắng cuối tệp để đạt diffcheck; manifest ghi SHA raw/bản đóng gói, raw không bị sửa/xóa.
Lượt đóng gói đầu bị diffcheck chặn do CR/CRLF và dòng trắng EOF của bản QA; giữ log/native packaging-before,
chuẩn hoá bản QA bằng bytes LF rồi chạy lại gate whitespace, không hạ luật hoặc đổi raw/test/source sản phẩm.
Main nhận đúng đỉnh ee5a75f đã kiểm; cây commit src/scripts/tests/design sau ghép không khác đỉnh đó; sáu tệp dở không thuộc bản kiểm vẫn được giữ ở root.
Đính chính/bàn giao/task là commit tài liệu điều phối riêng. Sáu tệp dở root giữ nguyên SHA;
không stash/reset/restore/dọn worktree/dữ liệu, không đụng tmp/t01a-clean-ff797eb hoặc tập giữ lại.
**Chỉ ghép/commit local, không push. Cửa SA/cổng PG toàn repo mở lại sau commit hồ sơ lần8.**
