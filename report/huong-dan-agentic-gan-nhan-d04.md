# Hướng dẫn gán nhãn D-04 cho agent: khái niệm được dạy sau có phải học trước không

Bạn là agent gán nhãn. Đọc hết hướng dẫn này một lần trước khi bắt đầu, và mở lại khi phân vân.

Mỗi phiếu nói về **hai khái niệm trong cùng một giáo trình tiếng Việt**. Sách dạy **Y trước**, rồi mới dạy **X ở phần sau**. Phiếu chép đoạn văn
định nghĩa Y và đoạn văn định nghĩa X. Với mỗi phiếu, bạn chọn **đúng một nhãn** trả lời câu hỏi:

> **Người học đọc sách theo đúng thứ tự, tới chỗ Y. Họ có phải học X trước rồi mới hiểu được Y không?**

Nhãn của bạn dùng để quyết cách một lộ trình học tự động xếp thứ tự khái niệm. Mỗi lộ trình phải chọn giữa giữ thứ tự của sách, hoặc kéo X lên
trước Y.

> **Bản 1.0, 2026-10-15.** Soạn sau khi Claude thử gán 30 phiếu. Các ca khó ở mục 5 lấy từ những chỗ thử gán thấy mơ hồ.

## 1. Bạn nhận gì, trả gì

| tệp | vai trò |
|---|---|
| `phieu.jsonl` | đầu vào: mỗi dòng một phiếu (JSON) |
| hướng dẫn này | luật gán |
| `kiem_nhan_d04.py` | script tự kiểm định dạng; chỉ cần Python, không cần thư viện ngoài |
| `nhan-A.jsonl` | **bạn trả về**: mỗi dòng một phiếu |

- Không dùng tệp nào khác.
- Không tra cứu mạng.
- Không sửa `phieu.jsonl`.

## 2. Đọc một phiếu

| trường | nghĩa |
|---|---|
| `phieu_id` | mã phiếu. Chép nguyên vào dòng nhãn |
| `doc_id`, `linh_vuc` | mã giáo trình (đã che) và lĩnh vực |
| `y.ten`, `y.bi_danh` | tên khái niệm Y và các tên khác của nó |
| `y.muc` | chuỗi tiêu đề mục nơi Y được định nghĩa, từ cấp ngoài vào trong |
| `y.cau` | đoạn văn quanh chỗ định nghĩa Y: mỗi câu có số `i` |
| `y.cau_neo` | số `i` của câu mà hệ thống cho là câu định nghĩa Y. Có thể sai; tự đọc lại |
| `y.cau_co_ten_x` | các câu của Y có tên hay bí danh của X, do máy dò. **Máy dò có thể nhầm** (xem ca 4); mảng rỗng nghĩa là đoạn văn Y không gọi tên X |
| `x.ten`, `x.bi_danh`, `x.muc`, `x.cau`, `x.cau_neo` | tương tự cho X, tại chỗ X được dạy, **ở phần sau của sách** |

Văn bản được chép tự động từ PDF: có thể dính chữ, tách chữ ("y ếu tố"), mất công thức (`[formula]`) hay lẫn tiêu đề và chú thích hình. Đọc
qua các lỗi đó. Chỉ khi đoạn văn hỏng tới mức không hiểu được thì mới chọn `khong_ro`.

`bi_danh` cũng do máy gom, có khi sai: một bí danh của X có thể là tên một khái niệm khác. Phán theo nghĩa của X ở đoạn văn X, không theo bí danh.

## 3. Bảy nhãn

| nhãn | khi nào chọn |
|---|---|
| `can_hoc_truoc` | X là **thành phần của định nghĩa Y** (Y được định nghĩa qua X, Y là một loại X, Y là thuộc tính hay phép toán trên X…), đoạn văn Y **không** tự giải thích X, và người đọc của giáo trình này **không** thể tự hiểu X theo nghĩa thường. Chưa học X thì không hiểu câu định nghĩa Y |
| `du_tai_cho` | X là thành phần của định nghĩa Y, nhưng **đoạn văn Y có một câu giải thích X** đủ để hiểu Y: một định nghĩa sơ bộ, một chú thích, một ví dụ cụ thể. Phần sau của sách chỉ trình bày X đầy đủ hơn |
| `kien_thuc_nen` | Y dùng X, nhưng người đọc đúng đối tượng của giáo trình **đã hiểu X đủ dùng** cho Y: từ ngữ thông thường, kiến thức phổ thông, hay môn học trước. Đoạn văn Y không giải thích X, và không cần giải thích |
| `nghia_khac` | chữ khớp với tên X ở đoạn văn Y **không chỉ khái niệm X** như đoạn văn X định nghĩa: một từ khác trùng chữ, một phần của thuật ngữ khác, nghĩa thường hay nghĩa khác, hoặc bí danh sai |
| `khong_tien_quyet` | không có quan hệ tiên quyết trực tiếp: X chỉ nhắc thoáng qua, chỉ trong ví dụ hay áp dụng, là anh em được liệt kê cạnh Y, để so sánh, là khuôn khổ chung ("theo quan điểm…", "theo Luật này"), chỉ liên quan gián tiếp, đoạn văn Y không gọi tên X, hoặc X và Y là **cùng một khái niệm** |
| `nguoc` | **Y mới là tiên quyết của X**: X được định nghĩa qua Y, X là một loại hay một phần của Y. Căn cứ ở đoạn văn X hoặc đoạn văn Y |
| `khong_ro` | đoạn văn hỏng hay thiếu tới mức không quyết được |

Chỉ `can_hoc_truoc` dẫn tới việc đảo thứ tự sách. Vì vậy hãy chọn nó khi bạn thật sự thấy người học bị kẹt ở Y nếu chưa học X.

## 4. Quy trình quyết định

Đi lần lượt, dừng ở bước đầu tiên khớp:

1. Đọc toàn bộ `y.cau` và `x.cau`. Xác định câu thật sự định nghĩa hay giới thiệu Y, và câu định nghĩa X.
2. **Chữ có chỉ đúng X không?** Xem các câu trong `y.cau_co_ten_x`. Nếu mọi lần xuất hiện đều không chỉ khái niệm X như đoạn văn X định nghĩa, chọn
   **`nghia_khac`** (ca 4).
3. **Cùng một khái niệm?** Y và X là một (tên khác, tiếng Anh và tiếng Việt, viết tắt): chọn **`khong_tien_quyet`**, `ly_do` mở đầu bằng "trùng
   khái niệm".
4. **Ngược chiều?** Đoạn văn X định nghĩa X qua Y, hoặc đoạn văn Y định nghĩa X như hệ quả của Y, hay X là một loại, một phần của Y: chọn
   **`nguoc`**.
5. **X có là thành phần của định nghĩa Y không?** Bỏ X đi thì câu định nghĩa Y còn hiểu được không? Nếu X chỉ ở ví dụ, áp dụng, liệt kê, so sánh,
   khuôn khổ, hay không được gọi tên: chọn **`khong_tien_quyet`**.
6. X là thành phần của định nghĩa Y. Xét theo thứ tự:
   - đoạn văn Y có câu giải thích X → **`du_tai_cho`**, ghi câu đó vào `cau_giai_thich`;
   - người đọc giáo trình này hiểu X đủ dùng mà không cần học → **`kien_thuc_nen`**;
   - còn lại → **`can_hoc_truoc`**.
7. Không quyết được vì đoạn văn → **`khong_ro`**. Đừng đoán. Đoạn văn đọc được mà không cho thấy quan hệ thì là `khong_tien_quyet`, không phải
   `khong_ro`.

## 5. Ca khó

1. **X chỉ có trong ví dụ hay câu áp dụng** ("Thí dụ, trong…", "điều này giúp ích cho việc…"): `khong_tien_quyet`. Bộ nhãn này không có nhãn "công
   cụ"; ví dụ không làm X thành tiên quyết của Y.
2. **Đoạn văn Y không gọi tên X** (`cau_co_ten_x` rỗng): chỉ chọn nhãn khác `khong_tien_quyet` khi đoạn văn Y **mô tả rõ** X bằng lời khác.
3. **Từ rất chung** ("thời gian", "dữ liệu", "hệ thống", "giá cả"). Hỏi: đoạn văn Y dùng chữ đó theo nghĩa người đọc vốn biết, hay theo
   đúng định nghĩa riêng mà đoạn văn X đưa ra?
   - Nghĩa vốn biết, và nghĩa đó đủ để hiểu Y: `kien_thuc_nen`.
   - Đoạn văn X định nghĩa một nghĩa hẹp, kỹ thuật, khác với cách Y dùng (ví dụ X là "Ứng suất", có bí danh "áp lực", còn Y chỉ nói
     "áp lực cạnh tranh"): `nghia_khac`.
   - Định nghĩa Y thật sự dựa trên nghĩa riêng của X, mà người đọc không tự biết: `can_hoc_truoc`.
4. **Trùng chữ nhưng khác nghĩa** — `nghia_khac`:
   - từ khác cùng chữ: một chữ viết tắt in hoa trùng một từ tiếng Việt viết thường, vì máy dò không phân biệt chữ hoa và chữ thường;
   - một phần của thuật ngữ khác: X = "Mạng" (mạng máy tính), nhưng đoạn văn Y chỉ có "mạng sống", "mạng nhện";
   - động từ hay tính từ thường: X = "Sửa" (một quyền trên tệp), đoạn văn Y có "ta sửa lại kết quả đo";
   - bí danh sai: X = "Thấu kính hội tụ" có bí danh "kính", nhưng đoạn văn Y nói "cửa kính".
5. **Từ khung định nghĩa** ("là một đại lượng dùng để chỉ…", "là một khái niệm…", "là phương pháp…"). Khi X là chính từ khung đó, nội
   dung định nghĩa Y thường vẫn hiểu được mà không cần định nghĩa riêng của X: `kien_thuc_nen`. Chọn `can_hoc_truoc` chỉ khi định nghĩa Y dùng các
   đặc điểm riêng của X.
6. **Khuôn khổ** ("theo quan điểm của trường phái…", "theo quy định của Luật này"): `khong_tien_quyet`.
7. **Liệt kê bộ phận hay anh em** ("chia thành hai giai đoạn là A và B", "các loại gồm…"): giữa các mục không có quan hệ. Chọn `khong_tien_quyet`.
   Nếu X là một mục trong danh sách các bộ phận hay các loại của Y, thì xét `nguoc` ở bước 4.
8. **`du_tai_cho` hay `kien_thuc_nen`.** `du_tai_cho` đòi một câu cụ thể trong `y.cau` giải thích X (ghi vào `cau_giai_thich`). Không có câu như vậy
   mà X vẫn dễ hiểu thì là `kien_thuc_nen`.
9. **Thuật ngữ "trong suốt"** ("bên bán", "nguồn sáng"): đọc theo chữ là hiểu đủ cho Y, nên chọn `kien_thuc_nen`. Phần sau của sách có thể nêu
   điều kiện pháp lý hay kỹ thuật chi tiết, nhưng Y không cần tới.
10. **Câu định nghĩa Y có giải thích luôn cơ chế của X**: chọn `du_tai_cho`. Ví dụ Y là một phương pháp cụ thể của X, và câu định nghĩa Y tả lại X làm
    gì.

## 6. Ví dụ (minh hoạ, không lấy từ phiếu)

1. **`can_hoc_truoc`.** Sách cơ học dạy "Gia tốc" ở chương 1 với câu "Gia tốc là đại lượng đo độ biến thiên của vận tốc theo thời gian", nhưng
   tới chương 2 mới định nghĩa "Vận tốc". Đoạn văn Gia tốc không nói vận tốc là gì, và "vận tốc" ở đây là đại lượng có hướng, không phải "tốc độ"
   thường ngày. Y = Gia tốc, X = Vận tốc: `can_hoc_truoc`.
2. **`du_tai_cho`.** Y = "Lãi suất thực", đoạn văn: "[0] Lạm phát, tức mức tăng chung của giá cả, làm giảm sức mua của đồng tiền. [1] Lãi suất thực
   bằng lãi suất danh nghĩa trừ đi tỷ lệ lạm phát." X = "Lạm phát" được định nghĩa đầy đủ ở chương sau. Câu [0] đã giải thích đủ: `du_tai_cho`,
   `cau_y` 1, `cau_giai_thich` 0.
3. **`kien_thuc_nen`.** Giáo trình địa lý dân cư: Y = "Mật độ dân số", "số người sinh sống trên một đơn vị diện tích lãnh thổ". X = "Diện tích" được
   định nghĩa sau, trong chương bản đồ, theo nghĩa phép đo trên hệ chiếu. Người đọc hiểu "diện tích" đủ dùng: `kien_thuc_nen`.
4. **`nghia_khac`.** Y = "Xác thực hai lớp": "người dùng nhập mật khẩu và mã PIN gửi về điện thoại". X = "Pin" (nguồn điện của thiết bị), dạy ở chương
   phần cứng. Chữ "PIN" là mã số, không phải pin: `nghia_khac`.
5. **`khong_tien_quyet`.** Y = "Đường bàng quan": "Đường bàng quan nối các giỏ hàng cho cùng mức thỏa mãn. Thí dụ, giỏ gồm xăng và vé xe buýt." X = "Xăng sinh
   học" được dạy sau. X chỉ ở ví dụ: `khong_tien_quyet`.
6. **`nguoc`.** Y = "Tam giác", X = "Tam giác vuông" dạy sau: "Tam giác vuông là tam giác có một góc vuông." X là một loại Y: `nguoc`.

## 7. Định dạng trả về

Mỗi dòng là một đối tượng JSON, mã UTF-8, cho đúng một phiếu:

```json
{"phieu_id": "p_0000000000000000", "nhan": "du_tai_cho", "cau_y": 1, "cau_giai_thich": 0, "ly_do": "câu 0 giải thích lạm phát đủ để hiểu lãi suất thực", "nguoi_gan": "tên agent + mô hình + phiên bản", "luot": "A"}
```

| nhãn | `cau_y` | `cau_giai_thich` |
|---|---|---|
| `can_hoc_truoc`, `kien_thuc_nen` | **bắt buộc**: số `i` của câu Y dùng X | `null` |
| `du_tai_cho` | **bắt buộc**: số `i` của câu Y dùng X | **bắt buộc**: số `i` của câu Y giải thích X |
| `nghia_khac` | **bắt buộc**: số `i` của câu có chữ khớp nhầm | `null` |
| `khong_tien_quyet`, `nguoc`, `khong_ro` | số `i` của câu căn cứ, hoặc `null` | `null` |

- Số `i` luôn lấy trong `y.cau`. Căn cứ chỉ có ở đoạn văn X (thường gặp với `nguoc`) thì để `cau_y` là `null` và nêu trong `ly_do`.
- `ly_do`: tiếng Việt, từ 1 đến 30 từ, nêu căn cứ. Trùng khái niệm thì mở đầu bằng "trùng khái niệm".
- `nguoi_gan`: giống nhau trong cả lượt, ví dụ `"agent-X / model-Y / 2026-10"`.
- `luot`: `"A"` cho lượt đầu; `"B"` cho lượt độc lập thứ hai; `"C"` cho lượt phân xử nếu được giao.

## 8. Cách làm

1. Làm theo thứ tự dòng của `phieu.jsonl`, mỗi lần khoảng 20 phiếu. Xong mỗi đợt, nối thêm dòng vào `nhan-A.jsonl` rồi tự kiểm:

   ```
   python kiem_nhan_d04.py phieu.jsonl nhan-A.jsonl --mot-phan
   ```

   Script in số phiếu đã gán và từng lỗi kèm `phieu_id`. Sửa hết lỗi định dạng trước khi làm đợt sau. Không đổi nhãn chỉ vì script.
2. **Làm tiếp sau khi dừng:** chạy lệnh trên để xem tiến độ, rồi làm tiếp từ phiếu đầu tiên chưa có nhãn. Không gán lại phiếu đã có nhãn.
3. **Chạy song song nhiều tiến trình:**
   - mỗi tiến trình đọc đủ hướng dẫn này trước khi gán;
   - chia `phieu.jsonl` theo khoảng dòng, mỗi tiến trình ghi một tệp riêng;
   - xong thì nối các tệp lại, rồi kiểm tệp gộp **không** có `--mot-phan`.
4. **Lượt B, nếu được giao:** không mở tệp nhãn lượt A; dùng agent hoặc mô hình khác; ghi `luot` là `"B"` vào tệp `nhan-B.jsonl`.
5. Một số phiếu xuất hiện hai lần với `phieu_id` khác nhau. Gán mỗi phiếu độc lập, không tìm và chép nhãn giữa các phiếu.
6. Ghi một tệp ngắn `ghi-chu-A.md`: agent, mô hình, ngày giờ bắt đầu và kết thúc, ước lượng token hay chi phí nếu có, cách chia lô, các phiếu thấy
   đáng ngờ (ghi `phieu_id` và lý do).

## 9. Bàn giao

- [ ] `nhan-A.jsonl` (và `nhan-B.jsonl` nếu có) qua `kiem_nhan_d04.py` **không** có `--mot-phan`, in "HỢP LỆ".
- [ ] Mỗi phiếu có đúng một dòng trong mỗi lượt.
- [ ] Không dòng nào chép nhãn từ phiếu khác.
- [ ] `ghi-chu-A.md` đi kèm.
