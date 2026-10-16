# 17h — Chuyển vàng cũ sang id node mới

**Nguồn chân lý:** [spec gộp khâu trước A8](../../doc/gop-khau-truoc-a8-spec.md), mục 6.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** sẵn sàng giao

## Vì sao

Ở chuỗi gộp, id của khái niệm bị gộp thêm sẽ đổi theo ADR 0005. Vàng A8 cũ gắn với id cũ. Hiện bộ chấm từ chối mọi id vàng không có trong đồ thị,
và làm việc đó **trước** khi áp bản đồ danh tính. Vì vậy vàng cũ không chấm được chuỗi gộp. Chủ dự án đã chốt: bộ nào không chuyển trọn được thì để
riêng và dựng lại chỉ số sau.

## Cần làm

- Thêm một hàm miền thuần, không I/O, không gọi mô hình. Hàm quy id của bộ vàng (cạnh và đích) về id hiện hành, qua bảng chuyển hướng của canonical
  mà đồ thị đang dùng.
  - Chuỗi chuyển hướng được quy bắc cầu.
  - Gặp vòng lặp thì báo lỗi.
- Bộ chấm A8 có tuỳ chọn áp phép quy này **trước** bước từ chối id lạ. Với artifact v3, sau phép quy thì áp tiếp bản đồ danh tính như hiện nay.
- Báo cáo của bộ chấm ghi:
  - số cạnh vàng có hai đầu bị gộp làm một; các cạnh này rời phép chấm, giống `identity_dropped_gold_edges`;
  - danh sách khái niệm của vàng không quy được về id nào trong đồ thị. Có khái niệm như vậy thì bộ chấm **từ chối chấm** bộ đó và liệt kê
    chúng.
- Tệp vàng gốc không bị sửa.

## Nghiệm thu

- [ ] Test trên vàng và bảng chuyển hướng dựng tay:
  - id được quy qua bảng chuyển hướng, kể cả chuỗi hai bước;
  - cạnh có hai đầu bị gộp được đếm và rời phép chấm;
  - đích vàng cũng được quy;
  - khái niệm không quy được làm bộ chấm từ chối và liệt kê;
  - vòng chuyển hướng báo lỗi;
  - tệp vàng gốc không bị sửa (so băm trước và sau).
- [ ] Không bật tuỳ chọn thì bộ chấm giữ hành vi cũ, kể cả thông báo từ chối id lạ.
- [ ] Mỗi luật chặn có ít nhất một test thấy nó trượt khi luật bị bỏ. Toàn bộ test qua.
