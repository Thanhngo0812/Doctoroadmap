# 14 — Chấm đợt 2 theo luật đăng ký trước

**What to build:** Kết luận nhận hay không nhận luật nhất quán, bằng đúng luật ở ticket 09, không đổi luật sau khi thấy số.

**Người làm:** Claude (reviewer)

**Blocked by:** 13 — Chạy nhánh thử lần 2

**Status:** done — theo luật: không nhận (trượt cổng 1 đúng một ca gộp sai). **Chủ dự án chấp nhận bản này**,
2026-09-14; xem mục "Quyết định của chủ dự án" ở cuối.

- [x] Kiểm code đợt 2 như các vòng trước:
  - đọc diff so với commit `454a899`;
  - chạy toàn bộ test;
  - tự đột biến R1, R2, tập đồng nhất và phần sửa cache;
  - dựng lại từ nhật ký với mô hình bị bẫy.
- [x] Chấm độc lập bằng script riêng, đối chiếu với số ticket 13.
- [x] Áp năm cổng ở ticket 09.
- [x] Lấy mẫu 30 quan hệ không phải `subtype_of`, seed 42. Công bố danh sách kèm nhãn.
- [x] Ghi các số phụ ở ticket 09: mâu thuẫn bị bắt, cụm thử lại, cụm hoãn, các ca gộp sai còn lại và tín hiệu của chúng,
      so sánh với lần v3 đầu.
- [x] Ghi kết luận vào ticket này, báo cáo chạy thật và feedback. Trượt thì báo chủ dự án kèm số, không chỉnh gì rồi chấm
      lại trên bộ vàng này.

## Kiểm code

| Hạng mục | Kết quả |
|---|---|
| Diff so với `454a899` | Chỉ 5 file `src`/`scripts` và 2 file test, đều trong phạm vi ticket 10–12 |
| Test | ✅ 294/294 khi chặn mạng; `git diff --check` sạch |
| Đột biến đợt 2 (13 cái của tôi) | ✅ 13/13 bị bắt: bỏ R1, bỏ R2, bớt kiểu khỏi tập đồng nhất (2 cách), R2 không chuẩn hoá, chỉ báo mâu thuẫn đầu tiên, bỏ nhánh `ContradictionError`, bỏ fallback cache, không đếm cache trượt, bỏ khoá config, không đếm cụm hoãn, đếm thử lại theo lượt, không gửi lỗi khi thử lại |
| F80 (đột biến vòng 25) | ✅ M5, M9, M14 giờ đều bị bắt |
| Bất biến artifact | ✅ Cả bốn tài liệu |
| Dựng lại từ nhật ký | ✅ 0 lời gọi; node, cạnh, hoãn, redirect giống hệt; config hash giống. Riêng `partition_contradictions` và `contradiction_retried_calls` về 0 (F82) |

## Kết quả

Chấm độc lập khớp đúng số của ticket 13.

| Cổng | Ngưỡng | Mặc định | v3 lần đầu | **v3 + luật nhất quán** | |
|---|---|---:|---:|---:|---|
| 1. Precision gộp | ≥ 0,95 | 1,000 | 0,809 | **0,946** (35/2/12) | ❌ |
| 2. F1 gộp | ≥ 0,775 | 0,795 | 0,809 | 0,833 | ✅ |
| 3. Precision `subtype_of` | ≥ 0,635 | 0,635 | 0,688 | 0,658 (25 đúng, 13 sai) | ✅ |
| 4. Cụm hỏng hẳn | ≤ 1 | 0 | 0 | 0 | ✅ |
| 5. Mẫu 30 quan hệ đúng | ≥ 60% | — | 73% | 70% (21/30) | ✅ |

**Kết luận: không nhận.** Theo luật, trượt một cổng là đủ.

Khoảng cách tới ngưỡng chỉ là **một ca gộp sai**: với 35 cặp đúng, muốn precision ≥ 0,95 thì chỉ được sai tối đa một ca.
Không nới ngưỡng sau khi đã thấy số; đó chính là điều luật viết trước khi chạy ngăn lại.

## Số phụ

- **Luật bắt được gì.** 8 lượt thử bị bắt, gồm 10 mâu thuẫn: R1 `subtype_of` 6, R1 `precedes` 2, R1 `example_of` 1,
  R2 `equivalent_to` 1. Cả 8 lượt phán đều sửa được ở lần thử lại; 0 cụm bị hoãn.
- **Hai ca gộp sai còn lại đúng là hai ca ticket 09 đã nói luật không bắt được:** `Bài toán phân loại` / `Bài toán
  phân cụm`, và `Đường hồi quy mẫu Y theo X` / `Đường hồi quy mẫu`. Đây là mẫu mới mà hai ca vẫn lặp lại, nên lỗi mang
  tính hệ thống với prompt v3, không phải may rủi.
- **Cái giá của lượt thử lại.** So với v3 lần đầu, mất 4 cặp *cùng* và thêm 1 cặp:
  - cả 4 cặp mất đều nằm trong cụm có thử lại: `Độ chính xác` / `Độ chính xác ε`, `Độ tin cậy` / `Độ tin cậy của ước
    lượng`, `Không gian dữ liệu X` / `Không gian dữ liệu`, `Bài toán tìm kích thước mẫu` / `Xác định kích thước mẫu`;
  - khi được báo *"hãy tách hai nhóm"*, mô hình tách luôn cả node (F83);
  - cặp thêm là `Data preparation` / `Tiền xử lý dữ liệu`, nhờ R2.
- **So với mặc định:** precision gộp 1,000 → 0,946; recall 0,660 → 0,745; F1 0,795 → 0,833; precision `subtype_of`
  0,635 → 0,658; bắt được 27/47 cặp cha–con (mặc định 35/47); có thêm 35 quan hệ kiểu mở.
- **Chi phí:** 138 lời gọi flash-lite, gồm 8 lượt thử lại.

## Mẫu 30 quan hệ (seed 42; Claude gán, không phải người độc lập)

Đúng (21):
- `Hàm mật độ xác suất related_to Likelihood`
- `Kiến trúc Hub - Client used_with WebSocket`
- `Lấy mẫu aims_to_achieve Tính đại diện`
- `Khai phá dữ liệu uses Dữ liệu`
- `Ứng dụng của phương trình hồi quy tuyến tính mẫu uses Đường hồi quy tuyến tính mẫu`
- `Kiểm định giả thiết thống kê tests Giả thiết thống kê`
- `Khoảng ước lượng của phương sai tổng thể example_of Ước lượng phương sai` — ranh giới: bộ vàng gán *không chắc*
- `Quyết định chấp nhận H informs Kết luận cuối cùng`
- `Độ chính xác trong ước lượng tỉ lệ component_of Ước lượng tỉ lệ`
- `Quá khớp contrasts_with Kém khớp`
- `Ước lượng trung bình estimates Trung bình tổng thể`
- `Mẫu hai chiều rearranged_form_of Mẫu tương quan cặp`
- `Dữ liệu rời rạc contrasts_with Dữ liệu liên tục` — văn bản trình bày ví dụ dữ liệu rời rạc, rồi *"Khi dữ liệu liên
  tục, cần có cách tính cho likelihood"*
- `Maximum Likelihood Estimation uses Likelihood`
- `Quy tắc quyết định produces Quyết định chấp nhận H`
- `Biến đổi dữ liệu component_of Tiền xử lý dữ liệu`
- `Analytic approach precedes Data understanding` — văn bản liệt kê các bước theo đúng thứ tự
- `Kiểm định tham số contrasts_with Kiểm định phi tham số`
- `Phương sai mẫu hiệu chỉnh related_to Phương sai mẫu`
- `Làm sạch dữ liệu component_of Tiền xử lý dữ liệu`
- `Tiêu chuẩn kiểm định χ 0 2 uses Phân phối χ 2`

Sai (9):
- `Pessimistic Locking uses Mutex` — hai cơ chế dùng song song ở hai tầng; không cái nào dùng cái kia.
- `Mutex uses Race Condition` — sai kiểu: Mutex dùng để giải quyết race condition.
- `Kiến trúc phân lớp example_of Thiết kế hệ thống` — không câu nào nêu.
- `Bài toán học máy component_of Học máy` — kiểu gượng; bộ vàng gán *liên quan*.
- `Database Transaction supports Thiết kế Cơ sở dữ liệu` — không câu nào nêu.
- `Tỉ lệ mẫu computed_by Tổng thể` — tỉ lệ mẫu tính từ mẫu, không phải từ tổng thể.
- `Bài toán tìm kích thước mẫu example_of Xác định kích thước mẫu` — bộ vàng coi hai tên là một. Sau lượt thử lại mô hình
  tách chúng ra, rồi dùng quan hệ để lấp chỗ gộp.
- `Cây quyết định contrasts_with Rừng ngẫu nhiên` — văn bản chỉ liệt kê hai mô hình cạnh nhau.
- `Kiểm định giả thiết thống kê solves Bài toán kiểm định giả thiết thống kê` — câu trích không nêu; bộ vàng coi là một.

## Quyết định của chủ dự án (2026-09-14)

**Chấp nhận v3 cộng luật kiểm nhất quán, dù precision gộp 0,946 thấp hơn ngưỡng 0,95.** Đây là quyết định sản phẩm của
chủ dự án, vượt lên luật chấm viết trước; không phải kết quả của luật đó.

Những gì được chấp nhận, so với mặc định:
- precision gộp 1,000 → 0,946;
- recall 0,660 → 0,745, F1 0,795 → 0,833;
- precision `subtype_of` 0,635 → 0,658;
- thêm quan hệ kiểu mở từ 2a: 35 quan hệ khác `subtype_of`, mẫu cho 70% đúng.

Giới hạn đã biết, đi kèm quyết định:
- Hai kiểu gộp sai hệ thống còn lại (tên chung với tên riêng, như `Đường hồi quy mẫu Y theo X` / `Đường hồi quy mẫu`;
  và các bài toán anh em, như `Bài toán phân loại` / `Bài toán phân cụm`) không có luật nào chặn.
- Lượt thử lại tách cả node, làm mất cặp đúng (F83).
- Bộ vàng do Claude gán, và các thiết kế này đã được chọn sau khi thấy lỗi trên chính bộ vàng đó.

Việc tiếp theo: ticket 01 (spec, ADR), rồi ticket 15 với ngưỡng precision mới cho các lượt chạy xác nhận.
