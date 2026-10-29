# Sổ tay subagent web WayFinder (web, lõi, thiết kế)

Đọc tệp này **trước** lời giao vé. Lời giao (`tmp/claude-tools/prompt-cai-<vé>.md`) nói làm gì; tệp này nói làm thế nào và các lỗi người trước đã vấp.
Luật gốc: `task/web/00-ke-hoach.md` mục "Luật chung của mọi vé", và `report/handoff-dieu-phoi-2026-10-18.md` mục 4 (lời giao mẫu) và mục 7 (luật bắt buộc).
Mâu thuẫn thì theo hai tệp đó. Từ 2026-10-29 Claude điều phối, nghiệm thu và ghép; bạn làm thay một trong ba nhóm người trước đây.

## 1. Không được

- Ghép vào main, push, sửa nhánh của thư mục chung `C:\Users\ngoco\Desktop\Doctoroadmap` (luôn ở main).
- Sửa tệp vé, `00-ke-hoach.md`, bàn giao điều phối, spec, ADR. Thấy spec sai hay thiếu thì ghi mục "Câu hỏi" trong báo cáo.
- Mở tập giữ lại: `d01-t01`, `d01-t02`, `document-data/test/`, `Desktop\d02-tap-khoa`, mọi `khoa.jsonl`; in phần `cache` của `artifacts/phase_b/live.json`.
- Gọi nhà cung cấp mô hình, Cloudinary thật, SMTP thật. Mọi vé web là 0 USD; test dùng đồ giả/phát lại.
- Junction, symlink, hardlink vào `artifacts` hay dữ liệu. Không xoá/dọn worktree, artifact, PDF, ZIP, snapshot, DB của người khác. Không đụng
  `tmp/t01a-clean-ff797eb`.
- `git add -A`, `git add .`, `git reset`, `git stash`, `git checkout -- <tệp>`, `git restore` trên tệp không phải của bạn.
- Áp migration hay CLI vào DB dùng chung (`wayfinder` dev). Test dùng DB UUID riêng trên dịch vụ `db-test`.

## 2. Nhận việc khi đã có người làm dở

1. `git -C tmp/<tên> log --oneline main..HEAD`, `git -C tmp/<tên> status --short`, `git -C tmp/<tên> diff --stat`.
2. Đọc báo cáo vé, nhất là dòng **Trạng thái** và mục Câu hỏi.
3. Thay đổi chưa commit là việc dở chưa ai soát: giữ phần đúng, sửa phần sai, ghi vào báo cáo.

## 3. Lưu dần

- Commit WIP sau mỗi bước có test xanh, chỉ đường dẫn của mình: `git commit -m "wip(web): ..." -- <tệp> <tệp>`.
- Cập nhật dòng `**Trạng thái:**` đầu báo cáo sau mỗi bước: xong gì, đang làm gì, bước kế. Người nối tiếp chỉ cần dòng đó.
- Số đo, phản chứng, câu hỏi ghi vào báo cáo ngay khi có.

## 4. Môi trường (Windows, Git Bash)

- Worktree đúng **một cấp** dưới `tmp/`: `git worktree add -b work/<tên> tmp/<tên> main`, rồi `git -C tmp/<tên> config core.longpaths true`,
  `.venv/Scripts/python.exe -X utf8 tmp/claude-tools/copy_bundles.py tmp/<tên>` (phải in `bundles ok`), `mkdir -p tmp/<tên>/tmp`.
- Nhận main mới bằng `git merge --no-ff main` (không rebase). Kiểm mã thoát của merge, không nối qua ống; sau merge `git log -1` là commit merge.
- Python: `C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe`. Chạy test **từ gốc worktree** qua `scripts/w05_run_tests.py` (đặt `PYTHONPATH`
  vào worktree, bắt buộc PostgreSQL, thêm `-p no:cacheprovider`). Không chạy pytest trần: editable install nạp nhầm mã thư mục chung.
- Luôn có `--basetemp=tmp/pt-<tên-mới>`; mỗi lượt một tên mới. Thiếu thì gặp "Access is denied".
- PostgreSQL: container `wayfinder-db-test-1` phải healthy. Tắt thì báo Claude trong trả lời cuối; không tự khởi động DB khác.
- **RAM máy thấp, phiên đánh giá Pha A chạy song song.** Chỉ chạy test của vé, `src/web/backend/tests` (khi đụng backend) và test React. **Không chạy cả
  repo**; Claude chạy cổng toàn repo khi nghiệm thu.
- React: `npm ci` trong `src/web/frontend` của worktree; test `npx vitest run --pool=threads --maxWorkers=1`; build `npm run build`.
- **Ghi tệp bằng UTF-8.** Báo cáo W-17.1 React từng mất dấu tiếng Việt thành `?` vì ghi qua PowerShell mặc định. Dùng công cụ Write/Edit hoặc
  Python `encoding="utf-8"`; sau commit đọc lại `git show HEAD:<báo-cáo> | grep -c "?"` để soát.
- `git status` báo `M` mà `git diff` rỗng là chênh CRLF: không commit.

## 4b. Giao diện: bắt buộc áp dụng taste-skill (chủ dự án 2026-10-29)

Vé có React hay thiết kế **phải** áp dụng bộ taste-skill: đọc `SKILL.md` của `.agents/skills/design-taste-frontend` (chính) và skill hợp màn
(`minimalist-ui`, `high-end-visual-design`, `redesign-existing-projects`, `stitch-design-taste`…), cùng hướng đã chọn ở `.taste-skill/direction.json`
nếu có. Spec thiết kế, token, logo Artboard 9–28 và font Be Vietnam Pro đã chốt là căn cứ khi skill gợi ý khác. Báo cáo ghi tên skill và các đề xuất đã
áp dụng hay bỏ (kèm lý do).

## 5. Bằng chứng

- Mỗi tiêu chí nghiệm thu là một test **đỏ trước** trên bản sai (assertion fail, không phải setup error), rồi xanh. Ghi lệnh, mã thoát, số test vào báo cáo.
- Bảng phá: chụp bytes trước mỗi phép phá (`goc = p.read_bytes()`), khôi phục bằng `p.write_bytes(goc)` trong `finally`, đối chiếu SHA. Phép sống sót
  nghĩa là thiếu test: thêm test cho nó đỏ, hoặc ghi rõ vì sao tương đương.
- Claude sẽ chạy bộ phá **độc lập**. Test phải bắt hành vi quan sát được (HTTP, SQL độc lập, DOM), không nhắc lại cờ mã vừa gán.
- Điểm cuối mới: kèm ví dụ JSON thật trong báo cáo. Vé có giao diện: ảnh 390/768/1280, sáng/tối, có bàn phím và reduced-motion; ghi rõ ảnh nào thuộc lượt
  nào, commit nào. Số đo phải đến từ DOM/render thật, không điền hằng.
- Báo cáo ở `report/<vé>-<ngày>.md`, ngắn: phạm vi, lệnh đã chạy, số test, bảng phá, giới hạn, câu hỏi.

## 6. Kết thúc

1. Commit cuối; chạy lại test của vé **sau commit**, dán dòng tổng kết vào báo cáo.
2. `git status` sạch (trừ chênh CRLF).
3. Dòng Trạng thái: "xong, chờ nghiệm thu".
4. Trả lời cuối thật ngắn: nhánh, commit đỉnh, số test, bảng phá tóm tắt, câu hỏi.
