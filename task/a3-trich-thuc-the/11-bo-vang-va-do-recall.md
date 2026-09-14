# 11 — Bộ vàng gán mù và đo recall

**What to build:** Trả lời được câu **"A3 bỏ sót bao nhiêu?"** bằng số, thay vì bằng cảm giác. Đây là
khoảng trống mà cả hai báo cáo rà soát đều chỉ ra: dự án có 25 bất biến ở B0 nhưng chưa có một con số
nào nói chất lượng trích xuất ra sao.

## Phạm vi và cách gán

- **1 chương `nhap-mon-ml`** (văn xuôi) + **1 chương `xstk-ch3-1`** (đặc công thức). Hai giáo trình là
  thể loại đích; DOCX và slide là ca biên. Trục **văn xuôi vs công thức** là trục quyết định độ hạt có
  chuyển giao được hay không.
- **Gán 1 section trước để hiệu chỉnh độ hạt** → section đó **bị loại khỏi bộ chấm** → phần còn lại gán
  **mù**, trước khi chạy A3.

**Gán mù là bắt buộc.** Sửa output thành bộ vàng nghĩa là đo recall trên thứ dẫn xuất từ chính output —
vòng luẩn quẩn, con số đẹp một cách vô nghĩa. Và một section không được đóng hai vai vừa hiệu chỉnh vừa
chấm điểm.

## Điều bộ vàng này trả lời được, mà không gì khác trả lời được

Ngoài recall, nó là **phép đo quyết định đường leo công thức** (ticket 06): nếu khái niệm sót **tập
trung ở chương `xstk`** thì phải leo lên phương án cắt ảnh vùng công thức — một ticket B0 mới. Nếu sót
đều hai chương thì vấn đề ở prompt, không ở công thức.

Văn liệu giáo dục cảnh báo trước: người gán nhãn **bất đồng có hệ thống** về bề rộng vs chiều sâu. Nên
đọc kết quả theo cặp — **sót** và **thừa** — chứ không quy về một con số đúng/sai.

**Blocked by:** 10 — cần bộ chỉ số và độ hạt đã hiệu chỉnh trước khi gán, nếu không gán nhầm tầng.

**Status:** done

- [x] Bộ vàng lưu trong repo dạng đọc được, diff sạch, ghi rõ section nào dùng hiệu chỉnh (bị loại)
- [x] Gán **mù** — hoàn tất trước khi chạy A3 trên hai chương đó
- [x] Đo và ghi: **recall thực thể** trên mỗi chương riêng
- [x] Đo và ghi: **tỉ lệ thực thể thừa** (A3 có, bộ vàng không) — thừa không đồng nghĩa sai
- [x] Đo và ghi: **tỉ lệ có bằng chứng** hợp lệ
- [x] Không báo `single_chunk_ratio` trước merge vì cấu trúc A3 ép nó luôn bằng 1; chuyển phép đo sang
      đợt 2a
- [x] **Kết luận đường leo công thức**: sót có tập trung ở `xstk` không? Ghi rõ có/không kèm số
- [x] Bộ đo chạy được lặp lại bằng một lệnh, không phải thao tác tay
