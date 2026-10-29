# Lời giao subagent lõi — W-26 máy chủ demo local chạy thật

Bạn là subagent lõi của dự án WayFinder. Đọc theo thứ tự rồi mới làm:
1. `tmp/claude-tools/so-tay-agent-web.md` (sổ tay, luật cấm, môi trường, bằng chứng).
2. Vé `task/web/W-26-may-chu-demo-local-chay-that.md` (phạm vi và tiêu chí; nguồn chân lý của việc này).
3. `task/web/00-ke-hoach.md` mục "Luật chung của mọi vé"; `src/web/README.md`.
4. Mã: `src/web/backend/wayfinder/cli.py`, `worker.py`, `composition.py`, `settings.py`, `infrastructure/real_build.py`, `infrastructure/build_spend.py`,
   `infrastructure/learning_media.py`, `fakes/local_media.py`, `application/seed_samples.py`; test W-15 (`test_build_approval_w15.py`,
   `test_build_spend_w15.py`) để hiểu guard chi và receipt.

Worktree `tmp/w26-demo-local`, nhánh `work/w26-demo-local`, tạo từ main local mới nhất.

Điểm cần giữ:
- Mọi test 0 USD: mô hình, embedding, SMTP đều giả. **Không gọi Vertex, không gửi thư thật, không gọi Cloudinary** trong lúc cài/kiểm.
- Giấy phép chi tự động chỉ bật qua cờ của lệnh demo local; server/worker mặc định vẫn khoá chi. Không endpoint HTTP tạo giấy phép.
- Không sửa mã lõi `src/doc2roadmap` trừ khi bắt buộc; nếu bắt buộc thì ghi lý do vào báo cáo.
- Không đụng DB `wayfinder` dùng chung; test dùng DB UUID riêng trên `db-test`.
- Chạy `src/web/backend/tests` qua runner (và test React nếu đụng frontend). Không chạy cổng toàn repo.
- Bảng phá: bỏ kiểm tên DB, bỏ trần cuốn, bỏ trần ngày, cộng receipt hai lần, để cờ demo tắt mà vẫn chi, khởi tạo Cloudinary.

Bàn giao: báo cáo `report/w26-demo-local-<ngày>.md` theo sổ tay mục 5, có **lệnh chạy máy chủ demo** (từng bước PowerShell) để điều phối mở cho chủ dự án.
Không tự chạy máy chủ demo thật, không ghép, không push.
