# 13 — Lệnh chấm `a4-evaluate`

**What to build:** `a4-evaluate --doc-id … --gold …` chấm một phiên bản `canonical` trên bộ vàng A4 và in:
P/R/F1 theo cặp, tỉ lệ cặp trùng mà đồ thị đề cử bắt được, độ chính xác của cạnh `subtype_of`, số nhóm đồng âm bị để
chung, và độ đồng thuận giữa hai người gán.

## Vì sao cần trước lần chạy thật

Mọi tham số trong spec — k = 3, ngưỡng n-gram 0,5, độ phân giải 2, trần 9, chọn model, giữ hay bỏ kênh mô tả — là
điểm khởi đầu đã đo, chưa phải điểm chốt. Lệnh chấm là thứ biến bộ vàng thành số để chốt chúng. Nó dựng và test được
bằng một bộ vàng tay nhỏ, không cần chờ người dùng gán xong.

**Blocked by:** 05 — Bảng gán bộ vàng `a4-gold-sheet`

**Status:** done

**Cập nhật triển khai 2026-09-11:** Đã triển khai và đối chiếu bộ 8 cặp tính tay: P=.5, R=1/3, F1=.4, kappa=41/49; chưa có gold thật người dùng.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] Từ chối bộ vàng không mang `blind_before_first_a4_run: true`, cùng khuôn `a3-evaluate`.
- [x] **P/R/F1 theo cặp**: dương = nhãn *cùng*; dự đoán dương = hai đầu chung một node. Mục *không chắc* loại khỏi mẫu
      số và đếm riêng. Nhóm `deferred` tính là không gộp.
- [x] **Recall của đồ thị đề cử**: trong mọi cặp *cùng* của bộ vàng — kể cả cặp ngẫu nhiên ngoài đồ thị — tỉ lệ nằm trên
      một cạnh đề cử. Đây là trần cứng của A4: cặp không vào đồ thị thì không bao giờ được gộp.
- [x] **Cạnh `subtype_of`**: tỉ lệ cặp *cha–con* của bộ vàng có cạnh `subtype_of` đúng chiều; số cạnh `subtype_of` nối
      cặp mà bộ vàng không gán *cha–con*.
- [x] **Đồng âm**: số nhóm tên bộ vàng đánh *có đồng âm* mà A4 vẫn để chung một node.
- [x] **Đồng thuận**: Cohen's kappa và tỉ lệ trùng nhãn giữa hai file người gán trên phần giao, in kèm cỡ phần giao.
- [x] In rõ phiên bản `canonical` được chấm; mặc định là phiên bản mới nhất.
- [x] Test với bộ vàng tay 8–10 cặp có P/R/F1, recall đồ thị và kappa tính sẵn bằng tay; test từ chối bộ vàng thiếu cờ
      mù.
- [x] Toàn bộ test hiện có vẫn xanh.
