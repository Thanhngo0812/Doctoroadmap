# 21 — "Tổng quan môn học" chỉ gồm khái niệm của đề cương/lời nói đầu; nhắc tới trong bài thì gắn vào module

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R5 ("… hoặc ở mục 'Tổng quan' nếu chỉ có trong đề cương") · **Ai:** nhân viên ·
**Phụ thuộc:** — (làm cùng lượt chạy lại A10 của vé 20) · **Chi phí mô hình:** 0

**Trạng thái:** đã triển khai và chạy lại A10 sáu tài liệu (2026-10-03); số đo và giới hạn còn lại ở [báo cáo](../../report/v3-20-21-t10a-2026-10-03.md).

## Vì sao (Claude, 2026-10-02)
"Tổng quan môn học" trong `roadmap.html` không phải bản tóm tắt môn học. Đó chỉ là danh sách tên khái niệm `mentioned_only`/`unchecked` mà
`BuildRoadmap.place` không tìm được chunk nội dung để gắn vào module. Hiện mục này trộn nhiều thứ:

| tài liệu | số mục | theo vùng nhắc tới (`mentioned_in`) |
|---|---|---|
| doc-1 | 9 | mở đầu 5 ("Thang điểm chữ", "Thi viết rọc phách", "Số phức"…), bài tập 4 ("det(Y)"…) |
| doc-2 | 55 | bài tập 25, cuối sách 6, mở đầu 4, **không rõ 20** |
| doc-3 | 13 | hành chính 5 ("Final project", "Python"…), bài tập 1, **không rõ 7** |
| doc-6 | 6 | đề cương 4, không rõ 2 |
| nhap-mon-ml | 12 | mở đầu 12 (lời nói đầu liệt kê chủ đề sẽ học: SVM, K-NN, Ridge…) |

Hai lỗi:
1. **Trái R5:** khái niệm chỉ có trong bài tập, chỉ mục cuối sách hay thông tin hành chính cũng bị gọi là "Tổng quan môn học".
2. **Gắn module trượt.** Nhóm "không rõ" có chunk căn cứ A3 nằm trong vùng `noi_dung`: doc-2 18/20, doc-3 4/7 (ví dụ "Associative property of
   matrix multiplication", căn cứ "Matrix multiplication is distributive and associative…"). `place` chỉ tìm tên **nguyên văn** cho khái niệm
   chỉ-nhắc. Tên do mô hình đặt không có nguyên văn trong sách, nên rơi vào Tổng quan thay vì "Nhắc tới" của module.

## Việc cần làm
- **Gắn module cho khái niệm chỉ-nhắc:** dùng chunk căn cứ A3 / `defining_chunk_ids` thuộc vùng `noi_dung` (sớm nhất theo vị trí) **trước**
  bước tìm tên nguyên văn. Không có thì giữ cách cũ.
- **Chia nhóm theo vùng**, lưu `overview_groups` trong payload:
  - `tong_quan`: chỉ có ở `de_cuong` / `mo_dau`;
  - `chi_trong_bai_tap`: `bai_tap`;
  - `thong_tin_hoc_phan`: `hanh_chinh`;
  - `cuoi_sach`: `cuoi_sach`;
  - `khong_ro`: còn lại.
  Khái niệm thuộc nhiều vùng lấy theo thứ tự ưu tiên trên. `mentioned_in` có thể là chuỗi hoặc danh sách; chuẩn hoá trước khi xét.
- **HTML:** "Tổng quan môn học" chỉ hiện nhóm `tong_quan`. "Chỉ xuất hiện trong bài tập" là mục riêng. `thong_tin_hoc_phan` và `cuoi_sach`
  không hiện trong lộ trình, nhưng vẫn giữ trong dữ liệu. `overview_mentioned_node_ids` giữ để tương thích (bằng nhóm `tong_quan`).
- Không đổi `sequence`, `requires_edges`, `modules` (trừ danh sách `mentioned_node_ids` của module).

## Nghiệm thu
- **Test (fixture ở ít nhất hai ngôn ngữ ngoài vi/en):**
  - khái niệm chỉ-nhắc có căn cứ ở chunk nội dung được gắn vào module, dù tên không có nguyên văn;
  - mỗi vùng vào đúng nhóm, thứ tự ưu tiên đúng;
  - HTML chỉ ghi "Tổng quan môn học" cho nhóm `tong_quan`.
- **Chạy lại A10 sáu tài liệu cùng vé 20.** Báo số mục mỗi nhóm trước/sau; nhóm `khong_ro` của doc-2, doc-3 phải giảm rõ. Dãy học và cạnh
  không đổi.
- **Tôi kiểm:** đọc "Tổng quan môn học" và "Nhắc tới" của doc-1, doc-2, nhap-mon-ml, doc-6.
