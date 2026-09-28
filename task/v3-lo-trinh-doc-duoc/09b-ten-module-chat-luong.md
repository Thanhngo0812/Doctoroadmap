# 09b — Tên module: phần phụ có nghĩa, không lặp tên nền; tên nền lấy từ cây mục đã sửa

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R7 (bổ sung 2026-09-28) · **Ai:** nhân viên · **Phụ thuộc:** 09 ·
**Chi phí mô hình:** hỏi lại các module vi phạm (≈ 0,01 USD cho kho phát triển)

**Trạng thái (2026-09-28):** đã triển khai, test và chạy lại sáu tài liệu trên A9 v10. Không còn tên module trùng trong cả sáu; doc-1 và doc-2 không có phần phụ lặp nguyên tên nền hay `(1/1)`. Vẫn còn tên nền chung như `Chapter 1`/`Chapter 9` ở doc-2 và tiêu đề dài do cây mục, ngoài phạm vi luật phần phụ của vé. [Báo cáo](../../report/ket-qua-v3-05b-09b-11b-vertex-2026-09-28.md).

## Vì sao (kiểm thử vé 09, 2026-09-28)
Tên không còn trùng, nhưng phần phụ hay lặp tên nền ("2.1 Ma trận — Ma trận", "5.2 Dạng toàn phương trên không gian R n — trên không gian
R n"), hay chỉ là mẩu tên ("2.1 Ma trận — thực", "Vector — space", "Matrix — multiplication"); có cả "Jordan basis — Jordan basis" và
"(1/1)". doc-2 có nhiều tên nền "Chapter n" vì cây mục cũ bị vỡ.

## Việc cần làm
- Luật kiểm phần phụ, không dùng danh sách từ:
  - không trùng và không là chuỗi con của tên nền (sau chuẩn hoá), tên nền cũng không là chuỗi con của nó;
  - nếu mọi từ chỉ lấy từ **một** tên khái niệm thì phải là trọn tên đó, không là mẩu của nó;
  - phải có ít nhất một chữ cái.
- Vi phạm → hỏi lại một lần kèm lý do. Vẫn sai → dùng trọn tên của một–hai khái niệm tiêu biểu của module (khái niệm đầu module và khái
  niệm có nhiều cạnh ra nhất trong module). Chỉ dùng "(k/n)" khi hết cách, và không bao giờ in "(1/1)".
- Tài liệu có đồ thị dựng trên version chunks cũ (doc-2): đường dẫn mục dùng để đặt tên lấy từ cây đã sửa, bằng đúng phép chuyển theo văn
  bản của vé 14b (chỉ để hiển thị; ID, vai trò, cạnh giữ nguyên).

## Tệp liên quan
`domain/module_titles.py` (`grounded_suffix`, `common_content_title`), `application/use_cases/name_modules.py`, `prompts/a10/module_title.txt`.

## Nghiệm thu
- Test từng luật kiểm (lặp tên nền, mẩu tên, không chữ cái, "(1/1)"), trên tiêu đề tổng hợp ở ít nhất hai ngôn ngữ ngoài vi/en.
- **Tôi kiểm:** đọc lại toàn bộ tên module doc-1, doc-2 và một tài liệu khác.

## Kiểm thử (Claude, 2026-09-28) — luật phần phụ **đạt**; mục tiêu tên doc-2 **chưa đạt** → vé [09c](09c-module-theo-cay-sua.md)

- **Đột biến trên luật phần phụ:**
  - Bắt được: tắt luật lặp tên nền, tắt luật mẩu tên, tắt phép chuyển cây → test đỏ.
  - **Lọt:** tắt luật "phải có chữ cái" → test vẫn xanh. Ca không chữ duy nhất trong test là "(1/1)", mà ca này đã bị luật căn cứ bác vì
    "1" không có trong tên nguồn. Cần một ca cô lập, như
    `grounded_suffix("3 · 4", ["Satz 3", "Satz 4"], "Kapitel", ["Satz 3", "Satz 4"])` phải sai.
  - Nhánh "(k/n)" chỉ chạy khi có ít nhất hai module anh em, nên đột biến "(1/1)" không đổi hành vi. Không phải lỗ hổng.
- Sáu tài liệu không còn tên trùng, không còn "(1/1)".
- **Đọc tên từng tài liệu:**
  - doc-1: tốt; còn 8 tên quá 12 từ.
  - nhap-mon-ml: được; 5 tên dài.
  - **doc-6:** "document> — Cơ sở dữ liệu", "document> — Hệ Quản Trị CSDL". Nút gốc `<document>` bị lấy làm tên nền (bước làm sạch bỏ dấu
    "<"). Lỗi có từ vé 09: kho `v3-title-label-evaluation` đã có tên "document>". Bảng kiểm R11 cũng không bắt được (ghi cho vé 02b).
  - **doc-2:**
    - 15/48 tên nền ở cấp chương ("Chapter 1/2/3/4/5/7/8/9" kèm phần phụ);
    - "6B" trơ mã;
    - "identities" là nhãn in đậm đầu đoạn bị nhận nhầm làm tiêu đề;
    - vài module lấy tên khái niệm đầu ("List of length one", "Upper bound on number of distinct eigenvalues").
- **Nguyên nhân gốc doc-2** (kiểm bằng `scripts/doc-lo-trinh/thu_module_cay_sua.py`; chia lại trên cây vỡ trùng module hiện tại):
  - Cây đã sửa mới chỉ được chuyển cho **tên**. **Ranh giới module** vẫn tính trên cây vỡ, nên module vắt qua 3C/3D, 5B/5C, 7C/7D….
  - Chia lại trên đường dẫn mục của cây đã sửa (dãy học, ID, cạnh giữ nguyên):
    - module nằm gọn trong một mục cấp 2: 33/48 → 43/53;
    - tên nền cấp chương: 15 → 11;
    - có thêm "3D Invertibility and Isomorphisms", "5C Upper-Triangular Matrices", "5D Diagonalizable Operators", "7D Isometries…",
      "9D Tensor Products".
- **Còn lại sau khi chia đúng cây:**
  - tiêu đề chỉ có mã ("Chapter 1": tên chương "Vector Spaces" là dòng đầu của chunk; "6B", "7C": tên chỉ có trong mục lục hoặc bị mất);
  - nhãn viết thường bị nhận làm tiêu đề ("identities", "conjugate symmetry");
  - **8A/8B/8C bị lớp nhãn của vé 14b gắn `de_cuong`.** Đây là mục chứa không có nội dung trực tiếp nên không chunk nào nhận sai vai trò,
    nhưng luật tên nền đòi `noi_dung` nên rơi về "Chapter 8".
