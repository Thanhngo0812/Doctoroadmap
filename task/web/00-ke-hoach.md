# Web WayFinder — kế hoạch vé

**Nguồn chân lý:**
- [spec chức năng web](../../doc/web-chuc-nang-spec.md), cùng ADR [0020](../../doc/adr/0020-khoa-hoc-la-don-vi-chia-se-du-lieu-hoc-theo-nguoi-va-cuon.md) và
  [0021](../../doc/adr/0021-phien-dang-nhap-phia-may-chu-trong-cookie.md);
- [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), cùng ADR [0022](../../doc/adr/0022-postgresql-cho-du-lieu-web-artifact-o-kho-tep-hang-doi-bang-bang.md);
- [spec thiết kế giao diện](../../doc/web-thiet-ke-giao-dien-spec.md) (font Be Vietnam Pro, logo và favicon WayFinder, màu, bố cục từng trang);
- [spec Pha B2](../../doc/pha-b2-spec.md) cho mọi hợp đồng nội dung học;
- [ADR 0023](../../doc/adr/0023-cloudinary-cho-tep-goc-va-anh.md): tệp gốc và ảnh ở Cloudinary (gói miễn phí, riêng tư), artifact Pha A ở đĩa.

**Stack:** React (Vite, TypeScript) + FastAPI + PostgreSQL 16 (Docker) + Cloudinary (tệp gốc và ảnh) + Gmail SMTP. React phục vụ cùng nguồn với API.

**Nơi đặt mã** (chủ dự án chốt 2026-10-18): mọi mã web ở `src/web/` — `backend/wayfinder/` (gói Python), `backend/tests/`, `frontend/` (React),
`docker-compose.yml`. Lõi `src/doc2roadmap/` chỉ đổi ở W-05 (nới port sổ chi) và W-13 (`build_document`). `doc2roadmap` không bao giờ import `wayfinder`.

**Bản demo** (chủ dự án chốt 2026-10-18): ai cũng tải sách được, không cần xác minh email; khâu dựng không giới hạn (trần cài sẵn, mặc định tắt);
khoá mẫu chỉ ở dev; chỉ mời qua email mới cần xác minh.

**Quy trình:** Claude soạn vé; chủ dự án giao nhóm web và nhân viên; người soát (Claude, hay nhân viên cấp cao theo SA-45 khi Claude vắng) kiểm theo tiêu
chí của vé. Vé sửa sau soát đánh số tiếp từ W-24.

**Số vé:** tiền tố `W-` để không trùng dãy `SA-` (SA-45 giữ số 46 trở đi cho vé sửa Pha B).

## Luật chung của mọi vé

- **Test thấy đỏ trước** trên bản sai rồi mới xanh (AGENTS.md mục 5). Đường nối chính là **tầng dịch vụ** với kho bộ nhớ, đồng hồ giả, `Mailer` giả,
  `BuildRunner` giả, và Pha B chạy trên mô hình giả theo kịch bản (spec chức năng, "Quyết định kiểm thử"). Tầng HTTP chỉ kiểm thứ sống ở HTTP.
- **Mỗi vé một lát dọc:** di trú cơ sở dữ liệu, dịch vụ, API, giao diện React, test. Vé chỉ xong khi chạy được từ trình duyệt.
- **Mỗi vé thêm bảng thì thêm đúng một bản di trú Alembic,** tên theo vé. Không sửa di trú đã vào nhánh chính.
- **Test PostgreSQL:** lệnh kiểm của vé chạy cả bản PostgreSQL (dịch vụ `db-test` trong docker compose). Thiếu PostgreSQL thì coi là **hỏng**, không phải
  "bỏ qua".
- **Giao diện:**
  - theo spec thiết kế: token màu, chữ, khoảng cách, trạng thái rỗng, đang tải, lỗi;
  - **logo đã có** (chủ dự án xác nhận 2026-10-19): `design/Artboard 9.png` đến `design/Artboard 28.png`, thay tên giả định `logo1`–`logo8`;
    chọn biến thể theo spec thiết kế mục 1. Không còn điều kiện chờ tám logo cũ;
  - **theo yêu cầu chủ dự án 2026-10-18:** Figma và React phải đẹp, chỉn chu, nhất quán; đúng chức năng chưa đủ nghiệm thu giao diện. Đối chiếu tiêu chí
    thị giác và hiệu ứng ở spec thiết kế mục 3a cho mọi vé có giao diện;
  - hiệu ứng hover/focus/bấm, menu, hộp thoại, bảng trượt, khối gập và chuyển trạng thái theo token chuyển động; không cản thao tác, nhảy bố cục hay thêm
    thời gian chờ giả. Có phương án `prefers-reduced-motion`;
  - **được phép dùng các skill trong bộ `taste-skill` do chủ dự án nạp** cho cả thiết kế và React. Đọc `SKILL.md` khi dùng, ghi tên skill/đề xuất đã áp
    dụng trong báo cáo; spec và thương hiệu đã chốt là căn cứ. Chưa có skill thì tiếp tục theo spec, không tự coi là chặn vé;
  - chữ hiện cho người dùng là tiếng Việt;
  - mỗi vé có giao diện thì kèm ảnh chụp màn hình ở cỡ điện thoại (390 px) và máy tính (1280 px) trong báo cáo vé; kiểm bố cục thêm ở 768 px và kèm video
    ngắn của các tương tác có hiệu ứng thuộc vé. Người thiết kế/người soát xác nhận chất lượng thị giác; W-23 đối chiếu cả hiệu ứng.
- **Ví dụ JSON thật** của mọi điểm cuối mới trong báo cáo vé, cho nhóm React.
- **Không dùng tập giữ lại:** máy chủ web không nạp `d01-t01`, `d01-t02`, `document-data/test/`, `Desktop\d02-tap-khoa`. Dữ liệu dev là sáu cuốn phát triển.
  Không nhập `artifacts/phase_b/live.json` (có cache của tập giữ lại); không in phần `cache` của nó.
- **Tiền:** chỉ `gemini-3.1-flash-lite`. Mọi lượt có tiền dry-run trước, chủ dự án duyệt. Ngoài W-15, mọi vé là 0 USD.
- **Gemini backend web** (chủ dự án cập nhật 2026-10-19, thay quyết định 2026-10-18): FastAPI và worker **tạm dùng Vertex AI** cho sinh nội dung,
  embedding và dựng sách. Dùng `DOC2ROADMAP_LLM_TRANSPORT=vertex`, project/location và ADC phía máy chủ, không bắt buộc Gemini API key; bí mật không vào
  React/`VITE_*`. Chỉ chuyển sang Gemini Developer API khi chủ dự án yêu cầu chuẩn bị demo, không tự chuyển khi lỗi hay theo ngày. Test dùng đồ giả/phát
  lại, không gọi mạng; xem spec chức năng mục 1, 12 và bất biến kiểm thử 27.
- **Commit chỉ đường dẫn của vé** (`git commit -m … -- <tệp>`). Không sửa tệp của phiên pha A; cần đổi mã Pha A thì ghi yêu cầu vào báo cáo vé.
- **Nhánh và ghép vào main:** theo [quy trình nhánh và ghép main](../../doc/quy-trinh-nhanh-va-ghep-main.md).
  Thư mục chung luôn ở `main`; mỗi vé một nhánh trong worktree `tmp/<tên>`. Chỉ điều phối ghép bằng `--no-ff` tới mốc đã soát,
  sau cổng test đầy đủ xanh, rồi đẩy `main` lên GitHub. Người làm vé không sửa vé/kế hoạch/handoff; ghi đề xuất vào báo cáo vé.
- **Lưu dần:** làm tới đâu commit tới đó; báo cáo vé có dòng trạng thái ở đầu.
- **Cloudinary:**
  - test dùng `MediaStore` giả, không gọi Cloudinary;
  - `CLOUDINARY_URL` chỉ ở `.env`, không commit, không dán vào báo cáo hay chat; thiếu thì hỏi chủ dự án;
  - dev và triển khai tách bằng thư mục `wayfinder/dev`, `wayfinder/prod`;
  - trình duyệt không bao giờ nhận link Cloudinary dùng lâu được (ADR 0023).
- **Môi trường:** từ gốc worktree, chạy Python của `.venv` thư mục chung qua `scripts/w05_run_tests.py` bằng đường dẫn đầy đủ theo quy trình.
  Runner ghim import vào mã worktree, bắt buộc PostgreSQL và thêm `-p no:cacheprovider`; dùng `--basetemp` mới trong `tmp/`.
  Tạo sẵn thư mục cha `tmp/` trong worktree mới trước lượt kiểm đầu tiên.
  Không chạy pytest trần trong worktree vì editable install có thể nạp nhầm mã thư mục chung.

## Phụ thuộc vào vé Pha B2

Phần học (W-07…W-10) gọi use case Pha B2. Vé Pha B2 chưa xong thì gateway gọi hợp đồng đang có, ghi rõ trong báo cáo vé, và đổi khi vé B2 xong. Hợp đồng
còn đổi; nhóm web đã được báo.

## Bảng vé

| vé | việc | chặn bởi | trạng thái |
|---|---|---|---|
| [W-01](W-01-nen-web-fastapi-react-postgres.md) | nền: FastAPI, React, PostgreSQL, Alembic, đường nối test, token giao diện | — | đạt nền local; đã ghim c91551f; React 23 test/build và browser đạt; [soát](../../report/dieu-phoi-soat-ba-nhom-2026-10-19.md) |
| [W-02](W-02-dang-ky-dang-nhap-phien.md) | đăng ký, đăng nhập, đăng xuất, phiên cookie, CSRF, giới hạn thử | W-01 | đạt · đã ghép `a3f2f13`, mốc `8558df4`; [cổng và bàn giao](../../report/dieu-phoi-ghep-main-2026-10-20.md) |
| [W-03](W-03-xac-minh-email-quen-mat-khau.md) | xác minh email, quên mật khẩu, cổng gửi thư | W-02 | đạt · đã ghép `63f09ad`, mốc `9de8e75`; 2.085 Python/62 React/build, browser thật; [nghiệm thu](../../report/dieu-phoi-nghiem-thu-w03-va-ke-hoach-2026-10-20.md) |
| [W-04](W-04-ho-so-doi-mat-khau-dang-xuat-moi-noi.md) | hồ sơ, đổi mật khẩu, đăng xuất mọi nơi | W-02 | đủ điều kiện; có preview, chưa có nghiệp vụ W-04; xếp sau đường W-07 nếu chỉ có một phiên web |
| [W-05](W-05-kho-pha-b-postgresql.md) | kho Pha B trên PostgreSQL, `single_flight` liên tiến trình, nới port sổ chi | W-01 | đạt · đã ghép `a3f2f13`, gồm checkpoint W-02; [cổng và bàn giao](../../report/dieu-phoi-ghep-main-2026-10-20.md) |
| [W-06](W-06-khoa-mau-khoa-hoc-cua-toi-gateway.md) | khoá mẫu, "Khoá học của tôi", `LearningGateway`, test người ngoài khoá | W-02, W-05 | đạt · đã ghép `dc41ee8`, mốc `8b6e500`; 2.107 Python/77 React/build, browser PG; [nghiệm thu](../../report/dieu-phoi-nghiem-thu-w06-va-ke-hoach-2026-10-21.md) |
| [W-07](W-07-trang-lo-trinh-tien-do.md) | trang lộ trình và tiến độ | W-06, SA-34 | ưu tiên tiếp theo của web; đã soát SA-47 memory/JSON, triển khai theo hợp đồng hiện có và kiểm race/cách ly PostgreSQL ở W-07 |
| [W-08](W-08-trang-hoc-bai-giang-doc-trang.md) | trang học: bài giảng stream, "Đọc trang p" | W-07, SA-39, SA-40, SA-41 | ready-for-agent |
| [W-09](W-09-tro-ly-va-phien.md) | trợ lý và phiên chat | W-07, SA-32, SA-33, SA-42 | ready-for-agent |
| [W-10](W-10-quiz-tai-lieu-thu-vien.md) | quiz, tài liệu, thư viện | W-07, SA-35, SA-37 | ready-for-agent |
| [W-11](W-11-chia-se-link-thanh-vien.md) | chia sẻ bằng link, thành viên, rời khoá | W-06 | đủ điều kiện; sau W-07 nếu một phiên web; migration w11_0007 nối w14_0006, ghép sau mốc W-14 đã soát đạt |
| [W-12](W-12-moi-qua-email.md) | mời qua email, lời mời trong ứng dụng | W-03, W-11 | ready-for-agent |
| [W-13](W-13-dung-mot-cuon-o-loi.md) | use case `build_document` ở lõi | — | đạt nghiệm thu; doc-6 hoàn tất cả hai kho, điều phối tái lập 0 USD; [soát mới](../../report/dieu-phoi-kiem-lai-w13-w24-2026-10-19.md) |
| [W-14](W-14-tai-sach-len-ban-dung.md) | tải sách lên, xác nhận, kiểm sớm, hàng đợi, worker, ghi usage thực; bộ dựng giả | W-03, W-06 | đủ điều kiện; lõi chuẩn bị backend/worker, web tích hợp sau ưu tiên W-07; thêm FK build_id/nguồn upload; không dự toán, nối callback W-13 |
| [W-15](W-15-noi-bo-dung-that-do-usd-cuon.md) | nối bộ dựng thật, đo USD/cuốn và phút/cuốn | W-13, W-14 | W-13 đã đạt; còn chờ W-14 và phạm vi phê duyệt chi của vé |
| [W-16](W-16-muc-dung.md) | trang mức dùng và dải hết trần | W-09, W-14 | ready-for-agent |
| [W-17](W-17-quan-tri.md) | quản trị: người dùng, bản dựng, chi, khoá mẫu, nhật ký | W-14, W-16 | ready-for-agent |
| [W-18](W-18-tien-do-thanh-vien-cho-chu-khoa.md) | tiến độ tổng hợp của thành viên cho chủ khoá | W-07, W-11 | ready-for-agent |
| [W-19](W-19-bao-loi-noi-dung.md) | báo lỗi nội dung | W-08, W-09, W-10 | ready-for-agent |
| [W-20](W-20-xoa-tai-khoan-xoa-khoa-hoc.md) | xoá tài khoản, xoá khoá học | W-11, W-14 | ready-for-agent |
| [W-21](W-21-trien-khai-sao-luu-thu-dau-cuoi.md) | triển khai, sao lưu, thử đầu-cuối, soát an ninh | W-12, W-15, W-17, W-20 | ready-for-agent |
| [W-22](W-22-ban-figma.md) | bản Figma theo spec thiết kế | — | còn nguồn export Figma và đủ trang/prototype có kiểm chứng; [soát 2026-10-20](../../report/dieu-phoi-nghiem-thu-w02-w05-w24-2026-10-20.md) |
| [W-23](W-23-doi-chieu-figma-va-giao-dien.md) | đối chiếu Figma với giao diện React, chỉnh lệch | W-22, W-08, W-09, W-10 | ready-for-agent |
| [W-24](W-24-bo-sung-va-sua-ban-giao-w22.md) | sửa nút tối, vùng bấm mobile, giảm chuyển động, guard token; đủ bằng chứng W-22 | — | phần local W-06/W-04 đã ghép `dc41ee8`, sửa claim/TTL và kiểm 12 preview; vẫn thiếu Variables/bằng chứng Figma/prototype đầy đủ; [soát mới](../../report/dieu-phoi-nghiem-thu-w06-va-ke-hoach-2026-10-21.md) |

## Thứ tự đề xuất

- **Sau nghiệm thu W-06, 2026-10-21:** W-06 đã ghép `dc41ee8`, mốc `8b6e500`; cổng đúng mốc 2.107 Python đạt/0 fail/1 Cloudinary live không bật,
  React 77/build, browser PG 9 assertion/6 màn và 8/8 mutation bị bắt, 0 USD. Web ưu tiên W-07 rồi W-11; lõi chuẩn bị backend/worker W-14 bằng bộ dựng giả;
  thiết kế tiếp W-24 phần Figma, ưu tiên W-07/W-14. Phần local W-24 được tích hợp không đồng nghĩa đóng toàn vé.
  W-07 không tạo migration rỗng; tuyến đã chốt `w06_0005 → w14_0006 → w11_0007`: W-14 ghép trước, W-11 nối sau. W-14 bổ sung FK build_id và nguồn upload theo phần W-06 bàn giao.
  Đã soát SA-47 memory/JSON phục vụ mở W-07; các race/cách ly PostgreSQL vẫn phải kiểm trong W-07. Giữ soát B2 còn lại trước các vé học tương ứng.
  [Bằng chứng và kế hoạch](../../report/dieu-phoi-nghiem-thu-w06-va-ke-hoach-2026-10-21.md). Các đợt giao trước dưới đây giữ làm lịch sử.
- **Khởi động lại sau sự cố artifact, mốc mới nhất 2026-10-20:** chủ dự án xác nhận nhóm web mới xong W-03, các nhóm đang dừng.
  W-03 đã đạt và ghép `63f09ad` tới `9de8e75`; 2.085 Python đạt/0 fail/1 Cloudinary live không bật, React 62/build, Chromium HTTP + PostgreSQL thật đạt, 0 USD.
  Sáu graph phát triển tải được, doc-1 v8/doc-6 v29; không cần dựng lại để mở W-06. Lõi và web ưu tiên cùng W-06, thiết kế tiếp W-24/hỗ trợ màn khoá học.
  Test người ngoài tự liệt kê mọi route trên khoá riêng tư, kể cả join-sample; test riêng đăng nhập tham gia khoá mẫu dev, không miễn route.
  `w06_0005` nối `w03_0004`. W-04 đủ điều kiện nhưng không tách người khỏi W-06 nếu chỉ có một phiên web.
  [Bằng chứng và kế hoạch](../../report/dieu-phoi-nghiem-thu-w03-va-ke-hoach-2026-10-20.md), [lời giao ba nhóm](../../report/lenh-giao-viec-sau-w03-2026-10-20.md).
  Các dòng đợt ghép/giao trước dưới đây giữ làm lịch sử; trạng thái mới ở bảng và dòng này thay các ghi nhận W-03 đang làm/chưa soát trước đó.
- **Ghép bù 2026-10-20:** W-02/W-05 đã vào main bằng `a3f2f13` tới đúng `8558df4`; cổng đầy đủ 1.999 Python đạt, 1 Cloudinary live không bật,
  React 41/build đạt. Thư mục chung chuyển về main; W-03 làm trong `tmp/w03-email-recovery`, W-24 ở `tmp/w24-figma-evidence`.
  `781415b`, `79cb9c9` và helper `6cd6be7` chưa được soát; không thuộc bản ghép này. W-03 cần phán xét W-24 cho phần mang theo trước khi được ghép.
  [Biên bản tích hợp](../../report/dieu-phoi-ghep-main-2026-10-20.md).
- **Đã đẩy GitHub:** main cùng hồ sơ điều phối tới `83f3ffd`; W-03/W-24 đã nhận mốc này trong worktree riêng. Các thay đổi tài liệu nhật ký sau đó
  không thay mã qua cổng; trước lần ghép vé tiếp theo vẫn phải nhận main mới nhất và chạy lại cổng của vé đó.
- **Sau nghiệm thu 2026-10-20:** W-02/W-05 đạt; web ưu tiên W-03 và bố trí React/tích hợp W-06; lõi nhận backend/gateway W-06.
  W-04 đủ điều kiện nhưng chỉ chia khi có người, phân vùng AccountService với W-03. [Bằng chứng và giao việc](../../report/dieu-phoi-nghiem-thu-w02-w05-w24-2026-10-20.md).
- **Migration hiện tại:** đã kiểm một head `w01_0001 → w05_0002 → w02_0003 → w03_0004 → w06_0005`.
  W-03 email_token và W-06 course/membership đã bàn giao; giữ kiểm baseline W-01 và DB rỗng lên HEAD cho vé tiếp.
- **Thiết kế:** W-24 chỉ còn nguồn Variables export thực và đủ trang/prototype có guard đúng; phần vá runtime, sáu màu plugin và auth 390 đã đóng.
  Nay ưu tiên hỗ trợ màn W-06; TTL auth phải giữ xác minh 24 giờ/reset 60 phút. W-24 chưa đủ không chặn W-06 theo spec hiện hành.
- **Sau W-06:** mở W-07 và W-11; W-03 cùng W-06 đạt thì mở W-14 với bộ dựng giả. W-14 đạt mới mở W-15; W-13 đã đạt, không kiểm lại doc-6 khi chưa có thay đổi.
- **Phần học:** W-07 → W-08, W-09, W-10 theo phụ thuộc Pha B2. Claude còn yêu cầu soát độc lập SA-46/47/49/50/51;
  không lấy bàn giao nhân viên thay phán xét đạt. W-23 vẫn chờ W-22 và W-08/W-09/W-10.
- **Cuối:** W-16, W-17, W-18, W-19, W-20, rồi W-21 và W-23.

## Quyết định của chủ dự án

Đã trả lời hết ngày 2026-10-18; xem mục "Quyết định của chủ dự án" cuối spec chức năng. Điều phối xem [bản bàn giao điều phối](../../report/handoff-dieu-phoi-2026-10-18.md).
