# Spec — Pha B0.1–B0.4: Chuẩn hoá, parse và cắt chunk

> Spec triển khai, sinh từ phiên grilling ngày 2026-08-13. Vá ba lỗi của `B0-ingestion-spec.md`.
> Quyết định định danh: xem [ADR 0001](./adr/0001-dinh-danh-tat-dinh.md). Thuật ngữ: xem [CONTEXT.md](../CONTEXT.md).

## Problem Statement

Người dùng đưa vào một giáo trình PDF và muốn nhận về một lộ trình học. Toàn bộ Pha A đứng trên một bước nền:
tài liệu phải được cắt thành các chunk có cấu trúc, có định danh ổn định, trước khi bất kỳ khái niệm nào được
trích ra.

Hiện chưa có dòng code nào. Và tài liệu đặc tả sẵn có không dùng thẳng được vì ba vấn đề:

1. **Không rõ chuẩn hoá văn bản xảy ra lúc nào.** Sơ đồ đặc tả vẽ chuẩn hoá chạy *trước* parse, nhưng một
   file PDF chưa parse thì chưa có văn bản để chuẩn hoá. Vị trí ký tự của mọi chunk phụ thuộc vào việc gỡ
   được mâu thuẫn này.

2. **Công thức định danh chunk tự phá lời hứa của chính nó.** Nó băm cả vị trí của block, nên chèn một đoạn
   ở đầu tài liệu là đổi sạch định danh phía sau — trong khi đặc tả hứa rằng ingest lại sẽ giữ nguyên định
   danh cho block không đổi, để bằng chứng đã lưu không gãy. Bộ test đi kèm không phát hiện ra vì nó chỉ
   kiểm trường hợp chạy lại trên đúng file cũ.

3. **Định danh tài liệu chưa được đặc tả ở đâu cả**, dù nó nằm trong mọi phép băm.

Nếu triển khai nguyên văn, mỗi lần tài liệu được sửa là mọi bằng chứng của các bước sau bị gãy — và lỗi sẽ chỉ
lộ ra rất muộn, khi đồ thị khái niệm đã dựng xong và không còn truy được về nguồn.

## Solution

Triển khai bốn bước đầu của ingestion thành một pipeline tất định, không có mô hình ngôn ngữ nào tham gia:
chuẩn hoá văn bản, parse có nhận biết bố cục, dựng cây section và gán cha, rồi cắt chunk.

Ba sửa đổi so với đặc tả gốc:

- **Chuẩn hoá chạy sau parse**, trên từng khối một, rồi mới nối các leaf block theo thứ tự đọc bằng `\n`.
  Heading được chuẩn hoá và lưu trong cây section nhưng không thuộc `normalized_full_text`. Vị trí ký tự của
  leaf block trở thành offset tích luỹ lúc nối, nên bất biến "cắt chuỗi đầy đủ theo vị trí thì ra đúng nội
  dung chunk" đúng một cách tự nhiên, không cần bảng đối chiếu vị trí trước/sau chuẩn hoá.
- **Định danh băm theo nội dung và đường dẫn section**, không băm theo vị trí. Chi tiết và đánh đổi trong ADR 0001.
- **Định danh tài liệu là một mã logic ổn định do người gọi cấp**, tách khỏi hash của file gốc.

Kết quả cắt ra được đóng băng thành các tầng artifact đánh version riêng, nên cắt lại chunk không phải parse lại.

## User Stories

1. Là người vận hành, tôi muốn đưa một file PDF và một mã tài liệu vào bằng một lệnh duy nhất, để nhận về
   sections và chunks mà không phải viết code.
2. Là người vận hành, tôi muốn xem được cây section và các window đã gom sau khi chạy, để tự mắt kiểm tra
   xem tài liệu có bị hiểu sai cấu trúc không.
3. Là người vận hành, tôi muốn chạy lại đúng file cũ và nhận được đúng tập định danh cũ, để biết pipeline
   không âm thầm sinh dữ liệu trùng.
4. Là người vận hành, tôi muốn sửa vài đoạn trong tài liệu rồi ingest lại, để phần không đổi vẫn giữ nguyên
   định danh và công sức các bước sau không mất trắng.
5. Là người vận hành, tôi muốn biết một file đã được ingest hay chưa, để khỏi chạy lại tốn thời gian.
6. Là người vận hành, tôi muốn parse chỉ chạy một lần cho mỗi tài liệu, để thử nghiệm tham số cắt chunk không
   phải chờ mô hình bố cục chạy lại từ đầu.
7. Là kỹ sư triển khai, tôi muốn luật gán section cha nằm trong một hàm thuần không đụng I/O, để test nó
   trong mili-giây thay vì phải dựng cả PDF.
8. Là kỹ sư triển khai, tôi muốn đổi được thư viện parse mà không đụng vào logic cắt chunk, để thay adapter
   khi gặp tài liệu scan.
9. Là kỹ sư triển khai, tôi muốn bộ đếm token và bộ tách câu nằm sau giao diện trừu tượng, để nâng cấp chúng
   mà không sửa luật cắt.
10. Là kỹ sư triển khai, tôi muốn tham số cắt chunk đọc từ cấu hình, để chỉnh ngưỡng mà không sửa code.
11. Là kỹ sư triển khai, tôi muốn biết cấu hình nào đã sinh ra một tầng kết quả, để tái lập lại đúng lần chạy đó.
12. Là bước trích khái niệm, tôi muốn các chunk được gom sẵn thành window theo section cha trực tiếp, để mỗi
    lời gọi mô hình đọc trọn một mục.
13. Là bước trích khái niệm, tôi muốn mỗi chunk thuộc đúng một window, để không khái niệm nào bị trích hai lần
    và không đoạn nào bị bỏ sót.
14. Là bước trích khái niệm, tôi muốn window của một section cha **không** chứa chunk của section con, để
    preamble của chương được xét riêng khỏi nội dung các mục con.
15. Là bước trích khái niệm, tôi muốn section không có nội dung trực tiếp thì không sinh window, để không tốn
    lời gọi mô hình cho window rỗng.
16. Là bước trích khái niệm, tôi muốn tài liệu không có heading nào vẫn cho ra kết quả hợp lệ, để không phải
    có nhánh code riêng cho tài liệu phẳng.
17. Là bước trích khái niệm, tôi muốn biết loại của mỗi khối, để quyết định caption hay footnote có đáng làm
    bằng chứng chính không.
18. Là bước mention map, tôi muốn định danh chunk ổn định qua các lần ingest, để cột của ma trận khái
    niệm × chunk không bị xáo mỗi lần tài liệu được cập nhật.
19. Là bước mention map, tôi muốn văn bản đã được chuẩn hoá Unicode về một dạng duy nhất, để khớp tên chính
    xác không trượt chỉ vì tiếng Việt có hai cách tổ hợp dấu.
20. Là bước suy luận quan hệ tiên quyết, tôi muốn thứ tự đọc toàn cục chính xác, để suy được khái niệm nào
    được trình bày trước khái niệm nào.
21. Là bước suy luận quan hệ tiên quyết, tôi muốn vị trí xuất hiện đầu tiên chính xác tới từng khối, chứ
    không bị làm tròn về đầu mục.
22. Là bước suy luận quan hệ tiên quyết, tôi muốn biết đường dẫn section và cấp heading của mỗi chunk, để
    chọn được cách phân vùng phù hợp với cấu trúc tài liệu.
23. Là nhánh truy hồi trực tuyến, tôi muốn khớp trên chunk nhỏ nhưng ráp được cả mục làm ngữ cảnh, để trả lời
      chính xác mà không tốn thêm vector nào.
24. Là người đọc kết quả, tôi muốn mỗi chunk kèm số trang, để trích dẫn lại được về đúng chỗ trong tài liệu gốc.
25. Là người đọc kết quả, tôi muốn bảng được giữ nguyên khối thay vì bị dàn phẳng thành các dòng rời, để không
    mất quan hệ hàng cột.
26. Là người đọc kết quả, tôi muốn caption của bảng và hình đi kèm khối tương ứng, để khối không mất ngữ cảnh.
27. Là người đọc kết quả, tôi muốn không chunk nào bị cắt ngang câu, để đoạn trích dẫn luôn đọc được.
28. Là người bảo trì sau này, tôi muốn biết vì sao định danh lệch khỏi đặc tả gốc, để không "sửa lại cho đúng
    spec" và làm gãy mọi bằng chứng đã lưu.
29. Là nhà nghiên cứu, tôi muốn chạy lại được đúng một lần chạy cũ từ cấu hình đã ghi, để so sánh hai phương
    án cắt chunk một cách công bằng.

## Implementation Decisions

### Phạm vi
Bốn bước: chuẩn hoá văn bản, parse có nhận biết bố cục, gán section cha, cắt chunk. **Không** embed, **không**
vector database, **không** cơ sở dữ liệu quan hệ trong pha này. Kết quả ghi ra artifact dạng file.

Lý do dừng ở đây: đặc tả gốc đã tách tầng chunk và tầng embedding thành hai artifact đánh version độc lập, nên
đây là đường nối có sẵn. Ba quyết định còn mở của đặc tả đều thuộc nhánh embedding và đều cần đo trên corpus
thật trước khi chốt. Toàn bộ bất biến cần bảo vệ đều kiểm được mà không cần hạ tầng nào.

### Nguồn chân lý

Spec này được bổ sung bởi [`B0-va-cau-truc-spec.md`](./B0-va-cau-truc-spec.md) sau khi đo trên giáo trình thật.
Định danh vẫn băm và `section_path` vẫn là danh sách, nhưng quyết định “một leaf block là một chunk” đã bị
thay: các block văn bản liền kề trong cùng section được gộp quanh đích 256 token. Bảng, hình và cước chú vẫn
đứng riêng.

### Chuẩn hoá văn bản
Chạy **sau** parse, trên text của **từng khối một**. Heading đã chuẩn hoá được dùng để dựng section; chỉ các
leaf block được nối theo thứ tự đọc bằng đúng một ký tự `\n` để tạo `normalized_full_text`. Vị trí ký tự của
mỗi chunk là offset tích luỹ trong chuỗi leaf block đó.

Các phép bắt buộc: chuẩn hoá Unicode về dạng tổ hợp sẵn; chuẩn hoá khoảng trắng; gỡ dấu gạch nối mềm và nối
lại từ bị ngắt cuối dòng; chuẩn hoá dấu nháy và gạch ngang. **Không** hạ chữ thường, **không** bỏ dấu — nếu
cần dạng đó thì làm ở chỉ mục phụ, không đụng văn bản gốc.

Việc loại bỏ header, footer và số trang lặp **chuyển thành bộ lọc khối ở bước parse**, không còn là phép biến
đổi chuỗi ở bước chuẩn hoá. Thư viện parse đã phân loại sẵn các khối thuộc khung trang.

### Định danh
Xem ADR 0001 để biết lý do và đánh đổi. Công thức chốt:

```
section_id = "s_" + blake2b(doc_id | section_path | section_occurrence)
chunk_id   = "c_" + blake2b(doc_id | parent_section_id | normalized_text | split_index | chunk_occurrence)
```

`section_occurrence` đếm các section trùng đường dẫn trong một tài liệu. `chunk_occurrence` đếm các chunk
trùng `(normalized_text, split_index)` trong đúng một `parent_section_id`; nó không dùng chung bộ đếm giữa
hai section anh em trùng tên. Các bộ đếm đều theo thứ tự đọc. Định danh tài liệu là mã logic do người gọi
cấp; hash của file gốc ghi riêng trong manifest.

Vị trí ký tự **vẫn được lưu** để phục vụ trích dẫn — nó chỉ không còn nằm trong phép băm.

### Gán section cha
Section cha của một khối là heading đang mở gần nhất bao quanh nó, duy trì bằng một ngăn xếp heading. Cấp
heading được suy từ cách đánh số (`CHƯƠNG 1`, `1.1`, `1.1.1`, `a)`) thay vì tin cấp thô của parser; cấp thô
vẫn được lưu để truy vết. Khi gặp heading mới thì lấy ra mọi heading có cấp lớn hơn hoặc bằng, rồi mới đẩy
heading mới vào.

Hệ quả cần giữ đúng: nội dung trực tiếp của một section là các khối từ ngay sau heading đó tới ngay trước
heading con đầu tiên — **không** phải toàn bộ subtree.

Heading nhảy cấp không cần chèn section ảo; luật lấy-ra vẫn đúng. Heading con thật sự lồng theo cây parse mà
cấp suy ra không sâu hơn cha thì được kẹp ngay dưới cha và ghi lý do cảnh báo. Sau khi dựng xong, cây có từ
bốn heading trở lên nhưng chỉ một cấp cũng ghi cảnh báo `flat_heading_tree`. Ứng viên heading chữ thường kết
thúc bằng `:` hoặc dài quá 15 từ mà không đánh số được hạ thành text và ghi cảnh báo, không bị vứt bỏ.

### Cắt chunk
Đơn vị gốc vẫn là leaf block, nhưng các block có thể gộp liền kề trong cùng section được gộp đến
`target_tokens=256`. Nhóm chỉ có văn xuôi dùng `max_tokens=512`; nhóm có bảng dùng `max_table_tokens=2048`.
Nhóm đóng khi đạt đích; nhóm cuối ngắn được giữ. Không gộp qua ranh giới section; cước chú đứng riêng.

Một block văn xuôi dài quá trần vẫn ưu tiên cắt theo ranh giới câu, chồng lấn một câu và đánh `split_index`.
Bảng dài quá trần bảng cắt theo hàng, lặp dòng tiêu đề cột ở mỗi mảnh. Sau hai luật này, mọi mảnh vượt
`hard_cap_tokens=6000` đều bị cắt cưỡng bức tại cụm ký tự, ưu tiên khoảng trắng trong 10% cuối trước trần và
mang `oversize_reason="hard_cap_forced_split"`. Hình lấy caption làm nội dung và không lặp caption ở
`context_prefix`; bảng vẫn giữ caption trong trường ngữ cảnh.

> Trường ngữ cảnh cho caption có trong luật cắt của đặc tả gốc nhưng **thiếu trong bảng schema** của đặc tả đó.
> Spec này bổ sung nó.

### Đếm token và tách câu
Bộ đếm token dùng tokenizer SentencePiece của dòng Gemma, nạp cục bộ, ghim phiên bản. Đây là lựa chọn **lâu
dài chứ không phải tạm thời**: nhà cung cấp mô hình dự kiến dùng cho bước embedding không phát hành tokenizer
chạy ngoại tuyến, nên sẽ không bao giờ có bước "đổi sang tokenizer của mô hình embedding". Đếm token qua lời
gọi mạng bị loại vì nó biến mỗi khối thành một vòng gọi mạng và phá tính tất định.

Bộ tách câu Unicode dùng biểu thức chính quy cộng các bộ viết tắt dạng dữ liệu, ưu tiên tính tất định hơn độ
tinh vi — thư viện xử lý ngôn ngữ có thể đổi hành vi giữa các phiên bản, mà tính tất định ở đây là bất biến bắt
buộc. Nó chỉ chạy khi khối vượt ngưỡng nên hiếm khi được gọi.

Cả hai nằm sau giao diện trừu tượng khai báo ở tầng miền, để logic cắt chunk không phụ thuộc ngược lên tầng ứng dụng.

### Kiến trúc
Bốn tầng, phụ thuộc hướng vào trong. Cổng vào ra — parse tài liệu và lưu artifact — khai báo ở tầng ứng dụng.
Bộ đếm token và bộ tách câu là giao diện thuần, khai báo ở tầng miền, vì logic cắt chunk nằm trong miền và
không được import ngược lên trên.

Việc gom window và ráp ngữ cảnh từ nhỏ lên lớn là **logic ứng dụng** — không được lọt xuống tầng lưu trữ.

### Thư viện parse
Dùng thư viện parse có nhận biết bố cục ngay từ đầu, không dùng thư viện nhẹ làm bước đệm. Lý do: bước gán
section cha sống chết bằng cấp heading và thứ tự đọc; thư viện nhẹ đoán cấp heading theo cỡ chữ và thường sai
thứ tự đọc trên bố cục nhiều cột — test bước khó nhất trên dữ liệu sai là tự lừa mình.

Kéo theo ràng buộc: phiên bản Python phải ghim ở mức mà thư viện học máy đi kèm còn hỗ trợ.

### Artifact và version
Ba tầng tách rời, đánh version độc lập: cây parse, kết quả cắt chunk, và về sau là vector. Manifest của mỗi
tầng ghi hash cấu hình gồm adapter parse cùng phiên bản, tuỳ chọn chuẩn hoá, tham số cắt, và định danh
tokenizer. Hash cấu hình đổi thì tăng version.

**Cây parse được đóng băng ngay sau lần parse đầu tiên.** Mọi lần cắt lại chunk đọc từ artifact đó. Nhờ vậy
cắt lại không cần parse lại, và bước cắt trở nên tất định trên thực tế dù thư viện parse dùng mô hình học máy.

Điều này thay thế lời hứa "cùng đầu vào cho ra kết quả giống nhau tới từng byte" của đặc tả gốc — lời hứa đó
không giữ được với mô hình học máy. Lời hứa mới tách đôi: nhánh thuần tất định tuyệt đối, nhánh parse chỉ hứa
ổn định khi ghim phiên bản.

### Giao diện dòng lệnh
Hai lệnh: một lệnh nhận file và mã tài liệu rồi xuất artifact; một lệnh hiển thị cây section cùng các window
đã gom. Lệnh thứ hai tồn tại vì gán section cha là phần dễ sai nhất, mà nhìn được cây là cách rẻ nhất để bắt lỗi.

## Testing Decisions

Test tốt ở đây kiểm **hành vi quan sát được từ bên ngoài** — quan hệ giữa chunk và window, tính ổn định của
định danh — chứ không kiểm ngăn xếp heading được cài đặt thế nào.

### Hai seam

**Seam thuần: từ cây tài liệu ra sections và chunks.** Cây dựng bằng tay trong test. Gánh toàn bộ các bất biến.
Chạy trong mili-giây, không mạng, không mô hình.

**Seam parse: từ bytes ra cây tài liệu.** Test tích hợp trên một hai file thật. Chỉ kiểm thứ tự đọc, cấp
heading, bảng không bị dàn phẳng, và khối khung trang bị lọc.

Tách đôi vì thư viện parse dùng mô hình học máy: để nó nằm trong đường chạy của các test bất biến thì test vừa
chậm vừa có thể đổi kết quả khi nâng phiên bản — đúng thứ làm một bộ test bảo vệ bất biến mất giá trị.

### Bất biến được kiểm ở seam thuần

Mười bất biến của đặc tả gốc: phân hoạch window phủ hết và rời nhau; section cha là heading gần nhất; window
của cha không chứa chunk của con; section không có nội dung trực tiếp thì không sinh window; ingest lại cùng
file cho cùng tập định danh; thứ tự đọc tăng đơn điệu; không cắt ngang câu; văn bản đã chuẩn hoá Unicode; cắt
chuỗi đầy đủ theo vị trí ra đúng nội dung chunk; tài liệu không heading vẫn hợp lệ.

**Sáu bất biến bổ sung:**

- **Ổn định khi chèn**: chèn một đoạn vào đầu tài liệu, mọi định danh của phần không đổi phải giữ nguyên.
  Công thức định danh gốc **trượt** bài này.
- **Ổn định khi đổi cấu hình**: đổi trần hoặc đích, chỉ định danh của nhóm thật sự bị cắt/gộp lại được phép đổi.
- **I13 — suy cấp**: heading thô cùng cấp một nhưng đánh số `1`, `1.1`, `1.1.1`, `1.2`, `2` dựng thành cây ba cấp.
- **I14 — cây phẳng**: từ bốn heading không đánh số cùng cấp trở lên phải có lý do cảnh báo.
- **I15 — lý do vượt trần**: chunk vượt trần phải ghi đúng lý do bảng hoặc bộ tách; chunk trong trần không có lý do.
- **I16 — ranh giới section**: việc gộp không đưa block của hai section vào cùng một chunk.
- **I17 — cảnh báo bộ tách**: khối vượt trần chỉ có một span bao trọn phải ghi cảnh báo kèm vị trí.
- **I20 — trần cứng tuyệt đối**: không chunk nào vượt `hard_cap_tokens`, không có ngoại lệ.
- **I21 — lý do vượt trần áp dụng**: chunk vượt trần của loại nội dung phải mang lý do tường minh.

### Fixture

Bốn bộ, dựng thành cây tài liệu bằng tay và commit vào repo nên tất định tuyệt đối: cây có preamble chương và
preamble mục đúng ví dụ đối chiếu của đặc tả; tài liệu có heading nhảy cấp; tài liệu phẳng không heading; tài
liệu có bảng kèm caption.

Hai bộ hoãn lại: tài liệu bố cục hai cột và tài liệu scan. Chúng kiểm chất lượng thư viện parse chứ không kiểm
luật cắt chunk, và tài liệu scan còn cần mở nhánh nhận dạng ký tự quang học.

### Không có prior art
Repo trống, đây là bộ test đầu tiên. Nó đặt khuôn cho các pha sau: logic thuần test ở seam trong, thư viện
bên ngoài test riêng ở seam ngoài.

## Out of Scope

- **Embedding và vector database.** Sẽ dùng mô hình embedding qua API ở pha sau; tầng artifact đã tách sẵn.
- **Hiệu chỉnh ngưỡng độ dài chunk.** Đặc tả nói rõ phải đo trên corpus thật trước khi khoá. Ở đây nó là tham
  số cấu hình với giá trị mặc định.
- **Quyết định loại khối nào đủ tư cách làm bằng chứng chính.** Thuộc bước trích khái niệm.
- **Ghép tiền tố đường dẫn section khi embed.** Thuộc nhánh embedding, cần thử nghiệm A/B.
- **Cửa sổ trượt cho tài liệu phẳng.** Đó là *lớp đọc* của bước trích khái niệm; section cha lưu trong dữ liệu
  không đổi.
- **Nhánh nhận dạng ký tự quang học** cho tài liệu scan.
- **Bảng liên kết chunk với giai đoạn học.** Được điền ngược sau khi phân tầng topological.
- **Cơ sở dữ liệu quan hệ và migration.** Artifact dạng file là đủ cho pha này.

## Further Notes

**Rủi ro lớn nhất là cài đặt được thư viện parse**, không phải logic. Nó kéo theo một framework học máy nặng,
trên một máy Windows đang chạy phiên bản Python mới hơn mức các bánh xe cài đặt thường hỗ trợ. Việc đầu tiên
nên làm là dựng khung dự án và xác nhận cài được — **trước khi** viết bất kỳ logic nào.

**Lỗi kinh điển cần canh khi review**, chính đặc tả gốc cảnh báo: trong vòng lặp gán section cha, phải lấy
phần tử đỉnh ngăn xếp **sau khi** đã lấy ra và đẩy vào xong. Nếu đẩy trước khi lấy ra, hoặc lấy nhầm phần tử
đáy, thì mọi khối sẽ trỏ về section gốc — window phình thành cả chương và cấu trúc mất sạch. Triệu chứng rất
dễ nhìn ra bằng lệnh hiển thị cây, nhưng rất khó nhận ra nếu chỉ đọc số lượng chunk.

**Việc chấp nhận phân mảnh quá mức là có chủ đích.** Một khái niệm giới thiệu ở preamble chương rồi khai triển
ở mục con sẽ sinh ứng viên rời ở hai window. Bước hợp nhất phía sau lo việc gộp. Cố gom window to hơn để
"tránh phân mảnh" sẽ dồn nhiều khái niệm vào một ứng viên — tệ hơn nhiều.

**Đặc tả gốc vẫn nên đọc** để lấy chi tiết bảng schema và ví dụ đối chiếu cây section. Spec này chỉ ghi đè ba
điểm đã nêu; phần còn lại của nó vẫn có hiệu lực.
