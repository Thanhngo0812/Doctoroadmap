# SA-58 — Trợ lý: giá trị `scope` không khớp bộ tìm kiếm thật; ghi âm phản hồi nhiều vòng bị sai

**Nguồn:** lượt thật SA-55 (`report/pha-b-sa55-2026-10-22.md`, mục "Câu hỏi" 1 và 2); Claude đã kiểm lại trong mã ngày 2026-10-22.

**Ai:** agent Sonnet cài · Claude nghiệm thu · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** sẵn sàng

## Vì sao

Hai lỗi chỉ lộ ra khi chạy với mô hình và bộ tìm kiếm thật. Test hiện có không bắt được, vì chúng dùng BM25 cục bộ, bộ tìm giả nhận mọi `scope`, hay
bản ghi một vòng.

1. **`scope` của tìm kiếm.**
   - Trợ lý gửi xuống bộ tìm kiếm các giá trị `'ưu tiên module'` và `'all'`:
     - `assistant.py`, `_search` với giá trị mặc định;
     - công cụ `search_document` với giá trị mặc định;
     - lời gọi tìm kiếm trước vòng đầu;
     - `composition_phase_b.py`, `search`.
   - `SearchDocumentB.search` trong `application/phase_b/retrieval.py` chỉ nhận `uu_tien_module`, `ca_tai_lieu` hay `module:<index>`, nên ném `ValueError`.
   - Ở SA-55, phiên module hỏng ngay lượt đầu. Bộ chạy phải tự đổi chuỗi (`SCOPE_ALIASES`) mới chạy được.
   - Web dùng tìm kiếm thật, nên sẽ gặp lỗi này.
2. **Ghi âm phản hồi nhiều vòng.**
   - `RecordingToolSession.stream` trong `infrastructure/llm/phase_b.py` ghi `{"messages": messages}` bằng **tham chiếu** tới danh sách mà trợ lý nối thêm
     tin nhắn sau mỗi vòng.
   - Mỗi lần ghi tệp, bản ghi của vòng trước có thêm tin nhắn của vòng sau. Phát lại vì vậy báo "no unused session matching".
   - SA-55 phải truyền bản sao sâu trong bộ chạy để né lỗi này.

## Cần làm

- **`scope`:** trợ lý và runtime chỉ dùng giá trị chuẩn của bộ tìm kiếm:
  - phiên module: `uu_tien_module`;
  - phiên lộ trình: `ca_tai_lieu`.

  Mô tả công cụ `search_document` phải liệt kê các giá trị hợp lệ để mô hình biết. Mô hình gửi giá trị lạ thì trả lỗi có cấu trúc, như luật tham số sai hiện
  có. Không thêm bảng đổi chuỗi tiếng Việt vào bộ tìm kiếm.
- **Ghi âm:** `RecordingToolSession.stream` ghi bản sao sâu của `messages` tại thời điểm gọi. Kiểm thêm `ask_json`, `stream_json` xem có cùng lỗi tham chiếu
  không.
- Không đổi prompt, luật hậu kiểm hay hành vi nào khác.

## Tiêu chí nghiệm thu

- [ ] **Test qua bộ tìm kiếm thật.** Dựng trợ lý với `SearchDocumentB` thật, embedding giả và đồ thị tổng hợp nhỏ. Một lượt ở phiên module và một lượt ở
  phiên lộ trình đều chạy được. Test này đỏ trên mã cũ (`ValueError`).
- [ ] **Test công cụ:** mô hình giả gọi `search_document` không kèm `scope`, và kèm một `scope` lạ. Ca không kèm thì dùng giá trị chuẩn, ca lạ thì nhận lỗi có
  cấu trúc; không ca nào làm hỏng cả lượt.
- [ ] **Test ghi âm rồi phát lại** một lượt hai vòng (vòng 1 gọi công cụ, vòng 2 trả lời): phát lại khớp. Test này đỏ trên mã cũ.
- [ ] Thử sửa sai và ghi bảng vào báo cáo; mỗi dòng phải làm ít nhất một test đỏ:
  - trả lại `'ưu tiên module'`;
  - bỏ bản sao sâu.
- [ ] Bản ghi mẫu SA-55 (`tests/fixtures/phase_b/sa55-replay-sample.json`) vẫn phát lại khớp. Test Pha B, test kiến trúc và cổng toàn repo xanh. Cổng chạy
  trong worktree đã chép hai gói dữ liệu phát triển, và không chạy chồng với cổng khác.
