# Spec vá — Quyết provenance sau mention map

**Ngày:** 2026-09-18 · **Chủ dự án chốt hướng:** tinh chỉnh sau mention map, không mở lại A3
**Nguồn chân lý liên quan:** [spec A6–A8](./A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md) D1, D4, D9, D13, D14 ·
[`CONTEXT.md`](../CONTEXT.md) mục *Provenance* · phát hiện gốc: [F105](../feedback/F19-a6-a10-cum-chu-de-va-tien-quyet.md)

Đây là **spec vá**: nó chỉ thêm một stage và sửa hai chỗ trong spec A6–A8. Mọi luật khác giữ nguyên.

## Vấn đề

`defining_chunk_ids` — provenance — được A5 chọn, nhưng code chặn nó phải nằm trong `source_chunk_ids`, tức những
chunk mà **A3 đã trích ứng viên ra**. A3 đọc theo cửa sổ chunk và không biết danh sách khái niệm cuối cùng, nên một
khái niệm thường chỉ được trích ở chunk **mở đề**, không phải chunk **định nghĩa** nó. A5 vì vậy không thể trỏ tới
chunk định nghĩa dù có muốn.

**Bằng chứng** (lượt gán thử của chủ dự án trên `xstk-ch3-1` §2, 2026-09-18 — bốn cờ "nơi dạy sai", cả bốn đúng):

| Khái niệm | A3 trích ở trang | Provenance | Định nghĩa thật ở trang | Mention map thấy chunk đó qua |
|---|---|---|---|---|
| Hàm ước lượng | 21 | 21 | 22 | exact |
| Khoảng tin cậy | 22 | 22 | 23 | exact |
| Độ tin cậy | 22, 31, 33, 34 | 22 | 23 | exact |
| Xác suất mắc sai lầm | 22 | 22 | 23 | chỉ dense (sách dùng cách diễn đạt khác) |

Chunk chứa định nghĩa **luôn nằm trong mention map**. Thông tin còn thiếu lúc A3 chạy — ma trận khái niệm × mọi
chunk — chính là thứ mention map có.

**Quy mô** (đếm trên artifact hiện có; "có dấu hiệu định nghĩa" là ước lượng trên, cần mô hình lọc lại):

| Tài liệu | Khái niệm | Có ≥1 chunk ngoài provenance mang dấu hiệu định nghĩa | Chunk ứng viên mỗi khái niệm (trung vị / lớn nhất) |
|---|---:|---:|---|
| `baocao-canhan` | 36 | 0 (0%) | 3 / 13 |
| `naive-bayes` | 34 | 10 (29%) | 3 / 11 |
| `nhap-mon-ml` | 75 | 49 (65%) | 3 / 21 |
| `xstk-ch3-1` | 98 | 56 (57%) | 4 / 87 |

Trên chương đã có nhãn người, tỉ lệ thật là **4/26 khái niệm đích (15%)**.

**Vì sao phải sửa trước khi gán vàng.** Provenance là đầu vào của: sáu loại vị trí của E1, viện dẫn (D4 định nghĩa
trên chunk provenance), bộ sinh `same_section`, mức `định nghĩa` của mention map, cột "Nơi dạy" trong file gán, và
`first_order_index`. Lệch sớm một chunk một cách hệ thống thì con số đầu đề của E1 lệch theo: loại "cùng chunk" bị
đếm thiếu, loại "bắc cầu" bị đếm thừa.

## Quyết định

### V1 — Một stage mới `provenance`, nằm giữa `mentions` và `edges`

- Tầng artifact vẫn là `graph`; `stage` nay có năm giá trị: `clusters` → `mentions` → **`provenance`** → `edges` →
  `stages`. `--stop-after` nhận thêm `provenance`.
- **`mentions` vẫn không gọi mô hình** (user story 30 giữ nguyên). Stage mới là chỗ duy nhất của vá này có gọi mô hình.
- **Không đụng vào artifact `canonical`.** Phase A4 vẫn đóng; provenance đã tinh chỉnh chỉ nằm trong tầng `graph`.
- Stage ghi lại: `defining_chunk_ids` sau tinh chỉnh, và `defining_chunk_ids_source` giữ nguyên bản của A3/A4, để
  luôn đối chiếu được và để báo cáo đo được mức chênh.

### V2 — Tập ứng viên lấy từ mention map, không từ cửa sổ A3

Với mỗi node `learnable`: ứng viên là mọi chunk mà mention map ghi có nhắc nó, **kênh exact hoặc dense**, trừ những
chunk đã nằm trong provenance. Ca `Xác suất mắc sai lầm` cho thấy không được bỏ kênh dense: sách diễn đạt khác tên
chuẩn nên chỉ dense bắt được.

Trần an toàn: xét tối đa **12 chunk ứng viên** mỗi khái niệm, ưu tiên theo thứ tự tài liệu rồi tới kênh cứng trước.
Trên corpus hiện có, trung vị chỉ 3–4 chunk nên trần này gần như không cắt gì; nó chỉ chặn ca `Độ tin cậy` kiểu 42
hay 87 chunk.

### V3 — Luật thuần chạy trước, mô hình chỉ phán khi luật thuần không kết luận được

1. **Luật thuần** đánh dấu ứng viên có **dấu hiệu định nghĩa** đứng gần tên khái niệm hoặc alias: `được gọi là`,
   `gọi là`, `ta gọi`, `được định nghĩa`, `định nghĩa là`, `ký hiệu là`, `được ký hiệu`, `gọi tắt là`, `is called`,
   `is defined as`, `we define`, `is denoted by`, `is known as`.
   Danh sách dấu hiệu là **tham số cấu hình**, ghi vào manifest, không rải rác trong code.
2. Khái niệm **không có ứng viên nào** mang dấu hiệu: giữ nguyên provenance, **không gọi mô hình**.
3. Khái niệm có ứng viên mang dấu hiệu: **một lời gọi mô hình duy nhất** cho cả khái niệm đó, đưa tên, alias, mô tả
   A5, và nguyên văn các chunk ứng viên. Hỏi: chunk nào **dạy hoặc định nghĩa** khái niệm này?
4. Mô hình phải trả **câu định nghĩa trích nguyên văn** từ chunk nó chọn. Code kiểm câu đó có thật trong chunk sau
   khi chuẩn hoá khoảng trắng; không khớp thì **bỏ đề xuất**, ghi log. Đây đúng chốt chống bịa của A3/A4.
5. Mô hình được phép trả "không chunk nào" — đó là kết quả hợp lệ, không phải lỗi.

### V4 — Chỉ thêm, không bao giờ thay

- Chunk được duyệt **thêm vào** `defining_chunk_ids`. Không xoá chunk cũ, kể cả khi mô hình nói chunk cũ chỉ là mở đề.
- Lý do: một lỗi của bước mới không được phép làm mất dữ liệu của bước cũ, và `first_order_index` (tính bằng `min`)
  nhờ đó không đổi khi chunk thêm vào nằm sau.
- Nếu chunk thêm vào nằm **trước** chunk cũ thì `first_order_index` đổi; stage phải ghi rõ số node bị đổi để đợt sau
  biết mà kiểm.

### V5 — Dựng lại những thứ phái sinh từ provenance

Trong cùng stage, sau khi provenance đổi, **tính lại bằng đúng các hàm domain đang có** (không chép luật sang chỗ mới):
mức `định nghĩa` của mention map, viện dẫn, cặp chạm, sổ cặp cụm, cặp nghi tiên quyết. Artifact `provenance` mang
bản đã dựng lại; stage `edges` chỉ đọc bản này.

### V6 — Nhật ký và chỉ số bắt buộc

Stage ghi vào payload và `stats`:

- `provenance_log`: mỗi mục gồm `node_id`, chunk được thêm, kênh bắt được ứng viên, dấu hiệu khớp, câu trích của mô
  hình, và kết quả kiểm trích.
- `stats`: số khái niệm được xét, số khái niệm phải hỏi mô hình, số chunk được thêm, số đề xuất bị loại vì trích sai,
  số node đổi `first_order_index`, số lời gọi và chi phí.

## Luật chấm, viết trước khi đo

- **Kiểm tay trên tài liệu phát triển, làm ngay khi có kết quả đầu tiên:** rút ngẫu nhiên **30 chunk được thêm** trên
  bốn tài liệu cũ; reviewer chấm từng chunk có thật là chỗ dạy hoặc định nghĩa hay không. **Nhận bước này làm mặc
  định khi precision ≥ 0,90.** Dưới mức đó thì siết luật thuần và đo lại, hoặc bỏ bước này và ghi thành giới hạn.
- **Đối chiếu với nhãn người, làm sau khi có vàng:** đếm cờ "nơi dạy sai" trên hai chương vàng. Con số này **chỉ để
  báo cáo**, không dùng để chỉnh lại luật — chỉnh sau khi thấy vàng thì phải ghi rõ là hậu kiểm và tách riêng (D14).
- **So E1 trước và sau vá** trên cùng bộ vàng: bảng sáu loại vị trí tính hai lần, một lần với `defining_chunk_ids`
  gốc, một lần với bản đã vá. Chênh lệch giữa hai bảng chính là cái giá của lỗi này, và phải nằm trong báo cáo.

## Chi phí và tái lập

- Nhiều nhất **một lời gọi cho mỗi khái niệm có ứng viên mang dấu hiệu**: 0 / 10 / 49 / 56 lời gọi cho bốn tài liệu
  hiện có. Ước tính một giáo trình cỡ `doc-2`: vài trăm lời gọi, khoảng **0,5–1 USD**.
- `gemini-3.1-flash-lite`, `temperature` 0, như mọi khâu khác.
- Khoá cấu hình gồm: phiên bản mention map, danh sách dấu hiệu, trần ứng viên, `prompt_hash`, `model_id`. Đổi bất kỳ
  thứ nào thì sinh phiên bản mới; không đổi gì thì `reused=true`, 0 lời gọi.

## Testing

- **Seam module luật thuần:** dấu hiệu định nghĩa phải đứng gần tên hoặc alias, không chỉ là có mặt trong chunk;
  ứng viên không có dấu hiệu thì không gọi mô hình; trần 12 ứng viên cắt đúng thứ tự ưu tiên.
- **Seam use case với mô hình giả:** câu trích không có trong chunk thì đề xuất bị loại và ghi log; mô hình trả
  "không chunk nào" thì provenance giữ nguyên; chunk thêm vào nằm trước chunk cũ thì `first_order_index` đổi và được
  đếm vào stats.
- **Bất biến:** provenance sau vá luôn **chứa** provenance gốc; `defining_chunk_ids_source` không đổi; số node không
  đổi; không node `learnable` nào mất hết provenance.
- **Phái sinh:** sau khi provenance đổi, mức `định nghĩa` của mention map và tập viện dẫn phải đổi theo, chứng minh
  bằng một fixture nhỏ.
- **Đột biến tối thiểu:** thay vì thêm thì ghi đè provenance; bỏ kiểm câu trích; bỏ kênh dense khỏi tập ứng viên; gọi
  mô hình cả khi luật thuần không thấy dấu hiệu; quên dựng lại viện dẫn.

## Ngoài phạm vi

- Không sửa A3, không sửa A5, không sinh phiên bản `canonical` mới.
- Không đổi cách A4 gộp node hay đặt tên.
- Không dùng bước này để **xoá** provenance sai; xoá là việc của A13 với người duyệt.
