# R14 — bộ dựng cây tiêu đề, tách khỏi nhận tiêu đề

## Nguồn và phạm vi bằng chứng

Ngày 2026-10-07, paper-lookup tra arXiv `id_list=2303.13839,2401.11874,2609.00065`,
`max_results=3`, Atom parser trả đúng 3 record. Sandbox DNS thất bại, gọi lại
với quyền mạng thành công. Không upload sách/không dịch vụ trả phí.

- Ma et al., [HRDoc](https://arxiv.org/abs/2303.13839): metadata/abstract
  v1, 2023; có nhãn dòng và quan hệ, baseline encoder–decoder. Lượt này
  chưa đọc toàn văn HRDoc, không nhận là tái lập DSPS.
- Wang et al., [Detect-Order-Construct](https://arxiv.org/html/2401.11874v2),
  v2, 2024: đọc phần 4.4/Algorithm 1 và phần đánh giá. Bài tách phát hiện,
  thứ tự, dựng cây; dùng quan hệ cha–con/anh–em và chèn trên nhánh phải để
  giữ cây có thứ tự. Đây là gợi ý thiết kế, không bằng chứng GBDT sẽ đạt
  kết quả của Transformer trên sách tiếng Việt. API chưa ghi DOI xuất bản.

Prototype riêng dưới đây không dùng trọng số/mã của hai bài. Giữ classifier
heading LightGBM hiện tại; học thêm bộ chấm cha ứng viên từ bố cục/số mục,
decoder ràng buộc cha ở nhánh đang mở. Không dự đoán level độc lập rồi
chấp nhận cây vô lý. Đối chứng H0 là heading_level hiện hữu + stack.

## Nhãn sẵn có, không tự nhận là vàng

Native outline hiện chỉ d01-08 và doc-4 có số bookmark căn được đáng kể.
Chỉ nhận bookmark khớp token exact, cùng trang, duy nhất một dòng và dòng
không bị bookmark khác chiếm; giữ thứ tự và SHA của R5. Nhãn cây chiếu lên
các heading căn được: nếu cha thiếu, dùng tổ tiên gần nhất còn căn được.
**Đây là cây chiếu, không phải toàn cây tác giả**, outline có thể sai.
Không dùng tên/level bookmark làm features; chỉ typography/text của dòng PDF.

- d01-08: nguồn train duy nhất. Kiểm bỏ từng nhánh gốc, không gọi LOBO hay
  kiểm ngoài nguồn. Fit full nguồn này sau khi có bảng kiểm nhánh.
- doc-4: chỉ kiểm ngoài như cam kết; không train/tune trên nó.
- Không dùng 17 sách không có nhãn cây để tuyên bố accuracy phân tầng.

H2: LightGBM nhị phân chấm ứng viên cha, 100 cây/7 lá/min-child10,
lr0,05/seed42/class-balanced/n_jobs2. Teacher forcing chỉ trên train;
inference tự hồi quy trên nhánh phải đã dự đoán, argmax không tuning ngưỡng.
Không gọi score là xác suất đã hiệu chuẩn. Không quét tham số sau xem kết quả.

## Test và phép đo

- Cha luôn trước con, chỉ nhánh đang mở, một gốc ảo; không chu trình hoặc
  quay lại nhánh đã đóng. Test đối nghịch cho scorer muốn chọn nhánh đóng.
- Căn nhãn không tự biến cha thiếu thành cha trực tiếp, không dùng nhãn làm
  feature; split nhánh không lẫn train/test; đối chiếu ID thực truyền vào fit.
- Báo exact parent accuracy và ancestor precision/recall/F1, coverage căn
  nhãn, H0/H2, toàn từng nhánh và doc-4. Không đánh đồng với A1 đầu-cuối.

Lưu ý hợp đồng: chunker hiện có thể ưu tiên structure_profile/số mục hơn
`DocumentNode.level`. Vì vậy cây prototype đúng chưa chắc được chunker dùng.
Phải kiểm điều này riêng trước tích hợp; không thay chunker mặc định hoặc
cache của production chỉ để làm thí nghiệm thắng. Cả A1 chưa nghiệm thu.

Scientific-critical-thinking giữ giới hạn một nguồn train/nhãn yếu; ponytail
chỉ dùng ở việc tái dùng stack/LightGBM và tránh dependency mới, không giảm
phạm vi nghiên cứu chủ dự án giao. Bộ skill: Kassis, Agarwal, He, Patel &
Brueckner (2026), [Scientific Agent Skills](https://doi.org/10.48550/arXiv.2609.00065),
đã xác minh record v2, chưa có DOI tạp chí trong API.
