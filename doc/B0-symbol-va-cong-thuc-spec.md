# Spec — Chữ Hy Lạp, công thức, và một luật lọc tiêu đề không cần biết ngôn ngữ

> Spec triển khai, 2026-08-21. Sinh từ phiên grilling cùng ngày (Q1–Q4) sau báo cáo
> [F30–F33](../feedback/F14-xstk-chat-luong-chunk.md) trên tài liệu thứ hai.
> Định danh: [ADR 0001](./adr/0001-dinh-danh-tat-dinh.md) · [ADR 0002](./adr/0002-anh-va-tham-chieu-ngoai-dinh-danh-chunk.md)
> — đợt này **mở rộng** ADR 0002 sang công thức, không lật nó. Thuật ngữ: [CONTEXT.md](../CONTEXT.md)

## Problem Statement

Tài liệu thứ hai đi qua đường ống là một giáo trình xác suất thống kê, 59 trang. Mọi bất biến đều xanh, bảng
hoạt động đúng ngay lần đầu gặp dữ liệu thật, phân bố token chuẩn. **Cơ chế chạy tốt. Nội dung thì hỏng.**

### Chữ Hy Lạp của thống kê bị hỏng mã

**653 ký tự vùng dùng riêng nằm trong 80 trên 132 chunk — 61%.**

```
'ký hiệu là  và phương sai D(X) là phương sai tổng thể, ký hiệu là '
'X  N(  ;  2 )'
'| | n |  x |  x 2 |'
```

PDF nhúng chữ Hy Lạp bằng font Symbol, một font ánh xạ mã Latin sang ký tự Hy Lạp. Khi trích xuất, các mã đó
rơi vào vùng `U+F000–U+F0FF` thay vì được đưa về Unicode thật. `U+F061` chính là `0xF000` cộng mã chữ `a`, mà
`a` trong bảng Symbol là **α**.

Mười ký tự hay gặp nhất là **α** (149 lần), **→** (109), **μ** (90), **χ** (67), **σ** (43), **θ** (29),
**ε** (18), **∼**, **∈**, **≈**. Đó là toàn bộ bảng chữ cái của thống kê.

Đây **không phải mất chữ mà là hỏng chữ** — tệ hơn, vì không dấu vết nào báo. Truy vấn *"phương sai σ²"* không
khớp được với chunk chứa ký tự hỏng; bước trích khái niệm nhìn thấy rác thay vì tên khái niệm; và **bảng cũng
dính** — `Σ` trong dòng tiêu đề cột bị hỏng.

Với tài liệu đầu tiên con số này là **không**, nên bốn đợt vá trước không có cơ hội gặp nó.

### 264 công thức bị bỏ vì đọc nhầm trường

Thư viện parse trả về 264 mục nhãn công thức — 27% tài liệu — và adapter bỏ sạch vì trường văn bản rỗng.

Nội dung **chưa bao giờ mất**. Nó nằm ở một trường khác:

```
.text khác rỗng : 0/264
.orig khác rỗng : 263/264

ví dụ:  .text = ''
        .orig = 'X x1 x2 .  .  . xk ni n1 n2 .  .  . nk'
```

Đo trên 170 mục của tài liệu đầu: hai trường **giống hệt nhau ở 125 mục**, khác nhau ở 35 — và chỗ khác là
trường thô còn giữ dấu liệt kê mà trường đã dọn đã gỡ đi. Nói cách khác, **trường thô là chuỗi trích xuất
nguyên bản, trường kia là bản thư viện đã dọn**. Với công thức, thư viện xoá trắng bản đã dọn nhưng giữ bản thô.

Đây là **đọc nhầm trường**, cùng loại với lỗi thông báo lỗi ảnh lọt vào nội dung ở đợt hình: gọi đúng API nhưng
lấy sai thuộc tính. Và luật *"văn bản rỗng thì bỏ node"* áp cho **mọi** loại — công thức chỉ là loại đầu tiên
ta bắt gặp với số lượng đủ lớn để thấy.

### Nhưng nội dung thô đó không đọc được như văn xuôi

```
'1 2 ... n x x x x n + + + ='
'2 2 2 2 1 2 ( ) ( ) ... ( ) n x x x x x x s − + − + + − ='
```

Dòng sau lẽ ra là công thức phương sai mẫu. Trích xuất PDF đọc glyph theo thứ tự lưu trữ, nên **toán tử bị
tách khỏi toán hạng và dồn về cuối** — công thức hai chiều bị bẹp thành một chiều.

Tổng cộng **8.280 token**, tức **+28%** so với corpus hiện tại. Đưa thẳng vào phần văn bản của chunk là bơm
28% cháo chữ vào thứ sẽ được embed.

### Cảnh báo tự đánh bại chính nó

Danh sách lý do cảnh báo có **264 dòng giống hệt nhau**. Hai cảnh báo **chú thích mồ côi** — loại lỗi đợt trước
bỏ công vá — nằm lẫn giữa đống đó và không ai nhìn thấy.

### Và bộ lọc tiêu đề giả bị vượt qua bằng hai đường

**23 trên 67 section thật ra là gạch đầu dòng.** Dấu chấm tròn của font Symbol rơi vào vùng dùng riêng, nên
luật *"ký tự đầu là chữ thường"* không nhận ra — ký tự đầu là một mã hỏng, không phải chữ thường.

Và cụm nối `Trong đó:` quay lại — đúng cụm đã vá ở đợt hai, nhưng lần này **viết hoa** nên lọt qua luật chữ
thường.

## Solution

**Tra bảng Symbol về Unicode ở adapter**, cùng chỗ với việc gộp glyph lặp — cùng bản chất: hiện vật của trích
xuất PDF, không phải chuẩn hoá ngôn ngữ. Áp vô điều kiện cho nguồn PDF, vì ký tự vùng dùng riêng **không có
nghĩa hợp lệ nào** trong văn bản đã trích: để nguyên là sai chắc chắn, tra bảng là đúng bất cứ khi nào font là
Symbol.

Nhưng **ghi lại**: số ký tự đã ánh xạ vào thống kê parse, và một cảnh báo khi còn ký tự vùng dùng riêng không
tra được. Ta **không biết font** — thư viện parse không cho biết — nên đây là một phỏng đoán có căn cứ, và một
phỏng đoán phải để lại dấu vết.

**Đọc trường thô khi trường đã dọn rỗng**, cho **mọi** loại node. Lỗi nằm trong một luật chung; vá riêng một
nhãn là dựng lại đúng cái bẫy đó cho nhãn tiếp theo.

**Công thức quay lại nhưng nội dung thô không vào phần văn bản.** Đây chính là bài toán đã giải cho hình ở đợt
trước: nội dung tồn tại nhưng không phải chữ đọc được, nên **dấu vết vào văn bản, nội dung ra chỗ khác**. Phần
văn bản nhận một chuỗi cố định; nội dung thô ở lại cây parse; chunk trỏ về bằng một tham chiếu có định danh và
vị trí, đối xứng từng điểm với tham chiếu hình và tham chiếu bảng.

**Gom cảnh báo trùng lặp thành một dòng kèm số đếm**, để hai cảnh báo đang bị chôn nổi lên.

**Và bộ lọc tiêu đề nhận thêm một luật không cần biết ngôn ngữ nào:** một tiêu đề ứng viên **không đánh số** mà
văn bản của nó xuất hiện **từ hai lần trở lên** trong các khối thân bài của cùng tài liệu thì là cụm nối, không
phải tiêu đề. Luật này tự hiệu chỉnh theo từng tài liệu, dùng chính bằng chứng trong tài liệu đó — thay vì một
danh sách cụm từ tiếng Việt phải nuôi bằng tay.

## User Stories

**Chữ Hy Lạp đọc được**

1. Là người đọc giáo trình, tôi muốn thấy `σ` chứ không phải một ô vuông hỏng mã, vì đó là tên của khái niệm
   tôi đang học.
2. Là người dùng bước truy hồi, tôi muốn truy vấn *"phương sai σ²"* khớp được với chunk nói về nó.
3. Là người dựng lộ trình, tôi muốn `X ∼ N(μ; σ²)` hiện đúng, vì đó là ký hiệu trung tâm nhất của thống kê.
4. Là người dựng lộ trình, tôi muốn dòng tiêu đề cột của bảng cũng được sửa, vì `Σ` trong đó cũng hỏng.
5. Là người vận hành, tôi muốn biết **bao nhiêu** ký tự đã được ánh xạ, để đánh giá mức độ tin cậy của kết quả.
6. Là người vận hành, tôi muốn được **cảnh báo** khi còn ký tự vùng dùng riêng không tra được, vì đó là dấu
   hiệu tài liệu dùng một font khác mà bảng của ta chưa biết.
7. Là người ingest tài liệu DOCX, tôi muốn việc tra bảng **không** áp cho nguồn của mình, vì lỗi này chỉ có ở PDF.

**Công thức quay lại**

8. Là người dựng lộ trình, tôi muốn node có trường đã dọn rỗng nhưng trường thô có chữ **vẫn được giữ**, thay
   vì bị bỏ im lặng.
9. Là người dựng lộ trình, tôi muốn luật đó áp cho **mọi** loại node, không riêng công thức.
10. Là người đọc kết quả, tôi muốn chỗ có công thức để lại một **dấu vết đọc được** trong văn bản, để biết chỗ
    đó có công thức chứ không phải một khoảng trống.
11. Là người dùng bước truy hồi, tôi muốn nội dung thô của công thức **không** nằm trong phần được embed, vì
    nó là chuỗi ký hiệu bị xáo trộn và sẽ làm loãng vector.
12. Là người phát triển bước trích khái niệm, tôi muốn truy được nội dung thô của công thức khi cần, qua một
    tham chiếu ổn định.
13. Là người phát triển bước trích khái niệm, tôi muốn mỗi công thức có **định danh băm theo nội dung**, để
    dựng được node loại công thức khoá theo định danh đó.
14. Là người xây giao diện, tôi muốn tham chiếu công thức kèm **vị trí ký tự**, để hiện công thức đúng chỗ.
15. Là người dựng lộ trình, tôi muốn tham chiếu công thức **không** tham gia khoá băm định danh chunk, cùng lý
    do đã áp cho hình và bảng.
16. Là người dùng bước truy hồi, tôi muốn công thức **gộp được** vào đoạn văn quanh nó, để không sinh ra hàng
    trăm chunk tí hon.

**Cảnh báo đọc được**

17. Là người vận hành, tôi muốn cảnh báo cùng loại được **gom thành một dòng kèm số đếm**, để danh sách còn đọc
    được khi một tài liệu có hàng trăm sự kiện cùng loại.
18. Là người vận hành, tôi muốn một cảnh báo hiếm **không bị chôn** giữa hàng trăm cảnh báo thường gặp.

**Lọc tiêu đề không cần biết ngôn ngữ**

19. Là người dựng lộ trình, tôi muốn cụm nối như `Trong đó:` bị loại **dù nó viết hoa**, vì luật cũ chỉ bắt chữ
    thường.
20. Là người dựng lộ trình, tôi muốn luật lọc **không dựa vào một danh sách cụm từ tiếng Việt**, vì hệ thống
    phục vụ mọi ngôn ngữ.
21. Là người dựng lộ trình, tôi muốn luật lọc chạy được với chữ viết **không có khái niệm hoa/thường** như chữ
    Hán hay Ả Rập.
22. Là người dựng lộ trình, tôi muốn tiêu đề **có đánh số** được miễn trừ khỏi luật này, vì đánh số vốn đã là
    bằng chứng mạnh nhất rằng đây là tiêu đề.
23. Là người dựng lộ trình, tôi muốn gạch đầu dòng **không** trở thành section, kể cả khi dấu liệt kê của nó
    đến từ một font ký hiệu.

**Phiên bản và tính liên tục**

24. Là người vận hành, tôi muốn đợt này bump phiên bản adapter và phiên bản thuật toán, mỗi thứ một lần.
25. Là người vận hành, tôi muốn biết trước rằng **cả hai tài liệu** sẽ đổi định danh chunk, và đổi bao nhiêu.

## Implementation Decisions

### Bảng tra Symbol, đặt ở adapter

Bảng ánh xạ **Adobe Symbol** — một chuẩn công bố công khai, khoảng 190 mục — từ vùng `U+F000–U+F0FF` về Unicode
thật. Đặt ở adapter parse, cùng chỗ với việc gộp glyph lặp, và **chỉ áp cho nguồn PDF**.

Áp **vô điều kiện**, không gắn điều kiện *"tài liệu có vẻ là toán học"*: ký tự vùng dùng riêng không có nghĩa
hợp lệ nào trong văn bản đã trích, nên để nguyên là sai chắc chắn. Thêm một suy đoán nữa chỉ thêm một chỗ có
thể sai theo cả hai chiều.

**Nhưng phải ghi lại, vì đây là một phỏng đoán.** Thư viện parse **không cho biết font** — đã kiểm: đối tượng
mục không có thuộc tính nào về font hay glyph, và khối xuất xứ chỉ có khung, khoảng ký tự và số trang. Nên ta
đang đoán rằng font là Symbol. Bằng chứng ủng hộ mạnh — ba mẫu giải mã đọc lại đúng hoàn hảo — nhưng là bằng
chứng từ **một** tài liệu.

Do đó: **số ký tự đã ánh xạ vào thống kê parse**, và **một cảnh báo khi còn ký tự vùng dùng riêng không tra
được**. Tài liệu dùng font khác sẽ lộ ra ngay thay vì lại im lặng.

### Đọc trường thô khi trường đã dọn rỗng

Luật *"văn bản rỗng thì bỏ node"* đổi thành: thử trường đã dọn, rồi trường thô, **chỉ bỏ khi cả hai rỗng**.
Áp cho **mọi** loại node.

Thứ tự này quan trọng: trường đã dọn được ưu tiên vì nó là bản thư viện đã xử lý — với node thường hai trường
giống nhau, còn chỗ khác nhau thì bản đã dọn tốt hơn (nó đã gỡ dấu liệt kê thừa).

### Công thức: dấu vết vào văn bản, nội dung ra chỗ khác

Node công thức được giữ, và:

- Phần **văn bản** nhận một **chuỗi cố định** báo rằng đây là một công thức. Chuỗi này không chứa định danh và
  không chứa nội dung thô — cùng lý do đã áp cho hình không có chú thích: nếu định danh nằm trong văn bản thì
  cấu hình trích xuất chui vào khoá băm chunk qua đường vòng.
- **Nội dung thô ở lại node** trong cây parse, dưới một trường riêng.
- **Định danh công thức** băm theo nội dung thô, cùng nguyên tắc với định danh hình và định danh bảng.

Chunk mang thêm một danh sách tham chiếu công thức, hình dạng **đối xứng từng điểm** với hai loại tham chiếu
đã có: định danh cộng vị trí ký tự, dùng chung hệ toạ độ với vị trí ký tự sẵn có của chunk.

**Tham chiếu công thức không tham gia khoá băm định danh chunk.** Mở rộng của quyết định trung tâm trong ADR
0002, không phải quyết định mới — ADR đó phải được cập nhật để nói "hình, bảng và công thức".

### Công thức gộp được như văn xuôi

Loại khối `formula` vào tập loại được phép gộp. Công thức trong tài liệu này nằm **xen kẽ** mạch văn — 264 mục
xen giữa 429 khối văn bản và 172 mục danh sách — chứ không phải phụ lục tách rời. Để chúng đứng một mình sẽ
sinh **263 chunk tí hon**, đúng vấn đề đã mất một đợt để vá.

### Gom cảnh báo trùng lặp

Cảnh báo cùng loại được gom thành **một dòng kèm số đếm**. Với tài liệu này, 264 dòng giống hệt nhau trở thành
một dòng, và hai cảnh báo chú thích mồ côi lập tức nổi lên.

Việc gom nên theo **loại** cảnh báo chứ không theo toàn bộ chuỗi, để cảnh báo có kèm nguyên văn — như cảnh báo
chú thích mồ côi — vẫn giữ được nguyên văn của từng ca.

### Luật lọc tiêu đề mới, không cần biết ngôn ngữ

Một tiêu đề ứng viên **không đánh số** mà văn bản của nó xuất hiện **từ hai lần trở lên** trong các khối thân
bài của cùng tài liệu ⇒ là cụm nối, hạ xuống khối văn bản thường.

Đo trên cả hai tài liệu, ngưỡng hai tách hoàn hảo:

| Tiêu đề | Lần xuất hiện trong thân bài | Thật ra là |
|---|---:|---|
| `Chú ý .` | **11** | cụm nối |
| `Trong đó:` | **10** | cụm nối |
| `trong đó:` | **4** | cụm nối |
| `Làm sạch dữ liệu` | 1 | **tiêu đề thật** |
| `Giải` | 1 | **tiêu đề thật** |
| `TẬP THỂ TÁC GIẢ:` · `a) Chọn kiểu mô hình:` · các mục đánh số | **0** | tiêu đề thật |

Luật này **không cần biết ngôn ngữ nào**, không cần khái niệm hoa/thường nên chạy được với chữ Hán, Ả Rập,
Thái, và **tự hiệu chỉnh theo từng tài liệu**.

**Rủi ro đã biết và cách giảm:** một tiêu đề ngắn trùng với từ thông dụng sẽ bị oan — ví dụ một mục tên
`Overfitting` mà thân bài nhắc từ đó nhiều lần. Giảm bằng cách **miễn trừ hoàn toàn tiêu đề có đánh số**, đúng
quy ước đã dùng ở mọi luật khác trong bộ lọc. Trên hai tài liệu hiện có, ca oan không xảy ra.

Luật cũ — kết thúc bằng dấu hai chấm, không đánh số, ký tự đầu là chữ thường — **được giữ**. Hai luật độc lập
và cộng dồn.

### Gạch đầu dòng không phải tiêu đề

Sau khi tra bảng Symbol, tiêu đề bắt đầu bằng một **dấu liệt kê** — chấm tròn, ô vuông, gạch ngang, và các dấu
tương đương trong khối ký hiệu Unicode — thì không phải tiêu đề, hạ xuống khối văn bản thường.

Luật này **phải chạy sau** khi tra bảng Symbol, vì trước đó dấu chấm tròn còn là một mã vùng dùng riêng mà
không luật nào nhận ra.

### Phiên bản

| Tăng cái gì | Vì sao |
|---|---|
| Phiên bản adapter | tra bảng Symbol, đọc trường thô, giữ node công thức, tính định danh công thức |
| Phiên bản thuật toán cắt | chunk có thêm trường tham chiếu công thức; văn bản có thêm chuỗi cố định; luật lọc tiêu đề đổi |

**Đây là lần đầu tiên cả hai tài liệu đều đổi định danh chunk.** Nhưng mức độ rất khác nhau, và cả hai đều kiểm
được:

- **Tài liệu thứ hai**: đổi gần như toàn bộ — 653 ký tự được sửa và 263 node quay lại.
- **Tài liệu thứ nhất**: nó có **không** ký tự vùng dùng riêng và không tiêu đề nào lặp từ hai lần trở lên. Nên
  chỉ **hai nhóm chunk** được phép đổi định danh: nhóm chứa **một công thức được khôi phục**, và nhóm chứa
  **dấu hiệu hình không có chú thích** — vì dấu hiệu đó đổi sang dạng trung tính ngôn ngữ. Phần còn lại phải
  **giữ nguyên**. Nếu đổi nhiều hơn thế thì có gì đó ngoài dự kiến.

### Dấu hiệu trong văn bản không mang ngôn ngữ nào

Chuỗi cố định đánh dấu hình không có chú thích hiện **viết bằng tiếng Việt**. Đợt này thêm một chuỗi tương tự
cho công thức, nên đây là lúc sửa cả hai: **dấu hiệu là mã trung tính, không phải câu tiếng Việt**. Tầng trình
bày dịch sang ngôn ngữ người dùng khi hiển thị.

Lý do giống hệt lý do đã bỏ tên ngôn ngữ khỏi bộ tách câu: hệ thống phục vụ mọi giáo trình, và một câu tiếng
Việt nằm giữa corpus tiếng Trung là dữ liệu sai chỗ — nó còn bị embed vào vector.

## Testing Decisions

Một test tốt ở đây kiểm hành vi quan sát được: đưa vào một đầu vào, khẳng định về node, chunk, thống kê và cảnh
báo thu được.

Bài học lặp đi lặp lại của sáu vòng review: **giả định về đầu vào không bao giờ bị chất vấn** là thứ giết chết
bộ test. Đợt này là ví dụ rõ nhất — bốn đợt vá trước chạy trên một tài liệu có **không** ký tự hỏng mã và
**một** công thức, nên không đợt nào có cơ hội thấy hai lỗi nặng nhất.

### Ba seam, đều đã tồn tại, không thêm cái nào

**Seam adapter** — kết quả parse thật đã ghi lại vào, cây tài liệu ra. Gánh: tra bảng Symbol, đọc trường thô,
giữ node công thức, định danh công thức, thống kê và cảnh báo.

**Seam chunker thuần** — cây tài liệu dựng tay vào, section và chunk ra. Gánh: chuỗi cố định trong văn bản,
tham chiếu công thức có vị trí, công thức gộp được, luật lọc tiêu đề mới, gom cảnh báo.

Luật lọc mới cần **ngữ cảnh toàn tài liệu** để quyết định về một tiêu đề — seam này nhận nguyên cây nên nó phủ
được.

**Seam ingest** — kho lưu trữ thật trên thư mục tạm. Gánh: tham chiếu công thức sống sót qua vòng lưu rồi nạp
lại; thống kê vào manifest.

### Fixture thứ hai là bắt buộc

Fixture hiện có **không kiểm được hai lỗi nặng nhất đợt này**: nó có **không** ký tự vùng dùng riêng và **một**
công thức. Dùng nó để khẳng định *"653 ký tự về không"* hay *"263 node quay lại"* là không thể.

Ghi lại kết quả parse thật của tài liệu thứ hai thành fixture thứ hai. **Đã sinh thử và kiểm vòng ghi–đọc:**

```
992 -> 992 item · khác biệt 0
công thức giữ được trường thô sau nạp lại : 263/264
ký tự vùng dùng riêng sống sót            : 1771
fixture                                   : 1,51 MB
```

Vòng ghi–đọc **giữ nguyên trường thô** — đó là điều kiện sống còn, vì không có nó thì seam adapter không kiểm
được việc khôi phục công thức.

Kích thước **1,51 MB**, xấp xỉ fixture hiện có, nên tổng hai fixture khoảng **3 MB**. *(Ước lượng ban đầu của
tôi là 0,51 MB và nó sai gấp ba: tôi tính từ cây parse đã lưu, mà cây đó là bản **rút gọn** của dự án, còn bản
xuất của thư viện gồm cả đối tượng trang, xuất xứ đầy đủ và mọi trường ta vứt đi.)*

Hai fixture bù khuyết nhau:

| | tài liệu một | tài liệu hai |
|---|---:|---:|
| Ảnh | 9 | 5 |
| Bảng | **0** | **51** |
| Công thức | 1 | **264** |
| Ký tự vùng dùng riêng | **0** | **653** |

Tài liệu nguồn của tài liệu hai **đã nằm trong dự án**, nên việc sinh lại fixture tái lập được. Tài liệu nguồn
của tài liệu một thì không — xem ghi chú.

### Ca bắt buộc

| Ca | Mong muốn |
|---|---|
| Chuỗi có `U+F061`, `U+F063`, `U+F06D`, `U+F073` | ra `α`, `χ`, `μ`, `σ` |
| Chuỗi có `U+F0B7` | ra dấu chấm tròn |
| Nguồn DOCX có ký tự vùng dùng riêng | **không** tra bảng |
| Trên fixture hai | 653 ký tự vùng dùng riêng về **không**, hoặc phần còn lại có cảnh báo |
| Node có trường đã dọn rỗng, trường thô có chữ | **được giữ**, không bị bỏ |
| Node có **cả hai** rỗng | vẫn bị bỏ |
| Trên fixture hai | **263** node công thức quay lại |
| Chunk chứa công thức | văn bản có chuỗi cố định, **không** chứa nội dung thô, **không** chứa định danh |
| Chunk chứa hai công thức | hai tham chiếu, vị trí đúng theo thứ tự xuất hiện |
| Đổi tập tham chiếu công thức, giữ nguyên văn bản | định danh chunk **không đổi** |
| Công thức xen giữa hai đoạn văn ngắn | ra **một** chunk, không phải ba |
| Tiêu đề không đánh số lặp 2 lần trong thân bài | **bị loại** |
| Tiêu đề không đánh số lặp 1 lần | **được giữ** |
| Tiêu đề **có đánh số** lặp 5 lần | **được giữ** — miễn trừ |
| Tiêu đề bắt đầu bằng dấu liệt kê | **bị loại** |
| Ba trăm cảnh báo cùng loại | gom thành **một** dòng kèm số đếm |
| Cảnh báo hiếm lẫn giữa đống cảnh báo thường | **vẫn nhìn thấy** sau khi gom |

### Bất biến

| Mã | Nội dung |
|---|---|
| I22 | Không chunk nào chứa ký tự vùng dùng riêng, trừ khi có cảnh báo tương ứng |
| I23 | Node có trường thô khác rỗng **không bao giờ** bị bỏ im lặng |
| I24 | Đổi tham chiếu công thức mà giữ nguyên văn bản ⇒ định danh chunk **không đổi** |

### Đối chiếu cuối

Ingest lại **cả hai** tài liệu.

Tài liệu một: chỉ các chunk chứa công thức được khôi phục đổi định danh; phần còn lại **giữ nguyên**. Đây là
tiêu chí mạnh nhất của đợt vì nó rất dễ sai theo hướng "đổi nhiều hơn dự kiến".

Tài liệu hai: **không** ký tự vùng dùng riêng còn sót không cảnh báo; **263** công thức có mặt; `Trong đó:` và
`Chú ý .` **không** còn là section; **không** section nào bắt đầu bằng dấu liệt kê; danh sách cảnh báo đọc được
trong một màn hình.

## Out of Scope

- **Trích công thức thành LaTeX.** Thư viện parse có mô hình hiểu công thức nhưng không bật; bật nó là đưa một
  mô hình học máy vào pha vốn hoàn toàn tất định. Cần một quyết định riêng.
- **Sắp lại thứ tự ký hiệu trong công thức.** Nội dung thô bị xáo trộn vì công thức hai chiều bị bẹp thành một
  chiều. Sửa nó là dựng lại bố cục toán học — việc lớn hơn nhiều lần đợt này.
- **Các font ký hiệu khác** — Wingdings, ZapfDingbats cũng dùng vùng dùng riêng. Ta không biết font, nên chỉ
  làm bảng Symbol và **cảnh báo** khi còn sót. Mở rộng khi gặp tài liệu thật cần.
- **Khoảng trắng chèn giữa từ** — vẫn hoãn cùng lý do đã hoãn lỗi mất dấu cách: cần từ điển mới đếm đúng.
- **Tạo node loại công thức trong đồ thị.** Đợt này làm cho việc đó khả thi, không làm nó.
- **Chunk khai thiếu trang.** Vẫn hoãn.

## Further Notes

**Hai lỗi nặng nhất đợt này đều là "đọc sai thứ thư viện đưa cho".** Ký tự vùng dùng riêng là đọc đúng mã nhưng
không diễn giải; công thức là đọc đúng đối tượng nhưng sai trường. Cùng dạng với lỗi thông báo lỗi ảnh lọt vào
nội dung ở đợt hình. Ba lần rồi — đáng ghi vào hướng dẫn dự án: **khi một thư viện trả về thứ trông rỗng hoặc
trông lạ, kiểm mọi trường của nó trước khi kết luận là không có gì.**

**Một tài liệu không đủ để định mức độ.** Công thức bị bỏ đã được ghi nhận ở vòng review thứ hai và xếp mức
thấp — vì tài liệu đó có đúng một công thức. Tài liệu thứ hai có 264. Con số quyết định mức độ, và một tài liệu
chỉ cho một con số.

**Luật lọc tiêu đề mới đáng chú ý ở chỗ nó không chứa kiến thức ngôn ngữ nào.** Nó dùng chính bằng chứng trong
tài liệu: một cụm từ lặp lại trong thân bài thì không phải tiêu đề. Cùng tinh thần với việc bỏ tên ngôn ngữ
khỏi bộ tách câu ở đợt trước — và cùng lý do: hệ thống này phục vụ mọi giáo trình, không riêng giáo trình
tiếng Việt.

**Một chỗ không nhất quán cần bạn quyết.** Tài liệu nguồn thứ hai nằm trong dự án; tài liệu nguồn thứ nhất thì
không. Ghi chú của fixture hiện có hướng dẫn sinh lại bằng cách chạy trên tệp nguồn — mà tệp đó không ai ngoài
máy này có. Hoặc đưa cả hai vào dự án, hoặc chấp nhận rằng fixture chỉ sinh lại được trên một máy. Ngoài phạm
vi spec này, nhưng nên chốt trước khi có người thứ hai chạm vào repo.
