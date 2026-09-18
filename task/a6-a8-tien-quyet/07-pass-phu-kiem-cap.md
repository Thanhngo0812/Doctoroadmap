# 07 — Pass phụ: kiểm cặp nghi tiên quyết

**What to build:** Lượt đi theo trục còn lại để bù điểm mù của pass chính. Mô hình **chỉ phán các cặp nghi tiên
quyết** trong hồ sơ, không tự đề xuất cạnh mới.

Luật ở spec D8 và ADR 0008.

**Blocked by:** 06.

**Status:** done — 2026-09-16

- [x] Hồ sơ theo cặp: nguồn đề cử, trọng số từng kênh, chunk bằng chứng nguyên văn, mô tả hai node, thứ tự
      provenance, và đường đi gián tiếp đã có.
- [x] Bốn phán quyết của D8; cạnh sinh ra vẫn đi qua đúng executor của vé 06.
- [x] Hỏi **cả hai thứ tự**, hoặc hỏi một thứ tự chuẩn rồi kiểm nhất quán; hai lần lệch nhau thì hoãn.
- [x] Tỉa theo reachability **chỉ khi mọi cạnh trên đường đi đều có bằng chứng tường minh**; còn lại thì đưa
      đường đi vào hồ sơ.
- [x] Log đủ: cặp bị tỉa, cặp bị từ chối kèm lý do, cặp bị hoãn.
- [x] Cạnh ngoài hồ sơ bị từ chối và được ghi cờ.
- [x] Chạy thử thật trên cùng tài liệu ở vé 06: dán số phiên, lời gọi, chi phí, số cạnh thêm được vào vé.
- [x] Test theo hai seam; đột biến tối thiểu: cho tạo cạnh ngoài hồ sơ, bỏ lượt hỏi thứ hai, tỉa qua đường chưa
      có bằng chứng tường minh.

## Feedback nghiệm thu

- Cùng tài liệu `baocao-canhan`: 62 cặp ban đầu, 16 cặp tỉa bằng đường `requires` tường minh, 46 phiên cặp được
  phán, 93 lời gọi (gồm 1 retry), thêm 1 cạnh. Pass phụ dùng 131.423 input token và 6.493 output gồm thinking,
  chi phí 0,04259525 USD.
- Tổng pass chính + phụ: 233.382 input token, 11.369 output gồm thinking, 0,075399 USD.
- Mỗi cặp được hỏi ở cả hai thứ tự; kết quả lệch hướng/loại bị hoãn. Mọi cạnh `create` đi lại qua executor vé 06.
- Mutation đã thử và đều bị test bắt: cho cạnh ngoài hồ sơ; bỏ đối chiếu lượt hỏi thứ hai; tỉa qua đường có
  cạnh không tường minh.
