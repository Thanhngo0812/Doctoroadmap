# SA-30 — Sửa sau soát: K6 dò sai, cache bài hỏng, TTFT, câu trích cụt, tài liệu sau hậu kiểm

**Nguồn chân lý:**
- [soát SA-25–28](../../report/kiem-thu-pha-b-sa25-28-2026-10-18.md), mục 1, 2;
- [nghiên cứu bài giảng](../../report/nghien-cuu-bai-giang-tien-quyet-goi-mo-xu-ly-hong-2026-10-18.md), phần "phát hiện trong mã";
- [spec Pha B](../../doc/pha-b-spec.md), luật K1–K8.

**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (phát lại) · **Chặn bởi:** không · **Trạng thái:** ready-for-agent

## Vì sao

Năm lỗi, mỗi lỗi đã được Claude kiểm lại trên mã hoặc dữ liệu thật.

| # | Lỗi | Bằng chứng |
|---|---|---|
| 1 | **K6 dò lặp trên cả JSON đầu ra**, gồm câu trích nguyên văn và tên trường | 18 lần sinh của nhóm 2: 9/18 bị coi là lặp; dò trên chữ của ý thì 0/18. Đây là nguyên nhân hỏng lớn nhất của bài giảng |
| 2 | **`single_flight` cache mọi kết quả**, kể cả bài `fallback` | bài hỏng một lần thì bị lưu vĩnh viễn và trả cho mọi người học. Chủ dự án đã quyết bản lùi không bao giờ hiện |
| 3 | **`ttft_ms` = 0** | 18/18 dòng sổ chi bài giảng; vé 13 và 21 cần số này |
| 4 | **`_bounded_quote` cắt câu trích ở 120 ký tự** | ngắn hơn trần chung `quote_max_chars` (200), nên câu trích cạnh hiện ra bị cụt |
| 5 | **Tài liệu sau hậu kiểm (SA-25):** tiêu đề rỗng còn sót, dòng chỉ có dấu câu; 2/6 tài liệu `failed` vì mô hình không chép câu trích nguyên văn | đọc 6 tài liệu ở `tmp/phaseb-sa25-documents/` |

## Cần làm

1. **K6:** chỉ dò cụm lặp trên chữ của các ý (`text` của mọi mục và câu tự kiểm tra). Không dò trên câu trích, tên trường hay toàn bộ JSON. Giữ phần kiểm
   bị cắt (`MAX_TOKENS`). Đổi `lecture_validator_version`.
2. **Cache:**
   - bài có trạng thái khác `ready` (`fallback`, `failed`, `no_source` do lỗi) không vào cache chung;
   - lần bấm sau sinh lại, nhưng vẫn qua single-flight để hai yêu cầu đồng thời chỉ sinh một lần;
   - cache âm ngắn như hiện có (`negative_cache_seconds`) để không gọi dồn.

   Chính sách hiện gì khi bài hỏng hẳn chờ spec mới; vé này chỉ đảm bảo bài hỏng không bị lưu vĩnh viễn.
3. **TTFT:** đo thời điểm có mẩu đầu tiên từ stream của adapter, ghi vào `ttft_ms` của dòng sổ chi bài giảng. Áp tương tự cho trợ lý và tài liệu nếu cũng
   đang ghi 0.
4. **Câu trích cạnh:**
   - `_bounded_quote` dùng `quote_max_chars` từ `BSettings`;
   - cắt ở ranh giới câu nếu có, không ở giữa từ;
   - câu trích bị cắt thì giữ đúng khoảng ký tự nguồn.
5. **Tài liệu:**
   - sau hậu kiểm, bỏ tiêu đề không còn nội dung bên dưới và dòng chỉ có dấu câu;
   - khi nhãn hợp lệ mà câu trích của mô hình không nguyên văn, mã chọn câu của nguồn trùng nhiều từ nhất, như trợ lý đang làm;
   - đo bằng phát lại số tài liệu `ready` trước và sau.

## Tiêu chí nghiệm thu

- [ ] Test, mỗi cái thấy đỏ trên mã hiện tại rồi mới xanh:
  - hai ý khác nhau cùng trích một câu nguồn dài thì không hỏng K6;
  - ba ý lặp nguyên chữ thì vẫn hỏng K6;
  - bài `fallback` không vào cache: lần gọi sau sinh lại;
  - hai yêu cầu đồng thời vẫn chỉ sinh một lần;
  - `ttft_ms` khác 0 với mô hình giả có độ trễ;
  - câu trích 180 ký tự không bị cắt;
  - tiêu đề rỗng bị bỏ;
  - tài liệu có nhãn hợp lệ nhưng câu trích không nguyên văn vẫn có trích dẫn, với câu do mã chọn.
- [ ] Phát lại 0 USD 12 bài của nhóm 2. Báo trạng thái trước và sau (sau SA-26 là 9 `ready`, 3 `fallback`), cùng lý do hỏng còn lại.
- [ ] Phát lại 0 USD 6 tài liệu của nhóm 2. Báo trạng thái trước và sau; đính kèm 6 tài liệu cho Claude đọc.

## Ngoài vé

Bốn việc chờ đợt tra hỏi và spec mới:
- bài giảng gợi lại tiên quyết và gợi mở phần sau;
- hiện gì khi bài hỏng hẳn;
- stream trước hay sau khi bài qua cổng kiểm;
- giao diện hai tầng.
