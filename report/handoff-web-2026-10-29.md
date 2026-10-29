# Bàn giao điều phối web WayFinder — 2026-10-29

**Trạng thái:** viết tối 2026-10-29 bởi Claude (người điều phối web từ 29/10). Đang dừng giữa **nghiệm thu lần 15 (W-17.2)** theo lời chủ dự án
("khoan chạy toàn test… ngưng lát về làm tiếp"). Máy chủ demo **đang tắt** (Docker Desktop tắt). Main local `96515f08` + commit bàn giao này.

Tài liệu này đủ để một người hay một agent khác tiếp tục điều phối phần web mà không cần đọc lại cuộc trò chuyện. Bàn giao chung cũ
([handoff-dieu-phoi-2026-10-18.md](handoff-dieu-phoi-2026-10-18.md)) giữ làm lịch sử Pha B và các lần nghiệm thu 1–12 của Codex; phần web hiện hành
lấy tệp này làm chuẩn. Công cụ và lời giao của điều phối nằm trong `tmp/claude-tools/` (thư mục `tmp/` bị Git bỏ qua), nên bản sao để dùng ở máy khác
nằm cạnh tệp này: [handoff-web-2026-10-29/](handoff-web-2026-10-29/) (mục 15).

**Đọc theo thứ tự:** mục 0 → 1 → 4 → 5, rồi các mục khác khi cần.

---

## 0. Đọc nhanh

- **Web đã chạy được đầu-cuối:** đăng ký/đăng nhập/xác minh mail, hồ sơ, khoá học, lộ trình, bài giảng, trợ lý, quiz, tài liệu, chia sẻ, mời qua mail,
  tải sách và dựng thật, mức dùng, quản trị Người dùng/Nhật ký. Vé đã đạt: W-01…W-16, W-22, W-24, W-25, W-26 và mốc W-17.1 (mục 3).
- **Đang dở:** nghiệm thu W-17.2 (API danh sách bản dựng và bật/tắt khoá mẫu cho admin). Đã đọc diff, bộ phá của Claude chạy 6/8 phép, một phép sống
  sót → cần một vòng sửa test nhỏ rồi chạy cổng, ghép (mục 4).
- **Hàng đợi:** W-17.2 → W-27 mốc 1 (lõi) → D-R12-01/W-23 (thiết kế) → W-27 mốc 2 (web) → phần còn lại W-17 → W-18, W-19, W-20 → W-final (mục 5).
- **Ba câu đang chờ chủ dự án** về W-17.2 (mục 6). Không câu nào chặn việc sửa test.
- **Cách làm:** Claude soạn lời giao, tạo **một** subagent Sonnet mới cho mỗi việc (không tái dùng agent cũ), nghiệm thu bằng bộ phá độc lập, chạy cổng,
  ghép `--no-ff` vào main local (mục 10, 11).
- **Cấm tuyệt đối:** mở tập giữ lại; chi tiền khi chủ dự án chưa duyệt; dán bí mật; commit tệp của phiên khác; migrate DB dùng chung `wayfinder` (mục 12).

## 1. Bối cảnh và vai trò

| vai | ai | làm | không làm |
|---|---|---|---|
| chủ dự án | chủ dự án | duyệt tiền, chốt thiết kế và phạm vi, cấp khoá (Gmail, Vertex, Cloudinary) | |
| điều phối web | **Claude từ 2026-10-29** (Codex 2026-10-18…28) | soạn vé và lời giao, tạo subagent, nghiệm thu, ghép main, giữ nhật ký | tự viết mã sản phẩm, duyệt tiền, đổi spec/ADR khi chủ dự án chưa chốt |
| subagent web / lõi / thiết kế | agent Sonnet do điều phối tạo, **từng cái một** | làm một vé theo lời giao và sổ tay | ghép main, push, sửa vé/kế hoạch/bàn giao, chạy lượt có tiền |
| phiên Pha A (đánh giá) | phiên Claude khác, chạy song song trên cùng máy | `evaluation/`, `tests/evaluation/`, worktree `tmp/dg-*`, commit `*(eval)` | |

Từ 2026-10-29 ba subagent thay ba nhóm người (web, lõi, thiết kế). Luật cũ giữ nguyên, áp cho subagent như cho người.

### Quyết định của chủ dự án còn hiệu lực

| ngày | quyết định | nguồn |
|---|---|---|
| 18/10 | mã web ở `src/web/`; PostgreSQL trong Docker; Gmail SMTP; khoá mẫu chỉ ở dev; bản demo ai cũng tải sách được | spec chức năng, cuối tài liệu |
| 19/10 | web **tạm dùng Vertex AI** (không Gemini Developer API) | `task/web/00-ke-hoach.md`, luật chung |
| 22/10 | giữ Vertex tới gần buổi demo (~12/11) rồi mới đổi Developer API, và chỉ khi chủ dự án yêu cầu | bộ nhớ, mục 7.5 |
| 24/10 | bỏ Cloud Figma; thiết kế bàn giao HTML/CSS/token, web làm React | kế hoạch web |
| 28/10 | "admin đầu tiên ko đc khóa hay gì": không khoá/hạ quyền/xoá admin đầu tiên | [ADR 0030](../doc/adr/0030-bao-ve-tai-khoan-admin-dau-tien.md) |
| 29/10 | Claude điều phối; ba subagent; chạy **từng agent một**; xong việc **thay agent mới** ("nhớ subagent xong việc đổi đừng để nó đầy context") | cuộc trò chuyện 29/10 |
| 29/10 | agent làm React hay thiết kế **bắt buộc áp dụng taste-skill** | sổ tay mục 4b |
| 29/10 | nghiệm thu W-17.1 bằng **cổng rút gọn** (React + build + bộ phá + `src/web/backend/tests`) khi main chỉ đổi phần đánh giá | biên bản lần 13 |
| 29/10 | máy chủ demo local chạy thật: **mọi tài khoản** tải và dựng được ("sao ko phải là tài khoản nào cũng up đc"); không Cloudinary; mail thật; trần học cá nhân **3 USD/người/ngày** | vé W-26 |
| 29/10 | **bỏ W-21**: "tôi chỉ cần 1 src dựng trên máy rồi demo th, ko cần cái deploy w21 đâu" | kế hoạch web |
| 29/10 | **W-final** làm sau cùng: gói thư mục ngoài Desktop chỉ có mã + dữ liệu tối thiểu + README + một lệnh bật | vé W-final |
| 29/10 | lý do xếp hàng khi hết trần ngày phải hiện trên web: "có làm viết vé thêm" → W-27 | biên bản lần 14 |
| 29/10 | giữ `retry_unknown_within_cap=True` cho bản dựng demo: "ko sao cứ giữ vậy" | biên bản lần 14 |
| 29/10 | tối: tạo bàn giao chi tiết rồi **push mã web và bàn giao lên GitHub** (thay quyết định 24/10 "chỉ commit local") | cuộc trò chuyện 29/10 |

## 2. Git

- Thư mục chung `C:\Users\ngoco\Desktop\Doctoroadmap` **luôn ở `main`**. Mỗi vé một worktree `tmp/<tên>`, nhánh `work/<tên>`.
- Remote: `https://github.com/Thanhngo0812/Doctoroadmap.git`. **Repo đang ở chế độ công khai (PUBLIC)**; bộ nhớ cũ ghi "riêng tư" là sai.
- Lúc viết: `origin/main` = `5e19b9b3` (24/10); main local hơn 476 commit (web, Pha B, đánh giá Pha A, khoảng 1 GB bằng chứng gồm video `.webm` tới 54 MB).
  Trước khi push đã quét: không giá trị bí mật nào của `.env`/`src/web/.env` nằm trong cây mã hay trong 14 tệp zip đã commit; không đường dẫn tập giữ lại.
  Kết quả push ghi ở dòng trạng thái đầu tệp sau khi đẩy.
- Commit web/điều phối ngày 29/10 trên main:

| commit | nội dung |
|---|---|
| `3a0920b2` | Claude tiếp nhận điều phối web |
| `8e6f1fdf`, `ddb52df0` | nghiệm thu lần 13 lượt đầu (W-17.1 React chưa đạt) |
| `56c4b8c6`, `f71b694c` | vé W-26; bỏ W-21 |
| `e4465b4c` | **ghép W-17.1 React** (Người dùng/Nhật ký) |
| `e0bd4735` | biên bản lần 13 sau sửa |
| `5ecb7b49` … `8011ac37` | vé W-final và bẫy `.env` |
| `b94d4a88` | trạng thái trước compact |
| `843c07ef` | **ghép W-26 máy chủ demo local** |
| `a0c161ec` | biên bản lần 14 |
| `96515f08` | vé W-27, W-26 đạt, giữ `retry_unknown_within_cap` |

- Nhánh web **chưa ghép**: `work/w17-builds-samples-backend` (`cd198812`, W-17.2, đang nghiệm thu); `work/w23-paired-web-evidence` (`f9705f42`,
  W-23, chờ D-R12-01). Các nhánh `work/coord-*`, `coord/r14-w26-trial` là bản ghép thử của điều phối, không ghép.
- Tệp dở của phiên khác ở thư mục chung (không stage, không commit, không dọn): `report/ke-hoach-danh-gia-pha-a-2026-10-26.md`,
  `report/ket-qua-v3-05b-09b-11b-vertex-2026-09-28.md`, `scripts/thu-vertex/*.py`, `task/sau-a10/19-…`, `task/v3-lo-trinh-doc-duoc/19-…`, `uv.lock`,
  cùng nhiều thư mục chưa theo dõi (`.agents/skills/*`, `src/web/frontend/.taste-skill/`).

## 3. Trạng thái từng vé web

Chi tiết lịch sử ở [kế hoạch web](../task/web/00-ke-hoach.md). Bảng dưới là trạng thái hiện hành.

| vé | việc | trạng thái |
|---|---|---|
| W-01 | nền FastAPI + React + PostgreSQL + Alembic, token giao diện | đạt |
| W-02 | đăng ký, đăng nhập, phiên cookie, CSRF, giới hạn thử | đạt |
| W-03 | xác minh email, quên mật khẩu, cổng gửi thư | đạt |
| W-04 | hồ sơ, đổi mật khẩu, đăng xuất mọi nơi | đạt (React `f52466dc`, backend `c1f2fe9`) |
| W-05 | kho Pha B trên PostgreSQL | đạt |
| W-06 | khoá mẫu, Khoá học của tôi, `LearningGateway` | đạt |
| W-07 | lộ trình và tiến độ | đạt |
| W-08 | trang học, bài giảng `lecture-3` stream, đọc trang | đạt |
| W-09 | trợ lý và phiên chat (`answer-3`) | đạt |
| W-10 | quiz (`quiz-3`), tài liệu (`document-3`), thư viện | đạt |
| W-11 | chia sẻ bằng link, thành viên, rời khoá | đạt |
| W-12 | mời qua email, lời mời trong ứng dụng | đạt |
| W-13 | use case `build_document` ở lõi | đạt |
| W-14 | tải sách, xác nhận, hàng đợi, worker, ghi usage | đạt có ghi chú |
| W-15 | nối bộ dựng thật, đo USD/cuốn | đạt có ghi chú (billing chưa đối soát hoá đơn) |
| W-16 | trang mức dùng, dải hết trần | đạt |
| **W-17** | quản trị | **mở.** W-17.1 backend (`4e6f33cb`) + React Người dùng/Nhật ký (`e4465b4c`) đạt; **W-17.2 đang nghiệm thu**; còn tab Bản dựng/Khoá mẫu (React), Chi, log `lecture_validation`, retry/cancel của admin |
| W-18 | tiến độ thành viên cho chủ khoá | ready-for-agent, chưa giao |
| W-19 | báo lỗi nội dung | ready-for-agent, chưa giao |
| W-20 | xoá tài khoản, xoá khoá học (giữ ADR 0030: không xoá admin đầu tiên) | ready-for-agent, chưa giao |
| W-21 | triển khai, sao lưu | **bỏ** (29/10) |
| W-22, W-24 | bàn giao thiết kế HTML/CSS/token | đạt có ghi chú mốc web |
| **W-23** | đối chiếu React với spec/token/mẫu | **mở**, nhánh `f9705f42`, chờ sửa D-R12-01 (số đo React ghi sẵn) |
| W-25 | race xác nhận/huỷ bản dựng | đạt |
| **W-26** | máy chủ demo local chạy thật | **đạt**, ghép `843c07ef` (lần 14) |
| **W-27** | hiện lý do xếp hàng hết trần ngày trên web | ready-for-agent; mốc 1 lõi, mốc 2 web |
| **W-final** | gói bản chạy trên máy khác | chờ mọi vé khác; Claude viết lại chi tiết lúc làm |

Biên bản nghiệm thu do Claude viết: [lần 13](dieu-phoi-nghiem-thu-lan13-2026-10-29.md) (W-17.1 React),
[lần 14](dieu-phoi-nghiem-thu-lan14-2026-10-29.md) (W-26). Lần 1–12 do Codex viết, dẫn từ kế hoạch web.

## 4. Việc đang dở: nghiệm thu lần 15 — W-17.2

**Vé:** [W-17](../task/web/W-17-quan-tri.md), mốc 17.2. **Lời giao:** [prompt-cai-w17-2.md](handoff-web-2026-10-29/loi-giao/prompt-cai-w17-2.md).
**Nhánh:** `work/w17-builds-samples-backend`, worktree `tmp/w17-builds-samples-backend`, đỉnh `cd198812`, gốc main `96515f08` (bằng main hiện tại,
nên chưa cần nhận main). Báo cáo của subagent: `report/w17-2-builds-samples-backend-2026-10-29.md` trên nhánh.

**Subagent đã làm** (tự báo, Claude đã đọc diff thấy khớp):
- `GET /api/v1/admin/builds`: tìm `q` (doc_id, email người dựng, build_id), lọc `status`, `usage_complete`, `since`/`until` (nửa mở, phải có múi giờ),
  `limit` 1–100, `offset`, trả `total`. DTO chỉ có metadata; không `error_message` thô (lỗi trả văn bản cố định theo mã, mã lạ thành `khong_ro`),
  không tên tệp, không tiêu đề khoá, không `public_id`, không dữ liệu học.
- `PATCH /api/v1/admin/courses/{cid}` thân `{"is_sample": bool}` (`StrictBool`, `extra=forbid`): chỉ `env=dev`, chỉ khoá có `doc_id` thuộc sáu cuốn
  phát triển. Khoá ngoài danh sách trả **404** như khoá không có; `env≠dev` và "đã có khoá mẫu khác cùng doc_id" trả **409** `conflict` kèm `fields`.
  Khoá advisory `admin:samples` + `FOR UPDATE`; đổi thật thì ghi audit `admin_course_sample_set/unset` trong cùng giao dịch.
- Mã: `api/admin.py`, `application/admin.py`, `application/admin_ports.py`, `infrastructure/admin_store.py`, `src/web/openapi.json` (chỉ thêm).
  Không migration mới. Sửa hai test cũ để kho kiểm kê route chấp nhận route admin mới (`test_w17_admin.py`, `test_courses_w06.py`).
- Test: tệp mới `test_w17_builds_samples.py` 34 ca; toàn `src/web/backend/tests` 713 pass / 1 skip / 1 fail (ca fixture W-15, mục 9.3).
  Bộ phá của subagent 25/26 bắt (phép sống sót bỏ `FOR UPDATE`, tương đương vì đã có khoá advisory).

**Claude đã làm:** đọc toàn bộ diff; chạy 6/8 phép phá riêng trên `cd198812` (worktree `tmp/coord-r14-acceptance-20261029` đang detached ở đó).
Script và kết quả: [coord-r15-evidence-2026-10-29/mutations/](coord-r15-evidence-2026-10-29/mutations/).

| phép phá | kết quả |
|---|---|
| `q-email`: bỏ tìm theo email | bị bắt |
| `q-build-id`: bỏ tìm theo build_id | bị bắt |
| `course-count-all`: đếm mọi khoá thay vì khoá của bản dựng | bị bắt |
| `error-always`: luôn trả khối `error` kể cả khi không lỗi | bị bắt |
| `unset-conflict`: bỏ điều kiện `is_sample and` → bỏ cờ bị 409 sai khi có mẫu khác cùng doc_id | **sống sót** |
| `unset-action-name`: ghi audit `set` cho cả bỏ cờ | bị bắt |
| `since-before-until`: bỏ kiểm `since >= until` | **chưa chạy** — chuỗi cần thay khớp 2 chỗ trong `application/admin.py` (cả `list_audit`); sửa script cho chuỗi duy nhất |
| `requester-null`: luôn trả `requested_by=None` | **chưa chạy** |

**Còn phải làm, theo thứ tự:**
1. Sửa `pha_w17_2.py` (chép về `tmp/coord-r14-acceptance-20261029/tmp/coord-r15-mut/` hay worktree nghiệm thu mới), chạy hai phép còn lại.
2. Giao **một subagent lõi mới** (lời giao mới, theo mẫu `prompt-cai-w26-sua-r14.md`): **WEB-R15-01 (Required)** — test: khoá A không phải mẫu, khoá B
   cùng doc_id đang là mẫu, `PATCH A {"is_sample": false}` phải 200, không đổi DB, không ghi audit; phép `unset-conflict` phải bị bắt. Cộng mọi phép
   còn sống từ bước 1. Chỉ sửa test/bộ phá/báo cáo trên nhánh `work/w17-builds-samples-backend`.
3. Chạy lại 8 phép của Claude trên đỉnh mới; chạy cổng `src/web/backend/tests` trên đỉnh nhánh (đã gộp main nếu main đổi), **có fixture W-15** để
   xanh trọn (mục 9.3). React không đổi nên không chạy.
4. `bash tmp/claude-tools/ghep_guard.sh work/w17-builds-samples-backend <junit>` phải in `GUARD OK`; ghép `--no-ff` vào main.
5. Viết `report/dieu-phoi-nghiem-thu-lan15-2026-10-29.md` (hay ngày làm), chép bằng chứng vào `report/coord-r15-evidence-…`; cập nhật bảng W-17 trong
   kế hoạch web và dòng trạng thái của vé W-17; ghi spec (audit `admin_course_sample_set/unset`, hợp đồng hai điểm cuối) nếu chủ dự án đồng ý câu 3 mục 6.

## 5. Hàng đợi sau W-17.2

Chạy **từng subagent một**; mỗi việc một agent Sonnet mới, đọc sổ tay + lời giao. Lời giao chưa có thì Claude viết ở `tmp/claude-tools/` theo mẫu.

| thứ tự | subagent | việc | lời giao | ghi chú |
|---|---|---|---|---|
| 1 | lõi | **W-27 mốc 1**: trường `waiting` trong DTO bản dựng (lý do `daily_build_cap`, `resumes_at` 00:00 giờ Việt Nam), dùng chung hàm với worker, không lộ USD | **chưa viết** | vé [W-27](../task/web/W-27-ly-do-xep-hang-het-tran-ngay.md) |
| 2 | thiết kế | **D-R12-01** rồi mở rộng **W-23** | [prompt-cai-d-r12-01.md](handoff-web-2026-10-29/loi-giao/prompt-cai-d-r12-01.md) | tiếp nhánh `work/w23-paired-web-evidence`; taste-skill bắt buộc |
| 3 | web | **W-27 mốc 2**: câu chờ trên trang tiến trình và thẻ khoá học | chưa viết | taste-skill bắt buộc; sau mốc 1 đạt |
| 4 | web | **W-17 React** tab Bản dựng và Khoá mẫu theo API W-17.2 | chưa viết | taste-skill; dùng ví dụ JSON trong báo cáo W-17.2 |
| 5 | lõi | **W-17 phần Chi**: `spend_summary`, `system_caps_today`; log `lecture_validation` cho admin | chưa viết | receipt build không cộng trace `counted_in="build"`; ghi "ước theo token, không thay hoá đơn" |
| 6 | lõi + Claude | **W-17 retry/cancel của admin** | chưa viết | điểm treo từ Codex: `BuildService` đòi `require_upload`/`requested_by`; chốt port/route trước, không giả Actor người tải |
| 7 | web/lõi | W-18, W-19, W-20 | chưa viết | W-20 giữ ADR 0030 |
| 8 | lõi | **W-final** | Claude viết lại vé lúc đó | mục 7.9 |

Cloudinary không dùng ở máy chủ demo; thẻ "tín dụng Cloudinary" của W-17 cần chủ dự án quyết còn làm hay bỏ khi tới lượt.

## 6. Câu hỏi đang chờ chủ dự án

1. **W-17.2, mã lỗi khi máy chủ không ở dev:** giữ **409** để giao diện báo "chỉ có ở dev" (Claude đề nghị), hay 404 như lệnh nạp mẫu. Đã giải thích
   cho chủ dự án 29/10, chưa có trả lời; không chặn.
2. **W-17.2, tên tệp gốc và tiêu đề khoá trong danh sách bản dựng của admin:** đang ẩn vì là dữ liệu người dùng tự đặt. Claude đề nghị giữ ẩn; nếu cho
   xem thì sửa spec quyền riêng tư trước. Đã giải thích, chưa có trả lời.
3. **Spec cập nhật** hai loại audit `admin_course_sample_set/unset` và hợp đồng hai điểm cuối W-17.2 (spec mục 9/11, spec cơ sở dữ liệu cột `action`):
   Claude định ghi khi ghép, trừ khi chủ dự án muốn khác.
4. **Thẻ tín dụng Cloudinary** của W-17 (mục 5) khi demo không dùng Cloudinary.

## 7. Kiến trúc web

### 7.1 Thư mục

```
src/web/
  backend/wayfinder/        gói Python (FastAPI)
    api/                    router HTTP: auth, courses, learning, content, assistant, sharing, builds, admin, errors, openapi
    application/            use case: accounts, courses, learning_gateway, builds, build_worker, sharing, admin, seed_samples, ...
    domain/                 auth (Actor, decide), courses, sharing, file_paths (safe_path)
    infrastructure/         PostgreSQL store, mail, media (Cloudinary), disk_media (demo), real_build, build_spend, learning_runtime, ...
    fakes/                  đồ giả cho test (mail, media, build, assistant, lecture, quiz)
    migrations/versions/    Alembic
    cli.py, composition.py, settings.py, worker.py, demo_local.py, testing.py
  backend/tests/            test pytest (PostgreSQL bắt buộc)
  frontend/                 React + Vite + TypeScript
  docker-compose.yml        dịch vụ db (5432) và db-test (5433), project "wayfinder"
  .env.example              khoá cấu hình mẫu (không bí mật)
  openapi.json              hợp đồng xuất ra
  README.md                 cách chạy (mục máy chủ demo ở đầu)
src/doc2roadmap/            lõi Pha A/B; web import lõi, lõi không bao giờ import wayfinder
```

### 7.2 Migration (một head)

`w01_0001_foundation → w05_0002_phase_b → w02_0003_accounts → w03_0004_email_tokens → w06_0005_courses → w14_0006_builds → w11_0007_share_links →
w12_0008_invitations → w17_0009_first_admin`. Mỗi vé thêm bảng thì thêm đúng một migration; không sửa migration đã ghép. W-17.2 không thêm migration.
**DB dùng chung `wayfinder` (dev) chưa áp `w17_0009`**: việc đó cần chủ dự án và hồ sơ định danh admin đầu tiên; không tự làm.

### 7.3 Lệnh CLI (`python -m wayfinder.cli --env-file src/web/.env <lệnh>`)

`serve`, `worker`, `check`, `media-smoke`, `create-admin`, `seed-samples` (dùng Cloudinary), **`demo-local`** (W-26), `db upgrade`, `openapi export`.

### 7.4 Trang React (route)

`/`, `/demo`, `/dang-nhap`, `/dang-ky`, `/xac-minh`, `/quen-mat-khau`, `/dat-lai-mat-khau`, `/tai-khoan`, `/muc-dung`, `/khoa-hoc`, `/khoa-hoc/:cid`,
`/khoa-hoc/:cid/module/:mid`, `/khoa-hoc/:cid/module/:mid/khai-niem/:nid`, `/khoa-hoc/:cid/quiz/:aid`, `/khoa-hoc/:cid/tai-lieu/:did`,
`/khoa-hoc/:cid/thanh-vien`, `/join/:token`, `/tai-len`, `/ban-dung/:buildId`, `/admin`, `/admin/nguoi-dung`, `/admin/nhat-ky`.
Hợp đồng có phiên bản: `build-1`, `upload-1`, `usage-1`, `lecture-3`; trợ lý `answer-3`, quiz `quiz-3`, tài liệu `document-3` theo spec lõi.

### 7.5 Cấu hình và mô hình

- Web chạy `wayfinder.cli --env-file src/web/.env`: tệp được nạp vào biến môi trường **không ghi đè** biến đã có; rồi `WebSettings(_env_file=None)`.
- **Bẫy `.env` gốc:** `Settings` lõi (`src/doc2roadmap/config.py`, `env_prefix="DOC2ROADMAP_"`, `env_file=".env"`) còn tự đọc `.env` **ở thư mục đang
  đứng**. Chạy từ gốc repo thì `.env` gốc lặng lẽ cấp các khoá `DOC2ROADMAP_*` không có trong `src/web/.env`. Thứ tự ưu tiên: biến OS > `src/web/.env`
  > `.env` ở thư mục đang đứng > mặc định. W-final phải tính tới.
- **Web chỉ chạy Vertex**, chặn Gemini Developer API ở ba chốt: `composition.py:57` (transport phải `vertex`, có project/location),
  `infrastructure/real_build.py:18-19`, `infrastructure/build_spend.py:62-63, 175-178` (chỉ có giá Vertex `global`). Xác thực bằng ADC
  (`gcloud auth application-default login`) hoặc `GOOGLE_APPLICATION_CREDENTIALS`. Đổi sang Developer API (~12/11, khi chủ dự án yêu cầu): nới ba chốt,
  thêm bảng giá Developer API, thêm `DOC2ROADMAP_GEMINI_API_KEY` vào `src/web/.env`.
- Mô hình: chỉ `gemini-3.1-flash-lite`.
- `WAYFINDER_PUBLIC_BASE_URL` trong `src/web/.env` đang là `http://127.0.0.1:5173` (chế độ Vite). Mọi liên kết trong thư (xác minh, đặt lại mật khẩu,
  lời mời, báo dựng xong) ghép từ giá trị này. `demo-local` ghi đè thành `http://<host>:<port>` (mặc định 8000); có test và phép phá bắt.
- Khoá có trong `src/web/.env` (chỉ tên): `POSTGRES_PASSWORD`, `POSTGRES_TEST_PASSWORD`, `WAYFINDER_DATABASE_URL`, `WAYFINDER_TEST_DATABASE_URL`,
  `WAYFINDER_ENV`, `WAYFINDER_ARTIFACT_ROOT`, `CLOUDINARY_URL`, `WAYFINDER_SMTP_*`, `WAYFINDER_EMAIL_LOGO_URL`, `WAYFINDER_PUBLIC_BASE_URL`,
  `WAYFINDER_ALLOWED_ORIGINS`, khối Vertex `DOC2ROADMAP_LLM_TRANSPORT`/`_VERTEX_PROJECT`/`_VERTEX_LOCATION`. Đủ danh sách ở `src/web/.env.example`.

### 7.6 Tiền

- **Dựng sách:** worker thường luôn `allow_spend=False`. Giấy phép chi (`BuildSpendApproval`/`BuildSpendGuard` trong `infrastructure/build_spend.py`)
  chỉ do operator W-15 tạo, hoặc do `demo-local` qua `DemoSpendPolicy` (mỗi bản dựng một giấy phép `min(3 USD, 10 USD − đã chi hôm nay)`, giờ Việt Nam).
  Hook chi vá `urlopen` toàn tiến trình, nên worker demo chạy **tiến trình con riêng**. `retry_unknown_within_cap=True` (chủ dự án giữ): timeout không
  làm hỏng cả cuốn, phần chưa rõ không vào sổ ngày, trần 10 USD có thể vượt vài lần khoảng 0,36 USD.
- **Học (Pha B):** hai loại trần, cùng tính theo ngày giờ Việt Nam:
  - cá nhân — `assistant` và `document`: `learner_daily_max_usd`, **1 USD** mặc định, **3 USD/người/ngày trên máy chủ demo**;
  - dùng chung — `lecture`, `quiz_gen`, `quiz_verify`: `system_daily_max_usd` **5 USD/ngày cho cả máy chủ** (mặc định `BSettings`, demo không đổi).
  Lưu ý: tối 29/10 Claude trả lời chủ dự án rằng cả bài giảng/quiz tính vào 3 USD/người; đúng ra bài giảng và quiz tính vào trần chung 5 USD/ngày.
- `WAYFINDER_BUILD_MONTHLY_MAX` không đặt → trang Mức dùng hiện "Dựng lộ trình tháng này: Không giới hạn". Đặt `=3` thì hiện `x/3`.

### 7.7 Tệp và ảnh

ADR 0023: tệp gốc và ảnh ở Cloudinary (riêng tư, link tạm). Máy chủ demo dùng `DiskMediaStore` (`infrastructure/disk_media.py`): tệp ở
`<artifact-root>/demo-local/<tên DB>/media`, ảnh trang render bằng `pypdfium2`, link tải ký HMAC theo tiến trình (`/api/v1/demo-files/<token>`),
đường dẫn qua `safe_path`. Artifact Pha A ở đĩa (`artifacts/`, bị Git bỏ qua), không vào DB.

### 7.8 Thư

Gmail SMTP (`WAYFINDER_MAILER=smtp`, mật khẩu ứng dụng trong `src/web/.env`), gửi nền qua `BackgroundMailer`. Test dùng `FakeMailer`/`FakeSMTP`.

### 7.9 W-final (làm sau cùng)

Vé [W-final](../task/web/W-final-goi-ban-chay-may-khac.md): allowlist, không đường dẫn tuyệt đối `C:/Users/ngoco`, một lệnh bật, README tiếng Việt,
chỉ `src/web/.env.example` (rút còn khoá phải điền), `WAYFINDER_PUBLIC_BASE_URL` để 8000 hoặc lệnh bật tự đặt (không 5173), so `.env` gốc với mặc
định của lõi (bẫy 7.5). Tham khảo `Desktop\doctoroadmap-developer` (bản xuất thử, chỉ đọc).

## 8. Cách chạy

### 8.1 Chuẩn bị chung

- **Docker Desktop phải đang chạy** (sau khởi động lại máy, container dừng; `docker ps` báo lỗi pipe nghĩa là Docker Desktop chưa mở).
- Python: `C:\Users\ngoco\Desktop\Doctoroadmap\.venv\Scripts\python.exe` (lệnh `python` trần là stub, treo).
- Giao diện: `npm.cmd --prefix src/web/frontend ci --no-audit --no-fund` khi `node_modules` cũ (29/10 build báo thiếu `remark-math`… vì vậy), rồi
  `npm.cmd --prefix src/web/frontend run build`.

### 8.2 Máy chủ demo (W-26) — một cổng 8000

PowerShell, từ thư mục chung, sau khi Docker Desktop mở:

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap
docker compose -f src/web/docker-compose.yml --env-file src/web/.env up -d --wait db
$env:PYTHONPATH = "$($PWD.Path)\src\web\backend;$($PWD.Path)\src"
& .\.venv\Scripts\python.exe -X utf8 -m wayfinder.cli --env-file src/web/.env demo-local `
    --database wayfinder_demo_20261029 --admin-email <email admin> `
    --artifact-root C:\Users\ngoco\Desktop\Doctoroadmap\artifacts
```

- **Luôn truyền `--database wayfinder_demo_20261029`** để dùng lại dữ liệu cũ. Không truyền thì tên mặc định theo **ngày hôm nay**
  (`wayfinder_demo_<yyyymmdd>`), tức tạo DB mới, admin mới và nạp lại mẫu.
- DB đã có admin thì không hỏi mật khẩu. Lần đầu trên DB mới, lệnh hỏi mật khẩu bằng `getpass`; Claude chạy nền thì dùng
  [chay_demo.py](handoff-web-2026-10-29/cong-cu/chay_demo.py) (`python chay_demo.py <tệp-mật-khẩu> --env-file … demo-local …`), tệp mật khẩu để ngoài repo.
- Mở **http://127.0.0.1:8000**, dùng thống nhất `127.0.0.1` (không xen `localhost`, vì phiên/CSRF và liên kết trong thư đều theo `127.0.0.1`).
- Dừng: Ctrl+C (worker con dừng theo). Máy chủ do Claude chạy nền sẽ tắt khi phiên Claude kết thúc.
- `--role server|worker` chạy riêng từng phần; `--port` đổi cổng (liên kết thư đổi theo).

### 8.3 Chế độ phát triển (Vite 5173 + backend 8000)

Xem `src/web/README.md` các mục "Mở bản W-…": backend `serve` ở 8000 với `WAYFINDER_ALLOWED_ORIGINS` chứa cả 8000 và 5173,
`WAYFINDER_PUBLIC_BASE_URL=http://127.0.0.1:5173`, rồi `npm.cmd --prefix src/web/frontend run dev -- --port 5173 --strictPort`.

## 9. Kiểm thử

### 9.1 Backend

Từ **gốc worktree**, không chạy pytest trần (editable install nạp nhầm mã thư mục chung):

```bash
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py src/web/backend/tests \
  -o addopts= -q --tb=short -p no:warnings --basetemp=tmp/<tên-mới> --junitxml=tmp/<tên>.xml
```

Runner đặt `PYTHONPATH` vào worktree, bắt buộc PostgreSQL (container `wayfinder-db-test-1`, cổng 5433, phải healthy; bật bằng
`docker compose … up -d --wait db-test`), thêm `-p no:cacheprovider`. Mỗi lượt một `--basetemp` mới (thiếu thì "Access is denied"). Toàn
`src/web/backend/tests` mất khoảng 7–8 phút. Số đo gần nhất: 681 ca ở main sau W-26; 715 ca trên nhánh W-17.2.

### 9.2 React

Trong `src/web/frontend` của worktree: `npm ci`, `npx vitest run --pool=threads --maxWorkers=1` (283 ca ở lần 13), `npm run build`.

### 9.3 Fixture W-15 bị thiếu trong worktree mới

`test_internal_dry_run_w15.py::…[candidate]` cần `tmp/w15-candidate/input.pdf` (tệp không theo dõi, SHA bắt đầu `1f019766e74a747d`, sách huấn luyện,
không thuộc tập giữ lại). Thiếu thì đỏ `FileNotFoundError`. Bản đúng SHA có ở `tmp/coord-r10-acceptance-20261028/tmp/w15-candidate/input.pdf`.
**Chép thường** (`cp`), không hardlink/symlink, vì test kiểm `st_nlink == 1`:
`mkdir -p tmp/w15-candidate && cp ../coord-r10-acceptance-20261028/tmp/w15-candidate/input.pdf tmp/w15-candidate/`.
Lần 13 và 14 chưa biết chỗ này nên dùng `--deselect` riêng ca đó.

### 9.4 Tác dụng phụ của cổng

Cổng ghi đè `report/w06-evidence/http-*.json`, `report/w14-evidence/http-contract.json` và tạo `report/w15-evidence/sql/latest/`,
`report/w25-evidence/sql/latest/`. Trong worktree nghiệm thu thì `git checkout -- report/w06-evidence report/w14-evidence` sau mỗi lượt;
không làm việc đó ở thư mục chung khi chưa xem tệp là của ai.

## 10. Giao vé cho subagent

- Sổ tay chung: [so-tay-agent-web.md](handoff-web-2026-10-29/cong-cu/so-tay-agent-web.md) (bản làm việc ở `tmp/claude-tools/`). Mục 4b: React và
  thiết kế **bắt buộc** đọc `.agents/skills/design-taste-frontend/SKILL.md` và skill hợp màn (`minimalist-ui`, `high-end-visual-design`,
  `redesign-existing-projects`, `stitch-design-taste`…), cùng `src/web/frontend/.taste-skill/direction.json`. Hai thư mục này **chưa theo dõi trong Git**
  (bộ skill chủ dự án nạp), chỉ có trên máy này.
- Lời giao: `tmp/claude-tools/prompt-cai-<vé>.md`. Mẫu tốt: [prompt-cai-w17-2.md](handoff-web-2026-10-29/loi-giao/prompt-cai-w17-2.md) (vé mới),
  [prompt-cai-w26-sua-r14.md](handoff-web-2026-10-29/loi-giao/prompt-cai-w26-sua-r14.md) (vòng sửa nhỏ sau nghiệm thu). Lời giao nêu: worktree/nhánh,
  phạm vi tệp được sửa, bối cảnh, Required/Optional có mã (WEB-R<lần>-<số>), test phải đỏ trước, bảng phá, cách kết thúc.
- Tạo agent: công cụ Agent, `subagent_type: general-purpose`, `model: sonnet`, chạy nền; nội dung: "Đọc và làm đúng lời giao ở <đường dẫn>…, trả lời
  ngắn: nhánh, commit đỉnh, số test, bảng phá, câu hỏi". Dặn thêm nếu máy chủ demo đang chạy: không đụng cổng 8000, `wayfinder-db-1`, DB demo.
- Một agent một lúc (máy RAM thấp, phiên Pha A chạy song song); xong việc thì agent mới cho việc sau. Không chạy hai cổng PostgreSQL cùng lúc.

## 11. Nghiệm thu và ghép

1. Đọc báo cáo và `git diff main...<nhánh>` phần mã sản phẩm.
2. **Bộ phá độc lập** của Claude (khác bộ phá của subagent): mỗi phép thay một chuỗi duy nhất, chạy tệp test của vé qua runner, khôi phục bytes trong
   `finally`, đối chiếu SHA. Tệp mã là CRLF: chuẩn hoá `\r\n`→`\n` trước khi tìm chuỗi rồi ghi lại CRLF. Mẫu:
   [coord-r14-evidence-2026-10-29/mutations/pha_w26.py](coord-r14-evidence-2026-10-29/mutations/pha_w26.py). Phép sống sót → Required cho vòng sửa
   (subagent mới), trừ khi chứng minh tương đương.
3. Bản ghép thử ở worktree nghiệm thu (`git worktree add … main`, `core.longpaths true`,
   `python -X utf8 tmp/claude-tools/copy_bundles.py tmp/<tên>` phải in `bundles ok: copied 3145`), chép fixture W-15 (9.3), chạy cổng.
   Khi main chỉ đổi phần đánh giá, cổng rút gọn (React nếu đụng + build + `src/web/backend/tests` + bộ phá) là đủ; cổng toàn repo chỉ khi chủ dự án cho.
4. `ghep_guard.sh` đòi gốc nhánh = main hiện tại: main đã đổi thì `git -C tmp/<vé> merge --no-ff main` trước, cổng chạy trên đỉnh đó.
5. `bash tmp/claude-tools/ghep_guard.sh <nhánh> <junit>` → chỉ ghép khi in `GUARD OK`; `git merge --no-ff -m "merge(web): …; local only" <nhánh>`.
   Chuỗi kiểm rồi ghép dùng `&&`, không `;`.
6. Biên bản `report/dieu-phoi-nghiem-thu-lan<N>-<ngày>.md`, bằng chứng `report/coord-r<N>-evidence-<ngày>/`; cập nhật kế hoạch web, dòng trạng thái
   vé, bàn giao này, bộ nhớ. Commit **chỉ đường dẫn của mình**: tệp mới phải `git add` trước, rồi `git commit -m … -- <tệp>`.

## 12. Luật bắt buộc

- **Tập giữ lại, không ai mở:** `d01-t01`, `d01-t02`, `document-data/test/`, `Desktop\d02-tap-khoa`, mọi `khoa.jsonl`. Không in phần `cache` của
  `artifacts/phase_b/live.json`, không nhập nó vào DB. Web chỉ nạp sáu cuốn phát triển: doc-1, nhap-mon-ml, naive-bayes, doc-6, xstk-ch3-1, doc-4.
- **Tiền:** chỉ `gemini-3.1-flash-lite`; lượt có tiền phải dry-run, chủ dự án duyệt; mọi vé web là 0 USD (test dùng đồ giả). Máy chủ demo là ngoại lệ
  chủ dự án cho ngày 29/10, trong trần mục 7.6.
- **Bí mật** chỉ ở `.env` và `src/web/.env`; không dán vào báo cáo, chat, bàn giao (repo công khai).
- **Git:** commit chỉ đường dẫn của mình; không `git add -A`/`git add .`; không `stash`, `reset`, `checkout --` tệp của người khác; không đổi nhánh thư mục
  chung; không junction/symlink vào `artifacts`; không đụng `tmp/t01a-clean-ff797eb`; gỡ worktree chỉ sau khi `dir /AL /S /B` rỗng.
- **DB:** không migrate, không chạy CLI vào DB dùng chung `wayfinder`. Test dùng `db-test`. Máy chủ demo dùng DB riêng `wayfinder_demo_*`.
- **Spec/ADR:** subagent không sửa; câu hỏi ghi vào báo cáo; điều phối chỉ ghi khi chủ dự án đã chốt.

## 13. Máy chủ demo hiện tại

| mục | giá trị |
|---|---|
| DB | `wayfinder_demo_20261029` trên container `wayfinder-db-1` (5432) |
| admin | email của chủ dự án; mật khẩu ở tệp cục bộ ngoài repo (không ghi ở đây); quên thì dùng "Quên mật khẩu" (thư thật) |
| khoá mẫu | sáu cuốn phát triển, nạp lúc chạy đầu |
| media | `artifacts/demo-local/wayfinder_demo_20261029/media`; nhật ký chi `…/spend-audit/*.jsonl` |
| dùng thử 29/10 | 473 request, 0 lỗi 5xx; 2 lần tải sách và dựng thật: **0,3816 + 0,6289 = khoảng 1,01 USD** (ước theo token, giá embedding chưa đối soát hoá đơn); nhật ký chi của cả hai có đủ ba chặng `concepts`, `graph`, `learning_prep`, không chạm trần, không dừng; kết quả cuối của hai bản dựng chưa kiểm trong DB |
| trạng thái | **tắt** (Docker Desktop tắt, tiến trình nền của phiên Claude đã dừng). Bật lại theo 8.2 |

## 14. Bẫy và bài học

- Glob/find trên gốc repo treo vì repo rất lớn: dùng `git ls-files`, `ls -t`, hay đường dẫn cụ thể.
- PowerShell ghi tệp không phải UTF-8 → chữ Việt thành `?` (WEB-R13-01). Ghi bằng công cụ Write/Edit hoặc Python `encoding="utf-8"`.
- Tệp mã trong cây làm việc là CRLF; `git status` báo `M` mà `git diff` rỗng là chênh CRLF.
- Tệp bằng chứng chưa theo dõi ở thư mục chung có thể chặn `git merge` (lần 13): chuyển đi rồi ghép lại.
- `git commit -- <tệp mới>` báo lỗi pathspec nếu chưa `git add`.
- `ghep_guard.sh` từ chối khi nhánh không gốc ở main hiện tại.
- Test cũ chỉ so với chính giá trị cấu hình (ví dụ `cfg.public_base_url`) không bắt được lỗi ghi đè: phải so chuỗi cụ thể và cho cấu hình gốc mang
  giá trị sai thật (bài học W-26 lần 14).
- Bộ phá thay chuỗi phải kiểm chuỗi khớp **đúng một** chỗ (bài học `since-before-until` lần 15).
- Bộ nhớ cũ ghi repo GitHub "riêng tư": thực tế **công khai**; mọi thứ commit lên main sẽ công khai khi push.
- Worktree rất nhiều (hơn 90). `tmp/dg-*` và hai worktree trong scratchpad của phiên khác (`wt-ve04`, `wt-ve05`) thuộc phiên Pha A; không đụng.
- Lệnh chạy nền trong phiên Claude chết theo phiên; máy chủ demo cần bật lại sau mỗi phiên mới.

## 15. Công cụ đi kèm bàn giao

Bản sao trong repo (thư mục `tmp/` bị Git bỏ qua). Ở máy này dùng bản `tmp/claude-tools/`; ở máy khác chép thư mục này vào `tmp/claude-tools/`.

| tệp | dùng làm gì |
|---|---|
| [cong-cu/so-tay-agent-web.md](handoff-web-2026-10-29/cong-cu/so-tay-agent-web.md) | sổ tay mọi subagent web/lõi/thiết kế đọc trước lời giao |
| [cong-cu/ghep_guard.sh](handoff-web-2026-10-29/cong-cu/ghep_guard.sh) | chặn ghép khi main đổi, có cổng đang chạy, có `index.lock`, hay junit chưa xanh |
| [cong-cu/copy_bundles.py](handoff-web-2026-10-29/cong-cu/copy_bundles.py) | chép hai bộ fixture phát triển vào worktree, kiểm SHA, cấm link |
| [cong-cu/chay_demo.py](handoff-web-2026-10-29/cong-cu/chay_demo.py) | chạy `demo-local` lần đầu không cần gõ mật khẩu (đọc từ tệp ngoài repo) |
| [loi-giao/prompt-cai-w17-2.md](handoff-web-2026-10-29/loi-giao/prompt-cai-w17-2.md) | lời giao W-17.2 (đang nghiệm thu) |
| [loi-giao/prompt-cai-d-r12-01.md](handoff-web-2026-10-29/loi-giao/prompt-cai-d-r12-01.md) | lời giao thiết kế D-R12-01 + W-23 (chưa giao) |
| [loi-giao/prompt-cai-w26.md](handoff-web-2026-10-29/loi-giao/prompt-cai-w26.md), [prompt-cai-w26-sua-r14.md](handoff-web-2026-10-29/loi-giao/prompt-cai-w26-sua-r14.md), [prompt-cai-w17-1-sua-r13.md](handoff-web-2026-10-29/loi-giao/prompt-cai-w17-1-sua-r13.md) | lời giao đã dùng, làm mẫu |

Đường dẫn trong các công cụ là tuyệt đối theo máy này (`C:/Users/ngoco/Desktop/Doctoroadmap`); máy khác phải sửa.

## 16. Tài liệu chuẩn

- Spec: [chức năng web](../doc/web-chuc-nang-spec.md), [cơ sở dữ liệu](../doc/web-co-so-du-lieu-spec.md),
  [thiết kế giao diện](../doc/web-thiet-ke-giao-dien-spec.md), [Pha B2](../doc/pha-b2-spec.md), bài giảng/trợ lý/quiz/tài liệu 3 ở `doc/`.
- ADR web: 0020–0023 (khoá học, phiên cookie, PostgreSQL, Cloudinary), 0024–0026 (bài giảng/trợ lý), 0030 (admin đầu tiên).
- [Kế hoạch web](../task/web/00-ke-hoach.md) và vé `task/web/W-*.md`; [quy trình nhánh và ghép](../doc/quy-trinh-nhanh-va-ghep-main.md).
- [README web](../src/web/README.md).
- Bàn giao cũ (lịch sử, Pha B): [handoff-dieu-phoi-2026-10-18.md](handoff-dieu-phoi-2026-10-18.md).
