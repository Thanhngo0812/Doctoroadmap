# D-02 — Dữ liệu nhãn cấu trúc cho A1: cây mục và trang mẫu, gán bằng agentic, người duyệt mẫu

**Nguồn chân lý:** [kiểm thử vé 12–14](../../report/kiem-thu-ve-12-13-14-a1-mo-rong-2026-10-08.md) mục 5 · [vé 14](14-hoc-nhan-tieu-de.md) ·
[vé 15](15-a1-danh-gia-doc-lap-chon-duong.md) (dùng nhãn này) · [đặc tả D-01](D-01-dac-ta-du-lieu-pass-phu.md) (cách làm tương tự) ·
**Ai:** chủ dự án gán bằng agentic và duyệt mẫu; nhân viên xuất phiếu và viết bộ chấm; Claude chấm tập khoá ·
**Chi phí mô hình của dự án:** 0 USD.

**Trạng thái:** soạn 2026-10-08. Sách mới đã kiểm (mục "Sách"), cả hai đợt bổ sung `new-doc-2` và `new-doc-3`. Tập khoá đủ 8 cuốn PDF gốc
(toán rời rạc không cần nữa). Chờ chủ dự án xác nhận quyền dùng.

## Vì sao (Claude, 2026-10-08)

- **Thước đo đang dùng không đủ.**
  - Vé 14 đo bộ đọc nhẹ bằng độ khớp với docling (nhãn bạc), trên 19 cuốn đã xem qua nhiều vòng.
  - Sau 25 vòng, tỉ lệ chunk cùng mục lá với docling chỉ từ 0,616 lên 0,642.
  - Docling cũng sai: cấp mục phẳng, chú thích hình bị nhận thành tiêu đề, nhãn "Ví dụ 14." bị nhận thành tiêu đề. "Khớp docling" vì thế không
    phải "đúng".
- **Cần đáp án độc lập.** Cần nhãn cấu trúc trên sách chưa xem, để so **cả docling lẫn bộ đọc nhẹ** với cùng một đáp án.
- **Cách làm theo D-01.** Agentic gán (bạc), người duyệt một mẫu (vàng), báo cả hai.

## Sách (Claude kiểm 2026-10-08, 0 USD)

20 PDF trong `document-data/new-data-document/`, 10 lĩnh vực. Thêm đợt bổ sung `document-data/new-doc-2/`: 8 tệp, trong đó 3 cuốn mới.
- **Không trùng với sách đã có.** Không cuốn nào trùng byte với sách test (chỉ so băm, không đọc nội dung sách test), hay với sách D-01, doc-1,
  doc-4, xstk. Nội dung trùng với sách cũ tối đa 2%.
- **Thiếu tệp đi kèm.** README nhắc `manifest-d02.json` và báo cáo nghiệm thu, nhưng hai tệp này **chưa có**.
- **Bản quyền chưa ghi.**

**Phát hiện chính: 16/20 cuốn là sách quét kèm lớp chữ OCR, không phải PDF gốc.**
- Mỗi trang là một ảnh phủ kín trang; chữ là lớp OCR ẩn, phần lớn do Internet Archive làm, dùng font `GlyphLessFont`. Lớp này không có đậm,
  nghiêng hay tên font thật.
- **Đặc trưng mạnh nhất của bộ đọc nhẹ vô dụng ở đây.** Ở vé 14, "đậm" chiếm 42% độ quan trọng của mô hình nhận tiêu đề. Mô hình bố cục của
  docling nhìn ảnh nên vẫn chạy được.
- **Lỗi OCR mà cổng chữ không bắt được.** Chữ OCR có lỗi dấu thanh ("có thê", "mô ta", "quả trình"). Các lỗi này vẫn tạo ra âm tiết hợp lệ.
- So sánh: 16 cuốn D-01 và doc-1, doc-4, xstk đều là PDF gốc.

| sách | lĩnh vực | trang | loại | chữ (âm tiết hợp lệ) | trang bị cờ | vai trò đề xuất |
|---|---|---:|---|---|---:|---|
| dai-so-tuyen-tinh-bui-xuan-dieu-hust (`new-doc-2`) | Toán | 97 | gốc (LaTeX), có mục lục điện tử 104 mục; chỉ trùng 1,7% nội dung với doc-1 | 0,924, nhiều công thức | 0 | **khoá, gốc** |
| giai-tich-1-le-chi-ngoc-hust (`new-doc-2`) | Toán | 139 | gốc (Word), bài giảng khổ A4 | 0,854, nhiều công thức | 0 | **khoá, gốc** |
| toan-roi-rac-nguyen-duc-nghia-hust (`new-doc-2`) | Toán | — | **tệp tải thiếu**: dừng giữa bảng xref, không có `startxref` hay `%%EOF`; pypdfium2 không mở được | — | — | tải lại rồi kiểm |
| kinh-te-vi-mo-1-ptit (`new-doc-3`) | Kinh tế | 180 | gốc (Word); khác d01-09, chỉ trùng 0,2% | 0,978 | 0 | **khoá, gốc** |
| luat-kinh-doanh-ptit (`new-doc-3`) | Pháp luật | 264 | gốc (Word) | 0,995 | 0 | **khoá, gốc** |
| tam-ly-hoc-dai-cuong-hcmue | KHXH | 145 | gốc (Google Docs), có mục lục điện tử 225 mục | 0,995 | 0 | **khoá, gốc** |
| ly-thuyet-mach-ptit | Kỹ thuật | 183 | gốc (Word) | 0,927, nhiều công thức | 0 | **khoá, gốc** |
| vat-ly-2-dien-tu-quang-ptit | Vật lý | 310 | gốc (Word) | 0,954, nhiều công thức | 0 | **khoá, gốc** |
| mang-may-tinh-nguyen-toan-thang | CNTT | 214 | gốc (in từ trình duyệt); trang bản quyền có lỗi OCR; ghi bản quyền NXB Giáo dục | 0,901 | 0 | **khoá, gốc** |
| xahoi-hoc-dai-cuong-ussh-vnu | KHXH | 369 | quét + OCR | 0,964 | 0 | **khoá, quét** |
| tai-chinh-doanh-nghiep-le-thi-xuan | Kinh tế | 408 | quét + OCR | 0,980 | 8 | **khoá, quét** |
| nha-nuoc-va-phap-luat-dai-cuong-vnu | Pháp luật | 350 | quét + OCR | 0,995 | 1 | **khoá, quét** |
| sinh-hoc-te-bao-nguyen-nhu-hien | Sinh | 259 | quét + OCR | 0,927 | 0 | **khoá, quét** |
| giai-phau-nguoi-dai-hoc-y-ha-noi | Y | 516 | quét + OCR | 0,961 | 0 | **khoá, quét** |
| cau-truc-du-lieu-giai-thuat-do-xuan-loi | CNTT | 305 | quét + OCR; mã giả | 0,942 | 12 | **khoá, quét** |
| hoa-hoc-huu-co-tap-1-tran-manh-binh | Hoá | 373 | quét + OCR; OCR ra chữ Kirin (2% chữ cái) | 0,803 | 286 | kiểm cổng chữ, không gán |
| giai-phau-nguoi-nguyen-van-huy | Y | 204 | quét + OCR; tách âm tiết 6,3% | 0,939 | 124 | kiểm cổng chữ, không gán |
| vat-ly-dai-cuong-tap-1-co-nhiet | Vật lý | 515 | quét + OCR | 0,959 | 16 | dự phòng |
| hoa-dai-cuong-nguyen-minh-tuyen | Hoá | 328 | quét + OCR | 0,912 | 20 | dự phòng |
| dieu-khien-robot-cong-nghiep-nguyen-manh-tien | Kỹ thuật | 270 | quét + OCR; công thức OCR hỏng | 0,921 | 47 | dự phòng |
| phap-luat-dai-cuong-nguyen-thi-hong-van | Pháp luật | 280 | quét + OCR | 0,996 | 0 | dự phòng |
| xac-suat-thong-ke-le-van-dung-dhsp-dn | Toán | 204 | quét + OCR; 9 trang không chữ | 0,947 | 17 | dự phòng |
| dai-so-tuyen-tinh-le-tuan-hoa | Toán | 447 | quét + OCR (Acrobat); công thức OCR hỏng | 0,939 | 1 | dự phòng |
| chu-giai-di-truyen-hoc-vnu | Sinh | 279 | quét + OCR; sách chú giải dạng từ điển | 0,936 | 3 | dự phòng, không phải giáo trình |
| nguyen-ly-ke-toan-ueh-iuh | Kinh tế | 260 | quét + OCR; sách bài tập, nhiều bảng | 0,949 | 3 | dự phòng, không phải giáo trình |

"Trang bị cờ" là số trang vi phạm luật cổng chữ của vé 13, cộng luật tỉ lệ chữ ngoài Latin/Hy Lạp ≥ 1% của vé 13b.

### Phân tập

| tập | sách | ai được xem |
|---|---|---|
| **khoá, gốc** | 8 cuốn đánh dấu "khoá, gốc" ở bảng trên | chỉ Claude và chủ dự án |
| **khoá, quét** | 6 cuốn quét đánh dấu "khoá, quét" | chỉ Claude và chủ dự án |
| **phát triển có nhãn** | 6 cuốn D-01: d01-02 (toán), d01-06 (sinh), d01-07 (CNTT), d01-10 (kinh tế), d01-11 (luật), d01-15 (nông nghiệp) | nhân viên được xem hết |
| kiểm cổng chữ | hoá hữu cơ, giải phẫu Nguyễn Văn Huy | nhân viên (vé 13b) |
| dự phòng | 8 cuốn còn lại | đo tốc độ và kiểm lỗi chạy; không gán |

- **Sách gốc còn thiếu:** xuất từ Word, LaTeX hay Google Docs; **không** lấy bản quét Internet Archive.
  - Lý do: chủ dự án nói đầu vào sau này sẽ sạch như doc-4, doc-1, nên quyết định cho PDF gốc là quyết định chính.
  - Cần ít nhất 8 cuốn để quyết định theo từng cuốn; ít hơn thì kết quả chỉ để tham khảo.
- **Đợt `new-doc-2` (2026-10-08):** 8 tệp.
  - 5 tệp trùng byte với đợt trước: 4 cuốn gốc và giải phẫu Nguyễn Văn Huy. Chỉ dùng một bản.
  - Giải phẫu Nguyễn Văn Huy vẫn là bản quét: ảnh phủ kín mọi trang, chữ OCR lỗi nặng ("Các Sòi C(J. các bó sơi co'"). Nó không tính là sách gốc.
  - 2 cuốn toán HUST dùng được; toán rời rạc phải tải lại.
  - Sau đợt này đã có 3 cuốn toán (tính cả toán rời rạc), nên cuốn bổ sung phải **ngoài toán**: hoá, sinh, kinh tế, luật hoặc y.
- **Khoá nghĩa là:** nhân viên không mở PDF, không xem nhãn, không xem kết quả từng cuốn của tập khoá. Claude (hoặc chủ dự án) chạy script xuất
  phiếu của nhân viên trên tập khoá. Đánh giá cuối do Claude chạy **một lần**, với cấu hình đã đóng băng (vé 15, pha 4).

## Nhãn

Nhân viên xuất phiếu (vé 15, pha 1). Mỗi cuốn có:
- `dong/<sach>.jsonl`: mỗi dòng chữ của lớp chữ PDF (pypdfium2) một bản ghi, gồm `id` dạng `p0012-l003`, `trang`, `text`, `bbox`, `co_chu`, `dam`.
  Đây là **mã dòng chuẩn**; mọi nhãn trỏ vào mã này.
- `trang/<sach>/p0012.png`: ảnh trang khoảng 110 dpi.
- `muc_luc_dien_tu/<sach>.json`: mục lục điện tử (bookmark) nếu PDF có. Chỉ là gợi ý, phải đối chiếu với trang.

### L1 — cây mục của cả cuốn (bắt buộc)

- **Phạm vi trang:** cả cuốn nếu sách từ 300 trang trở xuống; nếu dài hơn thì trang 1–300.
- **Đầu ra:** `cay-muc/<sach>.jsonl`, mỗi tiêu đề một dòng, theo thứ tự đọc:

```json
{"sach": "tam-ly-hoc-dai-cuong-hcmue", "id": "h017", "dong": ["p0031-l002", "p0031-l003"], "text": "Chương 2. Cơ sở tự nhiên của tâm lý",
 "cap": 1, "cha": null, "vung": "noi_dung", "ghi_chu": ""}
```

| trường | luật |
|---|---|
| `dong` | mọi mã dòng tạo nên tiêu đề; tiêu đề nhiều dòng thì ghi đủ |
| `text` | chữ của tiêu đề, ghép từ các dòng; giữ nguyên lỗi trích chữ, vì so khớp dùng mã dòng |
| `cap` | độ sâu trong cây logic của sách, 1 là cao nhất |
| `cha` | `id` của tiêu đề cha; `null` khi `cap` là 1. Tiêu đề cha phải có `cap` nhỏ hơn đúng 1 |
| `vung` | chỉ ghi cho tiêu đề cấp 1, theo vai trò vùng của A2: `mo_dau` (lời nói đầu, giới thiệu, mục lục), `noi_dung`, `bai_tap`, `de_cuong`, `hanh_chinh` (bìa, bản quyền), `cuoi_sach` (tài liệu tham khảo, phụ lục, chỉ mục) |
| `ghi_chu` | `"nghi"` khi phân vân; `"liền đoạn"` khi tiêu đề in chung dòng với câu văn |

**Là tiêu đề:** dòng đặt tên cho một mục trong cấu trúc logic của sách.
- Phần, Chương, Bài (khi là bài học).
- Mục đánh số (`1.`, `1.1`, `I.`, `A.`, `a)`) khi mở một đoạn có nội dung riêng.
- Tiêu đề không đánh số nhưng in nổi bật và mở một mục: "Tóm tắt", "Câu hỏi ôn tập", "Bài tập chương 2", "Tài liệu tham khảo", "Lời nói đầu",
  "Mục lục", "Phụ lục".
- Sách luật chia theo điều: "Điều N. <tên điều>" là tiêu đề cấp thấp nhất.

**Không là tiêu đề:**
- đầu trang và chân trang lặp lại; số trang;
- chú thích hình, bảng ("Hình 2.1 …"); chữ nằm trong hình;
- các dòng liệt kê trong trang mục lục (riêng dòng "MỤC LỤC" là tiêu đề);
- nhãn khối như "Định nghĩa 1.2", "Định lý 3", "Ví dụ 4", "Chú ý", "Nhận xét", "Hệ quả"; "Bài 5" khi là bài tập;
- khoản và điểm liệt kê bên trong một điều luật.

**Cấp mục theo logic của sách, không theo cỡ chữ:**
- Không có "Phần" thì "Chương" là cấp 1.
- Mục không đánh số ngay dưới chương (ví dụ "Bài tập chương 2") là con của chương đó, kể cả khi in to.
- Tiêu đề "liền đoạn" ("1.2. Khái niệm. Tế bào là …") thì ghi mã dòng đó, `text` chỉ lấy phần tiêu đề.

### L2 — trang mẫu (bắt buộc với tập khoá; tuỳ chọn với tập phát triển)

- **Chọn trang:** script xuất phiếu chọn 8 trang mỗi cuốn, tất định theo seed, phân tầng: trang mở chương, trang có bảng, trang có hình, trang
  nhiều công thức, hai trang thường, một trang cuối sách, một trang ngẫu nhiên. Ghi danh sách trang vào `chon-trang-mau/<sach>.json`.
- **Đầu ra:** `trang-mau/<sach>.jsonl`, mỗi trang một dòng:

```json
{"sach": "…", "trang": 47, "dong": {"p0047-l001": "dau_trang", "p0047-l002": "tieu_de", "p0047-l003": "than_bai"},
 "thu_tu": ["p0047-l002", "p0047-l003"], "co_bang": false, "co_hinh": true, "ghi_chu": ""}
```

- **`dong`:** gán **mọi** mã dòng của trang một vai trò:
  - `tieu_de`, `than_bai`, `danh_sach`;
  - `cong_thuc`, `bang`, `ma_lenh`;
  - `chu_thich_hinh`, `chu_trong_hinh`;
  - `dau_trang`, `chan_trang`, `so_trang`, `chu_thich_cuoi_trang`;
  - `muc_luc`, `khac`.
- **`thu_tu`:** thứ tự đọc đúng của mọi dòng, trừ `dau_trang`, `chan_trang`, `so_trang`, `chu_trong_hinh`. Bảng đọc theo hàng; hai cột đọc hết cột
  trái rồi sang cột phải.

### Người duyệt (vàng)

- **Chủ dự án duyệt:**
  - toàn bộ L1 của 2 cuốn khoá (1 gốc, 1 quét);
  - 10% tiêu đề ngẫu nhiên của các cuốn khoá còn lại;
  - 20 trang L2 ngẫu nhiên.
- Sửa ghi vào tệp riêng `duyet/<sach>.jsonl`; không ghi đè nhãn agentic.
- Báo độ khớp giữa agentic và người: F1 tiêu đề, độ đúng của cha, độ đúng vai trò dòng.
- Khi chấm, chỗ có bản người sửa thì dùng bản người (vàng), chỗ khác dùng nhãn agentic (bạc). Báo số trên cả hai.

### Kiểm chất lượng

- Script kiểm định dạng do nhân viên viết (vé 15, pha 1). Phải kiểm:
  - mã dòng tồn tại;
  - `cap` và `cha` nhất quán;
  - trang L2 được gán đủ mọi dòng;
  - `thu_tu` là hoán vị đúng tập dòng cần xếp.
- Cuốn tâm lý học có mục lục điện tử: so cây của agentic với mục lục đó để kiểm nhanh. Mục lục điện tử không phải vàng, vì có thể thiếu mục.
- Nếu làm được: hai lượt agentic độc lập trên 2 cuốn, báo độ khớp.
- **Khi đưa agentic gán nhãn:** chỉ đưa [hướng dẫn gán D-02](../../report/huong-dan-agentic-gan-nhan-d02.md) (soạn 2026-10-08), phiếu và
  script kiểm. Không đưa tệp đặc tả này, không đưa kết quả của docling hay bộ đọc nhẹ. Tên tệp và luật định dạng trong hướng dẫn là chuẩn
  cho script xuất phiếu và script kiểm (vé 15, pha 1).

## Quyền và thứ tự làm

1. **Chủ dự án xác nhận quyền dùng 20 cuốn và dịch vụ agentic sẽ nhận nội dung.**
   - Chạy A1 tại máy để nghiên cứu là 0 USD và không gửi sách đi đâu.
   - Agentic gán nhãn là gửi ảnh và chữ của trang cho một dịch vụ ngoài, nên cần xác nhận như D-01.
   - Cuốn mạng máy tính có dòng cấm sao chép của NXB Giáo dục.
   - Cùng lúc, bổ sung `manifest-d02.json`: tên, tác giả, năm, nguồn tải, quyền.
2. Nhân viên làm vé 15, pha 1 (xuất phiếu); Claude kiểm.
3. Agentic gán L1 cho 6 cuốn phát triển trước, để nhân viên viết bộ chấm. Sau đó gán L1 và L2 cho tập khoá.
4. Chủ dự án duyệt mẫu theo mục "Người duyệt".
