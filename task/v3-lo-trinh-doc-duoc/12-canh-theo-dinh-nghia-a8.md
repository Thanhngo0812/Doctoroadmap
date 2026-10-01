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

## Kiểm thử phần đầu (Claude, 2026-10-01) — mã đạt; mất độ phủ do **đặc tả cửa sổ của tôi sai**; cổng pilot so nhầm mốc

Đã kiểm `64fbc24`, `57a7d8d`, `1ed9c34`.

**Mã và cách chạy**
- Toàn bộ test xanh.
- Hợp đồng đúng như vé:
  - đích chỉ là đại diện `taught`/`uncertain`;
  - câu trích `can_de_hieu` phải nằm trong cửa sổ;
  - `cong_cu` là cạnh mềm có lý do riêng;
  - không đòi câu trích chứa tên tiên quyết.
- Đột biến 4/5 bắt được. **Lọt:** tắt chốt `target_not_taught` trong hàm kiểm vẫn xanh, vì phiên đã lọc trước. Cần một test gửi thẳng đề
  xuất có đích chỉ-nhắc vào hàm kiểm, vì đích chỉ-nhắc vẫn có thể nằm trong `allowed_node_ids`.
- Kiểm soát chi tốt: dry-run trước, sổ có trần, pilot ở kho riêng. Không chạy pass phụ production khi chưa rõ nguyên nhân là quyết định
  đúng.

**Vì sao pass chính mất độ phủ** (bao đóng doc-1: 55 → 23/131 cạnh vàng)
- Trong `executor_log`, mọi đề xuất bị bác vì `quote_outside_definition_window` (doc-1 71, doc-2 124) đều có câu trích **nằm trong chính chunk
  neo**.
- 68/71 và 106/124 câu nằm **trước** câu neo, phần lớn 1–4 câu trước (doc-1 65/71, doc-2 104/124). Đó là câu giả thiết của định nghĩa toán,
  đúng nơi tiên quyết được gọi tên:
  - "Giả sử K là một trường." → Trường → Không gian véc tơ;
  - "Suppose A is an m-by-n matrix." → Matrix → Column vector;
  - "Cho A là ma trận vuông cấp n có trị riêng λ…" → Trị riêng → Không gian riêng.
- Cửa sổ "câu neo + hai câu sau" do **tôi** đặt trong vé này đã cắt mất phần đó. Các cạnh này bị hạ thành `cong_cu` hoặc hoãn.
  Ví dụ "Tổ hợp tuyến tính → Biểu diễn tuyến tính" và "Matrix → Row/Column vector" (đều là cạnh vàng) thành cạnh mềm.
- `definition_chunk_not_cited` (doc-2 260): phần lớn câu trích lấy từ chunk khác (bằng chứng đồng xuất hiện), nên hạ cấp là đúng. Chỉ
  2 + 6 ca câu trích nằm đúng trong cửa sổ mà quên ghi chunk neo.

**Chấm lại 0 USD** (`scripts/doc-lo-trinh/thu_cua_so_rong_a8.py`)
- Phương pháp: cho chính các đề xuất mô hình đã trả qua lại đúng hàm kiểm, cửa sổ −4…+2. Ở cửa sổ gốc, script ra đúng số của nhân viên.
- Phạm vi: hai đầu thuộc đích vàng, sau luật A9 và rút gọn bắc cầu, tức đúng các cạnh hiện ở dòng "cần:".

| | doc-1 trực tiếp | doc-1 bao đóng | doc-2 trực tiếp | doc-2 bao đóng |
|---|---|---|---|---|
| đồ thị cuối luồng cũ (A8 chính + phụ cũ → A9) | P 18/29 · R 18/28 | P 106/129 · R 106/131 | P 11/17 · R 11/32 | P 22/23 · R 22/68 |
| chính + pilot, cửa sổ gốc (số của nhân viên) | P 13/25 · R 13/28 | P 67/82 · R 67/131 | P 8/11 · R 8/32 | P 12/16 · R 12/68 |
| chính + pilot, cửa sổ −4…+2 (cận dưới) | P 15/25 · R 15/28 | P 91/105 · R 91/131 | P 10/13 · R 10/32 | P 18/22 · R 18/68 |

- **Cổng pilot so nhầm mốc.** Mốc đúng để quyết chạy pass phụ là **đồ thị cuối của luồng cũ**, không phải riêng pass chính cũ (P 17/21).
  Pass phụ vốn thêm cạnh gián tiếp, nên độ chính xác trực tiếp trước rút gọn luôn thấp hơn pass chính. Bản thân đồ thị cuối luồng cũ cũng
  chỉ P 21/42 trước rút gọn.
- Với cửa sổ sửa:
  - doc-1 ngang luồng cũ về độ chính xác (trực tiếp 0,60 so với 0,62; bao đóng 0,87 so với 0,82), độ phủ còn thấp hơn (bao đóng 0,69 so với
    0,81);
  - doc-2 trực tiếp tốt hơn (0,77 so với 0,65), bao đóng kém hơn (P 0,82 so với 0,96; R 0,26 so với 0,32).
- Đây là cận dưới vì mô hình chưa từng được xem cửa sổ rộng.

**Đọc năm cạnh pilot nhân viên nghi** (doc-1, ngoài bao đóng vàng)
- "Phần tử trung hòa → Không gian véc tơ": **đúng theo sách**. Tiên đề không gian véc tơ cần phần tử trung hoà, đã dạy ở 1.3 Nhóm. Vàng mới là
  bên ghi ngược (đã thấy ở kiểm thử 05b).
- "Vô hướng → Hàm thực liên tục": neo **không** sai so với node. Node A3 thực chất là ví dụ "tập C[a, b] các hàm thực liên tục", nên đây là
  độ hạt của A3.
- Ba cạnh nền ("Vô hướng → Không gian véc tơ thực", "Ma trận → Ma trận chuyển cơ sở / Ma trận tọa độ") là tiên quyết thật nhưng thô.
- Khi mở cửa sổ, pilot có thêm vài cạnh đáng ngờ, ví dụ "Số chiều → Cơ sở chính tắc", lấy từ câu ví dụ "Vậy dim R n = n…" đứng trước câu
  "được gọi là cơ sở chính tắc". Cửa sổ rộng hơn đổi một phần độ chính xác lấy độ phủ, nên phải đọc lại sau lượt chạy thật.

## Sửa đặc tả (Claude, 2026-10-01) và việc còn lại
1. **Cửa sổ định nghĩa = câu neo, tối đa bốn câu trước nó và hai câu sau nó, trong cùng chunk neo.** Giữ dòng tiêu đề khối nếu có.
   - Số câu trước đặt trong config, vào khoá cache.
   - Bốn câu phủ 65/71 (doc-1) và 104/124 (doc-2) câu trích bị bác. Mở tới đầu chunk không thêm gì trên phép đo tên nguyên văn, mà dễ kéo
     theo định nghĩa trước đó trong chunk dài.
2. Câu trích nằm trong cửa sổ mà quên chunk neo → executor tự gắn chunk neo, không bác.
3. Thêm test cho chốt `target_not_taught` (xem trên).
4. **Chạy lại pass chính sáu tài liệu** (≈ 2,1 USD) và **pilot 216 cặp** (≈ 0,6 USD) với cửa sổ mới. Báo bảng như trên, mốc là đồ thị cuối
   luồng cũ, cùng phân bố lỗi bác mới.
5. Nếu bảng thật không tệ hơn cận dưới và tôi đọc các cạnh cứng mới thấy chấp nhận được, **chạy pass phụ production** (dry-run trước, ≈ 31
   USD, nằm trong ngân sách chủ dự án đã duyệt). Sau đó A9/A10 và nghiệm thu đầy đủ như mục Nghiệm thu.
   - Đây là quyết định đọc, không phải cổng số (luật tăng tốc).
   - Không dùng độ chính xác trực tiếp trước rút gọn so với riêng pass chính cũ làm cổng.

## Bổ sung theo nguyên tắc đa ngôn ngữ (Claude, 2026-09-26; spec v3 R16)

Làm cùng lượt chạy lại A6–A8 của vé này:
- Thay `DEFAULT_COMMON_NAMES` (A6, danh sách vi/en) bằng tên xuất hiện ở quá một tỉ lệ chunk đặt trong config, đo trên chính tài liệu
  (kiểu IDF).
- Bỏ `DEFAULT_DEFINITION_SIGNALS` (A7, cụm định nghĩa vi/en). Tín hiệu nơi định nghĩa là chunk chứa câu bằng chứng A3 hoặc câu neo của
  khái niệm.
- Nghiệm thu thêm: test tổng hợp ở một ngôn ngữ ngoài vi/en cho cả hai luật; báo số tên bị coi là quá chung trên từng tài liệu phát triển.
