# Web WayFinder — kế hoạch vé

**Mới nhất — nghiệm thu lần 8, 2026-10-26:** W-10 aaf68eb, backend W-04 c1f2fe9 và guard thiết kế feb5f5e nhận/ghép **local 1be7e1c**; cổng ee5a75f: **2.824 Python/0 fail/1 skip/1 xfail cũ, 219 React/build**, browser 12 cấu hình/96 ảnh/65 Axe/27 SSE đủ body. Đóng hai lỗi W-10 và D-R7-02. W-04/W-16 còn React; W-23 chưa đạt, bảng ảnh đã sửa D-R8-01. Web React W-16 rồi W-04; lõi backend W-12; thiết kế W-23 đúng state và mẫu ba vé tiếp. SA-61 đã ghép ab5c2fa nhưng web vẫn Vertex. Chi mới 0 USD; **chỉ commit local/chưa push**. [biên bản lần 8](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan8-2026-10-26.md) và [lời giao lần 8](../../report/lenh-giao-viec-ba-nhom-lan8-2026-10-26.md).

**Mới nhất — nghiệm thu lần 7, 2026-10-26:** backend W-16 d1bf42b và mẫu W-10/thiết kế 26e4a9a đã ghép local **c5b4f5f**, cổng đúng 7e8c7d1 có 2.735 Python/0 fail/1 skip/1 xfail có sẵn, 203 React/build. W-10 fa346c9 chưa nhận do R-W10-1 vượt hạn tài liệu qua tool và R-W10-2 kết quả submit cũ ghi vào màn mới. Web sửa hai lỗi rồi React W-16; lõi backend W-04; thiết kế guard JS thật và W-23 đúng nguồn/trạng thái. W-23 chưa đạt, báo cáo đã đính chính; không Cloud. 0 USD, giữ Vertex và chỉ commit local/chưa push. [biên bản lần 7](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan7-2026-10-26.md), [lời giao](../../report/lenh-giao-viec-ba-nhom-lan7-2026-10-26.md).

**Mới nhất — nghiệm thu lần 6, 2026-10-25:** W-09 378131e và W-15 efed8db đạt (W-15 có ghi chú phạm vi đo/tích hợp), ghép local **7f54b14**. Cổng đúng c23d111: 2.716 Python/0 fail/1 skip/1 xfail có sẵn, 203 React/build; browser 12 cấu hình/102 ảnh/46 Axe. Thiết kế 0b5993e chưa nhận do D-R6-01 bộ lọc here/elsewhere; mốc thiết kế cũ giữ nguyên. Web bắt đầu W-10, lõi backend W-16, thiết kế sửa mẫu và soát React W-23. Chi điều phối 0 USD; chi W-15 đã kiểm known demo 1,96881130 USD + unknown upper 0,4139008 USD. Chỉ commit local/chưa push, không Cloud, giữ Vertex. [biên bản lần 6](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan6-2026-10-25.md), [lời giao](../../report/lenh-giao-viec-ba-nhom-lan6-2026-10-25.md).

**Mới nhất — nghiệm thu lần 5, 2026-10-25:** lõi/operator fb0c769 và thiết kế aa387f3 đạt mốc, ghép local `9028db2`; cổng đúng đỉnh8bb746f có 2.676 Python/0 fail/1 skip/1 xfail có sẵn,181 React/build. W-09 chưa nhận da4d639 do hai Required; web sửa trước W-10. Lõi chuẩn bị plan mới sau nhận main, chưa được chi; thiết kế hỗ trợ React/W23/mẫu W-10. Không push main, không Cloud, giữ Vertex. [Biên bản](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan5-2026-10-25.md), [lời giao](../../report/lenh-giao-viec-ba-nhom-lan5-2026-10-25.md).

**Đồng bộ local theo quyết định chủ dự án 2026-10-24:** tạm thời chưa cần push main; ghi commit mới nhất trên máy và chờ chủ dự án yêu cầu tiếp. Điều kiện soát/test trước ghép vẫn giữ nguyên.

**Mới nhất — nghiệm thu lần4 2026-10-24:** W-08 và mốc kiểm/dry-run0USD W-15 đã ghép local `bad8e45`; toàn W-15 còn mở. Thiết kế giữ đạt có ghi chú mốc web, chỉ vá3lỗi công thức preview mới, không Cloud. Web sang W-09; lõi sửa operator/điều kiện profile trước xin chi; thiết kế hỗ trợ React/W-23. SA-67/68 đã ghép, W-10 có đủ document-3/quiz-3. [Biên bản](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan4-2026-10-24.md), [lời giao ba nhóm](../../report/lenh-giao-viec-ba-nhom-lan4-2026-10-24.md). Giữ Vertex, chi mới0USD.

**Nguồn chân lý:**
- [spec chức năng web](../../doc/web-chuc-nang-spec.md), cùng ADR [0020](../../doc/adr/0020-khoa-hoc-la-don-vi-chia-se-du-lieu-hoc-theo-nguoi-va-cuon.md) và
  [0021](../../doc/adr/0021-phien-dang-nhap-phia-may-chu-trong-cookie.md);
- [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), cùng ADR [0022](../../doc/adr/0022-postgresql-cho-du-lieu-web-artifact-o-kho-tep-hang-doi-bang-bang.md);
- [spec thiết kế giao diện](../../doc/web-thiet-ke-giao-dien-spec.md) (font Be Vietnam Pro, logo và favicon WayFinder, màu, bố cục từng trang);
- [spec Pha B2](../../doc/pha-b2-spec.md) cho mọi hợp đồng nội dung học;
- [ADR 0023](../../doc/adr/0023-cloudinary-cho-tep-goc-va-anh.md): tệp gốc và ảnh ở Cloudinary (gói miễn phí, riêng tư), artifact Pha A ở đĩa.

**Quyết định mới của chủ dự án 2026-10-24:** nhóm thiết kế bàn giao HTML/CSS/token để nhóm web tham khảo và triển khai React;
hai nhóm soát giao diện thật. Bỏ điều kiện Cloud Figma, nhận có ghi chú mốc thiết kế web W-22/W-24 đã kiểm.
W-23 đối chiếu React với spec/token/mẫu HTML, vẫn chờ các màn W-08/W-09/W-10 để nhận toàn bộ.
SA-66 đã ghép `ba4350f`, **SA-69 đã ghép `973fa99`**; W-09 được gỡ chặn và nhận main để làm sau W-08, kiểm bằng fake hợp đồng đúng.
[Bản giao việc đã chỉnh](../../report/lenh-giao-viec-ba-nhom-lan3-2026-10-23.md), [quyết định và ghi chú](../../report/dieu-chinh-giao-viec-web-thiet-ke-2026-10-24.md).

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
| [W-04](W-04-ho-so-doi-mat-khau-dang-xuat-moi-noi.md) | hồ sơ, đổi mật khẩu, đăng xuất mọi nơi | W-02 | backend c1f2fe9 đạt · ghép local 1be7e1c; toàn vé còn React do web sau W-16 |
| [W-05](W-05-kho-pha-b-postgresql.md) | kho Pha B trên PostgreSQL, `single_flight` liên tiến trình, nới port sổ chi | W-01 | đạt · đã ghép `a3f2f13`, gồm checkpoint W-02; [cổng và bàn giao](../../report/dieu-phoi-ghep-main-2026-10-20.md) |
| [W-06](W-06-khoa-mau-khoa-hoc-cua-toi-gateway.md) | khoá mẫu, "Khoá học của tôi", `LearningGateway`, test người ngoài khoá | W-02, W-05 | đạt · đã ghép `dc41ee8`, mốc `8b6e500`; 2.107 Python/77 React/build, browser PG; [nghiệm thu](../../report/dieu-phoi-nghiem-thu-w06-va-ke-hoach-2026-10-21.md) |
| [W-07](W-07-trang-lo-trinh-tien-do.md) | trang lộ trình và tiến độ | W-06, SA-34 | đạt · đã ghép f20d198, mốc 2a14723; 2.114 Python/85 React/build, browser PostgreSQL: 11 kiểm tra/6 cấu hình; [soát](../../report/dieu-phoi-nghiem-thu-w07-w14-w24-va-ke-hoach-2026-10-21.md) |
| [W-08](W-08-trang-hoc-bai-giang-doc-trang.md) | trang học: bài giảng stream, "Đọc trang p" | W-07; SA-62/64/65/70 đã ghép | đạt · ghép local `bad8e45`, cổng `c4d281b`: 2.602Python/0fail/1skip/1xfail,181React/build; browser12cấu hình/109ảnh/17Axe; đóng2Required, [lần4](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan4-2026-10-24.md) |
| [W-09](W-09-tro-ly-va-phien.md) | trợ lý và phiên chat | W-08 và SA-66/69/70 đã ghép | đạt 378131e · ghép local 7f54b14; đóng hai Required, 203 React/102 ảnh/46 Axe; [lần6](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan6-2026-10-25.md) |
| [W-10](W-10-quiz-tai-lieu-thu-vien.md) | quiz, tài liệu, thư viện | W-07; SA-67/68 đã ghép | đạt aaf68eb · ghép local 1be7e1c; đóng 2 Required, 2.824 Python/219 React/build và browser; [lần8](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan8-2026-10-26.md) |
| [W-11](W-11-chia-se-link-thanh-vien.md) | chia sẻ bằng link, thành viên, rời khoá | W-06; W-14 đã ghép | đạt · ghép/đẩy `e85427a`, mốc `b625752`: 2.296 Python/143 React/build, browser 8 auth-return/48 ảnh/16 Axe; [soát lần2](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan2-2026-10-23.md) |
| [W-12](W-12-moi-qua-email.md) | mời qua email, lời mời trong ứng dụng | W-03, W-11 | giao lõi mốc backend sau W-04; web React sau W-16/W-04, chưa đóng toàn vé |
| [W-13](W-13-dung-mot-cuon-o-loi.md) | use case `build_document` ở lõi | — | đạt nghiệm thu; doc-6 hoàn tất cả hai kho, điều phối tái lập 0 USD; [soát mới](../../report/dieu-phoi-kiem-lai-w13-w24-2026-10-19.md) |
| [W-14](W-14-tai-sach-len-ban-dung.md) | tải sách lên, xác nhận, kiểm sớm, hàng đợi, worker, ghi usage thực; bộ dựng giả | W-03, W-06; W-25 đã đạt | đạt có ghi chú · đã ghép/đẩy `7fe63df`, mốc `61b5d80`:2185Python/104React/build, browser13nhóm/47ảnh/14Axe,0USD; [soát](../../report/dieu-phoi-nghiem-thu-w14-ba-nhom-va-ke-hoach-2026-10-22.md) |
| [W-15](W-15-noi-bo-dung-that-do-usd-cuon.md) | nối bộ dựng thật, đo USD/cuốn và phút/cuốn | W-13/14/SA-62 đã đạt | đạt có ghi chú efed8db · ghép local 7f54b14; dựng thật/đo chi/core retry; billing demo chưa đối soát, không nhận production SMTP/media; [lần6](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan6-2026-10-25.md) |
| [W-16](W-16-muc-dung.md) | trang mức dùng và dải hết trần | W-09, W-14 | backend d1bf42b đã đạt; W-10 đã nhận, giao web mở nhánh React W-16; toàn vé còn mở |
| [W-17](W-17-quan-tri.md) | quản trị: người dùng, bản dựng, chi, khoá mẫu, nhật ký | W-14, W-16 | chờ W-16 đầy đủ; chưa giao triển khai |
| [W-18](W-18-tien-do-thanh-vien-cho-chu-khoa.md) | tiến độ tổng hợp của thành viên cho chủ khoá | W-07, W-11 | ready-for-agent |
| [W-19](W-19-bao-loi-noi-dung.md) | báo lỗi nội dung | W-08, W-09, W-10 | ready-for-agent |
| [W-20](W-20-xoa-tai-khoan-xoa-khoa-hoc.md) | xoá tài khoản, xoá khoá học | W-11, W-14 | ready-for-agent |
| [W-21](W-21-trien-khai-sao-luu-thu-dau-cuoi.md) | triển khai, sao lưu, thử đầu-cuối, soát an ninh | W-12, W-15, W-17, W-20 | ready-for-agent |
| [W-22](W-22-ban-figma.md) | bàn giao thiết kế web HTML/CSS/token | — | đạt có ghi chú mốc web đã kiểm, theo chủ dự án 24/10; bỏ Cloud Figma, tiếp hỗ trợ React và các màn theo vé tương ứng |
| [W-23](W-23-doi-chieu-figma-va-giao-dien.md) | đối chiếu React với spec/token/mẫu HTML | W-22/W-24 đã nhận; W-08/W-09/W-10 | chưa đạt; W-10 đã nhận nên gỡ chờ chức năng, cần ảnh cùng state/viewport/video; D-R8-01 đã đính chính, không Cloud |
| [W-24](W-24-bo-sung-va-sua-ban-giao-w22.md) | sửa/bổ sung bàn giao thiết kế web | — | guard JS D-R7-02 feb5f5e đạt · ghép local 1be7e1c; 64 test/3 mutant độc lập, W-23 còn mở |
| [W-25](W-25-dong-bo-xac-nhan-huy-va-ket-thuc-ban-dung.md) | sửa race xác nhận/huỷ và huỷ khi publication W-14 | mã W-14 5b24ece, không chờ W-14 đạt | đạt · đã ghép/đẩy a572459, mốc4dbfe8e; 2.163 Python/85 React nền/build, sáu guard bị bắt, 0USD |

## Thứ tự đề xuất

**Ưu tiên lần 8:** web W-16 React → soát → W-04 React; lõi W-12 backend + mẫu thư; thiết kế hoàn tất W-23 và hỗ trợ các mẫu mới. Mỗi vé một nhánh/worktree. W-17 chờ toàn W-16; W-18/W-19/W-20 chưa đóng, W-21 chưa đến lượt. Đọc lời giao lần8 trước các thứ tự lịch sử dưới đây.

- **Ưu tiên lần 7, 2026-10-26:** web sửa hai Required W-10, sau nghiệm thu mới React W-16; lõi backend W-04; thiết kế guard thực thi JS và W-23 với nguồn ảnh/trạng thái đúng. Backend W-16 và mẫu W-10 đã nhận, không làm lại nền/core/pipeline, không chạy paid hoặc push GitHub. Xem lời giao lần 7 ở đầu tài liệu.

- **Ưu tiên lần 6, 2026-10-25:** web W-10; lõi backend W-16 theo phạm vi tệp riêng; thiết kế sửa D-R6-01 và đối chiếu W-23 trên React thực. W-09/W-15 đã nhận; không chạy lại paid, không push GitHub. Xem lời giao lần 6 ở đầu tài liệu.

- **Điều chỉnh 2026-10-24:** web sửa W-08; SA-66/SA-69 đã ghép, W-09 nhận main triển khai/kiểm bằng fake sau W-08.
  Theo dõi SA-70 về stream tự kiểm tra, giữ hồi quy W-08 tới khi nhận mã mới. Thiết kế tiếp bàn giao HTML/CSS/token và hỗ trợ soát React;
  W-22/W-24 đã nhận có ghi chú phạm vi web, bỏ Cloud. Lõi tiếp W-15; W-10 đọc spec mới document-3/quiz-3 và chờ mốc SA-67/68.
  Các đoạn kế hoạch cũ bên dưới giữ làm lịch sử; ưu tiên bản giao việc đã chỉnh ngày 24/10.

- **Nghiệm thu lần 3 tối 2026-10-23:** chưa ghép gói mới. Web sửa hai Required W-08 trước W-09; lõi tiếp W-15 sau port ngay:
  pipeline giả/PG → cache/identity → dry-run 0 USD → đề nghị trần riêng. Thiết kế giữ Variables/chat đã đạt, sửa preview/hồ sơ,
  giữ guard đầu ra thực và hoàn thiện Cloud. SA-62/64/65 đã ở main; SA-66 chờ Claude ghép cho answer-3.
  W-10 nhận spec SA-67/68 khi được chốt; W-23 chưa đủ phụ thuộc.
  [Biên bản](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan3-2026-10-23.md), [lời giao ba nhóm](../../report/lenh-giao-viec-ba-nhom-lan3-2026-10-23.md).

- **SA-62 hoàn tất 2026-10-23:** đã ghép/đẩy `9ac2a85`, gỡ chờ port của W-15; bổ sung ca dương default factory/PG tại `ce5f581`.
  Giữ hai ca âm factory cũ, RED bỏ injection bị assertion bắt. Sau khi main nhận SA-64, đã kiểm chứng tổ hợp tại `14110c0`:
  **2.355 Python đạt/0 fail/1 Cloudinary live không bật,143 React/build**, 0 USD. Ghi rõ thiếu sót trình tự ghép và hai lượt kiểm trong báo cáo.
  W-15 tiếp kiểm toàn pipeline/identity/cache/dry-run0USD, chưa chạy có tiền. W-08 đủ core SA-64 đã ghép1d91b0b, nhận main làm lecture-3;
  W-09 vẫn chờ SA-66 cho answer-3, SA-65 ảnh trang theo làn Claude. [Báo cáo/JUnit](../../report/sa62-tiep-nhan-test-web-2026-10-23.md).

- **Nghiệm thu lần 2 chiều 2026-10-23:** W-11 và mốc trace/test tương thích W-15 đạt, ghép/đẩy `e85427a`, mốc kiểm `b625752`.
  2.296 Python đạt/1 Cloudinary live không bật, 143 React/build; browser PG 48 ảnh/16 Axe/115 HTTP, 8 ca auth-return, DB/cổng đã dừng.
  Main có tài liệu `9ee69ce` ngay trước ghép; đã kiểm chứng sau ghép trên `817f487`, cùng 2.296 Python/143 React/build xanh; báo cáo giữ rõ thiếu sót trình tự và hai lượt cổng.
  W-24 còn3nhóm Required (plugin lỗi/guard, chat hạn mức/internal, checklist); các sửa cũ đã chứng minh đạt không giao lại, chưa ghép hai checkpoint mới.
  **Web W-08 theo lecture-3/ADR 0025, cổng cuối chờ SA-64 (thay SA-63), rồi W-09/W-10.** Lõi nhận SA-62 sau Claude ghép, kiểm PG/pipeline và dry-run0USD;
  thiết kế sửa3Required và cập nhật lecture-3, hoàn thiện Cloud. SA-65 ảnh trang ở artifact do Claude làm, không đổi DB; giữ Vertex.
  [Báo cáo lần 2](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan2-2026-10-23.md), [lời giao ba nhóm](../../report/lenh-giao-viec-ba-nhom-lan2-2026-10-23.md).

- **Sau soát ba nhóm, 2026-10-23:** W-11 `8539709` cần sửa mất `next` khi đổi form xác thực, tái hiện độc lập 8 assertion fail/2 control pass, chưa ghép.
  W-15 nhận riêng mốc adapter/kiểm 0 USD `eea5472`, ghép/đẩy **`d12b67c`**: 2.266 Python đạt/1 Cloudinary live không bật, 104 React/build; toàn vé vẫn chờ port PG, dry-run và duyệt tiền riêng.
  W-24 `16e95c1` còn năm Required mới về URL/quota-dữ liệu/plugin/mobile/checklist; 18 cấu hình browser không thay việc sửa lỗi. Cloud đọc lại vẫn 0 Variables/components/reactions/starting points.
  **Web sửa W-11 → W-08 → W-09 → W-10; lõi phối hợp port và kiểm identity/cache 0 USD; thiết kế sửa Required trước rồi chứng minh Cloud thật.**
  SA-56/57 và SA-58 đã ghép, gỡ chờ cũ của W-09; nối wrapper lecture/cache_only và không dùng replay tool schema cũ.
  Giữ Vertex tới chỉ thị demo của chủ dự án; SA-61 phải ghép trước lần đổi Developer API. Không dọn worktree/dữ liệu, không chi thêm.
  [Nghiệm thu/bằng chứng](../../report/dieu-phoi-nghiem-thu-w11-w15-w24-va-ke-hoach-2026-10-23.md), [lời giao ba nhóm](../../report/lenh-giao-viec-sau-w11-2026-10-23.md). Chưa gửi phiên nhân viên bên ngoài.

- **Kiểm lại 2026-10-22:** backend/schema W-14+W-25 đạt tại `4dbfe8e`, đã ghép/đẩy **`a572459`**, 2.163 Python/85 React nền/build, sáu guard bị bắt, 0 USD.
  **Web nhận main ngay**, không còn chờ backend: bỏ32 tệp basetemp khỏi Git/giữ local, giữ DTO upload_id/confirmed_at và chạy cổng W-14 cuối; W-14 đầu-cuối chưa đóng.
  Lõi bàn giao/hỗ trợ tích hợp, chưa chạy thật W-15. Thiết kế tiếp W-24: còn OS reduced-motion ảnh hỏng, token/guard chưa đủ và checklist/Cloud.
  W-08 còn chờ SA-53 qua SA-40/41, W-10 chờ SA-52; các nhánh SA do Claude nghiệm thu/ghép. Giữ W-11 riêng, hoàn tất sau W-14 nếu một phiên web; migration nối w14_0006.
  [Báo cáo và bằng chứng](../../report/dieu-phoi-kiem-lai-w25-w14-react-w24-va-ke-hoach-2026-10-22.md), [lời giao ba nhóm](../../report/lenh-giao-viec-sau-w25-2026-10-22.md). Chưa gửi phiên nhân viên.

- **Sau soát W-07/W-14/W-24, 2026-10-21:** W-07 đạt tại `2a14723`, đã ghép/đẩy `f20d198` (2.114 Python/85 React/build, browser PostgreSQL: 11 kiểm tra/6 cấu hình, 10 mutation bị bắt).
  W-14 backend chưa đạt do hai race huỷ tái hiện bằng PG; lõi ưu tiên **W-25**, web **React/tích hợp W-14** theo hợp đồng, giữ W-11 đang làm riêng.
  W-24 `c1df32a` chưa đạt, thiết kế sửa sáu nhóm Required, không lấy raw/preview mới làm chuẩn đã nghiệm thu.
  Giữ tuyến `w06_0005 → w14_0006 → w11_0007`; W-25 đạt mới ghép backend/schema W-14, rồi W-11 nối sau. React W-14 đạt mới đóng toàn W-14/mở W-15.
  [Phán xét/điểm kiểm](../../report/dieu-phoi-nghiem-thu-w07-w14-w24-va-ke-hoach-2026-10-21.md), [lời giao ba nhóm](../../report/lenh-giao-viec-sau-w07-2026-10-21.md). Chưa gửi phiên nhân viên, 0 USD.

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
