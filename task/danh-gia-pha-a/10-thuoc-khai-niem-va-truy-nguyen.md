# DG-10 — Thước khâu khái niệm (A3, A4, A5) và truy nguyên

**Nguồn:** spec mục 8, các dòng A3, A4, A5, Đầu-cuối, Truy nguyên, So với B5 · **Ai:** agent A · **Chi phí:** 0 · **Chặn bởi:** DG-09 · **Hạn:** 01/11 ·
**Trạng thái:** ready-for-agent

## Làm được gì

Lõi chấm (thuần) có thêm các thước sau, mỗi thước có mức nghiêm và mức nới. Đầu ra theo định dạng bảng số đếm theo chương.
- **A3:** độ phủ khái niệm G3 (trạng thái dạy ở đây hay qua ví dụ); độ phủ trong dãy học.
- **A4:**
  - tỉ lệ tách: một khái niệm vàng căn `khop` với từ 2 node trong dãy học trở lên;
  - tỉ lệ gộp nhầm: một node căn `khop` với từ 2 khái niệm vàng trở lên;
  - P/R kiểu B-cubed.
- **A5:**
  - câu neo đúng (cùng câu; cùng chunk ở mức nới);
  - trạng thái dạy: độ chính xác trên phần không `uncertain`, độ phủ, ma trận nhầm lẫn theo ánh xạ sáu giá trị sang bốn, đọc từ tệp giao thức.
- **Truy nguyên:**
  - tỉ lệ bằng chứng có thật: câu neo và câu bằng chứng khớp mờ trong văn bản trang;
  - tỉ lệ khái niệm bịa: tên và mọi tên khác đều không có trong văn bản sách;
  - tỉ lệ khái niệm và cạnh có bằng chứng.
- **Thước phụ so với B5** (Q38): độ phủ theo vị trí chương; tỉ lệ tách giữa các chương.

Văn bản sách được truyền vào lõi chấm dưới dạng dữ liệu (trang → chữ), để lõi vẫn thuần.

## Tiêu chí

- [ ] Mỗi thước có một ca dựng tay với số tính tay. Có các ca: mẫu số 0; `uncertain`; khái niệm vàng không căn được; node gộp hai vàng.
- [ ] Bằng chứng có thật trên hợp đồng hệ chính phát triển gần 1: câu neo lấy từ chunk nên phải khớp; ca nào không khớp thì in ra để Claude đọc.
- [ ] Bảng phá, gồm ít nhất: tính tách trên mọi node thay vì node trong dãy học; khớp câu không chuẩn hoá khoảng trắng; coi `uncertain` là sai.
- [ ] **Trần người** (từ soát DG-05, mục S-02): F1 của hệ so với từng người là một lần chấm với vàng thô của người đó (G3/G4 bản một người, chưa hội ý), do lõi chấm làm; gói thống kê chỉ gộp số đếm. Có test trên ca dựng tay hai người.
