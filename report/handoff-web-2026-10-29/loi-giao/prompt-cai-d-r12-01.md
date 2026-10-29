# Lời giao subagent thiết kế — W-23 sửa D-R12-01 rồi mở rộng đối chiếu

Bạn là subagent thiết kế của dự án WayFinder. Đọc theo thứ tự rồi mới làm:
1. `tmp/claude-tools/so-tay-agent-web.md` (sổ tay, luật cấm, môi trường, bằng chứng).
2. `task/web/W-23-doi-chieu-figma-va-giao-dien.md` và `doc/web-thiet-ke-giao-dien-spec.md`.
3. `report/lenh-giao-viec-ba-nhom-lan12-2026-10-28.md` **mục 3** (lời giao gốc; nhóm thiết kế chưa nhận nên chưa ai làm) và
   `report/dieu-phoi-nghiem-thu-ba-nhom-lan12-2026-10-28.md` mục 4.
4. Báo cáo W-23 hiện có trên nhánh dưới đây và bằng chứng điều phối ở `report/coord-ba-nhom-lan12-evidence-2026-10-28/` (`design-review/`,
   `browser-react-fonts/`, `browser-react-fallback/`).

Tiếp nhánh **`work/w23-paired-web-evidence`** trong worktree có sẵn **`tmp/w23-paired-web-evidence`** (đỉnh `f9705f42`). Không tạo nhánh mới. Trước hết
nhận main mới bằng `git merge --no-ff main`, kiểm mã thoát.

## Bước 1 — D-R12-01 (Required, làm trước)

Script và receipt đang gọi các số **điền sẵn** là "đo React thật": `reactActualMetrics`, `measuredHeight`, `leafSourceValid`/`diff=0`. Chạy khi không có
nguồn hay server React vẫn báo đủ. Đo thật trên React với Be Vietnam Pro: tab W-10 cao 45 px (receipt ghi 44), hàng tài liệu W-10 rộng 358 px (ghi 332),
padding hàng 16px 0 (ghi 16), h2 tự kiểm tra W-08 weight 600 (ghi 700).

- Dùng ảnh/JSON điều phối đã đo (run font thương hiệu và run fallback **tách riêng**, không trộn font/số đo giữa hai run). Ghi đúng commit, URL lấy từ
  receipt thật (URL `c1/m1/n1` đang khai không khớp runtime: course_id là UUID, module là `module_001`), viewport, DPR, theme, motion, state, font, crop.
- Bỏ nhãn measured/actual cho hằng. Số suy từ source ghi rõ "inferred / CSS minimum" (min-height 44 không có nghĩa measuredHeight 44). Nếu script tuyên bố
  source không đổi thì phải thật sự trích, băm, so source, hoặc dẫn proof có SHA.
- Giữ CSS rect tách với kích thước PNG đã giải mã. Không gắn số đo fresh offline cho PNG online cũ; fallback đổi kích thước (ví dụ HTML W-10 cao 770 thay
  807), không tuyên bố bounding box không đổi.
- **Không sửa React** cho khớp số ghi nhầm; không sửa React chéo nhóm. Không mở Cloud Figma.
- Test hoặc guard của script phải **đỏ** khi số đo là hằng hoặc khi không có server React (chứng minh bằng phép phá), rồi xanh với số đo thật.

Commit WIP, cập nhật Trạng thái báo cáo, rồi mới sang bước 2.

## Bước 2 — mở rộng W-23

Từ hai cặp đã có dữ liệu thật, hoàn thiện bảng lệch theo spec/token; sửa mẫu nếu mẫu sai, ghi "báo web" nếu React sai (không tự sửa React). Mở rộng
W-08/09/10 ở 768 px, sáng/tối, bàn phím, reduced-motion, video ngắn theo W-23; thêm đối chiếu màn Người dùng/Nhật ký của W-17.1 (nhánh
`work/w17-admin-users-react`, chỉ đọc). Hai phương án UX còn mở (hai/ba tab, cách đặt câu hỏi) giữ là đề xuất, không tự đổi. Giữ mọi ảnh/video/JSON cũ;
không sửa tám tệp W-23 chưa theo dõi ở thư mục chung.

Browser: HTTP/auth/PostgreSQL thật với model/Mailer/media giả, DB UUID riêng trên `db-test`, 0 USD; dừng server và gỡ DB của chính bạn sau lượt.

## Bàn giao

Báo cáo W-23 cập nhật (Trạng thái, bảng lệch, bảng phá, lệnh, ảnh). Không ghép, không push.
