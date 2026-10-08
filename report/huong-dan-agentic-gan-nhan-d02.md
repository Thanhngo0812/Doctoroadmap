# Hướng dẫn gán nhãn D-02 cho agent: cây mục và trang mẫu của giáo trình

Bạn là agent gán nhãn. Đọc hết hướng dẫn này một lần trước khi bắt đầu, và mở lại khi phân vân.

Mỗi cuốn sách là một giáo trình tiếng Việt dạng PDF. Bạn làm hai việc:
1. **Cây mục (phần 1):** ghi mọi tiêu đề của cuốn sách, kèm cấp và tiêu đề cha.
2. **Trang mẫu (phần 2):** trên vài trang được chọn, gán vai trò cho **mọi dòng** và ghi thứ tự đọc đúng.

Nhãn của bạn là đáp án để chấm các bộ đọc PDF. Nhãn **chỉ dựa vào chính cuốn sách** (ảnh trang và các tệp được giao):
- không tra mạng;
- không dùng kết quả nhận cấu trúc của bất kỳ phần mềm nào khác.

## 1. Bạn nhận gì, trả gì

Mỗi cuốn có một mã `<sach>`.

| tệp nhận | nội dung |
|---|---|
| `dong/<sach>.jsonl` | mọi dòng chữ của sách, mỗi dòng một bản ghi: `{"id": "p0012-l003", "trang": 12, "text": "…", "bbox": [x0, y0, x1, y1], "co_chu": 11.5, "dam": false}` |
| `trang/<sach>/p0012.png` | ảnh của trang 12 |
| `chon-trang-mau/<sach>.json` | các trang cần làm phần 2, ví dụ `{"trang": [6, 31, 47, 88, 120, 151, 190, 230]}` |
| `muc_luc_dien_tu/<sach>.json` | mục lục điện tử của PDF, **chỉ có ở một số cuốn**. Đây là gợi ý, có thể thiếu hoặc sai |
| `kiem_nhan_d02.py` | script tự kiểm định dạng |

| tệp trả | nội dung |
|---|---|
| `cay-muc/<sach>.jsonl` | phần 1: mỗi tiêu đề một dòng |
| `trang-mau/<sach>.jsonl` | phần 2: mỗi trang mẫu một dòng |
| `ghi-chu/<sach>.md` | thời gian làm, các chỗ phân vân, nhận xét về cấu trúc sách |

**Mã dòng (`id`) là thứ quan trọng nhất.** Mọi nhãn trỏ vào mã dòng có sẵn. Không tự đặt mã, không sửa chữ của dòng.
- Chữ của dòng lấy từ lớp chữ của PDF nên có thể sai: âm tiết bị tách, mất dấu, ký hiệu hỏng.
- **Sách quét**: ảnh trang là ảnh chụp, chữ là chữ nhận dạng OCR. Ở loại sách này, `dam` luôn là `false` và `co_chu` chỉ gần đúng.
- Luôn nhìn **ảnh trang** để quyết định. Chữ trong `dong` chỉ dùng để tìm đúng mã dòng.

## 2. Phần 1 — cây mục

### 2.1 Phạm vi

- Sách từ 300 trang trở xuống: làm cả cuốn.
- Sách dài hơn: làm trang 1–300.

### 2.2 Dòng nào là tiêu đề

**Là tiêu đề:** dòng đặt tên cho một mục trong cấu trúc logic của sách.
- Phần, Chương, Tuần; Bài, khi đó là bài học có nội dung riêng.
- Mục đánh số `1.`, `1.1`, `1.1.1`, `I.`, `A.`, `a)`, khi nó mở một đoạn có nội dung riêng bên dưới.
- Tiêu đề không đánh số nhưng in nổi bật và mở một mục. Ví dụ: "Mục tiêu", "Tóm tắt chương", "Câu hỏi ôn tập", "Bài tập chương 3", "Lời nói
  đầu", "Mục lục", "Tài liệu tham khảo", "Phụ lục".
- Sách chia theo điều luật: "Điều 5. Quyền của hội viên" là tiêu đề, thấp nhất trong cây.

**Không là tiêu đề:**
- dòng đầu trang hay chân trang lặp lại; số trang;
- tên chương lặp lại ở lề trên các trang sau. Chỉ lần in làm tiêu đề thật mới tính;
- chú thích hình, bảng ("Hình 3.2 …", "Bảng 1.4 …"); chữ nằm trong hình;
- các dòng liệt kê trong trang mục lục. Riêng dòng "MỤC LỤC" là tiêu đề;
- nhãn khối trong văn: "Định nghĩa 2.1.", "Định lý 3.", "Ví dụ 4.", "Chú ý.", "Nhận xét.", "Hệ quả.", "Chứng minh.";
- "Bài 5.", "Câu 3." khi đó là bài tập hay câu hỏi;
- khoản "1.", "2." và điểm "a)", "b)" bên trong một điều luật;
- mục liệt kê "1.", "a)", "-", "•" khi đó chỉ là một ý trong đoạn, không mở đoạn nội dung riêng;
- dòng trên bìa và trang lót: tên sách, tác giả, nhà xuất bản.

**Ca biên:**
- **Tiêu đề nhiều dòng**, ví dụ "CHƯƠNG 3" một dòng và "DÒNG CHẢY SÔNG NGÒI" dòng sau: là **một** tiêu đề, `dong` ghi đủ cả hai mã dòng.
- **Tiêu đề liền đoạn**, in chung dòng với câu văn ("a) Lưu lượng trung bình. Là giá trị …"):
  - chỉ tính là tiêu đề khi phần tên được in phân biệt (đậm hoặc nghiêng) và mở một khối nội dung;
  - nếu tính: `dong` là mã dòng đó, `text` chỉ lấy phần tên, `ghi_chu` là `"liền đoạn"`.
- **Không chắc:** vẫn ghi, `ghi_chu` là `"nghi"`.

### 2.3 Cấp và cha

- `cap` là độ sâu trong cây logic của sách, **không** dựa theo cỡ chữ.
  - Sách có "Phần" thì Phần là cấp 1, Chương là cấp 2.
  - Không có "Phần" thì Chương, hay Tuần, là cấp 1.
- "Lời nói đầu", "Mục lục", "Tài liệu tham khảo", "Phụ lục" luôn là cấp 1.
- Mục không đánh số nằm ngay dưới chương ("Câu hỏi ôn tập chương 3") là con của chương đó, kể cả khi in to.
- `cha` là tiêu đề gần nhất **phía trước** có cấp nhỏ hơn đúng 1. Cấp 1 thì `cha` là `null`.
- Sách bỏ qua một bậc đánh số (ví dụ chương rồi vào thẳng "a)") thì vẫn tính cấp liên tiếp: `a)` là cấp 2.

### 2.4 Vùng, chỉ ghi cho tiêu đề cấp 1

| vùng | ví dụ |
|---|---|
| `mo_dau` | lời nói đầu, lời giới thiệu, mục lục, danh mục từ viết tắt |
| `noi_dung` | các phần, chương nội dung |
| `bai_tap` | phần bài tập hay đề thi đứng riêng ở cấp 1 |
| `de_cuong` | đề cương, mục tiêu học phần, kế hoạch giảng dạy |
| `hanh_chinh` | quyết định ban hành, thông tin tác giả, các trang hành chính có tiêu đề |
| `cuoi_sach` | tài liệu tham khảo, phụ lục, chỉ mục, đáp số |

### 2.5 Cách làm

1. Xem trang mục lục in sẵn và `muc_luc_dien_tu` (nếu có) để nắm cấu trúc sách. Nhưng chỉ ghi tiêu đề **thấy trong thân sách**.
2. Đi lần lượt từng trang, theo đợt khoảng 30 trang.
   - Với mỗi tiêu đề, tìm mã dòng của nó trong `dong/<sach>.jsonl`, cùng trang.
   - Giữ trong đầu danh sách các tiêu đề đang mở theo từng cấp, để ghi đúng `cha`.
3. Mục lục in sẵn và thân sách lệch nhau (thiếu mục, khác tên): ghi theo thân sách và nêu vào `ghi-chu`.

### 2.6 Định dạng trả về

Mỗi tiêu đề một dòng JSON, theo thứ tự đọc:

```json
{"sach": "<sach>", "id": "h010", "dong": ["p0031-l002", "p0031-l003"], "text": "CHƯƠNG 3. DÒNG CHẢY SÔNG NGÒI", "cap": 1, "cha": null, "vung": "noi_dung", "ghi_chu": ""}
```

| trường | luật |
|---|---|
| `id` | `h` cộng số, không trùng, tăng dần theo thứ tự đọc |
| `dong` | ít nhất một mã dòng có thật. Một mã dòng không thuộc hai tiêu đề |
| `text` | chữ của tiêu đề, không rỗng |
| `cap` | số nguyên từ 1 đến 6 |
| `cha` | `null` khi `cap` là 1; nếu không, là `id` của tiêu đề gần nhất phía trước có `cap` nhỏ hơn đúng 1 |
| `vung` | bắt buộc với cấp 1, chọn một giá trị ở mục 2.4; `null` với cấp khác |
| `ghi_chu` | `""`, `"nghi"`, `"liền đoạn"` hoặc lời ngắn |

### 2.7 Ví dụ (tự soạn, không lấy từ sách được giao)

Các dòng của một cuốn "Thuỷ văn đại cương" (trích):

| mã dòng | chữ | quyết định |
|---|---|---|
| p0003-l001 | LỜI NÓI ĐẦU | tiêu đề h001, cấp 1, vùng `mo_dau` |
| p0005-l001 | MỤC LỤC | tiêu đề h002, cấp 1, vùng `mo_dau` |
| p0005-l002 | Chương 1. Mở đầu ........ 7 | không: dòng trong mục lục |
| p0031-l001 | Thuỷ văn đại cương | không: đầu trang lặp lại |
| p0031-l002 | CHƯƠNG 3 | tiêu đề h010, gộp với dòng dưới |
| p0031-l003 | DÒNG CHẢY SÔNG NGÒI | thuộc h010: cấp 1, vùng `noi_dung` |
| p0031-l004 | 3.1. Khái niệm về dòng chảy | tiêu đề h011, cấp 2, cha h010 |
| p0031-l005 | 3.1.1. Lưu lượng nước | tiêu đề h012, cấp 3, cha h011 |
| p0032-l004 | Định nghĩa 3.1. Lưu lượng nước là thể tích nước … | không: nhãn khối |
| p0032-l009 | Ví dụ 3.2. Một con sông có diện tích mặt cắt … | không: nhãn khối |
| p0033-l002 | 3.1.2. Mực nước | tiêu đề h013, cấp 3, cha h011 |
| p0036-l002 | 3.2. Các nhân tố ảnh hưởng tới dòng chảy | tiêu đề h014, cấp 2, cha h010 |
| p0041-l005 | Câu hỏi ôn tập chương 3 | tiêu đề h015, cấp 2, cha h010 |
| p0041-l006 | 1. Nêu khái niệm lưu lượng nước. | không: câu hỏi |
| p0102-l001 | TÀI LIỆU THAM KHẢO | tiêu đề h040, cấp 1, vùng `cuoi_sach` |

## 3. Phần 2 — trang mẫu

### 3.1 Vai trò của dòng

Trên mỗi trang trong `chon-trang-mau/<sach>.json`, gán **mọi** mã dòng của trang đúng một vai trò:

| vai trò | nghĩa |
|---|---|
| `tieu_de` | dòng thuộc một tiêu đề đã ghi ở phần 1. Phải khớp đúng phần 1 |
| `than_bai` | dòng văn xuôi của đoạn văn. Gồm cả công thức nhỏ chen trong dòng, và nhãn khối như "Định nghĩa 2.1." |
| `danh_sach` | dòng của một ý liệt kê ("-", "•", "a)", "1)"), kể cả các dòng nối tiếp của ý đó |
| `cong_thuc` | dòng chỉ có công thức đứng riêng, kể cả số hiệu "(3.4)" |
| `bang` | chữ trong ô của bảng, kể cả hàng tiêu đề của bảng |
| `ma_lenh` | mã nguồn, mã giả, câu lệnh |
| `chu_thich_hinh` | chú thích hình hoặc bảng ("Hình 3.2 …", "Bảng 1.4 …"), kể cả các dòng nối tiếp |
| `chu_trong_hinh` | chữ nằm trong hình, sơ đồ, biểu đồ: nhãn, trục, chú giải |
| `dau_trang` | dòng đầu trang lặp lại, kể cả khi dính số trang ("48 Chương 3. Không gian véctơ") |
| `chan_trang` | dòng chân trang lặp lại (tên trường, bản quyền), kể cả khi dính số trang |
| `so_trang` | dòng chỉ có số trang, kể cả "Trang 12" |
| `chu_thich_cuoi_trang` | chú thích cuối trang |
| `muc_luc` | dòng liệt kê trong trang mục lục |
| `khac` | còn lại: chữ trên bìa, chữ trang trí, hình mờ |

Thêm hai cờ cho cả trang:
- `co_bang`: trang có bảng hay không, nhìn theo ảnh trang;
- `co_hinh`: trang có hình hay không, kể cả hình không chứa dòng chữ nào.

### 3.2 Thứ tự đọc

`thu_tu` liệt kê mọi dòng **trừ** `dau_trang`, `chan_trang`, `so_trang`, `chu_trong_hinh`, theo thứ tự một người đọc trang này:
- từ trên xuống; trang hai cột thì đọc hết cột trái rồi mới sang cột phải;
- bảng đọc theo hàng, mỗi hàng từ trái sang phải;
- chú thích hình hay bảng đặt đúng chỗ in: ngay sau hình nếu in dưới hình, ngay trước bảng nếu in trên bảng;
- công thức đặt đúng chỗ trong mạch văn;
- chú thích cuối trang để cuối cùng.

### 3.3 Định dạng trả về

Mỗi trang mẫu một dòng JSON:

```json
{"sach": "<sach>", "trang": 36, "dong": {"p0036-l001": "dau_trang", "p0036-l002": "tieu_de", "p0036-l003": "than_bai"}, "thu_tu": ["p0036-l002", "p0036-l003"], "co_bang": false, "co_hinh": true, "ghi_chu": ""}
```

| trường | luật |
|---|---|
| `trang` | một trang có trong `chon-trang-mau`; mỗi trang đúng một dòng |
| `dong` | khoá là **đúng toàn bộ** mã dòng của trang, giá trị là một vai trò ở mục 3.1 |
| `thu_tu` | hoán vị đúng tập dòng có vai trò không thuộc `dau_trang`, `chan_trang`, `so_trang`, `chu_trong_hinh` |
| `co_bang`, `co_hinh` | `true` hoặc `false` |
| khớp phần 1 | tập dòng `tieu_de` trên trang phải bằng tập mã dòng của các tiêu đề phần 1 nằm trên trang đó |

### 3.4 Ví dụ (tự soạn)

Trang 36 của cuốn "Thuỷ văn đại cương":

| mã dòng | chữ | vai trò |
|---|---|---|
| p0036-l001 | Thuỷ văn đại cương | `dau_trang` |
| p0036-l002 | 3.2. Các nhân tố ảnh hưởng tới dòng chảy | `tieu_de` |
| p0036-l003 | Dòng chảy sông ngòi chịu ảnh hưởng của khí hậu, địa hình và | `than_bai` |
| p0036-l004 | thảm phủ thực vật trên lưu vực¹. Lưu lượng được tính theo | `than_bai` |
| p0036-l005 | Q = F · v | `cong_thuc` |
| p0036-l006 | (3.4) | `cong_thuc` |
| p0036-l007 | mưa | `chu_trong_hinh` |
| p0036-l008 | bốc hơi | `chu_trong_hinh` |
| p0036-l009 | Hình 3.2. Cân bằng nước trên lưu vực | `chu_thich_hinh` |
| p0036-l010 | ¹ Lưu vực là phần diện tích mặt đất cấp nước cho sông. | `chu_thich_cuoi_trang` |
| p0036-l011 | 36 | `so_trang` |

`thu_tu`: l002, l003, l004, l005, l006, l009, l010 (viết đủ mã dòng). `co_bang`: `false`. `co_hinh`: `true`.

## 4. Cách làm và tự kiểm

1. Làm từng cuốn: phần 1 trước, phần 2 sau.
2. Xong mỗi đợt khoảng 30 trang của phần 1, và sau phần 2, chạy:

   ```
   python kiem_nhan_d02.py --sach <sach> --thu-muc .
   ```

   Sửa hết lỗi trước khi làm tiếp.
3. **Làm tiếp sau khi dừng:** đọc dòng cuối của `cay-muc/<sach>.jsonl` để biết đã tới trang nào, rồi làm tiếp. Không ghi lại tiêu đề đã có.
4. **Lượt thứ hai độc lập, nếu được giao:** ghi vào thư mục riêng `luot-B/`, không mở kết quả lượt đầu.
5. `ghi-chu/<sach>.md` ghi:
   - agent và mô hình;
   - thời gian bắt đầu, kết thúc;
   - các tiêu đề `"nghi"` và lý do;
   - chỗ mục lục in sẵn lệch thân sách;
   - trang khó (hai cột, bảng lớn, chữ OCR hỏng).

## 5. Bàn giao

- [ ] `kiem_nhan_d02.py` in "ĐẠT" cho từng cuốn.
- [ ] Phần 1 phủ đúng phạm vi trang ở mục 2.1.
- [ ] Mỗi trang trong `chon-trang-mau` có đúng một dòng ở phần 2, đủ mọi mã dòng.
- [ ] Không dùng nguồn ngoài sách và các tệp được giao.
- [ ] Có `ghi-chu/<sach>.md`.
