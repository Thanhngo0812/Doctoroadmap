# 18 — Làm sạch watermark của `doc-1` trước khi nạp

**What to build:** `doc-1` đi được hết A1–A5 mà không mang theo dòng watermark của Studocu. Vé 11 đã dừng đúng luật
ở đây: 114 trên 229 chunk còn chuỗi `lOMoARcPSD|31898200`, một chunk còn `Scan to open on Studeersnel`.

**Blocked by:** None. **Chặn:** vé 11 không chạy tiếp `doc-1` và `doc-2` cho tới khi vé này xong.

**Status:** đã cài và kiểm sạch ingest ngày 2026-09-21; phần chạy tiếp vé 11 còn chặn chất lượng A3/A5 (xem dưới).
**Chủ dự án chốt hướng (a) ngày 2026-09-20.**

Hướng (a) đụng vào bước ingest của phase B0 đã đóng, nên đây là **ngoại lệ có chủ đích** như vé 17: chỉ thêm một
tham số, **mặc định giữ nguyên hành vi**. Điều kiện nhận lại: không khai mẫu thì bốn tài liệu cũ và `doc-3` phải
`reused=true` ở đúng phiên bản hiện có, và toàn bộ suite xanh.

## Đo được gì

| | `doc-1` |
|---|---|
| Chunk | 229 |
| Chunk còn watermark | **114** (trang 1–158) |
| Chunk có email cá nhân | **0** — parser đã bỏ được dòng email |
| Dòng lặp trên mọi trang | `lOMoARcPSD|31898200`, `Scan to open on Studeersnel`, và dòng `Downloaded by …` |

Nguy cơ riêng tư nhỏ hơn lo ban đầu vì email không lọt vào chunk nào. Cái còn lại là **mã theo dõi gắn với tài khoản
của chủ dự án** và **nhiễu**: 114 chunk mang một chuỗi vô nghĩa, nó sẽ vào prompt A3, vào embedding, và vào mention
map.

## Ba hướng

| | Cách | Ưu | Nhược |
|---|---|---|---|
| **(a)** | Ingest nhận danh sách mẫu dòng cần bỏ, ví dụ `--strip-line`, ghi mẫu đã dùng vào manifest | hẹp, tường minh, **không đổi hành vi mặc định** nên bốn tài liệu cũ không bị ảnh hưởng | phải khai tay cho từng tài liệu |
| (b) | Luật chung: bỏ dòng ngắn lặp trên ≥60% số trang, ghi mọi dòng đã bỏ vào manifest | tự động cho mọi tài liệu sau này | đổi hành vi phase B0 đã đóng; nếu ai ingest lại bốn tài liệu cũ thì mọi artifact phía sau phải chạy lại |
| (c) | Chủ dự án tìm bản PDF sạch của cùng giáo trình | không đụng code | phụ thuộc có bản khác hay không |

Reviewer đề xuất **(a)**; **chủ dự án chốt (a)** ngày 2026-09-20. Hướng (b) ghi lại làm việc của đợt nghiên cứu sau.

## Việc phải làm

- [x] `ingest` nhận `--strip-line` lặp nhiều lần, so khớp **sau khi chuẩn hoá khoảng trắng**, áp trước khi cắt chunk.
- [x] Manifest của `parse_tree` và `chunks` ghi đủ danh sách mẫu và **số dòng bị tác động**.
- [ ] Không có mẫu thì hành vi **y hệt hiện nay**; bốn tài liệu cũ giữ nguyên artifact, `reused=true`.
      Unit test xác nhận hash/config/text cũ không đổi; `baocao-canhan` và `doc-3` tái dùng. Hai tài liệu cũ khác có
      `adapter_version` trước cấu hình parser hiện tại nên bắt đầu parse mới (đã dừng, không ghi version); PDF
      `nhap-mon-ml` không có trong workspace. Chưa thể khẳng định tiêu chí tái dùng đủ 4/4.
- [x] Test: tài liệu có dòng lặp và mẫu khai báo thì chunk sạch và số dòng bỏ được ghi; không khai mẫu thì chunk
      giữ nguyên. Đột biến: bỏ chuẩn hoá khoảng trắng, áp mẫu sau khi cắt chunk, quên ghi manifest.
- [x] Ingest lại `doc-1` với ba mẫu đã đo, rồi **kiểm lại**: 0 chunk chứa `lOMoARcPSD`, 0 chunk chứa `Studeersnel`,
      0 chunk chứa email. Dán số chunk trước/sau.
- [ ] Chạy tiếp vé 11: `doc-1` qua A1–A5, rồi `doc-2`.

## Thêm từ review vòng 35 (làm cùng vé này)

- [x] **F111:** guard tên ký hiệu của vé 17 chỉ đếm, không ghi tên bị loại. Thêm danh sách có trần 50 tên vào
      artifact ứng viên, để vòng sau kiểm được F110 trên `doc-2`.
- [x] **F112:** thêm test ghim `load_gold(..., require_complete=True)`; hiện đổi thành `False` không test nào đỏ.

## Kiểm chứng chạy thật — 2026-09-21

`doc-1` parse/chunks v1: **229 chunk**, 114 có mã theo dõi, 1 có Studeersnel, 0 có email. Chạy
`--strip-line "lOMoARcPSD|31898200" --strip-line "Scan to open on Studeersnel" --strip-line "Downloaded by"`
cho parse/chunks v3: **218 chunk**, 79 window; 140 dòng văn bản bị tác động, ghi cùng ba mẫu trong **cả hai**
manifest. Quét độc lập `node.text`, `node.raw_text`, toàn bộ JSON chunk/section/document: **0** mã theo dõi,
**0** Studeersnel, **0** email. Nạp lại đúng lệnh tái dùng parse/chunks v3. Nội dung `chunks.json` v2/v3 có SHA-256
giống nhau; v3 bổ sung làm sạch `raw_text` vốn còn 140 node ở v2. Artifact v1/v2 cũ còn trên đĩa và còn mã theo dõi;
không tự ý xóa lịch sử artifact.

Suite toàn bộ xanh ngày 2026-09-21. Đột biến ba nhánh trong vé đều đỏ trước bản sửa; thêm kiểm `raw_text`, đếm
dòng một lần khi có nhiều lần khớp, no-op không mẫu, trần 50 tên F111 và `require_complete` F112. Phần A3/A5 của
vé 11 cần đánh giá riêng: `doc-2` đã đo thấy ký hiệu 3C bị loại kể cả sau guard alias có bằng chứng, và A5 `doc-1`
nhận `en` trên PDF tiếng Việt bị lỗi mã chữ. Không coi hai artifact này là đầu vào vàng đạt chất lượng.
