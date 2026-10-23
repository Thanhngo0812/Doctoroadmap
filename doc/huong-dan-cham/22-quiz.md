# Hướng dẫn chấm câu hỏi trắc nghiệm (SA-22)

Đọc [luật chung](00-chung.md) trước. Giao thức gốc: [báo cáo quiz](../../report/nghien-cuu-quiz-tu-kiem-tra-2026-10-11.md), mục 2.1, 5.3, 5.6;
vé [SA-22](../../task/sau-a10/22-danh-gia-quiz.md).

**Thời gian:** khoảng 8 giờ cho khoảng 320 câu, tức khoảng 1,5 phút mỗi câu. Chấm thử: 20 câu ngoài mẫu.

## 1. Việc này để làm gì

Hệ thống sinh câu trắc nghiệm để người học tự kiểm tra sau mỗi module. Có hai kiểu câu:
- câu do mô hình viết;
- câu điền khuyết, dựng từ một câu trong sách.

Trước khi đưa câu cho người học, mô hình kiểm câu một lần nữa. Ta muốn biết:
- câu có đạt chuẩn viết câu trắc nghiệm không;
- có bao nhiêu câu có hơn một đáp án đúng;
- lần kiểm của mô hình bắt được bao nhiêu lỗi.

Trong phiếu có trộn cả những câu mà lần kiểm đã loại. Bạn không biết câu nào, và cũng đừng đoán.

## 2. Bạn nhận được gì

- `phieu-sa22-<mã>.html`. Mỗi câu gồm:
  - mã câu, cuốn, module;
  - câu dẫn và các phương án A, B, C;
  - khối **"Đáp án và nguồn"**, **gập sẵn**: khái niệm mà câu kiểm, phương án hệ thống đánh dấu đúng, câu trích sách làm căn cứ kèm trang, ảnh
    công thức nếu có.

  Tên khái niệm chỉ nằm trong khối gập. Với câu điền khuyết, tên khái niệm chính là đáp án; hiện ra trước thì bước tự làm câu mất ý nghĩa.
- `cham-sa22-<mã>.xlsx`, sheet **Chấm**, mỗi dòng một câu.

## 3. Cách chấm một câu

**Bước 1 — tự làm câu.** Đọc câu dẫn và phương án. Ghi phương án bạn chọn vào cột `dap_an_cua_ban`, **trước khi** mở khối "Đáp án và nguồn". Không chắc
thì vẫn chọn, rồi ghi `khong_chac` vào `ghi_chu`. Bạn chọn sai là tín hiệu câu mơ hồ hay đáp án sai, nên đừng mở khối trước.

**Bước 2 — mở khối "Đáp án và nguồn",** đọc câu trích, mở PDF nếu cần.

**Bước 3 — chấm các cột vàng:**

| cột | giá trị | `co` khi |
|---|---|---|
| `dap_an_dung` | `co` / `khong` | phương án hệ thống đánh dấu đúng thật sự đúng theo câu trích |
| `mot_dap_an` | `co` / `khong` | **chỉ một** phương án đúng theo tài liệu. Một phương án nhiễu cũng đúng, hay đúng một phần mà vẫn chấp nhận được, thì `khong` |
| `nhieu_sai` | `co` / `khong` | mọi phương án nhiễu đều sai theo tài liệu |
| `dung_khai_niem` | `co` / `khong` | câu kiểm đúng khái niệm ghi trong khối "Đáp án và nguồn", không phải một khái niệm khác |
| `bloom_nguoi` | `nho` / `hieu` / `van_dung` / `phan_tich_tro_len` | mức nhận thức câu đòi hỏi, theo bạn (mục 4) |
| `loi_viet_cau` | mã lỗi, cách nhau bằng dấu phẩy, hoặc trống | các lỗi viết câu trong bảng ở mục 5. Ví dụ `L04,L12`. Không có lỗi thì để trống |
| `tieng_viet` | 1–3 | 3: tự nhiên; 2: hiểu được nhưng vụng; 1: sai ngữ pháp, khó hiểu |
| `ket_luan` | `dung_ngay` / `sua_nhe` / `bo` | bạn có đưa câu này cho người học không |

`ket_luan`:
- `sua_nhe`: sửa một hai chữ là dùng được;
- `bo`: phải viết lại, hoặc câu sai.

## 4. Mức Bloom

| mức | câu đòi hỏi | ví dụ |
|---|---|---|
| `nho` | nhận ra hay nhắc lại điều sách viết | "Khái niệm nào được định nghĩa là …?" |
| `hieu` | diễn đạt lại, phân biệt, giải thích bằng lời khác sách | "Điểm khác nhau giữa đơn ánh và toàn ánh là gì?" |
| `van_dung` | áp dụng vào một trường hợp cụ thể chưa có nguyên văn trong sách | "Ánh xạ f(x) = 2x trên ℝ thuộc loại nào?" |
| `phan_tich_tro_len` | phân tích, đánh giá, so nhiều ý | hiếm gặp |

Câu điền khuyết hầu như luôn là `nho`.

## 5. Bảng lỗi viết câu

Rút từ bảng 19 lỗi của Moore và cộng sự (2023), theo hướng dẫn của Haladyna, Downing và Rodriguez. "Nhiều hơn một đáp án đúng" đã có cột
`mot_dap_an` riêng, nên không có trong bảng mã.

| mã | lỗi | có lỗi khi |
|---|---|---|
| L01 | mơ hồ | câu dẫn hay phương án hiểu được theo hai cách |
| L02 | câu nhiễu khó tin | người chưa học bài cũng loại được ngay một phương án nhiễu |
| L03 | "không có đáp án nào đúng" | có phương án này |
| L04 | phương án dài nhất là đáp án | đáp án dài hơn hẳn các phương án nhiễu |
| L05 | thông tin thừa | câu dẫn có thông tin không cần để trả lời |
| L06 | thực chất là câu đúng/sai | các phương án chỉ là đúng/sai, có/không |
| L07 | gợi ý hội tụ | đáp án chung nhiều từ nhất với các phương án khác, nên đoán được bằng cách tìm phương án "ở giữa" |
| L08 | gợi ý logic | câu dẫn và đáp án có liên hệ hình thức để đoán, ví dụ câu dẫn hỏi "hai điều kiện", chỉ đáp án có hai ý |
| L09 | "tất cả các đáp án trên" | có phương án này |
| L10 | chỗ trống giữa câu | câu dẫn có chỗ trống `___` nằm giữa câu |
| L11 | từ tuyệt đối | phương án có "luôn luôn", "không bao giờ", "mọi", "chỉ" |
| L12 | lặp từ câu dẫn ở đáp án | một từ đặc trưng của câu dẫn chỉ lặp lại ở đáp án, không ở phương án nhiễu |
| L13 | câu dẫn không tập trung | đọc câu dẫn mà chưa xem phương án thì không biết câu hỏi hỏi gì |
| L14 | dạng tổ hợp | phương án kiểu "1 và 3 đúng" |
| L15 | gợi ý ngữ pháp | phương án nhiễu không khớp ngữ pháp với câu dẫn, đáp án thì khớp |
| L16 | sai thứ tự | phương án là số hay mốc nhưng không xếp theo thứ tự |
| L17 | từ mơ hồ | "thường", "đôi khi", "có thể", "đa số" làm câu không rõ đúng sai |
| L18 | câu dẫn phủ định | câu dẫn hỏi "không", "ngoại trừ" mà không nhấn mạnh rõ |

Một câu có 0–1 lỗi viết câu và không có lỗi nặng là **chấp nhận được**. **Lỗi nặng** là:
- `dap_an_dung = khong`;
- `mot_dap_an = khong`;
- `nhieu_sai = khong`.

Bạn không cần tự tính; Claude tính từ các cột.

## 6. Ca khó

- **Câu điền khuyết:** câu dẫn là một câu sách có chỗ trống. Theo định nghĩa thì có lỗi L10. Chấm L10 thật, đừng bỏ qua vì "kiểu câu này vốn vậy".
- **Phương án gần đúng:** một phương án nhiễu là khái niệm cha hay con của đáp án, ví dụ "Ánh xạ" khi đáp án là "Song ánh". Nếu câu trích cho phép cả hai
  thì `mot_dap_an = khong`.
- **Câu đúng theo hiểu biết chung nhưng sách nói khác:** theo sách.
- **Công thức trong câu:** so với ảnh công thức gốc. Ký hiệu chép sai thì `dap_an_dung` hay `nhieu_sai` có thể là `khong`.
- **Bạn làm sai câu ở bước 1:** không có nghĩa câu sai. Xem lại sau khi mở đáp án. Nếu câu mơ hồ thì ghi L01.

## 7. Kết quả của bạn được dùng thế nào

Luật quyết định viết trước, ở mục 5.6 của báo cáo. Chính:
- bản mô hình làm mặc định nếu ≥ 80% câu chấp nhận được và ≤ 3% lỗi nặng;
- lần kiểm của mô hình được giữ nếu nó bắt ≥ 50% số lỗi nặng mà người tìm thấy, với độ chính xác ≥ 0,5.
