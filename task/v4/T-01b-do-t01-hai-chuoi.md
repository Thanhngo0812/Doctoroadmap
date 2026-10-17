# T-01b — Đo T-01: chuỗi v3 và chuỗi gộp trên hai cuốn giữ lại

**Nguồn chân lý:**
- [vé T-01a](T-01a-chay-luong-hai-cuon-giu-lai.md), [báo cáo đóng băng vàng](../../report/v4-T01a-buoc8-2026-10-17.md);
- [spec đổi mặc định](../../doc/doi-mac-dinh-chuoi-gop-spec.md), mục "Quyết định khác — T-01";
- [cổng 19l](../../report/v4-19l-cong-doi-mac-dinh-2026-10-17.md).

**Ai:** Claude · **Chi phí mô hình:** ước 6–8 USD; dry-run từng bước, chủ dự án duyệt chi sau dry-run · **Chặn bởi:** T-01a bước 8 (xong 2026-10-17)
· **Trạng thái:** chờ duyệt chi

## Vì sao

T-01 là tập giữ lại duy nhất chưa dùng để chỉnh luồng.
- **Kết luận cuối của đợt gộp.** Chuỗi gộp đã nghiệm thu trên tài liệu phát triển (17i, cổng 19l). T-01 trả lời câu hỏi còn lại: trên tài liệu mới,
  chuỗi gộp có kém v3 không. Chủ dự án duyệt hướng "đo cả v3 và chuỗi gộp" ngày 2026-10-17.
- **Số cuối của vé 05 và pass phụ ML.**
- **Không phải cổng bật/tắt.** Mã v3 đã gỡ (19n). Kết quả xấu dẫn tới vé sửa, không quay lại v3.

**Vàng** (chỉ số đếm, không xem nội dung):

| Tài liệu | Đích | Cạnh vàng | Hai người cùng ghi / hợp |
|---|---|---|---|
| d01-t01 | 46 | 69 | 30 / 112 |
| d01-t02 | 37 | 36 | 18 / 84 |

Vàng gắn với canonical v1, tức chuỗi v3.

## Ba nhánh

| Nhánh | Mã | Nhãn vùng | Dùng để |
|---|---|---|---|
| **A — v3** | checkout sạch `2c93c5a` | bản nhãn hiện có (chunk v2) | mốc |
| **B — gộp** | checkout sạch `36b81ff` | bản nhãn hiện có | so với A: nghiệm thu đợt gộp |
| **C — gộp + 05a** | checkout sạch `36b81ff` | `label-roles` lại theo luật 05a | sản phẩm hiện tại; so với B: số của vé 05 |

- Luật 05a chỉ đổi vai trò ở `d01-t02`: 2 nhóm tiêu đề lặp, 10 mục đang khoá `de_cuong`. Đếm bằng script chỉ in số nguyên. Ở `d01-t01` nhánh C
  trùng nhánh B, không chạy.
- Cả ba nhánh dùng pass phụ ML mặc định. Không có quyết định người duyệt gộp (`--identity-review`, `--merge-review`).

## Cần làm

1. **Thứ tự chạy.** `roadmap` đi theo canonical mới nhất, nên:
   - A chạy trước, trên canonical v1;
   - rồi B: `a4 --gold tests/fixtures/a4/gold-blind.json --no-gold-for-doc --language vi`, rồi `roadmap`;
   - rồi C ở `d01-t02`: `label-roles`, `a4`, `roadmap`.

   Mỗi bước có chi đều dry-run trước. Cổng chất lượng chữ mà từ chối thì dừng và báo, không tự thêm cờ lý do.
2. **Ghim mã.** Mỗi nhánh chạy từ worktree sạch của đúng commit, script dừng nếu import nhầm mã (như cổng 19l). Ghi bảng nguồn gốc artifact.
3. **Script chấm, chỉ in allowlist.**
   - Chỉ in trường số hoặc bool: Q6, Q7, Q7b, P/R trực tiếp và bao đóng kèm số đếm; số đích trong dãy học; số đích cùng trạng thái dạy giữa hai
     nhánh; số cạnh vàng bị gộp làm một; số khái niệm vàng không quy được id; lời gọi, USD, giây.
   - Nhánh B và C chấm với vàng quy id qua bảng chuyển hướng (`--remap-gold-ids`, vé 17h). Nhánh A chấm thẳng, có áp `identity_map`.
   - Test phải có chuỗi bí mật giả cài trong trường lồng, và phải đỏ trên bản in ngây thơ.
   - Không dùng các script in tên khái niệm (`doc_lech.py`, `canh_sai.py`, `so_trang_thai.py`) trên hai cuốn này.

## Tiêu chí đặt trước

Chốt ngày 2026-10-17, trước khi chấm. **Không sửa sau khi thấy số.** Mốc là nhánh A trên chính hai cuốn. Phán đạt khi tiêu chí 1–3 đều đạt ở cả hai cuốn.

1. **Neo ở đích vàng:** số đích vàng trong dãy học ("được dạy" hoặc "không chắc") của B không thấp hơn A, từng cuốn. Ghi thêm số đích cùng trạng
   thái dạy giữa A và B.
2. **Gộp sai mà vàng phát hiện** (cạnh vàng có hai đầu bị gộp làm một): tổng hai cuốn, B không nhiều hơn A.
3. **E4:** B không kém A quá **0,15** ở bất kỳ chỉ số nào sau đây, từng cuốn:
   - Q6 (cao hơn là kém);
   - Q7, Q7b, P/R trực tiếp, P/R bao đóng (thấp hơn là kém).

   Căn cứ của ngưỡng:
   - dải xáo đầu vào của 19j rộng tới 0,17–0,18 ở Q7 và 0,14 ở R bao đóng;
   - đổi canonical gây lệch tới 0,06 (19l);
   - E4 một lượt nhiễu khoảng ±0,15.
4. **Khái niệm vàng không quy được id** sang canonical gộp: ghi số. Nếu bộ chấm từ chối một cuốn thì cuốn đó để riêng, theo quyết định đã chốt, và
   phán dựa trên cuốn còn lại.
5. **Chi phí và thời gian:** lời gọi, USD, phút/cuốn của từng nhánh, gồm cả phần trước A8. Đây là thông tin, không phải tiêu chí đạt/trượt.

**Nhánh C** chỉ báo số, so với B và A. Không có tiêu chí đạt/trượt riêng.

**Sau khi chấm:**
- Ghi mọi số vào báo cáo trước.
- Chỉ đọc nội dung chỗ lệch (mở mù hai cuốn) khi tiêu chí trượt, hoặc khi chủ dự án cho phép.
- Sau khi đọc, mọi sửa đổi dựa trên chỗ đã đọc không được đo lại trên T-01 như số giữ lại.

## Nghiệm thu

- [ ] Báo cáo `report/v4-T01b-<ngày>.md`, chỉ số liệu:
  - SHA mã của từng nhánh, bảng nguồn gốc artifact;
  - bảng A/B/C theo cuốn;
  - phán theo tiêu chí trên, kèm chi thật so với dự toán.
- [ ] Script chấm allowlist có test chuỗi bí mật giả, đã thấy đỏ trên bản ngây thơ.
- [ ] Kế hoạch v4 ghi kết luận của đợt gộp và việc tiếp theo.
