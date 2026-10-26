# W-09 — vá R-W09-1 và R-W09-2 sau nghiệm thu lần 5

Đợt 2026-10-25, nhánh `work/w09-assistant`, worktree `tmp/w09-assistant`. Mốc nộp trước `da4d6399965f5a67accaacc6ea34af8ce56f0dd5`. Báo cáo này bổ sung hồ sơ W-09, không tự kết luận vé đạt hoặc ghép main.

## Nền và phạm vi

Đã nhận main `6249dab` bằng `git merge main`, tạo mốc tích hợp `9e7f9e501acbc53bd25370faa1232a62c351e0db`. Nhận phần lõi/thiết kế điều phối đã ghép; giữ nguyên hai worktree W-08/W-11 và bằng chứng cũ.

Mã sửa/test/harness: **`0ba4ac8f5bc63256e33d736a08c0d6411a5b0b48`**. Chỉ sửa ranh giới kết thúc lượt ở hook React và callback bài giảng ở web runtime, cùng test/fake/harness cần để kiểm. Không viết lại auth/quyền/DTO, core Pha B, renderer Markdown, thư viện hoặc migration. Head CSDL vẫn `w11_0007`. Không đổi transport Vertex hoặc trần chi.

## R-W09-1 — câu hỏi biến mất sau final

Trước sửa, final thành công xoá live turn nên ô nhập mở lại, nhưng `active.current` vẫn giữ khoá đến EOF và sau GET usage. Người học gửi câu thứ hai: form xoá draft rồi `run()` thoát sớm; không có POST tiếp theo.

Bản vá dùng trạng thái terminal trên chính request đang chạy. Final đánh dấu terminal cùng lúc cập nhật giao diện, cho phép lượt kế tiếp nhận khoá mới ngay. Callback SSE, usage, catch và finally đều kiểm request còn là request hiện tại trước khi đổi trạng thái. Phản hồi cũ về muộn không ghi usage đè lên lượt mới, không xoá chữ hoặc mở ô nhập khi câu mới còn stream. Lượt retry vẫn giữ intent/client_turn_id; không đổi payload hoặc tạo lại mã khi thử lại.

Nhận nguyên helper của điều phối ở `web-review/Assistant.final-usage-race.test.tsx`, chỉ đổi ba import sang đường dẫn source trong worktree. Ca gốc giữ nguyên assertion POST count 2. Thêm bốn ca độc lập: usage cũ thành công/lỗi khi lượt hai đang stream; final nhưng EOF cũ chưa tới rồi lỗi đuôi; usage cũ về sau cả usage mới.

| Bằng chứng | Kết quả |
| --- | --- |
| `r1-red.xml` trên mã sau nhận main, trước vá | 1 assertion fail / 1 test; 0 setup error, native 1; draft rỗng và chỉ 1 POST |
| `r1-expanded-red2.xml` trên nguồn cũ phục hồi có kiểm byte | 5 assertion fail / 5 test, đều POST count 1 thay vì 2; native 1 |
| `r1-green2.xml` | 22 đạt gồm 5 ca mới và 17 ca W-09 trước; native 0 |

`r1-expanded-red.xml` và lượt `r1-green.xml` đầu có bốn ca phụ không vào được tài khoản vì fixture thiếu `email_verified`; giữ log/XML lịch sử nhưng **không tính bốn lỗi đó là phản chứng chức năng**. Đã bổ sung trường fixture đúng hợp đồng, chạy lại chính assertion trên nguồn cũ thành `r1-expanded-red2`, không tăng timeout/skip/hạ assertion. Ca nguyên gốc của điều phối vẫn tái hiện đúng ở mọi lượt RED.

## R-W09-2 — tool bài giảng thường bị ép cache-only

Callback web trước đây luôn gọi `cache_only=True` và bỏ `allow_spend`; cả yêu cầu tool thường cũng trả not_cached/rỗng. Bản vá chuyển `owner`, `cache_only` mặc định False, `allow_spend` mặc định False xuống `Lecture3UseCase.make`. Không sửa lõi và không tự bật chi. Focus prefetch của lõi vẫn truyền True/False tương ứng cache-only/allow-spend nên cache miss không sinh bài.

Test gọi WebLearningRuntime/AssistantUseCase thật với model kịch bản: mặc định và `cache_only=False` sinh bài ready đúng một lần, `cache_only=True` miss không gọi model; đọc lại cache dùng chung không sinh thêm. Spy biên callback kiểm chính xác owner/graph/permission; ca thực tế không cấp quyền hoặc cấp False không gọi model. Focus miss/hit đọc cache đúng nội dung, không sinh thêm.

| Bằng chứng | Kết quả |
| --- | --- |
| `r2-red.xml` trước sửa | 6 assertion fail, 2 control pass, 0 setup error; native 1 |
| `r2-green.xml` | 26 đạt, native 0 |
| `backend-green2.xml` | 29 đạt gồm HTTP/PostgreSQL thật và các ca permission bổ sung; native 0 |

Ca HTTP/PostgreSQL mới gửi tool mở bài chưa cache qua route thật, nhận artifact bài học và kiểm cache ready/body bằng connection SQL độc lập, đúng owner phiên; người khác không thấy phiên. Lượt `r2-http-green` đầu đã vượt kiểm sinh/cache nhưng assertion thêm về learner_id ở ledger không đúng với khoản bài giảng dùng chung. Đã đối chiếu lõi, thay phép kiểm đó bằng owner bản ghi phiên thực; không sửa ledger/core hoặc dùng lỗi assertion phụ này làm RED của hồi quy.

## Guard và nguồn

Chạy `run_mutations.py` tuần tự, **trước** full gate/browser, luôn phục hồi exact bytes trong finally. Receipts mới ghim `0ba4ac8` và SHA-256 gốc/phá/phục hồi:

| Phép phá | Assertion fail |
| --- | --- |
| Khoá lại sau final như cũ | 5 |
| Cho usage cũ ghi vào state mới | 1 |
| Cho finally cũ mở khoá lượt mới | 3 |
| Ép callback bài giảng cache-only, bỏ permission | 8 |

Tất cả native khác 0, setup error 0, nguồn sau phục hồi khớp byte trước phá. Chỉ **bốn** mutant này được tuyên bố chạy trên mốc vá. 19 mutant của đợt cũ giữ nguyên provenance lịch sử, không gán thành đã chạy lại trên HEAD hiện tại. Hồ sơ và các lỗi setup ban đầu do điều phối giao vẫn giữ nguyên tại `report/coord-ba-nhom-lan5-evidence-2026-10-25/web-review/`.

## Cổng cuối và browser

Lệnh/kết quả mới trong `report/w09-required-fixes-2026-10-25/`, basetemp dưới `tmp/`. Full gate dùng runner bắt buộc PostgreSQL; không pytest trần. Không model, embedding, Mailer hoặc MediaStore thật, không Cloudinary/replay có tiền.

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w09-required-final1-20261025 --junitxml=report/w09-required-fixes-2026-10-25/full.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=junit --outputFile=../../../report/w09-required-fixes-2026-10-25/react-final.xml
npm.cmd --prefix src/web/frontend run build
```

`run_full_gate.py` ghi main/commit/lệnh và SHA của toàn bộ source/script trước/sau; sao lưu tệp HTTP W-06/W-14 do test tự sinh vào phạm vi W-09 trước phục hồi byte cũ. SQL của W-15/W-25 sinh vào tên lượt riêng để không ghi đè hai thư mục `sql/latest/` đang giữ làm bằng chứng cũ.

`fixture-verification.json` đối chiếu lại **3.144 cặp tệp snapshot/worktree**, kiểm manifest SHA và không liên kết, không ghi dữ liệu. Loại đúng một learner store CLI `artifacts/phase_b/doc-1-rebuild-20261020.json` theo allowlist của `copy_w06_fixtures.py`; store này không có trong worktree và không được nhập PostgreSQL. Phép kiểm đầu tiên quá rộng đã dừng tại tệp CLI vắng mặt; đã đính chính nhận xét nhầm “khác hash”, không chép bù/ghi đè hoặc đổi dữ liệu để làm xanh.

Browser mới giữ toàn bộ kiểm responsive 390/768/1280 sáng/tối/reduced-motion và kiểm quyền/lịch sử/artifact trước. Bổ sung giữ phản hồi **usage thật đã lấy qua HTTP** bằng network gate phía browser; người học gửi hai câu liên tiếp, xác nhận hai POST với hai client_turn_id, câu hỏi nguyên vẹn, ô nhập vẫn khoá khi usage cũ trả về giữa stream mới, và SQL tăng đúng hai lượt. Đây là cố ý trễ mạng, không mock kết quả câu trả lời/DB. Tool thường được kiểm trên trang lộ trình không gửi focus, cache fixture trong DB UUID riêng được làm rỗng trước yêu cầu; SQL/cache và số gọi fake bài giảng xác nhận sinh đúng một lần.

React toàn bộ: **203 đạt**, build native 0; không skip hoặc nới timeout để nhận bản vá. Browser đầy đủ `browser-required-final1` trên `0ba4ac8`, source sạch: **12 cấu hình, 102 ảnh, 386 bản ghi HTTP/SSE, 46 lượt Axe** không violation; 0 page error, 0 console error ngoài dự kiến. 97 console error là CSP do công cụ Axe/HTTP 401–404 của ca khách và thu hồi quyền; giữ log gốc. Axe menu nổi giữ phạm vi riêng, không ghi mọi ảnh đều đã Axe; JSON ghi scope từng lượt và các phép đo tương phản bổ sung.

`browser-summary.json` có SQL qua connection độc lập: ca R-W09-1 tăng số lượt lưu **24 → 26**, nhận đúng hai POST/ID khác nhau và nguyên câu hỏi. Ca R-W09-2 từ cache bài giảng rỗng **0 → 1**, số gọi fake bài giảng **1 → 2**, nhận thẻ mở bài đúng node. Các ca retry cùng ID, disconnect/history, privacy, thu hồi membership vẫn chạy trong harness cũ. DB UUID được đóng/xoá và thread server dừng, native 0; WinError 10054/cảnh báo shutdown của lượt cố ý ngắt kết nối được giữ trong log, không giấu hoặc ghi thành lỗi giao diện.

Runtime tổng hợp 32 lượt lưu, 27 phiên, một tài liệu và một quiz attempt, owner đúng learner thử. Có 41 lời gọi provider **giả**, chi phí thật **0 USD**. Khoản 1 USD trong ledger là fixture hạn mức dựng sẵn, không phải lời gọi trả tiền.

Ảnh/video:

- [Câu thứ hai đang stream khi usage cũ đã về](w09-evidence/browser-required-final1/usage-pending-next-question-1280-dark-reduced.png).
- [Hai câu đã hoàn tất](w09-evidence/browser-required-final1/usage-race-completed-1280-dark-reduced.png).
- [Tool thường sinh bài chưa cache và hiện thẻ mở đúng bài](w09-evidence/browser-required-final1/ordinary-lecture-generated-1280-dark-reduced.png).
- [Sáng 1280](w09-evidence/browser-required-final1/lesson-current-1280-light.png) · [390 sáng](w09-evidence/browser-required-final1/conversation-options-390-light.png) · [768 tối](w09-evidence/browser-required-final1/lesson-768-dark.png).
- [Video người học](w09-evidence/browser-required-final1/learner.webm).

Đã quan sát trực tiếp ảnh cuộc trò chuyện 390 sáng, hai ca mới 1280 tối và bố cục chuẩn thừa hưởng W-09; không đổi giao diện trong đợt vá logic này. Giữ design-taste-frontend/app screens, token/font/logo và reduced-motion đã được kiểm. W-10 chỉ bắt đầu sau khi điều phối nghiệm thu W-09.

Taste inspector không có FAIL; hai WARN kế thừa là generic font `math` của MathML/KaTeX và phần bài đọc dài nằm dưới fold. Không thay renderer/font hoặc ép toàn bài giảng vào một màn để xoá cảnh báo của công cụ.

## Cổng cuối và trạng thái bàn giao

| Cổng trên `0ba4ac8` | Kết quả |
| --- | --- |
| Toàn repo qua `scripts/w05_run_tests.py`, PostgreSQL bắt buộc | **2.707 đạt**, 1 Cloudinary skip, 1 replay xfail có sẵn; 0 fail/error, 8 warning, native 0; 703,69 s |
| React toàn bộ | **203 đạt**, native 0 |
| Build | native 0 |
| Browser/HTTP/PostgreSQL mới | native 0; 12 cấu hình, 102 ảnh/46 Axe, SQL độc lập |

`full-exit.json`/`gate-source.json` ghi lệnh, main `6249dab`, source commit, native exit và SHA-256 các tệp được theo dõi dưới `src/`, `scripts/` trước/sau; tất cả giữ nguyên. Lượt main mới nhất trước cổng đã nhận bằng merge, sau cổng main vẫn `6249dab`. Bản commit hồ sơ sau đó không đổi source/script đã kiểm. Không gán cổng lịch sử 2.622 Python hoặc 198 React thành cổng mới.

Sau cổng, đã lưu bản sinh mới và phục hồi sạch ba tệp HTTP W-06/W-14, thêm năm tệp SQL W-14: hash/bản trước/bản sau trong `generated-contracts.json`, `generated-w14-sql.json`. 43 JSON SQL W-15/W-25 được chép độc lập/hash vào `generated-sql/` của W-09; bản local tên lượt riêng vẫn giữ nguyên ở thư mục gốc. `legacy-sql-preservation.json` xác nhận các tệp `sql/latest/` cũ vẫn khớp toàn bộ hash của bằng chứng trước. Không đưa đường dẫn vé khác vào commit này.

Log/XML gốc được giữ ZIP kèm manifest SHA trước khi xuất bản UTF-8/LF và bỏ dấu cách cuối dòng cho Git; không thay assertion/kết quả JUnit/native exit. Manifest bằng chứng ghi ảnh, video, HTTP/SQL và log mới; hồ sơ RED/setup lỗi lịch sử được giữ và phân biệt như trên.

Đã tự soát phạm vi và tính đúng, giữ quyền/giới hạn chi tại server, không thêm package hoặc bảng. Hai Required đã được vá và kiểm local; **chờ điều phối soát/ghép W-09**, không tự đóng vé hoặc làm W-10 trước mốc đó. W-10 đã đủ SA-67/68; phần thư viện chỉ đọc/preview W-09 được giữ để tái dùng sau nghiệm thu.
