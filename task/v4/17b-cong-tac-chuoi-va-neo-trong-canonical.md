# 17b — Công tắc chuỗi và neo trong stage canonical

**Nguồn chân lý:** [spec gộp khâu trước A8](../../doc/gop-khau-truoc-a8-spec.md), mục 1, 2, 4 và 6 (chi phí).
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (test bằng mô hình giả) · **Chặn bởi:** 17a · **Trạng thái:** đã cài và kiểm chứng (2026-10-16); xem [báo cáo cài đặt và kiểm chứng](../../report/v4-17-phan-tich-va-kiem-chung-2026-10-16.md)

## Vì sao

Đây là lát đầu của chuỗi gộp: stage canonical tự mang trạng thái dạy và câu neo, để vé 17c nối chuỗi đồ thị vào. Trong vé này, phần neo gọi riêng
**mỗi khái niệm một lời**. Cách này giữ đúng hợp đồng C8 và làm đối chứng cho việc gom lô ở vé 17d.

## Cần làm

**Công tắc chuỗi**
- Thêm tuỳ chọn cấu hình chọn chuỗi thượng nguồn, nhận `v3` hoặc `gop`. Mặc định là `v3`.
- Chuỗi `gop` được ghi vào config và manifest của canonical, nên nằm trong khoá cache. Chuỗi `v3` không thêm khoá nào vào config, để mọi canonical
  v3 đã có vẫn được tái dùng.
- Chuỗi `gop` đòi A4/A5 đầy đủ. Lệnh `a4` ở chế độ `--names-only` hay `--prepare` mà gặp chuỗi `gop` thì dừng với thông báo rõ.

**Phần neo trong stage canonical (chuỗi `gop`)**
- Chạy sau mô tả và kiểm mô tả của A5, bằng lõi của vé 17a, mỗi khái niệm một lời gọi.
- Vùng tìm câu ứng viên theo spec mục 4 (đã sửa 2026-10-16):
  - chunk nguồn của node;
  - chunk có bằng chứng A3;
  - chunk có tên hoặc alias khớp chính xác. Tính trực tiếp trên toàn văn bằng hàm khớp tên của mention map; không dùng kênh độ gần nghĩa và không
    dùng provenance;
  - chunk nhắc ký hiệu;
  - chunk có tiêu đề mang tên.
- Chỉ xét chunk có vai trò nội dung. Nhãn vai trò phải đọc theo đúng phiên bản chunk của A3.
- Node media và node không học được thì không qua phần neo.

**Ghi lên node**
- Ghi đúng các trường C8 đang ghi: `teaching_status`, `anchor`, `teaching_chunk_ids`, `teaching_order_index`, `teaching_conflict`, và
  `mentioned_in` khi có. Pass phụ ML và A10 đọc thẳng các trường này, nên dạng của chúng phải giữ như chuỗi v3.
- Thêm chunk chứa câu neo vào `defining_chunk_ids` theo luật chỉ thêm. Bản trước giữ ở trường nguồn, như provenance đang làm.
- Tính lại vị trí dạy sớm nhất.

**Payload và chi phí**
- Payload canonical có thêm:
  - nhật ký neo, nhật ký lời phán neo, nhật ký xác minh kiến thức nền, cùng dạng với chuỗi v3;
  - một khai báo "canonical đã có neo", để A8 đọc ở vé 17c.
- `cost_summary` của canonical tách theo phần: phán cụm, phán sửa, mô tả, kiểm mô tả, neo, xác minh kiến thức nền. Có thêm một tổng. Thời gian
  từng phần đo theo cơ chế đo stage hiện có.
- Cỡ lô của phần neo nằm trong config. Vé này chỉ có giá trị "một khái niệm"; vé 17d thêm giá trị "theo lô A5".

**Chốt chặn chi và dự toán (`a4` ở chuỗi `gop`)**
- Mọi lời gọi tốn tiền phải có `--allow-spend`, như các stage neo và danh tính của chuỗi v3.
- `--dry-run` liệt kê dự toán từng phần mà không gọi mô hình hay embedding. Phần nào chưa ước được trước khi chạy (vì phụ thuộc kết quả phần trước)
  thì ghi "chưa biết", giống dry-run của lệnh `roadmap`.

## Nghiệm thu

- [x] Test qua `execute` của stage canonical trên fixture tài liệu thật, với mô hình giả:
  - neo và trạng thái dạy được ghi đúng trường;
  - mã câu neo không có trong ứng viên thì bị bác;
  - câu trích nằm ngoài ngữ cảnh thì bị bác;
  - khái niệm không có ứng viên không sinh lời gọi nào;
  - `prior_knowledge` không được xác minh thì hạ xuống `uncertain`;
  - chunk neo được thêm vào `defining_chunk_ids`, không chunk cũ nào bị xoá.
- [x] Ứng viên không lấy từ kênh độ gần nghĩa hay provenance. Test có một chunk chỉ gần nghĩa, và chunk đó không thành ứng viên.
- [x] Canonical `v3` giữ nguyên băm config. Một canonical v3 có sẵn được tái dùng.
- [x] Đổi chuỗi hay đổi cỡ lô phần neo thì khoá cache đổi. Chạy lại cùng cấu hình thì tái dùng toàn bộ.
- [x] Ở chuỗi `gop`, thiếu `--allow-spend` thì chặn trước lời gọi đầu tiên. `--dry-run` không gọi mô hình hay embedding.
- [x] `--names-only` / `--prepare` với chuỗi `gop` thì dừng với thông báo rõ.
- [x] Mỗi luật chặn có ít nhất một test thấy nó trượt khi luật bị bỏ (AGENTS.md mục 5). Toàn bộ test qua.
