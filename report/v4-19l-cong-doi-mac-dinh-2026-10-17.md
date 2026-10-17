# 19l — Cổng đổi mặc định sang chuỗi gộp

Ngày 2026-10-17. Người chạy: Claude. Vé [19l](../task/v4/19l-cong-dung-lai-artifact.md), spec [đổi mặc định chuỗi gộp](../doc/doi-mac-dinh-chuoi-gop-spec.md)
pha 3. **Chi thật khoảng 3,39 USD** (Vertex, gemini-3.1-flash-lite, temperature 0), kể cả 0,19 USD chạy chẩn đoán. Tổng đợt 19 khoảng 6,45 USD
trên trần 10 USD.

## Phán: qua, bật mặc định ở 19m

| Tiêu chí | Mốc | Cổng | |
|---|---|---|---|
| Neo ở đích vàng, cùng trạng thái dạy | doc-1 25/26, xstk 26/26, doc-4 47/47 | 25/26, 26/26, 47/47 | đạt |
| Gộp sai mà vàng phát hiện | không quá 3 | 1 (doc-1 0, xstk 1, doc-4 0) | đạt, tốt hơn 17i (3) |
| Lời gọi và USD trước A8, doc-4 | khoảng 1.230 lời, 1,0 USD | 1.108 lời, 0,88 USD | đạt |
| E4 trong dải nhiễu 19j | bảng mục 3 của báo cáo 19j | doc-1 và doc-4 lệch dưới dải tới 0,06; xstk lệch dưới dải rõ | qua sau khi đọc, xem mục 4 |
| E4 pass phụ ML so với 18d | không tụt rõ | doc-4 tốt hơn; doc-1 và xstk thấp hơn ở Q7b và bao đóng | qua sau khi đọc, xem mục 4 |

E4 lệch dưới dải nhiễu của 19j ở cả ba tài liệu. Đọc từng chỗ lệch thì không thấy lỗi do mã đợt 19:
- **doc-1 và doc-4:** mỗi tài liệu chỉ khác 19j ở 2 cạnh vàng. Ở doc-1, pass chính không đề xuất hai cạnh dù cả hai khái niệm cùng phiên. Ở doc-4,
  hai cạnh do pass phụ ML ra. Hai cạnh đều nằm trên một chuỗi, nên bao đóng tụt theo. Đây là đúng kiểu nhiễu đầu vào mà 19j đo.
- **xstk:** dãy học mất ba khái niệm mà văn bản có dạy, vì neo "một khái niệm" xếp chúng là "chỉ nhắc". Lỗi này có từ v3; neo gom vào A5 của 17i
  tình cờ né được. Chạy pass chính nối tiếp trên đúng canonical của cổng không cứu được: cùng 6/36 cạnh vàng.

Dải của 19j chỉ đo nhiễu khi giữ cố định canonical của 17i. Cổng đổi canonical: luật A4 mới và neo "một khái niệm". Đây là nhiễu đầu vào lớn hơn,
nên dải của 19j hẹp hơn mức lệch thật. Theo luật cổng, phán bằng cách đọc.

## 1. Mã và cách chạy

- **Commit mã:** `f4871fd83aa8169d771b8cbfe40d0a61d7baf56a`, cây `265e3fc287bd8ba678fda5e38a33a418e5f9eef2`. Commit này chứa 19a–19k và ba
  việc checkpoint của 19k.
- **Worktree sạch:** chạy bằng worktree sạch của commit ở `tmp/v4-19l/ma`. Thư mục làm việc chính còn lệch commit ở `cli/main.py`, `models.py`
  và hai tệp parser.
- **Script chạy:** `scripts/gop-khau/cong-19l/chay_tu_commit.py` dừng ngay nếu worktree bẩn, sai commit, hoặc `doc2roadmap` import nhầm mã
  của thư mục làm việc. Gốc lệnh vẫn là repo chính, để dùng kho `artifacts/`, `.env` và tệp vàng.
- **Lệnh:** như 17i, xem `scripts/gop-khau/cong-19l/chay_cong.sh`.
  - `a4 --upstream-chain gop --allow-spend`, có `--no-gold-for-doc --language vi` cho doc-1, doc-6 và doc-4;
  - `roadmap --upstream-chain gop --allow-spend`; xstk thêm `--allow-text-quality-reason`.
- **`Settings()` trước khi chạy:**
  - Vertex, `llm_max_in_flight` 100, TPM 1,6 triệu, 8 lần thử;
  - `canonical_concurrency` 16, `anchor_batch_mode` single, `merge_description_enabled` false;
  - `roadmap_main_parallel` true, `roadmap_concurrency` 4.
- **Dry-run trước:** 0 USD, kho chính không đổi.

**doc-1 canonical v5 chạy trước khi có commit.** Lúc đó vé chưa yêu cầu ghim mã. Mã của lượt này:
- workspace `d03f9e3`;
- bản vá `src/` (sha256 `7d40e1668d0d6ded…`) và 13 tệp mới, lưu ở `tmp/v4-19l/`.

Kiểm tái lập bằng `scripts/gop-khau/cong-19l/tai_lap_doc1.py`:
- chép kho doc-1 không có v5;
- chạy A4 bằng mã commit;
- mọi lời gọi mô hình bắt buộc lấy từ nhật ký của v5, nên 0 USD mô hình.

Kết quả: mọi trường nội dung trùng khít với v5, kể cả nút, chuyển hướng, cạnh, neo và nhật ký (bỏ cờ `reused`). Chỉ `stats` và `cost_summary` khác,
vì lượt kiểm tái dùng lời gọi. Config hash trùng. Vì vậy bảng nguồn gốc ghi v5 là "workspace, tái lập trùng khít từ commit". Không sửa artifact cũ để
gán nguồn gốc hồi tố.

## 2. Thời gian và chi phí

**A4/A5 chuỗi gộp, 6 tài liệu.**

| Tài liệu | Lời gọi | Theo phần (gộp / sửa / xác minh / mô tả / kiểm / neo) | USD | 17i, chạy từ đầu | Giây | Riêng embedding tên |
|---|---:|---|---:|---:|---:|---:|
| doc-1 | 406 | 58 / 76 / 25 / 21 / 16 / 210 | 0,291 | 0,449 | 505 | 382 |
| nhap-mon-ml | 102 | 20 / 7 / 6 / 2 / 5 / 62 | 0,078 | 0,197 | 47 | 16 |
| naive-bayes | 63 | 11 / 5 / 7 / 1 / 3 / 36 | 0,046 | 0,077 | 42 | 15 |
| doc-6 | 42 | 9 / 2 / 4 / 1 / 3 / 23 | 0,026 | 0,048 | 38 | 14 |
| xstk | 150 | 23 / 17 / 13 / 6 / 7 / 83+1 | 0,123 | 0,195 | 223 | 180 |
| doc-4 | 1.108 | 176 / 178 / 50 / 29 / 46 / 629 | 0,878 | 1,569 | 961 | 574 |
| **Tổng** | | | **1,442** | 2,535 | | |

- Phân sửa bỏ qua cạnh cắt chỉ có ngram (vé 19b): doc-1 42 cặp, xstk 5, doc-4 123.
- Mọi tài liệu đều rẻ hơn 17i: tổng giảm 43%.

**Chuỗi đồ thị, 3 tài liệu có vàng.** Đơn vị: giây theo stage.

| | cụm | mentions | pass chính | pass phụ ML | kiểm + nhãn | dãy học | tổng | USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| doc-1 | 23 | 15 | 13 | 22 | 18 | 6 | 104 | 0,241 |
| xstk | 149 | 7 | 11 | 11 | 1 | 5 | 190 | 0,142 |
| doc-4 | 358 | **744** | 240 | 147 | 6 | 11 | 1.510 | 1,377 |

**Phút/cuốn:**

| | A4 | đồ thị | tổng | ước, không tính chờ embedding |
|---|---:|---:|---:|---:|
| doc-1 | 8,4 phút | 1,7 phút | 10,2 phút | khoảng 3,8 phút |
| xstk | 3,7 phút | 3,2 phút | 6,9 phút | khoảng 1,6 phút |
| doc-4 | 16,0 phút | 25,2 phút | 41,2 phút | khoảng 14 phút |

Lượt 17i, doc-4: A4 14,7 phút và đồ thị 32 phút. Phần chạy thật giảm mạnh:
- pass chính: 13,7 phút xuống 4,0 phút;
- pass phụ ML: 9,9 phút xuống 2,4 phút.

**USD/cuốn:** doc-1 0,53; xstk 0,27; doc-4 2,26.

**Thời gian bị đội vì embedding trên Vertex, không phải vì mã.**
- Trên Vertex, gemini-embedding-001 nhận một văn bản mỗi request. Tài liệu có trên khoảng 100 văn bản thì bị quota bóp.
  - stage mentions của doc-4: 1.159 lời HTTP cho khoảng 630 câu truy vấn;
  - stage cụm của doc-4: 766 lời HTTP.
- Mã embedding không đổi so với 17i. Ở 17i, cùng bước embedding tên của doc-1 chỉ mất 9–43 giây. Tài liệu dưới 100 tên hôm nay chỉ mất 14–16 giây.
- Sản phẩm chạy Developer API, ở đó `batchEmbedContents` gom 100 văn bản vào một request. Vì vậy số phút ở trên là trần xấu của Vertex, không
  phải số của sản phẩm.

**Ô còn mở của 19g: stage mentions doc-4 toàn stage mất 744 giây.**
- Phần tính trên CPU khoảng 15 giây (số đo 19g).
- Phần còn lại là chờ embedding 630 câu truy vấn trên Vertex.
- Với Developer API, phần này còn 7 request gom lô.

## 3. Neo và gộp

| | Đích vàng: cùng trạng thái / cùng câu neo | Nút gộp (v3 → gộp) | Gộp mới / mất so với v3 |
|---|---|---|---|
| doc-1 | 25/26 / 25/26 | 225 → 223 | 5 / 12 |
| xstk | 26/26 / 25/26 | 98 → 97 | 1 / 5 |
| doc-4 | 47/47 / 46/47 | 620 → 629 | 1 / 12 |
| nhap-mon-ml | — | 75 → 75 | 2 / 2 |
| naive-bayes | — | 34 → 36 | 0 / 1 |
| doc-6 | — | 28 → 27 | 0 / 0 |

Gộp sai mà vàng phát hiện còn 1, ở xstk; 17i có 3. Hai gộp sai đã biết của 17i ở xstk nay được tách đúng:
- "Tỉ lệ mẫu = Tỉ lệ mẫu tổng quát";
- "Bài toán tìm kích thước mẫu = Xác định kích thước mẫu".

## 4. E4 và các chỗ đã đọc

| Chỉ số | doc-1 cổng | dải 19j | xstk cổng (song song / nối tiếp) | dải 19j | doc-4 cổng | 19j (nối tiếp / song song) |
|---|---|---|---|---|---|---|
| Q6 | 0,125 | 0,100–0,125 | 0,541 / 0,541 | 0,508–0,542 | 0,129 | 0,129 |
| Q7 | 0,544 | 0,419–0,596 | 0,225 / 0,241 | 0,253–0,427 | 0,616 | 0,638 / 0,636 |
| Q7b | 0,626 | 0,645–0,683 | 0,380 / 0,376 | 0,467–0,506 | 0,856 | 0,878 |
| P trực tiếp | 0,438 | 0,483–0,552 | 0,286 / 0,250 | 0,286–0,308 | 0,705 | 0,739 / 0,723 |
| R trực tiếp | 0,483 | 0,483–0,552 | 0,111 / 0,111 | 0,111 | 0,585 | 0,642 |
| P bao đóng | 0,695 | 0,713–0,797 | 0,538 / 0,514 | 0,528–0,618 | 0,876 | 0,893 / 0,892 |
| R bao đóng | 0,458 | 0,465–0,653 | **0,126 / 0,162** | 0,181–0,324 | 0,579 | 0,629 / 0,623 |
| Khái niệm trong dãy học | 205 | 205 | 73 | 77 | 495 | 549 |
| Cạnh cứng A10 | 400 | 397–419 | 124 / 135 | 140–148 | 908 | 1.052 / 1.043 |

Dải 19j của xstk và doc-1 ở bảng trên lấy từ các lượt `noi-s0`, `noi-x1`, `noi-x2` và `song-s1`.

Mốc 18d (v3, pass phụ ML):
- doc-1: Q7 0,603, Q7b 0,743, trực tiếp 0,438/0,500, bao đóng 0,821/0,664;
- xstk: Q7 0,206, Q7b 0,530, trực tiếp 0,333/0,143, bao đóng 0,593/0,163;
- doc-4 v3: Q7 0,483, Q7b 0,859, trực tiếp 0,667/0,566, bao đóng 0,856/0,522.

**Cách đọc.**
- `scripts/gop-khau/cong-19l/doc_lech.py` so từng cạnh vàng mà mỗi lượt bắt được qua bao đóng, theo tên khái niệm.
- `canh_sai.py` liệt kê cạnh cứng giữa các đích vàng mà vàng không có.

**doc-4.** Cổng bắt được 38/53 cạnh vàng; 19j song song bắt được 40/53.
- Hai cạnh chênh là "Phủ định biện chứng → Tính kế thừa" và "Tính kế thừa → Phát triển theo đường xoáy ốc".
- Ở 19j, cả hai do pass phụ ML ra. Chúng nằm trên một chuỗi, nên R bao đóng tụt 0,044.
- Dãy học ngắn hơn 54 khái niệm, đúng như 17i đã thấy: neo gom vào A5 nâng khoảng 67 khái niệm từ "chỉ nhắc" lên "được dạy", đọc mẫu thì khoảng
  3/4 là sai. Cổng dùng neo "một khái niệm", nên dãy học chặt hơn. E4 không đo được phần này.
- Mọi chỉ số tốt hơn v3, trừ Q7b ngang v3 (0,856 so với 0,859).

**doc-1.** Cổng bắt được 18/29; 19j song song và nối tiếp x1 đều bắt được 20/29.
- Pass chính của cổng không đề xuất "Hệ sinh → Cơ sở" và "Ma trận tọa độ → Ma trận chuyển cơ sở". Cả hai cặp đều có mặt cùng phiên, và nhật ký
  executor không có dòng nào cho chúng. So với lượt nối tiếp x1 của 19j, cạnh chênh lại là một cặp khác ("Tổ hợp tuyến tính → Độc lập tuyến
  tính"). Tức là các lượt khác nhau ở những cạnh lẻ, không theo một hướng.
- Có 3 cạnh sai mới giữa các đích, đều do pass phụ ML ra: "Cơ sở → Hệ sinh" (ngược chiều vàng), "Ma trận → Véc tơ tọa độ" và
  "Vô hướng → Phần tử đối". Cạnh thứ tư, "Ma trận → Ma trận chuyển cơ sở", hợp lý dù vàng không có.
- Đây là kiểu lật cạnh trục đã ghi ở 17i và trong nghiên cứu cải thiện chuỗi gộp: pass chính không tạo cạnh, pass phụ ML chọn chiều ngược lại. Lỗi
  không do mã đợt 19.

**xstk.** Cổng bắt được 6/36 cạnh vàng; 19j bắt được 8/36.
- Ba khái niệm có trong vàng rơi khỏi dãy học, vì neo "một khái niệm" phán "chỉ nhắc":
  - "Độ chính xác": lời phán ghi "không được định nghĩa, chỉ dùng trong công thức". Văn bản có "độ chính xác ε của ước lượng p theo công thức".
  - "Bài toán tìm kích thước mẫu": câu ứng viên duy nhất là câu giới thiệu hai bài toán ngược. Câu kế tiếp nói chỉ xét bài toán tìm độ tin cậy, nên
    lời phán kết luận "chỉ nhắc". Phần dạy nằm ở mục sau, không có trong ứng viên.
  - "Xác định kích thước mẫu": lời phán ghi "chỉ là tiêu đề mục". Văn bản có mục "Xác định kích thước mẫu trong ước lượng tỉ lệ" kèm đề bài tìm
    kích thước mẫu.
- Đọc văn bản thì cả ba đều được dạy, nên đây là phán sai.
- Đây cũng là trạng thái của v3 (26/26 đích cùng trạng thái v3). Neo gom vào A5 của 17i đưa chúng về "được dạy", và 17i đã quy nguồn gốc cho
  A2 gán nhầm vùng "đề cương" (vé 05).
- Bù lại, cổng tách đúng hai gộp sai đã biết. "Độ chính xác trong ước lượng tỉ lệ → Ước lượng tỉ lệ" có mà 19j không có.

**Chạy nối tiếp trên đúng canonical của cổng (chẩn đoán, 0,19 USD).**
- Script: `scripts/gop-khau/cong-19l/noi_tiep_xstk.py`, kho riêng.
- Kết quả: 79 cạnh pass chính so với 71; cùng 6/36 cạnh vàng; R bao đóng 0,162 so với 0,126; Q7b 0,376 so với 0,380.
- Bản nối tiếp chỉ ngang v3 ở R bao đóng (0,163). Chạy song song mất 4 cạnh bao đóng đúng trên 111.

**Về luật "R bao đóng xstk dưới 0,2 thì mở vé xét cách lai" của 19j.**
- Điều kiện đã xảy ra. Nhưng chạy nối tiếp hoàn toàn, tức trần của mọi cách lai, cũng chỉ đạt 0,162.
- Nguyên nhân nằm ở bước neo, không ở việc chạy song song. **Không mở vé cách lai.**
- Đòn bẩy cho xstk là vé 05: A2 gán vai trò vùng, và cách chọn câu ứng viên neo cho khái niệm có phần dạy nằm ở mục tiêu đề dạng gạch đầu dòng.

## 5. Chi phí

| Phần | USD |
|---|---:|
| A4/A5 chuỗi gộp, 6 tài liệu | 1,442 |
| Chuỗi đồ thị: doc-1 0,241, xstk 0,142, doc-4 1,377 | 1,760 |
| Chẩn đoán xstk nối tiếp | 0,186 |
| Embedding (không nằm trong `cost_summary`), ước | dưới 0,02 |
| **Tổng cổng** | **khoảng 3,39** |

Dry-run ước 3,7–4,3 USD. Đợt 19 gồm 19j 3,06 và cổng 3,39, tổng 6,45 trên trần 10.

**Sự cố.**
- Khi máy thiếu RAM, Claude Code dừng shell nền của cổng, đúng lúc chuỗi đồ thị doc-4 đang chạy.
- Tiến trình Python không bị dừng theo. Nó chạy xong bình thường (mã thoát 0) và ghi đủ v16–v23. Không phải chạy lại, không mất tiền.

## 6. Nguồn gốc artifact

Bảng đủ (SHA-256 của manifest và payload) nằm ở `scripts/gop-khau/cong-19l/nguon-goc.json`, sinh bằng `nguon_goc.py`. Tóm tắt:

| Artifact mới | Version | Stage | Commit |
|---|---|---|---|
| `artifacts/canonical/doc-1` | v5 | canonical | workspace `d03f9e3` + bản vá `7d40e166…`; tái lập trùng khít nội dung từ `f4871fd` |
| `artifacts/canonical/{nhap-mon-ml, naive-bayes, xstk-ch3-1}` | v8 | canonical | `f4871fd` |
| `artifacts/canonical/{doc-6, doc-4}` | v2 | canonical | `f4871fd` |
| `artifacts/graph/doc-1` | v46–v53 | cụm → dãy học | `f4871fd` |
| `artifacts/graph/xstk-ch3-1` | v49–v56 | cụm → dãy học | `f4871fd` |
| `artifacts/graph/doc-4` | v16–v23 | cụm → dãy học | `f4871fd` |

**Artifact thượng nguồn tái dùng:** commit sinh ra chúng chưa biết, vì có từ trước khi ghim mã.

| | candidates | chunks (neo / đồ thị) | retrieval |
|---|---|---|---|
| doc-1 | v3 | v7 | v3 |
| nhap-mon-ml | v7 | v6 | — |
| naive-bayes | v5 | v3 | — |
| doc-6 | v1 | v4 | — |
| xstk | v5 | v5 | v1 |
| doc-4 | v1 | v6 | v1 |

Commit không nằm trong config hash hay khoá cache.

## 7. Việc tiếp theo

1. **19m:** bật mặc định chuỗi gộp, ADR 0016, `CONTEXT.md`, phần ghi thêm của spec, tệp bàn giao Pha B. Artifact chuẩn của 6 tài liệu đã ở kho
   chính.
2. **Vé 05:** A2 gán vai trò vùng. Kết quả cổng cho thấy đây là đòn bẩy lớn nhất cho xstk dưới neo "một khái niệm". Đang chờ chủ dự án.
3. **19k, việc nhỏ:** dừng sớm khi lỗi. Không chặn 19m.
4. **Đợt baseline đánh giá:** dải nhiễu E4 phải tính cả nhiễu do đổi canonical, không chỉ nhiễu xáo đầu vào như 19j. Cổng lệch tới 0,06 ở doc-1 và
   doc-4 dù đọc không thấy lỗi.
