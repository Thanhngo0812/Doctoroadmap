# 06 — Pass chính trích mở, định tuyến và executor

**What to build:** Mô hình đọc từng (siêu) section của chương — hoặc từng cụm chủ đề, tuỳ định tuyến — rồi đề
xuất cạnh `requires` giữa các khái niệm trong danh sách của phiên. Executor kiểm từng thao tác bằng code và ghi
vào một nhật ký chỉ-thêm. Sau vé này, artifact có stage `edges` với phần cạnh của pass chính.

Luật ở spec D6, D7, D9, D10 và ADR 0008. Đây là vé nặng nhất của đợt.

**Blocked by:** 01, 03.

**Status:** done — 2026-09-16

- [x] Định tuyến theo D6: ngưỡng 20 khái niệm học được cho một phiên duy nhất; theo chương khi cây khai báo có
      phân cấp thật; theo cụm chủ đề khi cây thoái hoá. Lựa chọn và lý do vào manifest.
- [x] Gói đầu vào đủ năm phần của D7, trong đó có **khái niệm được nhắc ở đây nhưng dạy nơi khác**, lấy từ
      mention map.
- [x] Mô hình được hỏi theo **khái niệm đích**, kiểu PREAP: cần biết gì trước để hiểu nó **như đoạn này trình
      bày**.
- [x] Đầu ra đúng hợp đồng ở D7: cạnh kèm loại bằng chứng và chunk bằng chứng, cộng danh sách cờ. **Mô hình không
      trả confidence.**
- [x] Chỉ sinh `requires`. Khái niệm ngoài danh sách chỉ được ghi cờ.
- [x] **Không tool:** không tìm node, không đọc thêm chunk, không thêm cạnh đồng bộ.
- [x] Executor kiểm đủ bảy luật ở D9, mỗi luật trả lỗi riêng; đúng một lượt retry.
- [x] Phiên ghi đề xuất vào nhật ký chỉ-thêm; một bộ gộp tất định áp chúng, nên kết quả không phụ thuộc phiên nào
      xong trước.
- [x] Loại bằng chứng quy ra confidence bằng code theo D10; loại suy đoán bị từ chối; mỗi cạnh ghi quan hệ thứ tự
      tính từ provenance.
- [x] Checkpoint sau mỗi phiên; chạy lại khi không đổi gì thì 0 lời gọi.
- [x] Chạy thử thật trên **một** tài liệu cũ: dán số lời gọi, token, chi phí, số cạnh, số cờ vào vé.
- [x] Test theo hai seam; đột biến tối thiểu: cho cạnh trỏ ra ngoài danh sách, bỏ kiểm chunk bằng chứng nhắc hai
      đầu, nhận confidence do mô hình khai, chặn chu trình đồng bộ, đổi thứ tự phiên làm đổi kết quả.

## Feedback nghiệm thu

- Chạy thật `baocao-canhan` bằng `gemini-3.1-flash-lite`: 16/16 phiên hoàn tất, 16 lời gọi, 101.959 input
  token, 4.876 output gồm thinking, 28 cạnh, 1 cờ, chi phí 0,03280375 USD.
- Artifact checkpoint sau từng phiên; chạy lại toàn pipeline không đổi trả `reused=true` và 0 lời gọi.
- Định tuyến, năm phần input, prompt PREAP không tool, schema và bảy guard được tách ở seam luật thuần và seam
  use case.
- Mutation đã thử và đều bị test bắt: nhận cạnh canonical nhưng ngoài danh sách phiên; bỏ kiểm chunk nhắc cả
  hai đầu; bỏ ánh xạ confidence bằng code; chặn chu trình ngay trong phiên; gộp theo thứ tự hoàn tất.
