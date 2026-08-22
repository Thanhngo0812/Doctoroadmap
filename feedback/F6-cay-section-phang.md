# F11–F12 🔴 — Cây section phẳng hoàn toàn, và cờ cảnh báo mù đúng ca này

Vòng review 2 · 2026-08-15 · Dữ liệu: `artifacts/*/nhap-mon-ml/v1` (20 trang, 159 node, 132 chunk)

Đây là **lỗi nặng nhất từ đầu dự án**. Không phải lỗi code — code chạy đúng như đặc tả. Là **đặc tả đứng trên
một giả định mà PDF thật không thoả**.

---

## F11 🔴 — 27 heading, tất cả đều level 1

### Bằng chứng

Chạy Docling trực tiếp trên `nhap_mon_hoc_may_va_khai_pha_du_lieu_5944.pdf`, đọc thẳng thuộc tính của item:

```
(label, item.level, tree_level) -> Counter({('section_header', 1, 1): 27})
```

**Cả 27 heading đều `level=1` và `tree_level=1`.** Không phải adapter đọc sai — Docling **không hề suy ra
độ sâu heading** cho PDF. Nó chỉ trả lời "khối này là tiêu đề", không trả lời "tiêu đề cấp mấy".

### Hậu quả: cây section là một danh sách phẳng

```
<document>
├── NHẬP MÔN HỌC MÁY VÀ KHAI PHÁ DỮ LIỆU        [ 0 chunk]
├── TÀI LIỆU ĐỌC                                 [ 0 chunk]
├── TẬP THỂ TÁC GIẢ:                             [ 2 chunk]
├── MỤCLỤC                                       [ 0 chunk]
├── MỞĐẦU                                        [11 chunk]
├── CHƯƠNG 1. GIỚI THIỆU CHUNG VỀ HỌC MÁY...     [ 0 chunk]   ← chương, rỗng
├── 1.1 Các khái niệm và bài toán học cơ bản     [ 1 chunk]   ← anh em với CHƯƠNG 1
├── 1.1.1 Vài quan điểm về ML                    [21 chunk]   ← anh em với 1.1
├── trong đó:                                    [ 4 chunk]   ← heading giả, xem F14
├── 1.1.2 Bản chất của việc học, suy diễn...     [16 chunk]
...
```

`1.1.1` **là anh em** của `CHƯƠNG 1`, không phải cháu. Kiểm bằng độ sâu `section_path` của mọi chunk:

```
Counter({1: 132})     ← 132/132 chunk có section_path đúng 1 phần tử
```

Mọi chunk chỉ biết **một** tổ tiên trực tiếp. Không chunk nào biết mình thuộc chương nào.

### Bốn thứ phía sau gãy theo

| Ai | Cần gì | Hiện có gì |
|---|---|---|
| **T1** gom window theo `parent_section_id` | Window cấp mục *và* cấp chương | 23 window rời rạc, không có cấp chương |
| **DAG tiên quyết** | Thứ tự mục lồng nhau làm prior: 1.1 trước 1.2, 1.1.1 nằm trong 1.1 | Chỉ còn thứ tự tuyến tính, mất quan hệ bao hàm |
| **`section_path` khi embed** (§13.3) | `"CHƯƠNG 1 > 1.1 > 1.1.1"` làm tiền tố ngữ cảnh | `"1.1.1 Vài quan điểm về ML"` — không có chương |
| **T4 xếp stage** | "học hết chương 1 rồi sang chương 2" | Không truy được chunk nào thuộc chương 1 |

5 section **không sinh window nào** vì không có chunk trực tiếp:

```
'<document>'
'NHẬP MÔN HỌC MÁY VÀ KHAI PHÁ DỮ LIỆU'
'TÀI LIỆU ĐỌC'
'MỤCLỤC'
'CHƯƠNG 1. GIỚI THIỆU CHUNG VỀ HỌC MÁY VÀ KHAI PHÁ DỮ LIỆU'   ← cái này mới đau
```

Chương 1 **không sở hữu một chunk nào**, và vì cây phẳng nên nó cũng không có section con để mượn. Toàn bộ
nội dung của nó nằm ở 20 section khác **cùng cấp** với nó.

(Bất biến I4 — *"không có window rỗng"* — vẫn đúng: `assemble_windows` chỉ tạo entry cho section có chunk, nên
có đúng 23 window và không cái nào rỗng. I4 kiểm dict window, không kiểm việc một chương biến mất khỏi dict.)

### Vì sao bộ test không bắt được

Fixture ở seam thuần **dựng `DocumentTree` bằng tay**, và khi dựng tay thì ta tự gán `level=1,2,3` cho đúng ý.
Bất biến I2 (`parent_section_id` trỏ đúng tổ tiên gần nhất) **đúng tuyệt đối** — với đầu vào có level phân
tầng. Nó không bao giờ được hỏi câu "nếu mọi level đều bằng 1 thì sao".

Đây chính là cái giá của việc tách hai seam: seam thuần kiểm **thuật toán**, và thuật toán đúng. Không seam
nào kiểm **giả định về đầu vào**.

### Sửa: suy level từ chính tiêu đề

Docling sẽ **không bao giờ** cho độ sâu heading của PDF. Đừng chờ. Nguồn tín hiệu duy nhất còn lại là **đánh
số trong text**, và với giáo trình tiếng Việt nó rất đều:

| Mẫu tiêu đề | Level | Ví dụ trong tài liệu này |
|---|---|---|
| `CHƯƠNG <n>` / `PHẦN <n>` / `Chapter <n>` | 1 | `CHƯƠNG 1. GIỚI THIỆU CHUNG…` |
| `<n>.<n>` | 2 | `1.1 Các khái niệm và bài toán học cơ bản` |
| `<n>.<n>.<n>` | 3 | `1.1.1 Vài quan điểm về ML` |
| `<chữ cái>)` | 4 | `a) Chọn kiểu mô hình:` |
| Không số, đứng trước heading đánh số đầu tiên | 1 | `MỞĐẦU`, `TÀI LIỆU ĐỌC` (front matter) |
| Không số, đứng sau | *ứng viên đáng ngờ* → xem F14 | `trong đó:` |

Số chấm = độ sâu. `1.1.1` → 3. Đây không phải heuristic mong manh, nó là **quy ước đánh số** mà chính tài
liệu tuân theo — và nếu tài liệu không tuân theo thì ta phát hiện được (F12).

**Đặt ở đâu:** đây là *suy luận cấu trúc từ text*, thuần, không I/O ⇒ thuộc **domain**, không thuộc adapter.
Adapter chỉ báo trung thực điều Docling nói (`heading_level_raw = 1`); domain quyết định level thật. Trường
`heading_level_raw` đã có sẵn trong `Section` đúng để phục vụ việc này — giữ nguyên, ghi thêm `level` suy ra.

**Cảnh báo về định danh:** đổi cách gán level sẽ đổi `section_path` của gần như mọi section ⇒ **đổi toàn bộ
`section_id` và `chunk_id`**. Phải làm **trước khi** embed thật. Hiện tại chỉ có 1 tài liệu thử nghiệm nên chi
phí bằng 0; sau khi có vector store thì đây là một lần re-index toàn bộ. `algorithm_id` trong manifest phải
bump `section-id-v2` → `v3`.

---

## F12 🔴 — `structure_warning` không bật, dù cây phẳng 100%

### Lỗi

```python
# domain/chunking.py:113-126
raw_level = node.level
if raw_level is None or raw_level < 1:      # ← Docling trả 1, không vào nhánh này
    raw_level = stack[-1].level + 1
    structure_warning = True
...
if (node.tree_depth is not None and parent_depth is not None
        and node.tree_depth > parent_depth   # ← tree_depth == parent_depth == 1, sai
        and level <= stack[-1].level):
    level = stack[-1].level + 1
    structure_warning = True
```

Cả hai nhánh bật cờ đều đòi **level bất thường**. Nhưng ca hỏng ở đây là level **hoàn toàn bình thường** —
đều bằng 1, hợp lệ, nhất quán. Không nhánh nào chạm tới.

Kết quả trong artifact:

```json
"structure_warning": false
```

CLI in ra `Cảnh báo cấu trúc: không`. Người dùng đọc dòng đó và tin rằng cấu trúc ổn.

### Vì sao đây là lỗi riêng, không phải hệ quả của F11

Sửa F11 xong thì cây hết phẳng **với tài liệu này**. Nhưng cờ vẫn mù: tài liệu tiếp theo có thể dùng kiểu đánh
số ta chưa biết, và ta lại nhận một cây phẳng **im lặng**. Cờ tồn tại đúng để nói "tôi không chắc" — mà nó
không biết cách không chắc.

Một cảnh báo im lặng đúng lúc cần kêu **tệ hơn không có cảnh báo**, vì nó tạo niềm tin sai. Cùng loại lỗi với
F4 vòng trước (tên test hứa nhiều hơn thân test làm).

### Sửa: thêm kiểm tra ở mức tổng thể, sau khi duyệt xong

Cờ hiện tại chỉ nhìn **từng heading một**. Cần thêm một lượt nhìn **toàn cây**:

```python
headings = [s for s in sections if s.level > 0]
if len(headings) >= 4 and len({s.level for s in headings}) == 1:
    structure_warning = True      # mọi heading cùng một cấp — gần như chắc chắn parse hỏng
```

Và nên nâng cấp `structure_warning: bool` thành **danh sách lý do**, ghi vào manifest:

```json
"structure_warnings": ["flat_heading_tree: 27 heading cùng level 1"]
```

`bool` chỉ nói *có chuyện*, không nói *chuyện gì* — mà lúc soi 132 chunk thì "chuyện gì" mới là thứ cần.

### Test cần thêm

| Test | Nội dung |
|---|---|
| **I13** | `DocumentTree` với 5 heading **cùng `level=1`** và text đánh số `1`, `1.1`, `1.1.1`, `1.2`, `2` → cây phải có 3 cấp |
| **I14** | Cùng đầu vào nhưng text **không đánh số** → `structure_warning` phải **bật** |

I13 là bài mà bản hiện tại **trượt**. Đó là dấu hiệu nó đáng viết.
