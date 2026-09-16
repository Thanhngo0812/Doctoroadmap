# 02 — Stage `clusters`: đồ thị chủ đề và cụm chủ đề

**What to build:** Chạy được từ bảng node canonical tới **cụm chủ đề** cho một tài liệu, **không một lời gọi mô
hình phán nào**, và lưu thành artifact `graph` ở stage `clusters`. Mỗi node — kể cả khái niệm lẻ và media mồ côi
— có `cluster_id`.

Luật ở spec D1, D2, D3, D17.

**Blocked by:** None — bắt đầu được ngay.

**Status:** ready-for-agent

- [ ] Đồ thị chủ đề dựng bằng đúng ba kênh của D2, mỗi kênh tự chuẩn hoá trước khi hợp. **Không có ngưỡng cosine
      tuyệt đối nào trong code.**
- [ ] Cạnh cắt theo phân vị; mọi tham số vào manifest.
- [ ] Trọng số hạ theo bậc cho cả media lẫn chunk nhắc nhiều khái niệm; cảnh báo khi bậc media ≥ 5.
- [ ] Gom cụm theo D3: trần cứng **đếm theo khái niệm** (media cỡ 0), **không** lọc thành phần liên thông lớn
      nhất, cụm 1–2 khái niệm sáp nhập theo luật tất định đã ghi trong D3.
- [ ] Manifest ghi: tên thư viện, phiên bản, hàm mục tiêu, độ phân giải, seed, trần, thứ tự cạnh.
- [ ] Không cài được thư viện Leiden thì đi đường lui ở D17 và **ghi rõ trong manifest** rằng hàm mục tiêu là
      modularity.
- [ ] Chạy hai lần cho kết quả giống hệt; chạy lại khi không đổi gì thì `reused=true`.
- [ ] Số đo trên bốn tài liệu cũ dán vào vé: số cụm, phân bố cỡ cụm, số node không có cạnh nào, thời gian chạy.
- [ ] Test theo seam use case và seam luật thuần của spec; nộp danh sách đột biến, tối thiểu: bỏ luật trần, bật
      lọc thành phần liên thông lớn nhất, đổi seed mà manifest không đổi, cho media tính vào cỡ cụm.
