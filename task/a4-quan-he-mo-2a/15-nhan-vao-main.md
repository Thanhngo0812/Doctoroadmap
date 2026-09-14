# 15 — Nhận vào `main`

**What to build:** Chủ dự án đã chấp nhận bản v3 cộng luật kiểm nhất quán (ticket 14, 2026-09-14). Ticket này thử một mẫu
thứ hai trong kho riêng; qua thì mới gộp nhánh vào `main`, chạy kho chính, rồi cập nhật tài liệu vận hành.

## Ngưỡng cho các lượt chạy xác nhận — viết 2026-09-14, trước khi chạy

Chủ dự án chấp nhận precision gộp 0,946, thấp hơn ngưỡng cũ 0,95. Mẫu thứ hai và lượt chạy kho chính phải qua **cả bốn
điều kiện**:

1. Precision gộp ≥ **0,93**. Mức này thấp hơn 0,946 đã chấp nhận khoảng một ca gộp sai; chủ dự án có thể đổi con số
   này trước khi chạy.
2. F1 gộp ≥ 0,775.
3. Precision `subtype_of` ≥ 0,635.
4. Cụm hỏng hẳn ≤ 1 trên bốn tài liệu, tính cả cụm bị hoãn vì vẫn mâu thuẫn sau lần thử lại.

Không đổi các ngưỡng này sau khi thấy số.

## Vì sao chạy mẫu thứ hai ở kho riêng trước

Quyết định chấp nhận dựa trên một lần chạy duy nhất, nên cần một mẫu nữa để chắc lần đó không phải may.

Kho chọn `latest` là thư mục phiên bản có số lớn nhất (`_load_latest_stage`). Nếu chạy thẳng vào kho chính rồi trượt,
thì `revert` code không kéo `latest` về được. Chạy lại bằng code mặc định chỉ tìm thấy v7 trong cache và trả về nó, không
sinh phiên bản nào mới hơn. Muốn sạch thì phải xoá tay phiên bản vừa sinh. Chạy mẫu thứ hai ở kho riêng tránh được việc
đó.

**Blocked by:** 01 — Spec và ADR 0007 (Claude). Ticket 14 đã được chủ dự án chấp nhận.

**Status:** todo — mở theo quyết định của chủ dự án (2026-09-14)

- [ ] Commit phần đợt 2 lên nhánh `a4-quan-he-mo-2a`, gồm code, test, ticket và feedback, trước khi chạy gì.
- [ ] **Mẫu thứ hai**, trên nhánh, chưa gộp: chạy runner vào
      `artifacts/a4-ab/gemini-3.1-flash-lite-relations-v3-consistency-2`. Đây là mẫu mới, gọi flash-lite thật.
- [ ] Chấm mẫu thứ hai bằng `a4-evaluate` theo bốn điều kiện ở trên. Trượt thì dừng, không gộp, và báo reviewer cùng chủ
      dự án.
- [ ] Qua thì gộp nhánh `a4-quan-he-mo-2a` vào `main` bằng một commit gộp riêng (`--no-ff`), để revert được bằng một
      lệnh.
- [ ] Chạy `doc2roadmap a4 --doc-id <doc> --gold tests/fixtures/a4/gold-blind.json` cho bốn tài liệu vào kho chính.
- [ ] Chấm lượt chạy kho chính theo bốn điều kiện. Trượt thì:
  - `git revert -m 1` commit gộp;
  - **hỏi chủ dự án trước** khi xoá các phiên bản canonical vừa sinh, vì `latest` đang trỏ vào chúng;
  - báo reviewer.
- [ ] Chạy lại lần hai: `reused=true`, 0 lời gọi.
- [ ] Cập nhật báo cáo chạy thật (bảng số của bản mặc định mới, tên chỉ số mới), luồng 2a, README nếu có nhắc tên chỉ số,
      và trạng thái các ticket.
- [ ] Toàn bộ test xanh, chặn mạng.

## Kết quả mẫu thứ hai (2026-09-14, Claude làm theo yêu cầu của chủ dự án)

Chạy ở commit `3ab74ab` (đã có sửa F82), vào kho `…-relations-v3-consistency-2`; 138 lời gọi flash-lite.

| Điều kiện | Kết quả | |
|---|---:|---|
| Precision gộp ≥ 0,93 | 0,946 (35/2/12) | ✅ |
| F1 gộp ≥ 0,775 | 0,833 | ✅ |
| Precision `subtype_of` ≥ 0,635 | 0,658 | ✅ |
| Cụm hỏng hẳn ≤ 1 | 0 | ✅ |

**Mẫu này không độc lập.** 217/217 quyết định giống hệt từng byte với lần chạy ở ticket 13: với `temperature` 0,
flash-lite trả cùng một câu trả lời cho cùng đầu vào. Vì vậy lượt này chứng minh kết quả **tái lập được**, chứ không
chứng minh kết quả vững trước biến động ngẫu nhiên. Muốn đo biến động thì phải đổi đầu vào, tức cần tài liệu mới hoặc
nhãn mới, không phải chạy lại.

Không bắt buộc, có thể làm cùng: sửa F82 bằng cách ghi rõ nghĩa "trong lần chạy này" của các chỉ số mâu thuẫn, hoặc đếm
từ `attempts` của mọi dòng. F83 (lượt thử lại tách cả node) **không** sửa ở đây, vì sửa nó là đổi nội dung gửi cho mô
hình.
