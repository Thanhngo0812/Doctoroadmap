# 19c — Phục hồi gộp đúng ở A4

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 1a mục 3, 4, 6.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** đã cài và kiểm chứng 2026-10-17

## Vì sao

Chuỗi gộp sót một số gộp đúng (nghiên cứu mục 3):
- **Một cặp "khác" làm cả thành phần bị tách và hoãn.** Đây là gốc làm mất Gram-Schmidt, Imf = Ảnh, Hoài nghi luận = Thuyết hoài nghi.
- **Cặp chỉ khác cách viết vẫn bị phán tách:** χα 2 với χα^2, Gram - Schmidt với Gram-Schmidt.
- **Bộ phán ghi `coextensive_with` giữa hai node tách rời** mà R2 không bắt.

## Cần làm

Chỉ áp ở chuỗi `gop`. Mỗi luật có mục riêng trong config chuỗi `gop`.
1. **Giải mâu thuẫn bảo thủ.** Trong thành phần mâu thuẫn, giữ gộp cho các cặp chung **tên** sau chuẩn hoá. Các nhóm còn lại tách và hoãn như hiện nay.
   Nhật ký `transitive_conflict` ghi thêm các cặp được giữ.
2. **Buộc gộp khi chung tên sau chuẩn hoá.**
   - Chuẩn hoá: NFKC, bỏ dấu LaTeX, gộp gạch nối và khoảng trắng quanh gạch nối.
   - Áp cho tên, không áp cho alias.
   - Là ràng buộc "cùng" đi qua cơ chế ràng buộc sẵn có. Quyết định người duyệt "khác" vẫn thắng.
3. **R2 của chuỗi gộp nhận thêm `coextensive_with`.** So đúng nhãn như vé 17j, và đổi mã luật kiểm.

## Nghiệm thu

- [x] Test trên fixture thật với mô hình giả:
  - thành phần có một cặp "khác" vẫn giữ gộp cho cặp chung tên; cặp không chung tên bị tách và hoãn;
  - hai nhóm chỉ khác gạch nối hay LaTeX thì gộp, kể cả khi mô hình phán "khác";
  - người duyệt "khác" thắng luật buộc gộp;
  - hai nhóm chỉ chung alias thì không bị buộc gộp;
  - `coextensive_with` nối hai node tách rời thì bị phán lại.
- [x] Đổi luật thì khoá cache đổi. Băm config v3 giữ nguyên.
- [x] Mỗi luật có test thấy nó trượt khi luật bị bỏ. Toàn bộ test qua.

Ba luật mới đã được thấy đỏ trên mã cũ. Hai thử phá luật “không buộc gộp theo alias” và “người duyệt khác thắng” đều trượt assertion về thành viên node cuối. Sáu regression bổ sung giữ đúng nhóm/cặp hoãn sau khi ràng buộc gộp thành công. [Báo cáo 19a–19c](../../report/v4-19abc-sua-a4-2026-10-17.md); toàn kho **1.617 test qua**, xem [báo cáo tích hợp](../../report/v4-19-phan-tich-va-kiem-chung-2026-10-17.md).
