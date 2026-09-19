# 16 — Vá provenance: quyết nơi dạy sau mention map

**What to build:** Một stage mới `provenance` giữa `mentions` và `edges`. Nó lấy tập chunk ứng viên từ mention map,
dùng luật thuần lọc dấu hiệu định nghĩa, hỏi mô hình đúng một lần cho mỗi khái niệm còn nghi, rồi **thêm** chunk định
nghĩa vào `defining_chunk_ids` và dựng lại mọi thứ phái sinh từ provenance.

Luật ở [spec vá](../../doc/va-provenance-sau-mention-map-spec.md). Gốc vấn đề ở
[F105](../../feedback/F19-a6-a10-cum-chu-de-va-tien-quyet.md).

**Blocked by:** đợt sửa F104/F98/F99 (vì stage mới phải nối đúng chuỗi artifact). **Phải xong trước vé 11**, vì ba
tài liệu mới cần được vá provenance ngay từ lượt chạy đầu, và trước khi ai gán vàng.

**Status:** blocked — code, test, chạy thật và cache đã đạt ngày 2026-09-19; còn thiếu file nhãn thử đã điền để tính E1

- [x] Stage `provenance` trong tầng `graph`; `--stop-after` nhận thêm giá trị này; `mentions` vẫn **0 lời gọi**.
- [x] Tập ứng viên từ mention map (exact ∪ dense), trừ chunk đã có trong provenance, trần 12 chunk theo thứ tự tài
      liệu rồi kênh cứng trước.
- [x] Luật thuần: dấu hiệu định nghĩa đứng **gần tên hoặc alias**; danh sách dấu hiệu nằm trong cấu hình và vào
      manifest. Không có dấu hiệu thì không gọi mô hình.
- [x] Một lời gọi cho mỗi khái niệm còn nghi; mô hình phải trích **nguyên văn** câu định nghĩa; code kiểm câu đó có
      thật trong chunk, không khớp thì loại đề xuất và ghi log.
- [x] **Chỉ thêm, không thay.** Giữ `defining_chunk_ids_source` là bản gốc của A3/A4; `canonical` không bị đụng.
- [x] Dựng lại bằng chính các hàm domain đang có: mức `định nghĩa` của mention map, viện dẫn, cặp chạm, sổ cặp cụm,
      cặp nghi tiên quyết. Không chép luật sang chỗ mới.
- [x] `provenance_log` và `stats` đủ các trường ở V6 của spec vá, gồm số node đổi `first_order_index`.
- [x] Chạy thật bốn tài liệu cũ: dán số khái niệm được xét, số lời gọi, số chunk được thêm, số đề xuất bị loại vì
      trích sai, và chi phí. Chạy lại khi chặn mạng phải `reused=true`, 0 lời gọi.
- [x] Dán **bảng E1 tính hai lần** cho `xstk-ch3-1` trên nhãn gán thử đang có: một lần với provenance gốc, một lần
      với provenance đã vá. Đây là số cho thấy cái giá của lỗi. → reviewer chạy, bảng ở dưới.
- [x] Test theo hai seam và các đột biến tối thiểu ghi ở spec vá.

## Kết quả chạy thật — 2026-09-19

| Tài liệu | Khái niệm xét | Khái niệm hỏi | Chunk thêm | Trích sai | Đổi `first_order_index` | Call | Input / output token | USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `baocao-canhan` | 36 | 0 | 0 | 0 | 0 | 0 | 0 / 0 | 0,000000 |
| `naive-bayes` | 34 | 2 | 0 | 0 | 0 | 2 | 4.999 / 82 | 0,001373 |
| `nhap-mon-ml` | 75 | 3 | 2 | 0 | 0 | 3 | 4.753 / 257 | 0,001574 |
| `xstk-ch3-1` | 98 | 13 | 7 | 0 | 1 | 13 | 34.912 / 1.152 | 0,010456 |
| **Tổng** | **243** | **18** | **9** | **0** | **1** | **18** | **44.664 / 1.491** | **0,013403** |

- Lượt phát triển chỉ sinh 9 chunk mới nên không thể rút 30 mẫu không lặp. Đã kiểm tay toàn bộ **9/9**: cả chín
  chunk đều thật sự dạy/định nghĩa đúng node, precision quan sát **1,00**, vượt ngưỡng 0,90. Đây là kiểm toàn bộ tổng
  thể hiện có, không ghi khống là mẫu 30.
- Bất biến trên artifact thật: 0 node mất provenance nguồn; 0 node `learnable` rỗng provenance; số node trước/sau
  không đổi; 0 chunk trạng thái `added` có quote kiểm thất bại.
- Bốn ca biết trước của `xstk-ch3-1`: `Hàm ước lượng` được thêm chunk trang 22 chứa câu định nghĩa; ba node
  `Khoảng tin cậy`, `Độ tin cậy`, `Xác suất mắc sai lầm` đã có chunk trang 22 chứa chính câu định nghĩa trong
  provenance nguồn của canonical v7 nên luật add-only giữ nguyên. Node riêng `Độ tin cậy của ước lượng` được thêm
  đúng chunk này.
- Replay cả bốn tài liệu với `HTTP_PROXY` và `HTTPS_PROXY` trỏ `127.0.0.1:9`: cùng version cuối
  `89 / 19 / 19 / 19`, cả bốn `reused=true`; không có lời gọi mạng.
- Toàn bộ suite **383/383** xanh; seam riêng vé 16 có 23 test. Năm đột biến tối thiểu đều có test độc lập: ghi đè provenance,
  bỏ kiểm quote, bỏ dense, gọi mô hình khi không có dấu hiệu, và quên dựng lại citation.

## Cổng E1 — reviewer chạy xong, 2026-09-19

File nhãn đã điền **không nằm trong scratchpad** mà ở `artifacts/a8-gold/xstk-ch3-1-chuong-10-13-A1-output.xlsx`,
và bản JSON đã qua `a8-gold-check` là `artifacts/a8-gold/A1.json` (52 quan hệ, 27 cờ, 0 lỗi). Bộ chấm vé 05 nay có
cờ `--provenance patched|source` để chấm cùng một artifact theo provenance đã vá hoặc bản gốc của A3/A4.

Chạy `a8-score --doc-id xstk-ch3-1 --graph artifacts/graph/xstk-ch3-1/v15/graph.json --gold artifacts/a8-gold/A1.json`
hai lần, trên 52 cạnh vàng của 26 khái niệm đích:

| Loại vị trí | Provenance gốc | Sau khi vá | Chênh |
|---|---:|---:|---:|
| cùng chunk | 8 | **10** | **+2** |
| cùng mục | 2 | 1 | −1 |
| cùng chương | 2 | 2 | |
| cùng cụm chủ đề | 5 | 4 | −1 |
| bắc cầu (kênh cứng) | 31 | 31 | |
| bắc cầu (chỉ dense) | 1 | 1 | |
| ngầm | 3 | 3 | |
| **NMI cụm vs chương** | 0,698 | 0,698 | |

Vá làm 2 trong 52 cạnh (3,8%) đổi loại vị trí, đều đi từ loại rộng về **cùng chunk** — đúng chiều dự đoán ở F105.
Trên một chương và một người gán thì mức chênh này nhỏ; nó chỉ cho thấy phép đo E1 **có** nhạy với provenance, nên
việc vá trước khi gán vàng là đúng chỗ. Số thật của hai chương vàng sẽ đo lại ở vé 12.

Cổng nhận của spec vá đã đạt: kiểm tay 9/9 chunk được thêm (precision quan sát 1,00 ≥ 0,90), và bảng trước/sau đã có.

## Ghi chú cũ về cổng E1 (đã giải quyết)

Đã tìm và chạy `a8-gold-check` trên file
`xstk-ch3-1-chuong-10-13-A1.xlsx` trong scratchpad vé 04. Đây là **template trống**, không phải lượt gán thử được
nhắc ở F105: checker trả `edges=0`, `flags=0`, hai thời gian đều rỗng và cảnh báo `chưa có quan hệ nào được ghi`.
Nhánh `ve-05-bo-cham` cũng ghi rõ số thật còn chờ bộ vàng; trong workspace và hai worktree không có file A1 khác.
Vì không có 52 cạnh ở dạng máy đọc được nên chưa thể lập bảng E1 trước/sau mà không bịa dữ liệu. Vé 11 tiếp tục bị
chặn cho tới khi file đã điền (hoặc JSON từ `a8-gold-check`) được đặt vào workspace.

## Ghi chú cho người làm

- Đừng đụng vào A3, A5 hay artifact `canonical`. Vé này cố ý **không** mở lại phase đã đóng.
- Bốn ca đã biết, dùng làm ca kiểm tay đầu tiên trên `xstk-ch3-1`: `Hàm ước lượng` (định nghĩa ở trang 22),
  `Khoảng tin cậy`, `Độ tin cậy`, `Xác suất mắc sai lầm` (ba cái sau ở trang 23). Ca cuối chỉ bắt được qua kênh
  **dense**, nên nếu bỏ dense khỏi tập ứng viên thì sẽ trượt ca này.
- Số ứng viên thực tế rất nhỏ: trung vị 3–4 chunk mỗi khái niệm trên cả bốn tài liệu.
- Reviewer sẽ chấm tay 30 chunk được thêm; bước này chỉ thành mặc định khi precision ≥ 0,90 (luật viết trước ở spec vá).
