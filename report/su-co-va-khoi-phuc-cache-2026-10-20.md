# Sự cố cache phát triển và khôi phục — 2026-10-20

## Kết quả đã xác minh

- Đối chiếu từng tệp với SHA-256 trong [manifest nghiệm thu main](ghep-main-evidence-2026-10-20/development-fixtures.json): **787/927 khớp**, **140 thiếu**, **0 sai hash**.
- **doc-6: 122/122 khớp**, gồm PDF, parse tree, chunks, candidates, canonical, retrieval, graph và ảnh công thức. Đã khôi phục vào đúng đường dẫn gốc trong thư mục chung.
- **doc-1: 665/805 khớp**. Còn thiếu `artifacts/canonical/doc-1/v5/{canonical,manifest}.json` và toàn bộ 138 tệp graph trong manifest, gồm graph v45. Chưa đủ đầu vào để chốt lại cổng kiểm toàn repo.
- Đã chép lại 223 tệp đang thiếu; 564 tệp sẵn có được giữ nguyên. Chỉ thao tác các đường dẫn của doc-1/doc-6 có trong manifest, không đọc kho Pha B global hay tập giữ lại.
- Snapshot độc lập, dùng bản chép tệp: `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\development-fixtures-20261020`. Trạng thái và nguồn từng tệp ở `recovery-status.json` trong snapshot.
- Bằng chứng theo từng tệp: [cache-recovery-evidence-2026-10-20.json](cache-recovery-evidence-2026-10-20.json). Không có lời gọi mô hình hoặc dịch vụ trả phí; chi phí **0 USD**. Không sửa mã sản phẩm hay nới test.

## Nguồn khôi phục

- Cache doc-6 từ `tmp/w13-cache-audit-l5xwgnh1` và bản đối chứng `tmp/w13-cache-audit-ypyw9n6q`: 120 tệp cùng đường dẫn khớp manifest. PDF doc-6 vẫn còn ở thư mục chung.
- Ảnh công thức doc-6 tìm được trong fixture cũ, xác minh bằng SHA-256, không suy đoán từ tên tệp.
- Một phần doc-1 khôi phục từ fixture kiểm thử cũ; chỉ nhận tệp có nội dung khớp SHA-256 của manifest gốc. Chi tiết nguồn nằm trong JSON bằng chứng.
- Chưa tìm được nguồn khớp cho 140 tệp còn thiếu trong các bản local đã kiểm. Cần thêm bản sao lưu phát triển khác để khôi phục nguyên trạng; chưa thể cam kết tìm lại đủ. Không tự dựng lại bằng mô hình trả phí.

## Đối chiếu giả thuyết junction

Đã đọc lại các lệnh thực thi của phiên điều phối và phiên lõi, quy đổi giờ UTC sang Asia/Saigon:

1. Lệnh nạp đủ 927 tệp vào `tmp/ghep-main` dùng **`shutil.copyfile(src, dst)`**; không có thao tác tạo junction trong lệnh nạp này.
2. Lệnh gỡ `tmp/ghep-main` chạy khoảng **09:28:52–09:29:13**, sau khi lưu XML/log/manifest. Vì vậy không phải lệnh gỡ diễn ra lúc 09:35.
3. Lệnh gỡ `tmp/w05-postgres` chạy khoảng **09:35:01–09:35:20**. Trước khôi phục, `LastWriteTime` của các thư mục doc-6 graph/retrieval/formula_images là **09:35:03** và chúng rỗng.
4. **Bổ sung đã kiểm trực tiếp từ log phiên lõi:** ngày 2026-10-19 khoảng **21:33**, trong `tmp/w05-postgres` có lệnh `New-Item -ItemType Junction` cho sáu nhóm `parse_tree/chunks/candidates/canonical/retrieval/graph` của doc-1/doc-6 và `phase_b/formula_images/doc-6`, trỏ tới kho tương ứng ở thư mục chung. Lệnh kết thúc với mã 0. Đây là bằng chứng thiết lập junction ở **W-05**, khác với cách chép tệp vào `ghep-main`.
5. Các đích junction này trùng những nhóm dữ liệu bị thiếu, và mốc thư mục rỗng nằm trong khoảng gỡ W-05. Chuỗi bằng chứng ủng hộ mạnh việc dọn W-05 đã tác động qua junction. **Chưa tái hiện độc lập cơ chế xoá**, nên không trình bày một phép tái hiện chưa chạy là đã được chứng minh. Lệnh gốc được lưu trong JSON bằng chứng.

Điều phối xác nhận đã thực hiện cả hai lần dọn. Việc chỉ kiểm worktree sạch theo Git mà chưa kiểm liên kết/reparse point và chưa giữ snapshot độc lập đầy đủ là thiếu sót của điều phối. Manifest chỉ giữ đường dẫn/hash, không thay thế bản sao dữ liệu.

## Tháo junction còn tồn tại theo chỉ thị chủ dự án

- Đã gửi cảnh báo tới các phiên Codex web, lõi và hai phiên Figma đang hiển thị: không sửa, clean, xoá hoặc gỡ `tmp/t01a-clean-ff797eb`; yêu cầu báo lại agent con. Phiên ngoài app server hiện tại không có kênh gửi trực tiếp.
- `cmd /c dir /AL C:\Users\ngoco\Desktop\Doctoroadmap\tmp\t01a-clean-ff797eb` xác nhận `artifacts` là **JUNCTION** tới `C:\Users\ngoco\Desktop\Doctoroadmap\artifacts`.
- Chỉ điều phối chạy **`cmd /c rmdir C:\Users\ngoco\Desktop\Doctoroadmap\tmp\t01a-clean-ff797eb\artifacts`**, không `/S` và không xoá đệ quy.
- Kiểm sau lệnh: liên kết đã mất; thư mục đích `artifacts` còn nguyên; toàn bộ **564 tệp làm đối chứng trước thao tác vẫn khớp SHA-256**.
- Không gỡ worktree t01a. Tiếp tục giữ chỉ thị không đụng worktree này. Các bản cache/snapshot vừa khôi phục cũng không thuộc phạm vi dọn dẹp.
- Chưa xác định junction t01a có liên quan trực tiếp đến lần mất dữ liệu; tháo nó là loại bỏ một liên kết nguy hiểm còn tồn tại, không phải bằng chứng kết luận nguyên nhân.

## Bàn giao tiếp

Nhóm web/lõi có thể dùng các tệp đã khôi phục ở thư mục chung hoặc snapshot trên, chép đúng đường dẫn có trong manifest vào worktree riêng và kiểm hash. Không tạo junction tới kho artifact chung. Không coi toàn bộ 927 tệp đã có; cổng đầy đủ vẫn chờ graph doc-1 v45 và các đầu vào còn thiếu. Các kiểm thử độc lập đủ fixture tiếp tục chạy qua `scripts/w05_run_tests.py`.

Trước mọi lần dọn worktree tiếp theo phải kiểm reparse point/junction và giữ bản sao độc lập của dữ liệu bỏ qua bởi Git. Không dùng kết quả `git status` sạch làm bằng chứng rằng không còn dữ liệu cần giữ.
