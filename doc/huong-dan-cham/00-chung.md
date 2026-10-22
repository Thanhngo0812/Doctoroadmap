# Hướng dẫn chấm Pha B: luật chung

Dành cho người chấm của đợt đánh giá Pha B. Đọc tài liệu này trước, rồi đọc hướng dẫn riêng của đợt bạn chấm:

| đợt | việc | hướng dẫn riêng | thời gian mỗi người (ước) |
|---|---|---|---|
| 19a | duyệt 40 câu hỏi thử của trợ lý | [19a-duyet-bo-cau-hoi.md](19a-duyet-bo-cau-hoi.md) | khoảng 40 phút |
| SA-20 | xếp hạng tên module, chấm mô tả | [20-ten-module.md](20-ten-module.md) | khoảng 5,5 giờ |
| SA-21 | chấm bài giảng | [21-bai-giang.md](21-bai-giang.md) | khoảng 10 giờ |
| SA-22 | chấm câu hỏi trắc nghiệm | [22-quiz.md](22-quiz.md) | khoảng 8 giờ |
| SA-23 | chấm câu trả lời của trợ lý | [23-tro-ly.md](23-tro-ly.md) | khoảng 4,5 giờ |

Tổng khoảng 29 giờ mỗi người, chia thành nhiều buổi. Giờ ước ghi ở đây sẽ được sửa sau đợt chấm thử.

Thứ tự đề nghị: **19a trước**, vì đánh giá trợ lý chờ bộ câu này. Sau đó tới SA-20, SA-22, SA-21, SA-23.

---

## 1. Việc này để làm gì

Hệ thống đọc một giáo trình rồi dựng ra một lộ trình học. Mỗi module có tên, mỗi khái niệm có bài giảng, có câu hỏi trắc nghiệm, và có trợ lý để hỏi
đáp. Phần lớn nội dung này do mô hình ngôn ngữ viết. Muốn biết nó tốt tới đâu và tốt hơn các cách đơn giản không, ta cần **người** đọc và chấm.

Kết quả chấm của bạn là **kết luận cuối** của các đánh giá. Máy cũng tự đo, nhưng số máy đo chỉ dùng để tham khảo. Trong báo cáo đồ án, kết quả được
ghi là "chấm của nhóm", không phải "chấm của chuyên gia".

## 2. Bốn nguyên tắc

1. **Chấm độc lập.** Không bàn với người chấm kia cho tới khi cả hai đã nộp. Sau khi nộp mới có buổi hội ý (mục 7). Bàn trước thì hai bộ nhãn
   giống nhau một cách giả tạo, và độ đồng thuận đo ra mất nghĩa.
2. **Chấm mù.** Bạn không được biết bản nào do cấu hình nào sinh ra. Các bản được đặt tên A, B, C, D theo thứ tự ngẫu nhiên, mỗi phiếu một kiểu.
   Đừng cố đoán. Nếu tình cờ đoán ra, ví dụ một bản chỉ gồm câu chép nguyên văn sách, thì vẫn chấm theo tiêu chí như mọi bản khác.
3. **Chấm theo tài liệu.** "Đúng" nghĩa là đúng **theo cuốn sách**, không phải theo hiểu biết riêng của bạn hay theo Internet. Khi phân vân, mở PDF
   ở trang được ghi. Ngoại lệ duy nhất: phần được đánh dấu là "ví dụ ngoài sách" thì chấm bằng hiểu biết chung (hướng dẫn riêng sẽ ghi rõ).
4. **Không dùng công cụ AI để chấm.** Không hỏi ChatGPT, Claude, Gemini hay công cụ tương tự để đọc hộ, tóm tắt hộ hay chấm hộ. Đánh giá này đo
   chính mô hình ngôn ngữ, nên nhãn phải là nhãn của người.

## 3. Bạn nhận được gì

Mỗi đợt, chủ dự án gửi bạn một thư mục:

| thứ | dùng để làm gì |
|---|---|
| `phieu-<đợt>-<mã>.html` | **Đọc** các mục cần chấm. Mở bằng trình duyệt, chạy được khi không có mạng. Ảnh công thức đã nhúng sẵn |
| `cham-<đợt>-<mã>.xlsx` | **Ghi** nhãn. Mỗi dòng một mục, khớp với mã mục trong tệp HTML |
| PDF của sáu cuốn phát triển | Tra khi cần |
| Hướng dẫn này và hướng dẫn riêng của đợt | Luật chấm |

- `<mã>` là mã người chấm của bạn, `C1` hoặc `C2`.
- Đợt tên module (SA-20) không có tệp HTML: mọi thứ cần đọc đều nằm trong Excel.
- Mỗi người chấm có tệp riêng. Hai tệp có cùng các mục, nhưng thứ tự mục và thứ tự A/B/C/D có thể khác nhau.

**Tệp Excel có ba sheet:**

| sheet | nội dung | bạn làm gì |
|---|---|---|
| **Hướng dẫn** | đợt, mã người chấm, tóm tắt luật, các ô ghi thời gian | ghi giờ bắt đầu và giờ kết thúc mỗi buổi |
| **Chấm** | mỗi dòng một mục. Cột xám là thông tin, cột vàng là chỗ bạn ghi | **chỉ ghi vào cột vàng** |
| **Ghi chú chung** | bảng trống | ghi điều muốn báo mà không gắn với một mục nào, ví dụ một tiêu chí khó hiểu |

Cột vàng có danh sách chọn sẵn. Chọn trong danh sách, đừng gõ chữ khác. Cột `ghi_chu` gõ tự do.

## 4. Quy trình mỗi đợt

1. **Đọc hướng dẫn riêng của đợt,** một lần từ đầu tới cuối.
2. **Chấm thử.** Mỗi đợt, trừ 19a, có vài mục chấm thử, đặt riêng trong tệp `thu-<đợt>-<mã>.xlsx`. Hai người chấm thử độc lập rồi nộp. Claude so hai bản, và nếu
   một tiêu chí bị hiểu theo hai cách thì sửa hướng dẫn. Mục chấm thử không tính vào kết quả.
3. **Chấm thật,** theo thứ tự dòng trong tệp. Đừng sắp lại dòng, đừng lọc rồi chấm theo nhóm, vì thứ tự đã được trộn để tránh thiên lệch.
4. **Chia buổi.** Mỗi buổi tối đa 60–90 phút rồi nghỉ, vì chấm lâu sẽ mệt và dễ dãi dần. Ghi giờ vào sheet Hướng dẫn.
5. **Kiểm trước khi nộp:** mọi cột vàng đã có giá trị. Các cột chỉ áp cho một số mục, ví dụ "ví dụ ngoài sách" khi bài có phần đó, thì để trống
   ở mục không áp dụng. Hướng dẫn riêng ghi cột nào được để trống.
6. **Nộp** tệp Excel cho chủ dự án. Không gửi cho người chấm kia.

## 5. Khi phân vân

- Chọn nhãn bạn thấy **đúng nhất**, rồi ghi lý do ngắn vào `ghi_chu`. Đừng để trống chỉ vì không chắc.
- "Ngang" (hay "hoà") chỉ dùng khi hai bản thật sự tốt như nhau, hay tệ như nhau. Đừng dùng "ngang" để né một quyết định khó.
- Thấy một mục lỗi, ví dụ thiếu chữ, ảnh không hiện, hay hai bản giống hệt nhau, thì ghi `ghi_chu` bắt đầu bằng `LOI:`, rồi chấm phần chấm được.
- Một luật trong hướng dẫn trái với cảm nhận của bạn thì **vẫn theo luật**, và ghi điều đó vào sheet Ghi chú chung. Ta sửa luật sau đợt, không
  sửa giữa chừng.

## 6. Không được làm

- Bàn với người chấm kia trước khi cả hai nộp.
- Dùng công cụ AI để đọc, tóm tắt hay chấm.
- Tìm cách biết bản nào là cấu hình nào: mở repo, mở thư mục `artifacts`, hay hỏi người chạy.
- Sửa cột xám, xoá dòng, đổi thứ tự dòng, đổi tên tệp.
- Gửi phiếu hay nội dung sách ra ngoài nhóm.

## 7. Sau khi nộp: hội ý

1. Claude tính độ đồng thuận giữa hai người **trước** khi có hội ý:
   - κ của Cohen, kèm phần trăm đồng ý;
   - Gwet AC1 cho các nhãn hiếm, như lỗi viết câu, vì κ bị kéo thấp khi nhãn dương hiếm.
2. Claude gửi danh sách các mục hai người chấm khác nhau.
3. Hai người gặp nhau, xem từng mục, và chốt một **nhãn sau hội ý**. Nhãn gốc của từng người giữ nguyên trong tệp đã nộp, vì độ đồng thuận tính trên
   nhãn gốc.
4. Không chốt được thì ghi cả hai ý kiến. Khi ra quyết định, chủ dự án đọc những mục này.

## 8. Câu hỏi thường gặp

**Tôi có cần là chuyên gia môn học không?** Không. Bạn chấm theo sách, có PDF để tra. Chỗ nào cần hiểu sâu thì hướng dẫn riêng ghi cách làm.

**Tôi nhận ra một bản rõ ràng là "máy chép sách". Có sao không?** Không sao. Vẫn chấm như mọi bản khác. Ta đã biết trước điều này là không giấu được.

**Chấm sai một mục thì sao?** Trong lúc chấm, bạn được sửa nhãn của chính mình. Sau khi nộp thì không sửa nữa; chỗ khác nhau sẽ được bàn ở buổi hội ý.

**Tôi thấy hệ thống sai một cách thú vị. Ghi ở đâu?** Ghi vào `ghi_chu` của mục đó. Những ca như vậy sẽ được trích vào báo cáo.
