# 12 — Cạnh theo định nghĩa ở A8

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R12 · **Ai:** nhân viên · **Phụ thuộc:** 03–11 (đã xong) ·
**Chi phí mô hình:** chạy lại A8 sáu tài liệu phát triển. Dự toán bằng `--dry-run` trước; chủ dự án duyệt con số trước khi chạy.

**Trạng thái:** **đang triển khai, chưa đạt cổng chất lượng (2026-10-01)**. Sáu tài liệu đã chạy xong A6 → A7 → neo → danh tính và A8 pass chính; pilot pass phụ trong kho đánh giá đã hoàn tất, nhưng doc-1 chỉ 3/15 cạnh cứng mới khớp vàng trực tiếp. **A8 pass phụ production, A9/A10 mới, chấm mù và nghiệm thu cuối chưa làm**. Số liệu, artifact, chi phí và việc tiếp theo ở [báo cáo cập nhật](../../report/ket-qua-v3-12-tam-ngung-2026-09-29.md). Làm trước khi khoá cấu hình (T10) cho lượt tập giữ lại (07 v2). Chủ dự án nâng ngân sách 2026-09-28: có
300 USD credit Google Cloud, "miễn là dự án tốt, đồ thị chuẩn chỉ".

**Cổng chi phí A8:** Pass chính đã chạy trong trần 2,50 USD; pilot evaluation-only đã chạy trong trần 2 USD. Chủ dự án đã duyệt ngân sách lớn, nhưng dry-run pass phụ production ước 24.472 calls / 31,299322 USD trên sáu tài liệu và pilot chưa đạt cổng chất lượng. **Không chạy production pass phụ trước khi đối chiếu mù cạnh sai/thiếu và chứng minh bản sửa**, dù ngân sách sẵn có.

## Vì sao (cập nhật 2026-09-28, sau kiểm thử 05b)
- **Cạnh A8 quyết phần còn lại của lộ trình.** Trong v3, dãy học theo thứ tự sách và cạnh ngược đã mềm (vé 18). Sáu tài liệu: 0 cạnh cứng
  ngược thứ tự sách. Cạnh A8 quyết dòng "cần:", phụ thuộc module và `roadmap-target`. "Đồ thị chuẩn chỉ" nghĩa là cạnh cứng phải có
  thật, cần thật và có căn cứ.
- **Lỗi chính là thừa ràng buộc, không phải ngược chiều:**
  - T1 (v2): khoảng một nửa cạnh máy ngoài vàng bị ít nhất một người chấm mù coi là "không cần thứ tự";
  - T11: cạnh ngầm thêm vào phần lớn không cần (vé v2-06).
- **"Trong định nghĩa" hiện chỉ là lời khai của mô hình.** 417/483 cạnh doc-1 mang `evidence_kind = trong_dinh_nghia`, nhưng mã chỉ kiểm
  chunk căn cứ nhắc cả hai đầu. Không có gì kiểm căn cứ nằm trong đoạn định nghĩa của đích.
- **Đo 0 USD** (`scripts/doc-lo-trinh/thu_canh_cua_so_neo.py`; cửa sổ định nghĩa = câu neo + hai câu sau cùng chunk):
  - doc-1, cạnh cứng trong phạm vi vàng: có tên tiên quyết trong cửa sổ thì đúng theo bao đóng vàng 22/25 = 0,88; không có tên thì 7/14
    = 0,50. doc-2 quá ít cạnh trong phạm vi (12 + 2) để kết luận.
  - Chỉ khoảng một nửa cạnh vàng có tên tiên quyết nguyên văn trong cửa sổ (doc-1 18/36, doc-2 23/44). Phần còn lại được nhắc bằng diễn
    đạt khác ("the columns of A" cho Column vector). Vì vậy **không được** dùng luật tên nguyên văn thay cho mô hình: làm vậy mất tiên
    quyết thật.
- **Kho chính cũng phải chạy lại A8.** `secondary_edges` của doc-2, nhap-mon-ml, naive-bayes, doc-3 đã lỗi thời (dry-run ≈ 9,5 USD dưới
  prompt cũ). Vé này thay lượt chạy đó để không trả hai lần.

## Việc cần làm
- **Dời neo (C8 v3, vé 05/05b) và danh tính (vé 10b) lên trước A8** (W17 của spec v2). A8 chỉ nhận đại diện `taught`/`uncertain` sau
  danh tính, mỗi khái niệm có câu neo. `mentioned_only`/`unchecked` không làm đích; được hiện như ngữ cảnh.
- **Cửa sổ định nghĩa của đích** = câu neo và tối đa hai câu kế tiếp trong cùng chunk (như căn cứ mở rộng của vé 11b). Nếu neo là khối
  có tiêu đề (hạng 1 của vé 05b) thì gồm cả dòng tiêu đề.
- **Hai loại cạnh:**
  - `can_de_hieu`: cửa sổ định nghĩa của đích dùng tiên quyết (bằng tên, ký hiệu hoặc diễn đạt khác) và không hiểu được nếu chưa biết
    nó. `quote` phải là chuỗi con nguyên văn của cửa sổ, **kiểm bằng mã**; không đòi `quote` chứa tên tiên quyết.
  - `cong_cu`: tiên quyết chỉ cần cho ví dụ, bài tập, chứng minh hay phương pháp giải của phần đó. Căn cứ là chunk như hiện nay.
  - Chỉ `can_de_hieu` là cạnh cứng: ràng buộc dãy học, "cần:", `roadmap-target`, phụ thuộc module.
  - `cong_cu` là cạnh mềm có `soft_reason: "cong_cu"`. Nó không vào các thứ trên; hiện riêng hay ẩn thì ghi rõ trong spec-addendum.
  - `quote` không nằm trong cửa sổ → không nhận `can_de_hieu` (hỏi lại một lần như các bước khác, rồi hạ xuống `cong_cu` nếu chunk căn
    cứ hợp lệ, hoặc bỏ).
- **Giữ bộ sinh ứng viên và cấu trúc phiên hiện có** (pass chính theo phiên mục, pass phụ theo cặp nghi vấn), chỉ đổi hợp đồng căn cứ và
  prompt. **Không** thêm bộ sinh ứng viên mới trong vé này: bài học v2-06 là thêm cạnh đi kèm thừa ràng buộc.
- Prompt pass chính/phụ đổi tương ứng, viết bằng định nghĩa chức năng, không danh sách cụm từ; đăng ký lại `prompt_hash` có chủ đích.
- `canonical_version` và ID node giữ nguyên, nên bộ vàng vẫn chấm được.

## Nghiệm thu
- **Test (model giả, không mạng; fixture ở ít nhất hai ngôn ngữ ngoài vi/en, một chữ viết không cách từ):**
  - `quote` trong cửa sổ → cạnh cứng `can_de_hieu`;
  - `quote` ở chunk khác, dù chunk nhắc cả hai đầu → không nhận `can_de_hieu`;
  - diễn đạt khác được nhận ("the columns of A" cho Column vector);
  - `cong_cu` → cạnh mềm, không có trong "cần:", `roadmap-target`, phụ thuộc module;
  - A8 không nhận `mentioned_only` làm đích; nhận đại diện sau danh tính.
- **Dry-run:** sáu tài liệu, báo số lời gọi và USD từng stage; chủ dự án duyệt con số rồi mới `--allow-spend`.
- **Báo số** (thông tin cho reviewer, không phải cổng):
  - Mỗi tài liệu: số cạnh cứng trước/sau, tỉ lệ `can_de_hieu`/`cong_cu`, số tiên quyết cứng trực tiếp trung bình mỗi khái niệm.
  - doc-1, doc-2: độ chính xác và độ phủ **từng cạnh** (trực tiếp và theo bao đóng) trong phạm vi vàng, đặt cạnh hai đường cơ sở:
    1. cạnh A8 hiện tại;
    2. luật tên nguyên văn trong cửa sổ của `thu_canh_cua_so_neo.py` (doc-1: 0,88 trên 25 cạnh).
  - Q6/Q7/Q7b. Mọi thay đổi Q7 phải báo kèm đường cơ sở "n gần nhất" cùng số cạnh (bài học v2-06).
  - Cỡ `roadmap-target` của các đích vàng (số module, số khái niệm) trước/sau.
- **Chấm mù (chủ dự án quyết, kiểu T11):** mẫu cạnh cứng mới và mẫu cạnh bị hạ thành `cong_cu` trong hai chương vàng; nhãn "cần để hiểu /
  không cần thứ tự / ngược". Ghi trước giới hạn cỡ mẫu như T11.
- **Tôi kiểm:** đọc dòng "cần:" và phụ thuộc module của doc-1, doc-2 đối chiếu sách; bảng kiểm R11.

## Bổ sung theo nguyên tắc đa ngôn ngữ (Claude, 2026-09-26; spec v3 R16)

Làm cùng lượt chạy lại A6–A8 của vé này:
- Thay `DEFAULT_COMMON_NAMES` (A6, danh sách vi/en) bằng tên xuất hiện ở quá một tỉ lệ chunk đặt trong config, đo trên chính tài liệu
  (kiểu IDF).
- Bỏ `DEFAULT_DEFINITION_SIGNALS` (A7, cụm định nghĩa vi/en). Tín hiệu nơi định nghĩa là chunk chứa câu bằng chứng A3 hoặc câu neo của
  khái niệm.
- Nghiệm thu thêm: test tổng hợp ở một ngôn ngữ ngoài vi/en cho cả hai luật; báo số tên bị coi là quá chung trên từng tài liệu phát triển.
