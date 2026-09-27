# 05 — Neo và vị trí chỉ từ vùng dạy

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R3 · **Ai:** nhân viên · **Phụ thuộc:** 03 · **Chi phí mô hình:** chạy lại neo ≈ 0,5 USD toàn kho phát triển

**Trạng thái:** **đạt về mã** — Claude kiểm thử 2026-09-27 (mục cuối); kết quả doc-2 chạy lại sau vé [14b](14b-nhan-vai-tro-chia-lo.md). [Kết quả nhân viên](../../report/v3-05-14-16-ket-qua-2026-09-27.md).

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

## Kiểm thử (Claude, 2026-09-27) — đạt về mã; kết quả doc-2 chạy lại sau vé 14b

- **Mã:** câu ứng viên chỉ lấy từ chunk `noi_dung` (lọc trong `candidate_sentences`); khi A6 không đưa ứng viên thì quét tên chính xác,
  cũng chỉ trên chunk `noi_dung`; A10 định vị chỉ bằng chunk `noi_dung`; `prior_knowledge` qua lời gọi xác minh đóng, không thấy lý do
  của lượt neo; tách câu Unicode; tái dùng phán cũ theo hash đầu vào.
- **Test:** toàn bộ khoảng 714 test xanh (kể cả tích hợp). Đột biến 4/4 bị bắt: bỏ lọc vùng dạy; định vị lấy chunk ngoài vùng dạy;
  giữ `prior_knowledge` không cần xác minh; lộ lý do lượt neo cho lượt xác minh.
- **Đọc doc-1:** chương 1 chỉ có Tập hợp, Quan hệ và ánh xạ, Nhóm-Vành-Trường. "Số phức" chỉ có trong đề cương; "Đa thức" chỉ được dùng
  (P_n[x], đa thức đặc trưng), không được định nghĩa. Vì vậy `mentioned_only` là **đúng** — lỗi L1 đã được sửa. Q6 doc-1 1/39 → 3/39:
  hai lỗi mới chính là hai nút này đang nằm tạm cuối dãy học; vé 07 sẽ đưa nút chỉ-nhắc ra khỏi dãy và bộ chấm tính chúng là "thiếu đầu".
  Không phải hồi quy thật. Module đầu doc-1 là "1.1 Tập hợp"; nhap-mon-ml mở bằng mục 1.1.
- **Bảng kiểm** (so mặc định): tên module lấy từ vùng không dạy doc-1 4 → 0, nhap-mon-ml 4 → 0, doc-6 1 → 0; module 1 ngoài bài giảng
  doc-2, doc-6, nhap-mon-ml 1 → 0.
- **doc-2 bị hỏng bởi lỗi vai trò của vé 14:** 42 khái niệm trước được dạy nay thành chỉ-nhắc/không chắc; 17 trong số đó vì chunk neo
  cũ nằm trong mục bị mô hình gắn nhầm `de_cuong` (Nilpotent operator, Polar decomposition, Geometric multiplicity, Minimization problem,
  Polynomial applied to an operator…). Chỉ-nhắc trong dãy học doc-2 98 → 131. Chạy lại neo doc-2 sau vé 14b.
- Các tài liệu khác: số khái niệm được dạy doc-1 205 (không mất), doc-3 25 → 23, doc-6 12 → 11, nhap-mon-ml và naive-bayes giữ nguyên.
- **Ghi thêm:** `candidate_sentences` vẫn xếp hạng câu theo `DEFAULT_DEFINITION_SIGNALS` (danh sách vi/en; chỉ xếp hạng, không lọc) —
  đã ghi vào R16, làm cùng vé 12. Kết quả đang ở kho thử; khi xuất bản vào kho mặc định cần tái dùng checkpoint của kho thử (dry-run kho
  mặc định báo neo "sẽ chạy": doc-1 214, doc-6 23 khái niệm).
