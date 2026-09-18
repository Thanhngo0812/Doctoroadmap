# 02 — Stage `clusters`: đồ thị chủ đề và cụm chủ đề

**What to build:** Chạy được từ bảng node canonical tới **cụm chủ đề** cho một tài liệu, **không một lời gọi mô
hình phán nào**, và lưu thành artifact `graph` ở stage `clusters`. Mỗi node — kể cả khái niệm lẻ và media mồ côi
— có `cluster_id`.

Luật ở spec D1, D2, D3, D17.

**Blocked by:** None — bắt đầu được ngay.

**Status:** done — 2026-09-16

- [x] Đồ thị chủ đề dựng bằng đúng ba kênh của D2, mỗi kênh tự chuẩn hoá trước khi hợp. **Không có ngưỡng cosine
      tuyệt đối nào trong code.**
- [x] Cạnh cắt theo phân vị; mọi tham số vào manifest.
- [x] Trọng số hạ theo bậc cho cả media lẫn chunk nhắc nhiều khái niệm; cảnh báo khi bậc media ≥ 5.
- [x] Gom cụm theo D3: trần cứng **đếm theo khái niệm** (media cỡ 0), **không** lọc thành phần liên thông lớn
      nhất, cụm 1–2 khái niệm sáp nhập theo luật tất định đã ghi trong D3.
- [x] Manifest ghi: tên thư viện, phiên bản, hàm mục tiêu, độ phân giải, seed, trần, thứ tự cạnh.
- [x] Không cài được thư viện Leiden thì đi đường lui ở D17 và **ghi rõ trong manifest** rằng hàm mục tiêu là
      modularity.
- [x] Chạy hai lần cho kết quả giống hệt; chạy lại khi không đổi gì thì `reused=true`.
- [x] Số đo trên bốn tài liệu cũ dán vào vé: số cụm, phân bố cỡ cụm, số node không có cạnh nào, thời gian chạy.
- [x] Test theo seam use case và seam luật thuần của spec; nộp danh sách đột biến, tối thiểu: bỏ luật trần, bật
      lọc thành phần liên thông lớn nhất, đổi seed mà manifest không đổi, cho media tính vào cỡ cụm.

## Feedback nghiệm thu

- Đã cài `leidenalg==0.12.0`, dùng `CPMVertexPartition` và `Optimiser` với cưỡng chế trần cộng đồng. Vì thư viện
  cài được nên đường lui modularity D17 không được kích hoạt; manifest ghi rõ CPM, phiên bản, resolution, seed,
  trần, mức cưỡng chế và thứ tự cạnh.
- Số đo artifact thật; cỡ là số **khái niệm** trong từng cụm, số 0 là cụm chỉ có media:

| Tài liệu | Số cụm | Phân bố cỡ cụm | Node cô lập | Giây |
|---|---:|---|---:|---:|
| `baocao-canhan` | 8 | 0, 3, 4, 4, 5, 6, 6, 8 | 1 | 2.485 |
| `naive-bayes` | 8 | 0, 3, 3, 4, 5, 5, 6, 8 | 2 | 2.657 |
| `nhap-mon-ml` | 17 | 0, 0, 3, 3, 3, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6, 8, 8 | 4 | 4.604 |
| `xstk-ch3-1` | 20 | 0, 0, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 6, 8, 10, 11, 12 | 4 | 9.496 |

- Mutation đã thử và đều bị test bắt: bỏ trần cứng; chỉ giữ thành phần liên thông lớn nhất; cố định seed trong
  manifest; tính media như khái niệm khi áp trần.
- Test luật thuần, seam use case, tính tất định và cache đều xanh.
