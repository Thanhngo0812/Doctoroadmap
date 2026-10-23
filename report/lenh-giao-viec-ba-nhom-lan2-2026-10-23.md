# Lời giao ba nhóm sau nghiệm thu lần 2 — 2026-10-23

[Kết luận và đúng commit](dieu-phoi-nghiem-thu-ba-nhom-lan2-2026-10-23.md). Chủ dự án chuyển riêng từng đoạn; chưa gửi phiên bên ngoài.

## Nhóm web — W-08 theo lecture-3 mới nhất

> W-11 `253874bb` đã sửa Required giữ next, điều phối chốt cổng/ghép trong báo cáo. Chỉ bắt đầu W-08 từ main có mốc ghép được ghi tại đó.
> Tạo worktree một cấp `tmp/w08-lecture`, nhánh `work/w08-lecture`, giữ nguyên worktree W-11 và dữ liệu cũ.
>
> **Đọc cập nhật W-08, ADR 0025 và doc/bai-giang-3-spec.md trước khi cài.** Quyết định mới nhất lecture-3 thay lecture-2;
> SA-64 thay SA-63, Claude cài/ghép, không sửa lõi SA trong vé web. Body là body_md Markdown/LaTeX (KaTeX), sources/nhãn[Sx]/Trong sách,
> self_check có đáp án gập. Bỏ sections/bridge. Stream skeleton → delta{text} → final{lecture}/failure; chữ hiện ngay, không cổng hai ý.
> Validation chỉ cache/log admin, tuyệt đối không lộ JSON/SSE/tool cho người học.
> Trượt luật kiểm không làm bài lỗi hoặc có nhãn kiểm. Khi chưa có ý thì failure.message tiếng Việt và luôn nút Thử lại;
> sau delta đầu, lỗi đuôi giữ chữ đã gửi, ready + cat_ngan. Không dùng kiem_noi_dung/TTL 24 giờ từ hợp đồng cũ.
>
> Làm ngay khung trang học/gateway/HTTP/SSE, danh sách khái niệm, tiên quyết gập sẵn, next-up, progress theo người, source/media có kiểm quyền.
> Có thể dùng fake đúng hợp đồng mới trong lúc chờ SA-64; cổng tích hợp cuối phải nhận main đã ghép SA-64, không tự nhận core cũ là đạt hợp đồng mới.
> Kiểm delta đầu trước khi mô hình xong, giữ chữ sau lỗi đuôi, Markdown/LaTeX an toàn, nguồn đúng trang và nhãn lạ giữ nguyên,
> self_check gập/null, mọi failure có message/retry, cache validation không lọt phản hồi,
> một lần sinh chung/tách learner_status và SSE disconnect vẫn hoàn tất vào cache. Giữ zero external calls.
>
> UI đẹp/chỉn chu, đúng token/font/logo Artboard 9–28, được dùng taste-skill đã nạp. 390/768/1280 sáng/tối, vùng bấm 44×44 px,
> reduced-motion thật; ảnh/video/Axe và quan sát thị giác, không chỉ chụp ảnh. Preview W-24 mới chưa được nhận nguyên gói: bám spec/main đã duyệt.
> PostgreSQL bắt buộc, media/mailer/model/embedding giả, quyền người ngoài không miễn route. Test RED→GREEN, native exit và source SHA đúng mốc.
> Sau W-08 mới W-09 rồi W-10 nếu một phiên web. ADR 0026/SA-66 thay answer-2 bằng answer-3: answer_md Markdown/LaTeX/sources/delta,
> giữ graph_cards/artifacts/focus, đọc body_md lecture-3 cache-only không sinh bài. Cổng cuối W-09 chờ Claude ghép SA-66.
> Trần người học/ngày mới 1,00 USD theo quyết định; UI dùng used_ratio/limited/resets_at, không số lượt/ngày. Giữ quyền, phiên, client_turn_id và enum SA-58.
> Giữ Vertex; không tự chuyển API hoặc xin chi cho test web.
> Trước W-10 đọc kế hoạch Pha B `f346e71`: SA-67 tài liệu/SA-68 quiz là đợt nâng tiếp theo; nhận spec/mốc thật khi có, không tự chốt hợp đồng tương lai.

## Nhóm lõi — W-15 sau SA-62, chưa chạy có tiền

> Mốc `6627c00` đã có trace accounting và hai test thiếu port tương thích; không làm lại adapter đã đạt.
> Claude đã nhận/chốt người làm port bằng **SA-62**, không còn chờ phiên Pha A quyết ai sửa. Giữ hai tệp composition cho làn Claude.
> SA-62 `266dbdc` chưa được gọi là main cho tới khi Claude ghép. Sau điều phối ghép phần web, nhận main đó và phối hợp qua handoff cho Claude nhận vào nhánh SA-62.
>
> Khi SA-62 vào main: thêm ca dương default DocumentPipeline/worker có port trước provider, giữ ca âm PipelineWithoutStorePort;
> kiểm pipeline thật với mô hình/embedding fake, chặn ADC/provider và constructor JSON/SQLite, PG xuyên kết nối độc lập.
> Kiểm tên/cache/module_assignment/session/spend guard cùng store; callback/usage thiếu/receipt một lần/huỷ/lease và identity/pipeline-version.
> Meter delta là tổng build duy nhất. Trace counted_in=build giữ raw extra, typed tiền/token 0; raw báo cáo phải lọc, không cộng lần hai.
> DailySpendGuard Pha B không tính module_title/embedding của build; không diễn giải test purpose lecture thành guard build, không sửa budget.py để ép nghĩa.
>
> Artifact Pha A vẫn ở kho tệp. Không chuyển graph/chunks/manifest/index vào PostgreSQL, chỉ tiêm kho Pha B/sổ chi cho đường web.
> SA-65 do Claude lo ảnh trang mới/chụp bù; khi nhận dữ liệu mới cần manifest/SHA riêng và bản sao đã kiểm, không sửa đè snapshot hay bằng chứng lịch sử.
> Doc-6 v29/alias doc-6 khác ID hash PDF của web; kiểm identity/cache/fingerprint trên bản sao có SHA, chỉ báo số hit/miss/unknown và phạm vi kiểm.
> Chưa có cache hit được chứng minh thì không hứa dựng doc-6 miễn phí và không tự đổi ID/version để lách.
>
> Sau kiểm fake/PG: dry-run thật nội bộ với collector, bản sao artifact, allow_spend=False và guard mạng; không vào queue/course ready.
> Bảng từng bước gồm cache, gọi sinh/embedding, USD/phút/embedding wait, trần có căn cứ; số chưa đo ghi chưa biết.
> Chỉ chủ dự án duyệt đúng cuốn/lượt/trần mới mở có tiền. Giữ Vertex, chuỗi đọc nhẹ → kiểm chữ → label-roles → A3/A3′ → A4 vi/coverage none → roadmap → learning_prep.
> Báo rõ mốc chuẩn bị nào đã xong; chưa xin đóng toàn W-15 khi chưa chạy đủ tiêu chí thật.

## Nhóm thiết kế — W-24 còn ba nhóm sửa

> Giữ `tmp/w24-figma-evidence`, nhánh `work/w24-figma-evidence`. Cả `7a522e5` và `d72993e` chưa được ghép.
> Đã đóng qua kiểm độc lập: suffix/copybox, wording xoá/huỷ/quota, bỏ OCR, 37×2 token ở hai nhánh mode, 44 px/chữ tràn cũ.
> Không làm lại các điểm này. Có 45 test head/40 checkpoint, 18 cấu hình browser đạt hình học; còn ba Required:
>
> 1. Plugin không được nuốt lỗi Variables. Ép createVariable primary lỗi hiện chỉ 72/74 giá trị mà không báo.
>    Ghi attempted/created/failed theo tên/type/mode, phát hiện thiếu và cho người chạy biết; đừng chỉ log số frame/reaction.
>    Guard chạy output thực của block plugin: đổi alpha 0.14→0.99 phải đỏ (guard hiện vẫn xanh), và tạo lỗi phải được bắt bằng assertion độc lập.
> 2. W-09 bỏ trần bịa 30 lượt/ngày/còn 24. Dùng used_ratio/limited/resets_at của usage-1; 10 lượt/phút là tần suất riêng.
>    Tiến trình công cụ là lời người học hiểu, bỏ raw toolname/JSON arguments. Đồng bộ cả HTML lẫn plugin.
>    Khi cập nhật answer-3 theo ADR 0026, trần ngày mới là 1,00 USD, giao diện vẫn tỷ lệ/hết trần; Markdown/LaTeX và sources mở đúng trang.
> 3. Checklist: sửa anchor email/xoá khoá; pending invitation và phiên chat rỗng cần màn riêng hoặc ghi thiếu.
>    Viewer placeholder có controls chưa phải ảnh nguồn/thao tác hoạt động; ghi đúng phạm vi. Đồng bộ số 45/40 test với commit, không claim đủ mọi Required khi plugin còn lỗi.
>
> **Cập nhật mới nhất ADR 0025/SA-64**, được giao từ đợt này: W-08 chờ chữ đầu, body_md Markdown/LaTeX hiện theo delta,
> có Trong sách/sources/nhãn[Sx] mở đúng trang và self_check đáp án gập; bỏ sections/bridge/lecture-2, không nhãn validation.
> Lỗi chưa có chữ hiện message+Thử lại luôn; lỗi đuôi giữ chữ/cat_ngan. Đừng hoàn thiện thêm cổng hai ý/failed vì trượt kiểm theo lời giao cũ.
>
> Sau sửa local: hoàn thiện Variables/components/variants/bindings/reactions trên file Figma thật UVhhlZnqdpV0JDcAHwJczo và bốn video Present.
> Chưa có receipt/export/video mới thì ghi chưa xác minh; các số Cloud rỗng cũ phải có ngày, không giả thành số hiện tại.
> HTML/plugin source không thay Cloud. W-22/W-24/W-23 còn mở, tiếp cùng vé và bám spec; được dùng taste-skill để làm đẹp nhưng không bịa quy tắc nghiệp vụ.

## Luật chung

- Chỉ làm vé trong worktree một cấp `tmp/<tên>`, root luôn main; không tự ghép/push main, không sửa vé/kế hoạch/handoff.
- Chỉ commit đường dẫn của vé; giữ mọi worktree/snapshot/ZIP, không links và không đụng `tmp/t01a-clean-ff797eb`.
- Dữ liệu chỉ chép allowlist/đối chiếu SHA; không live.json/tập giữ lại, không commit .env/PDF/artifact/basetemp.
- Python qua scripts/w05_run_tests.py, PostgreSQL bắt buộc; cổng toàn repo chạy lần lượt. Main đổi thì nhận main/kiểm lại, không skip/giảm assertion.
- Mọi test lượt này 0 USD, fake/replay hợp đồng hiện tại; paid call và đổi Vertex cần đúng chỉ thị chủ dự án.
- Log/native exit/JUnit/SQL/ảnh/video gắn đúng commit, giữ lượt đỏ và nguyên nhân. Không lấy diagnostic exit0 hoặc tự báo hoàn tất thay nghiệm thu.
