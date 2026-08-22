# Ghi chú bổ sung — sửa câu bị đứt tại ranh giới trang

**Status:** completed — 2026-08-16  
**Phạm vi:** Docling adapter cho PDF; adapter hiện ở version 4, không đổi schema và không đổi thuật toán chunk `section-id-v3`.

## 1. Hiện tượng

Ở artifact `nhap-mon-ml/v1`, một số chunk kết thúc hoặc bắt đầu bằng nửa câu:

```text
... Máy sẽ cần tìm ra hàm y* từ một tập dữ liệu D ... đã thu
thập trong quá khứ. Tập D thường được gọi là tập huấn luyện ...
```

Trường hợp trên nằm ở cuối trang 7 và đầu trang 8 của PDF
`nhap_mon_hoc_may_va_khai_pha_du_lieu_5944.pdf`.

Nguyên nhân có hai lớp:

1. Docling tạo hai `DocItem` cho hai phần của cùng một đoạn văn khi đoạn đi qua ranh giới trang.
2. Các hình nổi làm thứ tự `iterate_items()` trên trang 7 bị đảo. Thứ tự adapter v2 nhận được là:

```text
figure
trong đó:
hai list item
... đã thu
figure
heading 1.1.2
hai đoạn mở đầu section
figure
thập trong quá khứ ...
```

Vì vậy, chỉ bỏ qua `figure`/`footnote` khi gộp là chưa đủ: các text item vẫn sai thứ tự và có thể bị gán nhầm section.
Chunker cũ còn đóng nhóm đang chờ khi gặp một block khác loại, nên nửa câu bị giữ thành hai chunk khác nhau.

## 2. Quyết định sửa

Bản sửa nằm trong Docling adapter, trước bước dựng section, `normalized_full_text` và áp ngân sách token.
Đây là lỗi của output parse/layout; sửa ở chunker sẽ che cây parse sai và có thể tạo một chunk với `char_span` không liên tục.

### 2.1 Sửa reading order cho trang PDF một cột

Adapter gom các node theo trang và chỉ sắp lại một trang khi:

- mọi node của trang có `bbox`; và
- không có hai block nội dung nằm ngang tách rời nhau — dấu hiệu đơn giản rằng trang không phải bố cục đa cột.

Trang đủ điều kiện được gom thành hàng theo độ chồng dọc của `bbox`, sắp các hàng từ trên xuống dưới, rồi sắp block
trong cùng hàng từ trái sang phải. Hai block được xem là cùng hàng khi phần chồng dọc lớn hơn một nửa chiều cao block
ngắn hơn. `figure` và `footnote` không tham gia phép nhận diện số cột nhưng vẫn được giữ và sắp vào vị trí hình học.

Nếu trang có dấu hiệu đa cột, adapter giữ nguyên reading order của Docling. Fixture `two-column.pdf` bảo vệ output
end-to-end; unit test dựng node trực tiếp bảo vệ riêng nhánh guard đa cột `False`. Không thêm dependency hoặc bộ phân tích
layout thứ hai.

### 2.2 Stitch hai mảnh qua ranh giới trang

Sau khi reading order đúng, adapter xem `figure` và `footnote` là block tách khỏi dòng văn bản khi tìm mảnh tiếp nối.
Hai node chỉ được stitch khi đồng thời thỏa các điều kiện:

- cả hai thuộc nhóm `text`, `paragraph` hoặc `list_item`;
- node sau nằm đúng trang kế tiếp;
- giữa chúng chỉ có `figure`/`footnote`, không có heading, bảng hoặc block nội dung khác;
- node trước không kết thúc bằng `.`, `!`, `?`, `:`; luật cũng nhận dấu đóng ngoặc/nháy và số cước chú sau dấu câu;
- ký tự đầu tiên của node sau là chữ thường.

Text được nối bằng đúng một dấu cách. Node sau bị loại khỏi cây vì nội dung của nó đã nằm trong node trước.
Figure/footnote không bị xóa và tiếp tục sinh chunk độc lập. Header, footer, số trang và caption vẫn đi qua bộ lọc
page-furniture đã có từ trước.

Không dùng newline đơn thuần làm tín hiệu kết thúc câu vì xuống dòng trong PDF extraction không ổn định.

### 2.3 Token budget và vị trí ký tự

Stitch chạy trước `chunk_document()`. Vì vậy:

1. câu gốc được phục hồi trước;
2. chunker mới gộp các leaf block quanh `target_tokens=256`;
3. block dài vẫn được cắt theo câu dưới `max_tokens=512` như cũ;
4. `normalized_full_text` và `char_span` được tính trên text đã stitch nên bất biến I9 vẫn giữ.

Node đã stitch giữ `page` và `bbox` của mảnh đầu. Đây là quy ước hiện có của chunk gộp: trường `page` là trang bắt đầu,
không phải danh sách toàn bộ trang mà nội dung đi qua.

## 3. Các vị trí được sửa trên tài liệu thật

| Ranh giới | Cuối trang trước | Đầu trang sau | Kết quả |
|---|---|---|---|
| 7 → 8 | `... đã thu` | `thập trong quá khứ ...` | `... đã thu thập trong quá khứ ...` |
| 9 → 10 | `... giá trị trong Y )` | `thì chúng ta ...` | một câu liên tục |
| 11 → 12 | `... giải quyết nhu cầu` | `thực tế kia ...` | một list item liên tục |
| 12 → 13 | `... tham số đã` | `tốt chưa ...` | một list item liên tục |
| 19 → 20 | `... Chúng` | `ta cần xác định ...` | `... Chúng ta cần xác định ...` |

Trang 7 là trang duy nhất cần sửa reading order hình học. Sau khi sửa, thứ tự liên quan là:

```text
ba figure của Hình 2
heading 1.1.2
hai đoạn mở đầu
trong đó:
hai list item
đoạn "Trong thực tế ... đã thu thập trong quá khứ ..."
```

## 4. Thay đổi code và cache

| File | Thay đổi |
|---|---|
| `src/doc2roadmap/infrastructure/parsing/docling_parser.py` | repair reading order theo hàng, stitch page break, sửa glyph Unicode, thống kê repair, tăng adapter version |
| `src/doc2roadmap/presentation/cli/main.py` | hiển thị số trang được sắp lại và số page break đã stitch |
| `tests/unit/infrastructure/test_docling_adapter.py` | regression test trên fixture Docling thật, guard đa cột trực tiếp, sort cùng hàng và xác nhận DOCX không bị tác động |

`ADAPTER_VERSION` tăng từ `2` lên `3` ở bản sửa reading order, rồi từ `3` lên `4` khi xử lý review F10. Parse config hash
vì vậy thay đổi và cache parse cũ tự hết hiệu lực.
`CHUNK_ALGORITHM_ID` vẫn là `section-id-v3` vì chunker không đổi; chunk artifact mới được sinh từ parse config có adapter version 4.

## 5. Kết quả kiểm chứng

### Test

```text
44 passed, 8 warnings in 23.40s
```

Các warning đều là deprecation warning từ Docling/RapidOCR đã tồn tại, không phải lỗi test.

### Re-ingest PDF thật

```text
thời gian tạo artifact v3: 160.8 giây
tái ingest từ cache v3   : 0.716 giây
Docling items            : 170
node output              : 153
node bị lọc              : 12
page-break node đã stitch: 5
trang được sắp lại       : 1
section                  : 27
chunk                    : 49
window                   : 22
```

Phép đối chiếu số node: `153 output + 12 bị lọc + 5 được hấp thụ khi stitch = 170 Docling items`.

| Chỉ số | v1 trước sửa | v2 reading order | v3 sau review F10 |
|---|---:|---:|---:|
| Parse node | 158 | 153 | 153 |
| Chunk | 50 | 49 | 49 |
| Text chunk | 39 | 38 | 38 |
| Trung vị token, mọi chunk | 202 | 233 | 233 |
| Trung vị token, text chunk | 248 | 258 | 258 |
| Token lớn nhất | 400 | 400 | 400 |
| Chunk oversize | 0 | 0 | 0 |

Kiểm tra artifact `v3`:

- `adapter_version = 4`;
- đủ 5 cụm từ sau stitch;
- không còn node bắt đầu bằng `thập trong quá khứ`;
- `order_index` tăng đơn điệu;
- I9: `normalized_full_text[char_start:char_end] == chunk.text` với **0/49 vi phạm**;
- 8 figure và 3 footnote vẫn còn trong parse tree;
- `chunks.json` của v3 giống hệt v2;
- artifact mới ở `artifacts/parse_tree/nhap-mon-ml/v3` và `artifacts/chunks/nhap-mon-ml/v3`.

## 6. Giới hạn có chủ đích

- Repair chỉ chạy với PDF; DOCX giữ nguyên output Docling.
- Heuristic chỉ tự sắp trang một cột được nhận diện chắc chắn. Trang đa cột tiếp tục tin reading order của Docling để tránh
  một phép sort theo trục dọc làm xen kẽ hai cột.
- Stitch ưu tiên độ chính xác: câu tiếp nối bắt đầu bằng chữ hoa sẽ không tự nối. Nếu corpus thật cho thấy nhiều false negative
  thuộc nhóm này thì mới mở rộng tín hiệu; không thêm từ điển hoặc mô hình ngôn ngữ ở pha B0.
- Figure/footnote được bảo toàn dưới dạng block độc lập; bản sửa không cố suy luận figure anchor hay quan hệ tham chiếu mới.

## 7. Xử lý feedback F10 (F22–F26)

| Feedback | Trạng thái | Xử lý |
|---|---|---|
| F22 — regex glyph xóa ký hiệu sau từ tiếng Việt | **Đã sửa** | Lookbehind đổi từ ASCII-only sang Unicode letter guard; thêm ca `các c c c`, `học c c c`, `lần n n n`. |
| F23 — guard đa cột chưa được test | **Đã sửa** | Unit test trực tiếp: hai text block ngang tách rời trả `False` và giữ nguyên order; figure bên cạnh không tạo cột; thiếu bbox trả `False`. |
| F24 — sort cùng hàng không có dung sai dọc | **Đã sửa** | Gom hàng theo vertical overlap > 1/2 chiều cao block ngắn hơn, sau đó sort theo `left`; có regression test top lệch ngược left. |
| F25 — chunk stitch chỉ ghi trang đầu | **Ghi nhận, hoãn** | Không chặn B0. Thêm `page_end` sẽ đổi model/schema/artifact và cần provenance theo span; chỉ triển khai khi consumer citation theo trang được làm. |
| F26 — `_is_single_column` O(n²) | **Ghi nhận, giữ nguyên** | Trang thật hiện tối đa 12 node; reviewer xác nhận chưa cần tối ưu. Code có `ponytail` comment chỉ rõ khi nào đổi sang sweep. |

F22–F24 làm adapter tăng version `3 → 4`. Không bump `CHUNK_ALGORITHM_ID` vì chunker và schema không đổi. Artifact PDF
thật v3 xác nhận output chunk giống hệt v2, nên bản sửa chỉ đóng lỗ mất dữ liệu/test/layout mà không làm đổi nội dung hiện có.
