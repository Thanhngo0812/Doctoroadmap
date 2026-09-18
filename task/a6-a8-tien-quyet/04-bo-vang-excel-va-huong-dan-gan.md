# 04 — Bộ vàng: file Excel gán mù và hướng dẫn gán nhãn

**What to build:** Hai người gán nhãn mở một **file Excel** ra là làm được ngay: đọc chương trong sách, ghi các
quan hệ tiên quyết họ thấy, và đánh cờ khi danh sách khái niệm có gì sai. Kèm một **hướng dẫn** viết theo giao
thức PREAP. Đọc ngược file đó về thành dữ liệu chấm được.

Luật ở spec D13 và ADR 0009.

**Blocked by:** None — bắt đầu được ngay. (Việc của Claude.)

**Status:** done — 2026-09-16, trên nhánh `ve-04-bo-vang` (tách từ `85816ea`)

- [x] Lệnh sinh file Excel từ artifact canonical của một tài liệu và một chương.
- [x] Bốn sheet: hướng dẫn; khái niệm (khoá, kèm nơi dạy theo chương, mục, trang); quan hệ; cờ.
- [x] Sheet quan hệ: khái niệm đích chọn trong phạm vi **chương đã chọn**; đầu được cần chọn trong **mọi khái
      niệm của tài liệu**; kèm vị trí trong sách, loại bằng chứng, ghi chú.
- [x] **Mù:** file không chứa cạnh nào của pipeline, kể cả quan hệ đề xuất của A3 và 2a.
- [x] Ô ẩn ghi phiên bản artifact và phiên bản danh sách khái niệm.
- [x] Đọc ngược file: bắt được khái niệm không tồn tại, cặp trùng, cạnh tự nối, và file gán cho phiên bản
      artifact khác.
- [x] Hướng dẫn gán nhãn bằng tiếng Việt: định nghĩa quan hệ tiên quyết, luật "như đoạn này trình bày", ví dụ
      đúng và sai, các ca khó (nhắc trong định nghĩa nhưng không cần để hiểu; cha–con; anh em), và luật không
      phải gán mọi cặp.
- [x] `openpyxl` khai thành phụ thuộc trực tiếp.
- [x] Test theo seam bộ vàng; đột biến tối thiểu: rò cạnh pipeline vào file, danh sách chọn sai phạm vi, bỏ ô
      phiên bản.

## Cách dùng

```text
# 1. Xem chương và số khái niệm đích ở từng cấp heading
doc2roadmap a8-gold-sheet --doc-id <doc> --list-chapters [--chapter-level 2]

# 2. Sinh một file cho mỗi người gán (không ghi đè file đã có, trừ khi --force)
doc2roadmap a8-gold-sheet --doc-id <doc> --chapter-level 2 --chapter 10-13 --annotator A1
doc2roadmap a8-gold-sheet --doc-id <doc> --chapter-level 2 --chapter 10-13 --annotator A2

# 3. Người gán nộp file về; kiểm, và chỉ đóng băng thành JSON khi không còn lỗi
doc2roadmap a8-gold-check --doc-id <doc> --chapter-level 2 --chapter 10-13 \
    --file <file đã gán> --output artifacts/a8-gold/vang/<doc>-A1.json
```

`--chapter` nhận một số, một dải (`10-13`), một danh sách (`2,4`) hoặc một `section_id`. File và JSON chỉ được ghi
trong `artifact_dir`, vì chúng chứa nội dung rút từ sách. `a8-gold-check` trả mã 1 khi file còn lỗi.

## Bằng chứng bàn giao

**Sản phẩm**

| Thứ | Nơi |
|---|---|
| Sinh và đọc file gán | module `a8_gold` trong use case (không đụng code pipeline của nhân viên) |
| Hai lệnh `a8-gold-sheet`, `a8-gold-check` | CLI |
| Hướng dẫn cho người gán | [`doc/huong-dan-gan-nhan-tien-quyet.md`](../../doc/huong-dan-gan-nhan-tien-quyet.md) |
| Báo cáo chi tiết về PREAP | [`report/preap-giao-thuc-gan-nhan-tien-quyet.md`](../../report/preap-giao-thuc-gan-nhan-tien-quyet.md) |
| Phụ thuộc | `openpyxl==3.1.5` trong `pyproject.toml`; `uv.lock` đổi đúng 2 dòng (`uv lock --offline`) |

**Những gì file Excel làm, ngoài yêu cầu tối thiểu**

- Danh sách chọn dùng tên định nghĩa trong workbook, nên Excel 365 tìm được theo chữ đang gõ.
- Tô màu ngay trong sheet: đỏ khi A trùng B, vàng khi một cặp bị ghi hai lần, tím khi có cả hai chiều.
- Hai ô ghi **thời gian gán** và **thời gian rà soát**, đọc ngược vào kết quả — PREAP đo thời gian, và đánh giá của
  họ chỉ có số trên đoạn văn ngắn.
- Cột *Mức cần* (Bắt buộc / Hữu ích), không bắt buộc, theo đề xuất trọng số của PREAP.
- Sheet cờ có sáu loại: không phải khái niệm, thiếu khái niệm, node gộp sai, tên sai, nơi dạy sai, khác.
- Bảng tra "C số → tên chương" trong sheet Hướng dẫn, vì cột *Nơi dạy* ghi `[C số]`.
- **Không ghi đè im lặng** file đã có: chạy lại lệnh sinh trên file người gán đã nộp về sẽ bị từ chối.
- Kiểm **vòng mọi độ dài** trong nhãn của từng người (PREAP coi quan hệ tiên quyết là bất đối xứng và bắc cầu).

**Chạy thử trên artifact thật** (bản chép trong scratchpad; không gọi mô hình)

- `xstk-ch3-1`, cấp 2, dải `10-13` (phần ước lượng 2.1–2.4): 26 khái niệm đích / 98 khái niệm, 208 dòng quan hệ.
- `nhap-mon-ml`, cấp 1, mục 6 (chương 1): 60 khái niệm đích / 75, 480 dòng quan hệ.
- Điền thử ba quan hệ bằng nhãn thật, trong đó một dòng tự nối, cộng một cờ thiếu khái niệm: lệnh kiểm trả mã 1 và
  **không** ghi JSON. Xoá dòng lỗi thì trả mã 0 và ghi JSON với `node_id` thật, thời gian 35 phút, đúng hai cạnh
  và một cờ.

**Hai điều chỉ lộ ra trên dữ liệu thật, đã sửa**

1. **Alias trong node canonical là object** (`candidate_id`, `name`, `evidence`), không phải chuỗi. Bản đầu in
   nguyên object vào cột *Tên khác*. Đã sửa, và fixture test giờ dùng đúng hình dạng alias thật.
2. **Cây heading không khớp chương của tác giả.** Ở `xstk-ch3-1`, cấp 1 chỉ có một mục ôm cả 98 khái niệm, còn ba
   phần 1.x, 2.x, 3.x nằm phẳng ở cấp 2, lẫn cả vài đầu mục bài tập. Ở `nhap-mon-ml`, cấp 1 lẫn trang bìa và mục lục.
   Vì vậy đơn vị gán nhận **một dải hoặc danh sách mục** ở một cấp đã chọn. Đã ghi bổ sung vào spec D13.

**Test**

- `tests/unit/application/test_a8_gold.py`: **21 test**, gồm hai test đi qua CLI.
- Toàn bộ test khi chặn mạng: **320/320**, gồm 299 test cũ.
- **26 đột biến, 26 bị bắt**, file khôi phục đúng từng byte sau mỗi lần:

| # | Đột biến | Test bắt |
|---|---|---|
| M1 | rò cạnh pipeline vào file qua alias | cạnh pipeline không bao giờ vào file |
| M2 | danh sách đích lấy mọi khái niệm | danh sách chọn đúng phạm vi |
| M3 | cột đích dùng danh sách mọi khái niệm | danh sách chọn đúng phạm vi |
| M4 | không kiểm mã danh sách khái niệm | từ chối file của artifact khác |
| M5 | không kiểm phiên bản canonical | từ chối file của artifact khác |
| M6 | nhận khái niệm đích ngoài chương | báo đủ lỗi |
| M7 | bỏ kiểm vòng | từ chối vòng mọi độ dài |
| M8 | bỏ kiểm cặp trùng | báo đủ lỗi |
| M9 | nhận dòng thiếu loại bằng chứng | báo đủ lỗi |
| M10 | bỏ kiểm tự nối | báo đủ lỗi; CLI chỉ đóng băng file sạch |
| M11 | nhãn không phân biệt tên trùng | nhãn luôn duy nhất; đọc ngược đúng node |
| M12 | nơi dạy bỏ số trang | nơi dạy ghi chương, mục, trang |
| M13 | media thành khái niệm đích | phạm vi khái niệm; đếm chương; CLI |
| M14 | thời gian không nhận dấu phẩy | đọc ngược đúng node |
| M15 | không đòi canonical đã qua A5 | phạm vi từ store |
| M16 | cờ "Tên sai" không cần khái niệm | báo đủ lỗi |
| M17 | CLI ghi file ngoài `artifact_dir` | CLI từ chối ghi ra ngoài |
| M18 | CLI đóng băng cả file còn lỗi | CLI chỉ đóng băng file sạch |
| M19 | CLI trả mã 0 khi file còn lỗi | CLI chỉ đóng băng file sạch |
| M20 | xác định chương sai cấp | bắt ngay lúc nạp test (dữ liệu tham số hoá không dựng được) |
| M21 | alias object không được mở ra | danh sách chọn đúng phạm vi |
| M22 | bỏ chặn ghi đè | không ghi đè im lặng; CLI |
| M23 | dải mục chỉ lấy đầu dải | một đơn vị gán ghép nhiều mục; từ chối chương sai |
| M24 | nhãn dải không gộp số liền nhau | một đơn vị gán ghép nhiều mục |
| M25 | mã danh sách không phụ thuộc đơn vị gán | một đơn vị gán ghép nhiều mục (thêm mục bài tập không có khái niệm) |
| M26 | CLI luôn ghi đè | CLI chỉ đóng băng file sạch (lần sinh thứ hai phải bị từ chối) |

M25 lọt ở lượt đầu: fixture cũ không có mục nào trống khái niệm, nên đổi đơn vị gán là đổi luôn tập khái niệm đích.
Đã thêm một mục "Bài tập" không có khái niệm để giữ đúng điều đó.

**Chưa làm, để vé sau**

- Tính độ đồng thuận có kể bắc cầu, gộp nhãn sau hội ý, và chấm: vé 05 và 12.
- Nhánh này chưa gộp vào `main`: trên `main` nhân viên đang có thay đổi chưa commit ở đúng `main.py`,
  `pyproject.toml` và `uv.lock`.
