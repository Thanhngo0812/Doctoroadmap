# Thư viện prompt sản phẩm

## Bố cục và tên

- Mỗi phase có một thư mục, mỗi khâu có một file `.txt`.
- Nếu nhiều khâu dùng chung prompt, mọi khâu phải đọc cùng một file; không chép bản sao.
- Tên file viết thường và nối từ bằng dấu gạch ngang. Few-shot của A3 nằm trong `a3/few-shot/`.
- Biến thể thí nghiệm nằm tại `scripts/<tên-thí-nghiệm>_prompts/`, không đặt trong thư viện sản phẩm.

Khung chỉ dẫn viết bằng tiếng Anh. Dữ liệu đầu vào và few-shot giữ ngôn ngữ của tài liệu.

## Nhận diện và quy trình thay đổi

Tên v1, v2.1, v3 chỉ dùng để mô tả trong tài liệu. Nhận diện chính thức của prompt là `prompt_hash`:

- A3 băm system, section, glean, validation, few-shot, schema, model, tham số sinh và seed node types.
- A4 băm prompt của khâu, schema, model, tham số sinh; describe/check còn băm luật ngôn ngữ và phiên bản validator câu.

Đổi prompt là đổi hành vi. Khi đổi có chủ đích, phải cập nhật hash vàng, ghi lại fixture hợp đồng, chạy lại và chấm theo
luật viết trước khi chạy. Không chỉnh prompt rồi chấm lại trên cùng bộ vàng.

## Tên cũ và tên mới

| Tên cũ | Tên mới |
|---|---|
| `system.txt` | `a3/system.txt` |
| `section.txt` | `a3/section.txt` |
| `glean.txt` | `a3/glean.txt` |
| `validation.txt` | `a3/validation.txt` |
| `few-shot.txt` | `a3/few-shot/default.txt` |
| `few-shot-statistics.txt` | `a3/few-shot/statistics.txt` |
| `few-shot-technical-report.txt` | `a3/few-shot/technical-report.txt` |
| `a4-merge.txt`, `a4-repair.txt` | `a4/partition.txt` |
| `a4-describe.txt` | `a4/describe.txt` |
| `a4-check.txt` | `a4/check.txt` |
