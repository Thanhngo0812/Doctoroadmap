# 17k — Chuỗi gộp tắt đề cử theo mô tả nháp làm mặc định

**Nguồn chân lý:** [spec gộp khâu trước A8](../../doc/gop-khau-truoc-a8-spec.md), mục 3.1 (đính chính 2026-10-16);
[nghiệm thu 17i lượt 1](../../report/v4-17i-nghiem-thu-chuoi-gop-luot-1-2026-10-16.md), mục 2. Chủ dự án duyệt 2026-10-16.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (test bằng mô hình giả) · **Chặn bởi:** 17j · **Trạng thái:** hoàn tất 2026-10-16

## Vì sao

Ở chuỗi gộp, nguồn đề cử theo độ gần mô tả nháp (vé 17e) tốn nhiều mà gần như không có ích.

**Tốn nhiều:**
- doc-4: 1.570/2.129 cạnh đề cử đến từ nguồn này;
- các cạnh đó biến thành cặp bị cắt ngang cụm, nên số lời phán sửa tăng vọt: doc-4 1.545 lời, 1,275 USD;
- vì vậy chuỗi gộp đắt hơn v3: doc-1 +28%, doc-4 +60%.

**Gần như không có ích:**
- trên 4 tài liệu, khoảng 720 cặp chỉ có nguồn này;
- chúng chỉ ra 4 lần gộp: 1 đúng, 2 sai, 1 chưa rõ.

Tắt nguồn này trên doc-1 (thử bằng ngưỡng cosine 1,0):
- chi phí: −44% lời gọi, −24% USD so với v3;
- gộp: không kém;
- neo của đích vàng: không đổi.

## Cần làm

- Thêm một tuỳ chọn bật/tắt rõ ràng cho nguồn đề cử theo mô tả nháp của chuỗi `gop`. **Mặc định là tắt.** Không dùng mẹo đặt ngưỡng bằng 1,0.
- Khi tắt:
  - không đọc vector mô tả;
  - không sinh cạnh đề cử từ nguồn này;
  - số đếm của nguồn trong `stats` là 0, hoặc không có mục;
  - config ghi rõ là tắt.
- Khi bật: hành vi y như vé 17e, cùng tham số top-k và ngưỡng.
- Cập nhật `.env.example`. Chuỗi v3 không đổi.

## Nghiệm thu

- [x] Test trên fixture thật, với mô hình giả: mặc định không có cặp nào mang nguồn mô tả. Bật tuỳ chọn thì có lại, đúng như vé 17e.
- [x] Bật hay tắt thì khoá cache đổi. Băm config của chuỗi v3 giữ nguyên.
- [x] Mỗi luật chặn có ít nhất một test thấy nó trượt khi luật bị bỏ. Toàn bộ test qua.

Cấu hình: `DOC2ROADMAP_MERGE_DESCRIPTION_ENABLED=false`; đặt `true` để bật lại khi đo.
[Bằng chứng hồi quy và nghiệm thu](../../report/v4-17k-tat-de-cu-mo-ta-2026-10-16.md).
