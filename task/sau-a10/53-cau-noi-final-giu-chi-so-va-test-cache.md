# SA-53 — Bài giảng: lọc câu nối ở bản final giữ đúng chỉ số; test cho lớp lọc trước K6 và test cache theo hằng số thật

**Nguồn chân lý:** [spec B2](../../doc/pha-b2-spec.md), mục 6, K6 và K10–K12, nguyên tắc không rút ý đã gửi; [SA-49](49-bai-giang-mot-cau-noi-moi-tien-quyet.md);
[soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md), mục SA-49.

**Ai:** Claude cài (chủ dự án giao 2026-10-21) · người soát độc lập kiểm trước khi ghép · **Chi phí mô hình:** 0 USD ·
**Chặn bởi:** không · **Trạng thái:** sẵn sàng

## Vì sao

- **Câu nối đã bị K6 loại lại hiện trong bản final.** Mô hình giả trả câu nối `[a, a-trùng, c]`. Câu c qua K11/K12 nhưng lặp ý a, nên bị K6 loại lúc
  stream khi cổng chưa mở. Stream chỉ phát `a`, nhưng final và cache có `[a, c]`. Ca đối chứng `[a, c]`, không có câu trùng đứng trước, thì final bằng
  stream.
- **Gốc lỗi:** đoạn lọc câu nối trùng ở bản final, thêm ở SA-49, thay `output["bridges"]` bằng mảng đã rút ngắn. Sau đó `retained_indices` (khi cắt đuôi)
  và `dropped_indices` (K6), vốn đánh theo vị trí trong mảng gốc của luồng, lại được so với vị trí trong mảng đã rút ngắn. Ca cắt đuôi đúng nhờ
  `_merge_emitted` bù lại; ca K6 loại một câu đứng sau thì không được bù.
- **Lớp lọc trước K6 chưa có test thấy đỏ.** Bỏ lớp này thì mọi test vẫn xanh, dù `repeated_idea_text` tính trên bản đã lọc. Hai câu nối trùng có thể
  bật K6 giả: tốn một lượt sửa, hoặc bài bị gắn nhãn "cắt ngắn".
- **Test cache không chống lùi phiên bản.** Lùi `lecture_validator_version` về `lecture-validator-5` vẫn xanh, vì test tự đặt cứng phiên bản.

## Cần làm

- Ở bản final, áp lọc theo chỉ số gốc của luồng, gồm phần giữ khi cắt đuôi và phần bỏ của K6, rồi mới hay cùng lúc lọc câu nối trùng tiên quyết. Câu
  đã bị K6 loại lúc stream không được vào final hay cache.
- Đổi `lecture_validator_version` thành `lecture-validator-7`, vì bài đã cache có thể chứa câu nối lọt như trên.
- Sửa test cache: ghi bản cache bằng khoá tính với chuỗi cũ ghi cứng `lecture-validator-6`, rồi tra bằng `BSettings()` mặc định.

## Tiêu chí nghiệm thu

- [ ] Regression `[a, a-trùng, c]`, với c bị K6 loại trước cổng: đỏ trên mã hiện hành, xanh sau sửa. Final, cache và `prerequisites[].bridge` bằng
  đúng các câu đã phát. Ca đối chứng không có câu trùng đứng trước vẫn xanh.
- [ ] Test cho lớp lọc trước K6: hai câu nối trùng tiên quyết, lặp một chuỗi 8 từ, không làm bài thành "cắt ngắn" hay phải sửa. Bỏ lớp lọc thì test đỏ.
- [ ] Lùi `lecture_validator_version` về `lecture-validator-6`: test cache đỏ.
- [ ] Test bài giảng, hợp đồng, SA-45/49 và kiến trúc xanh; cổng toàn repo qua runner xanh. Phát lại 0 USD các bản ghi SA-43 còn ghim được
  (xstk-ch3-1@68, doc-4@27; doc-1@57 đã mất), báo số câu nối và số cặp (bài, tiên quyết).

## Ngoài vé

- Không đổi S3, không đổi nhiệt độ sửa.
- Không đổi K6 thành bộ chấm ngữ nghĩa.
- Không sửa prompt, cũng không sửa mã hoá prompt của bản ghi.
