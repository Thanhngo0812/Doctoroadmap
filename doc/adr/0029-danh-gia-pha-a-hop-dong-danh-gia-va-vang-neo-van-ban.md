# Đánh giá Pha A qua một hợp đồng đánh giá chung và vàng người neo vào văn bản

**Status:** accepted — 2026-10-26. Chủ dự án xác nhận qua 39 quyết định (kế hoạch `report/ke-hoach-danh-gia-pha-a-2026-10-26.md`, mục 15).
Spec: [danh-gia-pha-a-spec](../danh-gia-pha-a-spec.md). Bổ sung ADR 0009; không thay nó.

Mọi hệ được đánh giá (hệ chính, baseline, ablation, oracle, bản seminar không LLM) xuất ra một hợp đồng đánh giá JSON chung. Bộ chấm chỉ đọc hợp
đồng đó cộng vàng, không đọc artifact hay nhập mã pipeline. Vàng do người gán: hai sinh viên chuyên ngành mỗi chủ đề, độc lập, rồi hội ý. Vàng
ghi theo trang và câu nguyên văn, **không** lấy danh sách khái niệm hay id của máy. Kho khái niệm được chốt trước, rồi mới gán quan hệ trên kho
đó. Đầu ra máy được ghép với vàng qua một bước căn, có luật viết trước và nhật ký.

Đo được khi quyết định (2026-10-26):
- trong thước cũ, chỉ vàng tiên quyết A8 là của người; Q3, vàng A4 (416 mục) và câu neo (79/84) là của Claude hoặc AI;
- vàng A8 cũ gắn `canonical_version`, phải chuyển id mỗi lần A4 đổi (vé 17h); F1 giữa hai người gán của nó chỉ 0,35–0,42;
- PREAP đo được: khi người gán vừa thêm khái niệm vừa gán quan hệ, κ tụt từ 0,62 xuống 0,25 (VL §6.1).

## Considered Options

- **Giữ vàng gắn danh sách khái niệm của pipeline (giao thức ADR 0009 nguyên dạng).** Rẻ hơn, nhưng có ba vấn đề:
  - P/R có điều kiện trên tập khái niệm của máy;
  - mỗi lần A4 đổi phải chuyển id;
  - không chấm được B5 (LLM đọc thẳng) hay bản seminar trên cùng vàng.

  Loại.
- **Dùng benchmark tiên quyết nước ngoài, dịch sang tiếng Việt.** Loại vì:
  - các bộ đó không kèm cuốn sách để hệ đọc;
  - nhãn gán theo kiến thức nền, không bám văn bản;
  - tập kiểm cân bằng thổi precision lên;
  - văn bản dịch không phải giáo trình tiếng Việt thật.

  Nghiên cứu R-02 đã kiểm chín bộ và đi tới cùng kết luận.
- **Nhãn agentic làm vàng tập thử.** Là bạc (ADR 0009, đặc tả dữ liệu huấn luyện). Chỉ dùng cho bản nháp G1, G2 có người duyệt, và cho phát triển.
- **Mỗi hệ có một bộ chấm riêng đọc artifact trực tiếp, như các script nghiên cứu hiện nay.** Loại: không so được nhiều hệ trên cùng thước, và
  không có một lệnh chạy lại.

## Consequences

- **Bước căn thành một nguồn sai số mới.** Phải báo tỉ lệ căn tự động, tỉ lệ căn tay, và đồng thuận giữa người và Claude trên 20% số ca căn tay.
- **Hợp đồng có phiên bản (`danh-gia-xuat-1`).** Đổi hợp đồng thì bộ xuất và mọi adapter phải đổi theo.
- **Vàng không phải chuyển id khi pipeline đổi.** Nâng cấp khâu trong cửa sổ 01–06/11 không làm hỏng vàng.
- **Phạm vi P/R:** vẫn giới hạn trong chương có vàng, nhưng không còn có điều kiện trên tập khái niệm của máy.
- **Người gán cần nhiều công hơn**, vì phải tự lập kho khái niệm. Bù lại, một lần gán G3 cho vàng của A3, A4, A5 và tập đích của A8.
- **Mọi thay đổi sau khi giao thức được commit** (trước 07/11) được báo là hậu kiểm.
