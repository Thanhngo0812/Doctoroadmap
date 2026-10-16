# 17e — A4 đề cử thêm nguồn của danh tính, phán theo tiêu chí cùng ngoại diên

**Nguồn chân lý:** [spec gộp khâu trước A8](../../doc/gop-khau-truoc-a8-spec.md), mục 3.1, 3.3 và 3.7.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (test bằng mô hình giả) · **Chặn bởi:** 17b · **Trạng thái:** đã cài và kiểm chứng (2026-10-16); xem [báo cáo cài đặt và kiểm chứng](../../report/v4-17-phan-tich-va-kiem-chung-2026-10-16.md)

## Vì sao

Danh tính gộp hẳn vào A4. A4 phải tự bắt được các cặp mà danh tính đang bắt. Trên ba tài liệu phát triển, 13/20 lần gộp của danh tính chỉ được đề
cử nhờ độ gần mô tả. Tiêu chí phán cũng phải thống nhất: cùng ngoại diên (R8b).

## Cần làm

Mọi thay đổi chỉ áp ở chuỗi `gop`. A4 của chuỗi v3 giữ nguyên prompt, config và cache.

**Đề cử.** Giữ các nguồn hiện có: alias, độ giống chuỗi của tên, láng giềng gần nhất theo vector tên. Thêm năm nguồn, tính trên nhóm ứng viên, và
dùng lại hàm sinh cặp của danh tính khi được:
1. tên hoặc alias trùng nhau sau chuẩn hoá: NFKC, bỏ dấu LaTeX, gộp gạch nối;
2. viết tắt theo chữ đầu, với tên ít nhất hai từ;
3. hai tên khác nhau đúng một tiền tố chung chung lặp lại trong chính tài liệu, theo luật hiện có của danh tính;
4. câu bằng chứng A3 trùng nhau;
5. độ gần mô tả nháp: top-3 mỗi phía, cosine từ ngưỡng trở lên (khởi điểm 0,85).
   - Vector lấy từ vector mô tả nháp A3 **đã lưu** của từng ứng viên, gộp theo nhóm giống cách A4 gộp vector tên. Không embed thêm.
   - Nhóm thiếu vector thì không được đề cử theo nguồn này.

Cặp mới vào đồ thị đề cử cùng các cạnh cũ. Chia cụm giữ cách hiện có: Leiden, có trần cỡ cụm. Không nguồn nào được tự gộp; mọi gộp vẫn qua mô hình
phán (ADR 0006). Tham số của các nguồn nằm trong config.

**Tiêu chí phán (prompt phán cụm và phán sửa của chuỗi `gop`).**
- Hai nhóm là một thực thể khi và chỉ khi cùng định nghĩa, cùng tập đối tượng, chỉ khác cách gọi.
- "Khác cách gọi" gồm: đồng nghĩa, ký hiệu, viết tắt, số ít/số nhiều, cách viết, bản dịch.
- Phán trên câu bằng chứng nguyên văn. Prompt nhắc rằng một câu thường định nghĩa nhiều khái niệm khác nhau.
- Các quan hệ không đồng nhất **giữ tách**: trường hợp riêng, bằng nhau nhờ mệnh đề, mệnh đề khác, đối tượng khác loại.
- Trường hợp riêng đi ra thành quan hệ đề xuất kiểu mở (ví dụ `subtype_of`), qua đường quan hệ đề xuất 2a hiện có.
- Đầu ra tự mâu thuẫn bị bắt phán lại như hiện nay.

**Nhật ký và số liệu**
- Nhật ký quyết định ghi, cho từng cặp nghi trùng: nguồn đề cử, lời phán, quan hệ.
- Số liệu thêm:
  - số cặp đề cử theo từng nguồn; một cặp có nhiều nguồn thì đếm ở mỗi nguồn và đếm trong tổng hợp;
  - số cặp bị cắt ngang cụm.

## Nghiệm thu

- [x] Test trên fixture tài liệu thật, với mô hình giả:
  - mỗi nguồn mới sinh cặp nghi trùng đúng loại;
  - không nguồn nào tự gộp khi mô hình không phán gộp, kể cả cặp có cosine mô tả 0,99;
  - cặp được phán "trường hợp riêng" giữ tách và ra một quan hệ đề xuất;
  - nhóm thiếu vector mô tả không gây lỗi và không được đề cử theo nguồn mô tả.
- [x] Không có lời gọi embedding nào ngoài embedding tên đã có.
- [x] Số cặp theo nguồn có trong `stats` và khớp số cặp trong nhật ký.
- [x] Đổi tham số nguồn đề cử thì khoá cache đổi. Canonical v3 giữ nguyên băm config.
- [x] Mỗi luật chặn có ít nhất một test thấy nó trượt khi luật bị bỏ. Toàn bộ test qua.
