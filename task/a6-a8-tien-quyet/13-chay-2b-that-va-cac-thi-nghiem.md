# 13 — Chạy 2b thật, E3, E4 và ablation trích mở đối đầu kiểm cặp

**What to build:** Chạy 2b đầy đủ trên các chương có vàng, đo chất lượng phán quyết, đo mức rò rỉ kiến thức nền,
và đo chính lựa chọn thiết kế của đợt này.

**Blocked by:** 09, 10, 12. (Việc của Claude.)

**Status:** ready-for-agent

- [ ] Prompt, ngưỡng và luật **đóng băng trước khi mở vàng**; bộ vàng chạy **một lần**.
- [ ] E3: P/R/F1 trên cạnh trực tiếp và trên bao đóng; số lời gọi, token, USD; ba lượt chạy để đo Jaccard cạnh.
- [ ] E4: cùng cặp, hỏi **không kèm văn bản**, đếm cạnh mô hình vẫn khẳng định mà vàng không có.
- [ ] E6: chạy lại danh sách khái niệm của các phiên có vàng theo kiểu kiểm cặp; so với trích mở.
- [ ] Áp **luật đổi mặc định** đã viết trước: chỉ chuyển sang kiểm cặp khi hơn ≥ 0,05 F1, khoảng tin cậy của hiệu
      không chứa 0, và recall không thấp hơn.
- [ ] E7 và E8 nếu kịp: cái giá của các bước nhất quán, và hiệu chỉnh mức trừ cho cạnh ngược thứ tự.
- [ ] Chi phí cộng dồn của cả đợt nằm trong trần 50 USD; sắp vượt thì dừng và hỏi chủ dự án.
- [ ] Thay đổi nào **sau khi thấy số** đều ghi rõ là hậu kiểm và tách riêng trong báo cáo.
