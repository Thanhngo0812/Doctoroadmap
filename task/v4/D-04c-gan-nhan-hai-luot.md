# D-04c — Gán nhãn cạnh ngược hai lượt độc lập

**Nguồn chân lý:** [đặc tả D-04](D-04-dac-ta-nhan-canh-nguoc.md), bước 3 và mục "Kiểm chất lượng".
**Ai:** **chủ dự án**, bằng agentic · Claude kiểm định dạng · **Chi phí mô hình:** do chủ dự án chọn dịch vụ agentic · **Chặn bởi:** D-04a, D-04b ·
**Trạng thái:** chờ chủ dự án

## Vì sao

Một lượt agentic là không đủ: ở D-01, cùng mô hình nhưng khác ngữ cảnh chỉ đạt kappa 0,43. Hai lượt độc lập cho biết độ nhiễu, và phần đồng thuận
là nhãn dùng để đo luật.

## Cần làm

- Chủ dự án quyết dịch vụ nào được nhận phiếu, vì phiếu chứa văn bản giáo trình.
- **Lượt A và lượt B:** hai agent hoặc hai mô hình khác nhau, không thấy nhãn của nhau, mỗi lượt gán đủ mọi phiếu đúng một lần.
- Mỗi lượt tự chạy bộ kiểm định dạng trước khi trả. Lỗi thì tự sửa định dạng; không đổi nhãn vì bộ kiểm.
- Claude kiểm hai tệp và báo danh sách cặp lệch A–B. Lượt ba (agent khác) gán riêng các cặp lệch, không thấy nhãn A và B. Cặp vẫn không có đa số
  thì thành `khong_ro`.

## Nghiệm thu

- [ ] Hai tệp nhãn A, B và tệp lượt ba đều qua được bộ kiểm định dạng.
- [ ] Mỗi dòng nhãn ghi `nguoi_gan` (agent, mô hình, phiên bản) và `luot`. A và B khác agent hoặc khác mô hình.
- [ ] Ghi chép của từng lượt (cách chia lô, số subagent, sự cố) được giao kèm.
