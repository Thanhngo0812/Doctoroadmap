# 09 — Tên module theo nội dung

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R7 · **Ai:** nhân viên · **Phụ thuộc:** 03 · **Chi phí mô hình:** ≈ 0,05 USD / tài liệu

**Trạng thái:** chờ giao

## Việc cần làm
- Làm sạch tiêu đề, không phụ thuộc ngôn ngữ *(sửa 2026-09-26 theo spec v3 R7)*:
  - bỏ ký tự đầu dòng theo loại Unicode (ký hiệu, vùng dùng riêng, dấu đầu dòng), và tiền tố một ký tự lặp ở đầu nhiều tiêu đề của
    cùng tài liệu (như "u " do font ký hiệu);
  - chữ dính ("MỞĐẦU") chỉ tách khi chính tài liệu có bằng chứng (cùng tiêu đề xuất hiện ở chỗ khác có khoảng trắng);
  - không nhận câu văn > 12 từ làm tiêu đề (với chữ viết không cách từ, đếm theo ký tự với ngưỡng riêng trong config).
- Tên module = tiêu đề mục `noi_dung` cụ thể nhất chung cho các khái niệm của module.
- Tên trùng với module khác hoặc không có: một lời gọi mô hình sinh phần phụ ngắn ("— Phép toán và lượng từ") từ **tên các khái niệm
  trong module**, viết bằng ngôn ngữ của tài liệu; mã kiểm mỗi từ nội dung của phần phụ có trong tên khái niệm hoặc tiêu đề mục (với
  chữ viết không cách từ: kiểm theo chuỗi con); hỏng thì dùng "(k/n)".
- Stage hoặc bước riêng, có cache, qua `SpendGuard`.

## Tệp liên quan
`domain/sequence.py` (`build_sequence_roadmap`, `title_of`), use case mới cho đặt tên, prompt mới trong `prompts/a10/`.

## Nghiệm thu
- Test làm sạch tiêu đề và kiểm từ của phần phụ (từ lạ bị từ chối) trên tiêu đề tổng hợp ở ít nhất hai ngôn ngữ ngoài vi/en (một chữ
  viết không cách từ); test không còn tên trùng.
- **Tôi kiểm:** bảng kiểm vé 02 — 0 tên trùng, 0 tên từ vùng ngoài `noi_dung` trên sáu tài liệu; đọc tên module doc-1, doc-2.
