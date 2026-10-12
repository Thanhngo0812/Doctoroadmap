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

## 8. Cập nhật 2026-10-11: lượt A xong, E0' xong

### 8.1 Lượt A

Agentic gộp xong `nhan-A-gop.jsonl` lúc 01:05 ngày 2026-10-11. Script kiểm định dạng chạy không `--mot-phan`: 65.525/65.525 cặp, ĐẠT, mã thoát 0.
Phân bố nhãn:
- `khong` 47.114;
- `can_de_hieu` 15.658;
- `cong_cu` 1.607;
- `khop_nham` 801;
- `nguoc` 336;
- `khong_ro` 9.

Claude chấm bằng `scripts/pass-phu-ml/kiem_chat_luong_d01.py` (cần khoá), được ba kết quả:
- **Phiếu kiểm**, đủ 83 phiếu, 371 cặp: cạnh cứng P 0,67, R 0,79, khớp 0,84 (TP 81, FP 40, FN 21, TN 229).
  - Kết quả này tốt hơn hẳn mẫu 23 cặp lúc đầu (P khoảng 0,4, mục 1.4).
  - Để so: ở vòng 1, LLM v3 được P 0,36–0,75 ở mức cặp (mục 7 vòng 1).
  - Lưu ý lạc quan ở mục 1.4 vẫn còn.
- **Phiếu lặp**, 3.142 cặp: năm nhãn khớp 0,76, kappa 0,45; cạnh cứng kappa 0,49. Cùng agentic gán lại cùng phiếu mà chỉ đồng thuận mức trung bình,
  đúng với đo ở mục 1.2.
- **Theo nhóm người gán:**
  - Tệp gộp có ít nhất 17 nhãn `nguoi_gan` khác nhau, gồm GPT-6 và GPT-6.1-sol.
  - Trên phiếu kiểm, không nhóm nào kém hẳn: P từ 0,54 tới 0,79, R từ 0,68 tới 0,85, mỗi nhóm 2–18 phiếu.
  - Riêng nhóm "Codex / GPT-6 / 2026-10" (269 phiếu, từ phiếu 4582 tới 5495, 3.077 cặp) gán `can_de_hieu` 74% trong cửa sổ, so với 32–46% ở các nhóm
    lớn khác. Nhóm này chỉ có 2 phiếu kiểm. E5 sẽ thử bỏ nhóm này.
- **Lý do lặp nguyên văn** chỉ rơi vào nhãn `khong`, kiểu "Đoạn văn không cho thấy quan hệ tiên quyết trực tiếp với Y" (5.414 lần).
  - Với nhãn âm thì lý do chung chung là tự nhiên, nên chưa đủ để nói là điền hàng loạt.
  - Phiếu kiểm cho R 0,79, tức `khong` không nuốt quá nhiều cạnh vàng.
- **`cong_cu` gần như biến mất** (2,5% số cặp), đúng hướng tác dụng phụ đã thấy sau bản 1.1 (mục 1.5). Cạnh mềm E8 vì vậy thiếu dữ liệu.

### 8.2 E0'

Hai việc của E0' đều xong:
- **Bảng đặc trưng D-01:** `scripts/pass-phu-ml/dung_bang_d01.py` cho 16 cuốn, 5.818 phiếu (thật và lặp), 65.154 dòng. Con số này đúng bằng 65.525 trừ
  371 cặp phiếu kiểm.
  - Không dòng nào thiếu nhãn A.
  - Kiểm chéo: cột "X có tên trong cửa sổ" tính lại từ đặc trưng trùng trường `trong_cua_so` của phiếu ở **cả 65.154 dòng**. Đặc trưng và phiếu dùng
    đúng một cửa sổ.
- **Tách hàm có kiểm hồi quy:** phần tính đặc trưng của `dung_bang_cap.py` đã tách thành `Context` và `pair_features` để dùng chung. Bảng vòng 1 dựng
  lại bằng mã mới **khớp từng byte** với bản gốc trên doc-1 và nhap-mon-ml (cùng mã `src/` hôm nay); bản gốc cũng khớp từng byte với bảng ngày
  2026-10-05.
- **Bỏ đặc trưng pass chính không làm hụt:** vòng 1 đã đo bằng `--khong-main`, nên không chạy lại.

| tài liệu | AP đủ 90 đặc trưng | AP bỏ 8 đặc trưng `main_*` |
|---|---:|---:|
| doc-1 | 0,596 | 0,587 |
| nhap-mon-ml | 0,479 | 0,528 |
| xstk-ch3-1 | 0,706 | 0,707 |
| doc-4 | 0,338 | 0,354 |

### 8.3 E5: LightGBM học trên D-01

> Số của mục này đo với bộ khớp tên có lỗi (mục 8.11). Sau khi sửa, E5 gần như không đổi (doc-4 P bao đóng 0,856, R 0,522); vòng 1 đổi nhiều hơn.
> Bảng mới ở mục 8.11.

**Cách làm** (`scripts/pass-phu-ml/thi_nghiem_e5.py`):
- Học trên 34.391 dòng D-01: phiếu thật, X có tên trong cửa sổ. Tập này gồm 5.414 phiếu, 16 sách, tỉ lệ dương (`can_de_hieu` của lượt A) 0,388;
  94% là cặp mà luồng có hỏi.
- Dùng đúng mô hình và 82 đặc trưng của vòng 1 (bỏ nhóm `main_*`).
- Ngưỡng chốt trên dự đoán ngoài mẫu của D-01 (chia theo sách) trước khi nhìn vàng.
- Chấm doc-1, xstk, doc-4 bằng bộ E4 của vòng 1. Bộ này chưa từng thấy ba tài liệu đó, và cũng không thấy lĩnh vực của chúng ở dạng nhãn.

**Kiểm bộ đo:** mốc vòng 1 chạy lại trên mã `src/` hôm nay ra **đúng từng số** của báo cáo vòng 1, nên mọi chênh lệch dưới đây là do điểm, không do mã
phát lại.

Bảng dưới so ba phương án: LLM v3 (số của vòng 1), vòng 1 (học trên ý định LLM v3), và E5 (học trên D-01, ngưỡng hiệu chỉnh), Wilson 95%:

| tài liệu | phương án | cạnh phụ | Q7 | Q7b | bao đóng P | bao đóng R |
|---|---|---:|---:|---:|---|---|
| doc-4 | LLM v3 | 1.473 | 0,322 | 0,606 | 0,584 (0,50–0,67) | 0,459 (0,38–0,54) |
| | vòng 1 | 701 | **0,595** | 0,720 | 0,717 (0,63–0,79) | 0,478 (0,40–0,56) |
| | **E5** | 690 | 0,476 | **0,873** | **0,872 (0,79–0,93)** | **0,516 (0,44–0,59)** |
| doc-1 | LLM v3 | 468 | 0,667 | **0,877** | **0,874** (0,80–0,92) | **0,740** (0,66–0,81) |
| | vòng 1 | 167 | **0,672** | 0,802 | 0,815 (0,73–0,88) | 0,672 (0,59–0,75) |
| | E5 | 195 | 0,603 | 0,743 | 0,821 (0,74–0,88) | 0,664 (0,58–0,74) |
| xstk | LLM v3 | 171 | **0,414** | **0,644** | **0,636** (0,47–0,78) | **0,214** (0,14–0,30) |
| | vòng 1 | 51 | 0,195 | 0,511 | 0,593 (0,41–0,76) | 0,163 (0,10–0,25) |
| | E5 | 58 | 0,214 | 0,445 | 0,562 (0,39–0,72) | 0,184 (0,12–0,27) |

**Đường học và hai phép bỏ** (ngưỡng hiệu chỉnh; mỗi ô là Q7 / Q7b / bao đóng P / bao đóng R):

| học trên | doc-1 | xstk | doc-4 |
|---|---|---|---|
| 10% phiếu (3.436 dòng) | 0,675 / 0,589 / 0,671 / 0,733 | 0,230 / 0,750 / 0,750 / 0,214 | 0,412 / 0,870 / 0,878 / 0,453 |
| 25% | 0,532 / 0,663 / 0,775 / 0,656 | 0,267 / 0,730 / 0,767 / 0,235 | 0,440 / 0,864 / 0,870 / 0,421 |
| 50% | 0,561 / 0,739 / 0,820 / 0,626 | 0,238 / 0,730 / 0,793 / 0,235 | 0,449 / 0,873 / 0,900 / 0,509 |
| 100% | 0,603 / 0,743 / 0,821 / 0,664 | 0,214 / 0,445 / 0,562 / 0,184 | 0,476 / 0,873 / 0,872 / 0,516 |
| 100%, chỉ cặp của luồng | 0,607 / 0,740 / 0,815 / 0,672 | 0,206 / 0,497 / 0,593 / 0,163 | 0,489 / 0,873 / 0,902 / 0,522 |
| 100%, bỏ nhóm dễ dãi (mục 8.1) | 0,583 / 0,747 / 0,822 / 0,634 | 0,206 / 0,482 / 0,571 / 0,163 | 0,455 / 0,873 / 0,901 / 0,516 |

**Đọc kết quả** (phán xét của Claude):
- **doc-4:** mọi biến thể học trên D-01 đều cho bao đóng P 0,87–0,90 và Q7b 0,86–0,87, so với 0,717 / 0,720 của vòng 1 và 0,584 / 0,606 của LLM v3.
  - Đây là tài liệu lớn nhất, có 72 cạnh vàng, và kết quả ổn định qua mọi cỡ dữ liệu, nên đây là tín hiệu thật: nhãn agentic đa lĩnh vực làm bộ kiểm
    **chặt hơn**.
  - Cái giá là Q7: 0,41–0,49, so với 0,595 của vòng 1. Bao đóng R thì ngang vòng 1.
- **doc-1 và xstk:** kết quả nhảy rất mạnh giữa các cấu hình gần như giống nhau.
  - Ở xstk, bao đóng P là 0,75–0,79 khi học trên 10–50% dữ liệu, nhưng 0,56 khi học trên 100%.
  - Ở doc-1, Q7 dao động từ 0,53 tới 0,68.
  - Vàng xstk rất nhỏ và nhiễu (vòng 1, mục 9), và lắp cạnh có tỉa cặp nên vài cạnh đổi là đổi cả bao đóng. Không kết luận được E5 hơn hay kém vòng 1
    ở hai tài liệu này.
- **Đường học phẳng:** học trên 10% D-01 đã ngang 100%.
  - Với LightGBM trên đặc trưng cấu trúc, giới hạn nằm ở **đặc trưng**, không ở lượng nhãn.
  - 65 nghìn cặp D-01 chỉ đáng giá nếu mô hình đọc được văn bản cửa sổ, tức E6 (cross-encoder).
- **Hai phép bỏ** không đổi kết luận. Nhóm người gán dễ dãi và 6% dòng không phải cặp của luồng không làm hỏng bộ học.

**Hệ quả cho kế hoạch:**
- **E9 phải làm trước khi chọn cấu hình:** nhiều seed và bootstrap theo cạnh. Nhiễu của phép đo đầu cuối trên doc-1 và xstk lớn hơn chênh lệch giữa các
  phương án.
- **E6 (cross-encoder) là đòn bẩy kế tiếp**, cần máy GPU.
- Kết luận cuối vẫn chờ T-01.

### 8.4 Lượt B

Lượt B xong ngày 2026-10-11, từ 10:28 tới 11:02, chia 91 lô. Script kiểm định dạng chạy không `--mot-phan`: 10.178/10.178 cặp, ĐẠT, mã thoát 0.

**Người gán không phải Claude như mục 1.5 đề xuất.** Tệp ghi `OpenAI Codex multi-agent / GPT-6-Astra + GPT-6.1-Sol`, cùng họ GPT-6 với lượt A.
- A và B vẫn là hai phiên độc lập, khác mô hình con.
- Nhưng đồng thuận A∩B không loại được thiên lệch chung của họ GPT-6. Báo cáo gọi nó là "đồng thuận hai lượt cùng họ mô hình".

Chấm bằng `kiem_chat_luong_d01.py`:

| phép đo | lượt A | lượt B |
|---|---|---|
| phiếu kiểm, cạnh cứng (cùng 371 cặp) | P 0,67, R 0,79, khớp 0,84 | **P 0,81**, R 0,77, **khớp 0,89** |
| phiếu lặp, năm nhãn / cạnh cứng (kappa) | 0,45 / 0,49 (3.142 cặp) | **0,85 / 0,90** (465 cặp) |
| `can_de_hieu` trong cửa sổ, cùng 5.195 cặp của 831 phiếu thật | 39% | 31% |
| `khop_nham` trong cửa sổ, cùng các cặp đó | 2% | 11% |

**A so với B**, trên 9.342 cặp của 831 phiếu thật trong mẫu:
- năm nhãn: khớp 0,75, kappa 0,47;
- theo từng nhãn (một với còn lại): `can_de_hieu` 0,56; `khong` 0,49; `cong_cu` 0,29; `khop_nham` 0,28; `nguoc` 0,11;
- cạnh cứng theo lĩnh vực: từ 0,46 (Sinh học) tới 0,65 (CNTT);
- bất đồng lớn nhất: A gán `can_de_hieu` mà B gán `khong` (685 cặp), chiều ngược lại 443 cặp; A gán `khong` mà B gán `khop_nham` 379 cặp,
  B gán `nguoc` 211 cặp.

**Đọc kết quả** (phán xét của Claude):
- B chặt và ổn định hơn A, và gần vàng hơn trên phiếu kiểm.
- Kappa A–B với cạnh cứng (0,56) nằm trong khoảng đồng thuận người theo PREAP (0,45–0,71). Hai nhãn hiếm `nguoc` và `cong_cu` thì gần như không
  đồng thuận.
- E10 sẽ so học trên A, trên B và trên A∩B, ở cùng cỡ dữ liệu trên 831 phiếu này.

### 8.5 E9: nhiều seed

> Số dưới đây đo với bộ khớp tên có lỗi (mục 8.11). E9 đã chạy lại sau khi sửa: bảng và cách đọc mới ở mục 8.11. Khoảng cách của E5 ở doc-4 còn
> khoảng một nửa, và độ bất ổn Q7 của vòng 1 ở doc-1 phần lớn do lỗi.

**Cách làm.** Học lại vòng 1 (ý định LLM v3) và E5 (nhãn A) với 5 seed LightGBM mới (1–5), cộng seed gốc 20261005: 6 seed mỗi phương án. Mỗi seed lắp
cạnh với ngưỡng hiệu chỉnh và chấm E4 trên ba tài liệu vàng.
- Tham số `--seed` thêm vào `thi_nghiem_e2b.py`; E5 dùng chung qua đó.
- Không truyền seed thì điểm vòng 1 ra y hệt bản đã lưu, đã kiểm trên cả ba tài liệu.

Mỗi ô ghi trung bình ± độ lệch chuẩn [min–max] qua 6 seed:

| tài liệu | phương án | Q7 | Q7b | bao đóng P | bao đóng R |
|---|---|---|---|---|---|
| doc-1 | vòng 1 | 0,630 ± 0,088 [0,47–0,70] | 0,722 ± 0,069 [0,64–0,80] | 0,788 ± 0,052 [0,70–0,83] | 0,684 ± 0,066 [0,56–0,74] |
| | E5 | 0,596 ± 0,010 [0,58–0,60] | 0,747 ± 0,002 | 0,825 ± 0,004 | 0,654 ± 0,015 |
| xstk | vòng 1 | 0,200 ± 0,004 | 0,498 ± 0,034 | 0,591 ± 0,019 | 0,177 ± 0,011 |
| | E5 | 0,228 ± 0,025 | 0,546 ± 0,083 [0,45–0,62] | 0,645 ± 0,067 [0,56–0,72] | 0,184 ± 0,013 |
| doc-4 | vòng 1 | 0,581 ± 0,011 | 0,717 ± 0,004 | 0,712 ± 0,009 | 0,473 ± 0,014 |
| | E5 | 0,483 ± 0,004 | 0,866 ± 0,008 | 0,877 ± 0,011 | 0,518 ± 0,003 |

Hiệu E5 trừ vòng 1, ghép theo seed (số seed E5 hơn trên 6):

| tài liệu | Q7 | Q7b | bao đóng P | bao đóng R |
|---|---|---|---|---|
| doc-1 | −0,034 ± 0,093 (2/6) | +0,025 ± 0,070 (4/6) | +0,037 ± 0,054 (4/6) | −0,030 ± 0,074 (1/6) |
| xstk | **+0,028 ± 0,023 (6/6)** | +0,048 ± 0,104 (4/6) | +0,054 ± 0,071 (4/6) | +0,007 ± 0,011 (2/6) |
| doc-4 | **−0,098 ± 0,013 (0/6)** | **+0,149 ± 0,009 (6/6)** | **+0,166 ± 0,017 (6/6)** | **+0,045 ± 0,012 (6/6)** |

**Đọc kết quả** (phán xét của Claude):
- **Vòng 1 không ổn định ở doc-1.** Q7 dao động từ 0,47 tới 0,70 chỉ vì đổi seed. Con số 0,672 của báo cáo vòng 1 là một seed khá may: trung bình là
  0,630. Kết luận "doc-1 sát LLM" của vòng 1 vì vậy cần đọc lại với độ lệch này.
- **E5 ổn định hơn hẳn ở doc-1:** độ lệch chuẩn của bao đóng P là 0,004, so với 0,052 của vòng 1. Học trên 34 nghìn nhãn đa lĩnh vực cho bộ kiểm ít
  phụ thuộc may rủi hơn học trên vài nghìn nhãn LLM của ba tài liệu.
- **doc-4: kết luận vững.** E5 hơn vòng 1 ở P, Q7b, R trong 6/6 seed, với chênh lệch gấp hơn 10 lần độ lệch chuẩn. E5 kém Q7 trong 6/6 seed.
- **doc-1 và xstk:** chênh lệch nằm trong nhiễu, trừ Q7 của xstk (E5 hơn 6/6, +0,028). Cũng chính xstk là nơi E5 dao động theo seed nhiều nhất, vì
  vàng nhỏ.
- **Đánh đổi lặp lại ở cả hai tài liệu lớn:** E5 cho P và Q7b cao hơn nhưng Q7 thấp hơn. Bộ kiểm học từ nhãn agentic chặt hơn, giữ ít cạnh gián tiếp
  hơn. Chọn bên nào là chọn giữa độ chính xác và độ phủ tổ tiên. Kết luận cuối phải đo trên T-01.

### 8.6 E10: so nguồn nhãn ở cùng cỡ

**Cách làm.** Học trên 831 phiếu thật của mẫu lượt B (5.195 dòng trong cửa sổ, 16 sách), với ba nguồn nhãn:
- **A:** nhãn lượt A, chỉ trên mẫu;
- **B:** nhãn lượt B;
- **A∩B:** chỉ giữ cặp A và B cùng nói cạnh cứng hoặc cùng nói không; còn 4.063 dòng.

Mỗi nguồn chạy 3 seed (1–3), ngưỡng hiệu chỉnh, chấm E4. Thêm hai mốc ở cùng seed 1–3 lấy từ E9: vòng 1, và A trên đủ 65 nghìn cặp (E5). Mỗi ô ghi
trung bình ± độ lệch chuẩn qua 3 seed:

| tài liệu | nguồn nhãn | cạnh | Q7 | Q7b | bao đóng P | bao đóng R |
|---|---|---:|---|---|---|---|
| doc-1 | vòng 1 (ý định LLM v3) | 166 | 0,578 ± 0,104 | 0,719 ± 0,069 | 0,803 ± 0,047 | 0,656 ± 0,086 |
| | A, đủ 65 nghìn cặp | 195 | 0,596 ± 0,012 | **0,748** ± 0,001 | **0,827** ± 0,004 | 0,654 ± 0,017 |
| | A, mẫu | 199 | **0,597** ± 0,013 | **0,748** ± 0,001 | **0,827** ± 0,004 | **0,657** ± 0,020 |
| | B, mẫu | 172 | 0,550 ± 0,018 | 0,692 ± 0,041 | 0,794 ± 0,024 | 0,634 ± 0,013 |
| | A∩B, mẫu | 172 | 0,568 ± 0,013 | 0,678 ± 0,005 | 0,789 ± 0,001 | 0,629 ± 0,005 |
| xstk | vòng 1 | 49 | 0,200 ± 0,004 | 0,496 ± 0,046 | 0,584 ± 0,028 | 0,177 ± 0,012 |
| | A, đủ | 57 | 0,213 ± 0,007 | 0,530 ± 0,077 | 0,632 ± 0,061 | 0,184 ± 0,021 |
| | A, mẫu | 69 | **0,249** ± 0,004 | 0,449 ± 0,051 | 0,495 ± 0,018 | **0,228** ± 0,029 |
| | B, mẫu | 51 | 0,221 ± 0,001 | **0,701** ± 0,099 | **0,707** ± 0,087 | 0,221 ± 0,012 |
| | A∩B, mẫu | 57 | 0,226 ± 0,007 | 0,490 ± 0,005 | 0,538 ± 0,000 | 0,214 ± 0,000 |
| doc-4 | vòng 1 | 700 | **0,579** ± 0,014 | 0,715 ± 0,005 | 0,708 ± 0,012 | 0,468 ± 0,019 |
| | A, đủ | 679 | 0,484 ± 0,002 | **0,864** ± 0,008 | 0,876 ± 0,013 | **0,518** ± 0,003 |
| | A, mẫu | 724 | 0,413 ± 0,026 | 0,826 ± 0,013 | 0,860 ± 0,024 | 0,465 ± 0,039 |
| | B, mẫu | 730 | 0,422 ± 0,003 | 0,860 ± 0,005 | 0,876 ± 0,012 | 0,501 ± 0,003 |
| | A∩B, mẫu | 636 | 0,439 ± 0,023 | 0,860 ± 0,011 | **0,887** ± 0,012 | 0,478 ± 0,000 |

**Đọc kết quả** (phán xét của Claude):
- **Mức tăng ở doc-4 đến từ nhãn agentic đa lĩnh vực nói chung, không từ riêng lượt A.** Cả ba nguồn trên mẫu 831 phiếu đều cho P 0,86–0,89 và Q7b
  0,83–0,86, so với 0,708 và 0,715 của vòng 1.
- **Nhãn "sạch hơn" không cho kết quả đầu cuối tốt hơn.** B và A∩B gần vàng hơn A trên phiếu kiểm (mục 8.4), nhưng ở doc-1 lại kém A ở cả bốn chỉ số.
  Ở doc-4, A∩B chỉ nhỉnh hơn về P (0,887 so với 0,860). Ở xstk, B tốt nhất về P nhưng dao động lớn (± 0,087).
  - Điều này khớp với Cache & Distil (R-02 §3.4): học trò khá bền với nhiễu của thầy.
  - Nó cũng khớp với đường học phẳng (mục 8.3): với bộ đặc trưng này, chất lượng nhãn và lượng nhãn đều không còn là nút thắt.
- **Đủ 65 nghìn cặp so với mẫu 831 phiếu:** ngang nhau ở doc-1. Ở doc-4, bản đủ dữ liệu giữ Q7 và R tốt hơn (0,484 / 0,518 so với 0,413 / 0,465),
  ổn định hơn qua seed.

**Hệ quả cho kế hoạch:**
- Nguồn nhãn cho bản triển khai LightGBM là **lượt A đủ 65 nghìn cặp**. Không cần gán lượt B cho toàn bộ D-01, và không cần lọc đồng thuận.
- Lượt B vẫn có ích: B là thước đo độ nhiễu của nhãn, và là dữ liệu đối chứng cho E6.
- Nút thắt nằm ở mô hình và đặc trưng. Đòn bẩy kế tiếp là E6 (cross-encoder đọc cửa sổ). Kết luận cuối vẫn chờ T-01.

### 8.7 Chuẩn bị E6 (cross-encoder)

**Ước thời gian** (2026-10-11, chưa thử, chưa biết con GPU cụ thể): khoảng 2–3 ngày theo lịch, trong đó Claude làm trực tiếp chừng 1–1,5 ngày, phần
còn lại máy GPU tự chạy qua đêm.

| bước | việc | thời gian |
|---|---|---|
| dựng máy | kiểm GPU, driver; cài torch CUDA, transformers; chép dữ liệu; chạy thử một lô | 1–2 giờ |
| dựng dữ liệu | đầu vào = tên Y, cửa sổ có đánh dấu X, `x_dinh_nghia`; cho D-01 và doc-1, xstk, doc-4; kiểm khớp bảng E5 | 3–4 giờ |
| huấn luyện | khoảng 36 nghìn cặp trong cửa sổ; PhoBERT-base và multilingual-e5-base (đóng băng embedding); 3 seed; 2–3 epoch; ước 2–4 giờ mỗi lượt | 12–24 giờ máy |
| đo | chấm ba tài liệu vàng, ghép với LightGBM, E4, phút/cuốn trên CPU | 3–4 giờ |
| báo cáo | | 1–2 giờ |

Bản rút gọn để quyết có làm tiếp không (chỉ PhoBERT, 1 seed, 2 epoch) mất khoảng 1 ngày. Không dùng bản này để kết luận, vì E9 cho thấy một seed
dễ cho số "may".

**Rủi ro thời gian:**
- con GPU 4 GB cụ thể làm tốc độ chênh 2–3 lần;
- e5-base có thể không vừa bộ nhớ, khi đó chỉ làm PhoBERT;
- PhoBERT cần câu đã tách từ; dùng underthesea sẽ lệch với cách tách lúc huấn luyện trước.

**Bộ nhớ chỉ là chuyện lúc fine-tune.** Lúc fine-tune phải giữ gradient và trạng thái Adam, khoảng 16 byte mỗi tham số. Lúc suy luận trong sản phẩm chỉ
còn trọng số:
- PhoBERT-base: khoảng 0,54 GB fp32, 0,14 GB int8;
- e5-base: khoảng 1,1 GB fp32.

Sản phẩm chạy cross-encoder trên CPU, không cần GPU. Cái giá là thời gian CPU: ước 10–30 cặp mỗi giây, vài phút cho một cuốn cỡ doc-4 (4.124 ứng
viên). E6 phải đo số này. Cách tăng tốc nếu cần:
- ONNX cộng int8;
- cắt độ dài đầu vào;
- chỉ chấm cặp mà LightGBM chưa chắc.

**Chủ dự án cần cung cấp trước E6:**
- kết quả `nvidia-smi`, RAM, ổ đĩa còn trống;
- máy để chạy qua đêm được không;
- cách SSH. Không ghi thông tin đăng nhập vào repo, bộ nhớ hay báo cáo.

### 8.8 Vé T-01a: Claude kiểm, đạt (2026-10-11)

Nhân viên chạy A1 → A5 trên hai cuốn giữ lại và giao bốn phiếu trống ([báo cáo của nhân viên](v4-T01a-2026-10-11.md), commit `e13a6b1`). Claude kiểm
lại từng tiêu chí của [vé](../task/v4/T-01a-chay-luong-hai-cuon-giu-lai.md) bằng lệnh chỉ in metadata, không mở sách, chunk, canonical hay phiếu.

| tiêu chí | Claude tự kiểm | kết quả |
|---|---|---|
| checker in ĐẠT cả hai cuốn, mã thoát 0 | chạy `kiem_t01a.py d01-t01 d01-t02` | đạt: canonical v1 complete (419 và 464 nút), adapter 11, `vi`, flash-lite qua Vertex, chưa có graph |
| tổng chi ≤ 5 USD | đọc chi trong manifest | đạt: LLM đo được 1,942 USD; phần chưa đo không đủ vượt trần (xem dưới) |
| hai cặp phiếu A1/A2 có SHA-256 | băm tệp, không mở | đạt: bốn phiếu, hai tệp chọn phạm vi, hai danh sách chương, cả tám hash khớp báo cáo |
| không có tệp nào của hai cuốn trong git | `git show --stat`, `git ls-files` | đạt: `e13a6b1` chỉ có báo cáo; không tệp nào trong `document-data/` hay `artifacts/` được theo dõi |
| điều kiện 1 và 2 có ghi | đọc báo cáo; kiểm checkout | đạt: chủ dự án xác nhận quyền 2026-10-11; chạy trên checkout sạch ghim `ff797eb` (kiểm HEAD, không có thay đổi ở `src/`, `scripts/`), 1.107 test xanh |

**Phần chi chưa đo:** một lời gọi A3 của d01-t02 thiếu số token, và 150.289 token embedding chưa quy đổi ra USD. Lời gọi A3 trung bình tốn khoảng
0,001 USD. Muốn vượt trần thì giá embedding phải trên khoảng 20 USD mỗi triệu token, gấp khoảng 80 lần giá input của chính LLM trong mã (0,25 USD
mỗi triệu). Số 429 chưa đo được: telemetry chưa ghi riêng số này.

**Sự cố mất mù d01-t01, lỗi do Claude.**
- **Nguyên nhân:** bản đầu của `kiem_t01a.py` in nguyên `stats` của manifest. Trong `candidates.stats` có `candidate_quality`, chứa tên và mô tả
  khái niệm (mô tả trùng, tên thiếu bằng chứng, cảnh báo). Khi viết, Claude chỉ thử ca đỏ trên d01-03, doc-4 và ca xanh trên dữ liệu dựng giả, chưa
  kiểm xem `stats` có chứa chữ hay không.
- **Ai thấy gì:** agent của nhân viên thấy một phần tên và mô tả khái niệm của d01-t01 khi chạy checker sau A5. Báo cáo và commit không chép nội
  dung đó; Claude đã kiểm báo cáo không có các khoá của khối bị lộ trước khi đọc.
- **Xử lý:**
  - chủ dự án chấp nhận giữ d01-t01 kèm ghi nhận sự cố;
  - nhân viên vá checker bằng danh sách trường số được phép in, kèm test hồi quy dữ liệu giả;
  - Claude chạy lại test: đỏ trên bản cũ ở đúng khẳng định "chuỗi bí mật không được lọt ra", xanh trên bản vá.
- **Ảnh hưởng tới phép đo vòng 2: nhỏ.**
  - Đầu ra A1 → A5 của d01-t01 đã có trước khi lộ, và mã chạy ghim ở `ff797eb`.
  - Học trò LightGBM, Claude và hai người gán đều chưa thấy nội dung.
  - Rủi ro còn lại: nhân viên đã thấy một phần nội dung, nên các vé triển khai vòng 2 không được chỉnh theo d01-t01.
- **Luật từ nay:** công cụ kiểm trên tập giữ lại chỉ in theo danh sách trường được phép, không in nguyên dict nào của manifest.

**Ghi chú phụ:**
- Chương do agent chọn từ danh sách chương, là ngoại lệ chủ dự án duyệt, không phải người chọn:
  - d01-t01: dải 36–40, 46 khái niệm đích;
  - d01-t02: chương 10, 37 khái niệm đích;
  - cả hai nằm trong mốc 26–47.
- Khối "nguyên đầu ra" của checker trong báo cáo nhân viên lệch thứ tự khoá `role_counts` so với đầu ra thật; mọi số y hệt.
- `scripts/do-chi-phi/bao_cao.py` (của Claude) đòi artifact graph, nên không chạy được trên lượt dừng ở A5. Sửa khi cần.
- `document-data/` chưa có trong `.gitignore`. Một lệnh `git add -A` sẽ đưa hai cuốn giữ lại vào commit. Đề nghị chủ dự án hoặc nhân viên thêm vào
  `.gitignore`.

**Còn lại của T-01:** hai người gán nộp phiếu, rồi làm bước 8 của vé (`a8-gold-check`, gộp, hội ý, đóng băng JSON, ghi SHA-256). Sau đó mới tới vé
đánh giá vòng 2, chạy A6 → A10 trên cấu hình đã khoá.

### 8.9 Quy lỗi thượng nguồn: hệ quả cho vòng 2 (2026-10-12)

Chủ dự án hỏi trạng thái dạy, neo và danh tính có quan trọng với A8 không. Báo cáo riêng:
[quy lỗi thượng nguồn](quy-loi-thuong-nguon-a8-2026-10-12.md). Số dưới đây đã đo lại sau khi sửa lỗi bộ khớp (mục 8.11). Trên 172 cạnh vàng của
doc-1, xstk và doc-4, pass phụ LLM v3 tìm được 73 cạnh, E5 tìm được 74; E5 ít cạnh thừa hơn (27/92 so với 34/93). Phép quy lỗi đổi thứ tự ưu tiên
của vòng 2 ở ba điểm:
- **Trần hồi tưởng do thượng nguồn:** 36/99 cạnh thiếu nằm ở trạng thái dạy, danh tính và cửa sổ. Không mô hình chấm nào lấy lại được các cạnh
  này, kể cả E6. Riêng xstk, chuỗi A2 → C8 làm mất 29/62 cạnh vàng (vé 05).
- **E7 có trần rõ ràng:** 39/136 cạnh vàng có tên X ngoài cửa sổ của Y (bản đầu ghi 49, do lỗi bộ khớp). E5 chỉ lấy được 3 cạnh trong số đó,
  LLM v3 lấy được 8. Đây là phần lớn nhất mà pass phụ ML còn để lại sau phần "mô hình".
- **E8 và cạnh mềm:** cạnh vàng chỉ có đường đi qua cạnh mềm là 15 với E5 và 25 với LLM v3 (doc-4 chiếm 14 và 20), do cạnh `cong_cu` và luật
  làm mềm cạnh ngược thứ tự sách (R17).

### 8.10 E6: cross-encoder (2026-10-12, đang chạy)

**Máy.** Chủ dự án cấp SSH máy GPU ngày 2026-10-12: laptop Dell, RTX 3050 Laptop 4 GB, Ryzen 5 5600H, RAM 6,6 GiB, Ubuntu 26.04, Python 3.14. Môi
trường: torch 2.14.1 (CUDA 13.0), transformers 5.19.0. Dựng máy gặp hai sự cố:
- **Driver NVIDIA không nạp.** Kernel tự cập nhật lên 7.0.0-34 nhưng module NVIDIA chỉ có cho 7.0.0-22. Chủ dự án nâng kernel lên 7.0.0-38 và driver
  lên 595.99.02, rồi khởi động lại.
- **pip đứt ở đúng 136,6 MB với mọi tệp lớn.** `/tmp` là tmpfs có hạn mức theo người dùng (`usrquota`), mà pip tải tạm vào đó. Lỗi hiện thành
  "Connection interrupted", tới cuối mới ra "Disk quota exceeded". Cách chữa: đặt `TMPDIR` sang ổ chính.

**Dữ liệu** (`dung_du_lieu_e6.py`). Mỗi dòng là một cặp "X là tiên quyết của Y" kèm văn bản cửa sổ định nghĩa của Y:
- **Học:** 34.386 cặp trong cửa sổ, từ 5.541 phiếu thật D-01 của 16 sách, nhãn lượt A. Bỏ 5 cặp `khong_ro`, còn 5 nhãn: `can_de_hieu` 13.340,
  `khong` 18.773, `cong_cu` 1.330, `khop_nham` 759, `nguoc` 184. Phiếu kiểm và phiếu lặp không vào tập học.
- **Chấm:** ứng viên của ba tài liệu vàng, đúng tập `ung_vien` của E5: doc-1 1.017, xstk 277, doc-4 4.124. Số dòng khớp bảng E5 ở cả ba.
- **Đánh dấu:** tên X bọc `@ … @`, tên Y bọc `# … #`, theo kiểu entity marker dạng dấu câu, dùng dấu có sẵn trong từ vựng. Câu được tách từ bằng
  underthesea trước rồi mới chèn dấu, vì underthesea dính dấu vào từ bên cạnh ("@_K"). Chỉ đánh dấu lần nhắc trùng ranh giới từ. 69 cặp học (0,2%)
  không đặt được dấu X, vì cách tách từ theo câu lệch với cách tách của luồng.
- Mỗi văn bản có hai bản: âm tiết cách nhau (multilingual-e5) và từ ghép nối `_` (PhoBERT).

**Dữ liệu đã chép lên máy GPU** (2026-10-12, vào `~/e6/du-lieu`), theo luật ghi lại mọi văn bản giáo trình rời laptop:

| tệp | nội dung | SHA-256 |
|---|---|---|
| `d01.jsonl` | 34.386 cặp học của 16 sách D-01 (phần học), văn bản cửa sổ, nhãn A | `c850e718c7f195d8eeeccc4787ac37b5096076c3fe3823a5e7540d3311577d04` |
| `doc-1.jsonl` | 1.017 ứng viên, văn bản cửa sổ | `d3681460833f277e82fb4141f05ae739aa85e84b950676f14b48e4c3ade14f6d` |
| `xstk-ch3-1.jsonl` | 277 ứng viên | `614d85fc8fa65a3a37ae55d3c6cc9a52bc022a8efdf809d07799622f0e4733a1` |
| `doc-4.jsonl` | 4.124 ứng viên | `fb3b5c602dac126bdf55f511e3b5bc8b110e276a306932d3daf9094258a9bbb0` |

Không chép gì của T-01, không chép `khoa.jsonl` hay đáp án phiếu kiểm. Cột `nhom` (mã sách D-01) lấy từ khoá, để chia nhóm theo sách.

**Thiết kế** (`e6_cross_encoder.py` trên máy GPU, `thi_nghiem_e6.py` trên laptop):
- **Đầu vào:** đoạn A là "# Y # @ X @ : câu định nghĩa của X", tối đa 64 token; đoạn B là các câu của cửa sổ. Hết chỗ thì giữ trước câu neo có X,
  câu có X gần neo nhất, câu neo, rồi tới các câu gần neo.
- **Chia:** bốn nhóm sách cố định, cân số dòng (8,1–9,2 nghìn cặp, tỉ lệ dương 0,36–0,42). Mỗi nếp học trên 12 sách, đoán 4 sách còn lại và ba tài
  liệu đo. Điểm trên tài liệu đo là trung bình bốn mô hình nếp.
- **Học:** 5 lớp; điểm cạnh cứng là xác suất `can_de_hieu`. Đóng băng embedding từ, bf16, AdamW, tối đa 3 epoch. Số epoch chọn bằng AP ngoài mẫu
  trên D-01, không nhìn vàng.
- **So và ghép:** LightGBM của E5 học lại trên đúng bốn nhóm sách, để so AP theo sách cho công bằng; số E5 cũ học trên 15 sách nên có lợi hơn.
  Ghép bằng trung bình xác suất đã hiệu chỉnh theo nếp.
- **Ngưỡng:** ba chính sách như E5, chốt trên D-01. E4 dùng chính sách hiệu chỉnh, `--chi-cung --tach-tu`, như `e5-a-hieu-chinh`.
- **Mô hình:** `vinai/phobert-base` (MIT, đầu vào tách từ) và `intfloat/multilingual-e5-base` (MIT), mỗi mô hình 3 seed.
- **Cấu hình chạy**, chốt sau các lượt chạy thử 512 dòng: lô 8, tích luỹ 4 (lô hiệu dụng 32), lr 3e-5.
  - PhoBERT: 256 token, cũng là trần của mô hình. 20% số cặp phải bỏ bớt câu; bộ nhớ đỉnh 2,42 GiB. Lô 16 chạm 3,28 GiB kèm một lần cấp phát hụt,
    nên đã hạ lô.
  - e5: 384 token. Ở 256 token, 47% số cặp phải bỏ câu, vì XLM-R tốn nhiều token hơn cho mỗi âm tiết; ở 384 còn 5,5%. Bộ nhớ đỉnh 3,34 GiB trên
    3,95 GiB, không cần gradient checkpointing (có checkpointing thì 2,36 GiB nhưng chậm hơn 50%).
  - Ước thời gian: khoảng 1,75 giờ mỗi seed PhoBERT, 2,3 giờ mỗi seed e5; sáu lượt khoảng 12 giờ. Hàng đợi chạy từ 11:27 ngày 2026-10-12.
- **Phút/cuốn trên CPU:** `e6_toc_do_cpu.py` chạy trên laptop, đo bản fp32 và bản int8 động.

**Kết quả sớm: PhoBERT seed 1** (2026-10-12, sau khi sửa bộ khớp ở mục 8.11; e5 và seed 2–3 còn chạy). Lượt chạy mất khoảng 3 giờ trên máy GPU,
GPU ở 86–88°C nên bị hạ xung (705–780 MHz).

Trên D-01, dự đoán ngoài mẫu so với nhãn agentic `can_de_hieu`:
- AP gộp theo epoch: 0,640 / 0,680 / 0,679, nên chọn epoch 2.
- PhoBERT đạt AP 0,680, LightGBM học trên đúng bốn nhóm sách đạt 0,663, bản ghép đạt **0,714**.
- PhoBERT hơn LightGBM ở 13/16 sách, phần lớn chỉ hơn ít (rõ nhất ở d01-15: 0,557 so với 0,486; d01-11: 0,559 so với 0,515).

E4 trên vàng người (ngưỡng hiệu chỉnh, `--chi-cung --tach-tu`; mỗi ô là số cạnh pass phụ / Q7 / Q7b / bao đóng P / bao đóng R):

| tài liệu | LLM v3 | E5 | E6 PhoBERT | E6 ghép LightGBM |
|---|---|---|---|---|
| doc-4 | 1.473 / 0,322 / 0,606 / 0,584 / 0,459 | 727 / **0,483** / 0,859 / 0,856 / **0,522** | 818 / 0,421 / 0,844 / **0,871** / 0,509 | 770 / 0,429 / 0,848 / 0,859 / 0,497 |
| doc-1 | 468 / **0,667** / **0,877** / **0,874** / **0,740** | 196 / 0,603 / 0,743 / 0,821 / 0,664 | 218 / 0,605 / 0,780 / 0,859 / 0,557 | 201 / 0,603 / 0,685 / 0,798 / 0,664 |
| xstk | 171 / **0,414** / 0,644 / 0,636 / 0,214 | 59 / 0,206 / 0,530 / 0,593 / 0,163 | 58 / 0,342 / 0,802 / 0,810 / 0,173 | 62 / 0,331 / **0,811** / **0,821** / **0,235** |

Khoảng Wilson của bao đóng P: doc-4 E6 0,79–0,93, E5 0,77–0,91; xstk E6 0,60–0,92, E5 0,41–0,76.

**Đọc kết quả** (phán xét của Claude, mới một seed):
- **doc-4:** E6 ngang E5; mọi chênh lệch nằm trong khoảng tin cậy.
- **doc-1:** E6 không hơn E5. Bản riêng chặt hơn (P 0,859) nhưng R thấp hơn (0,557); bản ghép thì ngang E5. LLM v3 vẫn tốt nhất ở doc-1.
- **xstk:** E6 hơn E5 rõ ở Q7, Q7b, P; bản ghép có R cao hơn cả LLM v3. Nhưng E9 cho thấy P của E5 ở xstk dao động 0,58–0,77 chỉ vì đổi seed, nên
  phải chờ thêm seed.
- Trên D-01, đọc văn bản giúp ít (+0,017 AP), còn ghép với LightGBM giúp rõ (+0,051). Trên vàng, ghép chưa hơn từng mô hình riêng.

**Phút/cuốn** (doc-4, 4.652 ứng viên, PhoBERT nếp 0):
- **CPU laptop** (Ryzen 7 7730U, 8 luồng): fp32 5,5 cặp/giây, khoảng 14 phút; mã hoá chỉ mất 2,2 giây.
- **int8 động của PyTorch:** 8,6 cặp/giây nhưng hỏng điểm (lệch tối đa 0,78, Spearman 0,58 so với fp32), không dùng được.
- **GPU** (máy GPU, đang hạ xung): theo log, khoảng 135 cặp/giây, tức khoảng 35 giây cho doc-4.
- So sánh: LightGBM mất 1–2 phút mỗi cuốn, LLM v3 mất 4,5–5 giờ.
- Chủ dự án cho biết có thể host mô hình trên máy GPU và nối bằng dây LAN. Nếu E6 đáng dùng thì phương án là:
  - một dịch vụ suy luận nhỏ trên máy GPU;
  - pass phụ gọi dịch vụ đó;
  - không gọi được thì lùi về LightGBM.

### 8.11 Lỗi bộ khớp tên theo ranh giới từ (2026-10-12, lỗi của Claude)

**Phát hiện.** Khi đọc 49 cạnh vàng mà phép quy lỗi (mục 8.9) xếp vào loại "X ngoài cửa sổ" để chuẩn bị E7, Claude thấy 10/23 cạnh của doc-4 có X là
«Quy luật», trong khi cửa sổ của Y viết rõ "những quy luật…".

**Nguyên nhân.** `segmented()` trong `dung_bang_cap.py` (chế độ `--tach-tu`) chuẩn hoá cả câu sau khi underthesea đã nối từ ghép bằng `_`. Phép đổi
y→i cuối âm tiết của `_mention_normalize` chỉ áp khi sau "y" không phải chữ, mà `_` lại là chữ (`\w`). Tên thì được chuẩn hoá khi âm tiết còn cách
nhau, nên "quy luật" thành mẫu `qui[ _]luật`, còn câu vẫn là `quy_luật`: không bao giờ khớp. Mọi tên có âm tiết **không đứng cuối** tận cùng
bằng "y" đều trượt: quy luật, tỷ lệ, lý thuyết, mức ý nghĩa, chủ nghĩa duy vật, không suy biến. "Định lý" vẫn khớp vì "lý" đứng cuối.

**Sửa.** Chuẩn hoá từng âm tiết rồi mới nối `_`. Test `tests/unit/scripts/test_khop_tu_am_tiet_y.py`: đỏ trên mã cũ ở cả bốn ca có "y", xanh
sau khi sửa; ca chặn ("chất" không khớp vào "vật chất") xanh cả hai lần. Dựng lại bảng vòng 1: chỉ ba cột `*_tu` đổi, và chỉ ở dòng có tên hoặc
bí danh chứa âm tiết "y" (doc-1 4 dòng, xstk 42 dòng, nhap-mon-ml không đổi).

**Ảnh hưởng đo được:**
- **Tập ứng viên** (hợp đồng cho phép, tên X trong cửa sổ) thiếu: doc-4 528 cặp (13%; 300 cặp LLM v3 đã hỏi; 10 cạnh vàng), xstk 21, doc-1 1.
- **Phiếu D-01:** 816 cặp đã gán nhãn bị đánh dấu `trong_cua_so: false` lúc xuất, nên không vào tập học của E5 và E6. Agentic gán các cặp này
  khi được báo X không có trong cửa sổ, nên nhãn của chúng có thể nghiêng về `khong`.
- **Các số đã báo bị ảnh hưởng:** E5, vòng 1 chạy lại với `--tach-tu`, E9, E10 (tập ứng viên và câu trích của `lap_canh.py --tach-tu`); phép quy
  lỗi (mục 8.9 và báo cáo quy lỗi: trần của E7 không phải 49 cạnh). Số LLM v3 và "không pass phụ" không đổi. Bảng và kết quả cũ giữ ở các thư
  mục `*-truoc-sua-y` trong `tmp/pass-phu-ml/`.
- **E6:** hàng đợi đầu tiên dừng sau 7 phút, dữ liệu dựng lại theo bộ khớp đã sửa: 35.202 cặp học (thêm 816), doc-4 4.652 ứng viên (thêm 528),
  xstk 298, doc-1 1.018. Trong 816 cặp mới vào tập học, tỉ lệ `can_de_hieu` chỉ 23,5%, so với 38% của cả tập. Có thể vì agentic gán chúng khi
  được báo X không có trong cửa sổ. Hàng đợi chạy lại từ 11:52.

**Chạy lại E5 và vòng 1 sau khi sửa** (ngưỡng hiệu chỉnh, `--chi-cung --tach-tu`; mỗi ô là số cạnh pass phụ / Q7 / Q7b / bao đóng P / bao đóng R):

| tài liệu | E5 trước | E5 sau | vòng 1 trước | vòng 1 sau |
|---|---|---|---|---|
| doc-4 | 690 / 0,476 / 0,873 / 0,872 / 0,516 | 727 / 0,483 / 0,859 / 0,856 / 0,522 | 701 / 0,595 / 0,720 / 0,717 / 0,478 | 740 / 0,547 / 0,727 / 0,703 / 0,447 |
| doc-1 | 195 / 0,603 / 0,743 / 0,821 / 0,664 | 196 / 0,603 / 0,743 / 0,821 / 0,664 | 167 / 0,672 / 0,802 / 0,815 / 0,672 | 168 / 0,711 / 0,722 / 0,781 / 0,763 |
| xstk | 58 / 0,214 / 0,445 / 0,562 / 0,184 | 59 / 0,206 / 0,530 / 0,593 / 0,163 | 51 / 0,195 / 0,511 / 0,593 / 0,163 | 53 / 0,202 / 0,522 / 0,600 / 0,184 |

**Đọc kết quả** (phán xét của Claude):
- **Kết luận chính của E5 không đổi.** Ở doc-4, E5 vẫn chặt hơn vòng 1 rõ rệt (bao đóng P 0,856 so với 0,703). Mọi chênh lệch trước và sau khi sửa
  đều nằm trong khoảng Wilson.
- 528 ứng viên mới của doc-4 thêm 37 cạnh pass phụ cho E5, nhưng bao đóng chỉ thêm 1 cặp đúng (83 so với 82). Các cạnh «Quy luật» trước đây đã có
  qua bắc cầu.
- **Vòng 1 ở doc-1 đổi mạnh** dù doc-1 chỉ thêm 1 ứng viên: tập học của vòng 1 gồm cả doc-4, nên đổi doc-4 là đổi mô hình. Độ nhạy này khớp với
  kết luận của E9 rằng doc-1 và xstk nhiễu hơn chênh lệch giữa các phương án.
- **E10 chưa chạy lại.** E10 so các nguồn nhãn trên cùng tập ứng viên (bị thiếu như nhau), nên chưa ưu tiên.

**E9 chạy lại sau khi sửa** (6 seed mỗi phương án: seed gốc và seed 1–5; mỗi ô là trung bình ± độ lệch chuẩn [min–max]; kết quả ở
`tmp/pass-phu-ml/ket-qua/e9-sua-y.jsonl`):

| tài liệu | phương án | Q7 | Q7b | bao đóng P | bao đóng R |
|---|---|---|---|---|---|
| doc-1 | vòng 1 | 0,687 ± 0,029 [0,64–0,72] | 0,705 ± 0,077 [0,60–0,80] | 0,761 ± 0,056 [0,68–0,82] | 0,729 ± 0,046 [0,66–0,76] |
| | E5 | 0,589 ± 0,016 [0,56–0,60] | 0,746 ± 0,004 | 0,824 ± 0,004 | 0,648 ± 0,017 |
| xstk | vòng 1 | 0,197 ± 0,003 | 0,515 ± 0,005 | 0,595 ± 0,003 | 0,170 ± 0,010 |
| | E5 | 0,215 ± 0,011 | 0,555 ± 0,087 [0,46–0,71] | 0,656 ± 0,074 [0,58–0,77] | 0,189 ± 0,022 |
| doc-4 | vòng 1 | 0,561 ± 0,017 | 0,780 ± 0,033 [0,73–0,81] | 0,772 ± 0,046 [0,70–0,81] | 0,468 ± 0,017 |
| | E5 | 0,464 ± 0,032 [0,42–0,49] | 0,853 ± 0,007 | 0,865 ± 0,010 | 0,518 ± 0,006 |

Hiệu E5 trừ vòng 1, ghép theo seed (số seed E5 hơn trên 6):

| tài liệu | Q7 | Q7b | bao đóng P | bao đóng R |
|---|---|---|---|---|
| doc-1 | −0,098 ± 0,038 (0/6) | +0,041 ± 0,074 (4/6) | **+0,063 ± 0,054 (6/6)** | −0,081 ± 0,059 (0/6) |
| xstk | **+0,018 ± 0,013 (6/6)** | +0,040 ± 0,087 (4/6) | +0,060 ± 0,075 (3/6) | +0,019 ± 0,028 (4/6) |
| doc-4 | −0,097 ± 0,047 (0/6) | **+0,073 ± 0,036 (6/6)** | **+0,093 ± 0,043 (6/6)** | **+0,050 ± 0,022 (6/6)** |

**So với mục 8.5** (phán xét của Claude):
- **doc-4: E5 vẫn hơn vòng 1 ở P, Q7b, R trong 6/6 seed, nhưng khoảng cách còn khoảng một nửa** (P +0,093 so với +0,166 trước khi sửa). Phần đổi
  nằm ở vòng 1: P của vòng 1 lên 0,772 (trước 0,712), vì tập học của vòng 1 gồm các cặp «Quy luật» của chính doc-4 mà trước đây bị che. Câu "chênh
  lệch gấp hơn 10 lần độ lệch chuẩn" ở mục 8.5 không còn đúng: nay chỉ khoảng 2 lần.
- **doc-1: đánh đổi rõ hơn.** E5 có P cao hơn ở 6/6 seed, nhưng Q7 và R thấp hơn ở 0/6 seed.
- **"Vòng 1 không ổn định ở doc-1" phần lớn do lỗi bộ khớp.** Độ lệch chuẩn Q7 của vòng 1 còn 0,029 (trước 0,088). P và Q7b của vòng 1 vẫn dao động
  hơn E5 nhiều (0,056 và 0,077, so với 0,004).
- **Đánh đổi chung giữ nguyên:** E5 chặt hơn (P, Q7b), vòng 1 phủ tổ tiên rộng hơn (Q7). Kết luận cuối vẫn chờ T-01.

### 8.12 Khảo sát phạm vi E7 và E8 (2026-10-12, 0 USD)

**E7: ứng viên không nguyên văn.** Đọc 49 cạnh vàng mà bản đầu của phép quy lỗi xếp là "X ngoài cửa sổ". 10 cạnh hoá ra do lỗi bộ khớp (mục 8.11),
còn 39 cạnh. Cách X có mặt trong 39 cạnh này:
- **một phần tên:** "độ chính xác" cho «Độ chính xác trong ước lượng tỉ lệ», "phổ biến" cho «Tính phổ biến», "khả đảo" cho «Ma trận khả đảo»;
- **ký hiệu, công thức:** `det P`, `[β]S`, `(X1, …, Xn)`;
- **nhắc ngoài cửa sổ nhưng trong chunk dạy Y:** cửa sổ dừng ở ranh giới đoạn văn;
- **lỗi trích chữ của PDF:** "t ất nhiên";
- **ngầm hiểu:** sách không nhắc X, vàng dựa vào kiến thức môn học; ví dụ «Cơ sở» định nghĩa bằng "biểu diễn tuyến tính **duy nhất**".

Đo bốn bộ sinh ứng viên trên các cặp hợp đồng cho phép mà X không có trong cửa sổ (`pham_vi_e7.py`, đọc artifact pass phụ v3):

| bộ sinh | bắt được / 39 | cặp sinh thêm (doc-1 + xstk + doc-4) |
|---|---:|---:|
| tên X trong chunk neo hay chunk dạy của Y, ngoài cửa sổ | 13 | 4.005 |
| một phần tên X (tiền tố, hậu tố ≥ 2 âm tiết, bỏ "sự", "tính"…) trong cửa sổ | 22 | 48.403 |
| cặp nghi ngờ sẵn có của luồng (`suspected_pairs`) | 29 | 41.817 |
| hợp cả ba | 37 | 82.130 |

Tập ứng viên hiện có (X trong cửa sổ) là 5.968 cặp, chứa 97 cạnh vàng. Bộ sinh rẻ nhất cũng làm tập ứng viên phình thêm 67% để với tới 13 cạnh.
Thêm nữa, hợp đồng A8 đòi câu trích của cạnh cứng nằm trong cửa sổ, nên cạnh E7 sẽ trích một câu không nhắc tên X: lộ trình có cạnh mà căn cứ không
nói gì về tiên quyết. **Đánh giá của Claude: E7 lợi thấp, hoãn.** Nếu làm thì chỉ thử bộ "chunk dạy Y" sau E6, với bộ chấm đọc văn bản.

**E8: cạnh mềm.** Trong đồ thị A10 của E5 ở doc-4, 332/1.208 cạnh là mềm: 304 cạnh do R17 (`soften_backward_edges`: tiên quyết được dạy sau đích
thì làm mềm, để lộ trình giữ thứ tự sách), 28 cạnh `cong_cu`. Phát lại A9 → A10 khi tắt R17 (`phat_lai_tat_r17.py`, monkeypatch trong script
nghiên cứu, không sửa `src/`).
Bản có R17 của LLM v3 ra đúng từng số đã báo:

| tài liệu | hệ | R17 | cạnh cứng A10 | Q6 | Q7 | Q7b | bao đóng P | bao đóng R |
|---|---|---|---:|---:|---:|---:|---|---|
| doc-4 | LLM v3 | bật | 870 | 0,157 | 0,322 | 0,606 | 0,584 (0,50–0,67) | 0,459 (0,38–0,54) |
| | | tắt | 1.071 | 0,157 | 0,522 | 0,366 | 0,551 (0,45–0,65) | 0,340 (0,27–0,42) |
| | E5 | bật | 876 | 0,143 | 0,483 | 0,859 | 0,856 (0,77–0,91) | 0,522 (0,45–0,60) |
| | | tắt | 1.180 | 0,100 | 0,703 | 0,503 | 0,747 (0,64–0,83) | 0,371 (0,30–0,45) |
| doc-1 | E5 | bật / tắt | 376 / 395 | 0,103 / 0,179 | 0,603 / 0,603 | 0,743 / 0,679 | 0,821 / 0,857 | 0,664 / 0,641 |
| xstk | E5 | bật / tắt | 121 / 127 | không đổi | | | | |

**Đọc kết quả:**
- R17 không phải lỗ thuần. Tắt R17 thì doc-4 lấy lại phần lớn cạnh vàng "chỉ có đường mềm" (Q7 tăng 0,20–0,22), nhưng kéo theo rất nhiều tiên
  quyết sai (Q7b giảm 0,24–0,36). Bao đóng P và R trên rút gọn bắc cầu cũng giảm, vì thêm cạnh cứng làm các cạnh trực tiếp giữa đích vàng thành bắc
  cầu.
- Hướng có lý của E8 là **làm cứng có chọn lọc**: chỉ cạnh ngược mà bộ chấm tin chắc, hoặc chỉ cạnh ngược trong cùng một mục. Việc này đổi luật
  của A10 (`src/`), nên phải qua vé, và phải tránh khớp riêng doc-4, tài liệu duy nhất mà R17 tác động mạnh.

## 9. Chạy lại

Các lệnh sau tái lập số của báo cáo:

```
# mẫu lượt B (cần khoa.jsonl; chỉ Claude chạy)
.venv/Scripts/python.exe -I scripts/pass-phu-ml/chon_mau_luot_b.py --phieu tmp/d01-phieu/phieu.jsonl --khoa tmp/d01-phieu/khoa.jsonl \
    --ra <gói>/phieu.jsonl --ds-ra tmp/d01-luot-B/chon.json
# VI-AL-CPL: tải AL-CPL, liên kết Wikidata, đoạn mở đầu vi.wikipedia (có đệm ở tmp/pass-phu-ml/vi-al-cpl/dem.json)
.venv/Scripts/python.exe -I scripts/pass-phu-ml/vi_al_cpl.py
# chấm chất lượng lượt A (cần khoa.jsonl)
.venv/Scripts/python.exe -I scripts/pass-phu-ml/kiem_chat_luong_d01.py --phieu tmp/d01-phieu/phieu.jsonl --khoa tmp/d01-phieu/khoa.jsonl \
    --nhan tmp/d01-gan-nhan/nhan-A-gop.jsonl
# E0': bảng đặc trưng D-01 (cần khoa.jsonl; tmp/venv-ml có underthesea)
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/dung_bang_d01.py --phieu tmp/d01-phieu/phieu.jsonl --khoa tmp/d01-phieu/khoa.jsonl \
    --nhan tmp/d01-gan-nhan/nhan-A-gop.jsonl --nhan-cu tmp/d01-gan-nhan/nhan-A.jsonl
# E5: điểm và ngưỡng (biến thể: --ti-le-phieu=0.1|0.25|0.5, --chi-cap, "--bo-nhom=Codex / GPT-6 / 2026-10" --luot=e5-d01-a-bo-nhom-de-dai)
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/thi_nghiem_e5.py
# E4 cho từng tài liệu vàng (doc-1, xstk-ch3-1, doc-4); kết quả ở tmp/pass-phu-ml/ket-qua/e5.jsonl
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/lap_canh.py <doc> --diem=tmp/pass-phu-ml/diem/e5-d01-a/<doc>.csv \
    --nguong-tu=tmp/pass-phu-ml/diem/e5-d01-a/nguong.json --chinh-sach=hieu-chinh --chi-cung --tach-tu --nhan=e5-a-hieu-chinh
# E6, trên laptop: dữ liệu cross-encoder (cần khoa.jsonl), rồi chép tmp/pass-phu-ml/e6/du-lieu/*.jsonl và hai script e6_* lên máy GPU
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/dung_du_lieu_e6.py
# E6, trên máy GPU (~/e6): venv có torch, transformers; hang-doi.txt mỗi dòng một lượt, ví dụ
#   phobert-s1 --mo-hinh=vinai/phobert-base --tach-tu --seed=1 --lo=8 --tich-luy=4 --luu-mo-hinh
#   e5-s1 --mo-hinh=intfloat/multilingual-e5-base --do-dai=384 --seed=1 --lo=8 --tich-luy=4 --luu-mo-hinh
bash e6_chay_hang_doi.sh
# E6, trên laptop: chép ~/e6/ket-qua/<lượt> về tmp/pass-phu-ml/e6/ket-qua/, chốt ngưỡng, rồi E4 như E5
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/thi_nghiem_e6.py --ket-qua=tmp/pass-phu-ml/e6/ket-qua/<lượt> [--ghep=lightgbm]
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/lap_canh.py <doc> --diem=tmp/pass-phu-ml/diem/e6-<lượt>/<doc>.csv \
    --nguong-tu=tmp/pass-phu-ml/diem/e6-<lượt>/nguong.json --chinh-sach=hieu-chinh --chi-cung --tach-tu --nhan=e6-<lượt>-hieu-chinh
# E6: phút/cuốn trên CPU (tmp/venv-e6 có torch bản CPU), với mô hình nếp 0 chép về
tmp/venv-e6/Scripts/python.exe scripts/pass-phu-ml/e6_toc_do_cpu.py --mo-hinh=<thư mục mo-hinh> [--tach-tu] --int8
# sau khi sửa bộ khớp (mục 8.11): dựng lại bảng --tach-tu, bảng D-01, dữ liệu E6, rồi quy lỗi
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/dung_bang_cap.py doc-1 nhap-mon-ml xstk-ch3-1 doc-4 --tach-tu
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/quy_loi_thuong_nguon.py --tach-tu --he=khong,llm-v3,e5-a-hieu-chinh
# vòng 1 sau khi sửa, rồi lap_canh như E5 với --nhan=vong1-hieu-chinh-sua-y
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/thi_nghiem_e2b.py --nhan=y-dinh-cung --tach-tu --khong-main --luot=vong1-sua-y
# khảo sát E7 và E8 (mục 8.12)
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/pham_vi_e7.py
.venv/Scripts/python.exe scripts/pass-phu-ml/phat_lai_tat_r17.py --he=llm-v3,e5-a-hieu-chinh
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
