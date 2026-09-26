# 10 — Danh tính mở rộng

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R8 · **Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** ≈ 0,05 USD / tài liệu

**Trạng thái:** phần đề cử **đạt**; áp tự động trong luồng mặc định **chưa đạt** → vé [10b](10b-danh-tinh-xac-minh.md) — Claude
kiểm thử 2026-09-26 (mục cuối)

## Việc cần làm
Thêm nguồn ứng viên trong `identity_candidates`:
- chuẩn hoá tên như bước neo (`anchors._compact`: NFKC, bỏ dấu LaTeX, gộp gạch nối);
- viết tắt ↔ tên đầy đủ (chữ đầu các từ, bỏ dấu: CSDL ↔ Cơ sở dữ liệu);
- tên ký hiệu ↔ tên chữ qua tương tự mô tả + câu neo (vector nút sẵn có từ A6, top-3, ngưỡng ghi trong config);
- tiền tố chung chung thêm "hệ ", "phép ".
Phán và luật gộp (nhóm kiểm đủ; người duyệt gộp chạm vàng) giữ nguyên.

## Tệp liên quan
`domain/identity.py`, `application/use_cases/judge_identity.py`.

## Nghiệm thu
- Test mỗi nguồn: CSDL/Cơ sở dữ liệu; Upper triangular matrix/Upper-triangular matrix; Độc lập tuyến tính cực đại/Hệ độc lập tuyến
  tính cực đại; một cặp chỉ giống mô tả được đưa ra xét nhưng vẫn cần phán `same` mới gộp.
- **Tôi kiểm:** các cặp trong báo cáo L6 được đưa ra xét; đọc các gộp mới trên doc-1, doc-2, doc-6.

## Kiểm thử của nhân viên

Đã thấy test đỏ trước sửa, test bốn nguồn và luật gộp đều xanh. `a10-identity-v2`, top-3 hợp hai chiều, cosine ≥ 0,85
ghi trong config; vector mô tả A6 đề cử, câu neo đưa vào phán, không gọi thêm embedding.
Đủ **6/6 cặp L6** được đề cử; 5 same, Upper triangular/Upper-triangular được phán different do mô tả R trong QR
khác định nghĩa tổng quát. Không ép gộp để khớp danh sách lỗi.

Đã chạy doc-1/doc-2/doc-6 trên teaching v33/v27/v9: 378/723/31 lời gọi; 12/25/1 node gộp; 0/3/0 nhóm mở;
cả ba DAG, không cạnh treo. Chi telemetry **0,28330450 USD** trong mức 1,50 USD chủ dự án duyệt. Không chạy A8.
Kết quả nằm ở `artifacts/v3-identity-evaluation`, không thay kho mặc định; tái dùng 3/3 với 0 lời gọi.

**Chưa qua cổng xuất bản:** hai gộp mới thực sự chạm vàng doc-1 cần người duyệt; Q6 doc-1 1/39 → 3/39; doc-2 có
ba nhóm mở và một số phán same đáng nghi (trường hợp riêng/định lý bằng nhau bị coi là danh tính). CSDL lấy đại diện
ở đề cương, cần quyết cách giữ trạng thái dạy của nhóm trước vé 07. Không đổi luật phán/gộp ngoài phạm vi vé.
Đã xuất `review-pending.json` với quyết định để trống. [Toàn bộ số, đọc/phán và điểm cần duyệt](../../report/v3-01-03-10-ket-qua-2026-09-26.md).

## Kiểm thử (Claude, 2026-09-26) — đề cử đạt; áp tự động chưa đạt → vé 10b

- Test xanh. Đột biến 5/5 bị bắt: tắt nguồn viết tắt; bỏ ngưỡng cosine; bỏ giới hạn top-k; bỏ tiền tố "hệ"/"phép"; gạch nối không còn
  tương đương khoảng trắng.
- Đề cử: đủ 6/6 cặp L6 được đưa ra xét. Chi thật 0,2833 USD trong mức duyệt 1,50 USD; sổ chi giữ chỗ trước khi gọi mạng. Bảng kiểm
  R11 tôi chạy lại khớp đúng từng số nhân viên báo.
- **Đọc 44 cặp `same` mới** (mô tả, câu neo, định nghĩa trong sách). Tiêu chí: gộp khi và chỉ khi hai nút cùng ngoại diên.
  - Đúng **27/44 (61%)**: doc-1 8/9, doc-6 1/1, doc-2 18/34. Trong 32 gộp đã áp ở bản thử, **11 gộp sai**.
  - 17 cặp sai gồm: 11 trường hợp riêng/lớp con/thể hiện (Set ↔ Finite set, singular values ↔ positive singular values,
    Finite-dimensional vector space ↔ Finite-dimensional subspace, Volume ↔ Volume of a box…); 3 bằng nhau nhờ định lý hay đặc
    trưng (null T′ ↔ (range T)⁰, Characterization of normal operators ↔ Normal operator, column rank of ℳ(T) ↔ dim range T);
    1 hai định lý khác nhau (Schur ↔ upper-triangular form exists if F = C); 1 đối tượng ↔ ánh xạ (Matrix of a linear map ↔ ℳ);
    1 nút trộn hai nghĩa (Trace).
  - 8 cặp thuộc vùng xám, ghi riêng. Nhãn từng cặp: [10b-tap-kiem-danh-tinh.json](10b-tap-kiem-danh-tinh.json) — nhãn của tôi, không
    phải nhãn người.
  - Lý do mô hình tự ghi lộ quan hệ không-danh-tính ở 12/17 cặp sai ("specific case", "equivalent", "defined as being equal"), nhưng
    cũng dính 6/27 cặp đúng. Lọc theo từ khoá vì thế quá thô; cần bắt mô hình phân loại quan hệ vào một tập đóng (10b).
- **Hồi quy Q6 doc-1 (1/39 → 3/39) không do gộp sai nghĩa mà do bước gỡ chu trình sau gộp.**
  - Gộp "Hệ ĐLTT cực đại" vào "ĐLTT cực đại", cộng với gộp T5 cũ "Phụ thuộc tuyến tính" ← "Hệ véc tơ phụ thuộc tuyến tính", tạo chu
    trình ĐLTT cực đại → Hạng của hệ véc tơ → Phụ thuộc tuyến tính → ĐLTT cực đại.
  - Hai cách gỡ có trọng số bằng nhau (2.750). Hàm gỡ chọn xoá cạnh đúng Phụ thuộc tuyến tính → ĐLTT cực đại (căn cứ trong định
    nghĩa), thay vì cạnh Hạng → Phụ thuộc tuyến tính nhập từ một thành viên được dạy muộn. Nguyên nhân: `order_relation` của cạnh
    bị đổi đầu mút vẫn tính theo vị trí thành viên cũ.
  - Tính lại chiều cạnh theo vị trí đại diện rồi mới gỡ (thí nghiệm `scripts/doc-lo-trinh/thu_go_chu_trinh_sau_gop.py`, 0 USD):
    doc-1 Q6 về 1/39, Q7 89,67%, Q7b 58,90% (bằng baseline) mà vẫn giữ đủ 12 gộp; doc-2 không đổi (3/61).
- **Lỗi đại diện:** `identity_map` chọn thành viên có vị trí sớm nhất bất kể trạng thái dạy. doc-6 giữ "CSDL" (`mentioned_only`, đề
  cương) ở vị trí 0 và bỏ "Cơ sở dữ liệu" (`taught`); đại diện không nhận tên thành viên làm alias. Nếu vé 07 lọc khái niệm chỉ-nhắc
  trước khi sửa lỗi này, khái niệm trung tâm của môn sẽ biến mất khỏi dãy học → vé 07 chờ 10b.
- Đính chính của tôi: báo cáo L6 từng coi "ĐLTT cực đại ≈ Hệ ĐLTT cực đại" là trùng. Đọc kỹ thì đó là hai định nghĩa riêng (trong V
  ở mục cơ sở, trong S ở mục hạng), tức trường hợp riêng, không gộp. Cặp Upper triangular matrix / Upper-triangular matrix được phán
  `different` là đúng theo mô tả hiện có, nhưng mô tả của nút đầu bị thu hẹp thành "ma trận R trong QR" — lỗi mô tả ở A5, ngoài
  phạm vi 10b.
- Rủi ro hiện tại: `a10-identity-v2` đã nằm trong luồng mặc định. **Không chạy `roadmap --allow-spend` để xuất bản lộ trình trước khi
  10b xong** (`--dry-run` sẽ báo identity "sẽ chạy").
