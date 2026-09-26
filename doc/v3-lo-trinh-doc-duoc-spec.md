# Spec v3 — Lộ trình chuẩn chỉ và đọc được

**Ngày:** 2026-09-26 · **Chủ dự án duyệt hướng:** tăng tốc, tôi tự đọc lộ trình để phán; được đổi cả các pha A trước.
**Căn cứ:** [báo cáo đánh giá 2026-09-26](../report/danh-gia-lo-trinh-2026-09-26.md) (L1–L8). **Vé:** `task/v3-lo-trinh-doc-duoc/`.
**Quy trình:** tôi viết spec và vé → chủ dự án giao nhân viên cài đặt → tôi kiểm thử theo vé và nghiên cứu tiếp.

## Mục tiêu

Một người học mở lộ trình phải thấy: mỗi module là một buổi học có tên nói đúng nội dung; thứ tự theo sách trừ chỗ sách buộc phải
đảo; chỉ những gì tài liệu thật sự dạy mới là mục bài học; mỗi khái niệm chỉ ghi vài tiên quyết trực tiếp đúng nghĩa; phần đề cương,
bài tập, lời nói đầu không trở thành bài học.

## Nghiệm thu

Chủ dự án bỏ yêu cầu một con số chuẩn cho mọi quyết định. Mỗi vé nghiệm thu bằng hai lớp:
1. **Test tự động** cho bất biến của vé (nhân viên viết, tôi review; test phải được thấy đỏ trước).
2. **Bảng kiểm đọc được** (R11) chạy trên doc-1, doc-2, doc-6, nhap-mon-ml, doc-3, naive-bayes, cộng **tôi đọc lộ trình** trước và
   sau, ghi phán xét vào vé. Không đọc tập giữ lại (xstk, doc-4) để chỉnh luồng.
Các số đo cũ (Q6, Q7, Q7b…) vẫn báo kèm để phát hiện hồi quy, không làm cổng.

## Quyết định

### R1 — Vùng văn bản có vai trò *(A2; sửa L1, L3, L4)*
Mỗi section mang `role` ∈ `noi_dung` · `bai_tap` · `de_cuong` · `mo_dau` · `hanh_chinh`.
- `bai_tap`: tiêu đề "Bài tập", "Câu hỏi ôn tập", "Đề số", "Exercises …", "Problems", "Exercise set"; vùng kéo tới tiêu đề cùng cấp
  hoặc cao hơn kế tiếp.
- `de_cuong`: "Nội dung môn học", "Đề cương", "Mục lục", "Contents", trang mục lục đã phát hiện (`_toc_runs`), slide "Nội dung"
  lặp lại giữa bài.
- `mo_dau`: phần trước chương đầu tiên có số — "Lời nói đầu", "Preface", "Foreword", "About the author", "Major improvements…".
- `hanh_chinh`: thang điểm, lịch, thông tin giảng viên (từ khoá có danh sách, kiểm tra được).
- `cuoi_sach` *(bổ sung 2026-09-26 sau kiểm thử vé 03, làm ở vé 04)*: "Photo Credits", "Index", "Symbol Index", "References",
  "Bibliography", "Tài liệu tham khảo". Không phải nơi dạy; bảng chỉ mục chứa gần hết tên khái niệm, nên để nó thành `noi_dung` sẽ
  làm bẩn bước neo.
Luật bằng mẫu tiêu đề và vị trí (không gọi mô hình), danh sách mẫu nằm trong mã và có test từng mẫu. *Lý do:* Wang và cộng sự 2016
dùng cấu trúc sách làm tín hiệu — nhưng chỉ khi vùng đúng; mọi lỗi L1 đến từ việc coi đề cương/bài tập là nơi dạy.

### R2 — Nhận cấu trúc mục kiểu sách toán *(A2; sửa L4)*
Tiêu đề mục dạng số+chữ ("3C Matrices", "Section 3C") là cấp mục; mục đánh số kết quả ("3.36 definition: …", "Định lý 2.1.",
"Ví dụ 3.") là **khối**, không phải tiêu đề mục; tiêu đề `bai_tap` đóng lại khi gặp tiêu đề mục kế tiếp. Tự nhận, không cần cờ
theo tài liệu (khác `--heading-scheme vn-textbook`, vốn giữ nguyên).

### R3 — Neo và vị trí chỉ lấy từ vùng `noi_dung` *(A9' — neo; sửa L1, L2)*
Câu ứng viên của bước neo chỉ lấy từ chunk `noi_dung`; khái niệm chỉ xuất hiện ở `de_cuong`/`mo_dau`/`bai_tap` nhận trạng thái
`mentioned_only` (ghi rõ vùng). Vị trí dạy không bao giờ rơi về chunk ngoài `noi_dung`.

### R4 — Cạnh không lấy căn cứ từ đề cương hay lời nói đầu *(A9 — luật kiểm; sửa L1)*
Cạnh `requires` mà **mọi** chunk căn cứ thuộc `de_cuong` hoặc `mo_dau` bị loại ở A9 (luật thuần, áp được lên đồ thị đã có, không
chạy lại A8). Cạnh chỉ có căn cứ ở `bai_tap` bị hạ thành cạnh mềm (không ràng buộc dãy học). *Lý do:* thứ tự liệt kê trong đề cương
không phải phụ thuộc (doc-6: chuỗi 7 cạnh giả).

### R5 — Dãy học chỉ gồm khái niệm được dạy *(A10; sửa L2)*
Dãy học và module chỉ chứa `taught` và `uncertain`. `mentioned_only` và `unchecked` rời dãy học: cạnh qua chúng được co lại như
nút bị loại (`bypass_excluded`), nên chúng không kéo được khái niệm được dạy; chúng hiện ở cuối module nơi được nhắc đầu tiên
trong vùng `noi_dung` dưới dạng "Nhắc tới (học ở phần khác / ngoài tài liệu)", hoặc ở mục "Tổng quan" nếu chỉ có trong đề cương.
*Lý do:* lý thuyết không gian tri thức chỉ xếp đường học trên các mục thuộc miền học; Reigeluth: tổng quan là tổng quan, không phải bài.

### R6 — Hiển thị tiên quyết rút gọn và phụ thuộc cấp module *(A10 hiển thị, roadmap-target; sửa L5 phần hiển thị)*
- Dòng "cần:" chỉ hiện cạnh của **rút gọn bắc cầu** (sơ đồ Hasse), tối đa 3, phần còn lại "và N khái niệm khác". Đồ thị đầy đủ
  giữ nguyên cho tính toán.
- **Phụ thuộc cấp module:** module M cần module N khi có cạnh từ khái niệm của N tới khái niệm của M; hiện "Học trước: module …".
- `roadmap-target` trả **các module cần học** (đóng theo phụ thuộc module) thay vì danh sách khái niệm rời.
*Lý do:* sơ đồ Hasse là cách trình bày chuẩn của quan hệ thứ tự (KST; Aho–Garey–Ullman 1972); cấp module bền với lỗi từng cạnh.

### R7 — Tên module theo nội dung và không trùng *(A10/A11; sửa L3)*
- Làm sạch tiêu đề: bỏ ký tự đầu dòng PDF ("u ", "▪", "•"), chuẩn khoảng trắng ("MỞĐẦU" → "MỞ ĐẦU" khi nhận được), không nhận câu
  văn dài làm tiêu đề.
- Tên = tiêu đề mục `noi_dung` cụ thể nhất chung cho module; nếu trùng với module khác hoặc không có, sinh tên ngắn bằng mô hình từ
  **tên các khái niệm trong module** (mỗi từ nội dung của tên phải lấy từ tên khái niệm hoặc tiêu đề mục — kiểm bằng mã), dạng
  "1.1 Tập hợp — Phép toán và lượng từ". Một lời gọi mỗi module trùng, ≈ vài chục lời gọi mỗi tài liệu.
*Lý do:* nguyên tắc tín hiệu (hai phân tích gộp) — tiêu đề có nghĩa giúp hiểu, nhất là người ít kiến thức nền.

### R8 — Danh tính mở rộng *(A9'' — danh tính; sửa L6)*
Thêm nguồn ứng viên: (a) chuẩn hoá tên như bước neo (NFKC, bỏ dấu LaTeX, gộp gạch nối); (b) viết tắt ↔ tên đầy đủ (chữ đầu các
từ: CSDL ↔ Cơ sở dữ liệu); (c) tên có ký hiệu ↔ tên chữ (Im f ↔ Ảnh; Ker ↔ Nhân) qua **độ tương tự mô tả + câu neo** (embedding
đã có, top-k nhỏ); (d) tiền tố chung chung thêm "Hệ ", "Phép ". Phán và luật gộp giữ nguyên (nhóm kiểm đủ; người duyệt gộp chạm vàng).

### R8b — Danh tính là cùng ngoại diên; đại diện được dạy; gỡ chu trình theo vị trí đại diện *(A9''; bổ sung 2026-09-26 sau kiểm thử vé 10)*
Kiểm thử vé 10: phán `same` cho cặp từ nguồn mới chỉ đúng 27/44; lỗi là trường hợp riêng, bằng nhau nhờ định lý, hai mệnh đề khác
nhau, đối tượng với ánh xạ. Quyết định:
- **Tiêu chí danh tính:** hai nút là một khi và chỉ khi cùng ngoại diên (cùng định nghĩa, cùng tập đối tượng), chỉ khác cách gọi
  (đồng nghĩa, ký hiệu, viết tắt, số ít/số nhiều, cách viết, bản dịch, đổi tên biến tự do). Trường hợp riêng/lớp con/thể hiện, bằng
  nhau nhờ định lý hay đặc trưng, hai mệnh đề khác nhau, đối tượng với phép dựng — đều **không** gộp.
- **Lượt xác minh:** mọi phán `same` qua thêm một lời gọi độc lập (không thấy phán lượt 1), phân loại quan hệ vào tập đóng; chỉ
  `dong_nhat` được gộp. Quyết định người vẫn thắng.
- **Đại diện** là thành viên `taught` được dạy sớm nhất (không có ai `taught` thì lấy thành viên sớm nhất); tên thành viên khác thành
  alias của đại diện.
- **Gỡ chu trình sau gộp:** cạnh bị đổi đầu mút được tính lại `order_relation` theo vị trí của đại diện trước khi gỡ.
*Lý do:* sameAs bị dùng lẫn cho quan hệ yếu hơn (Halpin và cộng sự, 2010); kiểm chứng độc lập giảm lỗi (Chain-of-Verification, 2024);
thứ tự sách là tín hiệu chiều tiên quyết nên phải đo theo vị trí thật của nút sau gộp. Vé: [10b](../task/v3-lo-trinh-doc-duoc/10b-danh-tinh-xac-minh.md).

### R9 — Tên khái niệm có nội dung *(sau A5; sửa L7)*
Tên chỉ là nhãn đánh số ("Tính chất 1", "Định lý 4", "Hệ quả 2") hoặc từ chung ("Definition", "Theorem") không được làm tên hiển
thị: từ chung bị loại khỏi khái niệm; nhãn đánh số được đổi thành tên nội dung ngắn sinh từ câu neo (kiểm câu trích), nhãn cũ giữ
làm alias. Không đổi `node_id` — bộ vàng không bị ảnh hưởng.

### R10 — Chạy thử có dự toán *(CLI; bài học sự cố 2026-09-26)*
`roadmap --dry-run`: liệt kê **mọi** stage sẽ gọi mô hình (không chỉ stage đầu), kèm số lời gọi ước và USD ước; không gọi mô hình.

### R11 — Bảng kiểm đọc được *(công cụ kiểm thử của tôi)*
Script kiểm tự động trên artifact `stages`: module 1 không lấy từ vùng ngoài `noi_dung`; không tên module trùng; không tên chứa mẫu
vùng ngoài `noi_dung`; không `mentioned_only` trong dãy học; dòng "cần:" ≤ 3; không khái niệm tên nhãn đánh số/từ chung; không mục
nào của một section `noi_dung` bị tách thành hai module cách nhau quá một chương. Kèm phán xét đọc của tôi.

### R12 — Cạnh theo định nghĩa ở A8 *(A8; sửa gốc L5 — việc đắt, sau R1–R9)*
Dời neo và danh tính lên trước A8 (W17 cũ). Căn cứ của cạnh "cần để hiểu" là **đoạn định nghĩa (câu neo) của đích**; cạnh chỉ có
căn cứ ở ví dụ, bài tập hay phương pháp giải được gắn loại `cong_cu` (nên biết trước khi làm bài), không ràng buộc hiểu định nghĩa.
*Lý do:* RefD (tiên quyết bất đối xứng theo tham chiếu trong định nghĩa); T1/T11: lỗi chính là thừa ràng buộc. Chi phí: chạy lại A8
mỗi tài liệu (≈ 1–7 USD), cần chủ dự án duyệt trước khi chạy.

### R13 — Trích mệnh đề có tên ở A3 *(A3; sửa L8 — sau vé 07, theo quyết định chủ dự án)*
A3 trích định lý/mệnh đề/công thức/phương pháp có tên thành nút `ket_qua` với tên nội dung. Đổi danh sách khái niệm → cần kế hoạch
ánh xạ bộ vàng (concept_hash) trước khi làm.

## Thứ tự

R10 và R11 trước (an toàn chi tiêu, công cụ kiểm) → R1, R2 (vai trò vùng, cấu trúc) → R3, R4, R5 (dùng vai trò) → R6, R7 (hiển thị,
tên) → R8, R9 → R12 (đắt) → R13 (sau vé 07). R8b phải xong trước R5, vì lọc khái niệm chỉ-nhắc cần đại diện nhóm là khái
niệm được dạy. Vé 07 (tập giữ lại) nên chạy **sau** R1–R9 để khoá cấu hình một lần trên luồng đã sửa:
đề nghị hoãn duyệt T10 tới khi các vé đó xong; T13 (liệt kê mù) làm được bất cứ lúc nào.

## Không đổi

Luật neo C8 v3 hiện hành ngoài phạm vi R3; dãy học Kahn theo vị trí dạy; chia module quy hoạch động; bộ vàng và các script chấm.

## Ghi chú cài đặt vé 01, 03, 10 (2026-09-26)

- R10: mỗi stage có `plan()` chỉ đọc, dùng chung nhánh cấu hình/cache với `execute()`. USD là ước lượng phần đã biết;
  không gán 0 cho stage chưa biết hoặc giá embedding chưa khai. Dự toán bao gồm A6/A7; `--dry-run` thắng `--allow-spend`.
- R1: trước chương có số chỉ áp khi tài liệu thực sự có chương có số. Bổ sung mẫu PDF dính chữ `MỤCLỤC`, `MỞĐẦU`,
  cùng mẫu hành chính “Hình thức và tiêu chuẩn đánh giá”. Giữ cách loại text `_toc_runs`, lưu dấu `is_toc` để tái tính.
  Tái gán vai trò không sửa lỗi cấp heading: doc-2 vẫn cần vé 04 trước khi dùng vai trò để loại nơi dạy.
- R8: top-3 hợp hai chiều (không đòi mutual), cosine mặc định 0,85. Dùng vector mô tả A6 sẵn có để đề cử;
  câu neo được xét trong lời phán, không tạo một loại embedding câu neo mới. Giữ nguyên luật gộp/duyệt.
- Công cụ kiểm chứng R8: `scripts/doc-lo-trinh/chay_danh_tinh_v3.py` mặc định dự toán; chỉ thêm `--allow-spend` khi
  được duyệt. Ngân sách lượt này tối đa 1,50 USD, có sổ chi và chốt dừng; kết quả thử không làm cache mặc định.
