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

## Nguyên tắc: tài liệu đa ngôn ngữ *(chủ dự án chốt 2026-09-26; áp cho mọi R dưới đây và mọi spec sau)*

Tài liệu đầu vào có thể thuộc bất kỳ ngôn ngữ và chữ viết nào. Các spec B0 đã đặt nguyên tắc này ("hệ thống phục vụ mọi giáo
trình, không riêng giáo trình tiếng Việt"); bản đầu của spec này vi phạm nó ở R1, R2, R7, R9, R11 bằng danh sách từ khoá
tiếng Việt/tiếng Anh.
- **Không** đưa vào luồng danh sách từ, cụm từ hay regex của một ngôn ngữ (tên mục, cụm định nghĩa, từ chung, tiền tố…). Gặp ngôn
  ngữ khác, luật kiểu này không báo lỗi mà lặng lẽ không chạy.
- Ưu tiên **bằng chứng cấu trúc trong chính tài liệu**: lặp lại, đánh số và chuỗi số, vị trí, khớp với tiêu đề hay mục lục của
  chính tài liệu, thuộc tính Unicode (chữ viết, loại ký tự).
- Chỗ cần hiểu nghĩa: **một lời gọi Gemini** với tập nhãn đóng, có cache, qua `SpendGuard` và `--dry-run`; không đặt trong khâu cắt
  chunk tất định của B0.
- Ngoại lệ chỉ được là cờ bật tay theo tài liệu hoặc chẩn đoán không đổi đầu ra, và phải nằm trong mục "Ngoại lệ đã biết".
- Vé chạm luật văn bản phải có fixture tổng hợp ở ít nhất hai ngôn ngữ ngoài vi/en: một chữ viết không phải Latin và một chữ viết
  không cách từ (Hán, Nhật, Thái). Khi có tài liệu thật ngôn ngữ thứ ba (T19, chủ dự án cung cấp), chạy thêm trên tài liệu đó.
- Ngôn ngữ giao diện (HTML, thông báo lỗi, bảng gán nhãn) nằm ngoài nguyên tắc này; dữ liệu trong artifact dùng mã trung tính, tầng
  trình bày dịch khi hiển thị (như B0).
- **Không vì sửa luật mà bắt chạy lại stage tốn tiền trên tài liệu hiện có.** Sửa nào đổi đầu ra trên tài liệu vi/en thì làm cùng
  lượt chạy lại đã có kế hoạch (vé 05 chạy lại neo, vé 12 chạy lại A6–A8, vé 13 chạy lại A3). Sửa còn lại phải cho kết quả y hệt trên
  tài liệu vi/en, kiểm bằng `--dry-run` trước/sau trên sáu tài liệu phát triển: không stage tốn tiền nào chuyển sang "sẽ chạy".

**Rà soát mã 2026-09-26 — chỗ đang vi phạm và vé sửa:**

| Chỗ | Với tài liệu ngôn ngữ khác | Vé |
|---|---|---|
| `canonical.alias_kind`: tên không có chữ Latin bị coi là ký hiệu | A3 loại gần hết khái niệm của sách chữ Kirin, Hán, Nhật, Hy Lạp, Ả Rập; A4 bỏ qua khi đề cử; A6 bỏ qua khi tìm nhắc tên | 16 |
| `mentions.exact_mentions` đòi ranh giới từ `\w`; `retrieval._tokens` tách theo khoảng trắng | chữ viết không cách từ: không khớp được tên nào, BM25 vô dụng | 16 |
| `DEFAULT_COMMON_NAMES` (A6) | danh sách vi/en | 12 |
| cụm "definition/denote/called" trong `_defined_script_symbol` (A3) | ký hiệu được định nghĩa bằng ngôn ngữ khác bị loại | 13 |
| `document_language`, `vietnamese()`, `--language` chỉ nhận vi/en (A5) | sách tiếng Pháp, Trung nhận mô tả tiếng Anh; câu tiếng Pháp nhiều dấu bị nhận là tiếng Việt nên mô tả đúng có thể bị bác | 15 |
| `ROLE_PATTERNS`, tìm chương đầu bằng "chương\|chapter" (vé 03) | bài tập, lời nói đầu, chỉ mục lại thành nơi dạy | 14 |
| `_MATH_CHAPTER` "Chapter", `_MATH_EXERCISES` "Exercises", `_MATH_RESULT` "định lý/ví dụ…", `_MATH_PAGE_HEADING` "Exercises" (vé 04, đang làm) | cấu trúc mục không nhận được | 14 |
| `DEFAULT_DEFINITION_SIGNALS` (A7) | khái niệm không có cụm vi/en bị bỏ khỏi bước chọn nơi định nghĩa | 12 |
| `PRIOR_SIGNALS` (neo) | `prior_knowledge` không bao giờ hợp lệ | 05 |
| kết câu `[.!?]` ASCII trong `anchors._SENTENCE` (neo) và `split_sentences` (A5) | câu tiếng Trung, Nhật, Hindi, Ả Rập không được tách | 05, 15 |
| `GENERIC_PREFIXES` (danh tính, chỉ đề cử) | bỏ sót ứng viên | 17 |
| mẫu vi/en trong R7, R9, R11 | sửa ngay trong spec này | 09, 11, 02b |

## Quyết định

### R1 — Vùng văn bản có vai trò *(A2; sửa L1, L3, L4; viết lại 2026-09-26 theo nguyên tắc đa ngôn ngữ)*
Mỗi section mang `role` ∈ `noi_dung` · `bai_tap` (bài tập, câu hỏi ôn tập, đề thi) · `de_cuong` (mục lục, đề cương, slide nội dung
lặp) · `mo_dau` (lời nói đầu, trang bìa) · `hanh_chinh` (thang điểm, lịch, thông tin giảng viên) · `cuoi_sach` (chỉ mục, tài liệu
tham khảo, nguồn ảnh). Chunk thừa hưởng vai trò của section; vùng kéo tới tiêu đề cùng cấp hoặc cao hơn kế tiếp. Gán theo hai lớp,
không có danh sách từ của ngôn ngữ nào:
1. **Cấu trúc trong tài liệu** (tất định, trong A2):
   - `de_cuong`: trang mục lục đã phát hiện (`_toc_runs`, khớp tiêu đề của chính tài liệu); tiêu đề lặp lại ở đầu nhiều mục.
   - `mo_dau`: phần trước phần tử đầu của **chuỗi chương** — chuỗi tiêu đề cấp cao cùng tiền tố, số tăng dần, nhận bằng
     `_chapter_sequences` mà không cần biết tiền tố là "Chương", "Chapter", "Kapitel" hay "第…章".
   - `cuoi_sach`: phần sau chương cuối mà đa số dòng là mục từ ngắn kết thúc bằng số trang (chỉ mục), hoặc mang mẫu trích dẫn
     (năm, tên viết tắt).
2. **Nhãn nghĩa** (một lời gọi Gemini mỗi tài liệu, là bước riêng sau A2): tiêu đề nào lớp 1 chưa quyết thì mô hình gán vào tập vai
   trò trên; đầu vào là tiêu đề, đường dẫn mục, vị trí và vài dòng đầu; mọi tiêu đề nhận đúng một nhãn; lỗi → `noi_dung` kèm cảnh
   báo. Ghi version chunks mới như `refresh_chunk_roles` (không đổi ID, text, offset), có cache và dự toán.
*Lý do:* Wang và cộng sự 2016 dùng cấu trúc sách làm tín hiệu — nhưng chỉ khi vùng đúng; mọi lỗi L1 đến từ việc coi đề cương/bài
tập là nơi dạy. Bảng chỉ mục chứa gần hết tên khái niệm, nên để nó thành `noi_dung` sẽ làm bẩn bước neo. Bản đầu (vé 03) dùng
danh sách mẫu vi/en trong mã; vé 14 thay.

### R2 — Nhận cấu trúc mục từ cách đánh số *(A2; sửa L4; viết lại 2026-09-26 theo nguyên tắc đa ngôn ngữ)*
Cấp mục suy từ chính cách đánh số của tài liệu, không từ tên mục của ngôn ngữ nào:
- **Chương:** chuỗi tiêu đề cùng tiền tố, số tăng dần (`_chapter_sequences`).
- **Mục số + chữ** ("3C", "Section 3C"): số chương đi liền một chữ in hoa (thuộc tính Unicode `Lu`), và phải thành **chuỗi** (A, B,
  C… tăng dần trong cùng số chương, ít nhất ba tiêu đề). Một tiêu đề lẻ kiểu "2D convolution" không được bật chế độ này.
- **Kết quả đánh số là khối, không phải mục:** một họ tiêu đề cùng tiền tố (rỗng như "3.36 …", hoặc một từ như "Định lý 2",
  "Theorem 4", "Satz 3", "定理 5") mà số chạy dày, xuyên qua ranh giới các mục cùng cấp (đánh lại theo chương chứ không theo mục)
  và thân ngắn → là khối trong mục đang mở. Nhận bằng thống kê đánh số, không bằng danh sách từ.
- **Mục bài tập đóng lại** khi gặp tiêu đề mục kế tiếp cùng cấp hoặc cao hơn (vai trò do R1 gán).
Tự nhận, không cần cờ theo tài liệu. `--heading-scheme vn-textbook` là ngoại lệ cũ (xem "Ngoại lệ đã biết"). Vé 04 làm bản đầu
bằng từ khoá tiếng Anh/Việt; vé 14 thay.

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
- Làm sạch tiêu đề không phụ thuộc ngôn ngữ *(sửa 2026-09-26)*: bỏ ký tự đầu dòng theo loại Unicode (ký hiệu, vùng dùng riêng,
  dấu đầu dòng) và tiền tố một ký tự lặp ở đầu nhiều tiêu đề của cùng tài liệu (như "u " do font ký hiệu); chuẩn khoảng trắng; chữ
  dính ("MỞĐẦU") chỉ tách khi chính tài liệu có bằng chứng (cùng tiêu đề xuất hiện ở chỗ khác có khoảng trắng); không nhận câu văn
  dài làm tiêu đề.
- Tên = tiêu đề mục `noi_dung` cụ thể nhất chung cho module; nếu trùng với module khác hoặc không có, sinh tên ngắn bằng mô hình từ
  **tên các khái niệm trong module** (mỗi từ nội dung của tên phải lấy từ tên khái niệm hoặc tiêu đề mục — kiểm bằng mã), dạng
  "1.1 Tập hợp — Phép toán và lượng từ", viết bằng ngôn ngữ của tài liệu. Một lời gọi mỗi module trùng, ≈ vài chục lời gọi mỗi tài
  liệu.
*Lý do:* nguyên tắc tín hiệu (hai phân tích gộp) — tiêu đề có nghĩa giúp hiểu, nhất là người ít kiến thức nền.

### R8 — Danh tính mở rộng *(A9'' — danh tính; sửa L6)*
Thêm nguồn ứng viên: (a) chuẩn hoá tên như bước neo (NFKC, bỏ dấu LaTeX, gộp gạch nối); (b) viết tắt ↔ tên đầy đủ (chữ đầu các
từ: CSDL ↔ Cơ sở dữ liệu); (c) tên có ký hiệu ↔ tên chữ (Im f ↔ Ảnh; Ker ↔ Nhân) qua **độ tương tự mô tả + câu neo** (embedding
đã có, top-k nhỏ); (d) tiền tố chung chung thêm "Hệ ", "Phép ". Phán và luật gộp giữ nguyên (nhóm kiểm đủ; người duyệt gộp chạm vàng).
*Sửa 2026-09-26:* (d) và danh sách tiền tố cũ trái nguyên tắc đa ngôn ngữ; thay bằng tiền tố/hậu tố lặp trong chính tài liệu (R16, vé 17).

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

### R9 — Tên khái niệm có nội dung *(sau A5; sửa L7; viết lại 2026-09-26 theo nguyên tắc đa ngôn ngữ)*
Tên chỉ là nhãn đánh số ("Tính chất 1", "Định lý 4", "Theorem 2") hoặc từ chung ("Definition", "Định lý" đứng một mình) không được
làm tên hiển thị. Nhận bằng bằng chứng trong tài liệu, không bằng danh sách từ: **họ nhãn** là tiền tố (một–hai từ) đi với ít nhất
hai số khác nhau trong tên khái niệm hoặc tiêu đề của cùng tài liệu. Tên là một phần tử của họ nhãn → nhãn đánh số: đổi thành tên nội
dung ngắn sinh từ câu neo, viết bằng ngôn ngữ của tài liệu (mã kiểm từ có trong câu neo), nhãn cũ giữ làm alias. Tên đúng bằng tiền tố
của họ → từ chung: bị loại khỏi khái niệm. Không đổi `node_id` — bộ vàng không bị ảnh hưởng.

### R10 — Chạy thử có dự toán *(CLI; bài học sự cố 2026-09-26)*
`roadmap --dry-run`: liệt kê **mọi** stage sẽ gọi mô hình (không chỉ stage đầu), kèm số lời gọi ước và USD ước; không gọi mô hình.

### R11 — Bảng kiểm đọc được *(công cụ kiểm thử của tôi)*
Script kiểm tự động trên artifact `stages`: module 1 không lấy từ vùng ngoài `noi_dung`; không tên module trùng; không tên chứa mẫu
vùng ngoài `noi_dung`; không `mentioned_only` trong dãy học; dòng "cần:" ≤ 3; không khái niệm tên nhãn đánh số/từ chung; không mục
nào của một section `noi_dung` bị tách thành hai module cách nhau quá một chương. Kèm phán xét đọc của tôi.
*Sửa 2026-09-26:* vùng của module lấy từ vai trò section (R1) chứ không từ mẫu tiêu đề vi/en; nhãn đánh số/từ chung nhận bằng họ nhãn
như R9 (vé 02b, tôi làm).

### R12 — Cạnh theo định nghĩa ở A8 *(A8; sửa gốc L5 — việc đắt, sau R1–R9)*
Dời neo và danh tính lên trước A8 (W17 cũ). Căn cứ của cạnh "cần để hiểu" là **đoạn định nghĩa (câu neo) của đích**; cạnh chỉ có
căn cứ ở ví dụ, bài tập hay phương pháp giải được gắn loại `cong_cu` (nên biết trước khi làm bài), không ràng buộc hiểu định nghĩa.
*Lý do:* RefD (tiên quyết bất đối xứng theo tham chiếu trong định nghĩa); T1/T11: lỗi chính là thừa ràng buộc. Chi phí: chạy lại A8
mỗi tài liệu (≈ 1–7 USD), cần chủ dự án duyệt trước khi chạy.

### R13 — Trích mệnh đề có tên ở A3 *(A3; sửa L8 — sau vé 07, theo quyết định chủ dự án)*
A3 trích định lý/mệnh đề/công thức/phương pháp có tên thành nút `ket_qua` với tên nội dung. Đổi danh sách khái niệm → cần kế hoạch
ánh xạ bộ vàng (concept_hash) trước khi làm.

### R14 — Ngôn ngữ tài liệu bất kỳ ở A5 *(A5; bổ sung 2026-09-26 theo nguyên tắc đa ngôn ngữ; vé 15)*
- `--language` nhận mã ISO 639-1 bất kỳ. Khi không khai, mã được xác định một lần mỗi tài liệu: chữ viết chiếm đa số (thuộc tính
  Unicode), cộng một lời gọi mô hình trên vài đoạn văn mẫu khi một chữ viết dùng cho nhiều ngôn ngữ (Latin, Kirin, Ả Rập…); mã ghi
  vào config.
- Mô tả khái niệm viết bằng ngôn ngữ đó. Kiểm "mô tả khác ngôn ngữ tài liệu" bằng chữ viết thay cho `vietnamese()`; không còn nhánh
  vi/en nào trong mã. Tách câu của mô tả dùng luật ranh giới câu Unicode của `UnicodeSentenceSplitter` (B0), không dùng `[.!?]`.
- A5 chạy bằng lệnh `canonicalize` riêng, không nằm trong chuỗi `roadmap`, nên sửa này không kéo chạy lại tài liệu hiện có; chỉ lần
  `canonicalize` sau mới dùng luật mới.

### R15 — Tên, ký hiệu và tìm nhắc tên không phụ thuộc chữ viết *(A3, A4, A6; bổ sung 2026-09-26; vé 16)*
- **Tên hay ký hiệu:** tên có ít nhất một từ gồm ≥ 2 chữ cái thuộc bất kỳ chữ viết nào (Unicode `L*`). Ký hiệu là chữ cái đơn, chữ
  thuộc khối ký hiệu toán học (Mathematical Alphanumeric Symbols, Letterlike Symbols), chỉ số trên/dưới. Bỏ điều kiện "có chữ LATIN".
- **Khớp tên trong văn bản:** chữ viết không cách từ (Hán, Kana, Thái, Lào, Khmer, Myanmar — nhận theo thuộc tính Unicode) không đòi
  ranh giới từ; BM25 tách các chữ viết đó thành bigram ký tự (cách làm phổ biến cho tiếng Trung, Nhật, Hàn).
- Ba sửa này cho kết quả y hệt với mọi tên và văn bản có chữ Latin, nên không được làm tài liệu hiện có phải chạy lại (kiểm bằng
  phân loại lại mọi tên trong artifact hiện có và `--dry-run`).

### R16 — Các danh sách từ còn lại: làm cùng lượt chạy lại đã có kế hoạch *(bổ sung 2026-09-26)*
Mỗi sửa dưới đây đổi đầu ra ngay trên tài liệu vi/en, nên gắn vào vé sẵn có sẽ chạy lại đúng stage đó:
- **`prior_knowledge` (neo — vé 05):** bỏ `PRIOR_SIGNALS`, thay bằng một lời gọi xác minh độc lập với câu hỏi đóng: câu trích có nói
  tường minh rằng người đọc phải biết trước khái niệm này không (cách làm như lượt xác minh R8b). Chỉ gọi cho phán `prior_knowledge`.
  Tách câu ứng viên của neo dùng luật ranh giới câu Unicode của B0.
- **Tên quá chung (A6 — vé 12):** thay `DEFAULT_COMMON_NAMES` bằng tên xuất hiện ở quá một tỉ lệ chunk đặt trong config, đo trên chính
  tài liệu (kiểu IDF, Spärck Jones 1972).
- **Nơi định nghĩa (A7 — vé 12):** bỏ `DEFAULT_DEFINITION_SIGNALS`; tín hiệu là chunk chứa câu bằng chứng A3 hoặc câu neo của khái niệm
  (đều do mô hình trích và mã đã kiểm có trong văn bản). R12 vốn đã lấy câu neo làm căn cứ.
- **Ký hiệu chữ hoa kiểu script (A3 — vé 13):** thay cụm "definition/denote/called" bằng: câu bằng chứng A3 (đã kiểm có trong văn bản)
  chứa ký hiệu đó, và ký hiệu còn xuất hiện ở ít nhất một chunk khác.
- **Tiền tố chung chung (danh tính, chỉ đề cử — vé 17):** thay danh sách "hệ/phép/tính/the notion of" bằng tiền tố hoặc hậu tố (≤ 2 từ)
  mà trong chính tài liệu gắn với ít nhất ba tên khái niệm khác. Danh tính rẻ và vé 10b đang chạy lại nó; lượt xác minh R8b vẫn quyết gộp.
Trong lúc chờ các vé 05, 12, 13: tài liệu ngôn ngữ khác vẫn chạy được, nhưng A6/A7 và bước neo kém hơn — giới hạn đã biết.

## Thứ tự

R10 và R11 trước (an toàn chi tiêu, công cụ kiểm) → R1, R2 (vai trò vùng, cấu trúc) → R3, R4, R5 (dùng vai trò) → R6, R7 (hiển thị,
tên) → R8, R9 → R12 (đắt) → R13 (sau vé 07). R8b phải xong trước R5, vì lọc khái niệm chỉ-nhắc cần đại diện nhóm là khái
niệm được dạy. Vé 07 (tập giữ lại) nên chạy **sau** R1–R9 để khoá cấu hình một lần trên luồng đã sửa:
đề nghị hoãn duyệt T10 tới khi các vé đó xong; T13 (liệt kê mù) làm được bất cứ lúc nào.
Vé sửa theo nguyên tắc đa ngôn ngữ: 16 (R15, nặng nhất) và 14 (R1/R2) trước, rồi 15 (R14), 17; phần R16 đi cùng vé 05, 12, 13. Các
vé này không đổi giao diện artifact nên làm song song được với R3–R9. Chạy thử tài liệu ngôn ngữ thứ ba (T19) sau 14–17. Khoá cấu
hình vé 07 v2 (T10) chờ cả các vé này.

## Không đổi

Luật neo C8 v3 hiện hành ngoài phạm vi R3; dãy học Kahn theo vị trí dạy; chia module quy hoạch động; bộ vàng và các script chấm.

## Ngoại lệ đã biết (nguyên tắc đa ngôn ngữ)

- `--heading-scheme vn-textbook` (v2): cờ bật tay theo tài liệu, giữ để chunk doc-4 và xstk (tập giữ lại) không đổi. Tài liệu mới
  không được cần cờ này.
- `split_syllable_ratio` (A1): chẩn đoán lỗi tách âm tiết riêng cho tiếng Việt, chỉ cảnh báo, không đổi đầu ra. Chưa có chẩn đoán
  tương đương cho ngôn ngữ khác — giới hạn đã biết.
- `name_key` dời dấu thanh tiếng Việt; `_mention_normalize` đổi y cuối từ thành i. Đây là chuẩn hoá chính tả tiếng Việt áp lên mọi
  văn bản, nhưng hai phía khớp được chuẩn hoá như nhau nên không làm sai ngôn ngữ khác.
- Giao diện HTML, thông báo lỗi, bảng gán nhãn cho người gán: ngôn ngữ giao diện.

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
