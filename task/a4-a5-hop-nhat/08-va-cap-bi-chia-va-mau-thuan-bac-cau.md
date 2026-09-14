# 08 — Vá cặp bị chia hai cụm, và mâu thuẫn bắc cầu

**What to build:** Sau lượt phán cụm, những cặp nghi trùng có hai đầu rơi vào **hai cụm khác nhau** được đem phán lại
bằng cụm nhỏ chứa mọi nhóm của hai node. Hai node trùng bị chia như `Kiến trúc Hub - Client` / `Mô hình Hub - Client`
giờ gộp được. Gộp bắc cầu mà
mâu thuẫn với một phán quyết đã có thì thành phần đó **không gộp**, kèm cảnh báo.

## Vì sao cần bước này

Louvain chia đồ thị theo cộng đồng, và thỉnh thoảng cắt đúng qua một cặp trùng thật. Trên bốn tài liệu: **38 cạnh bị
cắt**, và **2/25** cặp trùng của tập bạc nằm trên cạnh bị cắt. Không vá thì hai node trùng đi thẳng xuống 2b; để tầng
3 vớt nghĩa là mang lỗi qua cả 2b rồi mới sửa (Q26).

**Blocked by:** 07 — Phán theo cụm

**Status:** done

**Cập nhật hoàn tất 2026-09-12:** Đã thay lô cặp bằng phán cụm nhỏ, hoãn theo cặp, giữ merge đúng trước đó; chạy thật
flash-lite đạt 31 TP, 0 FP trên bốn tài liệu.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] Lấy mọi cạnh bị cắt mà sau lượt cụm hai đầu vẫn là hai node khác nhau; tạo cụm nhỏ gồm mọi nhóm thành viên của
      hai node và gọi đúng prompt/schema/validator ticket 07. Cạnh nối cùng cặp node chỉ gọi một lần.
- [x] Chỉ gộp khi toàn bộ hai node được đặt chung một node; kết quả tách hoặc hoãn ⇒ giữ nguyên. Hoãn/sai hai lần được
      ghi theo cặp node, không đưa nhóm đầu mút vào `deferred` toàn cục.
- [x] **Gộp bắc cầu có kiểm**: sau khi hợp theo các cặp *cùng*, thành phần nào chứa hai node đã bị một phán quyết trước
      **tách ra** — hai node mô hình đã chia riêng trong cùng một cụm, hoặc một cặp mang nhãn khác *cùng* ở lượt vá —
      thì **không gộp** thành phần đó: đánh `deferred`, phát cảnh báo, đếm.
- [x] Sau khi gộp: tính lại tên chuẩn, alias, ký hiệu, kiểu, id neo bằng luật ticket 02; chạy lại ánh xạ cạnh ticket 03.
- [x] Nhật ký ghi từng cụm vá cùng khuôn ticket 07 và ghi riêng `deferred_pair`.
- [x] Manifest: số cặp vá có quyết định hợp lệ, số cặp đã gộp, số cặp hoãn, số mâu thuẫn bắc cầu.
- [x] **Seam ②**: phát hiện mâu thuẫn bắc cầu — A *cùng* B, B *cùng* C, nhưng A và C đã bị tách trong một cụm ⇒ không
      gộp thành phần đó. Test phải thấy hỏng khi bỏ guard.
- [x] **Seam ①**, trọng tài giả: cặp bị cắt được phán *cùng* ⇒ lời gọi chứa đủ nhóm của hai node và hai node thành
      một; hoãn/sai không tháo merge đúng của lượt cụm; không chạm mạng.
- [x] Toàn bộ test hiện có vẫn xanh.
