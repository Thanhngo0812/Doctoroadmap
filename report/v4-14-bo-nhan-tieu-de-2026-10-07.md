# v4-14 — Bộ nhận tiêu đề học máy cho A1 nhẹ

Ngày 2026-10-07. **Đã hoàn tất triển khai thử và đánh giá P0–P7; bàn giao sếp kiểm, chưa đưa vào production.**

**Kết luận:** M2 cải thiện so với luật cũ, nhưng chưa đủ điều kiện thay A1. Trên 16 sách, F1 dòng trung vị **0,755→0,883**, chunk cùng mục lá **0,581→0,742**, chunk trùng từ ≥0,8 **0,430→0,637**. Cả ba còn dưới mục tiêu. Tốc độ đạt: median **0,02494 giây/trang**, lớn nhất trong 19 cuốn **0,04673 giây/trang**. Đây là kết quả nghiên cứu hợp lệ theo vé, không phải chứng nhận chất lượng A1/roadmap đã đạt chuẩn.

[Snapshot số đo và nhận xét](v4-14-so-do-2026-10-07.json) giữ đầy đủ TP/FP/FN, mẫu số, P/R, hai chiều Jaccard, timings, hashes, coverage, mẫu và review; không phụ thuộc việc thư mục `tmp/` còn được giữ hay không.

## 1. Thiết kế đã triển khai

Mã nghiên cứu ở `scripts/doc-nhe/`; hook lựa chọn heading ở `scripts/thu-a1/doc_nhe.py`. Không thay `src/`, `.env`, dependency production hoặc mặc định A1. Chi phí LLM/embedding: **0 USD**. Không chạy A2–A10; không mở PDF trong `document-data/test/`.

Các nguồn và lý do chọn mô hình nằm trong [nghiên cứu đã duyệt](v4-14-nghien-cuu-va-ke-hoach-A1-2026-10-07.md). Tóm tắt áp dụng:

- [GROBID](https://grobid.readthedocs.io/en/latest/Principles/): tín hiệu bố cục tương đối, đặc trưng dòng/ngữ cảnh và đánh giá tách tài liệu; không sao chép toàn bộ pipeline.
- [CERMINE, 2015](https://doi.org/10.1007/s10032-015-0249-8): học phân loại bố cục và căn nhãn tự động; cần báo sai số/coverage của nhãn.
- [VILA, 2022](https://aclanthology.org/2022.tacl-1.22/): nhóm dòng/khối mang thông tin, nhưng lỗi phân nhóm có thể giới hạn mô hình. Không dùng Transformer; đo cả trích PDF thay vì chỉ inference.
- [LightGBM, 2017](https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html): GBDT phù hợp đặc trưng số và CPU. Lượt này dùng GBDT thường, không tuyên bố bật GOSS.

`paper-lookup` hỗ trợ chọn/kiểm nguồn, không thay phép đo trên sách Việt. `ponytail` dẫn đến tái sử dụng parser, chunker, tokenizer và các thư viện có sẵn; không thêm CRF/Transformer khi chưa chứng minh cần chúng. Skill PDF được dùng để kiểm trực tiếp bố cục các mẫu nghi vấn. `scientific-critical-thinking` hỗ trợ phân biệt kết quả trên nhãn bạc với chất lượng A1 thực; không áp điểm chứng nhận y khoa cho benchmark này. Nguồn phần mềm: Kassis, Agarwal, He, Patel, Brueckner (2026), [Scientific Agent Skills](https://arxiv.org/abs/2609.00065), hồ sơ v2 đã kiểm khi nghiên cứu.

### Mô hình cố định trước khi xem điểm kiểm

| Mã | Cấu hình |
|---|---|
| M0 | Luật v4 trước vé; hash đầu ra mặc định giữ nguyên trên ba fixture PDF. |
| M1 | Logistic C=1, balanced, max_iter=1000, scaler chỉ fit train. |
| M2 | LightGBM 300 cây, tối đa 15 lá/cây, learning rate 0,05, min child=30, balanced, CPU 2 luồng, deterministic. |
| M3 | Như M2 nhưng bỏ bản sao hàng xóm và cờ ngữ cảnh, còn 23 feature dòng hiện tại. |
| Oracle bạc | Nhãn bạc ở dòng đã căn; unknown giữ M0. Chỉ chẩn đoán grouping/cấp mục, không phải model triển khai hoặc upper bound tuyệt đối. |

Seed 42; threshold 0,5 cho cả ba model. Với balanced weights, score không phải xác suất đã hiệu chỉnh. Không tuning theo kết quả LOBO hay ba tài liệu ngoài.

M1/M2 dùng **73 feature**: 23 của dòng hiện tại, 46 bản sao của dòng trước/sau cùng trang, 4 cờ có hàng xóm/khác font. Không có ID sách, nhà xuất bản, nhãn Docling hoặc tên font mã hóa theo sách. `viet_accent` là tỷ lệ token có dấu, không phải bộ nhận âm tiết hợp lệ.

**61 fit:** 16 LOBO × 3 = 48; 10 lượt giữ riêng nhóm nguồn cho M2; 3 model full16 chỉ dùng ba tài liệu phát triển cũ. Từng JSON model ghi train/heldout, hash, score và thời gian. Dòng unknown không tham gia fit hoặc F1 mức dòng.

## 2. Dữ liệu, nhãn và giới hạn mẫu số

Manifest ghim 16 train (2.990 trang) và 3 external bằng SHA-256 PDF/cây/chunk-config. Không đọc cây `latest` giữa lượt chạy. Version 16 train lần lượt: **2,2,1,2,2,2,2,1,1,1,1,1,1,2,2,1**. Ngoài: doc-1 v5, doc-4 v3, xstk-ch3-1 v3.

Doc-1/xstk có metadata adapter `docling:2.114.0`, không có hậu tố pypdfium2; không tự chạy lại để đồng nhất mốc. Bảy cây D01 có sửa glyph đã duyệt, trong khi PDF trực tiếp không dùng bảng sửa riêng từng sách. Đó là khác biệt đầu vào phải tính đến khi đọc coverage.

Chunk reference được **dựng lại từ cây ghim bằng cùng chunker/config** cho cả hai phía, không lấy nguyên chunk production. Riêng doc-4/xstk, metadata chunk-config đang tham chiếu parse v2 nhưng cây đánh giá là v3: bảng này đo tác động parser trên v3 với cùng cấu hình, không chứng minh tương đương output production v2.

Ba external đã dùng để phát triển luật v4 trước đây, nên đây là **kiểm chuyển giao trên bộ phát triển cũ**, không phải kiểm mù mới.

| Tài liệu | Dòng thô | Giữ lại | Nhãn 1 | Nhãn 0 | Unknown | Tiêu đề bạc phủ trước/sau lọc / tổng |
|---|---:|---:|---:|---:|---:|---:|
| d01-01 | 19711 | 19709 | 239 | 7590 | 11880 | 225/225/225 |
| d01-02 | 11808 | 11412 | 264 | 3718 | 7430 | 257/257/265 |
| d01-03 | 3793 | 3417 | 236 | 2173 | 1008 | 240/231/258 |
| d01-04 | 5654 | 5477 | 186 | 3155 | 2136 | 186/186/188 |
| d01-05 | 4585 | 4422 | 291 | 3519 | 612 | 301/286/312 |
| d01-06 | 5502 | 5364 | 277 | 3524 | 1563 | 264/264/277 |
| d01-07 | 3604 | 3604 | 216 | 2689 | 699 | 215/215/222 |
| d01-08 | 9095 | 8629 | 323 | 7087 | 1219 | 322/322/323 |
| d01-09 | 11671 | 11294 | 210 | 6979 | 4105 | 194/194/209 |
| d01-10 | 7318 | 6803 | 421 | 4638 | 1744 | 410/410/421 |
| d01-11 | 4203 | 4061 | 294 | 2648 | 1119 | 241/241/243 |
| d01-12 | 3321 | 3220 | 202 | 2607 | 411 | 198/192/214 |
| d01-13 | 3611 | 3446 | 304 | 2119 | 1023 | 300/300/305 |
| d01-14 | 5327 | 5068 | 406 | 3470 | 1192 | 399/399/485 |
| d01-15 | 7660 | 7426 | 562 | 5822 | 1042 | 565/562/636 |
| d01-16 | 1378 | 1377 | 119 | 1030 | 228 | 113/113/115 |
| doc-1 | 8307 | 8037 | 111 | 3854 | 4072 | 108/108/109 |
| doc-4 | 8072 | 7859 | 338 | 5930 | 1591 | 304/304/304 |
| xstk-ch3-1 | 3700 | 3583 | 71 | 1807 | 1705 | 65/65/67 |

16 train có **108.241 dòng thô**, giữ **104.729**; trong đó **4.550 positive, 62.768 negative, 37.411 unknown (35,72%)**. Lọc lề bỏ 3.512 dòng và làm mất coverage của 33 nút heading bạc (4.430 xuống 4.397 trên tổng 4.698).

F1 mức dòng chỉ chấm nhãn 0/1 trong số dòng giữ lại. Đặc biệt d01-01/02 có nhiều unknown do toán/glyph/đơn vị dòng; không được đọc F1 đó thành chất lượng tất cả dòng. Coverage tiêu đề d01-14 chỉ 399/485 ≈82,3%. Dòng thô và nút Docling là đơn vị khác nhau: một tiêu đề có thể trải nhiều dòng.

Đã rà **80 căn nhãn** (5/cuốn) trước train; đọc tất cả cặp dòng/nút nguồn, kiểm ảnh PDF cho mẫu 4/46/51. Không xác nhận lỗi cơ chế căn nhãn trong mẫu, nhưng mẫu 27/46 có nhãn ngữ nghĩa đáng ngờ. Đây là agent review, không phải 80 nhãn vàng do người chứng nhận. Không suy ra cả bộ căn nhãn hoàn toàn đúng.

## 3. Bảng điểm đầu-cuối

### 3.1 Tổng hợp 16 LOBO

Các số là trung vị theo cuốn, trừ cột min. Không gộp ba external vào bảng này.

| Phương án | F1 dòng median / min | F1 heading strict | Cùng mục lá legacy | Cùng mục lá strict | Chunk Jaccard ≥0,8 | Giây/trang median |
|---|---:|---:|---:|---:|---:|---:|
| M0 luật | 0,7553 / 0,0976 | 0,6830 | 0,5810 | 0,4659 | 0,4300 | 0,02180 |
| M1 logistic | 0,7741 / 0,2088 | 0,5963 | 0,6405 | 0,5248 | 0,5785 | 0,02681 |
| M2 LightGBM | **0,8834 / 0,2745** | **0,7379** | **0,7420** | 0,6159 | **0,6370** | 0,02494 |
| M3 bỏ context | 0,8428 / 0,2140 | 0,7218 | 0,7185 | **0,6284** | 0,5820 | 0,02524 |
| Oracle bạc | 1,0000 / 1,0000 | 0,8957 | 0,9040 | 0,8039 | 0,7260 | Không đo triển khai |

M2 hơn M3 về F1 dòng/heading/chunk tương đồng, nhưng **không thắng mọi metric**: strict leaf median của M3 nhỉnh hơn. Ngữ cảnh có ích trên nhiều sách, không phải bảo đảm cải thiện mọi khía cạnh cấu trúc.

| Mục tiêu vé | M2 đo được | Kết luận |
|---|---:|---|
| F1 dòng median ≥0,90 | 0,8834 | Chưa đạt |
| F1 cuốn tệ nhất ≥0,75 | 0,2745, d01-07 | Chưa đạt; nhãn bạc có lỗi, không miễn trừ cuốn này |
| Cùng mục lá legacy median ≥0,85 | 0,7420 | Chưa đạt |
| Chunk Jaccard ≥0,8 median ≥0,70 | 0,6370 | Chưa đạt |
| Parse + inference <0,1 giây/trang | Max median/cuốn 0,04673 trên cả 19 | Đạt trên máy đã đo |

### 3.2 Mức dòng theo cuốn

P/R/F1 của M2 đều tính trên dòng có nhãn bạc 0/1; không phải độ đúng toàn trang.

| Cuốn | M0 F1 | M1 F1 | M2 P/R/F1 | M3 F1 |
|---|---:|---:|---:|---:|
| d01-01 | 0,866 | 0,837 | 0,837/0,946/0,888 | 0,847 |
| d01-02 | 0,669 | 0,662 | 0,822/0,788/0,805 | 0,744 |
| d01-03 | 0,877 | 0,729 | 0,758/0,996/0,861 | 0,855 |
| d01-04 | 0,790 | 0,817 | 0,852/0,957/0,901 | 0,888 |
| d01-05 | 0,802 | 0,903 | 0,895/0,969/0,931 | 0,884 |
| d01-06 | 0,357 | 0,883 | 0,904/0,917/0,910 | 0,839 |
| d01-07 | 0,512 | 0,209 | 0,159/1,000/0,274 | 0,214 |
| d01-08 | 0,935 | 0,837 | 0,801/1,000/0,890 | 0,862 |
| d01-09 | 0,733 | 0,875 | 0,896/0,943/0,919 | 0,902 |
| d01-10 | 0,870 | 0,702 | 0,796/0,981/0,879 | 0,676 |
| d01-11 | 0,351 | 0,687 | 0,732/0,854/0,788 | 0,652 |
| d01-12 | 0,831 | 0,864 | 0,824/0,975/0,893 | 0,854 |
| d01-13 | 0,676 | 0,723 | 0,628/0,954/0,757 | 0,708 |
| d01-14 | 0,703 | 0,692 | 0,744/0,943/0,832 | 0,708 |
| d01-15 | 0,098 | 0,732 | 0,703/0,911/0,794 | 0,684 |
| d01-16 | 0,778 | 0,935 | 0,899/0,975/0,935 | 0,936 |

### 3.3 Cây và chunk theo cuốn

Trong cột R/P legacy, thứ tự là **recall rồi precision**, giữ đúng phép đo lịch sử. Strict heading ghép một-một, cùng trang, nguyên token và tỷ lệ containment ≥0,8. Strict leaf yêu cầu Jaccard ≥0,5, giữ thứ tự từ tên mục và mẫu số toàn bộ chunk gốc. Jaccard ≥0,8 dưới đây là chiều **Docling tìm bạn trong cây nhẹ**; chiều ngược và ngưỡng 0,5 đều có trong snapshot.

| Cuốn | Heading legacy R/P M0 → M2 | Heading strict F1 M0/M2 | Leaf legacy M0/M2/oracle | Leaf strict M0/M2 | Jaccard ≥0,8 M0/M2 |
|---|---|---:|---:|---:|---:|
| d01-01 | 0,893/0,955 → 0,964/0,920 | 0,820/0,795 | 0,772/0,766/0,938 | 0,632/0,651 | 0,409/0,417 |
| d01-02 | 0,751/0,733 → 0,928/0,968 | 0,580/0,695 | 0,552/0,674/0,814 | 0,430/0,498 | 0,290/0,281 |
| d01-03 | 0,922/0,907 → 0,957/0,826 | 0,734/0,744 | 0,669/0,691/0,816 | 0,570/0,588 | 0,496/0,511 |
| d01-04 | 0,670/0,969 → 0,973/0,856 | 0,719/0,836 | 0,480/0,767/0,903 | 0,423/0,683 | 0,427/0,540 |
| d01-05 | 0,654/1,000 → 0,939/0,919 | 0,749/0,834 | 0,616/0,814/0,873 | 0,556/0,720 | 0,653/0,799 |
| d01-06 | 0,199/0,821 → 0,931/0,827 | 0,297/0,783 | 0,113/0,777/0,905 | 0,072/0,682 | 0,275/0,697 |
| d01-07 | 0,788/0,562 → 0,995/0,383 | 0,444/0,210 | 0,405/0,263/0,766 | 0,280/0,138 | 0,286/0,247 |
| d01-08 | 0,941/0,970 → 1,000/0,788 | 0,929/0,731 | 0,834/0,698/0,967 | 0,760/0,624 | 0,726/0,646 |
| d01-09 | 0,617/0,985 → 0,933/0,815 | 0,641/0,729 | 0,610/0,740/0,934 | 0,483/0,601 | 0,598/0,629 |
| d01-10 | 0,812/0,980 → 0,983/0,862 | 0,824/0,784 | 0,769/0,780/0,956 | 0,680/0,712 | 0,591/0,661 |
| d01-11 | 0,362/1,000 → 0,909/0,954 | 0,348/0,656 | 0,148/0,608/0,954 | 0,123/0,512 | 0,312/0,645 |
| d01-12 | 0,776/1,000 → 0,949/0,894 | 0,716/0,741 | 0,763/0,887/0,981 | 0,624/0,763 | 0,774/0,808 |
| d01-13 | 0,603/0,989 → 0,993/0,962 | 0,650/0,735 | 0,511/0,744/0,889 | 0,449/0,544 | 0,407/0,584 |
| d01-14 | 0,715/0,830 → 0,928/0,780 | 0,512/0,558 | 0,441/0,624/0,755 | 0,363/0,502 | 0,433/0,567 |
| d01-15 | 0,171/0,591 → 0,950/0,824 | 0,083/0,642 | 0,040/0,705/0,881 | 0,023/0,608 | 0,243/0,724 |
| d01-16 | 0,687/0,963 → 0,974/0,901 | 0,769/0,864 | 0,655/0,908/0,975 | 0,555/0,832 | 0,605/0,782 |

Oracle đạt leaf legacy median 0,904 nhưng strict chỉ 0,804 và strict heading 0,896 dù F1 dòng là 1 theo định nghĩa. Vẫn còn sai biệt do unknown, lọc lề, tách/gộp tiêu đề và cấp mục. Điều này **không chứng minh cần CRF ngay**, nhưng bác giả định “học đúng heading là đủ thay toàn bộ A1”.

### 3.4 Theo lĩnh vực

Macro mean của hai cuốn mỗi lĩnh vực; đây là mô tả hai sách, không phải ước lượng tin cậy cho cả lĩnh vực.

| Lĩnh vực | M0 F1 | M1 F1 | M2 F1 | M3 F1 | Leaf legacy M0/M2 |
|---|---:|---:|---:|---:|---:|
| Toán học | 0,7673 | 0,7495 | 0,8463 | 0,7951 | 0,6620/0,7200 |
| Hóa học | 0,8334 | 0,7726 | 0,8810 | 0,8714 | 0,5745/0,7290 |
| Sinh học | 0,5799 | 0,8929 | 0,9205 | 0,8616 | 0,3645/0,7955 |
| Công nghệ thông tin | 0,7239 | 0,5231 | 0,5821 | 0,5379 | 0,6195/0,4805 |
| Kinh tế | 0,8015 | 0,7887 | 0,8988 | 0,7895 | 0,6895/0,7600 |
| Pháp luật | 0,5907 | 0,7756 | 0,8407 | 0,7531 | 0,4555/0,7475 |
| Kỹ thuật | 0,6899 | 0,7076 | 0,7944 | 0,7080 | 0,4760/0,6840 |
| Nông nghiệp | 0,4377 | 0,8334 | 0,8646 | 0,8098 | 0,3475/0,8065 |

### 3.5 Ba tài liệu kiểm ngoài

| Tài liệu | M0 F1 dòng | M1 F1 | M2 P/R/F1 | M3 F1 | Leaf legacy M0/M2/oracle | Leaf strict M0/M2 | Jaccard ≥0,8 M0/M2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| doc-1 | 0,879 | 0,562 | 0,614/0,973/0,753 | 0,630 | 0,864/0,739/0,960 | 0,804/0,618 | 0,558/0,538 |
| doc-4 | 0,879 | 0,915 | 0,951/0,973/0,962 | 0,953 | 0,867/0,915/0,955 | 0,629/0,779 | 0,732/0,753 |
| xstk-ch3-1 | 0,896 | 0,747 | 0,875/0,887/0,881 | 0,913 | 0,754/0,730/0,944 | 0,587/0,571 | 0,484/0,484 |

Heading legacy R/P M0→M2: doc-1 **0,963/0,860→0,991/0,774**; doc-4 **0,921/0,981→1,000/0,959**; xstk **0,881/0,982→0,910/0,969**. Strict heading F1 tương ứng: **0,824→0,709; 0,747→0,814; 0,770→0,763**.

M2 tốt hơn trên doc-4 nhưng lùi trên doc-1 và xstk ở leaf. Không chọn lại model theo từng cuốn sau khi nhìn bảng này; chưa có router được kiểm ngoài để quyết định tự động khi nào dùng M0/M2/M3.

## 4. Kiểm giữ riêng nhóm nguồn

Chỉ M2. Macro trung bình F1 theo **10 nhóm nguồn = 0,8133**. Chín nhóm chỉ có một sách nên bằng LOBO tương ứng; phép kiểm khác thật sự nằm ở nhóm Cao đẳng Đà Lạt gồm bảy sách.

| Sách | LOBO M2 | Giữ riêng cả nhóm Cao đẳng Đà Lạt |
|---|---:|---:|
| d01-05 | 0,9307 | 0,8674 |
| d01-06 | 0,9104 | 0,8817 |
| d01-11 | 0,7881 | 0,8330 |
| d01-13 | 0,7572 | 0,8789 |
| d01-14 | 0,8317 | 0,8267 |
| d01-15 | 0,7938 | 0,5603 |
| d01-16 | 0,9355 | 0,9138 |

D01-15 giảm rõ; không thể chỉ dùng LOBO để khẳng định tổng quát hóa sang mẫu sách/nhà xuất bản mới. Grouping theo publisher cũng chưa đồng nghĩa đúng bằng grouping theo template bố cục thực tế.

## 5. Rà 50 bất đồng và importance

Lấy 25 FP + 25 FN so nhãn bạc, seed 42, luân phiên sách, không quá 5/cuốn; ưu tiên score bất đồng lớn, xen mẫu đánh số/không đánh số nếu có. **Không phải mẫu ngẫu nhiên để ước lượng tỷ lệ lỗi toàn bộ.**

Kết luận agent: **23 lỗi model; 2 lỗi nhãn bạc xác minh bằng ảnh; 11 nghi lỗi nhãn bạc chưa xác minh ảnh; 13 chưa phân xử; 1 chữ/sơ đồ bị trích hỏng.** Không sửa nhãn kiểm, không sửa threshold, không học lại từ kết luận này.

| Ví dụ | Bằng chứng và kết luận |
|---|---|
| d01-07, PDF trang 34: `2. Khai báo và sử dụng` | In đậm, dòng độc lập, mở mục dưới “Hàm người dùng”; Docling gán 0. Model dự đoán heading hợp lý. |
| d01-07, PDF trang 14: `3. Lệnh xoá dữ liệu` | In đậm, theo sau là câu lệnh SQL; Docling gán 0. Hai ca này giải thích một phần điểm thấp, không đủ để tuyên bố toàn bộ FP đều đúng. |
| d01-06, `Hình 2-4: Phương pháp dùng đầu lệch` | Chú thích hình bị model nâng thành heading: lỗi model thực. |
| d01-15, `Tổng cộng 10 điểm` | Ô tổng của bảng đánh giá bị coi thành mục. Thiếu hiểu cấu trúc bảng. |
| d01-01, tên hai tác giả trên bìa | Metadata có bố cục nổi bật dễ bị coi là heading. |
| d01-11, Điều 25 và Điều 45 | Tiêu đề dài bị bỏ sót; context hiện tại chưa giải quyết tốt độ dài/multiline. |
| d01-09, tiêu đề lý thuyết trò chơi | Nhiều dòng; một dòng bị demote làm hỏng tên/cấu trúc mục. |
| d01-10, tên tác giả gán heading; dòng `mạnhà…cung tiền` | Một ca nghi lỗi nhãn ngữ nghĩa, một ca chữ/mũi tên sơ đồ trích hỏng. |
| `Chú ý`, `Ví dụ`, `Bài 7`, các khoản luật | Cần thống nhất ontology heading/nhãn đoạn trước khi tạo nhãn vàng; chưa tự quyết toàn bộ là lỗi model. |

Ảnh kiểm ở `tmp/pdfs/v414/error-04.png`, `error-20.png`; mẫu và 50 nhận xét ở `tmp/doc-nhe-v414/errors-50*.json`. Hai trang d01-07 còn logo nguồn đầu trang: nghiên cứu này không sửa PDF hay bộ làm sạch sách.

Gain M2: lấy tỷ phần gain mỗi model LOBO rồi trung bình 16 model, không lấy full16 để tuyên bố tổng quát hóa.

| Feature | Tỷ phần gain trung bình |
|---|---:|
| bold | 42,18% |
| uppercase | 13,12% |
| numbered | 5,83% |
| center | 5,49% |
| chars | 2,73% |
| italic | 2,26% |
| tokens | 2,01% |
| next_font_diff | 1,73% |
| left | 1,72% |
| next_width | 1,31% |

Tổng feature ngữ cảnh chiếm **15,71% gain**. M1 có hệ số chuẩn hóa tuyệt đối trung bình lớn nhất ở width (2,881), left (2,185), chars (1,941), next_width (1,938), math (1,743), bold (1,512). Các feature tương quan mạnh; gain/hệ số không phải quan hệ nhân quả. Ablation M3 mới là đối chứng bổ sung cho lợi ích ngữ cảnh.

## 6. Vận hành, toàn vẹn và giới hạn

Dựng dataset + căn nhãn cả 19 cuốn: tổng thời gian ghi theo cuốn **96,89 giây**. Tổng thời gian **fit** của 61 model **88,12 giây**, không gồm trích feature, lưu JSON và scoring. Tổng 61 joblib **23.818.749 byte**; full M1 **3.405 byte**, M2 **541.700 byte**, M3 **538.020 byte**. Để model dưới `tmp/`, có lệnh dựng lại; không thêm model nhị phân vào mã production.

Các timing parse đọc PDF mới, tính feature/inference/gom nút; không dùng cache dòng. Nạp model và chunk/scoring nằm ngoài khoảng parse. Median ba lần giúp giảm nhiễu nhưng không phải benchmark cold-start; Windows có thể cache file. Không chạy huấn luyện/full test đồng thời với benchmark. RAM báo peak toàn bộ worker từng cuốn, gồm dataset, tokenizer, scoring và các model, không gọi đó là riêng RAM model.

Máy Windows x64, 16 logical processor, CPU identifier `AMD64 Family 25 Model 80 Stepping 0, AuthenticAMD`. LightGBM dùng 2 luồng. Sai khác nhỏ so kế hoạch: không chạy warm-up PDF fixture riêng; các thư viện/model/chunker đã nạp và chấm trước mỗi nhóm ba lần đọc PDF. Ba lần chạy là lặp kỹ thuật trên một máy, không phải ba mẫu độc lập. Có tác vụ biên tập/đọc metadata nhẹ cùng lúc; không suy rộng số giây này thành SLA máy khác. M3 vẫn dựng ma trận feature chung rồi lấy 23 cột, nên đây là ablation chất lượng chứ chưa tối ưu thời gian tạo feature cho M3.

Chưa nhận bảng, chưa sửa cấp mục và chưa sửa việc nối hình cuối cây. Không coi “đủ số hình” là “hình ở đúng mục”. Công thức/chú thích có thể bị nâng thành heading; cần xem thống kê toàn vẹn và phạm vi downstream trước mọi đề xuất thay Docling.

### Số đo mỗi cuốn — M2, trích PDF + feature + suy luận + gom nút

Min/median/max là ba lần đo mới, đơn vị giây. Cột phút chỉ là median/60, không bao gồm chấm điểm và chunk. RSS là MiB peak toàn worker (không riêng M2).

| Cuốn | Trang | Giây min/median/max | Phút/cuốn | Giây/trang | RSS MiB |
|---|---:|---:|---:|---:|---:|
| d01-01 | 237 | 4,614/5,126/5,621 | 0,0854 | 0,02163 | 377,0 |
| d01-02 | 199 | 2,832/2,886/2,886 | 0,0481 | 0,01450 | 352,4 |
| d01-03 | 125 | 2,409/2,717/2,808 | 0,0453 | 0,02173 | 358,6 |
| d01-04 | 178 | 4,972/5,050/5,654 | 0,0842 | 0,02837 | 362,0 |
| d01-05 | 150 | 3,954/4,037/4,967 | 0,0673 | 0,02692 | 293,5 |
| d01-06 | 171 | 6,216/6,236/6,398 | 0,1039 | 0,03647 | 422,6 |
| d01-07 | 115 | 2,412/2,454/2,728 | 0,0409 | 0,02134 | 298,1 |
| d01-08 | 237 | 9,515/9,640/10,281 | 0,1607 | 0,04068 | 374,9 |
| d01-09 | 379 | 11,740/11,849/13,313 | 0,1975 | 0,03126 | 377,4 |
| d01-10 | 260 | 5,412/6,034/11,536 | 0,1006 | 0,02321 | 448,7 |
| d01-11 | 134 | 3,568/3,575/3,648 | 0,0596 | 0,02668 | 322,4 |
| d01-12 | 101 | 3,070/3,098/3,591 | 0,0516 | 0,03067 | 285,4 |
| d01-13 | 165 | 2,528/2,600/2,728 | 0,0433 | 0,01576 | 468,8 |
| d01-14 | 262 | 4,091/4,193/4,267 | 0,0699 | 0,01601 | 377,1 |
| d01-15 | 225 | 6,587/6,637/6,665 | 0,1106 | 0,02950 | 350,0 |
| d01-16 | 52 | 1,104/1,131/1,151 | 0,0189 | 0,02175 | 298,9 |
| doc-1 | 102 | 1,989/2,041/2,110 | 0,0340 | 0,02001 | 316,6 |
| doc-4 | 214 | 9,937/10,001/10,266 | 0,1667 | 0,04673 | 351,0 |
| xstk-ch3-1 | 59 | 2,290/2,308/2,395 | 0,0385 | 0,03912 | 337,6 |

### Bảo toàn nội dung

- **M1 và M2: 19/19** giữ nguyên chuỗi chữ/ký hiệu không tính khoảng trắng theo từng trang so M0; chuỗi token và danh sách nút hình cũng bằng nhau. Đây là bảo toàn so bộ đọc nhẹ gốc, **không có nghĩa toàn bộ PDF đã được đọc đúng**.
- M3 giữ chữ/ký hiệu 17/19: d01-02 trang 76 thêm hai token `x`, d01-06 trang 26 thêm một `G` so M0. Đối chiếu chuỗi cho thấy thay ranh giới gom khối làm bước gộp glyph lặp chạy khác (`…arctgxxxx…`, `…GAATTCGG…`). Không sửa sau khi xem kết quả; đây là lỗi tương tác grouping/cleanup cần xử lý ở vòng sau, không coi M3 bảo toàn tuyệt đối.
- Trên 16 sách, word coverage so Docling median R/P của M0 và M2 đều **0,9845/0,9720**; điểm thứ tự theo trang đều **0,930**. Đây vẫn là độ giống tham chiếu bạc.
- Tổng nút 16 sách M0→M2: **formula 10.184→10.168; caption 854→615; heading 3.350→6.217; figure 852→852; table 0→0**. Đổi kiểu/ranh giới nút không đồng nghĩa mất chữ, nhưng có thể sai cấu trúc ngữ nghĩa.
- Số token nằm trong loại formula giảm ở 10/19 cuốn: ví dụ d01-07 **686→584**, d01-04 **1.419→1.366**. Phủ từ công thức so Docling median **0,485→0,484**. Không dùng kết quả nhận heading để tuyên bố công thức/bảng đạt chuẩn.

## 7. Lệnh và kiểm thử

[README tái lập](../scripts/doc-nhe/README.md). Một lệnh `tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/chay.py`; với thư mục mới, dừng ở bước kiểm 80 căn nhãn, chạy lại sau khi đã có nhận xét thật. Không tự động giả lập sự duyệt của người kiểm.

Các guard metric đã **đỏ trên cách chấm cũ**, sau đó mới sửa:

- wrong-page heading, token-boundary (`1`/`11`), duplicate heading một-một;
- chunk không chung từ nhưng trùng tên mục không được tính strict leaf đúng;
- hook promote/demote và metadata layout đỏ trước hook mới, baseline ba fixture giữ hash cũ;
- bỏ kiểm bbox hoặc cho heldout/unknown vào mảng học làm test tương ứng đỏ.

**Kiểm cuối:** bộ dự án (không integration) chọn 917/922 test: **915 đạt, 2 skip do không có thư viện ML trong `.venv`, 5 integration deselected**, exit 0. Cả **18/18 test vé 14** chạy trong `tmp/venv-ml` đều đạt (bao gồm hai test bị skip ở môi trường production). Chỉ có cảnh báo deprecation SWIG; không coi cảnh báo này là lỗi ứng dụng. Không cộng 915+18 thành số test độc lập vì hai tập chồng nhau.

Đã fit lại full M2 từ cùng mảng train thật/seed; so toàn bộ score trên doc-1/doc-4/xstk với record cũ, **max absolute difference = 0 ở cả ba**. Đây là một fit kiểm tái lập thêm ngoài 61 model lưu; lượt fit + so này ghi 5,22 giây, không cộng vào tổng 88,12 giây của 61 fit chính.

| Bất biến | Assertion chạy được |
|---|---|
| Sai trang, partial number, duplicate không được tính đúng | `test_heading_match_rejects_wrong_page`, `test_heading_match_uses_token_boundaries`, `test_heading_match_is_one_to_one` |
| Leaf cần overlap thật | `test_leaf_match_requires_content_overlap` |
| Unknown/conflicting không thành âm, bbox đúng vị trí | `test_unmatched_and_conflicting_rows_remain_unknown`, `test_alignment_uses_same_page_geometry` |
| Không lấy heldout/unknown vào mảng trước fit; feature không đọc label/qua trang | `test_lobo_excludes_heldout_and_unknown_labels`, `test_features_ignore_labels_and_cross_page_neighbors` |
| Không mở đường PDF ngoài allowlist | `test_manifest_rejects_non_allowlisted_paths` |
| Baseline giữ nguyên; model thay đúng số dòng và nội dung | `test_baseline_serialized_tree_unchanged` (3 fixture), `test_predictor_can_promote_and_demote_heading`, `test_describe_exposes_layout_without_changing_text` |
| Model save/load, fingerprint dữ liệu và nguồn ghim | `test_model_roundtrip_and_dataset_fingerprint`, `test_manifest_rejects_changed_pinned_input` |
| Review phải đủ 80 mẫu và đúng hash | `test_review_gate_requires_complete_matching_sample` |
| Seed ổn định | `test_lightgbm_fixed_seed_is_repeatable` và phép fit lại full M2 nêu trên |

Trong mỗi lượt benchmark, assertion so **toàn bộ nút parse mới** với nút dựng từ dự đoán OOF đã lưu đều qua; evaluator bác metadata nếu cuốn kiểm nằm trong train hoặc model hash sai. Snapshot chứa số liệu đầy đủ để kiểm lại các bảng. `git diff --check` đạt; mã mới không có trailing whitespace. Không commit gộp với các thay đổi vé 12/13 đang có của workspace.

Kiểm bàn giao cuối: chạy lại lệnh tổng `chay.py --out tmp/doc-nhe-v414`, exit 0; tái dùng đúng 19 dataset, 61 model và 19 kết quả đánh giá, không fit/parse lại. SHA-256 tất cả nguồn trong snapshot khớp tệp hiện tại; đủ 80 mẫu căn nhãn, 50 bất đồng và review đúng hash. Không còn tiến trình thí nghiệm của lượt này đang chạy.

Lệnh hồi quy thực tế:

```powershell
.venv/Scripts/python.exe -c "import sys;sys.path.insert(0,'src');import pytest;raise SystemExit(pytest.main(['tests','-m','not integration','-q','-p','no:cacheprovider','--basetemp','tmp/pytest-v414-regression']))"
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/bao_cao.py audit
tmp/venv-ml/Scripts/python.exe scripts/doc-nhe/bao_cao.py summary --snapshot report/v4-14-so-do-2026-10-07.json
```

## 8. Độ tin cậy của kết luận và bước nghiên cứu tiếp

Đơn vị tổng quát hóa là **cuốn sách/nhóm nguồn**, không phải hơn 100.000 dòng độc lập. Các fold LOBO còn chia sẻ phần lớn sách train. Chỉ báo mô tả median/min và chênh lệch; không gắn p-value hay khẳng định ý nghĩa thống kê từ số dòng rất lớn.

Điểm mạnh: cấu hình chốt trước khi xem outer score; loại heldout khỏi fit/scaler; cùng bộ trích dòng/chunker/tokenizer; thêm đối chứng bỏ context và oracle bạc; báo cả cuốn xấu, coverage và các metric chặt hơn.

| Vấn đề | Bằng chứng | Hệ quả và cách xử lý vòng sau |
|---|---|---|
| Nhãn bạc sai/khác ontology | Hai tiêu đề thật d01-07 gán 0; các ca tác giả, ví dụ, khoản luật | Không đồng nhất “giống Docling” với “đúng cho học”. Cần quy tắc nhãn và mẫu người kiểm độc lập trước tuning tiếp. |
| Selection qua coverage | D01-01/02 nhiều unknown, d01-14 phủ 82,3% nút heading | F1 dòng là F1 có điều kiện; ưu tiên kiểm phần unknown và lỗi glyph, không biến unknown thành negative. |
| Trùng khuôn nguồn | D01-15 giảm 0,794→0,560 khi giữ riêng nhóm nguồn | Bổ sung nhóm nguồn đa dạng hoặc chia theo template thực; không tối ưu chỉ LOBO. |
| Phụ thuộc mức cây | Nhận heading chỉ là nhãn nhị phân; cấp mục vẫn theo luật | Kiểm heading nhiều dòng, ranh giới khối, cấp mục; mô hình phân loại tốt chưa đủ cho chunk/roadmap. |
| Rà lỗi chưa mù | Agent thấy cả label và score khi đọc 50 bất đồng | Kết luận lỗi là chẩn đoán, chưa phải nhãn vàng; sếp/người thứ hai cần kiểm độc lập. |
| Mẫu cũ và quy mô nguồn nhỏ | 16 sách/8 lĩnh vực, 10 nhóm nguồn; 3 external từng dùng phát triển luật | Không tuyên bố đại diện toàn bộ giáo trình Việt hoặc hiệu quả trên scan/OCR, sách giữ lại mới. |

Nếu làm vòng hai: (1) chốt ontology + mẫu vàng heading độc lập; (2) xử lý lỗi đã có bằng chứng ở multiline/cấp mục/caption–formula; (3) mới đánh giá có cần CRF hay mô hình bố cục hay không. Dùng split trong train khi tuning; đóng băng phiên bản rồi mới xin phép mở bộ kiểm mới. **Không tự mở sách test, chỉnh nhãn kiểm hay thay A1 trong lượt này.**
