# Hướng dẫn gán nhãn D-01 cho agent: quan hệ tiên quyết trong đoạn định nghĩa

Bạn là agent gán nhãn. Đọc hết hướng dẫn này một lần trước khi bắt đầu, và mở lại khi phân vân.

Mỗi phiếu nói về **một khái niệm Y** được dạy trong một giáo trình tiếng Việt. Phiếu chép đoạn văn định nghĩa Y và một danh sách **ứng viên X**.
Với **mỗi** ứng viên X của **mỗi** phiếu, bạn chọn **đúng một nhãn** cho biết X đứng ở đâu so với Y *trong đoạn văn đó*.

Nhãn của bạn dùng để huấn luyện một bộ phân loại quan hệ tiên quyết, chạy không cần mô hình ngôn ngữ lớn.

## 1. Bạn nhận gì, trả gì

| tệp | vai trò |
|---|---|
| `phieu.jsonl` | đầu vào: mỗi dòng một phiếu (JSON) |
| hướng dẫn này | luật gán |
| `kiem_nhan_d01.py` | script tự kiểm định dạng; chỉ cần Python, không cần thư viện ngoài |
| `nhan-A.jsonl` | **bạn trả về**: mỗi dòng một cặp (phiếu, ứng viên) |

- Không dùng tệp nào khác.
- Không tra cứu mạng.
- Không sửa `phieu.jsonl`.

## 2. Đọc một phiếu

| trường | nghĩa |
|---|---|
| `phieu_id` | mã phiếu. Chép nguyên vào mọi dòng nhãn của phiếu |
| `doc_id`, `linh_vuc` | mã sách (đã ẩn tên) và lĩnh vực |
| `y_id`, `y_ten`, `y_bi_danh` | khái niệm đích Y: mã, tên, tên khác |
| `muc` | đường dẫn mục chứa Y trong sách, từ chương xuống mục nhỏ |
| `cau` | các câu của cửa sổ định nghĩa, dạng `{"i": số, "text": câu}`: tối đa bốn câu trước câu neo, câu neo, hai câu sau |
| `cau_neo` | số `i` của câu mà hệ thống chọn làm câu định nghĩa Y |
| `ung_vien` | danh sách X; mỗi X có các trường ở năm dòng dưới |
| `x_id`, `x_ten`, `x_bi_danh` | mã, tên, tên khác của X |
| `x_dinh_nghia` | câu định nghĩa X trong cùng sách, hoặc `null` nếu không có |
| `cau_co_ten` | các số `i` của câu có tên X (hoặc tên khác của X) |
| `trong_cua_so` | `true` nếu tên X có trong cửa sổ; `false` nếu không, đây là ứng viên "không nguyên văn" |

Lưu ý khi đọc:
- **`cau_neo` có thể lệch.** Nếu câu định nghĩa thật của Y là một câu khác trong cửa sổ, hãy dựa vào câu đó.
- **Chữ được trích từ PDF nên có lỗi.** Ví dụ:
  - âm tiết bị tách: "Ph ươ ng pháp";
  - mất dấu thanh: "có thê" thay cho "có thể";
  - chữ cái trông giống nhưng sai mã: "сủа";
  - ký hiệu toán bị mất: "x 0" thay cho "x ≥ 0".

  Đọc xuyên qua các lỗi đó như người đọc bình thường.
- **Dấu giữ chỗ.** `[formula]` là chỗ có công thức, `[figure]` là chỗ có hình; nội dung của chúng không có trong phiếu. Đánh giá bằng phần chữ còn
  lại.
- **Phiếu độc lập với nhau.** Phiếu đã được xáo thứ tự. Có thể có phiếu trông giống nhau; vẫn gán độc lập từng phiếu, không chép nhãn từ phiếu
  khác.

## 3. Câu hỏi cốt lõi

> **Để hiểu Y _như chính đoạn văn này trình bày_, người đọc có phải biết X trước không?**

Ba nguyên tắc:
1. **Theo đoạn văn, không theo hiểu biết của bạn.**
   - Kiến thức môn học chỉ dùng để *hiểu* câu chữ.
   - Đoạn văn không thể hiện quan hệ thì không gán quan hệ, kể cả khi bạn biết chắc hai khái niệm liên quan.
2. **Chỉ quan hệ trực tiếp.** X chỉ cần cho Y thông qua một ứng viên Z khác của cùng phiếu thì không phải quan hệ trực tiếp.
3. **Mỗi ứng viên đúng một nhãn**, không bỏ sót ứng viên nào.

## 4. Sáu nhãn

| nhãn | khi nào chọn | phép thử |
|---|---|---|
| `can_de_hieu` | X là **thành phần của định nghĩa Y** như sách viết. Gồm các trường hợp: Y được định nghĩa qua X; Y là một loại X; Y là thuộc tính, bộ phận, đại lượng hay phép toán của hoặc trên X; câu bối cảnh của định nghĩa đặt X làm đối tượng ("Xét một hệ chất điểm…") | chưa biết X thì **không hiểu được câu định nghĩa Y** |
| `cong_cu` | X có mặt trong phần trình bày Y với vai trò công cụ, phương pháp đo hay tính, dụng cụ, ví dụ hoặc ký hiệu; nhưng không cần X để hiểu Y là gì | chưa biết X vẫn hiểu Y là gì; cần X để đo, tính, làm bài, chứng minh hay áp dụng Y |
| `khong` | không có quan hệ tiên quyết trực tiếp. Gồm các trường hợp: nhắc thoáng qua; anh em được liệt kê cạnh nhau; so sánh hay đối lập; khuôn khổ hay bối cảnh chung không thuộc định nghĩa; hệ quả hay quy định nói sau định nghĩa; chỉ liên quan gián tiếp qua ứng viên khác; X và Y là cùng một khái niệm; đoạn văn không nói gì về quan hệ | — |
| `nguoc` | **Y mới là tiên quyết của X**: X được định nghĩa qua Y. Căn cứ nằm trong cửa sổ hoặc trong `x_dinh_nghia` | chưa biết Y thì không hiểu X |
| `khop_nham` | **chỉ dùng khi `trong_cua_so` là `true`.** Tên X có trong câu nhưng **không chỉ khái niệm X**: nằm trong một từ hay cụm khác ("chiều" trong "xoay chiều"), hoặc mang nghĩa thường, không phải nghĩa thuật ngữ của sách | — |
| `khong_ro` | đoạn văn hỏng hoặc thiếu đến mức không quyết được | — |

## 5. Quy trình quyết định cho mỗi ứng viên

1. Đọc `y_ten`, `muc` và **toàn bộ** `cau`; xác định câu thật sự định nghĩa hoặc giới thiệu Y. Đọc `x_ten`, `x_bi_danh`, `x_dinh_nghia`.
2. **Bước này chỉ áp dụng khi `trong_cua_so` là `true`.** Xem các câu trong `cau_co_ten`.
   - Nếu **mọi** lần tên X xuất hiện đều không chỉ khái niệm X, chọn **`khop_nham`**.
   - Nếu có ít nhất một lần chỉ đúng X, đi tiếp bước 3.
3. Câu định nghĩa Y, hoặc câu bối cảnh dẫn vào nó, có dựa vào X không? Chưa biết X thì không hiểu câu đó? Có thì chọn **`can_de_hieu`**.
4. Không, nhưng phần trình bày Y dùng X làm công cụ, phương pháp, dụng cụ, ví dụ hay ký hiệu? Có thì chọn **`cong_cu`**.
5. Không, nhưng X được định nghĩa qua Y, thấy trong cửa sổ hoặc trong `x_dinh_nghia`? Có thì chọn **`nguoc`**.
6. Còn lại chọn **`khong`**. Nếu X chỉ liên quan đến Y qua một ứng viên Z khác của cùng phiếu, ghi `x_id` của Z vào `trung_gian`.
7. Không đọc nổi đoạn văn, hoặc đoạn văn không đủ để quyết: chọn **`khong_ro`**. Đừng đoán. Nhưng đoạn văn đọc được mà không cho thấy quan hệ
   thì là `khong`, không phải `khong_ro`.

**Khi hai nhãn cùng đúng:** `can_de_hieu` thắng `cong_cu`. Đoạn văn cho thấy cả hai chiều mâu thuẫn nhau thì chọn `khong_ro`.

## 6. Ca khó

1. **Nhắc tới để giải thích thêm, so sánh hay đối lập**, không phải để định nghĩa: chọn `khong`.
   - Ví dụ: Y = "Thế năng", câu "…khác với động năng, thế năng phụ thuộc vào vị trí của vật": động năng là `khong`.
2. **Cái chung và cái riêng.**
   - "Y là một loại X", hay Y là trường hợp riêng mà sách giải thích bằng cái chung X: `can_de_hieu`.
   - Chiều ngược lại, X là trường hợp riêng của Y: `nguoc`.
3. **Anh em liệt kê.** "Các đặc trưng gồm A, B và C": giữa A, B, C không có quan hệ. Chọn `khong`.
4. **Toàn thể và bộ phận.**
   - Câu định nghĩa Y đi qua từng bộ phận X ("Y gồm X1 và X2, trong đó…"): `can_de_hieu`.
   - Chỉ liệt kê bộ phận rồi thôi: `khong`.
   - Y là bộ phận của X ("Y là lớp ngoài cùng của X"): `can_de_hieu`.
5. **Bối cảnh, khuôn khổ.** Câu mở đầu dạng "Theo quan điểm…", "Trong hệ quy chiếu…", "Ở Việt Nam…" không làm X thành tiên quyết, trừ khi
   định nghĩa thật sự xây trên X. Phân biệt với câu bối cảnh **đặt X làm đối tượng** của định nghĩa ("Cho một mạch điện gồm…", "Xét một
   hệ…"); trường hợp đó là `can_de_hieu`.
6. **Câu nói sau định nghĩa** về hệ quả, quy định, cách dùng hay ví dụ: thường là `cong_cu` (nếu X là công cụ hay phương pháp) hoặc `khong`.
7. **Câu trước câu neo nói về khái niệm khác.** Cửa sổ có thể bắt đầu bằng phần cuối của mục trước. X chỉ xuất hiện ở đó, không dính tới Y:
   `khong`.
8. **Khái niệm rất chung** ("dữ liệu", "hệ thống", "thời gian"). Chỉ gán quan hệ khi đoạn văn cần X **theo nghĩa thuật ngữ** của sách. Tên
   xuất hiện với nghĩa đời thường thì là `khop_nham`.
9. **Cùng một khái niệm** (tên khác, viết tắt, cách gọi khác): chọn `khong`, `ly_do` mở đầu bằng "trùng khái niệm".
10. **Ứng viên không nguyên văn** (`trong_cua_so: false`). Gán cùng luật.
    - Chọn `can_de_hieu` chỉ khi đoạn văn **mô tả rõ** X bằng lời khác hoặc gọi lại X ("trung tâm này"); ghi câu căn cứ.
    - Không có mô tả rõ thì chọn `khong`.
11. **Bắc cầu.** Y cần Z, Z cần X, và Z cũng là ứng viên: X là `khong`, `trung_gian` là Z. Nhưng câu định nghĩa Y dùng thẳng X thì X là
    `can_de_hieu`.

## 7. Ví dụ

Các ví dụ tự soạn để minh hoạ, không lấy từ sách trong phiếu. Dấu * đánh dấu câu neo.

**Ví dụ 1 — Y = "Công suất".**
- [0] Công là đại lượng đo phần năng lượng được truyền qua tác dụng của lực.
- [1]* Công suất là công thực hiện được trong một đơn vị thời gian.
- [2] Đơn vị của công suất là oát (W).

| X | nhãn | cau | trung_gian | lý do |
|---|---|---|---|---|
| Công | can_de_hieu | 1 | — | công suất định nghĩa qua công |
| Năng lượng | khong | — | Công | năng lượng chỉ có trong định nghĩa công |
| Oát | nguoc | 2 | — | oát là đơn vị của công suất, hiểu qua Y |

**Ví dụ 2 — Y = "Khối tâm": câu bối cảnh đặt X làm đối tượng.**
- [0] Xét một hệ chất điểm đặt trong trọng trường đều.
- [1]* Khối tâm của hệ là điểm có tọa độ bằng trung bình cộng tọa độ các phần tử của hệ, lấy trọng số theo khối lượng.

| X | nhãn | cau | lý do |
|---|---|---|---|
| Hệ chất điểm | can_de_hieu | 0 | câu 0 đặt hệ chất điểm làm đối tượng, câu 1 gọi lại là "hệ" |
| Khối lượng | can_de_hieu | 1 | trọng số của định nghĩa |
| Trọng trường đều | khong | — | chỉ là bối cảnh, định nghĩa khối tâm không dựa vào |

**Ví dụ 3 — Y = "Huyết áp": công cụ và chiều ngược.**
- [0]* Huyết áp là áp lực của dòng máu tác động lên thành động mạch.
- [1] Trên lâm sàng, huyết áp được đo bằng huyết áp kế đặt ở cánh tay.
- [2] Kết quả gồm hai trị số là huyết áp tâm thu và huyết áp tâm trương.

| X | nhãn | cau | lý do |
|---|---|---|---|
| Áp lực | can_de_hieu | 0 | huyết áp là một loại áp lực |
| Động mạch | can_de_hieu | 0 | định nghĩa nói áp lực lên thành động mạch |
| Huyết áp kế | cong_cu | 1 | dụng cụ đo, không cần để hiểu huyết áp là gì |
| Huyết áp tâm thu | nguoc | 2 | một trị số của huyết áp, hiểu qua Y |

**Ví dụ 4 — Y = "Độ to của âm": thuộc tính và anh em.**
- [0] Âm có ba đặc trưng sinh lí: độ cao, độ to và âm sắc.
- [1]* Độ to của âm là đặc trưng sinh lí gắn với cường độ âm: cường độ càng lớn, âm nghe càng to.

| X | nhãn | cau | lý do |
|---|---|---|---|
| Âm | can_de_hieu | 1 | độ to là một đặc trưng của âm |
| Cường độ âm | can_de_hieu | 1 | định nghĩa gắn độ to với cường độ âm |
| Âm sắc | khong | — | anh em, chỉ được liệt kê cạnh Y |

**Ví dụ 5 — Y = "Dòng điện xoay chiều": khớp nhầm.**
- [0]* Dòng điện xoay chiều là dòng điện có cường độ biến thiên tuần hoàn theo thời gian.

| X | nhãn | cau | lý do |
|---|---|---|---|
| Dòng điện | can_de_hieu | 0 | Y là một loại dòng điện |
| Chiều | khop_nham | 0 | "chiều" nằm trong cụm "xoay chiều", không chỉ khái niệm Chiều |

**Ví dụ 6 — Y = "Sốt": gọi lại bằng "trung tâm này", trung gian, ứng viên không nguyên văn.**
- [0] Thân nhiệt người bình thường được giữ ổn định quanh 37 °C nhờ trung tâm điều nhiệt ở vùng dưới đồi.
- [1]* Sốt là tình trạng thân nhiệt tăng cao hơn mức bình thường do trung tâm này bị đặt lại ở một ngưỡng cao hơn.

| X | trong_cua_so | nhãn | cau | trung_gian | lý do |
|---|---|---|---|---|---|
| Thân nhiệt | true | can_de_hieu | 1 | — | sốt là thân nhiệt tăng cao |
| Trung tâm điều nhiệt | true | can_de_hieu | 1 | — | câu 1 nói "trung tâm này" bị đặt lại ngưỡng |
| Vùng dưới đồi | true | khong | — | Trung tâm điều nhiệt | chỉ là vị trí của trung tâm điều nhiệt |
| Điều hòa thân nhiệt | false | can_de_hieu | 0 | — | câu 0 mô tả đúng quá trình này; định nghĩa sốt dựa vào nó |
| Hạ thân nhiệt | false | khong | — | — | đoạn văn không nói tới |

**Ví dụ 7 — Y = "Gió mùa": chiều ngược qua định nghĩa X, không dùng hiểu biết ngoài.**
- [0]* Gió mùa là loại gió thổi theo mùa, hướng gió ở hai mùa gần như ngược nhau.
- [1] Ở Việt Nam, gió mùa đông bắc hoạt động từ tháng 11 đến tháng 4 năm sau.

`x_dinh_nghia` của "Gió mùa đông bắc": "Gió mùa đông bắc là gió mùa thổi từ cao áp Xibia về nước ta vào mùa đông."

| X | trong_cua_so | nhãn | cau | lý do |
|---|---|---|---|---|
| Gió | true | can_de_hieu | 0 | gió mùa là một loại gió |
| Gió mùa đông bắc | true | nguoc | null | định nghĩa X: gió mùa đông bắc là một loại gió mùa |
| Hoàn lưu khí quyển | false | khong | — | đoạn văn không nói gì; không dùng hiểu biết ngoài đoạn văn |

**Ví dụ 8 — Y = "Nhịp tim": phương pháp đo, trùng khái niệm.**
- [0]* Nhịp tim là số lần tim co bóp trong một phút.
- [1] Có thể xác định nhịp tim bằng cách bắt mạch ở cổ tay hoặc ghi điện tâm đồ.

`x_dinh_nghia` của "Tần số tim": "Tần số tim là số lần tim đập trong một phút."

| X | trong_cua_so | nhãn | cau | lý do |
|---|---|---|---|---|
| Tim | true | can_de_hieu | 0 | định nghĩa đếm số lần tim co bóp |
| Điện tâm đồ | true | cong_cu | 1 | phương pháp đo, không cần để hiểu nhịp tim là gì |
| Tần số tim | false | khong | — | trùng khái niệm: cũng là số lần tim đập mỗi phút |

**Ví dụ 9 — đoạn văn hỏng.**
- [0]* §g l l¿ ®l ®o b»ng tÝch k l v¿ v t.

Mọi ứng viên của phiếu này chọn `khong_ro`, `cau` là `null`: không đọc được câu định nghĩa.

## 8. Định dạng trả về

Mỗi dòng là một đối tượng JSON, mã UTF-8, cho đúng một cặp (phiếu, ứng viên):

```json
{"phieu_id": "p_0000000000000000", "doc_id": "sach-000000000000", "y_id": "node_…", "x_id": "node_…", "nhan": "can_de_hieu", "cau": 1, "trung_gian": null, "ly_do": "công suất định nghĩa qua công", "nguoi_gan": "tên agent + mô hình + phiên bản", "luot": "A"}
```

| nhãn | `cau` | `trung_gian` |
|---|---|---|
| `can_de_hieu`, `cong_cu` | **bắt buộc**: số `i` của câu căn cứ | `null` |
| `nguoc` | số `i` của câu căn cứ, hoặc `null` nếu căn cứ chỉ nằm trong `x_dinh_nghia` | `null` |
| `khop_nham` | số `i` của câu có lần khớp nhầm, hoặc `null` | `null` |
| `khong` | `null` | `null`, hoặc `x_id` của ứng viên Z khác **cùng phiếu** |
| `khong_ro` | `null` | `null` |

- `phieu_id`, `doc_id`, `y_id`, `x_id` chép nguyên từ phiếu, không tự đặt.
- `ly_do`: tiếng Việt, từ 1 đến 30 từ, nêu căn cứ.
  - Nhãn `khong` vì cùng khái niệm: mở đầu bằng "trùng khái niệm".
  - Nhãn `nguoc` dựa vào `x_dinh_nghia`: nêu "định nghĩa X".
- `nguoi_gan`: giống nhau trong cả lượt, ví dụ `"agent-X / model-Y / 2026-10"`.
- `luot`: `"A"` cho lượt đầu; `"B"` cho lượt độc lập thứ hai; `"C"` cho lượt phân xử nếu được giao.

## 9. Cách làm

1. Làm theo thứ tự dòng của `phieu.jsonl`, mỗi lần khoảng 20 phiếu. Xong mỗi đợt, nối thêm dòng vào `nhan-A.jsonl` rồi tự kiểm:

   ```
   python kiem_nhan_d01.py --phieu phieu.jsonl --nhan nhan-A.jsonl --mot-phan
   ```

   Script in số cặp đã gán và từng lỗi kèm số dòng. Sửa hết lỗi trước khi làm đợt sau.
2. **Làm tiếp sau khi dừng:** chạy lệnh trên để xem tiến độ, rồi làm tiếp từ phiếu đầu tiên chưa đủ nhãn. Không gán lại cặp đã có.
3. **Chạy song song nhiều tiến trình:**
   - chia `phieu.jsonl` theo khoảng dòng, mỗi tiến trình ghi một tệp riêng;
   - xong thì nối các tệp lại;
   - kiểm tệp gộp **không** có `--mot-phan`.
4. **Lượt B, nếu được giao:**
   - không mở tệp nhãn lượt A;
   - nên dùng agent hoặc mô hình khác;
   - ghi `luot` là `"B"` vào tệp `nhan-B.jsonl`.
5. Ghi một tệp ngắn `ghi-chu-A.md`: agent, mô hình, ngày giờ bắt đầu và kết thúc, ước lượng token hoặc chi phí nếu có, các phiếu thấy đáng
   ngờ (ghi `phieu_id` và lý do).

## 10. Bàn giao

- [ ] `nhan-A.jsonl` (và `nhan-B.jsonl` nếu có) qua `kiem_nhan_d01.py` **không** có `--mot-phan`, in "ĐẠT".
- [ ] Mỗi cặp (phiếu, ứng viên) có đúng một dòng trong mỗi lượt.
- [ ] Không dòng nào dựa vào hiểu biết ngoài đoạn văn, hay chép nhãn từ phiếu khác.
- [ ] `ghi-chu-A.md` đi kèm.
