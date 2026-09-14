# 09 — Kế hoạch đợt 2: luật kiểm nhất quán trên v3

> **Kết quả 2026-09-14:** theo luật là không nhận. Precision gộp 0,946 (35/2/12), dưới ngưỡng 0,95 đúng một ca gộp sai;
> bốn cổng còn lại qua. Hai ca gộp sai còn lại đúng là hai ca mục "Kỳ vọng" đã nói trước.
> **Chủ dự án chấp nhận bản này dù precision thấp hơn ngưỡng.** Việc tiếp theo là ticket 01, rồi ticket 15 với ngưỡng
> xác nhận mới (precision gộp ≥ 0,93). Chi tiết ở [ticket 14](14-cham-dot-2.md).

**Quyết định của chủ dự án (2026-09-14):** chọn luật kiểm nhất quán trên v3, tức mục 4 trong "Hướng đi tiếp" ở feedback
F18, vòng 25. Giữ prompt v3 và kênh quan hệ mở. Thêm một luật kiểm, không cần nhãn: đầu ra tự mâu thuẫn thì bắt mô hình
phán lại.

**Nơi làm:** nhánh `a4-quan-he-mo-2a`, commit `454a899`. `main` giữ code mặc định (commit `aad4998`) cho tới khi đợt
này qua luật.

## Vì sao luật này nhắm đúng chỗ

Ở lần chạy v3, cả 9 ca gộp sai đều do mô hình phán. 7 trong số đó nằm trong node mà chính mô hình ghi một quan hệ giữa
hai nhóm của node đó, ví dụ gộp `Pessimistic Locking` với `Database Locking` rồi lại ghi `subtype_of` giữa chúng.
Đầu ra tự nói "đây là hai thứ", nên không cần nhãn vẫn biết nó sai. Validator hiện chỉ loại quan hệ và vẫn giữ lần gộp.

## Luật

Kiểm trong `validate_partition`, sau phần kiểm cấu trúc hiện có:

- **R1 — quan hệ trong cùng một node.** Một quan hệ nối hai nhóm khác nhau mà mô hình đặt chung node, với kiểu **không**
  thuộc tập đồng nhất ở dưới, thì đầu ra mâu thuẫn. Có quan hệ tức là hai thứ khác nhau.
- **R2 — quan hệ đồng nhất giữa hai node.** Kiểu thuộc tập đồng nhất nối hai nhóm nằm ở hai node khác nhau thì đầu ra mâu
  thuẫn. Cùng một thực thể thì phải chung node.
- **Tập đồng nhất** là danh sách cố định, so sau khi chuẩn hoá kiểu: `same_as`, `equivalent_to`, `identical_to`,
  `synonym_of`, `alias_of`. Không so mờ.
- Quan hệ đồng nhất nằm **trong** cùng node thì không mâu thuẫn, chỉ thừa. Nó vẫn bị `split_relation_edges` loại như hiện
  nay.

Gặp mâu thuẫn thì **dùng lại đúng cơ chế sẵn có**:
- báo lỗi, kèm id nhóm và kiểu quan hệ của từng mâu thuẫn;
- thử lại một lần, lỗi được gửi kèm prompt;
- vẫn mâu thuẫn thì cả cụm `deferred`.

Không thêm cách xử lý mới.

Kèm một sửa bắt buộc: đầu ra lấy từ cache hiện được kiểm lại **ngoài** `try` (`canonical_reasoning.py`, hàm `call`).
Luật kiểm chặt hơn làm một đầu ra cũ không qua được, và khi đó cả lượt chạy dừng. Phải chuyển thành coi như cache trượt
rồi gọi lại mô hình.

## Chia việc

| Ticket | Việc | Ai | Chờ |
|---|---|---|---|
| [10](10-luat-nhat-quan-trong-validator.md) | R1, R2 trong validator, lỗi riêng, test | Nhân viên | 09 |
| [11](11-cache-gap-dau-ra-khong-con-hop-le.md) | Cache: đầu ra cũ trượt luật thì gọi lại | Nhân viên | 09, làm song song 10 |
| [12](12-config-chi-so-va-runner.md) | Phiên bản luật trong config, chỉ số, runner | Nhân viên | 10, 11 |
| [13](13-chay-nhanh-thu-lan-2.md) | Chạy nhánh thử lần 2, mẫu mới | Nhân viên | 12 |
| [14](14-cham-dot-2.md) | Chấm theo luật dưới đây | Claude | 13 |
| [01](01-spec-va-adr.md) | Spec, ADR 0007, gồm cả luật nhất quán | Claude | 14 qua |
| [15](15-nhan-vao-main.md) | Mẫu thứ hai ở kho riêng; qua thì gộp vào `main` và chạy kho chính | Nhân viên | 14 qua, 01 xong |

## Luật đánh giá — viết 2026-09-14, trước mọi lần chạy

Chạy nhánh mới bằng flash-lite trên bốn tài liệu. Đây là mẫu mới: kho chính chỉ có quyết định của prompt v1 nên không
dùng lại được. So với mặc định: 31/0/16, F1 0,795, precision `subtype_of` 0,635. Nhận khi **qua cả năm cổng**, giữ
nguyên ngưỡng của ticket 00:

1. Precision gộp ≥ 0,95.
2. F1 gộp ≥ 0,775.
3. Precision `subtype_of` ≥ 0,635.
4. Cụm hỏng hẳn ≤ 1 trên bốn tài liệu, **tính cả cụm bị hoãn vì vẫn mâu thuẫn sau lần thử lại**.
5. Trong mẫu 30 quan hệ không phải `subtype_of` (seed 42), ≥ 60% đúng. Người gán là Claude.

Số phụ, ghi vào báo cáo nhưng không làm cổng:
- số lượt thử bị R1 hoặc R2 bắt, số cụm phải thử lại, và số cụm bị hoãn vì mâu thuẫn;
- các ca gộp sai còn lại, và ca nào không mang tín hiệu mâu thuẫn;
- so với lần chạy v3 đầu: precision và recall gộp, precision `subtype_of`, số quan hệ.

Trượt một cổng thì không nhận, và báo chủ dự án. Không chỉnh prompt hay luật rồi chấm lại trên bộ vàng này.

**Kỳ vọng, nói trước:**
- Trên chính mẫu v3 đầu, R1 bắt được 7/9 ca gộp sai và R2 bắt 1 quan hệ; 8/101 lượt phán sẽ phải thử lại.
- Hai ca gộp sai không mang tín hiệu thì luật này **không** bắt được: `Bài toán phân loại` / `Bài toán phân cụm`, và
  `Đường hồi quy mẫu Y theo X` / `Đường hồi quy mẫu`.
- Kể cả khi luật sửa đúng cả 7 ca và mọi thứ khác giữ nguyên, precision gộp chỉ khoảng 38/40 = 0,95, sát ngưỡng.
- Mẫu mới có thể nhiều hoặc ít ca gộp sai hơn mẫu đầu. **Khả năng trượt cổng 1 là đáng kể.**

**Giới hạn biết trước:**
- Luật được nghĩ ra sau khi đã đọc lỗi trên bộ vàng này, nên số sẽ lạc quan.
- Cổng 5 do Claude gán.
- Bộ vàng gán 3 cặp bộ phận là cha–con.

## Chi phí và đường lui

**Chi phí** (chỉ flash-lite):
- ticket 13: khoảng 134 lời gọi như lần v3 đầu, cộng số lượt thử lại (lần đầu ước khoảng 8);
- ticket 15: hai lượt ở mức đó, gồm mẫu thứ hai trong kho riêng và lượt chạy kho chính;
- lượt chạy lại sau đó: 0 lời gọi.

**Đường lui:**
- Trượt ở ticket 14, hoặc ở mẫu thứ hai (ticket 15), thì `main` không đổi gì. Nhánh giữ lại làm hồ sơ.
- Lượt chạy kho chính trượt thì `git revert` commit gộp. Kho chọn `latest` theo số phiên bản lớn nhất, nên phải hỏi chủ
  dự án trước khi xoá các phiên bản vừa sinh.
