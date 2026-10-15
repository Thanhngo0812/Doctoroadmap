# SA-12 — Bài giảng LLM có kiểm và cache

**Nguồn chân lý:** [ADR 0011](../../doc/adr/0011-noi-dung-hoc-sinh-khi-can-cache-theo-ngu-canh.md); [spec Pha B](../../doc/pha-b-spec.md), mục 1,
5, 8; bất biến 1, 3, 5, 6, 13; [báo cáo bài giảng](../../report/nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md), mục 4.1–4.5, 4.7.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** lượt thử 10 khái niệm, dưới 0,05 USD, dry-run trước · **Chặn bởi:** 01, 11 ·
**Trạng thái:** ready-for-agent

## Vì sao

Phần diễn giải, ví dụ, phân biệt và câu tự kiểm tra cần LLM. Nhưng mọi ý LLM viết về sách phải được kiểm trước khi tới người học, và bài phải được
dùng chung để giữ chi phí khoảng 0,002 USD mỗi bài.

## Cần làm

**Lắp ngữ cảnh** theo spec mục 8:
- **Thứ tự các khối:** thẻ khái niệm → câu định nghĩa → chunk dạy (S1) → tối đa 2 chunk định nghĩa thêm → tối đa 3 tiên quyết (`N#`, `Q#`) → tối
  đa 3 cạnh mở có bằng chứng (`R#`) → hình xác nhận → tối đa 1 chunk bài tập → tên khái niệm học sau → nhắc nhiệm vụ.
- **Ngân sách:** trần mềm 2.500 token, kèm thứ tự bỏ khối khi vượt; không bao giờ cắt chunk dạy hay câu định nghĩa.
- **Công thức:** đưa dạng `⟦CTk: chữ thô⟧`.
- **Mô tả A5 là bản nháp chưa kiểm:** không nạp.
- **Nhiều khái niệm cùng một chunk dạy:** chỉ dẫn "chỉ giảng khái niệm này".

**Lời gọi JSON** (chưa stream ở vé này) theo lược đồ của báo cáo mục 4.3. Nhiệt độ 0. Giới hạn lấy từ nguồn chung.

**Luật K1–K9** theo spec mục 8:
- sinh lại 1 lần với K1, K6, K8;
- bỏ ý với K2, K3, K5, K7;
- gắn cờ với K4;
- hỏng hết thì dùng bản của vé 11 (`status = fallback`).

**Nội dung ngoài sách:**
- `outside_document` chỉ được ở `example` và `contrasts`, tối đa 1 ý mỗi bài, không trích dẫn.
- K5 miễn cho ý này nhưng đếm riêng.

**Cache:**
- `lecture_key` là băm của tài liệu, khái niệm, `context_hash`, prompt, lược đồ, mô hình, cấu hình sinh và phiên bản hợp đồng.
- Chống sinh trùng, cache âm, sổ chi: dùng phần của vé 01.

**Lệnh CLI bài giảng:** có `--dry-run` và `--allow-spend`; chế độ không LLM vẫn còn.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả theo kịch bản, mỗi luật thấy đỏ trước:
  - câu trích bịa thì bỏ ý;
  - nhãn lạ thì bỏ ý;
  - ký hiệu toán mới thì bỏ ý;
  - ý ngoài sách nằm ở phần giải thích thì bỏ;
  - K8 sinh lại một lần rồi dùng bản lùi;
  - K6 phát hiện lặp thì sinh lại.
- [ ] Test cache:
  - cùng ngữ cảnh thì không gọi lần hai;
  - đổi chữ chunk thì gọi lại;
  - tăng phiên bản đồ thị mà ngữ cảnh không đổi thì không gọi;
  - hai yêu cầu đồng thời thì một lời gọi.
- [ ] Đổi giới hạn ở nguồn chung thì prompt đổi theo.
- [ ] Lượt thật 10 khái niệm (doc-1, doc-4, nhap-mon-ml), sau dry-run và chủ dự án duyệt. Báo:
  - USD mỗi bài;
  - giây tới khi xong bài;
  - tỉ lệ bỏ ý theo từng luật;
  - số bài rơi về bản lùi.

  Ghi lại phản hồi để phát lại.

## Ngoài vé

Hai việc không thuộc vé này:
- stream và tải trước (vé 13);
- chỉnh ngưỡng K4, chấm người, nhánh nhiệt độ (vé 21).
