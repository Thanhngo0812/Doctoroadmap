# 05 — Neo và vị trí chỉ từ vùng dạy

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R3 · **Ai:** nhân viên · **Phụ thuộc:** 03 · **Chi phí mô hình:** chạy lại neo ≈ 0,5 USD toàn kho phát triển

**Trạng thái:** chờ giao

## Việc cần làm
- Bước neo chỉ lấy câu ứng viên từ chunk `noi_dung`. Khái niệm chỉ có ứng viên ngoài `noi_dung` → `mentioned_only`, ghi vùng
  (`mentioned_in`: `de_cuong` | `mo_dau` | `bai_tap`).
- Vị trí dạy (A10 `place`) không bao giờ lấy chunk ngoài `noi_dung`; khái niệm không có neo lấy chunk `noi_dung` sớm nhất có nhắc tên.
- Đổi `candidate_rule` trong config để cache không tái dùng nhầm.

## Tệp liên quan
`domain/anchors.py`, `application/use_cases/anchor_concepts.py`, `application/use_cases/build_roadmap.py` (`place`).

## Nghiệm thu
- Test: khái niệm chỉ xuất hiện trong đề cương → `mentioned_only` với `mentioned_in="de_cuong"`; khái niệm có câu định nghĩa ở
  `noi_dung` và câu nhắc ở đề cương → neo ở `noi_dung`.
- **Tôi kiểm:** doc-1 không còn module có tên "ĐỀ CƯƠNG…"; "Đa thức", "Số phức" không còn định vị theo đề cương; nhap-mon-ml module
  đầu không còn là "MỞ ĐẦU" liệt kê phương pháp. Báo kèm Q6 doc-1/doc-2 để bắt hồi quy.

## Bổ sung theo nguyên tắc đa ngôn ngữ (Claude, 2026-09-26; spec v3 R16)

Làm cùng lượt chạy lại neo của vé này, để không phải chạy lại neo thêm lần nữa:
- Bỏ `PRIOR_SIGNALS` (danh sách cụm vi/en). Phán `prior_knowledge` qua thêm một lời gọi xác minh độc lập, câu hỏi đóng: câu trích có nói
  tường minh rằng người đọc phải biết trước khái niệm này không (cách làm như lượt xác minh R8b).
- Tách câu ứng viên (`anchors._SENTENCE`, hiện dùng `[.!?]` ASCII) bằng luật ranh giới câu Unicode của `UnicodeSentenceSplitter`.
- Nghiệm thu thêm: test tổng hợp tiếng Trung (câu kết bằng "。" được tách) và tiếng Pháp (`prior_knowledge` được xác minh không cần cụm
  từ); mô hình giả cho lượt xác minh.
