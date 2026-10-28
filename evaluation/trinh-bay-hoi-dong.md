Trạng thái: bản thiết kế ngày 2026-10-26. Phần kết quả (mục 13) sẽ điền sau lượt chạy 07–09/11. Bản này cập nhật song song với kế
hoạch kỹ thuật `report/ke-hoach-danh-gia-pha-a-2026-10-26.md`; mỗi khi kế hoạch đổi, bản này đổi theo.

# Đánh giá Pha A của hệ thống doc2roadmap

Tài liệu này trình bày cho hội đồng cách nhóm đánh giá Pha A: hệ thống biến một giáo trình thành lộ trình học, và nhóm kiểm chứng chất
lượng của lộ trình đó như thế nào. Mỗi phần trả lời một câu hỏi mà người nghe có thể đặt ra: đo cái gì, so với cái gì, đáp án chuẩn do ai
làm, và vì sao con số đáng tin.

## 1. Pha A làm gì

Pha A nhận một giáo trình PDF tiếng Việt và trả về một lộ trình học. Lộ trình là một dãy khái niệm chia thành các module; mỗi khái niệm
kèm danh sách khái niệm cần học trước. Quá trình đi qua mười khâu, từ đọc tệp PDF tới xếp dãy học. Hình 1 vẽ toàn luồng, Bảng 1 tóm tắt
từng khâu.

[CHÈN HÌNH 1 – Sơ đồ luồng Pha A. Bố cục từ trái sang phải: "Giáo trình PDF" → A1 Đọc PDF và cây mục → A2 Cắt đoạn và gán vai trò vùng
→ A3 Trích khái niệm → A4 Hợp nhất khái niệm trùng → A5 Câu định nghĩa và trạng thái dạy → A6/A7 Cụm chủ đề và bản đồ nhắc tên → A8 Suy
luận quan hệ tiên quyết → A9 Kiểm định đồ thị → A10 Xếp dãy học và chia module → "Lộ trình học". Tô màu khác cho các khâu có dùng mô hình
ngôn ngữ lớn (A2 một phần, A3, A4/A5, A8 bước suy luận chính, đặt tên module). Dưới mỗi khâu ghi một dòng đầu ra, ví dụ "cây mục",
"danh sách khái niệm", "đồ thị tiên quyết".]

Hình 1. Luồng xử lý của Pha A

Bảng 1. Các khâu của Pha A

| Khâu | Làm gì | Đầu ra | Dùng mô hình ngôn ngữ lớn |
|---|---|---|---|
| A1 | đọc chữ trong PDF, nhận tiêu đề, dựng cây mục | cây mục và văn bản | không (mô hình học máy nhỏ nhận tiêu đề) |
| A2 | cắt văn bản thành đoạn; gán vai trò cho từng mục (nội dung, bài tập, đề cương, mở đầu…) | đoạn văn có vai trò | một phần |
| A3 | trích các khái niệm xuất hiện trong từng mục | danh sách ứng viên | có |
| A4 | gộp các ứng viên cùng chỉ một khái niệm (tên khác, viết tắt) | danh sách khái niệm duy nhất | có |
| A5 | chọn câu định nghĩa của khái niệm; quyết định khái niệm có được dạy trong sách không | câu định nghĩa, trạng thái dạy | có |
| A6/A7 | gom khái niệm theo chủ đề; ghi nơi mỗi khái niệm được nhắc tới | cụm, bản đồ nhắc tên | không (embedding) |
| A8 | suy luận "phải hiểu X trước khi học Y" | cạnh tiên quyết | bước chính có; bước phụ là mô hình học máy |
| A9 | gỡ vòng lặp, kiểm các cạnh ngược thứ tự sách | đồ thị hợp lệ | không |
| A10 | xếp dãy học tôn trọng tiên quyết, chia module, đặt tên module | lộ trình | đặt tên module có |

## 2. Đánh giá để trả lời câu hỏi gì

Nhóm đặt năm câu hỏi nghiên cứu, liệt kê ở Bảng 2. Mỗi phần sau của tài liệu phục vụ một hay vài câu hỏi trong số đó.

Bảng 2. Câu hỏi nghiên cứu

| Mã | Câu hỏi | Trả lời bằng |
|---|---|---|
| RQ1 | Trên giáo trình chưa từng thấy, lộ trình có dạy đủ khái niệm trọng yếu và đặt khái niệm tiên quyết trước khái niệm cần nó không? | độ phủ khái niệm, tỉ lệ vi phạm thứ tự, đánh giá của người học; so với cách làm đơn giản |
| RQ2 | Từng khâu tốt tới đâu, và lỗi cuối cùng bắt nguồn từ khâu nào? | thước đo từng khâu; truy lỗi; thí nghiệm thay khâu bằng đáp án đúng |
| RQ3 | Tạo một lộ trình mất bao nhiêu phút và bao nhiêu tiền? | thời gian và chi phí theo khâu |
| RQ4 | Các lựa chọn thiết kế chính đóng góp bao nhiêu? | thí nghiệm bỏ hoặc thay từng bộ phận |
| RQ5 | Kết quả có ổn định không, khi đầu vào thay đổi mà nghĩa không đổi? | chạy lặp có nhiễu |

## 3. Vì sao nhóm dựng lại cách đánh giá

Trước đợt này, nhóm đã có một số thước đo từ quá trình phát triển. Khi rà lại để đưa ra hội đồng, nhóm thấy chúng chưa đủ chắc vì bốn lý
do:
- **Mẫu nhỏ.** Đáp án chuẩn về quan hệ tiên quyết bằng tiếng Việt chỉ có ở năm cuốn, mỗi cuốn một đến bốn chương.
- **Phần lớn không do người làm.** Ngoài quan hệ tiên quyết, các đáp án khác do mô hình hoặc trợ lý AI lập.
- **Phụ thuộc vào chính hệ thống.** Danh sách khái niệm để chấm lấy từ đầu ra của hệ, nên chỉ chấm được hệ trên chính danh sách của nó.
- **Đã dùng để chỉnh hệ.** Các tài liệu có đáp án đều đã được dùng khi phát triển, nên số đo trên chúng lạc quan hơn thực tế.

Vì vậy nhóm làm lại toàn bộ trên một bộ sách mới, với đáp án chuẩn do người lập độc lập với hệ thống.

## 4. Dữ liệu

Bộ sách được tách thành hai phần, như Bảng 3:
- **Tập phát triển** dùng để tìm lỗi và cải tiến hệ.
- **Tập thử** chỉ dùng một lần, sau khi hệ đã đóng băng, để lấy số báo cáo.

Không cuốn nào có mặt ở cả hai tập, và không cuốn nào trong tập thử từng được dùng để huấn luyện hay chỉnh hệ.

Bảng 3. Hai tập dữ liệu

| Tập | Nội dung | Dùng để |
|---|---|---|
| Phát triển | ba khoảng chương của ba giáo trình đã dùng khi phát triển: thống kê, đại số tuyến tính, nhập môn học máy | tìm lỗi, chọn cải tiến |
| Thử | 8 giáo trình tiếng Việt đầy đủ, mỗi chủ đề một cuốn: toán, vật lý, hoá học, sinh học, văn học, công nghệ thông tin, kinh tế, luật; từ 57 tới 422 trang, tổng 1.749 trang | số báo cáo cuối |

Bảng 4 liệt kê 8 cuốn. Mọi cuốn là PDF gốc có lớp chữ (từ 96,9% số trang trở lên), không phải bản quét. Hệ chạy trên **cả cuốn**, nên thời
gian và chi phí đo được là của một giáo trình thật. Đáp án chuẩn có hai phạm vi:
- cấu trúc mục và vai trò vùng được gán cho cả cuốn;
- khái niệm và quan hệ tiên quyết được gán trên **3 chương bốc ngẫu nhiên theo một hạt giống cố định** (một chương phần đầu, một phần giữa,
  một phần cuối). Ba chương chiếm từ 9% tới 75% cuốn, tuỳ chương dài hay ngắn; tổng cộng 561 trang.

Một quan hệ có thể lấy khái niệm tiên quyết từ bất kỳ phần nào trước đó của sách, nên vẫn chấm được các quan hệ xuyên chương dù ba chương
không liên quan với nhau. Khái niệm tiên quyết nằm ngoài ba chương được người gán ghi kèm trang nơi nó được định nghĩa.

Chương được bốc ngẫu nhiên trước khi chạy hệ, theo luật ghi sẵn trong giao thức. Luật lọc chỉ dựa vào cây mục, không nhìn nội dung: chương phải
đủ dài, không phải chương mở đầu, không phải chương chỉ có bài tập hay phụ lục. Nhóm cố ý **không** chọn những chương "có nhiều quan hệ",
vì muốn biết chương nào nhiều quan hệ thì phải đọc trước nội dung hoặc nhìn đầu ra của hệ, và kết quả khi đó sẽ thiên lệch.

Bảng 4. Danh sách sách tập thử (tên sách công bố sau khi đóng băng hệ, 07/11)

| Chủ đề | Mã | Tên sách | Số trang | Trang của ba chương bốc |
|---|---|---|---|---|
| Toán (xác suất thống kê) | T | — | 277 | 134 (48%) |
| Vật lý (cơ học lý thuyết) | L | — | 140 | 52 (37%) |
| Hoá học (hoá hữu cơ) | H | — | 179 | 134 (75%) |
| Sinh học (thực vật dược) | S | — | 108 | 59 (55%) |
| Văn học (lý luận văn học, phần tác phẩm) | V | — | 57 | 30 (53%) |
| Công nghệ thông tin (học máy) | C | — | 422 | 39 (9%) |
| Kinh tế (quản trị logistics) | K | — | 356 | 76 (21%) |
| Luật (luật lao động) | LU | — | 210 | 37 (18%) |

**Kiểm sách trước khi dùng.** Mỗi cuốn được kiểm ba điều trước khi bốc chương: có phải PDF gốc không; có trùng tệp (cùng mã băm SHA-256) với dữ liệu
từng dùng để huấn luyện hay với tập phát triển không; có trùng đoạn văn bản với các sách đó không. Lượt gom đầu có 4/8 cuốn bị loại và thay:
- cuốn hoá trùng hẳn một cuốn đã dùng huấn luyện;
- cuốn công nghệ thông tin là bản đầy đủ của một giáo trình trong tập phát triển;
- cuốn toán là sổ tay tóm tắt công thức, không phải giáo trình;
- cuốn sinh là tài liệu bồi dưỡng học sinh trung học cơ sở.

Đây là bằng chứng cho thấy kiểm nhiễm dữ liệu là cần thiết: nếu không kiểm, một phần tư tập thử sẽ là sách hệ đã thấy.

**Luật bốc chương được chốt trước khi mở mục lục.** Tệp giao thức ghi hạt giống (20261027) và độ dài tối thiểu của chương (5 trang) được lưu vào
lịch sử phiên bản trước khi người giữ sổ mở mục lục của bất kỳ cuốn thử nào. Mã băm của lần lưu đó chứng minh không ai chọn được hạt giống theo
kết quả bốc.

**Điều cần nói rõ về bộ sách:** cuốn văn chỉ có phần hai của một giáo trình lý luận văn học; cuốn sinh là giáo trình trình độ trung cấp; cuốn
toán cùng môn xác suất thống kê với một cuốn của tập phát triển, và cuốn công nghệ thông tin cùng ngành học máy với một cuốn của tập phát
triển (khác cuốn, không trùng đoạn văn bản nào).

Chọn 8 chủ đề để có thể nói hệ dùng được cho nhiều ngành, không chỉ ngành toán hay công nghệ thông tin. Chọn giáo trình đầy đủ để chất
lượng và chi phí đo được đúng với cách sản phẩm được dùng. Về thống kê, mỗi cuốn là một đơn vị độc lập, và ba chương trong cuốn là tầng thứ
hai (mục 9).

## 5. Đáp án chuẩn được làm thế nào

Muốn chấm hệ thì phải có đáp án chuẩn, gọi là **vàng**. Vàng của đợt này do người lập, theo một giao thức viết trước.

### 5.1 Người gán

Mỗi chủ đề có **hai sinh viên đại học của chính ngành đó**. Hai người cùng gán cuốn của chủ đề, **độc lập**, không trao đổi với nhau. Họ không được xem đầu ra của hệ trên các cuốn này cho tới khi vàng đã chốt. Tập phát triển do các sinh viên khác gán theo cùng giao
thức. Thông tin người gán (ngành, năm học) được ghi ẩn danh trong phụ lục.

### 5.2 Năm lớp vàng

Vàng gồm năm lớp, mỗi lớp dùng để chấm một số khâu (Bảng 5).

Bảng 5. Các lớp vàng

| Lớp | Người gán ghi gì | Dùng để chấm |
|---|---|---|
| G1 Cấu trúc | cây mục của cả cuốn: tiêu đề, cấp, trang | A1 |
| G2 Vai trò vùng | mỗi mục của cả cuốn là nội dung, bài tập, đề cương, mở đầu, hành chính hay phần cuối sách | A2 |
| G3 Kho khái niệm | trên 3 chương bốc: các khái niệm sách dạy, câu định nghĩa (trang và câu nguyên văn), trạng thái dạy, tên gọi khác | A3, A4, A5 |
| G4 Quan hệ tiên quyết | các cặp "phải hiểu X trước khi học Y" với Y thuộc 3 chương bốc, kèm câu trong sách làm bằng chứng | A8, A10 |
| G5 Phán mù đầu ra | sau khi hệ chạy: khái niệm và cạnh máy đưa ra mà vàng không có thì đúng hay sai; lộ trình có dễ học không | độ chính xác, đánh giá người dùng |

G1 và G2 chủ yếu là đối chiếu với mục lục, nên một trợ lý AI lập bản nháp và sinh viên duyệt lại toàn bộ. Bản nháp không lấy từ đầu ra
của hệ, để tránh chấm hệ bằng chính nó. Để biết người duyệt có duyệt thật hay chỉ gật đầu, nhóm cài sẵn 3–5 lỗi đã biết vào bản nháp mỗi cuốn,
rồi báo tỉ lệ lỗi cài được bắt. G3, G4 và G5 do sinh viên làm từ đầu.

### 5.3 Gán hai giai đoạn

Quan hệ tiên quyết được gán theo giao thức PREAP, một giao thức gán quan hệ tiên quyết trong giáo trình đã được công bố [6]. Hai điểm then
chốt của giao thức:
- **Bám văn bản:** chỉ ghi quan hệ mà cách sách trình bày thể hiện, không ghi theo hiểu biết riêng. Hệ cũng được thiết kế để trích đúng
  loại quan hệ này. Quan hệ mà người gán biết nhưng sách không viết ra thì vẫn được ghi, kèm cờ "kiến thức chuyên môn", và báo riêng.
- **Tách khái niệm khỏi quan hệ:** người gán chốt danh sách khái niệm trước, rồi mới gán quan hệ trên danh sách đó. PREAP đo được: khi
  người gán vừa thêm khái niệm vừa gán quan hệ, độ đồng thuận giữa hai người tụt từ 0,62 xuống 0,25 [6].

Hình 2 vẽ quy trình gán.

[CHÈN HÌNH 2 – Quy trình gán hai giai đoạn. Hai cột song song "Sinh viên A" và "Sinh viên B". Giai đoạn 1: mỗi người tự liệt kê khái niệm
→ phiếu bất đồng → hội ý → "Kho khái niệm chốt". Giai đoạn 2: mỗi người tự ghi quan hệ tiên quyết trên kho chốt → phiếu bất đồng → hội ý →
"Vàng quan hệ". Mũi tên phụ: ca vẫn bất đồng → "Tranh chấp (báo riêng)". Ghi chú bên lề: "độc lập, không xem đầu ra của hệ".]

Hình 2. Quy trình gán vàng hai giai đoạn

### 5.4 Khi hai người không đồng ý

Ca bất đồng được giải theo một quy trình cố định:
1. Nhóm lập phiếu chỉ gồm các mục hai người ghi khác nhau, kèm câu trích của mỗi bên.
2. Mỗi người ghi "giữ" hoặc "bỏ" cùng một dòng lý do. Phiếu được chuyển qua một vòng; người điều phối chỉ chuyển phiếu, không phán nội
   dung chuyên môn.
3. Ca vẫn bất đồng sau một vòng được ghi là **tranh chấp** và không đưa vào vàng chính. Kết quả được báo thêm trên hai phiên bản: vàng gồm
   mọi ý của cả hai người (hợp), và vàng chỉ gồm ý cả hai cùng ghi (giao). Nhờ vậy người đọc thấy cách xử lý tranh chấp làm đổi số tới đâu.

## 6. So đầu ra của máy với vàng

Máy và người có thể gọi cùng một khái niệm bằng hai cách khác nhau. Ví dụ, vàng ghi "Khoảng tin cậy của trung bình", còn máy ghi "Ước
lượng khoảng trung bình". Trước khi chấm, mỗi khái niệm của máy được ghép với khái niệm vàng tương ứng, qua hai bước:
1. **Ghép tự động** theo luật viết trước: trùng tên hay tên khác sau khi chuẩn hoá, hoặc máy chọn đúng câu định nghĩa mà người gán đã ghi.
2. **Ghép tay** cho các ca còn lại: khớp, máy rộng hơn, máy hẹp hơn, hay không khớp. Người ghép không biết khái niệm đó thuộc hệ nào trong
   các hệ được so. Mọi quyết định được ghi nhật ký. Một sinh viên của ngành ghép độc lập 20% số ca để kiểm.

Báo cáo ghi tỉ lệ ghép tự động, tỉ lệ ghép tay, và mức khớp giữa hai người ghép.

## 7. Đo gì ở từng khâu

Bảng 6 liệt kê thước đo chính của từng khâu, kèm cách hiểu con số. Mỗi khâu có một thước chính được chọn trước khi chấm; các thước khác chỉ
để mô tả thêm.

Bảng 6. Thước đo chính theo khâu

| Khâu | Câu hỏi | Thước chính | Hiểu con số |
|---|---|---|---|
| A1 Đọc PDF | chữ trong sách có về đúng mục không | M3: tỉ lệ ký tự nội dung nằm đúng mục | 0,95 nghĩa là 95% chữ nội dung về đúng mục |
| A2 Vai trò vùng | phần nội dung có bị gán nhầm thành đề cương hay bài tập không | độ phủ của vai trò "nội dung" | thấp nghĩa là có nội dung bị coi như không phải bài học |
| A3 Trích khái niệm | máy có tìm đủ khái niệm sách dạy không | độ phủ khái niệm vàng | 0,80 nghĩa là máy tìm được 80% khái niệm người gán ghi |
| A4 Hợp nhất | máy có tách một khái niệm thành hai, hay gộp hai khái niệm thành một không | tỉ lệ tách và tỉ lệ gộp nhầm | càng thấp càng tốt |
| A5 Định nghĩa, trạng thái | máy có chọn đúng câu định nghĩa và biết khái niệm nào được dạy không | tỉ lệ câu định nghĩa đúng; độ chính xác trạng thái | càng cao càng tốt |
| A8 Tiên quyết | các cạnh "X trước Y" của máy có đúng không, có đủ không | F1 cạnh tiên quyết | trung hoà giữa đúng và đủ, từ 0 tới 1 |
| A10 Lộ trình | lộ trình có đặt khái niệm tiên quyết trước khái niệm cần nó không | Q6: tỉ lệ cạnh vàng bị vi phạm | 0,10 nghĩa là 10% quan hệ tiên quyết thật bị đặt ngược hoặc thiếu |
| Đầu-cuối | người học nhận được gì | độ phủ khái niệm trong lộ trình, cộng Q6 | — |
| Truy nguyên | khái niệm và quan hệ có dẫn về đúng câu trong sách không | tỉ lệ bằng chứng có thật | 0,95 nghĩa là 95% câu hệ trích có nguyên văn trong sách |

Khung dưới ghi công thức của các thước chính.

> **Độ chính xác (P), độ phủ (R), F1** cho cạnh tiên quyết:
> P = số cạnh máy đúng / số cạnh máy đưa ra; R = số cạnh vàng máy tìm được / số cạnh vàng; F1 = 2·P·R / (P + R).
>
> **Q6 – tỉ lệ vi phạm thứ tự học:** Q6 = (số cạnh vàng X → Y mà lộ trình đặt Y trước X, hoặc thiếu X hay Y) / tổng số cạnh vàng.
> Mẫu số là toàn bộ vàng, nên một lộ trình bỏ bớt khái niệm không thể làm Q6 đẹp lên.
>
> **M3 – gán mục theo ký tự:** M3 = số ký tự nội dung được gán đúng mục sâu nhất / tổng số ký tự nội dung.
>
> **Độ phủ khái niệm:** = số khái niệm vàng có trong lộ trình / số khái niệm vàng được sách dạy.
>
> **Đồng thuận giữa hai người gán** (mục 9.1): F1 = 2a / (2a + b + c); a là số mục cả hai cùng ghi, b và c là số mục chỉ một người ghi [7].
>
> **Tỉ lệ bằng chứng có thật:** = số câu định nghĩa và câu bằng chứng của hệ tìm thấy nguyên văn trong sách / tổng số câu hệ trích.
> Thước này cho biết người học bấm vào một khái niệm hay một quan hệ có được dẫn về đúng câu trong sách không, hay câu đó do mô hình tự viết.

Có hai lưu ý về thước:
- Q6 và M3 là thước nhóm tự định nghĩa vì đúng với điều sản phẩm cần, và văn liệu chưa có thước trùng khớp. Báo cáo ghi kèm thước gần nhất
  có trong văn liệu: P/R/F1 cạnh, và F1 tiêu đề kiểu cuộc thi trích cấu trúc sách ICDAR 2013 [1].
- Cách chấm khái niệm, so với danh sách do người đọc tài liệu lập, theo cách các nghiên cứu về trích cụm từ khoá và khái niệm trong giáo
  trình vẫn làm [3], [4]. Lỗi hợp nhất được đo thêm bằng B-cubed, một thước gom cụm chuẩn trong bài toán đồng tham chiếu [5]. Độ khớp giữa
  lộ trình và thứ tự mục lục, đo bằng Kendall τ [2], chỉ dùng để chẩn đoán, vì mục lục không phải đáp án của thứ tự học tốt nhất.
- Người gán chỉ ghi các cặp có quan hệ, nên một cạnh máy đưa ra mà vàng không có chưa chắc đã sai. Vì vậy độ chính xác được báo hai cách:
  so với vàng, là cận dưới; và theo phán mù của người gán trên các cạnh ngoài vàng (lớp G5), như cách cuộc thi TExEval-2 chấm quan hệ mới [8].

## 8. So với cái gì

Một con số đứng một mình khó nói tốt hay xấu. Hệ được so với ba nhóm hệ khác, mỗi nhóm trả lời một kiểu câu hỏi (Bảng 7). Mọi hệ xuất kết
quả theo cùng một định dạng và được chấm bằng cùng bộ thước.

Bảng 7. Các hệ được so

| Nhóm | Hệ | Trả lời câu hỏi |
|---|---|---|
| Cách làm đơn giản (baseline) | B1: lộ trình theo đúng thứ tự mục lục | "Lấy mục lục làm lộ trình thì kém hơn bao nhiêu?" |
| | B2: cạnh "X được nhắc trong câu định nghĩa Y, X dạy trước Y", không dùng mô hình | "Bước suy luận bằng mô hình có hơn một luật đơn giản không?" |
| | B3: khái niệm lấy từ tiêu đề mục | "Trích khái niệm bằng mô hình có hơn đọc tiêu đề không?" |
| | B4: gộp khái niệm chỉ khi trùng tên | "Bước hợp nhất có cần thiết không?" |
| | **B5: mô hình ngôn ngữ đọc thẳng** cả sách (hoặc từng chương) và trả luôn khái niệm, quan hệ, lộ trình | **"Vì sao cần mười bước mà không hỏi thẳng mô hình?"** |
| Bỏ hoặc thay một bộ phận (ablation) | đọc PDF bằng công cụ docling thay bộ đọc nhẹ (trên 3–4 cuốn, vì docling chậm) | "Bộ đọc nhanh có làm kém chất lượng không?" |
| | bước phụ của A8 dùng mô hình ngôn ngữ thay mô hình học máy (trên các cặp của 3 chương bốc, vì bản mô hình ngôn ngữ rất tốn) | "Thay mô hình ngôn ngữ bằng học máy để tiết kiệm thì mất bao nhiêu chất lượng?" |
| | bỏ các quan hệ do bước suy luận chính của A8 đề xuất; hoặc bỏ các quan hệ do bước phụ đề xuất | "Mỗi bước của A8 đóng góp bao nhiêu?" |
| | tắt luật R17 | "Luật giữ thứ tự sách giúp hay hại?" |
| | tắt gán vai trò vùng A2; tắt lọc trạng thái dạy A5 (nếu lịch còn chỗ) | "Hai bước lọc này có cần không?" |
| | ba mô hình học máy (nhận tiêu đề và nối dòng ở A1, bước phụ ở A8) thay bằng hồi quy logistic, cùng đặc trưng | "Vì sao chọn LightGBM mà không dùng mô hình tuyến tính đơn giản hơn?" |
| | bước phụ của A8 dùng cross-encoder (mô hình mã hoá đọc thẳng câu văn) thay LightGBM trên đặc trưng | "Đọc câu văn có hơn đặc trưng cấu trúc không, và tốn thêm bao nhiêu thời gian?" |
| Thay khâu bằng đáp án đúng (oracle) | A8 nhận khái niệm vàng thay vì khái niệm máy trích | "Lỗi ở A8 hay ở các khâu trước?" |
| | A10 nhận quan hệ vàng thay vì quan hệ máy suy ra | "Cách xếp lộ trình có tốt không, khi quan hệ đúng hoàn toàn?" |

Luật R17 cần giải thích thêm. Khi hệ suy ra "phải học X trước Y" mà sách lại dạy X sau Y, luật này không ép người học đổi thứ tự, vì quan
hệ ngược thứ tự sách thường là quan hệ trích sai. Nhưng trong giai đoạn phát triển, nhóm thấy ở một giáo trình triết học, sách đôi khi dùng một khái niệm trước rồi mới định nghĩa nó ở
chương sau. Thí nghiệm tắt R17 đo luật này giúp hay hại trên từng ngành.

Hai baseline quan trọng nhất là B1 và B5, vì chúng là hai cách "đơn giản" mà người nghe nghĩ tới đầu tiên:
- **B1, mục lục:** giáo trình thường định nghĩa trước khi dùng, nên lộ trình theo mục lục có thể đã khá tốt. Hệ phải cho thấy giá trị
  thêm, ví dụ chỉ ra đúng khái niệm nào cần học trước, hay chia module hợp lý hơn.
- **B5, hỏi thẳng mô hình:** cùng mô hình mà hệ dùng, nhưng không qua mười bước. Nếu B5 kém hơn hệ chính về độ đúng của quan hệ, hay hay
  trích câu không có trong sách, thì mười bước là cần thiết. Nếu B5 đạt gần bằng ở một số thước, nhóm báo đúng như vậy; khi đó giá trị của
  luồng nằm ở chỗ mọi khái niệm và quan hệ đều truy được về câu trong sách, kết quả ổn định hơn, và từng bước có thể thay bằng mô hình nhỏ
  không cần mô hình ngôn ngữ lớn.

Để phép so với B5 công bằng, nhóm làm ba việc:
- **B5 không phải hình nộm.** Lời nhắc của B5 được viết và thử trên tập phát triển, có định dạng đầu ra rõ ràng và yêu cầu trích câu nguyên
  văn, với công sức tương đương phần còn lại.
- **Thước so được khai trước khi có số.** Ngoài các thước chính, nhóm khai sẵn bốn thước phụ, đều là chỗ hai cách làm khác nhau về bản
  chất: tỉ lệ khái niệm không có trong sách; độ phủ khái niệm theo độ dài sách (một lời gọi có thể chạm giới hạn độ dài đầu ra); tỉ lệ một
  khái niệm bị đặt hai tên ở hai chương; độ ổn định qua nhiều lần chạy. Không thước nào được thêm sau khi thấy kết quả.
- **Biết trước trên tập phát triển.** B5 chạy trên tập phát triển trước khi hệ đóng băng. Nếu B5 tốt hơn, nhóm cải tiến hệ theo hướng kết
  hợp: giữ khả năng truy về câu trong sách, nhưng cho mô hình nhìn ngữ cảnh rộng hơn như B5. Bản được đánh giá trên tập thử là bản sau cải
  tiến.

**Ba mô hình học máy được chọn thế nào.** Pha A có ba mô hình LightGBM [24] nhỏ: nhận dòng tiêu đề và nối tiêu đề nhiều dòng ở A1, và bước phụ của
A8. Siêu tham số chính của LightGBM là số lá của mỗi cây (`num_leaves`), tức độ phức tạp của mô hình. Nhóm không chọn tay mà theo một quy trình
khai trước, chạy trên 16 cuốn của tập huấn luyện:
- **Để ra từng cuốn (LOBO-16):** mỗi lần học trên 15 cuốn, chấm trên cuốn thứ 16, lặp cho đủ 16 cuốn. Như vậy điểm đo được là điểm trên một cuốn
  mà mô hình chưa từng thấy, giống tình huống sản phẩm gặp một giáo trình mới.
- **Dừng sớm không nhìn cuốn đang chấm:** trong 15 cuốn học, 3 cuốn dành để quyết định khi nào dừng thêm cây (tối đa 5000 cây).
- **Lưới số lá** {7, 15, 31, 63, 127, 255}, chấm bằng AP trung bình trên 16 cuốn.
- **Luật một sai số chuẩn:** trong các cấu hình có điểm không kém cấu hình tốt nhất quá một sai số chuẩn, chọn cấu hình **đơn giản nhất**. Với
  16 cuốn, các cấu hình gần nhau thường chênh dưới mức nhiễu, nên chọn mô hình đơn giản hơn để ít học thuộc tập huấn luyện [23].

Mô hình được chọn rồi đóng băng trước khi chạy tập thử; số trên 16 cuốn chỉ là bằng chứng chọn mô hình, số báo cáo vẫn lấy trên 8 giáo trình thử.
Cùng quy trình áp cho hồi quy logistic, để trả lời "vì sao LightGBM". Riêng bước phụ A8 được so thêm với một cross-encoder (multilingual-e5 [25]) đọc thẳng câu
văn; vì học mô hình này cần GPU, nó được chấm trên 4 phần chia theo cuốn, và LightGBM cùng logistic được chấm lại trên đúng 4 phần đó.

Kết quả chọn (bằng chứng trên 16 cuốn huấn luyện, nhãn bạc; chưa phải số báo cáo):

Bảng 7b. Chọn mô hình học máy

| Mô hình | Cấu hình cũ (đặt tay) | Cấu hình chọn | LightGBM so với logistic (AP trung bình theo cuốn) |
|---|---|---|---|
| A1 nhận tiêu đề | 15 lá | 7 lá | +0,023, thắng 15/16 cuốn (p = 0,0005) |
| A1 nối dòng tiêu đề | 7 lá | 15 lá | +0,054, chưa vượt nhiễu (dữ liệu chỉ 787 dòng) |
| A8 bước phụ | 15 lá | 7 lá | +0,010, chưa vượt nhiễu (p = 0,077) |

Cross-encoder ở bước phụ A8 đạt AP 0,644, thấp hơn LightGBM (0,660) trên cùng 4 phần, và chạy chậm hơn khoảng 25.000 lần trên CPU (2,5 phút cho
1.000 cặp so với dưới 0,01 giây). Đọc thẳng câu văn không hơn đặc trưng cấu trúc trên dữ liệu này, nên sản phẩm giữ LightGBM.

[CHÈN HÌNH 5 – Biểu đồ đường: trục ngang là số lá (7 → 255, thang log), trục dọc là AP trung bình trên 16 cuốn, mỗi mô hình một đường, có thanh
sai số chuẩn; đường ngang mảnh đánh dấu "tốt nhất − 1 SE"; điểm được chọn tô đậm.]

Số của thí nghiệm oracle được báo trong một cột riêng, không đặt ngang số của hệ thật. Khi một khâu được cho đáp án đúng, bài toán của các
khâu sau dễ đi hẳn, nên hai con số không cùng điều kiện [15].

## 9. Vì sao con số đáng tin

### 9.1 Trần do con người đặt ra

Quan hệ tiên quyết không có một đáp án duy nhất. Hai người đọc cùng một chương cũng ghi khác nhau. Vì vậy nhóm đo **đồng thuận giữa hai
người gán** và dùng nó làm trần. Nếu hai sinh viên chỉ đồng ý với nhau ở mức 0,5, không thể đòi máy đạt 0,9.

Hệ được so với **từng** người gán theo cùng một thước F1, rồi đặt cạnh F1 giữa hai người. Đồng thuận được đo bằng F1, không bằng hệ số
kappa thường dùng. Lý do: người gán chỉ ghi các cặp có quan hệ, nên không có danh sách các cặp "không quan hệ" để tính kappa. Trong
trường hợp này F1 giữa hai người là thước được khuyến nghị [7].

### 9.2 Khoảng tin cậy theo cuốn

Các quan hệ trong cùng một cuốn không độc lập với nhau: chúng cùng văn phong, cùng người gán, cùng một lần chạy của hệ. Nếu coi mỗi quan hệ
là một mẫu độc lập thì khoảng tin cậy sẽ hẹp hơn thực tế; văn liệu cho thấy làm như vậy có thể đẩy tỉ lệ kết luận sai lên rất cao [12].
Vì vậy:
- mọi thước được tính theo từng cuốn, và báo cả bảng từng cuốn lẫn trung bình;
- khoảng tin cậy 95% được tính bằng **bootstrap phân cấp**: lấy mẫu lại các cuốn, rồi các chương trong cuốn, hàng nghìn lần, để xem con số
  dao động bao nhiêu [12];
- khi so hai hệ, dùng **kiểm định hoán vị ghép cặp**: hai hệ được so trên cùng từng cuốn, và chỉ hoán vị trong cùng một cuốn [10], [11],
  [22]. Kèm theo là đếm số cuốn mà hệ này hơn hệ kia.

Với 8 cuốn, phép đếm này chỉ đạt mức ý nghĩa 5% khi cả 8 cuốn cùng nghiêng về một hệ. Vì vậy kết luận chính dựa trên kiểm định hoán vị
phân tầng theo cuốn và chương; phép đếm theo cuốn chỉ để bổ sung và để người đọc thấy kết quả có nhất quán giữa các ngành không.

Chỉ ba phép so được kiểm định chính thức, chọn trước khi chấm, và p-value được hiệu chỉnh theo phương pháp Holm cho cả ba:
1. Q6 của hệ so với mục lục (B1);
2. F1 quan hệ tiên quyết của hệ so với mô hình đọc thẳng (B5);
3. tỉ lệ bằng chứng có thật của hệ so với B5.

Các so sánh còn lại chỉ mô tả, để tránh việc "thử đủ phép, thế nào cũng có một phép đạt".

[CHÈN HÌNH 3 – Biểu đồ điểm theo cuốn (forest plot). Trục dọc: 8 cuốn, ghi tên chủ đề. Trục ngang: F1 cạnh tiên quyết. Mỗi cuốn một chấm
cho hệ chính và một chấm cho baseline B5, kèm thanh khoảng tin cậy. Dòng cuối: trung bình chung kèm khoảng tin cậy bootstrap phân cấp. Vẽ
từ số liệu sau lượt chạy.]

Hình 3. F1 cạnh tiên quyết theo từng cuốn

### 9.3 Độ ổn định trước nhiễu

Mô hình ngôn ngữ có thể cho kết quả khác nhau chỉ vì thứ tự thông tin trong lời nhắc thay đổi, dù nghĩa không đổi [13], [14]. Ở các lần thử
trước, chỉ đổi thứ tự ngữ cảnh đã làm một thước dao động tới ±0,15. Vì vậy bước suy luận chính được chạy **5 lần** trên mỗi cuốn, mỗi lần
xáo thứ tự ngữ cảnh. Báo cáo ghi trung bình, khoảng dao động, và tỉ lệ cạnh giữ nguyên qua 5 lần. Chênh lệch nhỏ hơn dải dao động này thì
không được kết luận là hơn.

### 9.4 Chốt luật chơi trước khi nhìn số

Có bốn biện pháp chống việc chỉnh luật sau khi đã thấy kết quả:
- **Giao thức viết trước** [20]: thước chính, cách ghép, cách tính khoảng tin cậy, các phép kiểm định được ghi vào một tệp có ngày và mã
  băm trước khi chạy tập thử.
- **Đóng băng:** vàng chốt ngày 06/11; mã nguồn và cấu hình hệ chốt ngày 07/11; tập thử chỉ chạy sau đó, đúng một lần.
- **Mù:** người gán không thấy đầu ra của hệ; người phán không biết đầu ra thuộc hệ nào. Phiếu phán có trộn câu đối chứng (cạnh vàng, cặp
  ngẫu nhiên) để đo độ khắt khe của chính người phán. Phần chấm lộ trình theo các khuyến nghị đánh giá người của [9]: hai người phán mọi
  mục, thang 7 mức có lời neo, xáo thứ tự trình bày, và báo như một nghiên cứu thăm dò.
- **Minh bạch:** mọi thay đổi sau khi thấy số được báo riêng là phân tích hậu kiểm.

## 10. Lỗi đến từ đâu

Một con số F1 cuối cùng không cho biết nên cải tiến khâu nào. Nhóm dùng hai cách để chỉ ra nguồn gốc lỗi.

**Truy lỗi theo khâu.** Với mỗi quan hệ tiên quyết trong vàng mà lộ trình làm sai, nhóm lần theo luồng và dừng ở **khâu đầu tiên** làm hỏng
nó [16]. Bảng 8 liệt kê các nguyên nhân theo thứ tự lần.

Bảng 8. Thứ tự truy nguyên nhân lỗi

| Thứ tự | Nguyên nhân | Khâu |
|---|---|---|
| 1 | câu định nghĩa nằm trong mục bị cắt sai hoặc bị gán nhầm vai trò | A1, A2 |
| 2 | máy không trích được khái niệm | A3 |
| 3 | khái niệm bị gộp nhầm hoặc bị tách đôi | A4 |
| 4 | máy cho rằng khái niệm không được dạy, nên bỏ khỏi lộ trình | A5 |
| 5 | cặp khái niệm không được đưa vào để xét | A6/A7 |
| 6 | bước suy luận không đề xuất quan hệ | A8 |
| 7 | quan hệ bị luật R17 làm mềm, hoặc bị xếp sai | A9/A10 |

**Thay khâu bằng đáp án đúng (oracle).** Như đã nói ở mục 8: nếu A8 chạy trên khái niệm vàng mà vẫn thiếu nhiều quan hệ, A8 là nút thắt;
nếu lúc đó quan hệ gần đủ, lỗi nằm ở các khâu trước.

[CHÈN HÌNH 4 – Biểu đồ thác nước. Cột đầu: tổng số quan hệ vàng. Mỗi cột tiếp theo là số quan hệ mất ở một khâu theo Bảng 8. Cột cuối: số
quan hệ lộ trình làm đúng. Tô màu theo khâu, cùng màu với Hình 1. Vẽ từ số liệu sau lượt chạy.]

Hình 4. Quan hệ tiên quyết bị mất qua từng khâu

## 11. Chi phí và thời gian

Đây là sản phẩm phục vụ người dùng, nên chi phí được đo ngang hàng với chất lượng [17], [18]. Với mỗi cuốn, nhóm ghi:
- số phút từ lúc nhận PDF tới lúc có lộ trình, chia theo khâu;
- số tiền gọi mô hình (USD), chia theo khâu;
- số lời gọi mô hình và số token;
- phút trên một trang và USD trên một trang, để so được giữa các cuốn dài ngắn khác nhau.

Sách thử là giáo trình đầy đủ, nên các con số trên chính là chi phí của sản phẩm khi xử lý một giáo trình thật.

Trong đợt đánh giá, hệ gọi mô hình qua nền tảng Vertex AI. Trên nền tảng này, mỗi lần tính embedding phải chờ khoảng 11–16 giây vì giới hạn
lưu lượng, trong khi bản sản phẩm dùng Gemini Developer API chỉ mất dưới một giây. Vì vậy thời gian được báo hai số: tổng, và tổng trừ phần
chờ embedding.

## 12. Tính trung thực và tái lập

Nhóm theo danh mục báo cáo nghiên cứu có trách nhiệm của ACL [21]. Cụ thể:
- **Phiếu mô tả bộ dữ liệu** theo mẫu Datasheets for Datasets [19]: nguồn sách, cách chọn, người gán, cách gán, giới hạn.
- **Khai việc dùng AI:** trợ lý AI lập bản nháp cấu trúc mục (G1, G2) để sinh viên duyệt; trợ lý AI ghép một phần khái niệm (mục 6), có
  người kiểm 20%.
- **Tái lập:** một lệnh chạy lại từ PDF tới bảng kết quả; mọi tệp đầu vào và vàng có mã băm SHA-256; ghi phiên bản mô hình và ngày chạy.

## 13. Kết quả

Mục này sẽ điền sau lượt chạy tập thử (07–09/11). Các bảng dưới là khung.

Bảng 9. Kết quả đầu-cuối trên 8 giáo trình (khoảng tin cậy 95% trong ngoặc)

| Hệ | Độ phủ khái niệm | Q6 (thấp là tốt) | F1 cạnh tiên quyết | Bằng chứng có thật | Phút/cuốn | USD/cuốn |
|---|---|---|---|---|---|---|
| Hệ chính | — | — | — | — | — | — |
| B1 mục lục | — | — | — | — | — | — |
| B2 luật đơn giản | — | — | — | — | — | — |
| B5 mô hình đọc thẳng | — | — | — | — | — | — |
| Trần người (F1 giữa hai sinh viên) | — | — | — | — | — | — |

Bảng 10. Kết quả từng khâu

| Khâu | Thước chính | Hệ chính | Trần người |
|---|---|---|---|
| A1 | M3 | — | — |
| A2 | độ phủ vai trò "nội dung" | — | — |
| A3 | độ phủ khái niệm | — | — |
| A4 | tỉ lệ tách / gộp nhầm | — | — |
| A5 | câu định nghĩa đúng; độ chính xác trạng thái | — | — |
| A8 | F1 cạnh | — | — |
| A10 | Q6 | — | — |

Bảng 11. Thí nghiệm bỏ hoặc thay bộ phận

| Thí nghiệm | Thay đổi so với hệ chính | Chi phí thay đổi |
|---|---|---|
| docling thay bộ đọc nhẹ (3–4 cuốn) | — | — |
| bước phụ A8 bằng mô hình ngôn ngữ (cặp của 3 chương bốc) | — | — |
| bỏ quan hệ của bước suy luận chính | — | — |
| bỏ quan hệ của bước phụ | — | — |
| tắt R17 | — | — |
| tắt gán vai trò vùng A2 (nếu chạy) | — | — |
| tắt lọc trạng thái dạy A5 (nếu chạy) | — | — |
| oracle A8 (khái niệm vàng) | — | — |
| oracle A10 (quan hệ vàng) | — | — |

Bảng 12. Đánh giá của người học (sinh viên chấm lộ trình, mù tên hệ)

| Tiêu chí | Hệ chính | B1 mục lục |
|---|---|---|
| Điểm rubric trung bình (thang 7) | — | — |
| Tỉ lệ được chọn khi so cặp | — | — |

## 14. Giới hạn

Nhóm nêu trước các giới hạn sau:
- **Người gán là sinh viên, không phải chuyên gia.** Bù lại, giao thức yêu cầu bám văn bản, và mọi phiếu đều có câu kiểm và câu đối chứng.
- **Mỗi chủ đề chỉ có một cuốn.** Kết quả cho thấy hệ hoạt động trên nhiều ngành, nhưng không đủ để kết luận riêng cho từng ngành.
- **Khái niệm và quan hệ tiên quyết chỉ được gán trên 3 chương mỗi cuốn**, không phải cả cuốn, vì gán cả một giáo trình dài vượt sức người
  gán trong thời gian có hạn. Cấu trúc mục và vai trò vùng vẫn được gán cho cả cuốn.
- **Bước ghép khái niệm có phần phán tay.** Nhóm giảm rủi ro bằng luật viết trước, nhật ký và kiểm 20%.
- **Kết quả có điều kiện trên mô hình và nền tảng đã dùng** (gemini-3.1-flash-lite qua Vertex AI, tháng 11/2026).

## 15. Lịch thực hiện

Bảng 13. Lịch đánh giá

| Thời gian | Việc |
|---|---|
| 26–28/10 | viết giao thức và hướng dẫn gán; gom sách |
| 29/10–02/11 | dựng công cụ chấm; gán thử; gán tập phát triển |
| 31/10–06/11 | sinh viên gán tập thử; chốt vàng ngày 06/11 |
| 01–06/11 | chạy B5 và đánh giá trên tập phát triển; cải tiến hệ |
| 07/11 | đóng băng hệ và giao thức |
| 07–09/11 | chạy tập thử |
| 09–10/11 | sinh viên phán mù đầu ra |
| 10–13/11 | phân tích, viết báo cáo |
| 14/11 | bảo vệ |

## Tài liệu tham khảo

[1] A. Doucet, G. Kazai, S. Colutto, and G. Mühlberger, "Overview of the ICDAR 2013 Competition on Book Structure Extraction," in *Proc.
12th Int. Conf. Document Analysis and Recognition (ICDAR)*, Washington, DC, USA, 2013. [Online]. Available:
http://www.cs.helsinki.fi/u/doucet/papers/ICDAR2013.pdf

[2] M. Lapata, "Automatic Evaluation of Information Ordering: Kendall's Tau," *Computational Linguistics*, vol. 32, no. 4, pp. 471–484,
2006, doi: 10.1162/coli.2006.32.4.471.

[3] S. N. Kim, O. Medelyan, M.-Y. Kan, and T. Baldwin, "SemEval-2010 Task 5: Automatic Keyphrase Extraction from Scientific Articles," in
*Proc. 5th Int. Workshop on Semantic Evaluation (SemEval)*, 2010, pp. 21–26. [Online]. Available: https://aclanthology.org/S10-1004

[4] M. Wang, H. Chau, K. Thaker, P. Brusilovsky, and D. He, "Concept Annotation for Intelligent Textbooks," arXiv:2005.11422, 2020.
[Online]. Available: https://arxiv.org/abs/2005.11422

[5] N. S. Moosavi and M. Strube, "Which Coreference Evaluation Metric Do You Trust? A Proposal for a Link-based Entity Aware Metric," in
*Proc. 54th ACL*, 2016, pp. 632–642. [Online]. Available: https://aclanthology.org/P16-1060

[6] C. Alzetta, I. Torre, and F. Koceva, "Annotation Protocol for Textbook Enrichment with Prerequisite Knowledge Graph," *Technology,
Knowledge and Learning*, vol. 29, pp. 197–228, 2024, doi: 10.1007/s10758-023-09682-6.

[7] G. Hripcsak and A. S. Rothschild, "Agreement, the F-Measure, and Reliability in Information Retrieval," *J. Am. Med. Inform. Assoc.*,
vol. 12, no. 3, pp. 296–298, 2005, doi: 10.1197/jamia.M1733.

[8] G. Bordea, E. Lefever, and P. Buitelaar, "SemEval-2016 Task 13: Taxonomy Extraction Evaluation (TExEval-2)," in *Proc. 10th Int.
Workshop on Semantic Evaluation (SemEval)*, 2016. [Online]. Available: https://aclanthology.org/S16-1168

[9] C. van der Lee, A. Gatt, E. van Miltenburg, S. Wubben, and E. Krahmer, "Best practices for the human evaluation of automatically
generated text," in *Proc. 12th Int. Conf. Natural Language Generation (INLG)*, 2019. [Online]. Available:
https://aclanthology.org/W19-8643

[10] P. Koehn, "Statistical Significance Tests for Machine Translation Evaluation," in *Proc. EMNLP*, 2004. [Online]. Available:
https://aclanthology.org/W04-3250

[11] R. Dror, G. Baumer, S. Shlomov, and R. Reichart, "The Hitchhiker's Guide to Testing Statistical Significance in Natural Language
Processing," in *Proc. 56th ACL*, 2018. [Online]. Available: https://aclanthology.org/P18-1128

[12] V. Saravanan, G. J. Berman, and S. J. Sober, "Application of the hierarchical bootstrap to multi-level data in neuroscience,"
arXiv:2007.07797, 2020. [Online]. Available: https://arxiv.org/abs/2007.07797

[13] B. Atil *et al.*, "Non-Determinism of 'Deterministic' LLM Settings," arXiv:2408.04667, 2024. [Online]. Available:
https://arxiv.org/abs/2408.04667

[14] M. Sclar, Y. Choi, Y. Tsvetkov, and A. Suhr, "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I
learned to start worrying about prompt formatting," in *Proc. ICLR*, 2024. [Online]. Available: https://arxiv.org/abs/2310.11324

[15] V. Stoyanov, N. Gilbert, C. Cardie, and E. Riloff, "Conundrums in Noun Phrase Coreference Resolution: Making Sense of the
State-of-the-Art," in *Proc. ACL-IJCNLP*, 2009. [Online]. Available: https://aclanthology.org/P09-1074

[16] J. K. Kummerfeld and D. Klein, "Error-Driven Analysis of Challenges in Coreference Resolution," in *Proc. EMNLP*, 2013. [Online].
Available: https://aclanthology.org/D13-1027

[17] J. Dodge, S. Gururangan, D. Card, R. Schwartz, and N. A. Smith, "Show Your Work: Improved Reporting of Experimental Results," in
*Proc. EMNLP-IJCNLP*, 2019. [Online]. Available: https://aclanthology.org/D19-1224

[18] R. Schwartz, J. Dodge, N. A. Smith, and O. Etzioni, "Green AI," arXiv:1907.10597, 2019. [Online]. Available:
https://arxiv.org/abs/1907.10597

[19] T. Gebru *et al.*, "Datasheets for Datasets," arXiv:1803.09010, 2018. [Online]. Available: https://arxiv.org/abs/1803.09010

[20] E. van Miltenburg, C. van der Lee, and E. Krahmer, "Preregistering NLP research," in *Proc. NAACL-HLT*, 2021. [Online]. Available:
https://aclanthology.org/2021.naacl-main.51

[21] ACL Rolling Review, "Responsible NLP Research Checklist." [Online]. Available: https://aclrollingreview.org/responsibleNLPresearch/
(truy cập 2026-10-26)

[22] A. Yeh, "More accurate tests for the statistical significance of result differences," in *Proc. COLING*, 2000. [Online].
Available: https://aclanthology.org/C00-2137

[23] T. Hastie, R. Tibshirani, and J. Friedman, *The Elements of Statistical Learning*, 2nd ed. New York, NY, USA: Springer, 2009, sec. 7.10.
[Online]. Available: https://hastie.su.domains/ElemStatLearn/

[24] G. Ke *et al.*, "LightGBM: A highly efficient gradient boosting decision tree," in *Proc. NeurIPS*, 2017. [Online]. Available:
https://papers.nips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree

[25] L. Wang *et al.*, "Multilingual E5 text embeddings: A technical report," arXiv:2402.05672, 2024. [Online]. Available:
https://arxiv.org/abs/2402.05672
