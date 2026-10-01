# Vé 12 — ba sửa sau cửa sổ −4…+2

Ngày 2026-10-01. Mã trước lượt sửa đã được chốt ở commit `632a929`. Lượt này chỉ chạy trong `artifacts/v3-r12-quote-evaluation/`; không chạy pass phụ đầy đủ hoặc sửa cache production. Đối chiếu 0 USD: `python scripts/doc-lo-trinh/so_sanh_a8_cua_so_v3.py --evaluation-root artifacts/v3-r12-quote-evaluation`. Script in cả ID và câu trích gốc của các cạnh cứng mới.

## Thay đổi và kiểm chứng

1. Cả phép kiểm trong chunk căn cứ và phép kiểm trong cửa sổ định nghĩa đều gộp mọi khoảng trắng trước khi so. Cạnh lưu lại đúng đoạn trích nguyên gốc (kể cả xuống dòng), không lưu bản mô hình đã dàn phẳng. Câu diễn đạt lại khác chữ vẫn bị bác.
2. Pass phụ: hai phán quyết cùng tạo cạnh, cùng chiều và cùng loại nhưng khác `evidence_kind` thì lấy nhãn tin cậy thấp hơn. Nếu cùng chiều nhưng khác loại, chọn `cong_cu` thành cạnh mềm. Khác chiều hoặc một bên không tạo vẫn `defer`.
3. Prompt của cả hai pass giới hạn căn cứ `can_de_hieu` ở chính phát biểu định nghĩa hoặc giả thiết giới thiệu đối tượng. Câu dẫn dắt/báo trước, ví dụ, bước chứng minh và hệ quả không đủ làm cạnh cứng. Đây là luật ngữ nghĩa trong prompt; executor vẫn chỉ kiểm được vị trí câu trích, nên không bảo đảm chặn mọi ca.

Test mới đã đỏ trên mã cũ rồi xanh sau sửa. Toàn bộ `tests/unit` và `tests/integration` xanh trước khi chạy Vertex. Dry-run pass chính: 458 phiên; chạy thật 598 completion, **1,984043 USD** theo usage. Pilot dry-run còn 205 cặp hai chương vàng (doc-1: 139; doc-2: 66), chạy thật 418 completion, **0,449748 USD**. Tổng usage **2,433791 USD**; không có reservation treo trong hai ledger. Đây là ước giá theo token, không phải hóa đơn Cloud.

| Tài liệu | Cạnh chính | Cứng | Mềm |
|---|---:|---:|---:|
| doc-1 | 207 | 199 | 8 |
| doc-2 | 573 | 504 | 69 |
| doc-3 | 11 | 8 | 3 |
| doc-6 | 3 | 3 | 0 |
| naive-bayes | 6 | 6 | 0 |
| nhap-mon-ml | 38 | 35 | 3 |

Log vẫn có `quote_outside_evidence_chunk` (doc-1: 61, doc-2: 125) và `definition_chunk_not_cited` (9, 162); đây là **lượt bác/repair trong log**, không phải số cạnh cuối mất, và không được tự nới tiếp luật từ số này.

## Chấm vàng — mốc đúng là đồ thị cuối luồng cũ sau rút gọn

`P a/b`: a đúng trên b cạnh dự đoán; `R a/b`: a đúng trên b cạnh vàng. “Bao đóng” là quan hệ đạt được theo đường đi. Hàng lượt mới = chính + pilot qua A9 hiện hành, rồi rút gọn bắc cầu.

| Tài liệu | Đồ thị | Trực tiếp | Bao đóng |
|---|---|---|---|
| doc-1 | Luồng cũ cuối | P 18/29 · R 18/28 | P 106/129 · R 106/131 |
| doc-1 | Lượt cửa sổ −4…+2 trước sửa | P 15/25 · R 15/28 | P 108/127 · R 108/131 |
| doc-1 | Lượt ba sửa | **P 17/29 · R 17/28** | **P 109/134 · R 109/131** |
| doc-2 | Luồng cũ cuối | P 11/17 · R 11/32 | P 22/23 · R 22/68 |
| doc-2 | Lượt cửa sổ −4…+2 trước sửa | P 11/14 · R 11/32 | P 19/23 · R 19/68 |
| doc-2 | Lượt ba sửa | **P 11/16 · R 11/32** | **P 20/25 · R 20/68** |

So với lượt trước, doc-1 lấy lại 2 cạnh trực tiếp đúng và 1 quan hệ bao đóng đúng, nhưng thêm 4 cạnh trực tiếp dự đoán và 7 quan hệ bao đóng dự đoán. Doc-2 lấy thêm 1 quan hệ bao đóng đúng, song số cạnh/quan hệ dự đoán cũng tăng. **Lượt thật chưa đạt hàng chấm lại 0 USD** trong vé (doc-1 17/28 trực tiếp, 118/145 bao đóng; doc-2 12/15 và 21/25), và vẫn chưa chứng minh chất lượng vượt luồng cũ ở cả hai chương.

## Cạnh cứng mới trong phạm vi vàng so với đồ thị cuối luồng cũ

Nhãn “chưa vàng” chỉ có nghĩa không phải cạnh trực tiếp trong bộ chấm, không tự kết luận sai. Câu trích dưới đây là đoạn gốc lưu trên cạnh; ID node đầy đủ có trong output của script đối chiếu.

### doc-1 — 13 cạnh

| Cạnh | Nhãn trực tiếp | Câu trích gốc |
|---|---|---|
| Số chiều → Cơ sở chính tắc | Chưa vàng | “Vậy dim R n = n và B là một cơ sở. B được gọi là cơ sở chính tắc…” |
| Vô hướng → Độc lập tuyến tính | Chưa vàng | “Định nghĩa 3… độc lập tuyến tính nếu hệ thức [formula] chỉ xảy ra…” |
| Véc tơ → Phần tử đối | Chưa vàng | “Các phần tử của V được gọi là các véc tơ… α′ được gọi là phần tử đối…” |
| Tổ hợp tuyến tính → Độc lập tuyến tính | Vàng | “Hệ… độc lập tuyến tính nếu hệ thức [formula] chỉ xảy ra…” |
| Ma trận → Ma trận chuyển cơ sở | Chưa vàng | “Đặt P = … Khi đó (3.1)… P… được gọi là ma trận chuyển cơ sở…” |
| Ma trận → Ma trận tọa độ | Chưa vàng | “Véc tơ (α)S… viết ở dạng cột dẫn đến ma trận [α]S…” |
| Tọa độ → Ma trận chuyển cơ sở | Chưa vàng | “Giả sử α ∈ V có tọa độ… trong các cơ sở S và T.” |
| Phần tử trung hòa → Không gian véc tơ | Chưa vàng | “Các phần tử của V được gọi là các véc tơ… θ được gọi là phần tử trung hòa…” |
| Không gian véc tơ hữu hạn sinh → Không gian véc tơ vô hạn chiều | Chưa vàng | “Nếu V không có một cơ sở nào gồm hữu hạn phần tử…” |
| Cơ sở → Không gian véc tơ vô hạn chiều | Vàng | “Nếu V không có một cơ sở nào gồm hữu hạn phần tử…” |
| Độc lập tuyến tính → Cơ sở chính tắc | Chưa vàng | “Hệ B độc lập tuyến tính vì hệ thức [formula]… Vậy dim R n = n…” |
| Độc lập tuyến tính → Tọa độ | Chưa vàng | “Giả sử S… là một cơ sở… biểu diễn tuyến tính duy nhất [formula] Định nghĩa 7 (Tọa độ)…” |
| Không gian véc tơ thực → Cơ sở | Chưa vàng | “Một hệ véc tơ của V được gọi là một cơ sở…” |

### doc-2 — 9 cạnh

| Cạnh | Nhãn trực tiếp | Câu trích gốc |
|---|---|---|
| Row vector → Row rank | Vàng | “The row rank of A is the dimension of the span of the rows…” |
| Matrix multiplication → Column-row factorization | Chưa vàng | “Then there exist an m-by-c matrix C and a c-by-n matrix R… A = CR.” |
| Matrix multiplication → Row-column rule | Vàng | “In other words, the entry… of AB equals (row j of A) times (column k of B).” |
| Matrix multiplication → Linear combination of the columns | Vàng | “the definition of matrix multiplication implies that the entry… of Ab is [formula]” |
| Column rank → Column-row factorization | Vàng | “Suppose A is an m-by-n matrix… column rank c ≥ 1.” |
| Column vector → Row-column rule | Vàng | “the product of the 1-by-n matrix Aj,⋅ and the n-by-1 matrix B⋅,k…” |
| Row rank → Column rank | Chưa vàng | “The row rank of A is the dimension of the span of the rows…” |
| Scalar multiplication on matrices → dim F^m,n = mn | Vàng | “With addition and scalar multiplication defined as above… dimension mn.” |
| Scalar multiplication on matrices → additive identity of F^m,n | Chưa vàng | “With addition and scalar multiplication defined as above… dimension mn.” |

**Còn đáng đọc:** “Số chiều → Cơ sở chính tắc” vẫn trích câu kết ví dụ; “Độc lập tuyến tính → Cơ sở chính tắc” kéo cả đoạn chứng minh; “Row rank → Column rank” vẫn có thể là hai định nghĩa cùng khối, không phải tiên quyết. Prompt mới chưa loại sạch các ca này. Chủ dự án quyết định có chấp nhận/điều chỉnh tiếp hay không trước bất kỳ pass phụ đầy đủ nào.

**Điểm dừng:** không chạy pass phụ đầy đủ (~31 USD), A9/A10 production hoặc đưa nhãn vàng vào hệ thống. Đợi chủ dự án đọc bảng và 22 cạnh trên.
