# SA-06 — Tên và mô tả module do LLM đặt

**Nguồn chân lý:** [ADR 0014](../../doc/adr/0014-ten-module-do-llm-dat.md); [spec Pha B](../../doc/pha-b-spec.md), mục 2, bất biến 12 và 13;
[báo cáo tên module](../../report/nghien-cuu-ten-va-mo-ta-module-2026-10-11.md), mục 6.1a, 6.2, 6.3.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** dưới 0,1 USD cho sáu cuốn (khoảng 142 lời gọi), dry-run trước, chủ dự án duyệt trong trần
chung 16 USD · **Chặn bởi:** 05 · **Trạng thái:** ready-for-agent

## Vì sao

Chủ dự án chốt: "sau A10 cứ LLM thoải mái", nên LLM đặt tên và viết mô tả cho mọi module, dùng cho cả đồ án lẫn seminar.

## Cần làm

**Mỗi module một lời gọi**, đầu vào gồm:
- **khái niệm của module:** `display_name` kèm mô tả A5 cắt còn tối đa 200 ký tự, theo thứ tự dãy học;
- **tiêu đề tác giả:** đường mục đã làm sạch (của mục đa số và của tổ tiên chung), cờ "trùng đúng một mục";
- **ứng viên:** 3–5 tên do mã xếp hạng theo độ phủ, độ phân biệt với module ±1, độ trung tâm và lời của tác giả (báo cáo, mục 6.3);
- **đối chứng:** tên và khái niệm của module ±1, ghi "không thuộc module này";
- **ràng buộc:** viết từ nguồn giới hạn dùng chung, cùng giá trị với luật kiểm.

Prompt nói rõ: nếu module trùng một mục và tiêu đề tốt thì mặc định giữ tiêu đề tác giả.

**Đầu ra:** `title`, và `description` gồm 1–2 câu, mỗi câu có `node_ids` (`module_ids` là tuỳ chọn).

**Năm luật kiểm** theo spec mục 2:
- từ vựng có căn cứ;
- không mượn từ module kề;
- `node_ids` hợp lệ;
- hình thức tên;
- mảnh tên nguyên vẹn.

Hỏng luật nào cũng đi đường lùi của vé 05 và ghi luật đã hỏng vào `naming_flags`.

**Cache và cấu hình:**
- Khoá cache gồm đầu vào chuẩn hoá, kể cả tên module kề.
- Nhiệt độ 0. Tăng phiên bản thuật toán của khâu tên.
- Khâu vẫn qua chốt chi và `--dry-run` của `roadmap`. Có thêm lệnh chạy riêng khâu tên trên artifact A10 có sẵn.

**Trường kết quả:** `title_source = llm`, `description_source = llm`; `roadmap.html` hiện mô tả.

## Tiêu chí nghiệm thu

- [ ] Dry-run trên sáu cuốn: số lời gọi (bằng số module) và USD ước.
- [ ] Sau khi chủ dự án duyệt, chạy thật. Báo cho từng cuốn:
  - số tên do LLM đặt và số tên rơi về đường lùi, kèm luật đã hỏng;
  - số câu bị loại vì mượn từ module kề;
  - USD và phút.
- [ ] Test với mô hình giả theo kịch bản, mỗi cái thấy đỏ trước:
  - từ mượn của module kề dẫn tới đường lùi;
  - từ bịa dẫn tới đường lùi;
  - `node_ids` ngoài module bị loại;
  - tên có số mục bị loại;
  - tên trùng với module ±2 bị loại;
  - module trùng một mục, tiêu đề tốt, mô hình trả đúng tiêu đề đó thì giữ;
  - đổi một giới hạn ở nguồn chung thì prompt đổi theo.
- [ ] Chạy lại thì 0 lời gọi. Đổi tên module kề thì chỉ module bị ảnh hưởng được gọi lại.
- [ ] Ghi lại các phản hồi thật để phát lại thành test hồi quy 0 USD.
- [ ] Claude đọc toàn bộ tên và mô tả của sáu cuốn, ghi phán xét vào vé.

## Ngoài vé

Hai việc không thuộc vé này:
- chấm mù và chọn biến thể (vé 20);
- sửa A1 và A2.
