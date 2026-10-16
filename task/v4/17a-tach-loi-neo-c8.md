# 17a — Tách lõi neo C8 khỏi stage `teaching`

**Nguồn chân lý:** [spec gộp khâu trước A8](../../doc/gop-khau-truoc-a8-spec.md), mục 4 và Testing Decisions.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** đã cài và kiểm chứng (2026-10-16); xem [báo cáo cài đặt và kiểm chứng](../../report/v4-17-phan-tich-va-kiem-chung-2026-10-16.md)

## Vì sao

A5 mới (vé 17b, 17d) phải dùng đúng luật neo của C8:
- dựng câu ứng viên;
- kiểm phản hồi;
- xác minh kiến thức nền;
- ghi trường lên node.

Hiện các luật này nằm trong stage `teaching` và gắn với artifact đồ thị: mention map, upstream `provenance`, checkpoint. Tách chúng ra trước để
vé sau gọi lại được, không phải chép luật. Đây là vé chuẩn bị, không đổi hành vi.

## Cần làm

- Tách khỏi stage `teaching` một lõi neo không phụ thuộc artifact đồ thị.
  - **Đầu vào:** danh sách node, chunk có nhãn vai trò, và tập chunk nhắc tên cứng của từng node. Bên gọi cấp tập này: stage `teaching` lấy từ
    mention map, còn stage canonical ở vé 17b tự tính.
  - **Đầu ra:** câu ứng viên của từng node, lời phán đã kiểm, kết quả xác minh kiến thức nền, các trường ghi lên node, nhật ký lời phán, số lời gọi
    và token.
- Luật giữ y hệt hiện nay:
  - vùng tìm, hạng và thứ tự câu, tối đa 6 câu;
  - không có ứng viên thì quét tên chính xác thêm một lần;
  - nhánh `mentioned_only` / `unchecked` không gọi mô hình;
  - lời phán hỏng quá lượt sửa thì nhận `uncertain` và được giữ;
  - `prior_knowledge` qua lượt xác minh độc lập, không xác nhận thì hạ xuống `uncertain`.
- Stage `teaching` của chuỗi v3 đi qua lõi này. Không đổi bất cứ thứ gì sau đây: prompt, schema, config, khoá cache, checkpoint, dạng payload.

## Nghiệm thu

- [x] Test hiện có của stage `teaching` và của miền neo vẫn xanh, không sửa kỳ vọng.
- [x] Test mới gọi lõi trực tiếp, với mô hình giả và không có artifact đồ thị. Phủ các nhánh:
  - có ứng viên;
  - không ứng viên nhưng tên chỉ nằm ngoài vùng nội dung;
  - không thấy tên ở đâu;
  - lời phán hỏng;
  - `prior_knowledge` được xác nhận và không được xác nhận.
- [x] Test hồi quy trên fixture tài liệu thật, với mô hình phát lại: payload stage `teaching` trước và sau khi tách có cùng băm.
- [x] Khoá cache của stage `teaching` không đổi: một artifact `teaching` có sẵn được tái dùng, 0 lời gọi.
- [x] Toàn bộ test qua.
