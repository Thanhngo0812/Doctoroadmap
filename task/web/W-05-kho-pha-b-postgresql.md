# W-05 — Kho Pha B trên PostgreSQL, `single_flight` liên tiến trình, nới port sổ chi

**Nguồn chân lý:** [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), mục 4, 5, "Quyết định kiểm thử"; [ADR 0022](../../doc/adr/0022-postgresql-cho-du-lieu-web-artifact-o-kho-tep-hang-doi-bang-bang.md);
[spec Pha B2](../../doc/pha-b2-spec.md), mục 8, 9.
**Ai:** nhân viên lõi · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-01 · **Trạng thái:** ready-for-agent

**Đợt tiếp theo 2026-10-19:** lõi nhận sau checkpoint commit W-01, không chờ phần cache toàn chuỗi W-13.
Migration W-05 đi trước W-02, dự kiến `w05_0002` nối `w01_0001`; bàn giao mốc migration cho web trước khi ghép W-02.
Test W-01 về schema rỗng phải kiểm ở revision `w01_0001`, đồng thời thêm kiểm nâng HEAD đủ bảng, không bỏ assertion nền.
Xem [kế hoạch ba nhóm](../../report/dieu-phoi-soat-ba-nhom-2026-10-19.md).

## Vì sao

- Kho JSON của Pha B chỉ an toàn trong một tiến trình. Web chạy nhiều worker.
- `single_flight` và bản ghi hỏng 60 giây sống trong bộ nhớ tiến trình, nên hai worker sinh trùng bài và trả tiền hai lần.
- Trần ngày của người học phải đọc cả sổ chi rồi lọc trong Python. Trên sổ chi lớn dần, mỗi tin nhắn sẽ chậm dần.

## Cần làm

**Bản cài `PostgresPhaseBStore`** của port `PhaseBStore` (port ở lõi), đặt ở `src/web/backend/wayfinder/infrastructure/` để lõi không dính SQLAlchemy;
bộ test hợp đồng của lõi được gọi lại từ test của `wayfinder`. Bốn bảng `phase_b_cache`, `phase_b_negative`, `phase_b_record`, `usage_ledger` như spec mục 4.
- `put_record` tách `owner` và `doc_id` từ `value` ra cột; `get_record` và `list_records` trả **đúng** `dict` đã ghi.
- `usage_rows` trả đúng `dict` đã ghi; các trường ngoài cột nằm trong `extra`.
- **`single_flight` ba lớp,** như spec mục 5:
  - bản đồ `_Flight` trong tiến trình;
  - advisory lock trên một kết nối riêng, có `lock_timeout`;
  - lấy được khoá thì đọc lại cache và bản ghi hỏng trước khi sinh.
- Bản ghi hỏng ngắn hạn nằm ở `phase_b_negative`, dùng chung mọi tiến trình. Lỗi được ghi lại theo loại và câu báo; lần đọc sau ném lại lỗi cùng loại nếu
  loại đó có trong danh sách đã đăng ký.

**Nới port**, giữ tương thích ngược; sửa cả bản JSON và bản bộ nhớ:
- `usage_rows(doc_id=None, *, learner_id=None, since=None, purposes=None)`;
- `anonymize_learner_usage(learner_id)`.
- **Trần người học** (SA-42, đã được vá tiếp ở SA-48) đổi sang gọi bộ lọc mới, giữ nguyên luật giữ chỗ và regression hiện hành.
  Không chỉ kiểm số chi đã ghi: còn có bản ghi `spend_reservation` cho lời gọi đang chạy.
- **`atomic()` liên tiến trình:** giữ hợp đồng lõi, hỗ trợ ngữ cảnh lồng mà `DailySpendGuard.reserve/check` đang dùng.
  Check trần và tạo giữ chỗ, cập nhật tiến độ/quiz phải nguyên tử giữa các worker; khoá `single_flight` không tự thay các yêu cầu này.

**Liệt kê `kind` thật:** quét mã Pha B, ghi vào báo cáo vé danh sách `kind` đang có, và `kind` nào không có trường `owner`.

**Nối dây:** composition của `wayfinder` dùng bản PostgreSQL. CLI và test lõi không đổi, vẫn dùng bản JSON và bản bộ nhớ.

**Phần ở lõi** (`src/doc2roadmap/`): nới port, sửa hai bản cài JSON/bộ nhớ và cập nhật lời gọi trần người học sang bộ lọc theo mục "Nới port".
Không đổi luật/trần giữ chỗ SA-48 hoặc thêm phụ thuộc mới vào lõi.

**Di trú:** bốn bảng Pha B, cùng chỉ mục ở spec mục 4.

## Tiêu chí nghiệm thu

- [ ] **Bộ test hợp đồng hiện có của kho Pha B chạy trên cả ba bản cài,** không sửa kỳ vọng của bộ test. Báo số test của mỗi bản.
- [ ] Hai **tiến trình** (không phải hai luồng) gọi `single_flight` cùng khoá với một hàm sinh chậm: hàm sinh chạy đúng 1 lần; tiến trình sau nhận kết quả
  của tiến trình đầu. Thấy đỏ khi tắt lớp advisory lock.
- [ ] Bản ghi hỏng do tiến trình A ghi chặn tiến trình B gọi lại trong thời hạn; hết hạn thì B sinh lại.
- [ ] `usage_rows(learner_id, since, purposes)` cho cùng tập dòng với lọc trong Python trên cùng dữ liệu, ở cả ba bản cài.
- [ ] Bản PostgreSQL: kế hoạch truy vấn (`EXPLAIN`) của truy vấn trần người học dùng chỉ mục, không quét cả bảng. Ghi kết quả vào báo cáo.
- [ ] `anonymize_learner_usage` giữ nguyên tổng `cost_usd`, và không còn dòng nào mang `learner_id` cũ.
- [ ] Ghi một dòng sổ chi có trường lạ rồi đọc lại: `dict` giống hệt.
- [ ] Test đồng thời hiện có của trợ lý chạy được trên bản PostgreSQL.
- [ ] Regression SA-47/SA-48 về tiến độ, giữ chỗ chi, lỗi/timeout và qua ngày vẫn đạt; test hai tiến trình trên PostgreSQL không cho vượt trần
  khi cùng tranh phần ngân sách cuối. Tắt bảo vệ `atomic()` phải làm assertion này đỏ, không chỉ dựa vào hai luồng cùng tiến trình.
- [ ] Sau ghép W-02/W-05, Alembic đúng một head; DB rỗng nâng HEAD thành công, test W-01 tại revision nền vẫn còn nguyên ý nghĩa.

## Ngoài vé

Nhập dữ liệu từ `artifacts/phase_b/live.json` (không làm). Tách bảng theo `kind`.
