# 08 — Tầng 3: validate toàn cục

**What to build:** Khi đã thấy toàn cảnh đồ thị, xử lý tồn đọng và giải mâu thuẫn: chu trình, cổng chất lượng,
cạnh thừa, và các cờ do 2b cùng người gán nhãn để lại.

Luật ở spec D11.

**Blocked by:** 06 — cả hai pass đều ghi vào cùng một nhật ký, nên tầng 3 chạy được khi mới có pass chính.

**Status:** done — 2026-09-16

- [x] Xử lý tồn đọng: cặp hoãn của 2b, cụm hoãn của 2a, cờ khái niệm thiếu, cờ node sai.
- [x] Chuẩn hoá sổ đăng ký kiểu; **không** tự quy tên nghi đồng nghĩa `requires` về `requires`.
- [x] Chu trình: chạy trên đúng đồ thị con `requires` của node `learnable`; giải theo từng thành phần liên thông
      mạnh; thứ tự ưu tiên **giữ** cạnh đúng như D11, với confidence là tiêu chí **cuối cùng**.
- [x] Chu trình hai cạnh được giữ và ra cờ trung tính `two_way_requires` kèm hai cạnh/bằng chứng; không làm trượt cổng.
- [x] Cổng chất lượng chỉ đếm cạnh `requires`, mẫu số là node `learnable`.
- [x] Cạnh thừa chỉ được **đánh dấu** kèm đường đi thay thế; **không xoá**.
- [x] Node mới gán cụm incremental, không chạy lại gom cụm.
- [x] Test theo seam luật thuần; đột biến tối thiểu: cắt theo confidence trước tiên, xoá cạnh thừa, chạy chu
      trình trên đồ thị đầy đủ, đếm cả cạnh kiểu mở vào cổng chất lượng.

## Feedback nghiệm thu

- Tầng validate hợp nhất backlog từ 2a/2b, cờ thiếu/sai node; node đã giải quyết được gán vào centroid cụm gần
  nhất mà không chạy lại Leiden.
- Bộ giải SCC chỉ nhận `requires` giữa node `learnable`, tìm feedback-edge set nhỏ nhất tới trần 16 cạnh rồi dùng
  heuristic `eades_priority`; ưu tiên giữ lần lượt
  loại bằng chứng, thứ tự provenance, số nguồn độc lập, rồi mới confidence. Chu trình hai cạnh được giữ nguyên,
  sinh cờ `two_way_requires` cho A13 và không ảnh hưởng cổng chất lượng.
- Cạnh thừa còn nguyên trong artifact và có `redundant_via`; tên kiểu nghi đồng nghĩa `requires` chỉ bị gắn cờ.
- Lần chạy lại `baocao-canhan` ở v77 phát hiện 1 cờ `two_way_requires`, giữ đủ hai cạnh và bằng chứng; quality gate
  đạt với 25 cạnh / 36 khái niệm, 8 node cô lập, nên A10 chạy mode `requires`.
- Mutation đã thử và đều bị test bắt: đưa confidence lên đầu; xoá cạnh thừa; cho cạnh mở tham gia chu trình; đếm
  cạnh mở vào cổng chất lượng; cắt nhầm chu trình hai cạnh đã dành cho A13.
