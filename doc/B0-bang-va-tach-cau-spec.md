# Spec — Bảng thành công dân hạng nhất, và tách câu thôi chỉ dành cho tiếng Việt

> Spec triển khai, 2026-08-20. Bổ sung cho [B0-anh-va-tham-chieu-spec.md](./B0-anh-va-tham-chieu-spec.md).
> Định danh: [ADR 0001](./adr/0001-dinh-danh-tat-dinh.md) · [ADR 0002](./adr/0002-anh-va-tham-chieu-ngoai-dinh-danh-chunk.md)
> — đợt này **mở rộng** ADR 0002 sang bảng, không lật nó.
> Thuật ngữ: [CONTEXT.md](../CONTEXT.md)

## Problem Statement

Hai vấn đề độc lập, cùng một bản chất: **bước ingest chưa giao đủ thứ mà các pha sau cần**, và cả hai đều
không lộ ra trên tài liệu thử nghiệm hiện có.

### Một — bảng là công dân hạng hai

Đợt trước đã cho **hình** ba thứ: định danh tất định băm theo nội dung, vị trí trong chunk, và file trên đĩa.
**Bảng không được gì cả.**

Một bảng hiện tan vào phần văn bản của chunk dưới dạng markdown. Không có định danh bảng, không có danh sách
tham chiếu bảng, không có cách nào biết bảng bắt đầu ở đâu trong chunk. Sự bất đối xứng là tuyệt đối: chunk có
tham chiếu hình, và không có gì tương đương cho bảng.

Hệ quả cho bước trích khái niệm chạy song song ở pha sau: nó **không thể** tạo một node loại bảng có định danh
sống sót qua các lần ingest lại, nên cũng không thể vẽ một cạnh từ khái niệm tới một bảng cụ thể. Nó nhìn thấy
markdown trong văn bản, đọc hiểu được, nhưng không có cái tay nắm nào để trỏ vào.

Còn một chỗ hỏng nữa, tinh vi hơn: **bảng lớn bị cắt theo hàng thành nhiều chunk**, và hiện không gì ghi lại
rằng các mảnh ấy vốn là một bảng. Một bảng trải ba chunk trông y hệt ba đoạn markdown không liên quan.

### Hai — bộ tách câu chỉ biết tiếng Việt, và với chữ viết khác thì nó không làm gì

Bộ tách câu hiện tại nhận đúng lớp dấu chấm, chấm than, chấm hỏi — và **đòi có khoảng trắng ngay sau**. Đo thật:

```
CJK    khối 800 token · tách được   1 câu · ra 1 chunk 800 token   (vượt trần 56%)
Hindi  khối 961 token · tách được   1 câu · ra 1 chunk 960 token   (vượt trần 87%)
EN     khối 641 token · tách  240 câu · nhưng cắt sai tại 'Dr.' và 'Mr.'
```

Với tiếng Trung, Nhật, Hindi, Ả Rập, Thái, Khmer — các dấu kết câu của những chữ viết đó đều **vô hình** với
biểu thức hiện tại, và phần lớn chữ viết ấy vốn không dùng khoảng trắng giữa câu. Bộ tách trả về **đúng một
câu** cho cả khối, nên khối quá dài không bao giờ được cắt và thành một chunk khổng lồ.

Với chữ Latin không phải tiếng Việt thì ngược lại — nó cắt **quá tay**. Danh sách viết tắt chỉ có năm mục tiếng
Việt, nên các viết tắt thông dụng trong học thuật đều tạo ranh giới giả. Câu *"Dr. Smith met Mr. Jones. They
agreed."* bị cắt thành **bốn** câu thay vì hai.

### Và bất biến canh chỗ này không thể đỏ

Cờ vượt trần được **tự bật** mỗi khi số token vượt trần. Nên bất biến I15 — *"không chunk nào vượt trần, trừ
khi được đánh dấu tường minh"* — chỉ khẳng định lại điều mà code vừa tự gán cho nó. Nó **không bao giờ có thể
đỏ**, nên nó không canh gì cả. Cùng loại với lỗi tên-test-hứa-nhiều-hơn-thân-test ở vòng review đầu tiên.

## Solution

**Bảng nhận đúng ba thứ mà hình đã nhận**, trừ file trên đĩa — vì nội dung bảng vốn đã nằm trong phần văn bản
dưới dạng markdown, thứ mà mô hình đọc trực tiếp được. Cụ thể: một định danh băm theo nội dung các hàng đã
chuẩn hoá, và một danh sách tham chiếu có vị trí trên chunk, đối xứng từng điểm với tham chiếu hình.

Khi một bảng bị cắt theo hàng thành nhiều chunk, **mọi mảnh mang cùng một định danh bảng** và khác nhau ở vị
trí. Nhờ vậy bước trích khái niệm ghép lại được: ba chunk cùng định danh bảng là ba mảnh của một bảng, không
phải ba bảng.

Cấu trúc hàng cột **ở nguyên trong cây parse** — nó đã có sẵn ở đó. Không thêm tầng lưu trữ nào.

Và như hình, **tham chiếu bảng đứng ngoài khoá băm định danh chunk**. Đây là mở rộng của quyết định đã ghi
trong ADR 0002, không phải một quyết định mới.

**Bộ tách câu thôi mang tên một ngôn ngữ.** Lớp dấu kết câu mở rộng theo Unicode; yêu cầu khoảng trắng phía sau
được bỏ với những dấu thuộc chữ viết không dùng khoảng trắng; và danh sách viết tắt trở thành **dữ liệu** —
một bộ dùng chung cho chữ Latin cộng các bộ theo ngôn ngữ, thay vì năm mục viết cứng trong biểu thức.

Không thêm phụ thuộc nào. Bộ tách hiện tại đã là một biểu thức chính quy tất định; làm nó biết nhiều chữ viết
hơn là mở rộng thứ đang có, không phải thay bằng một tầng mới khó gỡ lỗi.

**Và chỗ nào bộ tách bó tay thì phải kêu.** Khi một khối vượt trần mà bộ tách chỉ trả về đúng một ranh giới
bao trọn khối, đó là tín hiệu nó không hiểu chữ viết này — hệ thống ghi một lý do cảnh báo thay vì lặng lẽ gắn
cờ vượt trần rồi đi tiếp.

## User Stories

**Bảng có danh tính**

1. Là người phát triển bước trích khái niệm, tôi muốn mỗi bảng có định danh tất định, để dựng được node loại
   bảng mà không sợ nó đổi tên sau mỗi lần ingest lại.
2. Là người phát triển bước trích khái niệm, tôi muốn định danh bảng sinh từ **nội dung** bảng, để cùng một
   bảng luôn nhận cùng định danh dù nó dịch chỗ trong tài liệu.
3. Là người phát triển bước trích khái niệm, tôi muốn chunk khai báo những bảng nằm trong nó, để vẽ được cạnh
   từ khái niệm tới một bảng cụ thể.
4. Là người xây giao diện, tôi muốn mỗi tham chiếu bảng kèm **vị trí ký tự**, để hiện bảng đúng chỗ trong đoạn
   văn.
5. Là người phát triển bước trích khái niệm, tôi muốn **mọi mảnh của một bảng bị cắt mang cùng định danh**, để
   biết ba chunk đó là một bảng chứ không phải ba bảng.
6. Là người dựng lộ trình, tôi muốn tham chiếu bảng **không** tham gia khoá băm định danh chunk, cùng lý do đã
   áp cho tham chiếu hình.
7. Là người phát triển bước trích khái niệm, tôi muốn cấu trúc hàng cột vẫn truy được từ cây parse, để xử lý
   theo cột khi cần mà không phải phân tích lại markdown.
8. Là người dựng lộ trình, tôi muốn chú thích bảng vẫn nằm ở tiền tố ngữ cảnh như hiện nay, không bị đổi.

**Tách câu toàn cầu**

9. Là người ingest một giáo trình tiếng Trung, tôi muốn khối văn bản dài được cắt tại dấu kết câu của chữ Hán,
   để nó không thành một chunk khổng lồ vượt trần.
10. Là người ingest tài liệu tiếng Nhật, tôi muốn dấu chấm than và chấm hỏi dạng toàn rộng được nhận là dấu
    kết câu.
11. Là người ingest tài liệu tiếng Hindi, tôi muốn dấu danda được nhận là dấu kết câu.
12. Là người ingest tài liệu tiếng Ả Rập, tôi muốn dấu chấm hỏi và dấu chấm của chữ Ả Rập được nhận là dấu kết
    câu.
13. Là người ingest tài liệu dùng chữ viết không có khoảng trắng, tôi muốn ranh giới câu **không** đòi khoảng
    trắng phía sau.
14. Là người ingest tài liệu tiếng Anh, tôi muốn các danh xưng viết tắt **không** tạo ranh giới câu giả.
15. Là người ingest tài liệu học thuật, tôi muốn các viết tắt kiểu *ví dụ*, *tức là*, *và cộng sự*, *so với*
    không tạo ranh giới giả.
16. Là người ingest giáo trình, tôi muốn các viết tắt chỉ hình, phương trình, mục, tập, số, trang không tạo
    ranh giới giả.
17. Là người ingest tài liệu tiếng Việt, tôi muốn các học hàm học vị viết tắt **vẫn hoạt động đúng như hiện
    nay** — đợt này không được làm hỏng ngôn ngữ duy nhất đang chạy tốt.
18. Là người vận hành, tôi muốn danh sách viết tắt là **dữ liệu**, để bổ sung một mục không phải sửa biểu thức
    chính quy.
19. Là người vận hành, tôi muốn dấu chấm lửng được xử lý đúng, vì nó phổ biến trong văn bản đã chuẩn hoá.
20. Là người dựng lộ trình, tôi muốn bộ tách câu **không mang tên một ngôn ngữ**, vì nó phục vụ mọi tài liệu.

**Không im lặng nữa**

21. Là người vận hành, tôi muốn được cảnh báo khi bộ tách câu **không cắt nổi** một khối vượt trần, để biết
    chữ viết đó chưa được hỗ trợ.
22. Là người vận hành, tôi muốn cờ vượt trần nói rõ **vì sao** vượt, để phân biệt "một hàng bảng không chia nhỏ
    được" với "bộ tách không hiểu chữ viết này".
23. Là người dựng lộ trình, tôi muốn một bất biến thật sự **có thể đỏ**, thay vì một bất biến khẳng định lại
    điều code vừa tự gán.

**Phiên bản và tính liên tục**

24. Là người vận hành, tôi muốn đợt này bump phiên bản một lần duy nhất.
25. Là người vận hành, tôi muốn biết trước rằng tập định danh chunk của tài liệu thử nghiệm **không đổi** sau
    đợt này, vì nó không có bảng và bộ tách câu chưa từng chạy trên nó.

## Implementation Decisions

### Định danh bảng

Định danh bảng băm theo **nội dung các hàng đã chuẩn hoá**, cùng cách và cùng nguyên tắc với định danh hình và
định danh chunk. Nó được tính ở adapter, nơi cấu trúc hàng cột còn nguyên, và đi kèm node bảng trong cây parse.

Không dùng vị trí, không dùng số trang, không dùng thứ tự đọc — cùng lý do đã ghi trong ADR 0001.

### Tham chiếu bảng trên chunk

Chunk mang thêm một danh sách tham chiếu bảng, hình dạng **đối xứng từng điểm** với tham chiếu hình: định danh
cộng vị trí ký tự, dùng chung hệ toạ độ với vị trí ký tự sẵn có của chunk.

Danh sách này **không tham gia khoá băm định danh chunk**. Đây là mở rộng của quyết định trung tâm trong ADR
0002, và ADR đó phải được cập nhật để nói "hình và bảng" thay vì chỉ "hình".

### Bảng bị cắt theo hàng

Khi một bảng vượt trần và bị cắt theo hàng, **mọi mảnh mang cùng một định danh bảng**, khác nhau ở vị trí ký
tự. Chỉ số mảnh sẵn có tiếp tục phân biệt thứ tự các mảnh.

Đây là điều làm cho việc dựng node bảng ở pha sau khả thi: ba chunk cùng định danh bảng là ba mảnh của một
bảng. Nếu mỗi mảnh nhận một định danh riêng thì bước trích khái niệm sẽ thấy ba bảng và không có cách nào biết
là sai.

### Cấu trúc bảng ở đâu

Cấu trúc hàng cột **ở nguyên trong cây parse**, nơi nó đã có sẵn. Không thêm tầng lưu trữ và không nhân đôi dữ
liệu vào artifact chunk.

Lý do khác với hình: byte ảnh **không thể** sống trong văn bản, nên phải có file. Nội dung bảng thì **đã** nằm
trong phần văn bản dưới dạng markdown, và đó chính là thứ mô hình đọc. Ai cần hàng cột dạng có cấu trúc thì
đọc cây parse theo định danh bảng.

### Bộ tách câu thôi gắn với một ngôn ngữ

Đổi tên cho hết mang tên một ngôn ngữ, và tách luật thành **dữ liệu**:

- **Lớp dấu kết câu** mở rộng theo Unicode, gồm ít nhất: dấu chấm, chấm than, chấm hỏi, chấm lửng, dấu chấm
  ngang của chữ Hán, dạng toàn rộng của chấm than và chấm hỏi, dấu danda của chữ Devanagari, dấu chấm hỏi và
  dấu chấm của chữ Ả Rập, dấu kết câu của chữ Khmer.
- **Yêu cầu khoảng trắng phía sau** chỉ áp cho các dấu thuộc chữ viết có dùng khoảng trắng. Với dấu thuộc chữ
  viết không dùng khoảng trắng, ranh giới nằm ngay sau dấu.
- **Danh sách viết tắt** trở thành dữ liệu, gồm một bộ dùng chung cho chữ Latin và các bộ theo ngôn ngữ. Bộ
  tiếng Việt hiện có được giữ nguyên trong bộ theo ngôn ngữ.
- Cơ chế che tạm hiện có cho số thập phân được giữ.

Không thêm phụ thuộc. Không dùng thư viện tách câu ngoài: bộ phổ biến nhất **không hỗ trợ tiếng Việt** và sẽ
rơi về luật tiếng Anh, làm hỏng đúng ngôn ngữ duy nhất đang chạy đúng.

### Cờ vượt trần nói rõ lý do

Cờ đúng/sai đổi thành **lý do**, hoặc giữ cờ và thêm một trường lý do. Hai lý do ban đầu: một hàng bảng không
chia nhỏ được, và bộ tách câu không tìm được ranh giới nào trong khối.

### Cảnh báo khi bộ tách bó tay

Khi một khối vượt trần mà bộ tách trả về **đúng một** ranh giới bao trọn khối, ghi một lý do cảnh báo. Đây là
dấu hiệu chữ viết chưa được hỗ trợ, và nó phải hiện ra ở manifest lẫn dòng lệnh thay vì lặng lẽ thành một chunk
vượt trần.

### Phiên bản

| Tăng cái gì | Vì sao |
|---|---|
| Phiên bản adapter | định danh bảng được tính ở adapter, nên cây parse đổi hình dạng |
| Phiên bản thuật toán cắt | chunk có thêm trường tham chiếu bảng và trường lý do vượt trần |

**Dự đoán kiểm được: tập định danh chunk của tài liệu thử nghiệm không đổi sau đợt này.** Tài liệu đó không có
bảng nào, và bộ tách câu chưa từng chạy trên nó — mọi chunk đều có chỉ số mảnh bằng không, khối lớn nhất là 400
token dưới trần 512. Chỉ **hình dạng** artifact đổi. Nếu tập định danh đổi thì có gì đó ngoài dự kiến, và phải
tìm ra trước khi đóng đợt.

## Testing Decisions

Một test tốt ở đây kiểm hành vi quan sát được: đưa vào một đầu vào, khẳng định về chunk, tham chiếu và cảnh báo
thu được.

Bài học của bốn vòng review: thứ giết chết bộ test là **giả định về đầu vào không bao giờ bị chất vấn**. Cây
heading phẳng, hình không chú thích, chữ viết không có khoảng trắng — cả ba đều là đầu vào hợp lệ mà không
fixture nào từng có. Đợt này phải có ca kiểm cho chữ viết không phải Latin, dù corpus hiện tại không có.

### Bốn seam, đều đã tồn tại, không thêm cái nào

**Seam adapter** — kết quả parse thật đã ghi lại vào, cây tài liệu ra. Gánh: định danh bảng được tính và ổn
định; cấu trúc hàng cột còn nguyên trong cây.

**Seam chunker thuần** — cây tài liệu dựng tay vào, section và chunk ra. Gánh: tham chiếu bảng có vị trí đúng;
bảng bị cắt theo hàng cho các mảnh **cùng định danh**; định danh chunk **không đổi** khi tham chiếu bảng đổi;
cảnh báo bật khi bộ tách bó tay.

**Seam bộ tách câu** — chuỗi vào, danh sách ranh giới ra. Gánh toàn bộ phần chữ viết toàn cầu. Đây là seam rẻ
nhất và nên có nhiều ca nhất.

**Seam ingest** — kho lưu trữ thật trên thư mục tạm. Gánh: tham chiếu bảng sống sót qua vòng lưu rồi nạp lại.

### Fixture bảng

Tài liệu thử nghiệm **không có bảng nào**, nên không kiểm được phần bảng trên nó. Fixture DOCX sẵn có **có một
bảng** và đang được một test tích hợp khẳng định — dùng nó cho đường đi thật, và dựng cây bằng tay cho các ca
bảng lớn bị cắt theo hàng.

### Ca bắt buộc cho bộ tách câu

Các ca dưới đây lấy từ phép đo thật trên bản hiện tại, và bản hiện tại **trượt** phần lớn:

| Đầu vào | Hiện tại | Mong muốn |
|---|---|---|
| `TS. An đo 3.14 đơn vị. PGS. Bình nói "đồng ý!" Câu cuối?` | 3 câu ✅ | vẫn 3 câu |
| `Dr. Smith met Mr. Jones. They agreed.` | **4 câu** ❌ | 2 câu |
| `Use a model, e.g. logistic regression. Then evaluate.` | **3 câu** ❌ | 2 câu |
| `See Goodfellow et al. 2016 for details. It is standard.` | **3 câu** ❌ | 2 câu |
| `As shown in Fig. 3 the loss drops. We then stop.` | **3 câu** ❌ | 2 câu |
| `这是第一句。这是第二句。第三句。` | **1 câu** ❌ | 3 câu |
| `これは最初の文です。これは二番目です。` | **1 câu** ❌ | 2 câu |
| `यह पहला वाक्य है। यह दूसरा है।` | **1 câu** ❌ | 2 câu |
| `هذه الجملة الأولى؟ وهذه الثانية.` | **1 câu** ❌ | 2 câu |
| `テスト！次の文？終わり。` | **1 câu** ❌ | 3 câu |

Ca đầu tiên là ca **hồi quy**: nó đang đúng và không được phép hỏng.

### Bất biến mới

| Mã | Nội dung | Seam |
|---|---|---|
| I17 | Khối vượt trần mà bộ tách chỉ trả về một ranh giới ⇒ có lý do cảnh báo | thuần |
| I18 | Mọi mảnh của một bảng bị cắt mang **cùng** định danh bảng | thuần |
| I19 | Đổi tham chiếu bảng mà giữ nguyên văn bản ⇒ định danh chunk **không đổi** | thuần |

I17 là bài mà bản hiện tại **trượt**: hiện nó lặng lẽ gắn cờ vượt trần và đi tiếp.

### Prior art

Bài kiểm "đổi tham chiếu hình mà giữ nguyên văn bản thì định danh chunk không đổi" ở đợt trước là mẫu trực tiếp
cho I19. Bài kiểm guard đa cột dựng node bằng tay là mẫu cho cách kiểm một nhánh mà fixture thật không chạm tới.

### Đối chiếu cuối

Ingest lại tài liệu thử nghiệm và khẳng định **tập định danh chunk giống hệt trước đợt này**. Sau đó ingest
fixture DOCX có bảng và kiểm tham chiếu bảng trỏ đúng vị trí markdown trong văn bản.

## Out of Scope

- **Tạo node loại hình hoặc bảng trong đồ thị.** Đợt này làm cho việc đó **khả thi**, không làm nó. Bước trích
  khái niệm tự dựng node theo định danh khi tới lúc.
- **Loại cạnh nối khái niệm với hình hoặc bảng.** Mô hình hiện có đúng một loại cạnh; thêm loại thứ hai là thay
  đổi miền cần phiên grilling riêng.
- **Đưa ảnh thô cho mô hình đa phương thức.** Vẫn ngoài phạm vi như đợt trước.
- **Cách dựng prompt cho bước trích khái niệm** — chèn dấu hiệu hình và bảng vào văn bản gửi cho mô hình là
  việc của tầng ráp prompt ở pha sau, không phải của artifact. Artifact cung cấp dữ liệu; tầng ráp dựng khung
  nhìn.
- **Tách từ cho chữ viết không có khoảng trắng.** Đợt này lo **ranh giới câu**, không lo ranh giới từ. Đếm
  token vẫn do bộ tokenizer lo.
- **Ngưỡng kích thước chunk cho từng ngôn ngữ.** Đích 256 token đo trên một giáo trình tiếng Việt; chữ viết
  khác có mật độ token khác. Khoá lại khi có corpus đa ngôn ngữ.
- **Chunk khai thiếu trang.** Vẫn hoãn.

## Further Notes

**Vì sao hai vấn đề này đi cùng một đợt.** Chúng không liên quan về mặt kỹ thuật. Nhưng cả hai đều đổi hình
dạng artifact chunk, nên gộp lại thì chỉ bump phiên bản một lần thay vì hai.

**Bảng khác hình ở đúng một điểm.** Hình cần file vì byte nhị phân không sống được trong văn bản. Bảng thì nội
dung đã ở trong văn bản rồi. Đó là toàn bộ lý do bảng không cần tầng lưu trữ riêng — và cũng là lý do đừng dựng
một tầng cho đối xứng hình thức.

**Bộ tách câu hiện là mã chết trên corpus này.** Mọi chunk có chỉ số mảnh bằng không, khối lớn nhất 400 token
dưới trần 512. Nên đợt này **không sửa lỗi đang gây hại** — nó gỡ một quả mìn cho tài liệu tiếp theo. Với một
giáo trình tiếng Trung, mỗi khối dài sẽ thành một chunk vượt trần, và hệ thống sẽ **không nói gì**.

**Cờ vượt trần tự bật là một bài học lặp lại.** Nó khiến bất biến canh nó không bao giờ đỏ được — đúng dạng
"tên test hứa nhiều hơn thân test làm" đã gặp ở vòng một, và "guard chưa từng chạy nhánh chặn" ở vòng ba. Ba
lần cùng một hình dạng lỗi: **một thứ trông như đang bảo vệ nhưng không bảo vệ gì**. Đáng ghi vào tài liệu
hướng dẫn viết test của dự án.
