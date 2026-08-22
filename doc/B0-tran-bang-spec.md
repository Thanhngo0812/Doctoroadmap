# Spec — Ba trần token thay vì một, để bảng giữ được cấu trúc

> Spec triển khai, 2026-08-21. Sinh từ phiên grilling cùng ngày (Q1–Q4 cộng hai câu về phạm vi).
> Bổ sung cho [B0-bang-va-tach-cau-spec.md](./B0-bang-va-tach-cau-spec.md).
> Định danh: [ADR 0001](./adr/0001-dinh-danh-tat-dinh.md) · [ADR 0002](./adr/0002-anh-va-tham-chieu-ngoai-dinh-danh-chunk.md)
> Thuật ngữ: [CONTEXT.md](../CONTEXT.md)

## Problem Statement

Một trần token duy nhất đang phục vụ hai loại nội dung có bản chất khác hẳn nhau, và nó sai với một trong hai.

Trần 512 token hợp lý cho văn xuôi: khoảng nửa trang sách, đủ một ý kèm giải thích. Với bảng thì nó cắt một
bảng **mười một hàng**. Đo trên tokenizer thật:

| Bảng | Vượt 512 | Vượt 2048 | Vượt 8192 |
|---|---:|---:|---:|
| 4 cột, ô ngắn kiểu bảng kết quả | **20 hàng** | 79 hàng | 307 hàng |
| 6 cột, ô mô tả dài | **11 hàng** | 45 hàng | 175 hàng |

Bảng mười một hàng là bảng bình thường trong giáo trình. Cắt nó làm đôi không phục vụ ai.

### Và câu dẫn bảng đang bị bỏ lại một mình

Chỗ này chỉ lộ ra khi đo. Luật gộp đóng nhóm khi vượt trần, nên **bất kỳ bảng nào trên 512 token cũng không
gộp được với gì cả** — kể cả câu ngay trước giới thiệu nó. Dựng thử một đoạn có câu dẫn, bảng ba mươi hàng, và
câu bình luận phía sau:

```
 22 token  ['text']            <- "Bảng 1 dưới đây so sánh các mô hình…" BỊ BỎ LẠI MỘT MÌNH
499 token  ['table']           <- mảnh một
217 token  ['table','text']    <- mảnh hai cộng câu sau
```

Chunk hai mươi hai token là đúng loại nhiễu vector mà đợt trước vừa diệt ở chú thích hình. Và nó **không tự
khỏi** khi nâng trần cắt — vì trần *gộp* là một chuyện khác.

### Nhưng bỏ hẳn trần thì có một vực phía sau

Mô hình nhúng dự kiến dùng nhận tối đa **8192 token**. Một bảng phụ lục 175–307 hàng vượt nó, và khi ấy lời gọi
API hỏng hoặc cắt cụt âm thầm.

Tệ hơn: **ta đếm bằng tokenizer Gemma, còn giới hạn kia là của Gemini.** Không có tokenizer Gemini chạy
offline để đối chiếu — đó là quyết định đã ghi từ đầu dự án. Sai số giữa hai bộ đếm không đo được, nên đi sát
8192 là đi mù.

### Còn một lỗ nữa, cùng bản chất

Văn xuôi cũng có thể vượt trần mà không cắt được: một khối chữ viết không có dấu kết câu nào. Hiện nó thành một
chunk lớn tuỳ ý, được gắn lý do, rồi đi tiếp. Không có gì chặn nó ở 6000 hay 60000 token.

## Solution

Thay một trần bằng **ba**, mỗi cái trả lời một câu hỏi khác nhau:

**Trần văn xuôi** giữ nguyên 512 — bao nhiêu chữ thì thành một đơn vị truy hồi tốt.

**Trần bảng**, mới, mặc định 2048 — một bảng lớn cỡ nào thì vẫn nên nằm gọn một chỗ. Với con số này, bảng tới
45–79 hàng giữ nguyên cấu trúc trong một chunk, tức gần như mọi bảng trong giáo trình. Lớn hơn thì vẫn cắt
theo hàng, và **định danh bảng đã ghép các mảnh lại được** từ đợt trước — nên cấu trúc không bao giờ mất, chỉ
là có lúc nó nằm ở nhiều chunk.

**Trần cứng**, mới, mặc định 6000 — biên an toàn dưới giới hạn của mô hình nhúng. Không chunk nào được vượt nó,
**không ngoại lệ nào**. Hết cách cắt thì cắt cưỡng bức và ghi rõ đã làm vậy.

Và **trần gộp nâng theo trần bảng khi nhóm có chứa bảng**, để câu dẫn không bị bỏ lại.

Điểm mấu chốt cần nói rõ, vì nó dễ bị hiểu ngược: **cắt chunk không phải cắt bảng.** Cấu trúc hàng cột sống
trong cây parse, nguyên vẹn, khoá theo định danh bảng, và không lần cắt nào chạm tới nó. Thứ bị chia là *đơn vị
truy hồi*, không phải *dữ liệu*.

## User Stories

**Bảng giữ được cấu trúc**

1. Là người dựng lộ trình, tôi muốn một bảng mười một hàng nằm gọn trong một chunk, vì đó là bảng bình thường
   trong giáo trình.
2. Là người dựng lộ trình, tôi muốn trần cho bảng tách khỏi trần cho văn xuôi, vì hai loại nội dung này không
   giống nhau.
3. Là người dựng lộ trình, tôi muốn bảng tới khoảng bốn mươi lăm hàng giữ nguyên trong một chunk.
4. Là người dựng lộ trình, tôi muốn bảng lớn hơn nữa **vẫn được cắt theo hàng**, để nó còn dùng được cho truy
   hồi và không làm hỏng lời gọi nhúng.
5. Là người phát triển bước trích khái niệm, tôi muốn các mảnh của một bảng bị cắt vẫn ghép lại được qua định
   danh bảng, như đã có từ đợt trước.
6. Là người vận hành, tôi muốn trần bảng là tham số hiệu chỉnh được, vì con số hiện tại chưa đo trên corpus thật.

**Câu dẫn không bị bỏ lại**

7. Là người dùng bước truy hồi, tôi muốn câu giới thiệu bảng nằm cùng chunk với bảng, để vector không bị một
   mẩu hai mươi hai token làm nhiễu.
8. Là người dựng lộ trình, tôi muốn trần gộp nâng lên theo trần bảng khi nhóm có chứa bảng, vì nhóm chứa bảng
   vốn là một loại đơn vị khác.
9. Là người dựng lộ trình, tôi muốn **đích kích thước giữ nguyên** khi nhóm có bảng, để một bảng nhỏ không kéo
   theo hàng loạt đoạn văn không liên quan vào cùng chunk.
10. Là người đọc kết quả, tôi muốn biết trước rằng phân bố kích thước chunk sẽ có **hai đỉnh**, để khi nhìn số
    liệu không tưởng là hệ thống hỏng.

**Trần cứng, không ngoại lệ**

11. Là người vận hành, tôi muốn **không chunk nào** vượt trần cứng, để lời gọi nhúng không bao giờ hỏng vì kích
    thước.
12. Là người vận hành, tôi muốn trần cứng nằm đủ xa giới hạn của mô hình nhúng, vì bộ đếm token của ta chỉ là
    xấp xỉ của bộ đếm mà mô hình dùng.
13. Là người dựng lộ trình, tôi muốn một khối văn xuôi không cắt được vẫn bị **cắt cưỡng bức** khi vượt trần
    cứng, thay vì được miễn trừ.
14. Là người vận hành, tôi muốn chunk bị cắt cưỡng bức mang một lý do **riêng biệt**, để phân biệt với hai loại
    vượt trần đã biết.
15. Là người dựng lộ trình, tôi muốn cắt cưỡng bức ưu tiên ranh giới an toàn gần nhất, để hạn chế cắt giữa từ.
16. Là người dựng lộ trình, tôi muốn cắt cưỡng bức **không bao giờ** tách một dấu phụ khỏi ký tự gốc của nó, vì
    tiếng Việt sẽ vỡ chữ.
17. Là người phát triển bước nhúng, tôi muốn đếm lại token bằng bộ đếm của chính mô hình trước khi gọi API, vì
    bộ đếm ở bước ingest chỉ là xấp xỉ.

**Cấu hình và bất biến**

18. Là người vận hành, tôi muốn cả ba trần là tham số cấu hình có mặc định, không phải hằng số chôn trong mã.
19. Là người vận hành, tôi muốn cả ba trần tham gia hash cấu hình, để đổi một trần là chunk lại và kiểm được.
20. Là người dựng lộ trình, tôi muốn một bất biến khẳng định **mọi chunk dưới trần cứng, không ngoại lệ** — và
    nó phải là bất biến **có thể đỏ**.
21. Là người dựng lộ trình, tôi muốn bất biến thứ hai khẳng định chunk chỉ được vượt trần áp dụng của nó khi
    mang lý do tường minh.
22. Là người vận hành, tôi muốn manifest ghi cả ba trần, để nhìn artifact là biết nó sinh dưới cấu hình nào.

**Tính liên tục**

23. Là người vận hành, tôi muốn đợt này bump phiên bản thuật toán một lần.
24. Là người vận hành, tôi muốn biết trước rằng tập định danh chunk của tài liệu thử nghiệm **không đổi**, vì
    nó không có bảng và không khối nào vượt trần.

## Implementation Decisions

### Ba trần, mỗi trần một câu hỏi

| Tham số | Mặc định | Trả lời câu hỏi |
|---|---:|---|
| trần văn xuôi | 512 | bao nhiêu chữ thành một đơn vị truy hồi tốt |
| trần bảng | 2048 | bảng lớn cỡ nào thì vẫn nên nằm gọn một chỗ |
| trần cứng | 6000 | ngưỡng nào thì chắc chắn an toàn với mô hình nhúng |

Cả ba là **tham số cấu hình có mặc định**, cả ba **tham gia hash cấu hình**. Trần cứng không làm hằng số: đổi
mô hình nhúng là đổi giới hạn, và bắt sửa mã cho một con số vận hành là sai chỗ. Bù lại, mặc định phải đặt đủ
thấp để không ai vô tình nâng nó lên sát giới hạn thật.

### Trần nào áp cho khối nào

Khối bảng dùng trần bảng; mọi khối khác dùng trần văn xuôi. Vượt trần áp dụng thì đi vào đường cắt sẵn có của
loại đó — bảng cắt theo hàng, văn xuôi cắt theo ranh giới câu.

### Trần gộp nâng theo, đích thì không

Khi nhóm ứng viên **có chứa** một khối bảng, trần đóng nhóm là trần bảng thay vì trần văn xuôi. Đây là thứ
cứu câu dẫn khỏi bị bỏ lại.

**Đích kích thước giữ nguyên.** Đây là lựa chọn có chủ ý, và nó quyết định hành vi:

```
câu dẫn 22 token   -> nhóm = 22, dưới đích, đi tiếp
bảng   700 token   -> ứng viên = 722, dưới trần bảng 2048 -> gộp
                      722 đã đạt đích 256 -> đóng nhóm
câu sau            -> mở nhóm mới, gộp tiếp với văn xuôi phía sau
```

Nếu nâng cả đích theo thì một bảng nhỏ sẽ hút hàng loạt đoạn văn không liên quan vào cùng chunk cho tới 2048.
Nâng trần mà giữ đích cứu được câu dẫn — vốn là khiếm khuyết đo được — mà không mở cửa cho chuyện đó.

**Giới hạn đã biết và chấp nhận:** với bảng **vượt** trần bảng, câu dẫn vẫn bị bỏ lại, vì việc cắt bảng xảy ra
sau khi gom nhóm. Ca này chỉ xảy ra với bảng trên 45–79 hàng. Không sửa trong đợt này; ghi lại để khỏi trôi.

### Trần cứng, không ngoại lệ

Sau khi mọi đường cắt theo loại đã chạy, mảnh nào còn vượt trần cứng thì bị **cắt cưỡng bức**.

Cắt cưỡng bức ưu tiên ranh giới an toàn gần nhất trong một cửa sổ hợp lý trước điểm trần: khoảng trắng trước,
rồi tới ranh giới ký tự. Nó **không bao giờ** được tách một dấu phụ khỏi ký tự gốc — với tiếng Việt điều đó làm
vỡ chữ, và với chữ viết khác nó sinh ký tự không hợp lệ.

Bất biến vị trí ký tự vẫn phải đúng với các mảnh cắt cưỡng bức: chúng liền mạch trong chuỗi văn bản đầy đủ. Chỉ
số mảnh tăng dần như với mọi lần cắt khác, nên định danh của chúng vẫn phân biệt được.

### Từ vựng lý do vượt trần

Ba giá trị, cộng giá trị trống nghĩa là nằm trong trần:

| Lý do | Khi nào |
|---|---|
| hàng bảng vượt trần | một hàng đơn lẻ không chia nhỏ được |
| bộ tách câu không tìm được ranh giới | khối văn xuôi mà bộ tách trả về đúng một ranh giới |
| **cắt cưỡng bức theo trần cứng** | mới — mảnh vẫn vượt trần cứng sau mọi đường cắt |

Hai giá trị đầu đã có; giá trị thứ ba là của đợt này.

### Hai bất biến, phát biểu lại cho có thể đỏ

Bất biến trần token hiện tại không bao giờ đỏ được, vì cờ vượt trần được tự bật đúng lúc điều kiện xảy ra. Nó
được tách thành hai:

- **Không chunk nào vượt trần cứng.** Không ngoại lệ, không miễn trừ, không "trừ khi có lý do". Đây là bất biến
  **có thể đỏ**: một lỗi sinh ra chunk bảy nghìn token sẽ làm nó đỏ.
- **Chunk chỉ được vượt trần áp dụng của nó khi mang một lý do.** Đây là bất biến yếu hơn nhưng vẫn có ích: nó
  bắt được trường hợp một chunk vượt trần mà không ai ghi vì sao.

### Ai canh giới hạn của mô hình nhúng

**Cả hai tầng, nhưng bước ingest làm phần rẻ.** Bước ingest đặt trần cứng và không bao giờ vượt — tất định,
kiểm được, không cần mạng. Bước nhúng vẫn phải đếm lại bằng bộ đếm của chính mô hình trước khi gọi API, vì bộ
đếm ở đây chỉ là xấp xỉ; nhưng nếu tầng dưới làm đúng thì nó sẽ không bao giờ phải dùng tới.

Phần của bước nhúng **ngoài phạm vi** spec này vì bước đó chưa tồn tại. Ghi lại thành yêu cầu để khi dựng nó thì
không quên.

### Phiên bản

Phiên bản thuật toán cắt tăng một lần: ba tham số mới vào hash cấu hình, và từ vựng lý do có thêm một giá trị.
Phiên bản adapter **không** đổi — đợt này không chạm cây parse.

**Dự đoán kiểm được: tập định danh chunk của tài liệu thử nghiệm không đổi.** Tài liệu không có bảng nào, khối
lớn nhất 400 token dưới cả ba trần, và không nhóm nào chạm tới luật mới. Chỉ hình dạng cấu hình đổi. Nếu tập
định danh đổi thì có gì đó ngoài dự kiến.

## Testing Decisions

Một test tốt ở đây kiểm hành vi quan sát được: đưa vào một cây tài liệu, khẳng định về chunk, lý do và cảnh báo
thu được.

### Ba seam, đều đã tồn tại, không thêm cái nào

Đợt này gần như hoàn toàn nằm ở **tầng miền** — định danh bảng đã có từ đợt trước, adapter không đổi.

**Seam chunker thuần** gánh gần hết: ba trần áp đúng loại khối, trần gộp nâng theo khi nhóm có bảng, đích giữ
nguyên, cắt cưỡng bức, và cả hai bất biến.

**Seam ingest** gánh việc ba tham số đi từ cấu hình xuống tới manifest, và việc đổi một trần làm sinh phiên bản
chunk mới.

**Seam dòng lệnh** gánh việc hiển thị — nếu có gì cần hiển thị.

### Corpus không có bảng nào

Vẫn đúng như đợt trước, và cách xử lý cũng vậy: fixture DOCX sẵn có có một bảng cho đường đi thật, và cây dựng
tay cho mọi ca cần kích thước cụ thể. Bảng dựng tay là cách **duy nhất** kiểm được các ngưỡng, vì không tài
liệu nào trong tay có bảng đủ lớn.

Điều này cũng có nghĩa con số 2048 **chưa được kiểm chứng trên dữ liệu thật** — xem phần ghi chú.

### Ca bắt buộc

| Ca | Mong muốn |
|---|---|
| Bảng 11 hàng, 6 cột | **một** chunk, không cắt — đây là ca mở đầu spec |
| Bảng 30 hàng cùng câu dẫn và câu sau | câu dẫn **nằm cùng chunk với bảng**, không bị bỏ lại |
| Bảng vượt trần bảng | cắt theo hàng, mọi mảnh lặp dòng tiêu đề, mọi mảnh cùng định danh bảng |
| Bảng nhỏ giữa nhiều đoạn văn | **không** hút thêm văn xuôi tới 2048 — đích vẫn giữ |
| Khối văn xuôi 700 token | vẫn cắt theo câu ở trần 512, không hưởng trần bảng |
| Khối văn xuôi không có dấu kết câu, vượt trần cứng | **cắt cưỡng bức**, mang lý do riêng, mọi mảnh dưới trần cứng |
| Một hàng bảng vượt trần cứng | cắt cưỡng bức, mang lý do riêng |
| Cắt cưỡng bức trên chuỗi tiếng Việt | **không** tách dấu phụ khỏi ký tự gốc |
| Cắt cưỡng bức trên chuỗi không có khoảng trắng | vẫn cắt được, tại ranh giới ký tự |

### Bất biến

| Mã | Nội dung |
|---|---|
| I20 | **Không chunk nào vượt trần cứng.** Không ngoại lệ |
| I21 | Chunk vượt trần áp dụng của nó ⇒ mang một lý do tường minh |

I20 là bài **có thể đỏ**, khác với bất biến trần token hiện tại.

### Prior art

Bài kiểm cắt bảng theo hàng và bài kiểm cảnh báo khi bộ tách bó tay là hai mẫu gần nhất. Bài kiểm "đổi tham
chiếu mà giữ nguyên văn bản thì định danh chunk không đổi" là mẫu cho phần khẳng định tính liên tục.

### Đối chiếu cuối

Ingest lại tài liệu thử nghiệm và khẳng định **tập định danh chunk giống hệt trước đợt này**, rồi ingest fixture
DOCX và khẳng định bảng trong đó vẫn nguyên một chunk.

## Out of Scope

- **Bước nhúng đếm lại token bằng bộ đếm của mô hình.** Là yêu cầu đã ghi, nhưng bước đó chưa tồn tại.
- **Cứu câu dẫn của bảng vượt trần bảng.** Cần cắt bảng trước khi gom nhóm; chỉ xảy ra với bảng trên 45–79
  hàng. Ghi lại, không làm.
- **Hiệu chỉnh ba trần trên corpus thật.** Chưa có tài liệu nào có bảng.
- **Trần theo ngôn ngữ.** Mật độ token khác nhau giữa các chữ viết; chưa có corpus đa ngôn ngữ để đo.
- **Tạo node loại bảng trong đồ thị.** Vẫn thuộc bước trích khái niệm.
- **Chunk khai thiếu trang.** Vẫn hoãn.

## Further Notes

**Cắt chunk không phải cắt bảng.** Điều này đáng lặp lại vì nó dễ hiểu ngược, và chính nó làm cho quyết định
"vẫn giữ việc cắt" trở nên chấp nhận được. Cấu trúc hàng cột sống trong cây parse, nguyên vẹn, khoá theo định
danh bảng. Mọi mảnh của một bảng bị cắt mang cùng định danh và lặp lại dòng tiêu đề cột. Thứ bị chia là đơn vị
truy hồi, không phải dữ liệu — và điều đó chỉ đúng **từ đợt trước**, khi định danh bảng ra đời. Nếu hỏi câu này
sớm hơn một đợt thì câu trả lời đã phải khác.

**Vì sao 2048 chứ không phải bỏ hẳn trần.** Giới hạn của mô hình nhúng là 8192, chạm ở 175–307 hàng. Nhưng ta
đếm bằng một tokenizer khác với tokenizer mà mô hình dùng, và không có cách đối chiếu offline. 2048 để lại biên
gấp bốn lần, đủ cho sai số đó. Đi sát 8192 là đánh cược vào một con số ta không đo được.

**Con số 2048 chưa được kiểm chứng.** Đích 256 cho văn xuôi đo trên một giáo trình, và spec lúc đó đã ghi rõ đó
là điểm khởi đầu. Với bảng thì tệ hơn: **không** tài liệu nào trong tay có bảng. Con số này chọn từ phép tính
hàng-trên-token, không từ phép đo chất lượng truy hồi. Phải hiệu chỉnh khi có corpus, và phải ghi vào chỗ nào
người sau đọc được — nên nó là tham số cấu hình, không phải hằng số.

**Trần cứng làm một bất biến trở nên có nghĩa trở lại.** Bất biến trần token cũ không bao giờ đỏ được vì cờ
được tự bật đúng lúc điều kiện xảy ra — dạng lỗi mà dự án đã gặp ba lần: một thứ trông như đang bảo vệ nhưng
không bảo vệ gì. Trần cứng không có lối thoát nào, nên bất biến canh nó đỏ được thật.

**Phân bố kích thước chunk sẽ có hai đỉnh sau đợt này** — quanh 256 cho văn xuôi và tới 2048 cho chunk có bảng.
Đây là hệ quả có chủ ý, không phải lỗi. Ghi vào chỗ báo cáo số liệu để lần sau không ai nhìn biểu đồ rồi tưởng
hệ thống hỏng.
