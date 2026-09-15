# 04 — Nghiệm thu: không hash nào đổi

**What to build:** Chứng minh việc dời file không làm đổi hành vi. Mọi thứ đã có vẫn dùng lại được y nguyên, và bản cài
đặt vẫn đủ file prompt.

**Blocked by:** 02 — Test chốt; 03 — README, tài liệu và script

**Status:** done — 2026-09-15

- [x] Test hash vàng (ticket 02) xanh mà không sửa số nào.
- [x] Toàn bộ test xanh, chặn mạng. Test hợp đồng A3 và A4 phát lại fixture **cũ**, không ghi lại fixture nào.
- [x] `doc2roadmap a4 --doc-id <doc> --gold tests/fixtures/a4/gold-blind.json`, chặn mạng, cho cả bốn tài liệu: phải ra
      `reused=true`, và phiên bản vẫn là phiên bản mới nhất hiện có. Dán kết quả vào ticket.
- [x] A3: với từng tài liệu, `prompt_hash` ghi trong manifest ứng viên mới nhất (`config.prompt_hash`, cùng
      `model_id` và `generation` trong manifest đó) phải tính lại được từ file mới, với đúng few-shot đã dùng lúc trích.
      Dán bảng tài liệu → few-shot → hash vào ticket. Kỳ vọng, đo trên file cũ ngày 2026-09-14:

      | Tài liệu | Bản ứng viên | Few-shot |
      |---|---|---|
      | baocao-canhan | v7 | `technical-report` |
      | naive-bayes | v5 | `default` |
      | nhap-mon-ml | v7 | `default` |
      | xstk-ch3-1 | v5 | `statistics` |
- [x] Đóng gói: build wheel rồi liệt kê file. Mọi file dưới `prompts/a3/` và `prompts/a4/` phải có trong gói, và không
      còn file tên cũ.
- [x] `git status` sạch ngoài phạm vi đợt này. Các file được dời (không phải xoá rồi tạo mới) để `git log --follow` còn
      theo được lịch sử.

## Kết quả nghiệm thu

### A4 — phát lại kho chính khi chặn mạng

| Tài liệu | Bản canonical mới nhất | Kết quả |
|---|---:|---|
| `baocao-canhan` | v8 | `reused=true`, `stage=complete` |
| `naive-bayes` | v7 | `reused=true`, `stage=complete` |
| `nhap-mon-ml` | v7 | `reused=true`, `stage=complete` |
| `xstk-ch3-1` | v7 | `reused=true`, `stage=complete` |

Cả bốn lệnh dùng `tests/fixtures/a4/gold-blind.json`; không có phiên bản mới và không có lời gọi mô hình.

### A3 — tính lại hash từ đường dẫn mới

| Tài liệu | Bản ứng viên | Few-shot | Hash manifest và hash tính lại |
|---|---:|---|---|
| `baocao-canhan` | v7 | `technical-report` | `96b3124853dfc13efec646b3e3aca8a721d7fafbff0fd808a01c26743b500479` |
| `naive-bayes` | v5 | `default` | `8e7c14c360ce13e2a51b5ccb636a247ecfc7f637d73265d1feca7860dc244f71` |
| `nhap-mon-ml` | v7 | `default` | `8e7c14c360ce13e2a51b5ccb636a247ecfc7f637d73265d1feca7860dc244f71` |
| `xstk-ch3-1` | v5 | `statistics` | `1418ee7c073a2e9da6688b12cdd79c12a61587d2962673851fa645c2135b8c62` |

Cả `config.prompt_hash` lẫn `manifest.prompt_hash` đều khớp giá trị tính lại cho cả bốn tài liệu.

### Gói và test

- Wheel offline: `dist/doc2roadmap-0.1.0-py3-none-any.whl`. Gói chứa README prompt, đủ **7 file A3 + 3 file A4**
  theo bố cục mới; không chứa tên file sản phẩm cũ.
- Toàn suite: **299/299 pass**, gồm test unit và integration; không ghi lại fixture, không gọi mạng hay mô hình.
- `git diff --cached --name-status` nhận 10 đích là `R100`; `a4-repair.txt` là bản sao duy nhất bị xoá. Ngoài phạm vi
  đợt này chỉ có `.obsidian/` không được theo dõi, đã tồn tại trước khi bắt đầu và không bị đụng tới.
