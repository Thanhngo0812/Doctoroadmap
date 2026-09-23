# 00 — Kế hoạch v2: đồ thị và lộ trình neo vào văn bản

**Nguồn chân lý:** [`doc/v2-do-thi-va-lo-trinh-neo-van-ban-spec.md`](../../doc/v2-do-thi-va-lo-trinh-neo-van-ban-spec.md)
· ADR [0010](../../doc/adr/0010-lo-trinh-la-day-hoc-chia-module.md) · phân tích và số liệu ở
[`report/ke-hoach-v2-do-thi-va-lo-trinh-chuan.md`](../../report/ke-hoach-v2-do-thi-va-lo-trinh-chuan.md) · ngôn ngữ chung
ở [`CONTEXT.md`](../../CONTEXT.md)

## Quyết định của chủ dự án, 2026-09-23

1. Đồng ý toàn bộ hướng v2. **Lộ trình đổi đơn vị từ stage song song sang module có thứ tự** (ADR 0010). Quyết định này
   **thay** quyết định (2) ngày 2026-09-22 ("stage vẫn là nhóm học song song được") ở
   [`task/a6-a8-tien-quyet/00-ke-hoach.md`](../a6-a8-tien-quyet/00-ke-hoach.md).
2. Ngưỡng Q1–Q10 theo đề xuất; đã ghi ở spec v2, mục *Tiêu chí nghiệm thu đã chốt*.
3. Bật C8 v2 làm bản tạm (commit `f2bff0c`) cho tới khi gói B thay nó.
4. Chủ dự án lo phần việc người: [vé 10](10-viec-cua-chu-du-an.md).

## Vé

| vé | gói | ai | chi phí | chặn bởi | cổng nhận |
|---|---|---|---|---|---|
| [01](01-chan-chi-tieu.md) | F — chặn chi tiêu ngầm | Claude | 0 | — | test chốt chặn |
| [02](02-a10-day-hoc-va-module.md) | A — dãy học và module | Claude | 0 | — | bất biến trên 7 tài liệu; Q6 không tệ hơn CG |
| [03](03-lo-trinh-toi-muc-tieu.md) | E — lộ trình tới mục tiêu | Claude | 0 | 02 | Q7 được đo và báo |
| [04](04-neo-dinh-nghia.md) | B — neo định nghĩa (C8 v3) | Claude | ~0,3–0,6 USD | 10: N1 + nhãn khái niệm | Q9 ≥ 90%; nhãn N1 |
| [05](05-danh-tinh.md) | C — danh tính | Claude | ~0,1 USD | 04; 10: duyệt gộp | Q2 = 0 |
| [06](06-recall-co-muc-tieu.md) | D — recall có mục tiêu | Claude | ~1–3 USD | 04, 05; 10: chấm mù | Q4, Q5 |
| [07](07-xac-nhan-tap-giu-lai.md) | G — xác nhận trên tập giữ lại | Claude | ~1–2 USD | 02–06; 10: vàng N2 | Q10 |
| [10](10-viec-cua-chu-du-an.md) | việc của người | chủ dự án | — | xem vé | — |

```text
01 ─┐
02 ─┴─→ 03
04 ─→ 05 ─→ 06 ─→ (C1 cho doc-2 nếu 06 chưa đủ Q5 và chấm mù qua luật) ─→ 07
```

## Luật chung của đợt

- **Mỗi vé khoá cổng nhận trước khi chạy mô hình**, ghi vào chính vé; kết quả trượt ghi nguyên, không dời cột gôn.
- **Spec tổng và spec liên quan được sửa cùng commit với phần mã tương ứng** — `spec-addendum.md`, `CONTEXT.md`, spec
  A9–A10, spec A6–A8, spec provenance — không sửa trước.
- **Không chạy `roadmap` trên tài liệu nào ngoài `doc-1` khi chưa có vé 01**: nó sẽ chạy lại pass phụ theo F126 và tốn
  tiền. Sau vé 01, mọi lần chi phải có `--allow-spend`.
- **Không mở tập giữ lại** (`artifacts/a8-gold/xstk-ch3-1-chuong-10-13-*`, và N2 khi có) trước vé 07.
- Ngân sách: đã tiêu ≈ 13,8 / 50 USD. Dự chi cả đợt 4–12 USD.
