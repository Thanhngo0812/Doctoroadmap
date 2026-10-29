# DG-21 — Biến thể logistic và cross-encoder trong bộ đánh giá (phần D của DG-20)

**Nguồn:** spec mục 11 (hai hàng logistic, cross-encoder); vé DG-20 phần D · **Ai:** agent; Claude chạy phần cần `torch` · **Chi phí:** 0 ·
**Chặn bởi:** DG-20, DG-11 · **Hạn:** 04/11 · **Trạng thái:** ready-for-agent

## Vì sao

DG-20 so logistic và cross-encoder với LightGBM bằng LOBO trên D-01, nhưng để phần D (đưa hai biến thể vào bảng so trên tập thử) ngoài phạm vi. Hiện chưa có:
- mô hình logistic học trên đủ 16 cuốn: chỉ có mô hình theo từng lần chia;
- cách chạy A1 với mô hình khác;
- cách chấm lại cặp pass phụ bằng mô hình khác rồi phát lại A9 → A10.

Bảng 11 của bản hội đồng có ba hàng chờ số: `a1_logistic`, `a8_logistic`, `a8_cross_encoder`.

## Làm được gì

### A. Mô hình logistic cuối (học trên 16 cuốn D-01)

- Script trong `scripts/dg20/` học logistic M1 (nhận tiêu đề), M2 (nối dòng), M3 (pass phụ) trên đủ 16 cuốn học D-01. Dùng đúng đặc trưng, xử lý thiếu và chuẩn hoá
  của `scripts/dg20/logistic.py`.
- `C` là giá trị được chọn **nhiều nhất** qua 16 lần chia ở lưới mở rộng (`report/danh-gia-pha-a/DG-20-ket-qua/logistic-m*-c-rong.jsonl`). Hoà thì lấy `C` nhỏ hơn.
  Ghi lý do vào manifest.
- M3 cần xác suất đã hiệu chỉnh giống mô hình sản phẩm: hiệu chỉnh isotonic học trên dự đoán **ngoài mẫu** LOBO của logistic, cùng cách DG-20 làm cho LightGBM.
- Lưu vào `evaluation/mo-hinh/dg21/{m1,m2,m3}-logistic/`, mỗi thư mục có manifest (cấu hình, `C`, SHA-256 dữ liệu và tệp, phiên bản thư viện, seed) và kiểm
  nạp lại cho ra dự đoán y hệt.
- Cấm như DG-20: chỉ D-01 học; không đụng tập khoá, tập phát triển, tập thử.

### B. A1 với logistic

Lệnh chạy bộ đọc nhẹ (`NheParser`) với mô hình logistic thay `heading.joblib` và `join.joblib`, không gọi LLM, trên một PDF và manifest.
- Đầu ra chấm được bằng `cham-a1a2` với G1, cùng bộ chấm như hệ chính. Hệ `a1_logistic`; chỉ khối cấu trúc có nghĩa.
- Tìm cách dùng `NheParser(model_dir=...)`. Nếu bộ đọc kiểm SHA-256 cứng của mô hình sản phẩm, đừng sửa `src/`. Dừng phần đó, ghi trong báo cáo, đề xuất cách sửa nhỏ
  nhất (ví dụ cho phép thư mục mô hình có manifest SHA riêng).

### C. Pass phụ chấm lại, rồi phát lại A9 → A10

- Bộ chấm thay thế cài giao diện `SecondaryScorer` của sản phẩm, đặt ở seam xuất:
  - **logistic**: nạp mô hình M3 logistic và hiệu chỉnh isotonic;
  - **điểm có sẵn**: đọc điểm đã hiệu chỉnh của từng cặp từ tệp, dùng cho cross-encoder.
- Chạy `BuildSecondaryMLEdges` của sản phẩm (cùng luật ngưỡng "round-sum-isotonic…") với bộ chấm thay thế, trên **bản chép** kho của lượt chính. Không ghi vào
  kho lượt chính. Thay cạnh pass phụ, rồi phát lại A9 → A10 bằng bộ phát lại DG-11 (`canh_thay`). Xuất hợp đồng hệ `a8_logistic` hay `a8_cross_encoder`,
  `chi_phi` bằng 0, `bien_the` ghi tên mô hình và SHA.
- **Cross-encoder:** gói `danhgia` không phụ thuộc `torch`. Chia ba bước:
  1. lệnh xuất các cặp ứng viên kèm văn bản đúng như đầu vào của `scripts/dg20/ce_hoc.py` khi học (cùng cách cắt, độ dài 256, đánh dấu X/Y);
  2. script `scripts/dg21/ce_cham.py` chấm các cặp bằng mô hình cross-encoder, rồi hiệu chỉnh isotonic. Bản hiệu chỉnh học trên dự đoán ngoài mẫu epoch 3 của 4 nếp
     DG-20 (`ngoai-mau-nep*-e3.jsonl`). Script này Claude chạy ở môi trường có `torch`; agent chỉ test phần không cần `torch`;
  3. bộ chấm "điểm có sẵn" nạp tệp điểm.
- **Kiểm tái tạo (bắt buộc):** chạy cùng đường đó với bộ chấm LightGBM của sản phẩm trên kho fixture có graph thật. Cạnh pass phụ và dãy học phải **y hệt** lượt đã
  lưu. Không tái tạo được thì mọi số logistic và cross-encoder vô nghĩa, nên phải dừng và báo.

## Tiêu chí

- [ ] Mô hình logistic có manifest, kiểm nạp lại; `C` chọn đúng luật, có test tính tay luật chọn `C` (hoà lấy nhỏ hơn).
- [ ] Kiểm tái tạo pass phụ LightGBM qua adapter: lệch 0.
- [ ] Bộ chấm logistic trên fixture cho điểm khớp `predict_proba` của mô hình nạp trực tiếp, sau isotonic.
- [ ] Tệp cặp xuất cho cross-encoder: mỗi cặp ứng viên đúng một dòng, đúng hai chiều nếu luật pass phụ chấm hai chiều. Thiếu điểm thì lỗi, không coi là 0.
- [ ] Hợp đồng ba hệ qua validator; lệnh in theo cổng allowlist khi `tap = thu`, đồng thời thêm lệnh mới vào danh sách phân loại của `test_cong_allowlist.py`.
- [ ] Bảng phá, tối thiểu:
  - isotonic học trên dự đoán trong mẫu;
  - bỏ hiệu chỉnh;
  - adapter ghi vào kho lượt chính;
  - thiếu điểm cặp coi là 0;
  - chọn `C` lớn nhất thay `C` nhiều nhất.
