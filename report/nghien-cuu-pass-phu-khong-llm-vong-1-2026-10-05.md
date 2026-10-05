# Pass phụ A8 không dùng LLM — nghiên cứu và thí nghiệm vòng 1 (2026-10-05)

**Bối cảnh.** Ngày 2026-10-05 chủ dự án chốt ba điều:
- đồ án chuyên ngành chỉ làm tài liệu tiếng Việt;
- pass phụ A8 bỏ LLM, cho cả đồ án lẫn seminar; luồng LLM cũ giữ lại để so sánh;
- đích dài hạn của đồ án: LLM chỉ còn ở A3 (trích ứng viên) và A8 pass chính (agent suy luận cạnh). Các khâu khác nghiên cứu sau.

**Nền.** Báo cáo này nối tiếp [R-02](nghien-cuu-ml-dl-loc-cap-va-tien-quyet-2026-10-04.md). R-02 đặt chuỗi thí nghiệm 0 USD E0–E6 cho bài
"lọc cặp trước LLM"; ở đây đích đổi thành **thay hẳn LLM**.

Hai ghi chú cũ của chủ dự án được đọc làm tham khảo, không phải chân lý: [pipeline seminar V1–V13](../doc/pipeline-seminar-chuan-V1-V13-v2.md) và
[luồng agent](../doc/luong-moi-pipeline-agent-final-v2.md). Ba ý được dùng:
- tín hiệu "ngữ cảnh định nghĩa" (S2);
- học trọng số tín hiệu từ dữ liệu thay vì đặt tay;
- **tách từ tiếng Việt là bước không bỏ được** (V3). Mục 5 cho thấy ý này đúng.

**Phạm vi.**
- 0 USD, không gọi mô hình sinh văn bản.
- Embedding chạy tại máy; văn bản giáo trình không gửi đi đâu.
- Số đo trên tài liệu phát triển: doc-1, xstk, doc-4 có vàng người; nhap-mon-ml chỉ dùng để học. Tài liệu tiếng Anh (doc-2, doc-3) chỉ dùng ở
  vài phép đo phụ.
- Kết luận cuối về chất lượng cần tập giữ lại mới (vé T-01).

## Tóm tắt

1. **Pass phụ không đổi thứ tự học; nó mang độ phủ của dòng "cần:".** Phát lại A9→A10 không có pass phụ: Q6 giữ nguyên ở cả ba tài liệu vàng,
   vì dãy học bám sách. Q7 (độ phủ tổ tiên) tụt mạnh:
   - doc-1: 0,667 → 0,213;
   - xstk: 0,414 → 0,113;
   - doc-4: 0,322 → 0,185.

   Bản thay phải giữ được độ phủ này mà không hạ độ chính xác.
2. **Bài toán thu hẹp được.**
   - Phép chấm vàng chỉ tính **cạnh cứng** (`can_de_hieu`).
   - Hợp đồng vé 12 đòi cạnh cứng có câu trích nguyên văn trong cửa sổ định nghĩa của đích.

   Vì vậy bản không LLM chỉ cần **kiểm từng lần X được nhắc trong cửa sổ định nghĩa của Y**: X có thật là tiên quyết trực tiếp của Y không.
3. **Nhãn của LLM nhiễu, và kiểm định còn "ăn mất" một phần ý định.**
   - 19–44% cặp đã hỏi bị hoãn.
   - Phần lớn cặp hoãn có hai thứ tự cùng muốn tạo cạnh, nhưng phản hồi trượt kiểm (nhiều nhất là `target_not_taught`).
   - Ở doc-4, 11% bản ghi pass phụ là phản hồi lỗi.

   **Ý định** của LLM (kể cả phản hồi bị loại) bắt được nhiều cạnh vàng hơn cạnh LLM thực sự tạo được (mục 7), nên được dùng làm nhãn. Đo
   đầu cuối thì học từ ý định và học từ cạnh v3 cho kết quả gần nhau (mục 5). Bộ lắp cạnh tất định thì không bao giờ trả phản hồi lỗi.
4. **Khớp tên theo âm tiết là nguồn ứng viên sai lớn nhất; tách từ tiếng Việt sửa được.**
   - "Chất" khớp vào "vật chất", "Độ" vào "trình độ", "Hợp" vào "tập hợp", "Hiệu" vào "kí hiệu".
   - Khớp theo ranh giới từ (underthesea) bỏ 21% ứng viên ở doc-1 và 26% ở doc-4, **không mất cạnh vàng nào**.
5. **Kết quả đầu cuối** của bản đề xuất (tách từ + LightGBM học ý định cạnh cứng + ngưỡng hiệu chỉnh), so với pass phụ LLM v3, Wilson 95%:

   | tài liệu | phương án | Q7 | Q7b | bao đóng P | bao đóng R |
   |---|---|---|---|---|---|
   | doc-4 | LLM v3 | 0,322 | 0,606 | 0,584 (0,50–0,67) | 0,459 (0,38–0,54) |
   | | **không LLM** | **0,595** | **0,720** | **0,717** (0,62–0,79) | **0,478** (0,40–0,56) |
   | doc-1 | LLM v3 | 0,667 | 0,877 | 0,874 (0,80–0,92) | 0,740 (0,66–0,81) |
   | | **không LLM** | 0,672 | 0,802 | 0,815 (0,73–0,88) | 0,672 (0,59–0,75) |
   | xstk | LLM v3 | 0,414 | 0,644 | 0,636 (0,47–0,78) | 0,214 (0,14–0,30) |
   | | **không LLM** | 0,195 | 0,511 | 0,593 (0,41–0,76) | 0,163 (0,10–0,25) |

   - **doc-4:** hơn LLM ở cả bốn chỉ số. Độ chính xác bao đóng hơn rõ nhất; ở cấu hình ngưỡng F1, khoảng tin cậy còn tách hẳn (0,69–0,84 so
     với 0,50–0,67).
   - **doc-1:** sát LLM, khoảng tin cậy chồng nhau.
   - **xstk:** kém về độ phủ.
6. **Tiền và thời gian.**
   - Pass phụ không LLM tốn 0 USD và khoảng 1–2 phút mỗi cuốn trên CPU (lắp cạnh doc-4: 36 giây).
   - Pass phụ LLM v3 trên doc-4 tốn 45,9 USD và 4,5–5 giờ; trên doc-1 khoảng 5,7 USD.
7. **Ngưỡng là đòn bẩy lớn.**
   - Ngưỡng F1 theo nhãn LLM không ổn định giữa các cuốn: có cuốn giữ gần hết ứng viên.
   - Chính sách hiệu chỉnh (isotonic trên dự đoán ngoài mẫu, giữ số cạnh bằng tổng xác suất) tự theo tỉ lệ dương của từng cuốn và chốt được
     trước khi nhìn vàng. Đây là mặc định đề xuất.
8. **Chưa đạt ở những điểm sau:**
   - xstk kém độ phủ;
   - doc-1 kém LLM chừng 0,06 ở độ chính xác;
   - chưa có cạnh cứng mà tên tiên quyết không xuất hiện nguyên văn trong cửa sổ (LLM có 20–38% cạnh cứng như vậy);
   - chưa sinh cạnh mềm `cong_cu`;
   - embedding e5-base không giúp.

   Đòn bẩy kế tiếp là **dữ liệu đa lĩnh vực** ([đặc tả D-01](../task/v4/D-01-dac-ta-du-lieu-pass-phu.md)) và mô hình đọc văn bản cửa sổ.
9. **Một kết quả đã phải đính chính.** Lần so mức cặp đầu tiên cho thấy ML "hơn hẳn thầy" (độ chính xác 0,64–1,00 so với 0,36–0,75). Con số
   này bị thổi lên vì tập so có cả cặp bị tỉa: những cặp này đã có đường nối sẵn nên gần như luôn đúng, và ML xếp chúng lên đầu. Chấm lại chỉ
   trên cặp LLM đã phán thì phán đoán của ML **ngang** LLM ở xstk và doc-4, **kém** ở doc-1 (mục 7).

---

## 1. Câu hỏi và cách đo

**Câu hỏi.** Một bộ phân loại không sinh văn bản có thay được pass phụ LLM mà giữ được chất lượng lộ trình trên vàng người không? Với chi phí
và thời gian bao nhiêu?

**Đo đầu cuối (E4).**
- Lấy artifact pass phụ v3 của từng tài liệu, giữ nguyên pass chính, nút, chunk, mention map; **chỉ thay `secondary_edges`**.
- Phát lại A9 → tên khái niệm (dùng lại phản hồi đã ghi; đầu vào khâu này không phụ thuộc cạnh) → A10 bằng mã hiện tại.
- Chấm bằng `cham_tap_giu_lai.score`, đúng hàm của tập giữ lại v3.
- **Kiểm chứng bộ phát lại:** đưa cạnh v3 nguyên vẹn vào thì ra **đúng từng phần tử** `sequence` và `requires_edges` của A10 đã chấm (doc-1,
  doc-2 v7; xstk v45; doc-4 v11), và mọi chỉ số trùng báo cáo tập giữ lại.

**Chỉ số.** Q6 (lỗi thứ tự học), Q7 (độ phủ tổ tiên), Q7b (độ chính xác tổ tiên), P/R cạnh trực tiếp và theo bao đóng trên rút gọn bắc cầu.
- Chỉ cạnh cứng được tính.
- Khoảng tin cậy Wilson 95% tính theo cặp bao đóng. Các cặp này không độc lập, nên khoảng thật rộng hơn.

**Chia dữ liệu.** Leave-one-document-out trên bốn tài liệu tiếng Việt. Cặp của tài liệu đo không bao giờ nằm trong tập học. Ngưỡng chọn trên
dự đoán ngoài mẫu của chính các tài liệu học.

## 2. Dữ liệu (E0)

`scripts/pass-phu-ml/dung_bang_cap.py` tách mỗi cặp ứng viên của pass phụ v3 thành hai dòng có hướng X→Y ("X là tiên quyết của Y"):
- đặc trưng chỉ lấy từ thứ có trước pass phụ;
- nhãn lấy từ `secondary_log`, `secondary_edges` và phán quyết từng thứ tự trong `decision_log`.

Số cặp và số cạnh khớp manifest ở cả sáu tài liệu.

| tài liệu | ngôn ngữ | cặp | đã hỏi | hoãn | bị tỉa | cạnh v3 (cứng/mềm) | ứng viên cửa sổ: âm tiết → từ | ý định cứng (ứng viên từ) |
|---|---|---:|---:|---:|---:|---|---|---:|
| doc-1 | vi | 3.471 | 2.763 | 514 (19%) | 708 | 468 (253/215) | 705 → 555 | 202 |
| nhap-mon-ml | vi | 997 | 883 | 264 (30%) | 114 | 88 (42/46) | 153 → 150 | 35 |
| xstk-ch3-1 | vi | 942 | 777 | 344 (44%) | 165 | 171 (69/102) | 185 → 176 | 69 |
| doc-4 | vi | 22.972 | 18.352 | 3.514 (19%) | 4.620 | 1.473 (620/853) | 3.610 → 2.659 | 597 |
| doc-2 | en | 9.513 | 7.455 | 2.397 (32%) | 2.058 | 1.060 (332/728) | 697 | — |
| doc-3 | en | 248 | 238 | 61 (26%) | 10 | 18 (13/5) | 34 | — |

**Đặc trưng.** Có 90 đặc trưng; danh sách đầy đủ ở đầu ra `nguong.json` của mỗi lượt. Các nhóm:
- nguồn cặp: năm nguồn ứng viên, trích dẫn có hướng, trọng số kênh của cặp cụm;
- thứ tự và cấu trúc mục;
- tên X trong cửa sổ định nghĩa Y (số câu, câu neo, vị trí; bản âm tiết và bản ranh giới từ);
- RefD trên chunk định nghĩa;
- độ phủ, đồng xuất hiện;
- PageRank trên đồ thị "được tham chiếu", cạnh pass chính;
- độ "khung" của X (bao nhiêu cửa sổ nhắc X), số tên cùng một cửa sổ;
- từ tiếng Việt đứng ngay trước tên X ("là", "của", "theo", "dựa trên", "ví dụ", "khác với"…);
- thuộc tính nút.

**Phản hồi lỗi của pass phụ LLM.**

| tài liệu | bản ghi lỗi | nguyên nhân lớn nhất |
|---|---|---|
| doc-1 | 545/5.526 (10%) | trích ngoài chunk 163, `target_not_taught` 86 |
| xstk | 535/1.582 (34%) | `target_not_taught` 258 |
| doc-4 | 4.393/38.556 (11%) | `target_not_taught` 1.199, chunk định nghĩa không được trích 750, trích ngoài chunk 726 |

Ở xstk, nguyên nhân này là hệ quả của lỗi A2 "Cách giải" đã thấy ở tập giữ lại: đích không được coi là "được dạy". 33/57 cạnh vàng nằm trong
cặp ứng viên của xstk rơi vào nhóm hoãn.

## 3. Pass phụ đóng góp gì (E4, mốc)

| tài liệu | phương án | cạnh pass phụ | Q6 | Q7 | Q7b | bao đóng P | bao đóng R |
|---|---|---:|---:|---:|---:|---:|---:|
| doc-1 | LLM v3 | 468 | 0,103 | 0,667 | 0,877 | 0,874 | 0,740 |
| | không pass phụ | 0 | 0,103 | 0,213 | 1,000 | 1,000 | 0,359 |
| doc-2 (en) | LLM v3 | 1.060 | 0,228 | 0,395 | 0,869 | 0,800 | 0,294 |
| | không pass phụ | 0 | 0,228 | 0,272 | 0,852 | 0,846 | 0,162 |
| xstk | LLM v3 | 171 | 0,550 | 0,414 | 0,644 | 0,636 | 0,214 |
| | không pass phụ | 0 | 0,550 | 0,113 | 0,833 | 0,857 | 0,061 |
| doc-4 | LLM v3 | 1.473 | 0,157 | 0,322 | 0,606 | 0,584 | 0,459 |
| | không pass phụ | 0 | 0,157 | 0,185 | 0,849 | 0,852 | 0,289 |

Q6 không đổi ở mọi tài liệu. Toàn bộ giá trị của pass phụ nằm ở Q7 và độ phủ bao đóng.

## 4. Luật đơn và mô hình trên mọi cặp (E1, E2)

- **E1, luật đơn so với cạnh v3:**
  - "tên X trong cửa sổ Y": P 0,27–0,37, R 0,40–0,47 ở tài liệu tiếng Việt;
  - trích dẫn có hướng: R cao hơn, P thấp hơn;
  - "X đứng trước Y cùng mục": gần như vô dụng.
- **E2, hồi quy logistic và LightGBM trên mọi cặp đã hỏi:** F1 mức cặp so với cạnh v3 chỉ 0,34–0,45; trần, tức ngưỡng tốt nhất trên chính
  tài liệu đo, là 0,36–0,53. Đặc trưng cấu trúc không tái tạo được phán quyết LLM trên toàn bộ cặp, nên bài toán được thu hẹp ở mục 5.
- **Luật "tên X trong cửa sổ Y" đi đầu cuối** (không học, mọi ứng viên thành cạnh cứng):
  - độ phủ ngang hoặc hơn LLM (doc-4 bao đóng R 0,591 so với 0,459; doc-2 Q7 0,506 so với 0,395);
  - độ chính xác thấp hơn ở doc-1, xstk, doc-4; riêng doc-2 cao hơn (0,920 so với 0,800).

## 5. Bộ kiểm cạnh cứng (E2b)

**Ứng viên.** Dòng X→Y mà:
- hợp đồng cho phép: đích được dạy hoặc chưa rõ, hai đầu học được;
- tên X có trong cửa sổ định nghĩa của Y.

**Nhãn** (so ba loại, học trên bốn tài liệu tiếng Việt):
- `v3`: v3 tạo cạnh X→Y;
- `y-dinh`: có thứ tự trả `create` X→Y (kể cả phản hồi bị loại), không thứ tự nào trả chiều ngược;
- `y-dinh-cung`: như `y-dinh` nhưng mọi `create` là `can_de_hieu`.

So ba loại nhãn đầu cuối (ứng viên âm tiết, ngưỡng F1; mỗi ô là Q7 / Q7b / bao đóng P / bao đóng R):

| nhãn | doc-1 | xstk | doc-4 |
|---|---|---|---|
| `v3` | 0,650 / 0,720 / 0,792 / 0,756 | 0,418 / 0,367 / 0,513 / 0,204 | 0,520 / 0,546 / 0,570 / 0,541 |
| `y-dinh` | 0,676 / 0,725 / 0,789 / 0,771 | 0,432 / 0,281 / 0,420 / 0,214 | 0,552 / 0,518 / 0,536 / 0,566 |
| `y-dinh-cung` | 0,781 / 0,590 / 0,682 / 0,885 | 0,466 / 0,323 / 0,442 / 0,235 | 0,548 / 0,620 / 0,607 / 0,572 |

Không loại nhãn nào thắng ở mọi nơi. `y-dinh-cung` được chọn vì lý do thiết kế:
- phép chấm chỉ tính cạnh cứng, và bộ lắp cạnh chỉ tạo cạnh cứng;
- LLM ghi nhiều cạnh nhắc tên là `cong_cu` (doc-1: 215/468), nên học "có cạnh" sẽ biến cả các cạnh đó thành cạnh cứng.

Các lượt sau (ứng viên theo ranh giới từ) chỉ chạy với nhãn này.

**Mô hình.** LightGBM (300 cây, 15 lá, `is_unbalance`). Hồi quy logistic kém hơn rõ: AP thấp hơn 0,05–0,12.

**AP so với nhãn `y-dinh-cung`, ứng viên theo ranh giới từ.**

| tài liệu | AP | tỉ lệ dương nền |
|---|---:|---:|
| doc-1 | 0,60 | 0,36 |
| nhap-mon-ml | 0,48 | 0,23 |
| xstk | 0,71 | 0,39 |
| doc-4 | 0,34 | 0,22 |

**Tách từ.** Khớp tên theo ranh giới từ (underthesea; giữa các âm tiết của tên cho phép cách hoặc `_`, hai đầu không dính chữ):
- doc-1: 705 → 555 ứng viên; bỏ "Hiệu" 56, "Hợp" 33, "Nhân" 10;
- doc-4: 3.610 → 2.659; bỏ "Độ" 107, "Thời" 101, "Chất" 86, "Lượng" 56, "Đạo" 54, "Trường" 50;
- xstk: 185 → 176; nhap-mon-ml: 153 → 150;
- **không cạnh vàng nào bị bỏ.**

Lỗi còn lại của bộ tách từ nằm ở mép tên. Ví dụ "Mức ý nghĩa" bị gộp với từ kế bên, nên vài ứng viên đúng bị loại (xstk: 3 cạnh v3).

**Embedding tại máy** (`multilingual-e5-base`, 7 đặc trưng cosine: tên X với câu neo Y, hai câu neo…) không tăng AP: doc-1 0,557 so với 0,570.
Không dùng ở bản đề xuất.

**Độ quan trọng của đặc trưng (gain)** xếp đầu theo thứ tự:
- chênh thứ tự định nghĩa;
- đồng xuất hiện (Jaccard);
- trọng số kênh dense của cặp cụm;
- độ trải của X;
- số câu cửa sổ có tên X theo ranh giới từ.

Trước khi tách từ, "độ dài tên X" đứng đầu; đó là dấu hiệu của lỗi khớp âm tiết.

## 6. Đầu cuối trên vàng (E4)

Bản đề xuất gồm bốn phần:
- ứng viên theo ranh giới từ;
- LightGBM học ý định cạnh cứng;
- ngưỡng hiệu chỉnh;
- lắp cạnh tất định qua `validate_main_proposals`.

Cách lắp cạnh: câu trích là câu của cửa sổ có tên X gần câu neo nhất; `can_de_hieu`, `trong_dinh_nghia`; cặp xét theo thứ tự và tỉa như v3.

| tài liệu | phương án | cạnh phụ | Q7 | Q7b | bao đóng P (Wilson 95%) | bao đóng R (Wilson 95%) |
|---|---|---:|---:|---:|---|---|
| doc-1 | LLM v3 | 468 | 0,667 | 0,877 | 0,874 (0,80–0,92) | 0,740 (0,66–0,81) |
| | luật cửa sổ, âm tiết | 420 | 0,588 | 0,718 | 0,727 (0,64–0,80) | 0,672 (0,59–0,75) |
| | luật cửa sổ, từ | 357 | 0,562 | 0,554 | 0,647 (0,56–0,72) | 0,656 (0,57–0,73) |
| | ML, âm tiết, ngưỡng F1 | 298 | 0,781 | 0,590 | 0,682 (0,61–0,75) | 0,885 (0,82–0,93) |
| | ML, từ, ngưỡng F1 | 300 | 0,610 | 0,663 | 0,724 (0,64–0,80) | 0,702 (0,62–0,77) |
| | ML, từ, ngưỡng tỉ lệ | 140 | 0,668 | 0,817 | 0,837 (0,75–0,90) | 0,664 (0,58–0,74) |
| | **ML, từ, ngưỡng hiệu chỉnh** | 167 | 0,672 | 0,802 | 0,815 (0,73–0,88) | 0,672 (0,59–0,75) |
| xstk | LLM v3 | 171 | 0,414 | 0,644 | 0,636 (0,47–0,78) | 0,214 (0,14–0,30) |
| | luật cửa sổ, từ | 117 | 0,553 | 0,330 | 0,450 (0,33–0,57) | 0,276 (0,20–0,37) |
| | ML, từ, ngưỡng F1 | 88 | 0,306 | 0,287 | 0,432 (0,30–0,58) | 0,194 (0,13–0,28) |
| | **ML, từ, ngưỡng hiệu chỉnh** | 51 | 0,195 | 0,511 | 0,593 (0,41–0,76) | 0,163 (0,10–0,25) |
| doc-4 | LLM v3 | 1.473 | 0,322 | 0,606 | 0,584 (0,50–0,67) | 0,459 (0,38–0,54) |
| | luật cửa sổ, âm tiết | 1.590 | 0,458 | 0,507 | 0,522 (0,45–0,59) | 0,591 (0,51–0,67) |
| | luật cửa sổ, từ | 1.428 | 0,544 | 0,675 | 0,755 (0,67–0,83) | 0,503 (0,43–0,58) |
| | ML, từ, ngưỡng F1 | 1.372 | 0,578 | 0,714 | 0,772 (0,69–0,84) | 0,553 (0,48–0,63) |
| | **ML, từ, ngưỡng hiệu chỉnh** | 701 | 0,595 | 0,720 | 0,717 (0,62–0,79) | 0,478 (0,40–0,56) |

**Cách đọc bảng:**
- Ở doc-4, chỉ riêng **luật cửa sổ theo ranh giới từ**, chưa học gì, đã hơn LLM ở cả bốn chỉ số. Với luật, khớp âm tiết là nguồn lỗi lớn
  nhất: chuyển sang ranh giới từ nâng bao đóng P từ 0,522 lên 0,755. Lỗi "khái niệm khung" của LLM v3 ở tập giữ lại (ví dụ "Phép biện chứng duy
  vật → Chất") là chuyện khác: đó là phán đoán của LLM.
- Ở doc-1, bộ kiểm học được mang lại phần lớn độ chính xác: bao đóng P 0,647 với luật, 0,815 với ML.
- Ở xstk, mọi bản lọc đều đổi độ phủ lấy độ chính xác; luật không lọc cho độ phủ cao nhất (Q7 0,553). Vàng xstk rất nhiễu: hai người gán chỉ
  cùng chọn 20/87 cạnh.
- Ba chính sách ngưỡng (F1, tỉ lệ, hiệu chỉnh) đều chốt trên tài liệu học trước khi chấm. Việc **chọn** chính sách hiệu chỉnh vẫn dựa một phần
  vào bảng này, tức là đã nhìn vàng phát triển. Vì vậy phải khoá cấu hình trước khi chạy tập giữ lại mới.

**Quét ngưỡng** (`quet_nguong.py`; giữ 10–100% ứng viên; dùng để hiểu, **không** để chọn): đường cong không đơn điệu.
- Ví dụ doc-1: giữ 50% cho Q7 0,56; giữ 60% cho Q7 0,78.
- Lý do: thêm hay bớt vài cạnh đổi cách tỉa cặp, cách gỡ chu trình và rút gọn bắc cầu.
- Hệ quả: so một điểm ngưỡng dễ sai; mỗi kết luận cần nhiều tài liệu.

## 7. So mức cặp với vàng (không qua A9/A10)

Tập so là ứng viên cửa sổ mà cả hai đầu đều là đích vàng và **LLM đã thật sự phán**. ML được giữ đúng số cạnh cứng mà LLM tạo, rồi so độ chính
xác bao đóng:

| tài liệu | ứng viên | dương (bao đóng) | LLM v3 cứng | ý định cứng LLM | ML cùng số cạnh |
|---|---:|---:|---|---|---|
| doc-1 | 44 | 13 | 16 cạnh, P 0,75, R 0,92 | 19 cạnh, P 0,63 | P 0,50–0,56 |
| xstk | 36 | 10 | 11 cạnh, P 0,36, R 0,40 | 14 cạnh, P 0,43, R 0,60 | P 0,36–0,45 |
| doc-4 | 96 | 27 | 15 cạnh, P 0,47, R 0,26 | 29 cạnh, P 0,55, R 0,59 | P 0,33–0,60 |

- Phán đoán của ML ngang LLM ở xstk và doc-4, kém ở doc-1. Mẫu quá nhỏ để phân biệt chắc.
- **Ý định** của LLM đúng hơn cạnh LLM thực sự tạo được: doc-4 R 0,59 so với 0,26. Phần chênh rơi vì trượt kiểm.
- Lợi thế đầu cuối của bản không LLM ở doc-4 đến từ ba nguồn:
  - lắp cạnh không lỗi;
  - tách từ;
  - ngưỡng ít dè dặt hơn LLM (LLM chỉ giữ 15/96).

## 8. Tiền và thời gian

| khâu | pass phụ LLM v3 | pass phụ không LLM (vòng 1) |
|---|---|---|
| doc-4 (22.972 cặp) | 45,92 USD; 4,5–5 giờ trên Vertex; 38.556 bản ghi lời gọi | 0 USD; lắp cạnh 36 giây; trích đặc trưng và tách từ khoảng 1 phút |
| doc-1 (3.471 cặp) | khoảng 5,7 USD (16,4 triệu token vào, 1,06 triệu ra) | 0 USD; dưới 1 phút |

Mô hình LightGBM học trong vài giây. Mã nghiên cứu còn chậm ở hai chỗ, có thể tối ưu khi đưa vào sản phẩm:
- `validate_main_proposals` dựng lại từ điển nút mỗi lần gọi;
- tỉa cặp tìm đường lại từ đầu cho mỗi cặp.

## 9. Giới hạn và rủi ro

- **Vàng nhỏ và nhiễu.** Mỗi tài liệu có 40–72 cạnh vàng; xstk gần như không đồng thuận. Lựa chọn thiết kế (tách từ, nhãn, chính sách ngưỡng)
  đã nhìn vàng phát triển, nên cần tập giữ lại mới (T-01) trước khi kết luận.
- **Trần của thầy.** Mô hình học từ LLM flash-lite, nên chép cả lỗi của nó. Dữ liệu nhãn tốt hơn và đa lĩnh vực là đòn bẩy chính (D-01).
- **Đổi miền.** Bốn tài liệu tiếng Việt chỉ thuộc bốn lĩnh vực. Văn liệu (CPRL, PRELEARN) cho thấy F1 tụt mạnh khi đổi miền.
- **Thiếu cạnh cứng không nguyên văn.** Bí danh lạ, viết tắt, đại từ, diễn đạt khác: LLM có 20–38% cạnh cứng như vậy, bản không LLM chưa có.
- **Chưa có cạnh mềm** cho danh sách "công cụ".
- **Phụ thuộc upstream LLM.** Đặc trưng dùng nút, câu neo, mention map do A3/A4/C8 (LLM) tạo. Seminar (toàn Pha A không LLM) phải đo lại trên
  upstream không LLM.
- **Giấy phép.** underthesea giấy phép Apache-2.0, chạy thuần Python, hợp với backend sản phẩm. VnCoreNLP chưa thử.
- **Cùng lỗi khớp âm tiết ở A6.** Kênh exact của mention map (A6) mắc đúng lỗi này. Nó sinh cặp `contact` và trích dẫn sai, làm phình số cặp.
  Sửa ở A6 sẽ bớt cặp và bớt nhiễu đặc trưng; ghi lại để làm khi tới A6.

## 10. Đề xuất bước tiếp

1. **Dữ liệu (chủ dự án):** giáo trình tiếng Việt đa lĩnh vực và nhãn theo [D-01](../task/v4/D-01-dac-ta-du-lieu-pass-phu.md). Hai cuốn để riêng
   làm tập giữ lại có vàng người (T-01).
2. **Vòng 2 (Claude, 0 USD trừ khi chạy luồng trên sách mới):**
   - học lại trên dữ liệu D-01;
   - thử bộ mã hoá chéo (PhoBERT hoặc multilingual-e5) đọc câu cửa sổ có đánh dấu X;
   - ứng viên không nguyên văn: bí danh, viết tắt, cosine câu–tên;
   - cạnh mềm từ ứng viên điểm trung bình;
   - đo ổn định qua nhiều seed.
3. **Vé triển khai cho nhân viên** sau vòng 2:
   - stage `a8-secondary-ml-v1` trong `src`: đặc trưng ở `domain`, mô hình đóng băng có băm trong config;
   - giữ stage LLM chọn được bằng cờ, để so;
   - nghiệm thu bằng chính bộ E4 này.
4. **Khoá cấu hình** trước khi chạy tập giữ lại mới, như T10.

## 11. Chạy lại

Mã nằm ở `scripts/pass-phu-ml/`. Kết quả nằm ở `tmp/pass-phu-ml/`, không commit vì chứa văn bản giáo trình.

```
# môi trường nghiên cứu riêng (không đụng .venv của dự án)
.tools/uv.exe venv tmp/venv-ml --python 3.12
.tools/uv.exe pip install --python tmp/venv-ml/Scripts/python.exe numpy==2.5.2 scipy==1.18.0 pandas==3.0.5 scikit-learn lightgbm \
    networkx==3.6.1 igraph==1.0.0 leidenalg==0.12.0 "pydantic-settings>=2.14,<3" openpyxl==3.1.5 underthesea pyvi
# E0: bảng cặp (bản có tách từ)
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/dung_bang_cap.py doc-1 nhap-mon-ml xstk-ch3-1 doc-4 --tach-tu
.venv/Scripts/python.exe scripts/pass-phu-ml/dung_bang_cap.py doc-2 doc-3
# E1–E2 trên mọi cặp; E2b bộ kiểm cạnh cứng
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/thi_nghiem_e1_e2.py
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/thi_nghiem_e2b.py --nhan=y-dinh-cung --mo-hinh=lightgbm --tach-tu
# E4: mốc, rồi bản đề xuất
.venv/Scripts/python.exe scripts/pass-phu-ml/phat_lai_e4.py <doc> llm-v3|khong
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/lap_canh.py <doc> --diem=tmp/pass-phu-ml/diem/lightgbm-y-dinh-cung-tach-tu/<doc>.csv \
    --nguong-tu=tmp/pass-phu-ml/diem/lightgbm-y-dinh-cung-tach-tu/nguong.json --chinh-sach=hieu-chinh --chi-cung --tach-tu
# quét ngưỡng; đặc trưng embedding (không dùng ở bản đề xuất)
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/quet_nguong.py <doc> <lượt điểm> [--tach-tu]
.venv/Scripts/python.exe scripts/pass-phu-ml/dac_trung_ngu_nghia.py
```

Phiên bản thư viện: scikit-learn 1.9.1, lightgbm 4.7.0, underthesea 9.5.0, multilingual-e5-base (Hugging Face, tải ngày 2026-10-05).
Seed 20261005.

**Lưu ý tái lập.**
- Các dòng "ML, âm tiết" ở mục 5 và 6 chạy lúc bảng chưa có ba đặc trưng tách từ (87 đặc trưng). Bảng hiện tại có 90 đặc trưng, nên chạy lại
  sẽ lệch chút ít; bản đề xuất (dòng "từ") chạy trên bảng hiện tại.
- Số E4 đã chạy lưu ở `tmp/pass-phu-ml/ket-qua/e4-chinh.jsonl` và `e4-tach-tu.jsonl`.
