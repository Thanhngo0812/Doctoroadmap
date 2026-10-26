# W-09 — trợ lý answer-3 và phiên học

**Bổ sung sau nghiệm thu lần 5, 2026-10-25:** đã nhận main `6249dab`, vá hai Required R-W09-1 (gửi câu tiếp khi usage/EOF cũ còn chờ) và R-W09-2 (tool bài giảng thường phải chuyển đúng cache_only/allow_spend). Mốc mã sửa `0ba4ac8`; xem [báo cáo vá và cổng mới](w09-required-fixes-2026-10-25.md). Các số liệu/mutant/mốc dưới đây là lịch sử trước đợt vá, không gán lại thành chạy trên HEAD mới. Chờ điều phối soát/ghép W-09 trước W-10.

Đợt triển khai ngày 2026-10-24, nhánh `work/w09-assistant`, worktree `tmp/w09-assistant`. Đã hoàn tất triển khai và cổng local, bàn giao để điều phối soát/ghép; không tự đánh dấu vé đạt hoặc ghép main.

## Mốc và phạm vi

- Main nền `46d829a55a62d852897f07102e89cf9a1fd5185e`; đã nhận bằng `git merge main` trong worktree riêng. Giữ worktree W-08/W-11 và mọi lượt bằng chứng cũ.
- Nhận SA-66 `ba4350f`, SA-69 `973fa99`, SA-70 `5188908` trên main; dùng answer-3/lecture-3, scope của lõi và enum search đã chốt. Không sửa use case Pha B hoặc đổi Vertex.
- Commit chức năng đầu `a25bad95e53370839b14e18a3cc34fba3d904eeb`; phần thư viện chỉ đọc `91657f93cf446bd79bbb1344c106f35d0fb93912`; **mốc mã/harness cuối `56acc16914eb2a20f1cb60eafa139cd04d74a4bc`**. Các commit sau phải phân biệt thay mã với chỉ bổ sung hồ sơ.
- Không thêm bảng/migration. PostgreSQL vẫn một head `w11_0007`; dùng PostgresPhaseBStore đã nhận, không nhập learner store CLI.

## Hành vi đã triển khai

Gateway/HTTP: tạo, lọc, đổi tên, xoá phiên; đọc lịch sử và gửi lượt SSE answer-3. Phiên thuộc người/cuốn; server lấy actor, doc/version và bài thuộc module từ course/graph đã phát hành. Body không cấp quyền bằng owner hoặc node_ids tự khai.

Mỗi lượt giữ `client_turn_id` và payload; thử lại cùng mã không thêm lượt hoặc đếm tần suất lần nữa. Hai payload khác nhau dùng cùng mã bị từ chối. Khoá PostgreSQL theo phiên tuần tự hoá hai lượt khác nhau; kiểm độc lập `pg_locks`, không dùng single_flight như mutex vì có thể gộp nhầm hai ý định. Lịch sử đã lưu còn được dùng để chống gọi lại khi đổi phiên bản prompt.

React dùng một khung chung ở lộ trình và trang học: chọn/đổi tên/xoá có xác nhận, lịch sử, chữ hiện dần, dòng công cụ, lỗi/thử lại/cập nhật phiên, nguồn đúng trang, ghi chú phiên module đã đổi. Lộ trình không gửi focus; trang học gửi bài đang mở ở từng lượt, kể cả sau mở tiên quyết. Retry giữ focus của lượt cũ. Cache miss của bài giảng không sinh bài mới.

Đã bắt và sửa race tải lịch sử: phản hồi GET lịch sử cũ không được ghi đè lượt mới vừa hoàn tất. Gộp theo client_turn_id, có `history-race-red.xml` (1 assertion fail, không setup error) → `history-race-green.xml` (10 đạt). Mở phiên mới/xoá phiên cũng khoá composer trong thời gian thao tác để không gửi nhầm phiên trước.

Khung xem tài liệu đã mở cũng được giữ khi server thay ID tạm của lượt bằng ID lưu trong lịch sử. React dùng client_turn_id làm key ổn định; `preview-race-red.xml` có 1 assertion đỏ → `preview-race-green.xml` có 11 đạt. Không giảm assertion hoặc nới timeout; ảnh browser chụp rõ khung xem đang mở.

Dòng công cụ phát từ callback lúc thật sự thực thi, thay vì lúc model mới phát yêu cầu. `tool-state-red2.xml` tái hiện model trả hai tool call trong một vòng trên mã cũ; bản sửa phát quiz running → quiz done → document running → document done. Sự kiện artifact vẫn do lõi phát sau khi hoàn thành, không tự bịa sự kiện sớm ở web. `regression-green2.xml` đạt 27 ca, gồm ba biến thể scope và các lỗi của lượt cổng đầu.

Lượt `tool-state-red` đầu kỳ vọng artifact phát ngay sau từng tool, lệch với hợp đồng lõi phát cuối lượt. Đã sửa kịch bản về đúng hợp đồng bằng hai tool call cùng vòng, chứng minh test mới vẫn đỏ trên mã cũ (`tool-state-red2`), rồi mới nhận bản sửa xanh; không sửa lõi hoặc giảm yêu cầu thứ tự thực thi.

Khách đóng trang chỉ ngừng nhận SSE: producer tiếp tục trên server và lưu PostgreSQL. Mở lại đọc lịch sử hoặc thử lại cùng mã. Đây là xử lý trong tiến trình, **chưa phải hàng đợi bền**: server dừng giữa lượt có thể cần thử lại; nội dung đã lưu vẫn còn.

Markdown/LaTeX dùng renderer/KaTeX thật với trust tắt, raw HTML và ảnh từ chữ bị chặn. Nguồn [Sx] lấy từ registry, nhãn lạ giữ nguyên. Link do mô hình viết trong chữ không thành hành động. Thẻ quiz/tài liệu chỉ hiện khi sự kiện đã đối chiếu bản ghi ready, đúng actor/cuốn; mở thẻ kiểm lại quyền và tham chiếu phiên. HTTP DTO loại raw tool args, validation, private ID/URL, đáp án riêng và chi phí.

Thẻ có xem trước nội dung quiz-3/document-3 đã lưu. Danh sách `GET /courses/{cid}/library` chỉ đọc được bổ sung để kiểm qua HTTP rằng xoá phiên vẫn giữ tài liệu/quiz, có `session_deleted`; không triển khai sinh trực tiếp, submit/chấm quiz hoặc màn thư viện W-10.

`/me/usage` giữ tương thích quota dựng và thêm usage-1: learner_today used_ratio/limited/resets_at, builds_this_month, shared_content_today. Tỷ lệ lấy sổ chi PostgreSQL chuẩn, không cộng counted_in=build hai lần. Hạn học 1 USD/người/ngày trong hợp đồng backend, giao diện chỉ hiện tỷ lệ và giờ đặt lại; giới hạn 10 lượt mới/phút theo người, chung các khoá.

## Sửa cấu hình bài giảng theo phản hồi chủ dự án

Web trước đây dựng GeminiToolModel mà không truyền giới hạn bài giảng: transport mặc định 2.048 token, lệch `BSettings.lecture_max_output_tokens = 4096`. Nhiệt độ mặc định model là 0, nhưng lời gọi thực tế của Lecture3UseCase đã truyền `lecture_temperature = 1.0`, nên không kết luận lần sinh cũ thực sự dùng temperature 0.

Đã lấy model ID, max_output_tokens và temperature trực tiếp từ BSettings khi composition tạo model bài giảng, khớp composition lõi: **gemini-3.1-flash-lite, 4.096 token, temperature 1,0**. Kiểm cả cấu hình model và JSON generationConfig thực sự đi qua adapter `_request` bằng fake transport; không gọi Vertex. Assistant/document/quiz có model theo mục đích, dùng cùng đối tượng VertexCredentials.

Bằng chứng: `lecture-config-red.xml` bắt 2048 != 4096 (native 1); `config-green2.xml` đạt 27 test (native 0). Test tên `test_lecture_model_uses_core_limits_instead_of_transport_defaults`. Sửa áp dụng cho lần sinh mới; không tự xoá hay sinh lại cache bài cũ trong DB của chủ dự án.

## Thiết kế và vận hành

Áp dụng taste-skill nhánh app screen, kế thừa token/font/logo Artboard của main và bố cục W-08. Tham khảo HTML W-09 của thiết kế, không nhập cả nhánh hoặc HTML công thức lỗi. Quyết định, hash HTML và ba lỗi công thức preview D-R4-01/02/03 ghi tại `w09-evidence/design-notes.md`.

Khung desktop 380 px; tablet dialog; mobile toàn màn. Tên CSS learning-chat-* tránh xung đột với demo cũ. Có focus/keyboard/Escape, vùng bấm 44 px, motion token và reduced-motion hệ điều hành. Taste inspector chạy trên bản DOM riêng để kiểm kiểu dáng, không thay bằng chứng tương tác React. Axe ghi đúng từng ảnh được chạy; phần toán/tương phản mà Axe yêu cầu review được đo bổ sung, có phản ví dụ cho chữ không đủ tương phản và bị che.

Bộ cuối `browser-final8`: 12 cấu hình, 71 ảnh tương tác, 27 lượt Axe (0 vi phạm), 343 bản ghi HTTP/SSE; có bản tee của cùng phản hồi nên đây không phải số request duy nhất. Không có page error. 59 console log đã phân loại: 2 probe 401 trước đăng nhập, 3 phản hồi 404 sau thu hồi quyền, 54 CSP do công cụ Axe thử font/style; không nới CSP ứng dụng. `browser-final-summary.json` lưu chi tiết, có JSON/SQL độc lập, DB UUID đã xoá và server đã dừng; chi ngoài 0 USD.

`contrast-dom-counterexamples.json` kiểm chính hàm đo/guard trên bản DOM offline: tô chữ cùng màu nền làm tương phản giảm từ 10,90 xuống 1,00 và bị bắt; phủ một phần tử thật lên chữ cũng bị bắt; phục hồi DOM thì guard xanh. Không thay mã đang chạy cổng. Lượt đầu đo khi animation đang chạy đã đỏ; lần chuẩn chờ font và CSS animation hoàn tất, giữ nguyên ngưỡng 4,5.

Hướng dẫn mở backend 8000 và frontend 5173, cùng kiểm fake/PG riêng, có trong `src/web/README.md`. Không tự mở dịch vụ dev, gửi thư, upload media hay gọi nhà cung cấp thật.

## Kiểm và hồ sơ

Tất cả kiểm trong đợt này dùng mô hình/embedding/media/mailer giả, PostgreSQL UUID thật; chi nhà cung cấp ngoài **0 USD**. Dữ liệu doc-1 v8 và sáu cuốn chép theo manifest W-06, kiểm SHA-256; không liên kết hoặc đọc learner store live. Basetemp dưới tmp, tách khỏi ảnh UI.

Lượt cổng đầu phát hiện thiếu tệp candidate cho kiểm dry-run W-15. Đã bổ sung bản chép độc lập từ train PDF, đúng `report/w15-evidence/candidate.json`, SHA-256 `1f019766e74a747d293c15ad5bc86b2ea90420b49a8437cf27c1f6805656a627`; xem `w15-fixture-copy.json`. Không đọc heldout, sửa test W-15 hoặc chạy dựng có chi. Test fake cũ được chuyển sang lecture-3/text stream, giữ kiểm cache/progress/embedding/shared ports, bổ sung kiểm adapter JSON riêng.

| Phép kiểm | Hồ sơ | Kết quả |
|---|---|---|
| HTTP/PG answer-3, quyền, focus, idempotency, rate, cap, disconnect | `library-green2.xml` | 43 đạt, native 0 |
| Cấu hình bài giảng/model theo mục đích | `lecture-config-red.xml`, `config-green2.xml` | RED native 1 → 27 đạt native 0 |
| Thư viện sau xoá phiên qua HTTP | `library-red.xml`, `library-green2.xml` | 3 assertion RED → GREEN |
| Mutation tuần tự, phục hồi byte nguồn | `mutations2/results.json` | 19/19 bị bắt, không setup error; runner native 0 |
| React toàn bộ trên mốc cuối | `react-final5.xml` | 192 đạt, native 0 |
| Build trên mốc cuối | `build-final5.log`, `.exit` | native 0 |
| Cổng Python/PostgreSQL toàn repo | `gate-final4.xml`, `.log`, `.exit` | 2.622 đạt, 1 Cloudinary skip, 1 replay xfail có sẵn; native 0 |
| Browser cuối | `browser-final8/` | 71 ảnh, 27 Axe, native 0 trên 56acc16 |

Lệnh cổng từ gốc worktree:

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w09-final4 --junitxml=report/w09-evidence/gate-final4.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=junit --outputFile=../../../report/w09-evidence/react-final5.xml
npm.cmd --prefix src/web/frontend run build
$env:W09_EVIDENCE_RUN = 'browser-final8'
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w09_web_runtime.py
```

Mỗi lần chọn basetemp/evidence mới. Không pytest trần. Mutation chạy tuần tự, không cùng gate/server trên cùng mã; mọi file được phục hồi byte sau mỗi phép phá. `w09-source-scope.json` ghi SHA-256 và Git blob của các file vé; hồ sơ cuối bổ sung manifest đúng mốc kiểm.

`final-gates-summary.json` ghi lệnh/native/JUnit trên 56acc16. `source-manifest-final.json` đã đối chiếu lại sau cổng: cả 1.043 file mã/test/script giữ nguyên SHA-256. Main vẫn `46d829a`; `workspace-preservation.json` xác nhận main/W-08/W-11 giữ đúng nhánh và mốc. Commit hồ sơ sau mốc mã chỉ thêm tài liệu/bằng chứng, không thay mã đã kiểm.

Các lượt dev/RED trước vẫn giữ nguyên, gồm lỗi fixture/môi trường, lỗi CSS demo, phép kiểm modal/KaTeX cần đo bổ sung và các lần harness chưa hoàn tất. Chúng không được trình bày thành bằng chứng xanh cuối. Cổng lần 1 có 2.618 đạt/3 lỗi/1 skip/1 xfail: thiếu candidate, fake lecture-2 cũ và OpenAPI bị thay trong khi suite đã nạp app cũ; không dùng lượt này nghiệm thu. Lần 2 đạt 2.622/1 skip/1 xfail trên backend sau sửa; lần 3 chủ động dừng sớm (native -1) khi phát hiện cần vá giữ preview. Lần 4 chốt toàn bộ trên 56acc16; mã được giữ nguyên trong lượt chốt.

Các log browser trên Windows có cảnh báo WinError 10054 lúc đóng kết nối và thông báo shutdown của harness. Không xoá log hoặc coi chúng là lỗi giao diện: lượt cuối có native 0, 0 page error, SQL độc lập và xác nhận thread server đã dừng/DB tạm đã xoá. Có video tương tác và raw audit để điều phối soát lại.

Ảnh/video các lượt browser lịch sử giữ tại local, không đưa toàn bộ ảnh trùng vào Git; `historical-browser-index.json` lưu đường dẫn/hash. Chỉ bộ browser cuối được giao làm ảnh/video chính. JSON hợp đồng do test W-06/W-14 sinh lại được chép và kiểm hash vào thư mục riêng của W-09 trước khi phục hồi tệp của vé khác.

Cổng main còn tự sinh hai thư mục untracked `report/w15-evidence/sql/latest/` và `report/w25-evidence/sql/latest/`. Giữ nguyên bản local, không commit vào phạm vi vé khác; bản chép độc lập/hash nằm tại `w09-evidence/generated-other-sql/manifest.json`. Mã nguồn và tệp đã theo dõi của làn khác đã được giữ sạch; hai thư mục untracked này được để lại có chủ đích.

Một số log/XML RED do pytest sinh có dấu cách cuối dòng. Bản đưa vào Git chỉ bỏ khoảng trắng cuối dòng; byte gốc giữ trong `raw-log-whitespace-backups2.zip`, đối chiếu SHA-256 tại `whitespace-normalization.json`. Tên/trạng thái/thuộc tính ca JUnit và native exit được giữ nguyên, không sửa kết quả hoặc assertion.

## Giới hạn và bước tiếp

- Chưa gọi mô hình/Mailer/Cloudinary thật hoặc chạy replay có tiền; thời gian quan sát với fake không phải độ trễ/SLA nhà cung cấp.
- Đóng browser tiếp tục được trong cùng tiến trình server; không bảo đảm khôi phục tác vụ đang chạy sau khi server chết.
- Cache bài giảng cũ không bị dọn do sửa giới hạn transport. Không thay đổi SA/core hoặc tự chuyển API.
- W-10 còn submit/chấm quiz, sinh tài liệu trực tiếp và thư viện đầy đủ; đã có mốc SA-67/68 để nhận sau khi điều phối soát/ghép W-09.
- Chờ điều phối soát và nghiệm thu; không tự sửa vé/kế hoạch/handoff hoặc ghép main.
