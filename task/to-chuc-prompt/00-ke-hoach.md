# 00 — Kế hoạch: tổ chức lại file prompt theo phase

**Quyết định của chủ dự án (2026-09-14):** sắp lại cách để prompt trong mã nguồn trước khi sang các phase sau (2b, A11,
tutor…), vì mỗi phase sẽ thêm prompt mới.

**Nơi làm:** nhánh `main`.

**Blocked by:** không còn. Ticket 15 của [`task/a4-quan-he-mo-2a/`](../a4-quan-he-mo-2a/) đã gộp nhánh vào `main`
(2026-09-14, commit `c418499`), nên nhân viên làm được ngay.

**Kết quả nhân viên:** tickets 01–04 hoàn tất ngày 2026-09-15; 299/299 test pass, 0 lời gọi mô hình.

**Review (Claude, 2026-09-15): nhận.** Kiểm độc lập khớp mọi con số: 7/7 hash vàng giống bản trước khi dời, 12/12 đột
biến bị bắt, kho chính dùng lại đủ bốn tài liệu, wheel đủ file. Chi tiết ở feedback F18, vòng 28. Đã commit theo lệnh
của chủ dự án.

Lưu ý: prompt phân hoạch trên `main` giờ là v3. `a4-merge.txt` và `a4-repair.txt` vẫn là hai bản sao giống hệt nhau,
đúng như hiện trạng mô tả dưới đây. Giá trị hash vàng ở ticket 02 lấy trên `main` hiện tại, trước khi dời file.

Lý do: nhánh `a4-quan-he-mo-2a` đang sửa đúng hai file `a4-merge.txt` và `a4-repair.txt`. Đổi tên hay gộp hai file này
trên `main` lúc đó sẽ gây xung đột khi gộp nhánh.

## Hiện trạng

- 11 file nằm phẳng trong `src/doc2roadmap/application/prompts/`. Prompt A4 có tiền tố `a4-`, prompt A3 thì không
  (`system.txt`, `section.txt`, `glean.txt`, `validation.txt`, ba file few-shot).
- Hai module nạp, mỗi cái một kiểu:
  - `application/extraction_prompt.py` (A3) có `_PROMPT_DIR` và `load_prompts(few_shot_path)`;
  - `application/canonical_prompt.py` (A4) có `canonical_prompts()` đọc `a4-{stage}.txt`.
- `a4-merge.txt` và `a4-repair.txt` là hai bản sao giống hệt. Lượt vá dùng lại prompt của lượt cụm (F69), nên ai sửa
  một file cũng phải nhớ sửa file kia.
- Biến thể thí nghiệm nằm riêng ở `scripts/a4_ab_prompts/`. Chỗ đó đúng, giữ nguyên.

## Bố cục mới

```text
src/doc2roadmap/application/prompts/
  README.md                  quy ước (ticket 03)
  a3/
    system.txt
    section.txt
    glean.txt
    validation.txt
    few-shot/
      default.txt            ← few-shot.txt
      statistics.txt         ← few-shot-statistics.txt
      technical-report.txt   ← few-shot-technical-report.txt
  a4/
    partition.txt            ← a4-merge.txt (lượt cụm và lượt vá cùng đọc file này)
    describe.txt             ← a4-describe.txt
    check.txt                ← a4-check.txt
```

Phase sau thêm thư mục của mình, ví dụ `2b/`. `templates/` (bảng HTML gán vàng) không phải prompt, nên không đụng tới.

## Bất biến: không hash nào được đổi

`prompt_hash` chỉ tính trên **nội dung**, không tính đường dẫn file:
- A3 (`extraction_prompt.prompt_hash`): system, section, glean, validation, few-shot, schema, model, tham số sinh, kiểu
  mồi;
- A4 (`CanonicalReasoning.prompt_hash`): văn bản của từng khâu, schema, model, tham số sinh.

Vì vậy nếu dời file mà giữ nguyên từng byte chữ thì:
- mọi cache quyết định còn dùng được;
- artifact canonical không đổi phiên bản;
- fixture hợp đồng không phải ghi lại.

Đợt này **không sửa chữ nào** trong prompt. Muốn sửa prompt thì làm ở một đợt khác, có luật chấm riêng.

## Chia việc

| Ticket | Việc | Ai |
|---|---|---|
| [01](01-thu-muc-theo-phase-va-ham-nap-chung.md) | Dời file vào thư mục theo phase; một hàm nạp chung; bỏ bản sao merge/vá | Nhân viên |
| [02](02-test-chot-hash-va-danh-muc-prompt.md) | Test hash vàng, test danh mục prompt, test lượt vá dùng chung file | Nhân viên |
| [03](03-readme-quy-uoc-tai-lieu-va-script.md) | README quy ước trong `prompts/`, cập nhật README gốc và script | Nhân viên |
| [04](04-nghiem-thu-khong-doi-hash.md) | Nghiệm thu: hash không đổi, kho chính dùng lại được, gói wheel đủ file | Nhân viên |

Sau ticket 04, Claude review như các vòng trước.

**Chi phí:** 0 lời gọi mô hình. Mọi bước nghiệm thu chạy khi chặn mạng.
