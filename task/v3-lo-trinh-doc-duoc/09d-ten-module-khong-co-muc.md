# 09d — Module không có tiêu đề mục chung: sinh tên từ tên các khái niệm, không lấy nguyên tên khái niệm đầu

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R7 · **Ai:** nhân viên · **Phụ thuộc:** 09c ·
**Chi phí mô hình:** một lời gọi mỗi module không có tiêu đề mục (sáu tài liệu phát triển: khoảng 10 lời gọi, < 0,01 USD)

**Trạng thái:** đã triển khai và chạy thử sáu tài liệu; chờ sếp đọc tên module trong kho đánh giá, chưa commit.

**Kết quả:** [báo cáo 09d](../../report/ket-qua-v3-09d-2026-10-01.md), artifact cuối ở
`artifacts/v3-09d-evaluation/graph/*/v2`.

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

## Kiểm thử (Claude, 2026-10-01) — cơ chế đạt; tên sinh ra **chưa đạt**, sửa cách sinh

**Cơ chế:**
- Test 24/24, có tiếng Tây Ban Nha và chữ Thái; ba test mới đỏ trên mã cũ.
- Toàn bộ test xanh; chi 0,0023 USD.
- Đột biến bắt được: cho tên là nguyên một khái niệm, bỏ hỏi module khái niệm, cho dòng đầu mở bằng chữ số (09c). **Lọt:** luật "không trùng
  tên module khác" chưa có test cô lập.
- Bảng kiểm R11 mới: `ten-theo-khai-niem-dau` về 0 ở bốn tài liệu.

**Đọc tên:**
- Luật căn cứ cấm mọi từ không có trong tên khái niệm, kể cả từ nối. Vì vậy mô hình **ghép liền các mẩu tên**, đọc không được:
  - "Basis bilinear m-linear Inner product";
  - "Neural Networks Dense Smart representations";
  - "Naive Bayes Dữ liệu liên tục Laplace Smoothing", trong đó "Naive Bayes" còn là mẩu tên chứ không phải một khái niệm;
  - "Artificial Intelligence Machine Learning Deep Learning".
- Tên rơi về dạng nối "Dữ liệu · Cơ sở dữ liệu", "Bernoulli Naive Bayes · Phân phối Gaussian" lại dễ đọc hơn.

**Sửa:**
- Với module không có tiêu đề mục, mô hình **chọn 2–3 tên khái niệm nguyên vẹn** trong danh sách của module: tên đại diện nội dung, không chỉ
  khái niệm đầu.
- Mã kiểm bằng khớp chính xác với danh sách, rồi nối bằng " · " theo thứ tự trong module. Module một khái niệm dùng tên khái niệm đó.
- Giữ fallback và luật không trùng tên module khác; thêm test cô lập cho luật này.
- Fixture đa ngôn ngữ như hiện có. Chi phí như cũ (< 0,01 USD).
