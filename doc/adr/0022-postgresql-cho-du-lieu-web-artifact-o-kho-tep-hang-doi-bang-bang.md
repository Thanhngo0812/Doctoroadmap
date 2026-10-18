# PostgreSQL cho dữ liệu web và kho Pha B; artifact Pha A ở kho tệp; hàng đợi bản dựng là một bảng

**Status:** proposed — 2026-10-18 (chờ chủ dự án duyệt cùng [spec cơ sở dữ liệu](../web-co-so-du-lieu-spec.md))

**Một cơ sở dữ liệu PostgreSQL** chứa dữ liệu web (tài khoản, khoá học, chia sẻ, bản dựng, nhật ký) và kho Pha B (cache, bản ghi, sổ chi).
- Kho Pha B trên PostgreSQL là bản cài thứ ba của port `PhaseBStore`, qua cùng bộ test hợp đồng với bản JSON và bản bộ nhớ.
- Bản ghi Pha B nằm trong **một bảng chung** `(kind, record_id, owner, doc_id, value jsonb)`, không tách bảng theo loại.
- `single_flight` khoá giữa các tiến trình bằng advisory lock.

**Artifact Pha A** (đồ thị, chunk, vector) và tệp tải lên **ở kho tệp** có phiên bản như hiện nay. Cơ sở dữ liệu chỉ giữ `doc_id`, phiên bản, và khoá lưu
trữ.

**Hàng đợi bản dựng** là bảng `build`; worker nhận việc bằng `FOR UPDATE SKIP LOCKED`, có nhịp tim.

**Căn cứ:**
- Kho JSON ghi lại cả tệp mỗi lần đổi, và chỉ an toàn trong một tiến trình. Web cần nhiều worker.
- Hợp đồng Pha B còn đổi thường xuyên. Một bảng chung giữ port không đổi, và di trú không phải chạy theo từng vé Pha B.
- Artifact Pha A lớn, có phiên bản, và đã có kho tệp cùng mã đọc ghi. Chuyển chúng vào cơ sở dữ liệu là việc lớn mà không có lợi cho chức năng web.
- Bản dựng ít (vài lượt mỗi người mỗi tháng) và chạy lâu. Một bảng là đủ; Redis hay Celery thêm một dịch vụ phải vận hành cho nhóm 4 người.

**Considered Options**

- *SQLite.* Gọn cho máy cá nhân, nhưng ghi đồng thời từ nhiều worker yếu, và không có advisory lock hay `SKIP LOCKED`.
- *Tách bảng Pha B theo loại* (phiên, lượt, tiến độ…). Truy vấn đẹp hơn, nhưng mỗi lần Pha B đổi trường lại cần di trú, và port phải đổi.
- *MongoDB hay kho tài liệu khác cho Pha B.* Thêm một hệ thứ hai; ràng buộc giao dịch giữa thành viên khoá học và dữ liệu học khó hơn.
- *Celery cộng Redis cho bản dựng.* Mạnh hơn khi nhiều việc ngắn; ở đây thừa.
- *pgvector cho vector.* Để sau; truy hồi hiện đọc vector từ artifact.

**Consequences**

- Port `PhaseBStore` nới `usage_rows` (lọc theo người, thời điểm, mục đích) và thêm `anonymize_learner_usage`, giữ tương thích ngược.
- Test lưu trữ cần một PostgreSQL thật (docker compose). Lệnh kiểm của vé coi thiếu PostgreSQL là hỏng.
- Sao lưu gồm hai phần: `pg_dump` và bản sao kho tệp. Khôi phục phải khớp cả hai.
