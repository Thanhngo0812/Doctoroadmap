# 04 — Nghiệm thu: không hash nào đổi

**What to build:** Chứng minh việc dời file không làm đổi hành vi. Mọi thứ đã có vẫn dùng lại được y nguyên, và bản cài
đặt vẫn đủ file prompt.

**Blocked by:** 02 — Test chốt; 03 — README, tài liệu và script

**Status:** todo

- [ ] Test hash vàng (ticket 02) xanh mà không sửa số nào.
- [ ] Toàn bộ test xanh, chặn mạng. Test hợp đồng A3 và A4 phát lại fixture **cũ**, không ghi lại fixture nào.
- [ ] `doc2roadmap a4 --doc-id <doc> --gold tests/fixtures/a4/gold-blind.json`, chặn mạng, cho cả bốn tài liệu: phải ra
      `reused=true`, và phiên bản vẫn là phiên bản mới nhất hiện có. Dán kết quả vào ticket.
- [ ] A3: với từng tài liệu, `prompt_hash` ghi trong manifest ứng viên mới nhất (`config.prompt_hash`, cùng
      `model_id` và `generation` trong manifest đó) phải tính lại được từ file mới, với đúng few-shot đã dùng lúc trích.
      Dán bảng tài liệu → few-shot → hash vào ticket. Kỳ vọng, đo trên file cũ ngày 2026-09-14:

      | Tài liệu | Bản ứng viên | Few-shot |
      |---|---|---|
      | baocao-canhan | v7 | `technical-report` |
      | naive-bayes | v5 | `default` |
      | nhap-mon-ml | v7 | `default` |
      | xstk-ch3-1 | v5 | `statistics` |
- [ ] Đóng gói: build wheel rồi liệt kê file. Mọi file dưới `prompts/a3/` và `prompts/a4/` phải có trong gói, và không
      còn file tên cũ.
- [ ] `git status` sạch ngoài phạm vi đợt này. Các file được dời (không phải xoá rồi tạo mới) để `git log --follow` còn
      theo được lịch sử.
