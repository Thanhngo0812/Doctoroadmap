# Kiểm thử vé 12, 13, 14 và đợt A1 mở rộng (Claude, 2026-10-08)

**Phạm vi:**
- mã chưa commit của nhân viên trong worktree (`src/`, `tests/`, `scripts/`);
- các báo cáo `report/v4-12-*`, `v4-13-*`, `v4-14-*`;
- artifact trong kho.

0 USD; không chạy khâu trả tiền; không mở `document-data/test/`.

## Kết luận

| vé | kết luận | việc tiếp |
|---|---|---|
| 12 — D-01 bước 2 | **Đạt.** Nhận với hai giới hạn đã biết: phiếu kiểm ít, chữ lỗi còn sót nhẹ | Chủ dự án giao `tmp/d01-phieu/phieu.jsonl` cho agentic theo D-01 bước 3 |
| 13 — bộ đọc chữ tiếng Việt | **Đạt một phần.** Mặc định pypdfium2 và chặn lệnh tốn tiền làm đúng. Cổng chữ có hai lỗi đã tái hiện | [vé 13b](../task/v4/13b-sua-cong-chat-luong-chu.md) |
| 14 vòng 1 — bộ nhận tiêu đề | **Đạt.** Kết quả nghiên cứu âm tính, báo trung thực | — |
| A1 mở rộng (R2–R25) | Phần đưa vào sản phẩm: **nhận**. Nghiên cứu R4–R25: **đề nghị dừng** | Chủ dự án quyết hướng (mục 5) |

## 1. Đã kiểm lại độc lập

- **Toàn bộ test dự án, có integration:** 1.081 đạt, 3 bỏ qua, 0 lỗi. Nhóm A1/heading trong `tmp/venv-ml`: 160 đạt.
  - Chạy pytest không có `--basetemp` sẽ báo "Access is denied". Lỗi do thư mục tạm của máy, không phải do mã.
- **Vé 12, chuỗi artifact:** 16/16 artifact danh tính lần ngược về đúng chunks mới nhất, qua Vertex.
- **Vé 12, chi và thời gian:** chạy lại `scripts/do-chi-phi/bao_cao.py` cho 16 cuốn được 28,0558 USD LLM đo được và 669,8 phút. Khớp từng số với báo
  cáo nhân viên.
- **Vé 12, phiếu:**
  - 5.901 phiếu: 5.541 thật, 83 kiểm, 277 lặp;
  - 65.525 cặp: 62.012 / 371 / 3.142;
  - 0 lỗi cấu trúc (chỉ số câu, câu neo, `trong_cua_so`);
  - cả 277 phiếu lặp đều đảo thứ tự ứng viên;
  - đọc thêm 3 phiếu ngẫu nhiên (seed khác nhân viên): đọc được, khớp tên hợp lý.
- **Vé 14 vòng 1:** tính lại trung vị từ TP/FP/FN từng cuốn trong snapshot. F1 dòng 0,7553 → 0,8834, thấp nhất 0,2745. Khớp báo cáo.

## 2. Vé 12

**Mã sửa đúng và có test:**
- A2 dùng retry chung (8 lần, tôn trọng Retry-After).
- `a3` thiếu mục thì thoát mã 2.
- A3 có điểm lưu theo mục: kiểm `source_hash` và `chunks_version`, giữ cổng 40% khi nạp lại.
- Rò suất của limiter sửa bằng `finally`. `release` vốn idempotent và `reconcile` sau `release` vẫn đúng.
- Bắt thêm `HTTPException` và `OSError`.
- `json.loads(strict=False)` chỉ nới ký tự điều khiển nằm trong chuỗi.

Đây là các lỗi thật. Nhân viên chẩn đoán bằng stack (py-spy) và viết test tái hiện trước khi sửa. Nhân viên cũng sửa đúng một lỗi trong
`xuat_phieu.py` của tôi: script ghi `kiem` vào trường lĩnh vực, làm lộ phiếu kiểm.

**Giới hạn, tôi nhận với tư cách người soạn D-01:**
- **Phiếu kiểm ít.** Chỉ có 83 phiếu, 371 cặp có đáp án vàng (102 có cạnh, 269 không), vì vàng của doc-1, xstk, doc-4 chỉ đủ chừng này. Nhân
  viên không nhân bản là đúng.
  - Độ đúng của agentic đo được với sai số khoảng ±4 điểm % trên cả 371 cặp, và ±8 điểm % trên lớp có cạnh.
  - Đủ để phát hiện hướng dẫn sai nặng, không đủ để so tinh hai agent. Bù bằng phiếu lặp (3.142 cặp) và hai lượt A/B.
- **Phiếu kiểm vẫn nhận ra được nếu soi thống kê.** 45 phiếu mang lĩnh vực "Khoa học xã hội", lĩnh vực không có ở sách thật. Trung vị 4 ứng viên,
  so với 11 ở phiếu thật. Agentic không chủ đích dò nên rủi ro thấp; ghi nhận, không sửa.
- **Chữ Kirin sót.** 39 phiếu thật có câu chứa chữ Kirin trông như chữ Latin (mục 3, lỗi 1b). Không tên khái niệm nào bị dính. Không đáng chạy lại
  khâu trả tiền.
- **Chi.**
  - 28,06 USD là phần LLM đo được trên chuỗi cuối. Chưa gồm embedding, các lượt bị thay và các lượt thiếu số đo.
  - Guard 43,28/75 USD là số dự phòng, không phải hoá đơn. Số thật lấy trên hoá đơn Vertex.
  - Dự toán ban đầu của tôi, khoảng 20 USD, thấp hơn thực tế.

## 3. Vé 13

**Làm đúng:**
- mặc định của `ingest` và `build_ingest` là pypdfium2;
- ba lệnh tốn tiền (`label-roles`, `a3`, `roadmap` ở A6) kiểm cây parse được ghim trước khi gọi mô hình;
- cờ `--allow-text-quality-reason` bắt buộc có lý do;
- khoá cache cũ giữ nguyên.

### Lỗi 1 (đã tái hiện): cổng bỏ sót chữ bị thay bằng chữ Kirin

Chạy `DoclingParser` thật trên vài trang:

| trang | bộ đọc | âm tiết hợp lệ | cảnh báo | mẫu chữ |
|---|---|---:|---:|---|
| d01-11 tr. 28–31 | docling-parse | 0,278 | **0** | "Ký kӃt và thӵc hiӋn hӧp đӗng vӟi chӫ vұt thӇ" |
| d01-05 tr. 38–41 | docling-parse | 0,428 | **0** | "xҧy ra sӵ tăng cѭӡng chuyӇn đӝng" |
| d01-08 tr. 58–61 | docling-parse | 0,685 | 3 (bắt đúng) | "Th ờ i gian ch ờ đợ i" |
| cả ba | pypdfium2 | 0,94–1,00 | 0 | chữ chuẩn |

- **Nguyên nhân.**
  - Luật âm tiết chỉ cảnh báo khi đồng thời có tách âm tiết từ 1% trở lên.
  - Tập ký tự lạ `_STRANGE` không có chữ Kirin.
  - Dấu hiệu có sẵn trong chính bảng đo của nhân viên: với docling-parse, 6 cuốn (d01-05, 06, 11, 13, 15, 16) chỉ có 0,38–0,46 âm tiết hợp lệ
    mà không luật nào bật.
- **Chỉ số tách rõ:** tỉ lệ chữ cái ngoài hệ Latin/Hy Lạp là 13–18% ở 6 cuốn đó (docling-parse), và không quá 0,4% ở mọi bản pdfium.
- **1b.** Cây parse sạch đang ghim của d01-05 cũng có 694 chữ Kirin trông như chữ Latin, trong 148 từ ("сủа", "nghiệт", "сhất", "nướс").
  - Cây này dùng pypdfium2 cộng làm sạch v2, và là đầu vào của A2 → A9'' và phiếu.
  - Lỗi dồn ở trang 145, 108, 85 (2,2–2,8% số chữ của trang), vẫn qua cổng.
- **Mức độ:** mặc định pypdfium2 tránh được dạng nặng ở 16 cuốn này. Nhưng lưới an toàn có lỗ, với mọi bộ đọc.

### Lỗi 2 (đã tái hiện): bộ đọc chỉ định rõ bị tự đổi, nên lệnh tái lập T10 của xstk không còn dùng parse đã khoá

```
ingest xstk-ch3-1.pdf --doc-id xstk-ch3-1 --pdf-backend docling-parse --pdf-text-policy legacy --dry-run
→ parse: cần parse mới | selected: pypdfium2 | reason: quality_fallback
  docling-parse: reused=True, cảnh báo VNI trang 3
  pypdfium2: reused=False, chưa parse
```

- Trang 3 của xstk có chữ VNI thật ("Trong ñoù: … laø caùc …"). Cổng bắt đúng, nhưng `select_parse` tự chuyển bộ đọc dù người chạy đã chỉ định rõ.
- Khi dry-run, lượt chưa parse (`quality=None`) bị coi là sạch và được chọn.
- **Chạy thật:**
  1. parse lại bằng pypdfium2, mất vài phút;
  2. nếu cả hai bộ đọc cùng cảnh báo thì thoát lỗi;
  3. nếu có cờ lý do thì chọn bản nhiều âm tiết hợp lệ hơn, có thể không phải bộ đọc đã khoá.

  Khi đó văn bản lệch với chunk gắn A3, và bước chuyển vai trò ở T10 hỏng.
- Một phần lỗi do vé của tôi: vé 13 chỉ ghi "tự parse lại bằng bộ đọc kia", không phân biệt bộ đọc mặc định với bộ đọc ghim để tái lập.

### Tài liệu và việc nhỏ

- Bảng khoá T10 và `scripts/khoa-cau-hinh/tao_bang.py` thiếu `--pdf-text-policy legacy`, trong khi `CONTEXT.md` ghi cả hai lệnh tái lập phải có cờ
  này.
- Các bước trả tiền của xstk ở T10 giờ bị chặn vì VNI ở trang 3, còn naive-bayes bị chặn vì trang 11. Lệnh T10 chưa ghi điều này.
- Cổng không xét nút `title` (một loại tiêu đề có thật), lại liệt kê loại `heading` không tồn tại.
- Bảng trong báo cáo v4-13 là số đo trước khi sửa nhận diện VNI. Nhân viên đã ghi chú điều này.

## 4. Vé 14 vòng 1

Nghiên cứu đúng vé:
- đọc nguồn GROBID, CERMINE, VILA;
- đo leave-one-book-out trên 16 cuốn và kiểm ngoài trên 3 tài liệu;
- rà 50 bất đồng, báo độ quan trọng đặc trưng;
- đo tốc độ gồm cả đọc PDF.

Kết luận trung thực: M2 hơn luật nhưng **chưa đạt** mục tiêu nào, trừ tốc độ.

| | F1 dòng trung vị / thấp nhất | cùng mục lá | chunk trùng ≥ 0,8 | giây/trang |
|---|---|---:|---:|---:|
| mục tiêu | ≥ 0,90 / ≥ 0,75 | ≥ 0,85 | ≥ 0,70 | < 0,1 |
| luật v4 | 0,755 / 0,098 | 0,581 | 0,430 | 0,022 |
| M2 LightGBM | 0,883 / 0,275 | 0,742 | 0,637 | 0,025 |

## 5. A1 mở rộng

### Phần đã vào sản phẩm: nhận

- **R2-P: giữ chữ lặp** (`preserve` là adapter 13; `legacy` là adapter 11).
  - Tôi quét chữ pypdfium2 của 19 cuốn. Regex cũ khớp 113 chỗ, toàn là nội dung công thức hay hình: biến `x`, `n` ở d01-02 và xstk; `H H H` hoá
    học; `G G G` DNA; nhãn đồ thị.
  - Không chỗ nào là chữ in chồng giả đậm trong thân bài. Vậy giữ chữ lặp là đúng với kho đích.
  - Cái giá thứ nhất: test vàng bốn tài liệu giờ chỉ khoá đường `legacy`. Đường mặc định chỉ khoá số nút đổi (27 và 5), không khoá nội dung.
  - Cái giá thứ hai: PDF đọc bằng docling-parse như nhập môn ML lại có "P P P" (27 nút).
- **R3b: nguồn gốc chú thích hình** ghi trong `parse_stats`. Chỉ là metadata, không đổi chunk.
- **`declared-v1`** trong chunker: CLI và sản phẩm chưa gọi tới. Giữ nếu bộ đọc nhẹ sẽ vào luồng; nếu không, nên gỡ trước khi chốt đồ án.

### Nghiên cứu R4–R25: đề nghị dừng

Không vòng nào được đưa vào sản phẩm. Nhân viên báo trung thực, giữ cả các số giảm. Nhưng đường cong đã phẳng:

| mốc | cùng mục lá chặt, trung vị 16 cuốn | doc-1 |
|---|---:|---:|
| luật v4 (M0) | 0,466 | 0,804 |
| vòng 1, M2 | 0,616 | 0,618 |
| R5 | 0,639 | — |
| R19 | 0,644 | 0,462 |
| R25 | 0,642 | 0,452 |

- **Đang chỉnh theo từng trang.** R20–R25 sửa từng trang cụ thể (d01-01 tr. 176, d01-06 tr. 18 và 36, d01-08 tr. 42, 59 và 64…) trên 19 cuốn đã
  xem qua nhiều vòng.
  - Chỉ số chính chỉ tăng ở 1/19 cuốn (d01-08, +0,003).
  - R20 làm giảm nhẹ 3 cuốn: d01-01, doc-1, doc-4.
  - Đây là chỉnh trên tập phát triển, có nguy cơ quá khớp; nhân viên cũng tự ghi nhận điều này.
- **Kém nhất đúng ở loại sách sẽ dùng.** doc-1 (đại số tuyến tính) là kiểu sách sạch chủ dự án nói sẽ dùng sau này. Bản hiện tại kém cả luật v4
  lẫn M2 vòng 1 trên đúng cuốn này.
- **Lợi ích tối đa có giới hạn.**
  - Trên máy này, docling mất khoảng 11 phút/cuốn (180 phút cho 16 cuốn, đo khi máy chạy song song việc khác). Các khâu LLM mất khoảng 42
    phút/cuốn (669,8 phút cho 16 cuốn, vé 12).
  - Vậy một bộ đọc nhẹ hoàn hảo cũng chỉ bớt được khoảng 20% thời gian mỗi cuốn.
  - Trong sản phẩm, Developer API chạy song song cao nên khâu LLM nhanh hơn và tỉ phần của A1 sẽ tăng. Khi đó đòn bẩy rẻ hơn là chạy docling song
    song theo đoạn trang trên máy nhiều nhân, hoặc dùng GPU.
- **Chi phí bảo trì:** 87 script nghiên cứu, 38 tệp test và 86 tệp báo cáo (6,5 MB, có tệp JSON 1,7 MB) đang chưa commit.

**Đề xuất:**
1. Dừng chuỗi R. Nhân viên viết một trang tổng kết: cấu hình tốt nhất và các lỗi còn mở.
2. Giữ docling cho A1. Khi cần tốc độ, đo docling song song theo đoạn trang (đầu ra y hệt, đã kiểm ở vé 10) hoặc GPU trên máy triển khai.
3. Dùng kết quả làm tư liệu cho seminar Pha A không LLM.
4. Nếu chủ dự án vẫn muốn làm tiếp: trước khi chỉnh thêm, cần một tập đánh giá độc lập (sách mới, nhãn cây mục do người gán). Tôi có thể soạn
   đặc tả theo kiểu D-01.

## 6. Việc cho chủ dự án

1. Giao `tmp/d01-phieu/phieu.jsonl` cho agentic theo D-01 bước 3, giữ riêng `khoa.jsonl`. Khi có nhãn, gửi lại để tôi chấm phiếu kiểm và phiếu
   lặp.
2. Giao vé 13b cho nhân viên. Vé này không chặn việc gán nhãn D-01.
3. Quyết hướng A1 mở rộng: dừng (tôi đề xuất), hay làm tiếp với tập đánh giá độc lập.
4. Nhân viên commit theo nhóm: vé 12; vé 13; phần sản phẩm của A1 mở rộng; `scripts/doc-nhe`. JSON snapshot lớn nên để ngoài git hoặc nén lại.
5. Đối soát hoá đơn Vertex của đợt D-01.

## Tái lập các phát hiện

- **Lỗi 1:** dùng `import_pages` của pypdfium2 để tạo PDF nhỏ từ d01-11 tr. 28–31 và d01-05 tr. 38–41. Chạy `DoclingParser("docling-parse").parse(...)`,
  rồi `tree_text_quality(tree)`.
- **Lỗi 1b:** đếm chữ cái có tên Unicode không bắt đầu bằng LATIN/GREEK trong cây `parse_tree/d01-05/v2`.
- **Lỗi 2:** lệnh dry-run ở mục 3.
- **R2-P:** quét regex `(?<![^\W\d_])([A-Za-z])(?: \1){2,}` trên `get_text_range()` của pypdfium2 cho 19 cuốn.
