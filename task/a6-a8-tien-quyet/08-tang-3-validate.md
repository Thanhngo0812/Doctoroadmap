# 08 — Tầng 3: validate toàn cục

**What to build:** Khi đã thấy toàn cảnh đồ thị, xử lý tồn đọng và giải mâu thuẫn: chu trình, cổng chất lượng,
cạnh thừa, và các cờ do 2b cùng người gán nhãn để lại.

Luật ở spec D11.

**Blocked by:** 06 — cả hai pass đều ghi vào cùng một nhật ký, nên tầng 3 chạy được khi mới có pass chính.

**Status:** ready-for-agent

- [ ] Xử lý tồn đọng: cặp hoãn của 2b, cụm hoãn của 2a, cờ khái niệm thiếu, cờ node sai.
- [ ] Chuẩn hoá sổ đăng ký kiểu; **không** tự quy tên nghi đồng nghĩa `requires` về `requires`.
- [ ] Chu trình: chạy trên đúng đồ thị con `requires` của node `learnable`; giải theo từng thành phần liên thông
      mạnh; thứ tự ưu tiên **giữ** cạnh đúng như D11, với confidence là tiêu chí **cuối cùng**.
- [ ] Chu trình hai cạnh ra **cờ danh tính** cho A13 trước khi nghĩ tới cắt cạnh.
- [ ] Cổng chất lượng chỉ đếm cạnh `requires`, mẫu số là node `learnable`.
- [ ] Cạnh thừa chỉ được **đánh dấu** kèm đường đi thay thế; **không xoá**.
- [ ] Node mới gán cụm incremental, không chạy lại gom cụm.
- [ ] Test theo seam luật thuần; đột biến tối thiểu: cắt theo confidence trước tiên, xoá cạnh thừa, chạy chu
      trình trên đồ thị đầy đủ, đếm cả cạnh kiểu mở vào cổng chất lượng.
