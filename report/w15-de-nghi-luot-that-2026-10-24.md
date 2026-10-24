# W-15 — chuẩn bị lượt Vertex thật sau kiểm 0 USD — 2026-10-24

**Hiện hành sau hồ sơ tiếp quản `4038055`. Chưa chạy có tiền; W-15 chưa đóng.**
Nhánh `work/w15-real-build`, worktree `tmp/w15-real-build`; main đã nhận `604cab0`
có SA-69/SA-70. Root giữ main. Không sửa `src/doc2roadmap/`, không ghép/push main.

## Kết quả và điểm còn thiếu

Port PostgreSQL và adapter cũ đã đạt, giữ nguyên. Lượt này bổ sung cách operator chạy
một lần được duyệt, giới hạn chi và harness dùng đường HTTP upload/confirm/worker thật.
Không thêm cờ mở chi vào API/Settings hoặc UI. Worker thường vẫn `allow_spend=False`.
Mã tách thành `bf761fe` (tái hiện doc-6), `5ed9ca1` (guard/grant), `ffd070d` (harness).

Đường toàn chuỗi với model/embedding giả, PostgreSQL thật đã chạy. Đây là bằng chứng
kết nối/meter/receipt/cache; chưa chứng minh chất lượng nội dung, tốc độ hay chi Vertex thật.
Lượt thật thành công còn phải được kiểm chất lượng, rồi chủ dự án/điều phối mới xét ghép và triển khai.

| Cổng trên mã mới | Kết quả | Bằng chứng |
|---|---|---|
| W-15/W-25, gồm 34 ca mới | 76 đạt, native 0 | [JUnit](w15-evidence/runs/operator-approved-scope-20261024-03.xml) |
| Mutation bản cuối | 29/29 bắt bằng assertion, 0 setup error, phục hồi nguyên byte | [JSON](w15-evidence/mutations/approved-final-20261024-01/mutations.json), [native](w15-evidence/runs/approved-mutations-final-20261024-01-exit.json) |
| Python toàn repo tại `ffd070d` | 2.534 đạt/0 lỗi/1 skip/1 xfail; native 0 | [JUnit](w15-evidence/runs/operator-full-20261024-01.xml), [native](w15-evidence/runs/operator-full-20261024-01-exit.json) |
| React/build tại `ffd070d` | 143 đạt; build thành công, native 0 | [React](w15-evidence/runs/operator-react-20261024-01.xml), [build](w15-evidence/runs/operator-build-20261024-01-exit.json) |

Các capture trước commit mang HEAD `4038055` và SHA từng tệp đang sửa, không được gán là
đã chạy trên cây sạch của commit đó. Cổng toàn repo dùng commit mã `ffd070d`.
Một skip là Cloudinary live; một xfail là replay SA-55 cũ, không thêm ngoại lệ ở lượt này.

Hai plan profile thật tại `ffd070d` đã dry-run riêng với provider/ADC guard, chi mới 0 USD:
[doc-6](w15-evidence/operator-20261024/doc6-plan-at-ffd070d.json),
[rau thủy canh](w15-evidence/operator-20261024/candidate-plan-at-ffd070d.json).
Collector trả một receipt, đọc 26/125 chunk tương ứng, downstream chưa chạy model.
Plan đều `approved=false`. Sau commit báo cáo phải chuẩn bị lại vì pipeline version chứa HEAD;
hai plan lưu ở đây chỉ là bằng chứng dry-run trên mốc mã đã kiểm, không dùng làm grant.

Backend thường lấy `WAYFINDER_ARTIFACT_ROOT` rồi truyền thành `artifact_dir` cho core.
Harness này chủ động dùng `tmp/w15-operator-<book>-<nonce>/artifacts` và database riêng;
**không ghi kho artifact/PG dùng chung của env**. Đồ thị/artifact Pha A vẫn là tệp;
record/cache Pha B và sổ chi nằm trong PostgreSQL của lượt. Chưa chuyển dữ liệu thử sang product.

## Doc-6: cache miss thật và cách chứng minh web 0 USD

Ca `test_doc6_real_web_worker_stops_at_the_first_uncached_stage_without_spending`
dùng PDF doc-6 thật, HTTP và DocumentPipeline mặc định, PG xuyên connection, guard provider/ADC.
Đọc xong, `concepts` gặp `SpendNotAllowed` ở label-roles; 0 gọi/0 USD, không course ready/mail thành công.
[Bằng chứng](w15-evidence/sql/doc6-web-cache-only-20261024-02/).
Ledger có một dòng terminal 0 USD hợp lệ; không được kết luận cần ledger rỗng.

Không đổi u-hash, parser/version/dependency hoặc nhập cache alias doc-6 v29.
Đề nghị một lần **bootstrap nội bộ có phí riêng** trên cùng u-hash/profile/PG để tạo cache hợp lệ;
sau đó lần web đầu tiên trong DB chưa có build được khóa chi false, dùng cache vừa tạo.
Chi bootstrap ghi riêng `purpose=build`, không gọi nó là phần web 0 USD.

Đã diễn tập chính cách này với PDF tổng hợp, thuật toán đầy đủ và provider giả:
`test_operator_bootstrap_then_web_ready_mail_uses_the_new_cache_without_more_fake_calls`.
Bootstrap có usage tổng hợp; lần HTTP kế tiếp không tăng gọi fake, receipt 0 USD,
reader PG độc lập thấy course ready và Console Mailer đúng một thư “Bản dựng xong”.
Chưa thực hiện bootstrap hoặc lần web ready này với PDF doc-6 thật.

## Hai lượt đề nghị chủ dự án duyệt mới

Mỗi lượt gồm nhiều request của pipeline; không thể chứng minh toàn chuỗi bằng một request API đơn lẻ.
Không tự chạy lại sau lỗi hoặc tăng trần. Cache/artifact/PG/bằng chứng giữ riêng theo lượt, không dọn dữ liệu.

| Lượt | PDF / SHA-256 đầy đủ | Trần đề nghị |
|---|---|---|
| 1. Bootstrap nội bộ doc-6, rồi web cache-only 0 USD | `doc-6.pdf`, 25 trang; `82cb494d407c4755d29deb7c08b9a4f3794f79e241c307fd2b5dfc149cd559c7` | **1,00 USD** cho bootstrap; web không được gọi có phí |
| 2. Một lần dựng ứng viên qua HTTP/worker | `document-data/train/nong-nghiep/rau-thuy-canh.pdf`, 52 trang; `1f019766e74a747d293c15ad5bc86b2ea90420b49a8437cf27c1f6805656a627` | **3,00 USD** |

**Tổng trần hai lượt 4,00 USD. Chưa có quyền chi.** Trần là quyết định giới hạn mức thử,
không hứa toàn cuốn chắc chắn xong trong số tiền này. Không dùng quyền W-13/SA/phục hồi cũ.

Căn cứ chọn mức thử: W-13 doc-6 fresh đã ghi **0,1203762 USD đủ usage**
([kết quả](w13-doc6-ket-qua-2026-10-19.json)); đây là mốc tham khảo lịch sử khác profile.
Ứng viên có 125 chunk/120 section so với doc-6 26/78; số context A3 trước nhãn 98 so với 21.
[Inventory 0 USD](w15-evidence/input-inventory-20261024.json) có ảnh/công thức và độ dài chữ.
Số này chưa qua label-roles, không suy thành số request/chi sau cùng hoặc dự toán bảo đảm.
Trần ứng viên cao hơn để thử sách lớn hơn; guard dừng trước dispatch không còn đủ dự phòng.

| Bước | Cache / gọi sinh / embedding dự kiến | USD / phút / embedding wait |
|---|---|---|
| doc_reading | Dry-run đã đọc bản sao SHA; không model | 0 USD; wall đo riêng trong receipt |
| concepts | label-roles còn run; A3/A3′/A4 vi coverage none giữ đủ | downstream unknown trước nhãn |
| graph | Cần canonical thật và tên module; đúng PG chung | số gọi/chi/phút unknown |
| learning_prep | Cần graph và concept-index thật | số gọi/chi/phút unknown |
| Tổng | Không lấy `inspect` làm cache hit | Trần thử ở trên; tổng dự toán chưa đầy đủ |

## Hàng rào của lượt được duyệt

`BuildSpendApproval` chỉ nhận từ operator tin cậy sau tin nhắn duyệt mới của chủ dự án.
Đối chiếu SHA đầy đủ, u-hash, pipeline version, model/profile và DB đã dry-run.
Reference bị tiêu thụ một lần trong cùng PostgreSQL trước dựng, kể cả lượt lỗi.
Không có endpoint nhận grant và không mở chi cho job khác. Phải dùng một process operator riêng;
hook ba transport được tuần tự hóa trong process, không dùng cùng worker phục vụ job khác.

`BuildSpendGuard` dự phòng request đang bay trước dispatch, chờ giải phóng dung lượng khi song song.
Giữ riêng known/held/unknown; timeout hoặc thiếu usage giữ cận trên và chặn request sau,
receipt phải failed/usage incomplete. Không biến unknown thành 0. Lỗi ghi audit vẫn trả phản hồi
đã tính tiền cho core meter, giữ chi đã biết, đánh failed và chặn dispatch tiếp.
Không thay bộ tính chi: **meter delta là chi build duy nhất**, trace counted_in=build không cộng lại.

Profile giá chỉ chấp nhận HTTPS Vertex global, Gemini 3.1 Flash-Lite standard text/ảnh nội tuyến
và Gemini Embedding 001 một text/request. Từ chối model/region/transport khác, tools,
priority, fileData/audio/video. Không in body/token/credentials vào audit.
Giá global Flash-Lite input 0,25/output kể cả thinking 1,50 USD/triệu token:
[bảng giá Google](https://cloud.google.com/vertex-ai/generative-ai/pricing).
Cửa sổ input 1.048.576/output 65.536:
[giới hạn model](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-1-flash-lite).
Embedding 0,15 USD/triệu token theo [Google](https://developers.googleblog.com/en/gemini-embedding-available-gemini-api/),
giới hạn 2.048 token theo [Vertex](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings).

Dự phòng bảo thủ mỗi generation **0,360448 USD**, mỗi embedding **0,0003072 USD**,
theo giới hạn model thay vì đoán token ảnh. Có thể làm giảm số gọi đồng thời; không phải dự báo chi.
Nếu giá/model/profile thay đổi, phải kiểm và chuẩn bị lại trước xin duyệt.
Non-200 giải phóng dự phòng; response 200 chưa biết usage giữ cận trên.
Receipt application model_calls có thể tính cả lần bị từ chối transport; audit `http_calls`
đếm request thực dispatch. Không sửa số của core để che sai khác này ở lượt dừng.

`web_timing.embedding_wait_seconds` là hợp các khoảng thời gian `_embed_vertex` theo bước,
gồm xác thực/limiter/request/retry/dự phòng; không phải riêng độ trễ mạng hoặc chờ permit.
Khoảng song song không cộng hai lần. Lượt không có grant giữ null/measured=false như trước.
Chưa sửa instrumentation lõi hoặc khẳng định đã tách các thành phần thời gian.

## Bằng chứng test và review

RED guard ban đầu: [10 assertion thiếu guard](w15-evidence/runs/spend-guard-red-20261024-01.xml).
RED grant: [4 assertion thiếu boundary](w15-evidence/runs/approval-red-20261024-01.xml).
Hai lỗi receipt đã tái hiện [2 fail/1 control](w15-evidence/runs/receipt-cost-red-20261024-01.xml):
mất chi đã biết khi audit hỏng và input-only usage bị đánh đủ; bản sửa đạt
[31 ca](w15-evidence/runs/receipt-cost-final-green-20261024-01.xml).
Audio/fileData đã [2 assertion fail/4 control](w15-evidence/runs/modality-red-20261024-02.xml)
rồi xanh trong scope cuối. Không giảm assertion/guard/timeout/skip/xfail để đạt.

Giữ cả lượt tự kiểm sai: doc6 đầu suy ledger rỗng; approval-green-01 đếm record không lọc ref;
operator-flow-01 so chuỗi Decimal với int; modality-red-01 fake provider trả None;
operator-approved-scope-02 gõ sai tên test và không chạy test nào. Chúng không được tính làm RED
chứng minh lỗi sản phẩm. Lượt sau dùng assertion đúng và nhãn mới, không ghi đè bằng chứng.

Review đúng phạm vi: không dependency/migration mới, không sửa learning budget hoặc thuật toán/index;
chỉ adapter worker và operator harness. Đã đọc ca âm/happy path, raw usage/known/unknown,
khóa PG/callback, bí mật/đường dẫn và giới hạn concurrency. Fake HTTP/ADC guard giữ suốt suite;
approval giả chỉ dùng trong test, chưa tạo file duyệt thật.

Đề nghị planner lõi trong [hồ sơ trước](w15-tiep-quan-kiem-main-2026-10-24.md) là phương án lịch sử,
không phải điều kiện mới buộc Claude viết lại trước lượt W-15 này. Dùng pipeline hiện có và cap
bảo thủ; downstream chưa biết vẫn ghi unknown. Adapter thường khóa chi, operator có grant mới
được gọi có phí. Các mệnh đề “chưa có cap/cách thực thi” trong hồ sơ trước được thay bởi hồ sơ này.

Chỉ sau cổng đạt mới chuẩn bị lại `--book doc-6`/`--book candidate` trên HEAD bàn giao,
bản sao riêng/SHA, PG riêng, dry-run collector allow_spend=false và provider/ADC guard.
Plan chứa `approved=false`; nếu HEAD hoặc config đổi thì bắt buộc chuẩn bị lại.
Chủ dự án duyệt đúng hai plan/version/hash/trần mới tạo approval file và chạy.

Sau lượt thật: đối chiếu receipt/SQL độc lập, ledger đúng một lần, usage thiếu có giải thích,
cache/graph/ready/Console Mailer, ảnh/công thức/nguồn và tính học được của module.
Ghi USD/phút/gọi/embedding wait thật từng bước và đề nghị vận hành dựa trên đo thật.
Chưa tự deploy, ghép main hoặc đóng W-15 khi chỉ có chuẩn bị 0 USD.

## Bảo toàn hồ sơ

[Tổng hợp](w15-evidence/operator-20261024/summary.json),
[kiểm lịch sử](w15-evidence/operator-20261024/historical-integrity.json),
[chuẩn hóa](w15-evidence/operator-20261024/normalization.json) và
[manifest](w15-evidence/operator-20261024/manifest.json) ghi SHA mới, raw giữ ở
`tmp/w15-operator-raw-20261024`. JSON values/JUnit case attributes không đổi.
Các manifest cũ 401 + 103 + 108 entry được kiểm lại, không ghi đè.
Export hồi quy W-06/W-14 được lưu riêng trước phục hồi; W-25 mới chuyển vào
`w15-evidence/w25-regressions` theo nhãn, không xóa tệp/dữ liệu/worktree.
Chỉ commit đường dẫn W-15; không `.env`/PDF/artifact/cache hoặc credentials cấu hình.
