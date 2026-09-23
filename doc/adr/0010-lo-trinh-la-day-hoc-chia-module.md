# Lộ trình là một dãy học chia module, không phải các tầng học song song

**Status:** accepted — 2026-09-23

Lộ trình từ nay là **một dãy học** — một phép sắp topo của đồ thị `requires`, luôn chọn khái niệm sẵn sàng đứng sớm nhất
theo thứ tự dạy của tài liệu — được **chia thành module liền mạch**, mỗi module tối đa `W` khái niệm và có thứ tự bên trong.
Stage cũ (tầng Coffman–Graham, mọi khái niệm trong một tầng học song song được) thôi là đơn vị trình bày của sản phẩm.

Đo trên hai chương vàng (`report/ke-hoach-v2-do-thi-va-lo-trinh-chuan.md` §3): sách tự đặt ngược 5/40 và 7/61 cạnh vàng;
dãy học chỉ còn 2/40 và 5/61; lộ trình Coffman–Graham, kể cả khi đọc mỗi tầng theo thứ tự sách, là 2/40 và 9/61. Muốn giữ
một thứ tự tốt mà vẫn chia thành tầng song song thì phải cắt thành 98 và 142 tầng. Tầng Coffman–Graham nằm gọn trong một
mục của sách 1/30 lần; module liền mạch 16/34.

**Considered Options**

- *Giữ tầng song song, xếp bằng Coffman–Graham.* Tối ưu đúng số tầng, nhưng mọi cặp không có cạnh bị đặt theo cách phá
  thế hoà tuỳ ý; cách mặc định tệ hơn cả 30 cách ngẫu nhiên trên hai đồ thị thưa, và tầng gần như không bao giờ mạch lạc.
- *Đi đúng thứ tự sách.* Mạch lạc nhất, nhưng vi phạm cạnh máy (189 cặp trên `doc-1`) và sai ~12% cạnh vàng — bỏ phí
  đúng phần giá trị mà đồ thị đem lại.
- *Sắp topo tối ưu khoảng cách Kendall tới thứ tự sách.* Khó hơn nhiều, chưa có bằng chứng hơn phép sắp tham lam.
- *Giữ chữ "stage" với nghĩa mới.* Bị bác: bất biến cũ "không cạnh nào nối hai khái niệm trong cùng stage" nằm trong
  spec và test; đổi nghĩa mà giữ tên thì mọi chỗ đọc cũ đều hiểu sai.

**Consequences**

- Hợp đồng artifact A10 đổi: `sequence`, `modules`, `chunk_module_map` thay `stages`, `chunk_stage_map`. Bộ chấm đọc được
  cả artifact cũ để so lịch sử.
- Thứ tự dạy của tài liệu đi vào bộ xếp, nên τ so thứ tự sách từ nay là **độ bám sách**, không còn là bằng chứng chất
  lượng. Đối chứng độc lập là lỗi thứ tự trên bộ vàng (Q6). Điều V8 của spec A9–A10 cấm được bỏ, có ghi lý do.
- Pha B mở khoá, làm quiz và lọc RAG theo module (`module_index <= hiện tại`). Trường `stage_id` của chỉ mục vector chưa
  có dữ liệu; đổi tên khi triển khai A12.
- Coffman–Graham giữ lại làm biến thể đối chứng trong thí nghiệm, không nằm trong chuỗi sản phẩm.
- Chia module theo ranh giới mục thì tự tối ưu chỉ số "module gọn trong một mục"; chỉ số ấy chỉ là kiểm tra tỉnh táo.
  Bằng chứng về độ mạch lạc phải do người chấm mù.
