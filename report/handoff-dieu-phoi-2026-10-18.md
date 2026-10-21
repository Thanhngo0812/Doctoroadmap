# Bàn giao điều phối — Pha B, Pha B2, web WayFinder (2026-10-18)

**Dòng trạng thái:** viết xong 2026-10-18 tối, bởi Claude, trước khi hết lượt dùng. Người điều phối cập nhật **mục 10 (nhật ký điều phối)** mỗi ngày, và
sửa mục 2 khi trạng thái đổi.

**Tiếp nhận 2026-10-18:** Codex nhận vai trò điều phối theo yêu cầu trực tiếp của chủ dự án. Đã đối chiếu Git, mã, kế hoạch, spec, báo cáo và chạy lại
280 test Pha B/B2 cùng 7 phép thử sửa sai phần nền. Báo cáo tiếp nhận và lời giao việc cụ thể ở
[báo cáo điều phối](dieu-phoi-tiep-nhan-2026-10-18.md). Đây chưa phải phán xét nghiệm thu SA-45.

**Tài liệu này dành cho ai:** người điều phối thay Claude trong những ngày Claude không có lượt. Đó có thể là chủ dự án, một nhân viên cấp cao, hay một
agent khác. Người điều phối:
- theo dõi các bảng vé, chọn vé tiếp theo, soạn lời giao vé, nhắc chủ dự án;
- chuyển báo cáo của người làm sang người soát, ghi phán xét vào bảng;
- gom câu hỏi thiết kế cho chủ dự án và cho Claude.

**Người điều phối không được:**
- duyệt tiền: chỉ chủ dự án duyệt;
- đổi spec, ADR, hay quyết định của chủ dự án: ghi thành câu hỏi ở mục 8;
- tự viết mã sản phẩm;
- mở tập giữ lại (mục 7).

**Đọc theo thứ tự:** mục 1 → cập nhật mới nhất ở mục 2 → 3 → 4, rồi các mục khác khi cần.

---

## 1. Ai làm gì

| vai | ai | làm | không làm |
|---|---|---|---|
| chủ dự án | chủ dự án | duyệt tiền, chốt thiết kế, giao việc, cấp tài khoản và khoá (Cloudinary, Gmail, Gemini), cung cấp logo | |
| người điều phối | Codex, tiếp nhận 2026-10-18 | chọn vé, soạn lời giao vé, nhắc, gom câu hỏi, giữ nhật ký | duyệt tiền, đổi spec, tự viết mã sản phẩm |
| người soát cấp cao | nhân viên cấp cao, vé [SA-45](../task/sau-a10/45-soat-thay-claude-nhan-vien-cap-cao.md) | soát vé Pha B, ghi phán xét, tạo vé sửa từ SA-46; soát cả vé web, vé sửa web từ W-24 | đổi spec, ADR, quyết định Q1–Q30 |
| nhân viên lõi | nhân viên đã làm SA-01…44 | vé Pha B, phần lõi của web: W-05 (nới port), W-13, W-15 | sửa tệp của phiên pha A |
| nhóm web (4 người) | nhóm đồ án | vé W-01…W-21, W-23 | sửa lõi ngoài W-05, W-13 |
| người thiết kế | trong nhóm | W-22 (Figma) | vẽ lại logo |
| agentic | họ mô hình **khác Gemini** | bộ câu hỏi thử 19a | thấy đáp án câu kiểm |
| phiên pha A | phiên Claude riêng | đồ thị, chuỗi gộp | |
| Claude | khi có lượt | nghiên cứu, kiểm thử, soát, nhắc việc, điều phối, viết spec và vé | cài mã sản phẩm |

## 2. Tình hình lúc bàn giao

**Pha B (vé `task/sau-a10/`, [kế hoạch](../task/sau-a10/00-ke-hoach.md)):**
- **SA-01…28:** đã soát. Còn treo:
  - lượt thật của SA-08, 10, 13 chưa chạy lại sau các vé sửa;
  - SA-28 chưa đạt, đã giao sang SA-29.
- **SA-29** (tên module): đã cài và chạy (commit `2356ee8`), chi 0,1425 USD trong trần 0,50 USD chủ dự án duyệt. Kết quả: tên LLM 136/160, mô tả LLM 82/160.
  **Chưa soát.** Doc-1 chỉ còn 1/33 mô tả do LLM viết; cần đọc kỹ.
- **SA-30** (K6, cache bài hỏng, TTFT, câu trích, tài liệu): đã cài, cùng commit. **Chưa soát.**
- **SA-31…44** (Pha B2):
  - nhân viên báo đã cài; bản bàn giao mới ghi 280 test đạt, ở [report/pha-b2-ban-giao-31-44-2026-10-18.md](pha-b2-ban-giao-31-44-2026-10-18.md) cùng 4 báo cáo con;
  - **đã commit:** `a7f57d0` ghép B2, `3871c85` sửa cắt đuôi bài giảng sau lỗi hậu cổng. Lúc Codex tiếp nhận, không có thay đổi chưa commit trong `src/`;
    đã chạy lại **280/280 test đạt**, cùng **7/7** bản sửa sai phần nền bị test bắt. **Vẫn chờ soát độc lập**, không giao lại việc commit B2;
  - **SA-43:** lượt thật đã chạy trong trần 0,50 USD chủ dự án duyệt, chi 0,0652 USD. Còn chờ soát nội dung 12 bài;
  - **SA-44:** còn 7 thao tác thử tay và ảnh chụp, vì công cụ trình duyệt của nhân viên bị chặn;
  - **ví dụ JSON thật cho nhóm web** ở `report/pha-b2-contract-examples-2026-10-18.json`.
- **Đồ thị hiện hành** (bản tên mới nhất): doc-1 v57, nhap-mon-ml v50, naive-bayes v49, doc-6 v29, xstk-ch3-1 v68, doc-4 v27.
- **SA-19a** (bộ câu hỏi thử): gói đã xuất ở `Desktop\pha-b-cau-hoi-thu\giao-agentic\`. **Chưa giao agentic.**
- **SA-20…23** (đánh giá): chạy sau khi soát xong các vé sửa và B2.
- **SA-45** (người soát cấp cao): vé sẵn, **chưa giao**.

**Web WayFinder (vé `task/web/`, [kế hoạch](../task/web/00-ke-hoach.md)):**
- Đã có:
  - [spec chức năng](../doc/web-chuc-nang-spec.md), [spec cơ sở dữ liệu](../doc/web-co-so-du-lieu-spec.md), [spec thiết kế](../doc/web-thiet-ke-giao-dien-spec.md);
  - ADR 0020–0023;
  - 23 vé gốc W-01…W-23; chủ dự án đã cho W-01/W-13/W-22 khởi động. Trạng thái hiện hành xem kế hoạch web; vé sửa sau soát bắt đầu từ W-24.
- **Quyết định của chủ dự án ngày 2026-10-18:**
  - mã web gom vào `src/web`; PostgreSQL chạy bằng Docker;
  - Cloudinary giữ tệp gốc và ảnh, tài sản riêng tư;
  - bản demo: ai cũng tải sách được, khâu dựng không giới hạn;
  - khoá mẫu chỉ có ở dev;
  - gửi thư bằng Gmail SMTP; dùng một tài khoản Cloudinary;
  - chủ khoá xem được tiến độ lớp.
- **Tệp thương hiệu** ở `design/` (chưa commit, của chủ dự án):
  - 6 favicon (`OTP1`–`OTP6`) và GIF chờ (7,4 MB);
  - **cập nhật 2026-10-19:** logo thực là 20 tệp `Artboard 9.png` đến `Artboard 28.png`, đã có đủ trong `design/`, thay tên giả định `logo1`–`logo8`.
    Đã xem ảnh: Artboard 21–24 đen nền trong, 25–28 trắng nền trong. W-01/W-22 không còn chờ logo; bảng dùng theo spec thiết kế mục 1.

**Cập nhật tiếp nhận W-13 ngày 2026-10-19:** W-13 đã có mã lõi/báo cáo triển khai nhưng **chưa commit, chưa soát độc lập** tại lượt kiểm đó; xem
[tiếp nhận W-13](dieu-phoi-tiep-nhan-w13-2026-10-19.md). Điều phối chạy lại 65 test W-13 + 2 kiến trúc đạt, bốn mutation bị bắt. CLI ghi SQLite;
PostgreSQL/worker web còn thuộc W-14. Doc-6 toàn chuỗi còn thiếu cache label-roles. Không coi báo triển khai là phán xét đạt.

**Tiếp nhận W-22 ngày 2026-10-19:** đã có token, preview, ảnh và link Figma; **chưa đủ nghiệm thu**. Điều phối chạy lại 20 test/17 cặp màu đạt,
nhưng kiểm Chrome thấy nút tối thiếu tương phản, vùng bấm mobile dưới 44 px, GIF vẫn chạy khi giảm chuyển động; đổi sai CSS mà 20 test vẫn xanh.
Chưa xác minh được đủ trang/trạng thái và bốn prototype trong Figma. Đã soạn [W-24](../task/web/W-24-bo-sung-va-sua-ban-giao-w22.md), chờ chủ dự án giao;
xem [tiếp nhận W-22](dieu-phoi-tiep-nhan-w22-2026-10-19.md). W-01 tiếp tục nền; W-23 chờ W-22 nghiệm thu.
Tại lượt này đã thấy `src/web/`, chưa soát hay xác nhận nghiệm thu W-01.

**Kiểm lại sau ba nhóm báo xong, 2026-10-19:** xem [soát ba nhóm và kế hoạch tiếp](dieu-phoi-soat-ba-nhom-2026-10-19.md).
W-01 đạt nền local: React 23 test/build, trình duyệt 6 tổ hợp đạt; `src/web/` chưa được Git theo dõi, cần ghim commit đúng phạm vi.
W-13 đã commit `e9ffce1`, điều phối chạy lại 68 test và 4 mutation đạt; doc-6 hết chuỗi vẫn thiếu cache, chưa đóng phần này.
W-24 đã bàn giao và sửa một phần nhưng chưa đạt toàn bộ: desktop GIF còn chạy khi giảm chuyển động, guard spacing/RGBA còn lọt,
bằng chứng đủ trang/Variables/bốn prototype Figma còn thiếu. Sau checkpoint W-01 mở W-02 cho web, W-05 cho lõi; thiết kế tiếp tục W-24.
Migration theo tuyến W-01 → W-05 → W-02, không tự tạo hai head; chưa mở W-15/W-23.

**Cập nhật sau bản sửa `7baa7d2`, 2026-10-19:** [kiểm lại W-13/W-24](dieu-phoi-kiem-lai-w13-w24-2026-10-19.md).
W-13 **đạt nghiệm thu**, đã kiểm độc lập doc-6 ở cả hai kho đủ bốn bước, graph 37/8, không gọi mô hình; 83 test W-13/kiến trúc/token đạt.
Nhân viên đã chạy hai lượt có tiền sau duyệt, tổng chi usage ghi nhận 0,2329025 USD, một lượt có cờ thiếu usage; đợt điều phối không phát sinh chi.
W-24 đã sửa đạt GIF/vùng bấm/guard/chat cũ; còn Variables thực (plugin lệch sáu màu tối), đủ trang/prototype và khung auth 390 tràn 20 px.
Không giao lại lỗi đã đóng. W-15 gỡ điểm chờ W-13, vẫn chờ W-14; kế hoạch W-02/W-05 tiếp tục, W-23 chưa mở.

**Cập nhật nghiệm thu 2026-10-20:** [soát W-02/W-05/W-24 và kế hoạch tiếp](dieu-phoi-nghiem-thu-w02-w05-w24-2026-10-20.md).
W-02/W-05 **đạt nghiệm thu độc lập local**, gồm tuyến `w01_0001 → w05_0002 → w02_0003`, một head và kiểm DB rỗng/baseline.
Điều phối tự chạy 168 backend/token đạt, 1 Cloudinary live không bật, 33 hồi quy lõi đạt; React sau sửa UI mới 41/41 và build đạt.
Mutation bỏ hạn idle, flight lock và atomic lock đều đỏ đúng assertion; browser/ảnh/video ở báo cáo, không gọi mô hình hay gửi thư thật.
W-24 đóng sáu màu plugin và auth tràn 390 cùng các lỗi runtime cũ; **còn hai nhóm**: nguồn export Figma, đủ trang/prototype có kiểm chứng.
Export hiện sinh từ JSON local, audit vẫn báo 4/4 khi cố ý gỡ handler. Không giao lại lỗi kỹ thuật đã đóng.
Đợt tới web ưu tiên W-03, lõi backend/gateway W-06 với web React/tích hợp, thiết kế hoàn thiện W-24 và màn W-03.
Đặt tuyến migration tiếp `w03_0004 → w06_0005`; W-04 chia sau nếu còn người; W-15 vẫn chờ W-14, W-23 chưa mở.
Giữ các yêu cầu soát độc lập SA-46/47/49/50/51 và đề xuất focus_node_id chờ duyệt ở mục 8; Vertex giữ nguyên.

**Ghép bù theo quy trình mới 2026-10-20:** [biên bản tích hợp](dieu-phoi-ghep-main-2026-10-20.md), theo quyết định `a4800a8`.
W-02/W-05 đã ghép main bằng `a3f2f13`, đúng mốc đã soát `8558df4`. Cổng cuối: 1.999 Python đạt, 1 Cloudinary live không bật,
React 41/build đạt; giữ đủ bằng chứng các lượt đỏ do môi trường trước đó. Đã đẩy main cùng hồ sơ tới `83f3ffd`; thư mục chung đã về main.
W-03 lưu snapshot `fdd0620`, đã chuyển `tmp/w03-email-recovery`, nhận main và cài React; phiên web đã được báo chờ chủ dự án mở lại đúng thư mục.
Thiết kế đã có `tmp/w24-figma-evidence` nhận main, chủ dự án chuyển lời giao. Giữ worktree W-05-core còn sửa dở; nhánh biên bản W-13 giữ lại do phép so sánh `tasks/todo.md` khác sau W-05.
Không kéo `781415b`/`79cb9c9`/`6cd6be7` hay mã W-03 vào bản ghép. W-13 không cần merge nhánh biên bản vì nội dung báo cáo đã có trên main.

## 3. Việc ngay, theo thứ tự

Mỗi việc ghi ai làm, và xong thì người điều phối đánh dấu ở mục 10.

**Ưu tiên hiện hành 2026-10-20:** chủ dự án chuyển [W-03](../task/web/W-03-xac-minh-email-quen-mat-khau.md) cho web,
[W-06](../task/web/W-06-khoa-mau-khoa-hoc-cua-toi-gateway.md) cho lõi backend và web React,
[W-24 phần còn lại](../task/web/W-24-bo-sung-va-sua-ban-giao-w22.md) cho thiết kế, kèm màn W-03.
Tiếp tục làn soát Pha B theo ghi chú Claude ở mục 8. Các mốc W-01/W-13/W-02/W-05 đã đạt, không giao lại.
Danh sách dưới giữ bối cảnh công việc từ lúc tiếp nhận; trạng thái mới ở mục 2 và nhật ký cuối tài liệu được ưu tiên.

1. **[Đã xong, Codex kiểm chứng] Mã SA-31…44 đã có commit để soát.**
   - Ghim `a7f57d0` và bản sửa `3871c85`; bộ kiểm Pha B/B2 của đợt tiếp nhận đạt 280 test. Đây không phải toàn bộ test của repo.
   - Thư mục làm việc vẫn còn tệp dở của người khác: `.gitignore`, `scripts/pass-phu-ml/*`, `task/v4/*`,
     `report/huong-dan-agentic-gan-nhan-d02.md` và tệp chưa được theo dõi. Không stage hay commit lẫn.
   - **Việc ưu tiên hiện tại chuyển sang giao SA-45**, không yêu cầu nhân viên commit lại B2.
2. **[Chủ dự án] Giao SA-45 cho nhân viên cấp cao.** Hàng đợi soát: SA-29 → SA-30 → SA-31…44 (đọc bàn giao B2 trước) → nội dung 12 bài của SA-43.
3. **[Chủ dự án] Làm 7 thao tác thử tay của SA-44**, hoặc bật quyền trình duyệt cho nhân viên.
   - Máy chủ xem thử ngoại tuyến: `http://127.0.0.1:18765/`, kho `tmp/b2-preview-manual.json`.
   - Danh sách 7 thao tác ở `report/pha-b2-sa37-44-2026-10-18.md` và ở vé SA-44.
   - Chụp ảnh từng thao tác, gửi người soát.
4. **[Chủ dự án] Giao gói 19a cho agentic** (họ mô hình khác Gemini).
   - Thư mục giao: `Desktop\pha-b-cau-hoi-thu\giao-agentic\`.
   - **Không** giao `Desktop\pha-b-cau-hoi-thu-nguoi-giu\`.
   - Agentic trả về thì người soát chạy `scripts/pha-b/kiem_cau_hoi_thu.py`, rồi chấm 12 câu kiểm bằng đáp án ở thư mục người giữ.
5. **[Chủ dự án] Chuẩn bị tài khoản cho web:**
   - `CLOUDINARY_URL` vào `.env`; bật "Allow delivery of PDF and ZIP files" (Settings → Security); xem cỡ tệp tối đa và tín dụng của gói;
   - Gmail: bật xác minh hai bước, tạo mật khẩu ứng dụng, đặt vào `.env`;
   - Docker Desktop (nền WSL2) trên máy của nhóm web;
   - logo đã có đủ Artboard 9–28, gồm PNG nền trong; SVG có thể bổ sung nếu có. Tệp gốc GIF là phần riêng, gửi nếu có để xuất lại vòng chờ.
6. **[Chủ dự án giao, cập nhật 2026-10-20] Ba nhóm chạy tiếp:**
   - **Web:** W-03, đồng thời bố trí người React/tích hợp W-06; W-04 chia sau nếu còn người;
   - **Lõi:** backend/gateway W-06 ở `src/web/`, kiểm use case/spend guard thực sự dùng PostgreSQL; W-13/W-05 đã đạt;
   - **Thiết kế:** chỉ hai nhóm bằng chứng W-24 còn lại và ưu tiên màn xác minh/đặt lại mật khẩu W-03. Thương hiệu giữ Artboard 9–28.

## 4. Cách giao một vé

**Chọn vé:** chỉ giao vé có mọi vé ở cột "chặn bởi" đã **đạt**, tức đã soát. Báo xong mà chưa soát thì chưa tính.

**Không giao song song hai vé sửa cùng một vùng mã.** Các cặp dễ đụng nhau:
- W-05 và mọi vé sửa kho Pha B (SA-46+ nếu chạm `phase_b_store.py`, `ports/phase_b.py`);
- W-13 và mọi vé của phiên pha A;
- W-06 với W-07…W-10, vì cả năm vé cùng thêm hàm vào `LearningGateway`. W-07 xong rồi mới giao song song W-08, W-09, W-10, mỗi vé một người.

**Lời giao vé mẫu** (dán cho người nhận, thay phần trong ngoặc):

> Bạn nhận vé [mã vé] ([đường dẫn tệp vé]). Đọc theo thứ tự: vé, kế hoạch vé ([đường dẫn 00-ke-hoach.md]) mục "Luật chung", rồi các spec mà vé dẫn ở
> dòng "Nguồn chân lý".
>
> Luật bắt buộc:
> - Làm trong worktree `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\<tên>`, nhánh `work/<tên>`, theo
>   [quy trình nhánh và ghép main](../doc/quy-trinh-nhanh-va-ghep-main.md). Không làm ở thư mục chung, không đổi nhánh của nó.
> - Chạy test qua `scripts/w05_run_tests.py` từ gốc worktree, bằng Python của `.venv` thư mục chung; không chạy pytest trần.
> - Không tự ghép vào main. Không sửa tệp vé, bảng kế hoạch hay bàn giao; điều cần ghi thì ghi trong báo cáo vé.
> - Lưu dần: làm tới đâu commit tới đó. Báo cáo vé có dòng trạng thái ở đầu.
> - Chỉ commit đường dẫn của vé, bằng `git commit -m … -- <tệp>`.
> - Không mở tập giữ lại: `d01-t01`, `d01-t02`, `document-data/test/`, `Desktop\d02-tap-khoa`; không in phần `cache` của `artifacts/phase_b/live.json`.
> - Lượt có tiền thì dry-run trước, gửi con số, chờ chủ dự án duyệt rồi mới chạy. Chỉ dùng `gemini-3.1-flash-lite`.
> - Mỗi tiêu chí nghiệm thu là một test thấy đỏ trên bản sai trước rồi mới xanh. Ghi lệnh đã chạy và số test vào báo cáo.
> - Thấy spec sai hay thiếu thì ghi vào mục "Câu hỏi" của báo cáo, không tự đổi spec.
> - Bí mật (`CLOUDINARY_URL`, mật khẩu Gmail, khoá Gemini) chỉ ở `.env`; không dán vào báo cáo hay chat.
>
> Xong thì báo cáo ở [report/<tên-vé>-<ngày>.md], kèm ảnh chụp (vé có giao diện) và ví dụ JSON thật (vé có điểm cuối mới).

**Nhận báo cáo:**
1. Kiểm báo cáo có đủ: lệnh đã chạy, số test, ảnh chụp hay ví dụ JSON nếu vé yêu cầu, tiền đã chi.
2. Chuyển cho người soát (SA-45). Người soát làm theo SA-45 mục 3: chạy test, thử sửa sai, đọc tận nơi đầu ra, kiểm lại một hai con số.
3. Ghi phán xét vào cột trạng thái của bảng kế hoạch: **đạt**, **đạt có ghi chú**, hay **chưa đạt → vé sửa số …**.
4. **Chưa đạt:** người soát tạo vé sửa theo khuôn của SA-45 mục 4, đánh số SA-46+ cho Pha B hay W-24+ cho web. Người điều phối sửa cột "chặn bởi" của các vé bị
   ảnh hưởng.

**Lượt có tiền:**
1. Người làm chạy dry-run và gửi con số.
2. Người điều phối chuyển con số cho chủ dự án, nói rõ lượt này để làm gì.
3. Chủ dự án trả lời bằng tin nhắn; người làm trích tin nhắn đó vào báo cáo.
4. Chạy xong thì ghi chi thật vào mục 10.

Hiện chỉ W-15 lượt 2 (dựng một cuốn mới, ước dưới 3 USD) và các lượt thật của SA-08, 10, 13 còn chờ chạy.

## 5. Lịch giao theo làn

Bốn làn chạy song song; trong mỗi làn, làm theo thứ tự.

| làn | thứ tự | ghi chú |
|---|---|---|
| **soát Pha B** (người soát) | SA-29 → SA-30 → SA-31…44 → nội dung SA-43 → các vé sửa SA-46+ → lượt thật SA-08, 10, 13 (chủ dự án duyệt) → SA-20…23 | SA-20…23 chỉ chạy khi mọi vé sửa đạt |
| **lõi** (nhân viên lõi) | W-13/W-05 đã đạt → backend/gateway W-06 cùng web → W-15 sau W-14; xử lý vé sửa SA-46+ theo soát | W-06 là vé chung, chỉ đạt khi đủ React/tích hợp; không tự sửa lõi ngoài phạm vi đã cho |
| **web** (nhóm web) | W-01/W-02 đã đạt → W-03, React/tích hợp W-06; W-04 khi có người → W-07 → (W-08 ∥ W-09 ∥ W-10) → (W-11 → W-12) ∥ W-14 → W-16 → W-17 ∥ W-18 ∥ W-19 → W-20 → W-21 → W-23 | phần học W-07…W-10 cần Pha B2 **đạt**; W-14 sau W-03/W-06 |
| **thiết kế** (người thiết kế) | hoàn thiện hai nhóm bằng chứng W-24/W-22, màn W-03 → duyệt ảnh chụp từng vé web → W-23 cùng web | logo Artboard 9–28 đã đủ; không giao lại lỗi runtime đã đóng |

Lịch theo làn là hướng dẫn phân người, không thêm cạnh chặn mới. Khi chọn vé, kiểm bảng phụ thuộc trong kế hoạch web: W-11 có thể bắt đầu sau W-06;
W-18 sau W-07/W-11; W-20 sau W-11/W-14. Không bắt các vé này chờ toàn bộ phần học nếu không có xung đột tệp thực tế.

**Điểm chờ dễ kẹt:**
- W-02/W-05 đã đạt, W-06 không còn chặn ở hai vé này. Web bàn giao migration `w03_0004` trước khi lõi ghép `w06_0005`; service/test/UI không phải chờ toàn bộ W-03.
- W-03/W-04 cùng sửa AccountService; chỉ làm song song khi đã phân vùng sửa. W-06 phải kiểm use case/spend guard cùng dùng kho PostgreSQL, không chỉ thay thuộc tính composition.
- W-08, W-09, W-10 cần các vé B2 được soát **đạt**. Người soát nên ưu tiên SA-32, 33, 35, 37, 39, 40, 41, 42.

## 6. Khi nào gọi chủ dự án ngay

Nhắn chủ dự án ngay, không chờ, khi có một trong các việc sau:
- một lượt cần chi tiền;
- người làm muốn đổi spec, ADR, hay quyết định;
- có người lỡ mở tập giữ lại, hay in nội dung của nó. Dừng vé đó lại, ghi chính xác đã thấy gì;
- test trên nhánh chính đỏ sau một commit;
- commit lẫn tệp của người khác;
- thiếu khoá hay tài khoản (Cloudinary, Gmail, Gemini);
- tín dụng Cloudinary trong tháng dùng quá 70%, hay Gmail báo vượt giới hạn gửi;
- câu hỏi cần phiên pha A trả lời (W-13);
- hai người làm cùng sửa một vùng mã.

## 7. Luật bắt buộc

**Tập giữ lại**, không ai được mở:
- `d01-t01`, `d01-t02`: chunk, tên khái niệm, tiêu đề và mô tả module, bài giảng, quiz;
- `document-data/test/`, `Desktop\d02-tap-khoa`, mọi tệp `khoa.jsonl`.
- Phần `cache` của `artifacts/phase_b/live.json` có tiêu đề module của T-01: không in, không nhập vào cơ sở dữ liệu.
- Khi thống kê usage, bỏ các dòng có `doc_id` bắt đầu bằng `d01-t0`.
- Script chỉ nạp sáu cuốn phát triển: doc-1, nhap-mon-ml, naive-bayes, doc-6, xstk-ch3-1, doc-4.
- Checker chạy trên tập giữ lại chỉ in các trường số có trong danh sách cho phép.

**Tiền:**
- chỉ dùng `gemini-3.1-flash-lite`;
- dry-run trước, chủ dự án duyệt;
- soát bằng cách phát lại phản hồi đã ghi, 0 USD.

**Git:** theo [quy trình nhánh và ghép main](../doc/quy-trinh-nhanh-va-ghep-main.md). Thư mục chung luôn ở main; mỗi vé một nhánh trong worktree `tmp/<tên>`.
Chỉ người điều phối ghép, bằng `--no-ff`, sau khi vé được soát đạt và cổng test đầy đủ xanh. Đẩy main lên GitHub sau mỗi lần ghép.
Chỉ commit đường dẫn của mình. Không sửa tệp của phiên pha A.

**Môi trường:**
- Python từ `.venv` ở thư mục chung, vì `python` trần chỉ là stub; dùng đường dẫn đầy đủ khi đứng trong worktree;
- chạy test từ gốc worktree qua `scripts/w05_run_tests.py`, không chạy pytest trần vì editable install có thể nạp nhầm mã;
- runner bắt buộc PostgreSQL và thêm `-p no:cacheprovider`; dùng `--basetemp` mới trong `tmp/`.

**Lưu dần:** mọi người và mọi agent ghi tệp theo từng phần, có dòng trạng thái. Agent nền chạy từng cái một.

**Bí mật:** chỉ ở `.env`.

## 8. Câu hỏi treo

**Cho Claude, khi quay lại:**
1. **S3 hay S2** (stream bài giảng): ở SA-43, khoảng từ cổng tới khi xong bài có p50 = 939 ms, đo trên 4 mẫu. Spec ghi "dưới 1 giây thì báo Claude". 4 mẫu là
   chưa đủ để quyết.
2. **Nhiệt độ của lần sinh lại:** nhánh 1,0 có hai prompt sửa không còn khớp bản ghi, nên chưa so được với nhánh 0.
3. **Thẻ lộ trình doc-4** ước 1.322 token, quá ngưỡng khoảng 800. Cần chọn: tên ngắn, hay lấy chi tiết module khi cần.
4. **Mô tả module của doc-1:** chỉ 1/33 do LLM viết. Xem lại luật từ vựng của mô tả.
5. **2026-10-19, Claude ghi trước khi nghỉ:**
   - SA-48 có báo cáo soát độc lập (`soat-pha-b-sa48-2026-10-19.md`). SA-46, 47, 49, 50, 51 mới có báo cáo bàn giao của nhân viên; khi quay lại phải
     soát độc lập, rồi mới chuyển 34, 37, 40, 42, 43 sang đạt.
   - Câu 1 đã có hướng: SA-45 giữ S3 (vé 39). Câu 2 vẫn treo: SA-51 có 10 cặp khớp, 2 cặp lệch fixture.

**Cho chủ dự án:**
4. **2026-10-19, chờ duyệt — đề xuất `focus_node_id`:**
   - Vấn đề: yêu cầu trợ lý (`answer-2`) không cho biết người học đang mở khái niệm nào. Hỏi "giải thích phần này" thì agent phải đoán bằng `search`.
   - Đề xuất: thêm trường tuỳ chọn `focus_node_id`, web gửi kèm mỗi lượt khi đang mở bài giảng, không lưu vào phiên. Agent nhận thẻ khái niệm và tóm tắt
     bài giảng đã có. Thêm vài trăm token mỗi lượt.
   - Đổi hợp đồng `answer-2`, nên cần chủ dự án duyệt. Duyệt rồi thì Claude viết một vé sửa Pha B (lõi) và thêm phần gửi kèm vào W-09.
1. **Đã rõ theo spec hiện hành, không cần hỏi lại:** giữ trần Pha B 0,20 USD mỗi người học mỗi ngày và 5 USD mỗi ngày cho nội dung dùng chung.
   Spec chức năng web, mục "Quyết định của chủ dự án", đã tách rõ câu "không giới hạn" chỉ áp cho khâu dựng. Chỉ mở lại khi chủ dự án muốn đổi.
2. **Đã giải quyết 2026-10-19:** chủ dự án xác nhận logo là Artboard 9–28; đã kiểm đủ tệp và cập nhật bảng trong spec thiết kế mục 1.
3. **Ghi nhận lịch sử 2026-10-18:** lúc tiếp nhận chưa thấy logo theo tên giả định; nay đã có Artboard 9–28, không còn yêu cầu cung cấp tám logo cũ.

**Cho phiên pha A, qua chủ dự án/nhân viên lõi khi giao W-13:**
1. **2026-10-18, Codex:** xác nhận vị trí A3 tạo ứng viên, chỉ mục A3′ và `label-roles` trong bốn bước công khai của `build_document` cho cuốn mới.
   `Canonicalize._run` đang đọc `load_latest_candidates`; `BuildMentions` đọc `load_latest_retrieval`. Danh sách lệnh dự kiến của W-13 chưa nêu A3/A3′;
   lượt doc-6 dùng dữ liệu cũ không đủ chứng minh chuỗi cho tệp mới. Ghi câu trả lời vào báo cáo W-13, không tự sửa spec hay mã của phiên pha A.
   - **Đã trả lời 2026-10-19 (Claude, ghi trong W-13):**
     - chuỗi: `ingest` → kiểm sớm (gồm cổng chữ, mã `chu_loi`) → `label-roles` → `a3` (A3 cùng A3′) → `a4` → `roadmap` → `learning_prep`;
     - `label-roles` bắt buộc, chạy trước `a3`, vì neo trong `a4` lọc chunk theo `role == noi_dung`;
     - vàng: gọi thẳng `Canonicalize.execute(a4_gold_coverage="none", gold_sheet_id=None)`. Hai trường này chỉ ghi vào manifest, không vào băm cấu hình;
       lệnh `a4` giữ nguyên cổng vàng.

**Người điều phối thêm câu mới vào đây,** kèm ngày và người hỏi.

## 9. Khi Claude quay lại

Claude đọc theo thứ tự:
1. mục 10 của tài liệu này;
2. `report/soat-pha-b-tong-hop-*.md` (SA-45 viết);
3. bảng trạng thái của `task/sau-a10/00-ke-hoach.md` và `task/web/00-ke-hoach.md`;
4. mục 8.

Chủ dự án tóm thêm tình hình bằng lời.

## 10. Nhật ký điều phối

Người điều phối ghi mỗi việc một dòng, mới nhất ở dưới cùng.

| ngày | việc | ai | trạng thái | ghi chú |
|---|---|---|---|---|
| 2026-10-18 | bàn giao điều phối | Claude | xong | spec web, ADR 0020–0023, vé W-01…W-23 đã commit |
| 2026-10-18 | commit mã SA-31…44 | nhân viên lõi | xong, Codex đã đối chiếu | `a7f57d0`, bản sửa `3871c85`; chưa thay thế soát SA-45 |
| | giao SA-45 | chủ dự án | chờ | |
| | 7 thao tác thử tay SA-44 | chủ dự án | chờ | |
| | giao 19a cho agentic | chủ dự án | chờ | |
| | tài khoản Cloudinary, Gmail, Docker; logo | chủ dự án | chờ | |
| | giao W-01, W-13, W-22 | chủ dự án | chờ | |
| 2026-10-18 | chính thức tiếp nhận điều phối | Codex | đã nhận | chủ dự án yêu cầu trực tiếp trong chat; giữ phạm vi vai trò ở mục 1 |
| 2026-10-18 | chạy lại kiểm Pha B/B2 và kiến trúc | Codex | 280/280 đạt | lần sandbox: 272 đạt, 8 lỗi quyền socket; chạy lại có quyền localhost: 280 đạt; không gọi mô hình trả phí |
| 2026-10-18 | kiểm phép sửa sai nền B2 | Codex | 7/7 bị test bắt | `scripts/phase-b/b2_foundation_mutations.py`; chỉ thay trong tiến trình thử |
| 2026-10-18 | đối chiếu sáu đồ thị phát triển | Codex | xong | 160 module, 901 khái niệm học; 136 tên LLM, 82 mô tả LLM; doc-1: 1/33 mô tả LLM |
| 2026-10-18 | đối chiếu web, thương hiệu, trần học | Codex | xong, còn việc giao | chưa có `src/web`; chưa thấy tám logo; trần học đã rõ trong spec, không hỏi lại |
| 2026-10-18 | soạn đợt giao việc tiếp theo | Codex | đã soạn, chưa gửi sang phiên khác | SA-45 ưu tiên; W-01 bắt đầu; W-13 xác nhận chuỗi mới; W-22 chuẩn bị phần không phụ thuộc logo; xem báo cáo tiếp nhận |
| 2026-10-18 | bổ sung yêu cầu giao diện theo chỉ thị chủ dự án | Codex | đã cập nhật spec và vé | Figma/React phải đẹp, chỉn chu, hiệu ứng phù hợp; được dùng `taste-skill` do chủ dự án nạp; tiêu chí ở spec thiết kế mục 3a, luật chung web, W-01/W-22/W-23 |
| 2026-10-18 | chốt đường Gemini backend web theo chỉ thị chủ dự án | Codex | đã cập nhật spec và vé | FastAPI/worker dùng Gemini Developer API bằng API key, không dùng Vertex; đồng bộ W-01/W-06/W-13/W-15/W-21 và luật chung; chưa sửa runtime sản phẩm |
| 2026-10-19 | đổi lại đường Gemini backend web theo chỉ thị mới | Codex | thay quyết định 2026-10-18 | FastAPI/worker tạm dùng Vertex cho sinh/embedding/dựng sách; chỉ chuyển Developer API khi chủ dự án yêu cầu chuẩn bị demo; đã đồng bộ spec và các vé, chưa sửa runtime hay bí mật |
| 2026-10-19 | xác nhận bộ logo thực tế theo chủ dự án | Codex | đủ 20 tệp, gỡ chờ logo | Artboard 9–28 trong `design/`; đã xem hình/alpha, cập nhật spec, W-01/W-22, luật chung và lời giao việc; thanh trên sáng/tối dùng Artboard 24/28 |
| 2026-10-19 | tiếp nhận triển khai W-13 | Codex | đã triển khai, chờ commit/soát | tự chạy lại 67 test đạt và 4/4 mutation bị bắt; kiểm XML nhân viên 1868/65 đều xanh; doc-6 toàn chuỗi chưa hoàn tất, PostgreSQL thuộc W-14; xem báo cáo tiếp nhận |
| 2026-10-19 | đồng bộ luồng dựng theo quyết định trong spec mục 4 | Codex | đã cập nhật tài liệu phụ thuộc | thả tệp → xác nhận → dựng; không dự toán/chi phí cho người dùng; ghi usage thực vào DB, kể cả lỗi/huỷ; W-14/W-15/W-21 và spec chức năng/CSDL đã đồng bộ, duyệt tiền nội bộ vẫn bắt buộc |
| 2026-10-19 | tiếp nhận và kiểm W-22 | Codex | chưa đủ nghiệm thu | 20 test/17 cặp đạt; 56 giá trị JSON/CSS khớp trong phạm vi kiểm; Chrome tái hiện lỗi nút tối, vùng bấm, GIF; phép đổi sai CSS không bị test bắt; Figma chưa xác minh trực tiếp |
| 2026-10-19 | soạn W-24 sửa/bổ sung W-22 | Codex | đã soạn, chưa gửi phiên khác | người làm W-22 sửa và bổ sung node/Variables/ảnh/video; W-01 tiếp tục nền theo spec, W-23 chờ W-22 nghiệm thu; bằng chứng ở artifacts/coord-w22-2026-10-19 |
| 2026-10-19 | kiểm lại bàn giao ba nhóm W-01/W-13/W-22-W-24 | Codex | nền local và lõi đã kiểm; thiết kế còn mở | 68 test W-13, 71 test web/token + 1 Cloudinary không bật, 23 React/build; browser W-01 đạt; W-13 4 mutation bị bắt; W-24 còn GIF/guard/vùng bấm và bằng chứng Figma |
| 2026-10-19 | soạn đợt W-02/W-05 và tiếp tục W-24 | Codex | đã cập nhật kế hoạch/vé, chưa gửi phiên khác | chốt commit W-01 trước; migration một tuyến W-01→W-05→W-02; giữ phần dựng hết cuốn W-13 mở, chưa duyệt chi hay mở W-15/W-23 |
| 2026-10-19 | kiểm lại W-13 sau doc-6 hoàn tất | Codex | đạt nghiệm thu W-13 | hai kho tái lập succeeded, đủ bốn bước, 0 lời gọi/0 USD; DB/artifact/PDF khớp; 83 test gộp đạt, mutation bỏ sửa cache bị bắt |
| 2026-10-19 | kiểm lại W-24 bản 7baa7d2 | Codex | đóng lỗi runtime cũ, chưa đóng toàn vé | GIF tĩnh bốn preview, vùng bấm cũ đạt, ba mutation token bị bắt, chat an toàn với payload thử; còn Figma/trang/prototype và khung auth 390 |
| 2026-10-20 | nghiệm thu độc lập W-02/W-05 và migration ghép | Codex | đạt phạm vi vé local | 168 backend/token đạt, 1 Cloudinary live không bật; 33 hồi quy lõi; React sau sửa UI 41/build; browser DB riêng, không gọi mô hình/gửi thư; xem báo cáo ngày 20 |
| 2026-10-20 | kiểm W-24 ba73cfc | Codex | kỹ thuật đạt, bằng chứng còn thiếu | đóng sáu màu plugin/auth 390; export tái lập từ JSON local; gỡ handler mà audit vẫn 4/4, chưa đủ bốn luồng gốc/Figma/trang |
| 2026-10-20 | soạn đợt W-03/W-06, tiếp tục phần còn lại W-24 | Codex | cập nhật kế hoạch/vé, chưa gửi phiên khác | web W-03 và React W-06, lõi backend W-06, thiết kế W-24/màn W-03; dành migration w03_0004→w06_0005; W-15/W-23 giữ phụ thuộc |
| 2026-10-20 | ghép bù W-02/W-05 theo quy trình a4800a8 | Codex | đã ghép a3f2f13 và đẩy GitHub tới 83f3ffd | mốc 8558df4; 1.999 Python đạt, 1 Cloudinary live không bật; React 41/build; thư mục chung về main; không kéo các commit chưa soát |
| 2026-10-20 | chuyển W-03/W-24 sang worktree riêng, dọn sau ghép | Codex | đã chuẩn bị và thông báo | W-03 snapshot fdd0620, nhận main 83f3ffd, npm ci/.env; thiết kế giữ 781415b/helper ở nhánh riêng; gỡ W-05-postgres sạch và nhánh W-02 đã được W-03 giữ lịch sử; giữ W-05-core bẩn và nhánh W-13 do điều kiện so sánh chưa thoả |
| 2026-10-20 | xử lý sự cố cache sau dọn worktree | Codex | doc-6 khôi phục đủ, doc-1 còn thiếu | Đã xác minh lệnh tạo junction ở W-05 và mốc gỡ 09:35; tháo riêng junction t01a sau dir /AL, 564 tệp đối chứng giữ nguyên; 787/927 hash khớp, doc-6 122/122, 12 kiểm tập trung đạt. Chi mới 0 USD; xem report/su-co-va-khoi-phuc-cache-2026-10-20.md |
| 2026-10-20 | dry-run đợt dựng lại doc-1 theo chỉ thị chủ dự án | Codex | đã dry-run, CHỜ tin nhắn duyệt có tiền | Main 88a6905, Nhe 102 trang/302 chunk, parse v6/chunks v8; 0 API/0 USD; roles 16 gọi, 0,018842 USD ước tính. Tổng tham chiếu 1,18–2,67 USD, đề nghị ngân sách 3 USD chưa duyệt. Không sửa test v45; fixture chờ quyết định. Xem report/doc1-du-tru-dung-lai-2026-10-20.md; tiền thật sau lượt chạy ghi thêm tại mục này |
| 2026-10-20 | nhận phê duyệt khôi phục toàn chuỗi và quyết định fixture | Codex | đã duyệt, đang chạy | Tin nhắn chủ dự án: “duyệt tất cả làm end to end khôi phục đi”; duyệt ngân sách 3 USD cho doc-1 qua Vertex và fixture nhỏ trong repo + snapshot SHA-256 cho kiểm tích hợp. Đã chép/đối chiếu 816 tệp trước dựng; không dùng liên kết. Chi thực chốt sau chạy tại report/doc1-khoi-phuc-end-to-end-2026-10-20.md |
| 2026-10-20 | khôi phục/dựng lại dữ liệu phát triển theo phê duyệt | Codex | đạt phạm vi đợt khôi phục | Doc-6 kiểm lại 122/122 SHA-256; doc-1 v8 có 35 module/223 khái niệm học được/475 requires_edges, A12 302 chunk, concept-index 223, ảnh 2.602 occurrence/2.234 PNG hợp lệ. Hai lượt thực chi **1,542275 USD** (1,35301175 + 0,18926325), ghi DB; replay 0 call/0 USD. Giữ usage_complete=false vì 75 HTTP 429, sổ phản hồi thành công đủ token. Bản sao mới 3.081 tệp và ZIP dưới document-data; 140 tệp lịch sử chưa khôi phục đúng hash không bị tính thay bằng bản mới. Xem report/doc1-khoi-phuc-end-to-end-2026-10-20.md |
| 2026-10-20 | chốt fixture quiz và đường cache Pha B doc-1 | Codex | đã kiểm, giữ rõ giới hạn | Quiz unit dùng fixture trong repo, không phụ thuộc v45. Kho mới artifacts/phase_b/doc-1-rebuild-20261020.json, thao tác học dùng graph v8 và --store rõ; 35 thẻ/tên khớp ngữ cảnh mới, đổi 1 node gây 1 cache miss, CLI/kiểm cache 0 API. Chưa so được cache v45/v57; quiz cloze offline ở module thử chỉ 1/5 câu, chưa nghiệm thu mọi quiz thật đủ 5; không sửa sản phẩm để che giới hạn. Runbook doc/du-lieu-phat-trien-va-fixture.md |
| 2026-10-20 | ghép fixture phục hồi vào main | Codex | đã ghép 34d2257 và đẩy GitHub | Mốc soát a69ebe2; worktree mới chỉ chép 3.081 tệp, cổng PostgreSQL/runner **1.999 đạt, 0 fail, 1 Cloudinary live không bật, exit 0**; React 41/build. Đã giữ cả bằng chứng vỏ PowerShell trả 1 vì cảnh báo rồi chạy lại xác nhận native exit 0. Giữ mọi worktree/snapshot, không dọn |
| 2026-10-20 | kiểm thử và nghiệm thu W-03 theo yêu cầu chủ dự án | Codex | đạt, đã ghép `63f09ad` và đẩy GitHub | Nhóm web giao e1f6297; điều phối sửa năm câu TTL thiết kế tại 9de8e75 (xác minh 24 giờ/reset 60 phút). Cổng đúng 9de8e75: **2.085 Python đạt, 0 fail, 1 Cloudinary live không bật, exit 0; React 62/build đạt**. Chromium HTTP/PostgreSQL/Argon2 thật: 18 cấu hình/8 assertion, 0 JS/overflow/axe được phát hiện; Mailer giả, **0 lời gọi mô hình/0 USD**. Mã merge khớp mốc đã kiểm; phần thiết kế local mang theo được xét, W-24/Figma đầy đủ chưa đóng. Xem report/dieu-phoi-nghiem-thu-w03-va-ke-hoach-2026-10-20.md |
| 2026-10-20 | lập kế hoạch khởi động lại sau sự cố artifact | Codex | đã cập nhật hồ sơ, lời giao để chủ dự án chuyển | Ghi nhận nhóm web mới xong W-03, W-06 chưa nghiệm thu. Sáu graph dev tải được (doc-1 v8/doc-6 v29); ưu tiên lõi backend/gateway W-06 + web React/tích hợp W-06, thiết kế tiếp W-24/hỗ trợ màn khoá học. Chốt hợp đồng join-sample/test người ngoài trước cài; migration w06_0005 nối w03_0004. W-04 sau W-06 nếu một phiên web; W-07/W-11/W-14 sau W-06 theo phụ thuộc, W-15 cần duyệt tiền riêng. Lời giao ở report/lenh-giao-viec-sau-w03-2026-10-20.md; không gửi sang phiên khác, không dọn worktree/snapshot |
| 2026-10-20 | làm rõ member và ngữ cảnh kiểm tham gia khoá mẫu | Codex | đã chuẩn hoá tài liệu theo quyền có sẵn | Member là người tham gia khoá; membership có role owner/learner. Spec đã cho tài khoản đăng nhập tham gia mẫu dev, nên không hỏi duyệt lại: test tự liệt kê mọi route cid nhắm khoá riêng tư phải trả not_found, kể cả join-sample; test riêng cho tham gia mẫu dev. Không miễn route khỏi bộ kiểm, không mở nội dung khoá cho người ngoài; chỉ đổi câu chữ tài liệu, không sửa mã sản phẩm |
| 2026-10-20 | đóng gói bốn cuốn còn thiếu cho W-06 theo yêu cầu chủ dự án | Codex | đã kiểm dữ liệu và gửi đúng nhân viên lõi | Snapshot document-data/development-w06-four-books-2026-10-20: **64/64 tệp SHA-256 khớp**, 82.876.105 byte; ZIP 23.235.604 byte kiểm CRC/hash từng entry. PDF khớp parse; graph nhap-mon-ml v50/naive-bayes v49/xstk-ch3-1 v68/doc-4 v27 và retrieval tương thích, tải lại từ bản chép riêng; phá hash/path traversal bị bắt. Gộp danh mục gói doc-1/doc-6 cũ thành 3.145 tệp đã kiểm; 0 mạng/0 mô hình/**0 USD**, không tạo liên kết hoặc dọn worktree. Đã gửi phiên lõi 01a14ef0-6db3-77c2-908e-fe8b0451b3e1, có biên nhận; chưa nghiệm thu W-06. Xem report/w06-ban-giao-bon-cuon-2026-10-20.md |
| 2026-10-21 | soát và nghiệm thu W-06 cả ba nhóm | Codex | đạt, đã ghép **dc41ee8** và đẩy GitHub | Nhận lõi bde3e0b/web d9b5e1a/thiết kế63dd8bd; mốc tích hợp soát **8b6e500**, chỉ sửa Required câu chữ/claim thiết kế. Worktree mới chép 3.144 tệp theo hash, không cache CLI/liên kết; **2.107 Python đạt, 0 fail, 1 Cloudinary live không bật; React 77/build; browser PG 9 assertion/6 cấu hình, 8/8 mutation bị bắt**, đúng một head w06_0005. 0 gọi mô hình/**0 USD**; FakeMailer/MemoryMediaStore, DB UUID riêng đã đóng/xoá, không seed DB phát triển. Xem report/dieu-phoi-nghiem-thu-w06-va-ke-hoach-2026-10-21.md |
| 2026-10-21 | phán xét thiết kế và lập đợt sau W-06 | Codex | local đã ghép, W-24 Cloud vẫn mở; kế hoạch đã cập nhật, chưa gửi phiên khác | Sửa nhầm trạng thái xác minh 24h, resend60s và claim nối reactions/Cloud/audit quá bằng chứng; 12 preview local đạt hình học sau ổn định. SA-47 memory/JSON được soát độc lập, 8 test trong cổng đạt; đủ mở W-07 theo hợp đồng, W-07 vẫn cần kiểm race/cách ly PG. Web ưu tiên W-07 rồi W-11; lõi backend/worker W-14 bộ dựng giả; thiết kế W-24/Figma + W-07/W-14. W-14 thêm FK build_id/nguồn upload; migration nhận head theo thứ tự ghép. W-15 cần dry-run/duyệt tiền mới; không dọn worktree/snapshot |
