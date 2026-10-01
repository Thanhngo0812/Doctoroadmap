# 09c — Module chia theo cây mục đã sửa; tên nền không lấy nút gốc, tiêu đề chỉ có mã hay nhãn đầu đoạn

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R7 (bổ sung 2026-09-28, lần 2) · **Ai:** nhân viên ·
**Phụ thuộc:** 09b · **Chi phí mô hình:** 0 cho chia module và tên nền; hỏi lại phần phụ cho module mới trùng tên (≈ 0,01 USD)

**Trạng thái:** đã triển khai và nghiệm thu trên sáu tài liệu (2026-09-29); [báo cáo](../../report/ket-qua-v3-09c-2026-09-29.md)

## Vì sao (kiểm thử vé 09b, 2026-09-28)
- doc-6 có hai module tên "document> — …". `common_content_title` đi từ gốc cây: nút `<document>` mang vai trò `noi_dung`, bước làm sạch
  bỏ dấu "<" nên nó thành tiêu đề hợp lệ. Hai khái niệm không chung mục nào sâu hơn thì tên nền là gốc.
- doc-2 có 15/48 tên nền ở cấp chương. 09b chuyển cây đã sửa cho **tên**, nhưng `BuildRoadmap` vẫn **chia module** trên đường dẫn mục của
  cây vỡ (version chunks cũ), nên module vắt qua hai mục (3C/3D, 5B/5C, 7C/7D…) và tổ tiên chung là chương.
  `scripts/doc-lo-trinh/thu_module_cay_sua.py` chia lại trên cây đã sửa, bằng đúng phép chia hiện hành: module nằm gọn trong một mục cấp 2
  tăng 33/48 → 43/53, tên nền cấp chương giảm 15 → 11.
- Phần còn lại là tiêu đề có sẵn trong cây nhưng không dùng được:
  - chỉ có mã: "Chapter 1", có tên chương "Vector Spaces" ở dòng đầu chunk; "6B", "7C", có tên trong mục lục hoặc đã mất;
  - nhãn in đậm đầu đoạn viết thường bị nhận làm tiêu đề: "identities", "conjugate symmetry", "positivity";
  - mục chứa 8A/8B/8C không có nội dung trực tiếp, lớp nhãn vé 14b gắn `de_cuong`. Không chunk nào nhận sai vai trò, nhưng luật tên nền
    đòi `noi_dung` nên rơi về "Chapter 8".

## Việc cần làm
- **Nút gốc không phải mục nội dung:** `common_content_title` không bao giờ trả section gốc (cấp 0). Không có mục chung sâu hơn thì dùng
  đường đặt tên theo khái niệm của R7 như hiện có.
- **Chia module trên cây đã sửa:**
  - Khi version chunks của đồ thị có `role_transfer`, `BuildRoadmap` tính `ancestry` từ cây đã sửa bằng `transfer_chunk_sections`. Đây là
    đường dẫn dùng cho `choose_levels`, `segment_modules` và `section_ids` của module; tính một lần, dùng chung với `NameModules`.
  - Chunk không chuyển được thì giữ đường dẫn cũ.
  - Chỉ đổi cách chia module: dãy học, ID, vai trò, cạnh giữ nguyên.
  - Ghi `title_sections_version` vào config của A10 (đổi khoá cache có chủ đích; A10 không tốn tiền).
- **Mục chứa:** section không có nội dung trực tiếp thì không bị loại khỏi tên nền vì vai trò của chính nó. Chunk con đều là nội dung
  dạy, vì mọi khái niệm của module được dạy ở `noi_dung`.
- **Tiêu đề chỉ có mã:** tiêu đề chỉ gồm tiền tố và số của họ chương (`chapter_members`/`_chapter_sequences`), hoặc chỉ gồm mã mục
  (`section_code`). Bổ sung từ bằng chứng của chính tài liệu, theo thứ tự:
  1. dòng mục lục có cùng mã, lấy phần chữ sau mã tới số trang. Mục lục là vùng trước chương đầu (`mo_dau`/`de_cuong`) có dạng "mã + chữ
     + số trang". Ở doc-2, mục "Contents" mang vai trò `mo_dau` và `is_toc` = False, nên không dựa vào cờ;
  2. dòng đầu của chunk đầu mục, nếu:
     - ngắn (≤ 12 từ theo cách tách của `clean_titles`);
     - không có `[formula]`/`[figure]`;
     - không mở đầu bằng chữ số (loại "7.34 definition: positive operator" là tiêu đề khối kết quả);
     - không phải một câu theo bộ tách câu Unicode đang dùng;
  3. không có thì giữ nguyên, ghi cờ `numbering_only_title`.

  Ước trên doc-2 (Claude, 2026-09-28):
  - bổ sung được 5/11: "Chapter 1/2/4/5/6" → "Vector Spaces", "Finite-Dimensional Vector Spaces", "Polynomials", "Eigenvalues and
    Eigenvectors", "Inner Product Spaces";
  - còn cờ 6: "Chapter 3/7/8/9", "6B", "7C". Các trang mục lục này bị mất khi parse; chấp nhận, không đoán.
- **Nhãn đầu đoạn:**
  - Chỉ áp cho chữ viết có hoa/thường. Nếu phần lớn tiêu đề cùng cấp trong tài liệu (≥ 90%) mở đầu bằng chữ hoa, tiêu đề mở đầu bằng chữ
    thường không được làm tên nền; lên mục cha.
  - Xét trên tiêu đề đã qua `clean_titles`. "Mở đầu" là chữ cái có hoa/thường đầu tiên (loại Unicode `Lu`/`Ll`), sau khi bỏ một ký hiệu
    liệt kê ở đầu: token gồm một chữ cái hoặc một dãy chữ số, theo sau đúng một dấu câu loại `Pe`/`Po` ("b)", "2.").
  - Đo trên cây hiện có (Claude, 2026-09-28):
    - doc-2 cấp 3: 112/119 mở đầu bằng chữ hoa (94%). Bảy nhãn bị loại: "identities", "from R 3 to R 2", "positivity", "definiteness",
      "additivity in first slot", "homogeneity in first slot", "conjugate symmetry".
    - doc-3 cấp 1: loại 3 tiêu đề slide là mẩu câu ("unstructured data has no intrinsic…", "applied to an old ML idea…",
      "predict/generate structured output…").
    - naive-bayes: loại 1 ("quyét dinh (play=yes/no)").
    - doc-1 (kể cả cấp 4 "b) Ma trận hàng, ma trận cột"…), doc-6, nhap-mon-ml: không loại tiêu đề nào.
  - Hai bản định nghĩa thô hơn đã thử và bỏ:
    - "từ đầu có ≥ 2 chữ cái" loại nhầm "1A 𝐑 𝑛 and 𝐂 𝑛" và "A fun multi-modal example";
    - "token đầu ≤ 2 ký tự kèm dấu câu" loại nhầm "OK, let's start at the beginning".
  - Đây là bằng chứng kiểu chữ trong chính tài liệu, không phải danh sách từ. Chữ viết không phân biệt hoa/thường không bị ảnh hưởng.
- **Test cô lập luật "phải có chữ cái"** của `grounded_suffix` (xem kiểm thử 09b).

## Tệp liên quan
`domain/module_titles.py`, `domain/sequence.py`, `application/use_cases/build_roadmap.py`, `application/use_cases/name_modules.py`,
`domain/document_structure.py` (họ đánh số), `domain/chunking.py` (`_toc_runs`).

## Nghiệm thu
- **Test (fixture ở ít nhất hai ngôn ngữ ngoài vi/en, một chữ viết không cách từ):**
  - tài liệu phẳng không bao giờ nhận tên nền là gốc;
  - cây vỡ gộp hai mục dưới một chương, cây sửa tách ra: module theo cây sửa và **dãy học không đổi**;
  - "Kapitel 3" được bổ sung từ mục lục "Kapitel 3 Lineare Abbildungen 51"; "第3章" được bổ sung từ dòng đầu "線形写像";
  - tiêu đề viết thường bất thường bị bỏ ở tài liệu chữ Latin, không ảnh hưởng tài liệu chữ Nhật;
  - mục chứa không có nội dung trực tiếp vẫn làm được tên nền;
  - luật chữ cái cô lập.
- **Dry-run:** sáu tài liệu trước và sau; chỉ A10 và tên module đổi, không stage A3–A9 nào chuyển "sẽ chạy".
- **Báo số:**
  - doc-2: module nằm gọn trong một mục cấp 2, số tên nền cấp chương, số tiêu đề chỉ có mã còn lại, số cờ;
  - tên module doc-6;
  - Q6/Q7/Q7b doc-1, doc-2 phải **giữ nguyên** (dãy học không đổi — bất biến kiểm được).
- **Tôi kiểm:** đọc toàn bộ tên module doc-1, doc-2, doc-6, nhap-mon-ml; bảng kiểm R11 (bản 02b nếu đã có).
