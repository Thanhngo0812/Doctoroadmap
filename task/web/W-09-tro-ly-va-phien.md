# W-09 — Trợ lý và phiên chat

**Nguồn chân lý:** [spec trợ lý 3](../../doc/tro-ly-3-spec.md), [ADR 0026](../../doc/adr/0026-tro-ly-3-gia-su-tu-nhien.md) (`answer-3`);
[spec Pha B2](../../doc/pha-b2-spec.md), mục 1–2, 8, 10 (`session-1`, `turn-1`, phần còn hiệu lực); [spec chức năng](../../doc/web-chuc-nang-spec.md),
mục 1 (công cụ buộc phía máy chủ, SSE), 7 (giới hạn tần suất), 8; [ADR 0017](../../doc/adr/0017-pham-vi-phien-la-noi-luu-neo-vao-khai-niem.md); spec thiết
kế, khung chat.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** W-07, SA-56/58 đã ghép; hợp đồng mới SA-66 sau SA-64 · **Trạng thái:**
sau W-08 chuẩn bị theo answer-3; cổng cuối chờ Claude nghiệm thu/ghép SA-66.

**Cập nhật mới nhất `a50955b`, 2026-10-23:** answer-3 dùng `answer_md` Markdown/LaTeX và `sources[]`; bỏ citations/outside_document_blocks cũ,
không còn insufficient_context/not_in_document. Stream progress/tool_call/delta/graph_card/artifact/final/failure; delta hiện ngay,
validation chỉ admin. Giữ graph_cards/artifacts/focus_node_id, phạm vi/quyền và client_turn_id.
Tiêu điểm đọc body_md lecture-3 từ cache, không sinh bài khi cache miss. Trần người học/ngày mới 1,00 USD theo ADR 0026,
UI vẫn dùng used_ratio/limited/resets_at, không bịa lượt/ngày. Độ trễ SA-60 là phép đo lịch sử; không coi 11,4s là độ trễ cố hữu của server giữ client.
Kiểm Markdown/LaTeX an toàn, nguồn đúng trang/nhãn lạ giữ chữ, validation không lọt, chữ không bị rút sau khi đã hiện, focus/cache-only 0 call.

**Đối chiếu 2026-10-23:** SA-56/SA-57 đã ghép `04c3efa`; SA-58 đã ghép `e2cfbac`. Gỡ chờ SA-56 ở cập nhật cũ bên dưới.
Gateway/composition phải cấp `get_lecture(concept, **kwargs)` và chuyển `cache_only` xuống `LectureUseCase.make`, như `composition_phase_b.py`;
`wayfinder/testing.py` hiện truyền `lecture.get` sai chữ ký, phải sửa trong phạm vi nối W-09 và kiểm cả focus/cache hit/cache miss lẫn tool call bình thường.
Không để cache miss của `cache_only=True` sinh bài mới. Search dùng enum chuẩn `uu_tien_module`/`ca_tai_lieu` của SA-58, không dịch chuỗi ở web.
Replay trước `e2cfbac` mang mô tả công cụ cũ: dùng fixture/fake đúng hợp đồng hiện tại ở 0 USD, không tự gọi model để làm lại replay.
Giữ Vertex tới khi chủ dự án yêu cầu đổi cho demo; SA-61 phải vào main trước khi chuyển Developer API.
SA-60 đo embedding Vertex khoảng 11,4 s/request, tổng p50 16,2 s: số đo của lượt Claude, không phải SLA mới hoặc lỗi kho JSON của web.
Giao diện phải hiện trạng thái chờ/công cụ và cho huỷ theo spec, không thêm chờ giả hoặc lộ thông tin triển khai cho người học.
Xem [kế hoạch](../../report/lenh-giao-viec-sau-w11-2026-10-23.md) và nhật ký mục 10 bàn giao.

**Phối hợp 2026-10-22:** nhận đề nghị của Claude ở mục 8 bàn giao và quyết định của chủ dự án về `focus_node_id`.
Giữ phần HTTP/gateway/React trong W-09 vì vé chưa triển khai; không tách vé mới. Lõi của hợp đồng thuộc
[SA-56](../sau-a10/56-tro-ly-focus-node-id.md), do Claude nghiệm thu/ghép. Không sửa use case trợ lý hoặc tự nhận SA-56 đã đạt.

## Vì sao

Trợ lý là phần "agent" của đề tài. Người học cần phiên chat ở trang lộ trình (phiên toàn lộ trình) và ở trang học (phiên của module), mở lại được phiên
cũ, và thấy trả lời hiện dần.

## Cần làm

**Gateway:** `create_session`, `list_sessions`, `rename_session`, `delete_session`, `list_turns`, `ask_stream`.
- **Phạm vi do web gửi:** `{kind: roadmap}` từ trang lộ trình; `{kind: module, node_ids}` từ trang học, với `node_ids` lấy từ đồ thị đã phát hành phía máy
  chủ, không tin danh sách do trình duyệt gửi.
- `ask_stream` truyền `owner`, `doc_id`, `graph_version` vào use case trợ lý. Công cụ của trợ lý chỉ nhận các giá trị này từ gateway.
- `ask_stream` nhận thêm `focus_node_id` tuỳ chọn của **từng lượt**, truyền nguyên giá trị vào use case SA-56. Gateway không tự tra, bỏ hoặc thay ID;
  lõi kiểm khái niệm trên đồ thị đang dùng. ID lạ vẫn cho lượt chạy, kết quả cuối có `focus_node_id = null` và cảnh báo `focus_ignored`.
  Không thêm trường tiêu điểm vào session/assistant_state, không ghi nhớ tiêu điểm của lượt trước.
- **Giới hạn tần suất:** `assistant_turns_per_minute` (10) mỗi người, đếm bằng `rate_limit_event`.

**HTTP:**
- `GET/POST /courses/{cid}/sessions` (lọc `roadmap_page`, `module:<id>`, `all`);
- `PATCH/DELETE /courses/{cid}/sessions/{sid}`;
- `GET /courses/{cid}/sessions/{sid}/turns`;
- `POST /courses/{cid}/sessions/{sid}/turns` trả **SSE** theo answer-3: progress/tool_call/delta/graph_card/artifact, rồi final hoặc failure.
- `client_turn_id` do trình duyệt sinh. Gửi lại cùng mã (mạng chập chờn) thì không tạo lượt thứ hai.
- Body POST lượt nhận `focus_node_id` tuỳ chọn; giữ nguyên focus đã dùng và cảnh báo hợp lệ theo lõi trong kết quả cuối answer-3; không tự bịa trường.
  Giữ kiểm membership, owner, graph/version phía máy chủ; tiêu điểm không mở quyền đọc ngoài khoá/phiên.

**Giao diện:**
- **khung chat** dùng chung cho hai trang: danh sách phiên (tiêu đề, ngày, câu hỏi cuối), nút "Phiên mới", đổi tên, xoá có xác nhận;
- **lượt:** câu hỏi; trả lời hiện dần; trích dẫn bấm được (mở trang sách); thẻ "nội dung ở module N — mở module"; ghi chú "module này đã đổi" khi phạm vi đã
  cũ;
- **tiến trình gọi công cụ** ("đang tìm trong sách…") hiện bằng dòng nhỏ;
- `status = daily_limit` hiện câu của mã và dải hết trần (W-16 làm phần dải);
- trang lộ trình có bộ lọc "tất cả".
- Trang học gửi ID khái niệm có bài giảng **đang mở** cùng mỗi lượt, kể cả bài tiên quyết thuộc module khác. Đổi bài thì lượt mới dùng ID mới;
  trang lộ trình không gửi trường này. Không lấy module của phiên thay cho khái niệm đang mở.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Thành viên B không liệt kê, không đọc lượt, không gửi câu hỏi vào phiên của A cùng khoá (`not_found`).
- [ ] Một kịch bản mô hình giả có lời gọi công cụ mang `owner` lạ trong tham số: công cụ vẫn chạy với `owner` của gateway; kho không có bản ghi nào của
  `owner` lạ.
- [ ] Phạm vi module với `node_ids` do trình duyệt gửi khác đồ thị: máy chủ dùng `node_ids` của đồ thị đã phát hành.
- [ ] Gửi lại cùng `client_turn_id` thì chỉ một lượt được lưu, và chỉ một lần gọi mô hình.
- [ ] HTTP/SSE với tiêu điểm hợp lệ: mock/use case nhận nguyên ID; answer-3 cuối trả đúng ID. Bỏ truyền ID hoặc thay bằng module ID thì test đỏ.
- [ ] HTTP/SSE với ID lạ: không lỗi chỉ vì ID lạ, cuối trả `null` và `focus_ignored`; không tự sinh bài giảng hay tạo usage ngoài lượt trợ lý.
- [ ] Cùng phiên, lượt sau không gửi tiêu điểm thì không kế thừa lượt trước; bản ghi session/assistant_state không có trường tiêu điểm.
- [ ] React: mở bài X rồi Y gửi đúng X/Y; mở bài tiên quyết gửi ID tiên quyết; hỏi từ trang lộ trình không gửi `focus_node_id`.
  Chạy bằng mô hình giả/phát lại trên main đã ghép SA-56, không gọi provider thật.
- [ ] Lượt thứ 11 trong một phút thì `rate_limited`.
- [ ] Trần ngày tính chung mọi khoá: chi ở khoá A làm khoá B trả `daily_limit` (đồng hồ giả, sổ chi bộ nhớ).
- [ ] Xoá phiên thì tài liệu do phiên tạo vẫn còn trong thư viện (bất biến 4 của Pha B2, kiểm lại qua HTTP).
- [ ] Ảnh chụp khung chat ở hai trang, phiên đã cũ, `daily_limit`; cỡ 390 px và 1280 px.

## Ngoài vé

Báo lỗi câu trả lời (W-19). Dời phiên giữa phạm vi (ngoài phạm vi Pha B2).
