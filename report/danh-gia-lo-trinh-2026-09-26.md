# Đánh giá lộ trình bằng đọc trực tiếp — 2026-09-26

Chủ dự án yêu cầu (2026-09-26): tăng tốc, không đòi con số chuẩn hoá cho mọi quyết định; tôi tự đọc lộ trình thật để phán đã
chuẩn chỉ và đọc được chưa, rồi lên kế hoạch cập nhật luồng dựa trên dữ liệu và nghiên cứu. Báo cáo này là phần "đọc và phán";
kế hoạch nằm ở [spec v3](../doc/v3-lo-trinh-doc-duoc-spec.md) và [vé v3](../task/v3-lo-trinh-doc-duoc/00-ke-hoach.md).

## Đọc gì

Lộ trình của chuỗi mặc định mới (neo C8 v3 + danh tính + A10), đọc bằng `scripts/doc-lo-trinh/in_lo_trinh.py`:
doc-1 stages v37, doc-2 v29, nhap-mon-ml v37, doc-3 v19, naive-bayes v37; doc-6 v8 (chuỗi cũ C8 v2 — để thấy slide buổi 1).
**Không đọc** lộ trình của tập giữ lại (xstk-ch3-1, doc-4).

## Phán xét chung

Trình tự lớn đúng (chương 1 → 5 ở doc-1; các module trong một mục thường cùng chủ đề), nên lộ trình **dùng được làm khung**.
Nhưng **chưa chuẩn chỉ và chưa dễ đọc**: một người học mở lộ trình sẽ gặp ngay tên module vô nghĩa, bài học đầu là đề cương,
nội dung một mục bị xé ra hai nơi, và danh sách "cần" dài không đúng nghĩa. Các lỗi này **lặp lại ở cả giáo trình lẫn slide**,
nên là lỗi của luồng, không của một tài liệu.

| | khái niệm | chỉ-được-nhắc trong dãy học | module | tên trùng | tên lấy từ vùng không dạy | module 1 |
|---|---|---|---|---|---|---|
| doc-1 | 218 | 17 (8%) | 39 | 15 | 4 | "1.1 Tập hợp" |
| doc-2 | 427 | 103 (24%) | 64 | 18 | **49** | "Preface for Students · The author's top ten" |
| doc-6 | 28 | 13 (46%) | 4 | 0 | 1 | "Nội dung môn học" (đề cương) |
| nhap-mon-ml | 75 | 19 (25%) | 15 | 1 | 4 | "MỞĐẦU" |
| doc-3 | 52 | 23 (44%) | 7 | 0 | 0 | "There are numerous ways* to create Machi…" |
| naive-bayes | 33 | 13 (39%) | 5 | 0 | 0 | "Giới Thiệu · Bayes's theorem" |

## Tám lỗi, kèm ví dụ

**L1 — Vùng không phải bài giảng định hình lộ trình.** Đề cương, lời nói đầu, "mở đầu" liệt kê, bài tập, đề thi sinh ra module
đầu, sinh cạnh giả và kéo vị trí.
- doc-6 module 1 "Nội dung môn học": 7 tên chương sau thành **chuỗi tiên quyết giả** CSDL → Mô hình quan hệ → Đại số quan hệ →
  SQL → Ràng buộc toàn vẹn → Phụ thuộc hàm → Dạng chuẩn — thứ tự liệt kê trong đề cương bị đọc thành phụ thuộc.
- nhap-mon-ml module 5 "MỞĐẦU": "SVM, K-NN, Rừng ngẫu nhiên… ← Siêu tham số, Bài toán phân loại" — các phương pháp chỉ được liệt kê.
- doc-2 module 1 lấy từ "Preface" và "The author's top ten", có cả "Definition", "Theorem" như khái niệm.
- doc-1 module 32 "Bài tập chương 4" chỉ chứa "KerT"; module 38 "… · Đề số 5".

**L2 — Khái niệm chỉ-được-nhắc nằm trong dãy học và kéo khái niệm được dạy đi theo.**
- doc-1: mục 3.5 bị xé đôi — module 28 đúng chỗ, còn module 37 (Độ dài, Góc, Hệ trực chuẩn, Gram-Schmidt) rơi **sau chương 5**,
  vì "Độ dài ← Tích vô hướng Euclid", mà nút này chỉ được nhắc ở bài tập chương 5.
- doc-1: "Định lý về số chiều" (mục 4.2) rơi xuống cuối lộ trình vì "← dim(Imf)", nút lấy từ "Đề số 5".
- doc-1: Phần tử trung hòa, Phần tử nghịch đảo, Luật giản ước (mục 1.3 Nhóm) bị kéo ra sau chương 3 bởi cạnh "Không gian véc tơ →
  Phần tử trung hòa" (một người chấm T1 cũng đánh cạnh này là ngược).

**L3 — Tên module không phân biệt, không nói nội dung.** "2.1 Ma trận" ×4, "1.2 Quan hệ và ánh xạ" ×3 (doc-1); "Exercises 3B"
×8 (doc-2); "u Ưu điểm · 1. Giới thiệu" (ký tự đầu dòng PDF, doc-6); một câu văn làm tên (doc-3).

**L4 — Cấu trúc mục của sách bị đọc sai (doc-2).** Tiêu đề mục thật kiểu "3C Matrices" không được nhận, nên nội dung mục 3C nằm dưới
"Exercises 3B"; các mục đánh số kết quả ("3.36 definition: …") lại thành tiêu đề.

**L5 — Danh sách "cần" dày và sai nghĩa.** "Hệ phương trình tuyến tính ← … Ma trận nghịch đảo, Hạng của ma trận, Ma trận bậc thang,
Hệ tam giác" — đó là công cụ để *giải*, không phải thứ cần để *hiểu định nghĩa*. "Không gian véc tơ ← Hệ phương trình tuyến tính"
(cạnh sinh từ ví dụ). "𝐅ⁿ ← Vector space" ngược (Axler định nghĩa 𝐅ⁿ ở 1A, trước không gian véc tơ). Khớp với số đo: T1/T11 cho thấy
lỗi chính của cạnh là **thừa ràng buộc**, không phải ngược; Q7b doc-1 59%.

**L6 — Trùng khái niệm chưa gộp.** Imf ≈ Ảnh của ánh xạ tuyến tính; Nhân ≈ KerT; Toán tử tuyến tính ≈ Tự đồng cấu; Độc lập tuyến
tính cực đại ≈ Hệ độc lập tuyến tính cực đại (doc-1); CSDL ≈ Cơ sở dữ liệu (doc-6); Upper triangular matrix ≈ Upper-triangular
matrix (doc-2). Bước danh tính chỉ sinh ứng viên từ trùng tên/alias, tiền tố chung chung, cùng câu neo — không bắt viết tắt, ký
hiệu, biến thể gạch nối.
*Đính chính 2026-09-26 (kiểm thử vé 10):* "Độc lập tuyến tính cực đại" và "Hệ độc lập tuyến tính cực đại" là hai định nghĩa riêng
trong sách (trong V ở mục cơ sở, trong S ở mục hạng), tức trường hợp riêng, **không** phải trùng; tiêu chí danh tính ở spec v3 R8b.

**L7 — Tên khái niệm vô nghĩa với người học.** "Tính chất 1", "Tính chất 3", "Định lý 4", "Định lý 7", "Hệ quả 2" (doc-1);
"Definition", "Theorem" (doc-2).

**L8 — Thiếu mệnh đề có tên** (đã đo: Q3 = 81%) — A3 trích khái niệm thành phần nhưng không trích định lý/mệnh đề thành nút.

## Căn cứ nghiên cứu cho hướng sửa

Nguồn dưới đây tôi đối chiếu qua trang tóm tắt/nguồn thứ cấp tìm được hôm nay; chỗ nào dùng hiểu biết có sẵn thì ghi rõ.
- **Tiên quyết là quan hệ bất đối xứng dựa trên định nghĩa.** RefD (Liang và cộng sự, EMNLP 2015) đo tiên quyết bằng mức hai khái
  niệm *tham chiếu nhau khác nhau thế nào* qua liên kết trong định nghĩa — cơ sở cho việc lấy **đoạn định nghĩa (câu neo)** làm căn cứ
  cạnh, thay vì mọi đoạn đồng xuất hiện. [RefD dataset](https://github.com/harrylclc/RefD-dataset)
- **Cấu trúc sách là tín hiệu mạnh nhưng phải đúng vùng.** Wang và cộng sự (CIKM 2016) trích bản đồ khái niệm từ giáo trình bằng
  đặc trưng cục bộ và toàn cục của cấu trúc sách, và làm chung hai việc chọn khái niệm chính và tìm quan hệ.
  [Using Prerequisites to Extract Concept Maps from Textbooks](https://clgiles.ist.psu.edu/pubs/CIKM2016-textbooks.pdf)
- **Chỉ những mục thuộc miền học mới được xếp thành đường học; trình bày bằng sơ đồ Hasse.** Lý thuyết không gian tri thức (Doignon
  & Falmagne): quan hệ suy diễn giữa các mục, đường học là dãy trạng thái tri thức, quan hệ bắc cầu được vẽ bằng sơ đồ Hasse.
  [Knowledge Spaces and Learning Spaces](https://arxiv.org/abs/1511.06757), [kst vignette](https://cran.r-project.org/web/packages/kst/vignettes/kst.pdf)
- **Rút gọn bắc cầu giữ nguyên quan hệ đạt tới mà bớt cạnh.** Aho, Garey, Ullman (1972); trong mạng tiên quyết môn học, liên kết
  bắc cầu là dư. [The transitive reduction of a directed graph](https://www.cs.tufts.edu/comp/150FP/archive/al-aho/transitive-reduction.pdf),
  [Course-prerequisite networks](https://arxiv.org/pdf/2506.23510)
- **Tiêu đề và tín hiệu cấu trúc giúp học, nhất là người ít kiến thức nền.** Hai phân tích gộp về nguyên tắc tín hiệu (signaling)
  cho hiệu ứng nhỏ–vừa trên hiểu và chuyển giao.
  [Meta-analysis of signaling, ETR&D 2020](https://link.springer.com/article/10.1007/s11423-020-09748-7),
  [How signaling affects learning with media, 2018](https://www.sciencedirect.com/science/article/abs/pii/S1747938X17300581)
- **Tiên quyết đưa vào đúng lúc cần; tổng quan là tổng quan, không phải bài học.** Lý thuyết mở rộng dần (Reigeluth & Stein 1983):
  trình tự đơn giản → phức tạp, tiên quyết kiểu Gagné đưa vào khi bài cần, có tổng hợp cuối đơn vị.
  [The Elaboration Theory of Instruction](https://ocw.metu.edu.tr/pluginfile.php/9337/mod_resource/content/1/Reigeluth%201983%20Article.pdf)
- **Đồ thị tri thức do LLM sinh thiếu chính xác, cần kiểm và hợp nhất.** Graphusion (2024).
  [Graphusion](https://arxiv.org/html/2407.10794v1) — cùng chiều với số đo nội bộ: T11 (cạnh ngầm 17–58% "không làm sai thứ tự").

## Kết luận cho kế hoạch

Ưu tiên theo tác động lên người đọc, rẻ trước: (1) vùng văn bản có vai trò (L1, L3, L4); (2) dãy học chỉ gồm khái niệm được dạy
(L2); (3) hiển thị tiên quyết rút gọn và phụ thuộc cấp module (L5 phần hiển thị); (4) tên module theo nội dung (L3); (5) danh tính
mở rộng (L6); (6) tên khái niệm có nội dung (L7); rồi mới đến các việc đắt: cạnh theo định nghĩa ở A8 (L5 phần gốc) và trích mệnh đề
ở A3 (L8). Chi tiết: spec v3.
