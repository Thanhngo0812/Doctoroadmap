# SA-45 — Tổng hợp soát Pha B, ngày 2026-10-18

Đã hoàn tất đợt soát **16 vé SA-29–44**, ghi phán xét trong kế hoạch và tạo **sáu vé sửa SA-46–51**. Năm vé chưa đạt là **34, 37, 40, 42, 43**. Vé 44 đạt theo quyết định trực tiếp của chủ dự án, miễn bảy thao tác/ảnh; không có kết quả thử tay hay ảnh để khẳng định đã làm.

Đợt này không sửa mã chức năng Pha B, không đổi spec/ADR và không chạy Gemini có tiền. Các lỗi còn mở có test tái hiện hoặc bằng chứng thiếu cặp so sánh; không coi toàn bộ Pha B2 đã nghiệm thu.

## Phán xét

| Vé | Phán xét | Bằng chứng / việc tiếp |
|---|---|---|
| 29 | Đạt có ghi chú | Đọc đủ 160 tên/mô tả; 136 tên LLM, 82 mô tả LLM; không trùng tên nguyên văn. Tên doc-4 module_012 còn rộng, đưa vé 20 đánh giá. |
| 30 | Đạt có ghi chú | K6 chỉ đọc chữ ý; tài liệu 6/6 ready, 17 quote được chọn lại, 0 lỗi offset. Runner B1 không khớp hash B2 nên phần tài liệu audit bằng phản hồi cũ qua mã mới, có ghi giới hạn. |
| 31 | Đạt có ghi chú | Scope thuần theo Jaccard, kho/đồng hồ/cấu hình có test và mutation. Ngoại lệ phạm vi test của nhóm này ghi riêng bên dưới. |
| 32 | Đạt có ghi chú | Lưu đủ 5 lượt, prompt tối đa 3 lượt/1.000 token; replay sáu phản hồi: 4 answered, 2 insufficient_context, 0 USD. |
| 33 | Đạt có ghi chú | Giải lại/stale không sửa scope đã lưu, có thẻ module. Thẻ doc-4 vẫn 1.322 token, vượt mốc gợi ý khoảng 800; chưa tự đổi cách cấp context. |
| 34 | **Chưa đạt → 47** | Quiz đọc rồi ghi đồng thời có thể ghi đè lựa chọn `not_learned` của learner thành `learned`. |
| 35 | Đạt | Cùng ID ở here/elsewhere, module suy theo đồ thị hiện hành; xóa phiên giữ nội dung và cách ly owner. |
| 36 | Đạt phần nhắc nền | Thêm ca bốn tiên quyết chưa học xác nhận chỉ nhắc ba, mutant 3→4 bị bắt. Chờ nền tiến độ sửa race ở 47. |
| 37 | **Chưa đạt → 46, 50** | Scope chuỗi của công cụ trợ lý bỏ lấy mẫu/trần; `n` ghi đè cấu hình; câu điền khuyết không giữ đủ Q3/Q6. Phần giới hạn tài liệu năm module đạt. |
| 38 | Đạt | Không có bản lùi; failed giữ skeleton, failure memo đúng TTL, cache ready riêng; timeout có test. |
| 39 | Đạt có ghi chú | Cổng hai giải thích, không phát ý trước cổng và cắt đuôi K6 có test; số timing thật còn nhỏ, giữ S3 đã chốt. |
| 40 | **Chưa đạt → 49** | Hai bridge khác chữ cho cùng tiên quyết được giữ/phát; thấy ở Tỉ lệ tổng thể và Bát chính đạo. |
| 41 | Đạt phần nhãn | Nhãn theo request, không lọt cache/prompt; chờ nền tiến độ/câu nối ở 47/49. |
| 42 | **Chưa đạt → 48** | Hai `call_json` đồng thời cùng learner gọi mô hình giả hai lần và ghi 0,24 USD khi trần là 0,20 USD. |
| 43 | **Chưa đạt → 51** | Đã đọc 12 bài; hai fixture nhánh sửa nhiệt độ 1 không khớp prompt, không đủ so sánh cặp công bằng. |
| 44 | Đạt theo chủ dự án duyệt | Miễn bảy thao tác/ảnh. 11 test HTTP đạt; máy chủ đã khởi động nền tại `http://127.0.0.1:8765/`, phản hồi HTTP 200. |

Phán xét không gộp lỗi của một vùng mã thành phủ nhận các phần đã đạt. Các vé phụ thuộc phần chưa đạt được cập nhật cạnh chặn trong `task/sau-a10/00-ke-hoach.md`.

## Vé sửa đã tạo

| Vé | Mức ưu tiên | Phạm vi | Chặn bởi |
|---|---|---|---|
| [48](../task/sau-a10/48-tran-ngay-giu-cho-dong-thoi.md) | Critical — trần chi | Tính lượt đang chạy, giữ chỗ/nguyên tử, chốt và giải phóng theo usage | — |
| [47](../task/sau-a10/47-tien-do-giu-lua-chon-khi-quiz-dong-thoi.md) | Required — dữ liệu learner | Quiz không ghi đè lựa chọn thủ công khi đồng thời | — |
| [46](../task/sau-a10/46-quiz-roadmap-chuan-hoa-pham-vi-va-tran.md) | Required — hành vi/chi phí | Chuẩn hoá scope roadmap, giữ trần cấu hình khi có `n`, seed/ưu tiên tiến độ | — |
| [49](../task/sau-a10/49-bai-giang-mot-cau-noi-moi-tien-quyet.md) | Required — hợp đồng | Một bridge cho một tiên quyết, nhất quán stream/final/cache | — |
| [50](../task/sau-a10/50-quiz-dien-khuyet-kiem-luat-va-cau-thieu.md) | Required — câu hỏi | Áp Q3/Q6 cho điền khuyết, bỏ câu dẫn thiếu phần xác định đáp án | 46 |
| [51](../task/sau-a10/51-do-lai-so-sanh-retry-lecture-2.md) | Required — bằng chứng | So matched subset, đo thời gian đúng mẫu; phần bổ sung có tiền cần duyệt mới | 49, 48 |

Các vé theo khuôn nguồn chân lý/vì sao/cần làm/tiêu chí/ngoài vé. SA-46/47/48/49/50 có tên test đã thấy đỏ. SA-51 là thiếu bằng chứng so sánh: yêu cầu test tổng hợp trên fixture giả trước, không thể tự tạo phản hồi trả phí còn thiếu bằng replay. SA-46 và 50 cùng vùng `quiz.py` nên chạy tuần tự; SA-48 chạm đường gọi chung, cần ghép xong guard trước khi nghiệm thu lại các vùng gọi mô hình. Chưa triển khai sáu vé sửa trong SA-45.

## Kiểm chứng cuối

Chạy bằng `.venv/Scripts/python.exe`, `--basetemp` trong `tmp`, tắt pytest cache. Lệnh cuối:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/phase-b/sa45_run_checks.py
```

Runner chọn **37 tệp test Pha B/kiến trúc cụ thể**, không discovery toàn repo; loại bài test tích hợp 19e dùng cuốn fixture ngoài sáu cuốn phát triển. Có HTTP localhost nên cần quyền chạy ngoài sandbox trên môi trường hiện tại. Kết quả JUnit `tmp/sa45-final-tests.xml`: **288 test = 279 passed + 9 xfailed, 0 lỗi ngoài dự kiến**. Chín `xfail(strict=True)` chính là lỗi đang chờ sửa, không phải chín test đã đạt.

Chạy cùng ba tệp audit với `--runxfail`:

```powershell
.venv/Scripts/python.exe -X utf8 -m pytest -q -p no:cacheprovider --basetemp tmp/sa45-all-regressions-red tests/unit/application/test_phase_b_sa45_artifact_audit.py tests/unit/application/test_sa45_sessions_audit_regressions.py tests/unit/application/test_phase_b_sa45_lecture_audit.py --runxfail --junitxml tmp/sa45-all-regressions-red.xml
```

Kết quả: **9 assertion hỏng đúng lỗi đã lập vé, 2 assertion đạt**, không lỗi thu thập/import. Hậu quả được đo từ số câu, tập node, đề công khai, bản ghi tiến độ, ledger và số item bridge; không chỉ kiểm cờ do mã vừa gán. Khi sửa phải bỏ nhãn xfail tương ứng; `strict=True` làm suite đỏ nếu lỗi tự hết mà nhãn chưa được bỏ.

Các phép sửa sai trong bộ nhớ cũng tái lập được: **15/15 mutant bị bắt**, gồm naming 1, foundation 7, quiz/tài liệu/nhắc nền 5, K6 2. Script ở `scripts/pha-b/sa45_mutation_naming.py`, `scripts/phase-b/b2_foundation_mutations.py`, `sa45_artifact_mutations.py`, `sa45_lecture_mutations.py`. Không sửa nguồn trên đĩa để thử mutant khi nhóm khác đang kiểm.

Đã đọc đầu ra thật: toàn bộ 160 tên/mô tả, sáu tài liệu đầy đủ, 12 bài SA-43, bốn câu quiz doc-4 và các JSON hợp đồng cho nhóm web. `ready` của mô hình không được diễn giải thành chứng nhận đúng ngữ nghĩa.

## Tiền và thời gian

**Chi Gemini/Vertex mới của SA-45: 0 USD, không gọi provider.** Lượt SA-29 trước đó có chỉ thị duyệt tiền trong phiên và dry-run, chi báo 0,142519 USD. Lượt SA-43 được duyệt riêng trần 0,50 USD; audit tự cộng ledger cách ly đúng **0,06523425 USD**, 40 dòng lecture + 40 validation + 10 timing. **90 dòng ledger không phải 90 HTTP**; run artifact ghi 30 attempts. Không dùng phần trần còn dư để chạy lượt mới.

Script `sa45_lecture_repro.py` chọn bốn arm đầu `ready` có đủ bốn mốc timing từ artifact lượt thật, rồi đối chiếu duy nhất với ledger; không chọn theo tên bài hoặc tốc độ replay. Trên n=4: skeleton p50/p90 21,5/32 ms; cổng 7.389/17.716 ms; final 8.292/18.405 ms; cổng→final 939/1.574 ms. Mười dòng timing thô có lẫn replay/timeout nên không gộp thành mười mẫu thật. Theo tín hiệu dưới một giây, cần cân nhắc S2, nhưng giữ S3 đến khi chủ dự án quyết.

Bridge nhánh 0 sau sửa: **17 tiên quyết có Q, 8 item bridge, 6 cặp (bài, tiên quyết) được phủ**, hai item trùng. Validation đếm 18 sự kiện K10, 3 K11, 2 K12 qua các lần thử; không coi đây là số ứng viên độc lập. Nhánh 0 10 ready/2 failed, nhánh 1 9 ready/3 failed với hai mismatch, nên chưa chọn được nhiệt độ thắng.

## Ngoại lệ quy trình và giới hạn bằng chứng

Một subagent đã chạy nhầm pytest toàn repo thay vì danh sách Pha B. Lệnh bị dừng ở 12%, không có verbose log tên test; **không thể khẳng định các test lúc đó đã truy cập những fixture nào**. Không có nội dung tập giữ lại được in ra để dùng cho phán xét, nhưng tôi không ký xác nhận tuyệt đối rằng lượt chạy nhầm đã tránh mọi truy cập tập giữ lại. Chi tiết lệnh/session và giới hạn ở báo cáo 31–36/42. Đã thay bằng runner danh sách tệp cố định cho kết quả cuối. Đây là ngoại lệ chưa đủ chứng cứ để đóng tiêu chí “không vi phạm luật” của SA-45; không giấu dưới kết quả 279 test đạt.

Các script audit chủ động chỉ nạp sáu cuốn được phép; không mở `live.json` hay thư mục tập khoá để điều tra lại ngoại lệ. Chỉ kiểm mã test/conftest đã xem và tên đường dẫn trong mã; việc này không khôi phục được nhật ký truy cập của lượt chạy nhầm. Các thay đổi Pha A và phần stage/working tree của phiên khác được giữ nguyên; commit chỉ whitelist đường dẫn của đợt soát.

Root từng tham gia triển khai gói B2. Ba lượt soát subagent dùng context mới theo từng vùng, và root đọc lại bằng chứng, thêm test/counter độc lập; đây vẫn là review nội bộ, không thay chấm chuyên gia hoặc người chấm mù của vé 20–23. Hai phản hồi cũ của nhánh retry 1 chưa khớp; phản hồi B1 qua context B2 không chứng minh prompt mới sinh nội dung giống trước. Không có kiểm thử thao tác trình duyệt của SA-44.

## Câu hỏi và việc còn treo cho chủ dự án/Claude

- Giữ S3 trong lúc sửa; sau SA-51 quyết định có chuyển S2 hay không và có giữ nhiệt độ sửa 0. Hiện chưa đủ bằng chứng để đổi.
- Thẻ lộ trình doc-4 1.322 token: giữ ghi chú, cân nhắc tên ngắn hoặc cấp chi tiết theo nhu cầu; không tự thêm phân trang/cắt tên ngoài spec.
- SA-19a: chủ dự án vẫn cần giao gói câu hỏi cho agentic dùng họ mô hình khác Gemini. Không mở đáp án ở thư mục người giữ trong lượt này, không tự gửi cho agent khác.
- Đánh giá 20–23 chạy sau các vé sửa liên quan. Vé 21 cần chấm lặp ý theo nghĩa, tập trung đúng khái niệm, ích lợi recall/câu nối; vé 22 cần đọc các câu điền khuyết sau SA-50.
- Neo/công thức Pha A có dấu hiệu lệch: recall Giao hoán của vành trỏ về hợp/giao tập hợp; định nghĩa ma trận chéo có `i = j` trong văn bản trích xuất. Báo phía Pha A kiểm nguồn, không sửa dữ liệu ở Pha B để che lỗi.

## Báo cáo chi tiết và mốc lưu

- [SA-29](soat-pha-b-29-2026-10-18.md).
- [SA-30 tài liệu và SA-37](soat-pha-b-30-tai-lieu-37-2026-10-18.md).
- [SA-31–36/42](soat-pha-b-31-36-42-2026-10-18.md).
- [SA-30 bài giảng, SA-38–41/43](soat-pha-b-30-38-43-2026-10-18.md).
- [SA-44](soat-pha-b-44-2026-10-18.md).

Đã lưu dần: `8aa7636` nhận duyệt SA-44; `c782fd8` tên module; `64c638f` quiz/tài liệu; `8fd8512` phiên/tiến độ/ngân sách; `e0064e0` bài giảng. Báo cáo tổng hợp/runner được lưu ở commit chốt SA-45 tiếp theo. Không push.
