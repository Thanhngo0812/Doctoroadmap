# 04 — Ứng viên media lấy thẳng từ tham chiếu B0

**What to build:** Hình và bảng thành thực thể **mà không cần mô hình nhận ra chúng**. Code đọc
`image_refs` / `table_refs` của chunk và tạo ứng viên `figure` / `table` — đường tất định, không tốn
lời gọi nào.

## Món quà B0 để lại mà chưa ai dùng

Hai hình giống hệt nhau **đã có cùng `media_id`** — B0 băm theo nội dung. Khử trùng lặp là phép so
chuỗi, **không tốn một lời gọi LLM nào** và tất định tuyệt đối. Đừng dựng lại bằng embedding như đường
khái niệm phải làm.

Quy mô corpus: **19 hình · 60 bảng** = 79 ứng viên media, bậc tối đa 2, 94% bậc 1.

`figure` và `table` là **tên kiểu dành riêng do code giữ** — LLM không được đặt hai tên này
(`spec-addendum` §0.1).

**Công thức không thành node ở vòng này** — 258 cái, nội dung lộn xộn thứ tự. `formula_refs` giữ nguyên
làm bằng chứng cho khái niệm.

## Cạnh: sàn đồng vị trí, không phải phán đoán

Cạnh `illustrates`/`tabulates` nối media sang **mọi thực thể học được trích từ cùng chunk** — suy trực
tiếp từ refs, tất định, không hỏi mô hình. Đây là **sàn recall**: không bao giờ sót cạnh đáng có.

Ticket 05 thêm tầng trên — mô hình đang nhìn ảnh nên nó xác nhận một **tập con** cạnh bằng
`confirmed: true`. Sai ở tầng đó **không xoá cạnh nào**, chỉ sai hoặc mất nhãn. Bất đối xứng này giống
hệt lý do ngưỡng blocking ở 2a thiên về recall.

## Media mồ côi là hợp lệ, nhưng phải khai lý do

Chunk có ảnh mà **không trích được thực thể nào** thì hình không có cạnh. Ba ca thật trong corpus:

```
baocao-canhan  126tok  'UỶ BAN NHÂN DÂN … TRƯỜNG ĐẠI HỌC SÀI GÒN…'      ← logo trên trang bìa
nhap-mon-ml     40tok  'lychee-inspired spherical chair / a girl giving…' ← 3 ảnh, gần như không chữ
xstk-ch3-1      25tok  'Khi đó ta có các kết quả sau: [formula]…'         ← toàn dấu công thức
```

**Logo trường trên trang bìa không minh hoạ khái niệm nào — và đó là đúng.** Bắt nó luôn có cạnh thì
người soát học cách bỏ qua cờ, rồi cờ thật cũng bị bỏ qua theo — đúng lớp lỗi *"cảnh báo không đọc được
thì bằng không có cảnh báo"* B0 đã dập bốn lần.

Nên media mồ côi mang `orphan_reason`, và **chỉ `unknown` mới là cờ thật**.

**Blocked by:** 01 — cần mô hình dữ liệu ứng viên. Không phụ thuộc 02/03: đường này không đi qua LLM nên
không cần xác minh bằng chứng.

**Status:** done

- [x] Ứng viên `figure`/`table` sinh từ refs của chunk, **không** gọi mô hình
- [x] Khử trùng lặp bằng `media_id` (băm nội dung), không bằng embedding
- [x] Ứng viên media mang `chunk_id` + vị trí ký tự của dấu, cùng hệ toạ độ với thực thể khái niệm
- [x] Cạnh `illustrates`/`tabulates` nối media sang **mọi thực thể học được trích từ cùng chunk**
- [x] Ảnh/bảng **có** chú thích ⇒ `description` = chú thích, `caption_source: original`
      (8/19 hình · **4/64 bảng**)
- [x] Ảnh/bảng **không** chú thích ⇒ chuyển sang ticket 05 để sinh mô tả — **không** để trống
- [x] Media không nối được thực thể nào ⇒ `orphan_reason` ∈ `cover_art` · `no_concept_in_chunk` ·
      `unknown`; **chỉ `unknown` phát cảnh báo**
- [x] Tỉ lệ media mồ côi ghi vào thống kê — cao bất thường nghĩa là A3 không trích được gì ở chunk có
      ảnh, đó mới là tín hiệu đáng nhìn
- [x] Trên bốn fixture: đúng **19 `figure` + 60 `table`**, không thừa không thiếu
- [x] Có test: hai chunk tham chiếu cùng một hình ⇒ **một** ứng viên, hai cạnh
- [x] Có test: chunk trang bìa (không thực thể nào) ⇒ media mồ côi có `orphan_reason`, **không** cảnh báo
