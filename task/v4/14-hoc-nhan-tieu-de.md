# v4-14 — Bộ nhận tiêu đề học từ nhãn docling, cho bộ đọc PDF nhẹ (nghiên cứu và triển khai thử)

**Nguồn chân lý:**
- [kiểm rộng 16 cuốn](../../report/v4-10-buoc-2b-kiem-rong-16-cuon-2026-10-05.md);
- [bước 2: bộ đọc nhẹ](../../report/v4-10-buoc-2-bo-doc-nhe-2026-10-05.md);
- mã `scripts/thu-a1/doc_nhe.py`, `doc_nhe_rong.py`, `so_chunk_doc_nhe.py`.

**Ai:** nhân viên nghiên cứu, triển khai thử, **báo cáo cho Claude kiểm** · **Phụ thuộc:** — (A1 của 16 cuốn D-01 đã có trong kho) ·
**Chi phí mô hình:** 0 USD. Không dùng LLM; chạy CPU tại máy.

**Trạng thái:** soạn 2026-10-05, chủ dự án giao cùng ngày.

## Vì sao (Claude, 2026-10-05)

Bộ đọc nhẹ (pypdfium2 cộng luật, không mô hình bố cục) nhanh hơn docling 55–450 lần. Một cuốn 400 trang mất khoảng 10–20 giây thay vì 10–20
phút. Trên 16 cuốn D-01, 8 lĩnh vực:
- **chữ đứng vững:** trùng docling trung vị R 0,99 / P 0,97;
- **tiêu đề thì không:** trung vị R 0,72, thấp nhất 0,17 (nông nghiệp), 0,20 (sinh học), 0,36 (pháp luật). Luật chỉnh trên 3 sách không bắt
  được các kiểu tiêu đề không đánh số của sách mới;
- hệ quả là chỉ trung vị 58% chunk rơi vào cùng mục lá với docling. Sai cấu trúc lan sang A2 (vai trò vùng), C8 và tên module.

Ý tưởng: thay luật tiêu đề bằng một **bộ phân loại học từ nhãn của docling** (nhãn bạc) trên chính 16 cuốn này. Mỗi dòng của bộ đọc nhẹ được
gán "tiêu đề hay không" theo cây docling; học trên đặc trưng bố cục rẻ. Hướng này cũng hợp seminar, vì cả Pha A không dùng LLM.

## Việc cần làm

### 1. Nghiên cứu ngắn, có nguồn

Đọc nguồn gốc (trang bài, mã nguồn) về nhận cấu trúc tài liệu PDF bằng đặc trưng bố cục, rồi ghi vào báo cáo cách mỗi hệ biểu diễn dòng, đặc
trưng, mô hình và cách đo. Gợi ý (phải tự kiểm lại, không tin tóm tắt):
- GROBID: CRF trên token có đặc trưng bố cục;
- CERMINE;
- các bài về gán nhãn dòng hay khối theo nhóm bố cục (VILA).

Kết luận cần chọn rõ: phân loại từng dòng (GBDT, hồi quy logistic) hay gán nhãn chuỗi (CRF), và vì sao.

### 2. Dữ liệu

- **Đơn vị:** dòng của bộ đọc nhẹ (`page_lines` → `describe` trong `doc_nhe.py`), kèm dòng trước và sau.
- **Nhãn:** khớp mỗi dòng với nút của cây docling cùng trang (`artifacts/parse_tree/d01-xx`, bản pypdfium2 mới nhất) theo chữ, cho phép
  tiêu đề docling nằm trọn trong dòng hoặc ngược lại.
  - Lớp tối thiểu: `tieu_de` (docling `section_header`/`title`) và `khac`.
  - Nếu làm được thì thêm: `dau_chan_trang` (dòng ở lề không khớp nút nào), `cong_thuc`, `danh_sach`.
  - Báo tỉ lệ dòng không khớp được, theo từng cuốn.
- Nhãn docling là **bạc**: docling cũng sai. Ví dụ doc-1 có "· Ví dụ 14." bị gán tiêu đề. Đọc tay khoảng 50 lỗi lớn nhất của mô hình để
  phân biệt mô hình sai với nhãn sai.
- **Không mở `document-data/test/`.** doc-1, doc-4, xstk chỉ dùng làm **kiểm ngoài**; không học trên chúng, vì luật v4 đã chỉnh trên chúng.

### 3. Đặc trưng

Không cần danh sách từ ngoài các mẫu đánh số đã có; đồ án chỉ làm tiếng Việt nên được dùng mẫu tiếng Việt.
- cỡ chữ so với thân bài của cuốn, đậm, nghiêng, tỉ lệ chữ hoa;
- độ dài (ký tự, từ), lề trái so với lề trang, căn giữa;
- khoảng trống trên và dưới so với chiều cao dòng;
- mẫu đánh số ("Chương", "Bài", "1.2", "I-", "A.", "a)"), kết thúc bằng dấu câu;
- tỉ lệ âm tiết tiếng Việt, tỉ lệ ký tự font toán, font đơn cách;
- vị trí trên trang, dòng có lặp qua các trang không;
- **ngữ cảnh**: các đặc trưng trên của dòng trước và dòng sau; dòng có khác font hay cỡ với hàng xóm không.

### 4. Mô hình và cách đo

- Chia **leave-one-book-out** trên 16 cuốn: cuốn đo không bao giờ nằm trong tập học. Báo theo từng cuốn và từng lĩnh vực, cả cuốn tệ nhất.
- Mức dòng: P/R/F1 tiêu đề so với docling; so với luật v4 hiện tại trên cùng dòng.
- **Đo đầu cuối bằng chính script đã có:** thay luật tiêu đề trong bộ đọc nhẹ bằng mô hình, chạy `doc_nhe_rong.py` và
  `so_chunk_doc_nhe.py` (cùng `chunk_document`, cùng tham số). Báo:
  - tiêu đề R/P;
  - tỉ lệ chunk cùng mục lá;
  - tỉ lệ chunk trùng từ từ 0,8;

  trên 16 cuốn và trên 3 tài liệu kiểm ngoài.
- Tốc độ: giây/trang **kể cả** suy luận mô hình; phải giữ dưới khoảng 0,1 giây/trang.

### 5. Triển khai thử

Mã ở `scripts/doc-nhe/` (hoặc mở rộng `scripts/thu-a1/`); chưa đưa vào `src/` và chưa đổi A1 của luồng.
- Mô hình huấn luyện lại được bằng một lệnh, seed cố định.
- Tệp mô hình nhỏ thì commit được; lớn thì để `tmp/` kèm lệnh dựng lại.
- Môi trường: dùng `tmp/venv-ml` (scikit-learn, lightgbm, underthesea). Không thêm gói vào `pyproject.toml` trong vé này.

## Nghiệm thu (chỉ tiêu để biết có đáng đưa vào luồng không, không phải cổng cứng)

- **Mục tiêu:**
  - tiêu đề F1 trung vị từ 0,9, cuốn tệ nhất từ 0,75;
  - chunk cùng mục lá trung vị từ 0,85;
  - chunk trùng từ từ 0,8 trung vị từ 0,7;
  - tốc độ dưới 0,1 giây/trang.

  Không đạt thì báo đủ số và phân tích lỗi; đó vẫn là kết quả nghiên cứu.
- **Báo cáo** `report/v4-14-bo-nhan-tieu-de-<ngày>.md`, gồm:
  - nguồn đã đọc;
  - bảng theo cuốn và lĩnh vực: luật v4 so với mô hình;
  - kiểm ngoài trên doc-1, doc-4, xstk;
  - lỗi tiêu biểu: mô hình sai hay nhãn docling sai;
  - độ quan trọng đặc trưng;
  - đề xuất có đưa vào A1 không, và cần gì thêm.
- Lệnh chạy lại được từ đầu; không đọc `document-data/test/`.
- **Báo cáo cho Claude kiểm thử** trước khi đề xuất đổi luồng.
