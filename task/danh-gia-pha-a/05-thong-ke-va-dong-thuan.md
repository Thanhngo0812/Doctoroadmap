# DG-05 — Thống kê và đồng thuận

**Nguồn:** spec mục 8 (đồng thuận, trần người), 9; VL §8, §9 · **Ai:** Claude cài (Q16), một agent soát độc lập trước khi ghép · **Chi phí:** 0 · **Chặn bởi:**
không. Đầu vào là bảng số đếm theo chương, theo định dạng ở DG-04 · **Hạn:** 31/10 · **Trạng thái:** ready-for-agent

## Làm được gì

Từ bảng số đếm theo chương của nhiều hệ, một lệnh cho ra:
- thước theo cuốn và trung bình macro;
- **CI 95% bootstrap phân cấp**: lấy lại cuốn, rồi chương trong cuốn; 10.000 vòng; LCG tất định;
- **p hoán vị ghép cặp phân tầng** cho từng cặp hệ, kèm **Holm** trên ba phép kiểm định chính;
- **sign test theo cuốn**, nhị thức chính xác;
- **đồng thuận**: PSA (F1 giữa hai người); bản có tín dụng bắc cầu kiểu PREAP lấy số đếm từ DG-03; Cohen κ và % đồng ý; Krippendorff α thứ bậc cho Likert;
- **trần người**: F1 hệ so với từng người, đặt cạnh F1 giữa hai người;
- **mô phỏng công suất**: với phương sai đo trên tập phát triển, cho biết hiệu ứng nhỏ nhất phát hiện được ở 8 cuốn × 3 chương.

## Tiêu chí

- [ ] Tất định: cùng seed thì ra cùng số trên hai lần chạy.
- [ ] Hai hệ giống hệt nhau cho p = 1. Hai hệ khác xa nhau ở mọi chương cho p < 0,001.
- [ ] Holm khớp ví dụ sách giáo khoa. Sign test khớp bảng nhị thức (8/8 → 0,0078; 7/8 → 0,0703).
- [ ] PSA khớp ví dụ trong Hripcsak & Rothschild 2005. κ và α khớp ví dụ tính tay. Mẫu số 0 thì trả `None`.
- [ ] Không nhập `doc2roadmap`.
- [ ] Bảng phá, gồm ít nhất: bootstrap theo cạnh thay vì theo cuốn; hoán vị không phân tầng; Holm bỏ bước dừng; dùng trung bình micro thay macro.
