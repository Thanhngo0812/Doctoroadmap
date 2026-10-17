# 19i — Pass phụ ML chậm trên tài liệu lớn

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 2 mục 5.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** đã cài và kiểm chứng 2026-10-17; 18d giữ ngoại lệ xstk đã chốt

## Vì sao

Pass phụ ML (`a8-secondary-ml-v1`) mất **592 giây** trên doc-4 ở chuỗi gộp. Trên d01-02 nó chỉ mất 18 giây, và 18d đo 3,8 phút trên doc-4 của chuỗi v3.
Chưa rõ nguyên nhân. Đồ thị nằm ở kho `tmp/v4-17i/artifacts`, `graph/doc-4/v4`, upstream v3.

## Cần làm

- Profile stage trên artifact pass chính có sẵn đó, 0 USD, ở kho thử. Tìm nút cổ chai: dựng đặc trưng, cửa sổ định nghĩa, bộ tách từ, khớp tên…
- Sửa nút cổ chai. **Đặc trưng, điểm, ngưỡng và cạnh phải giống hệt trước.**
- Không đổi khoá cache.

## Nghiệm thu

- [x] Ghi số giây trước và sau trên doc-4 kho thử, kèm nút cổ chai đã tìm.
- [x] Đặc trưng và điểm từng chiều trước và sau cùng băm; cạnh pass phụ y hệt.
- [x] Toàn bộ test qua.
- [x] Phát lại 18d giữ kết quả chất lượng đã chấp nhận ở lượt 2 (ngoại lệ xstk theo số cạnh chung); script vẫn trả 1 như ghi chú bên dưới.

**Kiểm chứng 2026-10-17:** 374,653 → 197,569 giây (1,90 lần). Cache chuẩn hoá/tách từ/cửa sổ theo tài liệu loại tính lặp. 4.650 chiều × 82 đặc trưng, điểm, xác suất, ba ngưỡng, 877 cạnh và toàn payload cùng băm; source/config hash không đổi. `upstream v3` trong kho này là phiên bản graph 3 của chuỗi `gop`. Chi tiết ở [báo cáo 19g–19i](../../report/v4-19gi-tang-toc-mentions-va-pass-phu-ml-2026-10-17.md).

Phát lại 18d: 4.905 chiều lệch điểm 0; cạnh và E4 của cả ba tài liệu trùng kết quả lượt 2 đã chốt. Script vẫn trả 1 do xstk ngoài ±0,03; vé 18d đã chấp nhận tài liệu này theo đủ 59/59 cạnh chuẩn, thừa 1. Không phát sinh lệch mới và không sửa script để đổi phán xét.

Toàn kho: **1.617 test qua**, xem [báo cáo tích hợp](../../report/v4-19-phan-tich-va-kiem-chung-2026-10-17.md).
