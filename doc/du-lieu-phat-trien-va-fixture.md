# Dữ liệu phát triển và fixture kiểm thử

Quyết định theo phê duyệt của chủ dự án ngày 2026-10-20: “duyệt tất cả làm end to end khôi phục đi”.

- Kiểm hồi quy đơn vị dùng fixture tổng hợp nhỏ trong repo. Quiz dùng `tests/fixtures/phase_b_quiz_graph`, không phụ thuộc graph v45 trong kho chung.
- Kiểm tích hợp cần dữ liệu sách thật dùng bản sao phát triển cố định dưới `document-data/`, kèm manifest SHA-256 được lưu trong report. Chỉ cho phép doc-1 và doc-6 trong bản nghiệm thu khôi phục này.
- Kho dùng chung `artifacts/` là kết quả làm việc, không phải bản sao lưu. Không tạo junction, symlink hoặc hardlink từ worktree tới dữ liệu chung. Không sao chép cả thư mục artifacts hoặc kho Pha B live; chỉ chép tệp ghi trong manifest.
- Giữ nguyên bản trước dựng `document-data/development-recovery-2026-10-20`; bản sau dựng và manifest được ghi trong báo cáo khôi phục. Không đưa PDF, cache mô hình hoặc dữ liệu sách vào Git.

## Dùng bản sao trong một worktree mới

Tạo worktree một cấp dưới `tmp/`, theo quy trình nhánh. Đặt `source` tới bản sao cố định và `target` tới gốc worktree mới. Đọc danh sách tệp từ manifest đã chốt. Với mỗi tệp, đối chiếu SHA-256 ở nguồn, `shutil.copyfile` sang đích, rồi đối chiếu lại SHA-256 ở đích. Dừng nếu nguồn/đích là liên kết, có đường dẫn thoát gốc, hoặc có dữ liệu đích khác hash. Không dùng `copytree` trên một cây chưa kiểm liên kết.

Chạy qua runner để kiểm đúng mã của worktree và bắt buộc PostgreSQL:

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-<moc> --junitxml=tmp/cong-<moc>.xml
npm.cmd --prefix src/web/frontend ci --no-audit --no-fund
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
```

Không dọn worktree cũ trong đợt khôi phục này. Trước bất kỳ đợt dọn nào sau này, kiểm tra reparse point tại gốc và các thư mục dữ liệu; không xoá đệ quy khi còn liên kết. Worktree `tmp/t01a-clean-ff797eb` tiếp tục được giữ nguyên.

## Đổi phiên bản graph

Số phiên bản chỉ có ý nghĩa trong một kho artifact. Dựng lại từ kho graph rỗng có thể bắt đầu từ v1; không đặt giả v45 hoặc v57. Graph nghiệm thu phải ghim đúng chunks và parse; chỉ mục truy hồi phải khớp chunk ID, nội dung và đường mục. Đổi graph cần đối chiếu cache Pha B theo nội dung/ngữ cảnh, không dùng lại chỉ vì trùng module ID.

Bản cache cũ không có nguồn riêng đã xác minh thì ghi rõ không đối chiếu được. Không mở dữ liệu giữ lại hoặc kho Pha B live chung để tìm thông tin bù.

## Pha B của doc-1 sau dựng lại

Graph học mới là **v8**, kho Pha B mới là **`artifacts/phase_b/doc-1-rebuild-20261020.json`**. Các thao tác đọc/học của doc-1 phải truyền rõ cả phiên bản và kho này. Ví dụ:

```text
doc2roadmap phase-b a12 --doc-id doc-1 --graph-version 8 --store artifacts/phase_b/doc-1-rebuild-20261020.json --mode offline
doc2roadmap phase-b progress --doc-id doc-1 --graph-version 8 --store artifacts/phase_b/doc-1-rebuild-20261020.json --mode offline
```

Khâu tên có đầu vào A10 v7 và đầu ra v8. Khi chỉ kiểm cache tên, dùng lệnh mặc định để runtime quay đúng đầu vào A10, không đặt lại tên trên đầu ra đã có tên:

```text
doc2roadmap phase-b names --doc-id doc-1 --dry-run --store artifacts/phase_b/doc-1-rebuild-20261020.json
```

Đã kiểm qua đường CLI thật với transport bị chặn: 35 ngữ cảnh tên có cache, 0 lời gọi cần thiết. Đổi thử một node ID làm đúng một ngữ cảnh miss cache; không phục vụ tên của node cũ. Kiểm 35 thẻ module, không có node thiếu hoặc tên lệch graph v8. Kho cũ v45/v57 không được chuyển trộn vào kho mới; không tuyên bố đã đối chiếu hay xoá cache cũ.

Các lệnh thử có ghi dữ liệu như quiz/session/progress nên chạy với một bản chép của kho mới trong `tmp/`; giữ snapshot và ZIP cố định nguyên vẹn. Không bật `--allow-spend` cho thao tác kiểm cache.
