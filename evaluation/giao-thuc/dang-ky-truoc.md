# Giao thức đăng ký trước — đánh giá Pha A trên tập thử

**Phiên bản:** dk-0 (NHÁP, chưa chốt) · **Người giữ:** Claude · **Duyệt:** chủ dự án · **Hạn chốt:** commit bản dk-1 trước 07/11/2026

Tệp này ghi mọi luật chơi trước khi chạy tập thử: thước, cách ghép, ngưỡng, luật căn, kiểm định, cách cắt khi trễ. Bản chốt (dk-1) được commit, và SHA-256 của
nó nằm trong bản ghi của **mọi** lượt chạy trên tập thử. Lệnh `luot` từ chối chạy tập thử khi thiếu SHA này. Sau ngày chốt, thân tệp không sửa nữa. Mọi thay
đổi ghi vào mục 14 (nhật ký hậu kiểm) và được báo là phân tích hậu kiểm.

Nguồn: spec `doc/danh-gia-pha-a-spec.md` (mục 4–15); kế hoạch `report/ke-hoach-danh-gia-pha-a-2026-10-26.md`; vé DG-18.

Các ô ghi **CHỜ** sẽ được điền từ số của tập phát triển (01–06/11) trước khi chốt. Bản dk-1 không được còn ô CHỜ nào.

## 1. Câu hỏi nghiên cứu

| RQ | Câu hỏi | Trả lời bằng |
|---|---|---|
| RQ1 | Trên giáo trình tiếng Việt chưa từng thấy, lộ trình có dạy đủ khái niệm trọng yếu và tôn trọng quan hệ tiên quyết thật không? | độ phủ khái niệm trong dãy học, Q6, G5; so với baseline |
| RQ2 | Từng khâu tốt tới đâu, và lỗi cuối bắt nguồn từ khâu nào? | thước từng khâu, quy lỗi, oracle A8 và A10 |
| RQ3 | Hệ tốn bao nhiêu phút và USD cho một cuốn, chia theo khâu? | sổ chi, thời gian, số lời gọi; phút/trang, USD/trang |
| RQ4 | Các quyết định thiết kế chính đóng góp bao nhiêu? | ablation (mục 9) |
| RQ5 | Kết quả ổn định tới đâu trước nhiễu đầu vào giữ nghĩa? | K lượt xáo pass chính (mục 7) |
| RQ6 | (seminar) Thay LLM bằng ML/DL ở từng khâu thì được và mất gì? | logistic, cross-encoder, cùng vàng và hợp đồng |

## 2. Đơn vị, phạm vi và cách ghép

- **Đơn vị thống kê** là cuốn (8 cuốn, mỗi chủ đề một cuốn), và chương bốc trong cuốn (3 chương mỗi cuốn).
- **Phạm vi vàng.** G1, G2 phủ cả cuốn. G3, G4 chỉ phủ 3 chương bốc, nên số A3–A10 là số có điều kiện trên các chương đó. Cạnh trong phạm vi là cạnh G4
  "văn bản thể hiện" có đích thuộc chương bốc.
- **Ghép:** mỗi thước tính số đếm theo chương, cộng lên cuốn, rồi lấy trung bình macro theo cuốn. Không tính trung bình của tỉ lệ chương.
- **Hai mức căn:** nghiêm (`khop`) và nới (`khop`, `may_rong_hon`, `may_hep_hon`). Chỉ số chính dùng mức nghiêm.
- **Vàng chính** là vàng sau hội ý. Vàng hợp và vàng giao (mục 10) chỉ dùng cho phân tích độ nhạy.
- Không kết luận riêng cho từng ngành hay từng cuốn.

## 3. Thước chính từng khâu

| Khâu | Thước chính (mức nghiêm) | Thước phụ chính |
|---|---|---|
| A1 | M3: tỉ lệ ký tự thân bài có mục sâu nhất trùng G1 (bộ chấm D-02) | M1 F1 tiêu đề; F1 complete entry; M2 |
| A2 | recall `noi_dung` theo mục và theo ký tự | macro-F1 sáu vai trò; tỉ lệ lỗi có hại |
| A3 | độ phủ khái niệm `day_o_day` và `day_qua_vi_du` | độ chính xác theo G5(a); khái niệm bịa |
| A4 | tỉ lệ tách; tỉ lệ gộp nhầm | B-cubed P/R |
| A5 | tỉ lệ câu neo đúng câu | câu neo cùng trang; độ chính xác và độ phủ trạng thái dạy |
| A6/A7 | trần ứng viên | — |
| A8 | F1 quan hệ (cạnh trực tiếp, qua bảng căn) | P/R bao đóng; precision hiệu chỉnh G5(b) kèm cận dưới; F1 so với từng người gán; PR-AUC pass phụ |
| A9/A10 | Q6 | Q7, Q7b; số chu trình (phải 0); rubric và so sánh cặp G5(c) |
| Đầu-cuối | độ phủ khái niệm trong dãy học; Q6 | — |
| Truy nguyên | tỉ lệ bằng chứng có thật (mức nghiêm) | khái niệm bịa; tỉ lệ có bằng chứng |
| Chi phí | phút/cuốn (có và không có giây chờ embedding); USD/cuốn | theo khâu; phút/trang, USD/trang |
| Ổn định | dải min–max của chỉ số chính qua K lượt | Jaccard tập cạnh giữa các lượt |

Định nghĩa đầy đủ ở spec mục 8. Q6 = (cạnh vàng trong phạm vi bị đặt ngược hoặc có đầu không nằm trong dãy học) / (tổng cạnh vàng trong phạm vi); thấp hơn
là tốt hơn.

## 4. Ánh xạ trạng thái dạy (sáu giá trị máy sang bốn giá trị vàng)

Tệp máy đọc: `evaluation/giao-thuc/anh-xa-trang-thai.json`. Bản chốt bỏ cờ `nhap` và đổi `phien_ban` thành `dk-1`.

| Máy | Được coi là đúng khi vàng là | Lý do |
|---|---|---|
| `taught` | `day_o_day`, `day_qua_vi_du` | máy không có giá trị riêng cho "dạy qua ví dụ" |
| `mentioned_only` | `chi_nhac` | |
| `prior_knowledge` | `kien_thuc_nen` | |
| `uncertain` | không quyết định (`null`) | máy tự nhận không biết: ra khỏi mẫu số độ chính xác, vẫn trong mẫu số độ phủ |
| `unchecked` | không quyết định (`null`) | khâu kiểm chưa chạy tới node: như trên |
| `not_subject_matter` | không bao giờ đúng (`[]`) | vàng không có khái niệm "không thuộc môn" |

Chiều ngược (oracle A8, DG-14): `day_o_day`, `day_qua_vi_du` thành `taught`; `chi_nhac` thành `mentioned_only`; `kien_thuc_nen` thành `prior_knowledge`;
trạng thái tranh chấp (`null`) thành `uncertain`.

## 5. Ngưỡng khớp mờ

Mọi ngưỡng dưới đây là hằng số trong mã lúc đóng băng. Mã đọc ngưỡng từ hằng số, nên đổi ngưỡng là đổi mã và phải ghi hậu kiểm.

| Chỗ dùng | Ngưỡng | Hằng số |
|---|---|---|
| Căn vàng–máy, luật 2: câu neo trùng câu định nghĩa vàng, cùng trang | độ giống ký tự ≥ 0,9 | `can.luat.NGUONG_CAU_MAC_DINH` |
| Căn vàng–máy, ứng viên gần: câu giống, cùng trang | ≥ 0,5 | `can.luat.NGUONG_GAN_MAC_DINH` |
| Căn vàng–máy, ứng viên gần: Jaccard âm tiết của tên | ≥ 0,34 | `can.luat.NGUONG_JACCARD_MAC_DINH` |
| Căn hai danh sách G3 của hai người gán: câu, gần, Jaccard | 0,9; 0,5; 0,5 | `phieu.can` |
| A5 câu neo đúng câu | ≥ 0,9 | `cham.khai_niem.NGUONG_CAU_NEO` |
| Truy nguyên (câu neo, câu bằng chứng có trong trang ghi kèm) | nghiêm ≥ 0,9; nới ≥ 0,75 | `cham.khai_niem.NGUONG_TRUY_NGUYEN` |
| A1/A2 định vị câu định nghĩa vào dòng (lỗi có hại, quy lỗi lý do 1) | ≥ 0,75 | `cham.a1a2.NGUONG_DINH_VI` |
| Oracle A8: gắn câu định nghĩa G3 vào chunk | bằng ngưỡng truy nguyên nghiêm (0,9) | `oracle_a8.canonical.NGUONG_CAU` |
| Validator phiếu: câu chép có trong trang (chỉ cảnh báo) | ≥ 0,85 | `phieu.kiem.NGUONG_CAU_MAC_DINH` |

Mọi so khớp tên dùng chuẩn hoá `danhgia.ten.chuan_hoa` (NFKC, chữ thường, gộp khoảng trắng, bỏ dấu câu hai đầu, giữ dấu tiếng Việt) và so theo ranh
giới âm tiết.

## 6. Luật căn khái niệm

Theo spec mục 7, chạy theo thứ tự:
1. Trùng tên hoặc tên khác sau chuẩn hoá, theo ranh giới âm tiết.
2. Câu neo của máy trùng câu định nghĩa vàng (cùng trang, ngưỡng ở mục 5).
3. Ký hiệu (không có từ nào dài từ hai chữ cái) không bao giờ dùng để căn hay đề cử ứng viên.

Phán tay:
- Chỉ phán cặp có ứng viên gần. Tối đa **k = 3** node gần nhất cho khái niệm vàng chưa căn bằng luật; **k = 1** node chưa căn gần nhất cho khái niệm đã
  căn (để bắt `may_hep_hon` khi máy tách khái niệm).
- Khái niệm vàng không có ứng viên gần là `khong_khop` mặc định.
- Node của mọi hệ gộp vào một bảng, khử trùng theo chữ chuẩn hoá, mang mã ngẫu nhiên, không lộ tên hệ. Claude phán, có nhật ký.
- 20% số ca phán tay được một sinh viên mỗi chủ đề phán lại độc lập. Báo % đồng ý và κ.

Khái niệm nguồn "ngoài" của G4 được căn theo cùng luật, dùng trang định nghĩa ghi kèm.

## 7. Bốc chương, N, seed, K

- **Bốc chương:** giao thức `evaluation/giao-thuc/boc-chuong-tap-thu.md` (boc-1, commit trước khi mở mục lục): seed **20261027**, N = **5** trang PDF, 3 chương
  mỗi cuốn (đầu, giữa, cuối).
- **K = 5** lượt cho hệ chính: lượt chính (không xáo) cộng 4 lượt xáo ngữ cảnh pass chính, chạy bằng `luot --bien-the xao-k --k 4 --seed 1`, tức seed 1, 2,
  3, 4. Dải nhiễu của một chỉ số là min–max qua 5 lượt.
- **B5:** K = 5 lượt bằng 5 biến thể định dạng lời nhắc giữ nghĩa (mục 8).
- **Seed thống kê:** bootstrap, hoán vị và mô phỏng công suất dùng seed **20261114** với bộ sinh LCG tất định trong `danhgia.thong_ke.lcg`.

## 8. Lời nhắc B5

Chế độ: **CHỜ** (B5a một lời gọi cả cuốn, hoặc B5b mỗi chương một lời gọi; chọn sau dry-run trên tập phát triển ngày 01/11 theo Q36, lý do ghi tại đây).

Lời nhắc nguyên văn: **CHỜ** (chép nguyên văn bản chốt từ `evaluation/giao-thuc/b5/loi-nhac-b5.md` vào đây, kèm SHA-256 của tệp đó và mã phiên bản lời nhắc).

## 9. Hệ được so, kiểm định và ngưỡng tuyên bố

Hệ được so như spec mục 11: hệ chính; B1–B5; ablation (tắt R17, bỏ cạnh pass chính, bỏ cạnh pass phụ, pass phụ LLM, docling, logistic, cross-encoder);
oracle A8, oracle A10. Số oracle báo trong cột riêng, không đặt ngang hệ thật.

**Ba phép kiểm định chính thức**, hai phía, hiệu chỉnh Holm trên cả ba, mức 0,05 cho cả họ:
1. Q6: hệ chính so với B1.
2. F1 quan hệ: hệ chính so với B5.
3. Tỉ lệ bằng chứng có thật: hệ chính so với B5.

Cách kiểm: hoán vị ghép cặp phân tầng (`thong_ke.hoan_vi_ghep_cap`). Đơn vị đổi nhãn là chương, 10.000 lần, thống kê là hiệu trung bình macro theo cuốn.
Hệ chính trong ba phép này là **lượt chính** (lượt nhiễu 0), không phải trung bình K lượt. Thước tính trên cả sách (truy nguyên, chi phí) chỉ có một đơn vị
`toan_sach` mỗi cuốn. Với các thước này, đơn vị hoán vị và bootstrap là cuốn, nên với 8 cuốn p hai phía nhỏ nhất là 2/256 ≈ 0,0078. Sau Holm, p đó vẫn dưới 0,05.

Mọi so sánh khác chỉ mô tả, báo cỡ hiệu ứng và CI. Thứ tự báo: cỡ hiệu ứng và CI trước, p sau. Phụ thêm, không thay kiểm định chính:
- **Khoảng tin cậy:** bootstrap phân cấp (lấy lại cuốn có hoàn lại, rồi chương trong cuốn), 10.000 vòng, khoảng phân vị 95%.
- **Sign test theo cuốn:** nhị thức chính xác. Với 8 cuốn, chỉ 8/8 cùng chiều mới cho p < 0,05.
- **Luật nhiễu:** chênh giữa hai hệ nhỏ hơn dải nhiễu K lượt của hệ chính thì không tuyên bố hệ nào hơn, dù p nhỏ.
- **G5:** phán tối đa 100 cạnh ngoài vàng mỗi hệ mỗi cuốn (chủ dự án chốt 29/10, chấp nhận khối lượng phán lớn) và tối đa 60 khái niệm (a) mỗi cuốn.
  - Precision hiệu chỉnh kèm CI Wilson trên tỉ lệ mẫu; báo thêm cận dưới coi cạnh thiếu trường là sai.
  - Likert báo trung bình và Krippendorff α thứ bậc.
  - So sánh cặp là vòng tròn đủ cặp giữa các hệ có lộ trình, báo thăm dò.

## 10. Luật tranh chấp và vàng thiếu

- **Hội ý một vòng, không gặp mặt.** Mỗi mục bất đồng mỗi người ghi "giữ" hoặc "bỏ":
  - cả hai giữ thì vào vàng chính;
  - cả hai bỏ thì loại;
  - còn lại là tranh chấp: không vào vàng chính, có trong vàng hợp, không có trong vàng giao.
- Trạng thái dạy tranh chấp: khái niệm vẫn ở kho chốt với trạng thái `null`. Nó không vào mẫu số độ phủ A3 và độ phủ đầu-cuối, vì vàng chính chỉ tính khái
  niệm cả hai người cùng ghi là dạy. Nó cũng không vào hai mẫu số trạng thái A5, độ chính xác và độ phủ, vì không có đáp án để so. Nó vẫn là node khi căn,
  vẫn là đầu cạnh G4, và được đếm riêng theo chương.
- **Chương chưa đủ hai người trước ngày đóng băng vàng (06/11):** vàng chỉ phủ các chương đã đủ, và bộ chấm giới hạn phạm vi đích theo các chương đó. Số chương
  thực phủ được báo theo cuốn.
- Phiếu sai thì gửi lại, không sửa hộ. Người giữ không phán thay sinh viên.

## 11. Thứ tự cắt khi trễ

Cắt theo đúng thứ tự dưới đây, và chỉ cắt bước kế khi bước trước không đủ:
1. bỏ ablation docling;
2. giảm K từ 5 xuống 3 (lượt chính cộng seed 1, 2);
3. cắt ở ranh giới chương (vàng chỉ phủ các chương đã xong).

Không cắt phương pháp: không bỏ ba phép kiểm định, không bỏ bước căn, không bỏ phiếu kiểm căn 20%, không đổi thước chính. Mỗi lần cắt ghi ở mục 14.

## 12. Mô phỏng công suất

Cách làm: `thong_ke.cong_suat.mo_phong_cong_suat`. Đầu vào là hiệu thước theo chương (hệ chính trừ hệ so sánh) đo trên tập phát triển; 8 cuốn × 3 chương;
1.000 mô phỏng × 1.000 hoán vị; α = 0,05. Kết quả báo hiệu ứng nhỏ nhất đạt công suất 0,8.

| Phép kiểm định | Số chương phát triển dùng | Hiệu ứng nhỏ nhất đạt công suất 0,8 |
|---|---|---|
| Q6 hệ chính so với B1 | CHỜ | CHỜ |
| F1 quan hệ hệ chính so với B5 | CHỜ | CHỜ |
| Bằng chứng có thật hệ chính so với B5 | CHỜ | CHỜ |

Tập phát triển chỉ có vài chương, nên mô phỏng này chỉ ước cỡ, không phải bảo đảm. Hiệu ứng nhỏ hơn mức phát hiện được sẽ được báo là "không đủ công suất để kết
luận", không phải "không có khác biệt".

## 13. Danh sách đóng băng

Điền ngày 06–07/11. Mọi lượt tập thử phải khớp đúng các giá trị này; lệch thì lượt không được dùng cho số chính.

| Mục | Giá trị |
|---|---|
| Commit mã (sản phẩm và `evaluation/`) | CHỜ |
| Hash cấu hình hệ chính (`config_hash` của manifest các khâu, từ dry-run) | CHỜ |
| Mô hình LLM, transport | `gemini-3.1-flash-lite`, Vertex |
| Mô hình ML đóng băng (DG-20) | A1 `r2-full-v2-dg20` (M1 7 lá, M2 15 lá, M3 7 lá); pass phụ `e5-d01-a-v2-dg20` |
| SHA-256 manifest và PDF 8 cuốn | `evaluation/bo-sach/thu/bang-hash.json` (SHA-256 của tệp này: CHỜ) |
| SHA-256 vàng G1–G4 mỗi cuốn (tệp ở sổ người giữ, ngoài repo) | CHỜ |
| SHA-256 tệp ánh xạ trạng thái | CHỜ |
| SHA-256 lời nhắc B5 | CHỜ |
| SHA-256 hướng dẫn gán G3 (g3-2), G4 (g4-1), G5 | CHỜ |

## 14. Nhật ký hậu kiểm

Mỗi dòng gồm ngày, mục bị đổi, lý do, và đổi trước hay sau khi thấy số tập thử. Bản dk-1 bắt đầu với bảng rỗng.

| Ngày | Mục | Thay đổi | Lý do | Trước hay sau khi thấy số |
|---|---|---|---|---|
