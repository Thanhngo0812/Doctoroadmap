# F44–F60 — Review đợt A3 / A3'

Vòng review 13 · 2026-09-03 · Phạm vi: [`task/a3-trich-thuc-the/`](../task/a3-trich-thuc-the/) 15/15 ticket

> **Bổ sung sau vòng đầu**: F48 (loại cạnh nghèo), F49 (artifact chưa chạy lại sau vá) và F50 (kiểu
> node không ổn định giữa các section) ghi thêm ở cuối, sau khi soi mã, đối chiếu dấu thời gian và đọc
> `candidates.json`.
>
> **Trạng thái sau xử lý**: bốn artifact đã chạy lại lần cuối bằng algorithm v2. F48 sinh 6 loại cạnh;
> F45 giữ `tool`/`dataset`/`module`/`mechanism` ngoài tập học; F50 lấy đa số và đã phất cờ mâu thuẫn
> xuyên kiểu còn lại. Số cuối nằm trong bảng trạng thái và báo cáo bên dưới.

## Kết luận

**Đợt này có chạy thật, và đó là khác biệt lớn nhất so với vòng 10** — `gemini-3.1-flash-lite`,
350 lời gọi, 452 thực thể, **0 section lỗi**. Ba tầng artifact có thật, hai cơ chế ghi–phát lại riêng
có thật, và **kết luận đường leo công thức được rút ra đúng bằng số**.

Nhưng **ba lỗi 🔴**, và cả ba cùng một dạng: *"cơ chế có mặt nhưng không làm việc nó sinh ra để làm"*.

```
F44  BM25 có mặt        -> không thấy thuật ngữ trong ngoặc, đúng thứ nó sinh ra để bắt
F45  learnable có mặt   -> chưa bao giờ được hỏi, mọi thứ phi-media mặc định true
F48  hệ cạnh mở có mặt  -> prompt không mời, mô hình chỉ đẻ ra requires
```

Hai trong ba (F45, F48) là **lỗ hổng trong ticket tôi viết**, không phải trong việc họ làm.

## Trạng thái xử lý — 2026-09-03

| Mục | Trạng thái | Kiểm chứng sau sửa |
|---|---|---|
| F44 | ✅ Xong | `overfitting`: BM25 không khớp → **hạng 1**; `P(A\|B)` vẫn hạng 1 |
| F45 | ✅ Xong | Schema và điểm tạo candidate đọc `learnable`; 4 CASIO đều `false`; nhóm lỗi đã nêu còn `true`: 0 |
| F46 | ✅ Xong | Thay bằng `cross_section_duplicate_name_ratio`; bỏ `single_chunk_ratio` khỏi A3 trước merge |
| F47 | 🟡 Ghi tồn đọng | Sau chạy lại: XSTK **4,77**, DOCX **18,06**; không nới prompt chung |
| F48 | ✅ Xong | LLM sinh **6 loại cạnh** trên corpus, thay vì chỉ `requires` |
| F49 | ✅ Xong | Bốn artifact cùng algorithm v2/prompt `38ce517a`: ML v6 · XSTK v3 · DOCX v5 · slide v4; 0 section lỗi |
| F50 | ✅ Xong | Bỏ phiếu đa số; `component→false`; cảnh báo xuyên kiểu bắt `Database Transaction` |

Báo cáo thi hành và số liệu đầy đủ: [`report/xu-ly-feedback-f44-f50.md`](../report/xu-ly-feedback-f44-f50.md).

## Kiểm chứng độc lập

| Khẳng định | Kết quả |
|---|---|
| Test | ✅ **178 passed**, exit 0 (115 → 178, **+63**) |
| Không test nào gọi mạng | ✅ — ba khớp `requests`/`urllib` đều là lớp giả và test lỗi |
| Chạy thật toàn corpus | ✅ 350 lời gọi · 452 thực thể · 0 section lỗi |
| Media đúng số | ✅ **19 figure + 60 table**, không thừa không thiếu |
| Mọi media có mô tả | ✅ `missing_media_descriptions: 0` — 11 `generated_multimodal` + 56 `generated_from_content` + 12 chú thích gốc |
| `figure`/`table` không bao giờ learnable | ✅ chặn ở tầng dataclass, `__post_init__` ném lỗi |
| `learnable` nhất quán theo kiểu | ✅ có kiểm, ném lỗi nếu lệch |
| Ba tầng artifact có phiên bản | ✅ `candidates/{doc}/v{n}` thật, manifest có `prompt_hash` |
| `prompt_hash` đổi khi few-shot đổi | ✅ v1 `093b0927` → v2 `9cac43cf` |
| Cạnh đồng vị trí là sàn, xác nhận không xoá được | ✅ có test số cạnh trước/sau |
| **Kết luận đường leo công thức** | ✅ **rút đúng** — xem dưới |

### Chỗ làm tốt nhất đợt: kết luận bộ vàng

```
nhap-mon-ml  recall 80,28%  ·  excess 18,57%
xstk-ch3-1   recall 52,50%  ·  excess 38,24%     <- chênh 27,78 điểm
```

Và báo cáo rút đúng hai kết luận, kể cả kết luận **phủ định**:

> *"Kết luận: thiếu sót tập trung rõ ở chương công thức. Đường leo hợp lý là ticket B0 lưu ảnh cắt
> formula theo bbox; **không nên tiếp tục làm prompt chung mịn hơn vì DOCX đã ở 18,60/1000 (quá mịn)**."*

Vế sau là chỗ đáng khen: nhận ra rằng chữa recall bằng cách nới prompt sẽ **phá tài liệu khác**. Đó là
suy luận mà bộ chỉ số bốn tài liệu sinh ra để cho phép, và nó được dùng đúng ngay lần đầu.

### Một phép đo có giá trị hơn nó trông

```
v2 và v3 của nhap-mon-ml: prompt_hash GIỐNG HỆT (9cac43cf)
  node_jaccard = 1,00      <- node hoàn toàn ổn định
  edge_jaccard = 0,27      <- 73% cạnh KHÁC nhau
```

Cùng mô hình, cùng prompt, cùng nhiệt độ, **cùng tập node** — mà ba phần tư số cạnh không lặp lại. Đây
là tái hiện độc lập phát hiện Frontiers 2026 **bên trong một mô hình duy nhất**, không phải giữa các mô
hình. Nó nói: `temperature = 0` giữ được node nhưng **không giữ được quan hệ**, và mọi thứ đứng trên
cạnh ở đợt sau phải tính tới điều đó.

Toàn bộ bậc thang trên 10 lần chuyển phiên bản, xếp theo cấu hình có đổi hay không:

```
                              node_J   edge_J
CÙNG cấu hình  (v2->v3)        1,000    0,270      <- bất định thuần
đổi prompt     (9 lần)     0,659–0,908  0,056–0,186
```

Hai điều đọc ra. Một: **node ổn định, cạnh thì không** — kể cả khi không đổi gì, hơn 70% cạnh đã khác.
Hai: **đổi prompt thì cạnh gần như bị xoá sạch** — thấp nhất 0,056, tức chỉ ~5% cạnh sống sót qua một
lần chỉnh prompt, trong khi node vẫn giữ được 90%.

Hệ quả cho các đợt sau: mọi thứ xây trên **node** thì tương đối bền qua việc chỉnh prompt; mọi thứ xây
trên **cạnh** — đồ thị tiên quyết, phân tầng, lộ trình — sẽ **dựng lại gần như từ đầu** mỗi lần prompt
đổi. Đó là lý do `prompt_hash` phải nằm trong khoá đóng băng artifact, và là lý do bộ vàng phải đo cạnh
chứ không chỉ đo node.

---

## F44 🔴 — BM25 không thấy thuật ngữ trong ngoặc, đúng thứ nó sinh ra để bắt

### Bằng chứng nằm ngay trong số đo của chính đợt

```
query "overfitting"  ->  dense=8  bm25=None  hybrid=8
```

`overfitting` **có** trong corpus, 2 lần. BM25 vẫn không thấy.

### Cơ chế

Bộ tách token gỡ `.,;:!?"'` ở hai đầu nhưng **không gỡ ngoặc**:

```
văn bản  : 'quá khớp (Overfitting)'  ->  token '(overfitting)'
truy vấn : 'overfitting'             ->  token 'overfitting'
                                          không bao giờ khớp
```

Cả hai lần xuất hiện trong corpus đều là `(Overfitting)`.

### Vì sao nặng hơn một truy vấn hỏng

Đây là **quy ước song ngữ chuẩn của giáo trình Việt** — và chính spec ăn mừng nó ở luật alias:
*"quá khớp (overfitting)"*, *"nhãn (label)"*, *"phán đoán (predict)"*. Mọi thuật ngữ tiếng Anh giới
thiệu theo lối đó đều **vô hình với BM25**.

Đo trên corpus: **369 token phân biệt bị kẹt trong ngoặc** trên tổng 35.614.

Và nó đánh trúng đúng lý do BM25 được thêm vào — ticket 14 viết: *"bù cho vector ở thuật ngữ chính xác,
ký hiệu, tên riêng"*. Thuật ngữ chính xác là thứ nó trượt.

### Sửa

Thêm ngoặc và dấu ngoặc vuông vào tập ký tự gỡ ở **hai đầu** token. Chỉ gỡ ngoài nên `P(A|B)` và
`sync.Mutex` không bị chạm — đã kiểm: `P(A|B)` → `p(a|b)` giữ nguyên.

Kèm test hồi quy: `_tokens('(Overfitting)')` phải khớp truy vấn `overfitting`.

## F45 🔴 — `learnable` chưa bao giờ được hỏi; bốn cái máy tính CASIO là mục học

### Hiện tượng

```
[organization] learnable=True · 'Trường Đại học Sài Gòn'
[tool]         learnable=True · 'Máy tính CASIO fx-500MS'
[tool]         learnable=True · 'Máy tính CASIO fx-570MS'
[tool]         learnable=True · 'Máy tính CASIO fx-500ES'
[tool]         learnable=True · 'Máy tính CASIO fx-570ES'
[database]     learnable=True · 'PostgreSQL'
[dataset]      learnable=True · 'Dữ liệu weather'
```

Bốn kiểu máy tính bỏ túi sẽ xếp tầng và vào giai đoạn lộ trình: *"Giai đoạn 3: Máy tính CASIO fx-500MS"*.
`Trường Đại học Sài Gòn` lấy từ trang bìa.

### Cơ chế

Mã đọc `item.get("learnable", True)` — nhưng **JSON schema gửi cho mô hình không có trường
`learnable`**. Mô hình chưa bao giờ được hỏi, nên nhánh đó **luôn rơi về mặc định `True`**. Một nhánh
đọc thứ không ai ghi.

### Hệ quả đúng bằng lỗi đã sửa cho media

14/373 node học được thuộc các kiểu này (`dataset` 4 · `tool` 7 · `organization` 1 · `technology` 1 ·
`database` 1). Chúng **không có cạnh `requires` nào** — không ai cần học CASIO trước khi học phương sai —
nên ở A9a chúng vào **mẫu số** và bị đếm là **node cô lập**. Đúng hai vế của cơ chế đã làm 79 node media
phá cổng, chỉ khác là lần này thủ phạm do mô hình sinh ra nên không đóng cứng tên kiểu trước được.

### Sửa

Thêm `learnable` vào **schema output**, kèm hướng dẫn ngắn trong prompt: *"người học có phải học và
hoàn thành node này không, hay nó chỉ là bối cảnh?"* Giữ mặc định `True` khi mô hình không khai — bất
đối xứng vẫn đúng. A13 lật cờ cho kiểu rõ ràng sai.

## F46 🟡 — `single_chunk_ratio` luôn bằng 1,0, và đó là **lỗi ticket của tôi**

```
nhap-mon-ml  single_chunk_ratio = 1,0
xstk-ch3-1   single_chunk_ratio = 1,0
```

Không phải trùng hợp: `source_chunk_ids` suy từ danh sách bằng chứng, mà trước merge mỗi ứng viên chỉ có
**một** câu bằng chứng ở **một** chunk. Chỉ số **luôn bằng 1,0 về mặt cấu trúc**.

Ticket 10 của tôi đòi nó làm tín hiệu độ hạt — *"95% node một-chunk nghĩa là đang trích mịn"* — nhưng
tín hiệu đó chỉ có nghĩa **sau merge**, khi cùng một khái niệm ở chương 2, 5, 8 được hợp nhất
`chunk_ids`. Trước merge nó không mang thông tin nào.

Nhân viên cài đặt đúng chữ trong ticket. Chỗ hở ở ticket.

**Thay bằng chỉ số làm được ngay**: **tỉ lệ tên thực thể trùng nhau xuyên section** — bóng của cùng tín
hiệu ở giai đoạn trước merge, tính được từ dữ liệu hiện có. Và chuyển `single_chunk_ratio` sang đợt 2a.

## F47 🟡 — Mật độ lệch dải ở hai tài liệu, và lệch **ngược chiều nhau**

```
nhap-mon-ml    10,97  ✓ trong dải 8–15
naive-bayes    10,20  ✓
xstk-ch3-1      4,87  ✗ QUÁ THÔ
baocao-canhan  18,60  ✗ QUÁ MỊN
```

Hai trên bốn ngoài dải, và **ngược chiều nhau** — nghĩa là prompt không đơn giản là thô hay mịn, mà
**không chuyển giao được giữa thể loại**. Văn xuôi báo cáo bị trích quá mịn; giáo trình đặc công thức bị
trích quá thô.

Báo cáo đã nhận ra và **từ chối chữa bằng cách nới prompt chung** — đúng. Nhưng nó nghĩa là vòng hiệu
chỉnh few-shot của ticket 10 **chưa đóng được**: nó hội tụ cho hai tài liệu, không cho bốn.

Ghi lại như một tồn đọng có số, không phải lỗi triển khai. Cách gỡ khả dĩ ở đợt sau: few-shot theo thể
loại tài liệu, hoặc chấp nhận dải rộng hơn và đo bằng recall thay vì bằng mật độ.

---

## F48 🔴 — Hệ cạnh mở về cơ chế, đóng về kết quả: mô hình chỉ đẻ ra `requires`

### Mã đúng là mở

```python
"edge_type": {"type": "string"}            # schema: chuỗi tự do, KHÔNG enum

def validate_llm_edge_type(edge_type):     # chỉ chặn ĐÚNG hai thứ
    if not value:                  raise   # rỗng
    if value in _REQUIRES_ALIASES: raise   # prerequisite_of · depends_on · needs
    return value                           # còn lại nhận hết
```

### Nhưng trên 452 thực thể và 193 cạnh, chỉ có **ba** loại cạnh

```
requires      124   <- mô hình sinh
tabulates      38   <- CODE sinh (đồng vị trí)
illustrates    31   <- CODE sinh (đồng vị trí)
```

Bỏ hai loại do code sinh thì **mô hình sinh ra duy nhất `requires`**. Không một `example_of`,
`contrasts_with`, `component_of`, `computed_by`, `uses` nào.

### Cơ chế: prompt bất đối xứng giữa node và cạnh

```
node_type là hệ mở. Các ví dụ định hướng là concept, definition, theorem,
algorithm, metric, method; bạn được đặt kiểu mới khi cần.      <- KHAI MỞ + 6 ví dụ

Cạnh tiên quyết chỉ mang tên requires; không dùng prerequisite_of
hay depends_on.                                                <- chỉ nói requires
```

**Loại cạnh duy nhất từng được nhắc tên trong prompt là `requires`.** Không câu nào nói cạnh cũng là hệ
mở, không một ví dụ khác. Mô hình kết luận hợp lý: cạnh = `requires`.

### Đây là lỗ hổng trong ticket tôi viết

Ticket 07 ghi *"Prompt mồi 5–6 kiểu, nói rõ được đặt kiểu mới"* — chữ "kiểu" trong ngữ cảnh đó đọc ra là
**node type**, và nhân viên hiểu đúng như vậy. Tôi **chưa bao giờ yêu cầu mồi loại cạnh**. Kết quả khớp
chính xác thứ tôi đặc tả: **11 kiểu node (giàu), 1 loại cạnh do mô hình sinh (nghèo)**.

### Vì sao đáng mức 🔴

Toàn bộ lập luận cho hệ kiểu mở dựa trên bài giáo dục 08/2026 dùng **tám loại cạnh** và hơn SOTA trước
14–31%. Hiện có một.

Và tool `traverse(node_id, edge_type, direction)` ở pha B — thứ spec gọi là *"chỗ hệ kiểu mở trả lương"* —
**không có gì để đi**, ngoài `requires` mà topo sort đã dùng. Mục tiêu "đồ thị giàu để agent truy vấn",
nêu bốn lần trong quá trình thiết kế, hiện chỉ đạt được ở nửa node.

### Sửa

Thêm vào prompt một câu **đối xứng** với câu `node_type`, kèm ví dụ:

> *"`edge_type` cũng là hệ mở. Ngoài `requires`, hãy đặt tên cho quan hệ bạn thấy: `example_of`,
> `contrasts_with`, `component_of`, `computed_by`, `uses`… Chỉ `requires` là tên dành riêng cho quan hệ
> tiên quyết."*

Rủi ro thấp vì hai lớp bảo vệ đã có: `validate_llm_edge_type` chặn đồng nghĩa `requires`, và luật
**danh sách cho phép** ở A9/A10 khiến thêm bao nhiêu loại cạnh cũng **không chạm được** topo sort. Đây
đúng là lúc dùng tới cái an toàn đã dựng sẵn.

Kèm chỉ số theo dõi: **số loại cạnh phân biệt do mô hình sinh** — hiện 1, và nó phải nhìn thấy được thì
mới biết bản vá có tác dụng.

## F49 🟡 — Ba trên bốn artifact chưa chạy lại sau khi vá

```
mã sửa            : extraction_prompt.py 18:30 · entities.py 18:34 · retrieval.py 18:10
artifact mới nhất : xstk-ch3-1    v1  16:55   <- TRƯỚC vá
                    naive-bayes   v2  16:58   <- TRƯỚC vá
                    nhap-mon-ml   v3  16:59   <- TRƯỚC vá
                    baocao-canhan v3  22:40   ✅ sau vá
```

Bản vá **có tác dụng** — kiểm trên đúng tài liệu đã chạy lại:

```
baocao v2 (trước vá)              baocao v3 (sau vá)
  tool          3 tong · 3 learnable    tool   2 tong · 0 learnable   ✅
  organization  1 tong · 1 learnable    (biến mất)
  technology    1 tong · 1 learnable    (biến mất)
  database      1 tong · 1 learnable    (biến mất)
```

Nhưng ba tài liệu kia vẫn mang dữ liệu cũ, nên **số vàng bốn tài liệu và mọi con số trong báo cáo hiện
mô tả trạng thái trước vá** — kể cả bốn cái máy tính CASIO ở F45 (chúng nằm trong `xstk`, artifact 16:55).

Đây đúng hình dạng **F41 vòng 10**: bản vá nằm trong mã, kho artifact còn đời cũ, và người mở `inspect`
thấy trạng thái tuần trước. Sửa: ingest lại đủ bốn tài liệu, cập nhật số vàng, và **đo lại F45 trên dữ
liệu sau vá** để biết còn bao nhiêu node học được sai.

## F50 🟠 — Kiểu node không ổn định giữa các section, và `learnable` đi theo nó

### Toàn bộ các lần nổ, trên 14 phiên bản artifact

| Tài liệu | Ver | Giờ | Kiểu mâu thuẫn | Số entity | Ép về |
|---|---|---|---|---:|---|
| nhap-mon-ml | v4 | 22:45 | `concept` | 51 | `true` — **đúng** |
| nhap-mon-ml | v5 | 23:00 | `concept` | 50 | `true` — **đúng** |
| baocao-canhan | v3 | 22:40 | `concept` | 30 | `true` — **đúng** |
| baocao-canhan | v4 | 22:53 | **`component`** | **3** | `true` — **đáng ngờ** |

Ranh giới thời gian nói lên tất cả:

```
7 phiên bản 16:41–16:59  ->  0 mâu thuẫn    (trước vá F45: learnable luôn true, không thể mâu thuẫn)
7 phiên bản 22:40–23:05  ->  4 mâu thuẫn    (sau vá: mô hình thật sự phán, và phán không nhất quán)
```

**4/7 lần chạy sau vá có mâu thuẫn — 57%.** Không phải ca hiếm.

Ba lần đầu ép `concept` về `true` là đúng. Lần thứ tư ép `component` về `true` thì đáng ngờ, vì hai kiểu
gần nghĩa nhất của nó trong cùng tài liệu — `module` và `mechanism` — đều được mô hình đặt **false**.

Hai tài liệu còn lại (`xstk`, `naive-bayes`) không mâu thuẫn lần nào.

### Nhưng cơ chế nhất quán-theo-kiểu không bắt được ca nặng nhất

```
[component ] learnable=True  · 'Module Auctions'
[module    ] learnable=False · 'Module Auctions'      <- CÙNG MỘT THỨ, hai kiểu, hai learnable
[mechanism ] learnable=False · 'Database Transaction'
[concept   ] learnable=True  · 'Database Transaction'
```

Luật hiện tại soi mâu thuẫn **bên trong một kiểu**. Ở đây mâu thuẫn nằm **giữa các kiểu** — cùng một
thực thể được hai section gán hai `node_type`, nên mỗi kiểu tự nó nhất quán và không cờ nào phất.

### Quy mô, đo trên bản mới nhất của cả bốn tài liệu

```
                  entity   ten mang NHIEU kieu   learnable NGUOC NHAU
nhap-mon-ml   110        4                     0
xstk-ch3-1    202        7                     0
baocao-canhan  75        3                     2      <- ca hai deu o day
naive-bayes    72        4                     0
```

**18/459 tên (≈4%) mang nhiều kiểu**, nhưng chỉ 2 gây hại. Lý do rõ: ở hai giáo trình các kiểu tranh
nhau (`concept` vs `metric` vs `algorithm` vs `method`) **đều learnable=true** nên chia kiểu vô hại.
Rủi ro chỉ hiện ra khi các kiểu tranh nhau **nằm hai bên ranh giới learnable** — và `baocao` là tài
liệu duy nhất có kiểu không-học-được.

### Cách gỡ mâu thuẫn hiện tại cũng có chỗ yếu

Ép về `true` là **đúng hướng đã gây ra F45**. Kịch bản với dữ liệu đang có: `xstk` có `tool` 4 entity,
learnable=false — đúng, CASIO không phải mục học. Chỉ cần **một** section lỡ khai `tool: true` là cả bốn
lật sang true, và cảnh báo chỉ báo **sau khi** đã lật. Một phiếu sai lật bốn phiếu đúng.

Với `concept` thì ép-true đúng. Với `component` ở `baocao/v4` thì đáng ngờ: hai kiểu gần nghĩa nhất của
nó — `module` và `mechanism` — đều được mô hình đặt **false**, chỉ `component` thành true **vì bị ép**.

### Sửa

1. **Bỏ phiếu theo đa số** thay cho ép-true. `concept` có 50 phiếu nên một phiếu lạc không lật nổi;
   `tool` có 4 phiếu false nên một phiếu true cũng không. Hoà phiếu mới rơi về `true` — giữ nguyên bất
   đối xứng "thừa rẻ hơn thiếu".
2. **Thêm cảnh báo cho mâu thuẫn xuyên kiểu**: cùng một tên chuẩn hoá mang nhiều `node_type` mà
   `learnable` khác nhau ⇒ phất cờ. Đây là ca hiện đang im lặng.
3. **Ghi vào spec 2a**: merge sẽ gặp ứng viên **khác kiểu nhau**, và spec chưa nói kiểu nào thắng.
   `learnable` đi theo kiểu, nên chọn kiểu là chọn luôn learnable — không nên để việc đó xảy ra ngầm.

### Hai số phụ đáng nhìn, cùng lấy từ `stats`

```
orphan_media_ratio       = 0,556   (5/9 media của nhap-mon-ml mồ côi — cao)
rejected_confirmation_labels = 8   so với confirmed_media_edges = 6
```

Tỉ lệ mồ côi 56% đúng thứ ticket 04 dặn theo dõi (*"cao bất thường nghĩa là A3 không trích được gì ở
chunk có ảnh"*). `unknown_orphan_media = 0` nên mọi ca đều có lý do — chưa phải lỗi, nhưng đáng đối
chiếu sau khi mật độ được hiệu chỉnh.

## Ba chỗ tôi phải sửa của chính mình

**Ticket 07 mồi `dataset` làm kiểu mẫu, trong khi §0.1 lấy `dataset` làm ví dụ điển hình của kiểu
KHÔNG học được.** Spec tự mâu thuẫn, nhân viên làm theo vế đầu. `dataset` xuất hiện 4 lần, learnable
toàn bộ — hệ quả trực tiếp. Bỏ `dataset` khỏi danh sách mồi, hoặc mồi kèm cờ `learnable: false`.

**Ticket 10 đòi một chỉ số không thể hoạt động ở giai đoạn này** — F46.

**Ticket 07 mồi kiểu node nhưng quên mồi loại cạnh** — F48. Cùng một chữ "kiểu" gánh hai nghĩa, và tôi
chỉ đặc tả một nửa. Đây là lần thứ hai trong đợt này một ticket của tôi cho ra đúng thứ nó viết mà không
phải thứ nó muốn.

**Tôi nghi `node_jaccard = 1,0` là mâu thuẫn số liệu, và tôi sai.** Tôi đọc *"ML tăng 81→98"* trong báo
cáo là v2→v3, thực ra là v1→v2 (đổi few-shot). v2 và v3 cùng `prompt_hash`, nên 1,0 là kết quả thật của
hai lần chạy cùng cấu hình. Kiểm bằng manifest mới thấy — lần thứ năm trong dự án một phép đọc vội suýt
thành kết luận sai.

---

# Vòng 14 — Kiểm chứng sau sửa, và hai phát hiện mới (2026-09-04)

## Bảy mục F44–F50: kiểm lại từng cái, không đọc dấu tích

| Mục | Kiểm chứng độc lập |
|---|---|
| Test | ✅ **186 passed**, exit 0 (178 → 186) |
| **F44** | ✅ `_strip_outer_punctuation` gỡ **cặp ngoặc khớp nhau**: `(Overfitting)`→`overfitting`, `[figure]`→`figure`, mà `P(A\|B)`→`p(a\|b)` **giữ nguyên**. Trên dữ liệu thật: `overfitting` từ `bm25=None` lên **hạng 1**, hybrid 8→2 |
| **F45** | ✅ `ENTITY_SCHEMA` có `"learnable": {"type": "boolean"}` nằm trong `required`. Kiểu không-học-được nay: `figure` · `table` · `tool` · `dataset` · `component` · `mechanism` · `module`. CASIO/organization/database **hết** learnable |
| **F46** | ✅ `single_chunk_ratio` thay bằng `cross_section_duplicate_name_ratio` |
| **F47** | 🟡 vẫn lệch 2/4 — xstk **4,77** · baocao **18,06**. Ghi tồn đọng, không nới prompt chung |
| **F48** | ✅ 4–6 loại cạnh mô hình sinh mỗi tài liệu: `component_of` · `computed_by` · `contrasts_with` · `example_of` · `requires` · `uses` |
| **F49** | ✅ cả bốn cùng `prompt_hash=38ce517a`: ML v6 · XSTK v3 · DOCX v5 · slide v4 |
| **F50** | ✅ bỏ phiếu đa số bằng `Counter`, hoà thì về `true`. `component` nay **`resolved_false`** — đúng chiều tôi nghi. Cảnh báo xuyên kiểu đã phất: `cross_type_learnable_conflict: Database Transaction (concept=true, mechanism=false)` |

### Cách sửa F44 khôn hơn đề xuất của tôi

Tôi đề nghị thêm ngoặc vào tập ký tự gỡ hai đầu. Họ làm chặt hơn: **chỉ gỡ khi hai đầu là một cặp khớp
nhau**, lặp cho ngoặc lồng. Nên `(0,0412` — ngoặc mở không có ngoặc đóng — **không** bị gỡ, còn
`P(A|B)` an toàn theo cấu trúc chứ không nhờ may.

### Độ ổn định nay có bốn điểm đo thay vì một

```
                      node_J   edge_J     (cùng prompt_hash)
nhap-mon-ml v5→v6      1,000    0,321
xstk        v2→v3      1,000    0,200
baocao      v4→v5      1,000    0,234
naive-bayes v3→v4      1,000    0,200
```

**Node ổn định tuyệt đối 4/4.** Cạnh 0,20–0,32 — phát hiện vòng 13 lặp lại trên cả bốn tài liệu, không
còn là một phép đo lẻ.

### Recall bộ vàng giảm — kiểm ra là dao động, không phải thoái lui

```
nhap-mon-ml  0,803 -> 0,775
xstk-ch3-1   0,525 -> 0,475
```

Nghi ngờ đầu: `entity_recall` lọc `if entity.learnable`, nên siết `learnable` sẽ **cơ học** kéo recall
xuống. Kiểm trực tiếp: **không một thực thể nào trong bộ vàng bị đánh non-learnable** trên cả hai
chương. Nên không phải hệ quả của F45/F50 — đó là dao động, nằm trong dải `node_jaccard` 0,84–0,90 khi
đổi prompt.

Nhưng nó lộ một điều đáng ghi: **recall đang báo tới ba chữ số thập phân trên phép đo có đầu vào dịch
~10% giữa hai lần chạy.** 0,775 và 0,803 không phân biệt được với nhau. Bộ vàng nên chạy vài lần rồi
báo khoảng, không báo một số.

### Bộ vàng dựng đúng chuẩn

`blind_before_first_a3_run: True` · section hiệu chỉnh gắn `include_in_score: False` · chính sách gán
ghi rõ (*"loại: ví dụ, tên sản phẩm, biến, tham số công thức"*) · `source_hash` và
`chunks_version_at_annotation` ghim. Đúng ticket 11, không cắt góc chỗ nào.

---

## F51 🟡 — Núm vặn quan trọng nhất nằm trong mã nguồn, không có đường chỉnh từ ngoài

### Hiện trạng

`DEFAULT_FEW_SHOT` nằm ở **dòng 43 của một module Python 220 dòng**. Đường duy nhất để thay là tham số
Python `few_shot=`; **`config.py` và CLI không có lối vào nào**.

### Vì sao đó là chỗ sai

Spec D11 nói rõ: *"Không có tham số `granularity`. **Núm vặn thật là ví dụ few-shot**"*. Ticket 10 đòi
vòng hiệu chỉnh: đo mật độ → chỉnh ví dụ → đo lại.

Và vòng đó **chưa đóng**: mật độ còn lệch 2/4 (xstk 4,77 · baocao 18,06), ngược chiều nhau. Việc chỉnh
ví dụ sẽ còn lặp nhiều lần. **Thứ được sửa nhiều nhất lại là thứ đòi sửa mã nguồn.**

Hệ quả: mỗi vòng hiệu chỉnh là một commit mã; diff trộn văn xuôi với code; không A/B được hai bộ ví dụ
từ dòng lệnh; và người hiểu nội dung giáo trình nhất chưa chắc là người sửa Python thoải mái nhất.

### Một tệp 220 dòng đang gánh bốn loại thứ có nhịp thay đổi khác hẳn nhau

```
SEED_NODE_TYPES        cấu hình
SYSTEM_PROMPT          văn bản       <- sửa khi đổi luật trích
DEFAULT_FEW_SHOT       văn bản       <- SỬA NHIỀU NHẤT (núm độ hạt)
3 × *_INSTRUCTION      văn bản
ENTITY_SCHEMA          hợp đồng
VALIDATION_SCHEMA      hợp đồng
prompt_hash + 4 hàm    logic
```

### Chỗ KHÔNG phải vấn đề, nói rõ để khỏi sửa nhầm

`ENTITY_SCHEMA` nằm ở tầng `application` **không** vi phạm phân tầng: nó là **JSON Schema chuẩn**, và
adapter Gemini tự ánh xạ sang `responseJsonSchema` của nó. Đổi nhà cung cấp thì adapter đổi tên trường,
schema giữ nguyên. Thiết kế đúng — đừng đẩy xuống `infrastructure`.

### Sửa

Tách **văn bản** khỏi **mã**: bốn khối prompt và bộ few-shot thành tệp dữ liệu cạnh module, nạp lúc
dựng. Thêm đường ghi đè qua `Settings`/CLI để trỏ tới bộ few-shot khác. Giữ nguyên `prompt_hash` — nó
đã băm cả nội dung few-shot nên tách tệp **không** làm mất tính vô hiệu hoá artifact.

Lợi ích trực tiếp: A/B hai bộ ví dụ thành hai lần chạy khác tham số, và diff của một vòng hiệu chỉnh
chỉ còn văn xuôi.

## F52 🟡 — Prompt nên viết bằng tiếng Anh: đo được **−24% token**, và phần ví dụ thì không

### Đo trước, bàn sau

Tôi dịch nguyên `SYSTEM_PROMPT` sang tiếng Anh giữ đủ mọi ràng buộc — bằng chứng nguyên văn, hệ kiểu mở,
tên dành riêng, luật `learnable`, luật mô tả media, `confirmed_entities` — rồi đếm bằng cùng một
tokenizer:

```
SYSTEM_PROMPT tiếng Việt : 1.928 ký tự · 522 token
SYSTEM_PROMPT tiếng Anh  : 1.840 ký tự · 396 token
chênh lệch               :            -126 token  (-24,1%)
```

Toàn bộ scaffolding hiện tại mỗi lượt gọi:

```
SYSTEM_PROMPT            522 token
DEFAULT_FEW_SHOT         243
SECTION_INSTRUCTION       21
GLEAN_INSTRUCTION         57
VALIDATION_INSTRUCTION    44
                       ------
                         887 token / lượt
```

Với **350 lượt gọi** một lần chạy corpus, riêng phần hệ thống chuyển sang tiếng Anh tiết kiệm khoảng
**44.000 token**. Và đây là chi phí trả **mỗi lượt**, kể cả mọi vòng quét lại.

> **Cảnh báo về phép đo**: đếm bằng tokenizer Gemma vì Gemini **không có tokenizer chạy offline** (ràng
> buộc đã ghi từ B0). Nên tỉ lệ là **chỉ báo, không phải con số chính xác** cho Gemini. Nhưng 24% đủ
> lớn để khó đảo chiều.

### Ba lý do khác, xếp theo độ chắc của bằng chứng

| Lý do | Bằng chứng |
|---|---|
| **Token rẻ hơn 24%** | **Đo được**, ở trên |
| Hướng dẫn tiếng Anh dễ được tuân thủ hơn | Quan sát phổ biến của ngành, **dự án chưa đo** — đừng ghi như sự thật |
| Dễ đổi nhà cung cấp | Tài liệu và quy ước prompt của mọi nhà cung cấp đều tiếng Anh trước |

### Nhưng **hướng dẫn** và **ví dụ** là hai thứ khác nhau

Đây là chỗ quan trọng nhất, và nó quyết định phạm vi việc phải làm.

```
SYSTEM_PROMPT              -> tiếng Anh    (hướng dẫn thuần)
3 × *_INSTRUCTION          -> tiếng Anh    (hướng dẫn thuần)
DEFAULT_FEW_SHOT
   nhãn: "CHUNK_TEXT:", "TRÍCH:", "KHÔNG TRÍCH:"   -> tiếng Anh
   đoạn trích giáo trình                            -> GIỮ TIẾNG VIỆT
```

Đoạn `"Quá khớp (Overfitting) xảy ra khi mô hình khớp dữ liệu huấn luyện nhưng tổng quát kém"`
**không dịch được** — nó không phải câu văn minh hoạ, nó **là văn bản corpus**. Nó tồn tại để dạy độ hạt
*trên đúng loại chữ mô hình sẽ gặp*. Dịch sang tiếng Anh là biến ví dụ thành thứ không còn giống dữ liệu
thật, và độ hạt là thứ nhạy với chuyện đó.

Nên khuôn đúng là **scaffolding tiếng Anh, dữ liệu minh hoạ giữ tiếng bản địa** — không phải "dịch hết".

### Chi phí đổi, và cách trả nó một lần

`prompt_hash` băm cả `SYSTEM_PROMPT` lẫn few-shot, nên đổi ngôn ngữ ⇒ hash mới ⇒ **chạy lại cả bốn tài
liệu**. Ở quy mô 350 lượt thì đó là một lần chạy, không đáng ngại — và nó **bắt buộc** phải xảy ra, vì
đó chính là cơ chế chống tái dùng artifact cũ im lặng.

Quan trọng hơn: **lần chạy lại đó chính là phép đo**. Bộ vàng và bộ chỉ số mật độ đã sẵn, nên so
Việt–Anh là hai con số recall và bốn con số mật độ, không phải một cuộc tranh luận.

### Việc này gắn với F51

Chừng nào prompt còn nằm trong module Python thì đổi ngôn ngữ là **sửa mã**, và giữ song song hai bản để
so là **hai nhánh mã**. Tách văn bản ra tệp dữ liệu (F51) biến nó thành **hai tệp và một tham số CLI**.

Nên thứ tự hợp lý: **F51 trước, F52 sau** — tách xong thì việc đổi ngôn ngữ và việc đo nó gần như miễn phí.

### Đề nghị

1. **Chuyển `SYSTEM_PROMPT` và ba chuỗi hướng dẫn sang tiếng Anh.** Lợi ích token đo được, rủi ro thấp.
2. **Giữ đoạn trích giáo trình trong few-shot bằng tiếng Việt**; chỉ dịch nhãn bao quanh.
3. **Đo, đừng tin**: chạy lại bốn tài liệu, so recall bộ vàng và mật độ với bản hiện tại. Nếu chất lượng
   ngang nhau thì lấy bản rẻ hơn; nếu tệ hơn thì quay lại và **đã có số để biết vì sao**.
4. Ghi kết quả vào số vàng — đây là lần đầu dự án có hai bản prompt để so, và đó là dữ liệu đáng giữ.

---

# Vòng 15 — Trạng thái xử lý F51–F52 (2026-09-04)

| Mục | Trạng thái | Kiểm chứng sau sửa |
|---|---|---|
| F51 | ✅ Xong | 5 khối văn bản ở `application/prompts/*.txt`; `Settings` và `extract`/`a3 --few-shot` cùng đi qua `load_prompts`; hash băm nội dung |
| F52 | ✅ Xong, đã A/B thật | System prompt **522→401 token (−23,2%)**; gold recall ML **77,46→83,10%**, XSTK **47,50→57,50%** |

Bốn artifact tiếng Anh dùng chung `prompt_hash=8e7c14c3`: ML v7 · XSTK v4 · DOCX v6 · slide v5.
Tổng **363 lời gọi · 474 thực thể · 0 section lỗi · 0 media thiếu mô tả**. Corpus vào dải đích
7,57→8,10 node học được/1000 token. F47 vẫn được giữ nguyên vì XSTK còn thô (5,13), DOCX còn mịn và
mịn hơn (19,70); không nới prompt chung.

Jaccard node/cạnh so với bản tiếng Việt: ML 0,948/0,099 · XSTK 0,795/0,116 · DOCX 0,765/0,148 · slide
0,741/0,103. Bản tiếng Anh được giữ vì recall tăng ở cả hai chương gold, excess cùng giảm, trong khi
system prompt rẻ hơn khoảng 23% theo tokenizer offline đã ghim.

Kiểm chứng cuối: **190 passed**, gồm cả 5 integration test; wheel chứa đủ 5 prompt file. Báo cáo chi tiết:
[`report/xu-ly-feedback-f44-f50.md`](../report/xu-ly-feedback-f44-f50.md).

---

# Vòng 16 — Kiểm chứng độc lập F51/F52, kiểm lại F44–F50 (2026-09-08)

Mã đã đổi tiếp sau vòng 14 (prompt ra tệp, chuyển tiếng Anh), nên **kiểm lại toàn bộ chín mục**,
không chỉ hai mục mới.

> **Bản tự báo của nhân viên khớp chính xác phép đo độc lập của tôi** — 522→401 token (−23,2%),
> recall 77,46→83,10 và 47,50→57,50, bốn cặp Jaccard, 190 passed. Không một con số nào lệch. Đây là
> lần đầu trong mười sáu vòng tôi kiểm mà không tìm thấy chỗ nào bản bàn giao nói quá.

| Mục | Trạng thái | Kiểm chứng độc lập |
|---|---|---|
| Test | ✅ | **190 passed**, exit 0 (186 → 190) |
| **F44** | ✅ giữ | `(Overfitting)`→`overfitting` · `P(A\|B)`→`p(a\|b)` · `(0,0412` không bị gỡ |
| **F45** | ⚠️ cơ chế giữ, kết quả trôi | Schema vẫn có `learnable`, prompt vẫn hỏi — nhưng xem **F53** |
| **F46** | ✅ | `cross_section_duplicate_name_ratio` chạy thật: 0,292–0,590. Kèm `granularity_band` phân loại `target`/`coarse`/`fine` |
| **F47** | 🟡 tồn đọng, **xấu đi một chút** | xstk 4,77→**5,13** (đỡ hơn) · baocao 18,06→**19,70** (lệch thêm) |
| **F48** | ✅ | 5–8 loại cạnh mỗi tài liệu, tăng từ 4–6 |
| **F49** | ✅ | Bốn artifact cùng `prompt_hash=8e7c14c3`: ML v7 · XSTK v4 · DOCX v6 · slide v5 |
| **F50** | ✅ cơ chế | Bỏ phiếu đa số chạy, cảnh báo phất trên ML v7 — nhưng xem **F53** |
| **F51** | ✅ | 5 tệp `application/prompts/*.txt` · `Settings.extraction_few_shot` · cờ CLI `--few-shot` |
| **F52** | ✅ **và có đo** | Xem dưới |

> **Một đính chính của tôi**: tôi báo `cross_section_duplicate_name_ratio = None` khi dò lần đầu. Sai —
> chỉ số nằm lồng trong `stats.metrics`, không ở `stats` mức gốc. F46 chạy đúng.

## F52 — lần đầu dự án quyết một câu hỏi prompt bằng số, không bằng lý lẽ

Vòng 14 tôi đề nghị: chuyển hướng dẫn sang tiếng Anh, **giữ đoạn trích giáo trình bằng tiếng Việt**, rồi
**đo chứ đừng tin**. Cả ba đều được làm.

```
system.txt      tiếng Anh          "Extract knowledge TAUGHT in the current section only…"
few-shot.txt    nhãn tiếng Anh     "EXTRACT:" · "DO NOT EXTRACT:"
                đoạn trích         "Quá khớp (Overfitting) xảy ra khi…"   <- GIỮ TIẾNG VIỆT
```

### Chi phí giảm đúng như đo trước

```
                TRƯỚC   SAU    chênh
system            522    401   -23%
few_shot          243    234    -4%   <- đúng, vì đoạn trích không dịch
ba instruction    122    110
                -----  -----
                  887    745   -16%     -> ~49.700 token / lần chạy corpus
```

### Và chất lượng **tăng**, không phải giữ nguyên

```
             recall bộ vàng
             Việt  ->  Anh
nhap-mon-ml  0,775 -> 0,831    +5,6 điểm
xstk-ch3-1   0,475 -> 0,575   +10,0 điểm
```

Cả bốn tài liệu đều tăng mật độ; xstk nhích về phía dải đích (4,77→5,13).

Họ còn ghi `prompt_translation_jaccard` — đúng thứ vòng 14 yêu cầu:

```
             node    edge
nhap-mon-ml  0,948   0,099
xstk         0,795   0,116
baocao       0,765   0,148
naive-bayes  0,741   0,103
```

**Đọc con số này cho đúng**: node lệch 5–26% giữa hai bản prompt, nên ±5 điểm recall nằm trong dải dao
động. Riêng xstk +10,0 thì lớn hơn dải đó. Thuyết phục hơn cả hai con số là **hướng nhất quán**: bốn
mật độ đều tăng, hai recall đều tăng, không có ngoại lệ.

Kết luận: **rẻ hơn 16% và không tệ hơn về chất lượng.** Đó là đủ để chốt, và nó được chốt bằng dữ liệu
chứ không bằng tranh luận — lần đầu trong dự án cho một câu hỏi về prompt.

---

## F53 🟠 — Bỏ phiếu đa số bất lực với kiểu hiếm, mà kiểu hiếm chính là chỗ cần nó

### Bằng chứng: sáu phiên bản của cùng một tài liệu

```
baocao-canhan, kiểu ngoài concept/method/algorithm/figure/table:

v1  093b  tool(2,True)  organization(1,True)  technology(1,True)  database_system(1,True) …
v2  9cac  tool(3,True)  organization(1,True)  technology(1,True)
v3  dbc0  tool(2,False)                                            <- vá F45 vào
v4  38ce  tool(1,False) component(3,True)  mechanism(1,False) module(1,False)
v5  38ce  tool(1,False) component(3,False) mechanism(1,False) module(1,False)   <- vá F50 vào
v6  8e7c  tool(1,True)  component(2,True)                          <- prompt tiếng Anh
```

`tool` đi **True → False → False → True**. `component` đi **True → False → True**. Không phải thoái lui
của bản dịch — đó là **dao động**, và nó có mặt từ trước khi đổi ngôn ngữ.

### Vì sao bỏ phiếu đa số không cứu được

Đếm trên bốn artifact mới nhất: **8/27 kiểu có ≤2 thực thể.**

```
nhap-mon-ml    metric(1) · theorem(1)
baocao         architecture(1) · component(2) · tool(1)
naive-bayes    figure(2) · metric(2) · theorem(2)
```

`concept` có **61 phiếu** — một phiếu lạc không lật nổi, đa số làm việc hoàn hảo. `tool` có **một
phiếu** — "đa số" của nó chính là phán đoán đơn lẻ đó, không có gì để bỏ phiếu.

Và đây là chỗ đau: **kiểu hiếm chính là các kiểu ứng viên không-học-được** — `tool`, `dataset`,
`organization`, `component`. Kiểu đông (`concept`, `method`, `algorithm`) thì learnable=true hiển nhiên,
chưa bao giờ có nguy cơ.

Nên F50 ổn định hoá đúng phần **chưa bao giờ gặp rủi ro**, và để nguyên phần có rủi ro.

### Hệ quả thực tế

`Makefile` (tool) và `ReadPump`/`WritePump` (component) hiện `learnable=true` — chúng sẽ xếp tầng và vào
giai đoạn lộ trình. Nhẹ hơn ca CASIO nhiều (đây là ca biên thật, tranh luận được), nhưng cơ chế thì
giống hệt: **một phán đoán đơn lẻ của mô hình quyết định một kiểu có vào lộ trình hay không, và nó đổi
mỗi lần chạy.**

### Sửa: sổ đăng ký kiểu phải **sống qua các lần chạy**

Hiện `type_registry` được dựng lại từ đầu mỗi lần chạy, nên mọi quyết định `learnable` đều là suy diễn
tươi từ 1–2 phiếu.

Đề nghị: sổ đăng ký là **artifact bền**, và `learnable` của một kiểu đã được người xác nhận ở A13 thì
**không bị suy diễn lại** — chỉ đổi khi người đổi.

Đây đúng nguyên tắc **ADR 0003 — tin dữ liệu khai báo, suy diễn là dự phòng**, chỉ là áp cho một loại
dữ liệu khai báo mới: phán quyết của người, thay vì cấp tiêu đề của Word. Suy diễn từ mô hình là **dự
phòng cho kiểu chưa ai duyệt**, không phải nguồn chân lý mỗi lần chạy.

Kèm một lưới an toàn rẻ: **kiểu có ≤2 thực thể phát cảnh báo `learnable_low_confidence`** — để người
review biết đâu là phán quyết dựa trên một phiếu, thay vì trộn lẫn với kiểu 61 phiếu.

## F47 — ghi lại vì nó xấu đi

```
             vòng 14  ->  vòng 15
xstk           4,77   ->   5,13    (đỡ hơn, vẫn dưới dải)
baocao        18,06   ->  19,70    (lệch THÊM)
```

Prompt tiếng Anh kéo mật độ **lên** ở cả bốn tài liệu — tốt cho xstk đang quá thô, nhưng đẩy baocao
đang quá mịn ra xa hơn. Nó xác nhận lại chẩn đoán vòng 13: **một prompt chung không chuyển giao được
giữa thể loại**, và chỉnh chung sẽ luôn cải thiện một đầu bằng cách làm hỏng đầu kia.

Giờ F51 đã cho phép chọn bộ few-shot lúc chạy, nên đường gỡ đã mở: **bộ few-shot theo thể loại**, không
phải một bộ cho tất cả.

### Trạng thái xử lý F53 (2026-09-08)

Đã thêm registry quyết định người duyệt tại `<artifact_dir>/type_registry.json`, ưu tiên hơn bỏ phiếu,
đọc lại mỗi lần chạy và đưa nội dung duyệt vào khóa cache. Kiểu chưa duyệt có ≤2 ứng viên được cảnh báo
`learnable_low_confidence`; figure/table do code quyết định nên không thuộc cảnh báo suy diễn này.
Không tự duyệt tool/component thay người; hiện review bằng tệp JSON, chưa có giao diện A13.

**202 test pass**, gồm integration. Test hồi quy đã thất bại trên code cũ vì tái dùng cache sau đổi
quyết định; sau sửa chứng minh node không học được không còn embedding. Không chạy lại corpus mô hình
thật, không thay số A/B vòng 15. F47 vẫn mở. [Hướng dẫn và kiểm chứng](../report/xu-ly-feedback-f53.md).

---

# Vòng 17 — Kiểm chứng F53 (2026-09-08)

## Cơ chế đúng, và tôi kiểm bằng thực nghiệm chứ không đọc mã

| Khẳng định | Kiểm chứng |
|---|---|
| Test | ✅ **202 passed**, exit 0 (190 → 202) |
| Bốn test nêu tên có thật | ✅ đúng bốn, đúng tệp: `test_a3_extract.py:428,468` · `test_a3_artifacts.py:9,27` |
| Không có tệp ⇒ rơi về suy diễn | ✅ trả `{}` |
| Chỉ đọc mục `reviewed: true` | ✅ `component` với `reviewed:false` bị loại, `tool`/`concept` được nhận |
| **Chặn lách bất biến I-G1** | ✅ `figure`/`table` trong sổ ⇒ **từ chối**, không cho ghi `figure: learnable=true` |
| Từ chối tên chưa chuẩn hoá | ✅ `'Tool '` ⇒ *"kiểu chưa chuẩn hoá"* |
| Từ chối giá trị sai kiểu | ✅ `learnable: 'no'` và `node_types: []` đều ném lỗi |
| Đổi sổ ⇒ mất cache | ✅ `reviewed_node_types` nằm trong `config`, mà `config_hash = _hash(config)` |
| Không thoái lui F44/F45/F48/F52 | ✅ tokenizer, schema `learnable`, lời mời đặt tên cạnh, prompt tiếng Anh — còn nguyên |

### Chỗ đúng nhất của đợt: hàng rào chống lách I-G1

`load_reviewed_node_types` gọi `validate_llm_node_type`, nên **không ai ghi được `figure: learnable=true`
vào sổ đăng ký**. Nếu thiếu hàng rào đó thì bước áp dụng gán thẳng `entity.learnable = value`, **bỏ qua
`__post_init__`** của dataclass — tức sổ đăng ký sẽ thành đường vòng qua bất biến media. Họ bịt đúng chỗ
đó, và tôi phải thử mới thấy nó được nghĩ tới.

### Và bản báo cáo tự khai đúng chỗ

> *"Ví dụ **minh họa**, không phải quyết định đã duyệt… Chưa tự phán quyết Makefile/ReadPump/WritePump
> thay người dùng… Số corpus vòng 15 là số lịch sử, **không phải kết quả chạy lại F53**."*

Tôi vào kiểm với giả thiết đây là **F49 lặp lần thứ ba** — mã sửa, artifact đời cũ. Đúng là artifact còn
ở `a3-section-conversation-v2` trong khi mã đã lên `v3`, và không có `type_registry.json` nào.

Nhưng lần này **khác về bản chất**: F53 tồn tại để nói *"phán quyết này thuộc về người"*. Nhân viên tự
điền `tool: false` vào sổ chính là làm đúng cái việc mà cơ chế sinh ra để ngăn. **Từ chối quyết thay là
hành xử đúng**, và họ ghi rõ mình đang từ chối.

---

## F54 🟡 — Cơ chế có, nhưng **không có đường tạo ra đầu vào cho nó**

### Trạng thái hiện tại

```
type_registry.json        : KHÔNG tồn tại
artifact                  : a3-section-conversation-v2   (mã đã ở v3)
learnable_low_confidence  : chưa từng phát trên dữ liệu thật
Makefile / ReadPump       : vẫn learnable=true trong artifact đang lưu
```

Đây là trạng thái **chờ người quyết** — hợp lệ. Nhưng nó **vô hình**: nhìn vào repo không phân biệt được
"sổ rỗng vì cố ý" với "sổ rỗng vì quên".

### Người soát ở A13 lấy danh sách việc ở đâu?

Không ở đâu. Cảnh báo `learnable_low_confidence` chỉ xuất hiện **trong đầu ra một lần chạy**, mà chưa có
lần chạy nào. Để biết cần duyệt kiểu nào, hiện phải hoặc chạy lại toàn bộ pipeline, hoặc viết mã đọc
artifact — tôi phải làm cái thứ hai để có bảng dưới:

```
kiểu          ứng viên   learnable   ví dụ
metric               3      True     Test error, standard deviation
theorem              3      True     Định lý No Free Lunch, Công thức Bayes
component            2      True     ReadPump, WritePump
architecture         1      True     Mô hình Hub - Client
tool                 1      True     Makefile
```

**Năm kiểu.** Đó là toàn bộ việc của A13 cho corpus này — nhỏ, làm trong vài phút, nhưng **không ai
nhìn thấy được nó** nếu không viết mã.

### Đề nghị: một lệnh, theo đúng khuôn ba lệnh đã có

Dự án đã có `a3-report`, `a3-compare`, `a3-evaluate`. Thêm một lệnh nữa đọc artifact mới nhất và in
đúng bảng trên — kèm cột `reviewed` để thấy cái nào đã quyết, cái nào chưa.

Nó biến A13 từ *"chạy lại pipeline rồi đọc cảnh báo"* thành *"chạy một lệnh, sửa năm dòng JSON"*.

### Một quan sát tempering: hiếm ≠ không-học-được

Nhìn bảng trên thì **3/5 kiểu rõ ràng là học được** — `theorem` (Định lý Bayes), `metric` (Test error),
`architecture` (mô hình Hub-Client) đều là thứ người học phải học. Chúng chỉ tình cờ **hiếm trong corpus
này**.

Chỉ **2/5** là ca thật cần cân nhắc: `tool` (Makefile) và `component` (ReadPump/WritePump).

Nên cảnh báo `learnable_low_confidence` đang đúng về cơ chế nhưng **tỉ lệ tín hiệu thấp** — nó nêu năm
thứ để người nhìn hai. Không phải lỗi, và với năm mục thì hoàn toàn chịu được. Đáng theo dõi nếu corpus
lớn lên và danh sách thành năm mươi: lúc đó nên xếp theo thứ tự đáng ngờ, ví dụ đưa kiểu **chưa từng
được duyệt ở bất kỳ tài liệu nào** lên trước.

## F47 — vẫn mở, và họ nói rõ vì sao

> *"F47 chưa được giải quyết: cần hiệu chỉnh few-shot riêng cho giáo trình xác suất và báo cáo kỹ thuật,
> rồi chạy A/B recall/mật độ trên corpus. Không đổi prompt chung hoặc tuyên bố mật độ đã được sửa chỉ
> nhờ registry."*

Đúng. Sổ đăng ký `learnable` **không** chạm tới mật độ — nó chỉ đổi node nào được tính là học được, mà
mật độ đã tính trên node học được từ đầu. Việc không nhập nhằng hai thứ đó là chỗ dễ nhầm và họ không nhầm.

Đường gỡ vẫn như vòng 16: **bộ few-shot theo thể loại**, giờ F51 đã cho phép chọn lúc chạy.

### Trạng thái xử lý F54 (2026-09-08)

Đã thêm `a3-review-types --doc-id ...` (lặp cờ để chọn nhiều tài liệu). Lệnh chỉ đọc artifact
mới nhất và registry hiện tại, không gọi AI, không tự duyệt. Đã chạy thật trên bốn tài liệu:
đúng 5 kiểu architecture/component/metric/theorem/tool; hiển thị cả giá trị artifact và quyết định duyệt.
Lưu ý metric có 3 ứng viên ở các tài liệu nơi nó hiếm, nhưng 72 trong toàn corpus; bảng có cả hai cột.

**204 test pass**, gồm integration; test mới kiểm cả tính chỉ đọc, version mới nhất, ngưỡng hiếm,
media, doc-id trùng và phản ánh quyết định người vừa sửa. F47 vẫn mở.
[Lệnh sử dụng và kết quả thật](../report/xu-ly-feedback-f54.md).

---

# Vòng 18 — Rà lại toàn luồng A3 (2026-09-08)

Không kiểm một feedback cụ thể nào, mà đi hết đường: `_build_contexts` → `extract_section` → vòng
gleaning → validation → `build_media_candidates` → artifact → `index_document`. Bốn phát hiện mới, một
lỗi tái hiện được, và một chỗ **tôi đã kết luận sai rồi tự bác bỏ** — ghi lại cả chỗ đó vì nó đổi mức
độ nghiêm trọng rất nhiều.

## Những chỗ đúng, kiểm rồi mới nói

- **Vòng gleaning**: thoát đúng khi `added == 0`; chỉ đặt `glean_limit_reached` khi vòng cuối *vẫn còn*
  sinh — tức không báo động giả khi tài liệu vừa hết tự nhiên ở vòng thứ năm.
- **Thứ tự validation → media**: `build_media_candidates` chạy **sau** pass kiểm định, nên cạnh media
  chỉ trỏ vào thực thể sống sót. Nếu đảo lại sẽ có cạnh trỏ vào node vừa bị loại.
- **`_add_edge` sạch**: có `early return` khi `evidence is None`, nên lỗi ở mục F55 dưới đây **không**
  xảy ra được ở cạnh.
- **Cổng 40% mô tả media** lấy tổng làm mẫu số nên không thể nổ sớm.
- **Bộ chặn lệch `prompt_hash` của replay là có thật và được test đúng** (`test_a3_llm.py:237` truyền
  `"changed"` và mong nổ). Vấn đề ở F57 nằm chỗ khác, không phải cơ chế.

---

## F54 ✅ — kiểm chứng: lệnh có thật, chạy đúng, và giải luôn điểm tôi nêu ở vòng 17

```
$ a3-review-types --doc-id nhap-mon-ml --doc-id xstk-ch3-1 --doc-id baocao-canhan --doc-id naive-bayes
Artifact: nhap-mon-ml v7, xstk-ch3-1 v4, baocao-canhan v6, naive-bayes v5
node_type    | rare_doc | artifact_learnable | reviewed | corpus_candidates | examples
architecture |    1     |       true         |  false   |         1         | Mô hình Hub - Client
component    |    2     |       true         |  false   |         2         | ReadPump; WritePump
metric       |    3     |       true         |  false   |        72         | Test error; standard deviation
theorem      |    3     |       true         |  false   |         3         | Công thức Bayes; Định lý No Free Lunch
tool         |    1     |       true         |  false   |         1         | Makefile
5 kiểu hiếm; chỉ đọc, không thay quyết định hoặc artifact.
```

Đúng năm kiểu tôi đếm tay ở vòng 17, đúng ví dụ, chỉ đọc như đã đặt. **204 test pass, exit 0.**

Đáng nói là cột **`corpus_candidates`** — tôi không yêu cầu. Vòng 17 tôi nêu rằng cảnh báo có tỉ lệ tín
hiệu thấp: `metric`, `theorem`, `architecture` hiển nhiên học được, chúng chỉ *hiếm trong tài liệu này*.
Cột đó tách đúng hai thứ ấy: `metric` hiếm ở góc nhìn tài liệu (3) nhưng **72 ứng viên toàn corpus** ⇒
nhìn một cái là biết không cần bàn. Còn `tool` và `component` thì 1 và 2 ở cả hai cột — đúng hai ca thật
sự cần người quyết. Họ đọc ra vấn đề đằng sau lời góp ý chứ không chỉ làm theo chữ.

---

## F55 🔴 — `_add_entity` nhánh gộp ghi `None` vào `evidence`, tôi tái hiện được

Thực thể **chỉ nhìn thấy trong ảnh** có `evidence=""` + `media_evidence_id`, nên `evidence` sau khi
dựng là `None`. Nhánh tạo mới xử lý đúng. Nhánh **gộp** thì không:

```python
existing = next((item for item in entities if names & _entity_names(item)), None)
if existing is None:
    entities.append(candidate)
    return candidate, True
if evidence not in existing.evidence:
    existing.evidence.append(evidence)   # <-- evidence có thể là None
```

Tái hiện:

```
evidence sau khi gộp: [EvidenceSpan(chunk_id='c_1', …), None]
source_chunk_ids  -> AttributeError: 'NoneType' object has no attribute 'chunk_id'
```

Không phải cảnh báo, không phải dữ liệu bẩn — **vỡ ở `source_chunk_ids`**, mà thuộc tính đó là thứ A4
merge và bước M (ma trận node×chunk) đều đọc.

**Vì sao chưa ai gặp**: `media_grounded_entities = 0` trên **cả bốn tài liệu**. Lỗi đang ngủ, và nó ngủ
vì lý do đáng lo hơn chính nó — xem F59.

### Đọc kỹ nhánh gộp thì còn hai chuyện nữa, cùng gốc

**(a) Gộp làm mất liên kết ảnh.** Nhánh gộp chỉ chép `evidence`, `aliases`, `description`. Còn
`media_evidence_id` và `source_refs` của ứng viên bị **vứt luôn**. Nên một khái niệm mô hình nhìn thấy
trong ảnh, trùng tên với thực thể đã có từ văn bản, sẽ gộp vào mà **không để lại dấu vết nào là nó cũng
xuất hiện trong hình đó** — đúng thứ thông tin ticket 05 sinh ra để giữ.

**(b) `media_grounded_entities` đếm sai đơn vị.** Dòng

```python
stats["media_grounded_entities"] += evidence is None
```

nằm **trước** khi biết ứng viên sẽ được thêm hay bị gộp. Nên nó đếm *lượt đề xuất*, không phải *thực thể
trong artifact*. Hôm nay cả hai bằng 0 nên không lệch. Ngày đường này chạy thật thì chỉ số sẽ cao hơn số
node có thật, mà F59 lại đang đọc đúng chỉ số đó để kết luận "đường này chưa chạy".

Cả ba đều nằm trong một đoạn mười dòng: nhánh gộp được viết cho thực thể văn bản, rồi thực thể
media-grounded được thêm vào sau mà nhánh gộp không được xem lại.

**Test**: `test_a3_extract.py:882–910` phủ nhánh *tạo mới* (`assert … == 1`). Nhánh *gộp* không có test
nào. Sửa một dòng (`if evidence is not None and evidence not in existing.evidence`), nhưng phải kèm test
gộp, không thì lần sau vẫn thế.

---

## F56 🟢 — **RÚT LẠI.** Cạnh giàu kiểu là đúng thiết kế; số `requires` ở A3 không phải chỉ số cần giữ

Mục này ban đầu tôi viết ở mức 🟠 với tiêu đề *"`requires` rụng 32 → 12 → 1, không chỉ số nào nhúc
nhích"*. Chủ dự án phản biện, tôi kiểm lại, và **cả hai vế của tiêu đề đó đều sai**. Giữ nguyên phần đo
vì nó có ích làm mốc, nhưng kết luận thì đảo.

### Vế sai thứ nhất: A3 không có nghĩa vụ sinh `requires`

| | |
|---|---|
| §693 | 2b nhận **output cô đọng của tầng 1** + danh sách edge đã có liên quan tới node trong section |
| §694.2 | *"**Xác minh** các edge đề xuất từ tầng 1 **và suy luận edge mới** giữa các node canonical"* |
| §446 | A8a nhận **danh sách concept + description + `first_order_index` + evidence tiêu biểu**, xuất `A requires B` kèm confidence |
| §726 | Đề xuất tầng 1 *"phải được xác minh lại, **không copy nguyên**"* |

Tức là suy luận tiên quyết ở 2b có **nguồn sinh riêng** từ bảng node, có doc-order prior, có rubric
confidence 0.9/0.7/0.5. Nó không bị chặn trên bởi số `requires` mà A3 đề xuất. Bảy cặp biến mất ở v7 —
2b tự tìm lại được, vì nó nhìn bảng concept chứ không nhìn danh sách cạnh cũ.

### Vế sai thứ hai: và việc dán nhãn lại còn **có lợi** cho 2b

2b nhận *"danh sách edge đã có liên quan đến các node trong section"* làm ngữ cảnh. Đưa cho nó một đồ thị
mà **74% cạnh mang nhãn `requires`** — như v1, hồi chỉ có 2 loại cạnh nên `requires` là thùng chứa tất
cả — chính là mồi cho nó sinh thừa tiên quyết. Đưa đồ thị gắn nhãn đúng (`Bài toán phân cụm`
**`example_of`** `Học không giám sát`) thì tốt hơn hẳn. Đây đúng là thứ §80–84 đặt ra khi dẫn công trình
tám loại cạnh hơn SOTA 14–31%.

Nên cú rơi 32 → 1 **không phải hồi quy**. Nó là `requires` thôi làm thùng rác.

### Vế sai thứ ba: chỉ số có sẵn, và nó **đã** nhúc nhích

Tôi viết *"A3 không phát ra chỉ số nào về cạnh"*. Sai — `a3-compare` đã tính `edge_jaccard` từ trước
(`report_a3.py:135`). Chạy qua đúng ba ranh giới:

```
nhap-mon-ml   v4 → v5   node_jaccard 0.897   edge_jaccard 0.056    (đổi prompt: mở loại cạnh)
              v5 → v6   node_jaccard 1.000   edge_jaccard 0.321    (CÙNG prompt_hash)
              v6 → v7   node_jaccard 0.948   edge_jaccard 0.099    (đổi prompt: sang tiếng Anh)
```

Công cụ có, chỉ số động rất mạnh, không ai chạy nó qua ranh giới đổi prompt. Đó là thiếu sót **quy
trình**, không phải thiếu sót mã — và nhẹ hơn nhiều so với những gì tôi viết ban đầu.

### Thứ duy nhất thực sự mới, và nó không nằm ở chỗ tôi tưởng

Dòng giữa mới là dòng đáng đọc: **`v5 → v6` cùng `prompt_hash`, `node_jaccard = 1.000` tuyệt đối, nhưng
`edge_jaccard` chỉ `0.321`.**

Cùng prompt, cùng model, cùng nhiệt độ — node tái lập **hoàn hảo**, cạnh tái lập **một phần ba**. Cạnh
không ổn định gấp bội node, và điều đó chưa được ghi ở đâu trong dự án. Hệ quả thật:

- Hai con số 0.056 và 0.099 kia phải đọc trên **nền nhiễu 0.321**, không phải nền 1.0. Chênh lệch còn
  thật nhưng nhỏ hơn nhiều so với ấn tượng ban đầu.
- 2b nhận *"edge đã có liên quan"* làm ngữ cảnh, mà ngữ cảnh đó chỉ tái lập 32% giữa hai lần chạy giống
  hệt nhau. Đây là lý do §726 bắt **xác minh lại, không copy nguyên** — và đo được con số này là bằng
  chứng cho thấy quy định đó đúng, chứ không phải thận trọng thừa.

### Còn lại đúng hai việc, đều nhỏ

1. **`few-shot.txt` không có một ví dụ cạnh nào** (873 ký tự, toàn ví dụ ranh giới thực thể), trong khi
   `system.txt` nêu đích danh 5 loại cạnh. Cho xem thực đơn mà không cho xem mẫu. Với `edge_jaccard`
   cùng-prompt chỉ 0.32, thêm một ví dụ cạnh là phép thử rẻ xem độ ổn định có lên không.
2. **Bộ vàng hiện chỉ phủ thực thể** (`tests/fixtures/a3/gold-entities.json`, `entity_recall`). Bộ vàng
   cho cạnh là việc **của 2b**, không phải của A3 — ghi ra đây để lúc làm 2b khỏi quên.

Chạy `a3-compare` qua mỗi lần đổi prompt thì nên thành thói quen, nhưng đó là dòng trong checklist bàn
giao, không phải ticket.

---

## F57 🟠 — Fixture hội thoại tự đối chiếu với chính nó

`replay.py:164` chặn đúng:

```python
if fixture.get("prompt_hash") != prompt_hash:
    raise ValueError("fixture hội thoại không khớp prompt_hash")
```

Nhưng nơi dùng fixture thật, `test_a3_llm.py:247`:

```python
replay = ReplayEntityExtractor(path, prompt_hash=fixture["prompt_hash"])
```

Giá trị đem so **lấy ra từ chính fixture đó**. Điều kiện là hằng đúng, không bao giờ nổ.

Hệ quả đo được:

```
fixture LLM có thật             : đúng 1 tệp  (a3-section-with-image.json)
prompt_hash trong fixture      : 9cac43cf    (đời thứ 2 / 5)
prompt_hash của mã hiện tại    : 8e7c14c3
system_prompt trong fixture    : "Bạn trích tri thức được GIẢNG…"  ← tiếng Việt, F52 đã bỏ
test dùng fixture này để chạy use case : không có
```

`test_a3_extract.py` giả lập LLM bằng `_Extractor` / `_Session` viết tay (dòng 83, 113). Nghĩa là:
**chưa một test nào chạy prompt hiện hành đối chiếu phản hồi thật của mô hình.** Ba đời prompt đã đổi
hình dạng phân bố cạnh trong khi bộ test xanh suốt — và nó xanh *đúng*, vì không có test nào đứng ở vị
trí bắt được.

Ghép với F56 thì thành một mạch: seam ghi–phát lại là chỗ duy nhất có thể phát hiện prompt đổi làm đổi
đầu ra, và nó đang bị nối vào chính nó.

**Đề nghị**: ghi lại fixture ở prompt hiện tại (`scripts/record_a3_fixture.py` đã có sẵn), và ở
`test_a3_llm.py:247` truyền `prompt_hash` **tính từ mã sản phẩm**, không lấy từ fixture. Lúc đó lần đổi
prompt tiếp theo sẽ làm đỏ một test — đó chính là việc nó sinh ra để làm.

---

## F58 🟡 — Bất đối xứng ở đường retry của `_run_contexts`

Lượt đầu, section thiếu `missing_media_descriptions` bị **bỏ kết quả** rồi chạy lại. Lượt retry thì
*vừa nhận kết quả vừa gắn cờ*. Nên một section hỏng **hai lần** vẫn góp thực thể vào artifact, đồng
thời chặn freeze bằng cờ.

Không sai rành mạch — giữ lại còn hơn mất trắng một section — nhưng hai lượt đang theo hai luật khác
nhau mà không có ghi chú nào nói vì sao. Hoặc thống nhất, hoặc thêm một dòng bình luận nêu chủ ý.

---

## F59 🟡 — Đường "khái niệm chỉ có trong ảnh" chưa từng chạy trên dữ liệu thật

```
media_grounded_entities:  nhap-mon-ml 0 · xstk 0 · baocao 0 · naive-bayes 0
```

Đây đúng là lý do tồn tại của ticket 05 (`evidence=""` + `media_evidence_id`, gọi mô hình thị giác cho
ảnh không chú thích). Cơ chế có, test đơn vị có, dữ liệu thật **không có ca nào** — kể cả tài liệu DOCX
mà anh cố tình chèn ảnh vào ruột để thử.

Hai khả năng, phân biệt được bằng đo: (a) bốn tài liệu này thật sự không có khái niệm nào *chỉ* xuất
hiện trong ảnh — hoàn toàn hợp lý với sách giáo trình, vì hình luôn kèm chữ giảng quanh nó; (b) prompt
dựng rào quá cao nên mô hình không bao giờ chọn nhánh đó. Câu `system.txt` hiện tại là *"For a concept
visible only in an image…"* — chữ **only** rất chặt.

Chưa cần sửa. Cần **biết là mình chưa biết**: đừng tính đường này là đã hoạt động cho tới khi có một ca
thật. F55 nằm đúng trên đường này, nên nó sẽ nổ vào **đúng ngày** đường này bắt đầu chạy.

---

## F60 — Ghi nhận, không phải lỗi: I-G1 chưa có mã thi hành

Tôi grep không thấy chỗ nào chặn "`requires` chỉ nối hai node `learnable=true`". Nhưng spec §195 đặt
việc thi hành ở **executor `add_edge` của tầng 2b**, mà tầng đó chưa xây. Nên đây là **đúng spec**,
không phải thiếu sót — tôi ghi ra để lần sau khỏi ai giật mình như tôi.

Đo thực tế: 0 vi phạm trên cả bốn tài liệu (1 · 2 · 0 · 2 cạnh `requires`). Mẫu quá nhỏ để nói lên gì.

Một đề nghị nhỏ: A3 **đã ghi cạnh `requires` vào artifact** mà 2b sẽ đọc. Đặt luôn một guard rẻ ở
`_add_edge` của A3 thì đề xuất sai không bao giờ tới được 2b, và nó không xung đột gì với guard chính
sẽ dựng sau.

---

## Mạch chung của vòng này

Bốn phát hiện tưởng rời nhau nhưng cùng một họ với các vòng trước — **cơ chế có mặt, nhưng không ai đo
xem nó có làm đúng việc nó sinh ra để làm không**:

| | cơ chế | thứ không được đo |
|---|---|---|
| F55 | nhánh gộp thực thể | nhánh gộp media-grounded |
| F56 | loại cạnh mở | *(rút lại — cạnh giàu kiểu là đúng; cái chưa đo là `edge_jaccard` cùng-prompt = 0,32)* |
| F57 | chặn lệch prompt | prompt thật so với fixture thật |
| F59 | trích khái niệm từ ảnh | có ca nào thật không |

A3 có test cho từng cơ chế rất tốt — 204 xanh, và mấy vòng gần đây tôi kiểm không bắt được chỗ nào bản
tự báo nói quá. Thứ còn thiếu không phải test đơn vị, mà là **đo phân bố đầu ra**: hai chỉ số ở F56 và
một fixture nối đúng dây ở F57 là đủ để ba đời prompt tới không trôi âm thầm như ba đời vừa rồi.

### Trạng thái xử lý vòng 18 (2026-09-11)

- F55: đã sửa gộp evidence/source_refs/media_evidence_id và đếm node sống sót sau validation.
  Test gộp hai thứ tự đã thất bại trên code cũ, nay kiểm được artifact serialize và chỉ số đúng.
- F57: đã ghi fixture mới bằng Gemini thật, hash tính từ code; replay đi qua extract_section
  với context fixture độc lập. Fixture cũ đã làm test đỏ đúng lỗi prompt_hash trước khi thay.
- F58: thêm comment chủ ý giữ kết quả retry cuối để chẩn đoán; thiếu coverage vẫn không ghi artifact.
- F56 đã rút lại: không ép số requires. Checklist ghi đo edge Jaccard cùng prompt, gold cạnh thuộc 2b.
- F59 vẫn chưa có ca thật chứng minh image-only; F60 giữ phạm vi executor 2b theo spec.
- F47 đã chạy thử few-shot riêng: báo cáo 19,70→15,60/1000; XSTK 5,13→5,03, gold recall
  57,5→60%. Cả hai vẫn ngoài dải, **chưa đóng**, không thay prompt mặc định.

**208 test pass**, gồm integration. Hai artifact thử nghiệm mới là báo cáo v7 và XSTK v5;
không coi chúng là corpus cùng hash với hai tài liệu còn lại.
[Chi tiết, hash, số đo và các giới hạn](../report/xu-ly-feedback-f55-f60.md).
