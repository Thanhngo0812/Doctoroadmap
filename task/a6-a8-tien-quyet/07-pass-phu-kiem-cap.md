# 07 — Pass phụ: kiểm cặp nghi tiên quyết

**What to build:** Lượt đi theo trục còn lại để bù điểm mù của pass chính. Mô hình **chỉ phán các cặp nghi tiên
quyết** trong hồ sơ, không tự đề xuất cạnh mới.

Luật ở spec D8 và ADR 0008.

**Blocked by:** 06.

**Status:** ready-for-agent

- [ ] Hồ sơ theo cặp: nguồn đề cử, trọng số từng kênh, chunk bằng chứng nguyên văn, mô tả hai node, thứ tự
      provenance, và đường đi gián tiếp đã có.
- [ ] Bốn phán quyết của D8; cạnh sinh ra vẫn đi qua đúng executor của vé 06.
- [ ] Hỏi **cả hai thứ tự**, hoặc hỏi một thứ tự chuẩn rồi kiểm nhất quán; hai lần lệch nhau thì hoãn.
- [ ] Tỉa theo reachability **chỉ khi mọi cạnh trên đường đi đều có bằng chứng tường minh**; còn lại thì đưa
      đường đi vào hồ sơ.
- [ ] Log đủ: cặp bị tỉa, cặp bị từ chối kèm lý do, cặp bị hoãn.
- [ ] Cạnh ngoài hồ sơ bị từ chối và được ghi cờ.
- [ ] Chạy thử thật trên cùng tài liệu ở vé 06: dán số phiên, lời gọi, chi phí, số cạnh thêm được vào vé.
- [ ] Test theo hai seam; đột biến tối thiểu: cho tạo cạnh ngoài hồ sơ, bỏ lượt hỏi thứ hai, tỉa qua đường chưa
      có bằng chứng tường minh.
