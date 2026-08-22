# Spec — Lưu ảnh và tham chiếu ảnh trong chunk

> Spec triển khai, sinh từ phiên grilling ngày 2026-08-16 (13 quyết định Q1–Q13).
> Định danh: [ADR 0001](./adr/0001-dinh-danh-tat-dinh.md) và ADR 0002 sẽ viết trong đợt này.
> Thuật ngữ: [CONTEXT.md](../CONTEXT.md) — **mục `Chunk` đang sai, phải sửa trong đợt này**.
> Bổ sung cho [B0-chunking-spec.md](./B0-chunking-spec.md) và [B0-va-cau-truc-spec.md](./B0-va-cau-truc-spec.md).

## Problem Statement

Giáo trình có hình. Lộ trình học sinh ra từ nó thì **không có hình nào cả** — không phải vì ai quyết định bỏ,
mà vì chưa ai từng hỏi. Thư viện parse chạy với tuỳ chọn trích ảnh **tắt**, nên pixel chưa bao giờ rời khỏi
file PDF. Thứ duy nhất còn lại của một bức hình là dòng chú thích của nó, và dòng đó bị đối xử như một khối
văn bản độc lập.

Cách làm hiện tại gây ra bốn thiệt hại, cả bốn đều đo được trên tài liệu thật:

1. **Ảnh không có chú thích bị xoá hẳn.** Luật hiện tại coi *"không chú thích"* đồng nghĩa *"không nội dung"*.
   Trang 9 có hai bức hình nằm cạnh nhau tạo thành một hình minh hoạ; thư viện parse chỉ gắn chú thích cho bức
   bên trái, nên **bức bên phải biến mất khỏi hệ thống** — không node, không chunk, không dấu vết.

2. **Chú thích mồ côi cũng bị xoá.** Thư viện parse gắn chú thích cho **tối đa một** hình trong một cụm. Cụm ba
   hình ở trang 7 nhận ba dòng mô tả riêng, còn chú thích chung của cả cụm không thuộc về hình nào và bị bộ lọc
   loại. Kết quả: thân bài viết *"Hình 2 chứa một tập ví dụ"* trong khi corpus không chỗ nào nói Hình 2 là gì.

3. **Chú thích hình trở thành vector nhiễu.** Hình bị loại khỏi luật gộp nên chú thích đứng một mình: tám chunk
   từ 6 đến 52 token, trung vị 13, kẹp giữa những chunk 233 và 259 token. Ba trong số đó là câu lệnh sinh ảnh
   bằng tiếng Anh, lạc lõng giữa một corpus tiếng Việt.

4. **Trường phân loại khối đang nói dối.** Chunk gộp bị gán cứng nhãn `text`, nên 34 khối danh sách của tài
   liệu không có đại diện nào trong kết quả. Câu hỏi *"loại khối nào đủ tư cách làm bằng chứng"* đang đứng trên
   một trường đã sai với **mọi** chunk gộp.

Và điều quan trọng nhất nằm ở phía sau: mục tiêu của dự án là một lộ trình có thể **cho người học xem hình
minh hoạ của khái niệm họ đang học**. Điều đó hiện không thể làm được, vì không có pixel nào ở bất cứ đâu.

## Solution

Trích **mọi** hình trong lúc parse và đóng băng chúng cạnh chính cây parse đã sinh ra chúng. Phép đo cho thấy
việc này **gần như miễn phí**: 144,0 giây có trích ảnh so với khoảng 146 giây không trích — thư viện parse vốn
đã dựng ảnh từng trang để chạy mô hình bố cục, cắt thêm vùng hình không tốn gì thêm. Chín bức hình của tài liệu
thử nghiệm chiếm 0,78 MB.

Mỗi bức hình mang một **định danh băm theo nội dung**, cùng nguyên tắc đã dùng cho chunk và section.

Phần văn bản của chunk giữ nguyên tính người-đọc-được: nó chứa **chú thích**, hoặc — khi hình không có chú
thích — một **chuỗi cố định** báo rằng chỗ này có một hình chưa được đặt tên. Đường dẫn và định danh hình
**không** nằm trong văn bản. Chúng sống trong một danh sách tham chiếu riêng, có kèm vị trí, và danh sách đó
**cố ý đứng ngoài khoá băm định danh chunk** — nhờ vậy đổi cấu hình trích ảnh không làm gãy bằng chứng đã lưu,
đúng như lần vá gần nhất giữ nguyên từng byte tập chunk.

Hình và bảng thôi là ngoại lệ của luật gộp. Không cần thêm ngưỡng nào: luật đóng nhóm khi vượt trần token vốn
đã tự đẩy bảng lớn ra đứng riêng, còn chú thích hình 13 token thì hoà vào đoạn văn quanh nó như mọi khối khác.

Chú thích mồ côi trở thành khối văn bản bình thường tại đúng vị trí đọc của nó — không đoán, không gán ghép.

Và bước ingest **vẫn không biết đồ thị tồn tại**. Nó lưu hình và tham chiếu; việc dựng thực thể hình trong đồ
thị là việc của bước trích khái niệm, và định danh băm theo nội dung đủ ổn định để bước đó tự làm bất cứ lúc
nào.

## User Stories

**Lưu hình**

1. Là người dựng lộ trình, tôi muốn mọi bức hình trong giáo trình được trích ra và lưu lại, để sau này còn có
   thể cho người học xem.
2. Là người dựng lộ trình, tôi muốn hình được lưu cạnh chính cây parse đã sinh ra nó, để hai thứ luôn khớp
   phiên bản với nhau.
3. Là người dựng lộ trình, tôi muốn mỗi hình có định danh sinh từ nội dung của nó, để cùng một bức hình luôn
   nhận cùng một tên dù nó đổi vị trí trong sách.
4. Là người vận hành, tôi muốn độ phân giải trích ảnh được ghim trong cấu hình, để nó không trôi âm thầm giữa
   các lần chạy.
5. Là người vận hành, tôi muốn đổi độ phân giải trích ảnh làm cây parse cũ hết hạn, để bản đổi thật sự có tác
   dụng thay vì bị bộ nhớ đệm che mất.
6. Là người dựng lộ trình, tôi muốn **hình không có chú thích vẫn được giữ**, vì thiếu chú thích không có nghĩa
   là không có nội dung.

**Tham chiếu trong chunk**

7. Là người dùng bước truy hồi, tôi muốn phần văn bản của chunk chỉ chứa chữ người đọc được, không chứa đường
   dẫn hay mã băm, để vector ngữ nghĩa không bị nhiễu.
8. Là người dựng lộ trình, tôi muốn chunk mang một danh sách tham chiếu tới các hình nằm trong nó, để truy ra
   hình mà không phải dò lại cây parse.
9. Là người xây giao diện, tôi muốn mỗi tham chiếu kèm **vị trí ký tự**, để chèn hình đúng chỗ trong đoạn văn
   thay vì dồn hết xuống cuối.
10. Là người dựng lộ trình, tôi muốn tham chiếu hình dùng **định danh**, không dùng đường dẫn, để đổi cách bố
    trí thư mục hay chuyển sang lưu trữ đám mây không phải sinh lại artifact.
11. Là người dựng lộ trình, tôi muốn tham chiếu hình **không** tham gia vào khoá băm định danh chunk, để đổi
    cấu hình trích ảnh không làm gãy mọi bằng chứng đã lưu.
12. Là người đọc kết quả, tôi muốn hình không chú thích để lại một dấu vết đọc được trong văn bản, để biết chỗ
    đó có hình chứ không phải một khoảng trống.
13. Là người dựng lộ trình, tôi muốn dấu vết đó là một **chuỗi cố định**, không chứa mã băm, để đổi cách trích
    ảnh không làm đổi nội dung chunk.

**Gộp**

14. Là người dùng bước truy hồi, tôi muốn chú thích hình được gộp vào đoạn văn quanh nó, để không còn vector 13
    token vô nghĩa.
15. Là người dùng bước truy hồi, tôi muốn bảng nhỏ cũng được gộp như khối thường, vì nó thuộc mạch văn.
16. Là người dựng lộ trình, tôi muốn bảng lớn **vẫn** đứng riêng và vẫn được cắt theo hàng, để nó còn dùng được
    cho truy hồi.
17. Là người dựng lộ trình, tôi muốn **không có tham số ngưỡng mới nào** cho việc này, vì luật trần token hiện
    có đã đủ.
18. Là người dựng lộ trình, tôi muốn cước chú tiếp tục đứng riêng, vì nó thuộc chân trang chứ không thuộc mạch
    văn.
19. Là người dựng lộ trình, tôi muốn chunk khai báo **tất cả** các loại khối nó chứa, để câu hỏi "loại khối nào
    đủ tư cách làm bằng chứng" có chỗ dựa đúng.
20. Là người dựng lộ trình, tôi muốn một chunk gộp từ đoạn văn và mục danh sách **không** bị gán cứng là đoạn
    văn, vì hiện tại nó đang bị như vậy.

**Chú thích mồ côi**

21. Là người dựng lộ trình, tôi muốn chú thích không thuộc về hình nào vẫn có mặt trong kết quả, tại đúng vị trí
    đọc của nó.
22. Là người vận hành, tôi muốn được cảnh báo khi số chú thích bị loại **không khớp** số chú thích được lấy lại,
    để biết có thứ vừa biến mất.
23. Là người vận hành, tôi muốn thống kê parse phân biệt "loại vì đã lấy lại được" với "loại vì mất hẳn", vì
    hiện tại hai chuyện đó gộp làm một con số.

**Ranh giới và phiên bản**

24. Là người phát triển bước trích khái niệm, tôi muốn định danh hình ổn định qua các lần ingest, để tự dựng
    thực thể hình lúc nào cũng được.
25. Là người dựng lộ trình, tôi muốn bước ingest **không** sinh thực thể đồ thị, để nó giữ nguyên tính tất định
    và không có mô hình nào tham gia.
26. Là người vận hành, tôi muốn đợt này tăng phiên bản adapter và phiên bản thuật toán **một lần duy nhất**, để
    không phải sinh lại artifact nhiều lần.
27. Là người vận hành, tôi muốn biết trước rằng đợt này **làm đổi mọi định danh chunk**, vì đó là điều lần vá
    trước không gây ra.

**Tài liệu**

28. Là người đọc từ điển thuật ngữ, tôi muốn định nghĩa **Chunk** phản ánh đúng hiện thực, vì nó vẫn đang mô tả
    một chunk là một khối lá duy nhất trong khi từ đợt trước chunk đã là một nhóm khối.
29. Là người đọc tài liệu, tôi muốn có một quyết định kiến trúc ghi lại vì sao định danh hình đứng ngoài khoá
    băm chunk, để lần sau không ai "dọn dẹp" nó vào.

## Implementation Decisions

### Trích và lưu hình

Bật trích ảnh trong tuỳ chọn của thư viện parse, ghim **độ phân giải bằng 2,0** vào cấu hình parse để nó tham
gia hash quyết định có parse lại hay không. Đo trên tài liệu thật ở độ phân giải này: chín hình từ 189×184 tới
707×452, tổng 0,78 MB PNG.

Hình được lưu **bên trong thư mục của chính phiên bản cây parse đã sinh ra chúng**. Chúng là sản phẩm của
parse, sống và chết cùng một lần đóng băng. Không dựng tầng artifact thứ tư và không dựng kho toàn cục dùng
chung — kho chung khử được trùng lặp nhưng tạo ra một tập tài nguyên không ai sở hữu, và xoá một tài liệu thì
không biết hình nào còn ai dùng.

Định danh hình băm theo **nội dung byte** của ảnh đã trích. Điểm yếu đã biết và được chấp nhận: đổi độ phân
giải trích ảnh làm đổi byte, kéo theo đổi mọi định danh hình. Chấp nhận được **vì** tham chiếu hình đứng ngoài
khoá băm chunk, nên định danh chunk không gãy theo. Hai quyết định này chỉ đúng khi đi cùng nhau, và đó là lý
do chúng thuộc cùng một ADR.

### Cổng parse đổi kiểu trả về

Cổng parse hiện trả đúng một thứ là cây tài liệu, và cây đó là dữ liệu miền thuần được tuần tự hoá thành JSON.
Byte ảnh không có đường nào đi qua nó, và **không nên** có: nhét ảnh vào cây sẽ biến tệp JSON 96 KB thành vài
MB base64.

Cổng parse đổi sang trả một bản ghi gồm **cây tài liệu cộng tập hình**, khoá theo định danh hình. Cổng kho lưu
trữ nhận thêm tập hình đó và tự quyết định ghi ra sao. Cây tài liệu **không đổi**, tầng miền vẫn không chạm tới
byte nhị phân, và adapter vẫn không biết kho lưu trữ nằm ở đâu.

### Nội dung văn bản của khối hình

Hình **có** chú thích: phần văn bản là chú thích, như hiện nay.

Hình **không** chú thích: phần văn bản là một **chuỗi cố định** báo rằng đây là hình chưa có chú thích. Chuỗi
này không chứa định danh hình. Lý do: định danh hình băm theo nội dung ảnh, nên nếu nó nằm trong văn bản thì
cấu hình trích ảnh sẽ chui vào khoá băm chunk qua đường vòng — đúng thứ ADR 0001 tồn tại để ngăn.

Hai hình không chú thích nằm cạnh nhau sẽ có cùng phần văn bản; bộ đếm lần xuất hiện sẵn có tự phân biệt định
danh của chúng.

**Nhánh dự phòng hiện có phải bị gỡ hẳn, không phải chỉ thêm chuỗi bên cạnh.** Bật trích ảnh **đổi hành vi**
của bản xuất markdown: trước nó trả một dòng thông báo lỗi ngắn, sau nó trả **nguyên ảnh nhúng base64**. Adapter
hiện dùng bản xuất đó làm dự phòng khi hình không có chú thích. Đo thật trên fixture kèm ảnh: một node nhận
**295.568 ký tự** base64 làm nội dung, và nó sẽ thành chunk, được đếm token, rồi được embed. Chuỗi lấy nội dung
cho hình sau đợt này chỉ còn đúng hai bậc — chú thích, hoặc chuỗi cố định.

### Tham chiếu hình trên chunk

Chunk mang thêm một danh sách tham chiếu. Hình dạng được chốt trong phiên grilling, và nó đủ cụ thể để đáng ghi
thẳng ra đây:

```
image_refs: [ { image_id, char_start }, … ]
```

`char_start` dùng **cùng hệ toạ độ** với vị trí ký tự sẵn có của chunk, tức là offset trong chuỗi văn bản đầy
đủ của tài liệu. Nhờ vậy không phát sinh khái niệm toạ độ mới, và tầng trình bày chèn được hình đúng chỗ trong
đoạn thay vì dồn hết xuống cuối.

Danh sách này chứa **định danh**, không chứa đường dẫn. Đường dẫn là chi tiết của kho lưu trữ; đổi bố trí thư
mục hay chuyển sang lưu trữ đám mây không được phép làm sinh lại artifact chunk.

**Tham chiếu hình không tham gia khoá băm định danh chunk.** Đây là quyết định trung tâm của đợt này.

### Luật gộp

Bỏ hình và bảng khỏi tập loại khối được phép gộp — tức là **thêm chúng vào** tập đó. Cước chú giữ nguyên trạng
thái đứng riêng.

**Không thêm tham số ngưỡng nào.** Luật hiện tại đóng nhóm khi thêm khối kế tiếp sẽ vượt trần token, nên một
bảng vài nghìn token gặp luật đó là tự động bị đẩy ra đứng một mình rồi đi tiếp vào đường cắt theo hàng. Bảng
tám mươi token thì gộp như đoạn văn. Hành vi mong muốn đã có sẵn trong luật hiện có.

### Phân loại khối của chunk

Trường phân loại khối đổi từ **một giá trị** sang **danh sách các loại có mặt** trong chunk.

Đây là vá một lỗi đang tồn tại, không chỉ đón đầu lỗi mới: chunk gộp hiện bị gán cứng nhãn đoạn văn, nên 34
khối danh sách của tài liệu thử nghiệm không có đại diện nào trong kết quả.

### Chú thích mồ côi

Chú thích mà không hình nào nhận sẽ trở thành **khối văn bản bình thường** tại đúng vị trí đọc của nó. Không
gán ghép theo toạ độ — chính việc thư viện parse đoán sai ranh giới cụm đã tạo ra vấn đề này, nên thêm một lớp
đoán nữa là sai hướng.

Thống kê parse phải **phân biệt** chú thích bị loại vì đã được lấy lại qua liên kết hình–chú thích với chú
thích bị loại vì không thuộc về hình nào. Khi hai con số lệch nhau thì ghi một lý do cảnh báo.

### Ranh giới với bước trích khái niệm

Bước ingest **không** sinh thực thể hình và **không** biết đồ thị tồn tại. Định danh hình băm theo nội dung là
đủ ổn định để bước trích khái niệm tự dựng node hình bất cứ lúc nào, khoá theo chính định danh đó.

Chọn ngược lại sẽ buộc một pha vốn hoàn toàn tất định, không có mô hình nào tham gia, phải mang theo khái niệm
"thực thể" — kéo theo câu hỏi về loại node và loại cạnh vào chỗ không có chúng.

### Phiên bản

| Tăng cái gì | Vì sao | Hệ quả |
|---|---|---|
| Phiên bản adapter | trích ảnh, giữ chú thích mồ côi, độ phân giải vào cấu hình parse | **parse lại**, đo được khoảng 144 giây cho tài liệu 20 trang |
| Phiên bản thuật toán cắt | hình và bảng vào luật gộp ⇒ ranh giới chunk đổi; thêm chuỗi cố định cho hình không chú thích | **mọi định danh chunk đổi** |

Định danh chunk đổi là **không tránh được** lần này — khác với lần vá trước vốn giữ nguyên tập chunk từng byte.
Làm ngay trong khi corpus còn một tài liệu và **chưa có kho vector nào**; sau khi embed thật thì đây là một lần
dựng lại chỉ mục toàn bộ.

## Testing Decisions

Một test tốt ở đây kiểm **hành vi quan sát được**: đưa vào một đầu vào, khẳng định về hình, chunk và thống kê
thu được. Không kiểm tên hàm nội bộ.

Bài học lặp lại ba vòng review vừa qua là **số đo trên dữ liệu tự sinh không thay được dữ liệu thật**, nên phần
lớn khẳng định trong đợt này neo vào kết quả parse thật đã ghi lại.

### Ba seam, đều đã tồn tại, không thêm cái nào

**Seam adapter** — kết quả parse thật đã ghi lại vào, cây tài liệu cộng tập hình ra. Gánh: trích đủ chín hình;
định danh hình là băm nội dung; hình không chú thích nhận chuỗi cố định thay vì bị loại; chú thích mồ côi thành
khối văn bản; thống kê phân biệt hai loại chú thích bị loại và bật cảnh báo khi lệch.

**Seam chunker thuần** — cây tài liệu dựng tay vào, section và chunk ra. Gánh: hình và bảng gộp được; bảng lớn
vẫn đứng riêng và vẫn cắt theo hàng; danh sách loại khối phản ánh đúng thành phần; tham chiếu hình có vị trí
đúng; và **định danh chunk không đổi khi tham chiếu hình đổi** — bài này là hiện thân của quyết định trung tâm.

**Seam ingest** — kho lưu trữ thật trên thư mục tạm. Gánh: hình được ghi xuống đúng thư mục của phiên bản parse;
tham chiếu hình sống sót qua vòng lưu rồi nạp lại; tăng phiên bản adapter làm cây parse cũ hết hạn.

### Fixture

Fixture kết quả parse ghi lại phải được **sinh lại kèm ảnh** và thay hẳn bản cũ — một nguồn sự thật duy nhất
cho mọi bài test. Đã kiểm chứng trước khi viết spec này:

```
ghi ra          : 1,49 MB   (bản không ảnh hiện tại: 0,22 MB)
nạp lại         : 0,11 giây (hiện tại: 0,04 giây)
ảnh khôi phục   : 9/9 nguyên vẹn
```

Vòng ghi–đọc giữ nguyên toàn bộ chín ảnh, nên seam adapter kiểm được việc trích ảnh mà không phải chạy thư viện
parse thật. Ghi chú nguồn gốc của fixture phải nêu rõ nó chứa ảnh và phải sinh lại khi nâng phiên bản thư viện
parse.

### Prior art

Bài kiểm ổn định định danh khi chèn đoạn, bài kiểm hai section anh em trùng tên, và bài kiểm guard đa cột dựng
node trực tiếp là ba mẫu để theo. Đặc biệt bài cuối: nó ra đời vì một fixture PDF **không chạm được** tới nhánh
cần kiểm, và bài học đó áp thẳng vào đây — khẳng định nào không đi qua được fixture thì dựng node bằng tay.

### Đối chiếu cuối trên tài liệu thật

Sau khi xong, ingest lại tài liệu thử nghiệm và kiểm bằng mắt: chín hình có mặt trên đĩa; bức hình trang 9
trước đây bị mất nay có chunk; chú thích cụm hình trang 7 có mặt trong văn bản; không chunk nào còn dưới 32
token chỉ vì chứa chú thích hình; và tập định danh chunk **khác** tập cũ, đúng như dự kiến.

## Out of Scope

- **Hình dạng đồ thị nhiều loại node.** Node hình có tham gia sắp thứ tự tô-pô, kiểm chu trình và chia giai
  đoạn hay bị lọc ra — thuộc bước trích khái niệm, và đã được tách khỏi spec này bằng quyết định "ingest không
  biết đồ thị tồn tại".
- **Loại cạnh nối khái niệm với hình.** Hiện chỉ có đúng một loại cạnh trong toàn bộ mô hình. Thêm loại thứ hai
  là một thay đổi miền thật sự, cần phiên grilling riêng.
- **Đưa ảnh thô cho mô hình đa phương thức lúc trích khái niệm.** Ý định đã nêu: hình không có chú thích thì
  gửi thẳng ảnh cho mô hình để nó tự nhận ra quan hệ. Cần cân chi phí, tính tất định, và mức độ nó phá nguyên
  tắc "chỉ dùng mô hình ở đúng ba chỗ".
- **Khử trùng lặp hình giữa các tài liệu.** Băm theo nội dung khiến việc này khả thi về sau, nhưng kho dùng
  chung đặt ra câu hỏi sở hữu và xoá mà đợt này không giải.
- **Trích nội dung công thức.** Vẫn ngoài phạm vi như đợt trước.
- **Chunk khai thiếu trang.** Đã chốt hoãn ngày 2026-08-16; không đụng tới trong đợt này.

## Further Notes

**Vì sao trích ảnh không tốn gì.** Thư viện parse đã dựng ảnh của từng trang để chạy mô hình bố cục rồi; cắt
thêm vùng hình chỉ là thao tác trên ảnh có sẵn trong bộ nhớ. Số đo: 144,0 giây có trích so với khoảng 146 giây
không trích — chênh lệch nằm trong nhiễu. Lập luận "trích ảnh làm chậm ingest" không có cơ sở.

**Hai bức hình cạnh nhau ở trang 9.** Ban đầu tôi ngờ thư viện parse nhận trùng một bức. Kiểm toạ độ cho thấy
chúng nằm cạnh nhau trong cùng dải dọc — hai bức khác nhau ghép thành một hình minh hoạ. Nghĩa là hệ thống
hiện tại đang mất **nửa** một hình, không phải mất một bản sao thừa.

**Một rủi ro nhỏ cần theo dõi.** Chunk mà nội dung *chỉ* gồm chuỗi cố định của hình không chú thích sẽ cho
vector giống hệt nhau giữa các hình khác nhau. Sau khi hình được gộp vào đoạn văn quanh nó thì ca này hiếm,
nhưng nó vẫn xảy ra được khi một hình đứng một mình trong một section. Đáng ghi lại để nếu gặp trên corpus thật
thì biết đường xử lý.

**Từ điển thuật ngữ đang lệch từ đợt trước.** Mục `Chunk` vẫn định nghĩa nó là *một khối lá sau khi chuẩn hoá*,
trong khi từ đợt gộp khối, một chunk là **một nhóm khối lá liền kề trong cùng một section**. Đợt này làm nó
lệch thêm — chunk giờ có thể chứa cả văn bản, hình lẫn bảng. Phải viết lại mục đó và thêm ba thuật ngữ: **hình**,
**tham chiếu hình**, **chú thích mồ côi**.

**ADR 0002 phải ghi bốn quyết định như một khối gắn liền**, vì tách rời chúng ra thì từng cái đều có vẻ tuỳ
tiện: hình là sản phẩm của parse; định danh hình băm theo nội dung; tham chiếu hình đứng **ngoài** khoá băm
chunk; bước ingest không biết đồ thị tồn tại. Ghi rõ điểm yếu còn lại — đổi độ phân giải trích ảnh làm đổi mọi
định danh hình — và ghi rõ vì sao chấp nhận được: vì quyết định thứ ba khiến định danh chunk không gãy theo.
