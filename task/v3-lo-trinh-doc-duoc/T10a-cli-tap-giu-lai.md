# T10a — Lệnh chuẩn cho lượt tập giữ lại: chuyển vai trò, dừng sau danh tính, bảng duyệt không đọc vàng

**Nguồn chân lý:** [giao thức T10/07 v2](T10-07v2-giao-thuc-tap-giu-lai.md) · **Ai:** nhân viên · **Phụ thuộc:** — (làm song song với pass phụ
vé 12) · **Chi phí mô hình:** 0

**Trạng thái:** đã triển khai lệnh và kiểm tương đương trên doc-6/doc-1 (2026-10-03); chưa chạy tập giữ lại. [Báo cáo](../../report/v3-20-21-t10a-2026-10-03.md). **Claude nghiệm thu: đạt (2026-10-03).**

## Vì sao (Claude, 2026-10-01, khi kiểm giao thức với mã hiện có)
- **Chuyển vai trò sang version chunks cũ chưa có lệnh chuẩn.** Bậc 1 của giao thức phải làm như doc-2: ingest lại làm cây tham chiếu, gán
  vai trò, rồi chuyển sang version chunks mà A3–A5 và bộ vàng gắn vào.
  - `LabelChunkRoles` đã có `transfer_from_chunks_version`, nhưng CLI `label-roles` không nhận cờ này.
  - doc-2 làm bằng `scripts/doc-lo-trinh/chay_vung_va_neo_v3.py`, script đó ghi cứng `DOC2_STRUCTURE_VERSION`.
- **Không dừng được sau danh tính.** `roadmap --stop-after` chỉ có clusters/mentions/provenance/edges/stages. Chuỗi v3 đặt neo và danh tính
  giữa provenance và edges. Giao thức cần dừng ngay sau danh tính để chủ dự án duyệt (T14) **trước** A8.
- **Bảng duyệt danh tính đọc vàng.** `scripts/duyet-danh-tinh/tao_bang.py` đọc `gold["edges"]` để đánh dấu cặp "chạm vàng".
  - Với tập giữ lại, làm vậy là mở vàng trước bước chấm; vàng xstk còn chưa chuyển sang JSON.
  - Script luôn ghi vào `artifacts/a8-gold/`, nơi có bảng chủ dự án đã điền.

## Việc cần làm
1. `label-roles --transfer-from-chunks-version <v>`: nối thẳng vào tham số đã có của use case; dry-run báo đúng phụ thuộc.
2. `roadmap --stop-after identity` (thêm `teaching` nếu rẻ). Dừng sau stage đó, dry-run và `--allow-spend` hoạt động như các điểm dừng
   khác. `--identity-review` chạy lại từ danh tính trở xuống đúng chuỗi v3.
3. `scripts/duyet-danh-tinh/tao_bang.py`:
   - chế độ **không cần tệp vàng**: liệt kê **mọi** cặp mà bước danh tính không phán `different` (gộp và tách nghĩa). Đây là tập lớn hơn
     yêu cầu "gộp chạm vàng" của W15, nên không phải đọc vàng;
   - tham số thư mục ra (mặc định giữ như cũ);
   - đọc được artifact `identity` của chuỗi v3.
4. Viết lại quy trình bậc 1–3 của giao thức thành lệnh CLI cụ thể trong `CONTEXT.md` hoặc `doc/spec-addendum.md`.
5. **Kiểm tương đương chuỗi** (thêm 2026-10-02):
   - Số nghiệm thu vé 12 đến từ các script đánh giá (`chay_tien_a8_v3.py`, `chay_a8_full_v3.py`), còn lượt tập giữ lại chạy bằng lệnh
     `roadmap` (`composition.build_learning_graph`). Hai đường dựng stage riêng. Ví dụ script dùng mô hình `max_output_tokens` 2048 cho neo,
     1024 cho danh tính, 512 cho tên khái niệm; composition dùng một mô hình 8192 cho mọi stage.
   - Viết script 0 USD: với mỗi stage của chuỗi composition, gọi `plan(doc, upstream=<artifact đầu vào trong kho đánh giá cuối>)` và so với
     artifact kế tiếp trong kho đó. Mọi stage phải ra **"tái dùng"** (cùng source hash và config hash).
   - Stage nào lệch thì sửa cho hai đường khớp, rồi kiểm lại. Lệch tham số chỉ ở bộ chuyển đổi, như `max_output_tokens` của mô hình, không
     vào config hash nhưng vẫn đổi lời gọi thật, cũng phải khớp hoặc ghi rõ là vô hại.
   - Chạy cho ít nhất doc-6 và doc-1 trên `v3-r12-final-evaluation`.

## Nghiệm thu
- **Test:**
  - `label-roles` chuyển vai trò qua CLI trên fixture hai version;
  - `--stop-after identity` dừng đúng chỗ và không gọi A8;
  - bảng duyệt chế độ không vàng liệt kê đủ cặp và không mở tệp vàng (fixture không có tệp vàng vẫn chạy).
- **Chạy thử 0 USD trên tài liệu phát triển** (không đụng tập giữ lại):
  - `roadmap --dry-run --stop-after identity` cho doc-1;
  - sinh bảng duyệt chế độ không vàng cho artifact identity v3 của doc-1, ghi vào `tmp/`.
- **Tôi kiểm:** đọc diff, chạy test, đối chiếu lệnh với giao thức.

## Kiểm thử của Claude (2026-10-03) — **đạt**
- **Test:** các test mới (dừng sau `teaching`/`identity`, plan không chạm A8, `label-roles` chuyển vai trò qua CLI) đỏ trên mã trước sửa,
  xanh sau sửa. Toàn bộ 825 test xanh trên `2d255e4`.
- **Kiểm tương đương chuỗi:** tôi chạy lại `kiem_tuong_duong_chuoi.py`. Cả doc-6 và doc-1 đạt 11/11 tầng "tái dùng". Trần token của adapter
  khớp manifest: provenance, pass chính, pass phụ 8192; neo 2048; danh tính 1024; tên khái niệm 512; tên module 128.
- **Đột biến**, để chắc script biết báo lệch:
  - đổi trần token neo 2048 → 4096, chỉ ở adapter: script báo `teaching` lệch ở cả hai tài liệu, mã thoát 1. Config hash vẫn bằng, nên
    phép so trần token là chốt duy nhất bắt được loại lệch này;
  - đặt `DOC2ROADMAP_A8_DEFINITION_AFTER=3`: `main_edges` ra "run", báo lệch, mã thoát 1.
- **Bảng duyệt không vàng:** `tmp/t10a-doc-1/` có 12 cặp, đúng bằng 11 `same` + 1 `sense_split` của identity v41; 369 cặp `different` bị bỏ
  đúng; 0 cặp chạm vàng. Test fixture không có tệp vàng vẫn chạy.
- **Lệnh bậc 1–3** trong `CONTEXT.md` khớp giao thức, kể cả bậc 2b T14 trước A8.
- **Bảng khoá** (`scripts/khoa-cau-hinh/tao_bang.py`, của tôi) đã cập nhật theo vé này và vé 22:
  - thêm cột so `prompt_hash` với manifest lượt nghiệm thu của doc-1 và doc-6;
  - ghi trần token thật của từng adapter;
  - ghi thiết lập bộ giới hạn (`llm_max_in_flight`, `llm_tpm_budget`, `llm_rpm_budget`) vào nhóm không thuộc phương pháp;
  - chỉ chặn khoá khi mã chạy (`src/`, `scripts/`, `pyproject.toml`, `uv.lock`) chưa commit. Tệp riêng của chủ dự án thì chỉ liệt kê;
  - lệnh khoá thật từ chối ghi khi lệch. Đột biến `prompt_hash` pass phụ: mã thoát 1, không ghi tệp khoá.
  - Bản nháp hiện tại: cả 10 `prompt_hash` khớp ở cả hai tài liệu.
