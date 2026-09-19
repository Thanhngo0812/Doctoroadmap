# Hướng dẫn gán nhãn quan hệ tiên quyết

Dành cho người gán nhãn. Đọc hết một lần trước khi bắt đầu, và mở lại bất cứ lúc nào còn phân vân.

Hướng dẫn này theo giao thức **PREAP** (Alzetta, Torre & Koceva, 2023). Vì sao chọn PREAP, và giao thức đó chi tiết
thế nào, xem [`report/preap-giao-thuc-gan-nhan-tien-quyet.md`](../report/preap-giao-thuc-gan-nhan-tien-quyet.md).
Phần quyết định của dự án nằm ở ADR [0009](./adr/0009-nhan-vang-tien-quyet-bam-van-ban.md) và spec
[A6–A8](./A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md), mục D13.

---

## 1. Việc này để làm gì

Hệ thống đang học cách đọc một giáo trình rồi tự vẽ ra **khái niệm nào phải học trước khái niệm nào**. Muốn biết
nó làm đúng tới đâu, ta cần một đáp án do **người** viết: đó là việc của bạn.

Nhãn bạn gán sẽ thành **bộ vàng**. Bộ vàng chỉ dùng để **chấm** hệ thống, một lần duy nhất. Không ai dùng nó để
chỉnh máy cho khớp.

## 2. Bạn nhận được gì

| Thứ | Dùng để làm gì |
|---|---|
| Cuốn giáo trình | Đọc **chương được giao** |
| File Excel riêng của bạn | Ghi quan hệ và cờ. Tên file có mã người gán của bạn, ví dụ `…-A1.xlsx` |
| Tài liệu này | Luật gán |

File Excel có bốn sheet nhìn thấy:

| Sheet | Nội dung | Bạn làm gì |
|---|---|---|
| **Hướng dẫn** | Tài liệu, chương, mã người gán, tóm tắt luật, ô ghi thời gian | Ghi thời gian vào hai ô vàng |
| **Quan hệ** | Bảng trống, mỗi dòng một quan hệ | **Ghi quan hệ ở đây** |
| **Cờ** | Bảng trống | Ghi khi danh sách khái niệm có gì sai |
| **Khái niệm** | Mọi khái niệm của tài liệu, kèm nơi dạy. **Bị khoá** | Chỉ đọc, lọc, tìm |

Ở sheet **Khái niệm**, dòng **in đậm** và có chữ **"Có"** ở cột *Thuộc chương đang gán* là **khái niệm đích** —
khái niệm được dạy trong chương bạn đang gán. Cột *Nơi dạy* ghi chương, mục và trang, ví dụ
`[C3] 3.2 Ước lượng khoảng — tr. 71, 72`.

> **Về số trang.** Sách được cắt thành từng đoạn, và cột *Nơi dạy* ghi trang **bắt đầu** của đoạn. Một đoạn có thể
> vắt sang trang kế, nên câu định nghĩa đôi khi nằm ở **trang liền sau** trang ghi trong cột. Không thấy ở trang đó
> thì xem thêm trang sau, đừng vội đánh cờ *Nơi dạy sai*. Cột **Câu định nghĩa máy tìm được** cho biết đúng câu cần
> tìm ở những khái niệm mà máy tìm được; cột này trống nghĩa là máy không tìm thấy, không có nghĩa là sách không có.

## 3. Quan hệ tiên quyết là gì

> **B là tiên quyết của A** khi người đọc phải biết B thì mới hiểu được A.

Trong đợt gán này, câu đó có thêm một vế, và vế đó quan trọng nhất:

> **… để hiểu A _như chính đoạn sách này trình bày_.**

Ta không hỏi "theo bạn, học A có cần B không". Ta hỏi "**tác giả cuốn sách này** dùng B để giải thích A không".
Hai câu hỏi cho đáp án khác nhau, và đợt này chỉ cần câu thứ hai.

Trong file, mỗi quan hệ ghi theo chiều: **A (khái niệm đích) cần biết trước B**.

## 4. Ba nguyên tắc

1. **Theo sách, không theo hiểu biết của bạn.** Sách không dùng B khi giải thích A thì không ghi, kể cả khi bạn
   biết chắc B có liên quan. Sách có dùng B thì ghi, kể cả khi bạn thấy cách trình bày đó lạ.
2. **Chỉ ghi tiên quyết trực tiếp.** Đã có *A cần B* và *B cần C* thì **không** ghi *A cần C* — trừ khi đoạn văn
   về A dùng thẳng C.
3. **Chỉ ghi cặp có quan hệ.** Bạn không phải xét mọi cặp khái niệm. Không ghi gì nghĩa là không có quan hệ.

Ba tính chất của quan hệ tiên quyết, hệ thống sẽ tự kiểm:

- **Không tự nối:** A không thể là tiên quyết của chính A.
- **Một chiều:** đã có *A cần B* thì không thể có *B cần A*.
- **Bắc cầu:** *A cần B* và *B cần C* thì tự hiểu là *A cần C*. Vì vậy bạn không phải ghi các cặp suy ra được, và
  lúc chấm, hai người ghi *A cần C* theo hai cách (trực tiếp, hoặc qua B) vẫn được tính là đồng ý với nhau.

## 5. Quy trình, từng bước

**Bước 0 — gán thử, một lần duy nhất trước khi vào chương thật**

PREAP khuyên có một đợt gán thử để người gán hiểu hướng dẫn giống nhau. Người quản lý sinh cho mỗi người một file của
**một chương khác** (không phải chương sẽ làm bộ vàng). Mỗi người gán vài trang đầu của chương đó theo đúng các bước
dưới đây, rồi hai người cùng người quản lý so kết quả và bàn chỗ hiểu khác nhau. **Nhãn gán thử bị bỏ**, không vào bộ
vàng. Sau buổi này mới bắt đầu chương thật, và từ đó hai người làm độc lập.

**Trước khi bắt đầu**

1. Mở file Excel của bạn. Ở sheet **Hướng dẫn**, kiểm tra đúng tài liệu, đúng chương, đúng mã của bạn.
2. Mở sheet **Khái niệm**, lọc cột *Thuộc chương đang gán* = *Có* để xem danh sách khái niệm đích. Lướt qua một
   lượt để biết chương này dạy gì.
3. Ghi lại giờ bắt đầu ở chỗ của bạn (điện thoại, giấy). Cuối buổi bạn sẽ ghi **tổng số phút** vào file.

**Gán**

4. **Đọc chương theo thứ tự**, từ đầu tới cuối.
5. Mỗi khi đoạn văn **dạy** một khái niệm đích A, tự hỏi:
   > *Để hiểu A như đoạn này trình bày, người đọc phải biết trước khái niệm nào trong danh sách?*
6. Với mỗi khái niệm B trả lời được câu hỏi đó, thêm **một dòng** ở sheet **Quan hệ**:
   - cột **Khái niệm đích (A)**: chọn A trong danh sách;
   - cột **Cần biết trước (B)**: chọn B trong danh sách. **B có thể được dạy ở chương khác**, kể cả chương sau;
   - cột **Vị trí trong sách**: trang, hoặc số mục, hoặc cả hai, ví dụ `tr. 72, mục 3.2`;
   - cột **Loại bằng chứng**: xem mục 7;
   - cột **Mức cần**: xem mục 8. Có thể để trống;
   - cột **Ghi chú**: tuỳ ý, nhưng rất có ích lúc hội ý.
7. Chọn tên bằng danh sách: bấm vào ô rồi **gõ vài chữ** để tìm. Đừng dán tên từ chỗ khác vào, vì dán sẽ bỏ qua
   kiểm tra.
8. Danh sách khái niệm có gì sai thì ghi ở sheet **Cờ** (mục 9). **Không** tự thêm khái niệm vào sheet Quan hệ.
9. Gán xong, ghi **tổng số phút gán** vào ô vàng *Thời gian gán*.

**Rà soát** — bước bắt buộc của PREAP

10. Với **từng dòng** bạn đã ghi, mở lại đúng đoạn sách ở cột *Vị trí*, đọc lại, rồi quyết: giữ, sửa, hay xoá.
    Hỏi lại ba câu: sách có thật sự dùng B để giải thích A không? Có phải tiên quyết **trực tiếp** không? Chiều có
    đúng không?
11. Nhìn các ô tô màu ở sheet Quan hệ và sửa hết (mục 11).
12. Ghi **tổng số phút rà soát** vào ô vàng *Thời gian rà soát*.

**Nộp**

13. Lưu file, gửi cho người quản lý đợt gán. **Không** gửi qua dịch vụ trực tuyến công cộng.
14. Người quản lý chạy kiểm tra tự động. Nếu có lỗi, bạn nhận lại danh sách lỗi theo từng dòng để sửa.

## 6. Các cột của sheet Quan hệ

| Cột | Bắt buộc | Ghi gì |
|---|---|---|
| STT | — | Số dòng, có sẵn |
| Khái niệm đích (A) | có | Khái niệm **được dạy trong chương đang gán** |
| Cần biết trước (B) | có | Bất kỳ khái niệm nào của tài liệu |
| Vị trí trong sách | nên có | Trang, mục — nơi bạn thấy sách dùng B để giải thích A |
| Loại bằng chứng | có | Một trong ba loại ở mục 7 |
| Mức cần | không | Bắt buộc, hoặc Hữu ích |
| Ghi chú | không | Lý do, câu trích ngắn, phân vân |

## 7. Loại bằng chứng

| Nhãn | Khi nào chọn | Ví dụ |
|---|---|---|
| **Nói rõ** | Sách nói thẳng là cần B, hoặc dẫn người đọc quay lại B | *"Nhắc lại khái niệm **phương sai** ở chương 2 trước khi xây dựng **khoảng tin cậy**."* → Khoảng tin cậy cần biết trước Phương sai |
| **Trong định nghĩa, cần để hiểu** | B nằm **trong câu định nghĩa** A, **và** không hiểu B thì không hiểu được câu định nghĩa đó | *"**Sai số chuẩn** là **độ lệch chuẩn** của phân phối mẫu của một thống kê."* → Sai số chuẩn cần Độ lệch chuẩn, và cần Phân phối mẫu |
| **Mạch trình bày** | Sách không nói thẳng, nhưng cách giải thích A dựa rõ ràng vào B | Mục về **kiểm định giả thuyết** dùng liên tục **mức ý nghĩa** và **giá trị p** để giải thích các bước, dù không có câu nào nói "cần biết trước" |

Không có loại **"đoán"**. Nếu bạn chỉ đoán, thì **không ghi**.

**Bẫy thường gặp nhất** (chính người làm PREAP tìm thấy lỗi này nhiều nhất trong bộ vàng của họ): **một khái niệm
được nhắc trong lúc giải thích khái niệm khác chưa chắc đã là tiên quyết.** Nếu nó chỉ là giải thích thêm, ví dụ
minh hoạ, hay phép so sánh, thì không ghi. Xem ca khó 1 ở mục 10.

## 8. Mức cần

Không bắt buộc. PREAP đề xuất cột này; tác giả PREAP vẫn đang thử nó, còn dự án dùng nó để phân tích thêm.

| Nhãn | Nghĩa |
|---|---|
| **Bắt buộc** | Sách trình bày B như điều **phải** biết để hiểu A |
| **Hữu ích** | B giúp hiểu A **sâu hơn**, nhưng không có B vẫn theo được đoạn văn |

Phân vân thì để trống.

## 9. Sheet Cờ

Danh sách khái niệm do máy tạo, nên có thể sai. Bạn **không sửa** danh sách; bạn **ghi cờ**.

| Loại cờ | Khi nào | Cần điền |
|---|---|---|
| **Không phải khái niệm** | Một mục trong danh sách không phải khái niệm để học: tên người, ví dụ cụ thể, một cụm từ vô nghĩa | Khái niệm liên quan |
| **Thiếu khái niệm** | Sách dạy một khái niệm quan trọng mà danh sách không có | **Tên khái niệm thiếu**; nên có vị trí |
| **Node gộp sai** | Một tên trong danh sách thực ra gộp hai khái niệm khác nhau | Khái niệm liên quan; ghi chú giải thích |
| **Tên sai** | Tên hiển thị không phải cách sách gọi khái niệm đó | Khái niệm liên quan |
| **Nơi dạy sai** | Cột *Nơi dạy* chỉ sai chỗ sách thật sự dạy khái niệm | Khái niệm liên quan; vị trí đúng |
| **Khác** | Mọi vấn đề khác | Ghi chú |

Khi một khái niệm bị thiếu mà bạn thấy nó là tiên quyết của một khái niệm đích, ghi cờ **Thiếu khái niệm** và nêu
điều đó trong ghi chú. Đừng chọn một khái niệm "gần giống" để thay.

## 10. Ca khó

Các ca dưới đây là ví dụ minh hoạ, không lấy từ cuốn sách bạn đang gán.

**1. Nhắc tới trong lúc giải thích, nhưng chỉ để giải thích thêm.**
> *"**Phương sai mẫu hiệu chỉnh** được tính từ **trung bình mẫu**; khác với **phương sai tổng thể**, ta chia cho
> n − 1."*

Trung bình mẫu dùng để định nghĩa → ghi *Phương sai mẫu hiệu chỉnh cần Trung bình mẫu*. Phương sai tổng thể chỉ để
so sánh → **không** ghi, trừ khi đoạn văn thật sự dựa vào nó để giải thích.

Ví dụ chính PREAP gặp: câu *"Đại số sơ cấp khác số học ở việc dùng trừu tượng, như dùng chữ thay cho số"* từng bị
gán thành *đại số sơ cấp* là tiên quyết của *chữ* và *số*. Sai chiều: chữ và số mới là thứ cần để hiểu phép trừu
tượng.

**2. Cái chung và cái riêng (cha–con).**
> *"**Khoảng tin cậy cho trung bình** là một trường hợp của **khoảng tin cậy** khi tham số là trung bình tổng thể."*

Sách dạy cái chung trước rồi dùng nó để giải thích cái riêng → ghi *Khoảng tin cậy cho trung bình cần Khoảng tin
cậy*. Nếu sách chỉ liệt kê các trường hợp mà không dựa vào cái chung để giải thích, thì không ghi.

**3. Liệt kê anh em.**
> *"Các bài toán học máy gồm **phân loại**, **phân cụm** và **hồi quy**."*

Cùng nằm trong một danh sách **không** tạo quan hệ giữa phân loại, phân cụm và hồi quy.

**4. Toàn thể và bộ phận.**
> *"**Tiền xử lý dữ liệu** gồm **làm sạch dữ liệu** và **biến đổi dữ liệu**."*

Nếu sau đó sách giải thích tiền xử lý bằng cách đi qua từng bước → ghi *Tiền xử lý dữ liệu cần Làm sạch dữ liệu* và
*…cần Biến đổi dữ liệu*. Nếu chỉ liệt kê rồi thôi → không ghi.

**5. Nguyên nhân, thời gian, cách tính.** PREAP ghi nhận các quan hệ kiểu *"A được tính từ B"*, *"A xảy ra sau B"*,
*"B gây ra A"* thường đi kèm quan hệ tiên quyết. Vẫn áp đúng câu hỏi ở bước 5: sách có dùng B để giải thích A không.

**6. Sách nhắc B trước khi dạy B.** Không sao. Thứ tự trang không quyết định. Nếu để hiểu A cần B thì ghi, dù B được
dạy ở chương sau.

**7. Ký hiệu và công thức.** `μ`, `σ²`, `x̄` không có trong danh sách. Nếu đoạn văn cần *trung bình tổng thể* và
danh sách có khái niệm đó, chọn tên khái niệm. Nếu danh sách không có, ghi cờ **Thiếu khái niệm**.

**8. Bắc cầu.** A cần B, B cần C. Đoạn văn về A có dùng thẳng C không? Có → ghi cả *A cần C*. Không → chỉ ghi *A cần
B*.

**9. Hai khái niệm có vẻ cần nhau.** Không được ghi cả hai chiều; file sẽ tô màu tím và kiểm tra sẽ báo lỗi. Đọc lại
cả hai đoạn và chọn chiều mà sách thật sự dùng. Không quyết được thì không ghi và nêu trong ghi chú của một dòng khác.

**10. Khái niệm được dạy ở nhiều chỗ.** Chỉ xét cách trình bày **trong chương đang gán**.

**11. Ví dụ, hình, bảng.** Không phải khái niệm; danh sách đã loại chúng ra. Nếu thấy một mục như vậy trong danh
sách, ghi cờ **Không phải khái niệm**.

**12. Khái niệm quá chung** (như *dữ liệu*, *mô hình*). Chỉ ghi khi đoạn văn thật sự cần người đọc biết khái niệm
đó theo nghĩa sách đã dạy, không phải nghĩa đời thường.

## 11. Màu cảnh báo ở sheet Quan hệ

| Màu | Nghĩa | Sửa |
|---|---|---|
| **Đỏ** | A trùng B | Chọn lại |
| **Vàng** | Cặp A–B đã có ở dòng khác | Xoá một dòng |
| **Tím** | Có cả *A cần B* lẫn *B cần A* | Đọc lại, giữ một chiều |

Kiểm tra tự động còn bắt thêm: vòng dài hơn (A cần B, B cần C, C cần A), khái niệm đích không thuộc chương, thiếu
loại bằng chứng, và tên không có trong danh sách.

## 12. Không được làm

- **Không tra cứu ngoài sách**: không tìm trên mạng, không hỏi trợ lý AI.
- **Không xem kết quả của máy** trước khi nộp.
- **Không bàn với người gán khác** trước khi nộp. Hai người làm độc lập thì độ đồng thuận mới có nghĩa.
- Không sửa sheet Khái niệm, không đổi tên sheet, không xoá sheet.
- Không đưa file lên Google Sheets hay dịch vụ trực tuyến khác: file chứa nội dung trích từ sách.

## 13. Sau khi nộp: hội ý

1. Người quản lý tính **độ đồng thuận** giữa hai người, có kể đồng thuận ngầm qua bắc cầu.
2. Hai người ngồi lại, **chỉ bàn các cặp lệch nhau**. Với mỗi cặp: mở đúng đoạn sách, đọc to, rồi chốt giữ hoặc bỏ,
   kèm một câu lý do.
3. Nếu gộp nhãn tạo ra vòng hoặc đường đi quá dài, bàn tiếp tới khi hết.
4. Kết quả hội ý là **bộ vàng chính**. Nhãn riêng của từng người vẫn được giữ, để báo cáo cả số trên hợp lẫn trên
   giao nhãn của hai người.

## 14. Mất bao lâu

Trong thí nghiệm của PREAP, một đoạn 135–286 token với 14–23 khái niệm mất 13–21,5 phút. Một chương giáo trình dài
hơn thế nhiều lần: trong dự án mẫu của PREAP, một chương 20.964 token có 140 khái niệm. Hãy chia thành nhiều buổi,
và ghi **thời gian thật** — con số đó cũng là một kết quả của đợt này.

## 15. Câu hỏi thường gặp

**Tôi không chắc một cặp có phải tiên quyết không.** Không ghi. Nếu muốn, ghi phân vân vào cột Ghi chú của một dòng
gần đó để nêu lúc hội ý.

**Danh sách chọn quá dài.** Gõ vài chữ đầu của tên để lọc. Nếu không tìm thấy, xem sheet Khái niệm: có thể sách gọi
bằng tên khác (cột *Tên khác trong tài liệu*).

**Tôi lỡ dán tên vào ô.** Không sao, kiểm tra tự động sẽ báo nếu tên không khớp danh sách.

**Một khái niệm đích không có tiên quyết nào.** Bình thường: khái niệm nền tảng thường không có. Không cần ghi gì.

**Tôi thấy một quan hệ giữa hai khái niệm đều không thuộc chương.** Không ghi. Đợt này chỉ gán cho khái niệm đích.
