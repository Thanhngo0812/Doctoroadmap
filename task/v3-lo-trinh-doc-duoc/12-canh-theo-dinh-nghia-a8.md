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

## Kết quả triển khai 2026-10-01 — dừng chờ đọc

Hợp đồng cửa sổ −4…+2 và tự gắn chunk neo đã triển khai; unit test toàn bộ xanh. Pass chính sáu tài liệu và pilot chỉ trong hai chương vàng đã chạy ở kho đánh giá riêng, **không chạy pass phụ đầy đủ**. Báo cáo số, bảng so đồ thị cuối luồng cũ sau rút gọn và danh sách 14 cạnh cứng mới: `report/ket-qua-v3-12-cua-so-dinh-nghia-2026-10-01.md`. Kết quả hỗn hợp (doc-1 bao đóng đúng 106→108, doc-2 22→19); cần chủ dự án đọc cạnh trước khi quyết định bước tiếp.

## Bổ sung theo nguyên tắc đa ngôn ngữ (Claude, 2026-09-26; spec v3 R16)

Làm cùng lượt chạy lại A6–A8 của vé này:
- Thay `DEFAULT_COMMON_NAMES` (A6, danh sách vi/en) bằng tên xuất hiện ở quá một tỉ lệ chunk đặt trong config, đo trên chính tài liệu
  (kiểu IDF).
- Bỏ `DEFAULT_DEFINITION_SIGNALS` (A7, cụm định nghĩa vi/en). Tín hiệu nơi định nghĩa là chunk chứa câu bằng chứng A3 hoặc câu neo của
  khái niệm.
- Nghiệm thu thêm: test tổng hợp ở một ngôn ngữ ngoài vi/en cho cả hai luật; báo số tên bị coi là quá chung trên từng tài liệu phát triển.

## Kiểm thử lượt cửa sổ −4…+2 (Claude, 2026-10-01) — kết quả đạt mốc; ba sửa nhỏ rồi chạy pass phụ đầy đủ

**Mã:**
- Toàn bộ `tests/unit` + `tests/integration` xanh trên mã chưa commit (mã thoát 0).
- Số câu trước/sau nằm trong config và khoá cache. Pass phụ lấy đúng thông số từ pass chính.
- Đột biến 4/4 bắt được: bỏ tự gắn chunk neo, bỏ câu trước neo, bỏ ranh giới đoạn, tắt chốt `target_not_taught`.

**Số đo:** tái lập bằng `so_sanh_a8_cua_so_v3.py`, khớp báo cáo.

| | doc-1 trực tiếp | doc-1 bao đóng | doc-2 trực tiếp | doc-2 bao đóng |
|---|---|---|---|---|
| đồ thị cuối luồng cũ, rút gọn | P 18/29 · R 18/28 | P 106/129 · R 106/131 | P 11/17 · R 11/32 | P 22/23 · R 22/68 |
| lượt chạy thật: chính + pilot, A9, rút gọn | P 15/25 · R 15/28 | P 108/127 · R 108/131 | P 11/14 · R 11/32 | P 19/23 · R 19/68 |
| + so câu trích sau khi gộp khoảng trắng (chấm lại 0 USD) | P 17/28 · R 17/28 | P 118/145 · R 118/131 | P 12/15 · R 12/32 | P 21/25 · R 21/68 |

- Lượt thật tốt hơn cận dưới tôi ước, nên điều kiện ở mục trước đã đạt.
- Với bước gộp khoảng trắng, luồng mới ngang luồng cũ về độ chính xác và vượt về độ phủ bao đóng ở doc-1 (0,90 so với 0,81). Ở doc-2,
  trực tiếp tốt hơn (P 0,80 so với 0,65); bao đóng P thấp hơn (0,84 so với 0,96), R gần bằng (21 so với 22).

**Đọc 14 cạnh cứng mới:**
- 12 chấp nhận được, trong đó "Phần tử trung hòa → Không gian véc tơ" đúng theo sách.
- 2 đáng ngờ: "Số chiều → Cơ sở chính tắc" (lấy từ câu ví dụ "Vậy dim R n = n…") và "Row rank → Column rank" (hai khái niệm định nghĩa cùng
  khối).

**Cạnh mất so với luồng cũ:**
- doc-1: "Véc tơ → Véc tơ n thành phần"; quan hệ "Tổ hợp tuyến tính ⇒ Phụ thuộc / Độc lập tuyến tính".
- doc-2: "Matrix → Scalar multiplication on matrices", "Linear combination of the columns → Column-row factorization". Hai cạnh vào tính chất
  kết hợp/phân phối mất do thiết kế (đích chỉ-nhắc).

**Nguyên cớ mất cạnh (đọc log):**
1. **Câu trích chỉ lệch khoảng trắng.** Mô hình chép câu nhiều dòng thành một dòng ("nếu hệ thức\n[formula]\nchỉ xảy ra" → "… [formula] chỉ xảy
   ra"). Chunk đều NFC, nên không phải lỗi Unicode.
   - Trong số bị bác vì `quote_outside_evidence_chunk`: doc-1 15/27, doc-2 33/71.
   - "Tổ hợp tuyến tính → Độc lập tuyến tính" bị bác ba lần vì đúng lỗi này.
   - Chấm lại (`thu_khoang_trang_a8.py`) lấy lại được: chính +4 / pilot +8 (doc-1), +5 / +1 (doc-2), kể cả bốn cạnh mất ở trên.
2. **Gộp hai thứ tự hỏi quá ngặt.**
   - 6 cặp bị hoãn chỉ vì hai thứ tự khác **nhãn loại căn cứ** (`evidence_kind`), dù cùng chiều và cùng loại cạnh.
   - 2 cặp cùng chiều nhưng khác cứng/công cụ.
   - Các cặp "một bên tạo, một bên không" (doc-1 9, doc-2 2) là bất đồng thật, hoãn là đúng.
3. **Cửa sổ rộng cho lọt câu không phải định nghĩa:**
   - câu báo trước "As we will soon see, for a linear map the next definition…" → Linear map → injective;
   - câu chứng minh "Khi đó từ tính độc lập tuyến tính … suy ra" → Độc lập tuyến tính → Ma trận tọa độ;
   - câu ví dụ đứng trước định nghĩa.

**Pass phụ đầy đủ trên pass chính mới:** dry-run 0 USD, 23.796 lời gọi ≈ 31,12 USD (doc-2 ≈ 20,70).

**Việc còn lại, theo thứ tự:**
1. So câu trích **sau khi gộp mọi khoảng trắng** (kể cả xuống dòng) ở cả hai phép kiểm (chunk căn cứ và cửa sổ).
   - Lưu lại đúng đoạn văn gốc làm `quote`.
   - Test: câu trích bị dàn một dòng được nhận; câu diễn đạt khác vẫn bị bác.
2. Gộp hai thứ tự của pass phụ:
   - cùng tạo, cùng chiều, cùng loại → tạo cạnh dù `evidence_kind` khác (lấy loại có độ tin thấp hơn);
   - cùng chiều nhưng khác loại → cạnh mềm `cong_cu`;
   - khác chiều hoặc khác quyết định → vẫn hoãn.
3. Prompt pass chính và pass phụ: câu trích `can_de_hieu` phải lấy từ chính định nghĩa/phát biểu, kể cả giả thiết giới thiệu đối tượng của
   nó. Không lấy câu dẫn dắt hay báo trước, ví dụ, bước chứng minh hay hệ quả; khi chỉ có những câu ấy thì `cong_cu` hoặc không tạo cạnh. Viết
   bằng định nghĩa chức năng, không danh sách cụm từ.
4. Chạy lại pass chính (≈ 2 USD) và pilot (≈ 0,45 USD). Gửi bảng như trên cùng danh sách cạnh cứng mới có câu trích.
5. Tôi đọc ngay. Nếu không tệ hơn hàng cuối của bảng trên → chạy **pass phụ đầy đủ** (dry-run trước, ≈ 31 USD, trong ngân sách đã duyệt),
   rồi A9/A10 và nghiệm thu.

## Lượt ba sửa 2026-10-01 — đã chạy, chờ đọc

Ba sửa đã triển khai: so câu trích sau gộp khoảng trắng và lưu span gốc; hoà giải hai thứ tự cùng chiều bằng nhãn căn cứ yếu hơn hoặc hạ cạnh mềm khi khác loại; prompt chỉ lấy phát biểu định nghĩa/giả thiết, không lấy dẫn dắt/ví dụ/chứng minh/hệ quả. Test tái hiện đã đỏ trước sửa rồi xanh. Đã chạy lại pass chính sáu tài liệu và pilot hai chương vàng trong kho đánh giá riêng; **chưa chạy pass phụ đầy đủ**. Bảng so đồ thị cuối luồng cũ, usage và 22 cạnh cứng mới kèm câu trích ở `report/ket-qua-v3-12-ba-sua-2026-10-01.md`.

Lượt thật doc-1: trực tiếp 17/29, bao đóng 109/134; doc-2: trực tiếp 11/16, bao đóng 20/25. Cải thiện so với lượt trước nhưng chưa đạt hàng chấm lại 0 USD, và vài câu ví dụ/chứng minh vẫn lọt. Dừng chờ chủ dự án đọc, **không tự suy từ “nếu không tệ hơn” để chạy pass phụ đầy đủ**.

## Kiểm thử lượt ba sửa (Claude, 2026-10-01) — **cho chạy pass phụ đầy đủ**

**Mã:**
- Toàn bộ `tests/unit` + `tests/integration` xanh (mã thoát 0).
- Đột biến 4/4 bắt được: so nguyên văn thay vì gộp khoảng trắng, lưu câu mô hình thay đoạn gốc, khác loại thành hoãn, lấy nhãn căn cứ của
  thứ tự đầu.
- Prompt dùng định nghĩa chức năng, không danh sách cụm từ.

**Số đo:** tái lập bằng `so_sanh_a8_cua_so_v3.py --evaluation-root artifacts/v3-r12-quote-evaluation`. Ngoặc là khoảng tin cậy Wilson 95%.

| | luồng cũ cuối, rút gọn | lượt ba sửa: chính + pilot, A9, rút gọn |
|---|---|---|
| doc-1 trực tiếp P · R | 18/29 (0,44–0,77) · 18/28 | 17/29 (0,41–0,74) · 17/28 |
| doc-1 bao đóng P · R | 106/129 (0,75–0,88) · 106/131 (0,73–0,87) | 109/134 (0,74–0,87) · 109/131 (0,76–0,89) |
| doc-2 trực tiếp P · R | 11/17 (0,41–0,83) · 11/32 | 11/16 (0,44–0,86) · 11/32 |
| doc-2 bao đóng P · R | 22/23 (0,79–0,99) · 22/68 (0,22–0,44) | 20/25 (0,61–0,91) · 20/68 (0,20–0,41) |

- **Mọi khoảng tin cậy đều chồng nhau.** Với 28–32 cạnh vàng mỗi chương, chênh vài cạnh giữa các lượt là nhiễu đo. Gold không phân định được
  thêm.
- So với hàng chấm lại 0 USD của mục trước, lượt thật thấp hơn chút về độ phủ (doc-1 bao đóng 109 so với 118). Phép chấm lại đó chưa tính
  luật prompt mới, vốn cố ý bớt cạnh; độ chính xác thì bằng nhau. Tôi quyết bằng đọc, không coi hàng đó là cổng số (luật tăng tốc).
- Đổi cạnh cụ thể so với luồng cũ:
  - Lấy lại: "Tổ hợp tuyến tính → Độc lập tuyến tính", "Matrix multiplication → Row-column rule / Linear combination of the columns",
    "Column vector → Row-column rule", "Row vector → Row rank".
  - Mất: "Ma trận tọa độ → Ma trận chuyển cơ sở", "Matrix → Matrix multiplication", "Matrix → Column vector", "Linear combination of the
    columns → Column-row factorization".

**Đọc 22 cạnh cứng mới:**
- Khoảng 16 đúng hoặc chấp nhận được, gồm 7 cạnh vàng trực tiếp.
- Khoảng 5–6 đáng ngờ:
  - "Số chiều → Cơ sở chính tắc" và "Độc lập tuyến tính → Cơ sở chính tắc": trích câu kết hoặc chứng minh của ví dụ;
  - "Không gian véc tơ thực → Cơ sở": sai độ cụ thể, đúng ra là "Không gian véc tơ";
  - "Không gian véc tơ hữu hạn sinh → Không gian véc tơ vô hạn chiều": câu trích nói về cơ sở;
  - "Row rank → Column rank": trích câu định nghĩa của chính tiên quyết.

**Đã thử hai luật thuần ở A9 để hạ các cạnh này; bỏ cả hai vì bắt nhầm cạnh đúng:**
1. "hai khái niệm chung một câu neo": doc-1 bao đóng 109 → 85. Nó bắt "Hệ sinh → Cơ sở", vì định nghĩa (a)/(b) bị bộ tách câu gộp thành một
   câu.
2. "câu trích là câu neo của chính tiên quyết": trong 9 cạnh nó bắt, chỉ "Row rank → Column rank" sai rõ. Nó bắt nhầm "Square matrix →
   Determinant of a matrix" và "Dạng tam giác → Tính định thức bằng biến đổi sơ cấp".

Các cạnh đáng ngờ còn lại thuộc loại câu nói gì (ví dụ, chứng minh), executor không kiểm được. Để lại cho đọc và chấm mù.

**Quyết định:** chốt hợp đồng lượt ba sửa và chạy pass phụ đầy đủ. Lý do:
- trên vàng ngang luồng cũ trong nhiễu đo;
- mỗi cạnh cứng có câu trích từ chính định nghĩa của đích, kiểm bằng mã;
- cạnh công cụ tách thành cạnh mềm;
- thêm vòng sửa chỉ đổi qua lại vài cạnh mà gold không phân định được.

**Việc tiếp theo cho nhân viên:**
1. Commit lượt ba sửa và 09d làm mốc.
2. Dry-run pass phụ đầy đủ trên pass chính của lượt ba sửa (tái dùng, không gọi lại pass chính) cho sáu tài liệu. Lần dry-run gần nhất ước
   ≈ 31 USD.
3. Chạy `--allow-spend` trong một kho đánh giá cuối (ngân sách lớn chủ dự án đã duyệt). Sau đó A9 → tên khái niệm → A10 → tên module.
4. Báo:
   - chi phí và số lần 429;
   - số cạnh cứng/mềm mỗi tài liệu;
   - `cham_tap_giu_lai.py` cho doc-1, doc-2 trên artifact `stages` cuối;
   - `kiem_doc_duoc.py` sáu tài liệu.
5. Tôi đọc lộ trình sáu tài liệu và nghiệm thu vé 12. Số nghiệm thu thành "mức tài liệu phát triển" trong giao thức T10/07 v2.
6. Nên có chấm mù kiểu T15 trên cạnh cứng của hai chương vàng nếu chủ dự án xếp được người, vì gold không còn phân định được.

## Chấm mù T15-dev (hai người, 2026-10-02) — luồng mới **ngang** luồng cũ; không cạnh nào ngược chiều

Bảng `cham-mu-v3-doc-{1,2}-A{1,2}.xlsx`, chấm bằng `scripts/cham-mu/cham_bang_v3.py`. doc-1 phía mới chấm theo đồ thị cuối
(`v3-r12-final-evaluation` v6; 0 cạnh hiển thị nằm ngoài bảng). doc-2 chấm theo đồ thị tạm, vì pass phụ doc-2 chưa xong; chấm lại bằng
`--moi-cuoi` khi xong.

| cạnh dư (không phải cạnh vàng trực tiếp) | A1 | A2 |
|---|---|---|
| cũ: không làm sai thứ tự học (doc-1 + doc-2) | 12/16 = 75% | 11/17 = 65% |
| mới: không làm sai thứ tự học (doc-1 + doc-2) | 10/15 = 67% | 10/15 = 67% |
| ngược chiều, cả hai luồng | 0 | 0 |

- **Độ tin người chấm:**
  - cạnh vàng được xác nhận đúng chiều: A1 10/10, A2 8/10;
  - đồng thuận cao: kappa +0,87 (doc-1) và +0,72 (doc-2), so với T1 là +0,40 / +0,19.
- **Kết luận:**
  - Hai luồng ngang nhau. Lỗi duy nhất là thừa ràng buộc, khoảng một phần ba cạnh dư, như T1/T11; không có lỗi ngược chiều.
  - Ngưỡng Q4 của v2 (≥ 0,90) cả hai luồng đều chưa đạt.
- **Cạnh cả hai người cùng cho là không cần**, luồng mới:
  - "Số chiều → Cơ sở chính tắc";
  - "Không gian véc tơ hữu hạn sinh → Không gian véc tơ vô hạn chiều";
  - "Row rank → Column rank";
  - "Scalar multiplication on matrices → additive identity of F^m,n";
  - "Không gian véc tơ thực → Hàm thực liên tục".
  Ba cạnh đầu tôi đã đánh dấu đáng ngờ khi đọc (câu trích từ ví dụ, hoặc là định nghĩa của chính tiên quyết). Cách đọc của tôi khớp người
  chấm. "Hàm thực liên tục" là node ví dụ của A3, có ở cả hai luồng.
- **Quyết định:** giữ hợp đồng vé 12, không mở vòng sửa thêm.
  - Hai luồng ngang nhau, mà luồng mới có câu trích kiểm bằng mã và tách cạnh công cụ.
  - Luật thuần để hạ loại cạnh này đã thử và bắt nhầm (mục trước).
  - Ghi "thừa ràng buộc ≈ 1/3 cạnh dư" làm giới hạn đã biết khi báo cáo.
