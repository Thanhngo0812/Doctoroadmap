# 18 — Làm sạch watermark của `doc-1` trước khi nạp

**What to build:** `doc-1` đi được hết A1–A5 mà không mang theo dòng watermark của Studocu. Vé 11 đã dừng đúng luật
ở đây: 114 trên 229 chunk còn chuỗi `lOMoARcPSD|31898200`, một chunk còn `Scan to open on Studeersnel`.

**Blocked by:** None. **Chặn:** vé 11 không chạy tiếp `doc-1` và `doc-2` cho tới khi vé này xong.

**Status:** chờ chủ dự án chọn hướng

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

Reviewer đề xuất **(a)**, và ghi (b) lại làm việc của đợt nghiên cứu sau.

## Việc phải làm nếu chọn (a)

- [ ] `ingest` nhận `--strip-line` lặp nhiều lần, so khớp **sau khi chuẩn hoá khoảng trắng**, áp trước khi cắt chunk.
- [ ] Manifest của `parse_tree` và `chunks` ghi đủ danh sách mẫu và **số dòng đã bỏ**.
- [ ] Không có mẫu thì hành vi **y hệt hiện nay**; bốn tài liệu cũ giữ nguyên artifact, `reused=true`.
- [ ] Test: tài liệu có dòng lặp và mẫu khai báo thì chunk sạch và số dòng bỏ được ghi; không khai mẫu thì chunk
      giữ nguyên. Đột biến: bỏ chuẩn hoá khoảng trắng, áp mẫu sau khi cắt chunk, quên ghi manifest.
- [ ] Ingest lại `doc-1` với ba mẫu đã đo, rồi **kiểm lại**: 0 chunk chứa `lOMoARcPSD`, 0 chunk chứa `Studeersnel`,
      0 chunk chứa email. Dán số chunk trước/sau.
- [ ] Chạy tiếp vé 11: `doc-1` qua A1–A5, rồi `doc-2`.
