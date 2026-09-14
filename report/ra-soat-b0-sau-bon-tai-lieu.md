# Rà soát pha B0 sau bốn tài liệu — hai tài liệu mới và toàn cảnh

Vòng 9 · 2026-08-29 · Hai tài liệu mới: `baocao-canhan` (DOCX, báo cáo cá nhân) và `naive-bayes`
(PDF, slide bài giảng 36 trang). Cả hai do tôi tự ingest và tự kiểm — không phải bàn giao của nhân viên,
nên vòng này không có mục "đối chiếu lời hứa", chỉ có số đo.

## 1. Kết luận nhanh

**Phần lõi giữ vững trên cả hai loại tài liệu chưa từng gặp: bất biến vị trí ký tự 0 vi phạm, định danh
0 trùng, trần token không thủng, manifest ghi đủ.** Nhưng hai tài liệu này mở hai đường code chưa từng
chạy thật — DOCX và slide — và mỗi đường lộ một lỗi nặng cộng một chùm lỗi vừa:

- **F35 🔴** — cây section DOCX gãy: **12/27 section lạc cha**, vì bộ dựng cây bỏ qua level thật mà
  Word đã khai, tự suy lại từ chữ bằng hai regex không biết `A.` (chấm) và `CHƯƠNG I` (số La Mã).
- **F36 🔴** — DOCX đứng ngoài toàn bộ đường ảnh, **im lặng**: dấu `[figure]` nằm trong chunk mà
  `image_refs` rỗng — dấu vết không có danh tính, phá đúng khế ước ADR 0002.
- Slide: luật tiêu-đề-lặp **hạ nhầm 8 tiêu đề slide thật** (F37), 13/40 chunk dưới 50 token,
  72 ký tự PUA của font template còn nguyên trong text (F40).
- **F34 tái hiện trên dữ liệu thật** đúng như dự đoán ở vòng 8: tám dòng cảnh báo giống hệt nhau
  không được gom.

Bốn tài liệu giờ phủ bốn thể loại: giáo trình PDF chữ, giáo trình PDF nhiều công thức, slide PDF,
báo cáo DOCX. Bài học lớn nhất của vòng: **mọi luật suy diễn của B0 được hiệu chỉnh trên một thể loại
duy nhất (giáo trình PDF), và mỗi thể loại mới làm lộ đúng những chỗ luật thay dữ liệu thật bằng
phỏng đoán.**

## 2. Số đo bốn tài liệu

| | nhap-mon-ml | xstk-ch3-1 | **baocao-canhan** | **naive-bayes** |
|---|---:|---:|---:|---:|
| Nguồn | PDF giáo trình | PDF giáo trình | **DOCX báo cáo** | **PDF slide** |
| Node giữ / tổng | 170 | ~1.100 | 267/396 | 224/224 |
| Section | 42* | 42 | 27 | 32 |
| Chunk | 41 | 126 | 30 | 40 |
| Token median / max | ~256 / <512 | ~— / <2048 | 155 / 268 | 106 / 513† |
| I9 vi phạm | 0 | 0 | **0** | **0** |
| Định danh trùng | 0 | 0 | **0** | **0** |
| refs ảnh / bảng / công thức | 9 / — / 1 | 5 / 51 / 263 | **0** / 0 / 0 | 2 / 13 / 32 |
| PUA còn sót trong chunk | 0 | 2 | 0 | **72** |
| Cảnh báo nổi bật | — | 29 dòng | `empty_node ×128` | `remaining_private_use: 149` |

\* số vòng 8. † 513 token là chunk bảng, dưới trần bảng 2048 — đúng thiết kế.

Điểm cộng xuyên suốt: đường PDF-sửa-chữa **tự tắt đúng** trên DOCX (`stitch=0, sắp lại trang=0`);
128 node bị bỏ của DOCX là đoạn trống Word dùng giãn dòng — luật "thử trường đã dọn rồi trường thô,
chỉ bỏ khi cả hai rỗng" (I23) hoạt động đúng; công thức trên slide đi đủ đường `.orig` → marker → ref.

---

## 3. F35 🔴 — Bộ dựng cây vứt level thật của Word, tự suy sai, 12/27 section lạc cha

### Hiện tượng

```
- CHƯƠNG I: CÔNG VIỆC ĐÃ ĐẢM NHẬN
    - A. Phần Lý Thuyết          ← đúng chỗ
- B. Phần Bài Tập                ← bật lên CẤP GỐC, ngang hàng CHƯƠNG
- C. Phần Đồ Án                  ← bật lên CẤP GỐC
```

Chỉ mục `A.` mỗi chương nằm đúng dưới chương; toàn bộ `B.` `C.` `D.` thành section cấp gốc.
**12/27 section sai `section_path`.**

### Trong khi dữ liệu vào hoàn toàn đúng

Cây parse đóng băng ghi level Docling lấy từ **style Word** — thứ tác giả tự khai:

```
level=1 tree_depth=2  'CHƯƠNG I: CÔNG VIỆC ĐÃ ĐẢM NHẬN'
level=2 tree_depth=3  'A. Phần Lý Thuyết'
level=2 tree_depth=3  'B. Phần Bài Tập'     ← level ĐÚNG, sẵn trong tree.json
level=2 tree_depth=3  'C. Phần Đồ Án'
```

### Cơ chế — hai regex hụt cộng dồn, và một guard chỉ cứu được đứa đầu

Bộ dựng cây **không đọc `node.level`**. Nó suy lại cấp từ văn bản tiêu đề:

1. `_LETTER_HEADING` chỉ khớp `A)` — ngoặc đơn. Tài liệu dùng `A.` — dấu chấm. Không khớp.
2. `_CHAPTER_HEADING` chỉ khớp `CHƯƠNG \d+` — chữ số Ả Rập. Tài liệu dùng số La Mã `CHƯƠNG I/II/III`.
   Không khớp. (Chương vẫn ra L1 nhờ nhánh mặc định "chưa thấy tiêu đề đánh số" — **may, không phải
   do thiết kế**.)

Không nhánh nào khớp ⇒ mọi tiêu đề chữ cái suy ra **level 1**. Guard theo `tree_depth` cứu được `A.`
(depth 3 > depth 2 của chương ⇒ kẹp về 2, phát `clamped_heading_level`) — nhưng khi `B.` đến, đỉnh stack
là `A.` cùng depth 3, điều kiện `3 > 3` sai ⇒ không kẹp ⇒ `B.` giữ level 1 ⇒ pop sạch stack, thành
section cấp gốc. Năm cảnh báo clamp toàn của `A.` chính là dấu vân tay của cơ chế này.

### Hệ quả xuôi dòng

`section_path` là **tiền tố ngữ cảnh khi embed**, là khoá gom **window của T1**, là `parent_section_id`
cho nhánh RAG. 44% section của tài liệu này mang đường dẫn cụt — mất tên chương phía trên.

### Hướng sửa — tin dữ liệu khai báo trước, suy diễn chỉ khi phải suy

Suy-level-từ-chữ sinh ra ở vòng 2 vì level Docling trên **PDF** là rác (27 heading đều L1). Nhưng trên
**DOCX**, level đến từ style tác giả khai — dữ liệu thật, không phải phỏng đoán của model layout.
Luật đúng phải là: **nguồn khai level tin cậy (DOCX style) ⇒ dùng level khai, suy diễn chỉ chạy khi cây
khai bị thoái hoá** (phẳng toàn L1 — đã có sẵn cảnh báo `flat_heading_tree` để nhận diện). Kèm theo,
dù đi nhánh nào: mở rộng `_LETTER_HEADING` nhận cả `A.`, `_CHAPTER_HEADING` nhận số La Mã.

---

## 4. F36 🔴 — DOCX đứng ngoài đường ảnh, và không gì báo

### Hiện tượng

Chunk đầu của `baocao-canhan`:

```
text       : 'UỶ BAN NHÂN DÂN\n…\n[figure]\nCÁC CÔNG NGHỆ…'
image_refs : []                     ← dấu vết KHÔNG có danh tính
```

Node figure trong cây: `image_id=None, page=None`. Manifest: `images_extracted: 0`. Cảnh báo
`missing_image`: **không phát**. Thứ duy nhất lên tiếng là Docling in ra stderr — *"Found DrawingML
elements… no DOCX to PDF converters"* — ngoài mọi kênh của hệ thống.

### Cơ chế — một cờ boolean làm hai việc không liên quan

```python
collapse_pdf_glyphs = Path(filename).suffix.lower() == ".pdf"
...
if collapse_pdf_glyphs:          # cờ tên là "sửa glyph PDF"
    image = self._image_bytes(item, document)   # ...nhưng gác luôn cổng trích ảnh
    ...
    else:
        warnings.append(f"missing_image: ...")  # cảnh báo cũng nằm trong cổng
```

Cờ sinh ra để bật bộ sửa glyph PDF, rồi được dùng luôn làm proxy "là PDF" cho việc trích ảnh.
Hệ quả: trên DOCX, cả trích ảnh **lẫn cảnh báo thiếu ảnh** đều không chạy. Ảnh raster nhúng trong một
DOCX khác sẽ mất **không dấu vết**; DrawingML (vẽ vector) cần LibreOffice mới xuất được — giới hạn đó
chấp nhận được, nhưng phải thành cảnh báo của mình, không phải một dòng stderr của thư viện.

### Đây là vi phạm khế ước ADR 0002

ADR chốt: nội-dung-không-phải-chữ để **dấu vết trong văn bản + danh tính trong danh sách tham chiếu**.
Chunk này có vế một, không có vế hai. Pha trích thực thể sau này gặp `[figure]` sẽ không có gì để trỏ về.

### Hướng sửa

Tách hai mối quan tâm: trích ảnh chạy cho **mọi** định dạng, `missing_image` phát khi có node hình mà
không lấy được byte (kèm lý do nếu biết — DrawingML cần LibreOffice). Ghi vào README yêu cầu LibreOffice
là phụ thuộc tuỳ chọn cho DOCX có hình vẽ.

---

## 5. F37 🟡 — Luật tiêu-đề-lặp hạ nhầm 8 tiêu đề slide thật

Slide lặp tiêu đề là **chuẩn thể loại** — deck này có «Naïve Bayes Classification» làm tiêu đề 7 slide,
và chuỗi đó cũng xuất hiện 4 lần trong khối thân (slide mục lục). Luật vòng 8 — *tiêu đề không đánh số
xuất hiện ≥2 lần trong thân ⇒ cụm nối, hạ xuống* — nổ đúng thiết kế, hạ **cả 7 tiêu đề thật** cộng
«Ví dụ». Nội dung các slide đó bị hút vào section đứng trước.

Ghi thẳng: đây không sửa được bằng chỉnh regex. Giữ cả 7 thì ra 7 section trùng tên — cũng không đúng.
**Slide là thể loại cần quyết định riêng** (mỗi slide một đơn vị? gom theo slide tiêu đề lớn?), xem mục 10.

Cũng trên deck này: «Trong đó:» — thứ đã bị hạ ở giáo trình hai vì lặp 10 lần — **sống lại thành section**
vì trong deck nó chỉ xuất hiện một lần. Luật tự hiệu chỉnh theo từng tài liệu nghĩa là mỗi tài liệu mới
tự đàm phán lại; đúng như thiết kế, nhưng đáng ghi để khỏi ngạc nhiên.

## 6. F38 🟡 — Run định dạng Word xé câu thành nhiều block

```
[text] '+ Triển khai dự án bằng'
[text] 'Docker Compose'            ← chữ đậm trong Word = block riêng
[text] ', thực hiện kiểm thử đầu cuối…'
```

**25/240 node text (10%)** của DOCX mở đầu như đứng giữa câu (`', thực hiện…'`, `'và giao thức'`,
`'sync.Mutex'`). Docling tách run định dạng (đậm, mã) thành item riêng; luật gộp nối bằng `\n` nên câu
trong chunk gãy dòng giữa chừng; bộ tách câu chạy theo block nên ranh câu sai; ranh chunk có thể rơi
giữa câu.

Đây là **bản DOCX của đúng bài toán nối-câu-qua-trang đã giải cho PDF** (`_stitch_pdf_page_breaks` —
chỉ chạy cho PDF). Luật nối tương tự — block trước không kết câu + block sau mở đầu bằng chữ thường
hoặc dấu câu ⇒ nối — dùng được gần nguyên, không cần khái niệm trang.

## 7. F39 🟡 — Đồ trang trí của tài liệu thành chunk rác

Hai chunk **99% là dấu chấm** (3.535 + 407 ký tự) — dòng kẻ chấm cho giảng viên viết tay trong trang
«NHẬN XÉT, ĐÁNH GIÁ CỦA GIẢNG VIÊN». Cộng hai chunk MỤC LỤC (~1.050 ký tự) lặp lại toàn bộ tiêu đề kèm
số trang. **4/30 chunk (13%) của tài liệu này là rác sẽ đi thẳng vào embedding.**

Chúng qua được mọi bộ lọc vì không rỗng, không phải header/footer lặp, không phải tiêu đề giả. Thiếu
một bộ lọc **nội-dung-không-ngôn-ngữ** (tỉ lệ chữ-cái quá thấp) và một quyết định cho section
mục-lục/biểu-mẫu. Nhẹ, nhưng nên làm trước B0.5 — rác này embed rồi thì trả giá ở truy hồi.

## 8. F40 🟡 — Bullet font template: một mã PUA, 72 lần, trong chunk

`remaining_private_use: 149` trên slide — **cảnh báo phát đúng**, cơ chế giám sát làm việc. Toàn bộ
72 ký tự lọt vào chunk là **một mã duy nhất `U+F097`** — dấu bullet của font template slide, ngoài bảng
Adobe Symbol. Nằm đầu các list_item, đi vào embedding như ký tự vô nghĩa.

Sửa rẻ: mã PUA mở đầu một list_item là dấu liệt kê ⇒ gỡ (mở rộng `_LEADING_BULLETS` sang dải PUA cho
block loại list), không cần đoán nghĩa từng font. Đằng nào nội dung bullet đã nằm trong cấu trúc
list_item rồi.

Cùng trên slide, ghi nhận **chất lượng OCR** (không phải lỗi code): 5 khối hỏng dấu tiếng Việt
(`'quyét dinh'`, `'Tong xac suat cua he bang 1:'`), một câu nhân đôi trong cùng block, tiêu đề
`'Cong thurc Bayes:'` hỏng dấu thành section. Slide dựng từ ảnh thì OCR là trần chất lượng — đáng ghi
vào manifest như một tín hiệu (`ocr_pages`?) để pha sau biết độ tin của文本, nhưng không sửa được ở B0.

## 9. F34 tái hiện y như dự đoán — và hai tồn đọng thành hiện hình

Vòng 8 dự đoán: *"một giáo trình có cùng một tiêu đề lặp ở nhiều chương sẽ làm ngập lại"*. Deck này
làm đúng thế, tám dòng giống hệt:

```
- rejected_heading_repeated: Naïve Bayes Classification   ×7 dòng nguyên văn
- rejected_heading_repeated: Ví dụ
```

Cảnh báo mang nguyên văn miễn trừ khỏi khử trùng lặp — khi nguyên văn trùng nhau thì tám dòng không mang
thêm thông tin nào. Sửa như đã chốt ở F34: **khử theo chuỗi đầy đủ, không theo loại.**

Tồn đọng cũ còn nguyên trạng: **F25** (chunk nhiều trang báo trang đầu — user hoãn), **F26** (dò cột
O(n²) có ghi chú ponytail — chấp nhận), **F29** (vượt `max_tokens` nhưng cắt câu thành công thì không
ghi `oversize_reason` — im lặng), **F33** (chèn space giữa từ khi sửa glyph).

## 10. Nhìn toàn pha — cái cần thêm, cái cần nâng

### Chẩn đoán chung của vòng này

Ba trong bốn phát hiện lớn (F35, F37, phần suy-level) chung một hình dạng: **luật suy diễn thay thế dữ
liệu khai báo, và luật được hiệu chỉnh trên một thể loại duy nhất.** Nguyên tắc cho pha tới: *mỗi luật
suy diễn phải khai rõ nó là dự phòng cho trường hợp thiếu dữ liệu thật, và phải nhường khi dữ liệu thật
có mặt.* Docling cho biết nguồn (DOCX/PDF), style Word cho level, `flat_heading_tree` đã nhận diện được
khi nào cây khai vô dụng — đủ nguyên liệu để phân nhánh đúng.

### Việc đề xuất, xếp theo ưu tiên

| # | Việc | Cỡ | Vì sao thứ tự này |
|---|---|---|---|
| 1 | **F35** — tin level khai báo của DOCX; mở rộng regex chữ cái (`A.`) và số La Mã | vừa | 🔴 sai `section_path` 44%, gãy window/T1/RAG |
| 2 | **F36** — gỡ trích ảnh khỏi cờ PDF; `missing_image` phát mọi định dạng | nhỏ | 🔴 mất dữ liệu im lặng, vi phạm ADR 0002 |
| 3 | **F38** — nối run định dạng DOCX (tái dùng luật stitch, bỏ điều kiện trang) | nhỏ | 10% block gãy câu, rẻ vì luật có sẵn |
| 4 | **F39** — lọc block phi ngôn ngữ + quyết định cho MỤC LỤC | nhỏ | chặn rác trước khi B0.5 embed |
| 5 | **F40** — gỡ bullet PUA đầu list_item | rất nhỏ | xoá 100% PUA còn sót của slide |
| 6 | **F34** — khử cảnh báo theo chuỗi đầy đủ | rất nhỏ | đã chốt cách sửa từ vòng 8 |
| 7 | **F29** — ghi `oversize_reason` cho mọi chunk vượt `max_tokens` | rất nhỏ | trả nợ im lặng |
| 8 | **Thể loại slide** — grill quyết định: mỗi slide một section? gom theo tiêu đề lặp? | cần bàn | F37 không sửa được bằng regex; cần quyết định sản phẩm |
| 9 | **Corpus hồi quy 4 tài liệu** — chốt số vàng mỗi tài liệu (section, chunk, refs, PUA, I9) thành test tự động | vừa | phương pháp so v1↔v2 đang làm tay mỗi vòng; 4 tài liệu là đủ giá trị để tự động |
| 10 | **B0.5** — embed (`gemini-embedding-2`) + vector store | pha mới | mở khoá sau khi 1–7 sạch |

Mục 8 đáng nhấn: bốn thể loại đã lộ diện và slide là thể loại **duy nhất** mà cấu trúc section hiện tại
không mô tả nổi. Trước khi viết spec sửa F37, nên chạy một phiên grill về câu hỏi "một slide deck muốn
thành roadmap thì đơn vị học là gì" — đó là câu hỏi sản phẩm, không phải câu hỏi regex.

### Cái không cần làm

- **Không** vá riêng «CHƯƠNG + số La Mã» như một danh sách cụm Việt — F35 sửa ở tầng "tin level khai
  báo" thì regex chương chỉ còn là dự phòng cho PDF.
- **Không** đụng F26 (ponytail đứng vững — trang dày nhất mới 11 node), **không** mở lại F25 (user hoãn).
- **Không** thêm OCR hậu xử lý sửa dấu tiếng Việt ở B0 — sai tầng; nếu cần thì là việc của pha
  làm giàu sau, khi đã có ngữ cảnh.

## 11. Ghi chú đo đạc của vòng này

Hai lần trong vòng này tôi đo ra "I9 vỡ 30/30, 40/40" — **cả hai đều là lỗi script của tôi**: đọc
`normalized_full_text` từ `tree.json` trong khi trường đó nằm ở `document.json` của artifact chunk.
Kiểm lại đúng file: **0 vi phạm cả bốn tài liệu.** Ghi lại vì đây là lần thứ ba trong dự án một phép đo
sai suýt thành kết luận — quy trình "nghi số lạ thì đo lại bằng đường khác" tiếp tục trả lương.
