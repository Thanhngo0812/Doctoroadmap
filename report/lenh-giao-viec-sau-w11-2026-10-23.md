# Lời giao ba nhóm sau soát W-11/W-15/W-24 — 2026-10-23

Chủ dự án có thể gửi riêng từng đoạn dưới đây. [Báo cáo và mốc nghiệm thu](dieu-phoi-nghiem-thu-w11-w15-w24-va-ke-hoach-2026-10-23.md) là căn cứ.
Không nhận lời “hoàn thành” thay cổng nghiệm thu; không yêu cầu làm lại phần đã được chứng minh đạt.

## 1. Gửi nhóm web — sửa W-11 trước, rồi W-08

> Tiếp W-11 trong `tmp/w11-share-links`, nhánh `work/w11-share-links`. Mốc đã soát `85397092` còn đúng một Required:
> link mời → đăng nhập → chuyển sang đăng ký hoặc ngược lại làm mất `next`, xác thực xong về `/khoa-hoc`.
>
> Đọc `src/web/frontend/src/Auth.tsx:258–263,319,334`. Giữ đích nội bộ đã sanitize trên cả link header/footer và `navigate` của view transition;
> giữ chặn open redirect. Test tái hiện sẵn ở nhánh `review/w11-auth-repro-20261023`, commit `3f3e923`, file `src/web/frontend/src/W11AuthReturn.repro.test.tsx`.
> Có thể lấy riêng test đó theo quy trình; đừng merge cả nhánh review/chép bằng chứng thành mã đã sửa.
> Tám ca hai chiều × header/footer × có/không transition hiện đỏ đúng đích; hai control trực tiếp xanh. Chứng minh RED→GREEN và kiểm thêm `next` nguy hiểm.
>
> Nhận main mới, giữ `w11_0007 → w14_0006`, chạy toàn cổng qua `scripts/w05_run_tests.py`, React/build và browser PostgreSQL:
> vào link mời, đổi form, xác thực, quay về đúng `/join/<token>` và tham gia. Kiểm cả trình duyệt giảm chuyển động và đường transition thường.
> Không hồi quy URL chỉ hiện một lần, list chỉ đuôi 6 ký tự, join transaction/lượt/cap 200, revoke/remove/leave hay dữ liệu học riêng.
> Giữ guard mutation đã có; log/native exit/JUnit phải ghim đúng commit. Sửa phạm vi nhỏ, không viết lại backend đã đạt review.
>
> Bàn giao bản vá và báo cáo cập nhật, chờ điều phối soát/ghép W-11 rồi làm W-08 theo vé.
> W-08 đã đủ SA-53: trang học/gateway/HTTP/SSE/React, stream sau cổng, không hiện bản lùi, trạng thái fatal có lối ra,
> prerequisite gập/mở, đọc trang nguồn, quyền media và PostgreSQL. Dùng spec/token đã được nhận trên main; preview W-24 mới chưa phải chuẩn đã nghiệm thu.
> Đẹp, thống nhất và hiệu ứng đúng token; cho phép dùng taste-skill đã nạp. Kiểm 390/768/1280 sáng/tối, reduced-motion thật, vùng bấm 44×44 px, ảnh/video/Axe phù hợp.
>
> Khi tới W-09: SA-56/57 (`04c3efa`) và SA-58 (`e2cfbac`) đã vào main. Nối wrapper `get_lecture(concept, **kwargs)` chuyển `cache_only`
> xuống `LectureUseCase.make`, sửa chỗ `lecture.get` sai chữ ký trong composition test web. Search dùng enum lõi; không vá chuỗi ở gateway.
> Replay cũ trước SA-58 không khớp tool description; dùng fake/fixture mới ở 0 USD, không chạy model để tạo lại.
> Giữ Vertex; không tự chuyển transport hoặc sửa SA-61.

## 2. Gửi nhóm lõi — W-15 chỉ xong tầng adapter, cần chốt port

> Đọc kết luận mốc `a8bb295`/tích hợp `eea5472` trong báo cáo điều phối. Giữ `tmp/w15-real-build`, nhánh `work/w15-real-build`, nhận main mới.
> Adapter/test 0 USD đã được review; toàn W-15 vẫn mở. Không tuyên bố toàn DocumentPipeline thật, doc-6 cache qua web hoặc dry-run thật đã đạt.
>
> Hoàn thiện hồ sơ port đã đề nghị: `DocumentPipeline(..., phase_b_store=None)` và `PhaseBRuntime(..., store=None)` chọn store trước mọi runtime con,
> session/spend guard/name/concept-index; không tạo JSON/SQLite rồi gán lại. Cần một nguồn tổng usage build, tránh cộng trùng trace purpose con với meter/receipt.
> Yêu cầu này đã ghi mục 8 bàn giao cho Claude/phiên pha A. Chưa có chốt quyền/phạm vi thì **chưa sửa tệp Pha A**; đề nghị chủ dự án chuyển nội dung này cho Claude.
>
> Trong lúc chờ, kiểm identity/cache trên bản sao manifest: doc-6 v29 không tự khớp ID hash PDF của web/pipeline version mới.
> Chỉ báo số hit/miss/unknown và lý do fingerprint/version, không in nội dung learner cache, không mở live.json/tập giữ lại.
> Ghim SHA ứng viên cuốn mới, kiểm alias có thể làm cold-cache giả; chưa tự dựng cuốn đó.
>
> Khi đã có port trên main: test xuyên PostgreSQL bằng engine/kết nối độc lập, chặn constructor JSON/SQLite/ADC/provider trong test,
> kiểm session/spend/name/concept-index, callback checkpoint, receipt một lần, huỷ/lease/usage thiếu và nguồn tính chi duy nhất.
> Kiểm lại helper version có Git HEAD và baseline, không hứa cache reuse từ một commit khác khi chưa đo.
> Sau đó dry-run thật nội bộ với collector/recorder web, bản sao artifact, `allow_spend=False` và guard mạng; không đưa dry-run vào queue/course ready.
> Lập bảng từng bước: cache hit/miss/unknown, gọi sinh/embedding, USD/phút, phần chờ embedding và trần đề nghị có căn cứ.
> **Chỉ khi chủ dự án duyệt đúng cuốn/lượt/trần mới chạy có tiền**; phê duyệt khôi phục/SA trước không áp dụng. Chưa có cờ mở chi trong adapter hiện tại.
> Giữ chuỗi đọc nhẹ → kiểm chữ → label-roles → A3/A3′ → A4 vi/coverage none → roadmap → a12/concept-index/formulas.
>
> Giữ Vertex theo quyết định mới nhất; đừng tự chuyển Developer API vào ngày dự kiến demo. SA-61 phải được Claude nghiệm thu/ghép trước lần đổi được chủ dự án yêu cầu.
> Nộp báo cáo có đúng commit/lệnh/native exit/SQL độc lập, các số chưa đo ghi chưa biết. Không xin đóng W-15 bằng test pipeline giả.

## 3. Gửi nhóm thiết kế — sửa năm Required W-24 trước khi mở thêm màn

> Tiếp `tmp/w24-figma-evidence`, nhánh `work/w24-figma-evidence`, mốc mới đã soát `16e95c1` chưa đạt.
> Phần sửa báo cáo `fe8ccf3` đúng; không làm lại OS reduced-motion/token raw/CSS đã đạt tại `78fb774`.
>
> 1. W-11: danh sách link chỉ đuôi 6 ký tự. URL đầy đủ và copy chỉ ở vùng kết quả tạo mới một lần; không copy lại từ list.
> 2. Sửa lời hứa sai: xoá khoá giữ dữ liệu học riêng/artifact dùng chung theo spec; huỷ sau confirm không hoàn lượt, usage đã phát sinh được giữ,
>    worker dừng ở ranh giới bước. Không hứa “không trừ lượt”/“đã giải phóng toàn bộ tài nguyên” cho mọi ca huỷ/lỗi.
> 3. Plugin sinh đúng 37 biến × 2 mode: đủ `radius/radius-xl`, `motion/motion-base`, radius-lg 14 và dark tint alpha 0.14;
>    bỏ tên thay thế sai, không chỉ đếm đủ 37. So trực tiếp output của plugin với hợp đồng JSON/CSS, bắt lỗi tạo mode/variable và báo đối tượng tạo được.
> 4. Sửa năm nút 36 px và chữ tràn ở 390 px của W-08/W-11, tối thiểu 44×44 px, bố cục chữ/nút phù hợp; kiểm cả 390/768/1280 sáng/tối.
> 5. Checklist tách đúng phần còn thiếu: fatal lecture với lối ra, viewer ảnh trang/điều khiển, báo lỗi nội dung, pre-gate/streaming.
>    Không dùng source excerpt/xoá khoá thay màn khác; bỏ lời hứa “OCR y khoa” chưa có spec.
>
> Bằng chứng điều phối có 18 cấu hình browser và diagnostic plugin hai nhánh mode. Script diagnostic exit 0 không có nghĩa parity đạt.
> Sau sửa local, chạy/đồng bộ đúng lên Figma file `UVhhlZnqdpV0JDcAHwJczo`: đọc lại hiện vẫn 0 Variables/0 native components/0 reactions/0 flow starting points.
> Tạo/bind Variables, native components/variants và bốn prototype thực; xuất receipt tên/kiểu/mode/giá trị/node/binding/reaction thực cùng video bấm Present.
> Plugin source hoặc HTML 4/4 không thay bằng chứng Cloud. Ưu tiên W-11/W-08, rồi chat/quiz; phần chưa có ghi thiếu.
> Tiếp cùng W-24, W-22/W-23 còn mở; không công bố preview mới là nguồn chuẩn React trước khi điều phối nhận đúng mốc.

## 4. Luật chung

- Mọi phiên vé ở worktree một cấp `tmp/<tên>`, thư mục chung luôn main. Không tự ghép/push main; chỉ commit đúng đường dẫn của vé.
- Chạy test Python qua runner `scripts/w05_run_tests.py`; không pytest trần, không skip PG, không giảm assert để xanh. Cổng toàn repo PostgreSQL chạy lần lượt.
- Main đổi sau gate thì nhận main và kiểm lại. Bằng chứng phải gắn đúng commit, native exit/JUnit/SHA, giữ cả lượt đỏ và nguyên nhân.
- Chỉ chép dữ liệu theo allowlist/SHA, không junction/symlink/hardlink; không dọn worktree/snapshot/ZIP/artifact, không đụng `tmp/t01a-clean-ff797eb`.
- Không mở tập giữ lại hoặc `artifacts/phase_b/live.json`, không commit `.env`/PDF/`document-data`/`artifacts`/pytest basetemp.
- Không gọi model/embedding/mail/media thật trong lượt 0 USD. Transport giữ Vertex; chỉ chủ dự án duyệt tiền/chuyển transport.
- Dùng skill phù hợp; giao diện và hiệu ứng phải chỉn chu theo spec, có giảm chuyển động và kiểm browser thật. Không nhận tự báo hoàn thành thay kiểm chứng.
