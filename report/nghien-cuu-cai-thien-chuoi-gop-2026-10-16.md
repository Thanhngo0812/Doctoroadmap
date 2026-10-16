# Nghiên cứu cải thiện chuỗi gộp (2026-10-16, bổ sung 2026-10-17)

**Phạm vi:**
- **Chi:** 0 USD. Không gọi mô hình, không chạy `doc2roadmap a4` hay `roadmap`.
- **Dữ liệu:** chỉ đọc kho riêng `tmp/v4-17i/artifacts`, các mốc v3 ở `artifacts/`, và lời phán C8 của 16 cuốn D-01. Riêng D-01, script chỉ in số tổng
  hợp.
- **Mã mới:** script và kết quả nằm ở `tmp/nghien-cuu-chuoi-gop/` (mục 9).

**Quyết định của chủ dự án (2026-10-16), báo cáo này lấy làm nền:**
- chuỗi gộp thành mặc định sau đợt này, **không chờ T-01**;
- neo "một khái niệm" (`anchor_batch_mode=single`) là mặc định, đã duyệt;
- đề cử theo mô tả nháp tắt (`DOC2ROADMAP_MERGE_DESCRIPTION_ENABLED=false`, vé 17k đã xong);
- phán sửa mỗi cặp một lời (`canonical_repair_batch_size=1`, vé 17j).

**Tóm tắt phát hiện:**

| Câu hỏi | Phát hiện chính | Lợi ước tính (doc-4, cấu hình mặc định) |
|---|---|---|
| 1. Neo tất định | Luật L8b quyết 18% khái niệm, 0% quá tay trên dữ liệu chỉnh luật; trên 16 cuốn D-01 chưa dùng để chỉnh thì quyết 7,9%, quá tay 3,4% | −91 lời neo, −0,065 USD |
| 2. Nguồn đề cử | `same_evidence` chưa tạo gộp nào trong 13 canonical; cạnh cắt chỉ có `ngram` không cho gộp nào ở cấu hình mặc định | −228 lời phán sửa, khoảng −0,19 USD |
| 3. Đồng nghĩa bị sót | Một cặp "khác" xoá cả thành phần gộp; mô hình tách 4 cặp chỉ khác cách viết | +2–4 gộp đúng mỗi tài liệu, 0 USD |
| 4. Thời gian | 45% thời gian canonical doc-4 nằm ngoài mọi phép đo, chủ yếu ở `prepare_anchors`; canonical chỉ chạy 4 lời đồng thời; pass chính tuần tự 28–31 phiên | canonical có thể từ khoảng 15 phút còn 4–6 phút (ước, cần đo) |
| 5. Cạnh trục | Không luật chống lật chiều nào có ích ổn định trên cả ba bộ vàng | — |

## 1. Bớt lời gọi neo bằng luật tất định

**Cách đo** (`q1_luat_neo.py`, `q1b_luat_chat.py`, `q1c_luat_duy_nhat.py`, `q1d_l8_khong_hai_cham.py`, `q1e_kiem_l8b_d01.py`):
- **Dữ liệu chỉnh luật:** 6 canonical có neo "một khái niệm": doc-1 v6, xstk v8, doc-4 v2, nhap-mon-ml v9, naive-bayes v9, doc-6 v3.
- **Ứng viên:** đúng danh sách LLM đã thấy, tức hàng cuối của khái niệm trong `anchor_decision_log`.
- **Hạng 0:** tính lại theo `src/doc2roadmap/domain/anchors.py:160-161`.
- **Mốc so:** lời phán cuối, sau xác minh (`anchor_log`, `teaching_status`).

**Nền:**
- Có 1.036 khái niệm được hỏi.
- Ứng viên đầu `k1` là câu bằng chứng A3 (hạng 0) ở 1.011 khái niệm (97,6%). Vì vậy riêng điều kiện "có hạng 0" không phân biệt được gì.
- LLM phán: `taught` 855, `mentioned_only` 177, `not_subject_matter` 2, `uncertain` 2.

| Luật (neo = k1, trạng thái = được dạy) | Luật quyết | LLM cũng "được dạy" | Cùng câu neo | Quá tay | USD neo bớt (lạnh) |
|---|---|---|---|---|---|
| L1: k1 hạng 0 | 1.011 | 841 | 707 | **170 (16,8%)** | 0,639 |
| L2: L1 + tên nằm trong câu | 879 | 724 | 617 | 155 | 0,563 |
| L3: L2 + từ định nghĩa ("được gọi là", "là một", "ký hiệu"…) | 362 | 326 | 307 | 36 (33 ở doc-4) | 0,237 |
| L6: k1 hạng 0 + tên ở vị trí được định nghĩa | 245 | 241 | 234 | 4 | 0,159 |
| L8: L6 + chỉ một ứng viên ở vị trí định nghĩa | 204 | 201 | 198 | 3 | 0,130 |
| **L8b: L8, bỏ dạng "Tên: …"** | **186 (18,0%)** | **186** | **184 (98,9%)** | **0** | **0,121** |

**Tên ở vị trí được định nghĩa** gồm hai dạng:
- câu, sau khi bỏ đầu "Định nghĩa n.", bắt đầu bằng tên rồi tới "là" hoặc "được…";
- tên đứng ngay sau "được gọi là", "gọi là", "ta gọi", "được định nghĩa là".

Ba ca quá tay của L8 ("Evaluation:", "Bảng từ vựng:", "Quá trình học:") đều thuộc dạng "Tên: …" ở đầu dòng gạch đầu dòng, nên L8b bỏ dạng này.

**L8b theo tài liệu:** doc-1 65/211, xstk 22/79, doc-4 91/626, nhap-mon-ml 6/62, naive-bayes 2/36, doc-6 0/22. Không có ca quá tay nào.

**Kiểm trên dữ liệu chưa dùng để chỉnh luật.** Luật L8b được chỉnh trên chính 6 tài liệu trên, nên tôi kiểm thêm trên lời phán C8 v3 của 16 cuốn D-01
(`ket-qua/q1e-l8b-d01.json`):

| | Được hỏi | Luật quyết | LLM cũng "được dạy" | Cùng câu neo | Quá tay | USD neo bớt |
|---|---|---|---|---|---|---|
| 16 cuốn D-01 | 7.361 | **585 (7,9%)** | 565 | 552 (97,7%) | **20 (3,4%)** | 0,356 / 4,25 (8,4%) |

Độ phủ và độ chính xác trên dữ liệu mới thấp hơn trên dữ liệu chỉnh luật. Con số thật nên lấy theo D-01: luật bớt khoảng 8–18% lời neo và quá tay khoảng
3%.

**Đích vàng:**
- L8b quyết 37/90 đích được hỏi. Câu neo trùng neo v3 ở 35/37; theo phán của Claude, 79/84 câu neo v3 là đúng.
- Hai chỗ lệch:
  - "Không gian véc tơ phức": v3 không có neo;
  - "Sự đấu tranh của các mặt đối lập": neo của luật là một câu định nghĩa, có lẽ còn tốt hơn neo v3.
- Luật không quyết đích nào trong 5 neo mà Claude nghi ngờ (`report/quy-loi-thuong-nguon-a8-2026-10-12.md:117-127`).

**Vì sao không dùng L3:**
- Ở doc-4 (văn bản triết), câu liệt kê như "chín trường phái … là: Nho gia, Mặc gia, …" kéo theo 33 khái niệm chỉ được nhắc.
- Với "Chất", k1 là câu vật lý ("Chất là cái gián đoạn…"), còn LLM chọn đúng câu triết học.
- L8 và L8b bỏ qua mọi ca có từ hai câu định nghĩa trở lên, nên tránh được cả hai lỗi này.

**Tác động trong cấu hình mặc định mới (neo "một khái niệm"):**
- Trên doc-4, neo "một khái niệm" cộng mô tả và kiểm mô tả tốn khoảng 0,684 USD lạnh, ngang chế độ a5 (0,664 USD theo cost_summary của doc-4 v3).
- L8b bớt 91 lời và 0,065 USD trên doc-4.
- Nguồn: `ket-qua/q6-chi-phi-lanh.json`, manifest `canonical/doc-4/v2` và `v3`.

## 2. Hiệu suất từng nguồn đề cử

**Cách đo** (`q2_nguon_de_cu.py`): dùng `nominations.edges`, `cut_edges` và nhật ký `nomination_pair` của cả 13 canonical chuỗi gộp.
- **Chi phí phán sửa:** lấy từ `usage` của các hàng `repair`, chia đều cho các cạnh cắt mà lời đó phủ.
- **Mô phỏng bỏ nguồn:**
  - (a) xoá cạnh chỉ có nguồn đó, rồi chia cụm lại bằng đúng thủ tục Louvain của `domain/nomination.py:221-229`;
  - (b) vẫn dùng cạnh để chia cụm, nhưng không phán sửa cạnh cắt chỉ có nguồn đó.

**doc-4 v3, cấu hình mặc định** (867 cạnh, 482 cạnh cắt, 467 lời phán sửa, 0,375 USD lạnh):

| Nguồn | Cặp | Chỉ nguồn này | Cắt, chỉ nguồn này | Gộp | Gộp chỉ nhờ nguồn này | USD phán sửa, chỉ nguồn này |
|---|---|---|---|---|---|---|
| name | 510 | 347 | 148 | 41 | 11 (5 qua phán sửa) | 0,109 |
| ngram | 312 | 160 | 116 | 29 | 1, trong cụm ("Mối liên hệ = Liên hệ") | 0,093 |
| same_evidence | 207 | 153 | 112 | **0** | 0 | **0,102** |
| alias / shared_name_or_alias | 18 | 0 | 0 | 11 | 0 | 0 |

**Hai tài liệu khác:**
- doc-1 v6:
  - same_evidence: 22 cặp, 0 gộp, 11 lời sửa chỉ nguồn này, 0,008 USD;
  - ngram chỉ nguồn này: 38 lời, 0,026 USD, 0 gộp;
  - name chỉ nguồn này: 47 lời, 0,034 USD, 1 gộp (KerT = Kerf).
- xstk v9: gộp duy nhất qua phán sửa chỉ nhờ name là gộp **sai** đã biết "Độ tin cậy = Độ tin cậy của ước lượng".

Nguồn: `ket-qua/q2-nguon-de-cu.json`, `q2d-gop-mot-nguon.json`.

**Phát hiện:**
- **same_evidence chưa từng tự tạo gộp nào trong 13 canonical.** Bỏ nó (mô phỏng a) mất 0 gộp ở mọi tài liệu. Trên doc-4 v3, số cạnh cắt giảm từ 482
  còn 328 (−32%).
- **Bỏ phán sửa cạnh cắt chỉ có ngram** (mô phỏng b) mất 0 gộp ở mọi cấu hình mặc định.
- **Phải giữ name.** Bỏ nó (a) mất 7 gộp trên doc-4 v3, 6 trên doc-1, 2 trên xstk.
- **Ngưỡng cosine không lọc được cạnh name.** 16/16 lần gộp qua phán sửa có cosine vector tên 0,891–0,988, và gần như mọi cạnh cắt cũng ≥ 0,85
  (`q2c_nguong_ten.py`).
- **Đề cử theo mô tả** (đối chiếu doc-4 v2): 1.262 cặp chỉ có nguồn này, 972 cạnh cắt, 0,818 USD, chỉ 3 gộp. Tắt là đúng.
- **Chia cụm A4 không tái lập được giữa hai tiến trình** (`q2b_tai_lap_cum.py`).
  - nhap-mon-ml v8 và v9 có cạnh và trọng số giống hệt nhau, mà số cạnh cắt đã lưu là 157 so với 156.
  - Chia lại với `PYTHONHASHSEED` từ 0 đến 3 thì khi khớp bản này, khi khớp bản kia.
  - Nguyên nhân: Louvain của networkx (`domain/nomination.py:224,228`) duyệt tập id dạng chuỗi, nên phụ thuộc hash ngẫu nhiên của tiến trình.
  - Hệ quả: chạy lại có thể ra cụm khác, mất tái dùng cache lời phán cụm, và thêm nhiễu cho phần gộp.

**Bỏ same_evidence cộng không phán sửa cạnh cắt chỉ có ngram**, ước theo mô phỏng:
- doc-4: từ 467 lời còn khoảng 239, bớt khoảng 0,19 USD;
- doc-1: bớt khoảng 49 lời, 0,034 USD.

Đây là ước tính vì chia cụm lại có thể đổi thêm cạnh cắt.

## 3. Phục hồi gộp đồng nghĩa bị sót, không kéo lại gộp sai

Theo dõi từng cặp qua mọi phiên bản (`q3_cap_dong_nghia.py`, `ket-qua/q3-cap.json`).

**3.1. Mâu thuẫn bắc cầu xoá cả thành phần.**
- `domain/canonical_decisions.py:148-166`: chỉ cần một cặp "khác" nằm trong thành phần thì **mọi** nhóm của thành phần bị tách thành đơn lẻ và bị hoãn
  (`canonical_merge.py:112-114`).
- Mỗi tài liệu có 2–3 thành phần như vậy, gồm 6–9 nhóm. Nhiều cặp trong đó đã được phán cùng **và** xác minh `dong_nhat`.

Mô phỏng cách giải "tham lam có ràng buộc" (`q3b_xung_dot.py`):
- nối cặp cùng theo thứ tự độ tin: chung tên sau chuẩn hoá, rồi xác minh `dong_nhat`, rồi số lời phán cùng;
- bỏ một phép nối nếu nó gom hai đầu của một cặp "khác".

| Tài liệu | Gộp phục hồi | Đánh giá |
|---|---|---|
| doc-1 v6 | Imf = Ảnh; Quá trình Gram - Schmidt = Quá trình Gram-Schmidt | đúng |
| xstk v9 | Độ chính xác = Độ chính xác ε; Xác định kích thước mẫu = … trong ước lượng trung bình | 1 đúng, **1 sai đã biết** |
| doc-4 v3 | Hoài nghi luận = Thuyết hoài nghi; Nhận thức luận = Lý luận nhận thức; CN duy vật biện chứng = Triết học duy vật biện chứng | 2 cặp nằm trong danh sách sót của 17i; cặp thứ ba có lẽ đúng |

**Biến thể bảo thủ:** trong thành phần mâu thuẫn, chỉ giữ cặp chung tên sau chuẩn hoá. Biến thể này phục hồi 2 cặp đúng (doc-1) và 0 cặp sai.

**3.2. Cặp chung tên sau chuẩn hoá bị mô hình tách.**
- Trên 6 tài liệu mặc định có 5 cặp như vậy; 4 cặp không được gộp, và cả 4 đều chỉ khác nhau về cách viết:
  - χα 2 = χα^2 và χ0 2 = χ0^2: lời sửa đầu trượt kiểm "lặp nhóm", lời sửa lại thì tách;
  - Gram - Schmidt = Gram-Schmidt: bị hoãn vì mâu thuẫn;
  - Véc tơ tọa độ = Véctơ tọa độ: bị phán khác.
- Luật "chung **tên** sau chuẩn hoá thì buộc gộp" cho thêm 4 gộp đúng và 0 gộp sai.
- Không áp luật này cho alias. 9 cặp chung alias bị tách đa số do alias A3 sai, ví dụ "Kết cấu" / "Phương thức liên kết" (`ket-qua/q3d.json`).

**3.3. Hướng không nên làm, hoặc chưa đủ bằng chứng:**
- **Luật ký hiệu trong câu bằng chứng** ("ký hiệu", ngoặc đơn, "còn gọi là"): không ra cặp đúng nào mới (`q3e_luat_ky_hieu.py`).
- **Imf = Ảnh của ánh xạ tuyến tính:** không được đề cử ở phiên bản nào. **Tự đồng cấu = Toán tử tuyến tính** và **Bao tuyến tính = Không gian con sinh
  bởi…** chỉ được đề cử nhờ mô tả, và bị phán `subtype_of` hoặc `coextensive_with`.
- **`coextensive_with` chưa có trong nhãn đồng nhất của R2 chuỗi gộp** (`canonical_decisions.py:21-24`). Nên thêm; lợi nhỏ.
- **Đưa mọi `subtype_of` sang xác minh mù: rủi ro cao.**
  - Số quan hệ `subtype_of`: doc-1 71, xstk 33, doc-4 223.
  - Bộ xác minh đã từng cho `dong_nhat` với Tọa độ = Véc tơ tọa độ (doc-1 v5) và với cả 3 gộp sai đã biết của xstk.
- **Chặn tên có cụm hạn định** ("… của X", "… trong X", "… tổng quát"): 4 ca trong các gộp mặc định, gồm 2 sai đã biết và 2 chưa rõ
  (`ket-qua/q3c-ten-chua-nhau.json`). Ưu tiên thấp.

## 4. Thời gian

**4.1. Vì sao `phase_measurements` "ra 0".** Số đo không hỏng mà bị lệch theo ba cách:
1. **Chế độ a5:** lời mô tả và kiểm gộp với neo được đo dưới tên `anchor` (`canonical_describe.py:46`; chi phí ở :57-59), nên `describe` ≈ 0 và không
   có `check`.
2. **Phần tái dùng:** chỉ đo thời gian tra cache. Ví dụ ở doc-1 v7, `merge` mất 0,006 giây.
3. **Đoạn CPU nằm ngoài mọi `measure_phase`:**
   - `build_nodes` (`canonicalize.py:139`);
   - đề cử và chia cụm (`:155-159`);
   - `prepare_anchors` (`:173`);
   - remap và ghi.

| Canonical | Thời gian stage (giây) | Tổng các phần (giây) | Không đo được |
|---|---|---|---|
| doc-4 v3 | 877 | 480 | **397 (45%)** |
| doc-4 v2 | 1.634 | 1.271 | 363 |
| doc-1 v6 | 130 | 101 | 29 |

**4.2. CPU tại máy** (`q4_do_cpu.py`, 0 USD). doc-4 đo hai lượt: lượt 1 khi máy đang tải nặng, lượt 2 khi máy rảnh hơn.

| Đoạn | doc-1 (231 node, 199 chunk) | doc-4, lượt 1 | doc-4, lượt 2 |
|---|---|---|---|
| `prepare_anchors` | 33,0 giây | 260 giây | **198 giây** |
| `build_nodes` | 3,8 giây | 45 giây | 24 giây |
| `nomination_graph` | 3,4 giây | 25 giây | 13 giây |
| `additional_nominations` | 1,3 giây | 9 giây | 5 giây |
| *Đối chiếu:* `exact_mentions` gọi từng node | 26,9 giây | 403 giây | 202 giây |
| *Đối chiếu:* `exact_mentions` một lần cho mọi node | 5,5 giây | 146 giây | 62 giây |

- Trên doc-4, bốn đoạn đầu cộng lại 240–339 giây, tức phần lớn trong 397 giây không đo được.
- Ở lượt 2, `prepare_anchors` (198 giây) gần bằng riêng `exact_mentions` gọi từng node (202 giây), nên gần như toàn bộ thời gian nằm ở bước dò tên này.
- Nguyên nhân: `canonical_anchors.py:43-44` gọi `exact_mentions([node], …)` cho từng node, nên toàn bộ chunk bị chuẩn hoá lại một lần cho mỗi node
  (`domain/mentions.py:43-44`). `heading_chunks` và `symbolic_name_chunks` cũng quét mọi chunk cho từng node (`anchor_core.py:73-76`).
- Chuẩn hoá chunk một lần là đủ và không đổi ngữ nghĩa. Ước bớt ít nhất 140 giây trên doc-4: hiệu giữa gọi từng node và gọi một lần, 202 − 62 giây.
- Số đo lượt 2 nằm ở `ket-qua/q4-cpu-doc-4.json`.

**4.3. Chuỗi đồ thị theo stage** (giây, từ `stats.runtime_seconds` trong manifest `tmp/v4-17i/artifacts/graph/<doc>/v*`):

| Stage | doc-1 (v9–16) | xstk (v9–16) | doc-4 (v1–8) |
|---|---|---|---|
| clusters (A6–A7) | 12,9 | 23,3 | 72,4 |
| mentions | 17,9 | 14,1 | **400,0** |
| main_edges (pass chính) | 151,6 | 157,4 | **824,8** |
| secondary_edges (ML) | 39,6 | 22,7 | **592,5** |
| validated (A9) | 1,1 | 0,4 | 6,6 |
| concept_labels | 16,0 | 0,3 | 5,4 |
| stages (A10) | 4,4 | 1,4 | 9,7 |
| module_titles¹ | khoảng 6 | khoảng 5 | khoảng 17 |
| **Tổng** | **khoảng 250** | **khoảng 225** | **khoảng 1.929 (32 phút)** |

¹ Manifest của `module_titles` không có `stats`, nên con số lấy từ chênh lệch `created_at` với stage trước. Đây là thêm một chỗ hở đo đạc.

**Đọc bảng:**
- **Pass chính tuần tự hoá.**
  - Mỗi phiên nhận `previous_edges_in_chapter`, nên các phiên trong một chương chạy nối tiếp (`build_main_edges.py:53-65, 91-111`).
  - doc-1 có làn dài nhất 28 phiên; xstk có 31 phiên trong một chương. Trần đồng thời 100 vì thế không dùng được.
  - Prompt pass chính không nhắc tới trường này (`prompts/a8/main.txt`). Spec A8 tự ghi rằng đây là nguồn nhiễu (F101,
    `doc/A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md:322-327`).
- **mentions trên doc-4 mất 400 giây.** Các vòng lặp Python thuần:
  - `document_common_names`: mỗi tên dò regex trên mọi chunk;
  - `exact_mentions` chạy hai lần (bản mới và bản cũ, `build_mentions.py:101-102`);
  - `dense_mentions`: tích vô hướng 630 × 671 × 768 viết bằng Python (`domain/mentions.py:92-98`), dù numpy đã là phụ thuộc (`pyproject.toml:20`).
- **clusters và mentions cùng embed 630 tên trên doc-4**, với cùng 51.865 token. Suy đoán: cùng một văn bản bị embed hai lần.
- **Pass phụ ML mất 592 giây trên doc-4.** ADR 0015 ghi 18 giây trên d01-02 (`doc/adr/0015-…md`, mục Căn cứ). Chưa tìm ra nguyên nhân; cần profile.

**4.4. Song song trong canonical:**
- `canonical_concurrency=4` (`config.py:47`, `composition.py:192`) áp cho mọi phần, kể cả neo (`canonicalize.py:190`).
- Chuỗi đồ thị dùng `llm_max_in_flight=100` trên Vertex (`composition.py:223-224`). Bộ giới hạn thích ứng tự hạ một nửa khi gặp 429
  (`infrastructure/llm/rate_limit.py:91-98`).
- Neo "một khái niệm" có rào chắn sau mỗi lô `NODE_BATCH=8` (`anchor_core.py:109-128`). Đường canonical không cần rào này vì không ghi checkpoint.
- `vertex_concurrency` (`config.py:28`) không được đọc ở đâu.
- Mỗi lời mất khoảng 1,7–2,1 giây. Ví dụ phán sửa doc-4 v2: 793 giây × 4 / 1.585 lời = 2,0 giây.

**Ước thời gian canonical doc-4** ở cấu hình mặc định mới, sau các khuyến nghị 1, 2, 7 và 8 (mục 7):
- phần LLM khoảng 540 giây ở 4 lời đồng thời, còn khoảng 140 giây ở 16;
- phần CPU khoảng 240 giây (lượt đo 2), còn khoảng 100 giây nếu sửa `prepare_anchors`;
- tổng khoảng 4–6 phút, so với 14,7 phút của lượt cuối 17i.

Đây là ước tính tuyến tính, cần một lượt đo thật.

## 5. Pass chính và cạnh trục

**5.1. Nhiễu giữa hai lượt** (`q5_nhieu_pass_chinh.py`, `q5b_phien_trung.py`). So cạnh pass chính giữa pha A và lượt cuối, theo cặp tên khái niệm:

| | Pha A | Lượt cuối | Giữ | Mất | Mới | Đảo chiều | Jaccard |
|---|---|---|---|---|---|---|---|
| doc-1 | 230 | 223 | 174 | 56 | 49 | 0 | 0,624 |
| xstk | 72 | 83 | 41 | 31 | 42 | 0 | 0,36 |

- Không phiên nào có đầu vào giống hệt giữa hai lượt: 0/58 ở doc-1, 0/30 ở xstk.
- Trường khác nhau, đếm trên doc-1: `mentioned_elsewhere` 56, `proposed_relations` 57, `previous_edges_in_chapter` 52, `target_concepts` 42.
- Vì vậy nhật ký hiện có chưa tách được nhiễu do mô hình khỏi nhiễu do đầu vào.
- Ở phiên trục, pha A ra "Không gian véc tơ → Véc tơ"; lượt cuối không ra cạnh này. Hai khái niệm có **cùng một câu neo**.

**5.2. Thử luật chống lật chiều trên vàng** (`q5c_chong_lat_chieu.py`).
- Luật áp lên tập cạnh máy đúng như bộ chấm (`a8_score.py:497-509`), rồi tính lại Q7, Q7b và P/R trực tiếp.
- Mốc L0 khớp đúng số của `cham_gop.py` ở cả 5 graph, nên phép tái lập đáng tin.
- Không chạy lại A9 hay A10.

| Graph | L0 (mốc) | LA: bỏ cạnh ML giữa hai khái niệm cùng câu neo | LD: thuật ngữ được định nghĩa làm tiền quyết | LE: tên xuất hiện trước trong câu neo làm tiền quyết |
|---|---|---|---|---|
| doc-1 pha A | 0,725 / 0,707 | 0,717 / 0,721 | 0,582 / 0,707 | **0,750 / 0,723** |
| doc-1 lượt cuối | 0,419 / 0,645 | 0,392 / 0,698 | 0,354 / 0,645 | **0,551 / 0,725** |
| xstk pha A | 0,230 / 0,730 | 0,194 / 0,713 | 0,206 / 0,642 | 0,206 / **0,642** |
| xstk lượt cuối | 0,278 / 0,506 | 0,266 / 0,557 | 0,278 / 0,506 | 0,278 / 0,506 |
| doc-4 lượt cuối | 0,638 / 0,878 | không đổi | không đổi | không đổi |

Mỗi ô là Q7 / Q7b. Nguồn: `ket-qua/q5c-chong-lat-chieu.json`.

**Ba luật thêm:**
- **LB** (bỏ mọi cạnh cùng câu neo, trừ cạnh pass chính có bằng chứng `noi_ro` hoặc `trong_dinh_nghia`): ra đúng như LA.
- **LC / LC2** (lật hoặc bỏ cạnh ML ngược thứ tự sách): không đổi gì. Cạnh ML ở doc-1 và xstk không có cạnh nào ngược thứ tự sách. Ở doc-4, LC2 bỏ 2 cạnh,
  không ảnh hưởng vàng.

**Kết luận: không luật nào có ích ổn định.**
- **LE** sửa đúng cạnh trục ở doc-1, đưa "Không gian véc tơ → Véc tơ" và "Hệ sinh → Cơ sở" về đúng chiều; Q7 lượt cuối tăng 0,13. Nhưng ở xstk pha A,
  LE lật cạnh vàng "Xác suất mắc sai lầm → Độ tin cậy", làm Q7b tụt 0,088. Ở doc-4, LE lật 6 cạnh ngoài vàng, như "Giải thoát → Brahman", mà vài cạnh
  trông sai.
- **LD** có hại.
- **LA và LB** đổi Q7 lấy Q7b.
- Mọi chênh lệch trên đều nằm trong mức nhiễu E4 một lượt (khoảng ±0,15).

Vàng chỉ có 3 cạnh giữa hai khái niệm cùng câu neo ở doc-1, 3 ở xstk, 0 ở doc-4. Mẫu này quá nhỏ để chọn luật. Máy có 28–35 cạnh như vậy ở doc-1, 15 ở
xstk, 19 ở doc-4.

**5.3. Đề xuất:**
1. **Đo nhiễu thuần mô hình:** phát lại đúng đầu vào các phiên doc-1 ba lần. Mỗi lần khoảng 78 lời × (11,5k token vào, 0,7k token ra), tức 0,31 USD;
   ba lần khoảng 0,93 USD. Nếu nhiễu lớn thì cân nhắc đồng thuận nhiều lượt cho các cặp trục
   ([self-consistency, Wang et al. 2023](https://arxiv.org/abs/2203.11171)). Văn liệu cho biết LLM chạy "tất định" vẫn dao động độ chính xác tới 15% giữa
   các lượt ([Atil et al. 2024](https://arxiv.org/abs/2408.04667)).
2. **Thí nghiệm bỏ `previous_edges_in_chapter`:** đầu vào phiên không còn phụ thuộc thứ tự xếp phiên, và mọi phiên chạy song song được (mục 4.3).
3. **Hai khái niệm cùng câu neo là dấu hiệu chất lượng neo**, vì cửa sổ định nghĩa của cả hai giống hệt nhau. Nên đếm hiện tượng này trong nghiệm thu
   neo, thay vì sửa ở A8.

Văn liệu dùng thứ tự trong giáo trình làm tín hiệu chiều tiên quyết: RefD ([Liang et al. 2015](https://aclanthology.org/D15-1193/)),
[Pan et al. 2017](https://aclanthology.org/P17-1133/), [Pal et al. 2020](https://arxiv.org/abs/2011.10337). Trên dữ liệu này, thứ tự sách (LC) không
giúp được gì, vì pass phụ ML đã tuân thứ tự sách.

## 6. Kế hoạch đổi mặc định

Các bước sắp theo thứ tự làm. Mỗi bước ghi người làm, chi phí và rủi ro.

**Bước 1. Gom các sửa đổi làm đổi khoá cache canonical vào một spec "đổi mặc định chuỗi gộp", làm trước khi dựng lại artifact.**
- **Nội dung:** khuyến nghị 1–6 ở mục 7: bỏ `same_evidence`, không phán sửa cạnh cắt chỉ có `ngram`, giải mâu thuẫn bảo thủ, buộc gộp chung tên sau
  chuẩn hoá, Louvain tất định, `coextensive_with` vào R2.
- **Vì sao trước:** mỗi sửa đổi đổi config canonical. Làm sau khi dựng lại thì phải dựng hai lần.
- **Người làm, chi phí:** nhân viên, 0 USD, test bằng mô hình giả.
- **Rủi ro:** gộp nhiều thay đổi trong một lượt nghiệm thu thì khó quy công từng cái. Bù lại, mỗi thay đổi đã có mô phỏng 0 USD riêng (mục 2, 3).

**Bước 2. Cấu hình mặc định và CLI.**
- **Cấu hình:**
  - `upstream_chain`: `v3` → `gop` (`config.py:49`);
  - `anchor_batch_mode`: `a5` → `single` (`config.py:50`), và cả mặc định của hàm dựng `Canonicalize` (`canonicalize.py:28`);
  - cập nhật `.env.example:34-35`;
  - `merge_description_enabled=false` và `canonical_repair_batch_size=1` đã đúng (`config.py:43,48`).
- **Sửa CLI bắt buộc:**
  - Hiện `a4 --names-only` / `--prepare` dừng hẳn khi chuỗi mặc định là `gop` (`presentation/cli/main.py:561-563`).
  - D-01 gọi đúng lệnh này (`scripts/pass-phu-ml/chay_d01.py:211`).
  - Phải cho `--names-only` / `--prepare` tự dùng `v3` khi không có `--upstream-chain` tường minh, kèm test.
- **Rủi ro:**
  - Lệnh `roadmap` chọn chuỗi theo canonical mới nhất (`application/graph_chain.py:5-6`). Chạy `a4` mặc định trên tài liệu cũ sẽ đổi chuỗi của lần
    `roadmap` sau. Đây là hành vi đúng, nhưng phải ghi vào README.
  - Băm config v3 không đổi (vé 17b), nên artifact v3 cũ vẫn tái dùng được khi gọi tường minh.

**Bước 3. Dựng lại artifact của 6 tài liệu phát triển và nghiệm thu một lượt.**
- **Phạm vi:** canonical `gop` neo "một khái niệm" cho doc-1, xstk, doc-4, nhap-mon-ml, naive-bayes, doc-6, cùng chuỗi đồ thị cho 3 tài liệu có vàng.
- **Chi phí ước:**
  - canonical lạnh khoảng 2,0 USD; theo q6, doc-4 khoảng 1,0–1,2 USD sau bước 1;
  - pass chính khoảng 2,9 USD (doc-4 khoảng 2,2; doc-1 khoảng 0,31; xstk khoảng 0,19);
  - tổng khoảng 5 USD, cần chủ dự án duyệt.
- **Mẹo tiết kiệm:** chạy trong kho riêng có sẵn canonical chuỗi gộp làm "lượt trước", để tái dùng lời gọi theo `input_hash`, rồi mới chép sang kho
  chính.
- **Rủi ro:**
  - E4 một lượt nhiễu khoảng ±0,15 (mục 5). So với pha A và lượt cuối của 17i, đừng so với một con số đơn.
  - Đo thời gian thật ở bước này, kèm `measure_phase` mới (khuyến nghị 7).

**Bước 4. T-01 trên chuỗi gộp.**
- **Cách làm:**
  - dựng canonical `gop` cho hai cuốn giữ lại;
  - chấm bằng `a8-roadmap-score --remap-gold-ids` (`main.py:119`);
  - nếu vàng gán trên graph provenance đã vá, chấm `a8-score --remap-gold-ids --gold-graph` (`main.py:107-110`).
- **Rủi ro:**
  - **Giữ mù tập giữ lại:**
    - nhân viên không được thấy;
    - script kiểm chỉ in trường số trong allowlist;
    - test phải dùng bí mật giả.
    Bài học từ T-01a: một checker in stats đã làm d01-t01 mất mù.
  - Bộ chấm từ chối bộ vàng có khái niệm không quy được (vé 17h). Theo chủ dự án, bộ đó để riêng và dựng chỉ số lại sau.
  - Không còn chờ T-01 để đổi mặc định, nên T-01 là số báo cáo, không phải cổng chặn.

**Bước 5. Đo lại E5 (ADR 0015).**
- **Vì sao:**
  - Đặc trưng lệch phân bố, vì chunk neo thay chunk do provenance vá.
  - Mô hình học trên D-01, mà D-01 chạy chuỗi v3 lớp tên.
  - Pass phụ ML trên doc-4 chậm bất thường (592 giây, mục 4.3).
- **Cách làm:**
  - **0 USD:** E4 của pass phụ trên ba graph gộp đã có (doc-1 v12, xstk v12, doc-4 v4) so với mốc 18d. 17i đã cho thấy không tụt quá nhiễu.
  - **Trả phí:** đo E5 đúng nghĩa trên nhãn D-01 đòi canonical `gop` đầy đủ cho các cuốn D-01, vì chuỗi gộp không có lớp tên. Ước vài USD mỗi cuốn,
    tổng dễ vượt 10 USD.
- **Đề xuất:**
  - chỉ làm bản trả phí khi E4 của bước 3 tụt;
  - học lại là vé riêng: chỉ đổi tệp mô hình và phiên bản, như ADR 0015 quy định.

**Bước 6. Quyết số phận D-01 trước khi gỡ stage cũ.**
- D-01 dựng dữ liệu bằng `a4 --names-only`, rồi `roadmap --stop-after identity` (`chay_d01.py:211,217`). Luồng này cần cả ba stage provenance, teaching
  và identity.
- **Lựa chọn:**
  - (a) đóng băng D-01: không thêm cuốn mới, rồi gỡ stage;
  - (b) giữ ba stage cho riêng đường lớp tên;
  - (c) dựng đường lớp tên cho chuỗi gộp. Cách này tốn thiết kế.
- **Đề xuất:** (a) nếu chủ dự án không định mở rộng D-01, còn không thì (b).
- **Rủi ro:** gỡ stage trước khi quyết thì D-01 gãy âm thầm. Lệnh `roadmap` sẽ báo stage không tồn tại giữa một lượt chạy dài.

**Bước 7. Tài liệu.**
- **ADR 0016:** danh tính là một phần của gộp ở A4; neo và trạng thái dạy quyết ở stage canonical; provenance rời chuỗi; neo "một khái niệm" là mặc định,
  và vì sao bỏ chế độ a5 (doc-4: 67 khái niệm từ "chỉ nhắc" thành "được dạy", 17i mục 7).
- **ADR 0004:** ghi rằng vector mô tả nháp chỉ còn là tuỳ chọn để đo, mặc định tắt.
- **`CONTEXT.md`:** "Cặp nghi trùng" (nguồn đề cử sau bước 1), "Xác minh danh tính" thành xác minh gộp khác tên ở A4, "Bản đồ danh tính" chỉ còn ở artifact
  v3, thêm "Câu neo" và "Trạng thái dạy".
- **`doc/spec-addendum.md`:** sơ đồ pha A và các mục A4, A5, A9', A9'' trỏ sang spec gộp khâu.
- **Spec gộp khâu:** sửa dòng "Lịch" (`doc/gop-khau-truoc-a8-spec.md:9-11`, "tắt mặc định… chờ T-01") theo quyết định mới.
- **Rủi ro:** thấp. Làm cùng commit với bước 2, để tài liệu không nói ngược mã.

**Bước 8. Vé gỡ ba stage cũ và đường A4 cũ**, sau bước 6.
- **Gỡ:**
  - `BuildProvenance`, `AnchorConcepts` (stage `teaching`), `JudgeIdentity`, nhánh `CanonicalReasoning.execute` v3;
  - các giá trị `--stop-after provenance|teaching|identity`, cờ `--identity-review`.
- **Phải giữ, vì mã khác đang dùng:**
  - `domain/provenance.quote_is_verbatim`, Pha B dùng (`application/phase_b/common.py:12`);
  - `judge_identity.VERIFY_SCHEMA` và `load_identity_review`, canonical dùng (`canonicalize.py:23`, `canonical_merge_verify.py:6`, `main.py:574`).
    Chuyển sang module trung tính trước khi xoá `judge_identity`;
  - `domain/identity.py`, dùng bởi `canonical_nominations.py:5`, `canonical_review.py:6`, `implicit.py:3`;
  - `application/anchor_core.py`, phần neo của canonical dùng.
- **Hợp đồng đọc artifact cũ** (spec mục 6): A8, A10, bộ chấm và Pha B vẫn phải đọc được artifact v3 có `identity_map`.
- **Rủi ro:** xoá nhầm hàm dùng chung. Test cần có: import toàn bộ gói sau khi gỡ, và một artifact v3 trong fixture vẫn chấm được.

**Bước 9. Kiểm tương thích Pha B, làm song song từ bước 3.**
- **Đã thử, 0 USD, chỉ đọc:** `load_learning_graph` (`application/phase_b/retrieval.py:98-130`) nạp được graph `stages` chuỗi gộp của doc-1 (v16, 32 module),
  xstk (v16, 13 module) và doc-4 (v8, 97 module). Node có `anchor` và `teaching_chunk_ids` đúng dạng mà bài giảng đọc (`phase_b/lectures.py:116-166`).
- **Rủi ro còn lại:**
  - bài giảng và quiz cache theo graph và ngữ cảnh, nên graph mới làm cache Pha B cũ mất hiệu lực; tiền LLM phát sinh lúc người dùng bấm;
  - id node đổi theo bảng chuyển hướng, nên tiến độ hay ghi chú nào lưu theo id node cũ cần quy qua `redirects`.
- **Đề xuất:** thêm một test tích hợp nạp graph chuỗi gộp qua bộ nạp Pha B, vì test 17c chỉ phủ A10 và bộ chấm.

## 7. Khuyến nghị xếp theo ưu tiên

**A. Gom vào spec "đổi mặc định chuỗi gộp"** (bước 1–2). Mọi mục đều đổi khoá cache canonical, nên phải làm trước khi dựng lại artifact.

| # | Khuyến nghị | Lợi ước tính | Rủi ro chất lượng | Thí nghiệm trả phí |
|---|---|---|---|---|
| 1 | Bỏ nguồn đề cử `same_evidence` | doc-4: −112 lời sửa, −0,10 USD, cạnh cắt −32% | 0 gộp mất trên 13 canonical | nằm trong lượt bước 3 |
| 2 | Không phán sửa cạnh cắt chỉ có `ngram`, vẫn dùng để chia cụm | doc-4: −116 lời, −0,093 USD; doc-1: −38 lời | 0 gộp mất ở cấu hình mặc định | như trên |
| 3 | Giải mâu thuẫn bắc cầu, biến thể bảo thủ: giữ cặp chung tên sau chuẩn hoá | +1–2 gộp đúng mỗi tài liệu, 0 USD | 0 gộp sai trong mô phỏng; biến thể tham lam kéo lại 1 gộp sai đã biết | như trên |
| 4 | Chung **tên** sau chuẩn hoá thì buộc gộp | +4 gộp đúng (χ² ×2, Gram-Schmidt, Véctơ tọa độ) | chưa thấy ca sai | như trên |
| 5 | Chia cụm A4 tất định: đổi id sang số nguyên đã sắp trước khi chạy Louvain | tái dùng cache ổn định, bớt nhiễu gộp | không | không |
| 6 | Thêm `coextensive_with` vào nhãn R2 chuỗi gộp | nhỏ | không | không |
| 7 | Luật neo L8b (tuỳ chọn trong spec) | −8 đến −18% lời neo; doc-4 −91 lời, −0,065 USD | quá tay khoảng 3% trên D-01 | không |
| — | Cấu hình mặc định, sửa CLI `--names-only`, tài liệu (bước 2, 7) | — | D-01 gãy nếu thiếu sửa CLI | — |

**B. Vé riêng.** Không đổi khoá cache, làm song song.

| # | Khuyến nghị | Lợi ước tính | Rủi ro | Thí nghiệm trả phí |
|---|---|---|---|---|
| 8 | `prepare_anchors` chuẩn hoá chunk một lần; thêm `measure_phase` cho các đoạn CPU; ghi `stats` cho `module_titles` | doc-4: bớt ít nhất 140 trong 198 giây; số đo đủ | không; test kiểm ứng viên giống hệt | không |
| 9 | Nâng `canonical_concurrency` lên khoảng 16; bỏ rào `NODE_BATCH` ở đường canonical; xoá `vertex_concurrency` | phần LLM canonical doc-4 có thể từ khoảng 540 giây còn khoảng 140 giây (ước) | 429 khi vượt TPM, đã có bộ giới hạn | đo trong lượt bước 3 |
| 10 | Stage mentions: tính `dense_mentions` bằng numpy, chạy `exact_mentions` một lần, không embed lại tên đã embed ở clusters | doc-4: phần lớn trong 400 giây | test kiểm mention map giống hệt | không |
| 11 | Profile pass phụ ML trên doc-4 (592 giây so với 18 giây ở d01-02) | có thể vài phút mỗi cuốn | không | không |
| 12 | Vé gỡ ba stage cũ (bước 8), sau khi quyết D-01 (bước 6) | mã gọn | xoá nhầm hàm dùng chung | không |
| 13 | Test tích hợp Pha B với graph chuỗi gộp (bước 9) | bắt lỗi tương thích | không | không |

**C. Nghiên cứu, thí nghiệm trả phí.** Cần chủ dự án duyệt.

| # | Thí nghiệm | Lợi kỳ vọng | Chi ước |
|---|---|---|---|
| 14 | Bỏ `previous_edges_in_chapter` ở pass chính để mọi phiên chạy song song | doc-4: pass chính từ 13,7 phút còn vài phút; bớt nhiễu do thứ tự | doc-1 + xstk khoảng 0,55 USD; thêm doc-4 khoảng 2,2 USD |
| 15 | Phát lại phiên pass chính với đầu vào cố định, đo nhiễu thuần mô hình | biết E4 nhiễu bao nhiêu, quyết bằng số | khoảng 0,93 USD |
| 16 | Xác minh mù cho cặp `subtype_of` | có thể phục hồi một số cặp như Tự đồng cấu | dưới 0,2 USD; rủi ro gộp sai cao, ưu tiên thấp |

**Không nên làm:**
- luật chống lật chiều LA–LE (mục 5.2);
- luật ký hiệu trong câu bằng chứng (mục 3.3);
- ngưỡng cosine cho cạnh name (mục 2);
- bật lại đề cử theo mô tả;
- gom lô lời phán sửa.

**Tác động gộp của nhóm A (ước tính), doc-4, cấu hình mặc định:**
- trước A8 khoảng 1.230 lời và khoảng 1,0 USD, so với ước khoảng 1.550 lời và 1,26 USD của neo "một khái niệm" chưa sửa (17i mục 7), và 2.295 lời,
  1,367 USD của chuỗi v3;
- cộng nhóm B, canonical doc-4 có thể còn khoảng 4–6 phút, so với 14,7 phút. Cần đo ở bước 3.

## 8. Văn liệu về gom lô và phán thực thể

- **Gom lô theo câu giống nhau cho độ chính xác kém nhất,** vì mô hình trả lời giống nhau cho nhiều câu. Gom theo câu khác nhau thì tốt nhất. Tiền bớt
  được 4–7 lần đến từ phần minh hoạ dùng chung ([BatchER, Fan et al., ICDE 2024](https://arxiv.org/abs/2312.03987)).
  - Điều này khớp với 17j: lô phán sửa gồm các cặp giống nhau. Vì đầu vào riêng của từng mục chiếm phần lớn token, gom lô gần như không bớt tiền.
  - Xem thêm [Cheng et al. 2023](https://arxiv.org/abs/2301.08721).
- **Phân cụm trong ngữ cảnh tốt nhất ở cỡ tập ≤ 9 bản ghi,** quá cỡ đó thì tụt. Có thêm bước chặn cụm sai
  ([LLM-CER, Fu et al. 2025](https://arxiv.org/abs/2506.02509)). Trần cụm A4 hiện là 9.
- **Cho mô hình thấy các bản ghi cùng lúc ("select")** tốt hơn phán từng cặp, nhưng có thiên lệch vị trí
  ([Wang et al., COLING 2025](https://arxiv.org/abs/2405.16884)).
- **Không có prompt tốt nhất chung cho mọi mô hình và bộ dữ liệu** ([Peeters et al., EDBT 2025](https://arxiv.org/abs/2310.11244)). Điều này khớp với
  việc prompt sửa ở 17i gộp lại được cặp đúng nhưng kéo về gộp sai.
- **Chọn câu hỏi để giảm bất định của phân hoạch** ([Li et al. 2024](https://arxiv.org/abs/2401.03426)) và **suy cặp nhờ tính bắc cầu**
  ([Wang et al., SIGMOD 2013](https://arxiv.org/abs/1408.6916)): cơ sở cho khuyến nghị 3.

## 9. Script và tệp kết quả

Tất cả nằm ở `tmp/nghien-cuu-chuoi-gop/`. Chạy từ gốc repo bằng `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <script>`.

**Hàm dùng chung:** `chung.py` (danh sách phiên bản, giá tiền, quy đích vàng).

**Câu hỏi 1:**
- `q1_luat_neo.py` → `ket-qua/q1-luat-neo.json`;
- `q1b_luat_chat.py` → `ket-qua/q1b-luat-chat.json`;
- `q1c_luat_duy_nhat.py` → `ket-qua/q1c-luat-duy-nhat.json`;
- `q1d_l8_khong_hai_cham.py` → `ket-qua/q1d-l8b.json`;
- `q1e_kiem_l8b_d01.py` → `ket-qua/q1e-l8b-d01.json`.

**Câu hỏi 2:**
- `q2_nguon_de_cu.py` → `ket-qua/q2-nguon-de-cu.json`;
- `q2b_tai_lap_cum.py` → in ra màn hình; chạy với nhiều `PYTHONHASHSEED`;
- `q2c_nguong_ten.py` → in ra màn hình;
- `q2d_gop_theo_nguon.py` → `ket-qua/q2d-gop-mot-nguon.json`.

**Câu hỏi 3:**
- `q3_tra_nhom.py` → `ket-qua/q3-nhom.json`;
- `q3_cap_dong_nghia.py` → `ket-qua/q3-cap.json`;
- `q3b_xung_dot.py` → `ket-qua/q3b-xung-dot.json`;
- `q3c_ten_chua_nhau.py` → `ket-qua/q3c-ten-chua-nhau.json`;
- `q3d_ten_chuan_hoa_quan_he.py` → `ket-qua/q3d.json`;
- `q3e_luat_ky_hieu.py` → `ket-qua/q3e-ky-hieu.json`.

**Câu hỏi 4:**
- `q4_do_cpu.py <doc> <v>` → `ket-qua/q4-cpu-<doc>.json`;
- bảng 4.3 đọc trực tiếp manifest graph.

**Câu hỏi 5:**
- `q5_nhieu_pass_chinh.py` → `ket-qua/q5-nhieu.json`;
- `q5b_phien_trung.py` → `ket-qua/q5b-phien.json`;
- `q5c_chong_lat_chieu.py` → `ket-qua/q5c-chong-lat-chieu.json`.

**Chi phí lạnh:** `q6_chi_phi_lanh.py` → `ket-qua/q6-chi-phi-lanh.json`.
- Lưu ý: với canonical neo a5, cột `anchor` đếm thừa, vì `anchor_decision_log` mang hàng của lượt trước. Phần neo nên lấy theo `cost_summary`, như 17i.

## 10. Quyết định sau đợt soát (grill) với chủ dự án, 2026-10-17

Chủ dự án đã xác nhận toàn bộ các điểm dưới đây.

1. **Spec "đổi mặc định chuỗi gộp"** gồm:
   - **sửa A4** (khuyến nghị 1–6): bỏ `same_evidence`; không phán sửa cạnh cắt chỉ có `ngram`; giải mâu thuẫn bắc cầu theo biến thể bảo thủ;
     chung tên sau chuẩn hoá thì buộc gộp; chia cụm A4 tất định; `coextensive_with` vào R2;
   - **cấu hình mặc định:** chuỗi gộp, neo "một khái niệm";
   - **sửa CLI:** `--names-only` tự dùng chuỗi v3;
   - **tài liệu:** ADR 0016, ADR 0004, `CONTEXT.md`, spec-addendum.

   **Không** đưa L8b vào; L8b để làm nghiên cứu sau.
2. **Vé tăng tốc, làm song song và trước lượt dựng lại** (khuyến nghị 8–11). Lượt dựng lại sẽ cho số phút/cuốn chuẩn.
3. **Thí nghiệm của Claude, làm trước lượt dựng lại:**
   - (15) phát lại phiên pass chính để đo nhiễu; dải nhiễu đo được là ngưỡng E4 của cổng;
   - (14) bỏ `previous_edges_in_chapter`, trên doc-1 và xstk trước; nhận thì đưa vào spec.
4. **Cổng kiêm dựng lại artifact:** 6 tài liệu phát triển. Tiêu chí:
   - neo ở đích vàng không kém 17i;
   - gộp sai mà vàng phát hiện không quá 3;
   - E4 trong dải nhiễu;
   - chi phí và lời gọi trước A8 không vượt mức ước.

   Luật khi trượt:
   - trượt về chất lượng thì chưa bật, sửa rồi chạy lại phần hỏng;
   - E4 lệch mà vẫn trong dải nhiễu thì coi là qua;
   - vượt tiền hay thời gian mà chất lượng đạt thì vẫn bật, và mở vé tối ưu.

   **Trần 10 USD** cho cả đợt, dry-run trước mỗi lượt có chi.
5. **Sau cổng:**
   - bật mặc định cùng commit với tài liệu;
   - **ngay sau đó**, một vé riêng gỡ ba stage cũ, nhánh v3 của A4, và ba tuỳ chọn thua (neo gom A5, đề cử theo mô tả, gom lô lời phán sửa);
   - giữ khả năng đọc artifact v3 cũ.
6. **Các mục khác:**
   - **D-01:** đóng băng, không thêm cuốn mới.
   - **E5:** chỉ đo bản 0 USD trong lượt dựng lại; học lại khi tụt rõ.
   - **Pha B:** chấp nhận mất cache bài giảng và quiz; thêm test tích hợp nạp đồ thị chuỗi gộp; báo phiên Pha B qua tệp bàn giao.
7. **T-01:** chờ có vàng rồi mới dựng canonical chuỗi gộp cho hai cuốn giữ lại; giữ mù theo allowlist. T-01 là số báo cáo, không phải cổng.
