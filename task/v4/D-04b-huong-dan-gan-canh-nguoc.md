# D-04b — Hướng dẫn gán nhãn cạnh ngược cho agentic, kèm thử gán

**Nguồn chân lý:** [đặc tả D-04](D-04-dac-ta-nhan-canh-nguoc.md), bước 3; mẫu [hướng dẫn agentic D-01](../../report/huong-dan-agentic-gan-nhan-d01.md).
**Ai:** Claude · **Chi phí mô hình:** 0 USD · **Chặn bởi:** D-04a · **Trạng thái:** ready-for-agent

## Vì sao

Agentic không được đọc đặc tả D-04, vì mục "Cách Claude dùng nhãn" nêu các luật đang được đo. Agentic cần một hướng dẫn riêng, tự đủ. D-01 cho thấy
hướng dẫn chưa thử trước sinh lỗi có hệ thống (căn cứ là câu định nghĩa X), phải gán lại 240 phiếu.

## Cần làm

- Viết hướng dẫn gán cho agentic theo mẫu D-01. Nội dung gồm: câu hỏi, bảy nhãn kèm phép thử, luật chung, định dạng trả về, cách chạy bộ kiểm định
  dạng, cách chia lô cho subagent, và quy ước hai lượt độc lập. Không nêu luật E8, nguồn cặp hay hệ đề xuất.
- Ví dụ trong hướng dẫn lấy từ phiếu **không** nằm trong bộ phiếu giao đi, hoặc viết ví dụ giả.
- Claude tự gán thử 30 phiếu: 10 doc-4, 10 nguồn 2 cùng chương, 10 nguồn 2 khác chương. Ghi chỗ mơ hồ giữa các nhãn (nhất là `can_hoc_truoc`,
  `du_tai_cho`, `kien_thuc_nen`), rồi sửa hướng dẫn. 30 nhãn thử này không dùng để đo.
- Gói giao chủ dự án gồm phiếu, hướng dẫn và bộ kiểm định dạng. Không có khoá.

## Nghiệm thu

- [ ] Hướng dẫn tự đủ: một agent chỉ đọc hướng dẫn và phiếu là gán được, không cần đặc tả.
- [ ] Không ví dụ nào trùng cặp (X, Y) của phiếu giao đi; kiểm bằng script, không bằng mắt.
- [ ] 30 nhãn thử qua được bộ kiểm định dạng. Ghi chép thử gán liệt kê từng chỗ đã sửa trong hướng dẫn.
- [ ] Gói giao không chứa khoá, đặc tả hay báo cáo vòng 2.
