# 23 — Tên module chỉ có mã mục thì thêm tên khái niệm

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md) R7 (tên module có nghĩa), bảng kiểm R11 (`ten-nen-chi-co-ma`) ·
**Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** gần 0 (chỉ hỏi lại module bị đổi tên; tên tối đa 128 token)

**Trạng thái:** đã làm trước T10 theo giao việc 2026-10-03; [kết quả](../../report/v3-23-ten-module-chi-co-ma-2026-10-03.md). Chưa chạy tập giữ lại. **Claude nghiệm thu: đạt (2026-10-03).**

## Vì sao (Claude, 2026-10-03)
- doc-2 (`v3-r12-final-evaluation` v8) có 5/53 module mà tên chỉ là mã: "Chapter 3", "6B", "7C", "Chapter 7", "Chapter 8". Người học không
  biết "6B" là gì, trong khi bên trong là Orthonormal list, Orthonormal basis, Gram-Schmidt procedure…
- `prepare_module_titles` đã tìm phần tên còn thiếu ở mục lục đầu sách và ở dòng đầu của mục. Không tìm được thì chỉ gắn cờ
  `numbering_only_title` và **giữ nguyên mã làm tên**.
- Module trải nhiều mục lấy tên mục chung sâu nhất. Nếu đó là chương mà tên chương chỉ có mã thì ra "Chapter 7" (module này chứa Cholesky
  factorization, Singular value decomposition…).
- Năm tài liệu còn lại có 0 tên kiểu này. Lỗi gắn với kiểu tách tiêu đề của docling ("Chapter 3" và tên chương thành hai khối), nên sách
  khác cũng có thể gặp.

## Việc cần làm
- Khi tên nền của module chỉ có mã (mục nằm trong `numbering_flags`, hoặc tên khớp trọn `section_code`), đưa module vào nhóm cần đặt tên
  (`needs_model`) như module bị chia của vé 09d: giữ mã làm tiền tố, mô hình chọn 1–3 tên khái niệm **nguyên vẹn** nối sau
  ("6B — Orthonormal basis · Gram-Schmidt procedure").
- Không đổi module, dãy học hay cạnh. Chỉ đổi `title` của module có tên nền chỉ có mã. Module khác giữ nguyên tên (tái dùng như 09d).
- Đổi config hash của bước tên module.
- Không thêm danh sách từ của ngôn ngữ nào: nhận mã bằng `section_code` và họ đánh số của chính tài liệu, như hiện nay.

## Nghiệm thu
- **Test**, fixture ở hai ngôn ngữ ngoài vi/en: mục chỉ có mã, không có mục lục → tên gồm mã và ít nhất một tên khái niệm nguyên vẹn. Test
  phải đỏ trên mã hiện tại.
- **Chạy lại bước tên module** sáu tài liệu trên kho cuối, tái dùng tên cũ:
  - `kiem_doc_duoc.py`: `ten-nen-chi-co-ma` = 0 ở doc-2, các loại khác không tăng;
  - mọi module khác giữ nguyên tên;
  - báo chi (một con số).
- **Chạy lại** `kiem_tuong_duong_chuoi.py` với đích `module_titles` mới; tôi sinh lại bảng khoá.
- **Tôi kiểm:** đọc năm tên mới của doc-2.

## Kiểm thử của Claude (2026-10-03) — **đạt**
- **Test:** cả hai fixture (tiếng Đức "Kapitel 3", tiếng Nhật "第3章") đỏ trên mã trước sửa (`remaining_items` 0 thay vì 1), xanh sau sửa.
  Toàn bộ 827 test xanh trên `fce6c48`.
  - Test chỉ đi qua nhánh dự phòng: mô hình giả trả tên bịa, nên tên lấy theo bậc cạnh. Nhánh mô hình trả hợp lệ (cho phép 1 tên khái
    niệm) mới được thử bằng lượt chạy thật trên doc-2. Nên thêm một test cho nhánh này (mô hình trả đúng một tên khái niệm nguyên vẹn
    thì nhận; tên bịa thì loại). Không chặn khoá, vì test không đổi hành vi.
- **So v8 → v9 trên sáu tài liệu** (script riêng của tôi): chỉ đổi 5 tên module của doc-2. `sequence`, `requires_edges`, `nodes`,
  `open_edges`, `non_learnable_nodes`, `overview_groups` và mọi trường module trừ tên đều giữ nguyên.
- **Năm tên mới** đều đọc được và chỉ dùng tên khái niệm nguyên vẹn:
  - "6B — Orthonormal list · Orthonormal basis · Gram-Schmidt procedure", "7C — positive operator · positive square root", "Chapter 8 —
    Jordan form · Jordan basis": tốt;
  - "Chapter 3 — Fundamental theorem of linear maps · identity operator", "Chapter 7 — positive invertible operator · singular values":
    chấp nhận được. "Singular value decomposition" có lẽ tiêu biểu hơn "singular values", nhưng đó là lựa chọn của mô hình trong tập hợp lệ.
- **Bảng kiểm R11:** `ten-nen-chi-co-ma` doc-2 5 → 0; các loại khác không đổi ở cả sáu tài liệu.
- **Nhân viên đã đổi luật kiểm của tôi** (`kiem_doc_duoc.py`): trước đây cờ bật khi **phần tên nền** (trước " — ") chỉ có mã; nay chỉ
  bật khi **cả tên** chỉ có mã. Theo luật cũ, v9 vẫn ra 5 cờ, vì thiết kế của chính vé 23 giữ mã làm tiền tố.
  - Đây là lỗi đặc tả của tôi: tiêu chí "`ten-nen-chi-co-ma` = 0" không đạt được với dạng tên tôi đặt ra. Luật mới đúng mục tiêu đọc
    được: "6B — …" có nghĩa, "6B" thì không.
  - Lỗi parse (mục mất tên) vẫn còn dấu: 6 cờ `numbering_only_title` trong payload tên module của doc-2, dùng cho hướng v4 A1/A2.
  - **Quy trình:** sửa script đánh giá của tôi phải ghi rõ trong báo cáo. Báo cáo vé 23 không nhắc thay đổi này; tôi chỉ thấy khi đọc diff.
- **Kiểm tương đương** với đích v9: doc-6 và doc-1 đều 11/11 tầng tái dùng; trần token tên module 128.
- **Bảng khoá nháp:** `prompt_hash` tên module mới (`0c36cd69…`) khớp manifest v9 ở cả hai tài liệu; mọi stage khớp.
- **Chi:** sổ kho cuối thêm 7 lời gọi, 0,000727 USD. Có thêm 5 bản ghi giữ chỗ (0,0076 USD) từ lần chạy đầu bị chặn trước khi gọi mô hình.
