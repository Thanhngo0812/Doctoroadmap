# 03 — README quy ước, tài liệu và script

**What to build:** Người thêm prompt cho phase mới đọc một file là biết để đâu, đặt tên thế nào, và phải làm gì khi sửa.
Tài liệu vận hành và script trỏ đúng đường dẫn mới.

**Blocked by:** 01 — Thư mục theo phase và hàm nạp chung

**Status:** done — 2026-09-15

- [x] `src/doc2roadmap/application/prompts/README.md` ghi các quy ước:
  - **Bố cục:** mỗi phase một thư mục, mỗi khâu một file. Khâu nào dùng chung prompt thì trỏ về cùng một file, không
    chép bản sao. Tên file viết thường, nối bằng gạch ngang.
  - **Ngôn ngữ:** khung prompt tiếng Anh; dữ liệu và few-shot giữ ngôn ngữ của tài liệu.
  - **Những gì đi vào `prompt_hash`**, cho A3 và A4, đúng như ticket 00.
  - **Quy trình đổi prompt:** đổi prompt là đổi hành vi. Phải cập nhật hash vàng (ticket 02), ghi lại fixture hợp đồng,
    chạy lại, và chấm theo luật viết trước khi chạy. Không chỉnh prompt rồi chấm lại trên cùng bộ vàng.
  - **Biến thể thí nghiệm** để trong `scripts/<…>_prompts/`, không để trong thư mục sản phẩm.
  - **Nhận diện:** tên phiên bản (v1, v2.1, v3…) chỉ dùng trong tài liệu. Nhận diện chính thức là `prompt_hash`.
  - **Bảng tên cũ → tên mới** cho người đọc báo cáo và feedback cũ.
- [x] `README.md` gốc: đoạn nói về prompt A3 và `--few-shot` trỏ sang `prompts/a3/…`, và nhắc tới `prompts/README.md`.
- [x] `scripts/run_a4_arm.py`: sửa phần help của `--partition-prompt`, hiện nhắc `a4-merge.txt` và `a4-repair.txt`,
      sang `a4/partition.txt`.
- [x] Tìm trong `src/`, `scripts/`, `tests/`, `README.md` mọi chỗ còn nhắc tên file cũ và sửa. Không sửa báo cáo,
      feedback và ticket cũ: đó là hồ sơ, đã có bảng tên cũ → tên mới.

## Bằng chứng bàn giao

- README trong gói ghi đủ bố cục, ngôn ngữ, thành phần hash, quy trình đổi hành vi, nơi đặt biến thể thí nghiệm, nhận
  diện bằng hash và bảng ánh xạ toàn bộ tên cũ sang tên mới.
- README gốc trỏ đúng thư mục A3 mới và tài liệu quy ước; help của runner A4 chỉ còn nêu `prompts/a4/partition.txt`.
- Quét `src/`, `scripts/`, `tests/` và `README.md`: tên file sản phẩm cũ chỉ còn trong bảng ánh xạ bắt buộc. Những tên
  như `path/to/few-shot.txt` là ví dụ đường dẫn tùy ý của `--few-shot`, không phải tham chiếu tới file sản phẩm cũ.
