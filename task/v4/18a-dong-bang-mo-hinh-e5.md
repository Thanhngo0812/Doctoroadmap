# 18a — Đóng băng mô hình E5 cho pass phụ không LLM

**Nguồn chân lý:** [spec pass phụ không LLM](../../doc/a8-pass-phu-ml-spec.md), mục 4 và 7.
**Ai:** Claude · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không vé nào · **Trạng thái:** xong 2026-10-16

## Vì sao

Học mô hình cần dữ liệu D-01 nằm ngoài repo, mà nhân viên không được thấy. Vì vậy Claude đóng băng mô hình thành tệp, còn sản phẩm chỉ nạp tệp đó.

## Cần làm

- Script nghiên cứu xuất mô hình cuối của lượt `e5-d01-a` (toàn bộ dòng D-01, nhãn lượt A, seed 20261005) ở định dạng văn bản của LightGBM.
- Xuất bộ hiệu chỉnh isotonic, học trên dự đoán ngoài mẫu chia theo sách, thành hai mảng điểm và xác suất, lưu trong JSON.
- JSON siêu dữ liệu gồm:
  - danh sách 82 đặc trưng theo thứ tự;
  - phiên bản;
  - ngày học;
  - nguồn nhãn;
  - AP ngoài mẫu;
  - giá trị thay cho ô thiếu (−1);
  - băm SHA-256 của tệp mô hình.
- Tệp nằm trong thư mục mô hình đóng gói cùng gói, cạnh mô hình A1 nhẹ. Không chứa văn bản giáo trình.

## Nghiệm thu

- [x] Nạp lại tệp bằng LightGBM thuần, không qua script nghiên cứu, rồi chấm bảng nghiên cứu của bốn tài liệu cũ: điểm trùng lượt `e5-d01-a`, chênh
      tối đa 1e-9.
- [x] Bộ hiệu chỉnh nạp từ JSON cho cùng số dương ước lượng và cùng ngưỡng hiệu chỉnh như `nguong.json` của `e5-d01-a` trên bốn tài liệu.
- [x] Kiểm bằng script rằng tệp không chứa tên khái niệm hay câu giáo trình nào.

## Kết quả (Claude, 2026-10-16)

- Script đóng băng: `scripts/pass-phu-ml/dong_bang_e5.py`. Tệp ra ở `vendor/a8-pass-phu-ml/`:
  - `model.txt`: LightGBM dạng văn bản, `feature_names` là tên thật của 82 đặc trưng;
  - `manifest.json`: thứ tự đặc trưng, giá trị thiếu −1, bộ hiệu chỉnh 136 mốc, luật ngưỡng, AP ngoài mẫu trung vị 0,681, SHA-256 của `model.txt`.
- `.gitattributes` ghim LF cho thư mục này, vì băm tính trên byte.
- Tự kiểm:
  - nạp lại bằng `lightgbm.Booster` thuần, điểm trên bốn tài liệu cũ lệch tối đa 1,1e-16 so với `e5-d01-a`;
  - số dương ước lượng và ngưỡng hiệu chỉnh khớp `nguong.json` trên cả bốn tài liệu (doc-1 223, nhap-mon-ml 62, xstk 79, doc-4 956);
  - dò 7.277 tên khái niệm, không tên nào có trong tệp.
- **Cho vé 18c:**
  - bộ hiệu chỉnh là nội suy tuyến tính, kẹp hai đầu (`numpy.interp` trên hai mảng `diem`, `xac_suat`);
  - thư mục mô hình phải được đóng gói vào wheel, giống `vendor/a1-nhe`.
