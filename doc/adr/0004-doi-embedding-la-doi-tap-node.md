# ADR 0004: Đổi mô hình embedding là đổi tập node

**Trạng thái:** accepted  
**Ngày:** 2026-09-03

## Bối cảnh

A3 dùng cùng một cổng embedding cho chunk, `description_draft` và mô tả media. Ở đợt merge 2a,
vector của `description_draft` quyết định cặp ứng viên nào lọt qua blocking. Vì vậy embedding không chỉ
ảnh hưởng thứ hạng tìm kiếm.

## Quyết định

`embedding_model_id` (gồm cả số chiều) là đầu vào của hash artifact và được ghi trong manifest. Khi
đổi mô hình hoặc số chiều, phải dựng lại vector ứng viên và chạy lại blocking/merge; không được dùng
chung node canonical, cluster hay mention map tạo từ vector cũ.

## Hệ quả

Đổi embedding có thể đổi cặp được so, cụm merge và do đó đổi tập node. Các tầng phụ thuộc phía sau gồm
canonical, graph, cluster và mention map phải bị vô hiệu hóa. `text` và `chunk_id` B0 không đổi vì tiền
tố `section_path` chỉ được ghép lúc embed.

## Cập nhật 2026-09-11

Quyết định trên giữ nguyên; phần bối cảnh đổi. Theo ADR 0006, thứ đề cử cặp nghi trùng giờ là **vector tên**
do A4 tự embed, cùng alias và độ giống chuỗi của tên — không còn là vector `description_draft`. Vector
`description_draft` mà A3 đang lưu hiện chưa có bước nào dùng. Đổi mô hình embedding vẫn đổi tập node, nhưng
qua đường hẹp hơn: nó đổi cặp nào được đem cho mô hình phán, không trực tiếp quyết định cặp nào là một.

## Cập nhật 2026-10-17

Quyết định trên giữ nguyên. Từ ADR 0016, chuỗi mặc định là chuỗi gộp, và vector `description_draft` của A3 **không dùng để đề cử ở A4**.
- Chuỗi gộp có cài một nguồn đề cử theo mô tả nháp. Đo thì thấy nguồn này nhiều nhiễu và đắt: trên 4 tài liệu, khoảng 720 cặp chỉ có nguồn này,
  ra 4 lần gộp, trong đó 1 lần đúng. Vì vậy nguồn này tắt mặc định (vé 17k), và phần mã gỡ ở vé 19o.
- Embedding vẫn đổi tập node qua đúng đường của bản cập nhật 2026-09-11: vector tên ở A4 chỉ đề cử cặp nghi trùng.
- Lượt đề cử theo mô tả của danh tính v3 (dùng vector A6) chỉ còn ở artifact chuỗi v3.
