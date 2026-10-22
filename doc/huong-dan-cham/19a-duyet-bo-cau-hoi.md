# Hướng dẫn duyệt bộ câu hỏi thử của trợ lý (19a)

Đọc [luật chung](00-chung.md) trước. Đặc tả gốc của bộ câu: [`task/sau-a10/19a-dac-ta-bo-cau-hoi-thu.md`](../../task/sau-a10/19a-dac-ta-bo-cau-hoi-thu.md),
mục 9.

**Thời gian:** khoảng 40 phút mỗi người. Hai người duyệt **cùng** 40 câu, **độc lập**.

## 1. Việc này để làm gì

Để đánh giá trợ lý (SA-23), ta cần một bộ câu hỏi giống câu người học thật sự hỏi, kèm đáp án tham chiếu. Bộ 200 câu do một dịch vụ agentic soạn từ
sáu cuốn phát triển. Bạn duyệt một mẫu 40 câu (20%) để biết bộ câu có dùng được không.

Nếu một tiêu chí sai quá ngưỡng, cả bộ bị trả về để sửa đúng tiêu chí đó. Ngưỡng đã chốt trước khi duyệt, xem mục 5.

## 2. Bạn nhận được gì

- `duyet-19a-<mã>.xlsx`: 40 dòng, mỗi dòng một câu. Cột xám:

  | cột | nghĩa |
  |---|---|
  | `cau_id` | mã câu |
  | `doc_id` | cuốn sách |
  | `loai` | loại câu: `dinh_nghia`, `tien_quyet`, `so_sanh`, `vi_du`, `lo_trinh`, `ngoai_tai_lieu` (kèm `kieu_ngoai`: gần chủ đề hay lạc đề), `nhieu_luot` |
  | `module_dang_mo` | module người học đang mở khi hỏi (số thứ tự và tên) |
  | `luot_truoc` | chỉ có ở câu nhiều lượt: 1–2 câu hỏi trước đó trong cùng hội thoại |
  | `cau_hoi` | câu cần duyệt |
  | `khai_niem_ky_vong` | 1–3 khái niệm mà câu hỏi nhắm tới, theo người soạn; hiện bằng tên |
  | `doan_tham_chieu` | 1–3 đoạn sách chứa câu trả lời, hiện nguyên văn kèm trang |
  | `y_chinh` | 1–3 ý chính mà một câu trả lời tốt phải có |
  | `da_tim` | chỉ có ở câu ngoài tài liệu: các từ khoá người soạn đã tìm trong sách |

- PDF của sáu cuốn.

## 3. Sáu ô cần chấm, mỗi ô `dung` / `sai`

| ô | `dung` khi | ví dụ `sai` |
|---|---|---|
| `tu_nhien` | giống câu một người học thật sự gõ: ngắn, có thể thiếu dấu, có thể dùng lời khác tên trong sách | chép nguyên câu định nghĩa trong sách rồi thêm "là gì?" |
| `dung_loai` | câu thuộc đúng loại ghi ở cột `loai` | ghi "so sánh" mà câu chỉ hỏi định nghĩa một khái niệm |
| `tra_loi_duoc` | câu thường: sách trả lời được. Câu ngoài tài liệu: sách **thật sự không** có câu trả lời. Bạn **tìm trong PDF** để kiểm | câu "ngoài tài liệu" nhưng sách có dạy |
| `khai_niem_dung` | `khai_niem_ky_vong` đúng là khái niệm câu hỏi nhắm tới. Câu ngoài tài liệu thì ô này để trống | câu hỏi về "toàn ánh" mà ghi khái niệm là "ánh xạ" |
| `doan_dung` | `doan_tham_chieu` thật sự chứa câu trả lời. Câu ngoài tài liệu thì ô này để trống | đoạn chỉ nhắc tên khái niệm, không có câu trả lời |
| `y_chinh_dung` | mọi ý trong `y_chinh` đều có trong sách, không thiếu ý cốt lõi. Câu ngoài tài liệu thì ô này để trống | một ý chính không có trong sách |

Ô `tra_loi_duoc` quan trọng nhất, vì nó quyết định cách chấm câu từ chối của trợ lý. Hãy kiểm kỹ ô này: tìm trong PDF theo vài từ khoá, không chỉ theo
tên khái niệm.

## 4. Ca khó

- **Câu nhiều lượt:** chấm câu cuối trong ngữ cảnh của `luot_truoc`. Câu "Vậy cái đó tính thế nào?" là tự nhiên nếu `luot_truoc` nói rõ "cái đó" là gì.
- **Câu ngoài tài liệu, gần chủ đề:** sách dạy chủ đề gần nhưng không dạy đúng điều được hỏi. Ví dụ sách dạy trị riêng nhưng không dạy chéo hoá. Nếu
  sách có **một câu** trả lời được, dù ngắn, thì `tra_loi_duoc = sai`. Tìm cả bằng từ khoá của bạn, không chỉ bằng `da_tim`.
- **Câu lộ trình** ("muốn học X cần học gì trước"): `y_chinh` là danh sách khái niệm. Chỉ cần mỗi khái niệm trong danh sách thật sự được sách dùng
  hay dạy trước X. Không cần danh sách đầy đủ tuyệt đối.

## 5. Luật nhận bộ câu (đã chốt trước khi duyệt)

- Một ô có tỉ lệ `sai` trên 15% ở **cả hai** người: cả bộ bị trả về agentic để sửa riêng ô đó.
- Ô `tra_loi_duoc` có tỉ lệ `sai` trên 10%: cả bộ bị trả về.
- Dưới ngưỡng: Claude sửa các câu sai đã thấy, rồi nhận bộ.

Bạn không cần tính các tỉ lệ này; Claude tính.

## 6. Không được làm

Ngoài [luật chung](00-chung.md), mục 6:
- Không sửa câu hỏi hay đáp án trong tệp. Thấy cách sửa thì ghi vào `ghi_chu`.
- Không chia sẻ bộ câu ra ngoài nhóm. Bộ này dùng để chấm trợ lý một lần; lộ ra thì không dùng được nữa.
