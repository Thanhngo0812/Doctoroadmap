# DG-08 — Điều phối lượt chạy

**Nguồn:** spec mục 13 · **Ai:** agent B; Claude chạy lượt thật · **Chi phí:** 0 khi cài; lượt thật có chi, chủ dự án duyệt · **Chặn bởi:** DG-04, DG-06 ·
**Hạn:** 31/10 · **Trạng thái:** ready-for-agent

## Làm được gì

Một lệnh nhận manifest sách và tên hệ hay biến thể, rồi chạy trọn một lượt trong một **thư mục lượt**. Thư mục lượt chứa:
- kho artifact mới và kho Pha B riêng;
- bản ghi lượt: commit, hash cấu hình, mô hình, transport, seed, ngày;
- **dry-run** và dự toán trước khi chi;
- sổ chi thật;
- hợp đồng đánh giá xuất ra.

Lệnh gọi đúng CLI pipeline sẵn có: `ingest`, `label-roles`, `a3`, `a4`, `roadmap`, với cờ của biến thể (`--a1 docling`, `secondary_mode`, seed xáo, bộ lọc cặp).
Biến thể chỉ đổi khâu sau thì dùng lại thượng nguồn của lượt chính, bằng cách chép artifact theo danh sách, không junction. Lượt bị ngắt thì chạy tiếp từ điểm
lưu, không đổi cấu hình, không xoá bản đã xong.

## Tiêu chí

- [ ] Dry-run trên một khoảng chương phát triển không tốn tiền và in dự toán.
- [ ] Dùng mô hình giả, chạy trọn từ PDF tới bảng điểm trên fixture nhỏ.
- [ ] Bản ghi lượt đủ trường. Có test: thiếu trường thì lượt không được coi là xong.
- [ ] Chạy tiếp sau ngắt không gọi lại bước đã xong. Test bằng bộ đếm lời gọi của mô hình giả.
- [ ] Không bao giờ ghi vào kho chung. Có test với đường dẫn kho chung bị chặn.
- [ ] Bảng phá, gồm ít nhất: dùng lại cache của lượt khác; quên truyền kho Pha B riêng; biến thể ghi đè thượng nguồn của lượt chính.

**Claude, sau ghép:** chạy hệ chính thật trên một khoảng chương phát triển, đo phút và USD, đối chiếu với lượt cũ.
