# 09 — Tên module theo nội dung

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R7 · **Ai:** nhân viên · **Phụ thuộc:** 03 · **Chi phí mô hình:** ≈ 0,05 USD / tài liệu

**Trạng thái:** chờ giao

## Việc cần làm
- Làm sạch tiêu đề (ký tự đầu dòng PDF "u ", "▪", "•"; khoảng trắng dính "MỞĐẦU"; không nhận câu văn > 12 từ làm tiêu đề).
- Tên module = tiêu đề mục `noi_dung` cụ thể nhất chung cho các khái niệm của module.
- Tên trùng với module khác hoặc không có: một lời gọi mô hình sinh phần phụ ngắn ("— Phép toán và lượng từ") từ **tên các khái niệm
  trong module**; mã kiểm mỗi từ nội dung của phần phụ có trong tên khái niệm hoặc tiêu đề mục; hỏng thì dùng "(phần k/n)".
- Stage hoặc bước riêng, có cache, qua `SpendGuard`.

## Tệp liên quan
`domain/sequence.py` (`build_sequence_roadmap`, `title_of`), use case mới cho đặt tên, prompt mới trong `prompts/a10/`.

## Nghiệm thu
- Test làm sạch tiêu đề; test kiểm từ của phần phụ (từ lạ bị từ chối); test không còn tên trùng.
- **Tôi kiểm:** bảng kiểm vé 02 — 0 tên trùng, 0 tên từ vùng ngoài `noi_dung` trên sáu tài liệu; đọc tên module doc-1, doc-2.
