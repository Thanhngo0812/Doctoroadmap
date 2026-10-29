# Lời giao subagent web — sửa W-17.1 React sau nghiệm thu lần 13 (WEB-R13-01…03)

Bạn là subagent web của dự án WayFinder. Đọc theo thứ tự rồi mới làm:
1. `tmp/claude-tools/so-tay-agent-web.md` (sổ tay, luật cấm, môi trường, bằng chứng).
2. Biên bản `report/dieu-phoi-nghiem-thu-lan13-2026-10-29.md` trên main (mục Required).
3. Báo cáo nhóm web `report/w17-react-tich-hop-2026-10-29.md` trên nhánh dưới đây.

Tiếp nhánh **`work/w17-admin-users-react`** trong worktree có sẵn **`tmp/w17-admin-users-react`** (của nhóm web trước, nay bạn nối tiếp). Không tạo nhánh
mới. Trước hết nhận main mới: `git -C tmp/w17-admin-users-react merge --no-ff main`, kiểm mã thoát.

Mã React đã đúng ở cả ba điểm dưới; việc là thêm test giữ bất biến và sửa báo cáo. **Không đổi hành vi `Admin.tsx`** trừ khi test mới chứng minh sai; nếu
đổi thì ghi lý do trong báo cáo.

## Required

- **WEB-R13-01 — báo cáo mất dấu.** Từ mục "Lượt tích hợp b75e611b…" tới hết, chữ tiếng Việt trong blob Git đã thành `?` (23 dòng). Viết lại các mục đó
  bằng UTF-8 với cùng nội dung và số liệu (đọc số từ JSON/JUnit/exit.json trong `report/w17-react-evidence/`, không đoán). Sau commit:
  `git show HEAD:report/w17-react-tich-hop-2026-10-29.md | grep -c "?"` chỉ còn dấu hỏi thật của câu hỏi, không còn chữ hỏng. Giữ `report/.gitattributes`
  `eol=lf` cho tệp này. Nếu manifest băm báo cáo thì cập nhật đúng SHA mới.
- **WEB-R13-02 — múi giờ lọc nhật ký không có test.** Phép phá của Claude đổi `new Date(value+'+07:00')` thành `new Date(value+'Z')` (lệch 7 giờ) mà
  281 test vẫn xanh. Thêm test: nhập "Từ"/"Đến" giờ Việt Nam trên `/admin/nhat-ky`, kiểm query gửi đi là UTC đúng (ví dụ 10:00 giờ Việt Nam →
  `03:00:00.000Z`), và ô nhập hiện lại đúng giờ Việt Nam khi tải trang có `since`/`until` UTC trên URL. Test phải đỏ trên phép phá trên.
- **WEB-R13-03 — PATCH bị 403 không có test gỡ dữ liệu.** Phép phá tắt nhánh `forbidden` trong `fail` (rơi xuống `setError`) vẫn xanh, vì test GET 403
  chỉ tìm chữ "Bạn không có quyền quản trị." — chữ này trùng giữa màn Denied và thông báo lỗi. Thêm test: bảng đã tải, mở sửa một tài khoản, PATCH trả 403
  `forbidden` → bảng và hộp thoại biến mất, hiện màn Denied (ví dụ có link "Về khoá học của tôi", không còn bộ lọc/nút Tải lại), không còn email nào của
  bảng cũ. Sửa test GET 403 hiện có để cũng phân biệt Denied với thông báo lỗi. Hai test phải đỏ trên phép phá trên.

Ghi bảng phá vào báo cáo: hai phép phá ở trên (chép đúng chuỗi thay thế), mỗi phép bị bắt bởi test nào, khôi phục bytes và SHA. Chạy
`npx vitest run src/Admin.test.tsx` rồi toàn bộ test React và `npm run build`. Không cần browser mới, không chạy test Python (không đụng backend).

## Optional (ghi vào báo cáo, không bắt buộc sửa)

Trên ảnh `first-admin-768-dark.png`, hai ô chọn bị khoá cho admin đầu tiên trông gần như ô đang bật (chỉ khác màu chữ). Nếu sửa CSS thì giữ tương phản
≥ 4,5:1 và kèm ảnh mới sáng/tối.

## Bàn giao

Cập nhật đầu báo cáo `report/w17-react-tich-hop-2026-10-29.md` một mục "Sửa sau nghiệm thu lần 13" (lệnh, số test, bảng phá, commit). Dòng Trạng thái:
"xong, chờ nghiệm thu". Không ghép, không push.
