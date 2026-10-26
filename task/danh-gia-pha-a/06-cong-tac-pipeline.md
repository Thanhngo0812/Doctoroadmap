# DG-06 — Công tắc trong pipeline, mặc định tắt

**Nguồn:** spec mục 3, 12 · **Ai:** agent B · **Chi phí:** 0 · **Chặn bởi:** DG-04, vì bộ xuất phải đọc được trường mới · **Hạn:** 30/10 · **Trạng thái:**
ready-for-agent

## Làm được gì

Pipeline có ba công tắc mới, đều mặc định tắt. Khi tắt, đầu ra **y hệt** hiện tại.
- **Bộ đếm giây chờ embedding:** bộ đo stage (vé 02) cộng dồn thời gian nằm trong lời gọi embedding. Đây chỉ là telemetry, không vào payload hay khoá cache.
  Bộ xuất DG-04 đưa nó vào khối `chi_phi`.
- **Seed xáo ngữ cảnh pass chính:** xáo thứ tự các khối ngữ cảnh giữ nghĩa trong lời nhắc pass chính, như cờ `--xao` của
  `scripts/gop-khau/thu_pass_chinh.py` (vé 19j). Không có seed thì không xáo.
- **Bộ lọc cặp pass phụ theo đích:** nhận danh sách đích được phép; chỉ cặp có đích trong danh sách mới được chấm. Dùng cho ablation pass phụ LLM trên chương
  bốc.

## Tiêu chí

Mọi test phải đỏ trên mã cũ.

- [ ] Mỗi công tắc khi tắt: artifact và khoá cache trên fixture trước và sau sửa giống hệt.
- [ ] Công tắc xáo: lời nhắc có cùng tập khối nhưng khác thứ tự; seed đổi thì thứ tự đổi; cùng seed thì cùng thứ tự.
- [ ] Bộ đếm embedding có mặt trong snapshot đo stage. Hash cấu hình không đổi khi chỉ telemetry đổi.
- [ ] Bộ lọc cặp: cặp ngoài danh sách không được gửi đi. Chạy với mô hình giả.
- [ ] Cổng toàn repo xanh.
- [ ] Bảng phá, gồm ít nhất: seed xáo lọt vào khoá cache khi tắt; bộ lọc áp cả khi danh sách rỗng; giây embedding cộng hai lần khi có retry.
