# SA-56 — Trợ lý biết khái niệm người học đang mở: trường tuỳ chọn `focus_node_id`

**Nguồn chân lý:** [spec B2](../../doc/pha-b2-spec.md), mục 3, `answer-2` (đã thêm trường ngày 2026-10-22);
[ADR 0012](../../doc/adr/0012-tro-ly-la-agent-goi-cong-cu.md); đề xuất 2026-10-19 ở mục 8 của
[bàn giao điều phối](../../report/handoff-dieu-phoi-2026-10-18.md). **Chủ dự án duyệt ngày 2026-10-22.**

**Ai:** agent Sonnet cài · Claude nghiệm thu · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** không · **Trạng thái:** sẵn sàng

## Vì sao

Yêu cầu `answer-2` chỉ có phiên và câu hỏi. Người học đang đọc bài giảng của một khái niệm mà hỏi "giải thích phần này" thì trợ lý không biết "phần này"
là gì. Nó phải đoán bằng `search` hay `lookup_concept`, tốn thêm vòng gọi công cụ và dễ lệch. Phiên module chỉ cho biết module, không cho biết khái niệm.

## Hành vi cần có

**Đầu vào.** `ask(...)` nhận thêm tham số tuỳ chọn `focus_node_id`. Web gửi kèm ở mỗi lượt khi đang mở bài giảng; phần gửi kèm thuộc W-09.
- Giá trị **không lưu vào phiên** và không vào `assistant_state`. Lượt sau không gửi thì không có tiêu điểm.
- Giá trị phải là khái niệm học được của đồ thị đang dùng. Nếu không phải, lượt vẫn chạy như khi không có tiêu điểm, và `warnings` có
  `{"kind": "focus_ignored"}`.
  - Đồ thị lên phiên bản mới có thể làm mất một nút, nên không ném lỗi.
  - Không tin giá trị do trình duyệt gửi.
- Không đòi khái niệm phải thuộc module của phiên: người học có thể mở bài của một tiên quyết.

**Khối tiêu điểm trong đầu vào mô hình.** Có tiêu điểm hợp lệ thì ngữ cảnh gửi mô hình có thêm khối `focus`:
- `node_id`, tên, số thứ tự và tên module;
- một dòng ghi rõ đây là khái niệm người học đang mở, "phần này" hay "cái này" trong câu hỏi chỉ khái niệm này;
- **câu định nghĩa có trích dẫn:** chunk của câu neo được thêm vào `sources` (bỏ trùng theo `chunk_id`) để có nhãn `[S#]` và qua hậu kiểm trích dẫn.
  Khối `focus` trỏ tới nhãn đó, không chép lại câu;
- **các ý của bài giảng nếu đã có trong cache,** gắn nhãn "đã hiện cho người học; không phải nguồn, không trích dẫn":
  - chỉ đọc cache, không bao giờ sinh bài giảng, 0 USD;
  - chỉ bài có `status = ready`;
  - khoá cache phải tính đúng như khi web mở bài, tức theo mô hình thật chứ không theo `generation_mode = unavailable`. Hãy đọc qua use case bài giảng
    mà trợ lý được dựng cùng, không tự tính khoá ở nơi khác.

**Trần kích thước.** Khối `focus` không quá `assistant_focus_tokens` (mặc định 400). Ước token cùng cách với phần còn lại của `assistant.py`. Quá trần
thì cắt các ý bài giảng trước. Thêm tham số vào `BSettings`, không đổi tham số khác.

**Khái niệm liên kết.** Chỉ đổi khi câu hỏi **không** khớp khái niệm nào:
- `linked` = tiêu điểm trước, rồi các khái niệm của lượt trước nếu câu hỏi là câu hỏi nối tiếp; bỏ trùng, tối đa 2;
- câu hỏi khớp khái niệm khác thì `linked` giữ như cũ, khối `focus` vẫn có. Ví dụ "phần này khác đơn ánh thế nào?" thì `linked` là đơn ánh, còn
  tiêu điểm vẫn là song ánh.

Thẻ đồ thị, khối nhắc nền và media vì vậy chạy theo tiêu điểm khi câu hỏi không nêu tên khái niệm. Luật của chúng không đổi.

**Không có tiêu điểm thì không đổi gì.** Prompt hệ thống và các tin nhắn gửi mô hình phải **giống hệt từng byte** với mã trước vé. Vì vậy dòng chỉ dẫn
về tiêu điểm nằm trong khối `focus`, không nằm trong prompt hệ thống. Bản ghi phát lại cũ, test SA-32 và `context_hash` của dry-run giữ nguyên.

**Đầu ra.** `answer-2` có thêm `focus_node_id`: giá trị đã dùng, hoặc `null` nếu không có hay bị bỏ. Trường thêm vào và tuỳ chọn, nên giữ
`contract_version = answer-2`. Dry-run tính cả khối `focus` vào ước token.

**Nơi gọi.** CLI `phase_b` có thêm `--focus-node-id`; trang xem thử (`presentation/preview/server.py`) gửi kèm khái niệm đang mở nếu có. Gateway web
không thuộc vé này.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên mã cũ hoặc trên bản sai:
- [ ] Hỏi "giải thích phần này" với tiêu điểm X, câu không khớp khái niệm nào:
  - `linked == [X]`;
  - đầu vào mô hình có khối `focus` của X, kèm nhãn nguồn của câu định nghĩa;
  - câu trả lời giả trích nhãn đó thì qua hậu kiểm;
  - không có lời gọi `search` hay `lookup_concept` nào do mô hình giả phải gọi để tìm X.
- [ ] Câu hỏi nêu tên Y, tiêu điểm X: `linked` là Y, khối `focus` vẫn là X.
- [ ] Câu nối tiếp ("còn cái kia thì sao?") khi phiên đã liên kết Z, tiêu điểm X: `linked == [X, Z]`.
- [ ] Không có tiêu điểm: prompt hệ thống và tin nhắn gửi mô hình giống hệt từng byte với mã trước vé, và `context_hash` của dry-run cũng vậy. So với giá
  trị ghi từ main **trước** khi sửa, không so mã với chính nó.
- [ ] `focus_node_id` lạ hoặc không học được: lượt chạy như không có tiêu điểm, đầu vào mô hình giống hệt ca không tiêu điểm, `warnings` có
  `focus_ignored`, `focus_node_id` trả về là `null`.
- [ ] Tiêu điểm không lưu: lượt kế không gửi thì không có khối `focus`; bản ghi phiên và `assistant_state` không có khoá tiêu điểm.
- [ ] Ý bài giảng:
  - cache có bài `ready` thì khối có các ý;
  - không có cache, hay bài `failed`, thì khối không có ý;
  - trong mọi ca, use case bài giảng **không được gọi sinh** (mô hình bài giảng giả đếm 0 lần) và sổ chi không có dòng mới.
- [ ] Bài giảng rất dài: khối `focus` không quá `assistant_focus_tokens`, ý bị cắt trước.
- [ ] Thử sửa sai, ghi bảng vào báo cáo; mỗi dòng phải làm ít nhất một test đỏ:
  - bỏ kiểm khái niệm hợp lệ;
  - lưu tiêu điểm vào phiên;
  - cho phép sinh bài giảng;
  - bỏ trần;
  - đặt dòng chỉ dẫn vào prompt hệ thống.
- [ ] Đo kích thước khối `focus` cho mọi khái niệm của sáu cuốn phát triển (0 USD, không cache bài giảng), báo p50, p90 và max. Tham khảo đo của Claude
  ngày 2026-10-22: thẻ `why_here` có p50 khoảng 420 token, p90 tới khoảng 1.130 token ở doc-4. Khối `focus` không chép thẻ đó, nên phải nhỏ hơn nhiều.
- [ ] Test Pha B, kiến trúc, cổng toàn repo xanh. Bản ghi phát lại cũ của SA-32 vẫn phát lại khớp.

## Ngoài vé

- Gateway web, HTTP và giao diện: W-09 gửi kèm trường này. Người điều phối thêm vào W-09 theo mục 8 của bàn giao.
- Lượt thật có tiền: gộp vào [SA-55](55-luot-that-tro-ly-gop-08-10.md), thêm vài lượt có tiêu điểm.
- Không đổi luật nhắc nền, luật thẻ module hay hậu kiểm.
