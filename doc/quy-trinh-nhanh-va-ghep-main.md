# Quy trình nhánh và ghép vào main

**Ngoại lệ tạm thời do chủ dự án quyết định 2026-10-24 — đồng bộ bằng commit local:**

> tạm thời k cần push lên main, commit đồng bộ mới nhất ở đây là đc, viết vô điều phối giao tiep đây là quyết định của tôi

Tạm thời dừng bước push main lên GitHub; commit phần đã nghiệm thu và hồ sơ mới nhất trên máy. Chỉ tiếp tục push khi chủ dự án yêu cầu. Ngoại lệ này ưu tiên hơn mục1.2, mục3.6 và mọi lời nhắc tự đẩy sau mỗi lần ghép bên dưới. Các điều kiện soát mã, nhận main local mới nhất, đúng commit, cổng test xanh, không force/rebase và bảo vệ dữ liệu vẫn giữ nguyên. Người điều phối ghi trạng thái local/remote thật trong bàn giao, không ghi đã đẩy khi chưa đẩy.

**Áp dụng từ** 2026-10-20 cho mọi làn: web, lõi, Pha B, thiết kế, phiên pha A, điều phối.
**Nguồn:** người điều phối báo repo chưa có quy định ghép vào main. Claude kiểm hiện trạng (mục 2) và chủ dự án chốt ba điểm (mục 1).

## 1. Quyết định của chủ dự án (2026-10-20)

1. **Người ghép vào main là người điều phối đương nhiệm:** Codex trong lúc Claude vắng, Claude khi tiếp nhận lại. Người làm vé không tự ghép.
   **Cập nhật 2026-10-22, chủ dự án chốt:** chia theo làn. **Claude ghép các nhánh Pha B** (vé SA) sau khi nghiệm thu; **người điều phối ghép phần web**.
   Hai người cùng ghép vào main, nên:
   - ghép ở thư mục chung, mỗi lần một lệnh. Gặp `index.lock` thì chờ, không xoá tệp khoá;
   - trước khi ghép, kiểm `git log -1 main`. Main có commit mới kể từ lúc chạy cổng thì quay lại mục 3.5 điều 2: nhánh nhận main, chạy lại cổng;
   - ghép xong đẩy ngay, để người kia nhận được main mới.
2. **Đẩy `main` lên GitHub sau mỗi lần ghép** (`origin`, repo riêng tư).
3. **Thư mục chung `C:\Users\ngoco\Desktop\Doctoroadmap` luôn đứng ở `main`.** Mỗi vé làm trong một worktree riêng `tmp/<tên>`. Chủ dự án mở phiên
   nhân viên ngay trong thư mục worktree đó.

## 2. Vì sao cần (hiện trạng ngày 2026-10-20)

- **Việc đã đạt chưa vào main:** W-02 và W-05 (đạt 2026-10-20) nằm ở nhánh `work/w02-accounts`. Nhánh mới tách từ main sẽ thiếu tài khoản và kho
  PostgreSQL.
- **Commit lạc nhánh:** thư mục chung đứng ở nhánh vé từ tối 2026-10-19, nay là `work/w03-email-recovery`. Ai commit ở đó cũng rơi vào nhánh vé:
  `fa49005` (bàn giao điều phối) và `781415b` (thiết kế W-24) đang nằm trên nhánh W-02.
- **Commit cuốn tệp của người khác:** hai commit thiết kế `7baa7d2` và `ba73cfc` mang theo 12 tệp vé, kế hoạch, bàn giao mà người điều phối đang sửa
  dở. `7baa7d2` còn mang theo hai báo cáo hoàn tất W-13.
- **Hồ sơ điều phối chưa commit:** 6 báo cáo `report/dieu-phoi-*.md` chưa được git theo dõi; 9 tệp vé và bàn giao đang sửa dở, nằm chung thư mục với
  mã W-03 đang làm.
- **Chưa có bản sao ngoài máy:** `origin/main` dừng ở 2026-08-22; `main` trên máy hơn 340 commit.
- **Test trong worktree dễ nhầm mã** (mục 3.3).
- **`document-data/` chưa có trong `.gitignore`,** mà thư mục này chứa tập giữ lại `document-data/test/`. Một lệnh `git add -A` sẽ cuốn cả vào. Đã thêm
  vào `.gitignore` cùng commit với tài liệu này.

## 3. Luật

### 3.1 Main chứa gì

- **Việc đã được soát độc lập là đạt:** cột trạng thái của bảng kế hoạch ghi "đạt" hay "đạt có ghi chú", và báo cáo soát ghim commit. Vé dài được ghép
  theo mốc khi người soát ghi rõ mốc nào đạt, tức một commit cụ thể.
- **Tài liệu:** spec, ADR, vé, bảng kế hoạch, bàn giao, báo cáo điều phối và nghiên cứu. Những tệp này commit thẳng lên main ở thư mục chung.
- **Không bao giờ:** mã đang làm, hay việc tự nghiệm thu mà chưa ai soát.

### 3.2 Nhánh và worktree

- **Một vé một nhánh,** tên `work/<mã vé chữ thường>-<tên ngắn>`, ví dụ `work/w03-email-recovery`, `work/sa52-focus-node`. Vé sửa sau soát (W-24 trở
  đi, SA-46 trở đi) cũng có nhánh riêng.
- **Tạo từ main mới nhất,** chạy ở thư mục chung:

  ```text
  git worktree add tmp/<tên> -b work/<tên> main
  ```

  Worktree phải nằm đúng một cấp dưới `tmp/` (thư mục git đã bỏ qua), vì runner test tìm `.env` của thư mục chung theo vị trí này.
- **Vé cần mã của một vé chưa ghép:** tách nhánh từ nhánh của vé đó (`-b work/<tên> work/<vé-kia>`), ghi "nhánh gốc" trong báo cáo vé. Chỉ ghép sau
  khi vé kia đã ghép.
- **Lần đầu vào worktree:** chạy `npm.cmd --prefix src/web/frontend ci`. Worktree không có `.env`. Test lấy cấu hình qua runner. Cần chạy máy chủ dev
  thì chép `src/web/.env` từ thư mục chung sang; `.env` đã bị bỏ qua nên không bao giờ vào commit.
- **Không ai đổi nhánh của thư mục chung.** Thấy nó không ở main thì báo người điều phối, không tự `git switch`.
- **Không bao giờ nối `artifacts` của thư mục chung vào worktree** bằng junction, symlink hay `mklink`. Gỡ một worktree có liên kết như vậy sẽ xoá
  luôn dữ liệu gốc. Sự cố 2026-10-20: toàn bộ artifact của doc-1 và doc-6 trong kho dùng chung thành rỗng đúng lúc gỡ một worktree. Dữ liệu phát
  triển chỉ được **chép** vào worktree, chép đúng cuốn cần dùng, và ghi danh sách SHA-256 của các tệp đã chép.
- **Trước khi gỡ bất kỳ worktree nào**, chạy `cmd /c "dir /AL /S /B <đường dẫn worktree>"`. Lệnh in ra gì là còn liên kết. Gỡ từng liên kết bằng
  `cmd /c rmdir <đường dẫn liên kết>`: lệnh này chỉ gỡ liên kết, không đụng thư mục đích. Sau đó chạy lại lệnh `dir` và phải không in gì, rồi mới gỡ
  worktree. Không bao giờ xoá đệ quy một thư mục còn liên kết.

### 3.3 Test trong worktree

- `.venv` cài lõi kiểu editable, trỏ vào `src/` của **thư mục chung**. Chạy python của `.venv` trong worktree sẽ nạp `doc2roadmap` và `wayfinder` của
  thư mục chung, không phải của worktree; Claude đã thử ngày 2026-10-20 ở `tmp/w05-postgres`. Vì thế chạy pytest trần trong worktree là test nhầm mã, mà
  kết quả vẫn có thể xanh.
- **Luôn chạy qua runner,** từ gốc worktree:

  ```text
  C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py <tham số pytest>
  ```

  Runner đặt `PYTHONPATH` vào `src/` của worktree, bắt buộc có PostgreSQL (`--require-postgres`) và thêm `-p no:cacheprovider`.

### 3.4 Commit

- **Chỉ đường dẫn của mình:** `git add -- <tệp>` rồi `git commit -m "…" -- <tệp>`. Không bao giờ dùng `git add -A`, `git add .` hay `git commit -a`.
- **Người làm vé** commit mã, test, báo cáo vé và bằng chứng của vé lên nhánh của vé. Họ không sửa tệp vé, bảng kế hoạch hay bàn giao. Điều cần ghi thì
  ghi trong báo cáo vé; spec sai hay thiếu thì ghi ở mục "Câu hỏi".
- **Người điều phối và Claude** sửa tệp vé, bảng kế hoạch, bàn giao và báo cáo điều phối ở thư mục chung, rồi commit thẳng lên main sau mỗi đợt.
- **Không bao giờ commit:** `.env`, `artifacts/`, `tmp/`, `document-data/`, tệp của tập giữ lại.

### 3.5 Điều kiện ghép

Người điều phối kiểm đủ sáu điều:

1. **Đã soát đạt:** cột trạng thái ghi "đạt" hay "đạt có ghi chú", và báo cáo soát ghim commit.
2. **Đã nhận main mới nhất:** trong worktree chạy `git merge main`, không rebase. Có xung đột thì người làm vé gỡ trên nhánh. Lần nhận main nào làm đổi
   mã của vé thì người soát xem lại phần đổi đó.
3. **Đỉnh ghép đúng mốc soát:** sau mốc soát mà còn commit mã thì chỉ ghép tới mốc (`git merge --no-ff <hash mốc>`). Phần sau chờ soát.
4. **Cổng test xanh** trên đúng đỉnh sẽ ghép, chạy ở worktree:

   ```text
   C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-<tên> --junitxml=tmp/cong-<tên>.xml
   npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
   npm.cmd --prefix src/web/frontend run build
   ```

   - Lệnh đầu không truyền đường dẫn test, nên chạy cả `tests/` lẫn `src/web/backend/tests/`, có PostgreSQL bắt buộc và kiểm Alembic đúng một head.
     Mốc 2026-10-19 là 2.062 test, khoảng 6 phút.
   - Gặp `WinError 5` (Access is denied) thì chạy lại cả vòng với `--basetemp` mới và ghi cả hai lần. Lặp lại thì coi là đỏ.
5. **Đúng phạm vi:** `git diff --stat main...<đỉnh>` chỉ gồm đường dẫn của vé và báo cáo vé. Không có tệp của phiên pha A, trừ vé được phép như W-05 và
   W-13. Không có tệp nào trong danh sách "không bao giờ commit" ở 3.4.
6. **Migration:** vé thêm bảng thì có đúng một bản di trú của vé, `down_revision` nối head hiện tại của main. Không sửa di trú đã ở main.

Main có commit mới sau lúc chạy cổng (chẳng hạn vừa ghép vé khác) thì quay lại điều 2.

### 3.6 Cách ghép

Ở thư mục chung (đang ở main):

```text
git merge --no-ff <nhánh hoặc hash mốc> -m "merge(W-xx): <tên vé> — đạt <ngày>, soát report/<tệp soát>.md"
git push origin main
```

- **Không rebase, không squash, không `push --force`.** Báo cáo soát trích mã commit, viết lại lịch sử là mất bằng chứng.
- **Sau khi ghép:**
  - ghi một dòng ở mục 10 của bàn giao: vé, hash commit ghép, kết quả cổng test (số đạt, số bỏ qua), đã đẩy;
  - cột trạng thái của bảng kế hoạch: "đạt · đã ghép `<hash>`";
  - dọn: `git worktree remove tmp/<tên>`, rồi `git branch -d work/<tên>`. Phải gỡ worktree trước, vì git không xoá nhánh đang mở ở một worktree.

### 3.7 Khi main đỏ

- **Revert commit ghép, không sửa nóng trên main:** chạy `git revert -m 1 <hash ghép>` rồi đẩy. Mở lại vé và báo chủ dự án, theo mục 6 của bàn giao.
- **Ghép lại sau khi sửa:** revert chính commit revert trước, rồi mới ghép nhánh sửa. Bỏ bước này thì git coi phần cũ đã ghép rồi và bỏ qua nó.

### 3.8 Phiên pha A

Cùng luật. Phiên pha A trước đây commit thẳng lên main; từ nay mỗi việc là một nhánh `work/a-<tên>` trong worktree riêng. Các worktree tách rời cũ của
phiên pha A trong `tmp/` (`t01b/…`, `v4-05b/ma`, `v4-19l/ma`, `pha-b-doc6/ma`, `t01a-clean-ff797eb`) giữ nguyên tới khi chủ dự án cho dọn.

## 4. Đợt ghép bù 2026-10-20 (người điều phối làm một lần)

Claude đã thử trước bằng `git merge-tree`, không đụng thư mục làm việc nào:
- ghép `8558df4` vào main không có xung đột;
- sau đó nhánh W-03 nhận main mới cũng không có xung đột;
- 9 tệp điều phối đang sửa dở giống hệt nhau ở hai phía, nên việc đưa thư mục chung về main không bị chặn;
- không có tệp chưa theo dõi nào trùng đường dẫn với tệp mà main mang vào.

0. **Dừng thư mục chung.** Báo mọi phiên đang làm ở thư mục chung dừng lại. Phiên W-03 commit phần mã dở lên `work/w03-email-recovery`, chỉ gồm tệp mã,
   test và báo cáo của W-03. Không commit `task/`, `report/handoff-dieu-phoi-2026-10-18.md` hay `report/dieu-phoi-*.md`: đó là tệp điều phối đang sửa
   dở.
1. **Ghép W-02/W-05 trong worktree tạm.** Main chưa được mở ở đâu nên làm được:

   ```text
   git worktree add tmp/ghep-main main
   cd tmp/ghep-main
   git merge --no-ff 8558df4 -m "merge(W-02, W-05): tài khoản, phiên, CSRF và kho Pha B trên PostgreSQL — đạt 2026-10-20, soát report/dieu-phoi-nghiem-thu-w02-w05-w24-2026-10-20.md"
   ```

   - **Vì sao ghép tới `8558df4` mà không tới đỉnh `work/w02-accounts`:** lần soát ghim `63256e0`; bản UI soát thêm khớp đúng `8558df4` (Claude đã
     đối chiếu băm tệp với manifest soát). Hai commit sau đó chưa ai soát: `781415b` (thiết kế W-24) và `79cb9c9` (sửa giao diện W-02). Cả hai đã nằm
     trong nhánh W-03 nên sẽ được soát cùng W-03; riêng `781415b` cần thêm phán xét W-24 trước khi ghép W-03.
   - Chạy cổng test ở điều 4 mục 3.5 trong `tmp/ghep-main`; lần đầu cần `npm.cmd --prefix src/web/frontend ci`. Đỏ thì dừng, báo Claude và chủ dự án,
     chưa đẩy.
   - Xanh thì về thư mục chung và gỡ worktree tạm: `git worktree remove tmp/ghep-main`.
   - **Không cần ghép `review/w13-complete-2026-10-19`.** Các tệp báo cáo của nhánh đó đã lên main với nội dung y hệt, qua `7baa7d2`. Tệp vé W-13 thì
     bản main mới hơn: trạng thái "đạt nghiệm thu" của điều phối đã thay dòng "chờ soát độc lập" của nhánh. Nhánh được xoá ở bước 6.
2. **Đưa thư mục chung về main:** `git switch main`. Git báo chặn thì dừng. Không dùng `--force`, không `git stash`: ngăn stash dùng chung cho mọi
   worktree, nên dễ lấy nhầm của phiên khác.
3. **Commit hồ sơ điều phối lên main,** đúng đường dẫn: tệp bàn giao, `task/web/00-ke-hoach.md`, bảy tệp vé đang sửa và sáu `report/dieu-phoi-*.md`.
   Thêm luôn các dòng trỏ ở mục 5.
4. **Chuyển W-03 sang worktree:**

   ```text
   git worktree add tmp/w03-email-recovery work/w03-email-recovery
   ```

   Chủ dự án mở lại phiên W-03 trong `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w03-email-recovery`. Trong đó chạy `git merge main` (đã thử: không xung
   đột) và `npm.cmd --prefix src/web/frontend ci`; chép `src/web/.env` nếu cần chạy máy chủ dev.
5. **Đẩy lên GitHub:** `git push origin main`. Lần đầu mang theo hơn 340 commit. Claude đã quét phần chưa đẩy:
   - không thấy khoá thật; hai chỗ khớp mẫu là URL giả trong test và một chỗ giữ chỗ trong spec;
   - không có đường dẫn của tập giữ lại;
   - tệp lớn nhất 7 MB, dưới giới hạn của GitHub.
6. **Dọn nhánh và worktree đã ghép:**
   - kiểm nhánh biên bản W-13. Lệnh sau phải không in gì:
     `git diff --stat main review/w13-complete-2026-10-19 -- report/w13-doc6-ket-qua-2026-10-19.json report/w13-doc6-kiem-cache-va-de-nghi-chi-2026-10-19.md report/w13-dung-mot-cuon-2026-10-19.md report/w13-hoan-tat-doc6-2026-10-19.md tasks/todo.md`.
     Không in gì thì xoá: `git branch -D review/w13-complete-2026-10-19`;
   - với từng worktree `tmp/w05-core` và `tmp/w05-postgres`: `git -C tmp/<tên> status --short` không in gì thì `git worktree remove tmp/<tên>`. Sau đó
     xoá hai nhánh: `git branch -d work/w05-core work/w05-postgres`;
   - nhánh `work/w02-accounts`: `git merge-base --is-ancestor work/w02-accounts work/w03-email-recovery` thành công thì
     `git branch -D work/w02-accounts`. Hai commit chưa soát của nhánh này đã nằm trong W-03;
   - không đụng các worktree của phiên pha A, cũng không đụng hai worktree `ve-04-bo-vang`, `ve-05-bo-cham` trong thư mục tạm cũ của Claude, khi chưa
     hỏi chủ dự án.
7. **Ghi nhật ký:** một dòng ở mục 10 của bàn giao. Cột trạng thái của W-02 và W-05 ghi "đạt · đã ghép `<hash>`".

## 5. Dòng trỏ cần thêm (người điều phối, ở bước 3 của mục 4)

- **Bàn giao mục 4, lời giao mẫu:** thêm vào phần "Luật bắt buộc":

  > - Làm trong worktree `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\<tên>`, nhánh `work/<tên>`, theo `doc/quy-trinh-nhanh-va-ghep-main.md`. Không làm ở
  >   thư mục chung, không đổi nhánh của nó.
  > - Chạy test qua `scripts/w05_run_tests.py` từ gốc worktree, không chạy pytest trần.
  > - Không tự ghép vào main. Không sửa tệp vé, bảng kế hoạch hay bàn giao; điều cần ghi thì ghi trong báo cáo vé.

- **Bàn giao mục 7:** thay dòng **Git:** bằng:

  > **Git:** theo `doc/quy-trinh-nhanh-va-ghep-main.md`. Thư mục chung luôn ở main; mỗi vé một nhánh trong worktree `tmp/<tên>`. Chỉ người điều phối
  > ghép, bằng `--no-ff`, sau khi vé được soát đạt và cổng test xanh. Đẩy main lên GitHub sau mỗi lần ghép. Chỉ commit đường dẫn của mình. Không sửa
  > tệp của phiên pha A.

- **`task/web/00-ke-hoach.md`, Luật chung:** thêm sau dòng "Commit chỉ đường dẫn của vé":

  > - **Nhánh và ghép vào main:** theo [quy trình nhánh và ghép main](../../doc/quy-trinh-nhanh-va-ghep-main.md).

- **`task/sau-a10/00-ke-hoach.md`:** Claude đã thêm trong cùng commit với tài liệu này.
