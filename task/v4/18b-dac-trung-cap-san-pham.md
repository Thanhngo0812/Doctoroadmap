# 18b — Đặc trưng cặp của pass phụ trong sản phẩm, kèm lệnh xuất bảng

**Nguồn chân lý:** [spec pass phụ không LLM](../../doc/a8-pass-phu-ml-spec.md), mục 2, 3, 6 và 7.
**Ai:** nhân viên · Claude kiểm khớp · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không vé nào · **Trạng thái:** ready-for-agent

## Vì sao

Mô hình đóng băng chỉ đúng khi nhận đúng đặc trưng nó đã học. Đặc trưng hiện chỉ có trong script nghiên cứu. Vé này đưa chúng vào sản phẩm và cho
Claude một lệnh để so từng giá trị với bảng nghiên cứu.

## Cần làm

- Hàm miền thuần tính đặc trưng cho mọi chiều X → Y của các cặp nghi tiên quyết đã chọn. Hàm nhận artifact pass chính, chunk và **một hàm tách từ
  được truyền vào**. Định nghĩa từng đặc trưng theo bảng nghiên cứu (script `dung_bang_cap.py` chế độ `--tach-tu`); chỉ làm 82 đặc trưng mà E5 dùng,
  không làm nhóm `main_*`.
- Cờ ứng viên: hợp đồng cho phép và tên X có trong cửa sổ định nghĩa Y theo **cả** khớp exact **và** khớp ranh giới từ. Câu tách từ chuẩn hoá từng
  âm tiết.
- Bản cài tách từ bằng underthesea ở tầng hạ tầng, có bộ nhớ đệm theo câu. Thêm underthesea 9.5.0 vào phụ thuộc. Mô hình tách từ đóng gói sẵn, không
  tải gì lúc chạy.
- Lệnh CLI xuất bảng đặc trưng (CSV) của một tài liệu từ artifact pass chính. Gồm cột định danh (cặp, X, Y), cờ ứng viên, và các đặc trưng. Thư mục ra
  do người chạy chọn.

## Nghiệm thu

- [ ] Test miền chạy với bộ tách từ giả:
  - tên một âm tiết không khớp giữa từ ghép;
  - tên có âm tiết "y" giữa từ ghép vẫn khớp;
  - ứng viên đòi hợp đồng cho phép;
  - các đặc trưng thứ tự, cùng mục, cùng chương;
  - ô thiếu được để trống, và bản cài chấm thay bằng −1.
- [ ] Test kiến trúc: miền không import underthesea.
- [ ] **Claude kiểm khớp**: xuất bảng cho doc-1, nhap-mon-ml, xstk-ch3-1 và doc-4, rồi so với bảng nghiên cứu. Yêu cầu:
  - cùng tập ứng viên;
  - mọi đặc trưng chênh tối đa 1e-9.
  - Cột lệch thì trả vé.
