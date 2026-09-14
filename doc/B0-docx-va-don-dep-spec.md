# Spec: B0 — Sửa đợt DOCX và dọn dẹp (F35, F36, F38, F39, F40, F34, F29)

**Trạng thái:** ready-for-agent
**Nguồn:** `report/ra-soat-b0-sau-bon-tai-lieu.md` (vòng 9, 2026-08-29)
**Tiền nhiệm:** `doc/B0-symbol-va-cong-thuc-spec.md` (vòng 8)

## Problem Statement

Người dùng ingest hai tài liệu thuộc hai thể loại hệ thống chưa từng gặp — một báo cáo DOCX và một bộ
slide PDF — và phát hiện:

1. **Cây section của DOCX gãy**: 12/27 section lạc lên cấp gốc, mất tên chương trong `section_path`,
   dù Word đã khai đúng cấp cho từng tiêu đề và cây parse đóng băng đã lưu đủ thông tin đó.
2. **Hình trong DOCX biến mất im lặng**: chunk chứa dấu `[figure]` nhưng danh sách tham chiếu hình
   rỗng — dấu vết không có danh tính, vi phạm khế ước ADR 0002. Không một cảnh báo nào của hệ thống
   lên tiếng; thứ duy nhất báo là một dòng stderr của thư viện parse.
3. **Câu trong DOCX bị xé thành nhiều khối**: 25/240 khối văn bản (10%) mở đầu như đứng giữa câu, vì
   run định dạng của Word (chữ đậm, tên mã) thành khối riêng — bản DOCX của đúng bài toán nối-câu-qua-trang
   đã giải cho PDF.
4. **Đồ trang trí thành chunk**: 4/30 chunk của DOCX là rác — dòng kẻ chấm 99% cho biểu mẫu viết tay,
   và mục lục lặp lại toàn bộ tiêu đề — sẽ đi thẳng vào embedding ở pha sau.
5. **Bullet font template còn nguyên trong chunk slide**: một mã vùng dùng riêng (U+F097) xuất hiện
   72 lần trong văn bản chunk, ngoài bảng tra Symbol.
6. **Danh sách cảnh báo lại ngập**: tám dòng `rejected_heading_repeated` giống hệt nhau không được gom —
   đúng chỗ hở đã dự đoán ở vòng 8 (F34).
7. **Chunk vượt trần văn xuôi mà không khai lý do**: `oversize_reason` chỉ được ghi khi trần cứng ép cắt,
   còn các đường vượt trần khác im lặng (F29).

Chẩn đoán chung: **các luật suy diễn của B0 được hiệu chỉnh trên một thể loại duy nhất (giáo trình PDF)
và thay thế cả những dữ liệu khai báo đáng tin mà nguồn đã cung cấp.**

## Solution

Từ góc nhìn người dùng: ingest lại bốn tài liệu sau đợt này thì —

- Báo cáo DOCX ra đúng cây hai cấp như trong Word: mọi mục `A.` `B.` `C.` `D.` nằm dưới đúng CHƯƠNG
  của nó; `section_path` mang đủ ngữ cảnh; window của T1 gom đúng.
- Tài liệu có hình mà không lấy được ảnh thì **hệ thống tự nói ra** bằng cảnh báo `missing_image` kèm
  lý do — trên mọi định dạng, không riêng PDF. Hình raster nhúng trong DOCX được trích như hình PDF.
- Câu bị Word xé thành nhiều run được nối lại thành một khối trước khi chunk; văn bản embed không còn
  gãy dòng giữa câu.
- Khối không mang nội dung ngôn ngữ (dòng kẻ chấm, mục lục) bị loại kèm cảnh báo — không chunk rác nào
  đi vào embedding.
- Văn bản chunk của slide sạch ký tự vùng dùng riêng: bullet template bị gỡ khỏi đầu mục liệt kê.
- Danh sách cảnh báo đọc được trong một màn hình với **mọi** tài liệu: dòng trùng nhau nguyên văn gom
  thành một kèm số đếm, dòng khác nguyên văn giữ riêng.
- Mọi chunk vượt trần áp dụng cho nó đều khai lý do trong `oversize_reason` — không còn vượt trần im lặng.
- Bốn tài liệu thật trở thành **corpus hồi quy tự động**: mỗi lần đổi luật, bộ test so số vàng của cả
  bốn và bắt buộc giải thích mọi sai khác — thay cho việc so v1↔v2 bằng tay mỗi vòng review.

## User Stories

1. As a **người đọc roadmap**, I want chunk của mục `B. Phần Bài Tập` mang section_path
   `CHƯƠNG I > B. Phần Bài Tập`, so that ngữ cảnh embed và trích dẫn nói đúng nó thuộc chương nào.
2. As a **bước T1 gom window**, I want section con nằm đúng dưới section cha trên mọi định dạng,
   so that window không trộn nội dung của hai chương khác nhau.
3. As a **nhánh RAG**, I want `parent_section_id` đúng với cấu trúc tác giả khai trong Word,
   so that truy hồi theo section trả về đúng phạm vi.
4. As a **người vận hành ingest**, I want hệ thống tin cấp tiêu đề mà nguồn khai báo khi cây khai có
   phân cấp thật, so that dữ liệu đúng không bị phỏng đoán ghi đè.
5. As a **người vận hành ingest**, I want suy diễn cấp từ đánh số tường minh vẫn thắng mọi nguồn khác,
   so that giáo trình PDF có mục `2.3.1` vẫn ra đúng ba cấp như tám vòng qua.
6. As a **người ingest giáo trình có chương số La Mã** (`CHƯƠNG IV`), I want nó nhận diện là chương
   cấp một, so that tài liệu Việt phổ biến không cần đổi cách đánh số để dùng được hệ thống.
7. As a **người ingest tài liệu có mục chữ cái chấm** (`A. Phần Lý Thuyết`), I want nó được xếp cấp
   như mục chữ cái ngoặc (`a)`), so that hai quy ước viết cùng nghĩa không cho hai cây khác nhau.
8. As a **pha trích thực thể sau này**, I want mọi dấu `[figure]` trong chunk đều có tham chiếu tương
   ứng hoặc một cảnh báo `missing_image` giải thích vì sao không, so that không gặp dấu vết mồ côi
   không trỏ về đâu.
9. As a **người dùng có DOCX chứa ảnh raster nhúng**, I want ảnh được trích, băm định danh và tham
   chiếu y như ảnh PDF, so that đường ảnh không phụ thuộc định dạng nguồn.
10. As a **người dùng có DOCX chứa hình vẽ DrawingML**, I want một cảnh báo nói rõ cần LibreOffice mới
    xuất được hình đó, so that tôi biết mình đang mất gì và cách lấy lại.
11. As a **người vận hành**, I want mọi thông điệp mất-dữ-liệu đi qua kênh cảnh báo của hệ thống thay
    vì stderr của thư viện, so that manifest là nơi duy nhất phải nhìn.
12. As a **bộ tách câu**, I want câu bị Word xé run được nối lại trước khi tách, so that ranh câu tính
    trên câu thật chứ không phải trên mảnh.
13. As a **mô hình embedding**, I want văn bản chunk không gãy dòng giữa câu (`bằng\nDocker Compose\n,`),
    so that vector không nhiễm nhiễu xuống-dòng vô nghĩa.
14. As a **người đọc chunk**, I want hai bullet thủ công liền nhau không bị dính thành một dòng,
    so that phép nối run không phá cấu trúc liệt kê.
15. As a **mô hình embedding**, I want không nhận chunk 99% dấu chấm hay chunk mục-lục lặp tiêu đề,
    so that không tốn chỗ trong chỉ mục cho nội dung không ai truy hồi.
16. As a **người vận hành**, I want mỗi khối bị loại vì phi ngôn ngữ có một cảnh báo kèm đoạn đầu
    nguyên văn, so that tôi kiểm được bộ lọc không nuốt nhầm nội dung thật.
17. As a **người đọc chunk slide**, I want đầu mục liệt kê không mở bằng ký tự vùng dùng riêng của font
    template, so that văn bản sạch với cả mắt người lẫn tokenizer.
18. As a **người vận hành**, I want số bullet vùng-dùng-riêng bị gỡ được đếm trong thống kê parse,
    so that cảnh báo `remaining_private_use` chỉ còn đo những ký tự thật sự chưa xử lý được.
19. As a **người vận hành mở danh sách cảnh báo**, I want tám dòng trùng nhau nguyên văn hiện thành
    một dòng `×8`, so that cảnh báo hiếm không chìm giữa những dòng lặp.
20. As a **người vận hành**, I want hai cảnh báo cùng loại nhưng khác nguyên văn vẫn giữ đủ cả hai,
    so that gom không làm mất thông tin — đúng lời hứa của vòng Symbol.
21. As a **người điều tra chunk to bất thường**, I want mọi chunk vượt trần áp dụng cho nó mang
    `oversize_reason` gọi tên đường vượt, so that không phải đoán vì sao một chunk 513 token tồn tại.
22. As a **người review đợt sau**, I want một bộ test số-vàng chạy trên fixture của cả bốn tài liệu thật,
    so that mọi thay đổi luật buộc phải nhìn thấy và giải thích ảnh hưởng chéo thể loại ngay trong CI,
    thay vì chờ một vòng review tay.
23. As a **người bảo trì**, I want fixture ghi lại cho hai tài liệu mới nằm cạnh hai fixture cũ,
    so that seam adapter kiểm được cả bốn thể loại trong dưới một giây, không cần parse thật.
24. As a **người đọc ADR**, I want nguyên tắc *tin dữ liệu khai báo, suy diễn là dự phòng* được ghi
    thành quyết định kiến trúc, so that đợt thể-loại-mới tiếp theo có luật chung để chiếu vào thay vì
    tranh luận lại từ đầu.

## Implementation Decisions

### D1 — Chuỗi ưu tiên ba bậc cho cấp tiêu đề (F35)

Bộ dựng cây section quyết định cấp của một tiêu đề theo thứ tự bằng chứng, mạnh trước yếu sau:

1. **Đánh số tường minh trong văn bản** — mục số (`1.`, `2.3.`), mục chữ cái (mở rộng: nhận cả `A.`
   lẫn `A)`, một chữ cái Unicode bất kỳ — bao gồm `Đ` — theo sau bởi chấm hoặc ngoặc đơn đóng),
   và **chuỗi chương tự hiệu chỉnh**: từ hai tiêu đề trở lên chung một tiền tố đứng ngay trước một
   số (chữ số hoặc La Mã), số khác nhau, có tiêu đề khác chen giữa các thành viên ⇒ chuỗi chương
   cấp 1, thành viên hưởng miễn trừ khỏi bộ lọc tiêu đề giả. Luật chuỗi **thay hẳn** danh sách từ
   khoá chương (`CHƯƠNG|PHẦN|CHAPTER|PHỤ LỤC`) — danh sách từ vựng là tập mở không bao giờ đủ,
   và vai miễn-trừ của nó tạo bất bình đẳng theo ngôn ngữ: `Kapitel 3` không được che chở khỏi luật
   tiêu-đề-lặp khi running header lặp tên chương, còn `CHƯƠNG 3` thì được. Ranh giới nguyên tắc:
   **định dạng đếm** (chữ số, La Mã, chữ cái + dấu ngăn) là tập đóng, giữ được; **từ vựng** phải
   thay bằng luật tự hiệu chỉnh. Đây là bằng chứng mạnh nhất vì do tác giả gõ ra.
2. **Cấp khai báo của cây parse, khi cây khai không thoái hoá** — nếu các tiêu đề của tài liệu khai
   từ hai cấp phân biệt trở lên, cấp khai báo được tin. Đo trên bốn tài liệu thật: chỉ DOCX có phân
   cấp thật ({1: 9, 2: 17}); ba PDF đều phẳng toàn cấp một — phép phân biệt này tách đúng bốn/bốn,
   không cần biết định dạng nguồn.
3. **Suy diễn hiện hành** — các nhánh dự phòng đang có (chữ cái nối sau mục số, mặc định cấp một)
   giữ nguyên cho cây thoái hoá.

Guard kẹp cấp theo `tree_depth` và toàn bộ bộ lọc tiêu đề giả (gạch đầu dòng, lặp, dấu hai chấm)
**giữ nguyên** — chúng quyết định *có phải tiêu đề không*, độc lập với *cấp mấy*.

### D2 — Trích ảnh tách khỏi cờ PDF, cảnh báo trên mọi định dạng (F36)

Cờ sửa-glyph-PDF chỉ còn chi phối việc sửa glyph. Trích ảnh chạy cho **mọi** định dạng nguồn:

- Node hình có byte ảnh ⇒ băm định danh, lưu ảnh, tham chiếu — y như PDF hiện nay.
- Node hình **không** lấy được byte ⇒ dấu `[figure]` vẫn vào văn bản, và cảnh báo `missing_image`
  **bắt buộc** phát kèm vị trí (trang nếu có) — trên DOCX cũng như PDF.
- ADR 0002 được bổ sung: *dấu vết không có tham chiếu là trạng thái suy giảm hợp lệ duy nhất khi byte
  không lấy được, và bắt buộc đi kèm cảnh báo `missing_image`* — không bao giờ im lặng.
- README ghi LibreOffice là phụ thuộc tuỳ chọn cho DOCX chứa hình vẽ DrawingML.

### D3 — Nối run định dạng trên đường không-bố-cục (F38)

Luật nối mới chạy cho các node **không có khung toạ độ** (đường DOCX — nội dung là dòng chảy logic,
không phải bố cục trang; PDF có bbox không đi đường này):

- Hai khối văn bản liền nhau, cùng section, khối trước **không kết thúc bằng dấu kết câu** ⇒ nối,
  **trừ khi** khối sau mở đầu bằng dấu hiệu liệt kê hoặc đánh số (`+`, `-`, bullet, `1.`, `a)`…) —
  guard này giữ hai bullet thủ công liền nhau không dính vào nhau.
- Luật nối theo chuỗi: `'…bằng'` + `'Docker Compose'` + `', thực hiện…'` phải ra **một** khối —
  khối đã nối tiếp tục xét nối với khối sau.
- Tái dùng bộ dấu kết câu và các loại được-nối của phép nối trang PDF; chỉ bỏ điều kiện ranh trang.
- Mỗi lần nối đếm vào thống kê parse (`runs_stitched`), không phát cảnh báo từng dòng.

### D4 — Bộ lọc khối phi ngôn ngữ và khối mục lục (F39)

Hai luật loại, chạy ở tầng dựng cấu trúc (sau chuẩn hoá, trước gộp):

- **Phi ngôn ngữ:** khối văn bản dài từ một ngưỡng ký tự trở lên mà tỉ lệ chữ-cái (Unicode letter)
  dưới ngưỡng ⇒ loại, cảnh báo `non_linguistic_block` kèm đoạn đầu nguyên văn. Ngưỡng chọn sao cho
  dòng kẻ chấm 99% bị loại còn dòng kỹ thuật ngắn (`x = 5`) sống — ngưỡng độ dài tối thiểu bảo vệ
  khối ngắn.
- **Mục lục:** khối mà đa số dòng của nó trùng nguyên văn một tiêu đề đã biết của chính tài liệu
  (bỏ qua số trang cuối dòng) ⇒ loại, cảnh báo `toc_block`. Luật dùng chính bằng chứng trong tài
  liệu — cùng triết lý với luật tiêu-đề-lặp — không dùng danh sách tên mục lục của bất kỳ ngôn ngữ nào.
- Node bị loại vẫn nằm trong cây parse đóng băng (chỉ tầng chunk bỏ) — I23 không bị chạm: đây là loại
  **có cảnh báo**, không phải bỏ im lặng.

### D5 — Gỡ bullet vùng dùng riêng đầu mục liệt kê (F40)

Trong adapter, sau khi tra bảng Symbol: mục liệt kê (`list_item`) mở đầu bằng ký tự vùng dùng riêng
**chưa ánh xạ được** ⇒ gỡ ký tự đó (và khoảng trắng theo sau), đếm vào thống kê parse
(`stripped_pua_bullets`). Ký tự vùng dùng riêng ở vị trí khác giữ nguyên và tiếp tục được đếm trong
`remaining_private_use` — cảnh báo đó chỉ còn đo những ký tự thật sự không xử lý được.

### D6 — Khử cảnh báo theo chuỗi đầy đủ (F34)

Phép gom cảnh báo đổi từ *miễn trừ theo loại* sang *khử theo chuỗi đầy đủ*: hai dòng giống hệt nhau
từng ký tự ⇒ một dòng kèm `×N`; khác nhau bất kỳ đâu (kể cả chỉ khác nguyên văn) ⇒ giữ riêng.
Đây là cách sửa đã chốt trong biên bản vòng 8. Thứ tự dòng ổn định giữa hai lần chạy giữ nguyên.

### D7 — `oversize_reason` cho mọi đường vượt trần (F29)

Bất biến mới **I25**: chunk có số token vượt **trần áp dụng cho nó** (512 văn xuôi; 2048 khi nhóm chứa
bảng) ⇒ `oversize_reason` khác rỗng, gọi tên đường vượt — câu-không-có-ranh, bảng-giữ-nguyên,
trần-cứng-ép-cắt. Chunk trong trần ⇒ để rỗng. Trần cứng 6000 và I20 không đổi.

### D8 — Corpus hồi quy bốn tài liệu

- Ghi fixture Docling cho hai tài liệu mới (báo cáo DOCX, slide) theo đúng cơ chế ghi-phát-lại hiện có,
  đặt cạnh hai fixture cũ. Repo đã private nên fixture chứa nội dung là chấp nhận được (quyết định
  vòng trước).
- Một bộ test số-vàng chạy toàn pipeline từ fixture qua chunk (không cần Docling thật): với mỗi tài
  liệu, ghim số section, số chunk, số tham chiếu ảnh/bảng/công thức, số ký tự vùng dùng riêng còn
  trong chunk, I9 = 0, định danh trùng = 0. Đổi luật làm lệch số vàng ⇒ test đỏ ⇒ người sửa cập nhật
  số vàng **có chủ đích** trong cùng commit — diff của số vàng chính là biên bản review.

### D9 — Phiên bản và ADR

- `adapter_version` nhích **một lần** cho cả đợt (D2, D3, D5 đổi adapter); `CHUNK_ALGORITHM_ID` nhích
  **một lần** cho cả đợt (D1, D4, D6, D7 đổi tầng chunk) — đúng bài học "mỗi đợt một cú nhích" của
  các vòng trước.
- ADR mới **0003 — tin dữ liệu khai báo, suy diễn là dự phòng**: mọi luật suy diễn phải khai nó là
  dự phòng cho trường hợp thiếu dữ liệu khai báo, và phải nhường khi dữ liệu khai báo có mặt và không
  thoái hoá. Ghi cả chẩn đoán vòng 9 làm bối cảnh: ba phát hiện lớn chung hình dạng "luật hiệu chỉnh
  trên một thể loại thay thế dữ liệu thật của thể loại khác".
- ADR 0002 bổ sung trạng thái suy giảm hợp lệ (D2).
- Từ điển thuật ngữ thêm: *cây khai báo*, *cây thoái hoá*, *run định dạng*, *khối phi ngôn ngữ*.

### Dự đoán ảnh hưởng chéo — tiêu chí mạnh nhất của đợt

Ingest lại cả bốn tài liệu sau đợt:

| Tài liệu | Được phép đổi | Phải giữ nguyên |
|---|---|---|
| nhap-mon-ml | *(không gì)* | toàn bộ chunk, cây 4 cấp, 9 tham chiếu hình |
| xstk-ch3-1 | dòng cảnh báo gom lại (D6) | toàn bộ định danh chunk, 263 công thức, 51 bảng |
| baocao-canhan | cây thành 2 cấp đủ 27 section; run nối lại; 4 chunk rác biến mất; thêm `missing_image` | nội dung văn bản thật không mất một câu nào |
| naive-bayes | 72 bullet U+F097 biến mất khỏi text; cảnh báo gom về một màn hình | 32 tham chiếu công thức, 13 bảng, 2 ảnh; các tiêu đề bị hạ (F37) **giữ nguyên trạng** |

Sai khác ngoài bảng này ⇒ **dừng và tìm ra vì sao** trước khi đóng đợt.

## Testing Decisions

- **Test tốt kiểm hành vi ngoài seam, không kiểm cách làm**: cho cây vào, đòi section/chunk ra —
  không khẳng định gì về regex hay cấu trúc stack bên trong.
- **Seam ① (thuần, domain)** gánh D1, D4, D6, D7: cây dựng tay với tiêu đề `A.`/`CHƯƠNG I`/khai báo
  hai cấp/khối chấm/mục lục; chạy mili-giây. Prior art: bộ test chunking hiện có với fixture tay.
- **Seam ② (adapter, fixture ghi lại)** gánh D2, D3, D5: bốn fixture Docling — hai cũ, hai ghi mới.
  Prior art: bộ test adapter và test Symbol/công thức hiện có.
- **Bộ số-vàng bốn tài liệu (D8)** là tầng trên cùng: từ fixture qua chunk, so số ghim. Đây là nơi
  bảng dự-đoán-ảnh-hưởng-chéo được thi hành tự động.
- Test hồi quy bắt buộc: tài liệu một và hai **không đổi một định danh chunk nào** (trừ khác biệt
  danh sách cảnh báo); luật chữ-cái mở rộng và luật chuỗi chương phải có test khẳng định chúng
  **không** bắt nhầm tiêu đề thường của hai giáo trình cũ (`Bài tập 1 / Bài tập 2` sát nhau không
  thành chương; thành viên chuỗi lặp qua running header không bị hạ).
- Test cho guard nối-run: hai bullet `+` liền nhau không dính; chuỗi ba mảnh nối thành một; khối kết
  thúc bằng dấu kết câu không nối.
- Test cho bộ lọc phi ngôn ngữ: khối chấm dài bị loại; `x = 5` ngắn sống; cảnh báo mang đoạn đầu.
- Ingest thật (integration, giữ cỡ hiện tại): smoke PDF + smoke DOCX qua đường mới không đổi hành vi.

## Out of Scope

- **F37 — thể loại slide**: hạ tiêu đề lặp trên slide là câu hỏi sản phẩm (*đơn vị học của một slide
  deck là gì*), cần một phiên grill riêng trước khi spec. Đợt này **giữ nguyên trạng** hành vi trên
  slide; bảng số vàng ghim trạng thái đó lại một cách có chủ đích.
- **F25** — chunk nhiều trang báo trang đầu: user đã hoãn từ vòng trước.
- **F26** — dò cột O(n²): giữ nguyên theo ghi chú ponytail; trang dày nhất hiện 11 node.
- **F33** — chèn space giữa từ khi sửa glyph PDF: nằm ngoài vùng chạm của đợt (thuần DOCX/slide/cảnh
  báo); để đợt riêng về chất lượng glyph nếu tái xuất hiện trên tài liệu mới.
- **Hậu xử lý OCR** (dấu tiếng Việt hỏng trên slide ảnh): sai tầng — B0 không sửa nội dung nguồn;
  nếu làm thì thuộc pha làm giàu sau.
- **B0.5** — embed và vector store: pha kế tiếp, mở khoá sau khi đợt này sạch.

## Further Notes

- Số đo neo quyết định D1 (đo 2026-08-29, trước đợt): cấp khai báo bốn tài liệu —
  nhap-mon-ml `{1: 27}`, xstk `{1: 67}`, naive-bayes `{1: 39}` (đều thoái hoá);
  baocao-canhan `{1: 9, 2: 17}` (phân cấp thật). Phép phân biệt thoái-hoá tách đúng 4/4 tài liệu
  mà không cần biết định dạng nguồn — đó là lý do chọn nó thay vì đánh hơi đuôi file.
- Rủi ro đã biết của D1-bậc-2: một PDF tương lai mà model layout đoán ra cây phân cấp **sai** sẽ được
  tin. Giảm nhẹ: bậc 1 (đánh số tường minh) thắng bậc 2, nên tài liệu đánh số — trường hợp phổ biến
  của giáo trình — miễn nhiễm; và bộ số vàng buộc mọi tài liệu mới vào corpus có chủ đích.
- Rủi ro đã biết của D3: văn bản DOCX cố tình xuống dòng không dấu câu (thơ, địa chỉ) sẽ bị nối.
  Chấp nhận cho thể loại tài liệu học thuật của dự án; guard dấu-liệt-kê chặn phần lớn ca thật.
- D5 chỉ gỡ bullet **chưa ánh xạ được** để không giẫm lên bảng Symbol: `U+F0B7` của Symbol vẫn ánh xạ
  thành `•` như vòng 8 đã chốt.
- Thứ tự làm gợi ý cho người chia ticket: fixture mới + số vàng hiện trạng **trước** (chốt đường
  chuẩn), rồi các luật, để mỗi luật đổi số vàng một cách nhìn thấy được.
- Vòng 8 từng ghi: *"khi thư viện trả về thứ trông rỗng hoặc trông lạ, kiểm mọi trường trước khi kết
  luận"*. Đợt này thêm vế đối ngẫu vào ADR 0003: *khi thư viện trả về thứ trông **đúng và đầy đủ**
  (level của Word), đừng thay nó bằng phỏng đoán của mình.*
