# 07 — Chấm theo luật đăng ký trước

**What to build:** Kết luận nhận hay không nhận quan hệ mở, bằng đúng luật ở ticket 00, không đổi luật sau khi thấy số.

**Người làm:** Claude (reviewer)

**Blocked by:** 06 — Chạy nhánh thử

**Status:** done — **không nhận** (trượt cổng 1), 2026-09-14

- [x] Áp năm cổng ở ticket 00 lên nhánh `gemini-3.1-flash-lite-relations-v3`.
- [x] Lấy mẫu 30 quan hệ không phải `subtype_of`, seed 42; ít hơn 30 thì lấy hết. Đọc câu trích của từng quan hệ và gán
      đúng/sai theo cả kiểu lẫn chiều. Công bố danh sách mẫu kèm nhãn.
- [x] Ghi các số phụ ở ticket 00:
  - precision `subtype_of` tăng bao nhiêu;
  - recall trên 47 và trên 44 cặp;
  - số quan hệ theo kiểu, và các tên dùng thay `subtype_of`;
  - so với A3: trùng, khác kiểu, cặp mới;
  - quan hệ 2a trên cặp có nhãn.
- [x] Soi riêng những cặp mà mặc định từng gắn `subtype_of` sai, xem giờ chúng thành kiểu gì.
- [x] Ghi kết luận vào báo cáo chạy thật (mục A/B) và vào feedback. Trượt thì báo chủ dự án kèm số, và không chỉnh prompt
      trên bộ vàng này.

## Kết quả

Tôi chấm độc lập bằng script riêng; số khớp đúng với ticket 06.

| Cổng | Ngưỡng | Mặc định (v1) | Quan hệ mở (v3) | |
|---|---|---:|---:|---|
| 1. Precision gộp | ≥ 0,95 | 1,000 | **0,809** (38/9/9) | ❌ |
| 2. F1 gộp | ≥ 0,775 | 0,795 | 0,809 | ✅ |
| 3. Precision `subtype_of` | ≥ 0,635 | 0,635 | 0,688 (22 đúng, 10 sai) | ✅ |
| 4. Cụm hỏng hẳn | ≤ 1 | 0 | 0 (0 lượt thử hỏng) | ✅ |
| 5. Mẫu 30 quan hệ đúng | ≥ 60% | — | 73% (22/30) | ✅ |

**Kết luận: không nhận.** Theo luật, trượt một cổng là đủ.

## Vì sao precision gộp gãy

Cả 9 ca gộp sai đều do mô hình trực tiếp phán *cùng*, không ca nào do code hay do bắc cầu. Có hai kiểu lỗi:

- **Node thành nhóm chủ đề.** Mô hình gộp những thứ khác nhau với lý do chung chung:
  - `Bài toán phân loại` + `Bài toán phân cụm` + `Bài toán hồi qui`: *"specific types of machine learning problems"*;
  - `Business understanding` + `Analytic approach` + `Data understanding`: *"steps in the process"*.
- **Gộp mà vẫn nói là cha–con.** Ví dụ `Pessimistic Locking` + `Database Locking` chung node, trong khi trong cùng đầu
  ra mô hình lại ghi `Pessimistic Locking subtype_of Database Locking`.

Bằng chứng: 9/51 node gộp chứa một quan hệ nối hai nhóm của chính nó (6 `subtype_of`, 2 `precedes`, 1 `example_of`,
2 `same_as`). 7/9 ca gộp sai nằm trong những node đó. Validator loại quan hệ mâu thuẫn, nhưng lần gộp sai vẫn được áp.
Để so sánh, prompt v1 chỉ có 2/70 đề xuất `subtype_of` rơi vào cùng node.

Nguyên nhân gốc nằm ở prompt v3 tôi viết. Prompt v1 buộc "cha–con ⇒ tách node **và** ghi `subtype_of`" trong cùng một
vế. Prompt v3 tách hai ý đó ra hai chỗ, nên mô hình không còn gắn quan hệ với việc tách node.

Có thêm một kiểu rò theo chiều ngược lại: `Data preparation equivalent_to Tiền xử lý dữ liệu`. Mô hình cho là cùng
một thứ nhưng vẫn để hai node riêng.

## Giả thuyết "bị ép chọn" — đúng một phần

Số phận của 19 cặp có nhãn mà mặc định gắn `subtype_of` sai:

| Nhãn vàng | Ở v3 |
|---|---|
| *liên quan* (11) | 6 chuyển sang kiểu khác đúng hơn (`statistic_of`, `tests`, `component_of` ×2, `aims_to_achieve`, `related_to`); 5 vẫn là `subtype_of` |
| *cùng* (8) | 6 đã được gộp; 1 thành `solves`; 1 tách, không cạnh |

Số phụ:
- precision `subtype_of`: 0,635 → 0,688;
- recall `subtype_of`: 35/47 → 24/47. Tính trên 44 cặp (bỏ 3 cặp bộ phận) là 24/44. Cả 3 cặp bộ phận giờ được gắn
  `component_of`, đúng kiểu, nhưng bộ vàng chấm là mất;
- không có tên nào dùng thay `subtype_of` (`is_a`, `kind_of`…); `example_of` xuất hiện 4 lần;
- cạnh 2a: 73. Trong đó 5 trùng bộ ba với A3, 15 cùng cặp nhưng khác kiểu, 53 là cặp mới. Có 34 cạnh không phải
  `subtype_of`, với 18 tên kiểu khác nhau;
- quan hệ 2a (khác `subtype_of`) trên cặp có nhãn: 2 cặp *cùng*, 4 cặp cha–con, 22 cặp *liên quan*, 0 cặp *khác*.

## Mẫu 30 quan hệ (seed 42; Claude gán, không phải người độc lập)

Đúng (22):
- `Maximum Likelihood Estimation uses Likelihood`
- `Kiến trúc Hub - Client used_with WebSocket`
- `Thu thập dữ liệu từ internet example_of Thu thập dữ liệu`
- `Ứng dụng của phương trình hồi quy tuyến tính mẫu uses Đường hồi quy tuyến tính mẫu`
- `Tỉ lệ mẫu tổng quát statistic_of Mẫu tổng quát`
- `Thiết kế Cơ sở dữ liệu component_of Thiết kế hệ thống`
- `Kiểm định tham số contrasts_with Kiểm định phi tham số`
- `Quyết định chấp nhận H informs Kết luận cuối cùng`
- `Độ chính xác component_of Ước lượng tỉ lệ`
- `Khai phá dữ liệu uses Dữ liệu`
- `Ước lượng trung bình estimates Trung bình tổng thể`
- `Kiểm định giả thiết thống kê tests Giả thiết thống kê`
- `Hàm mật độ xác suất related_to Likelihood`
- `Xác suất p(x i |c) example_of Likelihood`
- `Biến đổi dữ liệu component_of Tiền xử lý dữ liệu`
- `Phương sai mẫu hiệu chỉnh related_to Phương sai mẫu`
- `Làm sạch dữ liệu component_of Tiền xử lý dữ liệu`
- `Quy tắc quyết định produces Quyết định chấp nhận H`
- `Quá khớp contrasts_with Kém khớp`
- `Lấy mẫu aims_to_achieve Tính đại diện`
- `Tiêu chuẩn kiểm định χ 0 2 uses Phân phối χ 2`
- `Mẫu hai chiều rearranged_form_of Mẫu tương quan cặp`

Sai (8):
- `Mutex uses Race Condition` — sai kiểu: Mutex dùng để giải quyết race condition.
- `Kiểm định giả thiết thống kê solves Bài toán kiểm định giả thiết thống kê` — câu trích không nêu; bộ vàng coi hai tên
  là một.
- `Kiến trúc phân lớp example_of Thiết kế hệ thống` — không câu nào nêu.
- `Bài toán tìm kích thước mẫu uses Kích thước mẫu` — sai kiểu: bài toán này đi tìm kích thước mẫu.
- `Database Transaction supports Thiết kế Cơ sở dữ liệu` — không câu nào nêu.
- `Tỉ lệ mẫu computed_by Tổng thể` — sai: tỉ lệ mẫu tính từ mẫu, không phải từ tổng thể.
- `Cây quyết định contrasts_with Rừng ngẫu nhiên` — văn bản chỉ liệt kê hai mô hình cạnh nhau.
- `Bài toán học máy component_of Học máy` — kiểu gượng; bộ vàng gán *liên quan*.

Theo luật ở ticket 00, không chỉnh prompt rồi chấm lại trên bộ vàng này. Hướng đi tiếp do chủ dự án quyết; xem feedback
vòng 25.
