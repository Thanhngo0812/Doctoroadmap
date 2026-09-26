# 10b — Danh tính: xác minh quan hệ, đại diện được dạy, gỡ chu trình theo vị trí đại diện

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R8b · **Ai:** nhân viên · **Phụ thuộc:** 10 ·
**Chi phí mô hình:** lượt xác minh ≈ 0,02 USD (tập kiểm và ba tài liệu phát triển); lượt 1 danh tính v2 trên kho mặc định nếu
chưa có (≈ 0,28 USD; 0 nếu tái dùng được checkpoint của bản thử khi checkpoint_id khớp cấu hình)

**Trạng thái:** chờ giao. **Chặn vé 07:** lọc khái niệm chỉ-nhắc khỏi dãy học chỉ an toàn khi đại diện nhóm là khái niệm được dạy.

## Vì sao (kiểm thử vé 10, 2026-09-26)

1. Phán `same` cho cặp từ nguồn mới đúng **27/44 (61%)**; trong 32 gộp đã áp ở bản thử có **11 gộp sai**. Lỗi chính là trường hợp
   riêng/lớp con/thể hiện (Set ↔ Finite set; singular values ↔ positive singular values), bằng nhau nhờ định lý hay đặc trưng
   (null T′ ↔ (range T)⁰; Characterization of normal operators ↔ Normal operator), hai định lý khác nhau (Schur ↔ upper-triangular
   form exists if F = C), đối tượng ↔ ánh xạ (Matrix of a linear map ↔ ℳ). Luật hiện hành coi mọi `same` là gộp.
2. Đại diện được chọn theo vị trí sớm nhất bất kể trạng thái dạy. doc-6 giữ "CSDL" (`mentioned_only`, đề cương, vị trí 0) và bỏ
   "Cơ sở dữ liệu" (`taught`); đại diện cũng không nhận tên thành viên làm alias.
3. Gỡ chu trình sau gộp dùng `order_relation` tính theo vị trí của thành viên cũ. Ở doc-1, gộp tạo chu trình
   ĐLTT cực đại → Hạng của hệ véc tơ → Phụ thuộc tuyến tính → ĐLTT cực đại; hai cách gỡ có trọng số bằng nhau, hàm gỡ xoá cạnh đúng
   Phụ thuộc tuyến tính → ĐLTT cực đại (căn cứ trong định nghĩa) → Q6 doc-1 từ 1/39 lên 3/39.

## Việc cần làm

### A. Lượt xác minh quan hệ cho mọi phán `same` của mô hình
- Prompt mới `prompts/a10/identity_verify.txt`, đầu ra trong tập đóng `relation`:
  - `dong_nhat` — hai tên cho cùng một khái niệm: cùng định nghĩa, cùng tập đối tượng; chỉ khác cách gọi (đồng nghĩa, ký hiệu, viết
    tắt, số ít/số nhiều, cách viết, bản dịch) hoặc đổi tên biến tự do;
  - `truong_hop_rieng` — một bên là trường hợp riêng, lớp con hay thể hiện của bên kia (thêm điều kiện, cố định tham số, áp khái
    niệm chung lên một đối tượng cụ thể);
  - `bang_nhau_theo_menh_de` — hai bên bằng nhau hay tương đương nhờ một định lý, mệnh đề, tiêu chuẩn; hoặc một bên là đặc trưng
    (điều kiện tương đương) của bên kia;
  - `menh_de_khac` — hai kết quả khác nhau có nội dung gần nhau;
  - `doi_tuong_khac_loai` — một bên là đối tượng, bên kia là phép toán, ánh xạ hay cách dựng liên quan tới nó;
  - `khac`;
  kèm `reason`.
- **Xác minh độc lập:** lời gọi xác minh không thấy phán và lý do của lượt 1, chỉ thấy hai hồ sơ khái niệm (tên, alias, mô tả, câu neo).
- Chỉ `dong_nhat` giữ `same`; mọi lớp khác thành `different`. Log giữ `model_verdict` (lượt 1), `verify_relation`, `verify_reason`
  và `verdict` cuối. Quyết định người (`--identity-review`) vẫn thắng cả hai lượt.
- Prompt viết từ định nghĩa các lớp ở trên, **không** lấy ví dụ từ [tập kiểm](10b-tap-kiem-danh-tinh.json). Tối đa hai phiên bản
  prompt, báo kết quả cả hai.
- Lượt xác minh có checkpoint riêng; lượt 1 tái dùng checkpoint có sẵn, không gọi lại.

### B. Đại diện nhóm
- Đại diện là khái niệm `taught` có vị trí dạy sớm nhất trong nhóm; nhóm không có thành viên `taught` thì lấy sớm nhất như cũ.
- Tên và alias của các thành viên khác thành alias của đại diện (ghi nguồn `identity`), để người đọc và vé 11 thấy tên có nội dung
  (ví dụ nhóm "Tính chất 2" ↔ "Đổi chỗ hai hàng hoặc hai cột").

### C. Gỡ chu trình theo vị trí đại diện
- Trong `merge_and_break_cycles`: với mọi cạnh bị đổi đầu mút do gộp, tính lại `order_relation` từ vị trí của hai đầu mới (cùng
  bảng `position` dùng để chọn đại diện): bằng nhau → "cùng chunk", nguồn trước đích → "thuận", còn lại → "ngược"; lưu
  `order_relation_before_merge`. Cạnh không bị đổi đầu mút giữ giá trị A8. Sau đó mới gọi `_feedback_edges` như cũ.
- Cách làm mẫu và số đo: `scripts/doc-lo-trinh/thu_go_chu_trinh_sau_gop.py`.

### D. Cấu hình
`algorithm_id` → `a10-identity-v3`; config ghi hash prompt xác minh, tập quan hệ, luật đại diện, luật tính lại thứ tự.

## Tệp liên quan
`domain/identity.py` (`identity_map`, `merge_and_break_cycles`), `application/use_cases/judge_identity.py`, `prompts/a10/`.

## Nghiệm thu (đặt trước khi chạy tốn tiền)

**Test** (phải thấy đỏ trên mã hiện tại):
- B: nhóm {CSDL `mentioned_only` vị trí 1, Cơ sở dữ liệu `taught` vị trí 20} → đại diện "Cơ sở dữ liệu", alias có "CSDL"; nhóm
  không có ai `taught` → lấy thành viên sớm nhất.
- C: đồ thị nhỏ tái hiện chu trình doc-1: P (vị trí 131) → M (139), cạnh nhập từ M′ (163); M → R (160), nhập từ M′; R → P, nhập
  từ P′ (170); trọng số bằng nhau trước khi tính lại. Cạnh bị gỡ phải là R → P; P → M được giữ.
- A (mô hình giả): lượt 1 `same` và xác minh `truong_hop_rieng` → không gộp; xác minh `dong_nhat` → gộp; quyết định người
  "Đồng ý gộp" thắng lời bác của xác minh; phán `different` không gọi xác minh; payload xác minh không chứa verdict/reason lượt 1.

**Không tốn tiền:** B + C trên bản đồ danh tính của bản thử → doc-1 Q6 ≤ 1/39, doc-2 ≤ 3/61 (thí nghiệm của tôi: 1/39 và 3/61).

**Tốn tiền** (≈ 0,02 USD, sau `--dry-run`):
- Chạy lượt xác minh trên toàn bộ tập kiểm, không phụ thuộc lượt 1. Ngưỡng đặt trước:
  - trong các cặp không thuộc vùng xám: bác ≥ 9/10 cặp nhãn `different`, giữ ≥ 23/26 cặp nhãn `same`;
  - với 9 cặp T5 (nhãn người): khớp ≥ 8/9;
  - 8 cặp vùng xám báo riêng, không làm cổng.
- Báo từng cặp lệch nhãn. Trượt ngưỡng thì báo và dừng; không sửa prompt quá hai phiên bản.
- Rồi chạy luồng mặc định doc-1/doc-2/doc-6 (chạy `--dry-run` trước), bảng kiểm R11 trước/sau, Q6/Q7/Q7b. Tôi đọc lại mọi gộp.

## Sau vé này
Sinh bảng duyệt người cho các gộp chạm vàng còn lại sau xác minh (T18, dùng `scripts/duyet-danh-tinh/tao_bang.py`). Không tự duyệt.

## Không làm
Không thêm nguồn đề cử; không đổi lượt 1; không "hoàn tất nhóm mở". Với nhãn của tôi, xác minh đúng tự tách ba nhóm mở doc-2 thành
các nhóm đã kiểm đủ: {Matrix, Matrix of a linear map, Matrix of T}, {ℳ, Isomorphism between L(V, W) and F^m,n},
{Alternating multilinear form, Alternating m-linear form}, {Alternating n-linear forms, Alternating n-linear form}.

## Căn cứ
- Halpin, Hayes, McCusker, McGuinness, Thompson (ISWC 2010), *When owl:sameAs isn't the Same*: liên kết danh tính thường bị dùng
  cho quan hệ yếu hơn (giống nhau, liên quan); cần tách danh tính khỏi các quan hệ đó. Đó đúng là lớp lỗi ở đây.
- Khớp ontology tách tương đương (equivalence) khỏi bao hàm (subsumption); tập quan hệ ở mục A đi theo cách phân loại đó.
- Dhuliawala và cộng sự (Findings of ACL 2024), *Chain-of-Verification*: trả lời câu hỏi kiểm chứng độc lập với bản nháp giúp giảm
  lỗi. Vì vậy lượt xác minh không được thấy phán của lượt 1.
- Peeters, Steiner, Bizer (EDBT 2025), *Entity Matching using Large Language Models*: kết quả nhạy với cách đặt nhiệm vụ, và tri
  thức so khớp tường minh giúp ích. Vì vậy định nghĩa các lớp quan hệ được viết vào prompt.
- Raad và cộng sự (ISWC 2018): liên kết danh tính sai lộ ra qua cấu trúc mạng. Chu trình do gộp sinh ra là tín hiệu kiểu đó; ở đây
  dùng nó để chọn đúng cạnh cần gỡ.
- Thứ tự trình bày của sách là tín hiệu về chiều tiên quyết (Wang và cộng sự, CIKM 2016; A8 `order_relation`; dãy học neo sách
  của A10), nên sau khi gộp phải tính theo vị trí của đại diện.
