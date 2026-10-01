# T10a — Lệnh chuẩn cho lượt tập giữ lại: chuyển vai trò, dừng sau danh tính, bảng duyệt không đọc vàng

**Nguồn chân lý:** [giao thức T10/07 v2](T10-07v2-giao-thuc-tap-giu-lai.md) · **Ai:** nhân viên · **Phụ thuộc:** — (làm song song với pass phụ
vé 12) · **Chi phí mô hình:** 0

**Trạng thái:** chờ giao

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

## Nghiệm thu
- **Test:**
  - `label-roles` chuyển vai trò qua CLI trên fixture hai version;
  - `--stop-after identity` dừng đúng chỗ và không gọi A8;
  - bảng duyệt chế độ không vàng liệt kê đủ cặp và không mở tệp vàng (fixture không có tệp vàng vẫn chạy).
- **Chạy thử 0 USD trên tài liệu phát triển** (không đụng tập giữ lại):
  - `roadmap --dry-run --stop-after identity` cho doc-1;
  - sinh bảng duyệt chế độ không vàng cho artifact identity v3 của doc-1, ghi vào `tmp/`.
- **Tôi kiểm:** đọc diff, chạy test, đối chiếu lệnh với giao thức.
