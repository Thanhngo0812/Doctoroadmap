# Lời giao ba nhóm sau nghiệm thu lần 3 — 2026-10-23

**Đã chỉnh ngày 2026-10-24 theo chủ dự án và bàn giao mới nhất của Claude `2a39c32`.** SA-66 và SA-69 đều đã ghép, W-09 đã được gỡ chặn;
nhóm thiết kế được nhận mốc giao diện web có ghi chú, bỏ yêu cầu Cloud Figma. [Quyết định và phạm vi](dieu-chinh-giao-viec-web-thiet-ke-2026-10-24.md).

[Biên bản và bằng chứng](dieu-phoi-nghiem-thu-ba-nhom-lan3-2026-10-23.md). Chủ dự án chuyển riêng từng phần; điều phối chưa gửi phiên bên ngoài.

## Nhóm web — sửa hai lỗi W-08 trước, rồi W-09

> Tiếp `tmp/w08-lecture`, nhánh `work/w08-lecture`, nhận main mới nhất. Mốc bàn giao `89122f6` chưa được ghép.
> Điều phối đã kiểm độc lập 2.385 Python/158 React/build xanh, 12 cấu hình browser/101 ảnh/17 Axe; hồ sơ nguồn/hashes/mutation khớp.
> Không làm lại phần quyền/gateway/Markdown/media đã đạt. Hai Required còn lại trong `Learning.tsx`:
> Dùng HTML/CSS/token do nhóm thiết kế bàn giao trong `design/preview/` để tham khảo khi triển khai React;
> bản mới trên nhánh W-24 có thể đọc tại `tmp/w24-figma-evidence/design/preview/`. Chọn mẫu đúng spec, không nhập cả nhánh chưa duyệt hoặc chép đè mã đang làm.
>
> 1. Bài A đang mở, đánh dấu B trong sidebar: checkbox/tiến độ đổi nhưng nhãn B ở Cần biết trước/Tiếp theo vẫn đọc snapshot cũ.
>    Dùng tiến độ hiện tại cho mọi nhãn, kiểm lưu thành công và rollback; không gọi sinh lại bài chỉ để đổi nhãn.
> 2. Bộ lọc đáp án khi stream chỉ nhận `### Tự kiểm tra`, nhưng core nhận `##`, `####`, thụt đầu và dấu `:`.
>    Bốn dạng hợp lệ làm lộ đáp án trước final. Đồng bộ quy tắc che/gập khi stream, giữ đúng trường hợp final không có self_check.
>
> Helper và JUnit tại `report/coord-ba-nhom-lan3-evidence-2026-10-23/web-review/Learning.review-repro.test.tsx` và `runs/repro.xml`:
> 6 assertion fail/11 control pass, không setup error. Nhận ca hồi quy vào suite của vé; ghi RED→GREEN trên đúng mã, không giảm assertion/timeout.
> Chạy lại cổng qua runner và browser sau sửa, ghi commit/SHA/native/SQL, giữ các lượt cũ. Chờ điều phối nghiệm thu/ghép, không tự ghép main.
>
> Sau W-08 đạt: W-09 theo ADR0026/answer-3, đọc `doc/tro-ly-3-spec.md`, đặc biệt mục 8, và vé SA-69.
> **SA-66 đã ghép `ba4350f`, SA-69 đã ghép `973fa99`; Claude xác nhận W-09 có thể nhận answer-3 từ main.**
> Điểm chờ cũ do scope "module 4"/tên module đã được sửa ở lõi. Nhận main mới, kiểm công cụ quiz/tài liệu qua đường web bằng fake hợp đồng đúng;
> không tự dịch/vá scope ở web. Thẻ quiz/tài liệu lấy từ sự kiện `artifact`; link mô hình tự bịa dạng `quiz:…` trong chữ không biến thành link bấm được.
> answer_md/Markdown/LaTeX/sources/delta; focus body_md lecture-3 cache-only, không sinh khi miss;
> giữ session/quyền/client_turn_id/graph_cards/artifacts. Validation riêng admin, UI tỷ lệ used_ratio/limited/resets_at,
> trần học 1 USD/ngày theo hợp đồng, 10 lượt/phút riêng; không bịa số lượt/ngày hoặc lộ tool arguments.
> **Báo trước SA-70:** lõi sẽ ngừng phát delta từ tiêu đề tự kiểm tra bằng đúng bộ tách của core; tới lúc SA-70 ghép vẫn sửa/giữ hồi quy R-W08-2 phía web.
> Khi nhận SA-70 kiểm lại cả HTTP và React, không tạo hai bộ cắt lệch nhau. SA-70 do Claude phụ trách, nhóm web không sửa lõi.
> Giữ Vertex và mọi test 0 USD. W-10 sau W-09: spec document-3/quiz-3 và vé SA-67/68 đã có; đọc bản mới,
> chờ mốc triển khai được Claude nghiệm thu/ghép trước tích hợp cuối, không dùng hợp đồng cũ thay cho bản mới.

## Nhóm lõi — W-15 tiếp ngay, đã có port

> Tiếp `tmp/w15-real-build`, nhánh `work/w15-real-build`; nhận main mới nhất đã có SA-62 `9ac2a85`, SA-64 `1d91b0b`, SA-65 `4a4b957`.
> Hồ sơ `6bcbae6` đúng phạm vi pre-port, được ghi nhận; chưa có phần kiểm sau port/dry-run. Không tiếp tục ghi đang chờ chọn người Pha A/ghép SA-62.
> Ca dương default factory/PG tại `ce5f581` đã làm và ghép; giữ cả ca âm thiếu port, không làm lại hoặc dùng chúng thay kiểm toàn chuỗi.
>
> 1. DocumentPipeline thật + model/embedding fake + PG xuyên connection: tên module/A12/concept-index dùng cùng store;
>    chặn ADC/provider/JSON/SQLite fallback. Giữ chuỗi đọc nhẹ → kiểm chữ → label-roles → A3/A3′ → A4 vi/coverage none → roadmap → learning_prep.
> 2. Kiểm usage callback/receipt đúng một lần, thiếu usage có giải thích, huỷ/lease, version/identity/cache.
>    Meter delta là chi build duy nhất; counted_in=build chỉ trace, không cộng raw extra lần hai. Không sửa budget.py để biến purpose dựng thành hạn mức học.
> 3. Kiểm doc-6 v29/alias khác u-hash, parser/fingerprint/dependency; chỉ báo số hit/miss/unknown, không in cache hay đổi ID/version để lách.
>    SA-65 có dữ liệu ảnh mới thì nhận manifest/SHA riêng; không ghi đè snapshot/bằng chứng cũ. Artifact Pha A/ảnh trang vẫn là tệp, không chuyển vào DB.
> 4. Sau các kiểm trên mới dry-run thật nội bộ ở bản sao có SHA, collector web, allow_spend=False và guard mạng;
>    không queue/course-ready. Bảng từng bước gồm cache/gọi sinh/embedding/USD/phút/embedding wait, số chưa đo ghi chưa biết.
>    Trình đúng cuốn/hash/lượt/trần có căn cứ; chỉ chủ dự án duyệt mới mở có tiền. Ngân sách phục hồi/SA cũ không áp dụng.
>
> Bàn giao rõ milestone nào đã chạy; toàn W-15 chưa đóng khi chỉ có adapter hoặc audit metadata. Giữ Vertex, fake provider và chi mới 0 USD.
> Theo dõi SA-70 mục 11.7: lỗi chụp ảnh trang sẽ được ghi trong chi tiết bước, không làm hỏng cả lần dựng. Chỉ kiểm hành vi mới sau khi nhận mốc đã ghép;
> không sửa composition lõi thuộc làn Claude hoặc nhận spec mới là mã đã có.

## Nhóm thiết kế — nhận mốc web, hỗ trợ hoàn thiện giao diện thực tế

> Theo quyết định chủ dự án 2026-10-24, **nhận đạt có ghi chú phần thiết kế web đã bàn giao**: token, bố cục, thương hiệu, responsive và usage/chat đã kiểm.
> W-22/W-24 không còn bị giữ bởi Cloud Figma. Không giao thêm Variables export, native components/bindings/reactions trên Cloud hoặc video Present Figma.
> `f292f18` vẫn ở nhánh riêng, chưa ghép; phán xét phạm vi thiết kế không thay cổng kiểm mã trước khi ghép nhánh.
> Giữ các phần đã đạt, không làm lại plugin hay bộ token. Ưu tiên giúp nhóm React hoàn thiện giao diện web theo spec và bằng chứng trình duyệt.
> Tiếp tục bàn giao mẫu HTML/CSS/token cho nhóm web tham khảo; ghi rõ mẫu nào đã nhận, mẫu nào cần cập nhật.
> Nhóm web chuyển mẫu sang React, hai nhóm cùng soát kết quả; không yêu cầu nhóm web tự thiết kế lại những mẫu đã phù hợp.
>
> Việc tiếp theo:
> 1. Phối hợp soát React W-08 ở 390/768/1280 sáng/tối và giảm chuyển động: chữ/công thức đọc rõ, nguồn đúng trang,
>    nhân vật chờ đúng cỡ, message/Thử lại khi chưa có chữ, đáp án gập và giữ chữ sau lỗi đuôi. Hai lỗi W-08 điều phối đã tái hiện vẫn do nhóm web sửa.
> 2. Preview HTML chỉ là tài liệu hỗ trợ. Các chỗ LaTeX thô/spinner20/fatal khôngretry chưa sửa phải ghi rõ là bản cũ,
>    hoặc cập nhật khi dùng lại làm mẫu cho React; không bắt làm lại toàn bộ preview để đóng mốc thiết kế đã được nhận.
> 3. Sửa hai anchor sai và claim KaTeX/96px/100% trong báo cáo nếu tiếp tục dùng tài liệu đó. Trỏ ảnh/đường dẫn màn web thực tế;
>    không cần node Figma. Cú pháp $ của LaTeX không phải tiền USD trên UI.
> 4. Chuẩn bị và soát giao diện W-09 theo answer-3 bằng fake; SA-69 đã ghép, nhóm web nhận main để tích hợp sau W-08.
>    Tiếp đó hỗ trợ W-23 đối chiếu React với spec/token,
>    ghi nhận lỗi thị giác/hiệu ứng, ảnh và video trình duyệt khi cần chứng minh tương tác. Không giao tự sửa các tệp React nhóm web đang làm;
>    nếu nhận cài giao diện thì tách lát và worktree riêng được điều phối phân công.
>
> W-22/W-24 đạt có ghi chú trong phạm vi web đã kiểm. W-23 không chờ Cloud, nhưng nghiệm thu toàn bộ vẫn chờ các màn W-08/W-09/W-10 hoàn thành.
> Logo Artboard 9–28, Be Vietnam Pro/token/motion theo spec, được dùng taste-skill đã nạp. Giữ 390/768/1280 sáng/tối/reduced-motion,
> vùng bấm 44px và kiểm thị giác; không bịa nghiệp vụ. Các màn tương lai được nhận theo vé tương ứng khi có giao diện chạy thật.

## Luật chung

> Root luôn main; mỗi vé ở worktree một cấp tmp/<tên>, chỉ commit đúng đường dẫn vé, không tự sửa task/kế hoạch/handoff/ghép main.
> Không dọn worktree/snapshot/ZIP/artifact, không links, không đụng tmp/t01a-clean-ff797eb hoặc live.json/tập giữ lại.
> Dữ liệu chỉ chép allowlist/SHA; không commit .env/PDF/artifact. Python qua scripts/w05_run_tests.py, PostgreSQL bắt buộc;
> focused unit-only cần nạp backend conftest định nghĩa --require-postgres (xem lệnh design-focused2 trong biên bản).
> Chỉ một cổng toàn repo PostgreSQL cùng lúc. Main đổi thì nhận main/kiểm lại trước ghép; không giảm guard/skip/timeout để xanh.
> Tất cả công việc kiểm hiện tại 0 USD; lượt thật có tiền cần phê duyệt mới cho đúng cuốn/lượt/trần. Giữ Vertex tới khi chủ dự án yêu cầu đổi.
