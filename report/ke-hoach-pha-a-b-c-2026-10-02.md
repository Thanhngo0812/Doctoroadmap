# Kế hoạch còn lại của v3: pha A, B, C (2026-10-02)

Bản lưu theo yêu cầu của chủ dự án, trước khi nén ngữ cảnh. Kế hoạch chi tiết và trạng thái từng vé ở
[task/v3-lo-trinh-doc-duoc/00-ke-hoach.md](../task/v3-lo-trinh-doc-duoc/00-ke-hoach.md).

## Trạng thái lúc lưu
- **Vé 12** (cạnh theo định nghĩa ở A8): hợp đồng đã chốt. Pass phụ đầy đủ chạy trong kho `artifacts/v3-r12-final-evaluation`.
  - doc-1, doc-3, doc-6, naive-bayes, nhap-mon-ml đã xong tới tên module (v6).
  - doc-2 đang chạy tiếp pass phụ bằng mã vé 22.
- **Chấm mù T15-dev** (hai người làm riêng, không dùng AI):
  - luồng mới ngang luồng cũ, 0 cạnh ngược chiều;
  - khoảng 1/3 cạnh dư bị cho là "không cần thứ tự", ở cả hai luồng.
- **doc-1 trên đồ thị cuối:**
  - Q7b 0,877 (luồng cũ 0,660); Q7 0,667 (luồng cũ 0,825);
  - cạnh bao đóng P 97/111;
  - khoảng 89% dòng "cần:" là cần thật.
- **Vé đã xong:** 22 (song song cấu hình được, giảm giới hạn theo thế hệ, commit `ecc877c`); 09d (tên module chọn từ tên khái niệm); 02b (bảng
  kiểm không phụ thuộc ngôn ngữ).
- **Vé chờ giao:**
  - [20](../task/v3-lo-trinh-doc-duoc/20-giu-node-media-trong-lo-trinh.md): giữ node hình/bảng trong tệp lộ trình;
  - [21](../task/v3-lo-trinh-doc-duoc/21-tong-quan-mon-hoc.md): Tổng quan môn học;
  - [T10a](../task/v3-lo-trinh-doc-duoc/T10a-cli-tap-giu-lai.md): lệnh cho tập giữ lại và kiểm tương đương chuỗi.
- **[Giao thức T10/07 v2](../task/v3-lo-trinh-doc-duoc/T10-07v2-giao-thuc-tap-giu-lai.md):** soạn xong, chưa khoá.
- **Chi:** khoảng 45 USD trước phần doc-2 còn lại, ước theo sổ token. Tổng chính xác chờ báo cáo cuối vé 12. Ngân sách lớn đã được duyệt
  (credit Google Cloud 300 USD). Vẫn chỉ dùng `gemini-3.1-flash-lite`.

## Pha A — xong tài liệu phát triển (gần như không tốn tiền, khoảng 1–2 ngày)
1. **Nhân viên:**
   - doc-2 chạy nốt A9 → đặt tên khái niệm → A10 → đặt tên module.
   - Báo cáo cuối vé 12 ghi **một tổng chi duy nhất** cộng mọi sổ, số 429, điểm chấm doc-1/doc-2, bảng kiểm sáu tài liệu.
   - Làm vé **20** (giữ hình/bảng trong tệp lộ trình) và **21** (Tổng quan môn học), rồi chạy lại A10 cho sáu tài liệu.
   - Làm vé **T10a**: các lệnh cho lượt tập giữ lại và **kiểm tương đương chuỗi** (xem mục Rà quy trình).
   - Commit hết, cây sạch.
2. **Tôi (Claude):** đọc lộ trình sáu tài liệu, chấm lại chấm mù doc-2 theo đồ thị cuối (`scripts/cham-mu/cham_bang_v3.py --moi-cuoi`),
   nghiệm thu, rồi điền mức tài liệu phát triển vào giao thức.

## Pha B — khoá cấu hình và chạy tập giữ lại một lần (ước 15–40 USD, khoảng 1–2 ngày)
1. Tôi sinh bảng khoá (`scripts/khoa-cau-hinh/tao_bang.py`). **Chủ dự án duyệt và đặt trần chi** (đề xuất 50 USD).
2. Nhân viên chạy tới bước danh tính; dry-run trước, chủ dự án duyệt chi.
3. **Chủ dự án duyệt các cặp danh tính (T14)**, không cần mở bộ vàng.
4. Nhân viên chạy A8 → lộ trình; dry-run trước, chủ dự án duyệt chi.
5. Tôi chấm (`scripts/doc-lo-trinh/cham_tap_giu_lai.py`) và báo kết quả, kể cả kết quả xấu. Nếu xếp được người thì thêm chấm tay.

## Pha C — sau tập giữ lại
- Báo cáo tổng kết v3.
- Thử với 3–5 sinh viên học một chương bằng lộ trình.
- Rồi tới các hướng tiếp:
  - vé 13 (trích định lý/mệnh đề có tên ở A3, gộp với nhận dạng công thức ở A1);
  - tạo bài giảng (dùng cạnh mở, hình/bảng, cạnh công cụ);
  - tích hợp web (giới hạn chung cho nhiều worker, hàng đợi);
  - chuyển về Gemini API khi hết credit (chỉ đổi `.env`);
  - thử Flex/Batch để giảm chi phí;
  - tăng tốc A1 cho ứng dụng (đã tạm ngưng, ghi trong kế hoạch).
- Cải tiến v4 cần **tập giữ lại mới** (tài liệu mới và vàng mới) vì tập giữ lại hiện tại chỉ dùng được một lần.

## Rà quy trình (2026-10-02)
- **Đang chạy tốt:** vé có tiêu chí nghiệm thu, và Claude kiểm độc lập bằng đột biến, phát lại, mô phỏng. Cách này đã bắt được:
  - lỗi cửa sổ định nghĩa (Claude đặc tả sai);
  - cổng pilot so nhầm mốc;
  - nút thắt điểm lưu;
  - lỗi giới hạn chia đôi mỗi 429.
- **Chỗ hở đã tìm:** số nghiệm thu đến từ **script đánh giá**, còn tập giữ lại chạy bằng **lệnh `roadmap`**. Hai đường dựng chuỗi riêng; ví dụ
  `max_output_tokens` 2048/1024/512 ở script so với 8192 ở lệnh. Trước khi khoá, mọi stage của lệnh `roadmap` phải ra "tái dùng" trên
  artifact đã nghiệm thu (vé T10a mục 5, điều kiện 5 của giao thức).
- **Bốn luật thêm:**
  1. Đổi hợp đồng có tốn tiền thì phát lại 0 USD trên nhật ký cũ trước.
  2. Nhân viên commit trước khi báo kiểm thử.
  3. Đường đo nghiệm thu phải là đường chạy sản phẩm.
  4. Mỗi báo cáo tốn tiền có một tổng chi duy nhất.
