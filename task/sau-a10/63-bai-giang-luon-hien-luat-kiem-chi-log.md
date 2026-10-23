# SA-63 — Bài giảng luôn hiện; luật kiểm chỉ ghi log cho admin

**Nguồn:** chủ dự án 2026-10-23: "tôi muốn bài giảng vẫn hiện dù có hỏng, chỉ log lại thôi, đánh giá thì vẫn đánh giá nhưng production phải hoạt động";
"mục tiêu cuối cùng là 1 bài giảng tự nhiên hiện lên cho người dùng". [ADR 0024](../../doc/adr/0024-bai-giang-luon-hien-luat-kiem-chi-ghi-log.md);
[spec Pha B2](../../doc/pha-b2-spec.md), mục 6.1–6.6 (`49c5b20`). Số đo: SA-21, 16/50 bài hỏng ở lần bấm đầu
([báo cáo](../../report/danh-gia-sa21-2026-10-23.md)).

**Ai:** agent Sonnet cài · Claude nghiệm thu và ghép · **Chi phí mô hình:** 0 USD, chỉ mô hình giả · **Chặn bởi:** không về mã. Chạy sau khi SA-62 ghép, vì
một agent một lúc và cả hai cùng đụng `composition_phase_b.py` · **Ghép:** Claude ghi cửa ghép ở mục 10 bàn giao · **Trạng thái:** sẵn sàng

## Mục tiêu

Người học bấm một khái niệm là thấy một bài giảng đọc liền mạch. Luật kiểm không còn chặn gì. Luật chỉ còn là nhiệt kế: admin biết bài nào có ý lệch sách,
và đánh giá đo tỉ lệ đó. Trích dẫn hợp lệ vẫn có link về trang sách như hiện nay.

## Phạm vi tệp

Sửa:
- `src/doc2roadmap/application/phase_b/lectures.py`: luật kiểm thành log, bỏ cổng, sinh lại, đối tượng `failure`, khối `validation`;
- `src/doc2roadmap/domain/phase_b_limits.py`: `lecture_validator_version` lên `lecture-validator-8`; thôi dùng `lecture_failure_ttl_seconds`;
- `src/doc2roadmap/composition_phase_b.py`: chỉ khi đường `lecture(deterministic=True)` cần thêm `message`;
- trang xem thử `src/doc2roadmap/presentation/preview/phase_b.html` và `server.py`: hiện ý ngay khi tới; khi `failed` hiện `failure.message` và nút
  "Thử lại" với mọi lý do;
- test lõi mới trong `tests/`.

**Không sửa:**
- prompt bài giảng, để số đo sau còn so được với SA-21;
- luật câu nối K10–K12;
- quiz, và trợ lý ngoài phần cần để `get_lecture` không lộ `validation`;
- `src/web/`: người điều phối làm phần web theo mục 10 bàn giao.

## Cần làm

1. **Luật kiểm chỉ ghi log** (spec 6.1).
   - K2, K3, K5, K6 (lặp n-gram, cắt cụt), K7, K8, K9 không bỏ ý, không làm bài hỏng, không gây sinh lại.
   - Ý trượt K2 giữ các trích dẫn hợp lệ còn lại; nhãn lạ thì không có link. Ý trượt K3 vẫn link tới đoạn nguồn, nhưng không tô câu trích.
   - Ý trượt K5 hay K7 hiện như thường. Ví dụ ngoài sách vẫn mang cờ `outside_document` như hiện nay.
   - Vẫn bỏ, có ghi log: ý sai lược đồ hay chữ rỗng (K1 ở mức ý); ý gần trùng một ý trước (luật trùng ý của K6).
   - Câu nối giữ nguyên K10–K12.
2. **Khối `validation`** (spec 6.6): `{passed, rules: {luật: số ý}, items: [{section, index, rules}]}`. `passed` là kết quả theo luật cũ.
   - Lưu cùng bài trong cache, và ghi vào dòng `lecture_validation` của mỗi lần sinh.
   - **Không** có trong phản hồi cho người học: không ở kết quả nút bấm, không ở sự kiện `final`, không ở công cụ `get_lecture` của trợ lý.
3. **Không còn cổng.** Mỗi ý gửi sự kiện `item` ngay khi đóng xong. Sau ý đầu tiên, bài không còn hỏng được: hết token, JSON vỡ ở đuôi, lỗi mạng hay quá giờ
   đều trả `ready` kèm `cat_ngan`, và không rút ý nào đã gửi.
4. **Sinh lại** chỉ khi chưa có ý nào dùng được (đầu ra trống, hay JSON vỡ từ đầu): 1 lần, ở `lecture_retry_temperature`.
5. **Không có bài** (spec 6.3): `status = failed` với đối tượng `failure`:
   - `reason_code` ∈ `loi_mang`, `het_thoi_gian`, `tran_he_thong`, `khong_dung_duoc`, `khong_co_mo_hinh`. Bỏ `kiem_noi_dung`;
   - `message` tiếng Việt, nêu lý do rồi nhắc thử lại sau; hết trần hệ thống thì nhắc thử lại vào ngày mai;
   - `retryable` luôn true; giữ `read_page` và `ask_assistant`.
6. **Cache** (spec 6.4).
   - Bài trượt kiểm vào cache chung như bài `ready`.
   - Bản ghi lỗi được nhớ `negative_cache_seconds` (60); `tran_he_thong` thì tới hết ngày.
   - Thôi dùng 24 giờ. Lên `lecture-validator-8` để bản ghi `kiem_noi_dung` cũ hết hiệu lực.
   - Xoá khoá `lecture_failure_ttl_seconds` khỏi `BSettings` nếu cổng vẫn xanh mà không phải sửa bản ghi phát lại; không thì giữ khoá, ghi "không dùng" vào
     báo cáo.

## Tiêu chí nghiệm thu

Mọi test phải **đỏ trên mã cũ**. Ghi trong báo cáo cách đã thấy chúng đỏ.

- [ ] **Kịch bản SA-21:** mô hình giả trả một bài mà mọi ý giải thích có `quote` viết lại chữ PDF bị vỡ, ví dụ "vật chất" trong khi nguồn ghi "v ật chất".
      Mã cũ trả `failed`/`kiem_noi_dung`. Mã mới trả `ready`, đủ mọi ý, log có K3 cho từng ý, và 0 lời gọi sinh lại.
- [ ] Ý trượt K2, K5, K7 và câu tự kiểm tra trượt K9 vẫn có trong bài trả về. Bài chỉ còn 0–1 ý giải thích vẫn `ready`. Trích dẫn hợp lệ còn lại vẫn có link.
- [ ] Ý gần trùng và ý sai lược đồ bị bỏ, và có trong log. Câu nối trượt K11 hay K12 vẫn bị bỏ.
- [ ] **Stream:** sự kiện `item` đầu tiên đến ngay sau khi ý đầu đóng xong, trước khi ý thứ hai bắt đầu. Sau ý đầu, lỗi mạng giả, quá giờ giả, hay JSON
      vỡ ở đuôi đều trả `ready` kèm `cat_ngan`, và không rút ý nào.
- [ ] **Không có bài:** mỗi `reason_code` có `message` không rỗng và `retryable = true`. Đầu ra không đọc được thì sinh lại đúng 1 lần, rồi
      `khong_dung_duoc`. Không đường nào trả `kiem_noi_dung` hay câu TextRank.
- [ ] **Ghi nhớ lỗi, dùng đồng hồ giả:** sau lỗi mạng, bấm lại ở giây 59 thì 0 lời gọi; ở giây 61 thì gọi lại. `tran_he_thong` nhớ tới hết ngày.
- [ ] **Cache:** bài trượt kiểm bấm lần hai thì 0 lời gọi. Bản ghi `kiem_noi_dung` 24 giờ của `lecture-validator-7` không còn được phục vụ.
- [ ] **Không lộ `validation`:** khối này có trong bản ghi cache và trong dòng log, nhưng không có ở kết quả nút bấm, sự kiện `final`, hay `get_lecture`.
- [ ] Trang xem thử hiện ý ngay khi tới; khi `failed` thì hiện `message` và nút "Thử lại".
- [ ] Bảng phá trong báo cáo, gồm ít nhất các phép sau:
  - bỏ ý trượt K3 như cũ;
  - giữ cổng 2 ý;
  - để `validation` lọt vào phản hồi;
  - `retryable` false với `tran_he_thong`;
  - ghi nhớ lỗi 24 giờ;
  - sinh lại khi trượt K8.
- [ ] Test Pha B, test kiến trúc, và cổng toàn repo qua `scripts/w05_run_tests.py` xanh, cùng React test và build.
- [ ] Báo cáo kèm JSON của bài giảng trong kịch bản SA-21, đúng như người học nhận, để Claude đọc.

## Ngoài phạm vi

- Lượt thật có tiền để chấm nội dung các bài trượt kiểm (vé sau, xin duyệt riêng).
- Trang admin đọc log kiểm phía web (người điều phối).
- Sửa nguyên nhân bài trượt (chữ PDF vỡ, nhãn nguồn). Làm vé chẩn đoán riêng nếu chủ dự án muốn.
- Đổi prompt hay nhiệt độ (chờ SA-21 chấm xong).
