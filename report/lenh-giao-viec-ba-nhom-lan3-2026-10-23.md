# Lời giao ba nhóm sau nghiệm thu lần 3 — 2026-10-23

[Biên bản và bằng chứng](dieu-phoi-nghiem-thu-ba-nhom-lan3-2026-10-23.md). Chủ dự án chuyển riêng từng phần; điều phối chưa gửi phiên bên ngoài.

## Nhóm web — sửa hai lỗi W-08 trước, rồi W-09

> Tiếp `tmp/w08-lecture`, nhánh `work/w08-lecture`, nhận main mới nhất. Mốc bàn giao `89122f6` chưa được ghép.
> Điều phối đã kiểm độc lập 2.385 Python/158 React/build xanh, 12 cấu hình browser/101 ảnh/17 Axe; hồ sơ nguồn/hashes/mutation khớp.
> Không làm lại phần quyền/gateway/Markdown/media đã đạt. Hai Required còn lại trong `Learning.tsx`:
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
> Sau W-08 đạt: W-09 theo ADR0026/answer-3, đọc `doc/tro-ly-3-spec.md`. SA-66 đang ở làn Claude; chuẩn bị bằng fake hợp đồng mới được,
> cổng cuối phải nhận main đã ghép SA-66. answer_md/Markdown/LaTeX/sources/delta; focus body_md lecture-3 cache-only, không sinh khi miss;
> giữ session/quyền/client_turn_id/graph_cards/artifacts. Validation riêng admin, UI tỷ lệ used_ratio/limited/resets_at,
> trần học 1 USD/ngày theo hợp đồng, 10 lượt/phút riêng; không bịa số lượt/ngày hoặc lộ tool arguments.
> Giữ Vertex và mọi test 0 USD. W-10 sau W-09, nhận spec/mốc SA-67/68 thật khi có, không tự chốt hợp đồng tương lai.

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

## Nhóm thiết kế — giữ sửa đã đạt, hoàn thiện W-24

> Tiếp `tmp/w24-figma-evidence`, nhánh `work/w24-figma-evidence`; `f292f18` chưa được ghép.
> Điều phối đóng lỗi mã Variables báo lỗi/alpha và chat bịa trần/raw tools; xác nhận empty chat/pending invitation/section anchors mới.
> Không làm lại những phần này. Đã kiểm 49 test trên worktree qua runner, VM 9 nhánh, browser 12 cấu hình.
>
> Phần còn lại:
> 1. W-08 local phải dựng được công thức mẫu; hiện 0 .katex và LaTeX hiện thô. Khối chờ dùng nhân vật 96px và ảnh tĩnh khi reduced-motion,
>    không claim spinner96 khi CSS là20px. Mọi lỗi chưa có chữ có message/Thử lại, bỏ nhánh “không thể phục hồi” khôngretry;
>    lỗi đuôi giữ chữ/cat_ngan, không hứa hành động tải bản đủ ngoài hợp đồng. Giữ đáp án gập và nguồn đúng trang; đây là preview thiết kế, không giao viết lại React.
> 2. Sửa report138/152: #text-tool-action và #btn-delete-course không tồn tại; nút thật #btn-delete-course-permanent.
>    Bảng theo từng trạng thái có link/node/minh chứng thật hoặc ghi thiếu; sửa claim 100%, KaTeX/96px cho đúng.
>    W-09 KaTeX/answer-3 ghi rõ phạm vi chuẩn bị nếu chưa có minh chứng; cú pháp $ của LaTeX không phải tiền USD trên UI.
> 3. Đưa kiểm đầu ra plugin và lỗi create/set mode vào kiểm hồi quy dùng output thực. Mã hiện đã báo lỗi đúng;
>    guard text/toy vẫn lọt khi bỏ accounting create, nên không lấy số 49 hoặc 13 mutation làm bằng chứng bảo vệ mọi nhánh.
> 4. Hoàn thiện file Figma UVhhlZnqdpV0JDcAHwJczo: Variables Light/Dark đúng token, native components/variants/bindings,
>    prototype reactions/starting points và đủ bốn video Present. Đọc Cloud mới ở đợt này vẫn0Variables/components/bindings/reactions/startingpoints.
>    Nộp export/receipt/node IDs và video chạy thật; HTML/plugin source không thay bàn giao Cloud.
>
> W-22/W-24 vẫn mở; W-23 chưa thể đối chiếu trọn bộ. Logo Artboard9–28, Be Vietnam Pro/token/motion theo spec,
> được dùng taste-skill đã nạp. Giữ 390/768/1280 sáng/tối/reduced-motion, 44px, kiểm thị giác, không bịa nghiệp vụ.

## Luật chung

> Root luôn main; mỗi vé ở worktree một cấp tmp/<tên>, chỉ commit đúng đường dẫn vé, không tự sửa task/kế hoạch/handoff/ghép main.
> Không dọn worktree/snapshot/ZIP/artifact, không links, không đụng tmp/t01a-clean-ff797eb hoặc live.json/tập giữ lại.
> Dữ liệu chỉ chép allowlist/SHA; không commit .env/PDF/artifact. Python qua scripts/w05_run_tests.py, PostgreSQL bắt buộc;
> focused unit-only cần nạp backend conftest định nghĩa --require-postgres (xem lệnh design-focused2 trong biên bản).
> Chỉ một cổng toàn repo PostgreSQL cùng lúc. Main đổi thì nhận main/kiểm lại trước ghép; không giảm guard/skip/timeout để xanh.
> Tất cả công việc kiểm hiện tại 0 USD; lượt thật có tiền cần phê duyệt mới cho đúng cuốn/lượt/trần. Giữ Vertex tới khi chủ dự án yêu cầu đổi.
