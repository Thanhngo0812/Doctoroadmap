# Hướng dẫn chấm tên và mô tả module (SA-20)

Đọc [luật chung](00-chung.md) trước. Giao thức gốc: [báo cáo tên module](../../report/nghien-cuu-ten-va-mo-ta-module-2026-10-11.md), mục 7.4 và 7.6;
vé [SA-20](../../task/sau-a10/20-danh-gia-ten-module.md).

**Thời gian:** phần 1 khoảng 4,5 giờ (162 module), phần 2 khoảng 1 giờ (60 mô tả). Chấm thử: 8 module.

## 1. Việc này để làm gì

Lộ trình chia sách thành các module, mỗi module 3–8 khái niệm. Mỗi module cần một **tên** và một **mô tả ngắn**, vì đó là thứ người học thấy đầu tiên.
Có nhiều cách đặt tên, và ta muốn biết cách nào tốt nhất theo mắt người.

## 2. Bạn nhận được gì

Một tệp `cham-sa20-<mã>.xlsx`, không có tệp HTML. Ngoài ba sheet chung (Hướng dẫn, Chấm, Ghi chú chung), tệp có thêm:

| sheet | nội dung |
|---|---|
| **Chấm** | phần 1: tên module |
| **Chấm mô tả** | phần 2: mô tả module |
| **Khái niệm** | **bị khoá.** Mọi khái niệm của các module có trong phiếu: mã module, tên khái niệm, câu định nghĩa trong sách, trang |

## 3. Phần 1: xếp hạng tên

**Mỗi module là một nhóm 2–4 dòng liền nhau,** mỗi dòng một tên. Các tên được đặt nhãn A, B, C, D theo thứ tự ngẫu nhiên. Hai cách đặt tên ra **cùng
một chữ** thì chỉ hiện một dòng, nên có nhóm chỉ có 2 hay 3 dòng.

Cột xám ở dòng đầu mỗi nhóm:

| cột | nghĩa |
|---|---|
| `ma_phieu` | mã module trong phiếu |
| `cuon` | cuốn sách |
| `khai_niem` | các khái niệm của module, theo thứ tự trong sách |
| `module_truoc`, `module_sau` | **các khái niệm** của hai module kề, không phải tên của chúng. Hiện tên thì sẽ thiên về một cách đặt tên |
| `nhan`, `ten` | nhãn A–D và tên cần chấm, ở mọi dòng |

Cột vàng, ghi ở **mọi dòng** của nhóm:

| cột | giá trị | nghĩa |
|---|---|---|
| `hang` | 1–4 | 1 là tốt nhất. **Được để bằng hạng:** hai tên tốt như nhau thì cùng hạng. Hạng tính trong nhóm, không so với module khác |
| `dung_noi_dung` | `dat` / `khong` | tên nói đúng điều module dạy. `khong` nếu tên rộng hơn hẳn (kiểu "Phần II", "Chương 3", tên của cả chương), hay hẹp hơn hẳn (chỉ một khái niệm trong 6) |
| `phan_biet` | `dat` / `khong` | đọc tên thì biết module này khác hai module kề ở đâu. `khong` nếu tên cũng hợp y như vậy cho một module kề |
| `ngan_gon` | `dat` / `khong` | không thừa mã, số đánh mục, dấu `·` nối hai mẩu, mẩu câu cụt. Dài tới khoảng 8 từ vẫn có thể `dat` |
| `tu_nhien` | `dat` / `khong` | là một cụm tiếng Việt mà người dạy có thể viết làm tiêu đề. Thuật ngữ tiếng Anh được phép nếu sách dùng |

**Cách làm một nhóm:**
1. Đọc `khai_niem`. Nếu chưa rõ module dạy gì, tra sheet Khái niệm.
2. Liếc `module_truoc` và `module_sau` để biết module này nằm giữa cái gì.
3. Chấm bốn cột `dat`/`khong` cho từng tên.
4. Xếp hạng. Hạng phản ánh **cảm nhận chung** của bạn với tư cách người học: muốn thấy tên nào trên lộ trình. Hạng không bắt buộc phải theo số ô
   `dat`, nhưng một tên sai nội dung khó có thể đứng hạng 1.

**Ví dụ minh hoạ** (bịa để giải thích, không có trong phiếu). Module có các khái niệm: Đơn ánh, Toàn ánh, Song ánh, Ánh xạ ngược.

| nhãn | tên | nội dung | phân biệt | gọn | tự nhiên | hạng |
|---|---|---|---|---|---|---|
| A | Phân loại ánh xạ | dat | dat | dat | dat | 1 |
| B | Ánh xạ · Đơn ánh | khong (hẹp, chỉ một khái niệm) | khong | khong (dấu `·`) | khong | 3 |
| C | Đơn ánh, toàn ánh, song ánh và ánh xạ ngược | dat | dat | khong (liệt kê dài) | dat | 2 |
| D | Chương 1: Tập hợp và ánh xạ | khong (rộng) | khong | khong (số chương) | dat | 3 |

## 4. Phần 2: mô tả module

Sheet **Chấm mô tả** có 60 module, chọn theo tầng. Mỗi module có **một mô tả**, tách sẵn thành từng câu, mỗi câu một dòng.

| cột | giá trị | nghĩa |
|---|---|---|
| `duoc_do` | `tron` / `mot_phan` / `khong` | câu này được nội dung module chống đỡ: trọn vẹn, một phần, hay không. Căn cứ là các khái niệm của module và câu định nghĩa của chúng (sheet Khái niệm) |
| `sai_nang` | `co` / `khong` | câu nêu một khái niệm **không có** trong module, hay nói ngược với sách |
| `huu_ich` | `co_ich` / `binh_thuong` / `khong` | **chỉ ghi ở dòng đầu** của mỗi module: đọc xong mô tả thì có biết module dạy gì và cần gì trước không |

`mot_phan` dùng khi câu có hai ý mà chỉ một ý được chống đỡ, hay khi câu nói rộng hơn điều sách nói.

## 5. Ca khó

- **Tên dùng tiêu đề của tác giả.** Nếu tiêu đề mục trong sách khớp đúng nội dung module thì đó là tên tốt, dù nghe khô. Chấm như mọi tên khác.
- **Tên đúng nhưng chung chung,** ví dụ "Các khái niệm cơ bản": thường `dung_noi_dung = dat` nhưng `phan_biet = khong`.
- **Hai tên khác nhau một chữ:** vẫn xếp hạng. Được để bằng hạng nếu bạn thật sự không thấy khác.
- **Tên có lỗi chính tả:** `tu_nhien = khong`, ghi lỗi vào `ghi_chu`.
- **Module trộn hai chủ đề:** tên nêu được cả hai thì `dung_noi_dung = dat`, dù hơi dài.

## 6. Kết quả của bạn được dùng thế nào

Claude tính từ thứ hạng của bạn: trong mỗi cặp cách đặt tên, cách nào thắng ở bao nhiêu module. Luật quyết định đã viết trước, ở mục 7.6 của báo cáo.
Phần 2 quyết định có giữ mô tả do mô hình viết hay không: cần ít nhất 95% câu `tron` và không câu nào `sai_nang`.
