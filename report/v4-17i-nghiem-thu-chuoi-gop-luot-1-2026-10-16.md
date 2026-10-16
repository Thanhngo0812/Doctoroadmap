# Vé 17i — Nghiệm thu chuỗi gộp, lượt 1 (2026-10-16)

**Phán (cập nhật sau lượt cuối, mục 7–8): đạt với cấu hình đã chốt; chủ dự án quyết đổi mặc định sau đợt này.** Phần dưới đây là lượt 1.
- Neo và trạng thái dạy đạt.
- E4 trên doc-1 và xstk không kém v3.
- Số gộp sai mà vàng phát hiện được không tăng.
- Có ba lỗi phải sửa (vé 17j).
- Ở cấu hình spec chọn, chuỗi gộp **đắt hơn** v3. Nguyên nhân là nguồn đề cử theo mô tả nháp. Bỏ nguồn này thì doc-1 rẻ hơn v3 24% mà chất lượng gộp
  không kém đi.
- Còn thiếu: lượt cuối theo cấu hình sau 17j, và E4 của doc-4. Cả hai cần chủ dự án nâng trần chi.

## Cách chạy

- **Kho riêng:** `tmp/v4-17i/artifacts`, chép từ kho chính phần trước đồ thị của 6 tài liệu, không có thư mục `graph`. Chuỗi v3 và T-01 không bị đụng.
- **Đầu vào:** cùng bộ ứng viên A3 mà canonical v3 đã dùng. Đã kiểm cả 6 tài liệu.
- **Mô hình:** gemini-3.1-flash-lite, qua Vertex. Pass phụ là `a8-secondary-ml-v1`, mặc định sau vé 18e.
- **Script** (`scripts/gop-khau/`):
  - `so_chuoi_gop.py`: so gộp, trạng thái dạy và neo với v3;
  - `chi_phi_lanh.py`: chi phí một lượt chạy từ đầu, cộng token của mọi lời, kể cả lời tái dùng;
  - `cham_gop.py`: E4, quy id vàng qua bảng chuyển hướng (vé 17h);
  - `thu_prompt_gop.py`: hỏi lại lời phán cụm và lời phán sửa theo biến thể.
- **Pha A** (sau khi tìm ra lỗi): phán sửa mỗi cặp một lời, neo "một khái niệm". Chế độ neo này không có lời gọi A5 gộp nên tránh được lỗi sập.
- **xstk:** chuỗi đồ thị cần `--allow-text-quality-reason`. Chốt VNI ở trang 3 mới có sau lượt v3; chunk vẫn là chunk đã chấm.

## 1. Ba lỗi (vé 17j)

1. **Sập khi một lời gọi A5 gộp trượt kiểm sau mọi lượt sửa** (`KeyError: 'reused'`).
   - xstk sập sau 115 giây, doc-4 sau 16 phút.
   - Canonical không có checkpoint nên tiền của các lượt đó mất trắng, khoảng 0,85 USD.
2. **Gom lô lời phán sửa làm mô hình né gộp các cặp đồng nghĩa và bản dịch.** Đo trên các lời phán sửa có thật của nhap-mon-ml:

   | Biến thể | Cặp v3 có mà chuỗi gộp bỏ sót, được gộp lại | USD |
   |---|---|---|
   | prompt chuỗi gộp, lô 10 | 1/5 | 0,094 |
   | prompt chuỗi gộp, mỗi mục một lời | 5/5 | 0,111 |
   | prompt sửa thử, mỗi mục một lời | 5/5 | 0,114 |

   doc-6 cũng vậy: CSDL = Cơ sở dữ liệu và DBMS chỉ được gộp khi hỏi từng mục.
3. **R2 không bắt được `synonym` / `coextensive_with` nối hai node tách rời.**

## 2. Chi phí: một lượt chạy từ đầu, các bước trước A8

| Tài liệu | v3: A4/A5 + provenance + C8 + danh tính | Chuỗi gộp, pha A | Chuỗi gộp, bỏ đề cử theo mô tả |
|---|---|---|---|
| doc-1 | 918 lời, 0,478 USD | 877 lời, 0,611 USD | **514 lời, 0,365 USD** |
| doc-4 | 2.295 lời, 1,367 USD | 2.648 lời, 2,188 USD | chưa chạy |
| doc-6 | 78 lời, 0,035 USD | 75 lời, 0,048 USD | chưa chạy |

xstk, nhap-mon-ml và naive-bayes không so được: canonical v3 của chúng chạy trước khi nhật ký có ghi token.

**Lời phán sửa là phần làm chi phí phình ra:** doc-4 tốn 1.545 lời và 1,275 USD, doc-1 tốn 490 lời và 0,336 USD. Nguyên nhân là đề cử theo mô tả nháp:
- doc-4 có 1.570/2.129 cạnh đề cử từ nguồn này;
- trên 4 tài liệu, khoảng 720 cặp chỉ có nguồn mô tả, và chỉ ra 4 lần gộp: 1 đúng ("Hạng của f = dim(Imf)"), 2 sai ("Hàm thực liên tục = Không
  gian C[a,b]", "Đổi chỗ hai hàng = Tính chất 2"), 1 chưa rõ;
- tiêu chí cùng ngoại diên bác gần hết các cặp này, kể cả Nhân = KerT.

**Bỏ nguồn này trên doc-1** (ngưỡng cosine bằng 1,0, không sửa mã):
- **chi phí:** −44% lời gọi, −24% USD so với v3;
- **gộp:** cụm sạch hơn, nên gộp đúng thêm Nhân = KerT, Gram-Schmidt, độc lập / phụ thuộc tuyến tính với "Hệ véc tơ …". Mất "Hạng của f = dim(Imf)";
- **neo:** đích vàng không đổi.

Phần neo còn gọi riêng (211 lời trên doc-1). Gom neo vào A5 sau 17j sẽ bớt thêm.

**Thời gian:**
- canonical chuỗi gộp pha A: doc-4 27 phút, doc-1 7,7 phút (có tái dùng một phần);
- chuỗi đồ thị gộp: doc-1 4,6 phút, xstk 3,1 phút.

Ba stage cũ của v3 không ghi thời gian, nên chưa so phút được.

## 3. Gộp

Gộp sai mà vàng phát hiện được (cạnh vàng có hai đầu bị gộp làm một). Mốc của spec là 3.

| | doc-1 | xstk | doc-4 | tổng |
|---|---|---|---|---|
| v3 | 1 (Tọa độ = Véc tơ tọa độ) | 2 (Độ tin cậy; Xác định kích thước mẫu = … trong ước lượng trung bình) | 0 | 3 |
| chuỗi gộp | 0 | 3 (Độ tin cậy; Tỉ lệ mẫu = Tỉ lệ mẫu tổng quát; Bài toán tìm kích thước mẫu = Xác định kích thước mẫu) | 0 | 3 |

Tiêu chí cùng ngoại diên **chặt hơn** v3. Nó sửa được các gộp sai của v3:
- A4 v3 gộp phân loại / phân cụm / hồi qui;
- "Ý thức xã hội lạc hậu = vượt trước tồn tại xã hội";
- Cantơ = Triết học Cantơ;
- Tọa độ = Véc tơ tọa độ.

Nhưng nó bỏ sót nhiều cặp đồng nghĩa mà A4 v3 hoặc danh tính v3 bắt được:
- Thuyết không thể biết = Bất khả tri, Hoài nghi luận = Thuyết hoài nghi, Nhận thức luận = Lý luận nhận thức (doc-4);
- Bao tuyến tính = Không gian con sinh bởi…, Tự đồng cấu = Toán tử tuyến tính (doc-1);
- χα 2 = χα^2 (xstk).

Thử prompt sửa (cấm `subtype_of` giữa hai tên, cấm quan hệ đồng nhất giữa hai node) trên đúng các cặp này: gộp lại được 5 cặp đúng, nhưng kéo về 3
gộp sai, trong đó có 2/3 gộp sai mà vàng đã biết. **Không đổi prompt.**

Một chỗ cần chủ dự án quyết: theo cùng ngoại diên, "Độc lập tuyến tính" (tính chất) và "Hệ véc tơ độc lập tuyến tính" (đối tượng mang tính chất)
là khác loại nên tách ra. Nhưng với lộ trình học thì đó là một bài.

## 4. Neo và trạng thái dạy (pha A, neo "một khái niệm")

| | Đích vàng: cùng trạng thái | Đích vàng: cùng câu neo | Mọi khái niệm "được dạy": cùng câu neo |
|---|---|---|---|
| doc-1 | 25/26 | 25/26 | 196/203 |
| xstk | 26/26 | 24/26 | 68/72 |
| doc-4 | 47/47 | 46/47 | 461/483 |

Bỏ provenance khỏi vùng tìm không làm mất neo của đích vàng nào. So chế độ neo gom vào A5 với mốc này để ở lượt cuối, sau 17j.

## 5. E4 (pha A, pass phụ ML sản phẩm, vàng quy id qua bảng chuyển hướng)

| | Q7 | Q7b | trực tiếp P / R | bao đóng P / R |
|---|---|---|---|---|
| doc-1 v3 (mốc 18d) | 0,603 | 0,743 | 0,438 / 0,500 | 0,821 / 0,664 |
| doc-1 chuỗi gộp | **0,725** | 0,707 | **0,577 / 0,517** | 0,802 / **0,701** |
| xstk v3 (mốc 18d) | 0,206 | 0,530 | 0,333 / 0,143 | 0,593 / 0,163 |
| xstk chuỗi gộp | **0,230** | **0,730** | **0,500 / 0,222** | **0,839 / 0,248** |

Pass chính được chạy lại, nên một phần chênh là nhiễu của LLM. Chuỗi gộp không làm hạng mục nào tụt quá 0,04. Chưa có E4 của doc-4: riêng pass chính
doc-4 tốn khoảng 2,2 USD, vượt phần trần còn lại.

## 6. Chi và việc tiếp theo

**Đã chi khoảng 5,6 USD trên trần 6 USD:**
- canonical chuỗi gộp: 3,65 USD, kể cả doc-4 2,11 USD;
- chuỗi đồ thị doc-1 và xstk: 0,53 USD;
- thử prompt và lời phán sửa: khoảng 0,6 USD;
- mất trắng vì hai lượt sập: khoảng 0,85 USD.

**Đề xuất:**
1. 17j thêm việc thứ tư: chuỗi gộp **tắt đề cử theo mô tả mặc định**, giữ tuỳ chọn. Spec mục 3.1 cần ghi đính chính.
2. Sau 17j, chạy lượt cuối theo cấu hình mặc định: neo gom vào A5, phán sửa từng cặp, không đề cử theo mô tả. Phần lớn lời gọi được tái dùng.
   - canonical 6 tài liệu, khoảng 0,8 USD;
   - E4 doc-1 và xstk, khoảng 0,55 USD;
   - nếu chủ dự án muốn: E4 doc-4, khoảng 2,6 USD.

## 7. Lượt cuối (sau 17j; đề cử theo mô tả tắt bằng ngưỡng 1,0, nay là cấu hình mặc định của 17k)

**Cấu hình:** neo gom vào A5 (mặc định của 17d), phán sửa từng cặp. Chạy trên 3 tài liệu vàng, đủ cả canonical lẫn chuỗi đồ thị. Lượt này tốn 3,74 USD;
**tổng của vé 17i khoảng 9,3 USD**, trong trần 10 USD mà chủ dự án đã nâng.

**Chi phí các bước trước A8, một lượt chạy từ đầu.** Cột "chuỗi gộp" lấy hàng nhật ký cho gộp, phán sửa, xác minh và mô tả; phần neo lấy theo
`cost_summary`, vì nhật ký neo có mang theo hàng của lượt trước.

| | v3 | chuỗi gộp, neo A5 | chuỗi gộp, neo "một khái niệm" (doc-1 đo, doc-4 ước) |
|---|---|---|---|
| doc-1 | 918 lời, 0,478 USD | ~309 lời, ~0,356 USD | 514 lời, 0,365 USD |
| doc-4 | 2.295 lời, 1,367 USD | ~963 lời, ~1,24 USD | ~1.550 lời, ~1,26 USD |

**Thời gian.**
- canonical: doc-4 14,7 phút, doc-1 2,6 phút, xstk 1,5 phút (có tái dùng phần gộp);
- chuỗi đồ thị: doc-4 32 phút (pass chính 13,7 phút; pass phụ ML 9,9 phút, dài hơn 3,8 phút đo ở 18d), doc-1 4,3 phút, xstk 3,9 phút.

**E4.**

| | Q7 | Q7b | trực tiếp P / R | bao đóng P / R | khái niệm trong dãy học |
|---|---|---|---|---|---|
| doc-1 v3 / pha A / cuối | 0,603 / 0,725 / 0,419 | 0,743 / 0,707 / 0,645 | 0,438-0,500 / 0,577-0,517 / 0,516-0,552 | 0,821-0,664 / 0,802-0,701 / 0,713-0,465 | — / 208 / 205 |
| xstk v3 / pha A / cuối | 0,206 / 0,230 / 0,278 | 0,530 / 0,730 / 0,506 | 0,333-0,143 / 0,500-0,222 / 0,286-0,111 | 0,593-0,163 / 0,839-0,248 / 0,618-0,324 | — / 72 / 77 |
| doc-4 v3 / cuối | 0,483 / **0,638** | 0,859 / **0,878** | 0,667-0,566 / **0,739-0,642** | 0,856-0,522 / **0,893-0,629** | 489 / 549 |

**Nhiễu của E4 lớn hơn mọi khác biệt cần đo.**
- Ở doc-1, Q7 tụt từ 0,725 (pha A) xuống 0,419 (lượt cuối). Nguyên nhân là chiều của một cạnh trục bị đảo: "Không gian véc tơ → Véc tơ" do pass chính
  tạo ở pha A, còn ở lượt cuối pass chính không tạo, và pass phụ ML chọn chiều ngược lại.
- Câu neo của hai khái niệm này giống hệt nhau ở hai lượt. Cái khác là đầu vào phiên, vì vài lần gộp khác nhau làm cách xếp phiên khác đi.
- Vì vậy E4 chạy một lượt không phân định được hai chuỗi. Nó chỉ cho thấy chuỗi gộp không làm hại một cách hệ thống. doc-4 tốt hơn v3 ở mọi chỉ số.

**Neo gom vào A5 so với neo "một khái niệm".**
- **doc-1:** lệch 5 trạng thái, 6/203 câu neo.
- **xstk:** đích vàng còn khớp trạng thái v3 21/26, so với 26/26 khi neo "một khái niệm". Trong 5 lần đổi có 4 lần là sửa đúng: 3 đích bị A2 gắn nhầm
  "đề cương" được đưa về "được dạy" (vé 05), và "Phân phối chuẩn" được đưa về "chỉ nhắc". Nhưng có hai câu neo yếu: một câu liệt kê, một dòng
  tiêu đề.
- **doc-4:** 67 khái niệm từ "chỉ nhắc" thành "được dạy", so với 9 khi neo "một khái niệm". Đọc mẫu 12 thì khoảng 9 là chỉ được nhắc. Dãy học
  dài thêm 60 khái niệm, và E4 không thấy được việc này.
- **Tiền:** gần bằng nhau, vì lời A5 gộp mang câu ứng viên của nhiều khái niệm. Neo A5 chỉ bớt số lời gọi.

**Gộp sai mà vàng phát hiện được, lượt cuối:** doc-1 0, xstk 3, doc-4 0. Tổng 3, đúng bằng mốc của v3.

## 8. Phán nghiệm thu

**Đạt, với cấu hình đã chốt.** Chủ dự án quyết ngày 2026-10-16: chuỗi gộp thành mặc định sau đợt này. Lý do là ba stage cũ kéo dài thời gian, và
trình bày tốn công.

**Cấu hình:**
- tắt đề cử theo mô tả (17k);
- phán sửa từng cặp (17j);
- **đề xuất neo "một khái niệm"**: tiền như neo A5, mà phán "được dạy" sát C8. Chờ chủ dự án duyệt.

**Việc tiếp theo** là nghiên cứu cải thiện, báo cáo `report/nghien-cuu-cai-thien-chuoi-gop-2026-10-16.md`:
- bớt lời gọi neo bằng luật tất định;
- xem lại hiệu suất từng nguồn đề cử;
- phục hồi gộp đồng nghĩa bị sót;
- đo thời gian từng phần (`phase_measurements` đang ra 0);
- xử lý độ nhạy của pass chính với cạnh trục;
- lên kế hoạch đổi mặc định: T-01 quy id vàng, gỡ ba stage cũ.
