# DG-20 — Chọn lại siêu tham số ba mô hình học máy, baseline logistic, cross-encoder cho pass phụ

**Nguồn:** kế hoạch Q40 (2026-10-27) · **Ai:** agent C cài phần A, B và mã phần C; Claude chạy phần C trên máy GPU và nghiệm thu · **Chi phí:** 0 USD (không gọi
mô hình ngôn ngữ) · **Chặn bởi:** — · **Hạn:** phần A, B đóng băng **30/10**; phần C **31/10**, trước lượt chạy tập phát triển · **Trạng thái:** ready-for-agent

## Vì sao

Ba mô hình LightGBM của Pha A đang dùng siêu tham số đặt tay:

| Mô hình | Khâu | Cấu hình hiện tại | Tệp |
|---|---|---|---|
| M1 nhận tiêu đề | A1 | 15 lá, 300 cây, học 0,05 | `vendor/a1-nhe/heading.joblib` |
| M2 nối dòng tiêu đề | A1 | 7 lá, 150 cây, học 0,05 | `vendor/a1-nhe/join.joblib` |
| M3 pass phụ | A8 | 15 lá, 300 cây, học 0,03, hiệu chỉnh isotonic | `vendor/a8-pass-phu-ml/model.txt` |

Hội đồng sẽ hỏi "vì sao 15 lá" và "vì sao LightGBM". Vé này trả lời bằng một quy trình chọn khai trước, cộng hai đối chứng: hồi quy logistic cho cả ba mô hình,
và cross-encoder đọc văn bản cho M3.

## Phần A — chọn lại siêu tham số LightGBM (LOBO-16)

**Dữ liệu:** chỉ 16 cuốn học của D-01, đúng bảng đặc trưng và nhãn mà mô hình hiện tại đã học. **Không** dùng tập khoá D-02 (`Desktop\d02-tap-khoa`), `d01-t01`,
`d01-t02`, tập phát triển (xstk, doc-1, nhap-mon-ml) hay tập thử.

**Kiểm tái tạo trước tiên:** học lại với đúng cấu hình hiện tại trên đúng dữ liệu. Kết quả phải ra mô hình trùng mô hình trong `vendor/`: cùng SHA-256, hoặc cùng
dự đoán trên toàn bộ dòng học, sai khác không quá 1e-9. Không tái tạo được thì dừng và báo; khi đó chưa so được gì.

**Quy trình**, khai trước và không đổi sau khi thấy số:
1. **Vòng ngoài LOBO-16:** mỗi lần để ra một cuốn.
2. **Vòng trong:** trong 15 cuốn còn lại, 3 cuốn làm tập dừng sớm, chọn tất định theo seed `20261027` và mã cuốn để ra.
3. **Lưới:** `num_leaves` ∈ {7, 15, 31, 63, 127, 255}. Tốc độ học và các tham số khác giữ như cấu hình hiện tại của từng mô hình.
4. **Dừng sớm:** trần 5000 vòng, dừng khi điểm trên tập dừng sớm không tăng trong 100 vòng.
5. Với mỗi cấu hình: học lại trên đủ 15 cuốn với số vòng tốt nhất vừa tìm được, rồi chấm trên cuốn để ra.
6. **Thước chọn:** AP (average precision) trên cuốn để ra, lấy trung bình trên 16 cuốn. Báo kèm thước vận hành của sản phẩm: F1 ở ngưỡng 0,5 với M1, M2; AP sau
   hiệu chỉnh với M3.
7. **Luật một sai số chuẩn:** gọi best là cấu hình có AP trung bình cao nhất, SE là độ lệch chuẩn của AP theo cuốn của best chia √16. Chọn cấu hình **ít lá
   nhất** có AP trung bình ≥ AP(best) − SE.
8. **Mô hình cuối:** học trên đủ 16 cuốn với cấu hình được chọn. Số vòng là trung vị số vòng tốt nhất của 16 lần chia. Với M3, học lại bộ hiệu chỉnh isotonic trên
   dự đoán ngoài mẫu theo cuốn, như `dong_bang_e5.py`.
9. **Đóng băng:** ghi mô hình mới vào thư mục mới (không ghi đè `vendor/` khi chưa được Claude duyệt). Manifest gồm cấu hình, bảng lưới đủ 16 cuốn, SE, lý do
   chọn, SHA-256, phiên bản thư viện, seed.

## Phần B — baseline hồi quy logistic (cả ba mô hình)

- Cùng đặc trưng, cùng các lần chia LOBO, cùng vòng trong.
- Đặc trưng chuẩn hoá. Ô thiếu thay bằng trung vị của tập học, kèm cột chỉ báo thiếu.
- `class_weight` cân bằng. Tham số `C` ∈ {0,01; 0,1; 1; 10}, chọn trên tập dừng sớm của vòng trong.
- Báo AP theo cuốn của logistic cạnh LightGBM đã chọn, và hiệu theo cặp trên 16 cuốn: trung bình, khoảng tin cậy bootstrap theo cuốn (LCG tất định của
  `danhgia.thong_ke.lcg`), sign test (`danhgia.thong_ke.kiem_dinh.sign_test`).
- Thêm một bảng giải thích: hệ số logistic chuẩn hoá và độ quan trọng (gain) của LightGBM, 10 đặc trưng đầu mỗi mô hình.

## Phần C — cross-encoder cho M3 (pass phụ)

Chỉ M3 có phần này; hai mô hình A1 không cần.

- **Đầu vào:** đúng thiết kế E6 (`report/nghien-cuu-pass-phu-vong-2-ke-hoach-2026-10-10.md`, mục 3), tức phiếu D-01 gồm tên Y, cửa sổ có X được đánh dấu, và
  `x_dinh_nghia`. Nhãn nhị phân giống M3 (`can_de_hieu`).
- **Mô hình:** `FacebookAI/xlm-roberta-base` (MIT), đóng băng lớp embedding để vừa GPU 4 GB, độ dài 256, fp16, lô 8 với tích luỹ gradient 4, học 2e-5, 3 epoch,
  seed `20261027`. PhoBERT-base không chọn vì cần tách từ, dễ lệch với lúc huấn luyện trước; PhoBERT-v2 là AGPL.
- **Chia:** 4 phần theo cuốn (mỗi phần 4 cuốn), tất định theo seed. Học lại 16 lần trên máy GPU 4 GB không kịp trước ngày đóng băng. LightGBM đã chọn và
  logistic cũng được chấm lại trên **cùng 4 phần** để so ngang hàng.
- **Hiệu chỉnh và ngưỡng** như M3: isotonic trên dự đoán ngoài mẫu, rồi luật top-k của sản phẩm (`k = round(tổng xác suất hiệu chỉnh)`).
- **Đo phút trên CPU** của laptop cho 1.000 cặp, đặt cạnh LightGBM. Đây là chi phí nếu đưa vào sản phẩm.
- **Mã chạy được trên máy GPU Linux** (`venv` riêng, ghi rõ gói và phiên bản). Claude chạy phần học; agent C không SSH. Ghi danh sách dữ liệu chép lên máy GPU:
  chỉ phiếu D-01, không sách thử.

## Phần D — đưa vào bộ đánh giá trên tập thử

Không có thước mới; chỉ thêm hàng vào bảng so.
- **A1, logistic thay LightGBM:** chạy bộ đọc nhẹ với mô hình logistic trên 8 cuốn thử (không gọi mô hình ngôn ngữ), chấm bằng G1 qua bộ chấm DG-13.
- **A8 pass phụ, logistic hoặc cross-encoder thay LightGBM:** chấm lại các cặp ứng viên pass phụ của lượt hệ chính, rồi phát lại A9 → A10 bằng bộ phát lại
  DG-11. Chấm bằng G4.
- Nếu phần A đổi mô hình sản phẩm thì hệ chính chạy với mô hình mới, và mô hình cũ chỉ còn trong báo cáo LOBO.

## Tiêu chí

- [ ] Kiểm tái tạo đạt cho cả ba mô hình, hoặc báo rõ vì sao không tái tạo được.
- [ ] Không một dòng nào của cuốn để ra lọt vào học hay dừng sớm. Có test trên dữ liệu giả: cuốn để ra mang nhãn ngược hoàn toàn, nên mọi rò rỉ đều làm điểm
      ngoài mẫu tăng vọt.
- [ ] Luật một sai số chuẩn có test tính tay, gồm cả ca hoà điểm.
- [ ] Bảng lưới đủ 6 × 16 ô cho mỗi mô hình. Logistic có đủ 16 cuốn. Cross-encoder có đủ 4 phần.
- [ ] Bảng phá, gồm ít nhất:
  - dừng sớm trên cuốn để ra;
  - chọn cấu hình AP cao nhất, bỏ luật một SE;
  - chia ngẫu nhiên theo dòng thay vì theo cuốn;
  - logistic không chuẩn hoá;
  - hiệu chỉnh isotonic học trên dự đoán trong mẫu.
- [ ] Báo cáo `report/danh-gia-pha-a/DG-20-<ngày>.md`: bảng lưới, cấu hình chọn kèm lý do, so logistic, so cross-encoder (sau khi Claude chạy), phút CPU.
