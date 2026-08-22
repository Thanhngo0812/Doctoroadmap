# Spec — Vá pha B0 sau khi đo trên tài liệu thật

> Spec triển khai, sinh từ vòng review 2 ngày 2026-08-15 trên artifact `nhap-mon-ml`.
> Phát hiện gốc: [feedback/README.md](../feedback/README.md) — F11–F21.
> Quyết định định danh: [ADR 0001](./adr/0001-dinh-danh-tat-dinh.md). Thuật ngữ: [CONTEXT.md](../CONTEXT.md).
> Spec này **bổ sung**, không thay thế [B0-chunking-spec.md](./B0-chunking-spec.md).

## Problem Statement

Pha B0 đã chạy được: 25 test xanh, 12 bất biến được khẳng định, ingest một giáo trình PDF 20 trang ra 28
section và 132 chunk mà không lỗi. Nhưng khi mở artifact ra xem thì kết quả **không dùng được cho các bước
sau**.

Ba vấn đề, xếp theo mức thiệt hại:

1. **Cây section phẳng hoàn toàn.** Docling trả `level = 1` cho cả 27 heading của tài liệu — nó nhận ra "đây
   là tiêu đề" nhưng không nói "tiêu đề cấp mấy". Thuật toán gán section cha đứng trên cấp heading, nên khi
   mọi cấp bằng nhau thì `1.1.1` thành **anh em** của `CHƯƠNG 1` thay vì cháu. Kết quả: `CHƯƠNG 1` không sở
   hữu một chunk nào, `section_path` của mọi chunk chỉ dài một phần tử, và không có cách nào truy ra "các
   chunk thuộc chương 1". Bước trích khái niệm mất đơn vị window cấp chương; đồ thị tiên quyết mất tín hiệu
   bao hàm giữa các mục; bước xếp stage mất khái niệm "học xong chương này rồi sang chương sau".

2. **Hệ thống không hề báo.** Cờ cảnh báo cấu trúc chỉ bật khi một heading con có cấp *nhỏ hơn* cha — tình
   huống bất thường. Ở đây mọi cấp đều bằng 1, hoàn toàn "hợp lệ" và nhất quán, nên cờ im lặng. Dòng
   `Cảnh báo cấu trúc: không` in ra cho người dùng là một lời khẳng định sai.

3. **Chunk nhỏ hơn ngân sách tám lần.** Trung vị 62,5 token trong khi trần là 512 — và trần chưa bao giờ
   chạm, nên luật cắt câu chưa từng chạy. Kích thước chunk không do ai chọn: nó bằng kích thước đoạn văn mà
   tác giả giáo trình viết ra. Một phần năm số chunk ngắn hơn ngưỡng tối thiểu, nhỏ nhất là ba token. Vector
   của văn bản ngắn rất kém ổn định, nên các chunk này sẽ làm nhiễu ma trận mention map và làm bằng chứng hiện
   cho người học trở thành mảnh cụt không đọc được.

Kèm theo là bốn vấn đề nhỏ hơn nhưng cùng bản chất — **nội dung bẩn lọt qua mà không ai chặn**: thông báo lỗi
của thư viện parse nằm trong nội dung chunk, một cụm từ giữa câu bị nhận nhầm là tiêu đề rồi nuốt mất bằng đó
nội dung, ký hiệu toán bị nhân ba, và bảng thì bỏ qua giới hạn kích thước hoàn toàn.

Điểm chung của tất cả: **bộ test không thể bắt được cái nào**. Fixture ở seam thuần dựng cây tài liệu bằng
tay, mà dựng tay thì người viết tự gán cấp heading cho đúng ý mình. Không bài test nào từng hỏi câu *"nếu mọi
cấp heading đều bằng nhau thì sao"*, vì không ai nghĩ đó là chuyện có thể xảy ra. Seam thuần kiểm thuật toán,
và thuật toán đúng. Seam parse kiểm việc trích xuất, nhưng chỉ trên một PDF do chính dự án sinh ra với heading
đã phân cấp sẵn. **Không seam nào kiểm giả định về đầu vào.**

## Solution

Ngừng chờ thư viện parse cho biết cấp heading — nó sẽ không bao giờ cho. Suy cấp từ **cách đánh số trong chính
tiêu đề**, đúng như người đọc vẫn làm: `1.1.1` là ba cấp, `CHƯƠNG 1` là một cấp, `a)` là mục con của mục đang
mở. Đây không phải mẹo mong manh — đó là quy ước đánh số mà bản thân tài liệu tuân theo, và khi tài liệu không
tuân theo thì ta phát hiện được.

Kèm theo, đưa cờ cảnh báo từ chỗ nhìn từng heading một sang chỗ **nhìn cả cây sau khi dựng xong**, và đổi nó
từ một giá trị đúng/sai thành **danh sách lý do** ghi vào manifest. Một cờ đúng/sai chỉ nói *có chuyện*; lúc
phải soi 132 chunk thì *chuyện gì* mới là thứ cần biết.

Về kích thước, tách bạch hai vai trò đang bị lẫn: `max_tokens` là **trần** để cắt khối quá dài, còn thứ đang
thiếu là **đích** để gộp khối quá ngắn. Thêm `target_tokens`, gộp các leaf block liền kề trong cùng một section
cho tới khi đạt đích, không bao giờ gộp qua ranh giới section. Đo trên tài liệu thật: đích 256 cho ra 39 chunk
trung vị 270 token, thay vì 132 chunk trung vị 62.

Việc dọn nội dung bẩn đặt ở **adapter parse**, không đặt ở tầng chuẩn hoá của miền. Lý do: đó là hiện vật của
việc trích xuất PDF chứ không phải chuẩn hoá ngôn ngữ. Mọi bước chuẩn hoá hiện có đều **bảo toàn nghĩa**; gộp
glyph lặp thì **xoá chữ**, và một hàm có thể xoá chữ không nên nằm chung chỗ với các hàm không thể.

Cuối cùng, mọi thay đổi trên đều làm đổi định danh chunk, nên chúng đi **một đợt duy nhất** và tăng
`algorithm_id` một lần.

## User Stories

**Cấu trúc tài liệu**

1. Là người dựng lộ trình, tôi muốn `1.1.1` nằm dưới `1.1` nằm dưới `CHƯƠNG 1`, để cây section phản ánh đúng
   cấu trúc giáo trình.
2. Là người dựng lộ trình, tôi muốn cấp heading được suy từ cách đánh số trong tiêu đề, để không phụ thuộc
   vào thứ mà thư viện parse không cung cấp.
3. Là người dựng lộ trình, tôi muốn tiêu đề dạng `CHƯƠNG <số>` hoặc `PHẦN <số>` được nhận là cấp một, để phần
   thân giáo trình có gốc rõ ràng.
4. Là người dựng lộ trình, tôi muốn tiêu đề dạng `<số>.<số>` cho ra cấp bằng số thành phần, để `1.4.2` sâu
   hơn `1.4`.
5. Là người dựng lộ trình, tôi muốn tiêu đề dạng `a)` `b)` được nhận là mục con của mục đánh số đang mở, để
   `a) Chọn kiểu mô hình` nằm dưới `1.2.2` chứ không ngang hàng.
6. Là người dựng lộ trình, tôi muốn tiêu đề **không** đánh số mà xuất hiện **trước** tiêu đề đánh số đầu tiên
   được coi là cấp một, để `MỞ ĐẦU` và `TÀI LIỆU ĐỌC` nằm đúng chỗ phần đầu sách.
7. Là người dựng lộ trình, tôi muốn tiêu đề **không** đánh số mà xuất hiện **sau** đó được coi là mục con của
   mục đang mở, để `Làm sạch dữ liệu` nằm dưới `1.4.2 Tiền xử lý dữ liệu`.
8. Là người dựng lộ trình, tôi muốn `section_path` chứa đủ đường đi từ chương xuống mục, để có thể dùng làm
   tiền tố ngữ cảnh khi embed.
9. Là người dựng lộ trình, tôi muốn một section không có nội dung trực tiếp nhưng có section con vẫn tồn tại
   trong cây, để chương sách không biến mất khỏi cấu trúc.

**Cảnh báo cấu trúc**

10. Là người ingest tài liệu, tôi muốn được cảnh báo khi mọi heading rơi vào cùng một cấp, vì đó gần như chắc
    chắn là parse hỏng chứ không phải tài liệu phẳng thật.
11. Là người ingest tài liệu, tôi muốn cảnh báo nói rõ **lý do** chứ không chỉ có/không, để biết phải đi xem
    chỗ nào.
12. Là người ingest tài liệu, tôi muốn danh sách cảnh báo được ghi vào manifest, để soi lại về sau mà không
    phải chạy lại parse mất hai phút rưỡi.
13. Là người ingest tài liệu, tôi muốn lệnh dòng lệnh in ra từng lý do cảnh báo, để thấy ngay lúc chạy.
14. Là người ingest tài liệu, tôi muốn được cảnh báo khi một tiêu đề ứng viên bị loại, để biết hệ thống vừa
    ra một quyết định thay tôi.

**Lọc tiêu đề giả**

15. Là người dựng lộ trình, tôi muốn cụm từ giữa câu như `trong đó:` **không** trở thành section, để nội dung
    thật không bị gán vào một mục vô nghĩa.
16. Là người dựng lộ trình, tôi muốn một tiêu đề bị loại được hạ xuống thành khối văn bản thường, để nội dung
    của nó quay về đúng section cha thay vì biến mất.
17. Là người dựng lộ trình, tôi muốn window của `1.1.1` liền một mạch, không bị một tiêu đề giả xen giữa cắt
    làm đôi.
18. Là người dựng lộ trình, tôi muốn tiêu đề hợp lệ kết thúc bằng dấu hai chấm như `TẬP THỂ TÁC GIẢ:` và
    `a) Chọn kiểu mô hình:` **không** bị loại nhầm.

**Nội dung sạch**

19. Là người dùng bước truy hồi, tôi muốn chunk không chứa thông báo lỗi của thư viện parse, để vector không
    bị nhiễu bởi văn bản không thuộc tài liệu.
20. Là người dùng bước truy hồi, tôi muốn một hình không có chú thích và không có nội dung thì **không** sinh
    chunk, thay vì sinh một chunk chỉ gồm thông báo lỗi.
21. Là người dùng bước truy hồi, tôi muốn chú thích hình không bị lặp lại ở cả nội dung chunk lẫn tiền tố ngữ
    cảnh, để không đưa cùng một câu vào vector hai lần.
22. Là người đọc giáo trình, tôi muốn ký hiệu toán bị nhân ba như `P P P` và `x x x` được gộp về một, để khái
    niệm trung tâm của sách còn tìm được.
23. Là người đọc giáo trình, tôi muốn ký hiệu có chỉ số dưới như `x x xN` cũng được gộp đúng thành `xN`.
24. Là người đọc giáo trình, tôi muốn cụm lặp hợp lệ trong tiếng Việt **không** bị gộp nhầm.
25. Là người ingest tài liệu DOCX, tôi muốn việc gộp glyph **không** áp dụng cho nguồn của mình, vì lỗi đó chỉ
    có ở PDF.

**Kích thước chunk**

26. Là người dùng bước truy hồi, tôi muốn chunk có kích thước quanh 256 token, để vector đủ ổn định và đủ
    thông tin.
27. Là người dựng lộ trình, tôi muốn các leaf block liền kề trong cùng section được gộp lại cho đủ đích, để
    không còn chunk ba token.
28. Là người dựng lộ trình, tôi muốn việc gộp **không bao giờ** vượt qua ranh giới section, để mỗi chunk vẫn
    thuộc đúng một window.
29. Là người dựng lộ trình, tôi muốn bảng, hình và cước chú **không** bị gộp vào đoạn văn bên cạnh, vì chúng
    là loại nội dung khác.
30. Là người dựng lộ trình, tôi muốn một khối dài hơn trần vẫn được cắt theo ranh giới câu như trước, để luật
    cắt cũ không mất tác dụng.
31. Là người dựng lộ trình, tôi muốn vị trí ký tự của chunk sau khi gộp vẫn cắt đúng ra nội dung chunk từ
    chuỗi đầy đủ, để bằng chứng còn truy ngược được.
32. Là người vận hành, tôi muốn mọi tham số cấu hình trong manifest thật sự ảnh hưởng tới đầu ra, để đổi tham
    số không sinh ra một lần cắt lại vô ích cho kết quả y hệt.

**Bảng**

33. Là người dựng lộ trình, tôi muốn một bảng dài được cắt theo hàng thay vì thành một chunk khổng lồ, để nó
    còn dùng được cho truy hồi.
34. Là người dựng lộ trình, tôi muốn mỗi mảnh của bảng giữ lại dòng tiêu đề cột, để đọc riêng một mảnh vẫn
    hiểu.
35. Là người dựng lộ trình, tôi muốn có một bất biến khẳng định không chunk nào vượt trần, vì đó là lời hứa
    cốt lõi của tham số trần mà đến giờ chưa bài test nào bảo vệ.

**Thống kê và tái chạy**

36. Là người ingest tài liệu, tôi muốn manifest ghi lại số node bị bỏ theo từng loại, để biết tài liệu nào bị
    nuốt mất thứ gì mà không phải chạy lại parse.
37. Là người ingest tài liệu, tôi muốn được biết khi một node bị bỏ vì rỗng nội dung, đặc biệt là công thức.
38. Là người phát triển, tôi muốn sửa mã adapter thì lần ingest sau **phải** parse lại, chứ không im lặng dùng
    lại cây parse cũ khiến bản sửa của tôi không có tác dụng.

## Implementation Decisions

### Phạm vi và thứ tự

Một đợt duy nhất, vì mọi mục trừ hai mục cuối đều làm đổi định danh chunk. Thứ tự bắt buộc: cảnh báo cấu trúc
trước (để bước sau có cách tự kiểm), rồi suy cấp heading, rồi lọc tiêu đề giả (dùng chung luật đánh số của
bước trước), rồi các mục còn lại theo thứ tự tuỳ ý.

### Suy cấp heading — đặt ở tầng miền

Adapter tiếp tục báo trung thực điều thư viện parse nói và ghi vào `heading_level_raw`. Tầng miền quyết định
cấp thật. Đây là suy luận cấu trúc từ văn bản, thuần, không chạm I/O — nên nó thuộc miền, không thuộc adapter.

Luật, xét theo thứ tự, dừng ở luật đầu tiên khớp:

| Mẫu tiêu đề | Cấp |
|---|---|
| `CHƯƠNG <số>` · `PHẦN <số>` · `Chapter <số>` · `Phụ lục` | 1 |
| `<số>` nối bằng dấu chấm, theo sau là khoảng trắng | bằng số thành phần |
| `<chữ cái>)` | cấp của mục đánh số đang mở, cộng một |
| Không đánh số, trước tiêu đề đánh số đầu tiên | 1 |
| Không đánh số, sau đó | cấp của mục đang mở, cộng một |

Luật kẹp cấp hiện có được giữ nguyên: nếu cấp suy ra nhỏ hơn hoặc bằng cấp của mục đang mở **trong khi** cây
parse cho biết nó thật sự lồng bên trong, thì kẹp về cấp con và ghi một lý do cảnh báo.

Rủi ro đã biết: một tiêu đề mở đầu bằng số nhưng không phải số mục — ví dụ một năm — sẽ bị nhận là cấp một.
Chấp nhận, vì bộ lọc tiêu đề giả xử lý riêng chuyện "đây có phải tiêu đề không", còn luật này chỉ trả lời
"nếu là tiêu đề thì cấp mấy".

### Cảnh báo cấu trúc — đổi kiểu dữ liệu

Trường đúng/sai đổi thành danh sách chuỗi lý do, ghi vào manifest của tầng chunk và in ra ở lệnh dòng lệnh.
Bốn lý do ban đầu: cây heading phẳng, cấp heading bị kẹp, tiêu đề ứng viên bị loại, node bị bỏ vì rỗng nội
dung.

Điều kiện "cây heading phẳng": có từ bốn heading trở lên **và** mọi heading rơi vào cùng một cấp sau khi suy.
Phép kiểm này chạy **sau khi duyệt xong toàn cây**, không chạy trên từng heading — đó chính là lý do bản hiện
tại mù, vì nó chỉ nhìn được từng heading một.

### Lọc tiêu đề giả — tầng miền, chạy trước khi suy cấp

Một tiêu đề ứng viên bị loại và hạ xuống thành khối văn bản thường khi: kết thúc bằng dấu hai chấm **và**
không đánh số **và** ký tự đầu là chữ thường; hoặc dài hơn mười lăm từ **và** không đánh số. Mỗi lần loại ghi
một lý do cảnh báo kèm nguyên văn tiêu đề.

Điều kiện thứ nhất loại được `trong đó:` và giữ được cả `TẬP THỂ TÁC GIẢ:` (viết hoa) lẫn `a) Chọn kiểu mô
hình:` (có đánh số) lẫn `Làm sạch dữ liệu` (không có dấu hai chấm). Ba ca này đều có thật trong tài liệu đã
đo và phải được kiểm bằng test.

### Dọn nội dung ở adapter

**Hình:** lấy chú thích trước; chỉ khi không có chú thích mới lấy bản xuất markdown, và luôn gỡ bỏ chú thích
HTML trong đó. Không còn chú thích lẫn nội dung thì **bỏ node**, không sinh chunk. Với node hình, tiền tố ngữ
cảnh để trống vì nội dung chunk đã chính là chú thích — tránh đưa cùng một câu vào vector hai lần. Với bảng
thì vẫn giữ tiền tố ngữ cảnh, vì nội dung chunk là bảng chứ không phải chú thích.

**Gộp glyph lặp:** chỉ áp dụng cho nguồn PDF, đặt trong adapter. Gộp một chuỗi cùng **một chữ cái Latin đơn**
lặp liền nhau, phân cách bằng đúng một khoảng trắng. Giới hạn ở chữ cái Latin đơn (không dấu) là điều giữ cho
cụm lặp hợp lệ trong tiếng Việt không bị đụng tới.

Các ca bắt buộc phải xử lý đúng, lấy từ tài liệu đã đo:

| Đầu vào | Đầu ra mong muốn |
|---|---|
| `tiêu chí P P P khi giải quyết` | `tiêu chí P khi giải quyết` |
| `T T T : Cần phán đoán` | `T : Cần phán đoán` |
| `{ x x x 1 , x x x 2 , ..., x x xN }` | `{ x 1 , x 2 , ..., xN }` |
| `ha ha ha` | **không đổi** |
| `Hà Nội và Hà Nam` | **không đổi** |

Ca `x x xN` là ca khó: lần lặp cuối dính liền chỉ số dưới nên không có ranh giới từ ở cuối. Nếu bỏ sót ca này
thì hai mươi hai phần trăm số chunk vẫn còn bẩn — nó phải nằm trong test.

### Adapter phải góp phiên bản của chính nó vào hash cấu hình parse

Hiện `parser_config` chỉ gồm định danh của adapter, mà định danh đó chỉ là phiên bản thư viện parse. Sửa mã
adapter mà thư viện giữ nguyên phiên bản thì hash không đổi, nên lần ingest sau **tìm thấy cây parse cũ và
dùng lại** — bản sửa hình và gộp glyph sẽ không có tác dụng, và người sửa sẽ tưởng mình làm sai.

Adapter phải công bố thêm một số phiên bản của riêng nó, tăng tay mỗi khi đổi cách dựng node, và số đó vào
`parser_config`. Đợt này phải tăng.

### Gộp leaf block — tầng miền

Thay `min_tokens` bằng `target_tokens`, mặc định 256. Trần giữ nguyên 512. Tham số `min_tokens` bị bỏ hẳn khỏi
cấu hình vì nó chưa từng có hành vi.

Luật gộp: đi theo thứ tự đọc, tích luỹ các leaf block **trong cùng một section**; kết thúc nhóm hiện tại khi
thêm block kế tiếp sẽ vượt trần, hoặc khi nhóm đã đạt đích. Không gộp qua ranh giới section. Chỉ khối văn bản
và mục danh sách mới gộp được với nhau; bảng, hình và cước chú luôn đứng một mình. Nhóm cuối của một section
ngắn hơn đích thì giữ nguyên, vì không còn gì để gộp cùng.

Một khối đơn lẻ dài hơn trần vẫn đi qua đường cắt theo ranh giới câu như cũ, và chỉ đường đó mới sinh chỉ số
mảnh khác không.

Vị trí ký tự sau khi gộp là từ đầu block đầu tới cuối block cuối. Bất biến "cắt chuỗi đầy đủ theo vị trí ra
đúng nội dung chunk" vẫn đúng, vì các leaf block được nối bằng một ký tự xuống dòng theo đúng thứ tự đọc, và
nội dung trực tiếp của một section luôn là một dải liền mạch — bất kỳ tiêu đề xen giữa nào cũng mở một section
mới.

**Hệ quả cho định danh, phải ghi vào ADR:** gộp làm các block dính vào nhau trong khoá băm. Trước đây sửa
block thứ nhất chỉ đổi định danh của chính nó; sau khi gộp thì nó đổi định danh của cả nhóm. Đây là mất mát
thật về tính ổn định, đổi lấy chất lượng vector. `split_index` giữ nguyên ý nghĩa cũ — chỉ số mảnh khi một
khối quá dài bị cắt — nên vẫn bằng không với chunk gộp, và định danh vẫn không phụ thuộc vị trí.

### Cắt bảng theo hàng

Bảng được cắt theo hàng, mỗi mảnh giữ lại dòng tiêu đề cột và không vượt trần. Một hàng đơn lẻ dài hơn trần
thì giữ nguyên và được đánh dấu vượt trần trong chunk. Bất biến "không cắt ngang câu" không áp dụng cho bảng —
ranh giới của bảng là ranh giới hàng.

### Thống kê parse

Manifest của tầng parse ghi thêm: tổng số mục thư viện trả về, số node giữ lại, và số node bị bỏ theo từng
nhãn. Số đếm này do adapter trả về cùng cây parse.

### Phiên bản

`algorithm_id` tăng từ `section-id-v2` lên `section-id-v3`, một lần cho cả đợt. Trong cấu hình: bỏ
`min_tokens`, thêm `target_tokens`. Cây parse cũ trở nên hết hạn do phiên bản adapter tăng, nên mọi tài liệu
đã ingest phải parse lại — với tài liệu đã đo là khoảng hai phút rưỡi cho hai mươi trang.

## Testing Decisions

Một test tốt ở đây kiểm **hành vi quan sát được từ bên ngoài**: đưa vào một cây tài liệu, khẳng định về
section và chunk thu được. Không kiểm tên hàm nội bộ, không kiểm bước trung gian. Bài học của cả hai vòng
review là bộ test cũ đúng về thuật toán nhưng chưa bao giờ chất vấn **giả định về đầu vào** — nên phần lớn
test mới ở đây có dạng "đầu vào bất thường mà vẫn hợp lệ về hình thức".

### Ba seam, không thêm seam mới

**Seam thuần — `DocumentTree` vào, section và chunk ra.** Đã có, gánh phần lớn công việc: suy cấp heading, cảnh
báo cấu trúc, lọc tiêu đề giả, gộp block, cắt bảng. Cây tài liệu dựng tay với **mọi node heading đặt cấp bằng
một** — đó chính là điều kiện tái hiện lỗi gốc, và là fixture mà bộ test cũ chưa từng có.

**Seam adapter — cây parse thật vào, `DocumentTree` ra.** Đã có nhưng đổi cách nuôi dữ liệu. Thay vì chạy thư
viện parse trên PDF trong lúc test, lưu **một lần** kết quả parse thật của `nhap-mon-ml` thành fixture JSON,
rồi nạp lại và chạy adapter trên đó. Nhanh như test đơn vị nhưng đối chiếu với **dữ liệu thật**, không phải với
niềm tin của ta về giao diện thư viện — mà chính niềm tin sai về giao diện đó đã sinh ra lỗi thông báo lỗi lọt
vào nội dung. Ràng buộc: fixture phải được sinh lại khi nâng phiên bản thư viện parse, và phải có một dòng ghi
rõ nó sinh từ đâu.

Phương án này **đã được kiểm chứng trước khi viết spec**, vì nếu đối tượng tài liệu không sống sót qua vòng
ghi–đọc thì cả seam sụp. Ghi ra rồi nạp lại, so từng mục trên nhãn, cấp cây, cấp heading, số trang, nội dung,
bản xuất markdown của hình và chú thích:

```
snapshot gốc : 170 item        nạp lại : 0,04 s
snapshot sau : 170 item        parse   : 140,8 s
khác biệt    : 0
picture giữ được placeholder sau nạp lại: 9/9
```

Chín trên chín hình giữ nguyên thông báo lỗi ⇒ fixture tái hiện đúng ca lỗi cần test. Fixture đã nằm sẵn ở
`tests/fixtures/docling/` kèm ghi chú nguồn gốc và cách sinh lại.

**Seam chuẩn hoá — chuỗi vào, chuỗi ra.** Đã có. Không đổi trong đợt này: gộp glyph đặt ở adapter chứ không
đặt ở đây, nên tầng chuẩn hoá giữ nguyên tính chất mọi bước đều bảo toàn nghĩa.

Test tích hợp chạy thư viện parse thật trên PDF vẫn giữ, nhưng chỉ để bảo đảm đường ống còn nối được — không
dùng nó để khẳng định chi tiết nội dung.

### Bất biến mới

| Mã | Nội dung | Seam |
|---|---|---|
| I13 | Cây tài liệu có mọi heading cùng cấp một, tiêu đề đánh số `1`, `1.1`, `1.1.1`, `1.2`, `2` ⇒ cây thu được có ba cấp | thuần |
| I14 | Cùng đầu vào nhưng tiêu đề **không** đánh số ⇒ có lý do cảnh báo cây phẳng | thuần |
| I15 | Mọi chunk có số token không vượt trần, trừ chunk được đánh dấu vượt trần tường minh | thuần |
| I16 | Việc gộp không bao giờ tạo chunk có block thuộc hai section khác nhau | thuần |

I13 là bài mà bản hiện tại **trượt**. Đó là lý do nó đáng viết trước.

### Test cần thêm ngoài bất biến

- Tiêu đề `a)` nằm dưới mục đánh số đang mở, không ngang hàng.
- Tiêu đề không đánh số **trước** mục đánh số đầu tiên ra cấp một; **sau** thì ra mục con.
- `trong đó:` bị loại; `TẬP THỂ TÁC GIẢ:`, `a) Chọn kiểu mô hình:`, `Làm sạch dữ liệu` được giữ.
- Nội dung nằm sau một tiêu đề bị loại quay về đúng section cha.
- Gộp glyph: ba ca toán ở bảng trên phải gộp; `ha ha ha` và `Hà Nội và Hà Nam` phải **không** đổi.
- Hình không chú thích không sinh chunk; hình có chú thích sinh chunk không chứa chú thích HTML và có tiền tố
  ngữ cảnh để trống.
- Gộp block: đạt đích thì đóng nhóm; bảng và cước chú không bị gộp vào đoạn văn; nhóm cuối section ngắn vẫn
  giữ.
- Vị trí ký tự của chunk gộp cắt ra đúng nội dung — mở rộng bài kiểm hiện có.
- Bảng dài cắt theo hàng, mỗi mảnh có dòng tiêu đề cột.
- Sửa phiên bản adapter làm hash cấu hình parse đổi, nên cây parse cũ không được dùng lại.
- Bài kiểm ổn định định danh hiện có phải chạy lại được sau khi đổi luật gộp.

### Prior art trong dự án

Bộ test bất biến ở seam thuần và bài kiểm ổn định định danh khi chèn đoạn là mẫu để theo. Bài kiểm bộ đếm
trùng lặp giữa hai section anh em trùng tên là mẫu cho cách viết một bài test từ một lỗi thật đã gặp — nên làm
đúng như vậy với lỗi cây phẳng.

### Đối chiếu cuối cùng trên tài liệu thật

Sau khi xong, chạy lại ingest trên chính `nhap-mon-ml` và kiểm bằng mắt bốn điều: cây có ba cấp; `CHƯƠNG 1`
có section con; `trong đó:` không còn trong danh sách section; trung vị số token của chunk quanh 250 thay vì
62. Đây là phép kiểm rẻ nhất và là thứ đã phát hiện ra toàn bộ spec này.

## Out of Scope

- **Nhận diện tiêu đề bằng thuộc tính trình bày** — cỡ chữ, kiểu đậm, lề trái. Thư viện parse có trả toạ độ
  khung, và lề trái đúng là đã phân biệt được `Làm sạch dữ liệu` với văn bản thường trong tài liệu đã đo.
  Nhưng luật theo đánh số giải quyết được các ca thật đang có, và thêm một nguồn tín hiệu nữa lúc này là mở
  rộng phạm vi không cần thiết.
- **Tách từ tiếng Việt để sửa tiêu đề dính chữ** như `MỤCLỤC`. Quá nặng so với lợi ích; hai ca trong hai mươi
  trang và cả hai đều ở phần đầu sách.
- **Khôi phục công thức bị bỏ vì rỗng nội dung.** Đợt này chỉ đếm và cảnh báo. Trích được nội dung công thức
  là việc riêng, cần biết thư viện parse để nó ở đâu.
- **Gộp glyph bằng toạ độ khung** thay vì bằng mẫu văn bản. Chính xác hơn nhưng phải chạm tới tầng glyph.
- **Chồng lấn giữa các chunk gộp.** Ranh giới ở đây là ranh giới đoạn văn, vốn đã là ranh giới ngữ nghĩa —
  khác cửa sổ trượt cố định nơi chồng lấn tồn tại để cứu câu bị cắt giữa. Cần ngữ cảnh rộng hơn thì đã có
  window.
- **Hiệu chỉnh `target_tokens` trên nhiều tài liệu.** Con số 256 đo trên đúng một giáo trình. Khoá lại sau khi
  có thêm corpus.
- **Bước embed và kho vector.** Vẫn ngoài phạm vi như đợt trước.

## Further Notes

**Vì sao đợt này gộp làm một mà không chia nhỏ.** Suy cấp heading đổi `section_path`, lọc tiêu đề giả đổi số
section, gộp glyph đổi nội dung chunk, gộp block đổi ranh giới chunk. Cả bốn đều đi vào khoá băm định danh.
Làm rời từng cái là bốn lần đổi sạch định danh thay vì một. Hiện chưa có kho vector nào nên chi phí bằng
không; sau này thì mỗi lần là một lần dựng lại chỉ mục.

**Con số 256 đến từ đâu.** Mô phỏng trên chính tài liệu đã đo, gộp trong cùng section với các đích khác nhau:
đích 200 cho 46 chunk trung vị 223; đích 256 cho 39 chunk trung vị 270; đích 512 cho 31 chunk trung vị 316
nhưng có chunk chạm 511, tức bắt đầu nuốt gần trọn một section và mất khả năng định vị bằng chứng. Chọn 256 vì
nó giữ được khoảng hai đơn vị mỗi trang — đủ mịn để trích dẫn, đủ dài để vector ổn định.

**Nỗi lo trong đặc tả gốc hoá ra sai chỗ.** Đặc tả cảnh báo *"chunk quá nhỏ thì ma trận phình"*. Tính thử:
132 chunk nhân 250 khái niệm là 33 nghìn ô — mili-giây, phình không phải vấn đề. Vấn đề thật là **chất lượng
vector của văn bản ngắn**, thứ đặc tả không nhắc tới.

**Một quyết định của vòng trước bị lật.** Việc bỏ hẳn `min_tokens` từng được ghi nhận là làm đúng hơn yêu cầu,
với lập luận rằng luật một khối một chunk khiến tham số đó không có hành vi nào. Lập luận đó đúng về mã nguồn
nhưng dựa trên fixture tự sinh toàn đoạn văn dài đều. Dữ liệu thật cho thấy một phần năm số chunk quá ngắn để
làm đơn vị truy hồi. Đó không phải một quyết định tốt, đó là một lỗ hổng chưa lộ.

**Số đo hiệu năng của vòng trước cũng phải bỏ.** Đo trên PDF tự sinh không có ảnh cho ra 1,8 giây mỗi trang;
tài liệu thật có hình cho 7,2 giây mỗi trang — gấp gần bốn lần, vì nhận dạng ký tự thật sự chạy trên vùng ảnh.
Năm trăm trang là khoảng một giờ chứ không phải mười lăm phút. Điều này không đổi kết luận nào, chỉ làm quyết
định đóng băng cây parse đúng hơn nữa.

**Cả hai lần sai của vòng trước cùng một dạng:** số đo trên dữ liệu tự sinh không thay được số đo trên dữ liệu
thật. Đó cũng là lý do seam adapter trong spec này chuyển sang nuôi bằng kết quả parse thật đã lưu, thay vì
bằng đối tượng giả lập.
