# 09d — Module không có tiêu đề mục chung: sinh tên từ tên các khái niệm, không lấy nguyên tên khái niệm đầu

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R7 · **Ai:** nhân viên · **Phụ thuộc:** 09c ·
**Chi phí mô hình:** một lời gọi mỗi module không có tiêu đề mục (sáu tài liệu phát triển: khoảng 10 lời gọi, < 0,01 USD)

**Trạng thái:** chờ giao

## Vì sao (kiểm thử vé 09c, 2026-10-01)
R7: "Tên = tiêu đề mục `noi_dung` cụ thể nhất chung cho module; nếu trùng với module khác **hoặc không có**, sinh tên ngắn bằng mô hình từ
tên các khái niệm trong module". Từ vé 09, mã làm khác: khi không có tiêu đề mục chung, `module["title"] = names[module["node_ids"][0]]`, tức
lấy nguyên tên khái niệm đầu. Với tài liệu dạng slide, mọi module đều rơi vào đường này. Sau 09c, ví dụ:
- doc-3: "Artificial Intelligence", "Intercept", "output layer";
- doc-6: "Dữ liệu", "Xây dựng" (module chứa Xây dựng, Hệ Quản Trị CSDL, SQL, Mức ngoài);
- naive-bayes: "Posterior probability";
- doc-2: "List of length one", "Basis of V⊗W".

Một khái niệm lẻ không nói module học gì.

## Việc cần làm
- Module có `title_source = "concept"` (không có tiêu đề mục chung, kể cả sau phép bổ sung của 09c) → một lời gọi sinh tên ngắn từ **tên
  các khái niệm trong module**, viết bằng ngôn ngữ của tài liệu.
- Kiểm bằng luật căn cứ hiện có: mỗi từ nội dung phải lấy từ tên khái niệm của module (`grounded_suffix` với nguồn là tên khái niệm).
  Thêm hai luật:
  - không trùng tên module khác;
  - không là nguyên tên của đúng một khái niệm, trừ khi module chỉ có một khái niệm.
- Sai thì hỏi lại một lần kèm lý do. Vẫn sai thì dùng trọn tên của hai khái niệm tiêu biểu (đầu module và có nhiều cạnh ra nhất), như
  fallback của 09b.
- Ghi `title_source = "model_from_concepts"`; checkpoint và cache như bước tên module hiện có.

## Tệp liên quan
`application/use_cases/name_modules.py`, `domain/module_titles.py`, `application/prompts/a10/module_title.txt` (hoặc prompt riêng).

## Nghiệm thu
- **Test (fixture ở ít nhất hai ngôn ngữ ngoài vi/en, một chữ viết không cách từ):**
  - module không có tiêu đề mục được hỏi mô hình;
  - tên chứa từ không có trong tên khái niệm bị bác;
  - tên chỉ là nguyên tên một khái niệm (module ≥ 2 khái niệm) bị bác;
  - fallback hai khái niệm tiêu biểu;
  - module có tiêu đề mục không bị hỏi.
- **Dry-run:** sáu tài liệu; chỉ bước tên module đổi.
- **Báo:** tên module trước/sau của doc-3, doc-6, naive-bayes và các module `concept` của doc-2.
- **Tôi kiểm:** đọc tên module của ba tài liệu slide; bảng kiểm R11.
