# Hướng dẫn chấm câu trả lời của trợ lý (SA-23)

Đọc [luật chung](00-chung.md) trước. Giao thức gốc: [báo cáo trợ lý](../../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md), mục 5.3–5.4;
vé [SA-23](../../task/sau-a10/23-danh-gia-tro-ly.md). Bộ câu hỏi: [19a](../../task/sau-a10/19a-dac-ta-bo-cau-hoi-thu.md).

**Thời gian:** phần 1 khoảng 3 giờ (60 câu hỏi), phần 2 khoảng 1,5 giờ. Chấm thử: 6 câu hỏi ngoài mẫu.

## 1. Việc này để làm gì

Người học hỏi trợ lý về cuốn sách. Trợ lý chỉ được trả lời theo sách, và phải dẫn nguồn. Ta so hai cách trả lời trên cùng câu hỏi:
- một cách **dùng đồ thị** tiên quyết của lộ trình;
- một cách **chỉ tìm đoạn sách** rồi trả lời.

Máy cũng chấm bằng bộ đo RAGAS. Điểm của bạn dùng để biết điểm máy có đáng tin không.

## 2. Bạn nhận được gì

- `phieu-sa23-<mã>.html`. Mỗi câu hỏi gồm:
  - cuốn, module người học đang mở, và các lượt hỏi trước nếu là hội thoại nhiều lượt;
  - câu hỏi;
  - hai câu trả lời A và B, thứ tự ngẫu nhiên. Nhãn nguồn `[S1]`… bấm vào thì hiện câu trích kèm trang;
  - khối **"Gợi ý đáp án"**, gập sẵn: các ý chính và đoạn sách tham chiếu. Phần này do agentic soạn và người duyệt mẫu, **có thể sai**. Căn cứ cuối cùng
    luôn là sách.
- `cham-sa23-<mã>.xlsx`: sheet **Chấm cặp** cho phần 1.
- Phần 2 là tệp riêng, nhận sau khi đã nộp phần 1.

## 3. Phần 1: chấm cặp

Mỗi câu hỏi có ba dòng: `A`, `B` và `chon`. Ở dòng `A` và `B`, chấm câu trả lời tương ứng:

| cột | giá trị | nghĩa |
|---|---|---|
| `dung_tai_lieu` | `khong_loi` / `co_loi` | câu trả lời có điều nào **sai so với sách** không: nói ngược sách, nhầm khái niệm, bịa công thức |
| `tra_loi_dung_cau` | 1–3 | 3: trả lời thẳng và đủ điều được hỏi; 2: đúng hướng nhưng thiếu, hoặc lan man; 1: trả lời điều khác |
| `trich_dan` | `dung` / `co_loi` / `khong_co` | câu trích mà câu trả lời dẫn có đúng là chỗ nói điều đó không. `khong_co` khi câu trả lời về sách mà không dẫn nguồn nào |
| `tu_choi` | `tu_choi_dung` / `tu_choi_nham` / `tra_loi_bia` / trống | **chỉ** khi câu trả lời nói sách không có thông tin, hoặc khi câu hỏi nằm ngoài sách (mục 4) |

Ở dòng `chon`, cột `chon` nhận `A`, `ngang` hay `B`: nếu bạn là người học, bạn muốn nhận câu trả lời nào. Câu trả lời có lỗi sai so với sách khó có thể
thắng.

## 4. Câu hỏi ngoài sách và câu từ chối

Có câu hỏi về điều sách không dạy, ví dụ hỏi cách cài một phần mềm trong một cuốn đại số. Trợ lý đúng khi nói sách không có thông tin đó.

| tình huống | `tu_choi` |
|---|---|
| câu hỏi ngoài sách, trợ lý nói sách không có | `tu_choi_dung` |
| câu hỏi **trong** sách, trợ lý lại nói sách không có | `tu_choi_nham` |
| câu hỏi ngoài sách, trợ lý vẫn trả lời như thể sách có | `tra_loi_bia` |
| câu hỏi trong sách, trợ lý trả lời bình thường | để trống |

Muốn biết câu hỏi có nằm trong sách không, tìm trong PDF, đừng chỉ dựa vào gợi ý đáp án. Trợ lý được phép đưa một **ví dụ ngoài sách** nếu ghi rõ đó là
ngoài sách. Phần đó không bị tính là bịa, nhưng phải đúng theo hiểu biết chung.

## 5. Phần 2: chấm từng câu và khối nhắc nền

Phần 2 lấy **một** câu trả lời cho mỗi câu hỏi, đã tách sẵn thành từng câu, mỗi câu một dòng. Tệp phần 2 hiện thêm hai thứ mà phần 1 cố ý ẩn:
- **khối nhắc khái niệm nền,** tức gợi ý ôn lại tiên quyết chưa học;
- **thẻ "nội dung ở module N".**

Phần 1 ẩn hai thứ này vì chỉ một trong hai cách trả lời có chúng; hiện ra là lộ cách trả lời.

| cột | giá trị | nghĩa |
|---|---|---|
| `duoc_do` | `tron` / `mot_phan` / `khong` / `khong_nguon` | câu trích mà câu này dẫn có chống đỡ nó không, như ở bài giảng (khung AIS). `khong_nguon`: câu nói về sách mà không dẫn nguồn. Câu chào hay câu nối không có nội dung thì để trống |
| `nhac_nen` | `co_ich` / `trung_tinh` / `phien` / trống | chỉ ghi ở dòng đầu của câu trả lời có khối nhắc nền: khối đó giúp người học, không ảnh hưởng, hay làm phiền |

## 6. Ca khó

- **Hội thoại nhiều lượt:** câu hỏi cuối thường có "cái đó", "còn … thì sao". Chấm theo ý nghĩa trong ngữ cảnh các lượt trước.
- **Hai câu trả lời đều đúng, một bản dài hơn:** dài hơn không tự động tốt hơn. Chọn bản giúp người học hơn; thật sự như nhau thì `ngang`.
- **Câu trả lời nói "theo sách, có thể…":** cách nói thận trọng về quan hệ tiên quyết là đúng thiết kế, không phải lỗi.
- **Trích dẫn đúng trang nhưng câu trích không chứa điều được nói:** `trich_dan = co_loi`.
- **Câu trả lời một phần đúng, một phần từ chối:** chấm `dung_tai_lieu` trên phần đã trả lời. Để `tu_choi` trống, rồi ghi rõ vào `ghi_chu`.

## 7. Kết quả của bạn được dùng thế nào

Luật quyết định viết trước, ở mục 5.4 của báo cáo:
- điểm RAGAS chỉ được báo như kết quả nếu khớp với điểm người của bạn (κ ≥ 0,6);
- khối nhắc nền được giữ nếu ≥ 70% đánh giá là `co_ich` hay `trung_tinh`, và ≤ 15% là `phien`.
