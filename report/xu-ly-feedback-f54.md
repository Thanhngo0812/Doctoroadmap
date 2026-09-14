# F54 — Danh sách kiểu cần người duyệt

Chạy trực tiếp trên artifact đã lưu, không cần gọi mô hình, embedding hoặc ingest lại:

```powershell
.venv/Scripts/doc2roadmap.exe a3-review-types --doc-id nhap-mon-ml --doc-id xstk-ch3-1 --doc-id baocao-canhan --doc-id naive-bayes
```

Lệnh dùng candidate version mới nhất của từng tài liệu, loại doc-id trùng, bỏ figure/table,
và chọn các kiểu có 1–2 ứng viên trong ít nhất một tài liệu. Kiểu chưa duyệt đứng trước;
trong mỗi nhóm sắp theo tên. Không suy ra rằng kiểu hiếm là không học được.

## Kết quả thật ngày 2026-09-08

Đọc ML v7, XSTK v4, báo cáo v6, Naive Bayes v5:

| Kiểu | Ứng viên ở tài liệu có kiểu hiếm | Tổng corpus | learnable trong các tài liệu đó | reviewed | Ví dụ |
|---|---:|---:|---|---|---|
| architecture | 1 | 1 | true | false | Mô hình Hub - Client |
| component | 2 | 2 | true | false | ReadPump, WritePump |
| metric | 3 | 72 | true | false | Test error, standard deviation |
| theorem | 3 | 3 | true | false | Công thức Bayes, Định lý No Free Lunch |
| tool | 1 | 1 | true | false | Makefile |

Phân biệt hai cột số lượng là cần thiết: bảng feedback đếm 3 metric ở các tài liệu có kiểu
hiếm, không bao gồm 69 metric trong XSTK. Lệnh hiển thị cả hai, không thay đổi ngưỡng F53.

`artifact_learnable` là giá trị lưu ở các tài liệu có kiểu hiếm (`mixed` nếu bất đồng).
`reviewed` và `reviewed_learnable` đọc từ registry hiện tại, độc lập với artifact lịch sử.
Giá trị `-` nghĩa là chưa có quyết định được duyệt. Sau khi sửa registry, bảng phản ánh
quyết định mới ngay; artifact cũ không tự đổi. Muốn áp dụng vào kết quả trích, chạy lại
`extract` hoặc `a3` theo cơ chế vô hiệu hóa cache F53.

Người dùng lấy tên kiểu từ bảng rồi tạo/sửa `type_registry.json` theo
[hướng dẫn F53](xu-ly-feedback-f53.md). Lệnh không ghi tệp, không tự duyệt, không ghi đè
quyết định. Chưa có UI A13; đây là đường xem danh sách công việc bằng CLI.

## Kiểm chứng

Toàn bộ test: **204 passed**, gồm 5 integration test, 41,65 giây.
Lệnh: `.venv/Scripts/python.exe -m pytest --basetemp tmp/pytest-f54-full -p no:cacheprovider`.

- `test_review_types_cli_reads_latest_without_mutation`: đã thấy thất bại trên code cũ
  vì chưa có lệnh. Sau sửa kiểm tra chọn version mới nhất, gộp tài liệu không đếm trùng,
  hiển thị bất đồng, đọc quyết định mới và so toàn bộ byte tệp trước/sau để bảo vệ tính chỉ đọc.
- `test_review_types_excludes_common_and_media_but_counts_corpus`: ngưỡng 2/3, bỏ media,
  phân biệt số ứng viên hiếm/tổng, ví dụ đúng phạm vi, đầu vào rỗng và thiếu artifact.
- Đã chạy lệnh thật trên bốn tài liệu: đúng năm kiểu nêu trên, không gọi API.

F47 vẫn mở: thử nghiệm few-shot theo thể loại là việc riêng, không được thay bằng kết quả F54.
