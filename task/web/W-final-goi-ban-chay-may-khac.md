# W-final — Gói bản chạy được trên máy khác

**Nguồn:** chủ dự án 2026-10-29: "sau này khi ta hoàn tất hoàn thiện tất cả, bạn viết một vé W-final: là gom src và những thứ cần tối thiểu tạo thành
1 folder ngoài desktop để đem qua máy người khác chạy lên, có readme hướng dẫn làm gì làm gì r ấn gì để bật sv chạy, không cần mấy số liệu doc test gì,
chỉ cần code để ng khác chạy".
**Ai:** subagent lõi · **Chi phí:** 0 USD · **Chặn bởi:** mọi vé web còn mở (W-17, W-18, W-19, W-20, W-23, W-26) · **Trạng thái:** chờ; làm sau cùng.
Claude viết lại phần chi tiết của vé này khi mọi vé khác đã đạt, theo trạng thái mã lúc đó.

## Mục tiêu

Một thư mục ngoài Desktop (ví dụ `Desktop\WayFinder-ban-chay`) chép sang máy người khác, làm theo README là bật được máy chủ demo như W-26: backend,
giao diện, worker dựng sách, PostgreSQL, sáu khoá mẫu.

## Phải có

- Chỉ mã cần để chạy: `src/doc2roadmap`, `src/web` (backend, frontend, docker-compose), `pyproject.toml`, `uv.lock`, các mô hình/tệp lõi cần lúc chạy
  (ví dụ mô hình pass phụ, `vendor/` nếu mã nạp), logo/favicon/font giao diện dùng.
- Dữ liệu tối thiểu để có sáu khoá mẫu (đồ thị và tệp học của sáu cuốn phát triển), đường dẫn tương đối trong thư mục gói.
- Một lệnh bật (ví dụ `chay.ps1`, nhấp đúp hay chạy một dòng): kiểm Python/uv, Node, Docker và báo rõ thiếu gì; cài thư viện; bật PostgreSQL; tạo DB và
  migrate; nạp khoá mẫu; build giao diện; mở server và worker; in địa chỉ để mở trình duyệt. Chạy lại lần hai không hỏng dữ liệu đã có.
- `.env.example` liệt kê mọi khoá cần điền (Gmail, PostgreSQL, Vertex project hoặc khoá Gemini Developer API), không chứa bí mật thật.
- `README.md` tiếng Việt, từng bước cho người không rành: cài gì, điền gì, bấm gì, mở địa chỉ nào, dừng thế nào, lỗi hay gặp.

## Không được có

- Test, báo cáo, bằng chứng, `report/`, `task/`, `doc/` (trừ README gói), `evaluation/`, `document-data/`, `artifacts/phase_b/live.json`, tập giữ lại
  (`d01-t01`, `d01-t02`, `document-data/test/`, `Desktop\d02-tap-khoa`), `.env` thật, `.venv`, `node_modules`, `.git`.

## Tiêu chí nghiệm thu

- [ ] Script tạo gói chạy lại được, có danh sách cho phép (allowlist), test kiểm gói không chứa đường dẫn nằm ngoài allowlist hay bí mật.
- [ ] Không còn đường dẫn tuyệt đối của máy này (`C:/Users/ngoco`) trong mã và cấu hình của gói.
- [ ] Bật thử gói từ một thư mục khác trên máy này (sao chép mới, DB mới) theo đúng README: đăng ký, nhận thư, mở khoá mẫu, học được.
- [ ] Kích thước gói và thời gian cài lần đầu ghi trong báo cáo.

Tham khảo: thư mục `Desktop\doctoroadmap-developer` (bản xuất thử ngày 29/10, chưa soát) — đọc, không ghi đè.
