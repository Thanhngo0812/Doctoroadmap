# Nghiên cứu cải thiện chuỗi gộp (2026-10-16)

**Trạng thái: DỞ DANG.** Lượt này dừng sớm theo yêu cầu của chủ dự án, vì sắp hết usage. Câu hỏi 1, 2, 3 đã có số. Câu hỏi 4 và 5 có số một phần.
Câu hỏi 6 mới là phác thảo. Mỗi mục ghi rõ chỗ **CHƯA XONG** và bước kế tiếp.

**Phạm vi:**
- **Chi:** 0 USD. Không gọi mô hình, không chạy `a4` hay `roadmap`.
- **Dữ liệu:** chỉ đọc kho `tmp/v4-17i/artifacts`, cùng các mốc v3 ở `artifacts/`.
- **Mã mới:** script và kết quả nằm ở `tmp/nghien-cuu-chuoi-gop/`, liệt kê ở mục 8.

## 1. Bớt lời gọi neo bằng luật tất định

**Cách đo** (`q1_luat_neo.py`, `q1b_luat_chat.py`, `q1c_luat_duy_nhat.py`):
- **Dữ liệu:** 6 canonical có neo "một khái niệm": doc-1 v6, xstk v8, doc-4 v2, nhap-mon-ml v9, naive-bayes v9, doc-6 v3.
- **Ứng viên:** mỗi khái niệm đã hỏi LLM được lấy đúng danh sách ứng viên mà LLM đã thấy, tức hàng cuối của nó trong `anchor_decision_log`.
- **Hạng 0:** tính lại theo đúng luật ở `src/doc2roadmap/domain/anchors.py:160-161`.
- **Mốc so:** lời phán cuối, sau xác minh, lấy ở `anchor_log` và `teaching_status`.

**Nền:**
- Có 1.036 khái niệm được hỏi.
- Ứng viên đầu `k1` là câu bằng chứng A3 (hạng 0) ở 1.011 khái niệm (97,6%).
- Vì gần như khái niệm nào cũng có câu hạng 0, riêng điều kiện "có hạng 0" không phân biệt được gì.
- LLM phán: `taught` 855, `mentioned_only` 177, `not_subject_matter` 2, `uncertain` 2.

| Luật (đều đặt neo = k1, trạng thái = được dạy) | Luật quyết | LLM cũng "được dạy" | Cùng câu neo (khi LLM "được dạy") | Quá tay | USD neo bớt (lạnh) |
|---|---|---|---|---|---|
| L1: k1 hạng 0 | 1.011 | 841 | 707 | **170 (16,8%)** | 0,639 |
| L2: L1 + tên nằm trong câu | 879 | 724 | 617 | 155 | 0,563 |
| L3: L2 + từ định nghĩa ("được gọi là", "là một", "ký hiệu"…) | 362 | 326 | 307 | 36 (33 ở doc-4) | 0,237 |
| L6: k1 hạng 0 + tên đứng ở vị trí được định nghĩa | 245 | 241 | 234 | 4 | 0,159 |
| **L8: L6 + chỉ một ứng viên ở vị trí định nghĩa** | **204 (19,7%)** | **201** | **198 (98,5%)** | **3 (1,5%)** | **0,130** |

Nguồn: `tmp/nghien-cuu-chuoi-gop/ket-qua/q1-luat-neo.json`, `q1b-luat-chat.json`, `q1c-luat-duy-nhat.json`.

**"Tên ở vị trí được định nghĩa"** (L6) gồm hai dạng:
- câu, sau khi bỏ đầu "Định nghĩa n.", bắt đầu bằng tên rồi tới "là" hoặc "được…";
- tên đứng ngay sau "được gọi là", "gọi là", "ta gọi", "được định nghĩa là".

**L8 theo tài liệu:**

| Tài liệu | L8 quyết / được hỏi | Quá tay |
|---|---|---|
| doc-1 | 68/211 | 0 |
| xstk | 23/79 | 0 |
| doc-4 | 91/626 | 0 |
| nhap-mon-ml | 18/62 | 1 |
| naive-bayes | 4/36 | 2 |
| doc-6 | 0/22 | 0 |

**Ba ca quá tay** ("Evaluation:", "Bảng từ vựng:", "Quá trình học:") đều là dạng "Tên: …" ở đầu dòng gạch đầu dòng. Bỏ dấu `:` khỏi mẫu thì
có lẽ hết cả ba. Đây là suy đoán, chưa chạy lại.

**Đích vàng:**
- L8 quyết 37/90 đích được hỏi. Câu neo trùng câu neo v3 ở 35/37 (theo phán của Claude, 79/84 câu neo v3 là đúng).
- Hai chỗ lệch:
  - "Không gian véc tơ phức": v3 không có neo;
  - "Sự đấu tranh của các mặt đối lập": neo của luật là một câu định nghĩa, nên có lẽ còn tốt hơn neo v3.
- L8 không quyết đích nào trong 5 neo mà Claude nghi ngờ (`report/quy-loi-thuong-nguon-a8-2026-10-12.md:117-127`).

**L3 hỏng ở văn bản triết (doc-4):**
- Câu liệt kê như "chín trường phái … là: Nho gia, Mặc gia, …" kéo theo 33 khái niệm vốn chỉ được nhắc.
- "Chất" thì k1 là câu vật lý ("Chất là cái gián đoạn…"), còn LLM chọn đúng câu triết học.
- Vì vậy chỉ nên dùng L8, vì L8 bỏ qua các ca có từ hai câu định nghĩa trở lên.

**Tác động** (neo "một khái niệm", đề xuất của 17i mục 8):
- L8 bớt 20% số lời gọi neo, khoảng 0,13 USD trên 6 tài liệu. Riêng doc-4 bớt 91 lời và 0,065 USD.
- Nền doc-4: neo "một khái niệm" cộng mô tả và kiểm mô tả tốn khoảng 0,684 USD lạnh. Chế độ a5 tốn 0,664 USD (cost_summary của doc-4 v3).
- Có L8 thì chế độ "một khái niệm" xuống khoảng 0,62 USD, rẻ hơn a5, mà giữ được độ chặt của C8.
- Nguồn: `ket-qua/q6-chi-phi-lanh.json` và manifest `canonical/doc-4/v2`, `v3`.

## 2. Hiệu suất từng nguồn đề cử

**Cách đo** (`q2_nguon_de_cu.py`): dùng `nominations.edges`, `cut_edges` và `nomination_pair` của cả 13 canonical chuỗi gộp.
- **Chi phí phán sửa:** lấy từ `usage` của các hàng `repair`, chia đều cho các cạnh cắt mà lời đó phủ.
- **Mô phỏng bỏ nguồn:**
  - (a) xoá cạnh chỉ có nguồn đó, rồi chia cụm lại bằng đúng thủ tục Louvain của `domain/nomination.py:221-229`;
  - (b) giữ cạnh để chia cụm, nhưng không phán sửa cạnh cắt chỉ có nguồn đó.

**Cấu hình mặc định, không đề cử theo mô tả, doc-4 v3** (867 cạnh, 482 cạnh cắt, 467 lời phán sửa, 0,375 USD lạnh):

| Nguồn | Cặp | Chỉ nguồn này | Cắt chỉ nguồn này | Gộp | Gộp chỉ nhờ nguồn này | USD phán sửa chỉ nguồn này |
|---|---|---|---|---|---|---|
| name | 510 | 347 | 148 | 41 | 11 (5 qua phán sửa) | 0,109 |
| ngram | 312 | 160 | 116 | 29 | 1 (trong cụm, "Mối liên hệ = Liên hệ") | 0,093 |
| same_evidence | 207 | 153 | 112 | **0** | 0 | **0,102** |
| alias / shared_name_or_alias | 18 | 0 | 0 | 11 | 0 | 0 |

**doc-1 v6:**
- same_evidence: 22 cặp, 0 gộp, 11 lời phán sửa chỉ nguồn này, 0,008 USD.
- ngram chỉ nguồn này: 38 lời, 0,026 USD, 0 gộp.
- name chỉ nguồn này: 47 lời, 0,034 USD, 1 gộp (KerT = Kerf).

**xstk v9:**
- same_evidence: 15 cặp, 0 gộp nhờ riêng nó.
- name chỉ nguồn này cho 1 gộp qua phán sửa, và đó là gộp **sai** đã biết "Độ tin cậy = Độ tin cậy của ước lượng".

Nguồn: `ket-qua/q2-nguon-de-cu.json`, `q2d-gop-mot-nguon.json`.

**Phát hiện:**
- **same_evidence chưa từng tự mình tạo ra gộp nào trong 13 canonical.** Bỏ nó (mô phỏng a) mất 0 gộp ở mọi tài liệu. Trên doc-4 v3, số cạnh cắt
  giảm từ 482 còn 328 (−32%).
- **Cạnh cắt chỉ có ngram:** bỏ phán sửa (mô phỏng b) mất 0 gộp ở mọi cấu hình mặc định, và bớt 116 lời, 0,093 USD trên doc-4 v3.
- **Phải giữ name.** Bỏ nó (a) mất 7 gộp trên doc-4 v3, 6 trên doc-1, 2 trên xstk.
- **Ngưỡng cosine không lọc được cạnh chỉ có name.** Trọng số là cosine của vector tên. 16/16 lần gộp qua phán sửa có cosine từ 0,891 đến 0,988.
  Gần như mọi cạnh cắt cũng có cosine ≥ 0,85 (`q2c_nguong_ten.py`).
- **Đề cử theo mô tả (đối chiếu doc-4 v2):** 1.262 cặp chỉ có nguồn này, 972 cạnh cắt chỉ nguồn này, 0,818 USD, 3 gộp. Giữ tắt như vé 17k.
- **Chia cụm A4 không tái lập được giữa hai tiến trình** (`q2b_tai_lap_cum.py`).
  - nhap-mon-ml v8 và v9 có cạnh và trọng số giống hệt nhau, nhưng số cạnh cắt đã lưu khác nhau (157 so với 156).
  - Chia lại với `PYTHONHASHSEED` từ 0 đến 3 thì khớp lúc bản này, lúc bản kia.
  - Nguyên nhân: Louvain của networkx (`domain/nomination.py:224,228`) duyệt tập id dạng chuỗi, nên kết quả phụ thuộc hash ngẫu nhiên của
    tiến trình.
  - Hệ quả: chạy lại thì cụm có thể khác, mất tái dùng cache của lời phán cụm, và thêm nhiễu cho phần gộp.

**Gộp hai đề xuất** (bỏ same_evidence, không phán sửa cạnh cắt chỉ có ngram), ước theo mô phỏng:
- doc-4: từ 467 lời phán sửa còn khoảng 239, bớt khoảng 0,19 USD trên 0,375 USD;
- doc-1: bớt khoảng 49 lời và 0,034 USD.

Đây là ước tính: chia cụm lại có thể đổi thêm cạnh cắt, và trọng số cạnh còn lại giữ như đã lưu.

## 3. Phục hồi gộp đồng nghĩa bị sót, không kéo lại gộp sai

Theo dõi từng cặp qua mọi phiên bản (`q3_cap_dong_nghia.py`, `ket-qua/q3-cap.json`).

**3.1. Mâu thuẫn bắc cầu xoá cả thành phần.**
- Ở `domain/canonical_decisions.py:148-166`, chỉ cần một cặp "khác" nằm trong thành phần thì **mọi** nhóm của thành phần bị tách thành đơn lẻ
  và bị hoãn (`canonical_merge.py:112-114`).
- Mỗi tài liệu có 2–3 thành phần như vậy, chứa 6–9 nhóm. Nhiều cặp trong đó đã được phán cùng **và** xác minh `dong_nhat`.

Mô phỏng cách giải "tham lam có ràng buộc" (`q3b_xung_dot.py`):
- nối các cặp cùng theo thứ tự độ tin: chung tên sau chuẩn hoá, rồi xác minh `dong_nhat`, rồi số lời phán cùng;
- bỏ một phép nối nếu nó gom hai đầu của một cặp "khác".

| Tài liệu | Gộp phục hồi | Đánh giá |
|---|---|---|
| doc-1 v6 | Imf = Ảnh; Quá trình Gram - Schmidt = Quá trình Gram-Schmidt | đúng |
| xstk v9 | Độ chính xác = Độ chính xác ε; Xác định kích thước mẫu = … trong ước lượng trung bình | 1 đúng, **1 sai đã biết** |
| doc-4 v3 | Hoài nghi luận = Thuyết hoài nghi; Nhận thức luận = Lý luận nhận thức; CN duy vật biện chứng = Triết học duy vật biện chứng | 2 cặp nằm trong danh sách sót của 17i; cặp thứ ba có lẽ đúng |

Biến thể bảo thủ: trong thành phần mâu thuẫn, chỉ giữ cặp chung tên sau chuẩn hoá. Cách này phục hồi 2 cặp đúng của doc-1 (Imf = Ảnh, Gram-Schmidt) và
0 cặp sai.

**3.2. Cặp chung tên sau chuẩn hoá (`normalized_name`) bị mô hình tách.**
- Trên 6 tài liệu mặc định có 5 cặp như vậy, và 4 cặp không được gộp:
  - χα 2 = χα^2, χ0 2 = χ0^2: lời phán sửa đầu trượt kiểm "lặp nhóm", lời sửa lại thì tách;
  - Gram - Schmidt = Gram-Schmidt: hoãn vì mâu thuẫn;
  - Véc tơ tọa độ = Véctơ tọa độ: phán khác.
- Cả 4 cặp đều chỉ khác nhau về cách viết.
- Luật "chung tên sau chuẩn hoá thì buộc gộp", chỉ áp cho **tên**, không áp cho alias, cho thêm 4 gộp đúng và 0 gộp sai.
- Không mở rộng sang alias: 9 cặp chung alias bị tách đa số do alias A3 sai, ví dụ "Kết cấu" / "Phương thức liên kết", "Khoa học" / "Ý thức
  khoa học" (`ket-qua/q3d.json`).

**3.3. Các hướng không nên làm, hoặc chưa đủ bằng chứng:**
- **Luật ký hiệu trong câu bằng chứng** ("ký hiệu", ngoặc đơn, "còn gọi là"): không ra cặp đúng nào mới. Cặp "ký hiệu là tên" đều đã được đề cử, còn
  "chung ký hiệu" chỉ ra rác ở xstk (`q3e_luat_ky_hieu.py`).
- **Imf = Ảnh của ánh xạ tuyến tính:** không được đề cử ở phiên bản nào. **Tự đồng cấu = Toán tử tuyến tính** và **Bao tuyến tính = Không gian
  con sinh bởi…** chỉ được đề cử nhờ mô tả, và bị phán `subtype_of` hoặc `coextensive_with`.
- **`coextensive_with` không có trong danh sách nhãn đồng nhất của R2 chuỗi gộp** (`canonical_decisions.py:21-24`), nên "Bao tuyến tính" lọt qua
  như một quan hệ đề xuất. Nên thêm nhãn này. Lợi nhỏ, vì nguồn mô tả đã tắt.
- **Đưa mọi `subtype_of` sang xác minh mù: rủi ro.**
  - Số quan hệ `subtype_of` mà bộ phán ghi: doc-1 71, xstk 33, doc-4 223.
  - Bộ xác minh đã từng cho `dong_nhat` với Tọa độ = Véc tơ tọa độ (doc-1 v5), và với cả 3 gộp sai đã biết của xstk.
  - Chi để đo trước: khoảng 330 lời, dưới 0,2 USD.
- **Chặn tên có cụm hạn định ("… của X", "… trong X", "… tổng quát")** khi tên ngắn nằm trọn trong tên dài.
  - Trong các gộp mặc định có 4 ca: 2 sai đã biết (Độ tin cậy; Tỉ lệ mẫu tổng quát) và 2 chưa rõ ở doc-4.
  - Nguồn: `ket-qua/q3c-ten-chua-nhau.json`.
  - Tuỳ chọn, ưu tiên thấp.

## 4. Thời gian

**Vì sao `phase_measurements` "ra 0".** Số đo không hỏng mà lệch theo cách đo:
1. **Ở chế độ a5,** lời mô tả và lời kiểm gộp với neo được đo dưới tên `anchor` (`canonical_describe.py:46`; chi phí ở :57-59). Vì vậy
   `describe` ≈ 0 và không có khoá `check`.
2. **Phần tái dùng chỉ đo thời gian tra cache.** Ví dụ ở doc-1 v7, `merge` mất 0,006 giây.
3. **Nhiều đoạn CPU nằm ngoài mọi `measure_phase`:**
   - `build_nodes` (`canonicalize.py:139`);
   - đề cử và chia cụm (`:155-159`);
   - `prepare_anchors` (`:173`);
   - remap và ghi.

| Canonical | Thời gian stage (giây) | Tổng các phần (giây) | Không đo được |
|---|---|---|---|
| doc-4 v3 | 877 | 480 | **397 (45%)** |
| doc-4 v2 | 1.634 | 1.271 | 363 |
| doc-1 v6 | 130 | 101 | 29 |

**Đo CPU tại máy** (0 USD, `q4_do_cpu.py`):
- doc-1: `prepare_anchors` 33,0 giây, trong đó `exact_mentions` gọi từng node 26,9 giây. Gọi một lần cho mọi node chỉ mất 5,5 giây. `build_nodes`
  3,8 giây; `nomination_graph` 3,4 giây.
- Nguyên nhân là `canonical_anchors.py:43-44` gọi `exact_mentions([node], …)` cho từng node, nên mỗi node lại chuẩn hoá toàn bộ chunk
  (`domain/mentions.py:43-44`). `heading_chunks` và `symbolic_name_chunks` cũng quét mọi chunk cho từng node (`anchor_core.py:73-76`).
- Chuẩn hoá chunk một lần là đủ, không đổi ngữ nghĩa.
- **doc-4** (630 node, 671 chunk; kết quả in ra màn hình của lượt chạy nền):

  | Đoạn | Giây |
  |---|---|
  | `prepare_anchors` | **260** |
  | `build_nodes` | 45 |
  | `nomination_graph` | 25 |
  | `additional_nominations` | 9 |

  - Bốn đoạn cộng lại khoảng 339 giây, tức phần lớn của 397 giây không đo được.
  - Đo riêng `exact_mentions`: gọi từng node mất 403 giây, gọi một lần cho mọi node mất 146 giây. Hai số này lớn hơn chính `prepare_anchors`,
    nên có lẽ máy đang tải nặng lúc đo; chỉ nên đọc là cùng bậc độ lớn.
  - Chi phí tăng theo tích số node × số chunk.

**Song song:**
- **Canonical:** `canonical_concurrency=4` (`config.py:47`, truyền vào ở `composition.py:192`), dùng cho mọi phần, kể cả neo
  (`canonicalize.py:190`).
- **Chuỗi đồ thị:** dùng `llm_max_in_flight=100` trên Vertex (`composition.py:223-224`). Bộ giới hạn thích ứng tự hạ một nửa khi gặp 429
  (`infrastructure/llm/rate_limit.py:91-98`).
- **Neo "một khái niệm":** có rào chắn sau mỗi lô `NODE_BATCH=8` (`anchor_core.py:109-128`), nên trần thực tế là 8 lời đồng thời.
- **`vertex_concurrency`** (`config.py:28`) không được đọc ở đâu cả.
- **Độ trễ mỗi lời** khoảng 1,7–2,1 giây. Ví dụ phán sửa doc-4 v2: 793 giây × 4 / 1.585 lời = 2,0 giây.
- **Đề xuất:** nâng `canonical_concurrency` lên khoảng 16 và bỏ rào `NODE_BATCH` ở đường canonical. Phần LLM của doc-4 v3 (390 giây) ước còn khoảng
  100 giây, nếu không bị giới hạn TPM. Đây là ước tính, cần một lượt đo thật.

**Pass chính bị tuần tự hoá.**
- Các phiên trong một chương chạy nối tiếp, vì mỗi phiên nhận `previous_edges_in_chapter` (`build_main_edges.py:53-65, 91-111`).
- doc-1 có làn dài nhất 28 phiên. xstk có 31 phiên trong một chương. Vì vậy pass chính mất 150–157 giây cho 50–80 lời gọi, dù trần đồng thời là 100.
- Prompt pass chính không nhắc tới trường này (`prompts/a8/main.txt`). Spec A8 tự ghi rằng đây là nguồn nhiễu (F101,
  `doc/A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md:322-327`).
- Bỏ trường này thì mọi phiên chạy song song được. Riêng doc-4, pass chính đang mất 13,7 phút (17i mục 7). Cần thí nghiệm chất lượng (mục 7).

**CHƯA XONG:** chưa lập bảng thời gian theo stage cho cả chuỗi đồ thị, và chưa đo pass phụ ML. Theo 17i, pass phụ ML mất 9,9 phút trên doc-4.
Ở doc-1, stage `secondary_edges` mất 40–58 giây CPU (`graph/doc-1/v4`, `v12`).

## 5. Độ nhạy của pass chính với cạnh trục

So cạnh pass chính giữa graph pha A (v3) và graph lượt cuối (v11) theo cặp tên khái niệm (`q5_nhieu_pass_chinh.py`, `q5b_phien_trung.py`):

| | Pha A | Lượt cuối | Giữ | Mất | Mới | Đảo chiều | Jaccard |
|---|---|---|---|---|---|---|---|
| doc-1 | 230 | 223 | 174 | 56 | 49 | 0 | 0,624 |
| xstk | 72 | 83 | 41 | 31 | 42 | 0 | 0,36 |

**Đầu vào phiên luôn khác nhau giữa hai lượt:**
- Không phiên nào có đầu vào giống hệt (0/58 phiên ở doc-1, 0/30 ở xstk).
- Các trường khác nhau, đếm trên doc-1: `mentioned_elsewhere` 56, `proposed_relations` 57, `previous_edges_in_chapter` 52, `target_concepts` 42
  (mô tả khác vì chế độ neo khác).
- Vì vậy chưa tách được nhiễu do mô hình khỏi nhiễu do đầu vào.
- 43/56 cạnh mất ở doc-1 có cả hai đầu giữ nguyên câu neo.

**Phiên trục** `main_section_s_532aaa…`:
- Ở pha A, phiên này cho 8 cạnh, trong đó có "Không gian véc tơ → Véc tơ" với câu trích "Các phần tử của V được gọi là các véc tơ".
- Ở lượt cuối, nó cho 6 cạnh khác hẳn, ví dụ "Tập hợp → Không gian véc tơ".
- Hai khái niệm này **có cùng một câu neo**, là câu định nghĩa không gian véc tơ.

**Văn liệu:**
- **Không tất định:** LLM chạy ở chế độ "tất định" vẫn dao động độ chính xác tới 15% giữa các lượt
  ([Atil et al. 2024](https://arxiv.org/abs/2408.04667)).
- **Đồng thuận nhiều lượt:** self-consistency ([Wang et al. 2023](https://arxiv.org/abs/2203.11171)).
- **Thứ tự trong giáo trình** là tín hiệu chiều tiên quyết:
  - RefD ([Liang et al. 2015](https://aclanthology.org/D15-1193/));
  - [Pan et al. 2017](https://aclanthology.org/P17-1133/);
  - [Pal et al. 2020](https://arxiv.org/abs/2011.10337).

**Đề xuất:**
1. **Đo nhiễu thuần mô hình:** phát lại đúng đầu vào các phiên doc-1 ba lần. Mỗi lần khoảng 78 lời × (11,5k token vào, 0,7k token ra), tức
   khoảng 0,31 USD; ba lần khoảng 0,93 USD.
2. **Luật tất định chống lật chiều** cho cặp có cùng câu neo:
   - khái niệm nào được định nghĩa trong câu, theo "được gọi là" của khái niệm kia, thì phụ thuộc khái niệm kia;
   - hoặc lấy thứ tự xuất hiện trong sách làm chiều mặc định khi pass chính và pass phụ bất đồng.
3. **Bỏ trạng thái truyền giữa các phiên** (mục 4), để đầu vào không còn phụ thuộc thứ tự xếp phiên.

**CHƯA XONG:** chưa đếm số cặp cùng câu neo trong toàn graph, và chưa kiểm luật chống lật chiều trên vàng.

## 6. Kế hoạch đổi mặc định (phác thảo, CHƯA rà kỹ)

**Thứ tự đề nghị:**
1. **Sửa 0 USD trước khi đổi**, vì chúng đổi khoá cache và sẽ làm lại artifact. Gồm các khuyến nghị 1–5 ở mục 7.
2. **Cấu hình:**
   - `upstream_chain` từ `v3` sang `gop` (`config.py:49`);
   - `anchor_batch_mode` từ `a5` sang `single` (`config.py:50`);
   - cập nhật `.env.example:34-35`.
3. **T-01:** quy id vàng qua bảng chuyển hướng của vé 17h, rồi đo T-01 trên chuỗi gộp.
4. **Dựng lại artifact** của 6 tài liệu phát triển, kèm chuỗi đồ thị cho 3 tài liệu có vàng.
5. **Đo lại E5** của pass phụ ML (ADR 0015). Đặc trưng đã lệch, vì chunk neo thay cho chunk do provenance vá.
6. **Tài liệu:** ADR 0016, cập nhật ADR 0004, `CONTEXT.md`, `doc/spec-addendum.md`.
7. **Vé gỡ** ba stage cũ và đường A4 cũ.

**Giữ nguyên:** D-01 chỉ dùng lớp tên, tức chuỗi v3 (`canonicalize.py:38-39`).

**Rủi ro:**
- nhiễu E4 lớn hơn khác biệt cần đo (17i mục 7);
- cụm A4 không tái lập được (mục 2);
- ở chế độ a5, doc-4 có 67 khái niệm từ "chỉ nhắc" thành "được dạy" (17i mục 7).

## 7. Khuyến nghị xếp theo ưu tiên

| # | Khuyến nghị | Lợi ước tính | Rủi ro chất lượng | Cần | Thí nghiệm trả phí |
|---|---|---|---|---|---|
| 1 | Bỏ nguồn đề cử `same_evidence` | doc-4: bớt khoảng 112 lời phán sửa, 0,10 USD; cạnh cắt −32% | 0 gộp mất trên 13 canonical | vé nhỏ | không bắt buộc |
| 2 | Không phán sửa cạnh cắt chỉ có `ngram` (vẫn dùng để chia cụm) | doc-4: −116 lời, 0,093 USD; doc-1: −38 lời, 0,026 USD | 0 gộp mất ở cấu hình mặc định | vé nhỏ | gộp với 1 và 3 trong một lượt canonical 3 tài liệu, khoảng 0,8 USD |
| 3 | Giải mâu thuẫn bắc cầu kiểu tham lam có ràng buộc (hoặc biến thể bảo thủ) | khoảng 2–3 gộp đúng mỗi tài liệu, 0 USD | biến thể tham lam kéo lại 1 gộp sai đã biết ở xstk; biến thể bảo thủ: 0 | spec ngắn + vé | như trên |
| 4 | Chung **tên** sau chuẩn hoá thì buộc gộp | +4 gộp đúng (χ², Gram-Schmidt, Véctơ tọa độ) | chưa thấy ca sai | vé nhỏ | không |
| 5 | Chia cụm A4 tất định: đổi id thành số nguyên đã sắp trước khi chạy Louvain | tái dùng cache ổn định, bớt nhiễu | không | vé nhỏ | không |
| 6 | Neo "một khái niệm" cộng luật L8 (bỏ mẫu "Tên:") | −20% lời neo; trên doc-4 rẻ hơn a5 (khoảng 0,62 so với 0,66 USD) mà giữ độ chặt của C8 | 1,5% quá tay so với LLM | spec + vé | không |
| 7 | `prepare_anchors` chuẩn hoá chunk một lần; đặt `measure_phase` cho các đoạn CPU | doc-1 khoảng −25 giây; doc-4 phần lớn trong 260 giây của `prepare_anchors` (cộng 45 giây `build_nodes` nếu tối ưu tiếp) | không | vé nhỏ | không |
| 8 | Nâng `canonical_concurrency` lên khoảng 16, bỏ rào `NODE_BATCH` ở canonical, xoá `vertex_concurrency` | phần LLM của canonical doc-4 có thể từ khoảng 390 giây còn khoảng 100 giây (ước) | không | vé nhỏ | đo một lượt cùng 1–3 |
| 9 | Thí nghiệm bỏ `previous_edges_in_chapter` ở pass chính | pass chính chạy song song; doc-4 có thể từ 13,7 phút còn vài phút | chưa biết, cần E4 | spec | doc-1 + xstk khoảng 0,55 USD; thêm doc-4 khoảng 2,2 USD |
| 10 | Đo nhiễu pass chính bằng phát lại đầu vào cố định; luật chống lật chiều | quyết E4 bằng số có khoảng nhiễu | không | nghiên cứu | khoảng 0,93 USD |
| 11 | Thêm `coextensive_with` vào nhãn R2 của chuỗi gộp | nhỏ | không | vé nhỏ | không |
| 12 | Đo xác minh mù cho cặp `subtype_of` | có thể phục hồi một số cặp như Tự đồng cấu | cao: bộ xác minh đã từng cho `dong_nhat` với 4 gộp sai đã biết | nghiên cứu | dưới 0,2 USD |

**Văn liệu về gom lô và phán thực thể:**
- **Gom lô theo câu giống nhau cho độ chính xác kém nhất**, vì mô hình trả lời giống nhau cho nhiều câu. Gom theo câu khác nhau thì tốt nhất. Tiền
  bớt được 4–7 lần đến từ phần minh hoạ dùng chung ([BatchER, Fan et al., ICDE 2024](https://arxiv.org/abs/2312.03987)).
  - Điều này khớp với 17j: lời phán sửa gom lô gồm các cặp giống nhau, và vì đầu vào của từng mục chiếm phần lớn token nên gần như không bớt tiền.
  - Xem thêm [Cheng et al. 2023](https://arxiv.org/abs/2301.08721).
- **Phân cụm trong ngữ cảnh tốt nhất ở cỡ tập ≤ 9 bản ghi**, sau đó tụt. Có thêm bước chặn cụm sai ([LLM-CER, Fu et al. 2025](https://arxiv.org/abs/2506.02509)).
  Trần cụm A4 hiện là 9.
- **Cho mô hình thấy các bản ghi cùng lúc ("select")** tốt hơn phán từng cặp, nhưng có thiên lệch vị trí
  ([Wang et al., COLING 2025](https://arxiv.org/abs/2405.16884)).
- **Không có prompt tốt nhất chung cho mọi mô hình và bộ dữ liệu** ([Peeters et al., EDBT 2025](https://arxiv.org/abs/2310.11244)).
- **Chọn câu hỏi để giảm bất định của phân hoạch** ([Li et al. 2024](https://arxiv.org/abs/2401.03426)) và **suy cặp nhờ tính bắc cầu**
  ([Wang et al., SIGMOD 2013](https://arxiv.org/abs/1408.6916)): cơ sở cho khuyến nghị 3 và cho việc bớt lời phán sửa.

## 8. Script và tệp kết quả (để lượt sau làm tiếp)

Tất cả nằm ở `tmp/nghien-cuu-chuoi-gop/`. Chạy từ gốc repo bằng `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <script>`.

**Hàm dùng chung:** `chung.py` (danh sách phiên bản, giá tiền, quy đích vàng).

**Câu hỏi 1:**
- `q1_luat_neo.py` → `ket-qua/q1-luat-neo.json`;
- `q1b_luat_chat.py` → `ket-qua/q1b-luat-chat.json`;
- `q1c_luat_duy_nhat.py` → `ket-qua/q1c-luat-duy-nhat.json`.

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
- `q4_do_cpu.py <doc> <v>` → `ket-qua/q4-cpu-<doc>.json`. Đã chạy cho doc-1 v6 và doc-4 v3.

**Câu hỏi 5:**
- `q5_nhieu_pass_chinh.py` → `ket-qua/q5-nhieu.json`;
- `q5b_phien_trung.py` → `ket-qua/q5b-phien.json`.

**Chi phí lạnh:** `q6_chi_phi_lanh.py` → `ket-qua/q6-chi-phi-lanh.json`.
- Lưu ý: với canonical neo a5, cột `anchor` đếm thừa, vì `anchor_decision_log` mang hàng của lượt trước. Phần neo nên lấy theo `cost_summary`,
  như 17i đã làm.

**Bước kế tiếp:**
1. Đo lại CPU của doc-4 khi máy rảnh.
2. Lập bảng thời gian chuỗi đồ thị theo stage.
3. Thử L8 sau khi bỏ mẫu "Tên:".
4. Đếm cặp cùng câu neo và thử luật chống lật chiều trên vàng.
5. Rà kỹ kế hoạch ở mục 6.
6. Viết spec cho các khuyến nghị 1–5.
