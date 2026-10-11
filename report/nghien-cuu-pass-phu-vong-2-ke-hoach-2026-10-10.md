# Pass phụ A8 không LLM — kế hoạch vòng 2 (2026-10-10)

**Bối cảnh.** Ngày 2026-10-10, chủ dự án thôi dồn sức cho A1 và chuyển nguồn lực sang pass phụ A8 không LLM (vé 11, vòng 2), vì một bản pass phụ
phục vụ cả đồ án chuyên ngành lẫn seminar chuyên đề. Cùng ngày, chủ dự án báo gợi ý của thầy: lấy bộ dữ liệu tiên quyết công khai, nhờ agentic
dịch sang tiếng Việt và chuẩn hoá, rồi dùng để huấn luyện.

**Nền.** Báo cáo này nối tiếp [vòng 1](nghien-cuu-pass-phu-khong-llm-vong-1-2026-10-05.md) và [R-02](nghien-cuu-ml-dl-loc-cap-va-tien-quyet-2026-10-04.md).
Dữ liệu vòng 2 theo [đặc tả D-01](../task/v4/D-01-dac-ta-du-lieu-pass-phu.md). Agentic gán theo [hướng dẫn gán](huong-dan-agentic-gan-nhan-d01.md).

**Chủ dự án duyệt ngày 2026-10-10** bốn việc Claude đề xuất sau khi đọc phần nhãn đã có:
1. thêm bản 1.1 cho hướng dẫn gán (mục 1.5);
2. gán lại phiếu 1–240 của lượt A;
3. lượt B do Claude gán trên mẫu 15% phiếu;
4. nghiên cứu gợi ý của thầy và lập kế hoạch này.

**Phạm vi.** Mọi phép đo ở đây đều chỉ đọc, và không tốn tiền mô hình. Ở mục 2, chỉ tên khái niệm công khai được gửi tới Wikidata và Wikipedia;
văn bản giáo trình không đi đâu.

## Tóm tắt

1. **D-01 đang gán; tốc độ đủ, chất lượng có hai vấn đề đã xử lý.**
   - Agentic tự chia lô 8 phiếu cho subagent. Nhịp đo được từ 2.500 tới 10.000 cặp/giờ, tuỳ số subagent chạy cùng lúc (mục 1.1). Lượt A cần
     thêm từ 6 tới 25 giờ chạy.
   - **Lượt A không đồng nhất.** Phiếu 1–240 có tỉ lệ `khong` trong cửa sổ 3–16%, các khối từ phiếu 241 có 24–42%, dù cơ cấu lĩnh vực như nhau.
     Agentic đang gán lại 1–240.
   - **Một kiểu lỗi có hệ thống.** Agentic gán `can_de_hieu` khi câu căn cứ chỉ định nghĩa X: anh em của Y, hay X định nghĩa qua Y. Đã thêm
     ca khó 12 và ví dụ 10 vào hướng dẫn gán (bản 1.1).
   - **Nhãn nhiễu.** Cùng mô hình nhưng khác ngữ cảnh, phần gán lại so với nhãn cũ chỉ đạt kappa 0,43 (năm nhãn), 0,55 (cạnh cứng), và 0,09 riêng
     `cong_cu`. Trên 23 cặp phiếu kiểm đầu tiên, độ chính xác cạnh cứng chỉ khoảng 0,4. Mẫu còn nhỏ.
   - Lượt B do Claude gán, trong một gói ngoài repo: 956 phiếu, 10.178 cặp, gồm cả 83 phiếu kiểm.
2. **Gợi ý của thầy.** Kiểm 11 bộ công khai (mục 2.1). Dịch nhãn cặp tên khái niệm không giúp được bài toán cửa sổ, vì hai lưu ý của R-02 vẫn còn
   nguyên. Cách khả dĩ nhất không cần dịch:
   - **chiếu AL-CPL sang Wikipedia tiếng Việt**, đúng cách ITA-PREREQ đã làm cho tiếng Ý, lấy đoạn mở đầu của trang làm cửa sổ định nghĩa;
   - 374/545 khái niệm có trang tiếng Việt, nhưng chỉ ra **407 mẫu dùng được**, nhỏ hơn D-01 khoảng 160 lần. 68% số dương của AL-CPL là quan hệ bắc
     cầu (chỉ 646/2.002 cạnh là trực tiếp);
   - vì vậy với A8, bộ này chỉ là một nhánh ablation rẻ, không phải nguồn dữ liệu.

   Gợi ý dịch hợp nhất với **DEFT cho khâu C8 của seminar**: nhãn theo câu nên giữ nguyên khi dịch. Việc này để sau, khi seminar làm C8. Phần
   lớn các bộ dùng CC BY-NC-SA 4.0, nên chỉ dùng cho nghiên cứu; dùng trong sản phẩm thì chủ dự án quyết.
3. **Thí nghiệm vòng 2** (mục 3), gồm:
   - LightGBM học lại trên D-01, chia theo sách;
   - cross-encoder đọc cửa sổ có đánh dấu X;
   - ứng viên không nguyên văn, cạnh mềm, nhiều seed;
   - ablation theo nguồn nhãn: ý định LLM v3, agentic A, A∩B, có và không VI-AL-CPL.

   Đo đầu cuối trên vàng phát triển. Kết luận chất lượng cuối cần T-01.
4. **Máy.** LightGBM chạy trên laptop. Cross-encoder cần máy GPU 4 GB của chủ dự án. Ước của Claude, chưa thử:
   - PhoBERT-base (135 triệu tham số) vừa tinh chỉnh toàn bộ;
   - XLM-R base và multilingual-e5-base (278 triệu) không vừa nếu tinh chỉnh toàn bộ với Adam, phải đóng băng lớp embedding hoặc dùng LoRA.
5. **Lịch** (mục 5):
   - Vòng 2 không cần đợi đủ 65.525 cặp. Phiếu đã xáo, nên phần đã gán là mẫu ngẫu nhiên; đường học theo cỡ dữ liệu sẽ cho biết có cần gán hết
     không.
   - **Đường găng là T-01**, vàng người trên hai cuốn giữ lại. T-01 không phụ thuộc D-01 và bắt đầu được ngay.

---

## 1. D-01: trạng thái và chất lượng lượt A

Số trong mục này đo từ `tmp/d01-gan-nhan/` lúc 17:24–18:10 ngày 2026-10-10, chỉ đọc. Khoá phiếu kiểm (`khoa.jsonl`) chỉ Claude đọc.

### 1.1 Tiến độ và tốc độ

Agentic lượt A là OpenAI Codex / GPT-6. Từ khoảng 17:25, phiên chính chia lô 8 phiếu cho subagent; mỗi lô ghi một tệp `agent-<từ>-<đến>.jsonl`,
rồi phiên chính ghép dần vào `nhan-A.jsonl`.

| giờ | cặp lượt A khác nhau | cặp gán lại (phiếu 1–240) | nguồn |
|---|---:|---:|---|
| 17:24 | 3.203 | — | bàn giao phiên trước |
| 17:30 | 3.798 | — | đếm theo khoá `(phieu_id, x_id)` |
| 17:59 | 5.000 | 380 | như trên |
| 18:04 | 5.000 | 1.271 | như trên |
| 18:06 | 5.000 | 1.527 | như trên |

Nhịp đổi theo số subagent chạy cùng lúc:
- từ 17:30 tới 17:59, lượt A tăng khoảng 2.500 cặp/giờ;
- từ 17:59 tới 18:06, agentic dồn sức gán lại: khoảng 1.150 cặp trong 7 phút (cỡ 10.000 cặp/giờ), còn phần chưa gán đứng yên.

Với khoảng 60.500 cặp còn lại, lượt A cần thêm từ cỡ 6 giờ (nếu giữ nhịp cao) tới 25 giờ (nhịp thấp).

Lần báo miệng đầu tiên của Claude (khoảng 8.700 cặp/giờ, xong trong 7–10 giờ) dựa trên phép đếm **sai**: đếm dòng trên mọi tệp đã tính hai lần các
lô subagent đã ghép vào `nhan-A.jsonl`.

### 1.2 Lượt A không đồng nhất

Bảng dưới chia phần phiên chính đã gán thành khối 60 phiếu theo thứ tự trong `phieu.jsonl`, chỉ tính cặp có tên X trong cửa sổ:

| phiếu | cặp trong cửa sổ | `can_de_hieu` | `cong_cu` | `khong` | `khop_nham` |
|---|---:|---:|---:|---:|---:|
| 1–60 | 425 | 47% | 27% | 16% | 10% |
| 61–120 | 340 | 75% | 16% | 3% | 6% |
| 121–180 | 342 | 54% | 29% | 8% | 8% |
| 181–240 | 356 | 55% | 25% | 14% | 6% |
| 241–300 | 342 | 39% | 15% | 39% | 7% |
| 301–360 | 392 | 45% | 20% | 31% | 3% |

Hai điểm loại trừ khả năng do nội dung:
- Phiếu đã được xáo khi xuất. Cơ cấu lĩnh vực của phiếu 1–240 và 241–420 gần như y hệt, cùng 6,1 ứng viên trong cửa sổ mỗi phiếu.
- Các lô subagent làm từ phiếu 313 cũng có tỉ lệ `khong` 36–42%, như phiên chính sau phiếu 240.

Khối 10 phiếu cho thấy chỗ đổi nằm quanh phiếu 221–231. Đây cũng là lúc `ghi-chu-A.md` được tạo (16:11, đã xong 227 phiếu). `kiem-A.txt` ghi số cặp
từng lên xuống ở giai đoạn đầu (1.407 → 380 → … → 447 → 1.529), tức tệp nhãn từng bị viết lại.

**So sớm phần gán lại** (chụp lúc 18:05:50: 136 phiếu đầu đã gán lại, 1.527 cặp). Cùng mô hình, khác ngữ cảnh, đồng thuận chỉ ở mức trung bình:

| phép so | khớp | Cohen's kappa |
|---|---:|---:|
| năm nhãn | 0,64 | 0,43 |
| cạnh cứng: `can_de_hieu` so với còn lại | 0,80 | 0,55 |
| có cạnh: `can_de_hieu` hoặc `cong_cu` so với còn lại | 0,71 | 0,45 |
| `khong` so với còn lại | — | 0,47 |
| `khop_nham` so với còn lại | — | 0,42 |
| `cong_cu` so với còn lại | — | **0,09** |

Bản gán lại chặt hơn hẳn. Trong 852 cặp trong cửa sổ:
- `can_de_hieu` giảm từ 59% xuống 41%, `khong` tăng từ 9% lên 42%;
- `cong_cu` giảm từ 24% xuống 7%, thấp cả so với các khối từ phiếu 241 (15–20%);
- trên cả 1.527 cặp, kể cả ứng viên ngoài cửa sổ, `nguoc` tăng từ 0 lên 28 cặp.

Chưa đủ vàng để biết bản nào gần đúng hơn. Hai hệ quả cho vòng 2:
- nhãn agentic nhiễu ở mức kappa khoảng 0,4–0,55, quanh cận dưới của đồng thuận người theo PREAP (0,45–0,71, R-02);
- `cong_cu` gần như không ổn định (kappa 0,09), nên cạnh mềm (E8) phải đo thận trọng, và có thể phải gộp `cong_cu` với `khong` khi học cạnh cứng.

### 1.3 Lỗi có hệ thống: căn cứ là câu định nghĩa X

Cửa sổ định nghĩa thường chép cả câu định nghĩa các khái niệm nằm cạnh Y, nhất là trong mục phân loại. Agentic hay gán `can_de_hieu` cho X chỉ vì
cửa sổ định nghĩa X. Lý do ghi kiểu "câu k định nghĩa X…" thay vì nói định nghĩa Y dùng X thế nào. Ba phiếu Claude đọc tận nơi:
- Y = "Oligosaccharide không khử". Homooligosaccharide, heterooligosaccharide (một phép phân loại khác), oligosaccharide khử (anh em) và
  disaccharide đều thành `can_de_hieu`.
- Y = "Kích thước lắp đặt". Bốn loại kích thước anh em trong cùng mục (khuôn khổ, lắp ráp, giới hạn, qui cách) đều thành `can_de_hieu`.
- Y = "Liên kết động". "Stub" được định nghĩa qua Y (đúng ra là `nguoc`) mà thành `can_de_hieu`.

Cặp lệch vàng đầu tiên trên phiếu kiểm mà Claude đọc tận nơi cũng thuộc kiểu này: lý do tả chiều ngược mà nhãn là `can_de_hieu`. Lỗi này lan tới
đâu thì có hai số:
- **Chỉ báo cấu trúc:** 116/1.483 nhãn `can_de_hieu` (8%) trích đúng câu `x_dinh_nghia` của X mà không phải câu neo của Y.
- **Đọc mẫu ngẫu nhiên** 20 nhãn `can_de_hieu` trong cửa sổ: Claude thấy 2 sai rõ và 2 ca biên, tức 16–18/20 đúng. Đây là phán xét của Claude, không
  phải vàng.

Vậy lỗi tập trung ở mục phân loại, không lan khắp tệp. Nhưng nó rơi đúng vào loại mẫu âm khó (anh em, đối chiếu) mà bộ kiểm cạnh cứng cần học.

### 1.4 Phiếu kiểm và phiếu lặp

Phiếu kiểm và phiếu lặp nằm rải trong tệp, nên tới lúc đo mới có rất ít.

**Phiếu kiểm** (18:05: 6/83 phiếu, 23 cặp). Quy `can_de_hieu` là có cạnh:
- lượt A gốc khớp vàng 15/23; thay phần đã gán lại thì 16/23;
- vàng có cạnh: 6 cặp, lượt A bắt được 4 (5 cặp trong cửa sổ, 1 ngoài);
- vàng không có cạnh mà ứng viên trong cửa sổ: 10 cặp, lượt A gốc gán `can_de_hieu` 6 cặp, bản gán lại 5 cặp.

Độ chính xác cạnh cứng trên phiếu kiểm vì vậy chỉ khoảng 0,4. Mẫu rất nhỏ và chỉ từ ba tài liệu kiểm, nhưng cùng chiều với lỗi ở mục 1.3.

**Phiếu lặp:** 9 cặp so được, cả 9 giống nhau (đo lúc 17:30).

Phiếu kiểm nhận ra được qua ba dấu hiệu (lĩnh vực, ít ứng viên, `doc_id` riêng), nên độ đúng đo trên chúng có thể lạc quan
([kiểm thử vé 12](kiem-thu-ve-12-13-14-a1-mo-rong-2026-10-08.md)).

### 1.5 Việc đã làm sau khi chủ dự án duyệt

Bốn việc đã làm:
- **Hướng dẫn gán bản 1.1:** thêm ca khó 12 và ví dụ 10 (tự soạn, nhạc lý, đã soát không trùng phiếu). Không đổi luật cũ, chỉ nói rõ cách áp ca 2,
  ca 3, ca 11 khi cửa sổ có câu định nghĩa khái niệm khác.
- **[Bàn giao bổ sung](ban-giao-agentic-d01-bo-sung-2026-10-10.md) cho agentic lượt A:**
  - gán lại phiếu 1–240 bằng subagent mới, ghi vào `gan-lai-*.jsonl`;
  - giữ nguyên nhãn cũ trong `nhan-A.jsonl`, làm số đo "cùng mô hình, khác ngữ cảnh";
  - gộp cuối vào `nhan-A-gop.jsonl`.

  Agentic đã bắt đầu gán lại lúc khoảng 17:55.
- **Lượt B:** do Claude gán, trong một phiên Claude Code mở riêng tại `Desktop\d01-luot-B\`, ngoài repo.
  - Đặt ngoài repo để phiên đó không nạp bộ nhớ dự án và không thấy `khoa.jsonl` hay nhãn lượt A. Phiên đã đọc khoá (phiên phân tích này) không
    gán.
  - Mẫu gồm 956 phiếu, 10.178 cặp: 831 phiếu thật (15% mỗi sách, chia đều 16 sách), cả 83 phiếu kiểm, và 42 phiếu lặp có phiếu gốc trong mẫu.
    Chọn bằng `scripts/pass-phu-ml/chon_mau_luot_b.py`, seed 20261010.
  - Gửi phiếu cho Anthropic là quyết định của chủ dự án; mở phiên lượt B nghĩa là đồng ý.
- **Vì sao chọn Claude cho lượt B, không chọn Gemini:**
  - Claude khác họ mô hình với GPT-6 của lượt A;
  - Gemini flash-lite là thầy của nhãn LLM v3, nên A∩B sẽ dính với nhãn LLM v3;
  - Gemini Pro thì trái luật chỉ dùng flash-lite.

  Đổi lại, Claude cùng họ với phiên phân tích. Khi phân xử bất đồng A/B, Claude phải ghi rõ đó là phán xét của mình, hoặc giao lượt C cho bên thứ
  ba.

**Bản 1.1 có tác dụng không** (đo lúc 18:10). Chỉ báo ở mục 1.3 là tỉ lệ nhãn `can_de_hieu` trích câu định nghĩa X mà không phải câu neo Y. Bảng
dưới xem chỉ báo này trước và sau hai mốc: chỗ đổi nhịp quanh phiếu 230, và bản 1.1.

| nhóm | chỉ báo | `can_de_hieu` trong cửa sổ | `cong_cu` | `khong` | cặp trong cửa sổ |
|---|---:|---:|---:|---:|---:|
| A, phiếu 1–240 (trước chỗ đổi) | 93/989 = 9,4% | 57% | 25% | 11% | 1.463 |
| A, phiếu 241–437 (sau chỗ đổi, trước 1.1) | 33/642 = 5,1% | 46% | 18% | 30% | 1.210 |
| A, từ phiếu 438 (sau 1.1) | 1/34 = 2,9% | 36% | 7% | 51% | 88 |
| gán lại phiếu 1–240 (sau 1.1) | 14/479 = 2,9% | 40% | 7% | 43% | 1.088 |

Bảng cho thấy hai điều:
- Chỉ báo giảm qua cả hai mốc, đúng hướng bản 1.1 nhắm tới. Đây là số quan sát độc lập, không phải lời agentic tự báo.
- `cong_cu` cũng giảm từ 18% xuống 7% sau bản 1.1, dù bản 1.1 không nói gì về `cong_cu`. Có thể bản 1.1 làm agentic dè dặt quá tay.
  - Với cạnh cứng thì không sao, vì `cong_cu` và `khong` đều là âm.
  - Với cạnh mềm (E8) thì đáng lo. Lượt B cũng dùng bản 1.1, nên phép so A∩B không phát hiện được hiệu ứng này. Chỉ nhãn A trước 1.1 cho phép
    đối chiếu.

### 1.6 Kiểm khi lượt A và lượt B xong

Thứ tự kiểm khi hai lượt xong:
1. Kiểm định dạng `nhan-A-gop.jsonl` và `nhan-B.jsonl` không có `--mot-phan`.
2. Độ đúng trên phiếu kiểm của A và của B, ghi kèm lưu ý lạc quan ở mục 1.4. Độ tự nhất quán trên phiếu lặp.
3. Đồng thuận A cũ với A gán lại trên phiếu 1–240 (khoảng 2.500 cặp): cùng mô hình, khác ngữ cảnh.
4. Cohen's kappa A–B theo nhãn và theo lĩnh vực, trên 831 phiếu thật của mẫu.
5. Chỉ báo "trích câu định nghĩa X" (mục 1.3) trước và sau bản 1.1.
6. Đọc tận nơi một mẫu cặp lệch. Phân xử theo đặc tả D-01: lượt thứ ba, hoặc để `khong_ro`.

---

## 2. Gợi ý của thầy: dữ liệu công khai dịch sang tiếng Việt

### 2.1 Kiểm nguồn và giấy phép

Bảng dưới kiểm 11 bộ: chín bộ ở R-02 §2.3, cộng hai bộ trích định nghĩa ở R-02 §4.2. Giấy phép đọc từ README hoặc tệp LICENSE của kho chính thức
ngày 2026-10-10.

| bộ | văn bản kèm theo | nhãn | cỡ (đếm hoặc theo bài) | giấy phép | dùng được cho |
|---|---|---|---|---|---|
| CrowdComp [5] | không; tên trang Wikipedia | kết quả HIT Mechanical Turk, 5 miền | 1.600 cặp, 206 dương (R-02) | CC BY-NC-SA 4.0 (kho RefD-dataset) | không: chỉ tên |
| Course [4] | không | cặp dương và âm, CS và MATH | CS 678/108, MATH 658/75 (R-02) | CC BY-NC-SA 4.0 (kho RefD-dataset) | không: chỉ tên |
| University Course [6] | mô tả môn học của 11 trường | 3 người gán, **3 lớp có chiều**: B→A, A→B, không | 3.544 cặp, 521 khái niệm; đa số: 1.018 B→A, 669 A→B, 1.657 không, 200 không có đa số (Claude đếm) | CC BY-NC-SA 4.0 | phụ: chiếu sang Wikipedia như AL-CPL |
| MOOC [8] | phụ đề Coursera | cặp, κ 0,59–0,65 | 128–244 khái niệm mỗi miền | không tìm thấy nơi tải công khai | không |
| AL-CPL [1] | không có văn bản; khái niệm là tiêu đề Wikipedia tiếng Anh | chuyên gia sửa; đã mở rộng bắc cầu và cặp đảo | 4 miền, 545 khái niệm khác nhau, 6.529 cặp, 2.002 dương (kho) | CC BY-NC-SA 4.0 | chiếu sang Wikipedia tiếng Việt: 407 mẫu, chỉ làm ablation (mục 2.3) |
| LectureBank [7] | tệp bài giảng, chỉ có URL; 208 chủ đề có URL Wikipedia | cặp chủ đề, 0/1 | 42.750 cặp, 921 dương (Claude đếm) | **không ghi giấy phép** | chỉ đọc tham khảo |
| ITA-PREREQ/PRELEARN [2], [3] | trang Wikipedia tiếng Ý | chiếu từ AL-CPL | 457 khái niệm, 6.607 cặp (R-02) | cấp cho người tham gia khi xin; không có bản công khai | **tiền lệ phương pháp** cho mục 2.3 |
| MOOCCube [9] | MOOC tiếng Trung | cặp gán tay | 3.500 cặp (R-02) | kho MOOCCubeX ghi GPL-3.0 (giấy phép mã); điều khoản dữ liệu chưa rõ | không: tiếng Trung, quyền chưa rõ |
| Textbook của CPRL [10] | 6 giáo trình tiếng Trung × 3 miền | quan hệ | 84–139 khái niệm mỗi miền | bài ghi "will be publicly available later"; không tìm thấy | không |
| DEFT [11] | 21.303 câu giáo trình mở cnx.org, 7 môn | câu có định nghĩa không; thuật ngữ, định nghĩa | 28% câu có định nghĩa (R-02) | CC BY-NC-SA 4.0 ("Contact the authors for information on commercial use") | **C8 của seminar** (mục 2.4) |
| WCL [12] | câu Wikipedia tiếng Anh; bản tự gán EN/FR/IT | định nghĩa hay không | không ghi số trên trang tải | trang tải không ghi giấy phép, chỉ xin trích dẫn | phụ cho C8; quyền chưa rõ |

Hai lượt tìm ngày 2026-10-10 vẫn không thấy bộ tiên quyết hay bộ trích định nghĩa tiếng Việt công khai, khớp với R-02.

### 2.2 Dịch gỡ được gì, không gỡ được gì

R-02 §2.7 nêu ba lưu ý. Dịch chỉ gỡ lưu ý thứ ba (không có tiếng Việt). Hai lưu ý còn lại ảnh hưởng như sau.
- **Số F1 bị thổi do cách lấy âm.** Lưu ý này chỉ hại khi **đo** trên bộ ngoài. Khi **học**, ta chọn cặp theo đúng cách vòng 1 sinh ứng viên: X có tên
  trong cửa sổ định nghĩa của Y. Âm khi đó là âm tự nhiên, không phải cặp ngẫu nhiên. Không bao giờ báo số đo trên bộ ngoài như số chất lượng.
- **Nhãn theo kiến thức nền, không bám câu chữ.** Lưu ý này còn nguyên, và nặng thêm vì hai lẽ:
  - AL-CPL đã **mở rộng bắc cầu** (thêm (A, C) khi có (A, B) và (B, C)). Như vậy tiên quyết gián tiếp cũng thành dương, trái luật "chỉ quan hệ
    trực tiếp" của D-01. Claude đếm trên kho dữ liệu: đồ thị dương của cả bốn miền đều không có chu trình, và rút gọn bắc cầu chỉ còn
    **646/2.002 cạnh (32%)**: data mining 112/292, geometry 110/524, physics 179/487, precalculus 245/699. Cách giảm: chỉ lấy cạnh trong rút gọn
    bắc cầu làm dương, bỏ khỏi tập học các cặp chỉ dương nhờ bắc cầu.
  - Lỗi có hệ thống của agentic (mục 1.3) cũng đi theo hướng "liên quan là tiên quyết". Trộn thẳng dữ liệu ngoài vào tập học có thể đẩy mô hình
    thêm về hướng đó.
- **Lệch bài toán.** Bộ chỉ có cặp tên (CrowdComp, Course, LectureBank, MOOCCube) không cho cửa sổ để đọc. Dịch tên khái niệm không tạo ra cửa sổ.

Kết luận của Claude: không nên dịch các bộ cặp tên. Dữ liệu ngoài chỉ đáng dùng ở dạng có văn bản thật, và chỉ làm bước học trung gian, có
ablation. Văn liệu cho thấy học trung gian có thể giúp, nhưng không phải lúc nào cũng giúp: Pruksachatkun và cộng sự [14] thấy *"intermediate tasks
requiring high-level inference and reasoning abilities tend to work best"*.

### 2.3 Đề xuất A: VI-AL-CPL — chiếu AL-CPL sang Wikipedia tiếng Việt

**Tiền lệ.** ITA-PREREQ dựng đúng như vậy cho tiếng Ý [3]: *"we took the Italian version of the Wikipedia pages considered for AL-CPL, excluding
from the dataset those concepts (and the relations where they are involved) for which an Italian page was not available. Then, we mapped both positive
and negative relations"*. Văn bản tiếng Ý lấy bằng WikiExtractor từ bản dump tháng 1/2020.

**Cách dựng cho tiếng Việt** (đề xuất, chưa làm):
1. Liên kết liên ngôn ngữ (Wikidata) cho từng khái niệm AL-CPL → trang tiếng Việt.
2. Cửa sổ của A = đoạn mở đầu trang tiếng Việt của A. Đoạn này thường là câu định nghĩa, ví dụ "Ampe kế là dụng cụ đo cường độ dòng điện…".
3. Ứng viên = cặp (A, B) mà tên tiếng Việt của B có trong đoạn mở đầu của A, khớp theo ranh giới từ như vòng 1. Nhãn:
   - dương nếu (A, B) thuộc rút gọn bắc cầu của đồ thị dương;
   - bỏ, nếu (A, B) chỉ dương nhờ bắc cầu;
   - âm với các cặp âm của AL-CPL.
4. Dựng thành phiếu cùng định dạng D-01, để cross-encoder đọc cùng một kiểu đầu vào.

Không cần dịch, nên không cần agentic và không tốn tiền. Phần khái niệm thiếu trang tiếng Việt có thể nhờ agentic dịch đoạn mở đầu tiếng Anh sau,
nếu bước trên cho thấy có ích.

**Độ phủ đo ngày 2026-10-10** (`scratchpad`, Wikidata SPARQL và REST vi.wikipedia; chỉ gửi tên khái niệm công khai):
- 545 khái niệm khác nhau, **374 có trang tiếng Việt (69%)**, cả 374 đều có đoạn mở đầu (trung vị 284 ký tự). Đây là cận dưới: tiêu đề tiếng Anh là
  trang chuyển hướng chưa được giải.
- 4.139/6.529 cặp có trang tiếng Việt ở cả hai đầu. Chỉ **716 cặp** có tên B trong đoạn mở đầu của A (khớp theo ranh giới âm tiết, xấp xỉ; chưa
  tách từ như vòng 1).
- Trong 716 cặp đó: 273 dương trực tiếp, 309 chỉ dương nhờ bắc cầu (bỏ), 134 âm. **Còn 407 mẫu dùng được.**

| miền | cặp | cửa sổ | dương trực tiếp | chỉ bắc cầu | âm |
|---|---:|---:|---:|---:|---:|
| data mining | 826 | 17 | 9 | 3 | 5 |
| geometry | 1.681 | 190 | 50 | 114 | 26 |
| physics | 1.962 | 170 | 64 | 39 | 67 |
| precalculus | 2.060 | 339 | 150 | 153 | 36 |
| **tổng** | 6.529 | 716 | 273 | 309 | 134 |

**Kết luận của Claude:** 407 mẫu nhỏ hơn D-01 (65.525 cặp) khoảng 160 lần, và gần như chỉ thuộc toán và vật lý. Dịch thêm đoạn mở đầu tiếng Anh cho 171
khái niệm thiếu trang cũng chỉ nâng lên cỡ vài trăm mẫu nữa. Vì vậy VI-AL-CPL **không phải nguồn dữ liệu đáng kể cho A8**. Nó chỉ là một nhánh
ablation rẻ (E10): dữ liệu đã có sẵn, 0 USD. Kỳ vọng tác động của nó nhỏ.

**Cách dùng:** học trung gian cho cross-encoder rồi tinh chỉnh tiếp trên D-01, so với chỉ học D-01 (E10). Nhãn VI-AL-CPL là **nhãn người, nhưng theo
định nghĩa khác**: không gộp vào vàng, không dùng để chấm.

### 2.4 Đề xuất B: DEFT dịch cho khâu C8 của seminar (D-03, làm sau)

DEFT là bộ hợp nhất với gợi ý "dịch rồi huấn luyện", vì ba lẽ:
- Bài toán khớp một-một với C8: câu này có định nghĩa không, thuật ngữ nào.
- Nhãn gán theo câu, nên giữ nguyên khi dịch. Chỉ nhãn khoảng (thuật ngữ, định nghĩa) cần căn lại sau dịch.
- 21.303 câu giáo trình mở thuộc sinh học, lịch sử, vật lý, tâm lý, kinh tế, xã hội học, chính phủ; trùng nhiều lĩnh vực với D-01.

Việc này cần agentic dịch, và phục vụ C8 chứ không phục vụ A8. Đề xuất soạn D-03 (đặc tả dịch DEFT, theo mẫu D-01) khi seminar bắt đầu làm C8,
không phải bây giờ.

### 2.5 Giấy phép: chủ dự án quyết

Giấy phép quyết được làm và chia sẻ tới đâu:
- **CC BY-NC-SA 4.0** (AL-CPL, Course, CrowdComp, University Course, DEFT): được làm bản phái sinh (dịch, chiếu) với ba điều kiện: ghi công, phi
  thương mại, chia sẻ cùng giấy phép. Đồ án và seminar là việc học thuật, phi thương mại.
- **Wikipedia:** văn bản dùng CC BY-SA 4.0 cho sửa đổi từ 2023-06-07; sửa đổi cũ hơn giữ BY-SA 3.0 [15].
- **Bộ VI-AL-CPL ghép hai nguồn:** nhãn chịu BY-NC-SA, văn bản chịu BY-SA. Dùng nội bộ để nghiên cứu thì được. Nếu công bố, nên tách hai phần, mỗi
  phần giữ giấy phép riêng.
- **Mô hình học từ dữ liệu NC trong sản phẩm thương mại:** pháp lý chưa ngã ngũ. Ablation E10 cho biết dữ liệu NC có giúp không. Nếu giúp, chủ dự án
  quyết có đưa vào bản sản phẩm không.
- **LectureBank không ghi giấy phép:** chỉ đọc tham khảo, không phân phối lại.

---

## 3. Thí nghiệm vòng 2

### 3.1 Bài toán và nguồn nhãn

Bài toán giữ như vòng 1: với mỗi lần X có tên trong cửa sổ định nghĩa của Y, quyết X có là tiên quyết trực tiếp (cạnh cứng) của Y không. Vòng 2
thêm ba đầu ra: cạnh mềm `cong_cu`, chiều ngược `nguoc`, và ứng viên không nguyên văn (`trong_cua_so: false`).

Bốn nguồn nhãn, tất cả đều bạc hoặc lệch định nghĩa:

| nguồn | phạm vi | cỡ | ghi chú |
|---|---|---|---|
| ý định LLM v3 | doc-1, nhap-mon-ml, xstk, doc-4 | như vòng 1 | thầy là flash-lite; doc-1, xstk, doc-4 cũng là tài liệu đo |
| D-01 agentic A | 16 sách, 8 lĩnh vực | 65.525 cặp | bản gộp sau gán lại |
| D-01 A∩B | mẫu lượt B | 10.178 cặp | đồng thuận hai họ mô hình |
| VI-AL-CPL | Wikipedia tiếng Việt, 4 miền | 407 mẫu (273 dương) | nhãn người, định nghĩa khác |

**Xử lý nhãn nhiễu** (mục 1.2, 1.4). Ba điểm thiết kế:
- Mục tiêu học chính là nhị phân cạnh cứng: `can_de_hieu` so với còn lại, nơi đồng thuận cao nhất (kappa 0,55). Khi học cạnh cứng, `cong_cu` gộp
  với âm, vì kappa của nó chỉ 0,09.
- So ba cách dùng nhãn:
  - lượt A đơn;
  - đồng thuận A∩B;
  - nhãn mềm, lấy trung bình các lần gán cùng một cặp: A cũ và A gán lại trên phiếu 1–240, A và B trên mẫu lượt B.
- Thử confident learning (R-02 §3.4) để tìm nhãn nghi sai. Đọc tận nơi một mẫu cặp bị lọc trước khi tin.

**Bộ đặc trưng phải đổi.** `dung_bang_cap.py` của vòng 1 đọc artifact pass phụ và cạnh pass chính A8. Mười sáu sách D-01 dừng trước A8, vì chủ
dự án đồng ý bỏ A8 pass chính khi làm dữ liệu. Vòng 2 vì vậy:
- dựng bảng đặc trưng từ artifact danh tính của vé 12;
- bỏ nhóm đặc trưng dựa trên cạnh pass chính;
- đo lại vòng 1 khi không có nhóm này, để biết mất bao nhiêu.

### 3.2 Chia dữ liệu và cách đo

Ba tầng đo, mỗi tầng một vai:
- **Chọn mô hình:** chia nhóm theo sách trên D-01, không cuốn nào vừa học vừa đo. Số đo so với nhãn agentic chỉ cho biết học trò giống thầy tới đâu,
  nên chỉ dùng để chọn cấu hình.
- **Chất lượng phát triển:** bộ E4 của vòng 1. Thay `secondary_edges` trên doc-1, xstk, doc-4, phát lại A9 → A10, chấm trên vàng người. Khi đo một
  tài liệu, nhãn LLM v3 của nó không được ở tập học. Ba vàng này đã dùng để chọn thiết kế vòng 1, nên đây vẫn là số phát triển.
- **Kết luận cuối:** T-01, sau khi khoá cấu hình như T10.

Mọi bảng báo kèm Wilson 95% theo cặp bao đóng như vòng 1, và độ lệch giữa các seed.

### 3.3 Danh sách thí nghiệm

Bảng dưới xếp theo thứ tự làm. Mỗi dòng ghi cần gì và trả lời câu hỏi nào:

| mã | việc | cần | câu hỏi |
|---|---|---|---|
| E0' | dựng bảng đặc trưng cho 16 sách D-01 từ artifact vé 12; đo lại vòng 1 khi bỏ đặc trưng pass chính | laptop | mất gì khi không có cạnh pass chính? |
| E5 | LightGBM học trên D-01 (A gộp), chia theo sách; E4 trên doc-1, xstk, doc-4 | D-01 xong | nhãn agentic đa lĩnh vực có hơn ý định LLM v3 không? xstk có hết kém độ phủ không? |
| E6 | cross-encoder trên phiếu: tên Y, cửa sổ, X đánh dấu, `x_dinh_nghia`; đầu ra 5 nhãn; so và ghép với LightGBM | máy GPU | đọc văn bản có hơn đặc trưng cấu trúc không, và tốn bao nhiêu phút/cuốn trên CPU? |
| E7 | ứng viên không nguyên văn: bí danh, viết tắt, cosine câu–tên; học từ ứng viên `trong_cua_so: false` của D-01 | E5 | lấy lại được bao nhiêu trong 20–38% cạnh cứng LLM có mà vòng 1 thiếu? |
| E8 | cạnh mềm từ `cong_cu`, cho dòng "công cụ" | E5 | có thêm cạnh mềm mà không hại Q6, Q7b không? |
| E9 | 5 seed cho mỗi cấu hình chính; bootstrap theo sách | E5, E6 | khác biệt nào vượt nhiễu? |
| E10 | ablation nguồn nhãn: LLM v3 / A / A∩B (cùng cỡ, trên mẫu B) / có và không VI-AL-CPL trung gian | lượt B, VI-AL-CPL | nguồn nào đáng công gán? dữ liệu NC có giúp không? |

Mô hình mã hoá cho E6, theo giấy phép thẻ mô hình trên Hugging Face ngày 2026-10-10:
- `vinai/phobert-base` (MIT) cần đầu vào đã tách từ. Tách bằng underthesea (Apache-2.0) sẽ lệch với cách tách lúc huấn luyện trước (RDRSegmenter).
- `vinai/phobert-base-v2` dùng AGPL-3.0, chỉ dùng để so trong seminar, không đưa vào sản phẩm.
- `intfloat/multilingual-e5-base` và `FacebookAI/xlm-roberta-base` (MIT) không cần tách từ.

### 3.4 Số dùng để quyết gì

Số là thông tin, không phải cổng dừng. Mỗi kết quả dẫn tới một quyết định:
- E5 so với vòng 1 trên E4 → có nhận D-01 làm nguồn nhãn chính không.
- E6 → có thêm cross-encoder vào stage sản phẩm không, đánh đổi phút/cuốn trên CPU.
- E10 → có cần lượt B đầy đủ không, có dùng VI-AL-CPL không, và có dùng dữ liệu NC trong sản phẩm không (chủ dự án).

---

## 4. Máy và thời gian

Máy dùng cho từng phần như sau:
- **Laptop** (Ryzen 7 7730U, không CUDA): E0', E5, E7–E9 phần LightGBM, dựng VI-AL-CPL. Dùng `tmp/venv-ml`, không cài gói vào `.venv`.
- **Máy GPU 4 GB của chủ dự án** cho E6. Claude hỏi SSH khi tới E6, và ghi lại dữ liệu nào được chép lên máy, vì phiếu chứa văn bản giáo trình.
- **Ước bộ nhớ, chưa thử.** Tinh chỉnh toàn bộ với Adam, độ chính xác hỗn hợp, tốn khoảng 16 byte mỗi tham số trước khi tính activation.
  - PhoBERT-base (135 triệu tham số) cần khoảng 2,2 GB, vừa 4 GB với lô nhỏ, độ dài 256 và tích luỹ gradient.
  - XLM-R base và multilingual-e5-base (278–279 triệu, theo Hugging Face) cần khoảng 4,4 GB, **không vừa**. Phải đóng băng lớp embedding: lớp này
    chiếm khoảng 192 triệu tham số, do từ vựng 250 nghìn × 768. Hoặc dùng LoRA.
- **Suy luận trong sản phẩm chạy trên CPU.** Số cặp mỗi cuốn cỡ vài nghìn (doc-4: 2.659 ứng viên theo ranh giới từ). Phút/cuốn của cross-encoder trên
  CPU phải đo ở E6, rồi đặt cạnh 1–2 phút của LightGBM và 4,5–5 giờ của LLM v3.

## 5. Lịch và đường găng

Ba mạch chạy song song, không mạch nào phải đợi mạch kia:
1. **D-01.** Lượt A, gồm phần gán lại 1–240, còn từ 6 tới 25 giờ chạy (mục 1.1). Lượt B chạy độc lập, khi chủ dự án mở phiên tại
   `Desktop\d01-luot-B\`.
2. **Vòng 2 không cần đợi đủ 65.525 cặp.**
   - Phiếu đã được xáo khi xuất, nên phần đầu tệp đã gán là một mẫu ngẫu nhiên trên cả 16 sách.
   - Ngay bây giờ (0 USD): làm E0' và mã nạp nhãn D-01, chia theo sách.
   - Khi có khoảng 15–20 nghìn cặp, đã gồm phần gán lại, chạy E5 kèm **đường học theo cỡ dữ liệu**, học trên 10%, 25%, 50%… số cặp đã có.
   - Đường học phẳng thì đề xuất dừng lượt A sớm, tiết kiệm thời gian agentic. Đường học còn dốc thì gán tiếp.
3. **T-01 không phụ thuộc D-01**, bắt đầu được ngay (mục 5.1).

Kết luận chất lượng cuối chỉ có sau T-01. Không có T-01 thì vòng 2 chỉ báo được số phát triển.

### 5.1 T-01 cần gì

Theo giao thức vàng hiện có ([vé 04 của chuỗi A6–A8](../task/a6-a8-tien-quyet/04-bo-vang-excel-va-huong-dan-gan.md), [giao thức tập giữ lại
v3](../task/v3-lo-trinh-doc-duoc/T10-07v2-giao-thuc-tap-giu-lai.md)), T-01 gồm năm bước:
1. **Chủ dự án** xác nhận quyền dùng hai cuốn trong `document-data/test/` (Côn trùng đại cương, 92 trang; Thanh toán quốc tế, 113 trang), kể cả
   gửi lên Gemini. README của `document-data/` ghi metadata và quyền của hai cuốn này còn chờ bổ sung.
2. **Nhân viên** chạy luồng tới hết A5 (hoặc tới danh tính) trên hai cuốn. Có dry-run, chủ dự án duyệt chi. Nhân viên chỉ báo số đếm và chi phí,
   không đọc nội dung.
   - Tệp vàng gắn với `canonical_version` và `concept_hash` của artifact, nên luồng phía trước phải cố định từ đây.
   - Đề xuất không đợi vé 16: dùng cấu hình hiện tại và ghi lại. Vòng 2 chỉ đo A8, nên luồng phía trước chỉ cần cố định, không cần là bản cuối.
3. **Chủ dự án** chọn mỗi cuốn một chương. Lệnh `a8-gold-sheet --list-chapters` chỉ in số khái niệm đích theo chương. Mốc tham khảo: các chương vàng
   cũ có 26–47 khái niệm đích, mỗi người gán 35–65 cạnh.
4. **Hai người** gán mù bằng file Excel do `a8-gold-sheet` sinh và theo [hướng dẫn gán](../doc/huong-dan-gan-nhan-tien-quyet.md), rồi hội ý. Đóng băng
   JSON bằng `a8-gold-check` và ghi SHA-256.
5. **Claude** không mở gì của T-01 cho tới khi khoá cấu hình vòng 2.

Vàng T-01 phải do người gán. Nhãn agentic ở mục 1 nhiễu ở mức kappa 0,4–0,55, và học trò của vòng 2 học từ chính nhãn agentic. Đo học trò bằng một
lượt agentic khác chỉ cho biết hai agentic giống nhau tới đâu.

## 6. Cần chủ dự án quyết

Năm điểm cần quyết:
1. Mở phiên lượt B (đồng ý gửi phiếu cho Anthropic).
2. Dựng VI-AL-CPL (0 USD, chỉ gửi tên khái niệm công khai tới Wikidata và Wikipedia) và dùng dữ liệu CC BY-NC-SA cho nghiên cứu.
3. Cấp SSH máy GPU khi tới E6.
4. T-01 (mục 5.1): xác nhận quyền hai cuốn trong `test/`, chọn hai người gán, giao nhân viên chạy luồng tới A5. Claude soạn vé cho phần nhân viên
   nếu chủ dự án cần.
5. D-03 (dịch DEFT) khi seminar làm C8.

## 7. Sau vòng 2

Claude soạn vé triển khai stage `a8-secondary-ml-v1` trong `src/` theo quy trình spec → vé, đúng như mục 10 của vòng 1:
- đặc trưng ở `domain`;
- mô hình đóng băng có băm trong config;
- giữ stage LLM chọn được bằng cờ;
- nghiệm thu bằng bộ E4.

Nhân viên cài đặt, Claude kiểm thử.

## 8. Chạy lại

Các lệnh sau tái lập số của báo cáo:

```
# mẫu lượt B (cần khoa.jsonl; chỉ Claude chạy)
.venv/Scripts/python.exe -I scripts/pass-phu-ml/chon_mau_luot_b.py --phieu tmp/d01-phieu/phieu.jsonl --khoa tmp/d01-phieu/khoa.jsonl \
    --ra <gói>/phieu.jsonl --ds-ra tmp/d01-luot-B/chon.json
# VI-AL-CPL: tải AL-CPL, liên kết Wikidata, đoạn mở đầu vi.wikipedia (có đệm ở tmp/pass-phu-ml/vi-al-cpl/dem.json)
.venv/Scripts/python.exe -I scripts/pass-phu-ml/vi_al_cpl.py
```

Số ở mục 1 đo bằng script tạm trong scratchpad trên `tmp/d01-gan-nhan/` lúc 17:24–18:10. Tệp nhãn còn đang ghi, nên chạy lại sẽ ra số khác.

---

## Nguồn

Mọi trang mở ngày 2026-10-10. Các bài đã có trong R-02 không đọc lại, trừ chỗ ghi khác.

[1] C. Liang, J. Ye, S. Wang, B. Pursel, C. L. Giles, "Investigating active learning for concept prerequisite learning," in *Proc. AAAI (EAAI)*, 2018.
https://ojs.aaai.org/index.php/AAAI/article/view/11396 · dữ liệu: https://github.com/harrylclc/AL-CPL-dataset (README, mục License: CC BY-NC-SA 4.0).

[2] A. Miaschi, C. Alzetta, F. A. Cardillo, F. Dell'Orletta, "Linguistically-driven strategy for concept prerequisites learning on Italian," in
*Proc. BEA*, 2019, pp. 285–295. https://aclanthology.org/W19-4430/ — chỉ đọc tóm tắt.

[3] C. Alzetta, A. Miaschi, F. Dell'Orletta, F. Koceva, I. Torre, "PRELEARN @ EVALITA 2020: Overview of the prerequisite relation learning task for
Italian," in *Proc. EVALITA*, 2020. https://aclanthology.org/2020.evalita-1.54/ — đọc toàn văn mục dữ liệu.

[4] C. Liang, Z. Wu, W. Huang, C. L. Giles, "Measuring prerequisite relations among concepts," in *Proc. EMNLP*, 2015, pp. 1668–1674.
https://aclanthology.org/D15-1193/ · dữ liệu: https://github.com/harrylclc/RefD-dataset (CC BY-NC-SA 4.0).

[5] P. P. Talukdar, W. W. Cohen, "Crowdsourced comprehension: predicting prerequisite structure in Wikipedia," in *Proc. BEA*, 2012, pp. 307–315.
https://aclanthology.org/W12-2037/ · dữ liệu trong kho RefD-dataset.

[6] C. Liang, J. Ye, Z. Wu, B. Pursel, C. L. Giles, "Recovering concept prerequisite relations from university course dependencies," in *Proc. AAAI*,
2017, pp. 4786–4791. https://ojs.aaai.org/index.php/AAAI/article/view/10550 · dữ liệu: https://github.com/harrylclc/eaai17-cpr-recover (CC BY-NC-SA 4.0).

[7] I. Li, A. R. Fabbri, R. R. Tung, D. R. Radev, "What should I learn first: Introducing LectureBank for NLP education and prerequisite chain
learning," in *Proc. AAAI*, 2019. https://arxiv.org/abs/1811.12181 · dữ liệu: https://github.com/Yale-LILY/LectureBank (README không ghi giấy phép).

[8] L. Pan, C. Li, J. Li, J. Tang, "Prerequisite relation learning for concepts in MOOCs," in *Proc. ACL*, 2017, pp. 1447–1456.
https://aclanthology.org/P17-1133/

[9] J. Yu *et al.*, "MOOCCube: A large-scale data repository for NLP applications in MOOCs," in *Proc. ACL*, 2020.
https://aclanthology.org/2020.acl-main.285/ · kho kế nhiệm: https://github.com/THU-KEG/MOOCCubeX (GitHub nhận diện GPL-3.0).

[10] C. Jia, Y. Shen, Y. Tang, L. Sun, W. Lu, "Heterogeneous graph neural networks for concept prerequisite relation learning in educational data,"
in *Proc. NAACL*, 2021, pp. 2036–2047. https://aclanthology.org/2021.naacl-main.164/

[11] S. Spala, N. A. Miller, Y. Yang, F. Dernoncourt, C. Dockhorn, "DEFT: A corpus for definition extraction in free- and semi-structured text," in
*Proc. LAW*, 2019. https://aclanthology.org/W19-4015/ · dữ liệu: https://github.com/adobe-research/deft_corpus (README, mục Licensing Information:
CC BY-NC-SA 4.0).

[12] R. Navigli, P. Velardi, "Learning word-class lattices for definition and hypernym extraction," in *Proc. ACL*, 2010.
https://aclanthology.org/P10-1134/ · trang tải: https://nlp.uniroma1.it/wcl/ (không ghi giấy phép).

[13] Y. Zhu, H. Zamani, "Predicting prerequisite relations for unseen concepts," in *Proc. EMNLP*, 2022. https://aclanthology.org/2022.emnlp-main.585/

[14] Y. Pruksachatkun, J. Phang, H. Liu, P. M. Htut, X. Zhang, R. Y. Pang, C. Vania, K. Kann, S. R. Bowman, "Intermediate-task transfer learning with
pretrained language models: When and why does it work?" in *Proc. ACL*, 2020, pp. 5231–5247. doi:10.18653/v1/2020.acl-main.467 — chỉ đọc tóm tắt.

[15] Creative Commons, "Wikipedia moves to CC 4.0 licenses," 29/6/2023. https://creativecommons.org/2023/06/29/wikipedia-moves-to-cc-4-0-licenses/

Thẻ mô hình (giấy phép và số tham số đọc qua API Hugging Face): https://huggingface.co/vinai/phobert-base ·
https://huggingface.co/vinai/phobert-base-v2 · https://huggingface.co/intfloat/multilingual-e5-base · https://huggingface.co/FacebookAI/xlm-roberta-base
